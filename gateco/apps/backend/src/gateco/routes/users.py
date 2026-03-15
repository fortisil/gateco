"""User management routes."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.connection import get_session
from gateco.database.enums import AuditEventType
from gateco.database.models.user import User
from gateco.middleware.jwt_auth import get_current_user
from gateco.schemas.auth import UpdateUserRequest, UserResponse
from gateco.services import audit_service

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get the current authenticated user with organization.plan for FE entitlement gating."""
    org = user.organization
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


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UpdateUserRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update current user's profile."""
    user.name = body.name.strip()

    await audit_service.emit_event(
        session=session,
        org_id=user.organization_id,
        event_type=AuditEventType.settings_changed,
        actor_id=user.id,
        actor_name=user.name,
        details="User profile updated",
        ip_address=request.client.host if request.client else None,
    )

    org = user.organization
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
