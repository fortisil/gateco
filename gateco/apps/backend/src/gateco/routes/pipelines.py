"""Pipeline routes — CRUD + run."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.connection import get_session
from gateco.database.enums import AuditEventType
from gateco.database.models.user import User
from gateco.middleware.jwt_auth import get_current_user
from gateco.schemas.pipelines import CreatePipelineRequest, UpdatePipelineRequest
from gateco.services import audit_service, pipeline_service

router = APIRouter(prefix="/api/pipelines", tags=["pipelines"])


@router.get("")
async def list_pipelines(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await pipeline_service.list_pipelines(session, user.organization_id)
    return {"data": data}


@router.post("", status_code=201)
async def create_pipeline(
    body: CreatePipelineRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await pipeline_service.create_pipeline(
        session, user.organization_id, body.name,
        body.source_connector_id, body.envelope_config, body.schedule,
    )
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.pipeline_created,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Pipeline created: {body.name}",
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get("/{pipeline_id}")
async def get_pipeline(
    pipeline_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await pipeline_service.get_pipeline(session, user.organization_id, pipeline_id)


@router.patch("/{pipeline_id}")
async def update_pipeline(
    pipeline_id: UUID,
    body: UpdatePipelineRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await pipeline_service.update_pipeline(
        session, user.organization_id, pipeline_id, body.model_dump(exclude_unset=True),
    )
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.pipeline_updated,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Pipeline updated: {pipeline_id}",
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.post("/{pipeline_id}/run")
async def run_pipeline(
    pipeline_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await pipeline_service.run_pipeline(
        session, user.organization_id, pipeline_id,
        actor_id=user.id, actor_name=user.name,
    )
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.pipeline_run,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Pipeline run triggered: {pipeline_id}",
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get("/{pipeline_id}/runs")
async def list_runs(
    pipeline_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await pipeline_service.list_runs(session, user.organization_id, pipeline_id)
    return {"data": data}
