"""Coupon model.

Manages discount coupons for subscriptions.
Supports percentage and fixed amount discounts.
"""

import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from gateco.database.enums import DiscountType
from gateco.database.models.base import Base, UUIDPrimaryKeyMixin


class Coupon(Base, UUIDPrimaryKeyMixin):
    """Coupon model for subscription discounts.

    Attributes:
        id: UUID primary key
        code: Unique coupon code
        stripe_coupon_id: Stripe coupon ID
        discount_type: Type of discount (percentage or fixed)
        discount_value: Discount amount (percent or cents)
        currency: Currency for fixed amount discounts
        max_redemptions: Maximum number of uses
        redemption_count: Current redemption count
        valid_from: When coupon becomes valid
        valid_until: When coupon expires
        created_at: Record creation timestamp

    Constraints:
        - chk_discount_value: discount_value must be positive
        - chk_percent_range: percentage must be 1-100

    Properties:
        is_valid: True if coupon is within validity period and not exhausted
    """

    __tablename__ = "coupons"
    __table_args__ = (
        CheckConstraint(
            "discount_value > 0",
            name="chk_discount_value",
        ),
        CheckConstraint(
            "discount_type != 'percentage' OR (discount_value >= 1 AND discount_value <= 100)",
            name="chk_percent_range",
        ),
    )

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    stripe_coupon_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )
    discount_type: Mapped[DiscountType] = mapped_column(
        Enum(DiscountType, native_enum=True, name="discount_type"),
        nullable=False,
    )
    discount_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    currency: Mapped[Optional[str]] = mapped_column(
        String(3),
        nullable=True,
    )
    max_redemptions: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    redemption_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    valid_from: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    valid_until: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Coupon(id={self.id}, code={self.code!r}, "
            f"type={self.discount_type.value})>"
        )

    @property
    def is_percentage(self) -> bool:
        """Check if coupon is percentage-based."""
        return self.discount_type == DiscountType.percentage

    @property
    def is_fixed_amount(self) -> bool:
        """Check if coupon is fixed amount."""
        return self.discount_type == DiscountType.fixed_amount

    @property
    def is_valid(self) -> bool:
        """Check if coupon is currently valid."""
        now = datetime.datetime.now(datetime.timezone.utc)

        # Check validity period
        if now < self.valid_from:
            return False
        if self.valid_until is not None and now > self.valid_until:
            return False

        # Check redemption limit
        if (
            self.max_redemptions is not None
            and self.redemption_count >= self.max_redemptions
        ):
            return False

        return True

    @property
    def is_exhausted(self) -> bool:
        """Check if coupon has reached max redemptions."""
        if self.max_redemptions is None:
            return False
        return self.redemption_count >= self.max_redemptions

    @property
    def remaining_redemptions(self) -> Optional[int]:
        """Get remaining redemptions (None if unlimited)."""
        if self.max_redemptions is None:
            return None
        return max(0, self.max_redemptions - self.redemption_count)

    def calculate_discount(self, amount_cents: int) -> int:
        """Calculate discount amount for a given price.

        Args:
            amount_cents: Original price in cents

        Returns:
            Discount amount in cents
        """
        if self.is_percentage:
            return int(amount_cents * self.discount_value / 100)
        else:
            return min(self.discount_value, amount_cents)

    def redeem(self) -> None:
        """Record a redemption of this coupon."""
        self.redemption_count += 1


__all__ = ["Coupon"]
