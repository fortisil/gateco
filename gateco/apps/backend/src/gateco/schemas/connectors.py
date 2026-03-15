"""Connector request/response schemas."""

from pydantic import BaseModel, Field

# Secret fields by connector type
CONNECTOR_SECRET_FIELDS = {
    "pgvector": ["password"],
    "pinecone": ["api_key"],
    "opensearch": ["api_key"],
    "supabase": ["password"],
    "neon": ["connection_string"],
    "weaviate": ["api_key"],
    "qdrant": ["api_key"],
    "milvus": ["token"],
    "chroma": ["api_key"],
}

# Required fields per connector type
CONNECTOR_REQUIRED_FIELDS = {
    "pgvector": ["host", "port", "database"],
    "pinecone": ["api_key"],
    "opensearch": ["host", "api_key"],
    "supabase": ["host", "database", "password"],
    "neon": ["connection_string"],
    "weaviate": ["host", "api_key"],
    "qdrant": ["host"],
    "milvus": ["host"],
    "chroma": ["host"],
}

# Default values per connector type
CONNECTOR_DEFAULTS = {
    "pgvector": {"port": 5432, "user": "postgres", "schema": "public"},
    "supabase": {"port": 5432, "user": "postgres", "schema": "public"},
    "neon": {"schema": "public"},
    "milvus": {"port": 19530},
    "chroma": {"tenant": "default_tenant", "database": "default_database"},
}


VALID_METADATA_RESOLUTION_MODES = {"sidecar", "inline", "sql_view", "auto"}
POSTGRES_FAMILY_TYPES = {"pgvector", "supabase", "neon"}


class CreateConnectorRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: str  # ConnectorType value
    config: dict = Field(default_factory=dict)
    metadata_resolution_mode: str | None = None


class UpdateConnectorRequest(BaseModel):
    name: str | None = None
    config: dict | None = None
    metadata_resolution_mode: str | None = None


# Required fields per search config, per connector type
SEARCH_CONFIG_REQUIRED_FIELDS = {
    "pgvector": ["table_name", "vector_column", "id_column"],
    "supabase": ["table_name", "vector_column", "id_column"],
    "neon": ["table_name", "vector_column", "id_column"],
    "pinecone": ["index_name"],
    "qdrant": ["collection_name"],
    "weaviate": ["class_name"],
    "milvus": ["collection_name"],
    "opensearch": ["index_name", "vector_field"],
    "chroma": ["collection_name"],
}


class UpdateSearchConfigRequest(BaseModel):
    search_config: dict


class UpdateIngestionConfigRequest(BaseModel):
    ingestion_config: dict


class ConnectorResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str
    config: dict
    last_sync: str | None
    index_count: int
    record_count: int
    error_message: str | None
    created_at: str
    updated_at: str
    last_tested_at: str | None = None
    last_test_success: bool | None = None
    last_test_latency_ms: int | None = None
    server_version: str | None = None
    diagnostics: dict | None = None


class DiscoveredResourceSchema(BaseModel):
    name: str
    record_count: int | None = None
    dimension: int | None = None
    metric: str | None = None


class TestConnectorResponse(BaseModel):
    success: bool
    health_status: str = "failed"
    authenticated: bool = False
    schema_discovered: bool = False
    vector_ready: bool = False
    server_version: str | None = None
    resources: list[DiscoveredResourceSchema] | None = None
    resource_kind: str | None = None
    total_records: int | None = None
    approximate_counts: bool = False
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
    latency_ms: int | None = None
