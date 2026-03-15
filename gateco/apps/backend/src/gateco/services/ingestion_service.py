"""Ingestion service — orchestrates document ingestion: chunk -> embed -> insert -> register.

Writes to the same GatedResource + ResourceChunk registry as Phase 2 binding.
Retrieval resolves ingested vectors immediately with no separate bind step.

Wave 3 additions:
- Idempotency key cache (D3.7): replay cached responses for duplicate requests.
- Bring-Your-Own-Embeddings (D3.8): accept pre-embedded chunks, skip chunking + embedding.
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.enums import (
    AuditEventType,
    Classification,
    ConnectorType,
    ResourceType,
    Sensitivity,
)
from gateco.database.models.connector import Connector
from gateco.database.models.idempotency import IdempotencyRecord
from gateco.database.models.resource import GatedResource
from gateco.database.models.resource_chunk import ResourceChunk
from gateco.exceptions import ConflictError, ValidationError
from gateco.schemas.ingestion import (
    BatchIngestErrorItem,
    BatchIngestRequest,
    BatchIngestResponse,
    BatchIngestResultItem,
    IngestDocumentRequest,
    IngestDocumentResponse,
)
from gateco.services import audit_service
from gateco.services.chunking_service import Chunk, ChunkingConfig, chunk_text
from gateco.services.connector_adapters_insert import insert_vectors
from gateco.services.connector_service import _load
from gateco.services.embedding_service import EmbeddingConfig, generate_embeddings
from gateco.utils.crypto import decrypt_config_secrets

logger = logging.getLogger(__name__)

IDEMPOTENCY_TTL = timedelta(hours=24)

# Tier 1 connectors that support ingestion at launch
TIER_1_CONNECTORS = {
    ConnectorType.pgvector,
    ConnectorType.supabase,
    ConnectorType.neon,
    ConnectorType.pinecone,
    ConnectorType.qdrant,
}

VALID_CLASSIFICATIONS = {e.value for e in Classification}
VALID_SENSITIVITIES = {e.value for e in Sensitivity}


def is_ingestion_capable(connector_type: ConnectorType) -> bool:
    """Check if a connector type supports ingestion (Tier 1)."""
    return connector_type in TIER_1_CONNECTORS


async def ingest_document(
    session: AsyncSession,
    org_id: UUID,
    request: IngestDocumentRequest,
    embedding_config: EmbeddingConfig | None = None,
    chunking_config: ChunkingConfig | None = None,
    actor_id: UUID | None = None,
    actor_name: str = "",
) -> IngestDocumentResponse:
    """Ingest a single document: chunk, embed, insert vectors, register metadata.

    Supports:
    - Standard text ingestion (chunk + embed automatically)
    - BYOE: pre_embedded_chunks bypass chunking and embedding
    - Idempotency: if idempotency_key is set, replays cached response on duplicate

    Args:
        session: DB session.
        org_id: Organization ID.
        request: Ingestion request with text or pre_embedded_chunks and metadata.
        embedding_config: Optional embedding provider config.
        chunking_config: Optional chunking config.
        actor_id: Optional actor for audit trail.
        actor_name: Optional actor name for audit trail.

    Returns:
        IngestDocumentResponse with resource_id, chunk_count, vector_ids.

    Raises:
        ValidationError: If connector is not ingestion-capable or config is missing.
        ConflictError: If idempotency key exists with a different request fingerprint.
        RuntimeError: If embedding or vector insertion fails.
    """
    # D3.7 — Idempotency check
    if request.idempotency_key:
        cached = await _check_idempotency(
            session, request.idempotency_key, str(org_id), "ingest",
            request.model_dump(),
        )
        if cached is not None:
            return IngestDocumentResponse(**cached)

    # D3.8 — Validate mutual exclusivity of text vs pre_embedded_chunks
    if request.pre_embedded_chunks and request.text:
        raise _ingestion_error(
            "ingestion_validation_failed",
            "Cannot provide both 'text' and 'pre_embedded_chunks'. They are mutually exclusive.",
        )
    if not request.pre_embedded_chunks and not request.text:
        raise _ingestion_error(
            "ingestion_validation_failed",
            "Must provide either 'text' or 'pre_embedded_chunks'.",
        )

    connector_id = UUID(request.connector_id)

    # 1. Load and validate connector
    connector = await _load(session, org_id, connector_id)
    _validate_connector_for_ingestion(connector)

    # 2. Validate metadata
    _validate_metadata(request.classification, request.sensitivity)

    # D3.8 — BYOE path: use pre-embedded chunks directly
    if request.pre_embedded_chunks:
        chunks, embeddings = _prepare_byoe(request, connector)
    else:
        # 3. Standard path: chunk text
        chunks = chunk_text(request.text, chunking_config)
        if not chunks:
            raise ValidationError(detail="Text produced no chunks after processing")

        # 4. Generate embeddings
        try:
            chunk_texts = [c.text for c in chunks]
            embedding_result = await generate_embeddings(chunk_texts, embedding_config)
        except (ValueError, RuntimeError) as e:
            raise _ingestion_error("embedding_provider_error", str(e))

        # 5. Validate embedding dimensions
        _validate_dimensions(embedding_result.dimensions, connector)
        embeddings = embedding_result.embeddings

    # 6. Build vector records and insert into connector
    from gateco.schemas.connectors import CONNECTOR_SECRET_FIELDS

    secret_fields = CONNECTOR_SECRET_FIELDS.get(connector.type.value, [])
    decrypted_config = decrypt_config_secrets(connector.config or {}, secret_fields)
    ingestion_config = connector.ingestion_config or {}

    vector_records = []
    for i, chunk in enumerate(chunks):
        vector_id = f"{request.external_resource_id}_chunk_{i}"
        payload = {"text": chunk.text}
        if request.metadata:
            payload.update(request.metadata)
        vector_records.append({
            "id": vector_id,
            "vector": embeddings[i],
            "payload": payload,
        })

    try:
        await insert_vectors(
            connector.type.value, decrypted_config, ingestion_config, vector_records,
        )
    except Exception as e:
        raise _ingestion_error("connector_insert_failed", str(e))

    # 7. Register metadata (GatedResource + ResourceChunks)
    try:
        resource, vector_ids = await _register_metadata(
            session, org_id, connector, request, chunks, vector_records,
        )
    except Exception as e:
        logger.error("metadata_registration_failed: %s", str(e))
        raise _ingestion_error("metadata_registration_failed", str(e))

    # 8. Audit event
    await audit_service.emit_event(
        session=session,
        org_id=org_id,
        event_type=AuditEventType.document_ingested,
        actor_id=actor_id,
        actor_name=actor_name,
        details=(
            f"Document ingested: {request.external_resource_id}, "
            f"{len(chunks)} chunks, connector={connector_id}"
        ),
        resource_ids=[resource.id],
    )

    result = IngestDocumentResponse(
        status="success",
        resource_id=str(resource.id),
        external_resource_id=request.external_resource_id,
        chunk_count=len(chunks),
        vector_ids=vector_ids,
    )

    # D3.7 — Store idempotency record
    if request.idempotency_key:
        await _store_idempotency(
            session, request.idempotency_key, str(org_id), "ingest",
            request.model_dump(), result.model_dump(),
        )

    return result


async def ingest_batch(
    session: AsyncSession,
    org_id: UUID,
    request: BatchIngestRequest,
    embedding_config: EmbeddingConfig | None = None,
    chunking_config: ChunkingConfig | None = None,
    actor_id: UUID | None = None,
    actor_name: str = "",
) -> BatchIngestResponse:
    """Ingest a batch of documents. Each record processed independently.

    Returns partial success semantics: some records may succeed while others fail.
    Supports idempotency key caching (D3.7).
    """
    # D3.7 — Idempotency check
    if request.idempotency_key:
        cached = await _check_idempotency(
            session, request.idempotency_key, str(org_id), "ingest_batch",
            request.model_dump(),
        )
        if cached is not None:
            return BatchIngestResponse(**cached)

    connector_id = UUID(request.connector_id)
    connector = await _load(session, org_id, connector_id)
    _validate_connector_for_ingestion(connector)

    results: list[BatchIngestResultItem] = []
    errors: list[BatchIngestErrorItem] = []

    for record in request.records:
        try:
            single_request = IngestDocumentRequest(
                connector_id=request.connector_id,
                external_resource_id=record.external_resource_id,
                text=record.text,
                classification=record.classification,
                sensitivity=record.sensitivity,
                domain=record.domain,
                labels=record.labels,
                metadata=record.metadata,
                owner_principal_id=record.owner_principal_id,
            )
            result = await ingest_document(
                session, org_id, single_request, embedding_config, chunking_config,
                actor_id, actor_name,
            )
            results.append(BatchIngestResultItem(
                external_resource_id=result.external_resource_id,
                resource_id=result.resource_id,
                chunk_count=result.chunk_count,
                vector_ids=result.vector_ids,
            ))
        except ValidationError as e:
            errors.append(BatchIngestErrorItem(
                external_resource_id=record.external_resource_id,
                error_category=getattr(e, "_ingestion_category", "ingestion_validation_failed"),
                detail=e.detail,
            ))
        except Exception as e:
            errors.append(BatchIngestErrorItem(
                external_resource_id=record.external_resource_id,
                error_category="ingestion_validation_failed",
                detail=str(e),
            ))

    succeeded = len(results)
    failed = len(errors)

    if failed == 0:
        status = "success"
    elif succeeded == 0:
        status = "error"
    else:
        status = "partial_success"

    # Batch audit event
    resource_ids = [UUID(r.resource_id) for r in results]
    await audit_service.emit_event(
        session=session,
        org_id=org_id,
        event_type=AuditEventType.batch_ingested,
        actor_id=actor_id,
        actor_name=actor_name,
        details=(
            f"Batch ingestion: {succeeded} succeeded, {failed} failed, "
            f"connector={connector_id}"
        ),
        resource_ids=resource_ids if resource_ids else None,
    )

    batch_result = BatchIngestResponse(
        status=status,
        succeeded=succeeded,
        failed=failed,
        results=results,
        errors=errors,
    )

    # D3.7 — Store idempotency record
    if request.idempotency_key:
        await _store_idempotency(
            session, request.idempotency_key, str(org_id), "ingest_batch",
            request.model_dump(), batch_result.model_dump(),
        )

    return batch_result


def _validate_connector_for_ingestion(connector: Connector) -> None:
    """Validate that a connector is capable and configured for ingestion."""
    if not is_ingestion_capable(connector.type):
        raise _ingestion_error(
            "connector_not_ingestion_capable",
            f"Connector type '{connector.type.value}' does not support ingestion. "
            f"Tier 1 types: {', '.join(t.value for t in TIER_1_CONNECTORS)}",
        )
    if not connector.ingestion_config:
        raise _ingestion_error(
            "connector_write_config_missing",
            "Connector does not have ingestion_config set. "
            "Configure write settings before ingesting.",
        )


def _validate_metadata(
    classification: str | None,
    sensitivity: str | None,
) -> None:
    """Validate classification and sensitivity values."""
    if classification and classification not in VALID_CLASSIFICATIONS:
        raise _ingestion_error(
            "ingestion_validation_failed",
            f"Invalid classification: {classification}. "
            f"Valid: {', '.join(VALID_CLASSIFICATIONS)}",
        )
    if sensitivity and sensitivity not in VALID_SENSITIVITIES:
        raise _ingestion_error(
            "ingestion_validation_failed",
            f"Invalid sensitivity: {sensitivity}. "
            f"Valid: {', '.join(VALID_SENSITIVITIES)}",
        )


def _validate_dimensions(dimensions: int, connector: Connector) -> None:
    """Validate embedding dimensions match connector's expected dimension."""
    search_config = connector.search_config or {}
    expected = search_config.get("expected_dimension")
    if expected and dimensions != expected:
        raise _ingestion_error(
            "ingestion_validation_failed",
            f"Embedding dimensions ({dimensions}) do not match connector's "
            f"expected_dimension ({expected})",
        )


async def _register_metadata(
    session: AsyncSession,
    org_id: UUID,
    connector: Connector,
    request: IngestDocumentRequest,
    chunks: list,
    vector_records: list[dict],
) -> tuple[GatedResource, list[str]]:
    """Register or update GatedResource + ResourceChunks. Returns (resource, vector_ids)."""
    connector_id = connector.id

    # Lookup or create GatedResource by (org, connector, external_resource_key)
    res_result = await session.execute(
        select(GatedResource).where(
            GatedResource.organization_id == org_id,
            GatedResource.source_connector_id == connector_id,
            GatedResource.external_resource_key == request.external_resource_id,
            GatedResource.deleted_at.is_(None),
        )
    )
    resource = res_result.scalar_one_or_none()

    if resource is None:
        resource = GatedResource(
            organization_id=org_id,
            source_connector_id=connector_id,
            external_resource_key=request.external_resource_id,
            type=ResourceType.file,
            title=request.external_resource_id,
            content_url=f"ingestion://{request.external_resource_id}",
        )
        session.add(resource)
    # Update resource-level metadata
    if request.classification:
        resource.classification = Classification(request.classification)
    if request.sensitivity:
        resource.sensitivity = Sensitivity(request.sensitivity)
    if request.domain:
        resource.domain = request.domain
    if request.labels:
        resource.labels = request.labels
    if request.owner_principal_id:
        resource.owner_principal = UUID(request.owner_principal_id)

    await session.flush()

    # Create ResourceChunks with content_hash dedup
    vector_ids: list[str] = []
    for i, chunk in enumerate(chunks):
        vector_id = vector_records[i]["id"]

        # Check for content_hash dedup
        existing = await session.execute(
            select(ResourceChunk).where(
                ResourceChunk.resource_id == resource.id,
                ResourceChunk.content_hash == chunk.content_hash,
            )
        )
        if existing.scalar_one_or_none() is not None:
            # Chunk already exists with same content — skip (dedup)
            vector_ids.append(vector_id)
            continue

        # Check if vector_id already bound to this connector
        existing_by_vector = await session.execute(
            select(ResourceChunk).where(
                ResourceChunk.source_connector_id == connector_id,
                ResourceChunk.vector_id == vector_id,
            )
        )
        existing_chunk = existing_by_vector.scalar_one_or_none()
        if existing_chunk is not None:
            # Update existing chunk
            existing_chunk.resource_id = resource.id
            existing_chunk.content_hash = chunk.content_hash
            existing_chunk.index = chunk.index
        else:
            new_chunk = ResourceChunk(
                resource_id=resource.id,
                source_connector_id=connector_id,
                index=chunk.index,
                vector_id=vector_id,
                content_hash=chunk.content_hash,
            )
            session.add(new_chunk)

        vector_ids.append(vector_id)

    await session.flush()
    return resource, vector_ids


def _prepare_byoe(
    request: IngestDocumentRequest,
    connector: Connector,
) -> tuple[list[Chunk], list[list[float]]]:
    """Validate and prepare pre-embedded chunks for BYOE ingestion.

    Returns:
        Tuple of (chunks, embeddings) ready for vector insertion.

    Raises:
        ValidationError: If vectors have inconsistent dimensions or mismatch connector config.
    """
    pec = request.pre_embedded_chunks
    if not pec:
        raise _ingestion_error(
            "ingestion_validation_failed", "pre_embedded_chunks is empty",
        )

    # Validate all vectors have the same dimension
    dimensions = {len(c.vector) for c in pec}
    if len(dimensions) > 1:
        raise _ingestion_error(
            "ingestion_validation_failed",
            f"All pre_embedded_chunks must have the same vector dimension. "
            f"Found: {sorted(dimensions)}",
        )

    dim = dimensions.pop()

    # Validate against connector's expected_dimension
    search_config = connector.search_config or {}
    expected = search_config.get("expected_dimension")
    if expected and dim != expected:
        raise _ingestion_error(
            "ingestion_validation_failed",
            f"Pre-embedded vector dimension ({dim}) does not match connector's "
            f"expected_dimension ({expected})",
        )

    # Build Chunk objects (content_hash from text for dedup)
    chunks: list[Chunk] = []
    embeddings: list[list[float]] = []
    for i, pc in enumerate(pec):
        content_hash = hashlib.sha256(
            " ".join(pc.text.lower().split()).encode()
        ).hexdigest()
        chunks.append(Chunk(index=i, text=pc.text, content_hash=content_hash))
        embeddings.append(pc.vector)

    return chunks, embeddings


async def _check_idempotency(
    session: AsyncSession,
    key: str,
    org_id: str,
    endpoint: str,
    payload: dict,
) -> dict | None:
    """Check for an existing idempotency record. Returns cached response or None.

    Raises:
        ConflictError: If key exists but request fingerprint differs.
    """
    try:
        result = await session.execute(
            select(IdempotencyRecord).where(
                IdempotencyRecord.key == key,
                IdempotencyRecord.org_id == org_id,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None

        # Check if expired
        now = datetime.now(timezone.utc)
        if record.expires_at < now:
            # Expired — delete and treat as new
            await session.delete(record)
            await session.flush()
            return None

        # Compare fingerprints
        fingerprint = IdempotencyRecord.compute_fingerprint(payload)
        if record.request_fingerprint != fingerprint:
            raise ConflictError(
                detail=(
                    f"Idempotency key '{key}' already used with a different request payload. "
                    f"Use a new key for different requests."
                ),
            )

        logger.info("idempotency_cache_hit key=%s endpoint=%s", key, endpoint)
        return record.response_body
    except ConflictError:
        raise
    except Exception:
        logger.warning("idempotency_check_failed key=%s", key, exc_info=True)
        return None


async def _store_idempotency(
    session: AsyncSession,
    key: str,
    org_id: str,
    endpoint: str,
    payload: dict,
    response: dict,
) -> None:
    """Store an idempotency record with a 24h TTL."""
    try:
        fingerprint = IdempotencyRecord.compute_fingerprint(payload)
        record = IdempotencyRecord(
            key=key,
            org_id=org_id,
            request_fingerprint=fingerprint,
            endpoint=endpoint,
            response_body=response,
            expires_at=datetime.now(timezone.utc) + IDEMPOTENCY_TTL,
        )
        session.add(record)
        await session.flush()
    except Exception:
        logger.warning("idempotency_store_failed key=%s", key, exc_info=True)


def _ingestion_error(category: str, detail: str) -> ValidationError:
    """Create a ValidationError with an ingestion error category attached."""
    err = ValidationError(detail=detail)
    err._ingestion_category = category  # type: ignore[attr-defined]
    return err
