"""YAML profile loader with environment variable interpolation."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ConnectorConfig(BaseModel):
    """Connector settings from profile."""

    type: str = "pgvector"
    config: dict[str, Any] = Field(default_factory=dict)


class IdentityProviderConfig(BaseModel):
    """Identity provider settings from profile — used by s18 to create the test IDP."""

    type: str = "okta"
    config: dict[str, Any] = Field(default_factory=lambda: {"domain": "vh-test.okta.com", "api_token": "vh-fake-token"})


class CredentialsConfig(BaseModel):
    """Authentication credentials from profile."""

    email: str = "admin@acmecorp.com"
    password: str = "password123"


class FeaturesConfig(BaseModel):
    """Feature flags — which feature areas to exercise."""

    auth: bool = True
    connectors: bool = True
    ingestion: bool = True
    retroactive: bool = True
    policies: bool = True
    retrievals: bool = True
    metadata_resolution: bool = True
    simulator: bool = True
    audit: bool = True
    dashboard: bool = True
    billing: bool = True
    identity_providers: bool = True


class HarnessConfig(BaseModel):
    """Top-level harness configuration loaded from a YAML profile."""

    profile_name: str = "local-dev"
    base_url: str = "http://localhost:8000"
    credentials: CredentialsConfig = Field(default_factory=CredentialsConfig)
    connector: ConnectorConfig = Field(default_factory=ConnectorConfig)
    identity_provider: IdentityProviderConfig = Field(default_factory=IdentityProviderConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    output_dir: str = ".validation_harness/output"
    resource_prefix: str = "vh-"
    provider_mode: str = "native"  # "native" | "emulated_local_postgres"


# ---------------------------------------------------------------------------
# Environment variable interpolation
# ---------------------------------------------------------------------------

_ENV_VAR_PATTERN = re.compile(r"\$\{([^}:]+)(?::-([^}]*))?\}")


def _interpolate_env(value: Any) -> Any:
    """Recursively substitute ${VAR:-default} patterns in strings."""
    if isinstance(value, str):
        def _replace(match: re.Match) -> str:
            var_name = match.group(1)
            default = match.group(2) if match.group(2) is not None else ""
            return os.environ.get(var_name, default)
        return _ENV_VAR_PATTERN.sub(_replace, value)
    if isinstance(value, dict):
        return {k: _interpolate_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate_env(item) for item in value]
    return value


def load_profile(path: str | Path) -> HarnessConfig:
    """Load a YAML profile and return a validated HarnessConfig."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {path}")

    with open(path) as f:
        raw = yaml.safe_load(f) or {}

    interpolated = _interpolate_env(raw)
    return HarnessConfig.model_validate(interpolated)
