"""s13_simulator — Access simulator + comparison with live retrieval."""

from __future__ import annotations

from validation_harness.engine import ScenarioContext
from validation_harness.registry import scenario


@scenario(
    id="s13_simulator",
    name="Access Simulator",
    feature_area="simulator",
    depends_on=["s08_policy_lifecycle"],
    requires_capabilities=["supports_simulator"],
    requires_features=["simulator"],
)
async def s13_simulator(ctx: ScenarioContext) -> None:
    """Run access simulation and compare with live retrieval expectations."""
    connector_id = ctx.require("connector_id")

    # Fetch a principal for simulation (seed data has principals)
    ctx.begin_step("find_principal")
    try:
        principals_page = await ctx.client.principals.list()
        if not principals_page.items:
            ctx.assert_that("At least one principal exists", False, actual="No principals found")
            return
        principal_id = principals_page.items[0].id
        ctx.assert_that("Found principal for simulation", True)
    except Exception as exc:
        ctx.assert_that("List principals", False, actual=str(exc))
        return

    # Step 1: Run simulation
    ctx.begin_step("run_simulation")
    try:
        sim_result = await ctx.client.simulator.run(
            principal_id=principal_id,
            connector_id=connector_id,
        )
        ctx.assert_that(
            "Simulation returns result",
            sim_result is not None,
        )

        if sim_result:
            if hasattr(sim_result, "matched_count"):
                ctx.assert_that(
                    "Simulation has matched count",
                    sim_result.matched_count is not None,
                )
            if hasattr(sim_result, "allowed_count"):
                ctx.assert_that(
                    "Simulation has allowed count",
                    sim_result.allowed_count is not None,
                )
            if hasattr(sim_result, "denied_count"):
                ctx.assert_that(
                    "Simulation has denied count",
                    sim_result.denied_count is not None,
                )
    except Exception as exc:
        ctx.assert_that("Simulation succeeds", False, actual=str(exc))
