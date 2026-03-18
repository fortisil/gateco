"""Tests for connector capability matrix lookups and skip resolution."""

from __future__ import annotations

import pytest

from validation_harness.capabilities import (
    CONNECTOR_CAPABILITIES,
    ConnectorCapabilities,
    check_capabilities,
    get_capabilities,
)
from validation_harness.connector_defaults import (
    CONNECTOR_INGESTION_CONFIG_DEFAULTS,
    CONNECTOR_SEARCH_CONFIG_DEFAULTS,
)


class TestConnectorCapabilities:
    def test_pgvector_full_support(self):
        caps = get_capabilities("pgvector")
        assert caps is not None
        assert caps.supports_direct_ingestion is True
        assert caps.supports_batch_ingestion is True
        assert caps.supports_metadata_resolution_sql_view is True
        assert caps.expected_max_readiness_level == 4

    def test_weaviate_no_ingestion(self):
        caps = get_capabilities("weaviate")
        assert caps is not None
        assert caps.supports_direct_ingestion is False
        assert caps.supports_batch_ingestion is False
        assert caps.supports_retroactive_registration is True

    def test_pinecone_no_sql_view(self):
        caps = get_capabilities("pinecone")
        assert caps is not None
        assert caps.supports_metadata_resolution_sql_view is False

    def test_unknown_connector(self):
        caps = get_capabilities("unknown_db")
        assert caps is None

    def test_has_capability(self):
        caps = get_capabilities("pgvector")
        assert caps.has_capability("supports_direct_ingestion") is True
        assert caps.has_capability("supports_metadata_resolution_sql_view") is True

    def test_has_capability_unknown(self):
        caps = get_capabilities("pgvector")
        with pytest.raises(ValueError, match="Unknown capability"):
            caps.has_capability("nonexistent_cap")

    def test_to_dict(self):
        caps = get_capabilities("pgvector")
        d = caps.to_dict()
        assert isinstance(d, dict)
        assert "supports_direct_ingestion" in d
        assert "expected_max_readiness_level" in d


class TestCheckCapabilities:
    def test_all_met(self):
        met, unmet = check_capabilities(
            "pgvector", ["supports_direct_ingestion", "supports_search_config"]
        )
        assert met is True
        assert unmet == []

    def test_some_unmet(self):
        met, unmet = check_capabilities(
            "weaviate", ["supports_direct_ingestion", "supports_search_config"]
        )
        assert met is False
        assert "supports_direct_ingestion" in unmet

    def test_unknown_connector(self):
        met, unmet = check_capabilities(
            "unknown_db", ["supports_direct_ingestion"]
        )
        assert met is False
        assert unmet == ["supports_direct_ingestion"]

    def test_empty_requirements(self):
        met, unmet = check_capabilities("pgvector", [])
        assert met is True
        assert unmet == []


class TestAllConnectorsPresent:
    def test_known_connectors(self):
        expected = {
            "pgvector", "pinecone", "weaviate", "milvus", "chroma",
            "qdrant", "opensearch", "supabase", "neon",
        }
        assert set(CONNECTOR_CAPABILITIES.keys()) == expected

    def test_all_have_readiness_level(self):
        for name, caps in CONNECTOR_CAPABILITIES.items():
            assert caps.expected_max_readiness_level >= 0, f"{name} missing readiness"
            assert caps.expected_max_readiness_level <= 4, f"{name} readiness > 4"

    def test_capability_keys_match_backend_enum(self):
        """Ensure harness capability matrix stays in sync with backend ConnectorType enum."""
        import sys
        from pathlib import Path

        # Add backend source to path for import
        backend_src = Path(__file__).resolve().parents[3] / "apps" / "backend" / "src"
        sys.path.insert(0, str(backend_src))
        try:
            from gateco.database.enums import ConnectorType
            backend_types = {e.value for e in ConnectorType}
            harness_types = set(CONNECTOR_CAPABILITIES.keys())
            assert harness_types == backend_types, (
                f"Mismatch — harness has {harness_types - backend_types} extra, "
                f"missing {backend_types - harness_types}"
            )
        finally:
            sys.path.pop(0)


class TestReadinessFieldsParity:
    """Verify readiness fields are present across all three layers (backend, SDK, harness)."""

    def test_readiness_fields_present_across_layers(self):
        """Assert the 3-layer contract: backend schema → SDK model → s15 reads directly."""
        import sys
        from pathlib import Path

        # Check backend ConnectorResponse has policy_readiness_level
        backend_src = Path(__file__).resolve().parents[3] / "apps" / "backend" / "src"
        sys.path.insert(0, str(backend_src))
        try:
            from gateco.schemas.connectors import ConnectorResponse
            assert "policy_readiness_level" in ConnectorResponse.model_fields, (
                "ConnectorResponse missing policy_readiness_level field"
            )
        finally:
            sys.path.pop(0)

        # Check SDK Connector model accepts policy_readiness_level
        from gateco_sdk.types.connectors import Connector
        test_data = {
            "id": "test",
            "name": "test",
            "type": "pgvector",
            "policy_readiness_level": 2,
        }
        c = Connector.model_validate(test_data)
        assert c.policy_readiness_level == 2, (
            "SDK Connector model does not preserve policy_readiness_level"
        )

        # Check s15 reads policy_readiness_level directly (no hasattr fallback)
        import inspect
        from validation_harness.scenarios.s15_coverage_readiness import (
            s15_coverage_readiness,
        )
        source = inspect.getsource(s15_coverage_readiness)
        assert "hasattr" not in source, (
            "s15 still uses hasattr fallback for readiness — should read directly"
        )
        assert "policy_readiness_level" in source, (
            "s15 does not reference policy_readiness_level"
        )


class TestConnectorDefaultsParity:
    """Verify connector_defaults covers all capability matrix entries and backend fields."""

    def test_search_defaults_cover_all_capabilities(self):
        """Every connector in CONNECTOR_CAPABILITIES must have search config defaults."""
        for connector_type in CONNECTOR_CAPABILITIES:
            assert connector_type in CONNECTOR_SEARCH_CONFIG_DEFAULTS, (
                f"Missing search config defaults for {connector_type}"
            )

    def test_ingestion_defaults_cover_ingestion_capable(self):
        """Every connector with supports_direct_ingestion must have ingestion defaults."""
        for connector_type, caps in CONNECTOR_CAPABILITIES.items():
            if caps.supports_direct_ingestion:
                assert connector_type in CONNECTOR_INGESTION_CONFIG_DEFAULTS, (
                    f"Missing ingestion config defaults for {connector_type} "
                    f"(supports_direct_ingestion=True)"
                )

    def test_search_defaults_contain_backend_required_fields(self):
        """Each search config default must include all backend-required fields."""
        import sys
        from pathlib import Path

        backend_src = Path(__file__).resolve().parents[3] / "apps" / "backend" / "src"
        sys.path.insert(0, str(backend_src))
        try:
            from gateco.schemas.connectors import SEARCH_CONFIG_REQUIRED_FIELDS

            for connector_type, defaults in CONNECTOR_SEARCH_CONFIG_DEFAULTS.items():
                required = SEARCH_CONFIG_REQUIRED_FIELDS.get(connector_type, [])
                for field in required:
                    assert field in defaults, (
                        f"Search config defaults for {connector_type} missing "
                        f"required field '{field}'"
                    )
        finally:
            sys.path.pop(0)
