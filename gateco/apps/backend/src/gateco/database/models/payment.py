"""Payment model.

Records payment transactions for resource purchases and subscriptions.
Integrates with Stripe PaymentIntents.
"""

import datetime
import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from gateco.database.enums import PaymentStatus
from gateco.database.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from gateco.database.models.organization import Organization
    from gateco.database.models.resource import GatedResource


class Payment(Base, UUIDPrimaryKeyMixin):
    """Payment model for transaction records.

    Attributes:
        id: UUID primary key
        organization_id: FK to organization receiving payment
        resource_id: FK to purchased resource (nullable)
        stripe_payment_intent_id: Stripe PaymentIntent ID
        amount_cents: Payment amount in cents
        currency: Currency code (e.g., USD)
        status: Payment status
        customer_email: Customer's email address
        customer_name: Customer's name
        metadata: Additional payment metadata
        created_at: Record creation timestamp

    Properties:
        amount_dollars: Payment amount in dollars
        is_succeeded: True if payment succeeded
    """

    __tablename__ = "payments"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("gated_resources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )
    amount_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=True, name="payment_status"),
        nullable=False,
    )
    customer_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    customer_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    payment_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        backref="payments",
    )
    resource: Mapped[Optional["GatedResource"]] = relationship(
        "GatedResource",
        backref="payments",
    )

    def __repr__(self) -> str:
        return (
            f"<Payment(id={self.id}, amount={self.amount_cents}, "
            f"status={self.status.value})>"
        )

    @property
    def amount_dollars(self) -> float:
        """Get payment amount in dollars."""
        return self.amount_cents / 100

    @property
    def is_succeeded(self) -> bool:
        """Check if payment succeeded."""
        return self.status == PaymentStatus.succeeded

    @property
    def is_pending(self) -> bool:
        """Check if payment is pending."""
        return self.status == PaymentStatus.pending

    @property
    def is_failed(self) -> bool:
        """Check if payment failed."""
        return self.status == PaymentStatus.failed

    @property
    def is_refunded(self) -> bool:
        """Check if payment was refunded."""
        return self.status == PaymentStatus.refunded


__all__ = ["Payment"]
