"""Add idempotency_records table and retroactive_registered audit event type.

Revision ID: 014
Revises: 013
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade():
    # Create idempotency_records table
    op.create_table(
        "idempotency_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("org_id", sa.String(36), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("endpoint", sa.String(100), nullable=False),
        sa.Column("response_body", JSONB, nullable=False),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
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
        sa.UniqueConstraint("key", "org_id", name="uq_idempotency_key_org"),
    )
    op.create_index("ix_idempotency_expires", "idempotency_records", ["expires_at"])

    # Add retroactive_registered audit event type
    op.execute("ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'retroactive_registered'")


def downgrade():
    op.drop_index("ix_idempotency_expires", table_name="idempotency_records")
    op.drop_table("idempotency_records")
