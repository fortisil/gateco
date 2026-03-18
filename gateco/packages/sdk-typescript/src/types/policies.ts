/**
 * Types for policy endpoints.
 */

/** Access policy types. */
export type PolicyType = "rbac" | "abac" | "rebac";

/** Policy lifecycle status. */
export type PolicyStatus = "draft" | "active" | "archived";

/** Policy evaluation effect. */
export type PolicyEffect = "allow" | "deny";

/**
 * A single condition within a policy rule.
 *
 * Fields must be prefixed with `resource.` or `principal.`:
 * - Resource: `resource.classification`, `resource.sensitivity`, `resource.domain`,
 *   `resource.labels`, `resource.encryption_mode`
 * - Principal: `principal.roles`, `principal.groups`, `principal.attributes.*`
 *
 * Operators: `eq`, `ne`, `in`, `contains`, `lte`, `gte`.
 *
 * WARNING: Bare field names (e.g., `classification`) silently resolve against the
 * principal, not the resource. Always use `resource.classification`.
 */
export interface PolicyCondition {
  field?: string;
  operator?: string;
  value?: unknown;
}

/** A rule within a policy. */
export interface PolicyRule {
  id?: string;
  description?: string;
  effect: string;
  conditions?: Record<string, unknown>[];
  priority: number;
}

/** A policy resource. */
export interface Policy {
  id: string;
  name: string;
  description?: string;
  type: string;
  status: string;
  effect: string;
  resource_selectors?: Record<string, unknown>[];
  version: number;
  rules: PolicyRule[];
  created_by?: string;
  created_at?: string;
  updated_at?: string;
}

/** Request body for `POST /api/policies`. */
export interface CreatePolicyRequest {
  name: string;
  description?: string;
  type: string;
  effect: string;
  resource_selectors?: Record<string, unknown>[];
  rules?: Record<string, unknown>[];
}

/** Parse a raw JSON object into a Policy. */
export function parsePolicy(data: Record<string, unknown>): Policy {
  return {
    id: data["id"] as string,
    name: data["name"] as string,
    description: data["description"] as string | undefined,
    type: data["type"] as string,
    status: data["status"] as string,
    effect: data["effect"] as string,
    resource_selectors: data["resource_selectors"] as Record<string, unknown>[] | undefined,
    version: (data["version"] as number) ?? 1,
    rules: Array.isArray(data["rules"])
      ? (data["rules"] as Record<string, unknown>[]).map(parsePolicyRule)
      : [],
    created_by: data["created_by"] as string | undefined,
    created_at: data["created_at"] as string | undefined,
    updated_at: data["updated_at"] as string | undefined,
  };
}

/** Parse a raw JSON object into a PolicyRule. */
export function parsePolicyRule(data: Record<string, unknown>): PolicyRule {
  return {
    id: data["id"] as string | undefined,
    description: data["description"] as string | undefined,
    effect: data["effect"] as string,
    conditions: data["conditions"] as Record<string, unknown>[] | undefined,
    priority: (data["priority"] as number) ?? 0,
  };
}
