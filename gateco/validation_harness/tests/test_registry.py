"""Tests for scenario registration and topological sort."""

from __future__ import annotations

import pytest

from validation_harness.registry import (
    ScenarioDefinition,
    _REGISTRY,
    scenario,
    get_registry,
    topological_sort,
)


@pytest.fixture(autouse=True)
def clean_registry():
    """Clear registry before/after each test."""
    saved = dict(_REGISTRY)
    _REGISTRY.clear()
    yield
    _REGISTRY.clear()
    _REGISTRY.update(saved)


class TestScenarioDecorator:
    def test_registers_scenario(self):
        @scenario(id="test_a", name="Test A", feature_area="test")
        async def my_scenario(ctx):
            pass

        registry = get_registry()
        assert "test_a" in registry
        assert registry["test_a"].name == "Test A"
        assert registry["test_a"].fn is my_scenario

    def test_duplicate_id_raises(self):
        @scenario(id="dup", name="First", feature_area="test")
        async def first(ctx):
            pass

        with pytest.raises(ValueError, match="Duplicate scenario id"):
            @scenario(id="dup", name="Second", feature_area="test")
            async def second(ctx):
                pass

    def test_with_dependencies(self):
        @scenario(
            id="dep_a", name="A", feature_area="test",
            depends_on=["dep_b"],
            requires_capabilities=["supports_direct_ingestion"],
        )
        async def a(ctx):
            pass

        defn = get_registry()["dep_a"]
        assert defn.depends_on == ["dep_b"]
        assert defn.requires_capabilities == ["supports_direct_ingestion"]


class TestTopologicalSort:
    def test_no_deps(self):
        _REGISTRY["a"] = ScenarioDefinition(
            id="a", name="A", feature_area="test",
            fn=lambda ctx: None, depends_on=[],
        )
        _REGISTRY["b"] = ScenarioDefinition(
            id="b", name="B", feature_area="test",
            fn=lambda ctx: None, depends_on=[],
        )
        result = topological_sort(["a", "b"])
        assert set(result) == {"a", "b"}

    def test_linear_chain(self):
        _REGISTRY["c"] = ScenarioDefinition(
            id="c", name="C", feature_area="test",
            fn=lambda ctx: None, depends_on=["b"],
        )
        _REGISTRY["b"] = ScenarioDefinition(
            id="b", name="B", feature_area="test",
            fn=lambda ctx: None, depends_on=["a"],
        )
        _REGISTRY["a"] = ScenarioDefinition(
            id="a", name="A", feature_area="test",
            fn=lambda ctx: None, depends_on=[],
        )
        result = topological_sort(["a", "b", "c"])
        assert result.index("a") < result.index("b") < result.index("c")

    def test_diamond_deps(self):
        _REGISTRY["d"] = ScenarioDefinition(
            id="d", name="D", feature_area="test",
            fn=lambda ctx: None, depends_on=["b", "c"],
        )
        _REGISTRY["b"] = ScenarioDefinition(
            id="b", name="B", feature_area="test",
            fn=lambda ctx: None, depends_on=["a"],
        )
        _REGISTRY["c"] = ScenarioDefinition(
            id="c", name="C", feature_area="test",
            fn=lambda ctx: None, depends_on=["a"],
        )
        _REGISTRY["a"] = ScenarioDefinition(
            id="a", name="A", feature_area="test",
            fn=lambda ctx: None, depends_on=[],
        )
        result = topological_sort(["a", "b", "c", "d"])
        assert result.index("a") < result.index("b")
        assert result.index("a") < result.index("c")
        assert result.index("b") < result.index("d")
        assert result.index("c") < result.index("d")

    def test_cycle_detection(self):
        _REGISTRY["x"] = ScenarioDefinition(
            id="x", name="X", feature_area="test",
            fn=lambda ctx: None, depends_on=["y"],
        )
        _REGISTRY["y"] = ScenarioDefinition(
            id="y", name="Y", feature_area="test",
            fn=lambda ctx: None, depends_on=["x"],
        )
        with pytest.raises(ValueError, match="cycle"):
            topological_sort(["x", "y"])

    def test_external_dep_ignored(self):
        """Dependencies not in the candidate set are ignored."""
        _REGISTRY["solo"] = ScenarioDefinition(
            id="solo", name="Solo", feature_area="test",
            fn=lambda ctx: None, depends_on=["external"],
        )
        result = topological_sort(["solo"])
        assert result == ["solo"]
