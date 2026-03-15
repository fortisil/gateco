/**
 * Types for audit log endpoints.
 */

/** Audit event types for the audit trail. */
export type AuditEventType =
  | "user_login"
  | "user_logout"
  | "settings_changed"
  | "connector_added"
  | "connector_updated"
  | "connector_tested"
  | "connector_removed"
  | "connector_sync_started"
  | "connector_synced"
  | "connector_sync_failed"
  | "idp_added"
  | "idp_updated"
  | "idp_removed"
  | "idp_sync_started"
  | "idp_synced"
  | "idp_sync_failed"
  | "policy_created"
  | "policy_updated"
  | "policy_activated"
  | "policy_archived"
  | "policy_deleted"
  | "resource_updated"
  | "pipeline_created"
  | "pipeline_updated"
  | "pipeline_run"
  | "pipeline_error"
  | "retrieval_allowed"
  | "retrieval_denied"
  | "metadata_bound"
  | "document_ingested"
  | "batch_ingested"
  | "ingestion_failed"
  | "retroactive_registered";

/** An audit log event. */
export interface AuditEvent {
  id: string;
  event_type: string;
  actor_id?: string;
  actor_name?: string;
  principal_id?: string;
  details?: string;
  ip_address?: string;
  timestamp?: string;
  resource_ids: string[];
}

/** Parameters for audit log export. */
export interface AuditExportRequest {
  event_types?: string;
  date_from?: string;
  date_to?: string;
  format?: string;
}

/** Parse a raw JSON object into an AuditEvent. */
export function parseAuditEvent(data: Record<string, unknown>): AuditEvent {
  return {
    id: data["id"] as string,
    event_type: data["event_type"] as string,
    actor_id: data["actor_id"] as string | undefined,
    actor_name: data["actor_name"] as string | undefined,
    principal_id: data["principal_id"] as string | undefined,
    details: data["details"] as string | undefined,
    ip_address: data["ip_address"] as string | undefined,
    timestamp: data["timestamp"] as string | undefined,
    resource_ids: (data["resource_ids"] as string[]) ?? [],
  };
}
