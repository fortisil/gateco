"""s00_health — Backend health check (raw httpx, no SDK)."""

from __future__ import annotations

import httpx

from validation_harness.engine import ScenarioContext
from validation_harness.registry import scenario


@scenario(
    id="s00_health",
    name="Backend Health Check",
    feature_area="health",
    depends_on=[],
    requires_features=["auth"],
)
async def s00_health(ctx: ScenarioContext) -> None:
    """GET /health/db — verify backend is reachable and healthy."""
    ctx.begin_step("health_check")

    async with httpx.AsyncClient() as http:
        resp = await http.get(
            f"{ctx.config.base_url}/health/db", timeout=10
        )

    ctx.assert_that(
        "Health endpoint returns 200",
        resp.status_code == 200,
        expected=200,
        actual=resp.status_code,
    )

    if resp.status_code == 200:
        body = resp.json()
        ctx.assert_that(
            "Status is healthy",
            body.get("status") == "healthy",
            expected="healthy",
            actual=body.get("status"),
        )
