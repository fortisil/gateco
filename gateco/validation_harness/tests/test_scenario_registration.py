"""Tests that all real scenarios are registered correctly (including s18-s20)."""

from __future__ import annotations

import validation_harness.scenarios  # noqa: F401 — triggers registration
from validation_harness.registry import get_registry, topological_sort


class TestAllScenariosRegistered:
    def test_new_scenarios_registered(self):
        registry = get_registry()
        for sid in ("s18_idp_lifecycle", "s19_principal_policies", "s20_principal_retrieval"):
            assert sid in registry, f"{sid} not found in registry: {sorted(registry.keys())}"

    def test_s18_idp_lifecycle_registered(self):
        registry = get_registry()
        assert "s18_idp_lifecycle" in registry
        defn = registry["s18_idp_lifecycle"]
        assert defn.feature_area == "identity_providers"
        assert defn.depends_on == ["s01_auth"]

    def test_s19_principal_policies_registered(self):
        registry = get_registry()
        assert "s19_principal_policies" in registry
        defn = registry["s19_principal_policies"]
        assert defn.feature_area == "policies"
        assert "s18_idp_lifecycle" in defn.depends_on
        assert "s02_connector_lifecycle" in defn.depends_on

    def test_s19_cascading_skip_on_idp(self):
        registry = get_registry()
        defn = registry["s19_principal_policies"]
        assert "s18_idp_lifecycle" in defn.skip_when_dependency_skipped

    def test_s20_principal_retrieval_registered(self):
        registry = get_registry()
        assert "s20_principal_retrieval" in registry
        defn = registry["s20_principal_retrieval"]
        assert defn.feature_area == "retrievals"
        assert "s19_principal_policies" in defn.depends_on
        assert "s05_ingest_batch" in defn.skip_when_dependency_skipped
        assert "s18_idp_lifecycle" in defn.skip_when_dependency_skipped

    def test_topological_order_s18_before_s19_before_s20(self):
        registry = get_registry()
        ids = list(registry.keys())
        ordered = topological_sort(ids)
        assert ordered.index("s18_idp_lifecycle") < ordered.index("s19_principal_policies")
        assert ordered.index("s19_principal_policies") < ordered.index("s20_principal_retrieval")
