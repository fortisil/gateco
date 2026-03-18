"""Markdown report generation."""

from __future__ import annotations

from pathlib import Path

from validation_harness.models import CumulativeStatus, RunResult


def write_markdown_report(
    result: RunResult,
    output_dir: str,
    cumulative: CumulativeStatus | None = None,
) -> Path:
    """Generate a full markdown report.

    Returns path to the written file.
    """
    run_dir = Path(output_dir) / result.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    _section_executive_summary(lines, result)
    _section_target_stack(lines, result)
    _section_scenario_results(lines, result)
    _section_feature_rollup(lines, result)
    _section_readiness(lines, result)
    _section_compatibility(lines, result)
    _section_regression(lines, result)
    _section_cumulative_coverage(lines, cumulative)
    _section_evidence_paths(lines, result)

    report_path = run_dir / "report.md"
    report_path.write_text("\n".join(lines))
    return report_path


def _section_executive_summary(lines: list[str], result: RunResult) -> None:
    lines.append("# Gateco Validation Report")
    lines.append("")
    lines.append("## A. Executive Summary")
    lines.append("")

    status = "PASS" if result.failed == 0 and result.errored == 0 else "FAIL"
    lines.append(f"**Overall Status:** {status}")
    lines.append(f"**Run ID:** `{result.run_id}`")
    lines.append(f"**Duration:** {result.duration_ms:.0f}ms")
    lines.append("")
    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total | {result.total} |")
    lines.append(f"| Passed | {result.passed} |")
    lines.append(f"| Failed | {result.failed} |")
    lines.append(f"| Skipped | {result.skipped} |")
    lines.append(f"| Errored | {result.errored} |")
    lines.append("")

    if result.failed > 0 or result.errored > 0:
        lines.append("**Key failures:**")
        for s in result.scenarios:
            if s.status in ("failed", "error"):
                cat = s.failure_category.value if s.failure_category else "unknown"
                lines.append(f"- `{s.scenario_id}` — {s.scenario_name} ({cat})")
        lines.append("")


def _section_target_stack(lines: list[str], result: RunResult) -> None:
    lines.append("## B. Target Stack")
    lines.append("")
    lines.append(f"- **Profile:** {result.profile}")
    lines.append(f"- **Target URL:** {result.target_url}")
    lines.append(f"- **Connector:** {result.connector_type}")
    lines.append(f"- **IDP:** local (Phase 1)")
    lines.append("")


def _section_scenario_results(lines: list[str], result: RunResult) -> None:
    lines.append("## C. Scenario Results")
    lines.append("")
    lines.append("| Scenario | Feature | Status | Duration | Category | Notes |")
    lines.append("|----------|---------|--------|----------|----------|-------|")

    for s in result.scenarios:
        notes = ""
        if s.skip_reason:
            notes = s.skip_reason.value
        cat = s.failure_category.value if s.failure_category else "-"
        dur = f"{s.duration_ms:.0f}ms" if s.duration_ms else "-"
        lines.append(
            f"| `{s.scenario_id}` | {s.feature_area} | {s.status} | {dur} | {cat} | {notes} |"
        )
    lines.append("")


def _section_feature_rollup(lines: list[str], result: RunResult) -> None:
    lines.append("## D. Feature Rollup")
    lines.append("")
    if not result.feature_rollup:
        lines.append("No feature data.")
        lines.append("")
        return

    lines.append("| Feature Area | Status |")
    lines.append("|-------------|--------|")
    for area, status in sorted(result.feature_rollup.items()):
        lines.append(f"| {area} | {status} |")
    lines.append("")


def _section_readiness(lines: list[str], result: RunResult) -> None:
    lines.append("## E. Readiness Assessment")
    lines.append("")
    initial = result.readiness_initial or 0
    final = result.readiness_final or 0
    expected_max = result.readiness_expected_max or "N/A"
    expected_min = result.readiness_expected_min
    lines.append(f"- **Initial:** L{initial}")
    lines.append(f"- **Final:** L{final}")
    lines.append(f"- **Expected Max:** L{expected_max}")
    if expected_min is not None:
        lines.append(f"- **Expected Min:** L{expected_min}")
    lines.append("")
    if isinstance(expected_max, int) and final < expected_max:
        lines.append(
            f"**Gap:** Achieved L{final}, expected max L{expected_max}."
        )
        if result.readiness_gap_reason:
            lines.append(f"**Reason:** {result.readiness_gap_reason}")
        else:
            lines.append(
                "Check connector capabilities and policy configuration."
            )
        lines.append("")


def _section_compatibility(lines: list[str], result: RunResult) -> None:
    lines.append("## F. Compatibility Notes")
    lines.append("")
    skipped = [s for s in result.scenarios if s.status == "skipped"]
    if not skipped:
        lines.append("All scenarios executed (no expected skips).")
    else:
        lines.append("| Scenario | Reason |")
        lines.append("|----------|--------|")
        for s in skipped:
            reason = s.skip_reason.value if s.skip_reason else "unknown"
            lines.append(f"| `{s.scenario_id}` | {reason} |")
    lines.append("")


def _section_regression(lines: list[str], result: RunResult) -> None:
    lines.append("## G. Regression Comparison")
    lines.append("")
    if not result.regression_summary:
        lines.append("No baseline available for comparison.")
        lines.append("")
        return

    reg = result.regression_summary
    lines.append(f"**Compared to:** `{reg.compared_to_run_id}`")
    lines.append("")
    if reg.newly_failed:
        lines.append(f"**Newly failed ({len(reg.newly_failed)}):**")
        for sid in reg.newly_failed:
            lines.append(f"- `{sid}`")
        lines.append("")
    if reg.newly_passed:
        lines.append(f"**Newly passed ({len(reg.newly_passed)}):**")
        for sid in reg.newly_passed:
            lines.append(f"- `{sid}`")
        lines.append("")
    lines.append(
        f"Unchanged pass: {len(reg.unchanged_pass)}, "
        f"Unchanged fail: {len(reg.unchanged_fail)}"
    )
    lines.append("")


def _section_cumulative_coverage(
    lines: list[str], cumulative: CumulativeStatus | None
) -> None:
    lines.append("## H. Cumulative Gateco Coverage")
    lines.append("")
    if cumulative is None:
        lines.append("No cumulative data available.")
        lines.append("")
        return

    # Connectors
    lines.append("### Connectors")
    lines.append("| Connector | Status | Best Readiness |")
    lines.append("|-----------|--------|---------------|")
    for name, cs in sorted(cumulative.connectors.items()):
        readiness = f"L{cs.best_readiness}" if cs.best_readiness is not None else "-"
        lines.append(f"| {name} | {cs.status} | {readiness} |")
    lines.append("")

    # Features
    lines.append("### Features")
    lines.append("| Feature | Status | Tested Connectors |")
    lines.append("|---------|--------|-------------------|")
    for name, fs in sorted(cumulative.features.items()):
        connectors = ", ".join(fs.tested_connectors) if fs.tested_connectors else "-"
        lines.append(f"| {name} | {fs.status} | {connectors} |")
    lines.append("")

    # IDPs
    lines.append("### Identity Providers")
    lines.append("| IDP | Status |")
    lines.append("|-----|--------|")
    for name, idp in sorted(cumulative.identity_providers.items()):
        lines.append(f"| {name} | {idp.status} |")
    lines.append("")


def _section_evidence_paths(lines: list[str], result: RunResult) -> None:
    lines.append("## I. Evidence Paths")
    lines.append("")
    lines.append(f"- JSON report: `{result.run_id}/run_result.json`")
    lines.append(f"- Cleanup manifest: `{result.run_id}/created_resources.json`")
    if result.regression_summary:
        lines.append(f"- Regression: `{result.run_id}/regression_vs_previous.json`")
    lines.append("")
