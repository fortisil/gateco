/**
 * Types for retrieval endpoints.
 */

/** Reason a retrieval result was denied. */
export interface DenialReason {
  code: string;
  message?: string;
  policy_id?: string;
}

/** Trace of a policy evaluation during retrieval. */
export interface PolicyTrace {
  policy_id: string;
  policy_name?: string;
  decision: string;
  reason?: string;
  duration_ms?: number;
}

/** A single result item within a retrieval response. */
export interface RetrievalOutcome {
  resource_id: string;
  external_resource_id?: string;
  score?: number;
  granted: boolean;
  denial_reason?: DenialReason;
  policy_traces: PolicyTrace[];
  metadata: Record<string, unknown>;
  text?: string;
}

/** Request body for `POST /api/retrievals/execute`. */
export interface ExecuteRetrievalRequest {
  query_vector?: number[];
  query?: string;
  principal_id: string;
  connector_id: string;
  top_k?: number;
  filters?: Record<string, unknown>;
  include_unresolved?: boolean;
}

/** Full retrieval record returned by list / get / execute endpoints. */
export interface SecuredRetrieval {
  id: string;
  query?: string;
  principal_id?: string;
  connector_id?: string;
  organization_id?: string;
  status?: string;
  total_results: number;
  granted_count: number;
  denied_count: number;
  outcomes: RetrievalOutcome[];
  created_at?: string;
  duration_ms?: number;
  metadata: Record<string, unknown>;
}

/** Parse a raw JSON object into a SecuredRetrieval. */
export function parseSecuredRetrieval(data: Record<string, unknown>): SecuredRetrieval {
  return {
    id: data["id"] as string,
    query: data["query"] as string | undefined,
    principal_id: data["principal_id"] as string | undefined,
    connector_id: data["connector_id"] as string | undefined,
    organization_id: data["organization_id"] as string | undefined,
    status: data["status"] as string | undefined,
    total_results: (data["total_results"] as number) ?? 0,
    granted_count: (data["granted_count"] as number) ?? 0,
    denied_count: (data["denied_count"] as number) ?? 0,
    outcomes: Array.isArray(data["outcomes"])
      ? (data["outcomes"] as Record<string, unknown>[]).map(parseRetrievalOutcome)
      : [],
    created_at: data["created_at"] as string | undefined,
    duration_ms: data["duration_ms"] as number | undefined,
    metadata: (data["metadata"] as Record<string, unknown>) ?? {},
  };
}

/** Parse a raw JSON object into a RetrievalOutcome. */
export function parseRetrievalOutcome(data: Record<string, unknown>): RetrievalOutcome {
  return {
    resource_id: data["resource_id"] as string,
    external_resource_id: data["external_resource_id"] as string | undefined,
    score: data["score"] as number | undefined,
    granted: (data["granted"] as boolean) ?? false,
    denial_reason: data["denial_reason"]
      ? parseDenialReason(data["denial_reason"] as Record<string, unknown>)
      : undefined,
    policy_traces: Array.isArray(data["policy_traces"])
      ? (data["policy_traces"] as Record<string, unknown>[]).map(parsePolicyTrace)
      : [],
    metadata: (data["metadata"] as Record<string, unknown>) ?? {},
    text: data["text"] as string | undefined,
  };
}

/** Parse a raw JSON object into a DenialReason. */
export function parseDenialReason(data: Record<string, unknown>): DenialReason {
  return {
    code: data["code"] as string,
    message: data["message"] as string | undefined,
    policy_id: data["policy_id"] as string | undefined,
  };
}

/** Parse a raw JSON object into a PolicyTrace. */
export function parsePolicyTrace(data: Record<string, unknown>): PolicyTrace {
  return {
    policy_id: data["policy_id"] as string,
    policy_name: data["policy_name"] as string | undefined,
    decision: data["decision"] as string,
    reason: data["reason"] as string | undefined,
    duration_ms: data["duration_ms"] as number | undefined,
  };
}
