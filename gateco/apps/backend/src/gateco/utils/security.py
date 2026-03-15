"""JWT and password security utilities."""

import datetime
import os
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from gateco.exceptions import AuthenticationError

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return _pwd_ctx.verify(plain, hashed)


def create_access_token(
    user_id: UUID,
    org_id: UUID,
    role: str,
    plan: str,
    expires_delta: datetime.timedelta | None = None,
) -> str:
    """Create a short-lived JWT access token.

    Payload: {sub, org_id, role, plan, type, exp, iat}
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    exp = now + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": str(user_id),
        "org_id": str(org_id),
        "role": role,
        "plan": plan,
        "type": "access",
        "exp": exp,
        "iat": now,
    }
    return jwt.encode(payload, _get_secret(), algorithm=JWT_ALGORITHM)


def create_refresh_token(
    user_id: UUID,
    expires_delta: datetime.timedelta | None = None,
) -> str:
    """Create a long-lived JWT refresh token."""
    now = datetime.datetime.now(datetime.timezone.utc)
    exp = now + (expires_delta or datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": exp,
        "iat": now,
    }
    return jwt.encode(payload, _get_secret(), algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises AuthenticationError on failure."""
    try:
        return jwt.decode(token, _get_secret(), algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise AuthenticationError(detail=f"Invalid token: {exc}")


def _get_secret() -> str:
    secret = JWT_SECRET_KEY or os.getenv("JWT_SECRET_KEY", "") or os.getenv("SECRET_KEY", "")
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY (or SECRET_KEY) environment variable is not set")
    return secret
