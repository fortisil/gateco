"""s05_ingest_batch — Batch ingestion of remaining fixture documents."""

from __future__ import annotations

from pathlib import Path

from validation_harness.engine import ScenarioContext
from validation_harness.registry import scenario

_FIXTURES_DIR = Path(__file__).parent.parent.parent.parent / "fixtures" / "documents"

# Remaining 7 documents (public-company-overview handled by s04)
_BATCH_DOCS = [
    ("public-product-faq", "public", "low", "product"),
    ("internal-engineering-design", "internal", "medium", "engineering"),
    ("internal-quarterly-roadmap", "internal", "medium", "strategy"),
    ("confidential-board-minutes", "confidential", "high", "governance"),
    ("confidential-acquisition-target", "confidential", "high", "finance"),
    ("restricted-compensation-data", "restricted", "critical", "hr"),
    ("restricted-security-audit", "restricted", "critical", "security"),
]


@scenario(
    id="s05_ingest_batch",
    name="Batch Document Ingestion",
    feature_area="ingestion",
    depends_on=["s04_ingest_single"],
    requires_capabilities=["supports_batch_ingestion"],
    requires_features=["ingestion"],
)
async def s05_ingest_batch(ctx: ScenarioContext) -> None:
    """Batch ingest remaining 7 fixture documents."""
    connector_id = ctx.require("connector_id")
    prefix = ctx.config.resource_prefix

    ctx.begin_step("batch_ingest")

    records = []
    for name, classification, sensitivity, domain in _BATCH_DOCS:
        doc_path = _FIXTURES_DIR / f"{name}.txt"
        text = doc_path.read_text() if doc_path.exists() else f"Fixture document: {name}"

        records.append({
            "external_resource_id": f"{prefix}{name}",
            "text": text,
            "classification": classification,
            "sensitivity": sensitivity,
            "domain": domain,
            "metadata": {"title": name.replace("-", " ").title()},
        })

    result = await ctx.client.ingest.batch(
        connector_id=connector_id,
        records=records,
    )

    ctx.assert_that(
        "Batch ingest returns result",
        result is not None,
    )

    if result:
        succeeded = getattr(result, "succeeded", 0)
        failed = getattr(result, "failed", 0)
        ctx.assert_that(
            "All 7 documents succeeded",
            succeeded == 7,
            expected=7,
            actual=succeeded,
        )
        ctx.assert_that(
            "No documents failed",
            failed == 0,
            expected=0,
            actual=failed,
        )

        # Track ingested count for readiness verification
        ctx.share(
            "resources_ingested_count",
            ctx.get("resources_ingested_count", 0) + succeeded,
        )

        # Share all resource IDs
        if hasattr(result, "results"):
            resource_ids = []
            for r in result.results:
                if hasattr(r, "resource_id"):
                    resource_ids.append(str(r.resource_id))
            first_id = ctx.get("first_resource_id")
            if first_id:
                resource_ids.insert(0, first_id)
            ctx.share("all_resource_ids", resource_ids)
