/**
 * Test utilities for React component testing.
 *
 * This module provides wrapper components and helper functions
 * for testing React components with proper provider context.
 */

import React, { ReactElement, ReactNode } from 'react';
import { render, RenderOptions, RenderResult } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';

// ============================================================================
// Query Client Configuration
// ============================================================================

/**
 * Create a test-configured QueryClient.
 *
 * Disables retries and caching for predictable test behavior.
 */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
    logger: {
      log: () => {},
      warn: () => {},
      error: () => {},
    },
  });
}

// ============================================================================
// Provider Wrapper
// ============================================================================

interface AllProvidersProps {
  children: ReactNode;
  queryClient?: QueryClient;
  initialEntries?: string[];
}

/**
 * Wrapper component that provides all necessary context providers.
 */
export function AllProviders({
  children,
  queryClient = createTestQueryClient(),
  initialEntries = ['/'],
}: AllProvidersProps): ReactElement {
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

/**
 * Create a wrapper component with specific configuration.
 */
export function createWrapper(options: Partial<AllProvidersProps> = {}) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <AllProviders {...options}>{children}</AllProviders>;
  };
}

// ============================================================================
// Custom Render Function
// ============================================================================

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient;
  initialEntries?: string[];
}

/**
 * Custom render function that wraps components with all providers.
 *
 * Usage:
 * ```
 * import { renderWithProviders } from '@/tests/utils/test-utils';
 *
 * it('renders component', () => {
 *   const { getByText } = renderWithProviders(<MyComponent />);
 *   expect(getByText('Hello')).toBeInTheDocument();
 * });
 * ```
 */
export function renderWithProviders(
  ui: ReactElement,
  options: CustomRenderOptions = {}
): RenderResult & { queryClient: QueryClient } {
  const { queryClient = createTestQueryClient(), initialEntries, ...renderOptions } = options;

  const Wrapper = ({ children }: { children: ReactNode }) => (
    <AllProviders queryClient={queryClient} initialEntries={initialEntries}>
      {children}
    </AllProviders>
  );

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    queryClient,
  };
}

// ============================================================================
// Hook Testing Utilities
// ============================================================================

/**
 * Create a wrapper for testing hooks with React Query.
 */
export function createHookWrapper(options: Partial<AllProvidersProps> = {}) {
  const queryClient = options.queryClient ?? createTestQueryClient();

  return {
    wrapper: ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
    queryClient,
  };
}

// ============================================================================
// Mock Data Factories
// ============================================================================

/**
 * Create a mock user object.
 */
export function createMockUser(overrides: Partial<MockUser> = {}): MockUser {
  return {
    id: 'user_123',
    email: 'test@example.com',
    name: 'Test User',
    role: 'owner',
    organization: {
      id: 'org_456',
      name: 'Test Organization',
      slug: 'test-org',
      plan: 'free',
    },
    created_at: '2026-02-25T12:00:00Z',
    ...overrides,
  };
}

interface MockUser {
  id: string;
  email: string;
  name: string;
  role: 'owner' | 'admin' | 'member';
  organization: {
    id: string;
    name: string;
    slug: string;
    plan: 'free' | 'pro' | 'enterprise';
  };
  created_at: string;
}

/**
 * Create a mock resource object.
 */
export function createMockResource(overrides: Partial<MockResource> = {}): MockResource {
  return {
    id: 'res_123',
    type: 'link',
    title: 'Test Resource',
    description: 'A test resource',
    content_url: 'https://example.com/content',
    thumbnail_url: null,
    access_rule: {
      type: 'public',
      price_cents: null,
      currency: null,
      allowed_emails: null,
    },
    stats: {
      view_count: 0,
      unique_viewers: 0,
      revenue_cents: 0,
    },
    created_at: '2026-02-25T12:00:00Z',
    updated_at: '2026-02-25T12:00:00Z',
    ...overrides,
  };
}

interface MockResource {
  id: string;
  type: 'link' | 'file' | 'video';
  title: string;
  description: string | null;
  content_url: string;
  thumbnail_url: string | null;
  access_rule: {
    type: 'public' | 'paid' | 'invite_only';
    price_cents: number | null;
    currency: string | null;
    allowed_emails: string[] | null;
  };
  stats: {
    view_count: number;
    unique_viewers: number;
    revenue_cents: number;
  };
  created_at: string;
  updated_at: string;
}

/**
 * Create mock tokens.
 */
export function createMockTokens(): MockTokens {
  return {
    access_token: 'mock_access_token_123',
    refresh_token: 'mock_refresh_token_456',
    token_type: 'Bearer',
    expires_in: 900,
  };
}

interface MockTokens {
  access_token: string;
  refresh_token: string;
  token_type: 'Bearer';
  expires_in: number;
}

// ============================================================================
// Wait Utilities
// ============================================================================

/**
 * Wait for a condition to be true.
 */
export async function waitForCondition(
  condition: () => boolean,
  timeout = 5000,
  interval = 50
): Promise<void> {
  const startTime = Date.now();

  return new Promise((resolve, reject) => {
    const check = () => {
      if (condition()) {
        resolve();
      } else if (Date.now() - startTime > timeout) {
        reject(new Error('Timeout waiting for condition'));
      } else {
        setTimeout(check, interval);
      }
    };
    check();
  });
}

/**
 * Wait for a specified number of milliseconds.
 */
export function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ============================================================================
// Re-exports
// ============================================================================

// Re-export everything from testing-library for convenience
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';
