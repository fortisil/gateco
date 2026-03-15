export type AuditEventType =
  | 'retrieval_allowed'
  | 'retrieval_denied'
  | 'policy_created'
  | 'policy_updated'
  | 'policy_activated'
  | 'policy_archived'
  | 'connector_added'
  | 'connector_removed'
  | 'connector_synced'
  | 'idp_added'
  | 'idp_synced'
  | 'pipeline_run'
  | 'pipeline_error'
  | 'user_login'
  | 'settings_changed';

export interface AuditEvent {
  id: string;
  event_type: AuditEventType;
  actor_id: string;
  actor_name: string;
  principal_id: string | null;
  resource_ids: string[];
  details: Record<string, unknown>;
  ip_address: string | null;
  timestamp: string;
}

export interface AuditExportRequest {
  format: 'csv' | 'json';
  date_from: string;
  date_to: string;
  event_types?: AuditEventType[];
}
