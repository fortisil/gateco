"""
Alembic environment configuration.

Supports async migrations with SQLAlchemy.
"""

import asyncio
import os
from logging.config import fileConfig
from pathlib import Path

# Load .env from backend root
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import models to register metadata
# The models package imports all models, registering them with Base.metadata
from src.gateco.database.models import Base

# Import all models to ensure they're registered with the metadata
# Phase 1: Core Auth
from src.gateco.database.models import (
    Organization,
    User,
    UserSession,
    OAuthAccount,
)

# Phase 2: Resources
from src.gateco.database.models import (
    GatedResource,
    AccessRule,
    Invite,
)

# Phase 3: Billing
from src.gateco.database.models import (
    Subscription,
    Payment,
    Invoice,
    UsageLog,
    Coupon,
    StripeEvent,
)

# Alembic Config object
config = context.config

# Set sqlalchemy.url from environment
database_url = os.getenv("DATABASE_URL", "")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Generates SQL script without connecting to the database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Run migrations with the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates an async engine and runs migrations.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
