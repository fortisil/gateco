"""Pydantic schemas for metadata binding."""

from pydantic import BaseModel, Field


class BindingEntry(BaseModel):
    vector_id: str = Field(min_length=1, max_length=255)
    external_resource_id: str = Field(min_length=1, max_length=500)
    classification: str | None = None
    sensitivity: str | None = None
    domain: str | None = None
    labels: list[str] | None = None


class BindRequest(BaseModel):
    bindings: list[BindingEntry] = Field(min_length=1, max_length=5000)


class BindResult(BaseModel):
    created_resources: int
    updated_resources: int
    created_chunks: int
    rebound_chunks: int
    errors: list[dict]
    coverage_after: float | None


class CoverageDetail(BaseModel):
    bound_vector_count: int
    total_vector_count: int
    coverage_pct: float | None
    coverage_approximate: bool
    policy_readiness_level: int
    classification_breakdown: dict[str, int]
