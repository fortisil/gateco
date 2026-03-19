"""s19_principal_policies — Create policies with principal-based ABAC conditions."""

from __future__ import annotations

from validation_harness.engine import ScenarioContext
from validation_harness.models import CreatedResource
from validation_harness.registry import scenario


@scenario(
    id="s19_principal_policies",
    name="Principal-Scoped Policies",
    feature_area="policies",
    depends_on=["s18_idp_lifecycle", "s02_connector_lifecycle"],
    requires_features=["policies", "identity_providers"],
    skip_when_dependency_skipped=["s18_idp_lifecycle"],
)
async def s19_principal_policies(ctx: ScenarioContext) -> None:
    """Create policies using principal.groups and principal.attributes conditions."""
    prefix = ctx.config.resource_prefix
    connector_id = ctx.require("connector_id")

    principal_policy_ids: list[str] = []

    async def _create_activate_policy(name, **kwargs):
        """Helper: create policy, register for cleanup, activate, verify active."""
        p = await ctx.client.policies.create(name=name, **kwargs)
        ctx.assert_that(f"{name} created", p is not None and hasattr(p, "id"))
        if not p:
            return None
        pid = str(p.id)
        principal_policy_ids.append(pid)
        ctx.register_resource(
            CreatedResource(
                resource_type="policy",
                resource_id=pid,
                resource_name=name,
                owning_scenario="s19_principal_policies",
                deletion_method=f"DELETE /api/policies/{pid}",
            )
        )
        activated = await ctx.client.policies.activate(pid)
        ctx.assert_that(
            f"{name} status is active",
            hasattr(activated, "status") and activated.status == "active",
            expected="active",
            actual=getattr(activated, "status", None),
        )
        return pid

    # Step 1: Allow engineering group access to internal resources
    ctx.begin_step("create_engineering_allow_internal")
    try:
        await _create_activate_policy(
            f"{prefix}engineering-allow-internal",
            type="abac",
            effect="allow",
            description="Allow engineering group access to internal resources",
            resource_selectors=[{"connector_id": connector_id}],
            rules=[{
                "effect": "allow",
                "conditions": [
                    {"field": "principal.groups", "operator": "contains", "value": ["engineering"]},
                    {"field": "resource.classification", "operator": "eq", "value": "internal"},
                ],
            }],
        )
    except Exception as exc:
        ctx.assert_that("Create engineering-allow-internal", False, actual=str(exc))

    # Step 2: Deny marketing group access to confidential resources
    ctx.begin_step("create_marketing_deny_confidential")
    try:
        await _create_activate_policy(
            f"{prefix}marketing-deny-confidential",
            type="abac",
            effect="deny",
            description="Deny marketing group access to confidential resources",
            resource_selectors=[{"connector_id": connector_id}],
            rules=[{
                "effect": "deny",
                "priority": 100,
                "conditions": [
                    {"field": "principal.groups", "operator": "contains", "value": ["marketing"]},
                    {"field": "resource.classification", "operator": "eq", "value": "confidential"},
                ],
            }],
        )
    except Exception as exc:
        ctx.assert_that("Create marketing-deny-confidential", False, actual=str(exc))

    # Step 3: Allow engineering department access to engineering-domain resources
    ctx.begin_step("create_dept_attribute_policy")
    try:
        await _create_activate_policy(
            f"{prefix}dept-engineering-domain",
            type="abac",
            effect="allow",
            description="Allow engineering department access to engineering-domain resources",
            resource_selectors=[{"connector_id": connector_id}],
            rules=[{
                "effect": "allow",
                "conditions": [
                    {"field": "principal.attributes.department", "operator": "eq", "value": "engineering"},
                    {"field": "resource.domain", "operator": "eq", "value": "engineering"},
                ],
            }],
        )
    except Exception as exc:
        ctx.assert_that("Create dept-engineering-domain", False, actual=str(exc))

    # Step 4: Verify all policies appear in list and are active
    ctx.begin_step("verify_policies_in_list")
    try:
        policies_page = await ctx.client.policies.list(per_page=100)
        active_ids = [
            str(p.id) for p in policies_page.items
            if getattr(p, "status", None) == "active"
        ]
        for pid in principal_policy_ids:
            ctx.assert_that(
                f"Policy {pid} is active in list",
                pid in active_ids,
            )
    except Exception as exc:
        ctx.assert_that("Verify policies in list", False, actual=str(exc))

    ctx.share("principal_policy_ids", principal_policy_ids)
