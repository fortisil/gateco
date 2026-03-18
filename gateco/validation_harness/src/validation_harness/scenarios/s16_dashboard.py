"""s16_dashboard — Dashboard stats shape validation."""

from __future__ import annotations

from validation_harness.engine import ScenarioContext
from validation_harness.registry import scenario


@scenario(
    id="s16_dashboard",
    name="Dashboard Stats",
    feature_area="dashboard",
    depends_on=["s01_auth"],
    requires_features=["dashboard"],
)
async def s16_dashboard(ctx: ScenarioContext) -> None:
    """Verify dashboard stats endpoint returns valid structure."""
    ctx.begin_step("get_dashboard_stats")
    try:
        stats = await ctx.client.dashboard.get_stats()
        ctx.assert_that(
            "Dashboard stats returned",
            stats is not None,
        )

        # Lightweight shape validation
        if stats:
            for field in ["total_connectors", "total_resources", "total_retrievals"]:
                value = getattr(stats, field, None)
                if value is not None:
                    ctx.assert_that(
                        f"{field} is non-negative",
                        value >= 0,
                        actual=value,
                    )
    except Exception as exc:
        ctx.assert_that("Dashboard stats fetch", False, actual=str(exc))
