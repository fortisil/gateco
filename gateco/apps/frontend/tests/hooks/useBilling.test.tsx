/**
 * Tests for useBilling hooks.
 *
 * These tests verify the billing management hooks work correctly,
 * including plans listing, checkout initiation, usage tracking,
 * and invoice management.
 *
 * Hook location: apps/frontend/src/hooks/useBilling.ts
 *
 * Tests are marked with .skip until the hooks are implemented.
 * Remove .skip and uncomment the test code when ready.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

// Hooks - to be implemented
// import {
//   usePlans,
//   useCurrentPlan,
//   useUsage,
//   useInvoices,
//   useCheckout,
//   useBillingPortal,
//   useSubscription,
// } from '@/hooks/useBilling';

// Mock data
const mockPlans = [
  {
    id: 'free',
    name: 'Free',
    tier: 'free',
    price_monthly_cents: 0,
    price_yearly_cents: 0,
    features: {
      custom_branding: false,
      custom_domain: false,
      analytics: false,
      api_access: false,
      priority_support: false,
    },
    limits: {
      resources: 3,
      secured_retrievals: 100,
      team_members: 1,
      overage_price_cents: 0,
    },
  },
  {
    id: 'pro',
    name: 'Pro',
    tier: 'pro',
    price_monthly_cents: 2900,
    price_yearly_cents: 29000,
    features: {
      custom_branding: true,
      custom_domain: true,
      analytics: true,
      api_access: true,
      priority_support: false,
    },
    limits: {
      resources: null,
      secured_retrievals: 10000,
      team_members: 5,
      overage_price_cents: 500,
    },
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    tier: 'enterprise',
    price_monthly_cents: 9900,
    price_yearly_cents: 99000,
    features: {
      custom_branding: true,
      custom_domain: true,
      analytics: true,
      api_access: true,
      priority_support: true,
    },
    limits: {
      resources: null,
      secured_retrievals: null,
      team_members: null,
      overage_price_cents: 0,
    },
  },
];

const mockUsage = {
  period_start: '2026-02-01T00:00:00Z',
  period_end: '2026-02-28T23:59:59Z',
  secured_retrievals: {
    used: 45,
    limit: 100,
    overage: 0,
  },
  resources: {
    used: 2,
    limit: 3,
  },
  estimated_overage_cents: 0,
};

const mockInvoices = [
  {
    id: 'inv_1',
    stripe_invoice_id: 'in_test_123',
    amount_cents: 2900,
    currency: 'USD',
    status: 'paid',
    period_start: '2026-01-01T00:00:00Z',
    period_end: '2026-01-31T23:59:59Z',
    pdf_url: 'https://invoice.stripe.com/test/pdf',
    created_at: '2026-02-01T00:00:00Z',
  },
  {
    id: 'inv_2',
    stripe_invoice_id: 'in_test_456',
    amount_cents: 2900,
    currency: 'USD',
    status: 'paid',
    period_start: '2025-12-01T00:00:00Z',
    period_end: '2025-12-31T23:59:59Z',
    pdf_url: 'https://invoice.stripe.com/test/pdf2',
    created_at: '2026-01-01T00:00:00Z',
  },
];

const mockSubscription = {
  id: 'sub_test_123',
  plan_id: 'pro',
  status: 'active',
  current_period_start: '2026-02-01T00:00:00Z',
  current_period_end: '2026-02-28T23:59:59Z',
  cancel_at_period_end: false,
};

// MSW Server setup
const server = setupServer(
  // Get plans (public endpoint)
  http.get('http://localhost:8000/api/plans', () => {
    return HttpResponse.json({ plans: mockPlans });
  }),

  // Get current usage
  http.get('http://localhost:8000/api/billing/usage', ({ request }) => {
    const auth = request.headers.get('Authorization');
    if (!auth) {
      return HttpResponse.json(
        { error: { code: 'AUTH_TOKEN_INVALID' } },
        { status: 401 }
      );
    }
    return HttpResponse.json(mockUsage);
  }),

  // Get invoices
  http.get('http://localhost:8000/api/billing/invoices', ({ request }) => {
    const auth = request.headers.get('Authorization');
    if (!auth) {
      return HttpResponse.json(
        { error: { code: 'AUTH_TOKEN_INVALID' } },
        { status: 401 }
      );
    }
    return HttpResponse.json({
      data: mockInvoices,
      meta: { pagination: { page: 1, per_page: 20, total: 2, total_pages: 1 } },
    });
  }),

  // Start checkout
  http.post('http://localhost:8000/api/checkout/start', async ({ request }) => {
    const auth = request.headers.get('Authorization');
    if (!auth) {
      return HttpResponse.json(
        { error: { code: 'AUTH_TOKEN_INVALID' } },
        { status: 401 }
      );
    }

    const body = await request.json() as Record<string, unknown>;

    if (!mockPlans.find(p => p.id === body.plan_id)) {
      return HttpResponse.json(
        { error: { code: 'BILLING_INVALID_PLAN', message: 'Invalid plan' } },
        { status: 400 }
      );
    }

    if (body.plan_id === 'free') {
      return HttpResponse.json(
        { error: { code: 'BILLING_INVALID_PLAN', message: 'Cannot checkout free plan' } },
        { status: 400 }
      );
    }

    return HttpResponse.json({
      checkout_url: 'https://checkout.stripe.com/pay/cs_test_123',
      session_id: 'cs_test_123',
    });
  }),

  // Create billing portal session
  http.post('http://localhost:8000/api/billing/portal', ({ request }) => {
    const auth = request.headers.get('Authorization');
    if (!auth) {
      return HttpResponse.json(
        { error: { code: 'AUTH_TOKEN_INVALID' } },
        { status: 401 }
      );
    }
    return HttpResponse.json({
      portal_url: 'https://billing.stripe.com/session/bps_test_123',
    });
  }),

  // Get subscription
  http.get('http://localhost:8000/api/billing/subscription', ({ request }) => {
    const auth = request.headers.get('Authorization');
    if (!auth) {
      return HttpResponse.json(
        { error: { code: 'AUTH_TOKEN_INVALID' } },
        { status: 401 }
      );
    }
    return HttpResponse.json(mockSubscription);
  })
);

// Test wrapper with auth token
const createWrapper = (withAuth = true) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  // Mock auth context if needed
  if (withAuth) {
    // Set auth header for requests
  }

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

// Setup/teardown
beforeEach(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

afterEach(() => {
  server.resetHandlers();
  server.close();
});

// ============================================================================
// usePlans Tests
// ============================================================================

describe('usePlans', () => {
  it.skip('fetches available plans', async () => {
    // const { result } = renderHook(() => usePlans(), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => {
    //   expect(result.current.isLoading).toBe(false);
    // });

    // expect(result.current.data?.plans).toHaveLength(3);
    // expect(result.current.data?.plans[0].id).toBe('free');
    // expect(result.current.data?.plans[1].id).toBe('pro');
    // expect(result.current.data?.plans[2].id).toBe('enterprise');
    expect(true).toBe(true);
  });

  it.skip('is accessible without authentication', async () => {
    // Plans endpoint is public
    // const { result } = renderHook(() => usePlans(), {
    //   wrapper: createWrapper(false), // No auth
    // });

    // await waitFor(() => {
    //   expect(result.current.isLoading).toBe(false);
    // });

    // expect(result.current.data?.plans).toHaveLength(3);
    expect(true).toBe(true);
  });

  it.skip('returns plan features and limits', async () => {
    // const { result } = renderHook(() => usePlans(), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => {
    //   expect(result.current.isLoading).toBe(false);
    // });

    // const proPlan = result.current.data?.plans.find(p => p.id === 'pro');
    // expect(proPlan?.features.custom_branding).toBe(true);
    // expect(proPlan?.limits.secured_retrievals).toBe(10000);
    expect(true).toBe(true);
  });
});

// ============================================================================
// useCurrentPlan Tests
// ============================================================================

describe('useCurrentPlan', () => {
  it.skip('returns current organization plan', async () => {
    // const { result } = renderHook(() => useCurrentPlan(), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => {
    //   expect(result.current.isLoading).toBe(false);
    // });

    // expect(result.current.plan).toBeDefined();
    // expect(result.current.plan?.tier).toBe('free');
    expect(true).toBe(true);
  });

  it.skip('includes entitlements for current plan', async () => {
    // const { result } = renderHook(() => useCurrentPlan(), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => {
    //   expect(result.current.isLoading).toBe(false);
    // });

    // expect(result.current.entitlements).toBeDefined();
    // expect(result.current.entitlements?.custom_branding).toBe(false); // Free plan
    expect(true).toBe(true);
  });
});

// ============================================================================
// useUsage Tests
// ============================================================================

describe('useUsage', () => {
  it.skip('fetches current usage metrics', async () => {
    // const { result } = renderHook(() => useUsage(), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => {
    //   expect(result.current.isLoading).toBe(false);
    // });

    // expect(result.current.data?.secured_retrievals.used).toBe(45);
    // expect(result.current.data?.secured_retrievals.limit).toBe(100);
    expect(true).toBe(true);
  });

  it.skip('returns billing period dates', async () => {
    // const { result } = renderHook(() => useUsage(), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => {
    //   expect(result.current.isLoading).toBe(false);
    // });

    // expect(result.current.data?.period_start).toBeDefined();
    // expect(result.current.data?.period_end).toBeDefined();
    expect(true).toBe(true);
  });

  it.skip('calculates usage percentage', async () => {
    // const { result } = renderHook(() => useUsage(), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => {
    //   expect(result.current.isLoading).toBe(false);
    // });

    // // Helper function in hook
    // const percentage = result.current.getUsagePercentage('secured_retrievals');
    // expect(percentage).toBe(45); // 45/100 = 45%
    expect(true).toBe(true);
  });

  it.skip('shows overage when over limit', async () => {
    // server.use(
    //   http.get('http://localhost:8000/api/billing/usage', () => {
    //     return HttpResponse.json({
    //       ...mockUsage,
    //       secured_retrievals: {
    //         used: 150,
    //         limit: 100,
    //         overage: 50,
    //       },
    //       estimated_overage_cents: 2500, // $25
    //     });
    //   })
    // );

    // const { result } = renderHook(() => useUsage(), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => {
    //   expect(result.current.isLoading).toBe(false);
    // });

    // expect(result.current.data?.secured_retrievals.overage).toBe(50);
    // expect(result.current.data?.estimated_overage_cents).toBe(2500);
    expect(true).toBe(true);
  });

  it.skip('requires authentication', async () => {
    // server.use(
    //   http.get('http://localhost:8000/api/billing/usage', () => {
    //     return HttpResponse.json(
    //       { error: { code: 'AUTH_TOKEN_INVALID' } },
    //       { status: 401 }
    //     );
    //   })
    // );

    // const { result } = renderHook(() => useUsage(), {
    //   wrapper: createWrapper(false), // No auth
    // });

    // await waitFor(() => {
    //   expect(result.current.isError).toBe(true);
    // });
    expect(true).toBe(true);
  });
});

// ============================================================================
// useInvoices Tests
// ============================================================================

describe('useInvoices', () => {
  it.skip('fetches invoice list', async () => {
    // const { result } = renderHook(() => useInvoices(), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => {
    //   expect(result.current.isLoading).toBe(false);
    // });

    // expect(result.current.data?.data).toHaveLength(2);
    expect(true).toBe(true);
  });

  it.skip('returns invoice details', async () => {
    // const { result } = renderHook(() => useInvoices(), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => {
    //   expect(result.current.isLoading).toBe(false);
    // });

    // const firstInvoice = result.current.data?.data[0];
    // expect(firstInvoice?.amount_cents).toBe(2900);
    // expect(firstInvoice?.status).toBe('paid');
    // expect(firstInvoice?.pdf_url).toBeDefined();
    expect(true).toBe(true);
  });

  it.skip('supports pagination', async () => {
    // const { result } = renderHook(() => useInvoices({ page: 1, perPage: 10 }), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => {
    //   expect(result.current.isLoading).toBe(false);
    // });

    // expect(result.current.data?.meta.pagination.page).toBe(1);
    expect(true).toBe(true);
  });
});

// ============================================================================
// useCheckout Tests
// ============================================================================

describe('useCheckout', () => {
  it.skip('creates checkout session for Pro plan', async () => {
    // const { result } = renderHook(() => useCheckout(), {
    //   wrapper: createWrapper(),
    // });

    // await act(async () => {
    //   await result.current.mutateAsync({
    //     plan_id: 'pro',
    //     billing_period: 'monthly',
    //   });
    // });

    // expect(result.current.data?.checkout_url).toContain('checkout.stripe.com');
    // expect(result.current.data?.session_id).toBe('cs_test_123');
    expect(true).toBe(true);
  });

  it.skip('creates checkout session for Enterprise plan', async () => {
    // const { result } = renderHook(() => useCheckout(), {
    //   wrapper: createWrapper(),
    // });

    // await act(async () => {
    //   await result.current.mutateAsync({
    //     plan_id: 'enterprise',
    //     billing_period: 'yearly',
    //   });
    // });

    // expect(result.current.data?.checkout_url).toBeDefined();
    expect(true).toBe(true);
  });

  it.skip('rejects invalid plan', async () => {
    // const { result } = renderHook(() => useCheckout(), {
    //   wrapper: createWrapper(),
    // });

    // await expect(
    //   act(async () => {
    //     await result.current.mutateAsync({
    //       plan_id: 'invalid_plan',
    //       billing_period: 'monthly',
    //     });
    //   })
    // ).rejects.toThrow();

    // expect(result.current.error?.code).toBe('BILLING_INVALID_PLAN');
    expect(true).toBe(true);
  });

  it.skip('rejects free plan checkout', async () => {
    // const { result } = renderHook(() => useCheckout(), {
    //   wrapper: createWrapper(),
    // });

    // await expect(
    //   act(async () => {
    //     await result.current.mutateAsync({
    //       plan_id: 'free',
    //       billing_period: 'monthly',
    //     });
    //   })
    // ).rejects.toThrow();
    expect(true).toBe(true);
  });

  it.skip('requires authentication', async () => {
    // const { result } = renderHook(() => useCheckout(), {
    //   wrapper: createWrapper(false),
    // });

    // await expect(
    //   act(async () => {
    //     await result.current.mutateAsync({
    //       plan_id: 'pro',
    //       billing_period: 'monthly',
    //     });
    //   })
    // ).rejects.toThrow();
    expect(true).toBe(true);
  });
});

// ============================================================================
// useBillingPortal Tests
// ============================================================================

describe('useBillingPortal', () => {
  it.skip('creates billing portal session', async () => {
    // const { result } = renderHook(() => useBillingPortal(), {
    //   wrapper: createWrapper(),
    // });

    // await act(async () => {
    //   await result.current.mutateAsync();
    // });

    // expect(result.current.data?.portal_url).toContain('billing.stripe.com');
    expect(true).toBe(true);
  });

  it.skip('accepts return URL', async () => {
    // const { result } = renderHook(() => useBillingPortal(), {
    //   wrapper: createWrapper(),
    // });

    // await act(async () => {
    //   await result.current.mutateAsync({
    //     return_url: 'https://app.gateco.com/settings',
    //   });
    // });

    // expect(result.current.data?.portal_url).toBeDefined();
    expect(true).toBe(true);
  });

  it.skip('requires authentication', async () => {
    // const { result } = renderHook(() => useBillingPortal(), {
    //   wrapper: createWrapper(false),
    // });

    // await expect(
    //   act(async () => {
    //     await result.current.mutateAsync();
    //   })
    // ).rejects.toThrow();
    expect(true).toBe(true);
  });
});

// ============================================================================
// useSubscription Tests
// ============================================================================

describe('useSubscription', () => {
  it.skip('fetches current subscription', async () => {
    // const { result } = renderHook(() => useSubscription(), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => {
    //   expect(result.current.isLoading).toBe(false);
    // });

    // expect(result.current.data?.status).toBe('active');
    // expect(result.current.data?.plan_id).toBe('pro');
    expect(true).toBe(true);
  });

  it.skip('returns null for free plan', async () => {
    // server.use(
    //   http.get('http://localhost:8000/api/billing/subscription', () => {
    //     return HttpResponse.json(null);
    //   })
    // );

    // const { result } = renderHook(() => useSubscription(), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => {
    //   expect(result.current.isLoading).toBe(false);
    // });

    // expect(result.current.data).toBeNull();
    expect(true).toBe(true);
  });

  it.skip('shows cancel at period end status', async () => {
    // server.use(
    //   http.get('http://localhost:8000/api/billing/subscription', () => {
    //     return HttpResponse.json({
    //       ...mockSubscription,
    //       cancel_at_period_end: true,
    //     });
    //   })
    // );

    // const { result } = renderHook(() => useSubscription(), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => {
    //   expect(result.current.isLoading).toBe(false);
    // });

    // expect(result.current.data?.cancel_at_period_end).toBe(true);
    expect(true).toBe(true);
  });

  it.skip('includes helper for checking active status', async () => {
    // const { result } = renderHook(() => useSubscription(), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => {
    //   expect(result.current.isLoading).toBe(false);
    // });

    // expect(result.current.isActive).toBe(true);
    expect(true).toBe(true);
  });
});

// ============================================================================
// Upgrade Flow Integration Tests
// ============================================================================

describe('Upgrade Flow', () => {
  it.skip('complete upgrade flow: select plan -> checkout -> return', async () => {
    // 1. Get plans
    // const { result: plansResult } = renderHook(() => usePlans(), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => expect(plansResult.current.isLoading).toBe(false));

    // // 2. Select Pro plan and start checkout
    // const { result: checkoutResult } = renderHook(() => useCheckout(), {
    //   wrapper: createWrapper(),
    // });

    // await act(async () => {
    //   await checkoutResult.current.mutateAsync({
    //     plan_id: 'pro',
    //     billing_period: 'monthly',
    //   });
    // });

    // // 3. User redirects to Stripe checkout URL
    // expect(checkoutResult.current.data?.checkout_url).toBeDefined();

    // // 4. After returning, subscription should be active
    // // (This would be handled by webhook in real implementation)
    expect(true).toBe(true);
  });
});
