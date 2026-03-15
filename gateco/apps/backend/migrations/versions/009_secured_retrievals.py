"""Secured retrievals table.

Revision ID: 009
Revises: 008
Create Date: 2026-03-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "secured_retrievals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True,
        ),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column(
            "principal_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("principals.id", ondelete="SET NULL"), nullable=True, index=True,
        ),
        sa.Column("principal_name", sa.String(255), nullable=True),
        sa.Column(
            "connector_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("connectors.id", ondelete="SET NULL"), nullable=True, index=True,
        ),
        sa.Column("connector_name", sa.String(255), nullable=True),
        sa.Column("matched_chunks", sa.Integer, nullable=False, server_default="0"),
        sa.Column("allowed_chunks", sa.Integer, nullable=False, server_default="0"),
        sa.Column("denied_chunks", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "outcome",
            postgresql.ENUM("allowed", "partial", "denied",
                            name="retrieval_outcome", create_type=False),
            nullable=False,
        ),
        sa.Column("denial_reasons", postgresql.JSONB, nullable=True),
        sa.Column("policy_trace", postgresql.JSONB, nullable=True),
        sa.Column("resource_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column("chunk_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False, index=True,
        ),
    )

    op.create_index(
        "ix_secured_retrievals_org_ts", "secured_retrievals",
        ["organization_id", "timestamp"],
    )
    op.create_index(
        "ix_secured_retrievals_org_outcome", "secured_retrievals",
        ["organization_id", "outcome"],
    )


def downgrade() -> None:
    op.drop_index("ix_secured_retrievals_org_outcome", table_name="secured_retrievals")
    op.drop_index("ix_secured_retrievals_org_ts", table_name="secured_retrievals")
    op.drop_table("secured_retrievals")
