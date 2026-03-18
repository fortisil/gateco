"""s09_retrieval_allowed — Retrieval with outcome=allowed."""

from __future__ import annotations

from validation_harness.engine import ScenarioContext
from validation_harness.registry import scenario


@scenario(
    id="s09_retrieval_allowed",
    name="Retrieval Allowed",
    feature_area="retrievals",
    depends_on=["s08_policy_lifecycle", "s05_ingest_batch", "s03_connector_config"],
    requires_features=["retrievals"],
    skip_when_dependency_skipped=["s05_ingest_batch"],
)
async def s09_retrieval_allowed(ctx: ScenarioContext) -> None:
    """Execute retrieval and verify allowed results are present."""
    connector_id = ctx.require("connector_id")

    # Need a real principal (from IDP sync), not a user
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

    ctx.begin_step("retrieve_all")
    # Use top_k large enough to get all vectors, ensuring we hit public docs
    dummy_vector = [0.1] * 1536
    try:
        result = await ctx.client.retrievals.execute(
            query_vector=dummy_vector,
            connector_id=connector_id,
            principal_id=principal_id,
            query="company overview product FAQ",
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
        allowed_count = getattr(result, "allowed_chunks", 0)
        matched_chunks = getattr(result, "matched_chunks", 0)

        ctx.assert_that(
            "Retrieval found chunks",
            matched_chunks > 0,
            expected="> 0",
            actual=matched_chunks,
        )

        ctx.assert_that(
            "Some results allowed (public/internal docs)",
            allowed_count > 0,
            expected="> 0",
            actual=allowed_count,
        )

        outcome = getattr(result, "outcome", None)
        ctx.assert_that(
            "Outcome includes allowed results",
            outcome in ("allowed", "partial"),
            expected="allowed or partial",
            actual=outcome,
        )

        retrieval_id = getattr(result, "retrieval_id", None) or getattr(result, "id", None)
        ctx.share("retrieval_allowed_id", str(retrieval_id or ""))
