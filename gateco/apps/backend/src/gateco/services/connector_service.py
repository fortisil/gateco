"""Connector CRUD service."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.enums import ConnectorStatus, ConnectorType
from gateco.database.models.connector import Connector
from gateco.exceptions import NotFoundError, ValidationError
from gateco.schemas.connectors import CONNECTOR_SECRET_FIELDS, SEARCH_CONFIG_REQUIRED_FIELDS
from gateco.services.connector_testers import run_connection_test
from gateco.utils.crypto import decrypt_config_secrets, encrypt_config_secrets, mask_config_secrets
from gateco.utils.patch import apply_patch


def _secret_fields(connector_type: str) -> list[str]:
    return CONNECTOR_SECRET_FIELDS.get(connector_type, [])


def _serialize(c: Connector, bound_vector_count: int = 0) -> dict:
    config = mask_config_secrets(c.config or {}, _secret_fields(c.type.value))
    search_cfg = c.search_config
    connection_ready = c.status == ConnectorStatus.connected
    search_ready = (
        search_cfg is not None
        and _has_required_search_fields(c.type.value, search_cfg)
    )

    record_count = c.record_count or 0
    if record_count > 0 and bound_vector_count > 0:
        coverage_pct = round(bound_vector_count / record_count * 100, 2)
    else:
        coverage_pct = None

    from gateco.services.binding_service import compute_policy_readiness

    mode = getattr(c, "metadata_resolution_mode", None) or "sidecar"
    s_cfg = search_cfg or {}

    has_resource_level_bindings = False
    if mode == "sidecar" and bound_vector_count > 0:
        has_resource_level_bindings = True
    elif mode == "sql_view" and s_cfg.get("metadata_view_name"):
        has_resource_level_bindings = True
    elif mode == "inline" and s_cfg.get("metadata_field_mapping"):
        has_resource_level_bindings = True
    elif mode == "auto":
        has_resource_level_bindings = (
            bound_vector_count > 0
            or bool(s_cfg.get("metadata_view_name"))
            or bool(s_cfg.get("metadata_field_mapping"))
        )

    has_chunk_level = mode in ("inline", "sql_view") and has_resource_level_bindings

    policy_readiness_level = compute_policy_readiness(
        connection_ready,
        search_ready,
        coverage_pct,
        metadata_resolution_mode=mode,
        has_resource_level_bindings=has_resource_level_bindings,
        has_chunk_level_policy_metadata=has_chunk_level,
    )

    from gateco.services.ingestion_service import TIER_1_CONNECTORS

    ingestion_capable = c.type in TIER_1_CONNECTORS
    ingestion_ready = ingestion_capable and bool(c.ingestion_config)

    return {
        "id": str(c.id),
        "name": c.name,
        "type": c.type.value,
        "status": c.status.value,
        "config": config,
        "last_sync": c.last_sync.isoformat() if c.last_sync else None,
        "index_count": c.index_count,
        "record_count": c.record_count,
        "error_message": c.error_message,
        "created_at": c.created_at.isoformat(),
        "updated_at": c.updated_at.isoformat(),
        "last_tested_at": c.last_tested_at.isoformat() if c.last_tested_at else None,
        "last_test_success": c.last_test_success,
        "last_test_latency_ms": c.last_test_latency_ms,
        "server_version": c.server_version,
        "diagnostics": c.diagnostics,
        "search_config": search_cfg,
        "connection_ready": connection_ready,
        "search_ready": search_ready,
        "bound_vector_count": bound_vector_count,
        "coverage_pct": coverage_pct,
        "policy_readiness_level": policy_readiness_level,
        "ingestion_capable": ingestion_capable,
        "ingestion_ready": ingestion_ready,
        "ingestion_config": c.ingestion_config,
        "metadata_resolution_mode": getattr(c, "metadata_resolution_mode", None) or "sidecar",
    }


def _has_required_search_fields(connector_type: str, search_config: dict) -> bool:
    required = SEARCH_CONFIG_REQUIRED_FIELDS.get(connector_type, [])
    return all(search_config.get(f) for f in required)


async def list_connectors(session: AsyncSession, org_id: UUID) -> list[dict]:
    from sqlalchemy import func

    from gateco.database.models.resource_chunk import ResourceChunk

    result = await session.execute(
        select(Connector)
        .where(Connector.organization_id == org_id, Connector.deleted_at.is_(None))
        .order_by(Connector.created_at.desc())
    )
    connectors = list(result.scalars().all())

    # Batch-fetch bound vector counts
    if connectors:
        connector_ids = [c.id for c in connectors]
        count_result = await session.execute(
            select(
                ResourceChunk.source_connector_id,
                func.count(),
            )
            .where(ResourceChunk.source_connector_id.in_(connector_ids))
            .group_by(ResourceChunk.source_connector_id)
        )
        bound_counts = {row[0]: row[1] for row in count_result.all()}
    else:
        bound_counts = {}

    return [
        _serialize(c, bound_vector_count=bound_counts.get(c.id, 0))
        for c in connectors
    ]


async def get_connector(session: AsyncSession, org_id: UUID, connector_id: UUID) -> dict:
    from sqlalchemy import func

    from gateco.database.models.resource_chunk import ResourceChunk

    c = await _load(session, org_id, connector_id)
    count_result = await session.execute(
        select(func.count()).select_from(ResourceChunk).where(
            ResourceChunk.source_connector_id == connector_id,
        )
    )
    bound_count = count_result.scalar() or 0
    return _serialize(c, bound_vector_count=bound_count)


async def create_connector(
    session: AsyncSession,
    org_id: UUID,
    name: str,
    type_: str,
    config: dict,
    metadata_resolution_mode: str | None = None,
) -> dict:
    try:
        ct = ConnectorType(type_)
    except ValueError:
        raise ValidationError(detail=f"Invalid connector type: {type_}")

    if metadata_resolution_mode:
        _validate_metadata_resolution_mode(metadata_resolution_mode, type_)

    encrypted = encrypt_config_secrets(config, _secret_fields(type_))
    c = Connector(
        organization_id=org_id,
        name=name.strip(),
        type=ct,
        status=ConnectorStatus.disconnected,
        config=encrypted,
        metadata_resolution_mode=metadata_resolution_mode or "sidecar",
    )
    session.add(c)
    await session.flush()
    return _serialize(c)


async def update_connector(
    session: AsyncSession,
    org_id: UUID,
    connector_id: UUID,
    name: str | None,
    config: dict | None,
    metadata_resolution_mode: str | None = None,
) -> dict:
    c = await _load(session, org_id, connector_id)
    if name is not None:
        c.name = name.strip()
    if config is not None:
        sf = _secret_fields(c.type.value)
        merged = apply_patch(c.config or {}, config, secret_fields=sf)
        c.config = encrypt_config_secrets(merged, sf)
    if metadata_resolution_mode is not None:
        _validate_metadata_resolution_mode(metadata_resolution_mode, c.type.value)
        c.metadata_resolution_mode = metadata_resolution_mode
    await session.flush()
    return _serialize(c)


async def update_search_config(
    session: AsyncSession, org_id: UUID, connector_id: UUID, search_config: dict
) -> dict:
    """Update the search configuration for a connector."""
    c = await _load(session, org_id, connector_id)
    required = SEARCH_CONFIG_REQUIRED_FIELDS.get(c.type.value, [])
    missing = [f for f in required if not search_config.get(f)]
    if missing:
        raise ValidationError(detail=f"Missing required search config fields: {', '.join(missing)}")
    c.search_config = search_config
    await session.flush()
    return _serialize(c)


async def get_search_config(session: AsyncSession, org_id: UUID, connector_id: UUID) -> dict:
    """Get the search configuration for a connector."""
    c = await _load(session, org_id, connector_id)
    return {"search_config": c.search_config}


async def get_ingestion_config(session: AsyncSession, org_id: UUID, connector_id: UUID) -> dict:
    """Get the ingestion configuration for a connector."""
    c = await _load(session, org_id, connector_id)
    return {"ingestion_config": c.ingestion_config}


async def update_ingestion_config(
    session: AsyncSession, org_id: UUID, connector_id: UUID, ingestion_config: dict
) -> dict:
    """Update the ingestion configuration for a connector."""
    c = await _load(session, org_id, connector_id)
    c.ingestion_config = ingestion_config
    await session.flush()
    return _serialize(c)


async def delete_connector(session: AsyncSession, org_id: UUID, connector_id: UUID) -> None:
    c = await _load(session, org_id, connector_id)
    c.soft_delete()


async def test_connector(session: AsyncSession, org_id: UUID, connector_id: UUID) -> dict:
    """Test connector by performing a real, bounded, read-only health check."""
    c = await _load(session, org_id, connector_id)
    decrypted = decrypt_config_secrets(c.config or {}, _secret_fields(c.type.value))
    result = await run_connection_test(c.type.value, decrypted)

    # Persist diagnostics
    c.last_tested_at = datetime.now(timezone.utc)
    c.last_test_success = result.success
    c.last_test_latency_ms = result.latency_ms
    c.diagnostics = result.to_dict()
    if result.server_version:
        c.server_version = result.server_version

    # Update connector status
    if result.success:
        c.status = ConnectorStatus.connected
        c.error_message = None
        if result.total_records is not None:
            c.record_count = result.total_records
        if result.resources is not None:
            c.index_count = len(result.resources)
    else:
        c.status = ConnectorStatus.error
        c.error_message = result.error

    await session.flush()
    return result.to_dict()


def _validate_metadata_resolution_mode(mode: str, connector_type: str) -> None:
    """Validate metadata_resolution_mode against connector type constraints."""
    from gateco.schemas.connectors import POSTGRES_FAMILY_TYPES, VALID_METADATA_RESOLUTION_MODES

    if mode not in VALID_METADATA_RESOLUTION_MODES:
        raise ValidationError(
            detail=f"Invalid metadata_resolution_mode: {mode}. "
            f"Must be one of: {', '.join(sorted(VALID_METADATA_RESOLUTION_MODES))}"
        )
    if mode == "sql_view" and connector_type not in POSTGRES_FAMILY_TYPES:
        raise ValidationError(
            detail=f"sql_view mode is only available for Postgres-family connectors "
            f"({', '.join(sorted(POSTGRES_FAMILY_TYPES))}), not '{connector_type}'"
        )


async def _load(session: AsyncSession, org_id: UUID, connector_id: UUID) -> Connector:
    result = await session.execute(
        select(Connector).where(
            Connector.id == connector_id,
            Connector.organization_id == org_id,
            Connector.deleted_at.is_(None),
        )
    )
    c = result.scalar_one_or_none()
    if not c:
        raise NotFoundError(detail="Connector not found")
    return c
