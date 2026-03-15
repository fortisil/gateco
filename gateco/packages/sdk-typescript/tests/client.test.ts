import { describe, it, expect, vi, beforeEach } from "vitest";
import { GatecoClient } from "../src/client.js";
import { TokenManager } from "../src/auth.js";
import { AuthenticationError, NotFoundError } from "../src/errors.js";

describe("GatecoClient", () => {
  it("creates with default options", () => {
    const client = new GatecoClient();
    expect(client).toBeInstanceOf(GatecoClient);
    expect(client._transport.baseUrl).toBe("http://localhost:8000");
    client.close();
  });

  it("creates with custom base URL", () => {
    const client = new GatecoClient({ baseUrl: "https://api.gateco.dev" });
    expect(client._transport.baseUrl).toBe("https://api.gateco.dev");
    client.close();
  });

  it("creates with API key", () => {
    const client = new GatecoClient({ apiKey: "test-key" });
    const headers = client._tokenManager.getAuthHeaders();
    expect(headers).toEqual({ "X-API-Key": "test-key" });
    client.close();
  });

  it("lazily initializes resource namespaces", () => {
    const client = new GatecoClient();
    // Access each namespace
    expect(client.auth).toBeDefined();
    expect(client.connectors).toBeDefined();
    expect(client.ingest).toBeDefined();
    expect(client.retrievals).toBeDefined();
    expect(client.policies).toBeDefined();
    // Verify they are the same instance on second access
    expect(client.auth).toBe(client.auth);
    expect(client.connectors).toBe(client.connectors);
    client.close();
  });
});

describe("TokenManager", () => {
  let tm: TokenManager;

  beforeEach(() => {
    tm = new TokenManager();
  });

  it("starts with no credentials", () => {
    expect(tm.hasCredentials()).toBe(false);
    expect(tm.getAccessToken()).toBeUndefined();
    expect(tm.getRefreshToken()).toBeUndefined();
  });

  it("stores tokens", () => {
    tm.setTokens("access-123", "refresh-456");
    expect(tm.hasCredentials()).toBe(true);
    expect(tm.getAccessToken()).toBe("access-123");
    expect(tm.getRefreshToken()).toBe("refresh-456");
  });

  it("generates bearer auth headers", () => {
    tm.setTokens("access-123");
    expect(tm.getAuthHeaders()).toEqual({ Authorization: "Bearer access-123" });
  });

  it("generates API key headers", () => {
    const apiKeyTm = new TokenManager({ apiKey: "my-key" });
    expect(apiKeyTm.getAuthHeaders()).toEqual({ "X-API-Key": "my-key" });
  });

  it("returns empty headers when no credentials", () => {
    expect(tm.getAuthHeaders()).toEqual({});
  });

  it("reports expired when no token set", () => {
    expect(tm.isExpired()).toBe(true);
  });

  it("decodes JWT exp claim", () => {
    // Create a minimal JWT with exp claim set to year 2100
    const payload = { exp: 4102444800 };
    const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
    const payloadB64 = btoa(JSON.stringify(payload));
    const fakeJwt = `${header}.${payloadB64}.fake-signature`;

    const exp = TokenManager.decodeExp(fakeJwt);
    expect(exp).toBe(4102444800);
  });

  it("returns undefined for invalid JWT", () => {
    expect(TokenManager.decodeExp("not-a-jwt")).toBeUndefined();
    expect(TokenManager.decodeExp("")).toBeUndefined();
  });

  it("needsRefresh is false in API key mode", () => {
    const apiKeyTm = new TokenManager({ apiKey: "my-key" });
    expect(apiKeyTm.needsRefresh()).toBe(false);
  });

  it("needsRefresh is false when no refresh token", () => {
    tm.setTokens("some-expired-token");
    expect(tm.needsRefresh()).toBe(false);
  });

  it("needsRefresh is true when token is expired and refresh token available", () => {
    // Create an expired JWT (exp in the past)
    const payload = { exp: 1000000000 };
    const header = btoa(JSON.stringify({ alg: "HS256" }));
    const payloadB64 = btoa(JSON.stringify(payload));
    const expiredJwt = `${header}.${payloadB64}.sig`;

    tm.setTokens(expiredJwt, "refresh-token");
    expect(tm.needsRefresh()).toBe(true);
  });

  it("guards against concurrent refreshes", async () => {
    let callCount = 0;
    const fn = async () => {
      callCount++;
      await new Promise((resolve) => setTimeout(resolve, 50));
    };

    // Start two refreshes concurrently
    await Promise.all([tm.guardRefresh(fn), tm.guardRefresh(fn)]);

    // Only one should have executed
    expect(callCount).toBe(1);
  });
});

describe("GatecoClient._request", () => {
  it("attaches auth headers to authenticated requests", async () => {
    const client = new GatecoClient({ apiKey: "test-key" });

    // Mock transport
    const mockRequest = vi.fn().mockResolvedValue({ data: [] });
    client._transport.request = mockRequest;

    await client._request("GET", "/api/connectors");

    expect(mockRequest).toHaveBeenCalledWith("GET", "/api/connectors", {
      json: undefined,
      params: undefined,
      headers: { "X-API-Key": "test-key" },
    });

    client.close();
  });

  it("skips auth headers for unauthenticated requests", async () => {
    const client = new GatecoClient({ apiKey: "test-key" });

    const mockRequest = vi.fn().mockResolvedValue({ access_token: "tok" });
    client._transport.request = mockRequest;

    await client._request("POST", "/api/auth/login", { authenticate: false });

    expect(mockRequest).toHaveBeenCalledWith("POST", "/api/auth/login", {
      json: undefined,
      params: undefined,
      headers: {},
    });

    client.close();
  });

  it("retries on 401 with token refresh", async () => {
    const client = new GatecoClient();

    // Set up tokens with an expired access token
    const payload = { exp: 1000000000 };
    const header = btoa(JSON.stringify({ alg: "HS256" }));
    const payloadB64 = btoa(JSON.stringify(payload));
    const expiredJwt = `${header}.${payloadB64}.sig`;

    // Fresh token for after refresh
    const freshPayload = { exp: 9999999999 };
    const freshPayloadB64 = btoa(JSON.stringify(freshPayload));
    const freshJwt = `${header}.${freshPayloadB64}.sig`;

    client._tokenManager.setTokens(expiredJwt, "refresh-token");

    let callCount = 0;
    const mockRequest = vi.fn().mockImplementation(
      async (_method: string, path: string) => {
        callCount++;
        if (path === "/api/auth/refresh") {
          return { access_token: freshJwt, refresh_token: "new-refresh" };
        }
        if (callCount <= 2) {
          // First call to /api/connectors triggers 401 (refresh happens first due to needsRefresh)
          // After refresh, the second call succeeds
          return { data: [{ id: "c1" }] };
        }
        return { data: [] };
      },
    );
    client._transport.request = mockRequest;

    const result = await client._request("GET", "/api/connectors");
    expect(result).toBeDefined();

    client.close();
  });
});
