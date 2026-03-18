"""s12_metadata_resolution — Metadata resolution behavior validation."""

from __future__ import annotations

from validation_harness.capabilities import get_capabilities
from validation_harness.engine import ScenarioContext
from validation_harness.registry import scenario


@scenario(
    id="s12_metadata_resolution",
    name="Metadata Resolution",
    feature_area="metadata_resolution",
    depends_on=["s08_policy_lifecycle"],
    requires_features=["metadata_resolution"],
)
async def s12_metadata_resolution(ctx: ScenarioContext) -> None:
    """Validate metadata resolution modes (sidecar, inline, sql_view, auto)."""
    connector_id = ctx.require("connector_id")
    connector_type = ctx.config.connector.type
    caps = get_capabilities(connector_type)

    # Step 1: Sidecar mode (always supported)
    ctx.begin_step("sidecar_mode")
    try:
        await ctx.client.connectors.update(
            connector_id, metadata_resolution_mode="sidecar"
        )
        fetched = await ctx.client.connectors.get(connector_id)
        ctx.assert_that(
            "Sidecar mode accepted",
            getattr(fetched, "metadata_resolution_mode", None) == "sidecar",
            expected="sidecar",
            actual=getattr(fetched, "metadata_resolution_mode", None),
        )
    except Exception as exc:
        ctx.assert_that("Sidecar mode set", False, actual=str(exc))

    # Step 2: Inline mode (cap-gated)
    if caps and caps.supports_metadata_resolution_inline:
        ctx.begin_step("inline_mode")
        try:
            await ctx.client.connectors.update(
                connector_id, metadata_resolution_mode="inline"
            )
            fetched = await ctx.client.connectors.get(connector_id)
            ctx.assert_that(
                "Inline mode accepted",
                getattr(fetched, "metadata_resolution_mode", None) == "inline",
                expected="inline",
                actual=getattr(fetched, "metadata_resolution_mode", None),
            )
        except Exception as exc:
            ctx.assert_that("Inline mode set", False, actual=str(exc))

    # Step 3: SQL view mode (Postgres family only)
    if caps and caps.supports_metadata_resolution_sql_view:
        ctx.begin_step("sql_view_mode")
        try:
            await ctx.client.connectors.update(
                connector_id, metadata_resolution_mode="sql_view"
            )
            fetched = await ctx.client.connectors.get(connector_id)
            ctx.assert_that(
                "SQL view mode accepted for Postgres-family",
                getattr(fetched, "metadata_resolution_mode", None) == "sql_view",
                expected="sql_view",
                actual=getattr(fetched, "metadata_resolution_mode", None),
            )
        except Exception as exc:
            ctx.assert_that("SQL view mode set", False, actual=str(exc))

    # Step 4: Auto mode
    ctx.begin_step("auto_mode")
    try:
        await ctx.client.connectors.update(
            connector_id, metadata_resolution_mode="auto"
        )
        fetched = await ctx.client.connectors.get(connector_id)
        ctx.assert_that(
            "Auto mode accepted",
            getattr(fetched, "metadata_resolution_mode", None) == "auto",
            expected="auto",
            actual=getattr(fetched, "metadata_resolution_mode", None),
        )
    except Exception as exc:
        ctx.assert_that("Auto mode set", False, actual=str(exc))

    # Restore sidecar
    try:
        await ctx.client.connectors.update(
            connector_id, metadata_resolution_mode="sidecar"
        )
    except Exception:
        pass
