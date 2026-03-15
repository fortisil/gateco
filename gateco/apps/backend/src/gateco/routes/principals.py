"""Principals routes — list + detail."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.connection import get_session
from gateco.database.models.identity_provider import IdentityProvider
from gateco.database.models.principal import Principal
from gateco.database.models.user import User
from gateco.exceptions import NotFoundError
from gateco.middleware.jwt_auth import get_current_user
from gateco.schemas.common import paginate_meta

router = APIRouter(prefix="/api/principals", tags=["principals"])


def _serialize(p: Principal, idp_names: dict | None = None) -> dict:
    return {
        "id": str(p.id),
        "identity_provider_id": str(p.identity_provider_id),
        "identity_provider_name": (
            idp_names.get(p.identity_provider_id, "") if idp_names else ""
        ),
        "external_id": p.external_id,
        "display_name": p.display_name,
        "email": p.email,
        "groups": p.groups,
        "roles": p.roles,
        "attributes": p.attributes,
        "status": p.status.value,
        "last_seen": p.last_seen.isoformat() if p.last_seen else None,
        "created_at": p.created_at.isoformat(),
    }


@router.get("")
async def list_principals(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    base = select(Principal).where(Principal.organization_id == user.organization_id)
    count_q = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_q)).scalar() or 0

    offset = (page - 1) * per_page
    result = await session.execute(
        base.order_by(Principal.display_name).offset(offset).limit(per_page)
    )
    principals = result.scalars().all()

    # Resolve IDP names
    idp_ids = {p.identity_provider_id for p in principals if p.identity_provider_id}
    idp_names = {}
    if idp_ids:
        idp_result = await session.execute(
            select(IdentityProvider.id, IdentityProvider.name)
            .where(IdentityProvider.id.in_(idp_ids))
        )
        idp_names = {row[0]: row[1] for row in idp_result.all()}

    data = [_serialize(p, idp_names) for p in principals]
    return {"data": data, "meta": paginate_meta(page, per_page, total)}


@router.get("/{principal_id}")
async def get_principal(
    principal_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Principal).where(
            Principal.id == principal_id,
            Principal.organization_id == user.organization_id,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise NotFoundError(detail="Principal not found")

    idp_names = {}
    if p.identity_provider_id:
        idp_result = await session.execute(
            select(IdentityProvider.id, IdentityProvider.name)
            .where(IdentityProvider.id == p.identity_provider_id)
        )
        row = idp_result.first()
        if row:
            idp_names[row[0]] = row[1]

    return _serialize(p, idp_names)
