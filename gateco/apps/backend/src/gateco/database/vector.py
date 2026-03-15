"""
pgvector helper utilities.

Provides vector column type, similarity search, and sanity checks.
"""

import logging

from sqlalchemy import Column, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Reason: pgvector types are registered at import time by the pgvector package
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None
    logger.warning("pgvector package not installed - vector features unavailable")


def vector_column(dimensions: int = 1536, nullable: bool = True) -> Column:
    """
    Create a pgvector column with the specified dimensions.

    Args:
        dimensions: Vector dimensionality (default: 1536 for OpenAI embeddings).
        nullable: Whether the column allows NULL values.

    Returns:
        Column: SQLAlchemy column with Vector type.

    Raises:
        ImportError: If pgvector package is not installed.
    """
    if Vector is None:
        raise ImportError("pgvector package is required for vector columns")
    return Column(Vector(dimensions), nullable=nullable)


async def cosine_similarity_search(
    session: AsyncSession,
    table_name: str,
    column_name: str,
    query_vector: list[float],
    limit: int = 10,
) -> list[dict]:
    """
    Perform cosine similarity search against a vector column.

    Args:
        session: Async database session.
        table_name: Name of the table to search.
        column_name: Name of the vector column.
        query_vector: Query embedding vector.
        limit: Maximum number of results.

    Returns:
        list[dict]: Results with id and similarity score.
    """
    vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"
    sql = text(
        f"SELECT id, 1 - ({column_name} <=> :vec::vector) AS similarity "
        f"FROM {table_name} "
        f"ORDER BY {column_name} <=> :vec::vector "
        f"LIMIT :lim"
    )
    result = await session.execute(sql, {"vec": vector_str, "lim": limit})
    return [{"id": row[0], "similarity": row[1]} for row in result.fetchall()]


async def check_vector_extension(session: AsyncSession) -> bool:
    """
    Verify that the pgvector extension is installed and functional.

    Args:
        session: Async database session.

    Returns:
        bool: True if pgvector is available.
    """
    try:
        result = await session.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        )
        return result.scalar() is not None
    except Exception as e:
        logger.error(f"Vector extension check failed: {e}")
        return False
