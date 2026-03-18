"""Audit log routes — list + export."""

import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.connection import get_session
from gateco.database.models.audit_event import AuditEvent
from gateco.database.models.user import User
from gateco.exceptions import EntitlementError
from gateco.middleware.entitlement import PLAN_FEATURES
from gateco.middleware.jwt_auth import get_current_user
from gateco.schemas.common import paginate_meta

router = APIRouter(prefix="/api/audit-log", tags=["audit"])


@router.get("")
async def list_audit_events(
    event_types: str | None = None,  # comma-separated
    actor: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    query = select(AuditEvent).where(AuditEvent.organization_id == user.organization_id)

    if event_types:
        types = [t.strip() for t in event_types.split(",")]
        query = query.where(AuditEvent.event_type.in_(types))
    if actor:
        query = query.where(AuditEvent.actor_name.ilike(f"%{actor}%"))
    if date_from:
        query = query.where(AuditEvent.timestamp >= date_from)
    if date_to:
        query = query.where(AuditEvent.timestamp <= date_to)

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_q)).scalar() or 0

    # Paginate
    offset = (page - 1) * per_page
    result = await session.execute(
        query.order_by(AuditEvent.timestamp.desc()).offset(offset).limit(per_page)
    )
    events = result.scalars().all()

    data = [
        {
            "id": str(e.id),
            "event_type": e.event_type.value,
            "actor_id": str(e.actor_id) if e.actor_id else None,
            "actor_name": e.actor_name,
            "principal_id": None,
            "details": e.details,
            "ip_address": e.ip_address,
            "timestamp": e.timestamp.isoformat(),
            "resource_ids": [str(r) for r in e.resource_ids] if e.resource_ids else [],
        }
        for e in events
    ]

    return {"data": data, "meta": paginate_meta(page, per_page, total)}


@router.post("/export")
async def export_audit_log(
    request: Request,
    event_types: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    format: str = Query(default="json", regex="^(json|csv)$"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Export audit log as JSON or CSV (requires audit_export feature)."""
    plan = getattr(request.state, "plan", "free")
    features = PLAN_FEATURES.get(plan, PLAN_FEATURES["free"])
    if not features.get("audit_export", False):
        raise EntitlementError(
            detail=f"Feature 'audit_export' is not available on the {plan} plan",
            upgrade_to="pro" if plan == "free" else "enterprise",
        )

    query = select(AuditEvent).where(AuditEvent.organization_id == user.organization_id)

    if event_types:
        types = [t.strip() for t in event_types.split(",")]
        query = query.where(AuditEvent.event_type.in_(types))
    if date_from:
        query = query.where(AuditEvent.timestamp >= date_from)
    if date_to:
        query = query.where(AuditEvent.timestamp <= date_to)

    result = await session.execute(query.order_by(AuditEvent.timestamp.desc()))
    events = result.scalars().all()

    today = datetime.utcnow().strftime("%Y-%m-%d")

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "event_type", "actor_name", "details", "ip_address", "timestamp"])
        for e in events:
            writer.writerow([
                str(e.id), e.event_type.value, e.actor_name,
                e.details, e.ip_address, e.timestamp.isoformat(),
            ])
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=gateco-audit-log-{today}.csv"},
        )

    # JSON
    data = [
        {
            "id": str(e.id),
            "event_type": e.event_type.value,
            "actor_name": e.actor_name,
            "details": e.details,
            "ip_address": e.ip_address,
            "timestamp": e.timestamp.isoformat(),
        }
        for e in events
    ]
    content = json.dumps(data, indent=2)
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=gateco-audit-log-{today}.json"},
    )
