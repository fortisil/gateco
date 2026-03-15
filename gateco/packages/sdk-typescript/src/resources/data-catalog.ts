/**
 * Data catalog resource -- list, detail, update.
 */

import type { GatecoClient } from "../client.js";
import type { Page } from "../pagination.js";
import { parsePage, listAll } from "../pagination.js";
import type { GatedResource, GatedResourceDetail, DataCatalogFilters } from "../types/data-catalog.js";
import { parseGatedResource, parseGatedResourceDetail } from "../types/data-catalog.js";

/** Options for updating a gated resource. */
export interface UpdateGatedResourceOptions {
  classification?: string;
  sensitivity?: string;
  domain?: string;
  labels?: string[];
  encryptionMode?: string;
}

/** Namespace for data catalog endpoints. Accessed as `client.dataCatalog`. */
export class DataCatalogResource {
  constructor(private readonly client: GatecoClient) {}

  // ------------------------------------------------------------------
  // List
  // ------------------------------------------------------------------

  /** Fetch a single page of gated resources from the data catalog. */
  async list(
    page = 1,
    perPage = 20,
    filters: DataCatalogFilters = {},
  ): Promise<Page<GatedResource>> {
    const params: Record<string, string | number | boolean | undefined> = {
      page,
      per_page: perPage,
    };
    if (filters.classification !== undefined) params["classification"] = filters.classification;
    if (filters.sensitivity !== undefined) params["sensitivity"] = filters.sensitivity;
    if (filters.domain !== undefined) params["domain"] = filters.domain;
    if (filters.label !== undefined) params["label"] = filters.label;
    if (filters.source_connector_id !== undefined)
      params["source_connector_id"] = filters.source_connector_id;

    const raw = await this.client._request("GET", "/api/data-catalog", { params });
    return parsePage(raw, page, perPage, parseGatedResource);
  }

  /** Return an async generator that lazily paginates through all resources. */
  listAll(
    perPage = 100,
    filters: DataCatalogFilters = {},
  ): AsyncGenerator<GatedResource, void, undefined> {
    return listAll(
      async (page, pp) => {
        const params: Record<string, string | number | boolean | undefined> = {
          page,
          per_page: pp,
        };
        if (filters.classification !== undefined) params["classification"] = filters.classification;
        if (filters.sensitivity !== undefined) params["sensitivity"] = filters.sensitivity;
        if (filters.domain !== undefined) params["domain"] = filters.domain;
        if (filters.label !== undefined) params["label"] = filters.label;
        if (filters.source_connector_id !== undefined)
          params["source_connector_id"] = filters.source_connector_id;
        return (await this.client._request("GET", "/api/data-catalog", { params })) ?? {};
      },
      parseGatedResource,
      perPage,
    );
  }

  // ------------------------------------------------------------------
  // Detail + Update
  // ------------------------------------------------------------------

  /** Get detailed information for a single resource. */
  async get(resourceId: string): Promise<GatedResourceDetail> {
    const data = await this.client._request("GET", `/api/data-catalog/${resourceId}`);
    return parseGatedResourceDetail(data as Record<string, unknown>);
  }

  /** Update metadata on a gated resource. */
  async update(
    resourceId: string,
    options: UpdateGatedResourceOptions = {},
  ): Promise<GatedResource> {
    const body: Record<string, unknown> = {};
    if (options.classification !== undefined) body["classification"] = options.classification;
    if (options.sensitivity !== undefined) body["sensitivity"] = options.sensitivity;
    if (options.domain !== undefined) body["domain"] = options.domain;
    if (options.labels !== undefined) body["labels"] = options.labels;
    if (options.encryptionMode !== undefined) body["encryption_mode"] = options.encryptionMode;

    const data = await this.client._request("PATCH", `/api/data-catalog/${resourceId}`, {
      json: body,
    });
    return parseGatedResource(data as Record<string, unknown>);
  }
}
