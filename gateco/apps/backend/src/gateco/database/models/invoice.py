"""Invoice model.

Stores subscription invoice records from Stripe.
Tracks billing periods and payment status.
"""

import datetime
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from gateco.database.enums import InvoiceStatus
from gateco.database.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from gateco.database.models.organization import Organization
    from gateco.database.models.subscription import Subscription


class Invoice(Base, UUIDPrimaryKeyMixin):
    """Invoice model for subscription billing records.

    Attributes:
        id: UUID primary key
        organization_id: FK to organization billed
        subscription_id: FK to associated subscription
        stripe_invoice_id: Stripe invoice ID
        amount_cents: Invoice amount in cents
        currency: Currency code
        status: Invoice status
        period_start: Billing period start
        period_end: Billing period end
        pdf_url: URL to invoice PDF
        hosted_invoice_url: Stripe hosted invoice URL
        due_date: Invoice due date
        paid_at: When invoice was paid
        created_at: Record creation timestamp

    Properties:
        amount_dollars: Invoice amount in dollars
        is_paid: True if invoice is paid
    """

    __tablename__ = "invoices"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    stripe_invoice_id: Mapped[Optional[str]] = mapped_column(
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
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, native_enum=True, name="invoice_status"),
        nullable=False,
    )
    period_start: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    period_end: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    pdf_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    hosted_invoice_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    due_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    paid_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
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
        backref="invoices",
    )
    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription",
        backref="invoices",
    )

    def __repr__(self) -> str:
        return (
            f"<Invoice(id={self.id}, amount={self.amount_cents}, "
            f"status={self.status.value})>"
        )

    @property
    def amount_dollars(self) -> float:
        """Get invoice amount in dollars."""
        return self.amount_cents / 100

    @property
    def is_paid(self) -> bool:
        """Check if invoice is paid."""
        return self.status == InvoiceStatus.paid

    @property
    def is_open(self) -> bool:
        """Check if invoice is open (awaiting payment)."""
        return self.status == InvoiceStatus.open

    @property
    def is_void(self) -> bool:
        """Check if invoice is voided."""
        return self.status == InvoiceStatus.void

    def mark_paid(self) -> None:
        """Mark the invoice as paid."""
        self.status = InvoiceStatus.paid
        self.paid_at = datetime.datetime.now(datetime.timezone.utc)


__all__ = ["Invoice"]
