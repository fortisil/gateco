"""Regression comparison logic — compares runs against baselines."""

from __future__ import annotations

from validation_harness.models import (
    RegressionSummary,
    RunResult,
    RunSummary,
    ScenarioResult,
)


class RegressionComparator:
    """Compares a current run against a historical baseline."""

    @staticmethod
    def find_baseline(
        run: RunResult, history: list[RunSummary]
    ) -> RunSummary | None:
        """Find the most recent comparable run (same base_url + connector_type)."""
        candidates = [
            h
            for h in history
            if h.connector_type == run.connector_type
            and h.target_url == run.target_url
            and h.run_id != run.run_id
        ]
        if not candidates:
            return None
        # Most recent by timestamp
        return max(candidates, key=lambda h: h.timestamp)

    @staticmethod
    def compare(
        current: RunResult,
        baseline_scenarios: dict[str, str],
        baseline_run_id: str,
    ) -> RegressionSummary:
        """Compare current run scenarios against baseline scenario statuses.

        Args:
            current: The current RunResult.
            baseline_scenarios: Map of scenario_id -> status from the baseline run.
            baseline_run_id: The run ID of the baseline.

        Returns:
            RegressionSummary with newly failed/passed/unchanged lists.
        """
        newly_failed: list[str] = []
        newly_passed: list[str] = []
        unchanged_pass: list[str] = []
        unchanged_fail: list[str] = []

        for scenario in current.scenarios:
            sid = scenario.scenario_id
            current_pass = scenario.status == "passed"
            baseline_status = baseline_scenarios.get(sid)

            if baseline_status is None:
                # New scenario not in baseline
                continue

            baseline_pass = baseline_status == "passed"

            if current_pass and baseline_pass:
                unchanged_pass.append(sid)
            elif not current_pass and not baseline_pass:
                unchanged_fail.append(sid)
            elif current_pass and not baseline_pass:
                newly_passed.append(sid)
            else:  # not current_pass and baseline_pass
                newly_failed.append(sid)

        readiness_change = None
        if current.readiness_final is not None:
            readiness_change = current.readiness_final - (
                current.readiness_initial or 0
            )

        return RegressionSummary(
            compared_to_run_id=baseline_run_id,
            newly_failed=newly_failed,
            newly_passed=newly_passed,
            unchanged_pass=unchanged_pass,
            unchanged_fail=unchanged_fail,
            readiness_change=readiness_change,
        )
