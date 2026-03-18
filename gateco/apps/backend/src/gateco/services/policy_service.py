"""Policy CRUD service with D4 lifecycle enforcement."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from gateco.database.enums import PolicyEffect, PolicyStatus, PolicyType
from gateco.database.models.policy import Policy
from gateco.database.models.policy_rule import PolicyRule
from gateco.exceptions import NotFoundError, ValidationError


def _serialize_rule(r: PolicyRule) -> dict:
    return {
        "id": str(r.id),
        "description": r.description,
        "effect": r.effect.value,
        "conditions": r.conditions,
        "priority": r.priority,
    }


def _serialize_selectors(selectors: list | None) -> list:
    if not selectors:
        return []
    return list(selectors)


def _serialize(p: Policy) -> dict:
    return {
        "id": str(p.id),
        "name": p.name,
        "description": p.description,
        "type": p.type.value,
        "status": p.status.value,
        "effect": p.effect.value,
        "resource_selectors": _serialize_selectors(p.resource_selectors),
        "version": p.version,
        "rules": [_serialize_rule(r) for r in (p.rules or [])],
        "created_by": str(p.created_by) if p.created_by else None,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


async def list_policies(session: AsyncSession, org_id: UUID) -> list[dict]:
    result = await session.execute(
        select(Policy)
        .options(selectinload(Policy.rules))
        .where(Policy.organization_id == org_id, Policy.deleted_at.is_(None))
        .order_by(Policy.created_at.desc())
    )
    return [_serialize(p) for p in result.scalars().all()]


async def get_policy(session: AsyncSession, org_id: UUID, policy_id: UUID) -> dict:
    return _serialize(await _load(session, org_id, policy_id))


async def create_policy(
    session: AsyncSession, org_id: UUID, data: dict, created_by: UUID | None = None,
) -> dict:
    try:
        pt = PolicyType(data["type"])
    except (ValueError, KeyError):
        raise ValidationError(detail=f"Invalid policy type: {data.get('type')}")
    try:
        pe = PolicyEffect(data["effect"])
    except (ValueError, KeyError):
        raise ValidationError(detail=f"Invalid policy effect: {data.get('effect')}")

    p = Policy(
        organization_id=org_id,
        name=data["name"].strip(),
        description=data.get("description"),
        type=pt,
        status=PolicyStatus.draft,
        effect=pe,
        resource_selectors=data.get("resource_selectors"),
        version=1,
        created_by=created_by,
    )
    session.add(p)
    await session.flush()

    for rule_data in data.get("rules", []):
        rule = PolicyRule(
            policy_id=p.id,
            description=rule_data.get("description"),
            effect=PolicyEffect(rule_data["effect"]),
            conditions=rule_data.get("conditions"),
            priority=rule_data.get("priority", 0),
        )
        session.add(rule)

    await session.flush()
    return await get_policy(session, org_id, p.id)


async def update_policy(
    session: AsyncSession, org_id: UUID, policy_id: UUID, data: dict,
) -> dict:
    p = await _load(session, org_id, policy_id)
    if p.status != PolicyStatus.draft:
        raise ValidationError(detail="Only draft policies can be edited (D4)")

    if data.get("name") is not None:
        p.name = data["name"].strip()
    if data.get("description") is not None:
        p.description = data["description"]
    if data.get("effect") is not None:
        p.effect = PolicyEffect(data["effect"])
    if data.get("resource_selectors") is not None:
        p.resource_selectors = data["resource_selectors"]

    if data.get("rules") is not None:
        # Replace all rules
        for old in p.rules:
            await session.delete(old)
        await session.flush()
        for rule_data in data["rules"]:
            rule = PolicyRule(
                policy_id=p.id,
                description=rule_data.get("description"),
                effect=PolicyEffect(rule_data["effect"]),
                conditions=rule_data.get("conditions"),
                priority=rule_data.get("priority", 0),
            )
            session.add(rule)

    p.version += 1
    await session.flush()
    return await get_policy(session, org_id, p.id)


async def activate_policy(session: AsyncSession, org_id: UUID, policy_id: UUID) -> dict:
    p = await _load(session, org_id, policy_id)
    if p.status not in (PolicyStatus.draft, PolicyStatus.archived):
        raise ValidationError(detail="Only draft or archived policies can be activated")
    if not p.rules:
        raise ValidationError(detail="Policy must have at least one rule to activate")
    p.status = PolicyStatus.active
    await session.flush()
    return await get_policy(session, org_id, p.id)


async def archive_policy(session: AsyncSession, org_id: UUID, policy_id: UUID) -> dict:
    p = await _load(session, org_id, policy_id)
    if p.status == PolicyStatus.archived:
        raise ValidationError(detail="Policy is already archived")
    p.status = PolicyStatus.archived
    await session.flush()
    return await get_policy(session, org_id, p.id)


async def delete_policy(session: AsyncSession, org_id: UUID, policy_id: UUID) -> None:
    p = await _load(session, org_id, policy_id)
    p.soft_delete()


async def _load(session: AsyncSession, org_id: UUID, policy_id: UUID) -> Policy:
    result = await session.execute(
        select(Policy)
        .options(selectinload(Policy.rules))
        .where(
            Policy.id == policy_id,
            Policy.organization_id == org_id,
            Policy.deleted_at.is_(None),
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise NotFoundError(detail="Policy not found")
    return p
