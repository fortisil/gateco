"""Dashboard route — aggregated stats with real retrieval data."""

import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.connection import get_session
from gateco.database.enums import ConnectorStatus, IdentityProviderStatus, RetrievalOutcome
from gateco.database.models.connector import Connector
from gateco.database.models.identity_provider import IdentityProvider
from gateco.database.models.resource_chunk import ResourceChunk
from gateco.database.models.secured_retrieval import SecuredRetrieval
from gateco.database.models.user import User
from gateco.middleware.jwt_auth import get_current_user
from gateco.services.binding_service import compute_policy_readiness

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class DashboardStats(BaseModel):
    retrievals_today: int = 0
    retrievals_allowed: int = 0
    retrievals_denied: int = 0
    connectors_connected: int = 0
    connectors_error: int = 0
    idps_connected: int = 0
    idps_principal_count: int = 0
    last_idp_sync: str | None = None
    recent_denied: list[dict] = []
    total_bound_vectors: int = 0
    total_vectors: int = 0
    overall_coverage_pct: float | None = None
    connectors_policy_ready: int = 0


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Aggregate dashboard stats with real data from all milestones."""
    org_id = user.organization_id

    # Connector counts
    conn_q = await session.execute(
        select(Connector.status, func.count())
        .where(Connector.organization_id == org_id, Connector.deleted_at.is_(None))
        .group_by(Connector.status)
    )
    conn_counts = {row[0]: row[1] for row in conn_q.all()}

    # IDP counts
    idp_q = await session.execute(
        select(
            func.count().filter(IdentityProvider.status == IdentityProviderStatus.connected),
            func.coalesce(func.sum(IdentityProvider.principal_count), 0),
            func.max(IdentityProvider.last_sync),
        )
        .where(IdentityProvider.organization_id == org_id, IdentityProvider.deleted_at.is_(None))
    )
    idp_row = idp_q.one()

    # Retrieval counts (today)
    today_start = datetime.datetime.now(datetime.timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    retrieval_q = await session.execute(
        select(SecuredRetrieval.outcome, func.count())
        .where(
            SecuredRetrieval.organization_id == org_id,
            SecuredRetrieval.timestamp >= today_start,
        )
        .group_by(SecuredRetrieval.outcome)
    )
    retrieval_counts = {row[0]: row[1] for row in retrieval_q.all()}

    retrievals_allowed = retrieval_counts.get(RetrievalOutcome.allowed, 0) + retrieval_counts.get(
        RetrievalOutcome.partial, 0
    )
    retrievals_denied = retrieval_counts.get(RetrievalOutcome.denied, 0)

    # Recent denied retrievals
    denied_q = await session.execute(
        select(SecuredRetrieval)
        .where(
            SecuredRetrieval.organization_id == org_id,
            SecuredRetrieval.outcome == RetrievalOutcome.denied,
        )
        .order_by(SecuredRetrieval.timestamp.desc())
        .limit(5)
    )
    recent_denied = [
        {
            "id": str(r.id),
            "query": r.query[:100] if r.query else "",
            "principal_name": r.principal_name,
            "denial_reason": f"{r.denied_chunks} chunk(s) denied by policy",
            "timestamp": r.timestamp.isoformat(),
        }
        for r in denied_q.scalars().all()
    ]

    # Coverage stats across all connectors
    from gateco.schemas.connectors import SEARCH_CONFIG_REQUIRED_FIELDS

    all_connectors_result = await session.execute(
        select(Connector)
        .where(Connector.organization_id == org_id, Connector.deleted_at.is_(None))
    )
    all_connectors = list(all_connectors_result.scalars().all())

    # Total vectors = sum of record_count for connected connectors
    total_vectors = sum(
        c.record_count or 0
        for c in all_connectors
        if c.status == ConnectorStatus.connected
    )

    # Total bound vectors
    bound_q = await session.execute(
        select(func.count()).select_from(ResourceChunk).where(
            ResourceChunk.source_connector_id.in_([c.id for c in all_connectors])
        )
    ) if all_connectors else None
    total_bound_vectors = (bound_q.scalar() or 0) if bound_q else 0

    overall_coverage_pct = (
        round(total_bound_vectors / total_vectors * 100, 2)
        if total_vectors > 0
        else None
    )

    # Count connectors at L3
    # Per-connector bound counts for readiness
    if all_connectors:
        per_conn_bound = await session.execute(
            select(ResourceChunk.source_connector_id, func.count())
            .where(ResourceChunk.source_connector_id.in_([c.id for c in all_connectors]))
            .group_by(ResourceChunk.source_connector_id)
        )
        bound_map = {row[0]: row[1] for row in per_conn_bound.all()}
    else:
        bound_map = {}

    connectors_policy_ready = 0
    for c in all_connectors:
        conn_ready = c.status == ConnectorStatus.connected
        search_cfg = c.search_config
        required = SEARCH_CONFIG_REQUIRED_FIELDS.get(c.type.value, [])
        s_ready = search_cfg is not None and all(search_cfg.get(f) for f in required)
        bc = bound_map.get(c.id, 0)
        rc = c.record_count or 0
        cov = round(bc / rc * 100, 2) if rc > 0 and bc > 0 else None
        if compute_policy_readiness(conn_ready, s_ready, cov) == 3:
            connectors_policy_ready += 1

    return DashboardStats(
        retrievals_today=retrievals_allowed + retrievals_denied,
        retrievals_allowed=retrievals_allowed,
        retrievals_denied=retrievals_denied,
        connectors_connected=conn_counts.get(ConnectorStatus.connected, 0),
        connectors_error=conn_counts.get(ConnectorStatus.error, 0),
        idps_connected=idp_row[0] or 0,
        idps_principal_count=idp_row[1] or 0,
        last_idp_sync=idp_row[2].isoformat() if idp_row[2] else None,
        recent_denied=recent_denied,
        total_bound_vectors=total_bound_vectors,
        total_vectors=total_vectors,
        overall_coverage_pct=overall_coverage_pct,
        connectors_policy_ready=connectors_policy_ready,
    )
