"""Resources and access control tables.

Revision ID: 003
Revises: 002
Create Date: 2026-02-28

Creates resource management models:
- gated_resources: Access-controlled content
- access_rules: Access control settings
- invites: Resource invitations
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Phase 2 tables: gated_resources, access_rules, invites."""
    # Create ENUM types
    resource_type = postgresql.ENUM(
        "link", "file", "video",
        name="resource_type",
        create_type=True,
    )
    resource_type.create(op.get_bind(), checkfirst=True)

    access_rule_type = postgresql.ENUM(
        "public", "paid", "invite_only",
        name="access_rule_type",
        create_type=True,
    )
    access_rule_type.create(op.get_bind(), checkfirst=True)

    # Create gated_resources table
    op.create_table(
        "gated_resources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "type",
            postgresql.ENUM(
                "link", "file", "video",
                name="resource_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("content_url", sa.String(2048), nullable=False),
        sa.Column("thumbnail_url", sa.String(2048), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("view_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("unique_viewers", sa.Integer, nullable=False, server_default="0"),
        sa.Column("revenue_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
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
    )

    # Gated resources indexes
    op.create_index(
        "ix_gated_resources_organization_id",
        "gated_resources",
        ["organization_id"],
    )
    op.create_index(
        "ix_gated_resources_type",
        "gated_resources",
        ["type"],
    )
    op.create_index(
        "ix_gated_resources_deleted_at",
        "gated_resources",
        ["deleted_at"],
    )
    op.create_index(
        "ix_gated_resources_org_type",
        "gated_resources",
        ["organization_id", "type"],
    )
    op.create_index(
        "ix_gated_resources_org_deleted",
        "gated_resources",
        ["organization_id", "deleted_at"],
    )
    op.create_index(
        "ix_gated_resources_created_by",
        "gated_resources",
        ["created_by"],
    )

    # Create access_rules table
    op.create_table(
        "access_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "resource_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("gated_resources.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column(
            "type",
            postgresql.ENUM(
                "public", "paid", "invite_only",
                name="access_rule_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("price_cents", sa.Integer, nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column(
            "allowed_emails",
            postgresql.ARRAY(sa.String(255)),
            nullable=True,
        ),
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
        # Check constraints
        sa.CheckConstraint(
            "type != 'paid' OR price_cents >= 50",
            name="chk_paid_price",
        ),
        sa.CheckConstraint(
            "type != 'invite_only' OR allowed_emails IS NOT NULL",
            name="chk_invite_emails",
        ),
    )

    # Access rules indexes
    op.create_index(
        "ix_access_rules_resource_id",
        "access_rules",
        ["resource_id"],
        unique=True,
    )

    # Create invites table
    op.create_table(
        "invites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "resource_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("gated_resources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("token", sa.String(64), unique=True, nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Invites indexes
    op.create_index("ix_invites_resource_id", "invites", ["resource_id"])
    op.create_index("ix_invites_token", "invites", ["token"], unique=True)
    op.create_index("ix_invites_expires_at", "invites", ["expires_at"])
    op.create_index("ix_invites_email", "invites", ["email"])


def downgrade() -> None:
    """Drop Phase 2 tables in reverse order."""
    # Drop invites
    op.drop_index("ix_invites_email", table_name="invites")
    op.drop_index("ix_invites_expires_at", table_name="invites")
    op.drop_index("ix_invites_token", table_name="invites")
    op.drop_index("ix_invites_resource_id", table_name="invites")
    op.drop_table("invites")

    # Drop access_rules
    op.drop_index("ix_access_rules_resource_id", table_name="access_rules")
    op.drop_table("access_rules")

    # Drop gated_resources
    op.drop_index("ix_gated_resources_created_by", table_name="gated_resources")
    op.drop_index("ix_gated_resources_org_deleted", table_name="gated_resources")
    op.drop_index("ix_gated_resources_org_type", table_name="gated_resources")
    op.drop_index("ix_gated_resources_deleted_at", table_name="gated_resources")
    op.drop_index("ix_gated_resources_type", table_name="gated_resources")
    op.drop_index("ix_gated_resources_organization_id", table_name="gated_resources")
    op.drop_table("gated_resources")

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS access_rule_type")
    op.execute("DROP TYPE IF EXISTS resource_type")
