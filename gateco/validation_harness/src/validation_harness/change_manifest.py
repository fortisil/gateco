"""Change manifest — structured mapping of failures to actionable fixes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from validation_harness.skip_taxonomy import FailureCategory


class ChangeEntry(BaseModel):
    """A single actionable change derived from a validation run."""

    category: Literal[
        "backend_bug", "sdk_gap", "harness_fix", "schema_mismatch", "doc_update"
    ]
    severity: Literal["blocking", "degraded", "cosmetic"]
    component: str
    description: str
    scenario_id: str | None = None
    failure_category: str | None = None
    connector_type: str | None = None
    evidence: str | None = None
    suggested_fix_area: str | None = None
    suggested_owner: str | None = None


class ChangeManifest(BaseModel):
    """Collection of change entries from a single validation run."""

    run_id: str
    connector_type: str
    profile: str
    provider_mode: str = "native"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    entries: list[ChangeEntry] = Field(default_factory=list)


# Conservative auto-derivation mapping: failure category -> change category
_DERIVATION_MAP: dict[FailureCategory, str] = {
    FailureCategory.UNEXPECTED_SCHEMA: "schema_mismatch",
    FailureCategory.SDK_ERROR: "sdk_gap",
    FailureCategory.HARNESS_BUG: "harness_fix",
}


def derive_entries_from_results(
    scenarios: list,
    connector_type: str,
) -> list[ChangeEntry]:
    """Auto-derive change entries from scenario results (conservative).

    Only derives from unambiguous failure categories:
    - UNEXPECTED_SCHEMA -> schema_mismatch
    - SDK_ERROR -> sdk_gap
    - HARNESS_BUG -> harness_fix
    - AUTH_ERROR -> backend_bug (only derivable with cross-connector context)
    """
    entries: list[ChangeEntry] = []
    for result in scenarios:
        if result.failure_category is None:
            continue

        # Normalize to enum if it's a string
        cat = result.failure_category
        if isinstance(cat, str):
            try:
                cat = FailureCategory(cat)
            except ValueError:
                continue

        change_cat = _DERIVATION_MAP.get(cat)
        if change_cat is None:
            continue

        entries.append(
            ChangeEntry(
                category=change_cat,
                severity="degraded",
                component=f"scenario/{result.scenario_id}",
                description=(
                    f"Scenario {result.scenario_id} ({result.scenario_name}) "
                    f"failed with {cat.value}"
                ),
                scenario_id=result.scenario_id,
                failure_category=cat.value,
                connector_type=connector_type,
            )
        )

    return entries


def write_change_manifest(manifest: ChangeManifest, output_dir: str) -> Path:
    """Write a change manifest to the run's output directory."""
    run_dir = Path(output_dir) / manifest.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    path = run_dir / "change_manifest.json"
    path.write_text(manifest.model_dump_json(indent=2))
    return path


def merge_manifests(manifests: list[ChangeManifest]) -> list[ChangeEntry]:
    """Merge entries from multiple manifests, deduplicating by scenario_id + category."""
    seen: set[tuple[str | None, str]] = set()
    merged: list[ChangeEntry] = []

    for m in manifests:
        for entry in m.entries:
            key = (entry.scenario_id, entry.category)
            if key not in seen:
                seen.add(key)
                merged.append(entry)

    return merged
