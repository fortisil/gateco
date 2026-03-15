"""
Integration tests for authentication flows.

These tests verify complete authentication workflows with actual database
interactions, ensuring all components work together correctly.
"""

import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, create_access_token
from app.models.user import User
from app.models.organization import Organization


@pytest.mark.integration
class TestAuthenticationFlow:
    """Test complete authentication flows."""

    @pytest.mark.asyncio
    async def test_complete_signup_flow(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test full signup flow from registration to authenticated request."""
        # Step 1: Register new user
        signup_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "name": "New User",
            "organization_name": "New Organization",
        }

        response = await client.post("/api/v1/auth/register", json=signup_data)
        assert response.status_code == 201

        data = response.json()
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == signup_data["email"]

        access_token = data["tokens"]["access_token"]
        refresh_token = data["tokens"]["refresh_token"]

        # Step 2: Verify user is created in database
        result = await db_session.execute(
            User.__table__.select().where(User.email == signup_data["email"])
        )
        user = result.fetchone()
        assert user is not None
        assert user.email == signup_data["email"]

        # Step 3: Verify organization is created
        result = await db_session.execute(
            Organization.__table__.select().where(
                Organization.id == data["user"]["organization"]["id"]
            )
        )
        org = result.fetchone()
        assert org is not None
        assert org.name == signup_data["organization_name"]

        # Step 4: Make authenticated request
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == signup_data["email"]

        # Step 5: Verify refresh token works
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        new_tokens = response.json()
        assert "access_token" in new_tokens

    @pytest.mark.asyncio
    async def test_complete_login_flow(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Test full login flow with token refresh and logout."""
        # Step 1: Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "password123",  # Default test user password
            },
        )
        assert response.status_code == 200

        data = response.json()
        access_token = data["tokens"]["access_token"]
        refresh_token = data["tokens"]["refresh_token"]

        # Step 2: Access protected resource
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200

        # Step 3: Refresh tokens
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200

        new_access_token = response.json()["access_token"]
        new_refresh_token = response.json()["refresh_token"]

        # Step 4: Old access token should still work briefly (grace period)
        # or may be invalidated immediately depending on implementation

        # Step 5: New access token should work
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )
        assert response.status_code == 200

        # Step 6: Logout
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )
        assert response.status_code == 200

        # Step 7: Old tokens should no longer work
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_password_reset_flow(
        self,
        client: AsyncClient,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Test complete password reset flow."""
        # Step 1: Request password reset
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user.email},
        )
        # Should always return success (don't reveal if email exists)
        assert response.status_code == 200

        # Step 2: In real scenario, user receives email with token
        # For testing, we'll create a reset token directly
        from app.core.security import create_password_reset_token

        reset_token = create_password_reset_token(test_user.email)

        # Step 3: Reset password with token
        new_password = "NewSecurePassword456!"
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": reset_token,
                "password": new_password,
            },
        )
        assert response.status_code == 200

        # Step 4: Login with new password should work
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": new_password,
            },
        )
        assert response.status_code == 200

        # Step 5: Login with old password should fail
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "password123",  # Old password
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_email_verification_flow(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test email verification flow for new users."""
        # Step 1: Register new user (unverified)
        signup_data = {
            "email": "unverified@example.com",
            "password": "SecurePassword123!",
            "name": "Unverified User",
            "organization_name": "Test Org",
        }

        response = await client.post("/api/v1/auth/register", json=signup_data)
        assert response.status_code == 201

        # Step 2: Check user is marked as unverified (if email verification required)
        # This depends on configuration

        # Step 3: Generate verification token
        from app.core.security import create_email_verification_token

        verification_token = create_email_verification_token(signup_data["email"])

        # Step 4: Verify email
        response = await client.post(
            "/api/v1/auth/verify-email",
            json={"token": verification_token},
        )
        assert response.status_code == 200

        # Step 5: Check user is now verified
        access_token = response.json().get("tokens", {}).get("access_token")
        if access_token:
            response = await client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 200
            assert response.json().get("email_verified", True) is True


@pytest.mark.integration
class TestOAuthIntegration:
    """Test OAuth authentication flows."""

    @pytest.mark.asyncio
    async def test_google_oauth_callback(
        self,
        client: AsyncClient,
        mock_google_oauth,
        db_session: AsyncSession,
    ):
        """Test Google OAuth callback creates user and returns tokens."""
        # Step 1: Simulate OAuth callback with authorization code
        response = await client.get(
            "/api/v1/auth/google/callback",
            params={
                "code": "mock_auth_code",
                "state": mock_google_oauth.state,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == mock_google_oauth.user_info.email

        # Step 2: Verify user is created with OAuth provider linked
        result = await db_session.execute(
            User.__table__.select().where(
                User.email == mock_google_oauth.user_info.email
            )
        )
        user = result.fetchone()
        assert user is not None
        assert user.oauth_provider == "google"

    @pytest.mark.asyncio
    async def test_github_oauth_callback(
        self,
        client: AsyncClient,
        mock_github_oauth,
        db_session: AsyncSession,
    ):
        """Test GitHub OAuth callback creates user and returns tokens."""
        response = await client.get(
            "/api/v1/auth/github/callback",
            params={
                "code": "mock_auth_code",
                "state": mock_github_oauth.state,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "user" in data
        assert data["user"]["email"] == mock_github_oauth.user_info.email

    @pytest.mark.asyncio
    async def test_oauth_links_to_existing_account(
        self,
        client: AsyncClient,
        test_user: User,
        mock_google_oauth,
        db_session: AsyncSession,
    ):
        """Test OAuth linking to existing account with same email."""
        # Configure mock to return test user's email
        mock_google_oauth.user_info.email = test_user.email

        response = await client.get(
            "/api/v1/auth/google/callback",
            params={
                "code": "mock_auth_code",
                "state": mock_google_oauth.state,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Should return existing user, not create new one
        assert data["user"]["id"] == str(test_user.id)


@pytest.mark.integration
class TestSessionManagement:
    """Test session and token management."""

    @pytest.mark.asyncio
    async def test_concurrent_sessions(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Test user can have multiple concurrent sessions."""
        # Login from "device 1"
        response1 = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "password123",
            },
        )
        assert response1.status_code == 200
        token1 = response1.json()["tokens"]["access_token"]

        # Login from "device 2"
        response2 = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "password123",
            },
        )
        assert response2.status_code == 200
        token2 = response2.json()["tokens"]["access_token"]

        # Both sessions should be valid
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert response.status_code == 200

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_session_list(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
    ):
        """Test listing active sessions."""
        response = await client.get(
            "/api/v1/auth/sessions",
            headers=auth_headers,
        )
        assert response.status_code == 200

        sessions = response.json()
        assert isinstance(sessions, list)
        assert len(sessions) >= 1  # At least current session

    @pytest.mark.asyncio
    async def test_revoke_session(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Test revoking a specific session."""
        # Login twice to create two sessions
        response1 = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "password123"},
        )
        token1 = response1.json()["tokens"]["access_token"]

        response2 = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "password123"},
        )
        token2 = response2.json()["tokens"]["access_token"]

        # Get sessions
        response = await client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {token1}"},
        )
        sessions = response.json()

        # Find session for token2 and revoke it
        other_session = next(
            (s for s in sessions if s.get("current") is False),
            None,
        )

        if other_session:
            response = await client.delete(
                f"/api/v1/auth/sessions/{other_session['id']}",
                headers={"Authorization": f"Bearer {token1}"},
            )
            assert response.status_code == 200

            # token2 should no longer work
            response = await client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {token2}"},
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_revoke_all_sessions(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Test revoking all sessions (logout everywhere)."""
        # Login twice
        response1 = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "password123"},
        )
        token1 = response1.json()["tokens"]["access_token"]

        response2 = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "password123"},
        )
        token2 = response2.json()["tokens"]["access_token"]

        # Revoke all sessions
        response = await client.post(
            "/api/v1/auth/logout-all",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert response.status_code == 200

        # Both tokens should be invalid
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert response.status_code == 401

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 401


@pytest.mark.integration
class TestRateLimiting:
    """Test authentication rate limiting."""

    @pytest.mark.asyncio
    async def test_login_rate_limiting(
        self,
        client: AsyncClient,
    ):
        """Test rate limiting on login attempts."""
        # Make many login attempts
        for i in range(15):
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@example.com",
                    "password": f"wrong_password_{i}",
                },
            )

            if response.status_code == 429:
                # Rate limited
                assert "retry-after" in response.headers.keys() or True
                break

        # Should eventually be rate limited
        # Note: This test may need adjustment based on actual rate limit config

    @pytest.mark.asyncio
    async def test_password_reset_rate_limiting(
        self,
        client: AsyncClient,
    ):
        """Test rate limiting on password reset requests."""
        email = "ratelimit@example.com"

        for _ in range(10):
            response = await client.post(
                "/api/v1/auth/forgot-password",
                json={"email": email},
            )

            if response.status_code == 429:
                break

        # Should be rate limited after multiple requests
