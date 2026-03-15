/**
 * Error hierarchy for the Gateco SDK.
 *
 * Maps backend error codes and HTTP status codes to typed exceptions.
 */

/** Base error class for all Gateco SDK errors. */
export class GatecoError extends Error {
  /** Machine-readable error code from the API (e.g. `RESOURCE_NOT_FOUND`). */
  readonly code: string;
  /** HTTP status code returned by the API. */
  readonly statusCode: number;

  constructor(
    message = "An unexpected error occurred",
    options: { code?: string; statusCode?: number } = {},
  ) {
    super(message);
    this.name = "GatecoError";
    this.code = options.code ?? "UNKNOWN_ERROR";
    this.statusCode = options.statusCode ?? 500;
  }
}

/** Raised when the API returns 401 (invalid / expired credentials). */
export class AuthenticationError extends GatecoError {
  constructor(
    message = "Authentication failed",
    options: { code?: string } = {},
  ) {
    super(message, {
      code: options.code ?? "AUTH_INVALID_CREDENTIALS",
      statusCode: 401,
    });
    this.name = "AuthenticationError";
  }
}

/** Raised when the API returns 403 (insufficient permissions). */
export class AuthorizationError extends GatecoError {
  constructor(
    message = "Permission denied",
    options: { code?: string } = {},
  ) {
    super(message, {
      code: options.code ?? "AUTH_PERMISSION_DENIED",
      statusCode: 403,
    });
    this.name = "AuthorizationError";
  }
}

/** Raised when the API returns 404. */
export class NotFoundError extends GatecoError {
  constructor(
    message = "Resource not found",
    options: { code?: string } = {},
  ) {
    super(message, {
      code: options.code ?? "RESOURCE_NOT_FOUND",
      statusCode: 404,
    });
    this.name = "NotFoundError";
  }
}

/** Raised when the API returns 409 (e.g. duplicate resource). */
export class ConflictError extends GatecoError {
  constructor(message = "Conflict", options: { code?: string } = {}) {
    super(message, { code: options.code ?? "CONFLICT", statusCode: 409 });
    this.name = "ConflictError";
  }
}

/**
 * Raised when the API returns 403 with ENTITLEMENT_REQUIRED.
 *
 * The `upgradeTo` field indicates the plan tier that grants the required entitlement.
 */
export class EntitlementError extends GatecoError {
  readonly upgradeTo: string | undefined;

  constructor(
    message = "Entitlement required",
    options: { code?: string; upgradeTo?: string } = {},
  ) {
    super(message, {
      code: options.code ?? "ENTITLEMENT_REQUIRED",
      statusCode: 403,
    });
    this.name = "EntitlementError";
    this.upgradeTo = options.upgradeTo;
  }
}

/**
 * Raised when the API returns 429.
 *
 * The `retryAfter` field indicates seconds to wait before retrying.
 */
export class RateLimitError extends GatecoError {
  readonly retryAfter: number | undefined;

  constructor(
    message = "Rate limit exceeded",
    options: { code?: string; retryAfter?: number } = {},
  ) {
    super(message, {
      code: options.code ?? "RATE_LIMIT_EXCEEDED",
      statusCode: 429,
    });
    this.name = "RateLimitError";
    this.retryAfter = options.retryAfter;
  }
}

/** Raised when the API returns 422 (request validation failure). */
export class ValidationError extends GatecoError {
  constructor(
    message = "Validation error",
    options: { code?: string } = {},
  ) {
    super(message, {
      code: options.code ?? "VALIDATION_ERROR",
      statusCode: 422,
    });
    this.name = "ValidationError";
  }
}

// ---------------------------------------------------------------------------
// Mapping helpers
// ---------------------------------------------------------------------------

const STATUS_TO_ERROR: Record<number, typeof GatecoError> = {
  401: AuthenticationError,
  404: NotFoundError,
  409: ConflictError,
  422: ValidationError,
  429: RateLimitError,
};

const CODE_TO_ERROR: Record<string, typeof GatecoError> = {
  AUTH_INVALID_CREDENTIALS: AuthenticationError,
  AUTH_PERMISSION_DENIED: AuthorizationError,
  ENTITLEMENT_REQUIRED: EntitlementError,
  RESOURCE_NOT_FOUND: NotFoundError,
  CONFLICT: ConflictError,
  VALIDATION_ERROR: ValidationError,
  RATE_LIMIT_EXCEEDED: RateLimitError,
  INTERNAL_ERROR: GatecoError,
};

interface ErrorBody {
  error?: {
    code?: string;
    message?: string;
    upgrade_to?: string;
  };
}

/**
 * Build the most specific `GatecoError` subclass from an API response.
 *
 * @param statusCode - HTTP status code.
 * @param body - Parsed JSON body (may be `null`).
 * @param retryAfter - Value of the `Retry-After` header, if present.
 * @returns An instance of the appropriate `GatecoError` subclass.
 */
export function errorFromResponse(
  statusCode: number,
  body: ErrorBody | null,
  retryAfter?: number,
): GatecoError {
  let code = "UNKNOWN_ERROR";
  let message = "An unexpected error occurred";
  let upgradeTo: string | undefined;

  if (body?.error && typeof body.error === "object") {
    code = body.error.code ?? code;
    message = body.error.message ?? message;
    upgradeTo = body.error.upgrade_to;
  }

  // Prefer code-based lookup, fall back to status-based lookup.
  const ErrorClass = CODE_TO_ERROR[code] ?? STATUS_TO_ERROR[statusCode] ?? GatecoError;

  if (ErrorClass === EntitlementError) {
    return new EntitlementError(message, { code, upgradeTo });
  }
  if (ErrorClass === RateLimitError) {
    return new RateLimitError(message, { code, retryAfter });
  }
  if (ErrorClass === GatecoError) {
    return new GatecoError(message, { code, statusCode });
  }

  // For all other typed errors, construct with code only
  return new (ErrorClass as new (msg: string, opts: { code: string }) => GatecoError)(
    message,
    { code },
  );
}
