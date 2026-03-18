"""Combined CI summary generator — single artifact for multi-connector runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from validation_harness.change_manifest import ChangeManifest


class ProfileSummary(BaseModel):
    """Summary of a single connector profile run."""

    connector: str
    provider_mode: str = "native"
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errored: int = 0
    run_id: str | None = None


class CISummary(BaseModel):
    """Combined CI summary across all connector profiles."""

    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    profiles: list[ProfileSummary] = Field(default_factory=list)
    regressions: list[str] = Field(default_factory=list)
    change_manifest_total: int = 0
    blocking_changes: int = 0


def generate_ci_summary(output_dir: str) -> CISummary:
    """Scan output directory for run results and build a combined CI summary."""
    output_path = Path(output_dir)
    summary = CISummary()

    if not output_path.exists():
        return summary

    # Collect all run results
    run_dirs = sorted(output_path.glob("run-*"))
    for run_dir in run_dirs:
        result_file = run_dir / "run_result.json"
        if not result_file.exists():
            continue

        try:
            data = json.loads(result_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        # Read profile config to get provider_mode
        provider_mode = "native"
        manifest_file = run_dir / "change_manifest.json"
        if manifest_file.exists():
            try:
                manifest_data = json.loads(manifest_file.read_text())
                manifest = ChangeManifest.model_validate(manifest_data)
                provider_mode = manifest.provider_mode
                summary.change_manifest_total += len(manifest.entries)
                summary.blocking_changes += sum(
                    1 for e in manifest.entries if e.severity == "blocking"
                )
            except Exception:
                pass

        profile = ProfileSummary(
            connector=data.get("connector_type", "unknown"),
            provider_mode=provider_mode,
            passed=data.get("passed", 0),
            failed=data.get("failed", 0),
            skipped=data.get("skipped", 0),
            errored=data.get("errored", 0),
            run_id=data.get("run_id"),
        )
        summary.profiles.append(profile)

        # Check for regressions
        regression = data.get("regression_summary")
        if regression and regression.get("newly_failed"):
            for sid in regression["newly_failed"]:
                summary.regressions.append(
                    f"{profile.connector}: {sid}"
                )

    return summary


def write_ci_summary(summary: CISummary, output_dir: str) -> tuple[Path, Path]:
    """Write CI summary as both JSON and Markdown. Returns (json_path, md_path)."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # JSON
    json_path = output_path / "ci_connector_summary.json"
    json_path.write_text(summary.model_dump_json(indent=2))

    # Markdown
    md_path = output_path / "ci_connector_summary.md"
    lines = [
        "# CI Connector Validation Summary",
        "",
        f"Generated: {summary.generated_at.isoformat()}",
        "",
        "## Connector Results",
        "",
        "| Connector | Mode | Passed | Failed | Skipped | Errored |",
        "|-----------|------|--------|--------|---------|---------|",
    ]

    for p in summary.profiles:
        lines.append(
            f"| {p.connector} | {p.provider_mode} | {p.passed} | "
            f"{p.failed} | {p.skipped} | {p.errored} |"
        )

    lines.append("")

    if summary.regressions:
        lines.append("## Regressions")
        lines.append("")
        for r in summary.regressions:
            lines.append(f"- {r}")
        lines.append("")

    lines.append("## Change Manifest")
    lines.append("")
    lines.append(f"- Total entries: {summary.change_manifest_total}")
    lines.append(f"- Blocking: {summary.blocking_changes}")
    lines.append("")

    md_path.write_text("\n".join(lines))
    return json_path, md_path
