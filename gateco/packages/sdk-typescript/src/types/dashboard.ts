/**
 * Types for dashboard endpoints.
 */

/** Aggregated dashboard statistics. */
export interface DashboardStats {
  retrievals_today: number;
  retrievals_allowed: number;
  retrievals_denied: number;
  connectors_connected: number;
  connectors_error: number;
  idps_connected: number;
  idps_principal_count: number;
  last_idp_sync?: string;
  recent_denied: Record<string, unknown>[];
  total_bound_vectors: number;
  total_vectors: number;
  overall_coverage_pct?: number;
  connectors_policy_ready: number;
}

/** Parse a raw JSON object into DashboardStats. */
export function parseDashboardStats(data: Record<string, unknown>): DashboardStats {
  return {
    retrievals_today: (data["retrievals_today"] as number) ?? 0,
    retrievals_allowed: (data["retrievals_allowed"] as number) ?? 0,
    retrievals_denied: (data["retrievals_denied"] as number) ?? 0,
    connectors_connected: (data["connectors_connected"] as number) ?? 0,
    connectors_error: (data["connectors_error"] as number) ?? 0,
    idps_connected: (data["idps_connected"] as number) ?? 0,
    idps_principal_count: (data["idps_principal_count"] as number) ?? 0,
    last_idp_sync: data["last_idp_sync"] as string | undefined,
    recent_denied: (data["recent_denied"] as Record<string, unknown>[]) ?? [],
    total_bound_vectors: (data["total_bound_vectors"] as number) ?? 0,
    total_vectors: (data["total_vectors"] as number) ?? 0,
    overall_coverage_pct: data["overall_coverage_pct"] as number | undefined,
    connectors_policy_ready: (data["connectors_policy_ready"] as number) ?? 0,
  };
}
