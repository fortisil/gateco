/**
 * Gateco SDK client -- the main entry point for interacting with the Gateco API.
 */

import { TokenManager } from "./auth.js";
import { AuthenticationError } from "./errors.js";
import { Transport } from "./transport.js";
import type { TokenResponse } from "./types/auth.js";
import { parseTokenResponse } from "./types/auth.js";
import { AuthResource } from "./resources/auth.js";
import { ConnectorsResource } from "./resources/connectors.js";
import { IngestionResource } from "./resources/ingestion.js";
import { RetrievalsResource } from "./resources/retrievals.js";
import { PoliciesResource } from "./resources/policies.js";
import { IdentityProvidersResource } from "./resources/identity-providers.js";
import { PrincipalsResource } from "./resources/principals.js";
import { DataCatalogResource } from "./resources/data-catalog.js";
import { PipelinesResource } from "./resources/pipelines.js";
import { BillingResource } from "./resources/billing.js";
import { AuditResource } from "./resources/audit.js";
import { SimulatorResource } from "./resources/simulator.js";
import { DashboardResource } from "./resources/dashboard.js";
import { RetroactiveResource } from "./resources/retroactive.js";

/** Options for creating a GatecoClient instance. */
export interface GatecoClientOptions {
  /** Root URL of the Gateco API. */
  baseUrl?: string;
  /** Optional static API key (mutually exclusive with login flow). */
  apiKey?: string;
  /** HTTP request timeout in milliseconds. */
  timeout?: number;
  /** Maximum automatic retries for 429 / 5xx responses. */
  maxRetries?: number;
  /** Multiplier for exponential back-off between retries. */
  retryBackoffFactor?: number;
}

/** Internal request options. */
export interface InternalRequestOptions {
  json?: Record<string, unknown>;
  params?: Record<string, string | number | boolean | undefined>;
  authenticate?: boolean;
}

/**
 * Client for the Gateco API.
 *
 * @example
 * ```ts
 * const client = new GatecoClient({ baseUrl: "https://api.gateco.dev" });
 * await client.login("user@example.com", "secret");
 * const page = await client.connectors.list();
 * console.log(page.items);
 * client.close();
 * ```
 */
export class GatecoClient {
  /** @internal */
  readonly _transport: Transport;
  /** @internal */
  readonly _tokenManager: TokenManager;

  private _auth: AuthResource | undefined;
  private _connectors: ConnectorsResource | undefined;
  private _ingest: IngestionResource | undefined;
  private _retrievals: RetrievalsResource | undefined;
  private _policies: PoliciesResource | undefined;
  private _identityProviders: IdentityProvidersResource | undefined;
  private _principals: PrincipalsResource | undefined;
  private _dataCatalog: DataCatalogResource | undefined;
  private _pipelines: PipelinesResource | undefined;
  private _billing: BillingResource | undefined;
  private _audit: AuditResource | undefined;
  private _simulator: SimulatorResource | undefined;
  private _dashboard: DashboardResource | undefined;
  private _retroactive: RetroactiveResource | undefined;

  constructor(options: GatecoClientOptions = {}) {
    this._transport = new Transport(options.baseUrl ?? "http://localhost:8000", {
      timeout: options.timeout,
      maxRetries: options.maxRetries,
      retryBackoffFactor: options.retryBackoffFactor,
    });
    this._tokenManager = new TokenManager({ apiKey: options.apiKey });
  }

  // ------------------------------------------------------------------
  // Resource namespaces (lazy)
  // ------------------------------------------------------------------

  /** Authentication operations. */
  get auth(): AuthResource {
    if (this._auth === undefined) {
      this._auth = new AuthResource(this);
    }
    return this._auth;
  }

  /** Connector CRUD and management. */
  get connectors(): ConnectorsResource {
    if (this._connectors === undefined) {
      this._connectors = new ConnectorsResource(this);
    }
    return this._connectors;
  }

  /** Document ingestion operations. */
  get ingest(): IngestionResource {
    if (this._ingest === undefined) {
      this._ingest = new IngestionResource(this);
    }
    return this._ingest;
  }

  /** Permission-gated retrieval operations. */
  get retrievals(): RetrievalsResource {
    if (this._retrievals === undefined) {
      this._retrievals = new RetrievalsResource(this);
    }
    return this._retrievals;
  }

  /** Policy management operations. */
  get policies(): PoliciesResource {
    if (this._policies === undefined) {
      this._policies = new PoliciesResource(this);
    }
    return this._policies;
  }

  /** Identity provider CRUD and sync. */
  get identityProviders(): IdentityProvidersResource {
    if (this._identityProviders === undefined) {
      this._identityProviders = new IdentityProvidersResource(this);
    }
    return this._identityProviders;
  }

  /** Principal listing and detail. */
  get principals(): PrincipalsResource {
    if (this._principals === undefined) {
      this._principals = new PrincipalsResource(this);
    }
    return this._principals;
  }

  /** Data catalog operations. */
  get dataCatalog(): DataCatalogResource {
    if (this._dataCatalog === undefined) {
      this._dataCatalog = new DataCatalogResource(this);
    }
    return this._dataCatalog;
  }

  /** Pipeline CRUD and run management. */
  get pipelines(): PipelinesResource {
    if (this._pipelines === undefined) {
      this._pipelines = new PipelinesResource(this);
    }
    return this._pipelines;
  }

  /** Billing, plans, usage, invoices, and checkout. */
  get billing(): BillingResource {
    if (this._billing === undefined) {
      this._billing = new BillingResource(this);
    }
    return this._billing;
  }

  /** Audit log operations. */
  get audit(): AuditResource {
    if (this._audit === undefined) {
      this._audit = new AuditResource(this);
    }
    return this._audit;
  }

  /** Access simulator operations. */
  get simulator(): SimulatorResource {
    if (this._simulator === undefined) {
      this._simulator = new SimulatorResource(this);
    }
    return this._simulator;
  }

  /** Dashboard statistics. */
  get dashboard(): DashboardResource {
    if (this._dashboard === undefined) {
      this._dashboard = new DashboardResource(this);
    }
    return this._dashboard;
  }

  /** Retroactive registration operations. */
  get retroactive(): RetroactiveResource {
    if (this._retroactive === undefined) {
      this._retroactive = new RetroactiveResource(this);
    }
    return this._retroactive;
  }

  // ------------------------------------------------------------------
  // Convenience auth methods on the client itself
  // ------------------------------------------------------------------

  /** Shortcut for `client.auth.login(...)`. */
  async login(email: string, password: string): Promise<TokenResponse> {
    return this.auth.login(email, password);
  }

  /** Shortcut for `client.auth.signup(...)`. */
  async signup(
    name: string,
    email: string,
    password: string,
    organizationName: string,
  ): Promise<TokenResponse> {
    return this.auth.signup(name, email, password, organizationName);
  }

  // ------------------------------------------------------------------
  // Internal request with auto-refresh
  // ------------------------------------------------------------------

  /**
   * Send an authenticated request, refreshing the token if needed.
   *
   * @internal
   */
  async _request(
    method: string,
    path: string,
    options: InternalRequestOptions = {},
  ): Promise<Record<string, unknown> | null> {
    const authenticate = options.authenticate !== false;
    const headers: Record<string, string> = {};

    if (authenticate) {
      // Proactively refresh if token is near expiry.
      if (this._tokenManager.needsRefresh()) {
        await this._doRefresh();
      }
      Object.assign(headers, this._tokenManager.getAuthHeaders());
    }

    try {
      return await this._transport.request(method, path, {
        json: options.json,
        params: options.params,
        headers,
      });
    } catch (err) {
      if (err instanceof AuthenticationError && authenticate && this._tokenManager.getRefreshToken()) {
        // Fallback refresh on 401: token may have been revoked server-side.
        await this._doRefresh();
        const refreshedHeaders = this._tokenManager.getAuthHeaders();
        return this._transport.request(method, path, {
          json: options.json,
          params: options.params,
          headers: refreshedHeaders,
        });
      }
      throw err;
    }
  }

  /** Perform a token refresh, guarded against concurrent refreshes. */
  private async _doRefresh(): Promise<void> {
    await this._tokenManager.guardRefresh(async () => {
      // Double-check after acquiring the guard
      if (!this._tokenManager.needsRefresh()) {
        return;
      }
      const refreshToken = this._tokenManager.getRefreshToken();
      if (refreshToken === undefined) {
        return;
      }
      const data = await this._transport.request("POST", "/api/auth/refresh", {
        json: { refresh_token: refreshToken },
      });
      if (data) {
        const tokenResp = parseTokenResponse(data);
        this._tokenManager.setTokens(
          tokenResp.access_token,
          tokenResp.refresh_token,
        );
      }
    });
  }

  // ------------------------------------------------------------------
  // Cleanup
  // ------------------------------------------------------------------

  /** Close the underlying HTTP transport. */
  close(): void {
    this._transport.close();
  }
}
