"""Database test fixtures.

Provides async session fixtures with transaction rollback for isolation.
"""

import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.gateco.database.models import Base

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/gateco_test",
)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

# Test session factory
TestSessionFactory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session with transaction rollback.

    Creates all tables before the test and rolls back after,
    ensuring test isolation.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionFactory() as session:
        async with session.begin():
            try:
                yield session
            finally:
                await session.rollback()

    # Clean up tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="module")
async def setup_database():
    """Set up database schema for module-level tests."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def org_data():
    """Sample organization data."""
    return {
        "name": "Test Organization",
        "slug": "test-org",
    }


@pytest.fixture
def user_data():
    """Sample user data."""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "password_hash": "hashed_password_here",
    }
