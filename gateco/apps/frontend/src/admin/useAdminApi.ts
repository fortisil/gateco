/**
 * Custom hook for admin API calls with token authentication.
 */

interface ApiOptions {
  method?: string;
  body?: unknown;
}

interface ApiResult<T = unknown> {
  data: T | null;
  error: string | null;
}

export function useAdminApi() {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const adminToken = import.meta.env.VITE_ADMIN_TOKEN || '';

  async function callApi<T = unknown>(
    path: string,
    options: ApiOptions = {}
  ): Promise<ApiResult<T>> {
    const { method = 'GET', body } = options;
    try {
      const response = await fetch(`${apiUrl}${path}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': adminToken,
        },
        body: body ? JSON.stringify(body) : undefined,
      });

      if (!response.ok) {
        const text = await response.text();
        return { data: null, error: text || `HTTP ${response.status}` };
      }

      const data = (await response.json()) as T;
      return { data, error: null };
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      return { data: null, error: message };
    }
  }

  return { callApi };
}
