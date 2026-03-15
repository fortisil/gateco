"""Audit event emitter — writes to audit_events table.

Never raises on failure; logs a warning instead so it doesn't break the caller.
"""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.enums import AuditEventType
from gateco.database.models.audit_event import AuditEvent

logger = logging.getLogger(__name__)


async def emit_event(
    session: AsyncSession,
    org_id: UUID,
    event_type: AuditEventType,
    actor_id: UUID | None = None,
    actor_name: str = "",
    details: str = "",
    ip_address: str | None = None,
    principal_id: UUID | None = None,
    resource_ids: list[UUID] | None = None,
) -> None:
    """Persist an audit event to DB. Logs warning on failure (never raises)."""
    try:
        event = AuditEvent(
            organization_id=org_id,
            event_type=event_type,
            actor_id=actor_id,
            actor_name=actor_name,
            details=details,
            ip_address=ip_address,
            principal_id=principal_id,
            resource_ids=resource_ids,
        )
        session.add(event)
        await session.flush()
    except Exception:
        logger.warning("Failed to emit audit event %s", event_type.value, exc_info=True)
