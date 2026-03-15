/**
 * Auth resource -- login, signup, refresh, logout.
 */

import type { GatecoClient } from "../client.js";
import type { TokenResponse } from "../types/auth.js";
import { parseTokenResponse } from "../types/auth.js";
import { AuthenticationError } from "../errors.js";

/** Namespace for authentication endpoints. Accessed as `client.auth`. */
export class AuthResource {
  constructor(private readonly client: GatecoClient) {}

  /**
   * Authenticate with email and password.
   *
   * Stores the returned tokens in the client for subsequent requests.
   */
  async login(email: string, password: string): Promise<TokenResponse> {
    const data = await this.client._request("POST", "/api/auth/login", {
      json: { email, password },
      authenticate: false,
    });
    const tokenResp = parseTokenResponse(data as Record<string, unknown>);
    this.client._tokenManager.setTokens(
      tokenResp.access_token,
      tokenResp.refresh_token,
    );
    return tokenResp;
  }

  /**
   * Create a new account and organisation.
   *
   * Stores the returned tokens in the client for subsequent requests.
   */
  async signup(
    name: string,
    email: string,
    password: string,
    organizationName: string,
  ): Promise<TokenResponse> {
    const data = await this.client._request("POST", "/api/auth/signup", {
      json: {
        name,
        email,
        password,
        organization_name: organizationName,
      },
      authenticate: false,
    });
    const tokenResp = parseTokenResponse(data as Record<string, unknown>);
    this.client._tokenManager.setTokens(
      tokenResp.access_token,
      tokenResp.refresh_token,
    );
    return tokenResp;
  }

  /**
   * Refresh the current access token using the stored refresh token.
   *
   * Updates stored tokens with the new pair.
   */
  async refresh(): Promise<TokenResponse> {
    const refreshToken = this.client._tokenManager.getRefreshToken();
    if (refreshToken === undefined) {
      throw new AuthenticationError("No refresh token available");
    }

    const data = await this.client._request("POST", "/api/auth/refresh", {
      json: { refresh_token: refreshToken },
      authenticate: false,
    });
    const tokenResp = parseTokenResponse(data as Record<string, unknown>);
    this.client._tokenManager.setTokens(
      tokenResp.access_token,
      tokenResp.refresh_token,
    );
    return tokenResp;
  }

  /** Invalidate the current session. */
  async logout(): Promise<void> {
    await this.client._request("POST", "/api/auth/logout");
    this.client._tokenManager.setTokens("", undefined);
  }
}
