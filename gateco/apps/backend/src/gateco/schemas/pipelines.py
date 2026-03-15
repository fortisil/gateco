"""Pipeline request/response schemas."""

from pydantic import BaseModel, Field


class CreatePipelineRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    source_connector_id: str
    envelope_config: dict | None = None
    schedule: str = "manual"


class UpdatePipelineRequest(BaseModel):
    name: str | None = None
    envelope_config: dict | None = None
    status: str | None = None
    schedule: str | None = None


class PipelineResponse(BaseModel):
    id: str
    name: str
    source_connector_id: str
    envelope_config: dict | None
    status: str
    schedule: str
    last_run: str | None
    records_processed: int
    error_count: int
    created_at: str
    updated_at: str


class PipelineRunResponse(BaseModel):
    id: str
    pipeline_id: str
    status: str
    records_processed: int
    errors: int
    started_at: str
    completed_at: str | None
    duration_ms: int | None
