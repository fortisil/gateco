"""Invite model.

Manages invitations for invite-only resources.
Invites have unique tokens and can expire.
"""

import datetime
import secrets
import uuid
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from gateco.database.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from gateco.database.models.resource import GatedResource


def generate_invite_token() -> str:
    """Generate a secure invite token."""
    return secrets.token_urlsafe(32)


class Invite(Base, UUIDPrimaryKeyMixin):
    """Invite model for resource access invitations.

    Attributes:
        id: UUID primary key
        resource_id: FK to the resource being shared
        email: Invited user's email address
        token: Unique invite token (URL-safe)
        used_at: When the invite was used (null if unused)
        expires_at: Invite expiration timestamp
        created_at: Record creation timestamp

    Properties:
        is_valid: True if not used and not expired
        is_used: True if the invite has been used
        is_expired: True if the invite has expired
    """

    __tablename__ = "invites"

    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("gated_resources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        default=generate_invite_token,
    )
    used_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    resource: Mapped["GatedResource"] = relationship(
        "GatedResource",
        back_populates="invites",
    )

    def __repr__(self) -> str:
        return f"<Invite(id={self.id}, email={self.email!r}, valid={self.is_valid})>"

    @hybrid_property
    def is_valid(self) -> bool:
        """Check if invite is valid (not used and not expired)."""
        now = datetime.datetime.now(datetime.timezone.utc)
        return self.used_at is None and self.expires_at > now

    @is_valid.expression
    def is_valid(cls) -> Any:  # noqa: N805
        """SQL expression for is_valid check."""
        return (cls.used_at.is_(None)) & (cls.expires_at > func.now())

    @hybrid_property
    def is_used(self) -> bool:
        """Check if invite has been used."""
        return self.used_at is not None

    @is_used.expression
    def is_used(cls) -> Any:  # noqa: N805
        """SQL expression for is_used check."""
        return cls.used_at.isnot(None)

    @hybrid_property
    def is_expired(self) -> bool:
        """Check if invite has expired."""
        now = datetime.datetime.now(datetime.timezone.utc)
        return self.expires_at <= now

    @is_expired.expression
    def is_expired(cls) -> Any:  # noqa: N805
        """SQL expression for is_expired check."""
        return cls.expires_at <= func.now()

    def use(self) -> None:
        """Mark the invite as used."""
        self.used_at = datetime.datetime.now(datetime.timezone.utc)

    @classmethod
    def create_for_resource(
        cls,
        resource_id: uuid.UUID,
        email: str,
        expires_in_days: int = 7,
    ) -> "Invite":
        """Create a new invite for a resource.

        Args:
            resource_id: Resource to invite to
            email: Email address to invite
            expires_in_days: Days until expiration (default 7)

        Returns:
            New Invite instance
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        return cls(
            resource_id=resource_id,
            email=email,
            token=generate_invite_token(),
            expires_at=now + datetime.timedelta(days=expires_in_days),
        )


__all__ = ["Invite", "generate_invite_token"]
