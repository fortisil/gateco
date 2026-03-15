"""Add binding support: external_resource_key + source_connector_id on chunks.

Revision ID: 012
Revises: 011
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade():
    # Add external_resource_key to gated_resources for stable binding identity
    op.add_column(
        "gated_resources",
        sa.Column("external_resource_key", sa.String(500), nullable=True),
    )
    # Unique constraint: (org, connector, external_key)
    op.create_index(
        "uq_gated_resources_ext_key",
        "gated_resources",
        ["organization_id", "source_connector_id", "external_resource_key"],
        unique=True,
        postgresql_where=text(
            "external_resource_key IS NOT NULL AND deleted_at IS NULL"
        ),
    )

    # Add source_connector_id to resource_chunks (denormalized for scoped lookups)
    op.add_column(
        "resource_chunks",
        sa.Column(
            "source_connector_id",
            UUID(as_uuid=True),
            sa.ForeignKey("connectors.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    # Index for fast vector_id lookups scoped by connector
    op.create_index(
        "ix_resource_chunks_connector_vector",
        "resource_chunks",
        ["source_connector_id", "vector_id"],
    )
    # Connector-scoped unique constraint on vector_id
    op.create_index(
        "uq_resource_chunks_connector_vector_id",
        "resource_chunks",
        ["source_connector_id", "vector_id"],
        unique=True,
        postgresql_where=text(
            "vector_id IS NOT NULL AND source_connector_id IS NOT NULL"
        ),
    )
    # Index for coverage counting
    op.create_index(
        "ix_gated_resources_source_connector",
        "gated_resources",
        ["source_connector_id"],
        postgresql_where=text("deleted_at IS NULL"),
    )


def downgrade():
    op.drop_index("ix_gated_resources_source_connector", table_name="gated_resources")
    op.drop_index(
        "uq_resource_chunks_connector_vector_id", table_name="resource_chunks"
    )
    op.drop_index(
        "ix_resource_chunks_connector_vector", table_name="resource_chunks"
    )
    op.drop_column("resource_chunks", "source_connector_id")
    op.drop_index("uq_gated_resources_ext_key", table_name="gated_resources")
    op.drop_column("gated_resources", "external_resource_key")
