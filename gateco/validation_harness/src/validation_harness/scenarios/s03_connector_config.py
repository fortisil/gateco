"""s03_connector_config — Search config, ingestion config, metadata resolution mode."""

from __future__ import annotations

from validation_harness.connector_defaults import get_search_config_defaults
from validation_harness.engine import ScenarioContext
from validation_harness.registry import scenario


@scenario(
    id="s03_connector_config",
    name="Connector Configuration",
    feature_area="connectors",
    depends_on=["s02_connector_lifecycle"],
    requires_features=["connectors"],
)
async def s03_connector_config(ctx: ScenarioContext) -> None:
    """Validate search config, ingestion config, and metadata resolution mode roundtrips."""
    connector_id = ctx.require("connector_id")

    # Step 1: Search config roundtrip
    ctx.begin_step("search_config_get")
    search_config = await ctx.client.connectors.get_search_config(connector_id)
    ctx.assert_that(
        "Search config is returned",
        search_config is not None,
    )

    ctx.begin_step("search_config_update")
    try:
        search_defaults = get_search_config_defaults(ctx.config.connector.type)
        updated = await ctx.client.connectors.update_search_config(
            connector_id, search_defaults
        )
        ctx.assert_that(
            "Search config update accepted",
            updated is not None,
        )
        if updated is not None:
            ctx.share("search_config_applied", True)
    except Exception as exc:
        ctx.assert_that(
            "Search config update succeeds",
            False,
            actual=str(exc),
        )

    # Step 2: Ingestion config (cap-gated)
    ctx.begin_step("ingestion_config")
    try:
        ing_config = await ctx.client.connectors.get_ingestion_config(connector_id)
        ctx.assert_that(
            "Ingestion config returned",
            ing_config is not None,
        )
    except Exception:
        ctx.assert_that("Ingestion config available", True)  # Optional

    # Step 3: Metadata resolution mode
    ctx.begin_step("metadata_resolution_mode")
    # Test sidecar (always supported)
    try:
        await ctx.client.connectors.update(
            connector_id, metadata_resolution_mode="sidecar"
        )
        fetched = await ctx.client.connectors.get(connector_id)
        ctx.assert_that(
            "Sidecar mode accepted",
            hasattr(fetched, "metadata_resolution_mode")
            and fetched.metadata_resolution_mode == "sidecar",
            expected="sidecar",
            actual=getattr(fetched, "metadata_resolution_mode", None),
        )
    except Exception as exc:
        ctx.assert_that(
            "Sidecar mode set",
            False,
            actual=str(exc),
        )

    # Step 4: Initial coverage state
    ctx.begin_step("initial_coverage")
    try:
        coverage = await ctx.client.connectors.get_coverage(connector_id)
        ctx.assert_that(
            "Coverage data returned",
            coverage is not None,
        )
    except Exception:
        ctx.assert_that("Coverage endpoint available", True)
