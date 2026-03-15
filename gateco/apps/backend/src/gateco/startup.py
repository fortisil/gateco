"""
Application startup hook.

Handles graceful startup when DATABASE_URL is not configured.
The app runs in limited mode without a database connection.
"""

import logging
import os

logger = logging.getLogger(__name__)


async def on_startup() -> None:
    """
    Run startup checks for database connectivity.

    If DATABASE_URL is not set, logs a warning and skips DB initialization.
    The application continues to run in limited mode.
    """
    database_url = os.getenv("DATABASE_URL", "")

    if not database_url:
        logger.warning(
            "DATABASE_URL is not set. "
            "Application running in limited mode without database. "
            "Set DATABASE_URL in .env or environment to enable full functionality."
        )
        return

    logger.info("DATABASE_URL detected - initializing database connection")

    try:
        from .database.connection import check_db_connection

        status = await check_db_connection()
        if status.get("connected"):
            logger.info("Database connection verified successfully")
        else:
            logger.error(
                f"Database connection failed: {status.get('error', 'unknown')}"
            )
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
