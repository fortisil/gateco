"""s18_idp_lifecycle — Create IDP, trigger sync, verify principals, update, list.

NOTE: These scenarios validate Gateco's identity-provider object lifecycle and
principal-aware enforcement using the backend's stub sync. They do NOT validate
real SCIM/OIDC/SAML provider integrations.
"""

from __future__ import annotations

from validation_harness.engine import ScenarioContext
from validation_harness.models import CreatedResource
from validation_harness.registry import scenario


@scenario(
    id="s18_idp_lifecycle",
    name="IDP Lifecycle",
    feature_area="identity_providers",
    depends_on=["s01_auth"],
    requires_features=["identity_providers"],
)
async def s18_idp_lifecycle(ctx: ScenarioContext) -> None:
    """Create an IDP, sync principals, verify attributes, update config."""
    prefix = ctx.config.resource_prefix
    idp_type = ctx.config.identity_provider.type
    idp_config = dict(ctx.config.identity_provider.config)

    # Step 1: Create IDP
    ctx.begin_step("create_idp")
    try:
        idp = await ctx.client.identity_providers.create(
            name=f"{prefix}test-{idp_type}-idp",
            type=idp_type,
            config=idp_config,
        )
        ctx.assert_that("IDP created", idp is not None and hasattr(idp, "id"))
        ctx.assert_that(
            f"IDP type is {idp_type}",
            hasattr(idp, "type") and idp.type == idp_type,
            expected=idp_type,
            actual=getattr(idp, "type", None),
        )
        idp_id = str(idp.id)
        ctx.register_resource(
            CreatedResource(
                resource_type="identity_provider",
                resource_id=idp_id,
                resource_name=f"{prefix}test-{idp_type}-idp",
                owning_scenario="s18_idp_lifecycle",
                deletion_method=f"DELETE /api/identity-providers/{idp_id}",
            )
        )
    except Exception as exc:
        ctx.assert_that("Create IDP", False, actual=str(exc))
        return

    # Step 2: Trigger sync
    ctx.begin_step("trigger_sync")
    try:
        synced = await ctx.client.identity_providers.sync(idp_id)
        ctx.assert_that("Sync returned result", synced is not None)
        refreshed = await ctx.client.identity_providers.get(idp_id)
        ctx.assert_that(
            "IDP status is connected after sync",
            hasattr(refreshed, "status") and refreshed.status == "connected",
            expected="connected",
            actual=getattr(refreshed, "status", None),
        )
        ctx.assert_that(
            "Principal count >= 5",
            hasattr(refreshed, "principal_count") and refreshed.principal_count >= 5,
            expected=">=5",
            actual=getattr(refreshed, "principal_count", None),
        )
        ctx.assert_that(
            "Group count >= 2",
            hasattr(refreshed, "group_count") and refreshed.group_count >= 2,
            expected=">=2",
            actual=getattr(refreshed, "group_count", None),
        )
    except Exception as exc:
        ctx.assert_that("Trigger sync", False, actual=str(exc))
        return

    # Step 3: Verify synced principals
    ctx.begin_step("verify_principals")
    try:
        principals_page = await ctx.client.principals.list(per_page=100)
        all_principals = principals_page.items
        ctx.assert_that(
            "At least 5 principals exist",
            len(all_principals) >= 5,
            expected=">=5",
            actual=len(all_principals),
        )

        engineering_principals: list[str] = []
        marketing_principals: list[str] = []
        for p in all_principals:
            groups = getattr(p, "groups", None) or []
            if "engineering" in groups:
                engineering_principals.append(str(p.id))
            if "marketing" in groups:
                marketing_principals.append(str(p.id))

        ctx.assert_that(
            "At least 2 principals in engineering group",
            len(engineering_principals) >= 2,
            expected=">=2",
            actual=len(engineering_principals),
        )
        ctx.assert_that(
            "At least 1 principal in marketing group",
            len(marketing_principals) >= 1,
            expected=">=1",
            actual=len(marketing_principals),
        )
    except Exception as exc:
        ctx.assert_that("Verify principals", False, actual=str(exc))
        return

    # Step 4: Verify department attributes
    ctx.begin_step("verify_principal_attributes")
    try:
        if engineering_principals:
            eng_p = await ctx.client.principals.get(engineering_principals[0])
            ctx.assert_that(
                "Engineering principal has department=engineering",
                hasattr(eng_p, "attributes")
                and (eng_p.attributes or {}).get("department") == "engineering",
                expected="engineering",
                actual=(getattr(eng_p, "attributes", None) or {}).get("department"),
            )

        if marketing_principals:
            mkt_p = await ctx.client.principals.get(marketing_principals[0])
            ctx.assert_that(
                "Marketing principal has department=marketing",
                hasattr(mkt_p, "attributes")
                and (mkt_p.attributes or {}).get("department") == "marketing",
                expected="marketing",
                actual=(getattr(mkt_p, "attributes", None) or {}).get("department"),
            )
    except Exception as exc:
        ctx.assert_that("Verify principal attributes", False, actual=str(exc))

    # Step 5: Update IDP config
    ctx.begin_step("update_idp")
    try:
        updated = await ctx.client.identity_providers.update(
            idp_id, name=f"{prefix}test-{idp_type}-idp-updated",
        )
        ctx.assert_that(
            "IDP name updated",
            hasattr(updated, "name")
            and updated.name == f"{prefix}test-{idp_type}-idp-updated",
            expected=f"{prefix}test-{idp_type}-idp-updated",
            actual=getattr(updated, "name", None),
        )
    except Exception as exc:
        ctx.assert_that("Update IDP", False, actual=str(exc))

    # Step 6: Verify IDP appears in list
    ctx.begin_step("verify_idp_in_list")
    try:
        idp_page = await ctx.client.identity_providers.list(per_page=100)
        idp_ids = [str(i.id) for i in idp_page.items]
        ctx.assert_that(
            "Created IDP appears in list",
            idp_id in idp_ids,
            expected=f"{idp_id} in list",
            actual=idp_ids,
        )
    except Exception as exc:
        ctx.assert_that("Verify IDP in list", False, actual=str(exc))

    # Share state for downstream scenarios
    ctx.share("idp_id", idp_id)
    ctx.share("engineering_principal_ids", engineering_principals)
    ctx.share("marketing_principal_ids", marketing_principals)
    if engineering_principals:
        ctx.share("engineering_principal_id", engineering_principals[0])
    if marketing_principals:
        ctx.share("marketing_principal_id", marketing_principals[0])
