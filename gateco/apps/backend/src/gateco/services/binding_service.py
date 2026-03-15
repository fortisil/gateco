"""Binding service — bulk metadata binding into GatedResource + ResourceChunk."""

from collections import defaultdict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.enums import Classification, ResourceType, Sensitivity
from gateco.database.models.resource import GatedResource
from gateco.database.models.resource_chunk import ResourceChunk
from gateco.schemas.bindings import BindingEntry, BindResult, CoverageDetail
from gateco.services.connector_service import _load  # noqa: E402

VALID_CLASSIFICATIONS = {e.value for e in Classification}
VALID_SENSITIVITIES = {e.value for e in Sensitivity}


def _validate_enum_value(value: str | None, valid_set: set[str], label: str) -> str | None:
    """Validate an optional enum value, return error message if invalid."""
    if value is None:
        return None
    if value not in valid_set:
        return f"invalid {label}: {value}"
    return None


def _check_metadata_consistency(
    entries: list[BindingEntry],
) -> tuple[dict, str | None]:
    """Check metadata consistency across entries sharing an external_resource_id.

    Returns (merged_metadata, error_reason).
    """
    merged: dict = {
        "classification": None,
        "sensitivity": None,
        "domain": None,
        "labels": None,
    }
    for entry in entries:
        for field in ("classification", "sensitivity", "domain"):
            val = getattr(entry, field)
            if val is not None:
                if merged[field] is not None and merged[field] != val:
                    return {}, f"conflicting {field}: {merged[field]} vs {val}"
                merged[field] = val
        if entry.labels is not None:
            if merged["labels"] is not None and set(merged["labels"]) != set(entry.labels):
                return {}, (
                    f"conflicting labels: {merged['labels']} vs {entry.labels}"
                )
            merged["labels"] = entry.labels

    # Validate enum values
    err = _validate_enum_value(
        merged["classification"], VALID_CLASSIFICATIONS, "classification"
    )
    if err:
        return {}, err
    err = _validate_enum_value(merged["sensitivity"], VALID_SENSITIVITIES, "sensitivity")
    if err:
        return {}, err

    return merged, None


async def bind_metadata(
    session: AsyncSession,
    org_id: UUID,
    connector_id: UUID,
    bindings: list[BindingEntry],
) -> BindResult:
    """Bind vector metadata to GatedResource + ResourceChunk tables."""
    # Verify connector ownership
    connector = await _load(session, org_id, connector_id)

    # Group bindings by external_resource_id
    groups: dict[str, list[BindingEntry]] = defaultdict(list)
    for entry in bindings:
        groups[entry.external_resource_id].append(entry)

    created_resources = 0
    updated_resources = 0
    created_chunks = 0
    rebound_chunks = 0
    errors: list[dict] = []

    for ext_id, entries in groups.items():
        # Validate metadata consistency within group
        merged_meta, err = _check_metadata_consistency(entries)
        if err:
            errors.append({"external_resource_id": ext_id, "reason": err})
            continue

        # Lookup existing GatedResource
        res_result = await session.execute(
            select(GatedResource).where(
                GatedResource.organization_id == org_id,
                GatedResource.source_connector_id == connector_id,
                GatedResource.external_resource_key == ext_id,
                GatedResource.deleted_at.is_(None),
            )
        )
        resource = res_result.scalar_one_or_none()

        if resource is None:
            # Create new resource
            resource = GatedResource(
                organization_id=org_id,
                source_connector_id=connector_id,
                external_resource_key=ext_id,
                type=ResourceType.file,
                title=ext_id,
                content_url=f"binding://{ext_id}",
            )
            if merged_meta.get("classification"):
                resource.classification = Classification(merged_meta["classification"])
            if merged_meta.get("sensitivity"):
                resource.sensitivity = Sensitivity(merged_meta["sensitivity"])
            if merged_meta.get("domain"):
                resource.domain = merged_meta["domain"]
            if merged_meta.get("labels"):
                resource.labels = merged_meta["labels"]
            session.add(resource)
            await session.flush()
            created_resources += 1
        else:
            # Update existing resource metadata if provided
            updated = False
            if merged_meta.get("classification"):
                resource.classification = Classification(merged_meta["classification"])
                updated = True
            if merged_meta.get("sensitivity"):
                resource.sensitivity = Sensitivity(merged_meta["sensitivity"])
                updated = True
            if merged_meta.get("domain"):
                resource.domain = merged_meta["domain"]
                updated = True
            if merged_meta.get("labels"):
                resource.labels = merged_meta["labels"]
                updated = True
            if updated:
                updated_resources += 1

        # Process chunks for this group
        for entry in entries:
            chunk_result = await session.execute(
                select(ResourceChunk).where(
                    ResourceChunk.source_connector_id == connector_id,
                    ResourceChunk.vector_id == entry.vector_id,
                )
            )
            chunk = chunk_result.scalar_one_or_none()

            if chunk is None:
                # Determine next index for this resource
                max_idx_result = await session.execute(
                    select(func.coalesce(func.max(ResourceChunk.index), -1)).where(
                        ResourceChunk.resource_id == resource.id,
                    )
                )
                next_index = (max_idx_result.scalar() or 0) + 1

                chunk = ResourceChunk(
                    resource_id=resource.id,
                    source_connector_id=connector_id,
                    index=next_index,
                    vector_id=entry.vector_id,
                )
                session.add(chunk)
                created_chunks += 1
            elif chunk.resource_id != resource.id:
                # Rebind to new resource
                chunk.resource_id = resource.id
                rebound_chunks += 1
            # else: already bound to correct resource — no-op

    await session.flush()

    # Compute coverage after binding
    coverage_after = await _compute_coverage_pct(session, connector_id, connector)

    return BindResult(
        created_resources=created_resources,
        updated_resources=updated_resources,
        created_chunks=created_chunks,
        rebound_chunks=rebound_chunks,
        errors=errors,
        coverage_after=coverage_after,
    )


async def _compute_coverage_pct(
    session: AsyncSession, connector_id: UUID, connector=None
) -> float | None:
    """Compute coverage percentage for a connector."""
    bound_result = await session.execute(
        select(func.count()).select_from(ResourceChunk).where(
            ResourceChunk.source_connector_id == connector_id,
        )
    )
    bound_count = bound_result.scalar() or 0

    total_count = connector.record_count if connector else 0
    if not total_count or total_count <= 0:
        return None
    return round(bound_count / total_count * 100, 2)


def compute_policy_readiness(
    connection_ready: bool,
    search_ready: bool,
    coverage_pct: float | None = None,
    *,
    metadata_resolution_mode: str | None = None,
    has_active_policies: bool = False,
    has_resource_level_bindings: bool = False,
    has_chunk_level_policy_metadata: bool = False,
) -> int:
    """Compute semantic policy readiness level (L0-L4).

    Derived from CAPABILITY, not coverage percentage.

    L0: Not Ready — connector not reachable
    L1: Connection Ready — DB reachable, auth valid
    L2: Search Ready / Coarse Policy — can search, connector/namespace-level controls possible
    L3: Resource Policy Ready — resource-level metadata resolution + policy evaluation active
    L4: Chunk Policy Ready — chunk/vector-level metadata used in policy evaluation
    """
    if not connection_ready:
        return 0  # L0: Not Ready
    if not search_ready:
        return 1  # L1: Connection Ready
    if not has_active_policies or not has_resource_level_bindings:
        return 2  # L2: Search Ready / Coarse Policy
    if not has_chunk_level_policy_metadata:
        return 3  # L3: Resource Policy Ready
    return 4  # L4: Chunk Policy Ready


async def get_coverage_detail(
    session: AsyncSession,
    org_id: UUID,
    connector_id: UUID,
) -> CoverageDetail:
    """Get detailed coverage stats for a connector."""
    connector = await _load(session, org_id, connector_id)

    # Bound vector count
    bound_result = await session.execute(
        select(func.count()).select_from(ResourceChunk).where(
            ResourceChunk.source_connector_id == connector_id,
        )
    )
    bound_count = bound_result.scalar() or 0

    total_count = connector.record_count or 0

    if total_count > 0:
        coverage_pct = round(bound_count / total_count * 100, 2)
    else:
        coverage_pct = None

    # Classification breakdown
    breakdown_result = await session.execute(
        select(GatedResource.classification, func.count())
        .where(
            GatedResource.source_connector_id == connector_id,
            GatedResource.organization_id == org_id,
            GatedResource.deleted_at.is_(None),
        )
        .group_by(GatedResource.classification)
    )
    classification_breakdown = {}
    for row in breakdown_result.all():
        key = row[0].value if row[0] else "unclassified"
        classification_breakdown[key] = row[1]

    from gateco.database.enums import ConnectorStatus, PolicyStatus
    from gateco.database.models.policy import Policy

    connection_ready = connector.status == ConnectorStatus.connected
    search_ready = connector.search_config is not None

    # Determine resource-level bindings and active policies for L3/L4
    mode = getattr(connector, "metadata_resolution_mode", None) or "sidecar"
    search_config = connector.search_config or {}

    has_resource_level_bindings = False
    if mode == "sidecar" and bound_count > 0:
        has_resource_level_bindings = True
    elif mode == "sql_view" and search_config.get("metadata_view_name"):
        has_resource_level_bindings = True
    elif mode == "inline" and search_config.get("metadata_field_mapping"):
        has_resource_level_bindings = True
    elif mode == "auto":
        has_resource_level_bindings = (
            bound_count > 0
            or bool(search_config.get("metadata_view_name"))
            or bool(search_config.get("metadata_field_mapping"))
        )

    # Check for active policies
    policy_result = await session.execute(
        select(func.count()).select_from(Policy).where(
            Policy.organization_id == org_id,
            Policy.status == PolicyStatus.active,
            Policy.deleted_at.is_(None),
        )
    )
    has_active_policies = (policy_result.scalar() or 0) > 0

    # Chunk-level policy metadata: only for inline/sql_view modes
    has_chunk_level = mode in ("inline", "sql_view") and has_resource_level_bindings

    readiness = compute_policy_readiness(
        connection_ready,
        search_ready,
        coverage_pct,
        metadata_resolution_mode=mode,
        has_active_policies=has_active_policies,
        has_resource_level_bindings=has_resource_level_bindings,
        has_chunk_level_policy_metadata=has_chunk_level,
    )

    return CoverageDetail(
        bound_vector_count=bound_count,
        total_vector_count=total_count,
        coverage_pct=coverage_pct,
        coverage_approximate=True,
        policy_readiness_level=readiness,
        classification_breakdown=classification_breakdown,
    )
