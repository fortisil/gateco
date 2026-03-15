"""Secured retrieval service — the core Gateco product.

Combines connectors + resources + principals + policies + audit + billing.
Real vector search through connectors → multi-mode metadata resolution → deny-by-default.
"""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Literal
from uuid import UUID

import asyncpg
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from gateco.database.enums import AuditEventType, PolicyStatus, RetrievalOutcome
from gateco.database.models.connector import Connector
from gateco.database.models.policy import Policy
from gateco.database.models.principal import Principal
from gateco.database.models.resource import GatedResource
from gateco.database.models.resource_chunk import ResourceChunk
from gateco.database.models.secured_retrieval import SecuredRetrieval
from gateco.exceptions import EntitlementError, NotFoundError, ValidationError
from gateco.schemas.connectors import CONNECTOR_SECRET_FIELDS
from gateco.services import audit_service, usage_service
from gateco.services.connector_adapters import (
    VectorSearchResult,
    execute_vector_search,
)
from gateco.services.connector_testers import _build_pgvector_dsn
from gateco.services.policy_engine import evaluate_policies
from gateco.utils.crypto import decrypt_config_secrets

logger = logging.getLogger(__name__)

# Identifier validation for SQL view mode
_SQL_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$")

# Postgres-family connector types eligible for SQL view mode
POSTGRES_FAMILY_TYPES = {"pgvector", "supabase", "neon"}

# Allowed metadata field names for inline/sql_view mapping
ALLOWED_METADATA_FIELDS = {"classification", "sensitivity", "domain", "labels", "owner_principal"}


def _validate_sql_identifier(name: str) -> None:
    """Validate a SQL identifier (view name, column name) against injection."""
    if not _SQL_IDENTIFIER_RE.match(name):
        raise ValidationError(detail=f"Invalid SQL identifier: {name!r}")


@dataclass
class ResolvedPolicySubject:
    """Unified metadata subject for policy evaluation, regardless of resolution source."""

    vector_id: str
    resource_id: str | None = None
    chunk_id: str | None = None
    classification: str | None = None
    sensitivity: str | None = None
    domain: str | None = None
    labels: list[str] | None = None
    owner_principal: str | None = None
    source_mode: Literal["inline", "sql_view", "sidecar"] = "sidecar"


async def execute_retrieval(
    session: AsyncSession,
    org_id: UUID,
    plan: str,
    query_text: str,
    query_vector: list[float],
    principal_id: UUID,
    connector_id: UUID,
    top_k: int = 10,
    filters: dict | None = None,
    include_unresolved: bool = False,
    actor_id: UUID | None = None,
    actor_name: str = "",
) -> dict:
    """Execute a secured retrieval — the Gateco product core flow.

    Real vector search through connector → Phase 1 metadata resolution via
    resource_chunks → deny-by-default policy enforcement → per-result trace.
    """
    start = time.perf_counter()

    # 1. Usage limit check
    within_limit, used, limit = await usage_service.check_usage_limit(session, org_id, plan)
    if not within_limit:
        raise EntitlementError(
            detail=f"Retrieval limit exceeded: {used}/{limit}",
            upgrade_to="pro" if plan == "free" else "enterprise",
        )

    # 2. Load principal
    result = await session.execute(
        select(Principal).where(
            Principal.id == principal_id,
            Principal.organization_id == org_id,
        )
    )
    principal = result.scalar_one_or_none()
    if not principal:
        raise NotFoundError(detail="Principal not found")

    # 3. Load connector
    result = await session.execute(
        select(Connector).where(
            Connector.id == connector_id,
            Connector.organization_id == org_id,
            Connector.deleted_at.is_(None),
        )
    )
    connector = result.scalar_one_or_none()
    if not connector:
        raise NotFoundError(detail="Connector not found")

    # 4. Validate search_config exists
    if not connector.search_config:
        raise ValidationError(detail="Connector has no search configuration")

    # 5. Validate query_vector dimensions (if expected_dimension known)
    expected_dim = connector.search_config.get("expected_dimension")
    if expected_dim and len(query_vector) != expected_dim:
        raise ValidationError(
            detail=f"query_vector dimension {len(query_vector)} != expected {expected_dim}"
        )

    # 6. Decrypt config + execute vector search
    secret_fields = CONNECTOR_SECRET_FIELDS.get(connector.type.value, [])
    decrypted = decrypt_config_secrets(connector.config or {}, secret_fields)
    search_response = await execute_vector_search(
        connector.type.value, decrypted, connector.search_config, query_vector, top_k
    )
    connector_latency = search_response.latency_ms

    # Check for adapter-level errors
    if search_response.error_category and not search_response.results:
        raise ValidationError(
            detail=search_response.warnings[0] if search_response.warnings else "Search failed"
        )

    # 7. Resolve metadata via 3-step hierarchy (inline -> SQL view -> sidecar)
    vector_ids = [r.vector_id for r in search_response.results]
    resolved_subjects = await _resolve_metadata(
        connector, search_response.results, session, org_id,
    )
    metadata_modes_used: set[str] = set()
    for subj in resolved_subjects.values():
        metadata_modes_used.add(subj.source_mode)

    # 8. For sidecar/mixed resolution, load chunks and resources via existing path
    chunk_map: dict[str, ResourceChunk] = {}
    if vector_ids:
        chunk_result = await session.execute(
            select(ResourceChunk).where(
                ResourceChunk.vector_id.in_(vector_ids),
                ResourceChunk.source_connector_id == connector_id,
            )
        )
        chunks = list(chunk_result.scalars().all())
        chunk_map = {c.vector_id: c for c in chunks if c.vector_id}

    # Partition into resolved vs unresolved (deny-by-default)
    resolved_results = []
    unresolved_results = []
    for sr in search_response.results:
        if sr.vector_id in chunk_map:
            resolved_results.append((sr, chunk_map[sr.vector_id]))
        elif sr.vector_id in resolved_subjects:
            # Resolved via inline/sql_view but no sidecar chunk — still resolved
            resolved_results.append((sr, None))
        else:
            unresolved_results.append(sr)

    # 9. Load GatedResources for resolved chunks (batch)
    resource_ids = list({
        c.resource_id for _, c in resolved_results
        if c is not None
    })
    if resource_ids:
        res_result = await session.execute(
            select(GatedResource).where(
                GatedResource.id.in_(resource_ids),
                GatedResource.organization_id == org_id,
                GatedResource.deleted_at.is_(None),
            )
        )
        resources = list(res_result.scalars().all())
    else:
        resources = []
    resource_map = {r.id: r for r in resources}

    # 10. Policy evaluation on resolved resources
    result = await session.execute(
        select(Policy)
        .options(selectinload(Policy.rules))
        .where(
            Policy.organization_id == org_id,
            Policy.status == PolicyStatus.active,
            Policy.deleted_at.is_(None),
        )
    )
    active_policies = list(result.scalars().all())
    eval_result = evaluate_policies(principal, resources, active_policies)
    allowed_resource_ids = set(eval_result.allowed_resources)

    # Build policy trace lookup for per-result decisions
    trace_by_resource: dict[str, dict] = {}
    for t in eval_result.policy_trace:
        rid = t.get("resource_id")
        if rid and t.get("matched"):
            trace_by_resource[rid] = t

    # 11. Build per-result response (preserving connector similarity order)
    results = []
    allowed_count = 0
    denied_count = 0
    for sr, chunk in resolved_results:
        # For inline/sql_view resolved results without a sidecar chunk
        if chunk is None:
            subject = resolved_subjects.get(sr.vector_id)
            if subject and subject.source_mode in ("inline", "sql_view"):
                # Allow inline/sql_view resolved results (no resource-level policy yet)
                allowed_count += 1
                results.append({
                    "vector_id": sr.vector_id,
                    "score": sr.score,
                    "text": sr.text,
                    "resource_id": None,
                    "chunk_id": None,
                    "policy_decision": "allowed",
                    "matched_policy_id": None,
                    "denial_reason": None,
                    "metadata_resolution_mode_used": subject.source_mode,
                })
                continue
            unresolved_results.append(sr)
            continue

        resource = resource_map.get(chunk.resource_id)
        if not resource:
            # Resource not found in org — treat as unresolved
            unresolved_results.append(sr)
            continue
        resource_allowed = chunk.resource_id in allowed_resource_ids
        trace_info = trace_by_resource.get(str(chunk.resource_id), {})

        if resource_allowed:
            allowed_count += 1
        else:
            denied_count += 1

        subject = resolved_subjects.get(sr.vector_id)
        mode_used = subject.source_mode if subject else "sidecar"
        results.append({
            "vector_id": sr.vector_id,
            "score": sr.score,
            "text": sr.text if resource_allowed else None,
            "resource_id": str(chunk.resource_id),
            "chunk_id": str(chunk.id),
            "policy_decision": "allowed" if resource_allowed else "denied",
            "matched_policy_id": trace_info.get("policy_id"),
            "denial_reason": (
                next(
                    (r for r in eval_result.denial_reasons if str(chunk.resource_id) in r),
                    "Denied by policy",
                )
                if not resource_allowed
                else None
            ),
            "metadata_resolution_mode_used": mode_used,
        })

    # 12. Append unresolved if requested (diagnostic only — no content)
    if include_unresolved:
        for sr in unresolved_results:
            results.append({
                "vector_id": sr.vector_id,
                "score": sr.score,
                "text": None,
                "resource_id": None,
                "chunk_id": None,
                "policy_decision": "unresolved",
                "matched_policy_id": None,
                "denial_reason": "No metadata binding",
            })

    # Determine outcome
    if allowed_count == 0 and (denied_count > 0 or len(unresolved_results) > 0):
        outcome = RetrievalOutcome.denied
    elif denied_count == 0 and len(unresolved_results) == 0:
        outcome = RetrievalOutcome.allowed
    else:
        outcome = RetrievalOutcome.partial

    latency_ms = int((time.perf_counter() - start) * 1000)

    # Build warnings
    warnings = list(search_response.warnings)
    if unresolved_results:
        warnings.append(f"{len(unresolved_results)} vectors had no metadata binding")

    # 13. Persist retrieval record
    retrieval = SecuredRetrieval(
        organization_id=org_id,
        query=query_text or "",
        principal_id=principal_id,
        principal_name=principal.display_name,
        connector_id=connector_id,
        connector_name=connector.name,
        matched_chunks=len(search_response.results),
        allowed_chunks=allowed_count,
        denied_chunks=denied_count,
        unresolved_chunks=len(unresolved_results),
        connector_latency_ms=connector_latency,
        outcome=outcome,
        denial_reasons=eval_result.denial_reasons or None,
        policy_trace=eval_result.policy_trace or None,
        resource_ids=resource_ids or None,
        chunk_ids=[c.id for _, c in resolved_results] or None,
        latency_ms=latency_ms,
    )
    session.add(retrieval)

    # 14. Audit
    audit_type = (
        AuditEventType.retrieval_allowed
        if outcome != RetrievalOutcome.denied
        else AuditEventType.retrieval_denied
    )
    await audit_service.emit_event(
        session=session,
        org_id=org_id,
        event_type=audit_type,
        actor_id=actor_id,
        actor_name=actor_name,
        details=f"Retrieval: {(query_text or '')[:100]} → {outcome.value}",
        principal_id=principal_id,
        resource_ids=resource_ids,
    )

    # 15. Usage increment
    await usage_service.increment_retrievals(session, org_id)

    await session.flush()

    # 16. Return
    return {
        "retrieval_id": str(retrieval.id),
        "outcome": outcome.value,
        "query": query_text or "",
        "matched_chunks": len(search_response.results),
        "allowed_chunks": allowed_count,
        "denied_chunks": denied_count,
        "unresolved_chunks": len(unresolved_results),
        "connector_latency_ms": connector_latency,
        "results": results,
        "denial_reasons": eval_result.denial_reasons,
        "policy_trace": eval_result.policy_trace,
        "latency_ms": latency_ms,
        "warnings": warnings,
    }


async def _resolve_metadata(
    connector: Connector,
    search_results: list[VectorSearchResult],
    db: AsyncSession,
    org_id: UUID,
) -> dict[str, ResolvedPolicySubject]:
    """Spec Diagram 4: inline -> SQL view -> sidecar -> unresolved=deny."""
    mode = connector.metadata_resolution_mode or "sidecar"
    resolved: dict[str, ResolvedPolicySubject] = {}
    search_config = connector.search_config or {}

    # Step 1: Inline metadata (from vector payload)
    if mode in ("inline", "auto"):
        field_mapping = search_config.get("metadata_field_mapping")
        if mode == "inline" and not field_mapping:
            raise ValidationError(
                detail="metadata_field_mapping required for inline mode"
            )
        if field_mapping:
            for result in search_results:
                if result.metadata:
                    subject = _extract_inline_metadata(result, field_mapping)
                    if subject:
                        resolved[result.vector_id] = subject

    unresolved_ids = [
        r.vector_id for r in search_results if r.vector_id not in resolved
    ]

    # Step 2: SQL view (Postgres-family connectors only)
    if mode in ("sql_view", "auto") and unresolved_ids:
        view_name = search_config.get("metadata_view_name")
        if view_name and connector.type.value in POSTGRES_FAMILY_TYPES:
            view_resolved = await _resolve_sql_view(
                connector, unresolved_ids, search_config,
            )
            resolved.update(view_resolved)

    unresolved_ids = [
        r.vector_id for r in search_results if r.vector_id not in resolved
    ]

    # Step 3: Sidecar registry (existing behavior)
    if mode in ("sidecar", "auto") and unresolved_ids:
        sidecar_resolved = await _resolve_sidecar(
            unresolved_ids, connector.id, db,
        )
        resolved.update(sidecar_resolved)

    return resolved


def _extract_inline_metadata(
    result: VectorSearchResult,
    field_mapping: dict[str, str],
) -> ResolvedPolicySubject | None:
    """Extract metadata from vector payload using field mapping."""
    if not result.metadata:
        return None

    subject = ResolvedPolicySubject(
        vector_id=result.vector_id,
        source_mode="inline",
    )

    has_any = False
    for spec_field, payload_key in field_mapping.items():
        if spec_field not in ALLOWED_METADATA_FIELDS:
            continue
        value = result.metadata.get(payload_key)
        if value is not None:
            setattr(subject, spec_field, value)
            has_any = True

    return subject if has_any else None


async def _resolve_sql_view(
    connector: Connector,
    vector_ids: list[str],
    search_config: dict,
) -> dict[str, ResolvedPolicySubject]:
    """Query a named view for metadata. Postgres-family only."""
    view_name = search_config["metadata_view_name"]
    id_column = search_config.get("metadata_id_column", "vector_id")
    field_mapping = search_config.get("metadata_field_mapping", {})

    # Validate identifiers
    _validate_sql_identifier(view_name)
    _validate_sql_identifier(id_column)
    for col in field_mapping.values():
        _validate_sql_identifier(col)

    # Build safe parameterized query
    columns = [id_column] + list(field_mapping.values())
    col_str = ", ".join(f'"{c}"' for c in columns)
    sql = f'SELECT {col_str} FROM "{view_name}" WHERE "{id_column}" = ANY($1)'

    # Connect to the connector's database
    config = connector.config or {}
    if "connection_string" in config:
        dsn = config["connection_string"]
    else:
        dsn = _build_pgvector_dsn(config)

    resolved: dict[str, ResolvedPolicySubject] = {}
    try:
        conn = await asyncpg.connect(dsn, timeout=4.0)
        try:
            rows = await conn.fetch(sql, vector_ids)
            for row in rows:
                vid = str(row[id_column])
                subject = ResolvedPolicySubject(
                    vector_id=vid,
                    source_mode="sql_view",
                )
                for spec_field, db_col in field_mapping.items():
                    if spec_field in ALLOWED_METADATA_FIELDS:
                        value = row.get(db_col)
                        if value is not None:
                            setattr(subject, spec_field, value)
                resolved[vid] = subject
        finally:
            await conn.close()
    except Exception as e:
        logger.error("sql_view_resolution_error: %s", str(e))

    return resolved


async def _resolve_sidecar(
    vector_ids: list[str],
    connector_id: UUID,
    db: AsyncSession,
) -> dict[str, ResolvedPolicySubject]:
    """Resolve metadata via sidecar registry (existing ResourceChunk + GatedResource)."""
    if not vector_ids:
        return {}

    chunk_result = await db.execute(
        select(ResourceChunk).where(
            ResourceChunk.vector_id.in_(vector_ids),
            ResourceChunk.source_connector_id == connector_id,
        )
    )
    chunks = list(chunk_result.scalars().all())

    resolved: dict[str, ResolvedPolicySubject] = {}
    for chunk in chunks:
        if chunk.vector_id:
            resolved[chunk.vector_id] = ResolvedPolicySubject(
                vector_id=chunk.vector_id,
                resource_id=str(chunk.resource_id) if chunk.resource_id else None,
                chunk_id=str(chunk.id),
                source_mode="sidecar",
            )
    return resolved


async def list_retrievals(
    session: AsyncSession, org_id: UUID,
    outcome: str | None = None,
    principal_id: UUID | None = None,
    connector_id: UUID | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1, per_page: int = 20,
) -> dict:
    from sqlalchemy import func

    query = select(SecuredRetrieval).where(SecuredRetrieval.organization_id == org_id)
    if outcome:
        query = query.where(SecuredRetrieval.outcome == outcome)
    if principal_id:
        query = query.where(SecuredRetrieval.principal_id == principal_id)
    if connector_id:
        query = query.where(SecuredRetrieval.connector_id == connector_id)
    if date_from:
        query = query.where(SecuredRetrieval.timestamp >= date_from)
    if date_to:
        query = query.where(SecuredRetrieval.timestamp <= date_to)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_q)).scalar() or 0

    offset = (page - 1) * per_page
    result = await session.execute(
        query.order_by(SecuredRetrieval.timestamp.desc()).offset(offset).limit(per_page)
    )
    data = [_serialize_retrieval(r) for r in result.scalars().all()]
    total_pages = max(1, (total + per_page - 1) // per_page)

    return {
        "data": data,
        "meta": {"pagination": {
            "page": page, "per_page": per_page,
            "total": total, "total_pages": total_pages,
        }},
    }


async def get_retrieval(session: AsyncSession, org_id: UUID, retrieval_id: UUID) -> dict:
    result = await session.execute(
        select(SecuredRetrieval).where(
            SecuredRetrieval.id == retrieval_id,
            SecuredRetrieval.organization_id == org_id,
        )
    )
    r = result.scalar_one_or_none()
    if not r:
        raise NotFoundError(detail="Retrieval not found")
    return _serialize_retrieval(r)


def _serialize_retrieval(r: SecuredRetrieval) -> dict:
    return {
        "id": str(r.id),
        "query": r.query,
        "principal_id": str(r.principal_id) if r.principal_id else None,
        "principal_name": r.principal_name,
        "connector_id": str(r.connector_id) if r.connector_id else None,
        "connector_name": r.connector_name,
        "matched_chunks": r.matched_chunks,
        "allowed_chunks": r.allowed_chunks,
        "denied_chunks": r.denied_chunks,
        "unresolved_chunks": r.unresolved_chunks,
        "connector_latency_ms": r.connector_latency_ms,
        "outcome": r.outcome.value,
        "denial_reasons": r.denial_reasons,
        "policy_trace": r.policy_trace,
        "resource_ids": [str(rid) for rid in r.resource_ids] if r.resource_ids else [],
        "chunk_ids": [str(cid) for cid in r.chunk_ids] if r.chunk_ids else [],
        "latency_ms": r.latency_ms,
        "timestamp": r.timestamp.isoformat(),
    }
