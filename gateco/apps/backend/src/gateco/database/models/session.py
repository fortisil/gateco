"""UserSession model.

Stores refresh tokens for JWT authentication.
Sessions can be revoked individually for security.
"""

import datetime
import uuid
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from gateco.database.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from gateco.database.models.user import User


class UserSession(Base, UUIDPrimaryKeyMixin):
    """User session model for refresh token management.

    Attributes:
        id: UUID primary key
        user_id: FK to owning user
        refresh_token_hash: Hash of the refresh token (unique)
        user_agent: Browser/client user agent string
        ip_address: Client IP address (PostgreSQL INET type)
        expires_at: Token expiration timestamp
        revoked_at: When session was revoked (null if active)
        created_at: Session creation timestamp

    Properties:
        is_valid: True if not expired and not revoked
    """

    __tablename__ = "user_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    refresh_token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        INET,
        nullable=True,
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    revoked_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="sessions",
    )

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, valid={self.is_valid})>"

    @hybrid_property
    def is_valid(self) -> bool:
        """Check if session is valid (not expired and not revoked)."""
        now = datetime.datetime.now(datetime.timezone.utc)
        return self.revoked_at is None and self.expires_at > now

    @is_valid.expression
    def is_valid(cls) -> Any:  # noqa: N805
        """SQL expression for is_valid check."""
        return (cls.revoked_at.is_(None)) & (cls.expires_at > func.now())

    @hybrid_property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        now = datetime.datetime.now(datetime.timezone.utc)
        return self.expires_at <= now

    @is_expired.expression
    def is_expired(cls) -> Any:  # noqa: N805
        """SQL expression for is_expired check."""
        return cls.expires_at <= func.now()

    @hybrid_property
    def is_revoked(self) -> bool:
        """Check if session has been revoked."""
        return self.revoked_at is not None

    @is_revoked.expression
    def is_revoked(cls) -> Any:  # noqa: N805
        """SQL expression for is_revoked check."""
        return cls.revoked_at.isnot(None)

    def revoke(self) -> None:
        """Revoke this session."""
        self.revoked_at = datetime.datetime.now(datetime.timezone.utc)


__all__ = ["UserSession"]
