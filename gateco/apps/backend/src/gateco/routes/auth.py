"""Authentication routes: login, signup, OAuth, token refresh, logout."""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.connection import get_session
from gateco.database.enums import AuditEventType
from gateco.database.models.user import User
from gateco.middleware.jwt_auth import get_current_user
from gateco.middleware.rate_limit import check_rate_limit
from gateco.schemas.auth import (
    ExchangeCodeRequest,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    SignupRequest,
    TokenResponse,
)
from gateco.services import audit_service, auth_service
from gateco.services.oauth_service import (
    get_github_authorize_url,
    get_google_authorize_url,
    handle_github_callback,
    handle_google_callback,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Authenticate with email and password."""
    check_rate_limit(body.email)
    ip = request.client.host if request.client else None
    result = await auth_service.login(body.email, body.password, session, ip_address=ip)
    return result


@router.post("/signup", response_model=LoginResponse, status_code=201)
async def signup(
    body: SignupRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Register a new user and organization."""
    check_rate_limit(body.email)
    ip = request.client.host if request.client else None
    result = await auth_service.signup(
        name=body.name.strip(),
        email=body.email,
        password=body.password,
        org_name=body.organization_name.strip(),
        session=session,
        ip_address=ip,
    )
    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session),
):
    """Refresh access token using a valid refresh token."""
    return await auth_service.refresh_tokens(body.refresh_token, session)


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Revoke all sessions for the current user."""
    await auth_service.logout(user.id, session)
    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.user_logout,
        actor_id=user.id,
        actor_name=user.name,
        details="User logged out",
        ip_address=request.client.host if request.client else None,
    )


@router.post("/exchange", response_model=TokenResponse)
async def exchange_code(
    body: ExchangeCodeRequest,
    session: AsyncSession = Depends(get_session),
):
    """Exchange a one-time OAuth auth code for tokens (D3)."""
    return await auth_service.exchange_auth_code(body.code, session)


# ── OAuth redirects ──


@router.get("/google")
async def google_auth():
    """Redirect to Google OAuth consent screen."""
    return RedirectResponse(url=get_google_authorize_url(), status_code=302)


@router.get("/github")
async def github_auth():
    """Redirect to GitHub OAuth consent screen."""
    return RedirectResponse(url=get_github_authorize_url(), status_code=302)


@router.get("/google/callback")
async def google_callback(code: str, session: AsyncSession = Depends(get_session)):
    """Handle Google OAuth callback → redirect to FE with auth_code."""
    redirect_url = await handle_google_callback(code, session)
    return RedirectResponse(url=redirect_url, status_code=302)


@router.get("/github/callback")
async def github_callback(code: str, session: AsyncSession = Depends(get_session)):
    """Handle GitHub OAuth callback → redirect to FE with auth_code."""
    redirect_url = await handle_github_callback(code, session)
    return RedirectResponse(url=redirect_url, status_code=302)
