/**
 * Tests for useResources hooks.
 *
 * These tests verify the resource management hooks work correctly,
 * including listing, fetching, creating, updating, and deleting resources.
 *
 * Hook location: apps/frontend/src/hooks/useResources.ts
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
//   useResources,
//   useResource,
//   useCreateResource,
//   useUpdateResource,
//   useDeleteResource,
// } from '@/hooks/useResources';

// Mock data
const mockResources = [
  {
    id: 'res_1',
    type: 'link',
    title: 'Test Link Resource',
    description: 'A test link resource',
    content_url: 'https://example.com/content',
    access_rule: { type: 'public', price_cents: null },
    stats: { view_count: 100, unique_viewers: 50, revenue_cents: 0 },
    created_at: '2026-02-20T12:00:00Z',
  },
  {
    id: 'res_2',
    type: 'file',
    title: 'Test File Resource',
    description: 'A test file resource',
    content_url: 'https://example.com/file.pdf',
    access_rule: { type: 'paid', price_cents: 999 },
    stats: { view_count: 50, unique_viewers: 30, revenue_cents: 4995 },
    created_at: '2026-02-15T12:00:00Z',
  },
];

// MSW Server setup
const server = setupServer(
  // List resources
  http.get('http://localhost:8000/api/resources', ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const perPage = parseInt(url.searchParams.get('per_page') || '20');
    const type = url.searchParams.get('type');

    let filtered = [...mockResources];
    if (type) {
      filtered = filtered.filter(r => r.type === type);
    }

    return HttpResponse.json({
      data: filtered,
      meta: {
        pagination: {
          page,
          per_page: perPage,
          total: filtered.length,
          total_pages: 1,
        },
      },
    });
  }),

  // Get single resource
  http.get('http://localhost:8000/api/resources/:id', ({ params }) => {
    const resource = mockResources.find(r => r.id === params.id);
    if (!resource) {
      return HttpResponse.json(
        { error: { code: 'RESOURCE_NOT_FOUND', message: 'Not found' } },
        { status: 404 }
      );
    }
    return HttpResponse.json(resource);
  }),

  // Create resource
  http.post('http://localhost:8000/api/resources', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json(
      {
        id: 'res_new',
        ...body,
        stats: { view_count: 0, unique_viewers: 0, revenue_cents: 0 },
        created_at: new Date().toISOString(),
      },
      { status: 201 }
    );
  }),

  // Update resource
  http.patch('http://localhost:8000/api/resources/:id', async ({ params, request }) => {
    const resource = mockResources.find(r => r.id === params.id);
    if (!resource) {
      return HttpResponse.json(
        { error: { code: 'RESOURCE_NOT_FOUND', message: 'Not found' } },
        { status: 404 }
      );
    }
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...resource, ...body });
  }),

  // Delete resource
  http.delete('http://localhost:8000/api/resources/:id', ({ params }) => {
    const resource = mockResources.find(r => r.id === params.id);
    if (!resource) {
      return HttpResponse.json(
        { error: { code: 'RESOURCE_NOT_FOUND', message: 'Not found' } },
        { status: 404 }
      );
    }
    return new HttpResponse(null, { status: 204 });
  })
);

// Test wrapper
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

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
});

// Close server after all tests
afterEach(() => {
  server.close();
});

// ============================================================================
// useResources Tests
// ============================================================================

describe('useResources', () => {
  describe('Listing', () => {
    it.skip('fetches resources for organization', async () => {
      // const { result } = renderHook(() => useResources(), {
      //   wrapper: createWrapper(),
      // });

      // await waitFor(() => {
      //   expect(result.current.isLoading).toBe(false);
      // });

      // expect(result.current.data?.data).toHaveLength(2);
      // expect(result.current.data?.data[0].title).toBe('Test Link Resource');
      expect(true).toBe(true);
    });

    it.skip('supports pagination', async () => {
      // const { result } = renderHook(
      //   () => useResources({ page: 1, perPage: 10 }),
      //   { wrapper: createWrapper() }
      // );

      // await waitFor(() => {
      //   expect(result.current.isLoading).toBe(false);
      // });

      // expect(result.current.data?.meta.pagination.page).toBe(1);
      // expect(result.current.data?.meta.pagination.per_page).toBe(10);
      expect(true).toBe(true);
    });

    it.skip('supports type filtering', async () => {
      // const { result } = renderHook(
      //   () => useResources({ type: 'link' }),
      //   { wrapper: createWrapper() }
      // );

      // await waitFor(() => {
      //   expect(result.current.isLoading).toBe(false);
      // });

      // expect(result.current.data?.data.every(r => r.type === 'link')).toBe(true);
      expect(true).toBe(true);
    });

    it.skip('supports search', async () => {
      // const { result } = renderHook(
      //   () => useResources({ search: 'test' }),
      //   { wrapper: createWrapper() }
      // );

      // await waitFor(() => {
      //   expect(result.current.isLoading).toBe(false);
      // });

      // // Results should match search query
      // expect(result.current.data?.data.length).toBeGreaterThan(0);
      expect(true).toBe(true);
    });

    it.skip('returns loading state', () => {
      // const { result } = renderHook(() => useResources(), {
      //   wrapper: createWrapper(),
      // });

      // expect(result.current.isLoading).toBe(true);
      expect(true).toBe(true);
    });

    it.skip('returns error on failure', async () => {
      // server.use(
      //   http.get('http://localhost:8000/api/resources', () => {
      //     return HttpResponse.json(
      //       { error: { code: 'INTERNAL_ERROR', message: 'Server error' } },
      //       { status: 500 }
      //     );
      //   })
      // );

      // const { result } = renderHook(() => useResources(), {
      //   wrapper: createWrapper(),
      // });

      // await waitFor(() => {
      //   expect(result.current.isError).toBe(true);
      // });

      // expect(result.current.error).toBeDefined();
      expect(true).toBe(true);
    });
  });
});

// ============================================================================
// useResource Tests
// ============================================================================

describe('useResource', () => {
  it.skip('fetches single resource by ID', async () => {
    // const { result } = renderHook(() => useResource('res_1'), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => {
    //   expect(result.current.isLoading).toBe(false);
    // });

    // expect(result.current.data?.id).toBe('res_1');
    // expect(result.current.data?.title).toBe('Test Link Resource');
    expect(true).toBe(true);
  });

  it.skip('returns 404 error for non-existent', async () => {
    // const { result } = renderHook(() => useResource('nonexistent'), {
    //   wrapper: createWrapper(),
    // });

    // await waitFor(() => {
    //   expect(result.current.isError).toBe(true);
    // });

    // expect(result.current.error?.code).toBe('RESOURCE_NOT_FOUND');
    expect(true).toBe(true);
  });

  it.skip('does not fetch when ID is undefined', () => {
    // const { result } = renderHook(() => useResource(undefined), {
    //   wrapper: createWrapper(),
    // });

    // expect(result.current.isLoading).toBe(false);
    // expect(result.current.data).toBeUndefined();
    expect(true).toBe(true);
  });
});

// ============================================================================
// useCreateResource Tests
// ============================================================================

describe('useCreateResource', () => {
  it.skip('creates resource on mutation', async () => {
    // const { result } = renderHook(() => useCreateResource(), {
    //   wrapper: createWrapper(),
    // });

    // await act(async () => {
    //   await result.current.mutateAsync({
    //     type: 'link',
    //     title: 'New Resource',
    //     content_url: 'https://example.com/new',
    //     access_rule: { type: 'public' },
    //   });
    // });

    // expect(result.current.data?.id).toBe('res_new');
    // expect(result.current.data?.title).toBe('New Resource');
    expect(true).toBe(true);
  });

  it.skip('invalidates resource list cache on success', async () => {
    // const queryClient = new QueryClient({
    //   defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    // });

    // const wrapper = ({ children }: { children: ReactNode }) => (
    //   <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    // );

    // // First, populate the cache
    // const { result: listResult } = renderHook(() => useResources(), { wrapper });
    // await waitFor(() => expect(listResult.current.isLoading).toBe(false));

    // // Create a new resource
    // const { result: createResult } = renderHook(() => useCreateResource(), { wrapper });

    // await act(async () => {
    //   await createResult.current.mutateAsync({
    //     type: 'link',
    //     title: 'New',
    //     content_url: 'https://example.com',
    //     access_rule: { type: 'public' },
    //   });
    // });

    // // Cache should be invalidated
    // expect(queryClient.getQueryState(['resources'])?.isInvalidated).toBe(true);
    expect(true).toBe(true);
  });

  it.skip('returns error on validation failure', async () => {
    // server.use(
    //   http.post('http://localhost:8000/api/resources', () => {
    //     return HttpResponse.json(
    //       { error: { code: 'VALIDATION_ERROR', message: 'Invalid data' } },
    //       { status: 422 }
    //     );
    //   })
    // );

    // const { result } = renderHook(() => useCreateResource(), {
    //   wrapper: createWrapper(),
    // });

    // await expect(
    //   act(async () => {
    //     await result.current.mutateAsync({
    //       type: 'link',
    //       title: '', // Invalid - empty
    //       content_url: 'not-a-url',
    //       access_rule: { type: 'public' },
    //     });
    //   })
    // ).rejects.toThrow();

    // expect(result.current.error).toBeDefined();
    expect(true).toBe(true);
  });

  it.skip('returns error on limit exceeded', async () => {
    // server.use(
    //   http.post('http://localhost:8000/api/resources', () => {
    //     return HttpResponse.json(
    //       { error: { code: 'RESOURCE_LIMIT_EXCEEDED', message: 'Plan limit reached' } },
    //       { status: 403 }
    //     );
    //   })
    // );

    // const { result } = renderHook(() => useCreateResource(), {
    //   wrapper: createWrapper(),
    // });

    // await expect(
    //   act(async () => {
    //     await result.current.mutateAsync({
    //       type: 'link',
    //       title: 'Fourth Resource',
    //       content_url: 'https://example.com',
    //       access_rule: { type: 'public' },
    //     });
    //   })
    // ).rejects.toThrow();

    // expect(result.current.error?.code).toBe('RESOURCE_LIMIT_EXCEEDED');
    expect(true).toBe(true);
  });
});

// ============================================================================
// useUpdateResource Tests
// ============================================================================

describe('useUpdateResource', () => {
  it.skip('updates resource on mutation', async () => {
    // const { result } = renderHook(() => useUpdateResource(), {
    //   wrapper: createWrapper(),
    // });

    // await act(async () => {
    //   await result.current.mutateAsync({
    //     id: 'res_1',
    //     title: 'Updated Title',
    //   });
    // });

    // expect(result.current.data?.title).toBe('Updated Title');
    expect(true).toBe(true);
  });

  it.skip('invalidates caches on success', async () => {
    // const queryClient = new QueryClient({
    //   defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    // });

    // const wrapper = ({ children }: { children: ReactNode }) => (
    //   <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    // );

    // // Populate caches
    // const { result: listResult } = renderHook(() => useResources(), { wrapper });
    // const { result: detailResult } = renderHook(() => useResource('res_1'), { wrapper });

    // await waitFor(() => {
    //   expect(listResult.current.isLoading).toBe(false);
    //   expect(detailResult.current.isLoading).toBe(false);
    // });

    // // Update
    // const { result: updateResult } = renderHook(() => useUpdateResource(), { wrapper });

    // await act(async () => {
    //   await updateResult.current.mutateAsync({ id: 'res_1', title: 'New' });
    // });

    // // Both caches should be invalidated
    // expect(queryClient.getQueryState(['resources'])?.isInvalidated).toBe(true);
    // expect(queryClient.getQueryState(['resource', 'res_1'])?.isInvalidated).toBe(true);
    expect(true).toBe(true);
  });

  it.skip('returns error on not found', async () => {
    // const { result } = renderHook(() => useUpdateResource(), {
    //   wrapper: createWrapper(),
    // });

    // await expect(
    //   act(async () => {
    //     await result.current.mutateAsync({
    //       id: 'nonexistent',
    //       title: 'Updated',
    //     });
    //   })
    // ).rejects.toThrow();

    // expect(result.current.error?.code).toBe('RESOURCE_NOT_FOUND');
    expect(true).toBe(true);
  });
});

// ============================================================================
// useDeleteResource Tests
// ============================================================================

describe('useDeleteResource', () => {
  it.skip('deletes resource on mutation', async () => {
    // const { result } = renderHook(() => useDeleteResource(), {
    //   wrapper: createWrapper(),
    // });

    // await act(async () => {
    //   await result.current.mutateAsync('res_1');
    // });

    // expect(result.current.isSuccess).toBe(true);
    expect(true).toBe(true);
  });

  it.skip('invalidates resource list cache', async () => {
    // const queryClient = new QueryClient({
    //   defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    // });

    // const wrapper = ({ children }: { children: ReactNode }) => (
    //   <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    // );

    // // Populate cache
    // const { result: listResult } = renderHook(() => useResources(), { wrapper });
    // await waitFor(() => expect(listResult.current.isLoading).toBe(false));

    // // Delete
    // const { result: deleteResult } = renderHook(() => useDeleteResource(), { wrapper });

    // await act(async () => {
    //   await deleteResult.current.mutateAsync('res_1');
    // });

    // expect(queryClient.getQueryState(['resources'])?.isInvalidated).toBe(true);
    expect(true).toBe(true);
  });

  it.skip('returns error on not found', async () => {
    // const { result } = renderHook(() => useDeleteResource(), {
    //   wrapper: createWrapper(),
    // });

    // await expect(
    //   act(async () => {
    //     await result.current.mutateAsync('nonexistent');
    //   })
    // ).rejects.toThrow();
    expect(true).toBe(true);
  });
});

// ============================================================================
// useVerifyAccess Tests
// ============================================================================

describe('useVerifyAccess', () => {
  it.skip('verifies public resource access', async () => {
    // const { result } = renderHook(() => useVerifyAccess(), {
    //   wrapper: createWrapper(),
    // });

    // await act(async () => {
    //   await result.current.mutateAsync({ resourceId: 'res_1' });
    // });

    // expect(result.current.data?.has_access).toBe(true);
    // expect(result.current.data?.content_url).toBeDefined();
    expect(true).toBe(true);
  });

  it.skip('returns payment URL for paid resource', async () => {
    // server.use(
    //   http.post('http://localhost:8000/api/resources/:id/verify', () => {
    //     return HttpResponse.json({
    //       has_access: false,
    //       gate_type: 'payment',
    //       payment_url: 'https://checkout.stripe.com/test',
    //     });
    //   })
    // );

    // const { result } = renderHook(() => useVerifyAccess(), {
    //   wrapper: createWrapper(),
    // });

    // await act(async () => {
    //   await result.current.mutateAsync({ resourceId: 'res_2' });
    // });

    // expect(result.current.data?.has_access).toBe(false);
    // expect(result.current.data?.payment_url).toBeDefined();
    expect(true).toBe(true);
  });

  it.skip('verifies invite-only with email', async () => {
    // server.use(
    //   http.post('http://localhost:8000/api/resources/:id/verify', async ({ request }) => {
    //     const body = await request.json();
    //     if (body.email === 'allowed@example.com') {
    //       return HttpResponse.json({ has_access: true, content_url: 'https://...' });
    //     }
    //     return HttpResponse.json({ has_access: false, gate_type: 'email' });
    //   })
    // );

    // const { result } = renderHook(() => useVerifyAccess(), {
    //   wrapper: createWrapper(),
    // });

    // await act(async () => {
    //   await result.current.mutateAsync({
    //     resourceId: 'res_1',
    //     email: 'allowed@example.com',
    //   });
    // });

    // expect(result.current.data?.has_access).toBe(true);
    expect(true).toBe(true);
  });
});
