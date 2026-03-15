"""Policy evaluation engine v1.

Evaluates conditions against principal attributes and resource metadata.
Reused by Simulator (M5) and Retrieval engine (M6).
"""

from dataclasses import dataclass, field
from uuid import UUID

from gateco.database.enums import PolicyEffect, PolicyStatus
from gateco.database.models.policy import Policy
from gateco.database.models.principal import Principal
from gateco.database.models.resource import GatedResource

# Ordered classification/sensitivity levels for threshold comparison
_CLASSIFICATION_LEVELS = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}
_SENSITIVITY_LEVELS = {"low": 0, "medium": 1, "high": 2, "critical": 3}


@dataclass
class PolicyEvalResult:
    outcome: str = "allowed"  # "allowed" | "denied" | "partial"
    allowed_resources: list[UUID] = field(default_factory=list)
    denied_resources: list[UUID] = field(default_factory=list)
    policy_trace: list[dict] = field(default_factory=list)
    denial_reasons: list[str] = field(default_factory=list)


def evaluate_policies(
    principal: Principal,
    resources: list[GatedResource],
    active_policies: list[Policy],
) -> PolicyEvalResult:
    """Evaluate active policies against a principal and a set of resources."""
    result = PolicyEvalResult()

    for resource in resources:
        allowed = True
        resource_trace = []
        resource_denial = []

        for policy in active_policies:
            if policy.status != PolicyStatus.active:
                continue

            # Check if resource matches policy selectors
            if not _resource_matches_selectors(resource, policy.resource_selectors):
                resource_trace.append({
                    "policy_id": str(policy.id),
                    "policy_name": policy.name,
                    "version": policy.version,
                    "effect": policy.effect.value,
                    "matched": False,
                })
                continue

            # Evaluate rules
            rule_matched = False
            for rule in sorted(policy.rules or [], key=lambda r: r.priority, reverse=True):
                if _evaluate_conditions(principal, resource, rule.conditions or []):
                    rule_matched = True
                    if rule.effect == PolicyEffect.deny:
                        allowed = False
                        resource_denial.append(
                            f"Denied by policy '{policy.name}' rule: "
                            f"{rule.description or 'unnamed'}"
                        )
                    break  # first matching rule wins within a policy

            resource_trace.append({
                "policy_id": str(policy.id),
                "policy_name": policy.name,
                "version": policy.version,
                "effect": policy.effect.value,
                "matched": rule_matched,
            })

            # Policy-level effect if no rule matched but policy itself matches
            if not rule_matched and policy.effect == PolicyEffect.deny:
                allowed = False
                resource_denial.append(f"Denied by policy '{policy.name}' (default effect)")

        result.policy_trace.extend(resource_trace)

        if allowed:
            result.allowed_resources.append(resource.id)
        else:
            result.denied_resources.append(resource.id)
            result.denial_reasons.extend(resource_denial)

    # Determine overall outcome
    if not result.denied_resources:
        result.outcome = "allowed"
    elif not result.allowed_resources:
        result.outcome = "denied"
    else:
        result.outcome = "partial"

    return result


def _resource_matches_selectors(resource: GatedResource, selectors: list[dict] | None) -> bool:
    """Check if a resource matches all policy resource selectors."""
    if not selectors:
        return True  # no selectors = matches everything

    for sel in selectors:
        field_name = sel.get("field", "")
        op = sel.get("op", "eq")
        value = sel.get("value")

        resource_value = _get_resource_field(resource, field_name)
        if not _match_op(resource_value, op, value):
            return False

    return True


def _evaluate_conditions(
    principal: Principal, resource: GatedResource, conditions: list[dict]
) -> bool:
    """Evaluate all conditions against principal + resource. All must match (AND)."""
    if not conditions:
        return True

    for cond in conditions:
        field_name = cond.get("field", "")
        operator = cond.get("operator", "eq")
        value = cond.get("value")

        # Determine actual value from principal or resource
        if field_name.startswith("principal."):
            actual = _get_principal_field(principal, field_name.removeprefix("principal."))
        elif field_name.startswith("resource."):
            actual = _get_resource_field(resource, field_name.removeprefix("resource."))
        else:
            actual = _get_principal_field(principal, field_name)

        if not _match_op(actual, operator, value):
            return False

    return True


def _get_principal_field(principal: Principal, field_name: str):
    if field_name == "roles":
        return principal.roles or []
    if field_name == "groups":
        return principal.groups or []
    if field_name.startswith("attributes."):
        attr_key = field_name.removeprefix("attributes.")
        return (principal.attributes or {}).get(attr_key)
    return getattr(principal, field_name, None)


def _get_resource_field(resource: GatedResource, field_name: str):
    if field_name == "classification":
        return resource.classification.value if resource.classification else None
    if field_name == "sensitivity":
        return resource.sensitivity.value if resource.sensitivity else None
    if field_name == "domain":
        return resource.domain
    if field_name == "labels":
        return resource.labels or []
    if field_name == "encryption_mode":
        return resource.encryption_mode.value if resource.encryption_mode else None
    return getattr(resource, field_name, None)


def _match_op(actual, op: str, expected) -> bool:
    """Match an actual value against an expected value with the given operator."""
    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    if op == "in":
        if isinstance(expected, list):
            return actual in expected
        return False
    if op == "contains":
        if isinstance(actual, list) and isinstance(expected, list):
            return all(v in actual for v in expected)
        if isinstance(actual, list):
            return expected in actual
        return False
    if op == "lte":
        # For classification/sensitivity threshold comparison
        if expected in _CLASSIFICATION_LEVELS:
            levels = _CLASSIFICATION_LEVELS
        else:
            levels = _SENSITIVITY_LEVELS
        actual_level = levels.get(str(actual), 99)
        expected_level = levels.get(str(expected), 99)
        return actual_level <= expected_level
    if op == "gte":
        if expected in _CLASSIFICATION_LEVELS:
            levels = _CLASSIFICATION_LEVELS
        else:
            levels = _SENSITIVITY_LEVELS
        actual_level = levels.get(str(actual), -1)
        expected_level = levels.get(str(expected), -1)
        return actual_level >= expected_level
    return False
