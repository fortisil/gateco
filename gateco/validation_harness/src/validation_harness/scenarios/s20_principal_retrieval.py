"""s20_principal_retrieval — Verify retrieval outcomes differ by principal identity.

NOTE: These scenarios validate Gateco's principal-aware enforcement using the
backend's stub sync. They do NOT validate real SCIM/OIDC/SAML provider integrations.
"""

from __future__ import annotations

from validation_harness.engine import ScenarioContext
from validation_harness.registry import scenario


@scenario(
    id="s20_principal_retrieval",
    name="Principal-Based Retrieval Enforcement",
    feature_area="retrievals",
    depends_on=["s19_principal_policies", "s05_ingest_batch"],
    requires_features=["retrievals"],
    skip_when_dependency_skipped=["s05_ingest_batch", "s18_idp_lifecycle"],
)
async def s20_principal_retrieval(ctx: ScenarioContext) -> None:
    """Execute retrievals with different principals; verify identity-based outcomes differ."""
    connector_id = ctx.require("connector_id")
    engineering_principal_id = ctx.require("engineering_principal_id")
    marketing_principal_id = ctx.require("marketing_principal_id")

    dummy_vector = [0.1] * 1536
    query_text = "company overview internal engineering restricted confidential"

    # Step 1: Retrieve as engineering principal
    ctx.begin_step("retrieve_as_engineering")
    eng_allowed = 0
    eng_denied = 0
    eng_results = []
    try:
        eng_result = await ctx.client.retrievals.execute(
            query_vector=dummy_vector,
            query=query_text,
            principal_id=engineering_principal_id,
            connector_id=connector_id,
            top_k=50,
        )
        ctx.assert_that("Engineering retrieval returned result", eng_result is not None)

        eng_matched = getattr(eng_result, "matched_chunks", 0)
        eng_allowed = getattr(eng_result, "allowed_chunks", 0)
        eng_denied = getattr(eng_result, "denied_chunks", 0)
        eng_outcome = getattr(eng_result, "outcome", "unknown")
        eng_results = getattr(eng_result, "results", [])

        ctx.assert_that(
            "Engineering principal matched chunks",
            eng_matched > 0,
            expected=">0",
            actual=eng_matched,
        )
        ctx.assert_that(
            "Engineering principal has allowed chunks",
            eng_allowed > 0,
            expected=">0",
            actual=eng_allowed,
        )
        ctx.assert_that(
            "Engineering retrieval outcome",
            eng_outcome in ("allowed", "partial"),
            expected="allowed or partial",
            actual=eng_outcome,
        )
    except Exception as exc:
        ctx.assert_that("Retrieve as engineering principal", False, actual=str(exc))
        return

    # Step 2: Retrieve as marketing principal
    ctx.begin_step("retrieve_as_marketing")
    mkt_allowed = 0
    mkt_denied = 0
    mkt_results = []
    try:
        mkt_result = await ctx.client.retrievals.execute(
            query_vector=dummy_vector,
            query=query_text,
            principal_id=marketing_principal_id,
            connector_id=connector_id,
            top_k=50,
        )
        ctx.assert_that("Marketing retrieval returned result", mkt_result is not None)

        mkt_matched = getattr(mkt_result, "matched_chunks", 0)
        mkt_allowed = getattr(mkt_result, "allowed_chunks", 0)
        mkt_denied = getattr(mkt_result, "denied_chunks", 0)
        mkt_outcome = getattr(mkt_result, "outcome", "unknown")
        mkt_results = getattr(mkt_result, "results", [])

        ctx.assert_that(
            "Marketing principal matched chunks",
            mkt_matched > 0,
            expected=">0",
            actual=mkt_matched,
        )
        ctx.assert_that(
            "Marketing principal has denied chunks",
            mkt_denied > 0,
            expected=">0",
            actual=mkt_denied,
        )
        ctx.assert_that(
            "Marketing retrieval outcome includes denials",
            mkt_outcome in ("denied", "partial"),
            expected="denied or partial",
            actual=mkt_outcome,
        )
    except Exception as exc:
        ctx.assert_that("Retrieve as marketing principal", False, actual=str(exc))
        return

    # Step 3: Compare outcomes — the core identity-variance assertion
    ctx.begin_step("compare_principal_outcomes")
    ctx.assert_that(
        "Marketing principal denied >= engineering principal",
        mkt_denied >= eng_denied,
        expected=f"marketing_denied ({mkt_denied}) >= engineering_denied ({eng_denied})",
        actual=f"marketing_denied={mkt_denied}, engineering_denied={eng_denied}",
    )
    ctx.assert_that(
        "Outcomes differ between principals (identity-variance proof)",
        (eng_allowed != mkt_allowed) or (eng_denied != mkt_denied),
        expected="Different allowed or denied counts between principals",
        actual=f"eng(allowed={eng_allowed}, denied={eng_denied}), mkt(allowed={mkt_allowed}, denied={mkt_denied})",
    )

    # Step 4: Trace-level evidence
    ctx.begin_step("verify_denial_trace")
    if mkt_results:
        denied_results = [
            r for r in mkt_results
            if isinstance(r, dict) and r.get("policy_decision") == "denied"
        ]
        has_denial_reason = any(
            r.get("denial_reason") for r in denied_results
        )
        ctx.assert_that(
            "At least one marketing denial has a denial_reason trace",
            has_denial_reason or len(denied_results) == 0,
            expected="denial_reason present on denied results",
            actual=f"{len(denied_results)} denied results, has_reason={has_denial_reason}",
        )
    else:
        mkt_outcomes = getattr(mkt_result, "outcomes", [])
        denied_outcomes = [o for o in mkt_outcomes if not getattr(o, "granted", True)]
        has_reason = any(getattr(o, "denial_reason", None) for o in denied_outcomes)
        ctx.assert_that(
            "Marketing denial outcomes have trace data",
            has_reason or len(denied_outcomes) == 0,
            expected="denial_reason on denied outcomes",
            actual=f"{len(denied_outcomes)} denied, has_reason={has_reason}",
        )
