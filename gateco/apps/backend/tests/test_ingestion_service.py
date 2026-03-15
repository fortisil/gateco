"""Tests for the ingestion service."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from gateco.database.enums import ConnectorType
from gateco.exceptions import ValidationError
from gateco.schemas.ingestion import (
    BatchIngestRecord,
    BatchIngestRequest,
    IngestDocumentRequest,
)
from gateco.services.embedding_service import EmbeddingResult
from gateco.services.ingestion_service import (
    _validate_connector_for_ingestion,
    _validate_metadata,
    is_ingestion_capable,
)


class TestIsIngestionCapable:
    def test_tier1_connectors(self):
        for ct in [ConnectorType.pgvector, ConnectorType.supabase,
                    ConnectorType.neon, ConnectorType.pinecone, ConnectorType.qdrant]:
            assert is_ingestion_capable(ct) is True

    def test_tier2_connectors(self):
        for ct in [ConnectorType.weaviate, ConnectorType.milvus,
                    ConnectorType.opensearch, ConnectorType.chroma]:
            assert is_ingestion_capable(ct) is False


class TestValidateConnectorForIngestion:
    def test_not_ingestion_capable(self):
        connector = MagicMock()
        connector.type = ConnectorType.weaviate
        connector.ingestion_config = None
        with pytest.raises(ValidationError, match="does not support ingestion"):
            _validate_connector_for_ingestion(connector)

    def test_no_ingestion_config(self):
        connector = MagicMock()
        connector.type = ConnectorType.pgvector
        connector.ingestion_config = None
        with pytest.raises(ValidationError, match="ingestion_config"):
            _validate_connector_for_ingestion(connector)

    def test_valid_connector(self):
        connector = MagicMock()
        connector.type = ConnectorType.pgvector
        connector.ingestion_config = {"target_table": "embeddings"}
        _validate_connector_for_ingestion(connector)  # Should not raise


class TestValidateMetadata:
    def test_valid_classification(self):
        _validate_metadata("confidential", None)  # Should not raise

    def test_invalid_classification(self):
        with pytest.raises(ValidationError, match="Invalid classification"):
            _validate_metadata("top_secret", None)

    def test_valid_sensitivity(self):
        _validate_metadata(None, "high")  # Should not raise

    def test_invalid_sensitivity(self):
        with pytest.raises(ValidationError, match="Invalid sensitivity"):
            _validate_metadata(None, "extreme")

    def test_none_values(self):
        _validate_metadata(None, None)  # Should not raise


class TestIngestDocument:
    @pytest.mark.asyncio
    async def test_ingest_document_success(self):
        """Test full document ingestion flow with mocked dependencies."""
        org_id = uuid4()
        connector_id = uuid4()

        # Mock connector
        mock_connector = MagicMock()
        mock_connector.id = connector_id
        mock_connector.type = ConnectorType.pgvector
        mock_connector.ingestion_config = {"target_table": "embeddings"}
        mock_connector.config = {"host": "localhost", "port": 5432}
        mock_connector.search_config = None

        # Mock session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No existing resource
        mock_session.execute.return_value = mock_result

        # Mock embedding result — "A" * 1024 produces 3 chunks with default config
        # (512 chars, 50 overlap): [0:512], [462:974], [924:1024]
        mock_embedding = EmbeddingResult(
            embeddings=[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]],
            model="text-embedding-3-small",
            dimensions=2,
        )

        request = IngestDocumentRequest(
            connector_id=str(connector_id),
            external_resource_id="test_doc_1",
            text="A" * 1024,  # Will produce 3 chunks with default config
            classification="internal",
        )

        with (
            patch("gateco.services.ingestion_service._load", return_value=mock_connector),
            patch(
                "gateco.services.ingestion_service.generate_embeddings",
                return_value=mock_embedding,
            ),
            patch("gateco.services.ingestion_service.insert_vectors", new_callable=AsyncMock),
            patch("gateco.services.ingestion_service._register_metadata") as mock_register,
            patch("gateco.services.ingestion_service.audit_service") as mock_audit,
        ):
            mock_resource = MagicMock()
            mock_resource.id = uuid4()
            mock_register.return_value = (
                mock_resource,
                ["test_doc_1_chunk_0", "test_doc_1_chunk_1", "test_doc_1_chunk_2"],
            )
            mock_audit.emit_event = AsyncMock()

            from gateco.services.ingestion_service import ingest_document
            result = await ingest_document(mock_session, org_id, request)

            assert result.status == "success"
            assert result.external_resource_id == "test_doc_1"
            assert result.chunk_count == 3
            assert len(result.vector_ids) == 3

    @pytest.mark.asyncio
    async def test_ingest_non_tier1_connector(self):
        """Test that non-Tier-1 connectors are rejected."""
        org_id = uuid4()
        connector_id = uuid4()

        mock_connector = MagicMock()
        mock_connector.type = ConnectorType.weaviate
        mock_connector.ingestion_config = None

        mock_session = AsyncMock()

        request = IngestDocumentRequest(
            connector_id=str(connector_id),
            external_resource_id="doc_1",
            text="test text",
        )

        with patch("gateco.services.ingestion_service._load", return_value=mock_connector):
            from gateco.services.ingestion_service import ingest_document
            with pytest.raises(ValidationError, match="does not support ingestion"):
                await ingest_document(mock_session, org_id, request)

    @pytest.mark.asyncio
    async def test_ingest_empty_text(self):
        """Test that empty text after chunking raises validation error."""
        org_id = uuid4()
        connector_id = uuid4()

        mock_connector = MagicMock()
        mock_connector.type = ConnectorType.pgvector
        mock_connector.ingestion_config = {"target_table": "embeddings"}

        mock_session = AsyncMock()

        request = IngestDocumentRequest(
            connector_id=str(connector_id),
            external_resource_id="doc_1",
            text="   ",  # Whitespace only
        )

        with patch("gateco.services.ingestion_service._load", return_value=mock_connector):
            from gateco.services.ingestion_service import ingest_document
            with pytest.raises(ValidationError, match="no chunks"):
                await ingest_document(mock_session, org_id, request)


class TestIngestBatch:
    @pytest.mark.asyncio
    async def test_batch_partial_success(self):
        """Test batch ingestion with partial success."""
        org_id = uuid4()
        connector_id = uuid4()

        mock_connector = MagicMock()
        mock_connector.id = connector_id
        mock_connector.type = ConnectorType.pgvector
        mock_connector.ingestion_config = {"target_table": "embeddings"}

        mock_session = AsyncMock()

        request = BatchIngestRequest(
            connector_id=str(connector_id),
            records=[
                BatchIngestRecord(external_resource_id="doc_1", text="valid text " * 50),
                BatchIngestRecord(external_resource_id="doc_2", text="   "),  # Will fail
            ],
        )

        mock_resource = MagicMock()
        mock_resource.id = uuid4()

        call_count = 0

        async def mock_ingest(session, org_id, req, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if req.text.strip():
                from gateco.schemas.ingestion import IngestDocumentResponse
                return IngestDocumentResponse(
                    status="success",
                    resource_id=str(uuid4()),
                    external_resource_id=req.external_resource_id,
                    chunk_count=1,
                    vector_ids=["v1"],
                )
            else:
                raise ValidationError(detail="Text produced no chunks after processing")

        with (
            patch("gateco.services.ingestion_service._load", return_value=mock_connector),
            patch("gateco.services.ingestion_service.ingest_document", side_effect=mock_ingest),
            patch("gateco.services.ingestion_service.audit_service") as mock_audit,
        ):
            mock_audit.emit_event = AsyncMock()

            from gateco.services.ingestion_service import ingest_batch
            result = await ingest_batch(mock_session, org_id, request)

            assert result.status == "partial_success"
            assert result.succeeded == 1
            assert result.failed == 1
            assert len(result.results) == 1
            assert len(result.errors) == 1
