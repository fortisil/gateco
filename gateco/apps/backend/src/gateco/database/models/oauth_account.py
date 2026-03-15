"""OAuthAccount model.

Links external OAuth provider accounts to users.
Supports Google and GitHub OAuth providers.
"""

import datetime
import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gateco.database.enums import OAuthProvider
from gateco.database.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from gateco.database.models.user import User


class OAuthAccount(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """OAuth account model linking external providers to users.

    Attributes:
        id: UUID primary key
        user_id: FK to owning user
        provider: OAuth provider (google, github)
        provider_user_id: User ID from the OAuth provider
        access_token: Current access token (encrypted in production)
        refresh_token: Refresh token for getting new access tokens
        expires_at: When the access token expires
        provider_data: Additional data from the provider (JSONB)
        created_at: Record creation timestamp
        updated_at: Last modification timestamp

    Constraints:
        - uq_oauth_provider_user: Each provider account can only link to one user
    """

    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_user_id",
            name="uq_oauth_provider_user",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[OAuthProvider] = mapped_column(
        Enum(OAuthProvider, native_enum=True, name="oauth_provider"),
        nullable=False,
    )
    provider_user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    access_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    refresh_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    provider_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="oauth_accounts",
    )

    def __repr__(self) -> str:
        return (
            f"<OAuthAccount(id={self.id}, provider={self.provider.value}, "
            f"provider_user_id={self.provider_user_id!r})>"
        )

    @hybrid_property
    def is_token_expired(self) -> bool:
        """Check if access token has expired."""
        if self.expires_at is None:
            return False
        now = datetime.datetime.now(datetime.timezone.utc)
        return self.expires_at <= now

    @is_token_expired.expression
    def is_token_expired(cls) -> Any:  # noqa: N805
        """SQL expression for is_token_expired check."""
        from sqlalchemy.sql import func

        return (cls.expires_at.isnot(None)) & (cls.expires_at <= func.now())

    @property
    def has_refresh_token(self) -> bool:
        """Check if refresh token is available."""
        return self.refresh_token is not None

    @property
    def provider_email(self) -> Optional[str]:
        """Get email from provider data if available."""
        if self.provider_data and "email" in self.provider_data:
            return self.provider_data["email"]
        return None

    def update_tokens(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None,
    ) -> None:
        """Update OAuth tokens.

        Args:
            access_token: New access token
            refresh_token: New refresh token (optional)
            expires_in: Token expiration in seconds (optional)
        """
        self.access_token = access_token
        if refresh_token is not None:
            self.refresh_token = refresh_token
        if expires_in is not None:
            self.expires_at = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(seconds=expires_in)


__all__ = ["OAuthAccount"]
