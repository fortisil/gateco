"""PolicyRule model — individual conditions within a policy."""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gateco.database.enums import PolicyEffect
from gateco.database.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PolicyRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A single rule within a policy."""

    __tablename__ = "policy_rules"

    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    effect: Mapped[PolicyEffect] = mapped_column(
        Enum(PolicyEffect, native_enum=True, name="policy_effect"), nullable=False
    )
    conditions: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONB, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    policy: Mapped["Policy"] = relationship("Policy", back_populates="rules")

    def __repr__(self) -> str:
        return f"<PolicyRule(id={self.id}, effect={self.effect.value})>"


# Avoid circular import: use string for forward ref
from gateco.database.models.policy import Policy  # noqa: E402, F811

__all__ = ["PolicyRule"]
