/**
 * Low-level HTTP transport layer using native fetch.
 *
 * Handles JSON serialisation, error mapping, retries (429 + 5xx), and
 * Retry-After back-off.
 */

import { GatecoError, RateLimitError, errorFromResponse } from "./errors.js";

const DEFAULT_TIMEOUT = 30_000;
const DEFAULT_MAX_RETRIES = 2;
const DEFAULT_BACKOFF_FACTOR = 0.5;

/** Options for creating a Transport instance. */
export interface TransportOptions {
  /** Request timeout in milliseconds. */
  timeout?: number;
  /** Maximum number of automatic retries for 429 / 5xx responses. */
  maxRetries?: number;
  /** Multiplier for exponential back-off between retries. */
  retryBackoffFactor?: number;
}

/** Options for a single request. */
export interface RequestOptions {
  /** JSON-serialisable request body. */
  json?: Record<string, unknown>;
  /** Query parameters. */
  params?: Record<string, string | number | boolean | undefined>;
  /** Extra headers merged with defaults. */
  headers?: Record<string, string>;
}

/**
 * Async HTTP transport that wraps native `fetch`.
 *
 * Automatically retries on 429 (respecting Retry-After) and 5xx
 * responses up to `maxRetries` times with exponential back-off.
 */
export class Transport {
  readonly baseUrl: string;
  readonly timeout: number;
  readonly maxRetries: number;
  readonly retryBackoffFactor: number;

  constructor(baseUrl: string, options: TransportOptions = {}) {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this.timeout = options.timeout ?? DEFAULT_TIMEOUT;
    this.maxRetries = options.maxRetries ?? DEFAULT_MAX_RETRIES;
    this.retryBackoffFactor = options.retryBackoffFactor ?? DEFAULT_BACKOFF_FACTOR;
  }

  /**
   * Send an HTTP request and return the parsed JSON body.
   *
   * @param method - HTTP method (GET, POST, etc.).
   * @param path - URL path (will be joined to baseUrl).
   * @param options - Request options.
   * @returns Parsed JSON response body, or `null` for 204 No Content.
   * @throws GatecoError (or a subclass) when the API returns an error response.
   */
  async request(
    method: string,
    path: string,
    options: RequestOptions = {},
  ): Promise<Record<string, unknown> | null> {
    let lastError: GatecoError | null = null;

    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      const url = this.buildUrl(path, options.params);

      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...options.headers,
      };

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      let response: Response;
      try {
        response = await fetch(url, {
          method,
          headers,
          body: options.json ? JSON.stringify(options.json) : undefined,
          signal: controller.signal,
        });
      } catch (err) {
        clearTimeout(timeoutId);
        if (err instanceof DOMException && err.name === "AbortError") {
          throw new GatecoError("Request timed out", {
            code: "TIMEOUT",
            statusCode: 0,
          });
        }
        throw new GatecoError(
          `HTTP transport error: ${err instanceof Error ? err.message : String(err)}`,
          { code: "TRANSPORT_ERROR", statusCode: 0 },
        );
      } finally {
        clearTimeout(timeoutId);
      }

      // Success
      if (response.status === 204) {
        return null;
      }
      if (response.status >= 200 && response.status < 300) {
        return (await response.json()) as Record<string, unknown>;
      }

      // Parse error body
      const retryAfter = this.parseRetryAfter(response);
      let body: Record<string, unknown> | null = null;
      try {
        body = (await response.json()) as Record<string, unknown>;
      } catch {
        // body stays null
      }

      lastError = errorFromResponse(response.status, body, retryAfter);

      // Retryable?
      const isLast = attempt >= this.maxRetries;
      if (lastError instanceof RateLimitError && !isLast) {
        const wait = retryAfter ?? this.backoff(attempt);
        await this.sleep(wait * 1000);
        continue;
      }
      if (response.status >= 500 && response.status < 600 && !isLast) {
        await this.sleep(this.backoff(attempt) * 1000);
        continue;
      }

      // Not retryable or retries exhausted
      throw lastError;
    }

    // Should be unreachable, but satisfies the type checker.
    throw lastError ?? new GatecoError("Unexpected transport error");
  }

  /** No-op close for interface compatibility. */
  close(): void {
    // native fetch has no persistent connection to close
  }

  // ------------------------------------------------------------------
  // Helpers
  // ------------------------------------------------------------------

  private buildUrl(
    path: string,
    params?: Record<string, string | number | boolean | undefined>,
  ): string {
    const url = new URL(path, this.baseUrl);
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined) {
          url.searchParams.set(key, String(value));
        }
      }
    }
    return url.toString();
  }

  private backoff(attempt: number): number {
    return this.retryBackoffFactor * 2 ** attempt;
  }

  private parseRetryAfter(response: Response): number | undefined {
    const raw = response.headers.get("Retry-After") ?? response.headers.get("retry-after");
    if (raw === null) {
      return undefined;
    }
    const parsed = parseFloat(raw);
    return isNaN(parsed) ? undefined : parsed;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
