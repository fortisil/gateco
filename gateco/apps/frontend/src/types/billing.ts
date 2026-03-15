export type PlanTier = 'free' | 'pro' | 'enterprise';

export interface PlanFeatures {
  policy_studio: boolean;
  access_simulator: boolean;
  vendor_iam: boolean;
  audit_export: boolean;
  siem_export: boolean;
  content_ref_mode: boolean;
  custom_kms: boolean;
  private_data_plane: boolean;
  sso_scim: boolean;
  advanced_analytics: boolean;
  multi_connector: boolean;
  policy_versioning: boolean;
  rbac_policies: boolean;
  abac_policies: boolean;
}

export interface PlanLimits {
  secured_retrievals: number | null;
  connectors: number | null;
  identity_providers: number | null;
  policies: number | null;
  team_members: number | null;
  overage_price_cents: number;
}

export interface Plan {
  id: string;
  name: string;
  tier: PlanTier;
  price_monthly_cents: number;
  price_yearly_cents: number;
  features: PlanFeatures;
  limits: PlanLimits;
}

export interface UsageMetric {
  used: number;
  limit: number | null;
  overage?: number;
}

export interface Usage {
  period_start: string;
  period_end: string;
  secured_retrievals: UsageMetric & { overage: number };
  connectors: { used: number; limit: number | null };
  policies: { used: number; limit: number | null };
  estimated_overage_cents: number;
}

export interface Invoice {
  id: string;
  stripe_invoice_id: string;
  amount_cents: number;
  currency: string;
  status: 'paid' | 'pending' | 'failed';
  period_start: string;
  period_end: string;
  pdf_url: string;
  created_at: string;
}

export interface CheckoutRequest {
  plan_id: string;
  billing_period: 'monthly' | 'yearly';
}

export interface CheckoutResponse {
  checkout_url: string;
  session_id: string;
}

export interface BillingPortalRequest {
  return_url?: string;
}

export interface BillingPortalResponse {
  portal_url: string;
}

export interface Subscription {
  id: string;
  plan_id: string;
  status: 'active' | 'canceled' | 'past_due' | 'trialing';
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
}

export type FeatureKey = keyof PlanFeatures;
