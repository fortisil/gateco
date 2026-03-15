"""Retroactive registration routes — register unmanaged vectors as gated resources."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.connection import get_session
from gateco.database.models.user import User
from gateco.exceptions import ValidationError
from gateco.middleware.jwt_auth import get_current_user
from gateco.schemas.retroactive import RetroactiveRegisterRequest
from gateco.services import retroactive_service

router = APIRouter(prefix="/api/v1/retroactive-register", tags=["retroactive-registration"])


@router.post("", status_code=201)
async def retroactive_register(
    body: RetroactiveRegisterRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Scan a connector's vector DB and register unmanaged vectors as gated resources."""
    try:
        result = await retroactive_service.retroactive_register(
            session=session,
            org_id=user.organization_id,
            request=body,
            actor_id=user.id,
            actor_name=user.name,
        )
        return result
    except ValidationError as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "status": "error",
                "error_category": "retroactive_validation_failed",
                "detail": e.detail,
            },
        )
