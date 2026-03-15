"""
Database test fixtures.

Provides test database URL override and async session fixture.
"""

import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.gateco.database.models import Base


# Override DATABASE_URL for tests
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db",
)


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    return create_async_engine(TEST_DATABASE_URL, echo=True)


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncSession:
    """
    Provide an async database session for tests.

    Creates tables before tests and drops them after.
    Each test gets a fresh transaction that is rolled back.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
