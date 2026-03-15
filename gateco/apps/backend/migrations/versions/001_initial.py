"""Initial migration: pgvector extension and app_settings table.

Revision ID: 001
Revises: None
Create Date: 2024-01-01 00:00:00.000000

# popeye:requires_extension=vector
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension if available
    import os
    from sqlalchemy import text
    conn = op.get_bind()
    result = conn.execute(
        text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
    )
    if result.fetchone():
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    else:
        import logging
        logging.getLogger("alembic").warning(
            "pgvector extension not available — skipping. "
            "Install pgvector for vector search features."
        )

    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_app_settings_key", "app_settings", ["key"])


def downgrade() -> None:
    op.drop_index("ix_app_settings_key", table_name="app_settings")
    op.drop_table("app_settings")
    op.execute("DROP EXTENSION IF EXISTS vector")
