"""Connector routes — CRUD + test + binding + classification suggestions."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.connection import get_session
from gateco.database.enums import AuditEventType
from gateco.database.models.user import User
from gateco.middleware.entitlement import check_resource_limit
from gateco.middleware.jwt_auth import get_current_user
from gateco.schemas.bindings import BindRequest
from gateco.schemas.connectors import (
    CreateConnectorRequest,
    UpdateConnectorRequest,
    UpdateIngestionConfigRequest,
    UpdateSearchConfigRequest,
)
from gateco.schemas.suggestions import (
    ApplySuggestionsRequest,
    SuggestClassificationsRequest,
)
from gateco.services import audit_service, binding_service, connector_service
from gateco.services import classification_suggestion_service

router = APIRouter(prefix="/api/connectors", tags=["connectors"])


@router.get("")
async def list_connectors(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await connector_service.list_connectors(session, user.organization_id)
    return {"data": data}


@router.post("", status_code=201)
async def create_connector(
    body: CreateConnectorRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    plan = getattr(request.state, "plan", "free")
    await check_resource_limit("connectors", session, user.organization_id, plan)
    result = await connector_service.create_connector(
        session, user.organization_id, body.name, body.type, body.config,
        metadata_resolution_mode=body.metadata_resolution_mode,
    )
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.connector_added,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Connector created: {body.name}",
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get("/{connector_id}")
async def get_connector(
    connector_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await connector_service.get_connector(session, user.organization_id, connector_id)


@router.patch("/{connector_id}")
async def update_connector(
    connector_id: UUID,
    body: UpdateConnectorRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await connector_service.update_connector(
        session, user.organization_id, connector_id, body.name, body.config,
        metadata_resolution_mode=body.metadata_resolution_mode,
    )
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.connector_updated,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Connector updated: {connector_id}",
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.delete("/{connector_id}", status_code=204)
async def delete_connector(
    connector_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await connector_service.delete_connector(session, user.organization_id, connector_id)
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.connector_removed,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Connector removed: {connector_id}",
        ip_address=request.client.host if request.client else None,
    )


@router.get("/{connector_id}/search-config")
async def get_search_config(
    connector_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await connector_service.get_search_config(session, user.organization_id, connector_id)


@router.patch("/{connector_id}/search-config")
async def update_search_config(
    connector_id: UUID,
    body: UpdateSearchConfigRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await connector_service.update_search_config(
        session, user.organization_id, connector_id, body.search_config
    )
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.connector_updated,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Search config updated: {connector_id}",
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.post("/{connector_id}/test")
async def test_connector(
    connector_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await connector_service.test_connector(session, user.organization_id, connector_id)
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.connector_tested,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Connector tested: {connector_id} (success={result['success']})",
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.post("/{connector_id}/bind")
async def bind_metadata(
    connector_id: UUID,
    body: BindRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await binding_service.bind_metadata(
        session, user.organization_id, connector_id, body.bindings
    )
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.metadata_bound,
        actor_id=user.id,
        actor_name=user.name,
        details=(
            f"Metadata bound to connector {connector_id}: "
            f"{result.created_resources} resources created, "
            f"{result.created_chunks} chunks created, "
            f"{result.rebound_chunks} rebound, "
            f"{len(result.errors)} errors"
        ),
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get("/{connector_id}/ingestion-config")
async def get_ingestion_config(
    connector_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await connector_service.get_ingestion_config(session, user.organization_id, connector_id)


@router.patch("/{connector_id}/ingestion-config")
async def update_ingestion_config(
    connector_id: UUID,
    body: UpdateIngestionConfigRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await connector_service.update_ingestion_config(
        session, user.organization_id, connector_id, body.ingestion_config
    )
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.connector_updated,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Ingestion config updated: {connector_id}",
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get("/{connector_id}/coverage")
async def get_coverage(
    connector_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await binding_service.get_coverage_detail(
        session, user.organization_id, connector_id
    )


@router.post("/{connector_id}/suggest-classifications")
async def suggest_classifications(
    connector_id: UUID,
    body: SuggestClassificationsRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await classification_suggestion_service.suggest_classifications(
        session, user.organization_id, connector_id, body
    )
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.connector_updated,
        actor_id=user.id,
        actor_name=user.name,
        details=(
            f"Classification suggestions generated for connector {connector_id}: "
            f"{len(result.suggestions)} suggestions"
        ),
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.post("/{connector_id}/apply-suggestions")
async def apply_suggestions(
    connector_id: UUID,
    body: ApplySuggestionsRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await classification_suggestion_service.apply_suggestions(
        session, user.organization_id, connector_id, body
    )
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.metadata_bound,
        actor_id=user.id,
        actor_name=user.name,
        details=(
            f"Classification suggestions applied to connector {connector_id}: "
            f"{result.applied} applied, {result.resources_created} resources created"
        ),
        ip_address=request.client.host if request.client else None,
    )
    return result
