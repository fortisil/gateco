"""Pydantic data models for validation harness results and state."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from validation_harness.skip_taxonomy import FailureCategory, SkipReason


# ---------------------------------------------------------------------------
# Evidence & Assertions
# ---------------------------------------------------------------------------


class EvidenceRecord(BaseModel):
    """Single HTTP request/response captured during a scenario step."""

    timestamp: datetime
    method: str
    path: str
    status_code: int | None = None
    request_body: dict[str, Any] | None = None
    response_body: dict[str, Any] | None = None
    duration_ms: float
    error: str | None = None


class Assertion(BaseModel):
    """Single assertion within a scenario step."""

    description: str
    passed: bool
    expected: Any = None
    actual: Any = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Scenario Steps & Results
# ---------------------------------------------------------------------------


class ScenarioStep(BaseModel):
    """One logical step within a scenario."""

    name: str
    status: Literal["passed", "failed", "skipped", "error"] = "passed"
    assertions: list[Assertion] = Field(default_factory=list)
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    duration_ms: float = 0.0
    error: str | None = None


class CreatedResource(BaseModel):
    """Cleanup manifest entry for a resource created during validation."""

    resource_type: str
    resource_id: str
    resource_name: str
    owning_scenario: str
    deletion_method: str
    deletion_attempted: bool = False
    deletion_status: Literal["pending", "success", "failed", "skipped"] = "pending"


class ScenarioResult(BaseModel):
    """Result of executing a single scenario."""

    scenario_id: str
    scenario_name: str
    feature_area: str
    status: Literal["passed", "failed", "skipped", "error"]
    failure_category: FailureCategory | None = None
    skip_reason: SkipReason | None = None
    steps: list[ScenarioStep] = Field(default_factory=list)
    created_resources: list[CreatedResource] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float = 0.0
    prerequisites: list[str] = Field(default_factory=list)
    cleanup_status: Literal["success", "partial", "failed", "skipped"] = "skipped"
    regression_status: (
        Literal["new_pass", "new_fail", "unchanged", "new_scenario"] | None
    ) = None


# ---------------------------------------------------------------------------
# Run Result
# ---------------------------------------------------------------------------


class RegressionSummary(BaseModel):
    """Comparison between current run and a baseline."""

    compared_to_run_id: str
    newly_failed: list[str] = Field(default_factory=list)
    newly_passed: list[str] = Field(default_factory=list)
    unchanged_pass: list[str] = Field(default_factory=list)
    unchanged_fail: list[str] = Field(default_factory=list)
    readiness_change: int | None = None
    latency_change_pct: float | None = None


class RunResult(BaseModel):
    """Complete result of a validation run."""

    run_id: str
    started_at: datetime
    completed_at: datetime | None = None
    profile: str
    target_url: str
    connector_type: str
    scenarios: list[ScenarioResult] = Field(default_factory=list)
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errored: int = 0
    warnings: list[str] = Field(default_factory=list)
    feature_rollup: dict[str, Literal["passed", "failed", "partial", "skipped"]] = (
        Field(default_factory=dict)
    )
    regression_summary: RegressionSummary | None = None
    expected_capabilities: dict[str, bool] = Field(default_factory=dict)
    observed_capabilities: dict[str, bool] = Field(default_factory=dict)
    readiness_initial: int | None = None
    readiness_final: int | None = None
    readiness_expected_max: int | None = None
    readiness_expected_min: int | None = None
    readiness_gap_reason: str | None = None
    duration_ms: float = 0.0


# ---------------------------------------------------------------------------
# Cumulative Coverage State
# ---------------------------------------------------------------------------


class FeatureStatus(BaseModel):
    """Cumulative status for a feature area."""

    status: Literal["pass", "fail", "partial", "untested"] = "untested"
    tested_connectors: list[str] = Field(default_factory=list)
    last_run: str | None = None


class ConnectorStatus(BaseModel):
    """Cumulative status for a connector type."""

    status: Literal["pass", "fail", "partial", "untested"] = "untested"
    last_run_id: str | None = None
    best_readiness: int | None = None


class IDPStatus(BaseModel):
    """Cumulative status for an identity provider."""

    status: Literal["pass", "fail", "partial", "untested"] = "untested"
    last_run_id: str | None = None


class CombinationStatus(BaseModel):
    """Cumulative status for a connector+IDP combination."""

    status: Literal["pass", "fail", "partial", "untested"] = "untested"
    last_run_id: str | None = None


class RunSummary(BaseModel):
    """Lightweight summary of a past run for trend tracking."""

    run_id: str
    timestamp: datetime
    profile: str
    connector_type: str
    target_url: str
    total: int
    passed: int
    failed: int
    skipped: int
    readiness_final: int | None = None
    duration_ms: float = 0.0


class CumulativeStatus(BaseModel):
    """Cumulative coverage matrix persisted across runs."""

    last_updated: datetime
    features: dict[str, FeatureStatus] = Field(default_factory=dict)
    connectors: dict[str, ConnectorStatus] = Field(default_factory=dict)
    identity_providers: dict[str, IDPStatus] = Field(default_factory=dict)
    combinations: dict[str, CombinationStatus] = Field(default_factory=dict)
    recent_runs: list[RunSummary] = Field(default_factory=list)
