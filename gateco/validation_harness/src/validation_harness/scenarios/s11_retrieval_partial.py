"""s11_retrieval_partial — Retrieval with mixed outcomes."""

from __future__ import annotations

from validation_harness.engine import ScenarioContext
from validation_harness.registry import scenario


@scenario(
    id="s11_retrieval_partial",
    name="Retrieval Partial",
    feature_area="retrievals",
    depends_on=["s08_policy_lifecycle", "s05_ingest_batch", "s03_connector_config"],
    requires_features=["retrievals"],
    skip_when_dependency_skipped=["s05_ingest_batch"],
)
async def s11_retrieval_partial(ctx: ScenarioContext) -> None:
    """Execute broad retrieval expecting mixed allow/deny outcomes."""
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

    ctx.begin_step("retrieve_mixed")
    # Use top_k large enough to get all docs (public + restricted = mixed)
    dummy_vector = [0.1] * 1536
    try:
        result = await ctx.client.retrievals.execute(
            query_vector=dummy_vector,
            connector_id=connector_id,
            principal_id=principal_id,
            query="company overview compensation data engineering design security",
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
        outcome = getattr(result, "outcome", None)
        ctx.assert_that(
            "Outcome is partial (mixed allow/deny)",
            outcome == "partial",
            expected="partial",
            actual=outcome,
        )

        allowed_count = getattr(result, "allowed_chunks", 0)
        denied_count = getattr(result, "denied_chunks", 0)

        ctx.assert_that(
            "Has allowed results",
            allowed_count > 0,
            expected="> 0",
            actual=allowed_count,
        )
        ctx.assert_that(
            "Has denied results",
            denied_count > 0,
            expected="> 0",
            actual=denied_count,
        )

    # Step 2: Get retrieval detail
    ctx.begin_step("retrieval_detail")
    retrieval_id = ctx.get("retrieval_allowed_id")
    if retrieval_id:
        try:
            detail = await ctx.client.retrievals.get(retrieval_id)
            ctx.assert_that(
                "Retrieval detail returned",
                detail is not None,
            )
        except Exception as exc:
            ctx.assert_that(
                "Retrieval detail fetch",
                False,
                actual=str(exc),
            )
