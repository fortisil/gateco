"""Access Simulator route — dry-run policy evaluation."""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.connection import get_session
from gateco.database.enums import PolicyStatus
from gateco.database.models.policy import Policy
from gateco.database.models.principal import Principal
from gateco.database.models.resource import GatedResource
from gateco.database.models.user import User
from gateco.exceptions import NotFoundError
from gateco.middleware.entitlement import require_feature
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
    dependencies=[require_feature("access_simulator")],
)
async def run_simulation(
    body: SimulationRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Dry-run policy evaluation for a principal against resources."""
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
        select(Policy).where(
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
