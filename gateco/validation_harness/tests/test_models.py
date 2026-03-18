"""Tests for model serialization round-trips."""

from __future__ import annotations

from datetime import datetime, timezone

from validation_harness.models import (
    Assertion,
    CreatedResource,
    CumulativeStatus,
    EvidenceRecord,
    FeatureStatus,
    RunResult,
    RunSummary,
    ScenarioResult,
    ScenarioStep,
)
from validation_harness.skip_taxonomy import FailureCategory, SkipReason


class TestEvidenceRecord:
    def test_serialization_roundtrip(self):
        record = EvidenceRecord(
            timestamp=datetime(2026, 3, 17, 12, 0, 0, tzinfo=timezone.utc),
            method="GET",
            path="/api/health",
            status_code=200,
            request_body=None,
            response_body={"status": "healthy"},
            duration_ms=42.5,
            error=None,
        )
        data = record.model_dump(mode="json")
        restored = EvidenceRecord.model_validate(data)
        assert restored.method == "GET"
        assert restored.status_code == 200
        assert restored.duration_ms == 42.5


class TestAssertion:
    def test_passing_assertion(self):
        a = Assertion(description="test", passed=True, expected=200, actual=200)
        assert a.passed is True
        assert a.error is None

    def test_failing_assertion(self):
        a = Assertion(
            description="test",
            passed=False,
            expected=200,
            actual=404,
            error="Not found",
        )
        assert a.passed is False


class TestScenarioResult:
    def test_passed_scenario(self):
        result = ScenarioResult(
            scenario_id="s00_health",
            scenario_name="Health Check",
            feature_area="health",
            status="passed",
            duration_ms=100.0,
        )
        data = result.model_dump(mode="json")
        restored = ScenarioResult.model_validate(data)
        assert restored.status == "passed"
        assert restored.failure_category is None

    def test_skipped_scenario(self):
        result = ScenarioResult(
            scenario_id="s04_ingest",
            scenario_name="Ingest",
            feature_area="ingestion",
            status="skipped",
            skip_reason=SkipReason.UNSUPPORTED_CONNECTOR_CAPABILITY,
        )
        data = result.model_dump(mode="json")
        restored = ScenarioResult.model_validate(data)
        assert restored.skip_reason == SkipReason.UNSUPPORTED_CONNECTOR_CAPABILITY

    def test_failed_scenario(self):
        result = ScenarioResult(
            scenario_id="s01_auth",
            scenario_name="Auth",
            feature_area="auth",
            status="failed",
            failure_category=FailureCategory.AUTH_ERROR,
        )
        data = result.model_dump(mode="json")
        restored = ScenarioResult.model_validate(data)
        assert restored.failure_category == FailureCategory.AUTH_ERROR


class TestRunResult:
    def test_full_roundtrip(self):
        run = RunResult(
            run_id="run-abc123",
            started_at=datetime(2026, 3, 17, 12, 0, 0, tzinfo=timezone.utc),
            completed_at=datetime(2026, 3, 17, 12, 1, 0, tzinfo=timezone.utc),
            profile="local-dev",
            target_url="http://localhost:8000",
            connector_type="pgvector",
            total=5,
            passed=3,
            failed=1,
            skipped=1,
            errored=0,
            feature_rollup={"auth": "passed", "ingestion": "failed"},
            duration_ms=60000.0,
        )
        data = run.model_dump(mode="json")
        restored = RunResult.model_validate(data)
        assert restored.run_id == "run-abc123"
        assert restored.total == 5
        assert restored.feature_rollup["auth"] == "passed"


class TestCreatedResource:
    def test_roundtrip(self):
        resource = CreatedResource(
            resource_type="connector",
            resource_id="uuid-123",
            resource_name="vh-test",
            owning_scenario="s02",
            deletion_method="DELETE /api/connectors/uuid-123",
        )
        data = resource.model_dump(mode="json")
        restored = CreatedResource.model_validate(data)
        assert restored.deletion_status == "pending"


class TestCumulativeStatus:
    def test_empty_state(self):
        status = CumulativeStatus(
            last_updated=datetime(2026, 3, 17, tzinfo=timezone.utc)
        )
        data = status.model_dump(mode="json")
        restored = CumulativeStatus.model_validate(data)
        assert restored.features == {}
        assert restored.connectors == {}

    def test_with_data(self):
        status = CumulativeStatus(
            last_updated=datetime(2026, 3, 17, tzinfo=timezone.utc),
            features={
                "auth": FeatureStatus(
                    status="pass", tested_connectors=["pgvector"]
                )
            },
            recent_runs=[
                RunSummary(
                    run_id="run-1",
                    timestamp=datetime(2026, 3, 17, tzinfo=timezone.utc),
                    profile="local",
                    connector_type="pgvector",
                    target_url="http://localhost:8000",
                    total=10,
                    passed=8,
                    failed=1,
                    skipped=1,
                )
            ],
        )
        data = status.model_dump(mode="json")
        restored = CumulativeStatus.model_validate(data)
        assert restored.features["auth"].status == "pass"
        assert len(restored.recent_runs) == 1
