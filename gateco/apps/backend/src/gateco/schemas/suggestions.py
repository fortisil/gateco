"""Classification suggestion request/response schemas."""

from pydantic import BaseModel, Field


class SuggestClassificationsRequest(BaseModel):
    """Request body for ``POST /api/connectors/{id}/suggest-classifications``."""

    scan_limit: int = Field(1000, ge=1, le=10000)
    grouping_strategy: str = "individual"
    grouping_pattern: str | None = None
    sample_size: int = Field(10, ge=1, le=100)


class ClassificationSuggestion(BaseModel):
    """A single classification suggestion for a resource group."""

    resource_key: str
    vector_ids: list[str] = []
    suggested_classification: str | None = None
    suggested_sensitivity: str | None = None
    suggested_domain: str | None = None
    confidence: float = 0.0
    reasoning: str | None = None


class SuggestClassificationsResponse(BaseModel):
    """Response from ``POST /api/connectors/{id}/suggest-classifications``."""

    status: str
    scanned_vectors: int = 0
    suggestions: list[ClassificationSuggestion] = []


class ApplySuggestionsRequest(BaseModel):
    """Request body for ``POST /api/connectors/{id}/apply-suggestions``."""

    suggestions: list[ClassificationSuggestion]


class ApplySuggestionsResponse(BaseModel):
    """Response from ``POST /api/connectors/{id}/apply-suggestions``."""

    status: str
    applied: int = 0
    resources_created: int = 0
    errors: list[dict] = []
