"""Entitlement enforcement: feature gates and resource limits."""

from fastapi import Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.exceptions import EntitlementError
from gateco.services.stripe_service import PLANS

# Build lookup dicts from the static PLANS catalog
PLAN_FEATURES: dict[str, dict[str, bool]] = {p["id"]: p["features"] for p in PLANS}
PLAN_LIMITS: dict[str, dict[str, int | None]] = {p["id"]: p["limits"] for p in PLANS}


def require_feature(feature_name: str):
    """Dependency: returns 403 EntitlementError if org plan doesn't include feature."""

    async def _check(request: Request) -> None:
        plan = getattr(request.state, "plan", "free")
        features = PLAN_FEATURES.get(plan, PLAN_FEATURES["free"])
        if not features.get(feature_name, False):
            upgrade = "pro" if plan == "free" else "enterprise"
            raise EntitlementError(
                detail=f"Feature '{feature_name}' is not available on the {plan} plan",
                upgrade_to=upgrade,
            )

    return Depends(_check)


async def check_resource_limit(
    resource_type: str,
    session: AsyncSession,
    org_id,
    plan: str,
) -> None:
    """Raise EntitlementError if org exceeds plan limit for resource_type.

    resource_type is one of: connectors, identity_providers, policies
    """
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    limit = limits.get(resource_type)
    if limit is None:
        return  # unlimited

    # Dynamically pick the right model to count
    from gateco.database.models.connector import Connector
    from gateco.database.models.identity_provider import IdentityProvider
    from gateco.database.models.policy import Policy

    model_map = {
        "connectors": Connector,
        "identity_providers": IdentityProvider,
        "policies": Policy,
    }
    model = model_map.get(resource_type)
    if model is None:
        return

    query = select(func.count()).select_from(model).where(model.organization_id == org_id)
    # Exclude soft-deleted records from limit counts
    if hasattr(model, "deleted_at"):
        query = query.where(model.deleted_at.is_(None))
    result = await session.execute(query)
    count = result.scalar() or 0

    if count >= limit:
        upgrade = "pro" if plan == "free" else "enterprise"
        raise EntitlementError(
            detail=f"Plan limit reached: {count}/{limit} {resource_type}",
            upgrade_to=upgrade,
        )
