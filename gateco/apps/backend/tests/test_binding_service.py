"""Tests for binding service — bulk metadata binding."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from gateco.database.enums import Classification, ConnectorStatus, ResourceType, Sensitivity
from gateco.schemas.bindings import BindingEntry
from gateco.services.binding_service import (
    _check_metadata_consistency,
    bind_metadata,
    compute_policy_readiness,
    get_coverage_detail,
)


# ============================================================================
# compute_policy_readiness unit tests
# ============================================================================


class TestPolicyReadiness:
    """Tests for capability-based policy readiness levels (L0-L4).

    L0: Not Ready — connector not reachable
    L1: Connection Ready — DB reachable, auth valid
    L2: Search Ready / Coarse Policy — can search, connector/namespace-level controls
    L3: Resource Policy Ready — resource-level metadata resolution + policy active
    L4: Chunk Policy Ready — chunk/vector-level metadata in policy evaluation
    """

    def test_l0_not_connected(self):
        assert compute_policy_readiness(False, False, None) == 0
        assert compute_policy_readiness(False, True, 50.0) == 0
        # Even with all capabilities, no connection means L0
        assert compute_policy_readiness(
            False, True, 80.0,
            has_active_policies=True,
            has_resource_level_bindings=True,
            has_chunk_level_policy_metadata=True,
        ) == 0

    def test_l1_connected_no_search(self):
        assert compute_policy_readiness(True, False, None) == 1

    def test_l2_search_ready_no_policies(self):
        # Connected + search ready but no active policies => L2
        assert compute_policy_readiness(True, True, None) == 2
        assert compute_policy_readiness(True, True, 0) == 2
        assert compute_policy_readiness(True, True, 50.0) == 2
        # Search ready but missing resource bindings => L2
        assert compute_policy_readiness(
            True, True, 80.0,
            has_active_policies=True,
            has_resource_level_bindings=False,
        ) == 2

    def test_l3_resource_policy_ready(self):
        # Active policies + resource-level bindings => L3
        assert compute_policy_readiness(
            True, True, 80.0,
            has_active_policies=True,
            has_resource_level_bindings=True,
        ) == 3
        assert compute_policy_readiness(
            True, True, 100.0,
            has_active_policies=True,
            has_resource_level_bindings=True,
            has_chunk_level_policy_metadata=False,
        ) == 3

    def test_l4_chunk_policy_ready(self):
        # Full capability: chunk-level policy metadata => L4
        assert compute_policy_readiness(
            True, True, 100.0,
            has_active_policies=True,
            has_resource_level_bindings=True,
            has_chunk_level_policy_metadata=True,
        ) == 4


# ============================================================================
# _check_metadata_consistency unit tests
# ============================================================================


class TestMetadataConsistency:
    def test_single_entry_accepted(self):
        entry = BindingEntry(
            vector_id="v1",
            external_resource_id="r1",
            classification="public",
        )
        meta, err = _check_metadata_consistency([entry])
        assert err is None
        assert meta["classification"] == "public"

    def test_consistent_metadata_accepted(self):
        entries = [
            BindingEntry(vector_id="v1", external_resource_id="r1", classification="public"),
            BindingEntry(vector_id="v2", external_resource_id="r1", classification="public"),
        ]
        meta, err = _check_metadata_consistency(entries)
        assert err is None
        assert meta["classification"] == "public"

    def test_conflicting_classification_rejected(self):
        entries = [
            BindingEntry(vector_id="v1", external_resource_id="r1", classification="public"),
            BindingEntry(vector_id="v2", external_resource_id="r1", classification="internal"),
        ]
        _, err = _check_metadata_consistency(entries)
        assert err is not None
        assert "conflicting classification" in err

    def test_conflicting_sensitivity_rejected(self):
        entries = [
            BindingEntry(vector_id="v1", external_resource_id="r1", sensitivity="low"),
            BindingEntry(vector_id="v2", external_resource_id="r1", sensitivity="high"),
        ]
        _, err = _check_metadata_consistency(entries)
        assert err is not None
        assert "conflicting sensitivity" in err

    def test_conflicting_domain_rejected(self):
        entries = [
            BindingEntry(vector_id="v1", external_resource_id="r1", domain="finance"),
            BindingEntry(vector_id="v2", external_resource_id="r1", domain="legal"),
        ]
        _, err = _check_metadata_consistency(entries)
        assert err is not None
        assert "conflicting domain" in err

    def test_conflicting_labels_rejected(self):
        entries = [
            BindingEntry(vector_id="v1", external_resource_id="r1", labels=["a"]),
            BindingEntry(vector_id="v2", external_resource_id="r1", labels=["b"]),
        ]
        _, err = _check_metadata_consistency(entries)
        assert err is not None
        assert "conflicting labels" in err

    def test_null_and_value_accepted(self):
        entries = [
            BindingEntry(vector_id="v1", external_resource_id="r1", classification=None),
            BindingEntry(vector_id="v2", external_resource_id="r1", classification="public"),
        ]
        meta, err = _check_metadata_consistency(entries)
        assert err is None
        assert meta["classification"] == "public"

    def test_all_null_accepted(self):
        entries = [
            BindingEntry(vector_id="v1", external_resource_id="r1"),
            BindingEntry(vector_id="v2", external_resource_id="r1"),
        ]
        meta, err = _check_metadata_consistency(entries)
        assert err is None
        assert meta["classification"] is None

    def test_invalid_classification_rejected(self):
        entries = [
            BindingEntry(vector_id="v1", external_resource_id="r1", classification="top_secret"),
        ]
        _, err = _check_metadata_consistency(entries)
        assert err is not None
        assert "invalid classification" in err

    def test_invalid_sensitivity_rejected(self):
        entries = [
            BindingEntry(vector_id="v1", external_resource_id="r1", sensitivity="extreme"),
        ]
        _, err = _check_metadata_consistency(entries)
        assert err is not None
        assert "invalid sensitivity" in err


# ============================================================================
# BindRequest validation (Pydantic)
# ============================================================================


class TestBindRequestValidation:
    def test_max_batch_size_enforced(self):
        from pydantic import ValidationError as PydanticValidationError
        from gateco.schemas.bindings import BindRequest

        # 5001 entries should fail
        entries = [
            {"vector_id": f"v{i}", "external_resource_id": f"r{i}"}
            for i in range(5001)
        ]
        with pytest.raises(PydanticValidationError):
            BindRequest(bindings=entries)

    def test_empty_bindings_rejected(self):
        from pydantic import ValidationError as PydanticValidationError
        from gateco.schemas.bindings import BindRequest

        with pytest.raises(PydanticValidationError):
            BindRequest(bindings=[])

    def test_valid_batch_accepted(self):
        from gateco.schemas.bindings import BindRequest

        entries = [
            {"vector_id": "v1", "external_resource_id": "r1"},
            {"vector_id": "v2", "external_resource_id": "r1"},
        ]
        req = BindRequest(bindings=entries)
        assert len(req.bindings) == 2
