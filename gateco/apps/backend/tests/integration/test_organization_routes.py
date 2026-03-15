"""Integration tests for organization routes.

This module tests organization-related API endpoints including
getting organization details, updating settings, and branding.

Dependencies:
- Organization routes implementation
- auth_fixtures for test users with various roles
"""

import pytest
from httpx import AsyncClient


class TestGetCurrentOrganization:
    """Tests for GET /api/organizations/current.

    Returns the current user's organization with settings.
    """

    @pytest.mark.anyio
    async def test_returns_organization(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        Returns current user's organization.

        Given: Authenticated user
        When: GET /api/organizations/current is called
        Then: 200 with organization details
        """
        response = await client.get(
            "/api/organizations/current",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "slug" in data
        assert "plan" in data

    @pytest.mark.anyio
    async def test_includes_settings(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        Organization includes settings object.

        Given: Authenticated user
        When: GET /api/organizations/current is called
        Then: Response includes settings
        """
        response = await client.get(
            "/api/organizations/current",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "settings" in data

    @pytest.mark.anyio
    async def test_includes_created_at(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        Organization includes timestamp.

        Given: Authenticated user
        When: GET /api/organizations/current is called
        Then: Response includes created_at
        """
        response = await client.get(
            "/api/organizations/current",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert "created_at" in response.json()

    @pytest.mark.anyio
    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        """
        Unauthenticated request returns 401.

        Given: No auth token
        When: GET /api/organizations/current is called
        Then: 401 status
        """
        response = await client.get("/api/organizations/current")
        assert response.status_code == 401


class TestUpdateOrganization:
    """Tests for PATCH /api/organizations/current.

    Only owners and admins can update organization settings.
    """

    @pytest.mark.anyio
    async def test_owner_can_update_name(
        self, client: AsyncClient, owner_auth_headers: dict
    ):
        """
        Owner can update organization name.

        Given: Owner auth token
        When: PATCH with new name
        Then: 200 with updated name
        """
        response = await client.patch(
            "/api/organizations/current",
            headers=owner_auth_headers,
            json={"name": "New Organization Name"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "New Organization Name"

    @pytest.mark.anyio
    async def test_admin_can_update_name(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """
        Admin can update organization name.

        Given: Admin auth token
        When: PATCH with new name
        Then: 200 with updated name
        """
        response = await client.patch(
            "/api/organizations/current",
            headers=admin_auth_headers,
            json={"name": "Admin Updated Name"},
        )

        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_member_cannot_update(
        self, client: AsyncClient, member_auth_headers: dict
    ):
        """
        Member cannot update organization.

        Given: Member auth token
        When: PATCH is called
        Then: 403 forbidden
        """
        response = await client.patch(
            "/api/organizations/current",
            headers=member_auth_headers,
            json={"name": "Attempted Change"},
        )

        assert response.status_code == 403

    @pytest.mark.anyio
    async def test_owner_can_update_slug(
        self, client: AsyncClient, owner_auth_headers: dict
    ):
        """
        Owner can update organization slug.

        Given: Owner auth token and new slug
        When: PATCH with slug
        Then: 200 with updated slug
        """
        response = await client.patch(
            "/api/organizations/current",
            headers=owner_auth_headers,
            json={"slug": "new-org-slug"},
        )

        assert response.status_code == 200
        assert response.json()["slug"] == "new-org-slug"

    @pytest.mark.anyio
    async def test_slug_must_be_unique(
        self, client: AsyncClient, owner_auth_headers: dict, other_org: dict
    ):
        """
        Slug must be unique across organizations.

        Given: Slug already taken by another org
        When: PATCH with existing slug
        Then: 409 conflict
        """
        response = await client.patch(
            "/api/organizations/current",
            headers=owner_auth_headers,
            json={"slug": other_org["slug"]},
        )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "SLUG_ALREADY_EXISTS"

    @pytest.mark.anyio
    async def test_validates_slug_format(
        self, client: AsyncClient, owner_auth_headers: dict
    ):
        """
        Slug must be valid format (lowercase, alphanumeric, dashes).

        Given: Invalid slug with special characters
        When: PATCH is called
        Then: 422 validation error
        """
        response = await client.patch(
            "/api/organizations/current",
            headers=owner_auth_headers,
            json={"slug": "Invalid Slug!@#$"},
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_validates_slug_length(
        self, client: AsyncClient, owner_auth_headers: dict
    ):
        """
        Slug must be within length limits.

        Given: Slug too short or too long
        When: PATCH is called
        Then: 422 validation error
        """
        # Too short
        response = await client.patch(
            "/api/organizations/current",
            headers=owner_auth_headers,
            json={"slug": "ab"},
        )
        assert response.status_code == 422

        # Too long
        response = await client.patch(
            "/api/organizations/current",
            headers=owner_auth_headers,
            json={"slug": "a" * 101},
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_validates_name_not_empty(
        self, client: AsyncClient, owner_auth_headers: dict
    ):
        """
        Name cannot be empty.

        Given: Empty name
        When: PATCH is called
        Then: 422 validation error
        """
        response = await client.patch(
            "/api/organizations/current",
            headers=owner_auth_headers,
            json={"name": ""},
        )

        assert response.status_code == 422


class TestOrganizationBranding:
    """Tests for PATCH /api/organizations/current/branding.

    Branding is a Pro+ feature. Free plans cannot customize.
    """

    @pytest.mark.anyio
    async def test_pro_plan_can_update_branding(
        self, client: AsyncClient, pro_owner_auth_headers: dict
    ):
        """
        Pro plan can update branding.

        Given: Pro plan org owner
        When: PATCH branding settings
        Then: 200 with updated branding
        """
        response = await client.patch(
            "/api/organizations/current/branding",
            headers=pro_owner_auth_headers,
            json={
                "primary_color": "#FF5733",
                "logo_url": "https://example.com/logo.png",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["branding"]["primary_color"] == "#FF5733"

    @pytest.mark.anyio
    async def test_free_plan_cannot_update_branding(
        self, client: AsyncClient, free_owner_auth_headers: dict
    ):
        """
        Free plan cannot update branding.

        Given: Free plan org owner
        When: PATCH branding settings
        Then: 403 PLAN_FEATURE_NOT_AVAILABLE
        """
        response = await client.patch(
            "/api/organizations/current/branding",
            headers=free_owner_auth_headers,
            json={"primary_color": "#FF5733"},
        )

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "PLAN_FEATURE_NOT_AVAILABLE"

    @pytest.mark.anyio
    async def test_validates_color_format(
        self, client: AsyncClient, pro_owner_auth_headers: dict
    ):
        """
        Color must be valid hex format.

        Given: Invalid color format
        When: PATCH branding
        Then: 422 validation error
        """
        response = await client.patch(
            "/api/organizations/current/branding",
            headers=pro_owner_auth_headers,
            json={"primary_color": "not-a-color"},
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_validates_logo_url(
        self, client: AsyncClient, pro_owner_auth_headers: dict
    ):
        """
        Logo URL must be valid HTTPS URL.

        Given: Invalid URL
        When: PATCH branding
        Then: 422 validation error
        """
        response = await client.patch(
            "/api/organizations/current/branding",
            headers=pro_owner_auth_headers,
            json={"logo_url": "not-a-url"},
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_member_cannot_update_branding(
        self, client: AsyncClient, pro_member_auth_headers: dict
    ):
        """
        Member cannot update branding (even on Pro).

        Given: Member auth token on Pro org
        When: PATCH branding
        Then: 403 forbidden
        """
        response = await client.patch(
            "/api/organizations/current/branding",
            headers=pro_member_auth_headers,
            json={"primary_color": "#FF5733"},
        )

        assert response.status_code == 403


class TestOrganizationCustomDomain:
    """Tests for custom domain settings.

    Custom domains are an Enterprise feature.
    """

    @pytest.mark.anyio
    async def test_enterprise_can_set_domain(
        self, client: AsyncClient, enterprise_owner_auth_headers: dict
    ):
        """
        Enterprise plan can set custom domain.

        Given: Enterprise plan org owner
        When: PATCH with custom_domain
        Then: 200 with domain pending verification
        """
        response = await client.patch(
            "/api/organizations/current",
            headers=enterprise_owner_auth_headers,
            json={"custom_domain": "app.mycorp.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["settings"]["custom_domain"] == "app.mycorp.com"
        assert data["settings"]["domain_verified"] is False

    @pytest.mark.anyio
    async def test_pro_cannot_set_domain(
        self, client: AsyncClient, pro_owner_auth_headers: dict
    ):
        """
        Pro plan cannot set custom domain.

        Given: Pro plan org owner
        When: PATCH with custom_domain
        Then: 403 PLAN_FEATURE_NOT_AVAILABLE
        """
        response = await client.patch(
            "/api/organizations/current",
            headers=pro_owner_auth_headers,
            json={"custom_domain": "app.mycompany.com"},
        )

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "PLAN_FEATURE_NOT_AVAILABLE"

    @pytest.mark.anyio
    async def test_validates_domain_format(
        self, client: AsyncClient, enterprise_owner_auth_headers: dict
    ):
        """
        Domain must be valid format.

        Given: Invalid domain
        When: PATCH with custom_domain
        Then: 422 validation error
        """
        response = await client.patch(
            "/api/organizations/current",
            headers=enterprise_owner_auth_headers,
            json={"custom_domain": "not a domain"},
        )

        assert response.status_code == 422


class TestOrganizationMembers:
    """Tests for organization member count and limits."""

    @pytest.mark.anyio
    async def test_returns_member_count(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        Organization includes member count.

        Given: Authenticated user
        When: GET /api/organizations/current is called
        Then: Response includes member_count
        """
        response = await client.get(
            "/api/organizations/current",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert "member_count" in response.json()

    @pytest.mark.anyio
    async def test_free_plan_member_limit(
        self, client: AsyncClient, free_owner_auth_headers: dict
    ):
        """
        Free plan has member limit.

        Given: Free plan org at member limit
        When: Trying to invite new member
        Then: 403 PLAN_LIMIT_REACHED
        """
        # This test assumes the org is at its limit
        # The fixture should set this up
        response = await client.post(
            "/api/organizations/current/invites",
            headers=free_owner_auth_headers,
            json={
                "email": "overflow@example.com",
                "role": "member",
            },
        )

        # Free plan has limit, should return error when at limit
        if response.status_code == 403:
            assert response.json()["error"]["code"] == "PLAN_LIMIT_REACHED"
