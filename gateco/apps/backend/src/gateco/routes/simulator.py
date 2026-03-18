"""Access Simulator route — dry-run policy evaluation."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.connection import get_session
from gateco.database.enums import PolicyStatus
from gateco.database.models.policy import Policy
from gateco.database.models.principal import Principal
from gateco.database.models.resource import GatedResource
from gateco.database.models.user import User
from gateco.exceptions import EntitlementError, NotFoundError
from gateco.middleware.entitlement import PLAN_FEATURES
from gateco.middleware.jwt_auth import get_current_user
from gateco.services.policy_engine import evaluate_policies

router = APIRouter(prefix="/api/simulator", tags=["simulator"])


class SimulationRequest(BaseModel):
    principal_id: str
    query: str | None = None
    connector_id: str | None = None
    resource_ids: list[str] | None = None


class SimulationResponse(BaseModel):
    outcome: str
    matched_resources: int
    allowed: int
    denied: int
    policy_trace: list[dict]
    denial_reasons: list[str]


@router.post(
    "/run",
    response_model=SimulationResponse,
)
async def run_simulation(
    body: SimulationRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Dry-run policy evaluation for a principal against resources."""
    plan = getattr(request.state, "plan", "free")
    features = PLAN_FEATURES.get(plan, PLAN_FEATURES["free"])
    if not features.get("access_simulator", False):
        raise EntitlementError(
            detail=f"Feature 'access_simulator' is not available on the {plan} plan",
            upgrade_to="pro" if plan == "free" else "enterprise",
        )

    org_id = user.organization_id

    # Load principal
    result = await session.execute(
        select(Principal).where(
            Principal.id == UUID(body.principal_id),
            Principal.organization_id == org_id,
        )
    )
    principal = result.scalar_one_or_none()
    if not principal:
        raise NotFoundError(detail="Principal not found")

    # Load resources
    if body.resource_ids:
        resource_uuids = [UUID(r) for r in body.resource_ids]
        result = await session.execute(
            select(GatedResource).where(
                GatedResource.id.in_(resource_uuids),
                GatedResource.organization_id == org_id,
                GatedResource.deleted_at.is_(None),
            )
        )
    else:
        query = select(GatedResource).where(
            GatedResource.organization_id == org_id,
            GatedResource.deleted_at.is_(None),
        )
        if body.connector_id:
            query = query.where(GatedResource.source_connector_id == UUID(body.connector_id))
        result = await session.execute(query.limit(50))

    resources = list(result.scalars().all())

    # Load active policies
    result = await session.execute(
        select(Policy)
        .options(selectinload(Policy.rules))
        .where(
            Policy.organization_id == org_id,
            Policy.status == PolicyStatus.active,
            Policy.deleted_at.is_(None),
        )
    )
    policies = list(result.scalars().all())

    # Evaluate
    eval_result = evaluate_policies(principal, resources, policies)

    return SimulationResponse(
        outcome=eval_result.outcome,
        matched_resources=len(resources),
        allowed=len(eval_result.allowed_resources),
        denied=len(eval_result.denied_resources),
        policy_trace=eval_result.policy_trace,
        denial_reasons=eval_result.denial_reasons,
    )
