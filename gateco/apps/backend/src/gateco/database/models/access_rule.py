"""AccessRule model.

Defines access control settings for gated resources.
Supports public, paid, and invite-only access types.
"""

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gateco.database.enums import AccessRuleType
from gateco.database.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from gateco.database.models.resource import GatedResource


class AccessRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Access rule model defining how a resource can be accessed.

    Attributes:
        id: UUID primary key
        resource_id: FK to resource (unique - 1:1 relationship)
        type: Access type (public, paid, invite_only)
        price_cents: Price in cents (for paid access, min 50 = $0.50)
        currency: Currency code (default USD)
        allowed_emails: List of allowed emails (for invite_only)
        created_at: Record creation timestamp
        updated_at: Last modification timestamp

    Constraints:
        - chk_paid_price: If type is 'paid', price_cents must be >= 50
        - chk_invite_emails: If type is 'invite_only', allowed_emails must not be null
    """

    __tablename__ = "access_rules"
    __table_args__ = (
        CheckConstraint(
            "type != 'paid' OR price_cents >= 50",
            name="chk_paid_price",
        ),
        CheckConstraint(
            "type != 'invite_only' OR allowed_emails IS NOT NULL",
            name="chk_invite_emails",
        ),
    )

    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("gated_resources.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    type: Mapped[AccessRuleType] = mapped_column(
        Enum(AccessRuleType, native_enum=True, name="access_rule_type"),
        nullable=False,
    )
    price_cents: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    allowed_emails: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(255)),
        nullable=True,
    )

    # Relationships
    resource: Mapped["GatedResource"] = relationship(
        "GatedResource",
        back_populates="access_rule",
    )

    def __repr__(self) -> str:
        return f"<AccessRule(id={self.id}, type={self.type.value}, resource_id={self.resource_id})>"

    @property
    def is_public(self) -> bool:
        """Check if access is public."""
        return self.type == AccessRuleType.public

    @property
    def is_paid(self) -> bool:
        """Check if access requires payment."""
        return self.type == AccessRuleType.paid

    @property
    def is_invite_only(self) -> bool:
        """Check if access is invite-only."""
        return self.type == AccessRuleType.invite_only

    @property
    def price_dollars(self) -> Optional[float]:
        """Get price in dollars."""
        if self.price_cents is None:
            return None
        return self.price_cents / 100

    def is_email_allowed(self, email: str) -> bool:
        """Check if an email is in the allowed list.

        Args:
            email: Email address to check

        Returns:
            True if email is allowed or access is not invite-only
        """
        if not self.is_invite_only:
            return True
        if self.allowed_emails is None:
            return False
        return email.lower() in [e.lower() for e in self.allowed_emails]

    def add_allowed_email(self, email: str) -> None:
        """Add an email to the allowed list.

        Args:
            email: Email address to add
        """
        if self.allowed_emails is None:
            self.allowed_emails = []
        if email.lower() not in [e.lower() for e in self.allowed_emails]:
            self.allowed_emails = [*self.allowed_emails, email]

    def remove_allowed_email(self, email: str) -> None:
        """Remove an email from the allowed list.

        Args:
            email: Email address to remove
        """
        if self.allowed_emails is None:
            return
        self.allowed_emails = [
            e for e in self.allowed_emails if e.lower() != email.lower()
        ]


__all__ = ["AccessRule"]
