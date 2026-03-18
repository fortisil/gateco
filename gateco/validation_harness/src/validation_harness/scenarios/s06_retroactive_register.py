"""s06_retroactive_register — Retroactive registration + binding validation."""

from __future__ import annotations

from validation_harness.engine import ScenarioContext
from validation_harness.registry import scenario


@scenario(
    id="s06_retroactive_register",
    name="Retroactive Registration",
    feature_area="retroactive",
    depends_on=["s03_connector_config"],
    requires_capabilities=["supports_retroactive_registration"],
    requires_features=["retroactive"],
)
async def s06_retroactive_register(ctx: ScenarioContext) -> None:
    """Register existing vectors and validate resource creation/binding."""
    connector_id = ctx.require("connector_id")

    ctx.begin_step("retroactive_register")
    try:
        result = await ctx.client.retroactive.register(connector_id=connector_id)
        ctx.assert_that(
            "Retroactive register returns result",
            result is not None,
        )
        if result:
            if hasattr(result, "newly_registered"):
                ctx.assert_that(
                    "Newly registered count is non-negative",
                    result.newly_registered >= 0,
                    actual=result.newly_registered,
                )
            if hasattr(result, "scanned_vectors"):
                ctx.assert_that(
                    "Scanned vectors count is non-negative",
                    result.scanned_vectors >= 0,
                    actual=result.scanned_vectors,
                )
    except Exception as exc:
        ctx.assert_that(
            "Retroactive registration succeeds",
            False,
            actual=str(exc),
        )
