"""Policy request/response schemas."""

from pydantic import BaseModel, Field


class PolicyRuleRequest(BaseModel):
    description: str | None = None
    effect: str  # "allow" | "deny"
    conditions: list[dict] | None = None
    priority: int = 0


class CreatePolicyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    type: str  # "rbac" | "abac" | "rebac"
    effect: str  # "allow" | "deny"
    resource_selectors: list[dict] | None = None
    rules: list[PolicyRuleRequest] = Field(default_factory=list)


class UpdatePolicyRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    effect: str | None = None
    resource_selectors: list[dict] | None = None
    rules: list[PolicyRuleRequest] | None = None


class PolicyRuleResponse(BaseModel):
    id: str
    description: str | None
    effect: str
    conditions: list[dict] | None
    priority: int


class PolicyResponse(BaseModel):
    id: str
    name: str
    description: str | None
    type: str
    status: str
    effect: str
    resource_selectors: list[dict] | None
    version: int
    rules: list[PolicyRuleResponse]
    created_by: str | None
    created_at: str
    updated_at: str
