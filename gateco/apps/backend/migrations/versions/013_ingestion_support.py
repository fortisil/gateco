"""Add ingestion support: owner_principal, content_hash, ingestion_config.

Revision ID: 013
Revises: 012
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade():
    # Add owner_principal to gated_resources
    op.add_column(
        "gated_resources",
        sa.Column(
            "owner_principal",
            UUID(as_uuid=True),
            sa.ForeignKey("principals.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Add content_hash to resource_chunks for dedup
    op.add_column(
        "resource_chunks",
        sa.Column("content_hash", sa.String(64), nullable=True),
    )
    # Unique constraint for content dedup: (resource_id, content_hash)
    op.create_index(
        "uq_resource_chunks_content_hash",
        "resource_chunks",
        ["resource_id", "content_hash"],
        unique=True,
        postgresql_where=text("content_hash IS NOT NULL"),
    )

    # Add ingestion_config to connectors
    op.add_column(
        "connectors",
        sa.Column("ingestion_config", JSONB, nullable=True),
    )

    # Add new audit event types
    op.execute("ALTER TYPE auditeventtype ADD VALUE IF NOT EXISTS 'document_ingested'")
    op.execute("ALTER TYPE auditeventtype ADD VALUE IF NOT EXISTS 'batch_ingested'")
    op.execute("ALTER TYPE auditeventtype ADD VALUE IF NOT EXISTS 'ingestion_failed'")


def downgrade():
    op.drop_index("uq_resource_chunks_content_hash", table_name="resource_chunks")
    op.drop_column("resource_chunks", "content_hash")
    op.drop_column("gated_resources", "owner_principal")
    op.drop_column("connectors", "ingestion_config")
