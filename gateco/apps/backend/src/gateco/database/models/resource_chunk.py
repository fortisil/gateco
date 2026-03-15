"""ResourceChunk model — chunks of a gated resource."""

import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from gateco.database.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ResourceChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A chunk of content belonging to a GatedResource."""

    __tablename__ = "resource_chunks"

    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("gated_resources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    preview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    encrypted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    vector_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_connector_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("connectors.id", ondelete="SET NULL"),
        nullable=True,
    )
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
    )

    def __repr__(self) -> str:
        return f"<ResourceChunk(id={self.id}, resource_id={self.resource_id}, index={self.index})>"


__all__ = ["ResourceChunk"]
