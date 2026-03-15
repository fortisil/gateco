/**
 * Simulator resource -- dry-run policy evaluation.
 */

import type { GatecoClient } from "../client.js";
import type { SimulationResult } from "../types/simulator.js";
import { parseSimulationResult } from "../types/simulator.js";

/** Options for running a simulation. */
export interface RunSimulationOptions {
  principalId: string;
  query?: string;
  connectorId?: string;
  resourceIds?: string[];
}

/** Namespace for access simulator endpoints. Accessed as `client.simulator`. */
export class SimulatorResource {
  constructor(private readonly client: GatecoClient) {}

  /** Run a dry-run policy simulation for a principal against resources. */
  async run(options: RunSimulationOptions): Promise<SimulationResult> {
    const body: Record<string, unknown> = {
      principal_id: options.principalId,
    };
    if (options.query !== undefined) body["query"] = options.query;
    if (options.connectorId !== undefined) body["connector_id"] = options.connectorId;
    if (options.resourceIds !== undefined) body["resource_ids"] = options.resourceIds;

    const data = await this.client._request("POST", "/api/simulator/run", { json: body });
    return parseSimulationResult(data as Record<string, unknown>);
  }
}
