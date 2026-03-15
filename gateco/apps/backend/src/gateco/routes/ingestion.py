"""Ingestion routes — document and batch ingestion endpoints."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.connection import get_session
from gateco.database.models.user import User
from gateco.exceptions import ValidationError
from gateco.middleware.jwt_auth import get_current_user
from gateco.schemas.ingestion import (
    BatchIngestRequest,
    IngestDocumentRequest,
)
from gateco.services import ingestion_service

router = APIRouter(prefix="/api/v1/ingest", tags=["ingestion"])


@router.post("", status_code=201)
async def ingest_document(
    body: IngestDocumentRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Ingest a single document: chunk, embed, store vectors, register metadata."""
    try:
        result = await ingestion_service.ingest_document(
            session=session,
            org_id=user.organization_id,
            request=body,
            actor_id=user.id,
            actor_name=user.name,
        )
        return result
    except ValidationError as e:
        category = getattr(e, "_ingestion_category", "ingestion_validation_failed")
        return JSONResponse(
            status_code=e.status_code,
            content={
                "status": "error",
                "error_category": category,
                "detail": e.detail,
            },
        )


@router.post("/batch", status_code=201)
async def ingest_batch(
    body: BatchIngestRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Ingest a batch of documents. Returns partial success semantics."""
    try:
        result = await ingestion_service.ingest_batch(
            session=session,
            org_id=user.organization_id,
            request=body,
            actor_id=user.id,
            actor_name=user.name,
        )
        return result
    except ValidationError as e:
        category = getattr(e, "_ingestion_category", "ingestion_validation_failed")
        return JSONResponse(
            status_code=e.status_code,
            content={
                "status": "error",
                "error_category": category,
                "detail": e.detail,
            },
        )
