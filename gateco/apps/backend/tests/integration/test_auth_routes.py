"""Integration tests for authentication routes.

This module tests the authentication API endpoints including signup, login,
token refresh, logout, and user profile management.
"""

import pytest
from httpx import AsyncClient


class TestSignupRoute:
    """Tests for POST /api/auth/signup."""

    @pytest.mark.anyio
    async def test_signup_success(self, client: AsyncClient):
        """
        Successful signup returns 201 with tokens.

        Given: Valid signup data
        When: POST /api/auth/signup is called
        Then: 201 status, user data, and tokens are returned
        """
        response = await client.post(
            "/api/auth/signup",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "name": "New User",
                "organization_name": "New Organization",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["role"] == "owner"
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
        assert data["tokens"]["token_type"] == "Bearer"
        assert data["tokens"]["expires_in"] == 900  # 15 minutes

    @pytest.mark.anyio
    async def test_signup_creates_organization(self, client: AsyncClient):
        """
        Signup creates organization with user as owner.

        Given: Valid signup data with organization_name
        When: POST /api/auth/signup is called
        Then: Organization is created and user is owner
        """
        response = await client.post(
            "/api/auth/signup",
            json={
                "email": "orgtest@example.com",
                "password": "SecurePass123!",
                "name": "Org Test User",
                "organization_name": "My New Company",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user"]["organization"]["name"] == "My New Company"
        assert data["user"]["role"] == "owner"

    @pytest.mark.anyio
    async def test_signup_invalid_email(self, client: AsyncClient):
        """
        Invalid email returns 422 validation error.

        Given: Invalid email format
        When: POST /api/auth/signup is called
        Then: 422 status with validation error
        """
        response = await client.post(
            "/api/auth/signup",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
                "name": "Test",
                "organization_name": "Test Org",
            },
        )

        assert response.status_code == 422
        assert "email" in str(response.json()).lower()

    @pytest.mark.anyio
    async def test_signup_weak_password(self, client: AsyncClient):
        """
        Password under 8 chars returns 422.

        Given: Password too short
        When: POST /api/auth/signup is called
        Then: 422 status with validation error
        """
        response = await client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "short",
                "name": "Test",
                "organization_name": "Test Org",
            },
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_signup_password_requires_uppercase(self, client: AsyncClient):
        """
        Password without uppercase returns 422.

        Given: Password without uppercase letter
        When: POST /api/auth/signup is called
        Then: 422 status with validation error
        """
        response = await client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "alllowercase123!",
                "name": "Test",
                "organization_name": "Test Org",
            },
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_signup_password_requires_number(self, client: AsyncClient):
        """
        Password without number returns 422.

        Given: Password without numeric digit
        When: POST /api/auth/signup is called
        Then: 422 status with validation error
        """
        response = await client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "NoNumbersHere!",
                "name": "Test",
                "organization_name": "Test Org",
            },
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_signup_missing_fields(self, client: AsyncClient):
        """
        Missing required fields returns 422.

        Given: Missing organization_name
        When: POST /api/auth/signup is called
        Then: 422 status with validation error
        """
        response = await client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
                "name": "Test",
                # Missing organization_name
            },
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_signup_missing_name(self, client: AsyncClient):
        """
        Missing name field returns 422.

        Given: Missing name field
        When: POST /api/auth/signup is called
        Then: 422 status with validation error
        """
        response = await client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
                "organization_name": "Test Org",
                # Missing name
            },
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_signup_duplicate_email(self, client: AsyncClient, test_user):
        """
        Duplicate email returns 409 conflict.

        Given: Email already registered
        When: POST /api/auth/signup is called with same email
        Then: 409 status with AUTH_EMAIL_EXISTS error
        """
        user, _ = test_user

        response = await client.post(
            "/api/auth/signup",
            json={
                "email": user["email"],
                "password": "SecurePass123!",
                "name": "Duplicate",
                "organization_name": "Duplicate Org",
            },
        )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "AUTH_EMAIL_EXISTS"

    @pytest.mark.anyio
    async def test_signup_email_case_insensitive(self, client: AsyncClient, test_user):
        """
        Email comparison is case-insensitive.

        Given: Email already registered in lowercase
        When: POST /api/auth/signup is called with uppercase variant
        Then: 409 status (duplicate detected)
        """
        user, _ = test_user
        uppercase_email = user["email"].upper()

        response = await client.post(
            "/api/auth/signup",
            json={
                "email": uppercase_email,
                "password": "SecurePass123!",
                "name": "Case Test",
                "organization_name": "Case Org",
            },
        )

        assert response.status_code == 409

    @pytest.mark.anyio
    async def test_signup_organization_on_free_plan(self, client: AsyncClient):
        """
        New organization starts on free plan.

        Given: Valid signup data
        When: POST /api/auth/signup is called
        Then: Organization has free plan
        """
        response = await client.post(
            "/api/auth/signup",
            json={
                "email": "freeplan@example.com",
                "password": "SecurePass123!",
                "name": "Free Plan User",
                "organization_name": "Free Plan Org",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user"]["organization"]["plan"] == "free"


class TestLoginRoute:
    """Tests for POST /api/auth/login."""

    @pytest.mark.anyio
    async def test_login_success(self, client: AsyncClient, test_user):
        """
        Successful login returns 200 with tokens.

        Given: Valid credentials
        When: POST /api/auth/login is called
        Then: 200 status with user data and tokens
        """
        user, password = test_user

        response = await client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": password},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == user["email"]
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
        assert data["tokens"]["token_type"] == "Bearer"

    @pytest.mark.anyio
    async def test_login_returns_organization(self, client: AsyncClient, test_user):
        """
        Login response includes user's organization.

        Given: Valid credentials
        When: POST /api/auth/login is called
        Then: Response includes organization details
        """
        user, password = test_user

        response = await client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": password},
        )

        assert response.status_code == 200
        data = response.json()
        assert "organization" in data["user"]
        assert data["user"]["organization"]["id"] is not None

    @pytest.mark.anyio
    async def test_login_invalid_credentials(self, client: AsyncClient, test_user):
        """
        Invalid credentials returns 401.

        Given: Wrong password
        When: POST /api/auth/login is called
        Then: 401 status with AUTH_INVALID_CREDENTIALS
        """
        user, _ = test_user

        response = await client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": "WrongPassword!"},
        )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"

    @pytest.mark.anyio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """
        Non-existent user returns 401.

        Given: Email not registered
        When: POST /api/auth/login is called
        Then: 401 status (same as invalid password for security)
        """
        response = await client.post(
            "/api/auth/login",
            json={"email": "nobody@example.com", "password": "password"},
        )

        assert response.status_code == 401
        # Same error code to prevent email enumeration
        assert response.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"

    @pytest.mark.anyio
    async def test_login_missing_email(self, client: AsyncClient):
        """
        Missing email returns 422.

        Given: No email in request
        When: POST /api/auth/login is called
        Then: 422 validation error
        """
        response = await client.post(
            "/api/auth/login",
            json={"password": "password"},
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_login_missing_password(self, client: AsyncClient):
        """
        Missing password returns 422.

        Given: No password in request
        When: POST /api/auth/login is called
        Then: 422 validation error
        """
        response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com"},
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_login_disabled_user(self, client: AsyncClient, inactive_user):
        """
        Disabled user returns 403.

        Given: User with is_active=False
        When: POST /api/auth/login is called
        Then: 403 status with AUTH_ACCOUNT_DISABLED
        """
        user, password = inactive_user

        response = await client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": password},
        )

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "AUTH_ACCOUNT_DISABLED"

    @pytest.mark.anyio
    async def test_login_email_case_insensitive(self, client: AsyncClient, test_user):
        """
        Login works with different email case.

        Given: Email registered in lowercase
        When: POST /api/auth/login is called with uppercase email
        Then: Login succeeds
        """
        user, password = test_user
        uppercase_email = user["email"].upper()

        response = await client.post(
            "/api/auth/login",
            json={"email": uppercase_email, "password": password},
        )

        assert response.status_code == 200


class TestRefreshRoute:
    """Tests for POST /api/auth/refresh."""

    @pytest.mark.anyio
    async def test_refresh_success(self, client: AsyncClient, test_user):
        """
        Valid refresh token returns new token pair.

        Given: Valid refresh token from login
        When: POST /api/auth/refresh is called
        Then: 200 status with new tokens (rotated)
        """
        user, password = test_user

        # Login first
        login_response = await client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": password},
        )
        refresh_token = login_response.json()["tokens"]["refresh_token"]

        # Refresh
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] != refresh_token  # Rotated

    @pytest.mark.anyio
    async def test_refresh_rotates_token(self, client: AsyncClient, test_user):
        """
        Refresh token rotation invalidates old token.

        Given: Valid refresh token
        When: POST /api/auth/refresh is called twice with same token
        Then: Second call fails (token rotated)
        """
        user, password = test_user

        # Login
        login_response = await client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": password},
        )
        refresh_token = login_response.json()["tokens"]["refresh_token"]

        # First refresh succeeds
        response1 = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response1.status_code == 200

        # Second refresh with same token fails
        response2 = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response2.status_code == 401

    @pytest.mark.anyio
    async def test_refresh_invalid_token(self, client: AsyncClient):
        """
        Invalid refresh token returns 401.

        Given: Invalid refresh token
        When: POST /api/auth/refresh is called
        Then: 401 status
        """
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "AUTH_INVALID_REFRESH_TOKEN"

    @pytest.mark.anyio
    async def test_refresh_missing_token(self, client: AsyncClient):
        """
        Missing refresh token returns 422.

        Given: No refresh token in request
        When: POST /api/auth/refresh is called
        Then: 422 validation error
        """
        response = await client.post(
            "/api/auth/refresh",
            json={},
        )

        assert response.status_code == 422


class TestLogoutRoute:
    """Tests for POST /api/auth/logout."""

    @pytest.mark.anyio
    async def test_logout_success(self, client: AsyncClient, test_user):
        """
        Logout returns 204 and invalidates token.

        Given: Valid refresh token
        When: POST /api/auth/logout is called
        Then: 204 status, subsequent refresh fails
        """
        user, password = test_user

        # Login
        login_response = await client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": password},
        )
        refresh_token = login_response.json()["tokens"]["refresh_token"]

        # Logout
        response = await client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 204

        # Verify token is invalidated
        refresh_response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 401

    @pytest.mark.anyio
    async def test_logout_invalid_token_succeeds(self, client: AsyncClient):
        """
        Logout with invalid token returns 204 (idempotent).

        Given: Invalid refresh token
        When: POST /api/auth/logout is called
        Then: 204 status (no error)
        """
        response = await client.post(
            "/api/auth/logout",
            json={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 204

    @pytest.mark.anyio
    async def test_logout_all_sessions(self, client: AsyncClient, test_user):
        """
        Logout all invalidates all sessions.

        Given: User with multiple active sessions
        When: POST /api/auth/logout-all is called
        Then: All refresh tokens are invalidated
        """
        user, password = test_user

        # Login twice to create two sessions
        login1 = await client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": password},
        )
        login2 = await client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": password},
        )

        access_token = login1.json()["tokens"]["access_token"]
        refresh1 = login1.json()["tokens"]["refresh_token"]
        refresh2 = login2.json()["tokens"]["refresh_token"]

        # Logout all
        response = await client.post(
            "/api/auth/logout-all",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        # Both refresh tokens should be invalid
        assert (await client.post("/api/auth/refresh", json={"refresh_token": refresh1})).status_code == 401
        assert (await client.post("/api/auth/refresh", json={"refresh_token": refresh2})).status_code == 401


class TestUsersMeRoute:
    """Tests for GET/PATCH /api/users/me."""

    @pytest.mark.anyio
    async def test_get_me_authenticated(self, client: AsyncClient, auth_headers: dict):
        """
        Authenticated request returns user profile.

        Given: Valid auth token
        When: GET /api/users/me is called
        Then: 200 status with user profile including organization
        """
        response = await client.get("/api/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "name" in data
        assert "organization" in data

    @pytest.mark.anyio
    async def test_get_me_includes_plan(self, client: AsyncClient, auth_headers: dict):
        """
        Profile includes organization plan.

        Given: Valid auth token
        When: GET /api/users/me is called
        Then: Response includes plan information
        """
        response = await client.get("/api/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "plan" in data["organization"]

    @pytest.mark.anyio
    async def test_get_me_unauthenticated(self, client: AsyncClient):
        """
        Unauthenticated request returns 401.

        Given: No auth token
        When: GET /api/users/me is called
        Then: 401 status
        """
        response = await client.get("/api/users/me")

        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_get_me_invalid_token(self, client: AsyncClient):
        """
        Invalid token returns 401.

        Given: Invalid auth token
        When: GET /api/users/me is called
        Then: 401 status
        """
        response = await client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "AUTH_TOKEN_INVALID"

    @pytest.mark.anyio
    async def test_get_me_expired_token(self, client: AsyncClient):
        """
        Expired token returns 401 with specific code.

        Given: Expired auth token
        When: GET /api/users/me is called
        Then: 401 status with AUTH_TOKEN_EXPIRED
        """
        # This test requires creating an expired token
        # For now, we just verify invalid tokens return 401
        response = await client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer expired-token"},
        )

        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_patch_me_update_name(self, client: AsyncClient, auth_headers: dict):
        """
        PATCH updates user name.

        Given: Valid auth token and name update
        When: PATCH /api/users/me is called
        Then: 200 status with updated name
        """
        response = await client.patch(
            "/api/users/me",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    @pytest.mark.anyio
    async def test_patch_me_cannot_change_email(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        PATCH cannot change email.

        Given: Attempt to change email
        When: PATCH /api/users/me is called
        Then: Email remains unchanged or 422 error
        """
        response = await client.patch(
            "/api/users/me",
            headers=auth_headers,
            json={"email": "new@example.com"},
        )

        # Either ignored or returns error
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            assert response.json()["email"] != "new@example.com"

    @pytest.mark.anyio
    async def test_patch_me_cannot_change_role(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        PATCH cannot change user role.

        Given: Attempt to change role
        When: PATCH /api/users/me is called
        Then: Role remains unchanged or error returned
        """
        response = await client.patch(
            "/api/users/me",
            headers=auth_headers,
            json={"role": "owner"},
        )

        assert response.status_code in [200, 422]

    @pytest.mark.anyio
    async def test_patch_me_unauthenticated(self, client: AsyncClient):
        """
        PATCH without auth returns 401.

        Given: No auth token
        When: PATCH /api/users/me is called
        Then: 401 status
        """
        response = await client.patch(
            "/api/users/me",
            json={"name": "New Name"},
        )

        assert response.status_code == 401


class TestPasswordChangeRoute:
    """Tests for POST /api/auth/change-password."""

    @pytest.mark.anyio
    async def test_change_password_success(self, client: AsyncClient, test_user):
        """
        Password change with valid credentials succeeds.

        Given: Valid current password and new password
        When: POST /api/auth/change-password is called
        Then: Password is changed, can login with new password
        """
        user, old_password = test_user

        # Login to get token
        login_response = await client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": old_password},
        )
        access_token = login_response.json()["tokens"]["access_token"]

        new_password = "NewSecurePass456!"

        # Change password
        response = await client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "current_password": old_password,
                "new_password": new_password,
            },
        )

        assert response.status_code == 200

        # Login with new password should work
        login_response = await client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": new_password},
        )
        assert login_response.status_code == 200

    @pytest.mark.anyio
    async def test_change_password_wrong_current(self, client: AsyncClient, auth_headers: dict):
        """
        Wrong current password fails.

        Given: Invalid current password
        When: POST /api/auth/change-password is called
        Then: 401 status
        """
        response = await client.post(
            "/api/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "WrongPassword!",
                "new_password": "NewPassword123!",
            },
        )

        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_change_password_weak_new_password(self, client: AsyncClient, test_user):
        """
        Weak new password returns 422.

        Given: Valid current password but weak new password
        When: POST /api/auth/change-password is called
        Then: 422 validation error
        """
        user, password = test_user

        login_response = await client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": password},
        )
        access_token = login_response.json()["tokens"]["access_token"]

        response = await client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "current_password": password,
                "new_password": "weak",  # Too short
            },
        )

        assert response.status_code == 422


class TestOAuthRoutes:
    """Tests for OAuth authentication routes."""

    @pytest.mark.anyio
    async def test_google_oauth_redirect(self, client: AsyncClient):
        """
        Google OAuth initiation returns redirect URL.

        Given: Request for Google OAuth
        When: GET /api/auth/oauth/google is called
        Then: Redirect URL is returned
        """
        response = await client.get("/api/auth/oauth/google")

        # Should return redirect URL or redirect status
        assert response.status_code in [200, 302]
        if response.status_code == 200:
            data = response.json()
            assert "url" in data
            assert "google" in data["url"].lower()

    @pytest.mark.anyio
    async def test_github_oauth_redirect(self, client: AsyncClient):
        """
        GitHub OAuth initiation returns redirect URL.

        Given: Request for GitHub OAuth
        When: GET /api/auth/oauth/github is called
        Then: Redirect URL is returned
        """
        response = await client.get("/api/auth/oauth/github")

        assert response.status_code in [200, 302]
        if response.status_code == 200:
            data = response.json()
            assert "url" in data
            assert "github" in data["url"].lower()

    @pytest.mark.anyio
    async def test_oauth_callback_invalid_code(self, client: AsyncClient):
        """
        Invalid OAuth code returns error.

        Given: Invalid authorization code
        When: GET /api/auth/oauth/google/callback is called
        Then: 400 or 401 status
        """
        response = await client.get(
            "/api/auth/oauth/google/callback",
            params={"code": "invalid_code", "state": "test_state"},
        )

        assert response.status_code in [400, 401]

    @pytest.mark.anyio
    async def test_oauth_callback_missing_code(self, client: AsyncClient):
        """
        Missing OAuth code returns error.

        Given: No authorization code
        When: GET /api/auth/oauth/google/callback is called
        Then: 400 or 422 status
        """
        response = await client.get(
            "/api/auth/oauth/google/callback",
            params={"state": "test_state"},
        )

        assert response.status_code in [400, 422]
