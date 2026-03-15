import { apiGet, apiPost } from './client';
import type { Plan, Usage, Invoice, CheckoutRequest, CheckoutResponse, BillingPortalRequest, BillingPortalResponse, Subscription } from '@/types/billing';
import type { PaginatedResponse } from '@/types/gated-resource';

export async function getPlans(): Promise<{ plans: Plan[] }> {
  return apiGet<{ plans: Plan[] }>('/plans', undefined, false);
}

export async function getUsage(): Promise<Usage> {
  return apiGet<Usage>('/billing/usage');
}

export async function getInvoices(params?: { page?: number; perPage?: number }): Promise<PaginatedResponse<Invoice>> {
  return apiGet<PaginatedResponse<Invoice>>('/billing/invoices', {
    page: params?.page,
    per_page: params?.perPage,
  });
}

export async function startCheckout(data: CheckoutRequest): Promise<CheckoutResponse> {
  return apiPost<CheckoutResponse>('/checkout/start', data);
}

export async function createBillingPortal(data?: BillingPortalRequest): Promise<BillingPortalResponse> {
  return apiPost<BillingPortalResponse>('/billing/portal', data);
}

export async function getSubscription(): Promise<Subscription | null> {
  return apiGet<Subscription | null>('/billing/subscription');
}
