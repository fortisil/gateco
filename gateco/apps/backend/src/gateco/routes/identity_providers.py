"""Identity Provider routes — CRUD + sync."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.connection import get_session
from gateco.database.enums import AuditEventType
from gateco.database.models.user import User
from gateco.middleware.entitlement import check_resource_limit
from gateco.middleware.jwt_auth import get_current_user
from gateco.schemas.identity_providers import (
    CreateIdentityProviderRequest,
    UpdateIdentityProviderRequest,
)
from gateco.services import audit_service, identity_provider_service

router = APIRouter(prefix="/api/identity-providers", tags=["identity-providers"])


@router.get("")
async def list_identity_providers(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await identity_provider_service.list_identity_providers(session, user.organization_id)
    return {"data": data}


@router.post("", status_code=201)
async def create_identity_provider(
    body: CreateIdentityProviderRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    plan = getattr(request.state, "plan", "free")
    await check_resource_limit("identity_providers", session, user.organization_id, plan)
    result = await identity_provider_service.create_identity_provider(
        session, user.organization_id, body.name, body.type, body.config, body.sync_config
    )
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.idp_added,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Identity provider created: {body.name}",
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get("/{idp_id}")
async def get_identity_provider(
    idp_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await identity_provider_service.get_identity_provider(
        session, user.organization_id, idp_id
    )


@router.patch("/{idp_id}")
async def update_identity_provider(
    idp_id: UUID,
    body: UpdateIdentityProviderRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await identity_provider_service.update_identity_provider(
        session, user.organization_id, idp_id, body.name, body.config, body.sync_config
    )
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.idp_updated,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Identity provider updated: {idp_id}",
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.delete("/{idp_id}", status_code=204)
async def delete_identity_provider(
    idp_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await identity_provider_service.delete_identity_provider(
        session, user.organization_id, idp_id
    )
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.idp_removed,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Identity provider removed: {idp_id}",
        ip_address=request.client.host if request.client else None,
    )


@router.post("/{idp_id}/sync")
async def sync_identity_provider(
    idp_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.idp_sync_started,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Identity provider sync started: {idp_id}",
        ip_address=request.client.host if request.client else None,
    )
    return await identity_provider_service.trigger_sync(
        session, user.organization_id, idp_id,
        actor_id=user.id, actor_name=user.name,
    )
