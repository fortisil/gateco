"""Pipeline CRUD + run service."""

import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.enums import AuditEventType, PipelineRunStatus, PipelineStatus
from gateco.database.models.connector import Connector
from gateco.database.models.pipeline import Pipeline
from gateco.database.models.pipeline_run import PipelineRun
from gateco.exceptions import NotFoundError, ValidationError
from gateco.services import audit_service


def _serialize(p: Pipeline, connector_names: dict | None = None) -> dict:
    return {
        "id": str(p.id),
        "name": p.name,
        "source_connector_id": str(p.source_connector_id),
        "source_connector_name": (
            connector_names.get(p.source_connector_id, "") if connector_names else ""
        ),
        "envelope_config": p.envelope_config or {
            "encrypt": False, "classify": False,
            "default_classification": "internal", "default_sensitivity": "medium",
            "label_extraction": False,
        },
        "status": p.status.value,
        "schedule": p.schedule,
        "last_run": p.last_run.isoformat() if p.last_run else None,
        "records_processed": p.records_processed,
        "error_count": p.error_count,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


def _serialize_run(r: PipelineRun) -> dict:
    return {
        "id": str(r.id),
        "pipeline_id": str(r.pipeline_id),
        "status": r.status.value,
        "records_processed": r.records_processed,
        "errors": r.errors,
        "started_at": r.started_at.isoformat(),
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        "duration_ms": r.duration_ms,
    }


async def list_pipelines(session: AsyncSession, org_id: UUID) -> list[dict]:
    result = await session.execute(
        select(Pipeline)
        .where(Pipeline.organization_id == org_id, Pipeline.deleted_at.is_(None))
        .order_by(Pipeline.created_at.desc())
    )
    pipelines = result.scalars().all()

    # Resolve connector names
    conn_ids = {p.source_connector_id for p in pipelines if p.source_connector_id}
    connector_names = {}
    if conn_ids:
        conn_result = await session.execute(
            select(Connector.id, Connector.name).where(Connector.id.in_(conn_ids))
        )
        connector_names = {row[0]: row[1] for row in conn_result.all()}

    return [_serialize(p, connector_names) for p in pipelines]


async def get_pipeline(session: AsyncSession, org_id: UUID, pipeline_id: UUID) -> dict:
    p = await _load(session, org_id, pipeline_id)
    connector_names = await _resolve_connector_name(session, p.source_connector_id)
    return _serialize(p, connector_names)


async def create_pipeline(
    session: AsyncSession, org_id: UUID, name: str,
    source_connector_id: str, envelope_config: dict | None, schedule: str,
) -> dict:
    # Validate connector exists in same org
    conn_id = UUID(source_connector_id)
    result = await session.execute(
        select(Connector).where(
            Connector.id == conn_id,
            Connector.organization_id == org_id,
            Connector.deleted_at.is_(None),
        )
    )
    if not result.scalar_one_or_none():
        raise ValidationError(detail="Source connector not found in this organization")

    p = Pipeline(
        organization_id=org_id,
        name=name.strip(),
        source_connector_id=conn_id,
        envelope_config=envelope_config,
        status=PipelineStatus.active,
        schedule=schedule or "manual",
    )
    session.add(p)
    await session.flush()
    connector_names = await _resolve_connector_name(session, p.source_connector_id)
    return _serialize(p, connector_names)


async def update_pipeline(
    session: AsyncSession, org_id: UUID, pipeline_id: UUID, data: dict,
) -> dict:
    p = await _load(session, org_id, pipeline_id)
    if "name" in data and data["name"] is not None:
        p.name = data["name"].strip()
    if "envelope_config" in data:
        p.envelope_config = data["envelope_config"]
    if "status" in data and data["status"] is not None:
        try:
            p.status = PipelineStatus(data["status"])
        except ValueError:
            raise ValidationError(detail=f"Invalid pipeline status: {data['status']}")
    if "schedule" in data and data["schedule"] is not None:
        p.schedule = data["schedule"]
    await session.flush()
    connector_names = await _resolve_connector_name(session, p.source_connector_id)
    return _serialize(p, connector_names)


async def run_pipeline(
    session: AsyncSession, org_id: UUID, pipeline_id: UUID,
    actor_id: UUID | None = None, actor_name: str = "",
) -> dict:
    """Stub run: creates a PipelineRun and marks it completed."""
    p = await _load(session, org_id, pipeline_id)
    now = datetime.datetime.now(datetime.timezone.utc)

    run = PipelineRun(
        pipeline_id=p.id,
        status=PipelineRunStatus.running,
        started_at=now,
    )
    session.add(run)
    await session.flush()

    try:
        # Stub: simulate processing
        run.status = PipelineRunStatus.completed
        run.records_processed = 150
        run.errors = 0
        run.completed_at = datetime.datetime.now(datetime.timezone.utc)
        run.duration_ms = 1200

        p.last_run = run.completed_at
        p.records_processed += run.records_processed
    except Exception as e:
        run.status = PipelineRunStatus.failed
        run.errors = 1
        run.completed_at = datetime.datetime.now(datetime.timezone.utc)
        p.error_count += 1
        p.status = PipelineStatus.error

        await audit_service.emit_event(
            session=session,
            org_id=org_id,
            event_type=AuditEventType.pipeline_error,
            actor_id=actor_id,
            actor_name=actor_name,
            details=f"Pipeline run failed: {p.name} — {e}",
        )

    await session.flush()
    return _serialize_run(run)


async def list_runs(session: AsyncSession, org_id: UUID, pipeline_id: UUID) -> list[dict]:
    p = await _load(session, org_id, pipeline_id)
    result = await session.execute(
        select(PipelineRun)
        .where(PipelineRun.pipeline_id == p.id)
        .order_by(PipelineRun.started_at.desc())
    )
    return [_serialize_run(r) for r in result.scalars().all()]


async def _resolve_connector_name(session: AsyncSession, connector_id) -> dict:
    if not connector_id:
        return {}
    result = await session.execute(
        select(Connector.id, Connector.name).where(Connector.id == connector_id)
    )
    row = result.first()
    return {row[0]: row[1]} if row else {}


async def _load(session: AsyncSession, org_id: UUID, pipeline_id: UUID) -> Pipeline:
    result = await session.execute(
        select(Pipeline).where(
            Pipeline.id == pipeline_id,
            Pipeline.organization_id == org_id,
            Pipeline.deleted_at.is_(None),
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise NotFoundError(detail="Pipeline not found")
    return p
