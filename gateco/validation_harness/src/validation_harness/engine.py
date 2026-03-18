"""Scenario orchestrator — executes scenarios with dependency resolution and cleanup."""

from __future__ import annotations

import logging
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine

from gateco_sdk.client import AsyncGatecoClient
from gateco_sdk.errors import GatecoError

from validation_harness.api import EvidenceCapturingTransport, create_harness_client
from validation_harness.capabilities import CONNECTOR_CAPABILITIES, check_capabilities
from validation_harness.change_manifest import (
    ChangeEntry,
    ChangeManifest,
    derive_entries_from_results,
    write_change_manifest,
)
from validation_harness.cleanup import CleanupManager
from validation_harness.config import HarnessConfig
from validation_harness.models import (
    Assertion,
    CreatedResource,
    EvidenceRecord,
    RunResult,
    ScenarioResult,
    ScenarioStep,
)
from validation_harness.regression import RegressionComparator
from validation_harness.registry import (
    ScenarioDefinition,
    get_registry,
    topological_sort,
)
from validation_harness.skip_taxonomy import FailureCategory, SkipReason
from validation_harness.state import CoverageManager

logger = logging.getLogger(__name__)

# Entitlements that require specific plan tiers
_ENTITLEMENT_PLAN_MAP: dict[str, str] = {
    "simulator": "pro",
    "audit_export": "pro",
    "advanced_policies": "enterprise",
}


class ScenarioContext:
    """Shared context passed to every scenario function."""

    def __init__(
        self,
        client: AsyncGatecoClient,
        transport: EvidenceCapturingTransport,
        config: HarnessConfig,
    ) -> None:
        self.client = client
        self.transport = transport
        self.config = config
        self.state: dict[str, Any] = {}
        self._cleanup_manifest: list[CreatedResource] = []
        self._cleanup_fns: list[Callable[[], Coroutine[Any, Any, None]]] = []
        self._current_steps: list[ScenarioStep] = []
        self._current_step: ScenarioStep | None = None
        self._change_entries: list[ChangeEntry] = []
        # Phase 2 hooks
        self.principal_context: str | None = None
        self.actor_override: str | None = None

    # -- Shared state -------------------------------------------------------

    def share(self, key: str, value: Any) -> None:
        """Store a value for downstream scenarios."""
        self.state[key] = value

    def require(self, key: str) -> Any:
        """Retrieve a shared value or raise KeyError."""
        if key not in self.state:
            raise KeyError(f"Required shared state missing: {key}")
        return self.state[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a shared value with a default."""
        return self.state.get(key, default)

    # -- Change tracking ----------------------------------------------------

    def log_change(
        self,
        category: str,
        severity: str,
        component: str,
        description: str,
        *,
        scenario_id: str | None = None,
    ) -> None:
        """Record an explicit change entry for the change manifest."""
        self._change_entries.append(
            ChangeEntry(
                category=category,
                severity=severity,
                component=component,
                description=description,
                scenario_id=scenario_id,
                connector_type=self.config.connector.type,
            )
        )

    def drain_change_entries(self) -> list[ChangeEntry]:
        """Return and clear accumulated change entries."""
        entries = list(self._change_entries)
        self._change_entries.clear()
        return entries

    # -- Resource tracking --------------------------------------------------

    def register_resource(self, resource: CreatedResource) -> None:
        """Add a resource to the cleanup manifest."""
        self._cleanup_manifest.append(resource)

    def register_cleanup(self, fn: Callable[[], Coroutine[Any, Any, None]]) -> None:
        """Register an async cleanup function (runs in reverse order)."""
        self._cleanup_fns.append(fn)

    # -- Step tracking ------------------------------------------------------

    def begin_step(self, name: str) -> None:
        """Start a new scenario step (flushes evidence from previous step)."""
        if self._current_step is not None:
            self._finalize_current_step()
        self._current_step = ScenarioStep(name=name)

    def assert_that(
        self,
        description: str,
        condition: bool,
        *,
        expected: Any = None,
        actual: Any = None,
    ) -> None:
        """Record an assertion in the current step."""
        if self._current_step is None:
            self.begin_step("default")

        assertion = Assertion(
            description=description,
            passed=condition,
            expected=expected,
            actual=actual,
            error=None if condition else f"Assertion failed: {description}",
        )
        self._current_step.assertions.append(assertion)  # type: ignore[union-attr]

        if not condition:
            self._current_step.status = "failed"  # type: ignore[union-attr]

    def _finalize_current_step(self) -> None:
        """Finalize step: drain evidence, compute status, meta-check evidence."""
        if self._current_step is None:
            return

        self._current_step.evidence = self.transport.drain_evidence()

        # Meta-check: if step has assertions (expected API interaction) but no
        # evidence was captured, flag it as a warning assertion.
        if (
            self._current_step.assertions
            and not self._current_step.evidence
            and self._current_step.name != "default"
        ):
            self._current_step.assertions.append(
                Assertion(
                    description="[meta] Step expected API calls but no evidence captured",
                    passed=True,  # Warning, not failure
                    expected="evidence records > 0",
                    actual="0 (may be expected for non-API steps)",
                )
            )

        # If no assertions failed but there are assertions, mark passed
        if self._current_step.assertions:
            all_passed = all(a.passed for a in self._current_step.assertions)
            if all_passed and self._current_step.status != "error":
                self._current_step.status = "passed"
        elif self._current_step.status not in ("failed", "error"):
            self._current_step.status = "passed"

        self._current_steps.append(self._current_step)
        self._current_step = None

    def _collect_steps(self) -> list[ScenarioStep]:
        """Finalize and return all steps."""
        if self._current_step is not None:
            self._finalize_current_step()
        result = list(self._current_steps)
        self._current_steps.clear()
        return result

    def drain_created_resources(self) -> list[CreatedResource]:
        """Return and clear the cleanup manifest."""
        resources = list(self._cleanup_manifest)
        self._cleanup_manifest.clear()
        return resources


class Engine:
    """Orchestrates scenario execution with dependency resolution."""

    def __init__(self, config: HarnessConfig) -> None:
        self.config = config

    async def run(
        self,
        *,
        scenario_ids: list[str] | None = None,
        feature_filter: str | None = None,
        format: str = "console",
    ) -> RunResult:
        """Execute scenarios and return results."""
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        started_at = datetime.now(timezone.utc)

        registry = get_registry()

        # Filter scenarios
        if scenario_ids:
            candidates = [
                sid for sid in scenario_ids if sid in registry
            ]
        else:
            candidates = list(registry.keys())

        if feature_filter:
            candidates = [
                sid for sid in candidates
                if registry[sid].feature_area == feature_filter
            ]

        # Resolve dependencies — include transitive deps
        all_needed = set(candidates)
        changed = True
        while changed:
            changed = False
            for sid in list(all_needed):
                defn = registry.get(sid)
                if defn:
                    for dep in defn.depends_on:
                        if dep not in all_needed and dep in registry:
                            all_needed.add(dep)
                            changed = True

        # Topological sort
        ordered = topological_sort(list(all_needed))

        # Create client
        client, transport = await create_harness_client(
            self.config.base_url, timeout=30.0, max_retries=1
        )
        ctx = ScenarioContext(client, transport, self.config)
        ctx._steps_complete = []

        caps = CONNECTOR_CAPABILITIES.get(self.config.connector.type)
        results: list[ScenarioResult] = []
        failed_ids: set[str] = set()
        skipped_ids: set[str] = set()
        cleanup_mgr = CleanupManager(self.config.output_dir)
        all_created_resources: list[CreatedResource] = []

        try:
            for sid in ordered:
                defn = registry[sid]
                result = await self._execute_scenario(
                    ctx, defn, caps, failed_ids, skipped_ids
                )
                results.append(result)
                all_created_resources.extend(result.created_resources)
                if result.status in ("failed", "error"):
                    failed_ids.add(sid)
                elif result.status == "skipped":
                    skipped_ids.add(sid)
        finally:
            # Save cleanup manifest before running cleanup
            if all_created_resources:
                cleanup_mgr.save_manifest(run_id, all_created_resources)

            # Run cleanup
            await self._run_cleanup(ctx, client, cleanup_mgr, run_id)
            await client.close()

        completed_at = datetime.now(timezone.utc)
        elapsed = (completed_at - started_at).total_seconds() * 1000

        # Compute rollup
        total = len(results)
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")
        errored = sum(1 for r in results if r.status == "error")
        feature_rollup = self._compute_feature_rollup(results)

        cap_dict = caps.to_dict() if caps else {}

        # Extract readiness from shared state
        readiness_initial = ctx.get("readiness_initial")
        readiness_final = ctx.get("readiness_final")
        readiness_expected_min = ctx.get("readiness_expected_min")
        readiness_gap_reason = ctx.get("readiness_gap_reason")

        run_result = RunResult(
            run_id=run_id,
            started_at=started_at,
            completed_at=completed_at,
            profile=self.config.profile_name,
            target_url=self.config.base_url,
            connector_type=self.config.connector.type,
            scenarios=results,
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errored=errored,
            feature_rollup=feature_rollup,
            expected_capabilities={
                k: bool(v) for k, v in cap_dict.items()
                if isinstance(v, bool)
            },
            readiness_initial=readiness_initial,
            readiness_final=readiness_final,
            readiness_expected_max=caps.expected_max_readiness_level if caps else None,
            readiness_expected_min=readiness_expected_min,
            readiness_gap_reason=readiness_gap_reason,
            duration_ms=round(elapsed, 2),
        )

        # Regression comparison against baseline
        run_result.regression_summary = self._compute_regression(run_result)

        # Generate change manifest (must write even on partial runs)
        try:
            self._generate_change_manifest(run_result, ctx)
        except Exception as exc:
            logger.warning("Change manifest generation failed: %s", exc)

        return run_result

    def _generate_change_manifest(
        self, run: RunResult, ctx: ScenarioContext
    ) -> ChangeManifest:
        """Build and write the change manifest for this run."""
        # Collect explicit entries from scenarios
        explicit = ctx.drain_change_entries()

        # Derive conservative entries from failure categories
        derived = derive_entries_from_results(
            run.scenarios, run.connector_type
        )

        manifest = ChangeManifest(
            run_id=run.run_id,
            connector_type=run.connector_type,
            profile=run.profile,
            provider_mode=self.config.provider_mode,
            entries=explicit + derived,
        )

        write_change_manifest(manifest, self.config.output_dir)
        return manifest

    def _compute_regression(self, run: RunResult):
        """Compare run against most recent comparable baseline."""
        try:
            coverage_mgr = CoverageManager(self.config.output_dir)
            cumulative = coverage_mgr.load()

            baseline = RegressionComparator.find_baseline(
                run, cumulative.recent_runs
            )
            if baseline is None:
                return None

            # Load the full baseline run to get per-scenario statuses
            from pathlib import Path
            import json

            baseline_path = (
                Path(self.config.output_dir)
                / baseline.run_id
                / "run_result.json"
            )
            if not baseline_path.exists():
                return None

            from validation_harness.models import RunResult as RunResultModel
            baseline_run = RunResultModel.model_validate(
                json.loads(baseline_path.read_text())
            )
            baseline_scenarios = {
                s.scenario_id: s.status for s in baseline_run.scenarios
            }

            return RegressionComparator.compare(
                run, baseline_scenarios, baseline.run_id
            )
        except Exception as exc:
            logger.warning("Regression comparison failed: %s", exc)
            return None

    async def _execute_scenario(
        self,
        ctx: ScenarioContext,
        defn: ScenarioDefinition,
        caps: Any,
        failed_ids: set[str],
        skipped_ids: set[str] | None = None,
    ) -> ScenarioResult:
        """Execute a single scenario with skip/dependency checks."""
        scenario_start = datetime.now(timezone.utc)
        start_mono = time.monotonic()

        if skipped_ids is None:
            skipped_ids = set()

        # Skip layer 1: Dependency failures
        dep_failures = [d for d in defn.depends_on if d in failed_ids]
        if dep_failures:
            return ScenarioResult(
                scenario_id=defn.id,
                scenario_name=defn.name,
                feature_area=defn.feature_area,
                status="skipped",
                skip_reason=SkipReason.DEPENDENCY_FAILED,
                prerequisites=defn.depends_on,
                started_at=scenario_start,
                completed_at=datetime.now(timezone.utc),
            )

        # Skip layer 1b: Cascading dependency skips (for scenarios needing data
        # from skipped deps, e.g. retrieval scenarios when ingestion was skipped)
        if defn.skip_when_dependency_skipped:
            skipped_deps = [
                d for d in defn.skip_when_dependency_skipped
                if d in skipped_ids
            ]
            if skipped_deps:
                return ScenarioResult(
                    scenario_id=defn.id,
                    scenario_name=defn.name,
                    feature_area=defn.feature_area,
                    status="skipped",
                    skip_reason=SkipReason.NO_TEST_DATA_AVAILABLE,
                    prerequisites=defn.depends_on,
                    started_at=scenario_start,
                    completed_at=datetime.now(timezone.utc),
                )

        # Skip layer 2: Connector capabilities
        if defn.requires_capabilities and caps:
            met, unmet = check_capabilities(
                ctx.config.connector.type, defn.requires_capabilities
            )
            if not met:
                return ScenarioResult(
                    scenario_id=defn.id,
                    scenario_name=defn.name,
                    feature_area=defn.feature_area,
                    status="skipped",
                    skip_reason=SkipReason.UNSUPPORTED_CONNECTOR_CAPABILITY,
                    prerequisites=defn.depends_on,
                    started_at=scenario_start,
                    completed_at=datetime.now(timezone.utc),
                )

        # Skip layer 3: Entitlements
        for entitlement in defn.requires_entitlements:
            # In Phase 1, we don't have runtime entitlement info, so we check
            # whether the profile feature flag covers the entitlement area.
            # If the entitlement area is disabled in the profile, skip.
            ent_feature = entitlement.replace("_export", "").replace("advanced_", "")
            if not getattr(ctx.config.features, ent_feature, True):
                return ScenarioResult(
                    scenario_id=defn.id,
                    scenario_name=defn.name,
                    feature_area=defn.feature_area,
                    status="skipped",
                    skip_reason=SkipReason.MISSING_ENTITLEMENT,
                    prerequisites=defn.depends_on,
                    started_at=scenario_start,
                    completed_at=datetime.now(timezone.utc),
                )

        # Skip layer 4: Profile feature flags
        for feat in defn.requires_features:
            if not getattr(ctx.config.features, feat, True):
                return ScenarioResult(
                    scenario_id=defn.id,
                    scenario_name=defn.name,
                    feature_area=defn.feature_area,
                    status="skipped",
                    skip_reason=SkipReason.PROFILE_DISABLED_FEATURE,
                    prerequisites=defn.depends_on,
                    started_at=scenario_start,
                    completed_at=datetime.now(timezone.utc),
                )

        # Execute scenario
        try:
            ctx._steps_complete = []
            ctx._current_step = None
            await defn.fn(ctx)

            steps = ctx._collect_steps()
            resources = ctx.drain_created_resources()
            elapsed = (time.monotonic() - start_mono) * 1000

            # Determine overall status
            any_failed = any(s.status in ("failed", "error") for s in steps)
            failure_cat = None
            if any_failed:
                status = "failed"
                failure_cat = FailureCategory.ASSERTION_FAILED
            else:
                status = "passed"

            return ScenarioResult(
                scenario_id=defn.id,
                scenario_name=defn.name,
                feature_area=defn.feature_area,
                status=status,
                failure_category=failure_cat,
                steps=steps,
                created_resources=resources,
                prerequisites=defn.depends_on,
                started_at=scenario_start,
                completed_at=datetime.now(timezone.utc),
                duration_ms=round(elapsed, 2),
            )

        except GatecoError as exc:
            elapsed = (time.monotonic() - start_mono) * 1000
            steps = ctx._collect_steps()
            resources = ctx.drain_created_resources()

            category = FailureCategory.BACKEND_ERROR
            if exc.status_code == 401:
                category = FailureCategory.AUTH_ERROR
            elif exc.status_code == 0:
                category = FailureCategory.SDK_ERROR

            return ScenarioResult(
                scenario_id=defn.id,
                scenario_name=defn.name,
                feature_area=defn.feature_area,
                status="failed",
                failure_category=category,
                steps=steps,
                created_resources=resources,
                prerequisites=defn.depends_on,
                started_at=scenario_start,
                completed_at=datetime.now(timezone.utc),
                duration_ms=round(elapsed, 2),
            )

        except Exception as exc:
            elapsed = (time.monotonic() - start_mono) * 1000
            steps = ctx._collect_steps()
            resources = ctx.drain_created_resources()
            logger.error("Scenario %s error: %s", defn.id, traceback.format_exc())

            return ScenarioResult(
                scenario_id=defn.id,
                scenario_name=defn.name,
                feature_area=defn.feature_area,
                status="error",
                failure_category=FailureCategory.HARNESS_BUG,
                steps=steps,
                created_resources=resources,
                prerequisites=defn.depends_on,
                started_at=scenario_start,
                completed_at=datetime.now(timezone.utc),
                duration_ms=round(elapsed, 2),
            )

    async def _run_cleanup(
        self,
        ctx: ScenarioContext,
        client: AsyncGatecoClient,
        cleanup_mgr: CleanupManager,
        run_id: str,
    ) -> None:
        """Run registered cleanup functions in reverse order, then update manifest."""
        # Run registered cleanup functions
        for fn in reversed(ctx._cleanup_fns):
            try:
                await fn()
            except Exception as exc:
                logger.warning("Cleanup function failed: %s", exc)

        # Attempt manifest-based cleanup for any resources not covered by fns
        manifest_path = cleanup_mgr.manifest_path(run_id)
        if manifest_path.exists():
            try:
                updated = await cleanup_mgr.cleanup_from_manifest(
                    client, manifest_path
                )
                # Re-save manifest with deletion statuses
                cleanup_mgr.save_manifest(run_id, updated)
            except Exception as exc:
                logger.warning("Manifest-based cleanup failed: %s", exc)

    def _compute_feature_rollup(
        self, results: list[ScenarioResult]
    ) -> dict[str, str]:
        """Compute per-feature-area rollup status."""
        features: dict[str, list[str]] = {}
        for r in results:
            features.setdefault(r.feature_area, []).append(r.status)

        rollup: dict[str, str] = {}
        for area, statuses in features.items():
            non_skipped = [s for s in statuses if s != "skipped"]
            if not non_skipped:
                rollup[area] = "skipped"
            elif all(s == "passed" for s in non_skipped):
                rollup[area] = "passed"
            elif all(s in ("failed", "error") for s in non_skipped):
                rollup[area] = "failed"
            else:
                rollup[area] = "partial"

        return rollup
