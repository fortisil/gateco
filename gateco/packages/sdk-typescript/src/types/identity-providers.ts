/**
 * Types for identity provider endpoints.
 */

/** Supported identity provider types. */
export type IdentityProviderType = "okta" | "azure_ad" | "google" | "custom";

/** Identity provider lifecycle status. */
export type IdentityProviderStatus = "connected" | "error" | "syncing" | "disconnected";

/** Sync configuration for an identity provider. */
export interface SyncConfig {
  schedule?: string;
  scope?: string;
  filters?: Record<string, unknown>;
}

/** An identity provider resource. */
export interface IdentityProvider {
  id: string;
  name: string;
  type: string;
  status: string;
  config: Record<string, unknown>;
  sync_config?: Record<string, unknown>;
  principal_count: number;
  group_count: number;
  last_sync?: string;
  error_message?: string;
  created_at?: string;
  updated_at?: string;
}

/** Request body for `POST /api/identity-providers`. */
export interface CreateIdentityProviderRequest {
  name: string;
  type: string;
  config?: Record<string, unknown>;
  sync_config?: Record<string, unknown>;
}

/** Parse a raw JSON object into an IdentityProvider. */
export function parseIdentityProvider(data: Record<string, unknown>): IdentityProvider {
  return {
    id: data["id"] as string,
    name: data["name"] as string,
    type: data["type"] as string,
    status: data["status"] as string,
    config: (data["config"] as Record<string, unknown>) ?? {},
    sync_config: data["sync_config"] as Record<string, unknown> | undefined,
    principal_count: (data["principal_count"] as number) ?? 0,
    group_count: (data["group_count"] as number) ?? 0,
    last_sync: data["last_sync"] as string | undefined,
    error_message: data["error_message"] as string | undefined,
    created_at: data["created_at"] as string | undefined,
    updated_at: data["updated_at"] as string | undefined,
  };
}
