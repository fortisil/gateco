"""Retroactive registration service — scans vector DBs for unmanaged vectors and registers them.

Discovers vectors in connectors that have a list_vector_ids adapter, regardless of whether they
support direct ingestion. Creates GatedResource + ResourceChunk records so they become
policy-managed.
"""

import logging
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.enums import (
    AuditEventType,
    Classification,
    ConnectorType,
    ResourceType,
    Sensitivity,
)
from gateco.database.models.connector import Connector
from gateco.database.models.resource import GatedResource
from gateco.database.models.resource_chunk import ResourceChunk
from gateco.exceptions import ValidationError
from gateco.schemas.retroactive import (
    RetroactiveRegisterRequest,
    RetroactiveRegisterResponse,
)
from gateco.services import audit_service
from gateco.services.connector_adapters import LISTERS, list_vector_ids
from gateco.services.connector_service import _load
from gateco.services.ingestion_service import VALID_CLASSIFICATIONS, VALID_SENSITIVITIES
from gateco.utils.crypto import decrypt_config_secrets

logger = logging.getLogger(__name__)


async def retroactive_register(
    session: AsyncSession,
    org_id: UUID,
    request: RetroactiveRegisterRequest,
    actor_id: UUID | None = None,
    actor_name: str = "",
) -> RetroactiveRegisterResponse:
    """Scan a connector's vector DB and register unmanaged vectors as gated resources.

    Args:
        session: DB session.
        org_id: Organization ID.
        request: Retroactive registration request.
        actor_id: Optional actor for audit trail.
        actor_name: Optional actor name for audit trail.

    Returns:
        RetroactiveRegisterResponse with scan/registration counts.

    Raises:
        ValidationError: If connector is invalid or not Tier 1.
    """
    connector_id = UUID(request.connector_id)

    # 1. Load and validate connector
    connector = await _load(session, org_id, connector_id)
    if connector.type.value not in LISTERS:
        raise ValidationError(
            detail=(
                f"Connector type '{connector.type.value}' is not supported for "
                f"retroactive registration. Supported types: "
                f"{', '.join(sorted(LISTERS.keys()))}"
            ),
        )

    # Validate default metadata values
    if request.default_classification and request.default_classification not in VALID_CLASSIFICATIONS:
        raise ValidationError(
            detail=f"Invalid default_classification: {request.default_classification}",
        )
    if request.default_sensitivity and request.default_sensitivity not in VALID_SENSITIVITIES:
        raise ValidationError(
            detail=f"Invalid default_sensitivity: {request.default_sensitivity}",
        )

    # Validate grouping strategy
    if request.grouping_strategy not in ("individual", "regex", "prefix"):
        raise ValidationError(
            detail=f"Invalid grouping_strategy: {request.grouping_strategy}. "
            f"Must be 'individual', 'regex', or 'prefix'.",
        )
    if request.grouping_strategy in ("regex", "prefix") and not request.grouping_pattern:
        raise ValidationError(
            detail=f"grouping_pattern is required for '{request.grouping_strategy}' strategy.",
        )

    # 2. Scan vector IDs from the connector
    from gateco.schemas.connectors import CONNECTOR_SECRET_FIELDS

    secret_fields = CONNECTOR_SECRET_FIELDS.get(connector.type.value, [])
    decrypted_config = decrypt_config_secrets(connector.config or {}, secret_fields)
    search_config = connector.search_config or {}

    try:
        all_vector_ids = await list_vector_ids(
            connector.type.value, decrypted_config, search_config, request.scan_limit,
        )
    except Exception as e:
        raise ValidationError(detail=f"Failed to scan vector IDs: {e}")

    scanned_count = len(all_vector_ids)

    # 3. Find already-registered vector IDs for this connector
    existing_result = await session.execute(
        select(ResourceChunk.vector_id).where(
            ResourceChunk.source_connector_id == connector_id,
            ResourceChunk.vector_id.in_(all_vector_ids) if all_vector_ids else False,
        )
    )
    registered_ids = {row[0] for row in existing_result.all()}
    unregistered_ids = [vid for vid in all_vector_ids if vid not in registered_ids]

    already_registered = len(registered_ids)

    # 4. If dry_run, return counts without writing
    if request.dry_run:
        # Compute group count for dry run
        groups = _apply_grouping(unregistered_ids, request.grouping_strategy, request.grouping_pattern)
        return RetroactiveRegisterResponse(
            status="dry_run",
            scanned_vectors=scanned_count,
            already_registered=already_registered,
            newly_registered=len(unregistered_ids),
            resources_created=len(groups),
            errors=[],
        )

    if not unregistered_ids:
        return RetroactiveRegisterResponse(
            status="success",
            scanned_vectors=scanned_count,
            already_registered=already_registered,
            newly_registered=0,
            resources_created=0,
            errors=[],
        )

    # 5. Apply grouping strategy
    groups = _apply_grouping(unregistered_ids, request.grouping_strategy, request.grouping_pattern)

    # 6. Create GatedResource + ResourceChunk records
    errors: list[dict] = []
    resources_created = 0
    newly_registered = 0

    for resource_key, vector_ids in groups.items():
        try:
            resource = GatedResource(
                organization_id=org_id,
                source_connector_id=connector_id,
                external_resource_key=resource_key,
                type=ResourceType.file,
                title=resource_key,
                content_url=f"retroactive://{resource_key}",
            )
            if request.default_classification:
                resource.classification = Classification(request.default_classification)
            if request.default_sensitivity:
                resource.sensitivity = Sensitivity(request.default_sensitivity)
            if request.default_domain:
                resource.domain = request.default_domain
            if request.default_labels:
                resource.labels = request.default_labels

            session.add(resource)
            await session.flush()

            for i, vid in enumerate(vector_ids):
                chunk = ResourceChunk(
                    resource_id=resource.id,
                    source_connector_id=connector_id,
                    index=i,
                    vector_id=vid,
                )
                session.add(chunk)

            resources_created += 1
            newly_registered += len(vector_ids)
        except Exception as e:
            logger.error(
                "retroactive_register_error resource_key=%s error=%s",
                resource_key, str(e),
            )
            errors.append({
                "resource_key": resource_key,
                "vector_count": len(vector_ids),
                "error": str(e),
            })

    await session.flush()

    # 7. Audit event
    status = "success" if not errors else "partial_success"
    await audit_service.emit_event(
        session=session,
        org_id=org_id,
        event_type=AuditEventType.retroactive_registered,
        actor_id=actor_id,
        actor_name=actor_name,
        details=(
            f"Retroactive registration: scanned={scanned_count}, "
            f"registered={newly_registered}, resources={resources_created}, "
            f"errors={len(errors)}, connector={connector_id}"
        ),
    )

    return RetroactiveRegisterResponse(
        status=status,
        scanned_vectors=scanned_count,
        already_registered=already_registered,
        newly_registered=newly_registered,
        resources_created=resources_created,
        errors=errors,
    )


def _apply_grouping(
    vector_ids: list[str],
    strategy: str,
    pattern: str | None,
) -> dict[str, list[str]]:
    """Group vector IDs into resource keys based on the grouping strategy.

    Returns:
        Dict mapping resource_key -> list of vector IDs.
    """
    if strategy == "individual":
        return {vid: [vid] for vid in vector_ids}

    if strategy == "regex":
        compiled = re.compile(pattern)
        groups: dict[str, list[str]] = {}
        for vid in vector_ids:
            match = compiled.search(vid)
            key = match.group(1) if match and match.groups() else vid
            groups.setdefault(key, []).append(vid)
        return groups

    if strategy == "prefix":
        delimiter = pattern or "_"
        groups = {}
        for vid in vector_ids:
            parts = vid.split(delimiter)
            key = parts[0] if len(parts) > 1 else vid
            groups.setdefault(key, []).append(vid)
        return groups

    # Fallback: individual
    return {vid: [vid] for vid in vector_ids}
