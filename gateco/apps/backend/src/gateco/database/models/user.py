"""User model.

Users belong to an organization and have roles within it.
Supports both password and OAuth authentication.
"""

import datetime
import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gateco.database.enums import UserRole
from gateco.database.models.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from gateco.database.models.oauth_account import OAuthAccount
    from gateco.database.models.organization import Organization
    from gateco.database.models.session import UserSession


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """User model representing a member of an organization.

    Attributes:
        id: UUID primary key
        organization_id: FK to parent organization
        email: User email (unique per organization)
        password_hash: Hashed password (nullable for OAuth-only users)
        name: Display name
        role: User role within organization
        avatar_url: URL to avatar image
        email_verified_at: When email was verified
        last_login_at: Last login timestamp
        deleted_at: Soft delete timestamp
        created_at: Record creation timestamp
        updated_at: Last modification timestamp

    Constraints:
        - uq_users_org_email: Email must be unique within an organization
    """

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "email",
            name="uq_users_org_email",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=True, name="user_role"),
        nullable=False,
        default=UserRole.developer,
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    email_verified_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_login_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="users",
    )
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    oauth_accounts: Mapped[List["OAuthAccount"]] = relationship(
        "OAuthAccount",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email!r}, role={self.role.value})>"

    @property
    def is_owner(self) -> bool:
        """Check if user is organization admin (top role)."""
        return self.role == UserRole.org_admin

    @property
    def is_admin(self) -> bool:
        """Check if user has admin-level access."""
        return self.role in (UserRole.org_admin, UserRole.security_admin)

    @property
    def has_password(self) -> bool:
        """Check if user has a password set (vs OAuth-only)."""
        return self.password_hash is not None

    @property
    def is_email_verified(self) -> bool:
        """Check if email has been verified."""
        return self.email_verified_at is not None

    def update_last_login(self) -> None:
        """Update last login timestamp to now."""
        self.last_login_at = datetime.datetime.now(datetime.timezone.utc)

    def verify_email(self) -> None:
        """Mark email as verified."""
        self.email_verified_at = datetime.datetime.now(datetime.timezone.utc)


__all__ = ["User"]
