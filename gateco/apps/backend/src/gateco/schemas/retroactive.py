"""Pydantic schemas for retroactive policy registration."""

from pydantic import BaseModel, Field


class RetroactiveRegisterRequest(BaseModel):
    """Request to retroactively register unmanaged vectors as gated resources."""

    connector_id: str
    scan_limit: int = Field(1000, ge=1, le=10000)
    default_classification: str | None = None
    default_sensitivity: str | None = None
    default_domain: str | None = None
    default_labels: list[str] | None = None
    grouping_strategy: str = "individual"  # "individual" | "regex" | "prefix"
    grouping_pattern: str | None = None
    dry_run: bool = False


class RetroactiveRegisterResponse(BaseModel):
    """Response from retroactive registration."""

    status: str  # "success" | "partial_success" | "dry_run"
    scanned_vectors: int
    already_registered: int
    newly_registered: int
    resources_created: int
    errors: list[dict]
