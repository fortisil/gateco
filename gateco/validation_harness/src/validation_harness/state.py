"""Cumulative coverage matrix manager — persists across runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from validation_harness.models import (
    CombinationStatus,
    ConnectorStatus,
    CumulativeStatus,
    FeatureStatus,
    IDPStatus,
    RunResult,
    RunSummary,
)

_MAX_RECENT_RUNS = 50


class CoverageManager:
    """Manages cumulative coverage state across validation runs."""

    def __init__(self, output_dir: str) -> None:
        self.output_dir = Path(output_dir)
        self.status_path = self.output_dir / "cumulative_status.json"

    def load(self) -> CumulativeStatus:
        """Load cumulative status from disk, or return empty state."""
        if not self.status_path.exists():
            return CumulativeStatus(last_updated=datetime.now(timezone.utc))

        raw = json.loads(self.status_path.read_text())
        return CumulativeStatus.model_validate(raw)

    def save(self, status: CumulativeStatus) -> None:
        """Save cumulative status to disk."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.status_path.write_text(
            status.model_dump_json(indent=2)
        )

    def update_from_run(self, run: RunResult) -> CumulativeStatus:
        """Update cumulative state from a completed run."""
        status = self.load()
        status.last_updated = datetime.now(timezone.utc)

        # Update feature statuses
        for area, area_status in run.feature_rollup.items():
            feat = status.features.get(area, FeatureStatus())

            if area_status == "passed":
                feat.status = "pass"
            elif area_status == "failed":
                feat.status = "fail"
            elif area_status == "partial":
                feat.status = "partial"

            if run.connector_type not in feat.tested_connectors:
                feat.tested_connectors.append(run.connector_type)
            feat.last_run = run.run_id
            status.features[area] = feat

        # Update connector status
        conn = status.connectors.get(
            run.connector_type, ConnectorStatus()
        )
        all_passed = all(
            s.status == "passed" for s in run.scenarios if s.status != "skipped"
        )
        any_failed = any(
            s.status in ("failed", "error") for s in run.scenarios
        )

        if all_passed:
            conn.status = "pass"
        elif any_failed and any(s.status == "passed" for s in run.scenarios):
            conn.status = "partial"
        elif any_failed:
            conn.status = "fail"

        conn.last_run_id = run.run_id
        if run.readiness_final is not None:
            if conn.best_readiness is None or run.readiness_final > conn.best_readiness:
                conn.best_readiness = run.readiness_final
        status.connectors[run.connector_type] = conn

        # Update IDP status (Phase 1: local only)
        idp_key = "local"
        idp = status.identity_providers.get(idp_key, IDPStatus())
        idp.status = "pass" if all_passed else "partial" if any_failed else "fail"
        idp.last_run_id = run.run_id
        status.identity_providers[idp_key] = idp

        # Update combination status (connector + IDP)
        combo_key = f"{run.connector_type}+{idp_key}"
        combo = status.combinations.get(combo_key, CombinationStatus())
        combo.status = "pass" if all_passed else "partial" if any_failed else "fail"
        combo.last_run_id = run.run_id
        status.combinations[combo_key] = combo

        # Add run summary
        summary = RunSummary(
            run_id=run.run_id,
            timestamp=run.started_at,
            profile=run.profile,
            connector_type=run.connector_type,
            target_url=run.target_url,
            total=run.total,
            passed=run.passed,
            failed=run.failed,
            skipped=run.skipped,
            readiness_final=run.readiness_final,
            duration_ms=run.duration_ms,
        )
        status.recent_runs.append(summary)
        if len(status.recent_runs) > _MAX_RECENT_RUNS:
            status.recent_runs = status.recent_runs[-_MAX_RECENT_RUNS:]

        self.save(status)
        return status
