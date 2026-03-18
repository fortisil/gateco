"""Per-connector capability matrix and entitlement rules."""

from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass(frozen=True)
class ConnectorCapabilities:
    """Boolean capabilities for a connector type."""

    supports_direct_ingestion: bool
    supports_batch_ingestion: bool
    supports_retroactive_registration: bool
    supports_search_config: bool
    supports_ingestion_config: bool
    supports_metadata_resolution_inline: bool
    supports_metadata_resolution_sidecar: bool
    supports_metadata_resolution_sql_view: bool
    supports_chunk_level_binding: bool
    supports_resource_level_binding: bool
    expected_max_readiness_level: int  # L0-L4
    supports_simulator: bool
    supports_audit_export: bool

    def has_capability(self, name: str) -> bool:
        """Check a capability by field name."""
        value = getattr(self, name, None)
        if value is None:
            raise ValueError(f"Unknown capability: {name}")
        return bool(value)

    def to_dict(self) -> dict[str, bool | int]:
        """Return all capabilities as a dict."""
        return {f.name: getattr(self, f.name) for f in fields(self)}


# ---------------------------------------------------------------------------
# Capability matrix for all known connector types
# ---------------------------------------------------------------------------

CONNECTOR_CAPABILITIES: dict[str, ConnectorCapabilities] = {
    "pgvector": ConnectorCapabilities(
        supports_direct_ingestion=True,
        supports_batch_ingestion=True,
        supports_retroactive_registration=True,
        supports_search_config=True,
        supports_ingestion_config=True,
        supports_metadata_resolution_inline=True,
        supports_metadata_resolution_sidecar=True,
        supports_metadata_resolution_sql_view=True,
        supports_chunk_level_binding=True,
        supports_resource_level_binding=True,
        expected_max_readiness_level=4,
        supports_simulator=True,
        supports_audit_export=True,
    ),
    "pinecone": ConnectorCapabilities(
        supports_direct_ingestion=True,
        supports_batch_ingestion=True,
        supports_retroactive_registration=True,
        supports_search_config=True,
        supports_ingestion_config=True,
        supports_metadata_resolution_inline=True,
        supports_metadata_resolution_sidecar=True,
        supports_metadata_resolution_sql_view=False,
        supports_chunk_level_binding=True,
        supports_resource_level_binding=True,
        expected_max_readiness_level=4,
        supports_simulator=True,
        supports_audit_export=True,
    ),
    "weaviate": ConnectorCapabilities(
        supports_direct_ingestion=False,
        supports_batch_ingestion=False,
        supports_retroactive_registration=True,
        supports_search_config=True,
        supports_ingestion_config=False,
        supports_metadata_resolution_inline=True,
        supports_metadata_resolution_sidecar=True,
        supports_metadata_resolution_sql_view=False,
        supports_chunk_level_binding=False,
        supports_resource_level_binding=True,
        expected_max_readiness_level=3,
        supports_simulator=True,
        supports_audit_export=True,
    ),
    "milvus": ConnectorCapabilities(
        supports_direct_ingestion=False,
        supports_batch_ingestion=False,
        supports_retroactive_registration=True,
        supports_search_config=True,
        supports_ingestion_config=False,
        supports_metadata_resolution_inline=True,
        supports_metadata_resolution_sidecar=True,
        supports_metadata_resolution_sql_view=False,
        supports_chunk_level_binding=False,
        supports_resource_level_binding=True,
        expected_max_readiness_level=3,
        supports_simulator=True,
        supports_audit_export=True,
    ),
    "chroma": ConnectorCapabilities(
        supports_direct_ingestion=False,
        supports_batch_ingestion=False,
        supports_retroactive_registration=True,
        supports_search_config=True,
        supports_ingestion_config=False,
        supports_metadata_resolution_inline=True,
        supports_metadata_resolution_sidecar=True,
        supports_metadata_resolution_sql_view=False,
        supports_chunk_level_binding=False,
        supports_resource_level_binding=True,
        expected_max_readiness_level=3,
        supports_simulator=True,
        supports_audit_export=True,
    ),
    "qdrant": ConnectorCapabilities(
        supports_direct_ingestion=False,
        supports_batch_ingestion=False,
        supports_retroactive_registration=True,
        supports_search_config=True,
        supports_ingestion_config=False,
        supports_metadata_resolution_inline=True,
        supports_metadata_resolution_sidecar=True,
        supports_metadata_resolution_sql_view=False,
        supports_chunk_level_binding=False,
        supports_resource_level_binding=True,
        expected_max_readiness_level=3,
        supports_simulator=True,
        supports_audit_export=True,
    ),
    "opensearch": ConnectorCapabilities(
        supports_direct_ingestion=False,
        supports_batch_ingestion=False,
        supports_retroactive_registration=True,
        supports_search_config=True,
        supports_ingestion_config=False,
        supports_metadata_resolution_inline=True,
        supports_metadata_resolution_sidecar=True,
        supports_metadata_resolution_sql_view=False,
        supports_chunk_level_binding=False,
        supports_resource_level_binding=True,
        expected_max_readiness_level=3,
        supports_simulator=True,
        supports_audit_export=True,
    ),
    "supabase": ConnectorCapabilities(
        supports_direct_ingestion=True,
        supports_batch_ingestion=True,
        supports_retroactive_registration=True,
        supports_search_config=True,
        supports_ingestion_config=True,
        supports_metadata_resolution_inline=True,
        supports_metadata_resolution_sidecar=True,
        supports_metadata_resolution_sql_view=True,
        supports_chunk_level_binding=True,
        supports_resource_level_binding=True,
        expected_max_readiness_level=4,
        supports_simulator=True,
        supports_audit_export=True,
    ),
    "neon": ConnectorCapabilities(
        supports_direct_ingestion=True,
        supports_batch_ingestion=True,
        supports_retroactive_registration=True,
        supports_search_config=True,
        supports_ingestion_config=True,
        supports_metadata_resolution_inline=True,
        supports_metadata_resolution_sidecar=True,
        supports_metadata_resolution_sql_view=True,
        supports_chunk_level_binding=True,
        supports_resource_level_binding=True,
        expected_max_readiness_level=4,
        supports_simulator=True,
        supports_audit_export=True,
    ),
}


def get_capabilities(connector_type: str) -> ConnectorCapabilities | None:
    """Look up capabilities for a connector type. Returns None if unknown."""
    return CONNECTOR_CAPABILITIES.get(connector_type)


def check_capabilities(
    connector_type: str, required: list[str]
) -> tuple[bool, list[str]]:
    """Check if a connector meets all required capabilities.

    Returns (all_met, list_of_unmet_capability_names).
    """
    caps = CONNECTOR_CAPABILITIES.get(connector_type)
    if caps is None:
        return False, required

    unmet = [cap for cap in required if not caps.has_capability(cap)]
    return len(unmet) == 0, unmet
