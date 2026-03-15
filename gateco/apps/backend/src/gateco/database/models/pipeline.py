"""Pipeline model — data ingestion pipelines."""

import datetime
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from gateco.database.enums import PipelineStatus
from gateco.database.models.base import (
    Base,
    OrganizationScopedMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class Pipeline(Base, UUIDPrimaryKeyMixin, OrganizationScopedMixin, TimestampMixin, SoftDeleteMixin):
    """Data ingestion pipeline."""

    __tablename__ = "pipelines"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_connector_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("connectors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    envelope_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus, native_enum=True, name="pipeline_status"),
        nullable=False,
        default=PipelineStatus.active,
    )
    schedule: Mapped[str] = mapped_column(String(100), nullable=False, default="manual")
    last_run: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    records_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<Pipeline(id={self.id}, name={self.name!r}, status={self.status.value})>"


__all__ = ["Pipeline"]
