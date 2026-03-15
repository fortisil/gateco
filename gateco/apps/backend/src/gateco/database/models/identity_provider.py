"""IdentityProvider model — external identity sources."""

import datetime
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from gateco.database.enums import IdentityProviderStatus, IdentityProviderType
from gateco.database.models.base import (
    Base,
    OrganizationScopedMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class IdentityProvider(
    Base, UUIDPrimaryKeyMixin, OrganizationScopedMixin, TimestampMixin, SoftDeleteMixin
):
    """External identity provider connection."""

    __tablename__ = "identity_providers"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[IdentityProviderType] = mapped_column(
        Enum(IdentityProviderType, native_enum=True, name="identity_provider_type"),
        nullable=False,
    )
    status: Mapped[IdentityProviderStatus] = mapped_column(
        Enum(IdentityProviderStatus, native_enum=True, name="identity_provider_status"),
        nullable=False,
        default=IdentityProviderStatus.disconnected,
    )
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    sync_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    principal_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    group_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_sync: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<IdentityProvider(id={self.id}, name={self.name!r}, type={self.type.value})>"


__all__ = ["IdentityProvider"]
