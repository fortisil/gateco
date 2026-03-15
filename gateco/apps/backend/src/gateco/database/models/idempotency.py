"""IdempotencyRecord model — caches ingestion responses for idempotency key replay."""

import datetime
import hashlib
import json
import uuid

from sqlalchemy import DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from gateco.database.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class IdempotencyRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cached response for an idempotency key, scoped to an organization."""

    __tablename__ = "idempotency_records"

    key: Mapped[str] = mapped_column(String(255), nullable=False)
    org_id: Mapped[str] = mapped_column(String(36), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(100), nullable=False)
    response_body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("key", "org_id", name="uq_idempotency_key_org"),
        Index("ix_idempotency_expires", "expires_at"),
    )

    @staticmethod
    def compute_fingerprint(payload: dict) -> str:
        """SHA-256 hash of normalized request payload (excluding idempotency_key)."""
        clean = {k: v for k, v in payload.items() if k != "idempotency_key"}
        canonical = json.dumps(clean, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()


__all__ = ["IdempotencyRecord"]
