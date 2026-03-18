"""s01_auth — Login, token refresh, identity verification."""

from __future__ import annotations

from validation_harness.engine import ScenarioContext
from validation_harness.registry import scenario


@scenario(
    id="s01_auth",
    name="Authentication Flow",
    feature_area="auth",
    depends_on=["s00_health"],
    requires_features=["auth"],
)
async def s01_auth(ctx: ScenarioContext) -> None:
    """Login with profile credentials, verify identity, test refresh."""

    # Step 1: Login
    ctx.begin_step("login")
    token_resp = await ctx.client.login(
        ctx.config.credentials.email,
        ctx.config.credentials.password,
    )
    ctx.assert_that(
        "Login returns access_token",
        token_resp.access_token is not None and len(token_resp.access_token) > 0,
    )
    ctx.assert_that(
        "Login returns user",
        token_resp.user is not None,
    )

    # Step 2: Verify identity
    ctx.begin_step("verify_identity")
    me = await ctx.client._request("GET", "/api/users/me")
    ctx.assert_that(
        "GET /me returns user object",
        me is not None and "email" in (me or {}),
    )
    if me:
        ctx.assert_that(
            "Email matches credentials",
            me.get("email") == ctx.config.credentials.email,
            expected=ctx.config.credentials.email,
            actual=me.get("email"),
        )

        # Share state for downstream scenarios
        ctx.share("user_id", me.get("id"))
        ctx.share("org_id", me.get("organization_id"))

    # Step 3: Token refresh
    ctx.begin_step("token_refresh")
    if token_resp.refresh_token:
        refresh_resp = await ctx.client.auth.refresh()
        ctx.assert_that(
            "Refresh returns new access_token",
            refresh_resp.access_token is not None
            and refresh_resp.access_token != token_resp.access_token,
        )
    else:
        ctx.assert_that(
            "Refresh token available",
            False,
            expected="non-null refresh_token",
            actual=None,
        )
