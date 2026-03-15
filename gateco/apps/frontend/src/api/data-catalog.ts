import { apiGet, apiPatch } from './client';
import type { GatedResource, GatedResourceDetail, PaginatedResponse } from '@/types/gated-resource';

export interface DataCatalogFilters {
  classification?: string;
  sensitivity?: string;
  domain?: string;
  label?: string;
  source_connector_id?: string;
  page?: number;
  per_page?: number;
}

export function getDataCatalog(filters?: DataCatalogFilters): Promise<PaginatedResponse<GatedResource>> {
  return apiGet<PaginatedResponse<GatedResource>>('/data-catalog', filters as Record<string, string | number | undefined>);
}

export function getDataCatalogItem(id: string): Promise<GatedResourceDetail> {
  return apiGet<GatedResourceDetail>(`/data-catalog/${id}`);
}

export function updateDataCatalogItem(id: string, data: Partial<Pick<GatedResource, 'classification' | 'sensitivity' | 'labels'>>): Promise<GatedResource> {
  return apiPatch<GatedResource>(`/data-catalog/${id}`, data);
}
