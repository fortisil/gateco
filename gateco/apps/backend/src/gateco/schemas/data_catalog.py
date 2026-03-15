"""Data catalog request/response schemas."""

from pydantic import BaseModel


class UpdateResourceRequest(BaseModel):
    classification: str | None = None
    sensitivity: str | None = None
    domain: str | None = None
    labels: list[str] | None = None
    encryption_mode: str | None = None


class ResourceResponse(BaseModel):
    id: str
    title: str
    description: str | None
    type: str
    classification: str | None
    sensitivity: str | None
    domain: str | None
    labels: list[str] | None
    encryption_mode: str | None
    source_connector_id: str | None
    view_count: int
    created_at: str
    updated_at: str


class ResourceDetailResponse(ResourceResponse):
    chunks: list[dict]
    applicable_policies: list[dict]
    recent_access: list[dict]
