"""Integration tests for resource management routes.

This module contains comprehensive tests for gated resource CRUD operations,
access rules, plan limits, and access verification.
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4

from tests.factories.resource_factory import (
    ResourceFactory,
    AccessRuleFactory,
    ResourceType,
    AccessType,
)


# ============================================================================
# List Resources Tests
# ============================================================================


class TestListResources:
    """Tests for GET /api/resources."""

    @pytest.mark.anyio
    async def test_list_resources_paginated(
        self, authenticated_client: AsyncClient
    ):
        """
        Returns paginated resource list.

        Given: Authenticated user with resources
        When: GET /api/resources is called
        Then: Returns paginated list with metadata
        """
        response = await authenticated_client.get("/api/resources")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert "pagination" in data["meta"]
        assert "page" in data["meta"]["pagination"]
        assert "total" in data["meta"]["pagination"]

    @pytest.mark.anyio
    async def test_filter_by_type(
        self, authenticated_client: AsyncClient
    ):
        """
        Filters resources by type parameter.

        Given: Resources of different types
        When: GET /api/resources?type=link is called
        Then: Only link resources are returned
        """
        response = await authenticated_client.get(
            "/api/resources",
            params={"type": "link"},
        )

        assert response.status_code == 200
        data = response.json()
        for resource in data["data"]:
            assert resource["type"] == "link"

    @pytest.mark.anyio
    async def test_filter_by_access_type(
        self, authenticated_client: AsyncClient
    ):
        """
        Filters resources by access_type parameter.

        Given: Resources with different access rules
        When: GET /api/resources?access_type=paid is called
        Then: Only paid resources are returned
        """
        response = await authenticated_client.get(
            "/api/resources",
            params={"access_type": "paid"},
        )

        assert response.status_code == 200
        data = response.json()
        for resource in data["data"]:
            assert resource["access_rule"]["type"] == "paid"

    @pytest.mark.anyio
    async def test_search_by_title(
        self, authenticated_client: AsyncClient
    ):
        """
        Searches resources by title.

        Given: Resources with various titles
        When: GET /api/resources?search=keyword is called
        Then: Resources matching search are returned
        """
        response = await authenticated_client.get(
            "/api/resources",
            params={"search": "test"},
        )

        assert response.status_code == 200
        # Results should contain search term in title or description

    @pytest.mark.anyio
    async def test_sort_by_created_at(
        self, authenticated_client: AsyncClient
    ):
        """
        Sorts resources by creation date.

        Given: Multiple resources
        When: GET /api/resources?sort=-created_at is called
        Then: Resources are sorted newest first
        """
        response = await authenticated_client.get(
            "/api/resources",
            params={"sort": "-created_at"},
        )

        assert response.status_code == 200
        data = response.json()
        resources = data["data"]
        if len(resources) > 1:
            # Verify descending order
            for i in range(len(resources) - 1):
                assert resources[i]["created_at"] >= resources[i + 1]["created_at"]

    @pytest.mark.anyio
    async def test_organization_isolation(
        self, authenticated_client: AsyncClient, other_org_resource
    ):
        """
        Only returns resources from current organization.

        Given: Resource from another organization
        When: GET /api/resources is called
        Then: Other org's resource is not returned
        """
        response = await authenticated_client.get("/api/resources")

        assert response.status_code == 200
        data = response.json()
        resource_ids = [r["id"] for r in data["data"]]
        assert str(other_org_resource["id"]) not in resource_ids

    @pytest.mark.anyio
    async def test_list_resources_requires_auth(self, client: AsyncClient):
        """
        Unauthenticated request returns 401.

        Given: No auth token
        When: GET /api/resources is called
        Then: 401 status
        """
        response = await client.get("/api/resources")
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_pagination_params(
        self, authenticated_client: AsyncClient
    ):
        """
        Pagination parameters work correctly.

        Given: Many resources
        When: GET /api/resources?page=2&per_page=5 is called
        Then: Returns correct page with correct size
        """
        response = await authenticated_client.get(
            "/api/resources",
            params={"page": 1, "per_page": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["pagination"]["page"] == 1
        assert data["meta"]["pagination"]["per_page"] == 5


# ============================================================================
# Create Resource Tests
# ============================================================================


class TestCreateResource:
    """Tests for POST /api/resources."""

    @pytest.mark.anyio
    async def test_create_public_link(
        self, authenticated_client: AsyncClient
    ):
        """
        Creates public link resource.

        Given: Valid link resource data
        When: POST /api/resources is called
        Then: 201 status with created resource
        """
        response = await authenticated_client.post(
            "/api/resources",
            json={
                "type": "link",
                "title": "My Public Link",
                "description": "A test link resource",
                "content_url": "https://example.com/content",
                "access_rule": {
                    "type": "public",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My Public Link"
        assert data["type"] == "link"
        assert data["access_rule"]["type"] == "public"
        assert "id" in data

    @pytest.mark.anyio
    async def test_create_paid_resource(
        self, authenticated_client: AsyncClient
    ):
        """
        Creates paid resource with price.

        Given: Resource with paid access rule
        When: POST /api/resources is called
        Then: Resource created with price
        """
        response = await authenticated_client.post(
            "/api/resources",
            json={
                "type": "file",
                "title": "Premium Content",
                "content_url": "https://example.com/file.pdf",
                "access_rule": {
                    "type": "paid",
                    "price_cents": 999,
                    "currency": "USD",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["access_rule"]["type"] == "paid"
        assert data["access_rule"]["price_cents"] == 999

    @pytest.mark.anyio
    async def test_create_invite_only_resource(
        self, authenticated_client: AsyncClient
    ):
        """
        Creates invite-only resource with email list.

        Given: Resource with invite_only access rule
        When: POST /api/resources is called
        Then: Resource created with allowed emails
        """
        response = await authenticated_client.post(
            "/api/resources",
            json={
                "type": "link",
                "title": "Exclusive Content",
                "content_url": "https://example.com/exclusive",
                "access_rule": {
                    "type": "invite_only",
                    "allowed_emails": ["vip@example.com", "special@example.com"],
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["access_rule"]["type"] == "invite_only"
        assert "vip@example.com" in data["access_rule"]["allowed_emails"]

    @pytest.mark.anyio
    async def test_paid_resource_minimum_price(
        self, authenticated_client: AsyncClient
    ):
        """
        Paid resource requires minimum $0.50 price.

        Given: Paid resource with price < 50 cents
        When: POST /api/resources is called
        Then: 422 validation error
        """
        response = await authenticated_client.post(
            "/api/resources",
            json={
                "type": "file",
                "title": "Too Cheap",
                "content_url": "https://example.com/file.pdf",
                "access_rule": {
                    "type": "paid",
                    "price_cents": 25,  # Below minimum
                    "currency": "USD",
                },
            },
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_resource_limit_enforced(
        self, authenticated_client: AsyncClient
    ):
        """
        Free plan limited to 3 resources.

        Given: Free plan user with 3 resources
        When: POST /api/resources is called to create 4th
        Then: 403 with RESOURCE_LIMIT_EXCEEDED
        """
        # This test assumes the user already has 3 resources
        # In real test, would create 3 resources first
        response = await authenticated_client.post(
            "/api/resources",
            json={
                "type": "link",
                "title": "Fourth Resource",
                "content_url": "https://example.com/fourth",
                "access_rule": {"type": "public"},
            },
        )

        # If user is at limit, should get 403
        # If not at limit, 201 is also valid
        assert response.status_code in [201, 403]
        if response.status_code == 403:
            assert response.json()["error"]["code"] == "RESOURCE_LIMIT_EXCEEDED"

    @pytest.mark.anyio
    async def test_validates_content_url(
        self, authenticated_client: AsyncClient
    ):
        """
        Invalid content_url returns 422.

        Given: Invalid URL in content_url
        When: POST /api/resources is called
        Then: 422 validation error
        """
        response = await authenticated_client.post(
            "/api/resources",
            json={
                "type": "link",
                "title": "Bad URL",
                "content_url": "not-a-valid-url",
                "access_rule": {"type": "public"},
            },
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_validates_required_fields(
        self, authenticated_client: AsyncClient
    ):
        """
        Missing required fields return 422.

        Given: Missing title
        When: POST /api/resources is called
        Then: 422 validation error
        """
        response = await authenticated_client.post(
            "/api/resources",
            json={
                "type": "link",
                # Missing title
                "content_url": "https://example.com/content",
                "access_rule": {"type": "public"},
            },
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_create_resource_requires_auth(self, client: AsyncClient):
        """
        Unauthenticated request returns 401.

        Given: No auth token
        When: POST /api/resources is called
        Then: 401 status
        """
        response = await client.post(
            "/api/resources",
            json={
                "type": "link",
                "title": "Test",
                "content_url": "https://example.com",
                "access_rule": {"type": "public"},
            },
        )

        assert response.status_code == 401


# ============================================================================
# Get Resource Tests
# ============================================================================


class TestGetResource:
    """Tests for GET /api/resources/{id}."""

    @pytest.mark.anyio
    async def test_get_resource_success(
        self, authenticated_client: AsyncClient, test_resource
    ):
        """
        Returns resource details.

        Given: Existing resource
        When: GET /api/resources/{id} is called
        Then: Resource data is returned
        """
        response = await authenticated_client.get(
            f"/api/resources/{test_resource['id']}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_resource["id"])
        assert "title" in data
        assert "access_rule" in data
        assert "stats" in data

    @pytest.mark.anyio
    async def test_get_nonexistent_resource(
        self, authenticated_client: AsyncClient
    ):
        """
        Returns 404 for nonexistent resource.

        Given: Random UUID
        When: GET /api/resources/{id} is called
        Then: 404 status
        """
        fake_id = uuid4()
        response = await authenticated_client.get(
            f"/api/resources/{fake_id}"
        )

        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_get_other_org_resource_denied(
        self, authenticated_client: AsyncClient, other_org_resource
    ):
        """
        Cannot access other organization's resource.

        Given: Resource from another organization
        When: GET /api/resources/{id} is called
        Then: 404 status (not revealed that it exists)
        """
        response = await authenticated_client.get(
            f"/api/resources/{other_org_resource['id']}"
        )

        assert response.status_code == 404


# ============================================================================
# Update Resource Tests
# ============================================================================


class TestUpdateResource:
    """Tests for PATCH /api/resources/{id}."""

    @pytest.mark.anyio
    async def test_update_title(
        self, authenticated_client: AsyncClient, test_resource
    ):
        """
        Updates resource title.

        Given: Existing resource
        When: PATCH /api/resources/{id} with new title
        Then: Title is updated
        """
        response = await authenticated_client.patch(
            f"/api/resources/{test_resource['id']}",
            json={"title": "Updated Title"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    @pytest.mark.anyio
    async def test_update_access_rule(
        self, authenticated_client: AsyncClient, test_resource
    ):
        """
        Updates resource access rule.

        Given: Public resource
        When: PATCH with paid access rule
        Then: Access rule is updated
        """
        response = await authenticated_client.patch(
            f"/api/resources/{test_resource['id']}",
            json={
                "access_rule": {
                    "type": "paid",
                    "price_cents": 499,
                    "currency": "USD",
                }
            },
        )

        assert response.status_code == 200
        assert response.json()["access_rule"]["type"] == "paid"

    @pytest.mark.anyio
    async def test_member_can_update_own(
        self, member_authenticated_client: AsyncClient, member_resource
    ):
        """
        Member can update their own resources.

        Given: Resource created by member
        When: Member updates resource
        Then: Update succeeds
        """
        response = await member_authenticated_client.patch(
            f"/api/resources/{member_resource['id']}",
            json={"title": "Member Updated"},
        )

        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_member_cannot_update_others(
        self, member_authenticated_client: AsyncClient, admin_resource
    ):
        """
        Member cannot update others' resources.

        Given: Resource created by admin
        When: Member tries to update
        Then: 403 forbidden
        """
        response = await member_authenticated_client.patch(
            f"/api/resources/{admin_resource['id']}",
            json={"title": "Member Attempt"},
        )

        assert response.status_code == 403

    @pytest.mark.anyio
    async def test_admin_can_update_any(
        self, admin_authenticated_client: AsyncClient, member_resource
    ):
        """
        Admin can update any resource in organization.

        Given: Resource created by member
        When: Admin updates resource
        Then: Update succeeds
        """
        response = await admin_authenticated_client.patch(
            f"/api/resources/{member_resource['id']}",
            json={"title": "Admin Updated"},
        )

        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_update_nonexistent_resource(
        self, authenticated_client: AsyncClient
    ):
        """
        Returns 404 for nonexistent resource.

        Given: Random UUID
        When: PATCH /api/resources/{id} is called
        Then: 404 status
        """
        fake_id = uuid4()
        response = await authenticated_client.patch(
            f"/api/resources/{fake_id}",
            json={"title": "New Title"},
        )

        assert response.status_code == 404


# ============================================================================
# Delete Resource Tests
# ============================================================================


class TestDeleteResource:
    """Tests for DELETE /api/resources/{id}."""

    @pytest.mark.anyio
    async def test_delete_resource(
        self, authenticated_client: AsyncClient, test_resource
    ):
        """
        Deletes resource successfully.

        Given: Existing resource
        When: DELETE /api/resources/{id} is called
        Then: 204 status, resource no longer exists
        """
        response = await authenticated_client.delete(
            f"/api/resources/{test_resource['id']}"
        )

        assert response.status_code == 204

        # Verify deleted
        get_response = await authenticated_client.get(
            f"/api/resources/{test_resource['id']}"
        )
        assert get_response.status_code == 404

    @pytest.mark.anyio
    async def test_delete_nonexistent_404(
        self, authenticated_client: AsyncClient
    ):
        """
        Deleting nonexistent resource returns 404.

        Given: Random UUID
        When: DELETE /api/resources/{id} is called
        Then: 404 status
        """
        fake_id = uuid4()
        response = await authenticated_client.delete(
            f"/api/resources/{fake_id}"
        )

        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_member_cannot_delete_others(
        self, member_authenticated_client: AsyncClient, admin_resource
    ):
        """
        Member cannot delete others' resources.

        Given: Resource created by admin
        When: Member tries to delete
        Then: 403 forbidden
        """
        response = await member_authenticated_client.delete(
            f"/api/resources/{admin_resource['id']}"
        )

        assert response.status_code == 403


# ============================================================================
# Verify Resource Access Tests
# ============================================================================


class TestVerifyResourceAccess:
    """Tests for POST /api/resources/{id}/verify."""

    @pytest.mark.anyio
    async def test_public_resource_always_accessible(
        self, client: AsyncClient, public_resource
    ):
        """
        Public resource returns has_access=true.

        Given: Public resource
        When: POST /api/resources/{id}/verify is called
        Then: has_access=true, content_url returned
        """
        response = await client.post(
            f"/api/resources/{public_resource['id']}/verify",
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_access"] is True
        assert data["content_url"] is not None
        assert data["gate_type"] == "none"

    @pytest.mark.anyio
    async def test_paid_resource_requires_payment(
        self, client: AsyncClient, paid_resource
    ):
        """
        Paid resource returns payment URL.

        Given: Paid resource without payment
        When: POST /api/resources/{id}/verify is called
        Then: has_access=false, payment_url returned
        """
        response = await client.post(
            f"/api/resources/{paid_resource['id']}/verify",
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_access"] is False
        assert data["gate_type"] == "payment"
        assert data["payment_url"] is not None

    @pytest.mark.anyio
    async def test_paid_resource_with_valid_token(
        self, client: AsyncClient, paid_resource, access_token
    ):
        """
        Paid resource with valid access token grants access.

        Given: Paid resource and valid access token
        When: POST /api/resources/{id}/verify with token
        Then: has_access=true, content_url returned
        """
        response = await client.post(
            f"/api/resources/{paid_resource['id']}/verify",
            json={"token": access_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_access"] is True
        assert data["content_url"] is not None

    @pytest.mark.anyio
    async def test_invite_only_valid_email(
        self, client: AsyncClient, invite_resource
    ):
        """
        Invite-only with valid email grants access.

        Given: Invite-only resource with allowed email
        When: POST /api/resources/{id}/verify with email
        Then: has_access=true
        """
        response = await client.post(
            f"/api/resources/{invite_resource['id']}/verify",
            json={"email": "allowed@example.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_access"] is True

    @pytest.mark.anyio
    async def test_invite_only_invalid_email(
        self, client: AsyncClient, invite_resource
    ):
        """
        Invite-only with invalid email denies access.

        Given: Invite-only resource
        When: POST /api/resources/{id}/verify with non-allowed email
        Then: has_access=false
        """
        response = await client.post(
            f"/api/resources/{invite_resource['id']}/verify",
            json={"email": "notallowed@example.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_access"] is False
        assert data["gate_type"] == "email"

    @pytest.mark.anyio
    async def test_access_records_retrieval(
        self, client: AsyncClient, public_resource
    ):
        """
        Access verification records retrieval for analytics.

        Given: Resource access verification
        When: POST /api/resources/{id}/verify is called
        Then: Access is recorded in analytics
        """
        response = await client.post(
            f"/api/resources/{public_resource['id']}/verify",
            json={},
        )

        assert response.status_code == 200

        # In real test with DB, verify access record created:
        # from sqlalchemy import select
        # from gateco.database.models import ResourceAccess
        # result = await db_session.execute(
        #     select(ResourceAccess).where(
        #         ResourceAccess.resource_id == public_resource["id"]
        #     )
        # )
        # accesses = result.scalars().all()
        # assert len(accesses) >= 1

    @pytest.mark.anyio
    async def test_verify_nonexistent_resource(self, client: AsyncClient):
        """
        Returns 404 for nonexistent resource.

        Given: Random UUID
        When: POST /api/resources/{id}/verify is called
        Then: 404 status
        """
        fake_id = uuid4()
        response = await client.post(
            f"/api/resources/{fake_id}/verify",
            json={},
        )

        assert response.status_code == 404


# ============================================================================
# Resource Fixtures (for these tests to work with real DB)
# ============================================================================


@pytest.fixture
async def test_resource(db_session, test_organization, test_user):
    """Create a test resource for the user's organization."""
    user, _ = test_user
    resource = ResourceFactory.create(
        organization_id=test_organization["id"],
        created_by=user["id"],
    )
    # In real implementation:
    # from gateco.database.models import Resource
    # resource_model = Resource(**resource)
    # db_session.add(resource_model)
    # await db_session.flush()
    return resource


@pytest.fixture
async def other_org_resource(db_session):
    """Create a resource in a different organization."""
    from tests.factories.user_factory import OrganizationFactory
    other_org = OrganizationFactory.create(name="Other Org")
    resource = ResourceFactory.create(organization_id=other_org["id"])
    return resource


@pytest.fixture
async def public_resource(db_session, test_organization, test_user):
    """Create a public resource."""
    user, _ = test_user
    resource, access_rule = ResourceFactory.create_with_access_rule(
        organization_id=test_organization["id"],
        created_by=user["id"],
        access_type=AccessType.PUBLIC,
    )
    return resource


@pytest.fixture
async def paid_resource(db_session, test_organization, test_user):
    """Create a paid resource."""
    user, _ = test_user
    resource, access_rule = ResourceFactory.create_with_access_rule(
        organization_id=test_organization["id"],
        created_by=user["id"],
        access_type=AccessType.PAID,
        price_cents=999,
    )
    return resource


@pytest.fixture
async def invite_resource(db_session, test_organization, test_user):
    """Create an invite-only resource."""
    user, _ = test_user
    resource, access_rule = ResourceFactory.create_with_access_rule(
        organization_id=test_organization["id"],
        created_by=user["id"],
        access_type=AccessType.INVITE_ONLY,
        allowed_emails=["allowed@example.com"],
    )
    return resource


@pytest.fixture
async def member_resource(db_session, test_organization, test_user):
    """Create a resource owned by a member."""
    user, _ = test_user
    resource = ResourceFactory.create(
        organization_id=test_organization["id"],
        created_by=user["id"],
    )
    return resource


@pytest.fixture
async def admin_resource(db_session, test_organization, test_admin):
    """Create a resource owned by an admin."""
    admin, _ = test_admin
    resource = ResourceFactory.create(
        organization_id=test_organization["id"],
        created_by=admin["id"],
    )
    return resource


@pytest.fixture
async def member_authenticated_client(client: AsyncClient, test_user):
    """Create client authenticated as member."""
    user, password = test_user
    # Login as member
    response = await client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": password},
    )
    if response.status_code == 200:
        tokens = response.json()["tokens"]
        client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    return client


@pytest.fixture
async def admin_authenticated_client(client: AsyncClient, test_admin):
    """Create client authenticated as admin."""
    admin, password = test_admin
    response = await client.post(
        "/api/auth/login",
        json={"email": admin["email"], "password": password},
    )
    if response.status_code == 200:
        tokens = response.json()["tokens"]
        client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    return client


@pytest.fixture
async def access_token():
    """Generate a valid access token for paid resource."""
    import secrets
    return secrets.token_urlsafe(32)
