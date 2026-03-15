"""OAuth service: Google and GitHub OAuth flows (D3)."""

import logging
import os

import httpx
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from gateco.database.enums import OAuthProvider, PlanTier, UserRole
from gateco.database.models.oauth_account import OAuthAccount
from gateco.database.models.organization import Organization
from gateco.database.models.user import User
from gateco.services.auth_service import create_auth_code

logger = logging.getLogger(__name__)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def get_google_authorize_url() -> str:
    """Build Google OAuth2 authorization URL."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    redirect_uri = f"{BACKEND_URL}/api/auth/google/callback"
    return (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=openid+email+profile"
        "&access_type=offline"
    )


def get_github_authorize_url() -> str:
    """Build GitHub OAuth authorization URL."""
    client_id = os.getenv("GITHUB_CLIENT_ID", "")
    redirect_uri = f"{BACKEND_URL}/api/auth/github/callback"
    return (
        "https://github.com/login/oauth/authorize?"
        f"client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        "&scope=user:email"
    )


async def handle_google_callback(code: str, session: AsyncSession) -> str:
    """Exchange Google auth code → find/create user → return FE redirect URL with auth_code."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    redirect_uri = f"{BACKEND_URL}/api/auth/google/callback"

    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        tokens = token_resp.json()
        access_token = tokens.get("access_token", "")

        # Fetch user profile
        profile_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile = profile_resp.json()

    email = profile.get("email", "")
    name = profile.get("name", email.split("@")[0])
    provider_user_id = profile.get("id", "")

    user = await _find_or_create_oauth_user(
        session=session,
        provider=OAuthProvider.google,
        provider_user_id=provider_user_id,
        email=email,
        name=name,
        access_token=access_token,
        provider_data=profile,
    )

    auth_code = await create_auth_code(user.id, session)
    return f"{FRONTEND_URL}/oauth/callback?code={auth_code}"


async def handle_github_callback(code: str, session: AsyncSession) -> str:
    """Exchange GitHub auth code → find/create user → return FE redirect URL with auth_code."""
    client_id = os.getenv("GITHUB_CLIENT_ID", "")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET", "")

    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Accept": "application/json"},
        )
        tokens = token_resp.json()
        access_token = tokens.get("access_token", "")

        # Fetch user profile
        profile_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile = profile_resp.json()

        # Fetch primary email
        emails_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        emails = emails_resp.json()

    primary_email = ""
    if isinstance(emails, list):
        for e in emails:
            if e.get("primary"):
                primary_email = e.get("email", "")
                break
        if not primary_email and emails:
            primary_email = emails[0].get("email", "")

    name = profile.get("name") or profile.get("login", "")
    provider_user_id = str(profile.get("id", ""))

    user = await _find_or_create_oauth_user(
        session=session,
        provider=OAuthProvider.github,
        provider_user_id=provider_user_id,
        email=primary_email,
        name=name,
        access_token=access_token,
        provider_data=profile,
    )

    auth_code = await create_auth_code(user.id, session)
    return f"{FRONTEND_URL}/oauth/callback?code={auth_code}"


async def _find_or_create_oauth_user(
    session: AsyncSession,
    provider: OAuthProvider,
    provider_user_id: str,
    email: str,
    name: str,
    access_token: str,
    provider_data: dict,
) -> User:
    """Find existing OAuth account or create new user + org."""
    result = await session.execute(
        select(OAuthAccount)
        .options(selectinload(OAuthAccount.user).selectinload(User.organization))
        .where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
    )
    oauth_account = result.scalar_one_or_none()

    if oauth_account:
        oauth_account.update_tokens(access_token)
        return oauth_account.user

    # Check if a user with this email already exists
    result = await session.execute(
        select(User).options(selectinload(User.organization)).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if user:
        # Link OAuth account to existing user
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            access_token=access_token,
            provider_data=provider_data,
        )
        session.add(oauth_account)
        return user

    # Create new org + user
    slug = slugify(name or email.split("@")[0])
    counter = 1
    base_slug = slug
    while True:
        dup = await session.execute(select(Organization).where(Organization.slug == slug))
        if dup.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    org = Organization(name=name or email.split("@")[0], slug=slug, plan=PlanTier.free)
    session.add(org)
    await session.flush()

    user = User(
        organization_id=org.id,
        email=email,
        name=name,
        role=UserRole.org_admin,
    )
    session.add(user)
    await session.flush()

    oauth_account = OAuthAccount(
        user_id=user.id,
        provider=provider,
        provider_user_id=provider_user_id,
        access_token=access_token,
        provider_data=provider_data,
    )
    session.add(oauth_account)

    # Reload user with org for the caller
    result = await session.execute(
        select(User).options(selectinload(User.organization)).where(User.id == user.id)
    )
    return result.scalar_one()
