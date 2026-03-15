"""
Resource test fixtures.

Provides fixtures for creating test resources with various configurations
for testing gated content functionality.
"""

import pytest
from typing import Optional
from uuid import UUID

from tests.factories.resource_factory import (
    ResourceFactory,
    AccessRuleFactory,
    ResourceAccessFactory,
    InviteFactory,
    ResourceType,
    AccessType,
)


# ============================================================================
# Basic Resource Fixtures
# ============================================================================


@pytest.fixture
async def test_resource(db_session, test_organization: dict) -> dict:
    """
    Create a test link resource with public access.

    Returns:
        dict: Resource data with public access rule
    """
    resource, access_rule = ResourceFactory.create_with_access_rule(
        organization_id=test_organization["id"],
        title="Test Resource",
        resource_type=ResourceType.LINK,
        access_type=AccessType.PUBLIC,
    )
    # In real implementation with models:
    # from src.gateco.database.models import GatedResource, AccessRule
    # resource_model = GatedResource(**resource)
    # access_rule_model = AccessRule(**access_rule)
    # db_session.add(resource_model)
    # db_session.add(access_rule_model)
    # await db_session.flush()

    # Combine for convenience
    resource["access_rule"] = access_rule
    return resource


@pytest.fixture
async def test_file_resource(db_session, test_organization: dict) -> dict:
    """
    Create a test file resource with public access.

    Returns:
        dict: File resource data
    """
    resource, access_rule = ResourceFactory.create_with_access_rule(
        organization_id=test_organization["id"],
        title="Test File Resource",
        resource_type=ResourceType.FILE,
        content_url="https://example.com/files/test.pdf",
        access_type=AccessType.PUBLIC,
    )
    resource["access_rule"] = access_rule
    return resource


@pytest.fixture
async def test_video_resource(db_session, test_organization: dict) -> dict:
    """
    Create a test video resource with public access.

    Returns:
        dict: Video resource data
    """
    resource, access_rule = ResourceFactory.create_with_access_rule(
        organization_id=test_organization["id"],
        title="Test Video Resource",
        resource_type=ResourceType.VIDEO,
        content_url="https://example.com/videos/test.mp4",
        thumbnail_url="https://example.com/thumbnails/test.jpg",
        access_type=AccessType.PUBLIC,
    )
    resource["access_rule"] = access_rule
    return resource


# ============================================================================
# Access Type Specific Fixtures
# ============================================================================


@pytest.fixture
async def public_resource(db_session, test_organization: dict) -> dict:
    """
    Create a public access resource.

    Returns:
        dict: Resource with public access rule
    """
    resource, access_rule = ResourceFactory.create_with_access_rule(
        organization_id=test_organization["id"],
        title="Public Resource",
        access_type=AccessType.PUBLIC,
    )
    resource["access_rule"] = access_rule
    return resource


@pytest.fixture
async def paid_resource(db_session, test_organization: dict) -> dict:
    """
    Create a paid access resource ($9.99).

    Returns:
        dict: Resource with paid access rule
    """
    resource, access_rule = ResourceFactory.create_with_access_rule(
        organization_id=test_organization["id"],
        title="Paid Resource",
        access_type=AccessType.PAID,
        price_cents=999,
        currency="USD",
    )
    resource["access_rule"] = access_rule
    return resource


@pytest.fixture
async def expensive_resource(db_session, test_organization: dict) -> dict:
    """
    Create an expensive paid resource ($49.99).

    Returns:
        dict: Resource with high-price access rule
    """
    resource, access_rule = ResourceFactory.create_with_access_rule(
        organization_id=test_organization["id"],
        title="Premium Resource",
        access_type=AccessType.PAID,
        price_cents=4999,
        currency="USD",
    )
    resource["access_rule"] = access_rule
    return resource


@pytest.fixture
async def invite_resource(db_session, test_organization: dict) -> dict:
    """
    Create an invite-only access resource.

    Returns:
        dict: Resource with invite-only access rule
    """
    resource, access_rule = ResourceFactory.create_with_access_rule(
        organization_id=test_organization["id"],
        title="Invite-Only Resource",
        access_type=AccessType.INVITE_ONLY,
        allowed_emails=["allowed@example.com", "vip@example.com"],
    )
    resource["access_rule"] = access_rule
    return resource


# ============================================================================
# Plan Limit Testing Fixtures
# ============================================================================


@pytest.fixture
async def max_free_resources(db_session, test_organization: dict) -> list[dict]:
    """
    Create maximum resources allowed for free plan (3).

    Use this to test resource limit enforcement.

    Returns:
        list[dict]: List of 3 resources
    """
    resources = []
    for i in range(3):
        resource, access_rule = ResourceFactory.create_with_access_rule(
            organization_id=test_organization["id"],
            title=f"Free Plan Resource {i + 1}",
            access_type=AccessType.PUBLIC,
        )
        resource["access_rule"] = access_rule
        resources.append(resource)
    return resources


@pytest.fixture
async def many_resources(db_session, test_organization: dict) -> list[dict]:
    """
    Create many resources for pagination testing (25).

    Returns:
        list[dict]: List of 25 resources
    """
    resources = []
    for i in range(25):
        resource, access_rule = ResourceFactory.create_with_access_rule(
            organization_id=test_organization["id"],
            title=f"Resource {i + 1:02d}",
            access_type=AccessType.PUBLIC,
        )
        resource["access_rule"] = access_rule
        resources.append(resource)
    return resources


# ============================================================================
# Multi-Organization Fixtures
# ============================================================================


@pytest.fixture
async def another_organization(db_session) -> dict:
    """
    Create a second organization for cross-org testing.

    Returns:
        dict: Organization data
    """
    from tests.factories.user_factory import OrganizationFactory

    org = OrganizationFactory.create()
    return org


@pytest.fixture
async def other_org_resource(db_session, another_organization: dict) -> dict:
    """
    Create a resource belonging to a different organization.

    Use this to test cross-organization access denial.

    Returns:
        dict: Resource from another organization
    """
    resource, access_rule = ResourceFactory.create_with_access_rule(
        organization_id=another_organization["id"],
        title="Other Org Resource",
        access_type=AccessType.PUBLIC,
    )
    resource["access_rule"] = access_rule
    return resource


# ============================================================================
# Resource with Statistics Fixtures
# ============================================================================


@pytest.fixture
async def popular_resource(db_session, test_organization: dict) -> dict:
    """
    Create a resource with high view statistics.

    Returns:
        dict: Resource with stats
    """
    resource, access_rule = ResourceFactory.create_with_access_rule(
        organization_id=test_organization["id"],
        title="Popular Resource",
        access_type=AccessType.PUBLIC,
    )
    resource["access_rule"] = access_rule
    resource["stats"] = {
        "view_count": 1500,
        "unique_viewers": 800,
        "revenue_cents": 0,
    }
    return resource


@pytest.fixture
async def revenue_generating_resource(db_session, test_organization: dict) -> dict:
    """
    Create a paid resource with revenue statistics.

    Returns:
        dict: Paid resource with revenue stats
    """
    resource, access_rule = ResourceFactory.create_with_access_rule(
        organization_id=test_organization["id"],
        title="Revenue Generator",
        access_type=AccessType.PAID,
        price_cents=999,
    )
    resource["access_rule"] = access_rule
    resource["stats"] = {
        "view_count": 200,
        "unique_viewers": 150,
        "revenue_cents": 49950,  # 50 sales at $9.99
    }
    return resource


# ============================================================================
# Access Log Fixtures
# ============================================================================


@pytest.fixture
async def resource_with_access_logs(
    db_session, test_organization: dict
) -> tuple[dict, list[dict]]:
    """
    Create a resource with associated access logs.

    Returns:
        Tuple of (resource_dict, list of access_log_dicts)
    """
    resource, access_rule = ResourceFactory.create_with_access_rule(
        organization_id=test_organization["id"],
        title="Resource With Logs",
        access_type=AccessType.PUBLIC,
    )
    resource["access_rule"] = access_rule

    access_logs = [
        ResourceAccessFactory.create(
            resource_id=resource["id"],
            accessor_email=f"user{i}@example.com",
            accessor_ip=f"192.168.1.{i}",
            country="US",
        )
        for i in range(10)
    ]

    return resource, access_logs


# ============================================================================
# Invite Fixtures
# ============================================================================


@pytest.fixture
async def resource_with_invites(
    db_session, test_organization: dict
) -> tuple[dict, list[dict]]:
    """
    Create an invite-only resource with pending invites.

    Returns:
        Tuple of (resource_dict, list of invite_dicts)
    """
    resource, access_rule = ResourceFactory.create_with_access_rule(
        organization_id=test_organization["id"],
        title="Invite Resource",
        access_type=AccessType.INVITE_ONLY,
        allowed_emails=["allowed@example.com"],
    )
    resource["access_rule"] = access_rule

    invites = [
        InviteFactory.create(
            resource_id=resource["id"],
            email=f"invite{i}@example.com",
            used=i < 3,  # First 3 are used
        )
        for i in range(5)
    ]

    return resource, invites


@pytest.fixture
async def expired_invite(db_session, invite_resource: dict) -> dict:
    """
    Create an expired invite for an invite-only resource.

    Returns:
        dict: Expired invite data
    """
    from datetime import timedelta

    invite = InviteFactory.create(
        resource_id=invite_resource["id"],
        email="expired@example.com",
        expires_in_days=-1,  # Already expired
    )
    return invite


# ============================================================================
# Helper Functions
# ============================================================================


async def create_resource_for_user(
    db_session,
    organization_id: str,
    user_id: str,
    title: str = "User Resource",
    access_type: AccessType = AccessType.PUBLIC,
) -> dict:
    """
    Helper to create a resource owned by a specific user.

    Args:
        db_session: Database session
        organization_id: Organization ID
        user_id: User ID who creates the resource
        title: Resource title
        access_type: Access rule type

    Returns:
        dict: Resource data
    """
    resource, access_rule = ResourceFactory.create_with_access_rule(
        organization_id=organization_id,
        created_by=user_id,
        title=title,
        access_type=access_type,
    )
    resource["access_rule"] = access_rule
    return resource


def create_resource_request_payload(
    resource_type: str = "link",
    title: str = "New Resource",
    content_url: str = "https://example.com/content",
    access_type: str = "public",
    price_cents: Optional[int] = None,
    allowed_emails: Optional[list[str]] = None,
) -> dict:
    """
    Create a valid resource creation request payload.

    Args:
        resource_type: Type of resource
        title: Resource title
        content_url: Content URL
        access_type: Access rule type
        price_cents: Price in cents (for paid)
        allowed_emails: Allowed emails (for invite-only)

    Returns:
        dict: Request payload
    """
    payload = {
        "type": resource_type,
        "title": title,
        "content_url": content_url,
        "access_rule": {
            "type": access_type,
        },
    }

    if access_type == "paid":
        payload["access_rule"]["price_cents"] = price_cents or 999
        payload["access_rule"]["currency"] = "USD"
    elif access_type == "invite_only":
        payload["access_rule"]["allowed_emails"] = allowed_emails or ["test@example.com"]

    return payload
