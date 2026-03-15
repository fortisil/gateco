"""UsageLog model.

Tracks resource usage per billing period for organizations.
Used for metered billing and overage calculations.
"""

import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gateco.database.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from gateco.database.models.organization import Organization


class UsageLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Usage log model for tracking resource consumption.

    Attributes:
        id: UUID primary key
        organization_id: FK to organization
        period_start: Start of billing period
        period_end: End of billing period
        secured_retrievals: Number of secured resource retrievals
        resources_created: Number of resources created
        storage_bytes: Storage used in bytes
        overage_cents: Overage charges in cents
        created_at: Record creation timestamp
        updated_at: Last modification timestamp

    Constraints:
        - uq_usage_org_period: One record per organization per period
    """

    __tablename__ = "usage_logs"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "period_start",
            name="uq_usage_org_period",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_start: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    period_end: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    secured_retrievals: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    resources_created: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    storage_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )
    overage_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        backref="usage_logs",
    )

    def __repr__(self) -> str:
        return (
            f"<UsageLog(id={self.id}, org={self.organization_id}, "
            f"retrievals={self.secured_retrievals})>"
        )

    @property
    def storage_mb(self) -> float:
        """Get storage in megabytes."""
        return self.storage_bytes / (1024 * 1024)

    @property
    def storage_gb(self) -> float:
        """Get storage in gigabytes."""
        return self.storage_bytes / (1024 * 1024 * 1024)

    @property
    def overage_dollars(self) -> float:
        """Get overage charges in dollars."""
        return self.overage_cents / 100

    @property
    def has_overage(self) -> bool:
        """Check if there are overage charges."""
        return self.overage_cents > 0

    def increment_retrievals(self, count: int = 1) -> None:
        """Increment secured retrievals count.

        Args:
            count: Number of retrievals to add
        """
        self.secured_retrievals += count

    def increment_resources(self, count: int = 1) -> None:
        """Increment resources created count.

        Args:
            count: Number of resources to add
        """
        self.resources_created += count

    def add_storage(self, bytes_used: int) -> None:
        """Add storage usage.

        Args:
            bytes_used: Number of bytes to add
        """
        self.storage_bytes += bytes_used

    def add_overage(self, cents: int) -> None:
        """Add overage charges.

        Args:
            cents: Overage amount in cents
        """
        self.overage_cents += cents


__all__ = ["UsageLog"]
