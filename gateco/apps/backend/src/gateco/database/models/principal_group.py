"""PrincipalGroup model — groups synced from IdPs."""

import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from gateco.database.models.base import (
    Base,
    OrganizationScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class PrincipalGroup(Base, UUIDPrimaryKeyMixin, OrganizationScopedMixin, TimestampMixin):
    """A group synced from an identity provider."""

    __tablename__ = "principal_groups"

    identity_provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<PrincipalGroup(id={self.id}, name={self.name!r})>"


__all__ = ["PrincipalGroup"]
