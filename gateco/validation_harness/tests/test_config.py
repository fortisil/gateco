"""Tests for profile loading and environment variable interpolation."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from validation_harness.config import HarnessConfig, _interpolate_env, load_profile


class TestInterpolateEnv:
    def test_simple_substitution(self, monkeypatch):
        monkeypatch.setenv("MY_VAR", "hello")
        assert _interpolate_env("${MY_VAR:-default}") == "hello"

    def test_default_when_missing(self):
        result = _interpolate_env("${NONEXISTENT_VAR_12345:-fallback}")
        assert result == "fallback"

    def test_empty_default(self):
        result = _interpolate_env("${NONEXISTENT_VAR_12345:-}")
        assert result == ""

    def test_no_interpolation_needed(self):
        assert _interpolate_env("plain string") == "plain string"

    def test_nested_dict(self, monkeypatch):
        monkeypatch.setenv("DB_HOST", "localhost")
        data = {"url": "http://${DB_HOST:-127.0.0.1}:8000", "name": "test"}
        result = _interpolate_env(data)
        assert result["url"] == "http://localhost:8000"
        assert result["name"] == "test"

    def test_nested_list(self, monkeypatch):
        monkeypatch.setenv("ITEM", "val")
        data = ["${ITEM:-x}", "static"]
        result = _interpolate_env(data)
        assert result == ["val", "static"]

    def test_non_string_passthrough(self):
        assert _interpolate_env(42) == 42
        assert _interpolate_env(True) is True
        assert _interpolate_env(None) is None


class TestLoadProfile:
    def test_load_valid_profile(self):
        content = """
profile_name: test
base_url: "http://localhost:9000"
credentials:
  email: test@example.com
  password: secret
connector:
  type: pinecone
  config: {}
features:
  auth: true
  billing: false
output_dir: /tmp/output
resource_prefix: "test-"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            f.flush()

            config = load_profile(f.name)

        os.unlink(f.name)

        assert config.profile_name == "test"
        assert config.base_url == "http://localhost:9000"
        assert config.credentials.email == "test@example.com"
        assert config.connector.type == "pinecone"
        assert config.features.auth is True
        assert config.features.billing is False
        assert config.resource_prefix == "test-"

    def test_load_with_env_interpolation(self, monkeypatch):
        monkeypatch.setenv("TEST_BASE_URL", "http://staging:8080")
        content = """
profile_name: staging
base_url: "${TEST_BASE_URL:-http://localhost:8000}"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            f.flush()

            config = load_profile(f.name)

        os.unlink(f.name)
        assert config.base_url == "http://staging:8080"

    def test_load_missing_profile(self):
        with pytest.raises(FileNotFoundError):
            load_profile("/nonexistent/path.yaml")

    def test_defaults_applied(self):
        content = "profile_name: minimal\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            f.flush()

            config = load_profile(f.name)

        os.unlink(f.name)
        assert config.base_url == "http://localhost:8000"
        assert config.credentials.email == "admin@acmecorp.com"
        assert config.connector.type == "pgvector"
        assert config.resource_prefix == "vh-"
