"""Integration tests for user management routes.

This module tests user-related API endpoints including profile retrieval,
updates, organization user management, and invitations.

Dependencies:
- Task 1.5: Auth routes implementation (for user routes)
- auth_fixtures for test users with various roles
"""

import pytest
from httpx import AsyncClient


class TestGetCurrentUser:
    """Tests for GET /api/users/me.

    This endpoint returns the current authenticated user's profile
    along with their organization and plan details.
    """

    @pytest.mark.anyio
    async def test_returns_user_profile(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        Authenticated user can get their profile.

        Given: Valid auth token
        When: GET /api/users/me is called
        Then: 200 with user profile
        """
        response = await client.get("/api/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "id" in data["user"]
        assert "email" in data["user"]
        assert "name" in data["user"]
        assert "role" in data["user"]

    @pytest.mark.anyio
    async def test_includes_organization(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        Response includes user's organization.

        Given: Valid auth token
        When: GET /api/users/me is called
        Then: Response includes org details
        """
        response = await client.get("/api/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "org" in data
        assert "id" in data["org"]
        assert "name" in data["org"]
        assert "slug" in data["org"]

    @pytest.mark.anyio
    async def test_includes_plan_with_entitlements(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        Response includes plan with entitlements.

        Given: Valid auth token
        When: GET /api/users/me is called
        Then: plan object includes entitlements
        """
        response = await client.get("/api/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "plan" in data
        assert "tier" in data["plan"]
        assert "entitlements" in data["plan"]

    @pytest.mark.anyio
    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        """
        Unauthenticated request returns 401.

        Given: No auth token
        When: GET /api/users/me is called
        Then: 401 AUTH_TOKEN_MISSING
        """
        response = await client.get("/api/users/me")

        assert response.status_code == 401
        assert response.json()["error"]["code"] in [
            "AUTH_TOKEN_MISSING",
            "AUTH_TOKEN_INVALID",
        ]

    @pytest.mark.anyio
    async def test_invalid_token_returns_401(self, client: AsyncClient):
        """
        Invalid token returns 401.

        Given: Malformed auth token
        When: GET /api/users/me is called
        Then: 401 AUTH_TOKEN_INVALID
        """
        response = await client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "AUTH_TOKEN_INVALID"


class TestUpdateCurrentUser:
    """Tests for PATCH /api/users/me.

    Users can update limited profile fields (name).
    Email and role changes are restricted.
    """

    @pytest.mark.anyio
    async def test_updates_name(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        User can update their name.

        Given: Valid auth token and new name
        When: PATCH /api/users/me is called
        Then: 200 with updated name
        """
        response = await client.patch(
            "/api/users/me",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    @pytest.mark.anyio
    async def test_rejects_email_change(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        User cannot change their email.

        Given: Valid auth token and email change attempt
        When: PATCH /api/users/me is called
        Then: Email remains unchanged or 422 error
        """
        # Get original email
        original = await client.get("/api/users/me", headers=auth_headers)
        original_email = original.json()["user"]["email"]

        response = await client.patch(
            "/api/users/me",
            headers=auth_headers,
            json={"email": "new-email@example.com"},
        )

        # Either ignored (200 with same email) or rejected (422)
        if response.status_code == 200:
            assert response.json()["email"] == original_email
        else:
            assert response.status_code == 422

    @pytest.mark.anyio
    async def test_rejects_role_change(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        User cannot change their own role.

        Given: Valid auth token and role change attempt
        When: PATCH /api/users/me is called
        Then: Role remains unchanged
        """
        # Get original role
        original = await client.get("/api/users/me", headers=auth_headers)
        original_role = original.json()["user"]["role"]

        response = await client.patch(
            "/api/users/me",
            headers=auth_headers,
            json={"role": "owner" if original_role != "owner" else "member"},
        )

        if response.status_code == 200:
            assert response.json()["role"] == original_role

    @pytest.mark.anyio
    async def test_validates_name_length(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        Name must be valid length.

        Given: Empty name
        When: PATCH /api/users/me is called
        Then: 422 validation error
        """
        response = await client.patch(
            "/api/users/me",
            headers=auth_headers,
            json={"name": ""},
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        """
        Unauthenticated PATCH returns 401.

        Given: No auth token
        When: PATCH /api/users/me is called
        Then: 401 status
        """
        response = await client.patch(
            "/api/users/me",
            json={"name": "New Name"},
        )

        assert response.status_code == 401


class TestListOrganizationUsers:
    """Tests for GET /api/organizations/current/users.

    Only owners and admins can list organization users.
    """

    @pytest.mark.anyio
    async def test_owner_can_list_users(
        self, client: AsyncClient, owner_auth_headers: dict
    ):
        """
        Organization owner can list all users.

        Given: Owner auth token
        When: GET /api/organizations/current/users is called
        Then: 200 with list of users
        """
        response = await client.get(
            "/api/organizations/current/users",
            headers=owner_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert isinstance(data["users"], list)

    @pytest.mark.anyio
    async def test_admin_can_list_users(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """
        Admin can list organization users.

        Given: Admin auth token
        When: GET /api/organizations/current/users is called
        Then: 200 with list of users
        """
        response = await client.get(
            "/api/organizations/current/users",
            headers=admin_auth_headers,
        )

        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_member_cannot_list_users(
        self, client: AsyncClient, member_auth_headers: dict
    ):
        """
        Regular member cannot list users.

        Given: Member auth token
        When: GET /api/organizations/current/users is called
        Then: 403 forbidden
        """
        response = await client.get(
            "/api/organizations/current/users",
            headers=member_auth_headers,
        )

        assert response.status_code == 403

    @pytest.mark.anyio
    async def test_includes_user_roles(
        self, client: AsyncClient, owner_auth_headers: dict
    ):
        """
        User list includes roles.

        Given: Owner auth token
        When: GET /api/organizations/current/users is called
        Then: Each user has role field
        """
        response = await client.get(
            "/api/organizations/current/users",
            headers=owner_auth_headers,
        )

        assert response.status_code == 200
        for user in response.json()["users"]:
            assert "role" in user
            assert user["role"] in ["owner", "admin", "member"]


class TestInviteUser:
    """Tests for POST /api/organizations/current/invites.

    Owners can invite any role. Admins can invite members only.
    """

    @pytest.mark.anyio
    async def test_owner_can_invite_member(
        self, client: AsyncClient, owner_auth_headers: dict
    ):
        """
        Owner can invite new members.

        Given: Owner auth token and invite data
        When: POST /api/organizations/current/invites is called
        Then: 201 with invite details
        """
        response = await client.post(
            "/api/organizations/current/invites",
            headers=owner_auth_headers,
            json={
                "email": "newmember@example.com",
                "role": "member",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "invite_code" in data
        assert data["email"] == "newmember@example.com"

    @pytest.mark.anyio
    async def test_owner_can_invite_admin(
        self, client: AsyncClient, owner_auth_headers: dict
    ):
        """
        Owner can invite admins.

        Given: Owner auth token
        When: POST invite with role=admin
        Then: 201 success
        """
        response = await client.post(
            "/api/organizations/current/invites",
            headers=owner_auth_headers,
            json={
                "email": "newadmin@example.com",
                "role": "admin",
            },
        )

        assert response.status_code == 201

    @pytest.mark.anyio
    async def test_admin_can_invite_members(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """
        Admin can invite members.

        Given: Admin auth token
        When: POST invite with role=member
        Then: 201 success
        """
        response = await client.post(
            "/api/organizations/current/invites",
            headers=admin_auth_headers,
            json={
                "email": "another-member@example.com",
                "role": "member",
            },
        )

        assert response.status_code == 201

    @pytest.mark.anyio
    async def test_admin_cannot_invite_admin(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """
        Admin cannot invite other admins.

        Given: Admin auth token
        When: POST invite with role=admin
        Then: 403 forbidden
        """
        response = await client.post(
            "/api/organizations/current/invites",
            headers=admin_auth_headers,
            json={
                "email": "another-admin@example.com",
                "role": "admin",
            },
        )

        assert response.status_code == 403

    @pytest.mark.anyio
    async def test_admin_cannot_invite_owner(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """
        Admin cannot invite owners.

        Given: Admin auth token
        When: POST invite with role=owner
        Then: 403 forbidden
        """
        response = await client.post(
            "/api/organizations/current/invites",
            headers=admin_auth_headers,
            json={
                "email": "new-owner@example.com",
                "role": "owner",
            },
        )

        assert response.status_code == 403

    @pytest.mark.anyio
    async def test_member_cannot_invite(
        self, client: AsyncClient, member_auth_headers: dict
    ):
        """
        Member cannot send invites.

        Given: Member auth token
        When: POST invite
        Then: 403 forbidden
        """
        response = await client.post(
            "/api/organizations/current/invites",
            headers=member_auth_headers,
            json={
                "email": "someone@example.com",
                "role": "member",
            },
        )

        assert response.status_code == 403

    @pytest.mark.anyio
    async def test_validates_email_format(
        self, client: AsyncClient, owner_auth_headers: dict
    ):
        """
        Invalid email returns 422.

        Given: Invalid email format
        When: POST invite
        Then: 422 validation error
        """
        response = await client.post(
            "/api/organizations/current/invites",
            headers=owner_auth_headers,
            json={
                "email": "not-an-email",
                "role": "member",
            },
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_duplicate_invite_returns_409(
        self, client: AsyncClient, owner_auth_headers: dict
    ):
        """
        Duplicate invite returns conflict.

        Given: Pending invite exists for email
        When: POST invite with same email
        Then: 409 conflict
        """
        email = "duplicate-invite@example.com"

        # First invite
        await client.post(
            "/api/organizations/current/invites",
            headers=owner_auth_headers,
            json={"email": email, "role": "member"},
        )

        # Second invite
        response = await client.post(
            "/api/organizations/current/invites",
            headers=owner_auth_headers,
            json={"email": email, "role": "member"},
        )

        assert response.status_code == 409


class TestRemoveUser:
    """Tests for DELETE /api/organizations/current/users/{id}.

    Only owners can remove users. Cannot remove self.
    """

    @pytest.mark.anyio
    async def test_owner_can_remove_member(
        self, client: AsyncClient, owner_auth_headers: dict, test_member: dict
    ):
        """
        Owner can remove members.

        Given: Owner auth token and member ID
        When: DELETE user is called
        Then: 204 success
        """
        response = await client.delete(
            f"/api/organizations/current/users/{test_member['id']}",
            headers=owner_auth_headers,
        )

        assert response.status_code == 204

    @pytest.mark.anyio
    async def test_owner_can_remove_admin(
        self, client: AsyncClient, owner_auth_headers: dict, test_admin: dict
    ):
        """
        Owner can remove admins.

        Given: Owner auth token and admin ID
        When: DELETE user is called
        Then: 204 success
        """
        response = await client.delete(
            f"/api/organizations/current/users/{test_admin['id']}",
            headers=owner_auth_headers,
        )

        assert response.status_code == 204

    @pytest.mark.anyio
    async def test_owner_cannot_remove_self(
        self, client: AsyncClient, owner_auth_headers: dict, test_owner: dict
    ):
        """
        Owner cannot remove themselves.

        Given: Owner auth token
        When: DELETE self is called
        Then: 400 error
        """
        response = await client.delete(
            f"/api/organizations/current/users/{test_owner['id']}",
            headers=owner_auth_headers,
        )

        assert response.status_code == 400
        assert "cannot remove" in response.json()["error"]["message"].lower()

    @pytest.mark.anyio
    async def test_admin_cannot_remove_users(
        self, client: AsyncClient, admin_auth_headers: dict, test_member: dict
    ):
        """
        Admin cannot remove users.

        Given: Admin auth token
        When: DELETE user is called
        Then: 403 forbidden
        """
        response = await client.delete(
            f"/api/organizations/current/users/{test_member['id']}",
            headers=admin_auth_headers,
        )

        assert response.status_code == 403

    @pytest.mark.anyio
    async def test_member_cannot_remove_users(
        self, client: AsyncClient, member_auth_headers: dict, test_admin: dict
    ):
        """
        Member cannot remove users.

        Given: Member auth token
        When: DELETE user is called
        Then: 403 forbidden
        """
        response = await client.delete(
            f"/api/organizations/current/users/{test_admin['id']}",
            headers=member_auth_headers,
        )

        assert response.status_code == 403

    @pytest.mark.anyio
    async def test_cannot_remove_user_from_other_org(
        self, client: AsyncClient, owner_auth_headers: dict, other_org_user: dict
    ):
        """
        Cannot remove user from different organization.

        Given: User from different org
        When: DELETE user is called
        Then: 404 not found
        """
        response = await client.delete(
            f"/api/organizations/current/users/{other_org_user['id']}",
            headers=owner_auth_headers,
        )

        assert response.status_code == 404
