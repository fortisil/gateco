"""s10_retrieval_denied — Retrieval with denied results present."""

from __future__ import annotations

from validation_harness.engine import ScenarioContext
from validation_harness.registry import scenario


@scenario(
    id="s10_retrieval_denied",
    name="Retrieval Denied",
    feature_area="retrievals",
    depends_on=["s08_policy_lifecycle", "s05_ingest_batch", "s03_connector_config"],
    requires_features=["retrievals"],
    skip_when_dependency_skipped=["s05_ingest_batch"],
)
async def s10_retrieval_denied(ctx: ScenarioContext) -> None:
    """Execute retrieval and verify denied results are present (restricted docs)."""
    connector_id = ctx.require("connector_id")

    ctx.begin_step("find_principal")
    try:
        principals_page = await ctx.client.principals.list()
        if not principals_page.items:
            ctx.assert_that("At least one principal exists", False, actual="No principals")
            return
        principal_id = principals_page.items[0].id
    except Exception as exc:
        ctx.assert_that("List principals", False, actual=str(exc))
        return

    ctx.begin_step("retrieve_all_for_denied")
    # Use top_k large enough to include restricted docs
    dummy_vector = [0.1] * 1536
    try:
        result = await ctx.client.retrievals.execute(
            query_vector=dummy_vector,
            connector_id=connector_id,
            principal_id=principal_id,
            query="compensation data security audit restricted",
            top_k=50,
        )
    except Exception as exc:
        ctx.assert_that(
            "Retrieval execute succeeds",
            False,
            actual=str(exc),
        )
        return

    ctx.assert_that(
        "Retrieval returns result",
        result is not None,
    )

    if result:
        denied_count = getattr(result, "denied_chunks", 0)
        matched_chunks = getattr(result, "matched_chunks", 0)

        ctx.assert_that(
            "Retrieval found chunks",
            matched_chunks > 0,
            expected="> 0",
            actual=matched_chunks,
        )

        ctx.assert_that(
            "Some results denied (restricted docs)",
            denied_count > 0,
            expected="> 0",
            actual=denied_count,
        )

        outcome = getattr(result, "outcome", None)
        ctx.assert_that(
            "Outcome includes denied results",
            outcome in ("denied", "partial"),
            expected="denied or partial",
            actual=outcome,
        )
