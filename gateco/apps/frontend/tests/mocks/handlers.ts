/**
 * MSW (Mock Service Worker) handlers for API mocking.
 *
 * These handlers intercept network requests during testing and return
 * mock responses, enabling isolated frontend testing without a backend.
 */

import { http, HttpResponse } from 'msw';

const API_BASE = 'http://localhost:8000/api';

// ============================================================================
// Test Data
// ============================================================================

export const mockUser = {
  id: 'user_123',
  email: 'test@example.com',
  name: 'Test User',
  role: 'owner' as const,
  organization: {
    id: 'org_456',
    name: 'Test Organization',
    slug: 'test-org',
    plan: 'free' as const,
  },
  created_at: '2026-02-25T12:00:00Z',
};

export const mockTokens = {
  access_token: 'mock_access_token_123',
  refresh_token: 'mock_refresh_token_456',
  token_type: 'Bearer' as const,
  expires_in: 900,
};

export const mockPlans = [
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

export const mockResources = [
  {
    id: 'res_1',
    type: 'link',
    title: 'Test Link Resource',
    description: 'A test link resource',
    content_url: 'https://example.com/content',
    thumbnail_url: null,
    access_rule: {
      type: 'public',
      price_cents: null,
      currency: null,
      allowed_emails: null,
    },
    stats: {
      view_count: 150,
      unique_viewers: 100,
      revenue_cents: 0,
    },
    created_at: '2026-02-20T12:00:00Z',
    updated_at: '2026-02-25T12:00:00Z',
  },
  {
    id: 'res_2',
    type: 'file',
    title: 'Test Paid Resource',
    description: 'A paid file resource',
    content_url: 'https://example.com/file.pdf',
    thumbnail_url: 'https://example.com/thumb.jpg',
    access_rule: {
      type: 'paid',
      price_cents: 999,
      currency: 'USD',
      allowed_emails: null,
    },
    stats: {
      view_count: 50,
      unique_viewers: 30,
      revenue_cents: 9990,
    },
    created_at: '2026-02-15T12:00:00Z',
    updated_at: '2026-02-24T12:00:00Z',
  },
];

export const mockUsage = {
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

// ============================================================================
// Auth Handlers
// ============================================================================

export const authHandlers = [
  // Signup
  http.post(`${API_BASE}/auth/signup`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;

    // Validate required fields
    if (!body.email || !body.password || !body.name || !body.organization_name) {
      return HttpResponse.json(
        {
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Missing required fields',
            details: {},
            request_id: 'test_req_123',
          },
        },
        { status: 422 }
      );
    }

    // Check for duplicate email
    if (body.email === 'existing@example.com') {
      return HttpResponse.json(
        {
          error: {
            code: 'AUTH_EMAIL_EXISTS',
            message: 'Email already registered',
            request_id: 'test_req_123',
          },
        },
        { status: 409 }
      );
    }

    // Validate email format
    if (typeof body.email === 'string' && !body.email.includes('@')) {
      return HttpResponse.json(
        {
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid email format',
            details: { email: ['Invalid email address'] },
            request_id: 'test_req_123',
          },
        },
        { status: 422 }
      );
    }

    // Validate password length
    if (typeof body.password === 'string' && body.password.length < 8) {
      return HttpResponse.json(
        {
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Password too short',
            details: { password: ['Password must be at least 8 characters'] },
            request_id: 'test_req_123',
          },
        },
        { status: 422 }
      );
    }

    return HttpResponse.json(
      {
        user: {
          ...mockUser,
          email: body.email as string,
          name: body.name as string,
          organization: {
            ...mockUser.organization,
            name: body.organization_name as string,
          },
        },
        tokens: mockTokens,
      },
      { status: 201 }
    );
  }),

  // Login
  http.post(`${API_BASE}/auth/login`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;

    // Validate required fields
    if (!body.email || !body.password) {
      return HttpResponse.json(
        {
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Missing required fields',
            request_id: 'test_req_123',
          },
        },
        { status: 422 }
      );
    }

    // Simulate successful login
    if (body.email === 'test@example.com' && body.password === 'password123') {
      return HttpResponse.json({
        user: mockUser,
        tokens: mockTokens,
      });
    }

    // Simulate invalid credentials
    return HttpResponse.json(
      {
        error: {
          code: 'AUTH_INVALID_CREDENTIALS',
          message: 'Invalid email or password',
          request_id: 'test_req_123',
        },
      },
      { status: 401 }
    );
  }),

  // Refresh token
  http.post(`${API_BASE}/auth/refresh`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;

    if (!body.refresh_token) {
      return HttpResponse.json(
        {
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Refresh token required',
            request_id: 'test_req_123',
          },
        },
        { status: 422 }
      );
    }

    if (body.refresh_token === 'invalid_token') {
      return HttpResponse.json(
        {
          error: {
            code: 'AUTH_INVALID_REFRESH_TOKEN',
            message: 'Invalid refresh token',
            request_id: 'test_req_123',
          },
        },
        { status: 401 }
      );
    }

    return HttpResponse.json({
      access_token: 'new_access_token_789',
      refresh_token: 'new_refresh_token_012',
      token_type: 'Bearer',
      expires_in: 900,
    });
  }),

  // Logout
  http.post(`${API_BASE}/auth/logout`, () => {
    return new HttpResponse(null, { status: 204 });
  }),
];

// ============================================================================
// User Handlers
// ============================================================================

export const userHandlers = [
  // Get current user
  http.get(`${API_BASE}/users/me`, ({ request }) => {
    const authHeader = request.headers.get('Authorization');

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return HttpResponse.json(
        {
          error: {
            code: 'AUTH_TOKEN_INVALID',
            message: 'Missing or invalid token',
            request_id: 'test_req_123',
          },
        },
        { status: 401 }
      );
    }

    return HttpResponse.json(mockUser);
  }),

  // Update current user
  http.patch(`${API_BASE}/users/me`, async ({ request }) => {
    const authHeader = request.headers.get('Authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: { code: 'AUTH_TOKEN_INVALID', message: 'Unauthorized' } },
        { status: 401 }
      );
    }

    const body = await request.json() as Record<string, unknown>;

    return HttpResponse.json({
      ...mockUser,
      name: (body.name as string) || mockUser.name,
    });
  }),
];

// ============================================================================
// Resource Handlers
// ============================================================================

export const resourceHandlers = [
  // List resources
  http.get(`${API_BASE}/resources`, ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const perPage = parseInt(url.searchParams.get('per_page') || '20');
    const type = url.searchParams.get('type');

    let resources = [...mockResources];

    if (type) {
      resources = resources.filter((r) => r.type === type);
    }

    return HttpResponse.json({
      data: resources,
      meta: {
        pagination: {
          page,
          per_page: perPage,
          total: resources.length,
          total_pages: 1,
        },
      },
    });
  }),

  // Get single resource
  http.get(`${API_BASE}/resources/:id`, ({ params }) => {
    const resource = mockResources.find((r) => r.id === params.id);

    if (!resource) {
      return HttpResponse.json(
        {
          error: {
            code: 'RESOURCE_NOT_FOUND',
            message: 'Resource not found',
            request_id: 'test_req_123',
          },
        },
        { status: 404 }
      );
    }

    return HttpResponse.json(resource);
  }),

  // Create resource
  http.post(`${API_BASE}/resources`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;

    if (!body.title || !body.type || !body.content_url) {
      return HttpResponse.json(
        {
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Missing required fields',
            request_id: 'test_req_123',
          },
        },
        { status: 422 }
      );
    }

    return HttpResponse.json(
      {
        id: 'res_new',
        ...body,
        stats: { view_count: 0, unique_viewers: 0, revenue_cents: 0 },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      { status: 201 }
    );
  }),

  // Update resource
  http.patch(`${API_BASE}/resources/:id`, async ({ params, request }) => {
    const resource = mockResources.find((r) => r.id === params.id);

    if (!resource) {
      return HttpResponse.json(
        { error: { code: 'RESOURCE_NOT_FOUND', message: 'Resource not found' } },
        { status: 404 }
      );
    }

    const body = await request.json() as Record<string, unknown>;

    return HttpResponse.json({
      ...resource,
      ...body,
      updated_at: new Date().toISOString(),
    });
  }),

  // Delete resource
  http.delete(`${API_BASE}/resources/:id`, ({ params }) => {
    const resource = mockResources.find((r) => r.id === params.id);

    if (!resource) {
      return HttpResponse.json(
        { error: { code: 'RESOURCE_NOT_FOUND', message: 'Resource not found' } },
        { status: 404 }
      );
    }

    return new HttpResponse(null, { status: 204 });
  }),
];

// ============================================================================
// Billing Handlers
// ============================================================================

export const billingHandlers = [
  // Get plans
  http.get(`${API_BASE}/plans`, () => {
    return HttpResponse.json({ plans: mockPlans });
  }),

  // Start checkout
  http.post(`${API_BASE}/checkout/start`, async ({ request }) => {
    const authHeader = request.headers.get('Authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: { code: 'AUTH_TOKEN_INVALID', message: 'Unauthorized' } },
        { status: 401 }
      );
    }

    const body = await request.json() as Record<string, unknown>;

    if (!mockPlans.find((p) => p.id === body.plan_id)) {
      return HttpResponse.json(
        {
          error: {
            code: 'BILLING_INVALID_PLAN',
            message: 'Invalid plan',
            request_id: 'test_req_123',
          },
        },
        { status: 400 }
      );
    }

    return HttpResponse.json({
      checkout_url: 'https://checkout.stripe.com/pay/cs_test_123',
      session_id: 'cs_test_123',
    });
  }),

  // Get usage
  http.get(`${API_BASE}/billing/usage`, ({ request }) => {
    const authHeader = request.headers.get('Authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: { code: 'AUTH_TOKEN_INVALID', message: 'Unauthorized' } },
        { status: 401 }
      );
    }

    return HttpResponse.json(mockUsage);
  }),

  // Get invoices
  http.get(`${API_BASE}/billing/invoices`, ({ request }) => {
    const authHeader = request.headers.get('Authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: { code: 'AUTH_TOKEN_INVALID', message: 'Unauthorized' } },
        { status: 401 }
      );
    }

    return HttpResponse.json({
      data: [
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
      ],
      meta: {
        pagination: { page: 1, per_page: 20, total: 1, total_pages: 1 },
      },
    });
  }),

  // Create billing portal session
  http.post(`${API_BASE}/billing/portal`, ({ request }) => {
    const authHeader = request.headers.get('Authorization');

    if (!authHeader) {
      return HttpResponse.json(
        { error: { code: 'AUTH_TOKEN_INVALID', message: 'Unauthorized' } },
        { status: 401 }
      );
    }

    return HttpResponse.json({
      portal_url: 'https://billing.stripe.com/session/bps_test_123',
    });
  }),
];

// ============================================================================
// All Handlers
// ============================================================================

export const handlers = [
  ...authHandlers,
  ...userHandlers,
  ...resourceHandlers,
  ...billingHandlers,
];
