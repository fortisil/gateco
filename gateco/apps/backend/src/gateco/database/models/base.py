"""Base classes and mixins for SQLAlchemy models.

Provides reusable components for all database models:
- Base: DeclarativeBase with UUID type mapping
- TimestampMixin: created_at/updated_at with timezone
- SoftDeleteMixin: deleted_at column with is_deleted property
- UUIDPrimaryKeyMixin: UUID primary key with uuid4 default
- OrganizationScopedMixin: Indexed FK to organizations
"""

import datetime
import uuid
from typing import Any

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all models.

    Configures UUID type mapping for PostgreSQL compatibility.
    """

    type_annotation_map = {
        uuid.UUID: UUID(as_uuid=True),
    }


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns with timezone-aware UTC.

    Usage:
        class MyModel(Base, TimestampMixin):
            __tablename__ = "my_table"
            ...
    """

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin for soft delete support with indexed deleted_at column.

    Provides:
    - deleted_at: TIMESTAMPTZ column (indexed for filtering)
    - is_deleted: Hybrid property for checking deletion status
    - soft_delete(): Method to mark as deleted
    - restore(): Method to restore deleted record
    """

    deleted_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    @hybrid_property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted."""
        return self.deleted_at is not None

    @is_deleted.expression
    def is_deleted(cls) -> Any:  # noqa: N805
        """SQL expression for is_deleted."""
        return cls.deleted_at.isnot(None)

    def soft_delete(self) -> None:
        """Mark record as soft-deleted."""
        self.deleted_at = datetime.datetime.now(datetime.timezone.utc)

    def restore(self) -> None:
        """Restore soft-deleted record."""
        self.deleted_at = None


class UUIDPrimaryKeyMixin:
    """Mixin that adds a UUID primary key with uuid4 default.

    Provides:
    - id: UUID primary key, auto-generated on insert
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class OrganizationScopedMixin:
    """Mixin for models that belong to an organization with indexed FK.

    Provides:
    - organization_id: UUID FK to organizations table with CASCADE delete
    - Index on organization_id for efficient tenant filtering

    Usage:
        class Resource(Base, UUIDPrimaryKeyMixin, OrganizationScopedMixin, TimestampMixin):
            __tablename__ = "resources"
            ...
    """

    @declared_attr
    def organization_id(cls) -> Mapped[uuid.UUID]:  # noqa: N805
        return mapped_column(
            UUID(as_uuid=True),
            ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )


__all__ = [
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    "UUIDPrimaryKeyMixin",
    "OrganizationScopedMixin",
]
