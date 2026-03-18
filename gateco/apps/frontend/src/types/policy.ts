export type PolicyType = 'rbac' | 'abac' | 'rebac';

export type PolicyStatus = 'draft' | 'active' | 'archived';

export type PolicyEffect = 'allow' | 'deny';

/**
 * A single condition within a policy rule.
 *
 * Fields must be prefixed with `resource.` or `principal.`:
 * - Resource: `resource.classification`, `resource.sensitivity`, `resource.domain`, `resource.labels`, `resource.encryption_mode`
 * - Principal: `principal.roles`, `principal.groups`, `principal.attributes.*`
 *
 * WARNING: Bare field names (e.g., `classification`) silently resolve against the principal, not the resource.
 */
export interface PolicyCondition {
  field: string;
  operator: 'eq' | 'ne' | 'in' | 'contains' | 'gte' | 'lte';
  value: string | string[] | number;
}

export interface PolicyRule {
  id: string;
  description: string;
  effect: PolicyEffect;
  conditions: PolicyCondition[];
  priority: number;
}

export interface Policy {
  id: string;
  name: string;
  description: string;
  type: PolicyType;
  status: PolicyStatus;
  effect: PolicyEffect;
  rules: PolicyRule[];
  resource_selectors: string[];
  version: number;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface PolicyVersion {
  version: number;
  status: PolicyStatus;
  created_by: string;
  created_at: string;
  change_summary: string;
}
