"""Expand connector types and add diagnostic columns.

Revision ID: 010
Revises: 009
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade():
    # Add 6 new values to the connector_type enum
    # Note: PostgreSQL enum name confirmed as 'connector_type' from migration 005/006
    for value in ["supabase", "neon", "weaviate", "qdrant", "milvus", "chroma"]:
        op.execute(f"ALTER TYPE connector_type ADD VALUE IF NOT EXISTS '{value}'")

    # Add diagnostic columns to connectors table
    op.add_column("connectors", sa.Column("last_tested_at", sa.DateTime(timezone=True)))
    op.add_column("connectors", sa.Column("last_test_success", sa.Boolean))
    op.add_column("connectors", sa.Column("last_test_latency_ms", sa.Integer))
    op.add_column("connectors", sa.Column("diagnostics", JSONB))
    op.add_column("connectors", sa.Column("server_version", sa.String(100)))


def downgrade():
    # PostgreSQL does not support removing enum values.
    # Only drop the added columns.
    op.drop_column("connectors", "server_version")
    op.drop_column("connectors", "diagnostics")
    op.drop_column("connectors", "last_test_latency_ms")
    op.drop_column("connectors", "last_test_success")
    op.drop_column("connectors", "last_tested_at")
