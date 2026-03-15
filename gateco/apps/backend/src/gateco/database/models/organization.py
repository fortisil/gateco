"""Organization model.

Organizations are the top-level tenant container in Gateco.
All resources, users, and billing belong to an organization.
"""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gateco.database.enums import PlanTier
from gateco.database.models.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from gateco.database.models.user import User


class Organization(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Organization model representing a tenant in the system.

    Attributes:
        id: UUID primary key
        name: Organization display name
        slug: URL-friendly unique identifier
        plan: Current subscription plan tier
        stripe_customer_id: Stripe customer ID for billing
        deleted_at: Soft delete timestamp
        created_at: Record creation timestamp
        updated_at: Last modification timestamp
    """

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    plan: Mapped[PlanTier] = mapped_column(
        Enum(PlanTier, native_enum=True, name="plan_tier"),
        nullable=False,
        default=PlanTier.free,
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, slug={self.slug!r}, plan={self.plan.value})>"

    @property
    def is_free_tier(self) -> bool:
        """Check if organization is on free plan."""
        return self.plan == PlanTier.free

    @property
    def is_paid_tier(self) -> bool:
        """Check if organization is on a paid plan."""
        return self.plan in (PlanTier.pro, PlanTier.enterprise)


__all__ = ["Organization"]
