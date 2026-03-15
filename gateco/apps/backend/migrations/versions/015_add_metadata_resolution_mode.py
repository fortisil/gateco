"""Add metadata_resolution_mode to connectors.

Revision ID: 015
Revises: 014
"""

import sqlalchemy as sa
from alembic import op


revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "connectors",
        sa.Column(
            "metadata_resolution_mode",
            sa.String(20),
            nullable=True,
            server_default="sidecar",
        ),
    )


def downgrade() -> None:
    op.drop_column("connectors", "metadata_resolution_mode")
