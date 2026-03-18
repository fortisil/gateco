"""Evidence-capturing transport and harness client construction."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from gateco_sdk._auth import TokenManager
from gateco_sdk._transport import Transport
from gateco_sdk.client import AsyncGatecoClient
from gateco_sdk.errors import GatecoError

from validation_harness.models import EvidenceRecord


class EvidenceCapturingTransport(Transport):
    """Transport subclass that records every HTTP request/response as evidence."""

    def __init__(self, base_url: str, **kwargs: Any) -> None:
        super().__init__(base_url, **kwargs)
        self._evidence: list[EvidenceRecord] = []

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        """Intercept request, capture evidence, delegate to parent."""
        start = time.monotonic()
        ts = datetime.now(timezone.utc)
        status_code: int | None = None
        response_body: dict[str, Any] | None = None
        error_msg: str | None = None

        try:
            result = await super().request(
                method, path, json=json, params=params, headers=headers
            )
            response_body = result
            return result
        except GatecoError as exc:
            status_code = exc.status_code
            error_msg = exc.message
            raise
        except Exception as exc:
            error_msg = str(exc)
            raise
        finally:
            elapsed = (time.monotonic() - start) * 1000
            self._evidence.append(
                EvidenceRecord(
                    timestamp=ts,
                    method=method,
                    path=path,
                    status_code=status_code,
                    request_body=json,
                    response_body=response_body,
                    duration_ms=round(elapsed, 2),
                    error=error_msg,
                )
            )

    def drain_evidence(self) -> list[EvidenceRecord]:
        """Return and clear accumulated evidence records."""
        records = list(self._evidence)
        self._evidence.clear()
        return records


async def create_harness_client(
    base_url: str,
    *,
    timeout: float = 30.0,
    max_retries: int = 1,
) -> tuple[AsyncGatecoClient, EvidenceCapturingTransport]:
    """Create an AsyncGatecoClient with evidence-capturing transport.

    Returns (client, transport) so the engine can drain evidence per step.
    """
    client = AsyncGatecoClient(
        base_url,
        timeout=timeout,
        max_retries=max_retries,
    )

    transport = EvidenceCapturingTransport(
        base_url,
        timeout=timeout,
        max_retries=max_retries,
    )
    # Replace transport — safe because _request() only calls self._transport.request()
    client._transport = transport  # type: ignore[attr-defined]

    return client, transport
