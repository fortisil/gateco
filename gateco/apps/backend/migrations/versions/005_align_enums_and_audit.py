"""Align enums and add audit_events table.

Revision ID: 005
Revises: 004
Create Date: 2026-03-13

- Renames UserRole enum values (D1): owner/admin/member/viewer → org_admin/security_admin/data_owner/developer
- Creates 15 new enum types for the permission-aware retrieval layer
- Creates audit_events table
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Align UserRole, create new enums, create audit_events table."""

    # ── D1: Rename UserRole enum values ──
    op.execute("ALTER TYPE user_role RENAME VALUE 'owner' TO 'org_admin'")
    op.execute("ALTER TYPE user_role RENAME VALUE 'admin' TO 'security_admin'")
    op.execute("ALTER TYPE user_role RENAME VALUE 'member' TO 'data_owner'")
    op.execute("ALTER TYPE user_role RENAME VALUE 'viewer' TO 'developer'")

    # ── Create new enum types ──
    for name, values in _NEW_ENUMS.items():
        enum = postgresql.ENUM(*values, name=name, create_type=True)
        enum.create(op.get_bind(), checkfirst=True)

    # ── Create audit_events table ──
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "event_type",
            postgresql.ENUM(
                *_NEW_ENUMS["audit_event_type"],
                name="audit_event_type",
                create_type=False,
            ),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor_name", sa.String(255), nullable=True),
        sa.Column("principal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=True,
        ),
    )

    op.create_index(
        "ix_audit_events_org_type", "audit_events", ["organization_id", "event_type"]
    )
    op.create_index(
        "ix_audit_events_org_ts", "audit_events", ["organization_id", "timestamp"]
    )


def downgrade() -> None:
    """Drop audit_events, drop new enums, restore old UserRole values."""

    op.drop_index("ix_audit_events_org_ts", table_name="audit_events")
    op.drop_index("ix_audit_events_org_type", table_name="audit_events")
    op.drop_table("audit_events")

    for name in reversed(list(_NEW_ENUMS.keys())):
        op.execute(f"DROP TYPE IF EXISTS {name}")

    # Restore old UserRole values
    op.execute("ALTER TYPE user_role RENAME VALUE 'org_admin' TO 'owner'")
    op.execute("ALTER TYPE user_role RENAME VALUE 'security_admin' TO 'admin'")
    op.execute("ALTER TYPE user_role RENAME VALUE 'data_owner' TO 'member'")
    op.execute("ALTER TYPE user_role RENAME VALUE 'developer' TO 'viewer'")


# All new enum types and their values
_NEW_ENUMS = {
    "connector_type": ["pgvector", "pinecone", "opensearch"],
    "connector_status": ["connected", "error", "syncing", "disconnected"],
    "identity_provider_type": ["azure_entra_id", "aws_iam", "gcp", "okta"],
    "identity_provider_status": ["connected", "error", "syncing", "disconnected"],
    "pipeline_status": ["active", "paused", "error", "running"],
    "pipeline_run_status": ["completed", "failed", "running"],
    "policy_type": ["rbac", "abac", "rebac"],
    "policy_status": ["draft", "active", "archived"],
    "policy_effect": ["allow", "deny"],
    "classification": ["public", "internal", "confidential", "restricted"],
    "sensitivity": ["low", "medium", "high", "critical"],
    "encryption_mode": ["none", "at_rest", "envelope", "full"],
    "audit_event_type": [
        "user_login", "user_logout", "settings_changed",
        "connector_added", "connector_updated", "connector_tested",
        "connector_removed", "connector_sync_started", "connector_synced",
        "connector_sync_failed",
        "idp_added", "idp_updated", "idp_removed",
        "idp_sync_started", "idp_synced", "idp_sync_failed",
        "policy_created", "policy_updated", "policy_activated",
        "policy_archived", "policy_deleted",
        "resource_updated",
        "pipeline_created", "pipeline_updated", "pipeline_run", "pipeline_error",
        "retrieval_allowed", "retrieval_denied",
    ],
    "retrieval_outcome": ["allowed", "partial", "denied"],
    "principal_status": ["active", "inactive", "suspended"],
}
