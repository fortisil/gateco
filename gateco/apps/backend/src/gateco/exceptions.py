"""Gateco exception hierarchy and FastAPI exception handlers.

All API errors return: {"error": {"code": "...", "message": "..."}}
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class GatecoError(Exception):
    """Base exception for all Gateco errors."""

    def __init__(
        self,
        detail: str = "An error occurred",
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
    ):
        self.detail = detail
        self.code = code
        self.status_code = status_code
        super().__init__(detail)


class AuthenticationError(GatecoError):
    """401 — missing, expired, or invalid credentials."""

    def __init__(self, detail: str = "Invalid credentials", code: str = "AUTH_INVALID_CREDENTIALS"):
        super().__init__(detail=detail, code=code, status_code=401)


class AuthorizationError(GatecoError):
    """403 — authenticated but insufficient permissions."""

    def __init__(self, detail: str = "Permission denied", code: str = "AUTH_PERMISSION_DENIED"):
        super().__init__(detail=detail, code=code, status_code=403)


class NotFoundError(GatecoError):
    """404 — resource not found (also used for cross-org isolation per D7)."""

    def __init__(self, detail: str = "Resource not found", code: str = "RESOURCE_NOT_FOUND"):
        super().__init__(detail=detail, code=code, status_code=404)


class ConflictError(GatecoError):
    """409 — resource already exists or state conflict."""

    def __init__(self, detail: str = "Resource already exists", code: str = "CONFLICT"):
        super().__init__(detail=detail, code=code, status_code=409)


class EntitlementError(GatecoError):
    """403 — plan does not include this feature or limit exceeded."""

    def __init__(
        self,
        detail: str = "Feature not available on current plan",
        code: str = "ENTITLEMENT_REQUIRED",
        upgrade_to: str | None = None,
    ):
        self.upgrade_to = upgrade_to
        super().__init__(detail=detail, code=code, status_code=403)


class RateLimitError(GatecoError):
    """429 — too many requests."""

    def __init__(self, detail: str = "Too many requests", code: str = "RATE_LIMIT_EXCEEDED"):
        super().__init__(detail=detail, code=code, status_code=429)


class ValidationError(GatecoError):
    """422 — request validation failed."""

    def __init__(self, detail: str = "Validation error", code: str = "VALIDATION_ERROR"):
        super().__init__(detail=detail, code=code, status_code=422)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all Gateco exception handlers on the FastAPI app."""

    @app.exception_handler(GatecoError)
    async def gateco_error_handler(request: Request, exc: GatecoError) -> JSONResponse:
        body: dict = {"error": {"code": exc.code, "message": exc.detail}}
        if isinstance(exc, EntitlementError) and exc.upgrade_to:
            body["error"]["upgrade_to"] = exc.upgrade_to
        return JSONResponse(status_code=exc.status_code, content=body)
