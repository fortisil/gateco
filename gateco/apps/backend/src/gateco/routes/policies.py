"""Policy routes — CRUD + lifecycle (activate, archive)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.connection import get_session
from gateco.database.enums import AuditEventType
from gateco.database.models.user import User
from gateco.exceptions import EntitlementError
from gateco.middleware.entitlement import PLAN_FEATURES, check_resource_limit, require_feature
from gateco.middleware.jwt_auth import get_current_user
from gateco.schemas.policies import CreatePolicyRequest, UpdatePolicyRequest
from gateco.services import audit_service, policy_service

router = APIRouter(prefix="/api/policies", tags=["policies"])


@router.get("")
async def list_policies(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    data = await policy_service.list_policies(session, user.organization_id)
    return {"data": data}


@router.post("", status_code=201)
async def create_policy(
    body: CreatePolicyRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    plan = getattr(request.state, "plan", "free")
    # Feature gate — runs after get_current_user so request.state.plan is set
    features = PLAN_FEATURES.get(plan, PLAN_FEATURES["free"])
    if not features.get("policy_studio", False):
        raise EntitlementError(
            detail=f"Feature 'policy_studio' is not available on the {plan} plan",
            upgrade_to="pro" if plan == "free" else "enterprise",
        )
    await check_resource_limit("policies", session, user.organization_id, plan)
    result = await policy_service.create_policy(
        session, user.organization_id, body.model_dump(), created_by=user.id,
    )
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.policy_created,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Policy created: {body.name}",
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get("/{policy_id}")
async def get_policy(
    policy_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await policy_service.get_policy(session, user.organization_id, policy_id)


@router.patch("/{policy_id}")
async def update_policy(
    policy_id: UUID,
    body: UpdatePolicyRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Feature gate — runs after get_current_user so request.state.plan is set
    plan = getattr(request.state, "plan", "free")
    features = PLAN_FEATURES.get(plan, PLAN_FEATURES["free"])
    if not features.get("policy_studio", False):
        raise EntitlementError(
            detail=f"Feature 'policy_studio' is not available on the {plan} plan",
            upgrade_to="pro" if plan == "free" else "enterprise",
        )
    result = await policy_service.update_policy(
        session, user.organization_id, policy_id, body.model_dump(exclude_unset=True),
    )
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.policy_updated,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Policy updated: {policy_id}",
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await policy_service.delete_policy(session, user.organization_id, policy_id)
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.policy_deleted,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Policy deleted: {policy_id}",
        ip_address=request.client.host if request.client else None,
    )


@router.post("/{policy_id}/activate")
async def activate_policy(
    policy_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await policy_service.activate_policy(session, user.organization_id, policy_id)
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.policy_activated,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Policy activated: {policy_id}",
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.post("/{policy_id}/archive")
async def archive_policy(
    policy_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await policy_service.archive_policy(session, user.organization_id, policy_id)
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.policy_archived,
        actor_id=user.id,
        actor_name=user.name,
        details=f"Policy archived: {policy_id}",
        ip_address=request.client.host if request.client else None,
    )
    return result
