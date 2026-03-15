export type IdentityProviderType = 'azure_entra_id' | 'aws_iam' | 'gcp' | 'okta';

export type IdentityProviderStatus = 'connected' | 'error' | 'syncing' | 'disconnected';

export interface SyncConfig {
  auto_sync: boolean;
  sync_interval_minutes: number;
  sync_groups: boolean;
  sync_roles: boolean;
  sync_attributes: boolean;
}

export interface IdentityProvider {
  id: string;
  name: string;
  type: IdentityProviderType;
  status: IdentityProviderStatus;
  sync_config: SyncConfig;
  principal_count: number;
  group_count: number;
  last_sync: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateIdentityProviderRequest {
  name: string;
  type: IdentityProviderType;
  config: Record<string, string>;
  sync_config: SyncConfig;
}
