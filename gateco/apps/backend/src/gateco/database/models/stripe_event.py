"""StripeEvent model.

Stores Stripe webhook events for idempotent processing.
Ensures each webhook is processed exactly once.
"""

import datetime
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from gateco.database.models.base import Base, UUIDPrimaryKeyMixin


class StripeEvent(Base, UUIDPrimaryKeyMixin):
    """Stripe webhook event model for idempotent processing.

    Attributes:
        id: UUID primary key
        stripe_event_id: Stripe event ID (unique)
        event_type: Stripe event type (e.g., 'invoice.paid')
        organization_id: FK to related organization (nullable)
        processed: Whether the event has been processed
        error_message: Error message if processing failed
        payload: Full webhook payload (JSONB)
        created_at: When event was received
        processed_at: When event was processed

    Purpose:
        - Ensures idempotent webhook handling
        - Stores event payload for debugging
        - Tracks processing status and errors
    """

    __tablename__ = "stripe_events"

    stripe_event_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    processed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    payload: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    processed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    organization = relationship(
        "Organization",
        backref="stripe_events",
    )

    def __repr__(self) -> str:
        return (
            f"<StripeEvent(id={self.id}, type={self.event_type!r}, "
            f"processed={self.processed})>"
        )

    @property
    def is_processed(self) -> bool:
        """Check if event has been processed."""
        return self.processed

    @property
    def has_error(self) -> bool:
        """Check if event processing had an error."""
        return self.error_message is not None

    def mark_processed(self) -> None:
        """Mark the event as successfully processed."""
        self.processed = True
        self.processed_at = datetime.datetime.now(datetime.timezone.utc)
        self.error_message = None

    def mark_failed(self, error: str) -> None:
        """Mark the event as failed with an error message.

        Args:
            error: Error message describing the failure
        """
        self.processed = False
        self.error_message = error
        self.processed_at = datetime.datetime.now(datetime.timezone.utc)

    @classmethod
    def create_from_webhook(
        cls,
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
        organization_id: Optional[uuid.UUID] = None,
    ) -> "StripeEvent":
        """Create a new StripeEvent from a webhook payload.

        Args:
            event_id: Stripe event ID
            event_type: Stripe event type
            payload: Full webhook payload
            organization_id: Related organization ID (optional)

        Returns:
            New StripeEvent instance
        """
        return cls(
            stripe_event_id=event_id,
            event_type=event_type,
            payload=payload,
            organization_id=organization_id,
            processed=False,
        )


__all__ = ["StripeEvent"]
