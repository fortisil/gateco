/**
 * Principals resource -- list + detail.
 */

import type { GatecoClient } from "../client.js";
import type { Page } from "../pagination.js";
import { parsePage, listAll } from "../pagination.js";
import type { Principal } from "../types/principals.js";
import { parsePrincipal } from "../types/principals.js";

/** Namespace for principal endpoints. Accessed as `client.principals`. */
export class PrincipalsResource {
  constructor(private readonly client: GatecoClient) {}

  // ------------------------------------------------------------------
  // List
  // ------------------------------------------------------------------

  /** Fetch a single page of principals. */
  async list(page = 1, perPage = 20): Promise<Page<Principal>> {
    const raw = await this.client._request("GET", "/api/principals", {
      params: { page, per_page: perPage },
    });
    return parsePage(raw, page, perPage, parsePrincipal);
  }

  /** Return an async generator that lazily paginates through all principals. */
  listAll(perPage = 100): AsyncGenerator<Principal, void, undefined> {
    return listAll(
      async (page, pp) =>
        (await this.client._request("GET", "/api/principals", {
          params: { page, per_page: pp },
        })) ?? {},
      parsePrincipal,
      perPage,
    );
  }

  // ------------------------------------------------------------------
  // Detail
  // ------------------------------------------------------------------

  /** Get a single principal by ID. */
  async get(principalId: string): Promise<Principal> {
    const data = await this.client._request("GET", `/api/principals/${principalId}`);
    return parsePrincipal(data as Record<string, unknown>);
  }
}
