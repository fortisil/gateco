"""Per-connector-type default configs for search and ingestion."""

from __future__ import annotations

CONNECTOR_SEARCH_CONFIG_DEFAULTS: dict[str, dict] = {
    "pgvector": {
        "table_name": "vh_vectors",
        "vector_column": "embedding",
        "id_column": "id",
        "top_k": 5,
    },
    "supabase": {
        "table_name": "vh_vectors",
        "vector_column": "embedding",
        "id_column": "id",
        "top_k": 5,
    },
    "neon": {
        "table_name": "vh_vectors",
        "vector_column": "embedding",
        "id_column": "id",
        "top_k": 5,
    },
    "qdrant": {
        "collection_name": "vh_vectors",
        "top_k": 5,
    },
    "pinecone": {
        "index_name": "vh-vectors",
        "top_k": 5,
    },
    "weaviate": {
        "class_name": "VhVectors",
        "top_k": 5,
    },
    "milvus": {
        "collection_name": "vh_vectors",
        "top_k": 5,
    },
    "opensearch": {
        "index_name": "vh-vectors",
        "vector_field": "embedding",
        "top_k": 5,
    },
    "chroma": {
        "collection_name": "vh_vectors",
        "top_k": 5,
    },
}

CONNECTOR_INGESTION_CONFIG_DEFAULTS: dict[str, dict] = {
    "pgvector": {
        "target_table": "vh_vectors",
        "id_field": "id",
        "content_field": "content",
        "chunk_size": 500,
        "chunk_overlap": 50,
    },
    "supabase": {
        "target_table": "vh_vectors",
        "id_field": "id",
        "content_field": "content",
        "chunk_size": 500,
        "chunk_overlap": 50,
    },
    "neon": {
        "target_table": "vh_vectors",
        "id_field": "id",
        "content_field": "content",
        "chunk_size": 500,
        "chunk_overlap": 50,
    },
    "pinecone": {
        "index_name": "vh-vectors",
        "chunk_size": 500,
        "chunk_overlap": 50,
    },
}


def get_search_config_defaults(connector_type: str) -> dict:
    """Return search config defaults for a connector type.

    Raises KeyError if connector type has no defaults defined.
    """
    if connector_type not in CONNECTOR_SEARCH_CONFIG_DEFAULTS:
        raise KeyError(
            f"No search config defaults for connector type: {connector_type}"
        )
    return dict(CONNECTOR_SEARCH_CONFIG_DEFAULTS[connector_type])


def get_ingestion_config_defaults(connector_type: str) -> dict:
    """Return ingestion config defaults for a connector type.

    Raises KeyError if connector type has no defaults defined.
    """
    if connector_type not in CONNECTOR_INGESTION_CONFIG_DEFAULTS:
        raise KeyError(
            f"No ingestion config defaults for connector type: {connector_type}"
        )
    return dict(CONNECTOR_INGESTION_CONFIG_DEFAULTS[connector_type])
