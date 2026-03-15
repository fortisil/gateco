export type PolicyType = 'rbac' | 'abac' | 'rebac';

export type PolicyStatus = 'draft' | 'active' | 'archived';

export type PolicyEffect = 'allow' | 'deny';

export interface PolicyCondition {
  field: string;
  operator: 'eq' | 'neq' | 'in' | 'not_in' | 'contains' | 'gte' | 'lte';
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
