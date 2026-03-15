"""Usage tracking service for metered billing."""

import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.models.usage import UsageLog
from gateco.services.stripe_service import PLANS

PLAN_LIMITS = {p["id"]: p["limits"] for p in PLANS}


async def get_or_create_current_period(session: AsyncSession, org_id: UUID) -> UsageLog:
    """Get or create the UsageLog for the current billing period."""
    now = datetime.datetime.now(datetime.timezone.utc)
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = (period_start.month % 12) + 1
    next_year = period_start.year + (1 if next_month == 1 else 0)
    period_end = period_start.replace(year=next_year, month=next_month) - datetime.timedelta(
        microseconds=1
    )

    result = await session.execute(
        select(UsageLog).where(
            UsageLog.organization_id == org_id,
            UsageLog.period_start == period_start,
        )
    )
    usage = result.scalar_one_or_none()
    if usage:
        return usage

    usage = UsageLog(
        organization_id=org_id,
        period_start=period_start,
        period_end=period_end,
    )
    session.add(usage)
    await session.flush()
    return usage


async def increment_retrievals(session: AsyncSession, org_id: UUID, count: int = 1) -> None:
    """Increment the secured_retrievals counter for the current period."""
    usage = await get_or_create_current_period(session, org_id)
    usage.secured_retrievals = (usage.secured_retrievals or 0) + count
    await session.flush()


async def check_usage_limit(
    session: AsyncSession, org_id: UUID, plan: str,
) -> tuple[bool, int, int | None]:
    """Check if org is within retrieval limit. Returns (within_limit, used, limit)."""
    usage = await get_or_create_current_period(session, org_id)
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    limit = limits.get("secured_retrievals")
    used = usage.secured_retrievals or 0

    if limit is None:
        return True, used, None

    return used < limit, used, limit
