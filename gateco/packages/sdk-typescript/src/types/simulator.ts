/**
 * Types for access simulator endpoints.
 */

/** Request body for `POST /api/simulator/run`. */
export interface SimulationRequest {
  principal_id: string;
  query?: string;
  connector_id?: string;
  resource_ids?: string[];
}

/** Response from `POST /api/simulator/run`. */
export interface SimulationResult {
  outcome: string;
  matched_resources: number;
  allowed: number;
  denied: number;
  policy_trace: Record<string, unknown>[];
  denial_reasons: string[];
}

/** Parse a raw JSON object into a SimulationResult. */
export function parseSimulationResult(data: Record<string, unknown>): SimulationResult {
  return {
    outcome: data["outcome"] as string,
    matched_resources: (data["matched_resources"] as number) ?? 0,
    allowed: (data["allowed"] as number) ?? 0,
    denied: (data["denied"] as number) ?? 0,
    policy_trace: (data["policy_trace"] as Record<string, unknown>[]) ?? [],
    denial_reasons: (data["denial_reasons"] as string[]) ?? [],
  };
}
