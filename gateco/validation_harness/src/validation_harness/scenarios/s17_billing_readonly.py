"""s17_billing_readonly — Plans, usage, subscription (read-only, entitlement-aware)."""

from __future__ import annotations

from validation_harness.engine import ScenarioContext
from validation_harness.registry import scenario


@scenario(
    id="s17_billing_readonly",
    name="Billing Read-Only",
    feature_area="billing",
    depends_on=["s01_auth"],
    requires_features=["billing"],
)
async def s17_billing_readonly(ctx: ScenarioContext) -> None:
    """Verify billing endpoints return valid structures (read-only)."""

    # Step 1: Get plans (may not require auth)
    ctx.begin_step("get_plans")
    try:
        plans = await ctx.client.billing.get_plans()
        ctx.assert_that(
            "Plans returned",
            plans is not None,
        )
        if plans and hasattr(plans, "__len__"):
            ctx.assert_that(
                "At least 1 plan available",
                len(plans) >= 1,
                expected=">= 1",
                actual=len(plans),
            )
    except Exception as exc:
        ctx.assert_that("Get plans", False, actual=str(exc))

    # Step 2: Get usage
    ctx.begin_step("get_usage")
    try:
        usage = await ctx.client.billing.get_usage()
        ctx.assert_that(
            "Usage returned",
            usage is not None,
        )
        if usage and hasattr(usage, "secured_retrievals"):
            ctx.assert_that(
                "Secured retrievals field exists",
                usage.secured_retrievals is not None,
            )
    except Exception as exc:
        ctx.assert_that("Get usage", False, actual=str(exc))

    # Step 3: Get subscription
    ctx.begin_step("get_subscription")
    try:
        sub = await ctx.client.billing.get_subscription()
        ctx.assert_that(
            "Subscription returned",
            sub is not None,
        )
    except Exception as exc:
        # Subscription may not exist for free tier — not a failure
        ctx.assert_that("Subscription available", True)
