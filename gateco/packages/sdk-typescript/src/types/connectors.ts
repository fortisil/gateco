/**
 * Types for connector endpoints.
 */

/** Supported connector types. */
export type ConnectorType =
  | "pgvector"
  | "pinecone"
  | "opensearch"
  | "supabase"
  | "neon"
  | "weaviate"
  | "qdrant"
  | "milvus"
  | "chroma";

/** Connector lifecycle status. */
export type ConnectorStatus = "connected" | "error" | "syncing" | "disconnected";

/** Metadata resolution mode for a connector. */
export type MetadataResolutionMode = "sidecar" | "inline" | "sql_view" | "auto";

/** Semantic policy readiness levels (L0-L4). */
export enum PolicyReadinessLevel {
  NotReady = 0,
  ConnectionReady = 1,
  SearchReady = 2,
  ResourcePolicy = 3,
  ChunkPolicy = 4,
}

/** A configured connector instance. */
export interface Connector {
  id: string;
  name: string;
  type: string;
  config: Record<string, unknown>;
  status?: string;
  organization_id?: string;
  created_at?: string;
  updated_at?: string;
  metadata_resolution_mode?: MetadataResolutionMode;
}

/** Request body for `POST /api/connectors`. */
export interface CreateConnectorRequest {
  name: string;
  type: string;
  config?: Record<string, unknown>;
}

/** Response from `POST /api/connectors/{id}/test`. */
export interface TestConnectorResponse {
  status: string;
  message?: string;
  latency_ms?: number;
  details?: Record<string, unknown>;
}

/** Search configuration for a connector. */
export interface SearchConfig {
  top_k?: number;
  similarity_threshold?: number;
  filters?: Record<string, unknown>;
  extra?: Record<string, unknown>;
}

/** Ingestion configuration for a connector. */
export interface IngestionConfig {
  chunk_size?: number;
  chunk_overlap?: number;
  embedding_model?: string;
  extra?: Record<string, unknown>;
}

/** A single binding entry for `POST /api/connectors/{id}/bind`. */
export interface BindingEntry {
  vector_id: string;
  external_resource_id: string;
  metadata?: Record<string, unknown>;
}

/** Response from `POST /api/connectors/{id}/bind`. */
export interface BindResult {
  status: string;
  bound: number;
  errors: Record<string, unknown>[];
}

/** Response from `GET /api/connectors/{id}/coverage`. */
export interface CoverageDetail {
  total_resources: number;
  bound_resources: number;
  unbound_resources: number;
  coverage_percent: number;
  details: Record<string, unknown>[];
}

/** A single classification suggestion. */
export interface ClassificationSuggestion {
  resource_key: string;
  vector_ids: string[];
  suggested_classification?: string;
  suggested_sensitivity?: string;
  suggested_domain?: string;
  confidence: number;
  reasoning?: string;
}

/** Response from suggest-classifications. */
export interface SuggestClassificationsResponse {
  status: string;
  scanned_vectors: number;
  suggestions: ClassificationSuggestion[];
}

/** Response from apply-suggestions. */
export interface ApplySuggestionsResponse {
  status: string;
  applied: number;
  resources_created: number;
  errors: Record<string, unknown>[];
}

/** Parse a raw JSON object into a Connector. */
export function parseConnector(data: Record<string, unknown>): Connector {
  return {
    id: data["id"] as string,
    name: data["name"] as string,
    type: data["type"] as string,
    config: (data["config"] as Record<string, unknown>) ?? {},
    status: data["status"] as string | undefined,
    organization_id: data["organization_id"] as string | undefined,
    created_at: data["created_at"] as string | undefined,
    updated_at: data["updated_at"] as string | undefined,
    metadata_resolution_mode: data["metadata_resolution_mode"] as MetadataResolutionMode | undefined,
  };
}

/** Parse a raw JSON object into a TestConnectorResponse. */
export function parseTestConnectorResponse(data: Record<string, unknown>): TestConnectorResponse {
  return {
    status: data["status"] as string,
    message: data["message"] as string | undefined,
    latency_ms: data["latency_ms"] as number | undefined,
    details: data["details"] as Record<string, unknown> | undefined,
  };
}

/** Parse a raw JSON object into a BindResult. */
export function parseBindResult(data: Record<string, unknown>): BindResult {
  return {
    status: data["status"] as string,
    bound: (data["bound"] as number) ?? 0,
    errors: (data["errors"] as Record<string, unknown>[]) ?? [],
  };
}

/** Parse a raw JSON object into a CoverageDetail. */
export function parseCoverageDetail(data: Record<string, unknown>): CoverageDetail {
  return {
    total_resources: (data["total_resources"] as number) ?? 0,
    bound_resources: (data["bound_resources"] as number) ?? 0,
    unbound_resources: (data["unbound_resources"] as number) ?? 0,
    coverage_percent: (data["coverage_percent"] as number) ?? 0,
    details: (data["details"] as Record<string, unknown>[]) ?? [],
  };
}

/** Parse a raw JSON object into a SuggestClassificationsResponse. */
export function parseSuggestClassificationsResponse(
  data: Record<string, unknown>,
): SuggestClassificationsResponse {
  return {
    status: data["status"] as string,
    scanned_vectors: (data["scanned_vectors"] as number) ?? 0,
    suggestions: (data["suggestions"] as ClassificationSuggestion[]) ?? [],
  };
}

/** Parse a raw JSON object into an ApplySuggestionsResponse. */
export function parseApplySuggestionsResponse(
  data: Record<string, unknown>,
): ApplySuggestionsResponse {
  return {
    status: data["status"] as string,
    applied: (data["applied"] as number) ?? 0,
    resources_created: (data["resources_created"] as number) ?? 0,
    errors: (data["errors"] as Record<string, unknown>[]) ?? [],
  };
}
