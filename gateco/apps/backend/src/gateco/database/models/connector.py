"""Connector model — vector database connections."""

import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from gateco.database.enums import ConnectorStatus, ConnectorType
from gateco.database.models.base import (
    Base,
    OrganizationScopedMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class Connector(
    Base, UUIDPrimaryKeyMixin, OrganizationScopedMixin, TimestampMixin, SoftDeleteMixin,
):
    """Vector database connector."""

    __tablename__ = "connectors"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[ConnectorType] = mapped_column(
        Enum(ConnectorType, native_enum=True, name="connector_type"), nullable=False
    )
    status: Mapped[ConnectorStatus] = mapped_column(
        Enum(ConnectorStatus, native_enum=True, name="connector_status"),
        nullable=False,
        default=ConnectorStatus.disconnected,
    )
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    last_sync: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    index_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_tested_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_test_success: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    last_test_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    diagnostics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    server_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    search_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    ingestion_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    metadata_resolution_mode: Mapped[Optional[str]] = mapped_column(
        String(20), default="sidecar", nullable=True
    )

    def __repr__(self) -> str:
        return f"<Connector(id={self.id}, name={self.name!r}, type={self.type.value})>"


__all__ = ["Connector"]
