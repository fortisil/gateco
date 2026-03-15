/**
 * Types for billing endpoints.
 */

/** Numeric limits for a plan tier. */
export interface PlanLimits {
  secured_retrievals?: number;
  connectors?: number;
  policies?: number;
  identity_providers?: number;
}

/** Feature flags for a plan tier. */
export interface PlanFeatures {
  policy_studio: boolean;
  audit_export: boolean;
  access_simulator: boolean;
  custom_roles: boolean;
  sso: boolean;
}

/** A billing plan. */
export interface Plan {
  id: string;
  name: string;
  description?: string;
  price_monthly_cents: number;
  price_yearly_cents: number;
  limits?: PlanLimits;
  features?: PlanFeatures;
  stripe_price_id_monthly?: string;
  stripe_price_id_yearly?: string;
}

/** A single usage metric with used/limit. */
export interface UsageMetric {
  used: number;
  limit?: number;
  overage?: number;
}

/** Current billing period usage. */
export interface Usage {
  period_start?: string;
  period_end?: string;
  secured_retrievals?: UsageMetric;
  connectors?: UsageMetric;
  policies?: UsageMetric;
  estimated_overage_cents: number;
}

/** A billing invoice. */
export interface Invoice {
  id: string;
  stripe_invoice_id?: string;
  amount_cents: number;
  currency: string;
  status?: string;
  period_start?: string;
  period_end?: string;
  pdf_url?: string;
  created_at?: string;
}

/** An active subscription. */
export interface Subscription {
  id: string;
  plan_id: string;
  status: string;
  current_period_start?: string;
  current_period_end?: string;
  cancel_at_period_end: boolean;
}

/** Request body for `POST /api/checkout/start`. */
export interface CheckoutRequest {
  plan_id: string;
  billing_period?: string;
}

/** Response from `POST /api/checkout/start`. */
export interface CheckoutResponse {
  checkout_url: string;
  session_id: string;
}

/** Parse a raw JSON object into a PlanLimits. */
export function parsePlanLimits(data: Record<string, unknown>): PlanLimits {
  return {
    secured_retrievals: data["secured_retrievals"] as number | undefined,
    connectors: data["connectors"] as number | undefined,
    policies: data["policies"] as number | undefined,
    identity_providers: data["identity_providers"] as number | undefined,
  };
}

/** Parse a raw JSON object into a PlanFeatures. */
export function parsePlanFeatures(data: Record<string, unknown>): PlanFeatures {
  return {
    policy_studio: (data["policy_studio"] as boolean) ?? false,
    audit_export: (data["audit_export"] as boolean) ?? false,
    access_simulator: (data["access_simulator"] as boolean) ?? false,
    custom_roles: (data["custom_roles"] as boolean) ?? false,
    sso: (data["sso"] as boolean) ?? false,
  };
}

/** Parse a raw JSON object into a UsageMetric. */
export function parseUsageMetric(data: Record<string, unknown>): UsageMetric {
  return {
    used: (data["used"] as number) ?? 0,
    limit: data["limit"] as number | undefined,
    overage: data["overage"] as number | undefined,
  };
}

/** Parse a raw JSON object into a Plan. */
export function parsePlan(data: Record<string, unknown>): Plan {
  return {
    id: data["id"] as string,
    name: data["name"] as string,
    description: data["description"] as string | undefined,
    price_monthly_cents: (data["price_monthly_cents"] as number) ?? 0,
    price_yearly_cents: (data["price_yearly_cents"] as number) ?? 0,
    limits: data["limits"]
      ? parsePlanLimits(data["limits"] as Record<string, unknown>)
      : undefined,
    features: data["features"]
      ? parsePlanFeatures(data["features"] as Record<string, unknown>)
      : undefined,
    stripe_price_id_monthly: data["stripe_price_id_monthly"] as string | undefined,
    stripe_price_id_yearly: data["stripe_price_id_yearly"] as string | undefined,
  };
}

/** Parse a raw JSON object into a Usage. */
export function parseUsage(data: Record<string, unknown>): Usage {
  return {
    period_start: data["period_start"] as string | undefined,
    period_end: data["period_end"] as string | undefined,
    secured_retrievals: data["secured_retrievals"]
      ? parseUsageMetric(data["secured_retrievals"] as Record<string, unknown>)
      : undefined,
    connectors: data["connectors"]
      ? parseUsageMetric(data["connectors"] as Record<string, unknown>)
      : undefined,
    policies: data["policies"]
      ? parseUsageMetric(data["policies"] as Record<string, unknown>)
      : undefined,
    estimated_overage_cents: (data["estimated_overage_cents"] as number) ?? 0,
  };
}

/** Parse a raw JSON object into an Invoice. */
export function parseInvoice(data: Record<string, unknown>): Invoice {
  return {
    id: data["id"] as string,
    stripe_invoice_id: data["stripe_invoice_id"] as string | undefined,
    amount_cents: (data["amount_cents"] as number) ?? 0,
    currency: (data["currency"] as string) ?? "usd",
    status: data["status"] as string | undefined,
    period_start: data["period_start"] as string | undefined,
    period_end: data["period_end"] as string | undefined,
    pdf_url: data["pdf_url"] as string | undefined,
    created_at: data["created_at"] as string | undefined,
  };
}

/** Parse a raw JSON object into a Subscription. */
export function parseSubscription(data: Record<string, unknown>): Subscription {
  return {
    id: data["id"] as string,
    plan_id: data["plan_id"] as string,
    status: data["status"] as string,
    current_period_start: data["current_period_start"] as string | undefined,
    current_period_end: data["current_period_end"] as string | undefined,
    cancel_at_period_end: (data["cancel_at_period_end"] as boolean) ?? false,
  };
}

/** Parse a raw JSON object into a CheckoutResponse. */
export function parseCheckoutResponse(data: Record<string, unknown>): CheckoutResponse {
  return {
    checkout_url: data["checkout_url"] as string,
    session_id: data["session_id"] as string,
  };
}
