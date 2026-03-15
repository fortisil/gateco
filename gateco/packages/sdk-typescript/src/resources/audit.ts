/**
 * Audit resource -- list + export.
 */

import type { GatecoClient } from "../client.js";
import type { Page } from "../pagination.js";
import { parsePage, listAll } from "../pagination.js";
import type { AuditEvent } from "../types/audit.js";
import { parseAuditEvent } from "../types/audit.js";

/** Filters for audit log list queries. */
export interface AuditListFilters {
  eventTypes?: string;
  actor?: string;
  dateFrom?: string;
  dateTo?: string;
}

/** Filters for audit log export. */
export interface AuditExportFilters {
  eventTypes?: string;
  dateFrom?: string;
  dateTo?: string;
  format?: string;
}

/** Namespace for audit log endpoints. Accessed as `client.audit`. */
export class AuditResource {
  constructor(private readonly client: GatecoClient) {}

  // ------------------------------------------------------------------
  // List
  // ------------------------------------------------------------------

  /** Fetch a single page of audit events. */
  async list(
    page = 1,
    perPage = 20,
    filters: AuditListFilters = {},
  ): Promise<Page<AuditEvent>> {
    const params: Record<string, string | number | boolean | undefined> = {
      page,
      per_page: perPage,
    };
    if (filters.eventTypes !== undefined) params["event_types"] = filters.eventTypes;
    if (filters.actor !== undefined) params["actor"] = filters.actor;
    if (filters.dateFrom !== undefined) params["date_from"] = filters.dateFrom;
    if (filters.dateTo !== undefined) params["date_to"] = filters.dateTo;

    const raw = await this.client._request("GET", "/api/audit-log", { params });
    return parsePage(raw, page, perPage, parseAuditEvent);
  }

  /** Return an async generator that lazily paginates through all audit events. */
  listAll(
    perPage = 100,
    filters: AuditListFilters = {},
  ): AsyncGenerator<AuditEvent, void, undefined> {
    return listAll(
      async (page, pp) => {
        const params: Record<string, string | number | boolean | undefined> = {
          page,
          per_page: pp,
        };
        if (filters.eventTypes !== undefined) params["event_types"] = filters.eventTypes;
        if (filters.actor !== undefined) params["actor"] = filters.actor;
        if (filters.dateFrom !== undefined) params["date_from"] = filters.dateFrom;
        if (filters.dateTo !== undefined) params["date_to"] = filters.dateTo;
        return (await this.client._request("GET", "/api/audit-log", { params })) ?? {};
      },
      parseAuditEvent,
      perPage,
    );
  }

  // ------------------------------------------------------------------
  // Export
  // ------------------------------------------------------------------

  /** Export audit log as JSON or CSV. */
  async exportCsv(filters: AuditExportFilters = {}): Promise<Record<string, unknown>> {
    const params: Record<string, string | number | boolean | undefined> = {
      format: filters.format ?? "csv",
    };
    if (filters.eventTypes !== undefined) params["event_types"] = filters.eventTypes;
    if (filters.dateFrom !== undefined) params["date_from"] = filters.dateFrom;
    if (filters.dateTo !== undefined) params["date_to"] = filters.dateTo;

    const data = await this.client._request("POST", "/api/audit-log/export", { params });
    return (data as Record<string, unknown>) ?? {};
  }
}
