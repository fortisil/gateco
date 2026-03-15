/**
 * Types for ingestion endpoints.
 */

/** Request body for `POST /api/v1/ingest`. */
export interface IngestDocumentRequest {
  connector_id: string;
  external_resource_id: string;
  text: string;
  classification?: string;
  sensitivity?: string;
  domain?: string;
  labels?: string[];
  metadata?: Record<string, unknown>;
  owner_principal_id?: string;
  idempotency_key?: string;
}

/** Response from `POST /api/v1/ingest`. */
export interface IngestDocumentResponse {
  status: string;
  resource_id: string;
  external_resource_id: string;
  chunk_count: number;
  vector_ids: string[];
}

/** Request body for `POST /api/v1/ingest/batch`. */
export interface BatchIngestRequest {
  connector_id: string;
  records: Record<string, unknown>[];
  idempotency_key?: string;
}

/** Response from `POST /api/v1/ingest/batch`. */
export interface BatchIngestResponse {
  status: string;
  succeeded: number;
  failed: number;
  results: Record<string, unknown>[];
  errors: Record<string, unknown>[];
}

/** Parse a raw JSON object into an IngestDocumentResponse. */
export function parseIngestDocumentResponse(
  data: Record<string, unknown>,
): IngestDocumentResponse {
  return {
    status: data["status"] as string,
    resource_id: data["resource_id"] as string,
    external_resource_id: data["external_resource_id"] as string,
    chunk_count: (data["chunk_count"] as number) ?? 0,
    vector_ids: (data["vector_ids"] as string[]) ?? [],
  };
}

/** Parse a raw JSON object into a BatchIngestResponse. */
export function parseBatchIngestResponse(data: Record<string, unknown>): BatchIngestResponse {
  return {
    status: data["status"] as string,
    succeeded: (data["succeeded"] as number) ?? 0,
    failed: (data["failed"] as number) ?? 0,
    results: (data["results"] as Record<string, unknown>[]) ?? [],
    errors: (data["errors"] as Record<string, unknown>[]) ?? [],
  };
}
