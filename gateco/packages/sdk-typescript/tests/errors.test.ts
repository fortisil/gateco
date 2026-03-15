import { describe, it, expect } from "vitest";
import {
  GatecoError,
  AuthenticationError,
  AuthorizationError,
  NotFoundError,
  ConflictError,
  EntitlementError,
  RateLimitError,
  ValidationError,
  errorFromResponse,
} from "../src/errors.js";

describe("GatecoError", () => {
  it("creates a base error with defaults", () => {
    const err = new GatecoError();
    expect(err.message).toBe("An unexpected error occurred");
    expect(err.code).toBe("UNKNOWN_ERROR");
    expect(err.statusCode).toBe(500);
    expect(err.name).toBe("GatecoError");
    expect(err).toBeInstanceOf(Error);
  });

  it("creates a base error with custom values", () => {
    const err = new GatecoError("Something broke", { code: "CUSTOM", statusCode: 503 });
    expect(err.message).toBe("Something broke");
    expect(err.code).toBe("CUSTOM");
    expect(err.statusCode).toBe(503);
  });
});

describe("AuthenticationError", () => {
  it("defaults to 401 status", () => {
    const err = new AuthenticationError();
    expect(err.statusCode).toBe(401);
    expect(err.code).toBe("AUTH_INVALID_CREDENTIALS");
    expect(err.name).toBe("AuthenticationError");
    expect(err).toBeInstanceOf(GatecoError);
  });
});

describe("AuthorizationError", () => {
  it("defaults to 403 status", () => {
    const err = new AuthorizationError();
    expect(err.statusCode).toBe(403);
    expect(err.code).toBe("AUTH_PERMISSION_DENIED");
  });
});

describe("NotFoundError", () => {
  it("defaults to 404 status", () => {
    const err = new NotFoundError();
    expect(err.statusCode).toBe(404);
  });
});

describe("ConflictError", () => {
  it("defaults to 409 status", () => {
    const err = new ConflictError();
    expect(err.statusCode).toBe(409);
  });
});

describe("EntitlementError", () => {
  it("stores upgradeTo", () => {
    const err = new EntitlementError("Upgrade needed", { upgradeTo: "pro" });
    expect(err.statusCode).toBe(403);
    expect(err.upgradeTo).toBe("pro");
    expect(err.code).toBe("ENTITLEMENT_REQUIRED");
  });
});

describe("RateLimitError", () => {
  it("stores retryAfter", () => {
    const err = new RateLimitError("Slow down", { retryAfter: 30 });
    expect(err.statusCode).toBe(429);
    expect(err.retryAfter).toBe(30);
  });
});

describe("ValidationError", () => {
  it("defaults to 422 status", () => {
    const err = new ValidationError();
    expect(err.statusCode).toBe(422);
  });
});

describe("errorFromResponse", () => {
  it("maps 401 to AuthenticationError", () => {
    const err = errorFromResponse(401, null);
    expect(err).toBeInstanceOf(AuthenticationError);
    expect(err.statusCode).toBe(401);
  });

  it("maps 404 to NotFoundError", () => {
    const err = errorFromResponse(404, null);
    expect(err).toBeInstanceOf(NotFoundError);
  });

  it("maps 409 to ConflictError", () => {
    const err = errorFromResponse(409, null);
    expect(err).toBeInstanceOf(ConflictError);
  });

  it("maps 422 to ValidationError", () => {
    const err = errorFromResponse(422, null);
    expect(err).toBeInstanceOf(ValidationError);
  });

  it("maps 429 to RateLimitError with retryAfter", () => {
    const err = errorFromResponse(429, null, 60);
    expect(err).toBeInstanceOf(RateLimitError);
    expect((err as RateLimitError).retryAfter).toBe(60);
  });

  it("prefers code-based mapping over status-based", () => {
    const body = {
      error: {
        code: "ENTITLEMENT_REQUIRED",
        message: "Pro plan required",
        upgrade_to: "pro",
      },
    };
    const err = errorFromResponse(403, body);
    expect(err).toBeInstanceOf(EntitlementError);
    expect((err as EntitlementError).upgradeTo).toBe("pro");
    expect(err.message).toBe("Pro plan required");
  });

  it("maps AUTH_PERMISSION_DENIED to AuthorizationError", () => {
    const body = {
      error: {
        code: "AUTH_PERMISSION_DENIED",
        message: "Forbidden",
      },
    };
    const err = errorFromResponse(403, body);
    expect(err).toBeInstanceOf(AuthorizationError);
  });

  it("falls back to GatecoError for unknown status", () => {
    const err = errorFromResponse(502, null);
    expect(err).toBeInstanceOf(GatecoError);
    expect(err.statusCode).toBe(502);
  });

  it("extracts message from error body", () => {
    const body = {
      error: {
        code: "RESOURCE_NOT_FOUND",
        message: "Connector abc not found",
      },
    };
    const err = errorFromResponse(404, body);
    expect(err).toBeInstanceOf(NotFoundError);
    expect(err.message).toBe("Connector abc not found");
  });
});
