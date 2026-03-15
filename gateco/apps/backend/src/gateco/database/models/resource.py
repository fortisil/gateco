"""GatedResource model.

Represents content that can be access-controlled (links, files, videos).
Resources belong to organizations and have configurable access rules.
"""

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gateco.database.enums import Classification, EncryptionMode, ResourceType, Sensitivity
from gateco.database.models.base import (
    Base,
    OrganizationScopedMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from gateco.database.models.access_rule import AccessRule
    from gateco.database.models.invite import Invite
    from gateco.database.models.organization import Organization
    from gateco.database.models.user import User


class GatedResource(
    Base,
    UUIDPrimaryKeyMixin,
    OrganizationScopedMixin,
    TimestampMixin,
    SoftDeleteMixin,
):
    """Gated resource model representing access-controlled content.

    Attributes:
        id: UUID primary key
        organization_id: FK to owning organization
        type: Resource type (link, file, video)
        title: Resource title
        description: Optional description
        content_url: URL to the gated content
        thumbnail_url: Optional thumbnail image URL
        created_by: FK to user who created the resource
        view_count: Total views
        unique_viewers: Number of unique viewers
        revenue_cents: Total revenue in cents
        deleted_at: Soft delete timestamp
        created_at: Record creation timestamp
        updated_at: Last modification timestamp
    """

    __tablename__ = "gated_resources"
    __table_args__ = (
        Index("ix_gated_resources_org_type", "organization_id", "type"),
        Index("ix_gated_resources_org_deleted", "organization_id", "deleted_at"),
    )

    type: Mapped[ResourceType] = mapped_column(
        Enum(ResourceType, native_enum=True, name="resource_type"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    content_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )
    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    view_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    unique_viewers: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    revenue_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Permission-layer fields (M3)
    classification: Mapped[Optional[Classification]] = mapped_column(
        Enum(Classification, native_enum=True, name="classification"),
        nullable=True,
    )
    sensitivity: Mapped[Optional[Sensitivity]] = mapped_column(
        Enum(Sensitivity, native_enum=True, name="sensitivity"),
        nullable=True,
    )
    domain: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    labels: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    encryption_mode: Mapped[Optional[EncryptionMode]] = mapped_column(
        Enum(EncryptionMode, native_enum=True, name="encryption_mode"),
        nullable=True,
    )
    source_connector_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("connectors.id", ondelete="SET NULL"),
        nullable=True,
    )
    external_resource_key: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
    )
    owner_principal: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("principals.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        backref="resources",
    )
    creator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by],
    )
    access_rule: Mapped[Optional["AccessRule"]] = relationship(
        "AccessRule",
        back_populates="resource",
        uselist=False,
        cascade="all, delete-orphan",
    )
    invites: Mapped[List["Invite"]] = relationship(
        "Invite",
        back_populates="resource",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<GatedResource(id={self.id}, type={self.type.value}, "
            f"title={self.title!r})>"
        )

    @property
    def is_link(self) -> bool:
        """Check if resource is a link type."""
        return self.type == ResourceType.link

    @property
    def is_file(self) -> bool:
        """Check if resource is a file type."""
        return self.type == ResourceType.file

    @property
    def is_video(self) -> bool:
        """Check if resource is a video type."""
        return self.type == ResourceType.video

    @property
    def revenue_dollars(self) -> float:
        """Get revenue in dollars."""
        return self.revenue_cents / 100

    def increment_views(self, is_unique: bool = False) -> None:
        """Increment view counters.

        Args:
            is_unique: Whether this is a unique viewer
        """
        self.view_count += 1
        if is_unique:
            self.unique_viewers += 1

    def add_revenue(self, amount_cents: int) -> None:
        """Add revenue to the resource.

        Args:
            amount_cents: Amount in cents to add
        """
        self.revenue_cents += amount_cents


__all__ = ["GatedResource"]
