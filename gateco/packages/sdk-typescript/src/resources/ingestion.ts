/**
 * Ingestion resource -- document and batch ingestion.
 */

import type { GatecoClient } from "../client.js";
import type { IngestDocumentResponse, BatchIngestResponse } from "../types/ingestion.js";
import { parseIngestDocumentResponse, parseBatchIngestResponse } from "../types/ingestion.js";

/** Options for single document ingestion. */
export interface IngestDocumentOptions {
  classification?: string;
  sensitivity?: string;
  domain?: string;
  labels?: string[];
  metadata?: Record<string, unknown>;
  ownerPrincipalId?: string;
  idempotencyKey?: string;
}

/** Namespace for ingestion endpoints. Accessed as `client.ingest`. */
export class IngestionResource {
  constructor(private readonly client: GatecoClient) {}

  /**
   * Ingest a single document.
   *
   * Requires a Tier 1 connector (pgvector, supabase, neon, pinecone, qdrant).
   *
   * @param connectorId - Target connector (must be Tier 1).
   * @param externalResourceId - Caller-defined resource identifier.
   * @param text - Document text to embed and store.
   * @param options - Optional classification, sensitivity, labels, metadata, etc.
   */
  async document(
    connectorId: string,
    externalResourceId: string,
    text: string,
    options: IngestDocumentOptions = {},
  ): Promise<IngestDocumentResponse> {
    const body: Record<string, unknown> = {
      connector_id: connectorId,
      external_resource_id: externalResourceId,
      text,
    };
    if (options.classification !== undefined) body["classification"] = options.classification;
    if (options.sensitivity !== undefined) body["sensitivity"] = options.sensitivity;
    if (options.domain !== undefined) body["domain"] = options.domain;
    if (options.labels !== undefined) body["labels"] = options.labels;
    if (options.metadata !== undefined) body["metadata"] = options.metadata;
    if (options.ownerPrincipalId !== undefined) body["owner_principal_id"] = options.ownerPrincipalId;
    if (options.idempotencyKey !== undefined) body["idempotency_key"] = options.idempotencyKey;

    const data = await this.client._request("POST", "/api/v1/ingest", { json: body });
    return parseIngestDocumentResponse(data as Record<string, unknown>);
  }

  /**
   * Ingest a batch of documents in a single request.
   *
   * Requires a Tier 1 connector (pgvector, supabase, neon, pinecone, qdrant).
   *
   * @param connectorId - Target connector (must be Tier 1).
   * @param records - List of record objects, each containing at minimum
   *   `external_resource_id` and `text`.
   * @param idempotencyKey - Optional idempotency key for safe retries.
   */
  async batch(
    connectorId: string,
    records: Record<string, unknown>[],
    idempotencyKey?: string,
  ): Promise<BatchIngestResponse> {
    const body: Record<string, unknown> = {
      connector_id: connectorId,
      records,
    };
    if (idempotencyKey !== undefined) {
      body["idempotency_key"] = idempotencyKey;
    }

    const data = await this.client._request("POST", "/api/v1/ingest/batch", { json: body });
    return parseBatchIngestResponse(data as Record<string, unknown>);
  }
}
