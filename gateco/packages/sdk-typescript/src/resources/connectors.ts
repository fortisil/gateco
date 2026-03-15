/**
 * Connectors resource -- CRUD, test, bind, config, coverage.
 */

import type { GatecoClient } from "../client.js";
import type { Page } from "../pagination.js";
import { parsePage, listAll } from "../pagination.js";
import type {
  Connector,
  BindingEntry,
  BindResult,
  TestConnectorResponse,
  CoverageDetail,
  ClassificationSuggestion,
  SuggestClassificationsResponse,
  ApplySuggestionsResponse,
} from "../types/connectors.js";
import {
  parseConnector,
  parseTestConnectorResponse,
  parseBindResult,
  parseCoverageDetail,
  parseSuggestClassificationsResponse,
  parseApplySuggestionsResponse,
} from "../types/connectors.js";

/** Namespace for connector endpoints. Accessed as `client.connectors`. */
export class ConnectorsResource {
  constructor(private readonly client: GatecoClient) {}

  // ------------------------------------------------------------------
  // List
  // ------------------------------------------------------------------

  /** Fetch a single page of connectors. */
  async list(page = 1, perPage = 20): Promise<Page<Connector>> {
    const raw = await this.client._request("GET", "/api/connectors", {
      params: { page, per_page: perPage },
    });
    return parsePage(raw, page, perPage, parseConnector);
  }

  /** Return an async generator that lazily paginates through all connectors. */
  listAll(perPage = 100): AsyncGenerator<Connector, void, undefined> {
    return listAll(
      async (page, pp) =>
        (await this.client._request("GET", "/api/connectors", {
          params: { page, per_page: pp },
        })) ?? {},
      parseConnector,
      perPage,
    );
  }

  // ------------------------------------------------------------------
  // CRUD
  // ------------------------------------------------------------------

  /** Get a single connector by ID. */
  async get(connectorId: string): Promise<Connector> {
    const data = await this.client._request("GET", `/api/connectors/${connectorId}`);
    return parseConnector(data as Record<string, unknown>);
  }

  /** Create a new connector. */
  async create(
    name: string,
    type: string,
    config?: Record<string, unknown>,
  ): Promise<Connector> {
    const body: Record<string, unknown> = { name, type };
    if (config !== undefined) {
      body["config"] = config;
    }
    const data = await this.client._request("POST", "/api/connectors", { json: body });
    return parseConnector(data as Record<string, unknown>);
  }

  /** Update an existing connector. */
  async update(
    connectorId: string,
    options: { name?: string; config?: Record<string, unknown> } = {},
  ): Promise<Connector> {
    const body: Record<string, unknown> = {};
    if (options.name !== undefined) {
      body["name"] = options.name;
    }
    if (options.config !== undefined) {
      body["config"] = options.config;
    }
    const data = await this.client._request("PATCH", `/api/connectors/${connectorId}`, {
      json: body,
    });
    return parseConnector(data as Record<string, unknown>);
  }

  /** Delete a connector. */
  async delete(connectorId: string): Promise<void> {
    await this.client._request("DELETE", `/api/connectors/${connectorId}`);
  }

  // ------------------------------------------------------------------
  // Actions
  // ------------------------------------------------------------------

  /** Test connectivity for a connector. */
  async test(connectorId: string): Promise<TestConnectorResponse> {
    const data = await this.client._request(
      "POST",
      `/api/connectors/${connectorId}/test`,
    );
    return parseTestConnectorResponse(data as Record<string, unknown>);
  }

  /** Bind external resources to vector IDs. */
  async bind(
    connectorId: string,
    bindings: BindingEntry[],
  ): Promise<BindResult> {
    const data = await this.client._request(
      "POST",
      `/api/connectors/${connectorId}/bind`,
      { json: { bindings } },
    );
    return parseBindResult(data as Record<string, unknown>);
  }

  // ------------------------------------------------------------------
  // Config
  // ------------------------------------------------------------------

  /** Get the search configuration for a connector. */
  async searchConfig(connectorId: string): Promise<Record<string, unknown>> {
    const data = await this.client._request(
      "GET",
      `/api/connectors/${connectorId}/search-config`,
    );
    return (data as Record<string, unknown>) ?? {};
  }

  /** Update the search configuration for a connector. */
  async updateSearchConfig(
    connectorId: string,
    searchConfig: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    const data = await this.client._request(
      "PATCH",
      `/api/connectors/${connectorId}/search-config`,
      { json: searchConfig },
    );
    return (data as Record<string, unknown>) ?? {};
  }

  /** Get the ingestion configuration for a connector. */
  async ingestionConfig(connectorId: string): Promise<Record<string, unknown>> {
    const data = await this.client._request(
      "GET",
      `/api/connectors/${connectorId}/ingestion-config`,
    );
    return (data as Record<string, unknown>) ?? {};
  }

  /** Update the ingestion configuration for a connector. */
  async updateIngestionConfig(
    connectorId: string,
    ingestionConfig: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    const data = await this.client._request(
      "PATCH",
      `/api/connectors/${connectorId}/ingestion-config`,
      { json: ingestionConfig },
    );
    return (data as Record<string, unknown>) ?? {};
  }

  // ------------------------------------------------------------------
  // Coverage
  // ------------------------------------------------------------------

  /** Get binding coverage for a connector. */
  async coverage(connectorId: string): Promise<CoverageDetail> {
    const data = await this.client._request(
      "GET",
      `/api/connectors/${connectorId}/coverage`,
    );
    return parseCoverageDetail(data as Record<string, unknown>);
  }

  // ------------------------------------------------------------------
  // Classification suggestions
  // ------------------------------------------------------------------

  /** Generate classification suggestions for unmanaged vectors. */
  async suggestClassifications(
    connectorId: string,
    options: {
      scanLimit?: number;
      groupingStrategy?: string;
      groupingPattern?: string;
      sampleSize?: number;
    } = {},
  ): Promise<SuggestClassificationsResponse> {
    const body: Record<string, unknown> = {
      scan_limit: options.scanLimit ?? 1000,
      grouping_strategy: options.groupingStrategy ?? "individual",
      sample_size: options.sampleSize ?? 10,
    };
    if (options.groupingPattern !== undefined) {
      body["grouping_pattern"] = options.groupingPattern;
    }
    const data = await this.client._request(
      "POST",
      `/api/connectors/${connectorId}/suggest-classifications`,
      { json: body },
    );
    return parseSuggestClassificationsResponse(data as Record<string, unknown>);
  }

  /** Apply approved classification suggestions. */
  async applySuggestions(
    connectorId: string,
    suggestions: ClassificationSuggestion[],
  ): Promise<ApplySuggestionsResponse> {
    const data = await this.client._request(
      "POST",
      `/api/connectors/${connectorId}/apply-suggestions`,
      { json: { suggestions } },
    );
    return parseApplySuggestionsResponse(data as Record<string, unknown>);
  }
}
