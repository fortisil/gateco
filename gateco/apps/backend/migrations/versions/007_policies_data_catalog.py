"""Policies, policy rules, resource chunks + gated_resources columns.

Revision ID: 007
Revises: 006
Create Date: 2026-03-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── policies ──
    op.create_table(
        "policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "type",
            postgresql.ENUM("rbac", "abac", "rebac", name="policy_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM("draft", "active", "archived", name="policy_status", create_type=False),
            nullable=False, server_default="draft",
        ),
        sa.Column(
            "effect",
            postgresql.ENUM("allow", "deny", name="policy_effect", create_type=False),
            nullable=False,
        ),
        sa.Column("resource_selectors", postgresql.JSONB, nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, index=True),
    )

    # ── policy_rules ──
    op.create_table(
        "policy_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "policy_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True,
        ),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column(
            "effect",
            postgresql.ENUM("allow", "deny", name="policy_effect", create_type=False),
            nullable=False,
        ),
        sa.Column("conditions", postgresql.JSONB, nullable=True),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── resource_chunks ──
    op.create_table(
        "resource_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "resource_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("gated_resources.id", ondelete="CASCADE"), nullable=False, index=True,
        ),
        sa.Column("index", sa.Integer, nullable=False),
        sa.Column("preview", sa.Text, nullable=True),
        sa.Column("encrypted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("vector_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Add columns to gated_resources ──
    op.add_column("gated_resources", sa.Column(
        "classification",
        postgresql.ENUM("public", "internal", "confidential", "restricted",
                        name="classification", create_type=False),
        nullable=True,
    ))
    op.add_column("gated_resources", sa.Column(
        "sensitivity",
        postgresql.ENUM("low", "medium", "high", "critical",
                        name="sensitivity", create_type=False),
        nullable=True,
    ))
    op.add_column("gated_resources", sa.Column("domain", sa.String(200), nullable=True))
    op.add_column("gated_resources", sa.Column("labels", postgresql.ARRAY(sa.String), nullable=True))
    op.add_column("gated_resources", sa.Column(
        "encryption_mode",
        postgresql.ENUM("none", "at_rest", "envelope", "full",
                        name="encryption_mode", create_type=False),
        nullable=True,
    ))
    op.add_column("gated_resources", sa.Column(
        "source_connector_id", postgresql.UUID(as_uuid=True),
        sa.ForeignKey("connectors.id", ondelete="SET NULL"), nullable=True,
    ))


def downgrade() -> None:
    op.drop_column("gated_resources", "source_connector_id")
    op.drop_column("gated_resources", "encryption_mode")
    op.drop_column("gated_resources", "labels")
    op.drop_column("gated_resources", "domain")
    op.drop_column("gated_resources", "sensitivity")
    op.drop_column("gated_resources", "classification")
    op.drop_table("resource_chunks")
    op.drop_table("policy_rules")
    op.drop_table("policies")
