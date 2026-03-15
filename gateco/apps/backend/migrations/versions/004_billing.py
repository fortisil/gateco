"""Billing and payments tables.

Revision ID: 004
Revises: 003
Create Date: 2026-02-28

Creates billing models:
- subscriptions: Stripe subscription state
- payments: Payment transactions
- invoices: Subscription invoices
- usage_logs: Usage tracking
- coupons: Discount codes
- stripe_events: Webhook event tracking
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Phase 3 tables: billing models."""
    # Create ENUM types
    subscription_status = postgresql.ENUM(
        "active", "past_due", "canceled", "incomplete",
        "incomplete_expired", "trialing", "unpaid",
        name="subscription_status",
        create_type=True,
    )
    subscription_status.create(op.get_bind(), checkfirst=True)

    billing_period = postgresql.ENUM(
        "monthly", "yearly",
        name="billing_period",
        create_type=True,
    )
    billing_period.create(op.get_bind(), checkfirst=True)

    payment_status = postgresql.ENUM(
        "succeeded", "pending", "failed", "refunded",
        name="payment_status",
        create_type=True,
    )
    payment_status.create(op.get_bind(), checkfirst=True)

    invoice_status = postgresql.ENUM(
        "draft", "open", "paid", "void", "uncollectible",
        name="invoice_status",
        create_type=True,
    )
    invoice_status.create(op.get_bind(), checkfirst=True)

    discount_type = postgresql.ENUM(
        "percentage", "fixed_amount",
        name="discount_type",
        create_type=True,
    )
    discount_type.create(op.get_bind(), checkfirst=True)

    # Create subscriptions table
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column(
            "plan_tier",
            postgresql.ENUM(
                "free", "pro", "enterprise",
                name="plan_tier",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("stripe_subscription_id", sa.String(255), unique=True, nullable=True),
        sa.Column("stripe_price_id", sa.String(255), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active", "past_due", "canceled", "incomplete",
                "incomplete_expired", "trialing", "unpaid",
                name="subscription_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "billing_period",
            postgresql.ENUM(
                "monthly", "yearly",
                name="billing_period",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "cancel_at_period_end",
            sa.Boolean,
            nullable=False,
            server_default="false",
        ),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
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

    # Subscriptions indexes
    op.create_index(
        "ix_subscriptions_organization_id",
        "subscriptions",
        ["organization_id"],
        unique=True,
    )
    op.create_index(
        "ix_subscriptions_stripe_subscription_id",
        "subscriptions",
        ["stripe_subscription_id"],
        unique=True,
    )
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])

    # Create payments table
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "resource_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("gated_resources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "stripe_payment_intent_id",
            sa.String(255),
            unique=True,
            nullable=True,
        ),
        sa.Column("amount_cents", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column(
            "status",
            postgresql.ENUM(
                "succeeded", "pending", "failed", "refunded",
                name="payment_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("customer_email", sa.String(255), nullable=True),
        sa.Column("customer_name", sa.String(100), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Payments indexes
    op.create_index("ix_payments_organization_id", "payments", ["organization_id"])
    op.create_index("ix_payments_resource_id", "payments", ["resource_id"])
    op.create_index(
        "ix_payments_stripe_payment_intent_id",
        "payments",
        ["stripe_payment_intent_id"],
        unique=True,
    )

    # Create invoices table
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "subscription_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subscriptions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("stripe_invoice_id", sa.String(255), unique=True, nullable=True),
        sa.Column("amount_cents", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column(
            "status",
            postgresql.ENUM(
                "draft", "open", "paid", "void", "uncollectible",
                name="invoice_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pdf_url", sa.String(2048), nullable=True),
        sa.Column("hosted_invoice_url", sa.String(2048), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Invoices indexes
    op.create_index("ix_invoices_organization_id", "invoices", ["organization_id"])
    op.create_index("ix_invoices_subscription_id", "invoices", ["subscription_id"])
    op.create_index(
        "ix_invoices_stripe_invoice_id",
        "invoices",
        ["stripe_invoice_id"],
        unique=True,
    )

    # Create usage_logs table
    op.create_table(
        "usage_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "secured_retrievals",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "resources_created",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "storage_bytes",
            sa.BigInteger,
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "overage_cents",
            sa.Integer,
            nullable=False,
            server_default="0",
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
        sa.UniqueConstraint(
            "organization_id",
            "period_start",
            name="uq_usage_org_period",
        ),
    )

    # Usage logs indexes
    op.create_index("ix_usage_logs_organization_id", "usage_logs", ["organization_id"])
    op.create_index(
        "ix_usage_logs_org_period",
        "usage_logs",
        ["organization_id", "period_start"],
    )

    # Create coupons table
    op.create_table(
        "coupons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("stripe_coupon_id", sa.String(255), unique=True, nullable=True),
        sa.Column(
            "discount_type",
            postgresql.ENUM(
                "percentage", "fixed_amount",
                name="discount_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("discount_value", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("max_redemptions", sa.Integer, nullable=True),
        sa.Column("redemption_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "valid_from",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("discount_value > 0", name="chk_discount_value"),
        sa.CheckConstraint(
            "discount_type != 'percentage' OR (discount_value >= 1 AND discount_value <= 100)",
            name="chk_percent_range",
        ),
    )

    # Coupons indexes
    op.create_index("ix_coupons_code", "coupons", ["code"], unique=True)
    op.create_index("ix_coupons_stripe_coupon_id", "coupons", ["stripe_coupon_id"])

    # Create stripe_events table
    op.create_table(
        "stripe_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stripe_event_id", sa.String(255), unique=True, nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("processed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Stripe events indexes
    op.create_index(
        "ix_stripe_events_stripe_event_id",
        "stripe_events",
        ["stripe_event_id"],
        unique=True,
    )
    op.create_index("ix_stripe_events_event_type", "stripe_events", ["event_type"])
    op.create_index(
        "ix_stripe_events_organization_id",
        "stripe_events",
        ["organization_id"],
    )
    op.create_index("ix_stripe_events_processed", "stripe_events", ["processed"])


def downgrade() -> None:
    """Drop Phase 3 tables in reverse order."""
    # Drop stripe_events
    op.drop_index("ix_stripe_events_processed", table_name="stripe_events")
    op.drop_index("ix_stripe_events_organization_id", table_name="stripe_events")
    op.drop_index("ix_stripe_events_event_type", table_name="stripe_events")
    op.drop_index("ix_stripe_events_stripe_event_id", table_name="stripe_events")
    op.drop_table("stripe_events")

    # Drop coupons
    op.drop_index("ix_coupons_stripe_coupon_id", table_name="coupons")
    op.drop_index("ix_coupons_code", table_name="coupons")
    op.drop_table("coupons")

    # Drop usage_logs
    op.drop_index("ix_usage_logs_org_period", table_name="usage_logs")
    op.drop_index("ix_usage_logs_organization_id", table_name="usage_logs")
    op.drop_table("usage_logs")

    # Drop invoices
    op.drop_index("ix_invoices_stripe_invoice_id", table_name="invoices")
    op.drop_index("ix_invoices_subscription_id", table_name="invoices")
    op.drop_index("ix_invoices_organization_id", table_name="invoices")
    op.drop_table("invoices")

    # Drop payments
    op.drop_index("ix_payments_stripe_payment_intent_id", table_name="payments")
    op.drop_index("ix_payments_resource_id", table_name="payments")
    op.drop_index("ix_payments_organization_id", table_name="payments")
    op.drop_table("payments")

    # Drop subscriptions
    op.drop_index("ix_subscriptions_status", table_name="subscriptions")
    op.drop_index(
        "ix_subscriptions_stripe_subscription_id",
        table_name="subscriptions",
    )
    op.drop_index("ix_subscriptions_organization_id", table_name="subscriptions")
    op.drop_table("subscriptions")

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS discount_type")
    op.execute("DROP TYPE IF EXISTS invoice_status")
    op.execute("DROP TYPE IF EXISTS payment_status")
    op.execute("DROP TYPE IF EXISTS billing_period")
    op.execute("DROP TYPE IF EXISTS subscription_status")
