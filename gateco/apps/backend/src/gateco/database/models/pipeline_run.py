"""PipelineRun model — execution records for pipelines."""

import datetime
import uuid
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from gateco.database.enums import PipelineRunStatus
from gateco.database.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PipelineRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A single execution of a pipeline."""

    __tablename__ = "pipeline_runs"

    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pipelines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[PipelineRunStatus] = mapped_column(
        Enum(PipelineRunStatus, native_enum=True, name="pipeline_run_status"),
        nullable=False,
    )
    records_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<PipelineRun(id={self.id}, status={self.status.value})>"


__all__ = ["PipelineRun"]
