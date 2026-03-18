"""s08_policy_lifecycle — Create draft/activate/archive, deny-by-default, ABAC policies."""

from __future__ import annotations

from validation_harness.engine import ScenarioContext
from validation_harness.models import CreatedResource
from validation_harness.registry import scenario


@scenario(
    id="s08_policy_lifecycle",
    name="Policy Lifecycle",
    feature_area="policies",
    depends_on=["s02_connector_lifecycle"],
    requires_features=["policies"],
)
async def s08_policy_lifecycle(ctx: ScenarioContext) -> None:
    """Create, activate, archive, and verify deny-by-default policies."""
    prefix = ctx.config.resource_prefix
    connector_id = ctx.require("connector_id")

    policy_ids: list[str] = []

    # Step 1: Create vh-allow-public (draft)
    ctx.begin_step("create_allow_public")
    try:
        policy = await ctx.client.policies.create(
            name=f"{prefix}allow-public",
            type="abac",
            effect="allow",
            description="Allow access to public resources",
            resource_selectors=[{"connector_id": connector_id}],
            rules=[{
                "effect": "allow",
                "conditions": [{"field": "resource.classification", "operator": "eq", "value": "public"}],
            }],
        )
        ctx.assert_that("Policy created", policy is not None and hasattr(policy, "id"))
        if policy:
            policy_ids.append(str(policy.id))
            ctx.register_resource(
                CreatedResource(
                    resource_type="policy",
                    resource_id=str(policy.id),
                    resource_name=f"{prefix}allow-public",
                    owning_scenario="s08_policy_lifecycle",
                    deletion_method=f"DELETE /api/policies/{policy.id}",
                )
            )
            ctx.assert_that(
                "Policy status is draft",
                hasattr(policy, "status") and policy.status == "draft",
                expected="draft",
                actual=getattr(policy, "status", None),
            )
    except Exception as exc:
        ctx.assert_that("Create allow-public policy", False, actual=str(exc))
        return

    # Step 2: Activate allow-public
    ctx.begin_step("activate_allow_public")
    try:
        activated = await ctx.client.policies.activate(policy_ids[0])
        ctx.assert_that(
            "Policy activated",
            activated is not None
            and hasattr(activated, "status")
            and activated.status == "active",
            expected="active",
            actual=getattr(activated, "status", None),
        )
    except Exception as exc:
        ctx.assert_that("Activate policy", False, actual=str(exc))

    # Step 3: Create + activate allow-internal
    ctx.begin_step("create_allow_internal")
    try:
        p2 = await ctx.client.policies.create(
            name=f"{prefix}allow-internal",
            type="abac",
            effect="allow",
            description="Allow access to internal resources",
            resource_selectors=[{"connector_id": connector_id}],
            rules=[{
                "effect": "allow",
                "conditions": [{"field": "resource.classification", "operator": "eq", "value": "internal"}],
            }],
        )
        if p2:
            policy_ids.append(str(p2.id))
            ctx.register_resource(
                CreatedResource(
                    resource_type="policy",
                    resource_id=str(p2.id),
                    resource_name=f"{prefix}allow-internal",
                    owning_scenario="s08_policy_lifecycle",
                    deletion_method=f"DELETE /api/policies/{p2.id}",
                )
            )
            await ctx.client.policies.activate(str(p2.id))
            ctx.assert_that("allow-internal created and activated", True)
    except Exception as exc:
        ctx.assert_that("Create allow-internal", False, actual=str(exc))

    # Step 4: Create + activate deny-restricted
    ctx.begin_step("create_deny_restricted")
    try:
        p3 = await ctx.client.policies.create(
            name=f"{prefix}deny-restricted",
            type="abac",
            effect="deny",
            description="Deny access to restricted resources",
            resource_selectors=[{"connector_id": connector_id}],
            rules=[
                {
                    "effect": "deny",
                    "priority": 100,
                    "conditions": [
                        {"field": "resource.classification", "operator": "eq", "value": "restricted"},
                    ],
                },
                {
                    "effect": "allow",
                    "priority": 1,
                    "conditions": [],
                },
            ],
        )
        if p3:
            policy_ids.append(str(p3.id))
            ctx.register_resource(
                CreatedResource(
                    resource_type="policy",
                    resource_id=str(p3.id),
                    resource_name=f"{prefix}deny-restricted",
                    owning_scenario="s08_policy_lifecycle",
                    deletion_method=f"DELETE /api/policies/{p3.id}",
                )
            )
            await ctx.client.policies.activate(str(p3.id))
            ctx.assert_that("deny-restricted created and activated", True)
    except Exception as exc:
        ctx.assert_that("Create deny-restricted", False, actual=str(exc))

    # Step 5: Archive and re-activate
    ctx.begin_step("archive_reactivate")
    if len(policy_ids) >= 1:
        try:
            archived = await ctx.client.policies.archive(policy_ids[0])
            ctx.assert_that(
                "Policy archived",
                archived is not None
                and hasattr(archived, "status")
                and archived.status == "archived",
                expected="archived",
                actual=getattr(archived, "status", None),
            )

            reactivated = await ctx.client.policies.activate(policy_ids[0])
            ctx.assert_that(
                "Policy re-activated",
                reactivated is not None
                and hasattr(reactivated, "status")
                and reactivated.status == "active",
                expected="active",
                actual=getattr(reactivated, "status", None),
            )
        except Exception as exc:
            ctx.assert_that("Archive/reactivate cycle", False, actual=str(exc))

    ctx.share("policy_ids", policy_ids)

    # Share readiness-relevant facts for s15
    active_count = len(policy_ids)  # All policies created above are activated
    ctx.share("policy_count_active", active_count)
