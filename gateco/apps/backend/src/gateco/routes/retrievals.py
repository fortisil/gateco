"""Secured Retrieval routes — execute, list, detail."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.connection import get_session
from gateco.database.models.user import User
from gateco.middleware.jwt_auth import get_current_user
from gateco.services import retrieval_service

router = APIRouter(prefix="/api/retrievals", tags=["retrievals"])


class ExecuteRetrievalRequest(BaseModel):
    query_vector: list[float] = Field(..., min_length=1)
    query: str | None = Field(default=None, description="Optional text for audit trail")
    principal_id: str
    connector_id: str
    top_k: int = Field(default=10, ge=1, le=100)
    filters: dict | None = None
    include_unresolved: bool = Field(
        default=False,
        description="Include unresolved results for diagnostics",
    )


@router.post("/execute")
async def execute_retrieval(
    body: ExecuteRetrievalRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    plan = getattr(request.state, "plan", "free")
    return await retrieval_service.execute_retrieval(
        session=session,
        org_id=user.organization_id,
        plan=plan,
        query_text=body.query or "",
        query_vector=body.query_vector,
        principal_id=UUID(body.principal_id),
        connector_id=UUID(body.connector_id),
        top_k=body.top_k,
        filters=body.filters,
        include_unresolved=body.include_unresolved,
        actor_id=user.id,
        actor_name=user.name,
    )


@router.get("")
async def list_retrievals(
    outcome: str | None = None,
    principal_id: UUID | None = None,
    connector_id: UUID | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await retrieval_service.list_retrievals(
        session, user.organization_id,
        outcome=outcome, principal_id=principal_id,
        connector_id=connector_id,
        date_from=date_from, date_to=date_to,
        page=page, per_page=per_page,
    )


@router.get("/{retrieval_id}")
async def get_retrieval(
    retrieval_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await retrieval_service.get_retrieval(session, user.organization_id, retrieval_id)
