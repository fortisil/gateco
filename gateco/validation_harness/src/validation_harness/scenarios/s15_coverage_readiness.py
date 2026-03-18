"""s15_coverage_readiness — Fact-driven readiness progression verification."""

from __future__ import annotations

from validation_harness.capabilities import get_capabilities
from validation_harness.engine import ScenarioContext
from validation_harness.registry import scenario


@scenario(
    id="s15_coverage_readiness",
    name="Coverage & Readiness Assessment",
    feature_area="readiness",
    depends_on=["s02_connector_lifecycle"],
    requires_features=["connectors"],
)
async def s15_coverage_readiness(ctx: ScenarioContext) -> None:
    """Assess readiness level progression using upstream facts and connector state."""
    connector_id = ctx.get("connector_id")
    connector_type = ctx.config.connector.type
    caps = get_capabilities(connector_type)

    if not connector_id:
        ctx.begin_step("no_connector")
        ctx.assert_that("Connector available for readiness check", False)
        return

    # Step 1: Fetch connector state and read policy_readiness_level directly
    ctx.begin_step("fetch_connector_state")
    try:
        connector = await ctx.client.connectors.get(connector_id)
    except Exception as exc:
        ctx.assert_that("Fetch connector for readiness", False, actual=str(exc))
        return

    readiness_observed = connector.policy_readiness_level if connector.policy_readiness_level is not None else 0
    ctx.assert_that(
        "Readiness level fetched from connector",
        connector.policy_readiness_level is not None,
        expected="non-null policy_readiness_level",
        actual=readiness_observed,
    )

    # Step 2: Collect readiness facts from upstream scenarios + connector state
    ctx.begin_step("collect_readiness_facts")
    connector_test_passed = ctx.get("connector_test_passed", False)
    search_config_applied = ctx.get("search_config_applied", False)
    resources_ingested_count = ctx.get("resources_ingested_count", 0)
    policy_count_active = ctx.get("policy_count_active", 0)
    # Derive bindings from connector state, not from upstream flags
    bound_count = connector.bound_vector_count if connector.bound_vector_count is not None else 0
    resource_bindings_present = bound_count > 0

    ctx.assert_that(
        "Readiness facts collected",
        True,
        actual=(
            f"test={connector_test_passed}, search={search_config_applied}, "
            f"ingested={resources_ingested_count}, policies={policy_count_active}, "
            f"bindings={resource_bindings_present} (bound_vectors={bound_count})"
        ),
    )

    # Step 3: Derive expected bounds from facts
    ctx.begin_step("derive_expected_bounds")
    expected_minimum = 0
    gap_reasons: list[str] = []

    if connector_test_passed:
        expected_minimum = max(expected_minimum, 1)
    if search_config_applied:
        expected_minimum = max(expected_minimum, 2)
    if policy_count_active > 0 and resource_bindings_present:
        expected_minimum = max(expected_minimum, 3)
    if (
        caps
        and caps.supports_chunk_level_binding
        and connector.metadata_resolution_mode in ("inline", "sql_view")
        and resource_bindings_present
    ):
        expected_minimum = max(expected_minimum, 4)

    expected_maximum = caps.expected_max_readiness_level if caps else 4

    ctx.assert_that(
        f"Expected readiness bounds: min=L{expected_minimum}, max=L{expected_maximum}",
        True,
        expected=f"L{expected_minimum}-L{expected_maximum}",
        actual=f"L{readiness_observed}",
    )

    # Step 4: Compare observed vs expected
    ctx.begin_step("compare_observed_vs_expected")

    if readiness_observed < expected_minimum:
        gap_reasons.append(
            f"Observed L{readiness_observed} below expected minimum L{expected_minimum}"
        )
        ctx.assert_that(
            f"Readiness >= expected minimum L{expected_minimum}",
            False,
            expected=f">= L{expected_minimum}",
            actual=f"L{readiness_observed}",
        )
    else:
        ctx.assert_that(
            f"Readiness L{readiness_observed} meets minimum L{expected_minimum}",
            True,
            expected=f">= L{expected_minimum}",
            actual=f"L{readiness_observed}",
        )

    if expected_minimum <= readiness_observed < expected_maximum:
        gap_reasons.append(
            f"L{readiness_observed} is valid but below max L{expected_maximum} "
            f"(may require additional configuration)"
        )

    gap_reason = "; ".join(gap_reasons) if gap_reasons else None

    # Step 5: Emit results to shared state
    ctx.begin_step("emit_results")
    ctx.share("readiness_initial", readiness_observed)
    ctx.share("readiness_final", readiness_observed)
    ctx.share("readiness_expected_min", expected_minimum)
    ctx.share("readiness_gap_reason", gap_reason)

    ctx.assert_that(
        f"Readiness assessment complete: L{readiness_observed} "
        f"(min=L{expected_minimum}, max=L{expected_maximum})",
        True,
    )
