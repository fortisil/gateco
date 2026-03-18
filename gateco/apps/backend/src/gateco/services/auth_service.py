"""Authentication service: signup, login, refresh, logout, auth code exchange."""

import datetime
import hashlib
import uuid

from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from gateco.database.enums import AuditEventType, PlanTier, UserRole
from gateco.database.models.organization import Organization
from gateco.database.models.session import UserSession
from gateco.database.models.user import User
from gateco.exceptions import AuthenticationError, ConflictError
from gateco.services import audit_service
from gateco.utils.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _build_user_response(user: User, org: Organization) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "organization": {
            "id": str(org.id),
            "name": org.name,
            "slug": org.slug,
            "plan": org.plan.value,
        },
        "created_at": user.created_at.isoformat() if user.created_at else "",
    }


def _build_tokens(user: User, org: Organization) -> tuple[str, str, dict]:
    access = create_access_token(
        user_id=user.id,
        org_id=org.id,
        role=user.role.value,
        plan=org.plan.value,
    )
    refresh = create_refresh_token(user_id=user.id)
    token_resp = {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
    return access, refresh, token_resp


async def signup(
    name: str,
    email: str,
    password: str,
    org_name: str,
    session: AsyncSession,
    ip_address: str | None = None,
) -> dict:
    """Create org + user, return LoginResponse dict."""
    # Check email uniqueness
    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise ConflictError(detail="Email already registered")

    # Create organization
    base_slug = slugify(org_name)
    slug = base_slug
    # Ensure slug uniqueness
    counter = 1
    while True:
        dup = await session.execute(select(Organization).where(Organization.slug == slug))
        if dup.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    org = Organization(name=org_name, slug=slug, plan=PlanTier.free)
    session.add(org)
    await session.flush()

    # Create user
    user = User(
        organization_id=org.id,
        email=email,
        password_hash=hash_password(password),
        name=name.strip(),
        role=UserRole.org_admin,
    )
    session.add(user)
    await session.flush()

    # Tokens + session
    _, refresh, token_resp = _build_tokens(user, org)
    user_session = UserSession(
        user_id=user.id,
        refresh_token_hash=_hash_token(refresh),
        ip_address=ip_address,
        expires_at=datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    session.add(user_session)

    user.update_last_login()

    await audit_service.emit_event(
        session=session,
        org_id=org.id,
        event_type=AuditEventType.user_login,
        actor_id=user.id,
        actor_name=user.name,
        details=f"User signed up: {email}",
        ip_address=ip_address,
    )

    return {"user": _build_user_response(user, org), "tokens": token_resp}


async def login(
    email: str,
    password: str,
    session: AsyncSession,
    ip_address: str | None = None,
) -> dict:
    """Authenticate user, return LoginResponse dict."""
    result = await session.execute(
        select(User).options(selectinload(User.organization)).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        raise AuthenticationError(detail="Invalid email or password")

    if user.is_deleted:
        raise AuthenticationError(detail="Account deactivated")

    org = user.organization

    # Revoke existing active sessions for this user to prevent stale session
    # accumulation and avoid refresh_token_hash collisions.
    existing = await session.execute(
        select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None),
        )
    )
    for s in existing.scalars().all():
        s.revoke()

    _, refresh, token_resp = _build_tokens(user, org)
    user_session = UserSession(
        user_id=user.id,
        refresh_token_hash=_hash_token(refresh),
        ip_address=ip_address,
        expires_at=datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    session.add(user_session)

    user.update_last_login()

    await audit_service.emit_event(
        session=session,
        org_id=org.id,
        event_type=AuditEventType.user_login,
        actor_id=user.id,
        actor_name=user.name,
        details=f"User logged in: {email}",
        ip_address=ip_address,
    )

    return {"user": _build_user_response(user, org), "tokens": token_resp}


async def refresh_tokens(refresh_token: str, session: AsyncSession) -> dict:
    """Validate refresh token, revoke old session, issue new tokens."""
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise AuthenticationError(detail="Invalid token type")

    user_id = payload.get("sub")
    token_hash = _hash_token(refresh_token)

    result = await session.execute(
        select(UserSession).where(
            UserSession.user_id == uuid.UUID(user_id),
            UserSession.refresh_token_hash == token_hash,
            UserSession.revoked_at.is_(None),
        )
    )
    old_session = result.scalar_one_or_none()
    if not old_session or old_session.is_expired:
        raise AuthenticationError(detail="Invalid or expired refresh token")

    old_session.revoke()

    # Load user + org
    result = await session.execute(
        select(User).options(selectinload(User.organization)).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise AuthenticationError(detail="User not found")

    org = user.organization
    _, new_refresh, token_resp = _build_tokens(user, org)

    new_session = UserSession(
        user_id=user.id,
        refresh_token_hash=_hash_token(new_refresh),
        expires_at=datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    session.add(new_session)

    return token_resp


async def logout(user_id: uuid.UUID, session: AsyncSession) -> None:
    """Revoke all active sessions for user."""
    result = await session.execute(
        select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
        )
    )
    for s in result.scalars().all():
        s.revoke()


async def create_auth_code(user_id: uuid.UUID, session: AsyncSession) -> str:
    """Create a one-time auth code for OAuth callback (D3). Expires in 60s."""
    code = str(uuid.uuid4())
    auth_session = UserSession(
        user_id=user_id,
        refresh_token_hash=_hash_token(code),
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=60),
    )
    session.add(auth_session)
    await session.flush()
    return code


async def exchange_auth_code(code: str, session: AsyncSession) -> dict:
    """Exchange one-time auth code for tokens (D3)."""
    code_hash = _hash_token(code)
    result = await session.execute(
        select(UserSession).where(
            UserSession.refresh_token_hash == code_hash,
            UserSession.revoked_at.is_(None),
        )
    )
    auth_session = result.scalar_one_or_none()
    if not auth_session or auth_session.is_expired:
        raise AuthenticationError(detail="Invalid or expired auth code")

    auth_session.revoke()

    # Load user + org
    result = await session.execute(
        select(User)
        .options(selectinload(User.organization))
        .where(User.id == auth_session.user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise AuthenticationError(detail="User not found")

    org = user.organization
    _, refresh, token_resp = _build_tokens(user, org)

    new_session = UserSession(
        user_id=user.id,
        refresh_token_hash=_hash_token(refresh),
        expires_at=datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    session.add(new_session)

    return token_resp
