"""Rich terminal output for validation results."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from validation_harness.models import RunResult, ScenarioResult

_STATUS_COLORS = {
    "passed": "green",
    "failed": "red",
    "skipped": "yellow",
    "error": "bright_red",
}

_FEATURE_COLORS = {
    "passed": "green",
    "failed": "red",
    "partial": "yellow",
    "skipped": "dim",
}


def render_console_report(result: RunResult, console: Console | None = None) -> None:
    """Render a rich console report of a validation run."""
    console = console or Console()

    # Header
    console.print()
    console.rule("[bold]Gateco Validation Report[/bold]")
    console.print(f"  Run ID:     {result.run_id}")
    console.print(f"  Profile:    {result.profile}")
    console.print(f"  Target:     {result.target_url}")
    console.print(f"  Connector:  {result.connector_type}")
    console.print(f"  Duration:   {result.duration_ms:.0f}ms")
    console.print()

    # Summary
    _render_summary_table(result, console)

    # Scenario details
    console.print()
    _render_scenario_table(result.scenarios, console)

    # Feature rollup
    if result.feature_rollup:
        console.print()
        _render_feature_rollup(result.feature_rollup, console)

    # Readiness
    if result.readiness_expected_max is not None:
        console.print()
        initial = result.readiness_initial or 0
        final = result.readiness_final or 0
        expected_max = result.readiness_expected_max
        expected_min = result.readiness_expected_min
        min_str = f", expected min: L{expected_min}" if expected_min is not None else ""
        console.print(
            f"  Readiness: L{initial} → L{final} "
            f"(expected max: L{expected_max}{min_str})"
        )
        if result.readiness_gap_reason:
            console.print(f"  [yellow]Gap: {result.readiness_gap_reason}[/yellow]")

    # Regression
    if result.regression_summary:
        console.print()
        reg = result.regression_summary
        console.print("[bold]Regression vs[/bold]", reg.compared_to_run_id)
        if reg.newly_failed:
            console.print(
                f"  [red]Newly failed ({len(reg.newly_failed)}):[/red] "
                + ", ".join(reg.newly_failed)
            )
        if reg.newly_passed:
            console.print(
                f"  [green]Newly passed ({len(reg.newly_passed)}):[/green] "
                + ", ".join(reg.newly_passed)
            )

    # Warnings
    if result.warnings:
        console.print()
        for warning in result.warnings:
            console.print(f"  [yellow]⚠ {warning}[/yellow]")

    console.print()
    console.rule()


def _render_summary_table(result: RunResult, console: Console) -> None:
    """Render the summary statistics table."""
    table = Table(title="Summary", show_header=True, header_style="bold")
    table.add_column("Metric", style="dim")
    table.add_column("Count", justify="right")

    table.add_row("Total", str(result.total))
    table.add_row("Passed", f"[green]{result.passed}[/green]")
    table.add_row("Failed", f"[red]{result.failed}[/red]")
    table.add_row("Skipped", f"[yellow]{result.skipped}[/yellow]")
    table.add_row("Errored", f"[bright_red]{result.errored}[/bright_red]")

    console.print(table)


def _render_scenario_table(
    scenarios: list[ScenarioResult], console: Console
) -> None:
    """Render the scenario results table."""
    table = Table(title="Scenarios", show_header=True, header_style="bold")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Feature")
    table.add_column("Status")
    table.add_column("Duration", justify="right")
    table.add_column("Notes")

    for s in scenarios:
        color = _STATUS_COLORS.get(s.status, "white")
        notes = ""
        if s.skip_reason:
            notes = s.skip_reason.value
        elif s.failure_category:
            notes = s.failure_category.value

        table.add_row(
            s.scenario_id,
            s.scenario_name,
            s.feature_area,
            f"[{color}]{s.status}[/{color}]",
            f"{s.duration_ms:.0f}ms" if s.duration_ms else "-",
            notes,
        )

    console.print(table)


def _render_feature_rollup(
    rollup: dict[str, str], console: Console
) -> None:
    """Render the feature area rollup."""
    table = Table(title="Feature Rollup", show_header=True, header_style="bold")
    table.add_column("Feature Area")
    table.add_column("Status")

    for area, status in sorted(rollup.items()):
        color = _FEATURE_COLORS.get(status, "white")
        table.add_row(area, f"[{color}]{status}[/{color}]")

    console.print(table)
