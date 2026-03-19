"""Tests that CI profiles parse correctly and route to the expected IDP adapter.

No real API calls — uses monkeypatch for env vars with realistic dummy values.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from validation_harness.config import HarnessConfig, load_profile

# Resolved path to profiles/ directory
PROFILES_DIR = Path(__file__).resolve().parent.parent / "profiles"

# Map profile filename → (expected IDP type, expected adapter dotted path)
PROFILE_EXPECTATIONS = {
    "ci-okta.yaml": ("okta", "gateco.services.idp_adapters.okta.OktaAdapter"),
    "ci-azure.yaml": ("azure_entra_id", "gateco.services.idp_adapters.azure.AzureEntraAdapter"),
    "ci-aws-iam.yaml": ("aws_iam", "gateco.services.idp_adapters.aws.AWSIAMAdapter"),
    "ci-gcp.yaml": ("gcp", "gateco.services.idp_adapters.gcp.GCPAdapter"),
}

# Realistic (non-fake) env var values per profile — ensures _is_stub_config returns False
ENV_VARS_BY_PROFILE = {
    "ci-okta.yaml": {
        "OKTA_DOMAIN": "dev-12345678.okta.com",
        "OKTA_API_TOKEN": "00abcDEF123_realtoken",
    },
    "ci-azure.yaml": {
        "AZURE_TENANT_ID": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "AZURE_CLIENT_ID": "11111111-2222-3333-4444-555555555555",
        "AZURE_CLIENT_SECRET": "~realAzureClientSecret.value",
    },
    "ci-aws-iam.yaml": {
        "AWS_IDENTITY_STORE_ID": "d-1234567890",
        "AWS_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
        "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    },
    "ci-gcp.yaml": {
        "GCP_DOMAIN": "example.com",
        "GCP_ADMIN_EMAIL": "admin@example.com",
        "GCP_SERVICE_ACCOUNT_JSON": '{"type":"service_account","project_id":"my-project"}',
    },
}


@pytest.fixture(params=PROFILE_EXPECTATIONS.keys())
def profile_fixture(request, monkeypatch):
    """Parametrized fixture yielding (profile_name, config, expected_type, expected_adapter)."""
    profile_name = request.param
    expected_type, expected_adapter = PROFILE_EXPECTATIONS[profile_name]

    # Set env vars with realistic dummy values
    for var, val in ENV_VARS_BY_PROFILE[profile_name].items():
        monkeypatch.setenv(var, val)

    config = load_profile(PROFILES_DIR / profile_name)
    return profile_name, config, expected_type, expected_adapter


class TestProfileParsing:
    """Verify CI profiles parse into valid HarnessConfig."""

    def test_parses_to_harness_config(self, profile_fixture):
        _, config, _, _ = profile_fixture
        assert isinstance(config, HarnessConfig)

    def test_identity_provider_type_matches(self, profile_fixture):
        _, config, expected_type, _ = profile_fixture
        assert config.identity_provider.type == expected_type


class TestAdapterRouting:
    """Verify adapter dispatch routes to the correct class."""

    def test_adapter_class_in_registry(self, profile_fixture):
        from gateco.services.idp_adapters import ADAPTER_CLASSES
        _, config, _, expected_adapter = profile_fixture
        assert ADAPTER_CLASSES.get(config.identity_provider.type) == expected_adapter

    def test_adapter_class_importable(self, profile_fixture):
        _, _, _, expected_adapter = profile_fixture
        module_path, class_name = expected_adapter.rsplit(".", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        assert cls is not None


class TestNonStubRouting:
    """Verify realistic config values are not treated as stub."""

    def test_not_detected_as_stub(self, profile_fixture):
        from gateco.services.idp_adapters import _is_stub_config
        _, config, _, _ = profile_fixture
        assert _is_stub_config(config.identity_provider.config) is False

    def test_no_required_env_resolves_empty(self, profile_fixture):
        """All required env vars should resolve to non-empty strings."""
        profile_name, config, _, _ = profile_fixture
        idp_config = config.identity_provider.config
        for key, value in idp_config.items():
            if isinstance(value, str):
                assert value != "", (
                    f"Profile {profile_name}: identity_provider.config.{key} "
                    f"resolved to empty string — missing env var?"
                )
