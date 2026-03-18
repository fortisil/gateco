"""Data catalog service: list, detail, update GatedResources with policy context."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.enums import Classification, EncryptionMode, PolicyStatus, Sensitivity
from gateco.database.models.connector import Connector
from gateco.database.models.policy import Policy
from gateco.database.models.resource import GatedResource
from gateco.database.models.resource_chunk import ResourceChunk
from gateco.exceptions import NotFoundError, ValidationError
from gateco.services.policy_engine import _resource_matches_selectors


def _serialize(r: GatedResource, connector_names: dict | None = None) -> dict:
    return {
        "id": str(r.id),
        "title": r.title,
        "description": r.description,
        "type": r.type.value,
        "classification": r.classification.value if r.classification else None,
        "sensitivity": r.sensitivity.value if r.sensitivity else None,
        "domain": r.domain,
        "labels": r.labels,
        "chunk_ids": [],
        "acl_refs": [],
        "policy_ids": [],
        "encryption_mode": r.encryption_mode.value if r.encryption_mode else None,
        "source_connector_id": str(r.source_connector_id) if r.source_connector_id else None,
        "source_connector_name": (
            connector_names.get(r.source_connector_id, "") if connector_names else ""
        ),
        "view_count": r.view_count,
        "created_at": r.created_at.isoformat(),
        "updated_at": r.updated_at.isoformat(),
    }


async def list_resources(
    session: AsyncSession, org_id: UUID,
    classification: str | None = None,
    sensitivity: str | None = None,
    domain: str | None = None,
    label: str | None = None,
    source_connector_id: UUID | None = None,
    page: int = 1, per_page: int = 20,
) -> dict:
    query = (
        select(GatedResource)
        .where(GatedResource.organization_id == org_id, GatedResource.deleted_at.is_(None))
    )
    if classification:
        query = query.where(GatedResource.classification == classification)
    if sensitivity:
        query = query.where(GatedResource.sensitivity == sensitivity)
    if domain:
        query = query.where(GatedResource.domain == domain)
    if label:
        query = query.where(GatedResource.labels.any(label))
    if source_connector_id:
        query = query.where(GatedResource.source_connector_id == source_connector_id)

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_q)).scalar() or 0

    # Paginate
    offset = (page - 1) * per_page
    result = await session.execute(
        query.order_by(GatedResource.created_at.desc()).offset(offset).limit(per_page)
    )
    resources = result.scalars().all()
    total_pages = max(1, (total + per_page - 1) // per_page)

    # Resolve connector names
    conn_ids = {r.source_connector_id for r in resources if r.source_connector_id}
    connector_names = {}
    if conn_ids:
        conn_result = await session.execute(
            select(Connector.id, Connector.name).where(Connector.id.in_(conn_ids))
        )
        connector_names = {row[0]: row[1] for row in conn_result.all()}

    return {
        "data": [_serialize(r, connector_names) for r in resources],
        "meta": {
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            }
        },
    }


async def get_resource_detail(session: AsyncSession, org_id: UUID, resource_id: UUID) -> dict:
    result = await session.execute(
        select(GatedResource).where(
            GatedResource.id == resource_id,
            GatedResource.organization_id == org_id,
            GatedResource.deleted_at.is_(None),
        )
    )
    r = result.scalar_one_or_none()
    if not r:
        raise NotFoundError(detail="Resource not found")

    # Chunks
    chunks_result = await session.execute(
        select(ResourceChunk)
        .where(ResourceChunk.resource_id == r.id)
        .order_by(ResourceChunk.index)
    )
    chunks = [
        {
            "id": str(c.id),
            "index": c.index,
            "preview": c.preview,
            "encrypted": c.encrypted,
            "vector_id": c.vector_id,
        }
        for c in chunks_result.scalars().all()
    ]

    # Applicable active policies
    policies_result = await session.execute(
        select(Policy).where(
            Policy.organization_id == org_id,
            Policy.status == PolicyStatus.active,
            Policy.deleted_at.is_(None),
        )
    )
    applicable = []
    for p in policies_result.scalars().all():
        if _resource_matches_selectors(r, p.resource_selectors):
            applicable.append({
                "id": str(p.id),
                "name": p.name,
                "type": p.type.value,
                "effect": p.effect.value,
            })

    # Resolve connector name
    connector_names = {}
    if r.source_connector_id:
        conn_result = await session.execute(
            select(Connector.id, Connector.name).where(Connector.id == r.source_connector_id)
        )
        row = conn_result.first()
        if row:
            connector_names[row[0]] = row[1]

    data = _serialize(r, connector_names)
    data["chunks"] = chunks
    data["chunk_ids"] = [c["id"] for c in chunks]
    data["policy_ids"] = [p["id"] for p in applicable]
    data["applicable_policies"] = applicable
    data["recent_access"] = []  # populated in M6
    return data


async def update_resource(
    session: AsyncSession, org_id: UUID, resource_id: UUID, data: dict,
) -> dict:
    result = await session.execute(
        select(GatedResource).where(
            GatedResource.id == resource_id,
            GatedResource.organization_id == org_id,
            GatedResource.deleted_at.is_(None),
        )
    )
    r = result.scalar_one_or_none()
    if not r:
        raise NotFoundError(detail="Resource not found")

    if "classification" in data and data["classification"] is not None:
        try:
            r.classification = Classification(data["classification"])
        except ValueError:
            raise ValidationError(detail=f"Invalid classification: {data['classification']}")
    if "sensitivity" in data and data["sensitivity"] is not None:
        try:
            r.sensitivity = Sensitivity(data["sensitivity"])
        except ValueError:
            raise ValidationError(detail=f"Invalid sensitivity: {data['sensitivity']}")
    if "domain" in data:
        r.domain = data["domain"]
    if "labels" in data:
        r.labels = data["labels"]
    if "encryption_mode" in data and data["encryption_mode"] is not None:
        try:
            r.encryption_mode = EncryptionMode(data["encryption_mode"])
        except ValueError:
            raise ValidationError(detail=f"Invalid encryption_mode: {data['encryption_mode']}")

    await session.flush()
    await session.refresh(r)
    return _serialize(r)
