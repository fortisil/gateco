"""
Database connection management.

Provides async engine, session factory, and FastAPI dependency.
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from gateco.database.settings import db_settings

logger = logging.getLogger(__name__)

DATABASE_URL = db_settings.database_url

# Create async engine (lazy - only connects when DATABASE_URL is set)
engine = (
    create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )
    if DATABASE_URL
    else None
)

# Session factory
async_session_factory = (
    async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    if engine
    else None
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session.

    Yields:
        AsyncSession: Database session (auto-committed on success, rolled back on error).

    Raises:
        RuntimeError: If DATABASE_URL is not configured.
    """
    if async_session_factory is None:
        raise RuntimeError(
            "Database not configured. Set DATABASE_URL environment variable."
        )
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_connection() -> dict:
    """
    Health check helper - tests database connectivity.

    Returns:
        dict: Connection status with details.
    """
    if engine is None:
        return {"connected": False, "error": "DATABASE_URL not configured"}
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
            result.scalar()
        return {"connected": True}
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return {"connected": False, "error": str(e)}
