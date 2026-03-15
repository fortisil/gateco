"""Add search_config to connectors and audit columns to secured_retrievals.

Revision ID: 011
Revises: 010
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("connectors", sa.Column("search_config", JSONB, nullable=True))
    op.add_column(
        "secured_retrievals",
        sa.Column("unresolved_chunks", sa.Integer, server_default="0", nullable=False),
    )
    op.add_column(
        "secured_retrievals",
        sa.Column("connector_latency_ms", sa.Integer, nullable=True),
    )


def downgrade():
    op.drop_column("secured_retrievals", "connector_latency_ms")
    op.drop_column("secured_retrievals", "unresolved_chunks")
    op.drop_column("connectors", "search_config")
