"""JWT authentication middleware and FastAPI dependencies."""

from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from gateco.database.connection import get_session
from gateco.database.enums import UserRole
from gateco.database.models.organization import Organization
from gateco.database.models.user import User
from gateco.exceptions import AuthenticationError, AuthorizationError
from gateco.utils.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# Role hierarchy: org_admin > security_admin > data_owner > developer
ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.org_admin: 40,
    UserRole.security_admin: 30,
    UserRole.data_owner: 20,
    UserRole.developer: 10,
}


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Decode Bearer token, load User from DB, reject if soft-deleted."""
    if not token:
        raise AuthenticationError(detail="Missing authentication token")

    payload = decode_token(token)

    if payload.get("type") != "access":
        raise AuthenticationError(detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError(detail="Invalid token payload")

    result = await session.execute(
        select(User)
        .options(selectinload(User.organization))
        .where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if user is None or user.is_deleted:
        raise AuthenticationError(detail="User not found or deactivated")

    if user.organization.is_deleted:
        raise AuthenticationError(detail="Organization deactivated")

    # Inject org_id into request state for D7 enforcement
    request.state.org_id = user.organization_id
    request.state.user_id = user.id
    request.state.user_role = user.role
    request.state.plan = user.organization.plan.value

    return user


async def get_current_user_org(
    user: User = Depends(get_current_user),
) -> tuple[User, Organization]:
    """Convenience dependency returning (User, Organization) tuple."""
    return user, user.organization


def require_role(*roles: UserRole):
    """Dependency factory: require caller has at least one of the given roles.

    Uses role hierarchy — e.g. require_role(data_owner) also passes for
    security_admin and org_admin.
    """
    min_level = min(ROLE_HIERARCHY.get(r, 0) for r in roles)

    async def _check(user: User = Depends(get_current_user)) -> User:
        user_level = ROLE_HIERARCHY.get(user.role, 0)
        if user_level < min_level:
            raise AuthorizationError(detail="Insufficient role permissions")
        return user

    return Depends(_check)
