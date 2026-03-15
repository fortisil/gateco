"""
Admin authentication middleware.

Validates the X-Admin-Token header against the ADMIN_SETUP_TOKEN
environment variable. Used to protect admin setup endpoints.
"""

import logging
import os

from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)


async def require_admin_token(
    x_admin_token: str = Header(..., alias="X-Admin-Token"),
) -> str:
    """
    FastAPI dependency that validates the admin setup token.

    Args:
        x_admin_token (str): Token from X-Admin-Token header.

    Returns:
        str: The validated token.

    Raises:
        HTTPException: 403 if token is missing, invalid, or not configured.
    """
    expected = os.getenv("ADMIN_SETUP_TOKEN", "")
    if not expected:
        logger.warning("ADMIN_SETUP_TOKEN is not configured")
        raise HTTPException(
            status_code=403,
            detail="Admin setup token is not configured on the server.",
        )
    if x_admin_token != expected:
        logger.warning("Invalid admin token attempt")
        raise HTTPException(
            status_code=403,
            detail="Invalid admin token.",
        )
    return x_admin_token
