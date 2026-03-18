"""Scenario registration via @scenario decorator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

# Type alias for scenario functions
ScenarioFn = Callable[..., Coroutine[Any, Any, None]]


@dataclass
class ScenarioDefinition:
    """Metadata for a registered scenario."""

    id: str
    name: str
    feature_area: str
    fn: ScenarioFn
    depends_on: list[str] = field(default_factory=list)
    requires_capabilities: list[str] = field(default_factory=list)
    requires_entitlements: list[str] = field(default_factory=list)
    requires_features: list[str] = field(default_factory=list)
    skip_when_dependency_skipped: list[str] = field(default_factory=list)


# Global registry
_REGISTRY: dict[str, ScenarioDefinition] = {}


def scenario(
    *,
    id: str,
    name: str,
    feature_area: str,
    depends_on: list[str] | None = None,
    requires_capabilities: list[str] | None = None,
    requires_entitlements: list[str] | None = None,
    requires_features: list[str] | None = None,
    skip_when_dependency_skipped: list[str] | None = None,
) -> Callable[[ScenarioFn], ScenarioFn]:
    """Decorator to register a scenario function."""

    def decorator(fn: ScenarioFn) -> ScenarioFn:
        defn = ScenarioDefinition(
            id=id,
            name=name,
            feature_area=feature_area,
            fn=fn,
            depends_on=depends_on or [],
            requires_capabilities=requires_capabilities or [],
            requires_entitlements=requires_entitlements or [],
            requires_features=requires_features or [],
            skip_when_dependency_skipped=skip_when_dependency_skipped or [],
        )
        if id in _REGISTRY:
            raise ValueError(f"Duplicate scenario id: {id}")
        _REGISTRY[id] = defn
        return fn

    return decorator


def get_registry() -> dict[str, ScenarioDefinition]:
    """Return the global scenario registry (read-only view)."""
    return dict(_REGISTRY)


def get_scenario(scenario_id: str) -> ScenarioDefinition | None:
    """Look up a scenario by ID."""
    return _REGISTRY.get(scenario_id)


def topological_sort(
    scenario_ids: list[str],
) -> list[str]:
    """Topological sort of scenario IDs by depends_on.

    Returns ordered list. Raises ValueError on cycles.
    """
    id_set = set(scenario_ids)
    visited: set[str] = set()
    temp: set[str] = set()
    result: list[str] = []

    def visit(sid: str) -> None:
        if sid in visited:
            return
        if sid in temp:
            raise ValueError(f"Dependency cycle detected involving: {sid}")
        temp.add(sid)

        defn = _REGISTRY.get(sid)
        if defn:
            for dep in defn.depends_on:
                if dep in id_set:
                    visit(dep)

        temp.discard(sid)
        visited.add(sid)
        result.append(sid)

    for sid in scenario_ids:
        visit(sid)

    return result
