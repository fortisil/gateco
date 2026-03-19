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
from gateco.services.idp_adapters import sync_from_provider
from gateco.utils.crypto import decrypt_config_secrets, encrypt_config_secrets, mask_config_secrets
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
    """Dispatch sync to the appropriate IDP adapter, upsert principals and groups, update counts."""
    idp = await _load(session, org_id, idp_id)
    idp.status = IdentityProviderStatus.syncing
    await session.flush()

    try:
        now = datetime.datetime.now(datetime.timezone.utc)

        # Decrypt stored secrets before passing config to the adapter
        decrypted = decrypt_config_secrets(idp.config or {}, _secret_fields(idp.type.value))

        # Dispatch to the real adapter (falls back to stub for fake/placeholder configs)
        result = await sync_from_provider(idp.type.value, decrypted)

        # Upsert principals
        for sp in result.principals:
            ext_id = f"{idp.id}-{sp.external_id}"
            existing = await session.execute(
                select(Principal).where(
                    Principal.organization_id == org_id,
                    Principal.identity_provider_id == idp.id,
                    Principal.external_id == ext_id,
                )
            )
            principal = existing.scalar_one_or_none()
            if principal:
                principal.display_name = sp.display_name
                principal.email = sp.email
                principal.groups = sp.groups
                principal.roles = sp.roles
                principal.attributes = sp.attributes
                principal.last_seen = now
            else:
                session.add(Principal(
                    organization_id=org_id,
                    identity_provider_id=idp.id,
                    external_id=ext_id,
                    display_name=sp.display_name,
                    email=sp.email,
                    groups=sp.groups,
                    roles=sp.roles,
                    attributes=sp.attributes,
                    status=PrincipalStatus.active,
                    last_seen=now,
                ))

        # Upsert groups
        for sg in result.groups:
            ext_id = f"{idp.id}-{sg.external_id}"
            existing = await session.execute(
                select(PrincipalGroup).where(
                    PrincipalGroup.organization_id == org_id,
                    PrincipalGroup.identity_provider_id == idp.id,
                    PrincipalGroup.external_id == ext_id,
                )
            )
            group = existing.scalar_one_or_none()
            if group:
                group.name = sg.name
                group.member_count = sg.member_count
            else:
                session.add(PrincipalGroup(
                    organization_id=org_id,
                    identity_provider_id=idp.id,
                    external_id=ext_id,
                    name=sg.name,
                    member_count=sg.member_count,
                ))

        principal_count = len(result.principals)
        group_count = len(result.groups)
        idp.principal_count = principal_count
        idp.group_count = group_count
        idp.last_sync = now
        idp.status = IdentityProviderStatus.connected
        idp.error_message = None

        await audit_service.emit_event(
            session=session,
            org_id=org_id,
            event_type=AuditEventType.idp_synced,
            actor_id=actor_id,
            actor_name=actor_name,
            details=f"IDP sync completed: {idp.name} ({principal_count} principals, {group_count} groups)",
        )
    except Exception as e:
        idp.status = IdentityProviderStatus.error
        # Sanitize error message to avoid leaking credentials or internal URLs
        err_type = type(e).__name__
        err_msg = str(e)[:200]  # Truncate to avoid exposing full request details
        idp.error_message = f"{err_type}: {err_msg}"
        await audit_service.emit_event(
            session=session,
            org_id=org_id,
            event_type=AuditEventType.idp_sync_failed,
            actor_id=actor_id,
            actor_name=actor_name,
            details=f"IDP sync failed: {idp.name} — {err_type}",
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
