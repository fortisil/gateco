/**
 * Types for data catalog endpoints.
 */

/** Filters for data catalog list queries. */
export interface DataCatalogFilters {
  classification?: string;
  sensitivity?: string;
  domain?: string;
  label?: string;
  source_connector_id?: string;
}

/** A chunk belonging to a gated resource. */
export interface ResourceChunk {
  id?: string;
  vector_id?: string;
  content_preview?: string;
  metadata: Record<string, unknown>;
}

/** A gated resource in the data catalog. */
export interface GatedResource {
  id: string;
  title: string;
  description?: string;
  type?: string;
  classification?: string;
  sensitivity?: string;
  domain?: string;
  labels?: string[];
  encryption_mode?: string;
  source_connector_id?: string;
  view_count: number;
  created_at?: string;
  updated_at?: string;
}

/** Extended resource detail including chunks, policies, and access history. */
export interface GatedResourceDetail extends GatedResource {
  chunks: Record<string, unknown>[];
  applicable_policies: Record<string, unknown>[];
  recent_access: Record<string, unknown>[];
}

/** Parse a raw JSON object into a GatedResource. */
export function parseGatedResource(data: Record<string, unknown>): GatedResource {
  return {
    id: data["id"] as string,
    title: data["title"] as string,
    description: data["description"] as string | undefined,
    type: data["type"] as string | undefined,
    classification: data["classification"] as string | undefined,
    sensitivity: data["sensitivity"] as string | undefined,
    domain: data["domain"] as string | undefined,
    labels: data["labels"] as string[] | undefined,
    encryption_mode: data["encryption_mode"] as string | undefined,
    source_connector_id: data["source_connector_id"] as string | undefined,
    view_count: (data["view_count"] as number) ?? 0,
    created_at: data["created_at"] as string | undefined,
    updated_at: data["updated_at"] as string | undefined,
  };
}

/** Parse a raw JSON object into a GatedResourceDetail. */
export function parseGatedResourceDetail(data: Record<string, unknown>): GatedResourceDetail {
  return {
    ...parseGatedResource(data),
    chunks: (data["chunks"] as Record<string, unknown>[]) ?? [],
    applicable_policies: (data["applicable_policies"] as Record<string, unknown>[]) ?? [],
    recent_access: (data["recent_access"] as Record<string, unknown>[]) ?? [],
  };
}

/** Parse a raw JSON object into a ResourceChunk. */
export function parseResourceChunk(data: Record<string, unknown>): ResourceChunk {
  return {
    id: data["id"] as string | undefined,
    vector_id: data["vector_id"] as string | undefined,
    content_preview: data["content_preview"] as string | undefined,
    metadata: (data["metadata"] as Record<string, unknown>) ?? {},
  };
}
