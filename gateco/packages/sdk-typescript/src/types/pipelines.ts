/**
 * Types for pipeline endpoints.
 */

/** Envelope configuration for a pipeline. */
export interface EnvelopeConfig {
  format?: string;
  fields?: Record<string, unknown>;
}

/** A pipeline resource. */
export interface Pipeline {
  id: string;
  name: string;
  source_connector_id: string;
  envelope_config?: Record<string, unknown>;
  status?: string;
  schedule: string;
  last_run?: string;
  records_processed: number;
  error_count: number;
  created_at?: string;
  updated_at?: string;
}

/** A single pipeline run record. */
export interface PipelineRun {
  id: string;
  pipeline_id: string;
  status: string;
  records_processed: number;
  errors: number;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
}

/** Request body for `POST /api/pipelines`. */
export interface CreatePipelineRequest {
  name: string;
  source_connector_id: string;
  envelope_config?: Record<string, unknown>;
  schedule?: string;
}

/** Parse a raw JSON object into a Pipeline. */
export function parsePipeline(data: Record<string, unknown>): Pipeline {
  return {
    id: data["id"] as string,
    name: data["name"] as string,
    source_connector_id: data["source_connector_id"] as string,
    envelope_config: data["envelope_config"] as Record<string, unknown> | undefined,
    status: data["status"] as string | undefined,
    schedule: (data["schedule"] as string) ?? "manual",
    last_run: data["last_run"] as string | undefined,
    records_processed: (data["records_processed"] as number) ?? 0,
    error_count: (data["error_count"] as number) ?? 0,
    created_at: data["created_at"] as string | undefined,
    updated_at: data["updated_at"] as string | undefined,
  };
}

/** Parse a raw JSON object into a PipelineRun. */
export function parsePipelineRun(data: Record<string, unknown>): PipelineRun {
  return {
    id: data["id"] as string,
    pipeline_id: data["pipeline_id"] as string,
    status: data["status"] as string,
    records_processed: (data["records_processed"] as number) ?? 0,
    errors: (data["errors"] as number) ?? 0,
    started_at: data["started_at"] as string | undefined,
    completed_at: data["completed_at"] as string | undefined,
    duration_ms: data["duration_ms"] as number | undefined,
  };
}
