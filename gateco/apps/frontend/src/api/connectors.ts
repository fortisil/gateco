import { apiGet, apiPost, apiPatch, apiDelete } from './client';
import type {
  VectorDBConnector,
  CreateConnectorRequest,
  TestConnectorResponse,
  SearchConfig,
  IngestionConfig,
  ClassificationSuggestion,
  SuggestClassificationsResponse,
  ApplySuggestionsResponse,
} from '@/types/connector';
import type { BindingEntry, BindResult, CoverageDetail } from '@/types/binding';

export async function getConnectors(): Promise<VectorDBConnector[]> {
  const res = await apiGet<{ data: VectorDBConnector[] }>('/connectors');
  return res.data;
}

export function getConnector(id: string): Promise<VectorDBConnector> {
  return apiGet<VectorDBConnector>(`/connectors/${id}`);
}

export function createConnector(data: CreateConnectorRequest): Promise<VectorDBConnector> {
  return apiPost<VectorDBConnector>('/connectors', data);
}

export function testConnector(id: string): Promise<TestConnectorResponse> {
  return apiPost<TestConnectorResponse>(`/connectors/${id}/test`);
}

export function updateConnector(id: string, data: Partial<CreateConnectorRequest>): Promise<VectorDBConnector> {
  return apiPatch<VectorDBConnector>(`/connectors/${id}`, data);
}

export function deleteConnector(id: string): Promise<void> {
  return apiDelete(`/connectors/${id}`);
}

export function getSearchConfig(id: string): Promise<{ search_config: SearchConfig | null }> {
  return apiGet<{ search_config: SearchConfig | null }>(`/connectors/${id}/search-config`);
}

export function updateSearchConfig(id: string, search_config: SearchConfig): Promise<VectorDBConnector> {
  return apiPatch<VectorDBConnector>(`/connectors/${id}/search-config`, { search_config });
}

export function bindMetadata(connectorId: string, bindings: BindingEntry[]): Promise<BindResult> {
  return apiPost<BindResult>(`/connectors/${connectorId}/bind`, { bindings });
}

export function getConnectorCoverage(connectorId: string): Promise<CoverageDetail> {
  return apiGet<CoverageDetail>(`/connectors/${connectorId}/coverage`);
}

export function getIngestionConfig(id: string): Promise<{ ingestion_config: IngestionConfig | null }> {
  return apiGet<{ ingestion_config: IngestionConfig | null }>(`/connectors/${id}/ingestion-config`);
}

export function updateIngestionConfig(id: string, ingestion_config: IngestionConfig): Promise<VectorDBConnector> {
  return apiPatch<VectorDBConnector>(`/connectors/${id}/ingestion-config`, { ingestion_config });
}

export function suggestClassifications(
  connectorId: string,
  options: { scan_limit?: number; grouping_strategy?: string; grouping_pattern?: string; sample_size?: number } = {},
): Promise<SuggestClassificationsResponse> {
  return apiPost<SuggestClassificationsResponse>(`/connectors/${connectorId}/suggest-classifications`, options);
}

export function applySuggestions(
  connectorId: string,
  suggestions: ClassificationSuggestion[],
): Promise<ApplySuggestionsResponse> {
  return apiPost<ApplySuggestionsResponse>(`/connectors/${connectorId}/apply-suggestions`, { suggestions });
}
