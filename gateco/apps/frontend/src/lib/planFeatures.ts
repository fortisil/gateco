import type { FeatureKey, PlanFeatures, PlanTier } from '@/types/billing';

export interface PlanFeatureInfo {
  key: FeatureKey;
  label: string;
  description: string;
  requiredTier: PlanTier;
}

export const PLAN_FEATURES_CATALOG: PlanFeatureInfo[] = [
  { key: 'rbac_policies', label: 'RBAC Policies', description: 'Role-based access control policies', requiredTier: 'free' },
  { key: 'abac_policies', label: 'ABAC Policies', description: 'Attribute-based access control with fine-grained conditions', requiredTier: 'pro' },
  { key: 'policy_studio', label: 'Policy Studio', description: 'Visual policy editor with drag-and-drop rule building', requiredTier: 'pro' },
  { key: 'policy_versioning', label: 'Policy Versioning', description: 'Version history and diff viewer for policies', requiredTier: 'pro' },
  { key: 'access_simulator', label: 'Access Simulator', description: 'Simulate queries to see what a principal can access before going live', requiredTier: 'pro' },
  { key: 'vendor_iam', label: 'Vendor IAM Providers', description: 'Connect Azure Entra ID, AWS IAM, Okta, and more', requiredTier: 'pro' },
  { key: 'multi_connector', label: 'Multiple Connectors', description: 'Connect multiple vector databases simultaneously', requiredTier: 'pro' },
  { key: 'advanced_analytics', label: 'Advanced Analytics', description: 'Detailed retrieval analytics and trend insights', requiredTier: 'pro' },
  { key: 'audit_export', label: 'Audit Export', description: 'Export audit logs as CSV or JSON', requiredTier: 'pro' },
  { key: 'siem_export', label: 'SIEM Integration', description: 'Stream audit events to your SIEM platform', requiredTier: 'enterprise' },
  { key: 'content_ref_mode', label: 'Content Reference Mode', description: 'Return references instead of content for maximum security', requiredTier: 'enterprise' },
  { key: 'custom_kms', label: 'Custom KMS', description: 'Bring your own encryption keys', requiredTier: 'enterprise' },
  { key: 'sso_scim', label: 'SSO & SCIM', description: 'Enterprise single sign-on and user provisioning', requiredTier: 'enterprise' },
  { key: 'private_data_plane', label: 'Private Data Plane', description: 'Dedicated infrastructure in your cloud', requiredTier: 'enterprise' },
];

export const PLAN_FEATURES_MAP: Record<PlanTier, PlanFeatures> = {
  free: {
    rbac_policies: true, abac_policies: false, policy_studio: false, policy_versioning: false,
    access_simulator: false, vendor_iam: false, multi_connector: false, advanced_analytics: false,
    audit_export: false, siem_export: false, content_ref_mode: false, custom_kms: false,
    sso_scim: false, private_data_plane: false,
  },
  pro: {
    rbac_policies: true, abac_policies: true, policy_studio: true, policy_versioning: true,
    access_simulator: true, vendor_iam: true, multi_connector: true, advanced_analytics: true,
    audit_export: true, siem_export: false, content_ref_mode: false, custom_kms: false,
    sso_scim: false, private_data_plane: false,
  },
  enterprise: {
    rbac_policies: true, abac_policies: true, policy_studio: true, policy_versioning: true,
    access_simulator: true, vendor_iam: true, multi_connector: true, advanced_analytics: true,
    audit_export: true, siem_export: true, content_ref_mode: true, custom_kms: true,
    sso_scim: true, private_data_plane: true,
  },
};

export const TIER_ORDER: Record<PlanTier, number> = { free: 0, pro: 1, enterprise: 2 };

export function getFeatureInfo(key: FeatureKey): PlanFeatureInfo | undefined {
  return PLAN_FEATURES_CATALOG.find((f) => f.key === key);
}

export function getRequiredTier(key: FeatureKey): PlanTier {
  return getFeatureInfo(key)?.requiredTier ?? 'pro';
}
