"""Machine-readable skip and failure reason taxonomy."""

from __future__ import annotations

from enum import Enum


class SkipReason(str, Enum):
    """Why a scenario was skipped."""

    UNSUPPORTED_CONNECTOR_CAPABILITY = "unsupported_connector_capability"
    UNSUPPORTED_CONNECTOR_TIER = "unsupported_connector_tier"
    MISSING_ENTITLEMENT = "missing_entitlement"
    MISSING_EXTERNAL_CREDENTIALS = "missing_external_credentials"
    PROFILE_DISABLED_FEATURE = "profile_disabled_feature"
    ENVIRONMENT_NOT_CONFIGURED = "environment_not_configured"
    NOT_YET_SUPPORTED_BY_BACKEND = "not_yet_supported_by_backend"
    DEPENDENCY_FAILED = "dependency_failed"
    NO_TEST_DATA_AVAILABLE = "no_test_data_available"


class FailureCategory(str, Enum):
    """Root-cause classification for a failed scenario."""

    BACKEND_ERROR = "backend_error"
    SDK_ERROR = "sdk_error"
    CONNECTOR_ERROR = "connector_error"
    IDP_ERROR = "idp_error"
    ASSERTION_FAILED = "assertion_failed"
    FIXTURE_ERROR = "fixture_error"
    CLEANUP_ERROR = "cleanup_error"
    TIMEOUT = "timeout"
    UNEXPECTED_SCHEMA = "unexpected_schema"
    AUTH_ERROR = "auth_error"
    HARNESS_BUG = "harness_bug"
