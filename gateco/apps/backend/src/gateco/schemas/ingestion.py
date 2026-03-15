"""Pydantic schemas for document ingestion."""

from pydantic import BaseModel, Field


class PreEmbeddedChunk(BaseModel):
    """A pre-embedded chunk with text and its vector embedding (BYOE)."""

    text: str
    vector: list[float]


class IngestDocumentRequest(BaseModel):
    """Request to ingest a single document."""

    connector_id: str
    external_resource_id: str = Field(min_length=1, max_length=500)
    text: str | None = Field(default=None, min_length=1)
    pre_embedded_chunks: list[PreEmbeddedChunk] | None = None
    classification: str | None = None
    sensitivity: str | None = None
    domain: str | None = None
    labels: list[str] | None = None
    metadata: dict | None = None
    owner_principal_id: str | None = None
    idempotency_key: str | None = Field(default=None, max_length=255)


class IngestDocumentResponse(BaseModel):
    """Response from single document ingestion."""

    status: str  # "success"
    resource_id: str
    external_resource_id: str
    chunk_count: int
    vector_ids: list[str]


class IngestErrorResponse(BaseModel):
    """Error response from ingestion."""

    status: str = "error"
    error_category: str
    detail: str


class BatchIngestRecord(BaseModel):
    """A single record in a batch ingestion request."""

    external_resource_id: str = Field(min_length=1, max_length=500)
    text: str = Field(min_length=1)
    classification: str | None = None
    sensitivity: str | None = None
    domain: str | None = None
    labels: list[str] | None = None
    metadata: dict | None = None
    owner_principal_id: str | None = None


class BatchIngestRequest(BaseModel):
    """Request to ingest a batch of documents."""

    connector_id: str
    records: list[BatchIngestRecord] = Field(min_length=1, max_length=100)
    idempotency_key: str | None = Field(default=None, max_length=255)


class BatchIngestResultItem(BaseModel):
    """Result for a single successfully ingested record."""

    external_resource_id: str
    resource_id: str
    chunk_count: int
    vector_ids: list[str]


class BatchIngestErrorItem(BaseModel):
    """Error for a single failed record."""

    external_resource_id: str
    error_category: str
    detail: str


class BatchIngestResponse(BaseModel):
    """Response from batch ingestion."""

    status: str  # "success" | "partial_success" | "error"
    succeeded: int
    failed: int
    results: list[BatchIngestResultItem]
    errors: list[BatchIngestErrorItem]
