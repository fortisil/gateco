"""Subscription model.

Manages Stripe subscription state for organizations.
Tracks plan tier, billing period, and subscription lifecycle.
"""

import datetime
import uuid
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gateco.database.enums import BillingPeriod, PlanTier, SubscriptionStatus
from gateco.database.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from gateco.database.models.organization import Organization


class Subscription(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Subscription model for organization billing.

    Attributes:
        id: UUID primary key
        organization_id: FK to organization (unique - 1:1)
        plan_tier: Current plan tier
        stripe_subscription_id: Stripe subscription ID
        stripe_price_id: Stripe price ID
        status: Subscription status
        billing_period: Monthly or yearly billing
        current_period_start: Start of current billing period
        current_period_end: End of current billing period
        cancel_at_period_end: Whether to cancel at period end
        canceled_at: When subscription was canceled
        trial_start: Trial start timestamp
        trial_end: Trial end timestamp
        created_at: Record creation timestamp
        updated_at: Last modification timestamp

    Properties:
        is_active: True if subscription is active or trialing
        is_canceled: True if subscription is canceled
        days_remaining: Days until period end
    """

    __tablename__ = "subscriptions"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    plan_tier: Mapped[PlanTier] = mapped_column(
        Enum(PlanTier, native_enum=True, name="plan_tier", create_type=False),
        nullable=False,
    )
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )
    stripe_price_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, native_enum=True, name="subscription_status"),
        nullable=False,
        index=True,
    )
    billing_period: Mapped[BillingPeriod] = mapped_column(
        Enum(BillingPeriod, native_enum=True, name="billing_period"),
        nullable=False,
    )
    current_period_start: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    current_period_end: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    canceled_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    trial_start: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    trial_end: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        backref="subscription",
    )

    def __repr__(self) -> str:
        return (
            f"<Subscription(id={self.id}, plan={self.plan_tier.value}, "
            f"status={self.status.value})>"
        )

    @hybrid_property
    def is_active(self) -> bool:
        """Check if subscription is active or trialing."""
        return self.status in (SubscriptionStatus.active, SubscriptionStatus.trialing)

    @is_active.expression
    def is_active(cls) -> Any:  # noqa: N805
        """SQL expression for is_active check."""
        return cls.status.in_([SubscriptionStatus.active, SubscriptionStatus.trialing])

    @hybrid_property
    def is_canceled(self) -> bool:
        """Check if subscription is canceled."""
        return self.canceled_at is not None

    @is_canceled.expression
    def is_canceled(cls) -> Any:  # noqa: N805
        """SQL expression for is_canceled check."""
        return cls.canceled_at.isnot(None)

    @hybrid_property
    def is_trialing(self) -> bool:
        """Check if subscription is in trial period."""
        return self.status == SubscriptionStatus.trialing

    @is_trialing.expression
    def is_trialing(cls) -> Any:  # noqa: N805
        """SQL expression for is_trialing check."""
        return cls.status == SubscriptionStatus.trialing

    @property
    def days_remaining(self) -> int:
        """Get days remaining in current billing period."""
        now = datetime.datetime.now(datetime.timezone.utc)
        delta = self.current_period_end - now
        return max(0, delta.days)

    @property
    def is_yearly(self) -> bool:
        """Check if subscription is on yearly billing."""
        return self.billing_period == BillingPeriod.yearly

    def cancel(self, at_period_end: bool = True) -> None:
        """Cancel the subscription.

        Args:
            at_period_end: If True, cancel at end of period; if False, cancel immediately
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        self.canceled_at = now
        self.cancel_at_period_end = at_period_end
        if not at_period_end:
            self.status = SubscriptionStatus.canceled


__all__ = ["Subscription"]
