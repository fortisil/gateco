"""Identity Provider CRUD + sync service."""

import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.enums import (
    AuditEventType,
    IdentityProviderStatus,
    IdentityProviderType,
    PrincipalStatus,
)
from gateco.database.models.identity_provider import IdentityProvider
from gateco.database.models.principal import Principal
from gateco.database.models.principal_group import PrincipalGroup
from gateco.exceptions import NotFoundError, ValidationError
from gateco.schemas.identity_providers import IDP_SECRET_FIELDS
from gateco.services import audit_service
from gateco.utils.crypto import encrypt_config_secrets, mask_config_secrets
from gateco.utils.patch import apply_patch


def _secret_fields(idp_type: str) -> list[str]:
    return IDP_SECRET_FIELDS.get(idp_type, [])


def _serialize(idp: IdentityProvider) -> dict:
    config = mask_config_secrets(idp.config or {}, _secret_fields(idp.type.value))
    return {
        "id": str(idp.id),
        "name": idp.name,
        "type": idp.type.value,
        "status": idp.status.value,
        "config": config,
        "sync_config": idp.sync_config,
        "principal_count": idp.principal_count,
        "group_count": idp.group_count,
        "last_sync": idp.last_sync.isoformat() if idp.last_sync else None,
        "error_message": idp.error_message,
        "created_at": idp.created_at.isoformat(),
        "updated_at": idp.updated_at.isoformat(),
    }


async def list_identity_providers(session: AsyncSession, org_id: UUID) -> list[dict]:
    result = await session.execute(
        select(IdentityProvider)
        .where(IdentityProvider.organization_id == org_id, IdentityProvider.deleted_at.is_(None))
        .order_by(IdentityProvider.created_at.desc())
    )
    return [_serialize(i) for i in result.scalars().all()]


async def get_identity_provider(session: AsyncSession, org_id: UUID, idp_id: UUID) -> dict:
    return _serialize(await _load(session, org_id, idp_id))


async def create_identity_provider(
    session: AsyncSession, org_id: UUID, name: str, type_: str,
    config: dict, sync_config: dict | None,
) -> dict:
    try:
        it = IdentityProviderType(type_)
    except ValueError:
        raise ValidationError(detail=f"Invalid identity provider type: {type_}")
    encrypted = encrypt_config_secrets(config, _secret_fields(type_))
    idp = IdentityProvider(
        organization_id=org_id,
        name=name.strip(),
        type=it,
        status=IdentityProviderStatus.disconnected,
        config=encrypted,
        sync_config=sync_config,
    )
    session.add(idp)
    await session.flush()
    return _serialize(idp)


async def update_identity_provider(
    session: AsyncSession, org_id: UUID, idp_id: UUID,
    name: str | None, config: dict | None, sync_config: dict | None,
) -> dict:
    idp = await _load(session, org_id, idp_id)
    if name is not None:
        idp.name = name.strip()
    if config is not None:
        sf = _secret_fields(idp.type.value)
        merged = apply_patch(idp.config or {}, config, secret_fields=sf)
        idp.config = encrypt_config_secrets(merged, sf)
    if sync_config is not None:
        idp.sync_config = sync_config
    await session.flush()
    await session.refresh(idp)
    return _serialize(idp)


async def delete_identity_provider(session: AsyncSession, org_id: UUID, idp_id: UUID) -> None:
    idp = await _load(session, org_id, idp_id)
    idp.soft_delete()


async def trigger_sync(
    session: AsyncSession, org_id: UUID, idp_id: UUID,
    actor_id: UUID | None = None, actor_name: str = "",
) -> dict:
    """Stub sync: creates mock principals + groups, updates counts."""
    idp = await _load(session, org_id, idp_id)
    idp.status = IdentityProviderStatus.syncing
    await session.flush()

    try:
        # Mock: create 5 principals and 2 groups
        now = datetime.datetime.now(datetime.timezone.utc)
        mock_names = ["Alice", "Bob", "Carol", "Dave", "Eve"]
        for i, name in enumerate(mock_names):
            ext_id = f"ext-{idp_id}-{i}"
            existing = await session.execute(
                select(Principal).where(
                    Principal.organization_id == org_id,
                    Principal.identity_provider_id == idp.id,
                    Principal.external_id == ext_id,
                )
            )
            if existing.scalar_one_or_none():
                continue
            session.add(Principal(
                organization_id=org_id,
                identity_provider_id=idp.id,
                external_id=ext_id,
                display_name=name,
                email=f"{name.lower()}@example.com",
                groups=["engineering"] if i < 3 else ["marketing"],
                roles=["viewer"],
                attributes={"department": "engineering" if i < 3 else "marketing"},
                status=PrincipalStatus.active,
                last_seen=now,
            ))

        for g_name, count in [("engineering", 3), ("marketing", 2)]:
            ext_id = f"grp-{idp_id}-{g_name}"
            existing = await session.execute(
                select(PrincipalGroup).where(
                    PrincipalGroup.organization_id == org_id,
                    PrincipalGroup.identity_provider_id == idp.id,
                    PrincipalGroup.external_id == ext_id,
                )
            )
            if existing.scalar_one_or_none():
                continue
            session.add(PrincipalGroup(
                organization_id=org_id,
                identity_provider_id=idp.id,
                external_id=ext_id,
                name=g_name,
                member_count=count,
            ))

        idp.principal_count = 5
        idp.group_count = 2
        idp.last_sync = now
        idp.status = IdentityProviderStatus.connected
        idp.error_message = None

        await audit_service.emit_event(
            session=session,
            org_id=org_id,
            event_type=AuditEventType.idp_synced,
            actor_id=actor_id,
            actor_name=actor_name,
            details=f"IDP sync completed: {idp.name} (5 principals, 2 groups)",
        )
    except Exception as e:
        idp.status = IdentityProviderStatus.error
        idp.error_message = str(e)
        await audit_service.emit_event(
            session=session,
            org_id=org_id,
            event_type=AuditEventType.idp_sync_failed,
            actor_id=actor_id,
            actor_name=actor_name,
            details=f"IDP sync failed: {idp.name} — {e}",
        )

    await session.flush()
    await session.refresh(idp)
    return _serialize(idp)


async def _load(session: AsyncSession, org_id: UUID, idp_id: UUID) -> IdentityProvider:
    result = await session.execute(
        select(IdentityProvider).where(
            IdentityProvider.id == idp_id,
            IdentityProvider.organization_id == org_id,
            IdentityProvider.deleted_at.is_(None),
        )
    )
    idp = result.scalar_one_or_none()
    if not idp:
        raise NotFoundError(detail="Identity provider not found")
    return idp
