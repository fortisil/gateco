"""Click CLI for the Gateco Validation Harness."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import click
from rich.console import Console

from validation_harness.capabilities import CONNECTOR_CAPABILITIES
from validation_harness.config import load_profile
from validation_harness.engine import Engine
from validation_harness.reports.console_report import render_console_report
from validation_harness.reports.json_report import write_json_report
from validation_harness.reports.markdown_report import write_markdown_report
from validation_harness.state import CoverageManager

console = Console()


def _run_async(coro):
    """Run an async coroutine."""
    return asyncio.run(coro)


@click.group()
def main():
    """Gateco Validation Harness — integration verification framework."""
    pass


# ---------------------------------------------------------------------------
# Core commands
# ---------------------------------------------------------------------------


@main.command()
@click.option("-p", "--profile", required=True, help="Path to YAML profile")
@click.option("-s", "--scenarios", default=None, help="Comma-separated scenario IDs")
@click.option("-f", "--feature", default=None, help="Filter by feature area")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["console", "json", "markdown", "all"]),
    default="console",
    help="Output format",
)
def run(profile: str, scenarios: str | None, feature: str | None, fmt: str):
    """Run validation scenarios against a Gateco instance."""
    # Import scenarios to trigger registration
    import validation_harness.scenarios  # noqa: F401

    config = load_profile(profile)
    engine = Engine(config)

    scenario_ids = scenarios.split(",") if scenarios else None

    from rich.live import Live
    from rich.spinner import Spinner

    with Live(
        Spinner("dots", text="Running validation scenarios..."),
        console=console,
        transient=True,
    ):
        result = _run_async(
            engine.run(
                scenario_ids=scenario_ids, feature_filter=feature, format=fmt
            )
        )

    # Generate reports
    if fmt in ("console", "all"):
        render_console_report(result, console)

    if fmt in ("json", "all"):
        path = write_json_report(result, config.output_dir)
        console.print(f"JSON report: {path}")

    if fmt in ("markdown", "all"):
        coverage_mgr = CoverageManager(config.output_dir)
        cumulative = coverage_mgr.load()
        path = write_markdown_report(result, config.output_dir, cumulative)
        console.print(f"Markdown report: {path}")

    # Update cumulative state
    coverage_mgr = CoverageManager(config.output_dir)
    coverage_mgr.update_from_run(result)

    # Print change manifest summary
    from pathlib import Path as _Path

    manifest_path = _Path(config.output_dir) / result.run_id / "change_manifest.json"
    if manifest_path.exists():
        import json as _json

        manifest_data = _json.loads(manifest_path.read_text())
        entries = manifest_data.get("entries", [])
        if entries:
            blocking = sum(1 for e in entries if e.get("severity") == "blocking")
            degraded = sum(1 for e in entries if e.get("severity") == "degraded")
            cosmetic = sum(1 for e in entries if e.get("severity") == "cosmetic")
            console.print(
                f"Change manifest: {len(entries)} entries "
                f"({blocking} blocking, {degraded} degraded, {cosmetic} cosmetic)"
            )

    # Exit code
    if result.failed > 0 or result.errored > 0:
        sys.exit(1)


@main.command("list-scenarios")
def list_scenarios():
    """List all registered scenarios."""
    import validation_harness.scenarios  # noqa: F401

    from validation_harness.registry import get_registry

    registry = get_registry()
    if not registry:
        console.print("No scenarios registered.")
        return

    from rich.table import Table

    table = Table(title="Registered Scenarios", show_header=True, header_style="bold")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Feature")
    table.add_column("Depends On")
    table.add_column("Capabilities")

    for sid in sorted(registry.keys()):
        defn = registry[sid]
        deps = ", ".join(defn.depends_on) if defn.depends_on else "-"
        caps = ", ".join(defn.requires_capabilities) if defn.requires_capabilities else "-"
        table.add_row(sid, defn.name, defn.feature_area, deps, caps)

    console.print(table)


@main.command("list-features")
def list_features():
    """List all feature areas across scenarios."""
    import validation_harness.scenarios  # noqa: F401

    from validation_harness.registry import get_registry

    registry = get_registry()
    features: dict[str, list[str]] = {}
    for defn in registry.values():
        features.setdefault(defn.feature_area, []).append(defn.id)

    for area in sorted(features.keys()):
        ids = ", ".join(sorted(features[area]))
        console.print(f"  {area}: {ids}")


@main.command("list-capabilities")
@click.option("-c", "--connector", required=True, help="Connector type")
def list_capabilities(connector: str):
    """List capabilities for a connector type."""
    caps = CONNECTOR_CAPABILITIES.get(connector)
    if caps is None:
        console.print(f"Unknown connector type: {connector}")
        console.print(f"Known types: {', '.join(sorted(CONNECTOR_CAPABILITIES.keys()))}")
        sys.exit(1)

    console.print(f"Capabilities for [bold]{connector}[/bold]:")
    for name, value in caps.to_dict().items():
        icon = "[green]Y[/green]" if value else "[red]N[/red]"
        console.print(f"  {icon}  {name}: {value}")


# ---------------------------------------------------------------------------
# Reporting commands
# ---------------------------------------------------------------------------


@main.command("status")
def status():
    """Show cumulative coverage matrix."""
    # Try to find output dir from a default location
    output_dir = ".validation_harness/output"
    mgr = CoverageManager(output_dir)
    cumulative = mgr.load()

    if not cumulative.features and not cumulative.connectors:
        console.print("No cumulative data yet. Run some scenarios first.")
        return

    from rich.table import Table

    # Features table
    if cumulative.features:
        table = Table(title="Feature Coverage", show_header=True, header_style="bold")
        table.add_column("Feature")
        table.add_column("Status")
        table.add_column("Tested Connectors")

        for name, fs in sorted(cumulative.features.items()):
            connectors = ", ".join(fs.tested_connectors) if fs.tested_connectors else "-"
            table.add_row(name, fs.status, connectors)
        console.print(table)

    # Connectors table
    if cumulative.connectors:
        console.print()
        table = Table(title="Connector Coverage", show_header=True, header_style="bold")
        table.add_column("Connector")
        table.add_column("Status")
        table.add_column("Best Readiness")

        for name, cs in sorted(cumulative.connectors.items()):
            readiness = f"L{cs.best_readiness}" if cs.best_readiness is not None else "-"
            table.add_row(name, cs.status, readiness)
        console.print(table)


@main.command("report")
@click.argument("run_id", required=False)
def report(run_id: str | None):
    """View a past run report."""
    output_dir = Path(".validation_harness/output")
    if run_id:
        report_path = output_dir / run_id / "run_result.json"
    else:
        # Find most recent run
        runs = sorted(output_dir.glob("run-*/run_result.json"), reverse=True)
        if not runs:
            console.print("No runs found.")
            return
        report_path = runs[0]

    if not report_path.exists():
        console.print(f"Report not found: {report_path}")
        return

    from validation_harness.models import RunResult

    raw = json.loads(report_path.read_text())
    result = RunResult.model_validate(raw)
    render_console_report(result, console)


@main.command("compare")
@click.option("--run-a", required=True, help="First run ID")
@click.option("--run-b", required=True, help="Second run ID")
def compare(run_a: str, run_b: str):
    """Compare two validation runs."""
    output_dir = Path(".validation_harness/output")

    from validation_harness.models import RunResult
    from validation_harness.regression import RegressionComparator

    path_a = output_dir / run_a / "run_result.json"
    path_b = output_dir / run_b / "run_result.json"

    if not path_a.exists():
        console.print(f"Run not found: {run_a}")
        return
    if not path_b.exists():
        console.print(f"Run not found: {run_b}")
        return

    result_a = RunResult.model_validate(json.loads(path_a.read_text()))
    result_b = RunResult.model_validate(json.loads(path_b.read_text()))

    baseline = {s.scenario_id: s.status for s in result_a.scenarios}
    summary = RegressionComparator.compare(result_b, baseline, run_a)

    console.print(f"Comparing [bold]{run_b}[/bold] against [bold]{run_a}[/bold]:")
    console.print()
    if summary.newly_failed:
        console.print(f"[red]Newly failed ({len(summary.newly_failed)}):[/red]")
        for sid in summary.newly_failed:
            console.print(f"  - {sid}")
    if summary.newly_passed:
        console.print(f"[green]Newly passed ({len(summary.newly_passed)}):[/green]")
        for sid in summary.newly_passed:
            console.print(f"  - {sid}")
    console.print(
        f"Unchanged: {len(summary.unchanged_pass)} pass, "
        f"{len(summary.unchanged_fail)} fail"
    )


# ---------------------------------------------------------------------------
# Maintenance commands
# ---------------------------------------------------------------------------


@main.command("cleanup-only")
@click.option("-p", "--profile", required=True, help="Path to YAML profile")
@click.option(
    "--manifest",
    default=None,
    help="Path to created_resources.json manifest (uses manifest-based cleanup)",
)
def cleanup_only(profile: str, manifest: str | None):
    """Delete vh- resources without running scenarios.

    Without --manifest: uses prefix-based fallback (finds all vh- resources).
    With --manifest: uses manifest-based cleanup from a specific run.
    """
    from validation_harness.api import create_harness_client
    from validation_harness.cleanup import CleanupManager

    config = load_profile(profile)

    async def _cleanup():
        client, _ = await create_harness_client(config.base_url)
        try:
            await client.login(
                config.credentials.email, config.credentials.password
            )
            mgr = CleanupManager(config.output_dir)

            if manifest:
                resources = await mgr.cleanup_from_manifest(client, manifest)
                succeeded = sum(
                    1 for r in resources if r.deletion_status == "success"
                )
                failed = sum(
                    1 for r in resources if r.deletion_status == "failed"
                )
                console.print(
                    f"Manifest cleanup: {succeeded} deleted, {failed} failed "
                    f"(of {len(resources)} total)"
                )
            else:
                deleted = await mgr.cleanup_by_prefix(
                    client, config.resource_prefix
                )
                console.print(
                    f"Deleted {deleted} resources with prefix "
                    f"'{config.resource_prefix}'"
                )
        finally:
            await client.close()

    _run_async(_cleanup())


@main.command("rerun-failed")
@click.option("--from-run", required=True, help="Run ID to rerun failed scenarios from")
@click.option("-p", "--profile", required=True, help="Path to YAML profile")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["console", "json", "markdown", "all"]),
    default="console",
)
def rerun_failed(from_run: str, profile: str, fmt: str):
    """Re-execute only failed scenarios from a previous run."""
    import validation_harness.scenarios  # noqa: F401

    from validation_harness.models import RunResult

    output_dir = Path(".validation_harness/output")
    report_path = output_dir / from_run / "run_result.json"
    if not report_path.exists():
        console.print(f"Run not found: {from_run}")
        sys.exit(1)

    prev = RunResult.model_validate(json.loads(report_path.read_text()))
    failed_ids = [
        s.scenario_id for s in prev.scenarios if s.status in ("failed", "error")
    ]
    if not failed_ids:
        console.print("No failed scenarios to rerun.")
        return

    config = load_profile(profile)
    engine = Engine(config)
    result = _run_async(
        engine.run(scenario_ids=failed_ids, format=fmt)
    )

    if fmt in ("console", "all"):
        render_console_report(result, console)
    if fmt in ("json", "all"):
        path = write_json_report(result, config.output_dir)
        console.print(f"JSON report: {path}")

    coverage_mgr = CoverageManager(config.output_dir)
    coverage_mgr.update_from_run(result)

    if result.failed > 0 or result.errored > 0:
        sys.exit(1)


@main.command("doctor")
@click.option("-p", "--profile", required=True, help="Path to YAML profile")
@click.option(
    "--check",
    "check_filter",
    type=click.Choice(["all", "profile", "offline", "live"]),
    default="all",
    help="Which checks to run (default: all)",
)
@click.option("--json", "json_output", is_flag=True, help="Machine-readable JSON output")
def doctor(profile: str, check_filter: str, json_output: bool):
    """Preflight check: profile validation, filesystem, connectivity, credentials."""
    import sys as _sys
    import tempfile
    from pathlib import Path as _Path

    # Import CONNECTOR_REQUIRED_FIELDS from backend schemas (same sys.path
    # approach as test_capability_keys_match_backend_enum in test_capabilities.py)
    backend_src = _Path(__file__).resolve().parents[4] / "apps" / "backend" / "src"
    _sys.path.insert(0, str(backend_src))
    try:
        from gateco.schemas.connectors import CONNECTOR_REQUIRED_FIELDS
    except ImportError:
        CONNECTOR_REQUIRED_FIELDS = {}
    finally:
        if str(backend_src) in _sys.path:
            _sys.path.remove(str(backend_src))

    results = _run_doctor_checks(
        profile, check_filter, CONNECTOR_REQUIRED_FIELDS
    )

    if json_output:
        import json as _json

        console.print(_json.dumps(results, indent=2))
    else:
        # Pretty-print
        config_data = results.get("_config")
        if config_data and not json_output:
            console.print(f"Profile: [bold]{config_data['profile_name']}[/bold]")
            console.print(f"Target:  {config_data['base_url']}")
            console.print(f"Connector: {config_data['connector_type']}")
            console.print()

        for check in results["checks"]:
            if check["passed"]:
                console.print(f"[green]  PASS[/green] {check['name']}")
            else:
                detail = f" ({check['detail']})" if check.get("detail") else ""
                console.print(f"[red]  FAIL[/red] {check['name']}{detail}")

        console.print()
        total = len(results["checks"])
        passed = sum(1 for c in results["checks"] if c["passed"])
        console.print(f"Results: {passed}/{total} checks passed")

    # Remove internal config from JSON output
    output = {k: v for k, v in results.items() if not k.startswith("_")}

    if not results["overall_passed"]:
        sys.exit(1)


def _run_doctor_checks(
    profile_path: str,
    check_filter: str,
    connector_required_fields: dict,
) -> dict:
    """Run doctor checks and return structured results."""
    checks: list[dict] = []
    config = None
    config_meta: dict | None = None

    # --- Offline checks ---

    # Check 1: Profile loads
    if check_filter in ("all", "profile", "offline"):
        try:
            config = load_profile(profile_path)
            checks.append({
                "name": "Profile loads",
                "category": "offline",
                "passed": True,
                "failure_category": None,
                "detail": "Profile parsed and validated",
            })
            config_meta = {
                "profile_name": config.profile_name,
                "base_url": config.base_url,
                "connector_type": config.connector.type,
            }
        except Exception as exc:
            checks.append({
                "name": "Profile loads",
                "category": "offline",
                "passed": False,
                "failure_category": "config_error",
                "detail": str(exc),
            })

    # Check 2: Connector type known
    if check_filter in ("all", "profile", "offline") and config:
        caps = CONNECTOR_CAPABILITIES.get(config.connector.type)
        if caps:
            checks.append({
                "name": "Connector type known",
                "category": "offline",
                "passed": True,
                "failure_category": None,
                "detail": f"Type '{config.connector.type}' found in capability matrix",
            })
        else:
            known = ", ".join(sorted(CONNECTOR_CAPABILITIES.keys()))
            checks.append({
                "name": "Connector type known",
                "category": "offline",
                "passed": False,
                "failure_category": "config_error",
                "detail": f"Unknown type '{config.connector.type}'. Known: {known}",
            })

    # Check 3: Required connector fields
    if check_filter in ("all", "profile", "offline") and config:
        required = connector_required_fields.get(config.connector.type, [])
        missing = [f for f in required if f not in config.connector.config]
        if not missing:
            checks.append({
                "name": "Required connector fields",
                "category": "offline",
                "passed": True,
                "failure_category": None,
                "detail": f"All {len(required)} required fields present",
            })
        else:
            checks.append({
                "name": "Required connector fields",
                "category": "offline",
                "passed": False,
                "failure_category": "config_error",
                "detail": f"Missing fields: {', '.join(missing)}",
            })

    # Check 4: Output dir writable
    if check_filter in ("all", "offline") and config:
        import tempfile
        from pathlib import Path as _Path

        try:
            out_dir = _Path(config.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            # Verify writable by creating and removing a temp file
            tmp = out_dir / ".doctor_write_test"
            tmp.write_text("test")
            tmp.unlink()
            checks.append({
                "name": "Output dir writable",
                "category": "offline",
                "passed": True,
                "failure_category": None,
                "detail": f"Directory '{config.output_dir}' is writable",
            })
        except Exception as exc:
            checks.append({
                "name": "Output dir writable",
                "category": "offline",
                "passed": False,
                "failure_category": "filesystem_error",
                "detail": str(exc),
            })

    # --- Live checks ---

    if check_filter in ("all", "live") and config:
        live_results = _run_async(_run_live_doctor_checks(config))
        checks.extend(live_results)
    elif check_filter in ("all", "live") and not config:
        # Need to load profile for live checks even if not reporting profile checks
        if check_filter == "live":
            try:
                config = load_profile(profile_path)
                config_meta = {
                    "profile_name": config.profile_name,
                    "base_url": config.base_url,
                    "connector_type": config.connector.type,
                }
                live_results = _run_async(_run_live_doctor_checks(config))
                checks.extend(live_results)
            except Exception as exc:
                checks.append({
                    "name": "Profile loads (implicit for live)",
                    "category": "offline",
                    "passed": False,
                    "failure_category": "config_error",
                    "detail": str(exc),
                })

    overall_passed = all(c["passed"] for c in checks)

    result = {
        "profile": profile_path,
        "check_filter": check_filter,
        "overall_passed": overall_passed,
        "checks": checks,
    }
    if config_meta:
        result["_config"] = config_meta

    return result


async def _run_live_doctor_checks(config) -> list[dict]:
    """Run live checks (health + auth) and return check dicts."""
    import httpx

    checks: list[dict] = []

    # Check 5: Health check
    try:
        async with httpx.AsyncClient() as http:
            health_resp = await http.get(f"{config.base_url}/health", timeout=10)
            db_resp = await http.get(f"{config.base_url}/health/db", timeout=10)
        if health_resp.status_code == 200 and db_resp.status_code == 200:
            checks.append({
                "name": "Health check",
                "category": "live",
                "passed": True,
                "failure_category": None,
                "detail": "GET /health and /health/db returned 200",
            })
        else:
            checks.append({
                "name": "Health check",
                "category": "live",
                "passed": False,
                "failure_category": "backend_unreachable",
                "detail": (
                    f"/health={health_resp.status_code}, "
                    f"/health/db={db_resp.status_code}"
                ),
            })
    except Exception as exc:
        checks.append({
            "name": "Health check",
            "category": "live",
            "passed": False,
            "failure_category": "backend_unreachable",
            "detail": str(exc),
        })

    # Check 6: Authentication
    from validation_harness.api import create_harness_client

    try:
        client, _ = await create_harness_client(config.base_url)
        await client.login(config.credentials.email, config.credentials.password)
        checks.append({
            "name": "Authentication",
            "category": "live",
            "passed": True,
            "failure_category": None,
            "detail": f"Login succeeded as {config.credentials.email}",
        })
        await client.close()
    except Exception as exc:
        checks.append({
            "name": "Authentication",
            "category": "live",
            "passed": False,
            "failure_category": "auth_failed",
            "detail": str(exc),
        })

    return checks


@main.command("ci-summary")
@click.option(
    "-o", "--output-dir",
    default=".validation_harness/output",
    help="Output directory containing run results",
)
def ci_summary(output_dir: str):
    """Generate combined CI summary from all runs in the output directory."""
    from validation_harness.reports.ci_summary import (
        generate_ci_summary,
        write_ci_summary,
    )

    summary = generate_ci_summary(output_dir)

    if not summary.profiles:
        console.print("No run results found in output directory.")
        return

    json_path, md_path = write_ci_summary(summary, output_dir)

    # Print summary table
    from rich.table import Table

    table = Table(title="CI Connector Summary", show_header=True, header_style="bold")
    table.add_column("Connector")
    table.add_column("Mode")
    table.add_column("Passed", justify="right")
    table.add_column("Failed", justify="right")
    table.add_column("Skipped", justify="right")

    for p in summary.profiles:
        fail_style = "red" if p.failed > 0 else ""
        table.add_row(
            p.connector,
            p.provider_mode,
            str(p.passed),
            f"[{fail_style}]{p.failed}[/{fail_style}]" if fail_style else str(p.failed),
            str(p.skipped),
        )

    console.print(table)

    if summary.regressions:
        console.print(f"\n[red]Regressions: {len(summary.regressions)}[/red]")
        for r in summary.regressions:
            console.print(f"  - {r}")

    console.print(f"\nChange manifest: {summary.change_manifest_total} total, "
                  f"{summary.blocking_changes} blocking")
    console.print(f"JSON: {json_path}")
    console.print(f"Markdown: {md_path}")


if __name__ == "__main__":
    main()
