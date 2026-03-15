"""Data Catalog routes — list, detail, update."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.connection import get_session
from gateco.database.enums import AuditEventType
from gateco.database.models.user import User
from gateco.middleware.jwt_auth import get_current_user
from gateco.schemas.data_catalog import UpdateResourceRequest
from gateco.services import audit_service, data_catalog_service

router = APIRouter(prefix="/api/data-catalog", tags=["data-catalog"])


@router.get("")
async def list_resources(
    classification: str | None = None,
    sensitivity: str | None = None,
    domain: str | None = None,
    label: str | None = None,
    source_connector_id: UUID | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await data_catalog_service.list_resources(
        session, user.organization_id,
        classification=classification,
        sensitivity=sensitivity,
        domain=domain,
        label=label,
        source_connector_id=source_connector_id,
        page=page, per_page=per_page,
    )


@router.get("/{resource_id}")
async def get_resource_detail(
    resource_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await data_catalog_service.get_resource_detail(
        session, user.organization_id, resource_id,
    )


@router.patch("/{resource_id}")
async def update_resource(
    resource_id: UUID,
    body: UpdateResourceRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await data_catalog_service.update_resource(
        session, user.organization_id, resource_id, body.model_dump(exclude_unset=True),
    )
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.resource_updated,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Resource updated: {resource_id}",
        ip_address=request.client.host if request.client else None,
        resource_ids=[resource_id],
    )
    return result
