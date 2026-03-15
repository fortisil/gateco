"""Observability primitives: request ID, structured logging, timing."""

import logging
import time
import uuid

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("gateco.request")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Adds a unique X-Request-Id header to every response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Logs request method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        actor_id = getattr(request.state, "user_id", None)
        org_id = getattr(request.state, "org_id", None)
        req_id = getattr(request.state, "request_id", None)

        logger.info(
            "%s %s %s %.1fms actor=%s org=%s req=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            actor_id,
            org_id,
            req_id,
        )
        return response


def add_observability_middleware(app: FastAPI) -> None:
    """Register all observability middleware on the app."""
    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(RequestIdMiddleware)
