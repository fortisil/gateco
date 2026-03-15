"""SecuredRetrieval model — the core product record."""

import datetime
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from gateco.database.enums import RetrievalOutcome
from gateco.database.models.base import Base, OrganizationScopedMixin, UUIDPrimaryKeyMixin


class SecuredRetrieval(Base, UUIDPrimaryKeyMixin, OrganizationScopedMixin):
    """A single secured retrieval execution — the Gateco core product record."""

    __tablename__ = "secured_retrievals"
    __table_args__ = (
        Index("ix_secured_retrievals_org_ts", "organization_id", "timestamp"),
        Index("ix_secured_retrievals_org_outcome", "organization_id", "outcome"),
    )

    query: Mapped[str] = mapped_column(Text, nullable=False)
    principal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("principals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    principal_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    connector_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("connectors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    connector_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    matched_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    allowed_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    denied_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    outcome: Mapped[RetrievalOutcome] = mapped_column(
        Enum(RetrievalOutcome, native_enum=True, name="retrieval_outcome"),
        nullable=False,
    )
    denial_reasons: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    policy_trace: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONB, nullable=True)
    resource_ids: Mapped[Optional[List[uuid.UUID]]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=True
    )
    chunk_ids: Mapped[Optional[List[uuid.UUID]]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=True
    )
    unresolved_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    connector_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<SecuredRetrieval(id={self.id}, outcome={self.outcome.value})>"


__all__ = ["SecuredRetrieval"]
