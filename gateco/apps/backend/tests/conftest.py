"""
Test configuration and fixtures.

This is the main pytest configuration file that imports all fixtures
and sets up the test environment.
"""

import pytest
from httpx import AsyncClient
from httpx import ASGITransport

# Import database fixtures
pytest_plugins = [
    "tests.conftest_db",
    "tests.fixtures.auth_fixtures",
    "tests.fixtures.stripe_fixtures",
]


@pytest.fixture
def anyio_backend():
    """Use asyncio backend for pytest-anyio."""
    return "asyncio"


@pytest.fixture
async def client():
    """
    Create async test client for API testing.

    This client connects directly to the FastAPI app without
    making network requests, enabling fast integration tests.
    """
    from src.gateco.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def client_with_db(client, db_session):
    """
    Create async test client with database session available.

    Use this fixture when you need both HTTP client and database access.
    The database session is injected into the app's dependency system.
    """
    # In a real implementation, you would override the database
    # dependency to use the test session:
    #
    # from src.gateco.database.connection import get_db_session
    # app.dependency_overrides[get_db_session] = lambda: db_session

    yield client


# ============================================================================
# Environment Configuration
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def configure_test_environment():
    """
    Configure environment variables for testing.

    This runs once at the start of the test session.
    """
    import os

    # Set test-specific environment variables
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("DEBUG", "false")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
    os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-for-testing")
    os.environ.setdefault(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/gateco_test"
    )

    # Stripe test keys
    os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_mock")
    os.environ.setdefault("STRIPE_PUBLISHABLE_KEY", "pk_test_mock")
    os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_mock")

    # Disable actual external service calls
    os.environ.setdefault("DISABLE_EXTERNAL_SERVICES", "true")


# ============================================================================
# Common Test Helpers
# ============================================================================

@pytest.fixture
def random_email():
    """Generate a random email address for testing."""
    from uuid import uuid4
    return f"test_{uuid4().hex[:8]}@example.com"


@pytest.fixture
def random_password():
    """Generate a random secure password for testing."""
    import secrets
    return f"TestPass{secrets.token_hex(4)}!"


@pytest.fixture
def valid_signup_payload(random_email, random_password):
    """Generate valid signup request payload."""
    return {
        "email": random_email,
        "password": random_password,
        "name": "Test User",
        "organization_name": "Test Organization",
    }


# ============================================================================
# Response Assertion Helpers
# ============================================================================

class ResponseAssertions:
    """Helper class for common response assertions."""

    @staticmethod
    def assert_success(response, expected_status: int = 200):
        """Assert response is successful with expected status."""
        assert response.status_code == expected_status, (
            f"Expected {expected_status}, got {response.status_code}: {response.text}"
        )

    @staticmethod
    def assert_error(response, expected_status: int, expected_code: str = None):
        """Assert response is an error with expected status and code."""
        assert response.status_code == expected_status, (
            f"Expected {expected_status}, got {response.status_code}: {response.text}"
        )

        if expected_code:
            data = response.json()
            assert "error" in data, f"Response missing 'error' key: {data}"
            assert data["error"]["code"] == expected_code, (
                f"Expected error code '{expected_code}', got '{data['error']['code']}'"
            )

    @staticmethod
    def assert_validation_error(response, field: str = None):
        """Assert response is a validation error."""
        ResponseAssertions.assert_error(response, 422, "VALIDATION_ERROR")

        if field:
            data = response.json()
            details = data.get("error", {}).get("details", {})
            assert field in details, f"Expected validation error for field '{field}'"

    @staticmethod
    def assert_auth_error(response, code: str = "AUTH_INVALID_CREDENTIALS"):
        """Assert response is an authentication error."""
        ResponseAssertions.assert_error(response, 401, code)

    @staticmethod
    def assert_forbidden(response, code: str = "AUTH_PERMISSION_DENIED"):
        """Assert response is a forbidden error."""
        ResponseAssertions.assert_error(response, 403, code)

    @staticmethod
    def assert_not_found(response):
        """Assert response is a not found error."""
        ResponseAssertions.assert_error(response, 404, "RESOURCE_NOT_FOUND")


@pytest.fixture
def assert_response():
    """Provide response assertion helpers."""
    return ResponseAssertions


# ============================================================================
# Markers Configuration
# ============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "stripe: marks tests that require Stripe mocking"
    )
    config.addinivalue_line(
        "markers", "oauth: marks tests that require OAuth mocking"
    )
