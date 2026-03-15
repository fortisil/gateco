"""Connectors, identity providers, principals, principal groups.

Revision ID: 006
Revises: 005
Create Date: 2026-03-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── connectors ──
    op.create_table(
        "connectors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM("pgvector", "pinecone", "opensearch",
                            name="connector_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM("connected", "error", "syncing", "disconnected",
                            name="connector_status", create_type=False),
            nullable=False, server_default="disconnected",
        ),
        sa.Column("config", postgresql.JSONB, nullable=True),
        sa.Column("last_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column("index_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("record_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, index=True),
    )

    # ── identity_providers ──
    op.create_table(
        "identity_providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM("azure_entra_id", "aws_iam", "gcp", "okta",
                            name="identity_provider_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM("connected", "error", "syncing", "disconnected",
                            name="identity_provider_status", create_type=False),
            nullable=False, server_default="disconnected",
        ),
        sa.Column("config", postgresql.JSONB, nullable=True),
        sa.Column("sync_config", postgresql.JSONB, nullable=True),
        sa.Column("principal_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("group_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, index=True),
    )

    # ── principals ──
    op.create_table(
        "principals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True,
        ),
        sa.Column(
            "identity_provider_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity_providers.id", ondelete="CASCADE"), nullable=False, index=True,
        ),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("groups", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("roles", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("attributes", postgresql.JSONB, nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("active", "inactive", "suspended",
                            name="principal_status", create_type=False),
            nullable=False, server_default="active",
        ),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "organization_id", "identity_provider_id", "external_id",
            name="uq_principal_org_idp_ext",
        ),
    )

    # ── principal_groups ──
    op.create_table(
        "principal_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True,
        ),
        sa.Column(
            "identity_provider_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity_providers.id", ondelete="CASCADE"), nullable=False, index=True,
        ),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("member_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("principal_groups")
    op.drop_table("principals")
    op.drop_table("identity_providers")
    op.drop_table("connectors")
