"""s02_connector_lifecycle — Create/get/update/list/test connector."""

from __future__ import annotations

from validation_harness.engine import ScenarioContext
from validation_harness.models import CreatedResource
from validation_harness.registry import scenario


@scenario(
    id="s02_connector_lifecycle",
    name="Connector Lifecycle",
    feature_area="connectors",
    depends_on=["s01_auth"],
    requires_features=["connectors"],
)
async def s02_connector_lifecycle(ctx: ScenarioContext) -> None:
    """Create, get, update, list, and test a connector."""
    connector_name = f"{ctx.config.resource_prefix}{ctx.config.profile_name}-connector"
    connector_type = ctx.config.connector.type

    # Step 1: Check for existing connector (idempotent reuse for local dev)
    ctx.begin_step("check_existing")
    existing_id = None
    try:
        page = await ctx.client.connectors.list(per_page=100)
        for c in page.items:
            if hasattr(c, "name") and c.name == connector_name:
                existing_id = c.id
                break
    except Exception:
        pass

    if existing_id:
        ctx.assert_that("Reusing existing connector", True)
        ctx.share("connector_id", existing_id)
    else:
        # Step 2: Create connector
        ctx.begin_step("create_connector")
        connector = await ctx.client.connectors.create(
            name=connector_name,
            type=connector_type,
            config=ctx.config.connector.config,
        )
        ctx.assert_that(
            "Create returns connector with ID",
            connector is not None and hasattr(connector, "id"),
        )
        connector_id = connector.id
        ctx.share("connector_id", connector_id)

        ctx.register_resource(
            CreatedResource(
                resource_type="connector",
                resource_id=str(connector_id),
                resource_name=connector_name,
                owning_scenario="s02_connector_lifecycle",
                deletion_method=f"DELETE /api/connectors/{connector_id}",
            )
        )

    connector_id = ctx.require("connector_id")

    # Step 3: Get connector
    ctx.begin_step("get_connector")
    fetched = await ctx.client.connectors.get(connector_id)
    ctx.assert_that(
        "Get returns connector with matching ID",
        fetched is not None and str(fetched.id) == str(connector_id),
        expected=str(connector_id),
        actual=str(fetched.id) if fetched else None,
    )

    # Step 4: Update connector
    ctx.begin_step("update_connector")
    updated_name = f"{connector_name}-updated"
    updated = await ctx.client.connectors.update(
        connector_id, name=updated_name
    )
    ctx.assert_that(
        "Update changes name",
        updated is not None and hasattr(updated, "name") and updated.name == updated_name,
        expected=updated_name,
        actual=updated.name if updated else None,
    )
    # Restore original name (best-effort, not part of test assertions)
    try:
        await ctx.client.connectors.update(connector_id, name=connector_name)
    except Exception:
        pass  # Non-fatal: name restore is a cleanup convenience

    # Step 5: List connectors
    ctx.begin_step("list_connectors")
    page = await ctx.client.connectors.list(per_page=100)
    found = any(str(c.id) == str(connector_id) for c in page.items)
    ctx.assert_that(
        "Connector appears in list",
        found,
    )

    # Step 6: Test connectivity
    ctx.begin_step("test_connectivity")
    try:
        test_result = await ctx.client.connectors.test(connector_id)
        ctx.assert_that(
            "Test connectivity returns result",
            test_result is not None,
        )
        if test_result is not None:
            ctx.share("connector_test_passed", True)
    except Exception as exc:
        ctx.assert_that(
            "Test connectivity succeeds",
            False,
            expected="connection test result",
            actual=str(exc),
        )
