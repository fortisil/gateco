/**
 * Billing resource -- plans, usage, invoices, subscriptions, checkout, portal.
 */

import type { GatecoClient } from "../client.js";
import type { Page } from "../pagination.js";
import { parsePage } from "../pagination.js";
import type {
  Plan,
  Usage,
  Invoice,
  Subscription,
  CheckoutResponse,
} from "../types/billing.js";
import {
  parsePlan,
  parseUsage,
  parseInvoice,
  parseSubscription,
  parseCheckoutResponse,
} from "../types/billing.js";

/** Namespace for billing endpoints. Accessed as `client.billing`. */
export class BillingResource {
  constructor(private readonly client: GatecoClient) {}

  // ------------------------------------------------------------------
  // Plans (public)
  // ------------------------------------------------------------------

  /** List all available plans (public, no auth required). */
  async getPlans(): Promise<Plan[]> {
    const raw = await this.client._request("GET", "/api/plans", {
      authenticate: false,
    });
    const plansRaw = (raw && Array.isArray((raw as Record<string, unknown>)["plans"])
      ? (raw as Record<string, unknown>)["plans"]
      : []) as Record<string, unknown>[];
    return plansRaw.map(parsePlan);
  }

  // ------------------------------------------------------------------
  // Usage
  // ------------------------------------------------------------------

  /** Get current billing period usage for the authenticated organization. */
  async getUsage(): Promise<Usage> {
    const data = await this.client._request("GET", "/api/billing/usage");
    return parseUsage(data as Record<string, unknown>);
  }

  // ------------------------------------------------------------------
  // Invoices
  // ------------------------------------------------------------------

  /** Fetch a page of invoices. */
  async getInvoices(page = 1, perPage = 20): Promise<Page<Invoice>> {
    const raw = await this.client._request("GET", "/api/billing/invoices", {
      params: { page, per_page: perPage },
    });
    return parsePage(raw, page, perPage, parseInvoice);
  }

  // ------------------------------------------------------------------
  // Subscription
  // ------------------------------------------------------------------

  /** Get the current subscription for the authenticated organization. */
  async getSubscription(): Promise<Subscription | null> {
    const data = await this.client._request("GET", "/api/billing/subscription");
    if (data === null) {
      return null;
    }
    return parseSubscription(data as Record<string, unknown>);
  }

  // ------------------------------------------------------------------
  // Checkout
  // ------------------------------------------------------------------

  /** Create a Stripe Checkout Session for plan upgrade. */
  async startCheckout(
    planId: string,
    billingPeriod = "monthly",
  ): Promise<CheckoutResponse> {
    const data = await this.client._request("POST", "/api/checkout/start", {
      json: { plan_id: planId, billing_period: billingPeriod },
    });
    return parseCheckoutResponse(data as Record<string, unknown>);
  }

  // ------------------------------------------------------------------
  // Billing Portal
  // ------------------------------------------------------------------

  /** Create a Stripe Billing Portal session. */
  async createPortal(returnUrl?: string): Promise<Record<string, unknown>> {
    const body: Record<string, unknown> = {};
    if (returnUrl !== undefined) {
      body["return_url"] = returnUrl;
    }
    const data = await this.client._request("POST", "/api/billing/portal", {
      json: body,
    });
    return (data as Record<string, unknown>) ?? {};
  }
}
