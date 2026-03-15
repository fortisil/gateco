"""Principal model — identity subjects synced from IdPs."""

import datetime
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from gateco.database.enums import PrincipalStatus
from gateco.database.models.base import (
    Base,
    OrganizationScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class Principal(Base, UUIDPrimaryKeyMixin, OrganizationScopedMixin, TimestampMixin):
    """An identity principal synced from an identity provider."""

    __tablename__ = "principals"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "identity_provider_id", "external_id",
            name="uq_principal_org_idp_ext",
        ),
    )

    identity_provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    groups: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    roles: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    attributes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    status: Mapped[PrincipalStatus] = mapped_column(
        Enum(PrincipalStatus, native_enum=True, name="principal_status"),
        nullable=False,
        default=PrincipalStatus.active,
    )
    last_seen: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Principal(id={self.id}, display_name={self.display_name!r})>"


__all__ = ["Principal"]
