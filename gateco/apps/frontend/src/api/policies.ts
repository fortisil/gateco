import { apiGet, apiPost, apiPatch, apiDelete } from './client';
import type { Policy } from '@/types/policy';

export interface CreatePolicyRequest {
  name: string;
  description: string;
  type: Policy['type'];
  effect: Policy['effect'];
  rules: Policy['rules'];
  resource_selectors: string[];
}

export async function getPolicies(): Promise<Policy[]> {
  const res = await apiGet<{ data: Policy[] }>('/policies');
  return res.data;
}

export function getPolicy(id: string): Promise<Policy> {
  return apiGet<Policy>(`/policies/${id}`);
}

export function createPolicy(data: CreatePolicyRequest): Promise<Policy> {
  return apiPost<Policy>('/policies', data);
}

export function updatePolicy(id: string, data: Partial<CreatePolicyRequest>): Promise<Policy> {
  return apiPatch<Policy>(`/policies/${id}`, data);
}

export function deletePolicy(id: string): Promise<void> {
  return apiDelete(`/policies/${id}`);
}

export function activatePolicy(id: string): Promise<Policy> {
  return apiPost<Policy>(`/policies/${id}/activate`);
}

export function archivePolicy(id: string): Promise<Policy> {
  return apiPost<Policy>(`/policies/${id}/archive`);
}
