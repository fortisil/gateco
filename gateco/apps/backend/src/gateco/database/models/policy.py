"""Policy model — access control policies with versioning (D4)."""

import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gateco.database.enums import PolicyEffect, PolicyStatus, PolicyType
from gateco.database.models.base import (
    Base,
    OrganizationScopedMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from gateco.database.models.policy_rule import PolicyRule


class Policy(Base, UUIDPrimaryKeyMixin, OrganizationScopedMixin, TimestampMixin, SoftDeleteMixin):
    """Access control policy."""

    __tablename__ = "policies"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[PolicyType] = mapped_column(
        Enum(PolicyType, native_enum=True, name="policy_type"), nullable=False
    )
    status: Mapped[PolicyStatus] = mapped_column(
        Enum(PolicyStatus, native_enum=True, name="policy_status"),
        nullable=False,
        default=PolicyStatus.draft,
    )
    effect: Mapped[PolicyEffect] = mapped_column(
        Enum(PolicyEffect, native_enum=True, name="policy_effect"), nullable=False
    )
    resource_selectors: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB, nullable=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    rules: Mapped[List["PolicyRule"]] = relationship(
        "PolicyRule", back_populates="policy", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Policy(id={self.id}, name={self.name!r}, status={self.status.value})>"


__all__ = ["Policy"]
