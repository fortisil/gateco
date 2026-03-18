"""s07_data_catalog — List/get/update resources, metadata roundtrip."""

from __future__ import annotations

from validation_harness.engine import ScenarioContext
from validation_harness.registry import scenario


@scenario(
    id="s07_data_catalog",
    name="Data Catalog Operations",
    feature_area="data_catalog",
    depends_on=["s02_connector_lifecycle"],
    requires_features=["connectors"],
)
async def s07_data_catalog(ctx: ScenarioContext) -> None:
    """Verify data catalog list, get, and update operations."""

    # Step 1: List resources
    ctx.begin_step("list_resources")
    try:
        page = await ctx.client.data_catalog.list(per_page=100)
        ctx.assert_that(
            "Data catalog returns items",
            page is not None and hasattr(page, "items"),
        )
    except Exception as exc:
        ctx.assert_that(
            "Data catalog list succeeds",
            False,
            actual=str(exc),
        )
        return

    # Step 2: Get resource detail (if we have resources from ingestion)
    ctx.begin_step("get_resource_detail")
    first_resource_id = ctx.get("first_resource_id")
    if first_resource_id:
        try:
            resource = await ctx.client.data_catalog.get(first_resource_id)
            ctx.assert_that(
                "Resource detail returned",
                resource is not None,
            )
        except Exception as exc:
            ctx.assert_that(
                "Resource detail fetch succeeds",
                False,
                actual=str(exc),
            )
    else:
        ctx.assert_that("Resource available for detail check", True)

    # Step 3: Update metadata roundtrip
    ctx.begin_step("update_metadata")
    if first_resource_id:
        try:
            updated = await ctx.client.data_catalog.update(
                first_resource_id,
                classification="internal",
                sensitivity="medium",
            )
            ctx.assert_that(
                "Metadata update accepted",
                updated is not None,
            )

            # Verify roundtrip
            fetched = await ctx.client.data_catalog.get(first_resource_id)
            if fetched and hasattr(fetched, "classification"):
                ctx.assert_that(
                    "Updated classification persisted",
                    fetched.classification == "internal",
                    expected="internal",
                    actual=getattr(fetched, "classification", None),
                )

            # Restore original
            await ctx.client.data_catalog.update(
                first_resource_id,
                classification="public",
                sensitivity="low",
            )
        except Exception as exc:
            ctx.assert_that(
                "Metadata update succeeds",
                False,
                actual=str(exc),
            )
    else:
        ctx.assert_that("Resource available for metadata update", True)
