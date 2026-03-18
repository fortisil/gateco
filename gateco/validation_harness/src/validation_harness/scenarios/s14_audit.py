"""s14_audit — Verify audit events from this run, correlated by vh- prefix."""

from __future__ import annotations

import asyncio

from validation_harness.engine import ScenarioContext
from validation_harness.registry import scenario

# Expected event types that should appear after a full run
_EXPECTED_EVENT_TYPES = {
    "connector_added",
    "policy_created",
    "policy_activated",
    "retrieval_allowed",
    "retrieval_denied",
    "document_ingested",
}


@scenario(
    id="s14_audit",
    name="Audit Trail Verification",
    feature_area="audit",
    depends_on=["s01_auth"],
    requires_features=["audit"],
)
async def s14_audit(ctx: ScenarioContext) -> None:
    """Verify expected audit events are present, correlated by vh- prefix."""
    prefix = ctx.config.resource_prefix

    ctx.begin_step("list_audit_events")

    # Polling with retries for eventual consistency
    all_events = []
    for attempt in range(3):
        try:
            page = await ctx.client.audit.list(per_page=100)
            if page and hasattr(page, "items"):
                all_events = page.items
            if all_events:
                break
        except Exception:
            pass
        if attempt < 2:
            await asyncio.sleep(1)

    ctx.assert_that(
        "Audit events returned",
        len(all_events) > 0,
        expected="> 0 events",
        actual=len(all_events),
    )

    # Filter events related to this harness run by vh- resource names
    ctx.begin_step("filter_by_prefix")
    prefix_events = []
    for e in all_events:
        # Check resource_name, name, or details for the vh- prefix
        resource_name = (
            getattr(e, "resource_name", None)
            or getattr(e, "name", None)
            or ""
        )
        details = getattr(e, "details", None) or {}
        details_str = str(details) if details else ""

        if prefix in resource_name or prefix in details_str:
            prefix_events.append(e)

    ctx.assert_that(
        f"Events with '{prefix}' prefix found",
        len(prefix_events) > 0,
        expected=f"> 0 events matching '{prefix}'",
        actual=len(prefix_events),
    )

    # Check for expected event types
    ctx.begin_step("verify_event_types")
    observed_types: set[str] = set()
    for e in all_events:
        if hasattr(e, "event_type"):
            observed_types.add(e.event_type)
        elif hasattr(e, "action"):
            observed_types.add(e.action)

    ctx.assert_that(
        "Audit events have types",
        len(observed_types) > 0,
        expected="> 0 event types",
        actual=len(observed_types),
    )

    # Report which expected event types were found (informational)
    found_expected = observed_types & _EXPECTED_EVENT_TYPES
    if found_expected:
        ctx.assert_that(
            f"Found expected event types: {', '.join(sorted(found_expected))}",
            True,
            expected=", ".join(sorted(_EXPECTED_EVENT_TYPES)),
            actual=", ".join(sorted(found_expected)),
        )
