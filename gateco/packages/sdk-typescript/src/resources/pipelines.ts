/**
 * Pipelines resource -- CRUD + runs.
 */

import type { GatecoClient } from "../client.js";
import type { Page } from "../pagination.js";
import { parsePage, listAll } from "../pagination.js";
import type { Pipeline, PipelineRun } from "../types/pipelines.js";
import { parsePipeline, parsePipelineRun } from "../types/pipelines.js";

/** Options for creating a pipeline. */
export interface CreatePipelineOptions {
  name: string;
  sourceConnectorId: string;
  envelopeConfig?: Record<string, unknown>;
  schedule?: string;
}

/** Options for updating a pipeline. */
export interface UpdatePipelineOptions {
  name?: string;
  envelopeConfig?: Record<string, unknown>;
  status?: string;
  schedule?: string;
}

/** Namespace for pipeline endpoints. Accessed as `client.pipelines`. */
export class PipelinesResource {
  constructor(private readonly client: GatecoClient) {}

  // ------------------------------------------------------------------
  // List
  // ------------------------------------------------------------------

  /** Fetch a single page of pipelines. */
  async list(page = 1, perPage = 20): Promise<Page<Pipeline>> {
    const raw = await this.client._request("GET", "/api/pipelines", {
      params: { page, per_page: perPage },
    });
    return parsePage(raw, page, perPage, parsePipeline);
  }

  /** Return an async generator that lazily paginates through all pipelines. */
  listAll(perPage = 100): AsyncGenerator<Pipeline, void, undefined> {
    return listAll(
      async (page, pp) =>
        (await this.client._request("GET", "/api/pipelines", {
          params: { page, per_page: pp },
        })) ?? {},
      parsePipeline,
      perPage,
    );
  }

  // ------------------------------------------------------------------
  // CRUD
  // ------------------------------------------------------------------

  /** Get a single pipeline by ID. */
  async get(pipelineId: string): Promise<Pipeline> {
    const data = await this.client._request("GET", `/api/pipelines/${pipelineId}`);
    return parsePipeline(data as Record<string, unknown>);
  }

  /** Create a new pipeline. */
  async create(options: CreatePipelineOptions): Promise<Pipeline> {
    const body: Record<string, unknown> = {
      name: options.name,
      source_connector_id: options.sourceConnectorId,
    };
    if (options.envelopeConfig !== undefined) body["envelope_config"] = options.envelopeConfig;
    if (options.schedule !== undefined) body["schedule"] = options.schedule;

    const data = await this.client._request("POST", "/api/pipelines", { json: body });
    return parsePipeline(data as Record<string, unknown>);
  }

  /** Update an existing pipeline. */
  async update(pipelineId: string, options: UpdatePipelineOptions = {}): Promise<Pipeline> {
    const body: Record<string, unknown> = {};
    if (options.name !== undefined) body["name"] = options.name;
    if (options.envelopeConfig !== undefined) body["envelope_config"] = options.envelopeConfig;
    if (options.status !== undefined) body["status"] = options.status;
    if (options.schedule !== undefined) body["schedule"] = options.schedule;

    const data = await this.client._request("PATCH", `/api/pipelines/${pipelineId}`, {
      json: body,
    });
    return parsePipeline(data as Record<string, unknown>);
  }

  // ------------------------------------------------------------------
  // Runs
  // ------------------------------------------------------------------

  /** List runs for a pipeline. */
  async getRuns(pipelineId: string): Promise<PipelineRun[]> {
    const raw = await this.client._request("GET", `/api/pipelines/${pipelineId}/runs`);
    const itemsRaw = (raw && Array.isArray((raw as Record<string, unknown>)["data"])
      ? (raw as Record<string, unknown>)["data"]
      : []) as Record<string, unknown>[];
    return itemsRaw.map(parsePipelineRun);
  }

  /** Trigger a pipeline run. */
  async run(pipelineId: string): Promise<Record<string, unknown>> {
    const data = await this.client._request("POST", `/api/pipelines/${pipelineId}/run`);
    return (data as Record<string, unknown>) ?? {};
  }
}
