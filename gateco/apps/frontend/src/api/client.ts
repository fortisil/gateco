import { ApiRequestError } from '@/types/api';

const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api';

const LOG_PREFIX = '[Gateco API]';

function getAccessToken(): string | null {
  return localStorage.getItem('access_token');
}

async function handleResponse<T>(response: Response, method: string, path: string): Promise<T> {
  console.log(`${LOG_PREFIX} ${method} ${path} → ${response.status}`);

  if (response.status === 204) {
    return undefined as T;
  }

  const data = await response.json();

  if (!response.ok) {
    console.error(`${LOG_PREFIX} ${method} ${path} error:`, data);
    if (data.error) {
      throw new ApiRequestError(data.error, response.status);
    }
    throw new ApiRequestError(
      { code: 'UNKNOWN_ERROR', message: 'An unexpected error occurred' },
      response.status
    );
  }

  return data as T;
}

function buildHeaders(authenticated = true): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (authenticated) {
    const token = getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  return headers;
}

export async function apiGet<T>(
  path: string,
  params?: Record<string, string | number | undefined>,
  authenticated = true
): Promise<T> {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    });
  }

  console.log(`${LOG_PREFIX} GET ${path}`);
  try {
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: buildHeaders(authenticated),
    });
    return handleResponse<T>(response, 'GET', path);
  } catch (err) {
    console.error(`${LOG_PREFIX} GET ${path} network error:`, err);
    throw err;
  }
}

export async function apiPost<T>(
  path: string,
  body?: unknown,
  authenticated = true
): Promise<T> {
  console.log(`${LOG_PREFIX} POST ${path}`, body ? JSON.stringify(body).substring(0, 200) : '');
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: buildHeaders(authenticated),
      body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(response, 'POST', path);
  } catch (err) {
    console.error(`${LOG_PREFIX} POST ${path} network error:`, err);
    throw err;
  }
}

export async function apiPatch<T>(
  path: string,
  body: unknown,
  authenticated = true
): Promise<T> {
  console.log(`${LOG_PREFIX} PATCH ${path}`);
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'PATCH',
      headers: buildHeaders(authenticated),
      body: JSON.stringify(body),
    });
    return handleResponse<T>(response, 'PATCH', path);
  } catch (err) {
    console.error(`${LOG_PREFIX} PATCH ${path} network error:`, err);
    throw err;
  }
}

export async function apiDelete<T = void>(
  path: string,
  authenticated = true
): Promise<T> {
  console.log(`${LOG_PREFIX} DELETE ${path}`);
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'DELETE',
      headers: buildHeaders(authenticated),
    });
    return handleResponse<T>(response, 'DELETE', path);
  } catch (err) {
    console.error(`${LOG_PREFIX} DELETE ${path} network error:`, err);
    throw err;
  }
}
