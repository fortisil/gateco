/**
 * Types for principal endpoints.
 */

/** Arbitrary attributes attached to a principal. */
export interface PrincipalAttributes {
  department?: string;
  location?: string;
  clearance_level?: string;
  extra?: Record<string, unknown>;
}

/** An identity principal resource. */
export interface Principal {
  id: string;
  identity_provider_id?: string;
  identity_provider_name?: string;
  external_id?: string;
  display_name?: string;
  email?: string;
  groups: string[];
  roles: string[];
  attributes: Record<string, unknown>;
  status?: string;
  last_seen?: string;
  created_at?: string;
}

/** Parse a raw JSON object into a Principal. */
export function parsePrincipal(data: Record<string, unknown>): Principal {
  return {
    id: data["id"] as string,
    identity_provider_id: data["identity_provider_id"] as string | undefined,
    identity_provider_name: data["identity_provider_name"] as string | undefined,
    external_id: data["external_id"] as string | undefined,
    display_name: data["display_name"] as string | undefined,
    email: data["email"] as string | undefined,
    groups: (data["groups"] as string[]) ?? [],
    roles: (data["roles"] as string[]) ?? [],
    attributes: (data["attributes"] as Record<string, unknown>) ?? {},
    status: data["status"] as string | undefined,
    last_seen: data["last_seen"] as string | undefined,
    created_at: data["created_at"] as string | undefined,
  };
}
