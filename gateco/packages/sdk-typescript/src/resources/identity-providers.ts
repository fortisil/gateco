/**
 * Identity providers resource -- CRUD + sync.
 */

import type { GatecoClient } from "../client.js";
import type { Page } from "../pagination.js";
import { parsePage, listAll } from "../pagination.js";
import type { IdentityProvider } from "../types/identity-providers.js";
import { parseIdentityProvider } from "../types/identity-providers.js";

/** Options for creating an identity provider. */
export interface CreateIdentityProviderOptions {
  name: string;
  type: string;
  config?: Record<string, unknown>;
  syncConfig?: Record<string, unknown>;
}

/** Options for updating an identity provider. */
export interface UpdateIdentityProviderOptions {
  name?: string;
  config?: Record<string, unknown>;
  syncConfig?: Record<string, unknown>;
}

/** Namespace for identity provider endpoints. Accessed as `client.identityProviders`. */
export class IdentityProvidersResource {
  constructor(private readonly client: GatecoClient) {}

  // ------------------------------------------------------------------
  // List
  // ------------------------------------------------------------------

  /** Fetch a single page of identity providers. */
  async list(page = 1, perPage = 20): Promise<Page<IdentityProvider>> {
    const raw = await this.client._request("GET", "/api/identity-providers", {
      params: { page, per_page: perPage },
    });
    return parsePage(raw, page, perPage, parseIdentityProvider);
  }

  /** Return an async generator that lazily paginates through all identity providers. */
  listAll(perPage = 100): AsyncGenerator<IdentityProvider, void, undefined> {
    return listAll(
      async (page, pp) =>
        (await this.client._request("GET", "/api/identity-providers", {
          params: { page, per_page: pp },
        })) ?? {},
      parseIdentityProvider,
      perPage,
    );
  }

  // ------------------------------------------------------------------
  // CRUD
  // ------------------------------------------------------------------

  /** Get a single identity provider by ID. */
  async get(idpId: string): Promise<IdentityProvider> {
    const data = await this.client._request("GET", `/api/identity-providers/${idpId}`);
    return parseIdentityProvider(data as Record<string, unknown>);
  }

  /** Create a new identity provider. */
  async create(options: CreateIdentityProviderOptions): Promise<IdentityProvider> {
    const body: Record<string, unknown> = {
      name: options.name,
      type: options.type,
    };
    if (options.config !== undefined) body["config"] = options.config;
    if (options.syncConfig !== undefined) body["sync_config"] = options.syncConfig;

    const data = await this.client._request("POST", "/api/identity-providers", { json: body });
    return parseIdentityProvider(data as Record<string, unknown>);
  }

  /** Update an existing identity provider. */
  async update(
    idpId: string,
    options: UpdateIdentityProviderOptions = {},
  ): Promise<IdentityProvider> {
    const body: Record<string, unknown> = {};
    if (options.name !== undefined) body["name"] = options.name;
    if (options.config !== undefined) body["config"] = options.config;
    if (options.syncConfig !== undefined) body["sync_config"] = options.syncConfig;

    const data = await this.client._request("PATCH", `/api/identity-providers/${idpId}`, {
      json: body,
    });
    return parseIdentityProvider(data as Record<string, unknown>);
  }

  /** Delete an identity provider. */
  async delete(idpId: string): Promise<void> {
    await this.client._request("DELETE", `/api/identity-providers/${idpId}`);
  }

  // ------------------------------------------------------------------
  // Actions
  // ------------------------------------------------------------------

  /** Trigger a sync for an identity provider. */
  async sync(idpId: string): Promise<Record<string, unknown>> {
    const data = await this.client._request(
      "POST",
      `/api/identity-providers/${idpId}/sync`,
    );
    return (data as Record<string, unknown>) ?? {};
  }
}
