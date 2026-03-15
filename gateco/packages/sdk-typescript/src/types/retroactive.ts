/**
 * Types for retroactive registration endpoints.
 */

/** Request body for `POST /api/v1/retroactive-register`. */
export interface RetroactiveRegisterRequest {
  connector_id: string;
  scan_limit?: number;
  default_classification?: string;
  default_sensitivity?: string;
  default_domain?: string;
  default_labels?: string[];
  grouping_strategy?: string;
  grouping_pattern?: string;
  dry_run?: boolean;
}

/** Response from `POST /api/v1/retroactive-register`. */
export interface RetroactiveRegisterResponse {
  status: string;
  scanned_vectors: number;
  already_registered: number;
  newly_registered: number;
  resources_created: number;
  errors: Record<string, unknown>[];
}

/** Parse a raw JSON object into a RetroactiveRegisterResponse. */
export function parseRetroactiveRegisterResponse(
  data: Record<string, unknown>,
): RetroactiveRegisterResponse {
  return {
    status: data["status"] as string,
    scanned_vectors: (data["scanned_vectors"] as number) ?? 0,
    already_registered: (data["already_registered"] as number) ?? 0,
    newly_registered: (data["newly_registered"] as number) ?? 0,
    resources_created: (data["resources_created"] as number) ?? 0,
    errors: (data["errors"] as Record<string, unknown>[]) ?? [],
  };
}
