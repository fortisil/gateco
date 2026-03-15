"""
Admin database setup routes.

Provides endpoints for the admin wizard to configure and
initialize the database without using the CLI.
"""

import logging
import os
import subprocess
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from gateco.middleware.admin_auth import require_admin_token

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/db",
    tags=["admin"],
    dependencies=[Depends(require_admin_token)],
)


class TestRequest(BaseModel):
    """Request body for connection test."""

    database_url: str


class ApplyRequest(BaseModel):
    """Request body for applying database setup."""

    database_url: str
    mode: str = "default"


class StepResult(BaseModel):
    """Result of a single setup step."""

    step: str
    success: bool
    message: str


def _read_env_file() -> dict[str, str]:
    """
    Read key=value pairs from the backend .env file.

    Returns:
        dict[str, str]: Parsed environment variables.
    """
    env_path = Path(__file__).resolve().parents[3] / ".env"
    pairs: dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                pairs[key.strip()] = value.strip()
    return pairs


def _write_env_var(key: str, value: str) -> None:
    """
    Write or update a key in the backend .env file.

    Args:
        key (str): Environment variable name.
        value (str): Environment variable value.
    """
    env_path = Path(__file__).resolve().parents[3] / ".env"
    lines: list[str] = []
    found = False
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith(f"{key}="):
                lines.append(f"{key}={value}")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"{key}={value}")
    env_path.write_text("\n".join(lines) + "\n")


def _run_alembic_upgrade() -> StepResult:
    """
    Run alembic upgrade head as a subprocess.

    Returns:
        StepResult: Result of the migration step.
    """
    backend_dir = Path(__file__).resolve().parents[3]
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=str(backend_dir),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return StepResult(
                step="migrate",
                success=True,
                message="Migrations applied successfully.",
            )
        logger.error(f"Alembic failed: {result.stderr}")
        return StepResult(
            step="migrate",
            success=False,
            message=f"Migration failed: {result.stderr[:500]}",
        )
    except subprocess.TimeoutExpired:
        return StepResult(
            step="migrate",
            success=False,
            message="Migration timed out after 60 seconds.",
        )
    except FileNotFoundError:
        return StepResult(
            step="migrate",
            success=False,
            message="Alembic not found. Install with: pip install alembic",
        )


@router.get("/status")
async def db_status():
    """
    Get current database setup status.

    Returns:
        dict: Status information including connectivity and migration state.
    """
    import asyncpg

    db_url = os.getenv("DATABASE_URL", "")
    db_configured = bool(db_url)
    status = "unconfigured"
    last_error = None
    migrations_applied = 0

    if db_configured:
        # Convert SQLAlchemy URL to asyncpg format if needed
        connect_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        try:
            conn = await asyncpg.connect(connect_url)
            try:
                # Check alembic_version table
                row = await conn.fetchval(
                    "SELECT COUNT(*) FROM alembic_version"
                )
                migrations_applied = row or 0
                status = "ready"
            except asyncpg.UndefinedTableError:
                status = "configured"
            finally:
                await conn.close()
        except Exception as exc:
            logger.error(f"DB status check failed: {exc}")
            status = "error"
            last_error = str(exc)

    return {
        "status": status,
        "mode": "default",
        "lastError": last_error,
        "migrationsApplied": migrations_applied,
        "dbUrlConfigured": db_configured,
    }


@router.post("/test")
async def test_connection(body: TestRequest):
    """
    Test database connectivity without saving the URL.

    Args:
        body (TestRequest): Contains the database_url to test.

    Returns:
        dict: Success flag and message.
    """
    import asyncpg

    connect_url = body.database_url.replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    try:
        conn = await asyncpg.connect(connect_url)
        await conn.execute("SELECT 1")
        await conn.close()
        return {"success": True, "message": "Connection successful."}
    except Exception as exc:
        logger.error(f"Connection test failed: {exc}")
        return {"success": False, "message": str(exc)}


@router.post("/apply")
async def apply_setup(body: ApplyRequest):
    """
    Save DATABASE_URL to .env and run migrations.

    Args:
        body (ApplyRequest): Contains database_url and optional mode.

    Returns:
        dict: List of step results and final status.
    """
    steps: list[dict] = []

    # Step 1: Write DATABASE_URL to .env
    try:
        _write_env_var("DATABASE_URL", body.database_url)
        os.environ["DATABASE_URL"] = body.database_url
        steps.append({"step": "save_url", "success": True, "message": "DATABASE_URL saved."})
    except Exception as exc:
        steps.append({"step": "save_url", "success": False, "message": str(exc)})
        return {"steps": steps, "status": "error"}

    # Step 2: Run migrations
    migrate_result = _run_alembic_upgrade()
    steps.append(migrate_result.model_dump())

    final_status = "ready" if migrate_result.success else "error"
    return {"steps": steps, "status": final_status}


@router.post("/retry")
async def retry_setup():
    """
    Re-run migrations using the existing DATABASE_URL from .env.

    Returns:
        dict: List of step results and final status.
    """
    steps: list[dict] = []

    # Read DATABASE_URL from .env
    env_vars = _read_env_file()
    db_url = env_vars.get("DATABASE_URL", "")
    if not db_url:
        return {
            "steps": [
                {"step": "read_env", "success": False, "message": "DATABASE_URL not found in .env"}
            ],
            "status": "error",
        }

    os.environ["DATABASE_URL"] = db_url
    steps.append({"step": "read_env", "success": True, "message": "DATABASE_URL loaded from .env."})

    # Run migrations
    migrate_result = _run_alembic_upgrade()
    steps.append(migrate_result.model_dump())

    final_status = "ready" if migrate_result.success else "error"
    return {"steps": steps, "status": final_status}
