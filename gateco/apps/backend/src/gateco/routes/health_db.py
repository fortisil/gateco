"""
Database health check endpoint.

Returns database connectivity and migration status.
"""

import logging
import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health/db")
async def health_db():
    """
    Database health check endpoint.

    Returns:
        JSONResponse: 200 with DB details if healthy, 503 if not ready.
    """
    database_url = os.getenv("DATABASE_URL", "")

    if not database_url:
        return JSONResponse(
            status_code=503,
            content={
                "status": "DB_NOT_READY",
                "message": "DATABASE_URL not configured",
                "setup_hint": "Set DATABASE_URL in .env or run the setup wizard",
            },
        )

    try:
        from .database.connection import engine

        if engine is None:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "DB_NOT_READY",
                    "message": "Database engine not initialized",
                },
            )

        async with engine.connect() as conn:
            # Check basic connectivity
            await conn.execute(text("SELECT 1"))

            # Check migration status via alembic_version table
            migration_info = {"current_revision": None}
            try:
                result = await conn.execute(
                    text("SELECT version_num FROM alembic_version LIMIT 1")
                )
                row = result.first()
                if row:
                    migration_info["current_revision"] = row[0]
            except Exception:
                migration_info["current_revision"] = "alembic_version table not found"

        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "database": "connected",
                "migrations": migration_info,
            },
        )
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "DB_NOT_READY",
                "message": f"Database connection failed: {str(e)}",
            },
        )
