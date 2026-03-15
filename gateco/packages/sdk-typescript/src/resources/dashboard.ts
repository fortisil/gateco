/**
 * Dashboard resource -- aggregated stats.
 */

import type { GatecoClient } from "../client.js";
import type { DashboardStats } from "../types/dashboard.js";
import { parseDashboardStats } from "../types/dashboard.js";

/** Namespace for dashboard endpoints. Accessed as `client.dashboard`. */
export class DashboardResource {
  constructor(private readonly client: GatecoClient) {}

  /** Fetch aggregated dashboard statistics. */
  async getStats(): Promise<DashboardStats> {
    const data = await this.client._request("GET", "/api/dashboard/stats");
    return parseDashboardStats(data as Record<string, unknown>);
  }
}
