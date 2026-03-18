"""JSON report serialization."""

from __future__ import annotations

import json
from pathlib import Path

from validation_harness.models import RunResult


def write_json_report(result: RunResult, output_dir: str) -> Path:
    """Write RunResult to JSON file.

    Returns path to the written file.
    """
    run_dir = Path(output_dir) / result.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    report_path = run_dir / "run_result.json"
    report_path.write_text(result.model_dump_json(indent=2))

    # Write regression summary separately if present
    if result.regression_summary:
        reg_path = run_dir / "regression_vs_previous.json"
        reg_path.write_text(result.regression_summary.model_dump_json(indent=2))

    return report_path
