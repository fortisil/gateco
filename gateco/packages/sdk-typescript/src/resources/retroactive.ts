/**
 * Retroactive registration resource -- register unmanaged vectors.
 */

import type { GatecoClient } from "../client.js";
import type { RetroactiveRegisterResponse } from "../types/retroactive.js";
import { parseRetroactiveRegisterResponse } from "../types/retroactive.js";

/** Options for retroactive registration. */
export interface RetroactiveRegisterOptions {
  connectorId: string;
  scanLimit?: number;
  defaultClassification?: string;
  defaultSensitivity?: string;
  defaultDomain?: string;
  defaultLabels?: string[];
  groupingStrategy?: string;
  groupingPattern?: string;
  dryRun?: boolean;
}

/** Namespace for retroactive registration endpoints. Accessed as `client.retroactive`. */
export class RetroactiveResource {
  constructor(private readonly client: GatecoClient) {}

  /**
   * Scan a connector's vector DB and register unmanaged vectors as gated resources.
   *
   * Requires a Tier 1 connector (pgvector, supabase, neon, pinecone, qdrant).
   */
  async register(options: RetroactiveRegisterOptions): Promise<RetroactiveRegisterResponse> {
    const body: Record<string, unknown> = {
      connector_id: options.connectorId,
    };
    if (options.scanLimit !== undefined) body["scan_limit"] = options.scanLimit;
    if (options.defaultClassification !== undefined)
      body["default_classification"] = options.defaultClassification;
    if (options.defaultSensitivity !== undefined)
      body["default_sensitivity"] = options.defaultSensitivity;
    if (options.defaultDomain !== undefined) body["default_domain"] = options.defaultDomain;
    if (options.defaultLabels !== undefined) body["default_labels"] = options.defaultLabels;
    if (options.groupingStrategy !== undefined)
      body["grouping_strategy"] = options.groupingStrategy;
    if (options.groupingPattern !== undefined)
      body["grouping_pattern"] = options.groupingPattern;
    if (options.dryRun !== undefined) body["dry_run"] = options.dryRun;

    const data = await this.client._request("POST", "/api/v1/retroactive-register", {
      json: body,
    });
    return parseRetroactiveRegisterResponse(data as Record<string, unknown>);
  }
}
