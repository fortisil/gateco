"""
Authentication test fixtures.

Provides fixtures for creating test users, organizations, and authentication
headers for integration testing.
"""

import pytest
from typing import AsyncGenerator
from uuid import UUID
from httpx import AsyncClient

from tests.factories.user_factory import (
    UserFactory,
    OrganizationFactory,
    UserRole,
    PlanTier,
)


@pytest.fixture
async def test_organization(db_session) -> dict:
    """
    Create a test organization with free plan.

    Returns:
        dict: Organization data
    """
    org = OrganizationFactory.create()
    # In real implementation with models:
    # from src.gateco.database.models import Organization
    # org_model = Organization(**org)
    # db_session.add(org_model)
    # await db_session.flush()
    return org


@pytest.fixture
async def test_user(db_session, test_organization: dict) -> tuple[dict, str]:
    """
    Create a test user with member role.

    Returns:
        Tuple of (user_dict, plain_password)
    """
    user, password = UserFactory.create(
        organization_id=test_organization["id"],
        role=UserRole.MEMBER,
    )
    # In real implementation:
    # from src.gateco.database.models import User
    # user_model = User(**user)
    # db_session.add(user_model)
    # await db_session.flush()
    return user, password


@pytest.fixture
async def test_owner(db_session, test_organization: dict) -> tuple[dict, str]:
    """
    Create a test owner user.

    Returns:
        Tuple of (user_dict, plain_password)
    """
    user, password = UserFactory.create(
        organization_id=test_organization["id"],
        role=UserRole.OWNER,
    )
    return user, password


@pytest.fixture
async def test_admin(db_session, test_organization: dict) -> tuple[dict, str]:
    """
    Create a test admin user.

    Returns:
        Tuple of (user_dict, plain_password)
    """
    user, password = UserFactory.create(
        organization_id=test_organization["id"],
        role=UserRole.ADMIN,
    )
    return user, password


@pytest.fixture
async def auth_headers(test_user: tuple[dict, str]) -> dict[str, str]:
    """
    Create auth headers with valid JWT for member user.

    Returns:
        dict: Headers with Authorization bearer token
    """
    user, _ = test_user
    # In real implementation, would call:
    # from src.gateco.utils.security import create_access_token
    # token = create_access_token(
    #     user_id=str(user['id']),
    #     org_id=str(user['organization_id']),
    #     role=user['role'],
    #     plan="free",
    # )
    token = f"test_token_{user['id']}"
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def owner_auth_headers(test_owner: tuple[dict, str]) -> dict[str, str]:
    """
    Create auth headers with valid JWT for owner user.

    Returns:
        dict: Headers with Authorization bearer token
    """
    user, _ = test_owner
    token = f"test_token_{user['id']}"
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_auth_headers(test_admin: tuple[dict, str]) -> dict[str, str]:
    """
    Create auth headers with valid JWT for admin user.

    Returns:
        dict: Headers with Authorization bearer token
    """
    user, _ = test_admin
    token = f"test_token_{user['id']}"
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def pro_organization(db_session) -> dict:
    """
    Create a test organization with Pro plan.

    Returns:
        dict: Organization data with Pro plan
    """
    org = OrganizationFactory.create(plan=PlanTier.PRO)
    return org


@pytest.fixture
async def enterprise_organization(db_session) -> dict:
    """
    Create a test organization with Enterprise plan.

    Returns:
        dict: Organization data with Enterprise plan
    """
    org = OrganizationFactory.create(plan=PlanTier.ENTERPRISE)
    return org


@pytest.fixture
async def inactive_user(db_session, test_organization: dict) -> tuple[dict, str]:
    """
    Create an inactive test user.

    Returns:
        Tuple of (user_dict, plain_password)
    """
    user, password = UserFactory.create(
        organization_id=test_organization["id"],
        role=UserRole.MEMBER,
        is_active=False,
    )
    return user, password


@pytest.fixture
async def authenticated_client(
    client: AsyncClient,
    test_user: tuple[dict, str],
) -> AsyncClient:
    """
    Create an HTTP client with authentication headers set.

    This fixture logs in a test user and returns a client
    with the Authorization header already set.

    Returns:
        AsyncClient: HTTP client with auth headers
    """
    user, password = test_user

    # Login to get tokens
    response = await client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": password},
    )

    if response.status_code == 200:
        tokens = response.json()["tokens"]
        client.headers["Authorization"] = f"Bearer {tokens['access_token']}"

    return client


@pytest.fixture
async def owner_authenticated_client(
    client: AsyncClient,
    test_owner: tuple[dict, str],
) -> AsyncClient:
    """
    Create an HTTP client authenticated as organization owner.

    Returns:
        AsyncClient: HTTP client with owner auth headers
    """
    user, password = test_owner

    response = await client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": password},
    )

    if response.status_code == 200:
        tokens = response.json()["tokens"]
        client.headers["Authorization"] = f"Bearer {tokens['access_token']}"

    return client


# ============================================================================
# Signup/Login Response Fixtures
# ============================================================================

@pytest.fixture
def valid_signup_data() -> dict:
    """
    Valid signup request data.

    Returns:
        dict: Valid signup request payload
    """
    return {
        "email": "newuser@example.com",
        "password": "SecurePass123!",
        "name": "New User",
        "organization_name": "New Organization",
    }


@pytest.fixture
def valid_login_data(test_user: tuple[dict, str]) -> dict:
    """
    Valid login request data for test_user.

    Returns:
        dict: Valid login request payload
    """
    user, password = test_user
    return {
        "email": user["email"],
        "password": password,
    }


# ============================================================================
# Helper Functions for Tests
# ============================================================================

async def create_user_and_login(
    client: AsyncClient,
    email: str = None,
    password: str = "TestPass123!",
    name: str = "Test User",
    organization_name: str = "Test Organization",
) -> tuple[dict, dict]:
    """
    Helper to create a user via signup and return user + tokens.

    Args:
        client: HTTP client
        email: User email (generated if not provided)
        password: User password
        name: User name
        organization_name: Organization name

    Returns:
        Tuple of (user_data, tokens_data)
    """
    from uuid import uuid4

    signup_data = {
        "email": email or f"user_{uuid4().hex[:8]}@example.com",
        "password": password,
        "name": name,
        "organization_name": organization_name,
    }

    response = await client.post("/api/auth/signup", json=signup_data)

    if response.status_code == 201:
        data = response.json()
        return data["user"], data["tokens"]

    raise ValueError(f"Signup failed: {response.json()}")


async def get_auth_headers_for_user(
    client: AsyncClient,
    email: str,
    password: str,
) -> dict:
    """
    Helper to login and get auth headers.

    Args:
        client: HTTP client
        email: User email
        password: User password

    Returns:
        dict: Authorization headers
    """
    response = await client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )

    if response.status_code == 200:
        tokens = response.json()["tokens"]
        return {"Authorization": f"Bearer {tokens['access_token']}"}

    raise ValueError(f"Login failed: {response.json()}")
