export type ConnectorType =
  | 'pgvector'
  | 'pinecone'
  | 'opensearch'
  | 'supabase'
  | 'neon'
  | 'weaviate'
  | 'qdrant'
  | 'milvus'
  | 'chroma';

export type ConnectorStatus = 'connected' | 'error' | 'syncing' | 'disconnected';

export type ResourceKind = 'table' | 'index' | 'class' | 'collection' | 'namespace';
export type HealthStatus = 'ok' | 'degraded' | 'failed';

export interface ConnectorConfig {
  host?: string;
  port?: number;
  database?: string;
  api_key?: string;
  region?: string;
  index_name?: string;
  user?: string;
  password?: string;
  schema?: string;
  connection_string?: string;
  class_name?: string;
  collection_name?: string;
  token?: string;
  tenant?: string;
  [key: string]: string | number | boolean | undefined;
}

export interface SearchConfig {
  // Postgres family
  table_name?: string;
  vector_column?: string;
  id_column?: string;
  content_column?: string;
  metric?: 'cosine' | 'l2' | 'inner_product';
  // Pinecone
  index_name?: string;
  namespace?: string;
  // Qdrant / Milvus / Chroma
  collection_name?: string;
  // Weaviate
  class_name?: string;
  properties?: string[];
  // Milvus
  vector_field?: string;
  output_fields?: string[];
  // OpenSearch
  // index_name + vector_field already covered
  // Universal
  expected_dimension?: number;
  [key: string]: string | number | string[] | undefined;
}

export interface IngestionConfig {
  target_table?: string;
  target_collection?: string;
  target_index?: string;
  id_field?: string;
  content_field?: string;
  metadata_fields?: string[];
  upsert_mode?: 'insert' | 'upsert';
  namespace?: string;
  [key: string]: string | string[] | undefined;
}

export type MetadataResolutionMode = 'sidecar' | 'inline' | 'sql_view' | 'auto';

export interface VectorDBConnector {
  id: string;
  name: string;
  type: ConnectorType;
  status: ConnectorStatus;
  config: ConnectorConfig;
  last_sync: string | null;
  index_count: number;
  record_count: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  last_tested_at: string | null;
  last_test_success: boolean | null;
  last_test_latency_ms: number | null;
  server_version: string | null;
  diagnostics: TestConnectorResponse | null;
  search_config: SearchConfig | null;
  connection_ready: boolean;
  search_ready: boolean;
  bound_vector_count: number;
  coverage_pct: number | null;
  policy_readiness_level: 0 | 1 | 2 | 3 | 4;
  ingestion_capable: boolean;
  ingestion_ready: boolean;
  ingestion_config: IngestionConfig | null;
  metadata_resolution_mode?: MetadataResolutionMode;
}

export interface CreateConnectorRequest {
  name: string;
  type: ConnectorType;
  config: ConnectorConfig;
}

export interface DiscoveredResource {
  name: string;
  record_count: number | null;
  dimension: number | null;
  metric: string | null;
}

export interface ClassificationSuggestion {
  resource_key: string;
  vector_ids: string[];
  suggested_classification: string | null;
  suggested_sensitivity: string | null;
  suggested_domain: string | null;
  confidence: number;
  reasoning: string | null;
}

export interface SuggestClassificationsResponse {
  status: string;
  scanned_vectors: number;
  suggestions: ClassificationSuggestion[];
}

export interface ApplySuggestionsResponse {
  status: string;
  applied: number;
  resources_created: number;
  errors: Record<string, unknown>[];
}

export interface TestConnectorResponse {
  success: boolean;
  health_status: HealthStatus;
  authenticated: boolean;
  schema_discovered: boolean;
  vector_ready: boolean;
  server_version: string | null;
  resources: DiscoveredResource[] | null;
  resource_kind: ResourceKind | null;
  total_records: number | null;
  approximate_counts: boolean;
  warnings: string[];
  error: string | null;
  latency_ms: number;
}
