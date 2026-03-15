import { apiGet, apiPost, apiPatch, apiDelete } from './client';
import type { IdentityProvider, CreateIdentityProviderRequest } from '@/types/identity-provider';

export async function getIdentityProviders(): Promise<IdentityProvider[]> {
  const res = await apiGet<{ data: IdentityProvider[] }>('/identity-providers');
  return res.data;
}

export function getIdentityProvider(id: string): Promise<IdentityProvider> {
  return apiGet<IdentityProvider>(`/identity-providers/${id}`);
}

export function createIdentityProvider(data: CreateIdentityProviderRequest): Promise<IdentityProvider> {
  return apiPost<IdentityProvider>('/identity-providers', data);
}

export function syncIdentityProvider(id: string): Promise<{ message: string }> {
  return apiPost<{ message: string }>(`/identity-providers/${id}/sync`);
}

export function updateIdentityProvider(id: string, data: Partial<CreateIdentityProviderRequest>): Promise<IdentityProvider> {
  return apiPatch<IdentityProvider>(`/identity-providers/${id}`, data);
}

export function deleteIdentityProvider(id: string): Promise<void> {
  return apiDelete(`/identity-providers/${id}`);
}
