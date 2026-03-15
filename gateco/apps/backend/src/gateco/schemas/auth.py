"""Auth-related request/response schemas matching FE contract types."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    rememberMe: bool = False  # noqa: N815


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    organization_name: str = Field(min_length=1, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    plan: str  # "free" | "pro" | "enterprise"


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str  # "org_admin" | "security_admin" | "data_owner" | "developer"
    organization: OrganizationResponse
    created_at: str  # ISO 8601 UTC


class LoginResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse


class UpdateUserRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ExchangeCodeRequest(BaseModel):
    code: str  # one-time auth code from OAuth callback (D3)
