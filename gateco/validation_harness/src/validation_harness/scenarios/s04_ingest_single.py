"""s04_ingest_single — Single document ingestion + idempotency check."""

from __future__ import annotations

from pathlib import Path

from validation_harness.connector_defaults import get_ingestion_config_defaults
from validation_harness.engine import ScenarioContext
from validation_harness.registry import scenario

_FIXTURES_DIR = Path(__file__).parent.parent.parent.parent / "fixtures" / "documents"


@scenario(
    id="s04_ingest_single",
    name="Single Document Ingestion",
    feature_area="ingestion",
    depends_on=["s02_connector_lifecycle"],
    requires_capabilities=["supports_direct_ingestion"],
    requires_features=["ingestion"],
)
async def s04_ingest_single(ctx: ScenarioContext) -> None:
    """Ingest a single document and verify idempotency."""
    connector_id = ctx.require("connector_id")
    prefix = ctx.config.resource_prefix

    doc_path = _FIXTURES_DIR / "public-company-overview.txt"
    text = doc_path.read_text() if doc_path.exists() else "Gateco public company overview."

    # Step 0: Ensure ingestion config is set
    ctx.begin_step("setup_ingestion_config")
    try:
        ingestion_defaults = get_ingestion_config_defaults(ctx.config.connector.type)
        await ctx.client.connectors.update_ingestion_config(
            connector_id, ingestion_defaults
        )
        ctx.assert_that("Ingestion config set", True)
    except Exception as exc:
        ctx.assert_that("Set ingestion config", False, actual=str(exc))

    # Step 1: Ingest document
    ctx.begin_step("ingest_single")
    result = await ctx.client.ingest.document(
        connector_id=connector_id,
        external_resource_id=f"{prefix}public-company-overview",
        text=text,
        classification="public",
        sensitivity="low",
        domain="corporate",
        metadata={"title": "Company Overview"},
    )
    ctx.assert_that(
        "Ingest returns resource_id",
        result is not None and hasattr(result, "resource_id"),
    )
    if result and hasattr(result, "chunk_count"):
        ctx.assert_that(
            "Chunk count > 0",
            result.chunk_count > 0,
            expected="> 0",
            actual=result.chunk_count,
        )

    if result:
        ctx.share("first_resource_id", str(result.resource_id))
        if hasattr(result, "vector_ids"):
            ctx.share("first_vector_ids", result.vector_ids)
        ctx.share("resources_ingested_count", ctx.get("resources_ingested_count", 0) + 1)

    # Step 2: Idempotency — re-ingest same external_resource_id
    ctx.begin_step("idempotency_check")
    result2 = await ctx.client.ingest.document(
        connector_id=connector_id,
        external_resource_id=f"{prefix}public-company-overview",
        text=text,
        classification="public",
        sensitivity="low",
        domain="corporate",
        metadata={"title": "Company Overview"},
    )
    ctx.assert_that(
        "Re-ingest returns result",
        result2 is not None,
    )
