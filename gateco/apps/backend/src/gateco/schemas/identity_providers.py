"""Identity provider request/response schemas."""

from pydantic import BaseModel, Field

# Secret fields by IdP type
IDP_SECRET_FIELDS = {
    "azure_entra_id": ["client_secret"],
    "aws_iam": ["secret_access_key"],
    "gcp": ["service_account_json"],
    "okta": ["api_token"],
}


class CreateIdentityProviderRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: str  # IdentityProviderType value
    config: dict = Field(default_factory=dict)
    sync_config: dict | None = None


class UpdateIdentityProviderRequest(BaseModel):
    name: str | None = None
    config: dict | None = None
    sync_config: dict | None = None


class IdentityProviderResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str
    config: dict
    sync_config: dict | None
    principal_count: int
    group_count: int
    last_sync: str | None
    error_message: str | None
    created_at: str
    updated_at: str
