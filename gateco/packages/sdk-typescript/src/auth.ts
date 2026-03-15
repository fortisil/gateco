/**
 * Token management for the Gateco SDK.
 *
 * Supports both JWT-based auth (login/signup flow with refresh) and static
 * API-key auth.
 */

const EXPIRY_BUFFER_SECONDS = 30;

/**
 * Manages access and refresh tokens for authenticated API requests.
 *
 * In api-key mode the manager produces a static `X-API-Key` header and
 * never attempts token refresh. In JWT mode (populated via `setTokens`)
 * it decodes the JWT `exp` claim to decide when a refresh is needed.
 */
export class TokenManager {
  private readonly apiKey: string | undefined;
  private accessToken: string | undefined;
  private refreshTokenValue: string | undefined;
  private refreshInProgress: Promise<void> | undefined;

  constructor(options: { apiKey?: string } = {}) {
    this.apiKey = options.apiKey;
  }

  // ------------------------------------------------------------------
  // Token storage
  // ------------------------------------------------------------------

  /** Store a fresh pair of JWT tokens. */
  setTokens(accessToken: string, refreshToken?: string): void {
    this.accessToken = accessToken;
    if (refreshToken !== undefined) {
      this.refreshTokenValue = refreshToken;
    }
  }

  /** Get the current access token. */
  getAccessToken(): string | undefined {
    return this.accessToken;
  }

  /** Get the current refresh token. */
  getRefreshToken(): string | undefined {
    return this.refreshTokenValue;
  }

  /** Return `true` if any form of credential is available. */
  hasCredentials(): boolean {
    return this.apiKey !== undefined || this.accessToken !== undefined;
  }

  // ------------------------------------------------------------------
  // Expiry helpers
  // ------------------------------------------------------------------

  /** Return `true` if the current access token is expired (with 30s buffer). */
  isExpired(): boolean {
    if (this.accessToken === undefined) {
      return true;
    }
    const exp = TokenManager.decodeExp(this.accessToken);
    if (exp === undefined) {
      return false; // cannot determine; assume valid
    }
    return Date.now() / 1000 >= exp - EXPIRY_BUFFER_SECONDS;
  }

  /**
   * Return `true` if the access token should be refreshed.
   *
   * This is `true` when we are in JWT mode, the token is expired (or
   * about to expire), and a refresh token is available.
   */
  needsRefresh(): boolean {
    if (this.apiKey !== undefined) {
      return false;
    }
    if (this.refreshTokenValue === undefined) {
      return false;
    }
    return this.isExpired();
  }

  // ------------------------------------------------------------------
  // Header generation
  // ------------------------------------------------------------------

  /**
   * Build the authentication headers for the next request.
   *
   * @returns A record with either an `Authorization` bearer header or an
   *   `X-API-Key` header, or an empty record if no credentials are set.
   */
  getAuthHeaders(): Record<string, string> {
    if (this.apiKey !== undefined) {
      return { "X-API-Key": this.apiKey };
    }
    if (this.accessToken !== undefined) {
      return { Authorization: `Bearer ${this.accessToken}` };
    }
    return {};
  }

  // ------------------------------------------------------------------
  // Concurrency guard
  // ------------------------------------------------------------------

  /**
   * Guard against concurrent refresh calls.
   *
   * If a refresh is already in progress, returns the existing promise.
   * Otherwise calls the provided function and stores the promise until
   * it resolves.
   */
  async guardRefresh(fn: () => Promise<void>): Promise<void> {
    if (this.refreshInProgress) {
      return this.refreshInProgress;
    }
    this.refreshInProgress = fn().finally(() => {
      this.refreshInProgress = undefined;
    });
    return this.refreshInProgress;
  }

  // ------------------------------------------------------------------
  // JWT decoding (minimal, no verification)
  // ------------------------------------------------------------------

  /** Extract the `exp` claim from a JWT without verifying the signature. */
  static decodeExp(token: string): number | undefined {
    try {
      const parts = token.split(".");
      if (parts.length < 2) {
        return undefined;
      }
      const payloadB64 = parts[1]!;
      // Add padding
      const padded = payloadB64 + "=".repeat((4 - (payloadB64.length % 4)) % 4);
      const payloadJson = atob(padded.replace(/-/g, "+").replace(/_/g, "/"));
      const payload: Record<string, unknown> = JSON.parse(payloadJson);
      const exp = payload["exp"];
      return typeof exp === "number" ? exp : undefined;
    } catch {
      return undefined;
    }
  }
}
