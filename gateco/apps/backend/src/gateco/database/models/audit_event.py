"""AuditEvent model — append-only audit trail.

No soft delete, no updates. Ordered by timestamp DESC.
"""

import datetime
import uuid
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from gateco.database.enums import AuditEventType
from gateco.database.models.base import Base, OrganizationScopedMixin, UUIDPrimaryKeyMixin


class AuditEvent(Base, UUIDPrimaryKeyMixin, OrganizationScopedMixin):
    """Immutable audit event record."""

    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_org_type", "organization_id", "event_type"),
        Index("ix_audit_events_org_ts", "organization_id", "timestamp"),
    )

    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType, native_enum=True, name="audit_event_type"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    principal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    resource_ids: Mapped[Optional[list[uuid.UUID]]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=True
    )
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<AuditEvent(id={self.id}, type={self.event_type.value})>"


__all__ = ["AuditEvent"]
