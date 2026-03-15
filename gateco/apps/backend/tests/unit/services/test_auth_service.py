"""Unit tests for AuthService.

This module contains comprehensive unit tests for the authentication service,
covering password hashing, JWT token lifecycle, user authentication, and
session management.

These tests are designed to run once the AuthService is implemented.
They follow the test patterns defined in the QA Implementation Plan.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone, timedelta
import secrets


# ============================================================================
# Password Hashing Tests
# ============================================================================


class TestPasswordHashing:
    """Tests for password hashing functionality."""

    def test_hash_password_produces_bcrypt_hash(self):
        """
        Password hashing produces valid bcrypt hash.

        Given: Plain text password
        When: hash_password() is called
        Then: Returns bcrypt hash starting with $2b$
        """
        from src.gateco.utils.security import hash_password

        hashed = hash_password("TestPassword123!")

        assert hashed.startswith("$2b$")
        assert len(hashed) == 60  # bcrypt produces 60-char hash

    def test_verify_password_correct_password(self):
        """
        Correct password verification returns True.

        Given: Password hash and matching plain password
        When: verify_password() is called
        Then: Returns True
        """
        from src.gateco.utils.security import hash_password, verify_password

        password = "TestPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password(self):
        """
        Incorrect password verification returns False.

        Given: Password hash and non-matching plain password
        When: verify_password() is called
        Then: Returns False
        """
        from src.gateco.utils.security import hash_password, verify_password

        hashed = hash_password("CorrectPassword123!")

        assert verify_password("WrongPassword456!", hashed) is False

    def test_hash_password_different_salts(self):
        """
        Same password produces different hashes (unique salts).

        Given: Same plain text password
        When: hash_password() is called twice
        Then: Two different hashes are produced
        """
        from src.gateco.utils.security import hash_password

        password = "SamePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts produce different hashes

    def test_hash_password_minimum_cost_factor(self):
        """
        Password hashing uses sufficient cost factor.

        Given: Plain text password
        When: hash_password() is called
        Then: Hash uses cost factor >= 12 for security
        """
        from src.gateco.utils.security import hash_password

        hashed = hash_password("TestPassword123!")
        # bcrypt format: $2b$<cost>$<salt+hash>
        cost = int(hashed.split("$")[2])

        assert cost >= 12

    def test_verify_password_empty_password_returns_false(self):
        """
        Empty password verification returns False.

        Given: Password hash and empty password
        When: verify_password() is called
        Then: Returns False
        """
        from src.gateco.utils.security import hash_password, verify_password

        hashed = hash_password("ValidPassword123!")

        assert verify_password("", hashed) is False

    def test_verify_password_none_hash_raises_error(self):
        """
        None hash raises appropriate error.

        Given: None as password hash
        When: verify_password() is called
        Then: Raises TypeError or returns False
        """
        from src.gateco.utils.security import verify_password

        # Implementation may raise error or return False
        try:
            result = verify_password("password", None)
            assert result is False
        except (TypeError, ValueError):
            pass  # Expected behavior


# ============================================================================
# JWT Token Tests
# ============================================================================


class TestJWTTokens:
    """Tests for JWT token creation and validation."""

    def test_create_access_token_includes_required_claims(self):
        """
        Access token includes all required claims.

        Given: User credentials for token creation
        When: create_access_token() is called
        Then: Token contains sub, org_id, role, plan, exp, iat, jti claims
        """
        from src.gateco.utils.security import create_access_token, decode_token

        token = create_access_token(
            user_id="user_123",
            org_id="org_456",
            role="owner",
            plan="pro",
        )
        payload = decode_token(token)

        assert payload["sub"] == "user_123"
        assert payload["org_id"] == "org_456"
        assert payload["role"] == "owner"
        assert payload["plan"] == "pro"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_access_token_expires_in_15_minutes(self):
        """
        Access token has 15-minute expiry.

        Given: New access token
        When: Token is decoded
        Then: Expiry is 15 minutes from issue time
        """
        from src.gateco.utils.security import create_access_token, decode_token

        token = create_access_token(
            user_id="user_123",
            org_id="org_456",
            role="member",
            plan="free",
        )
        payload = decode_token(token)

        expiry_delta = payload["exp"] - payload["iat"]
        assert expiry_delta == 900  # 15 minutes in seconds

    def test_create_refresh_token_is_opaque(self):
        """
        Refresh token is random opaque string, not JWT.

        Given: User for refresh token creation
        When: create_refresh_token() is called
        Then: Token is opaque (not decodable JWT)
        """
        from src.gateco.utils.security import create_refresh_token
        import jose.jwt

        token = create_refresh_token()

        # Should not be decodable as JWT
        with pytest.raises(jose.jwt.JWTError):
            jose.jwt.decode(token, "any-key", algorithms=["HS256"])

        # Should be sufficiently random
        assert len(token) >= 32

    def test_refresh_token_is_unique(self):
        """
        Each refresh token is unique.

        Given: Multiple refresh token creation calls
        When: create_refresh_token() is called multiple times
        Then: Each token is different
        """
        from src.gateco.utils.security import create_refresh_token

        tokens = [create_refresh_token() for _ in range(10)]

        assert len(set(tokens)) == 10  # All unique

    def test_validate_access_token_success(self):
        """
        Valid token decodes successfully.

        Given: Valid access token
        When: validate_access_token() is called
        Then: Payload is returned without error
        """
        from src.gateco.utils.security import create_access_token, validate_access_token

        token = create_access_token(
            user_id="user_123",
            org_id="org_456",
            role="member",
            plan="free",
        )
        payload = validate_access_token(token)

        assert payload["sub"] == "user_123"

    def test_validate_access_token_expired(self):
        """
        Expired token raises AuthenticationError.

        Given: Expired access token
        When: validate_access_token() is called
        Then: AUTH_TOKEN_EXPIRED error is raised
        """
        from src.gateco.utils.security import validate_access_token
        from src.gateco.utils.errors import AuthenticationError
        import jose.jwt
        import os

        # Create token with past expiry
        expired_payload = {
            "sub": "user_123",
            "org_id": "org_456",
            "role": "member",
            "plan": "free",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "jti": str(uuid4()),
        }
        expired_token = jose.jwt.encode(
            expired_payload,
            os.environ.get("JWT_SECRET_KEY", "test-key"),
            algorithm="HS256",
        )

        with pytest.raises(AuthenticationError) as exc_info:
            validate_access_token(expired_token)

        assert exc_info.value.code == "AUTH_TOKEN_EXPIRED"

    def test_validate_access_token_invalid_signature(self):
        """
        Token with wrong signature raises AuthenticationError.

        Given: Token signed with different secret
        When: validate_access_token() is called
        Then: AUTH_TOKEN_INVALID error is raised
        """
        from src.gateco.utils.security import validate_access_token
        from src.gateco.utils.errors import AuthenticationError
        import jose.jwt

        # Create token with wrong key
        wrong_key_token = jose.jwt.encode(
            {
                "sub": "user_123",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            "wrong-secret-key",
            algorithm="HS256",
        )

        with pytest.raises(AuthenticationError) as exc_info:
            validate_access_token(wrong_key_token)

        assert exc_info.value.code == "AUTH_TOKEN_INVALID"

    def test_validate_access_token_malformed(self):
        """
        Malformed token raises AuthenticationError.

        Given: Invalid token string
        When: validate_access_token() is called
        Then: AUTH_TOKEN_INVALID error is raised
        """
        from src.gateco.utils.security import validate_access_token
        from src.gateco.utils.errors import AuthenticationError

        with pytest.raises(AuthenticationError) as exc_info:
            validate_access_token("not.a.valid.jwt")

        assert exc_info.value.code == "AUTH_TOKEN_INVALID"

    def test_each_token_has_unique_jti(self):
        """
        Each token has unique jti (JWT ID) for revocation.

        Given: Multiple tokens for same user
        When: Tokens are created
        Then: Each has unique jti
        """
        from src.gateco.utils.security import create_access_token, decode_token

        token1 = create_access_token(
            user_id="user_123", org_id="org_456", role="member", plan="free"
        )
        token2 = create_access_token(
            user_id="user_123", org_id="org_456", role="member", plan="free"
        )

        payload1 = decode_token(token1)
        payload2 = decode_token(token2)

        assert payload1["jti"] != payload2["jti"]


# ============================================================================
# Slug Generation Tests
# ============================================================================


class TestGenerateSlug:
    """Tests for slug generation utility."""

    def test_generates_lowercase_slug(self):
        """Slug should be lowercase."""
        from src.gateco.utils.security import generate_slug

        assert generate_slug("My Company") == "my-company"

    def test_replaces_special_characters(self):
        """Special characters should be replaced with dashes."""
        from src.gateco.utils.security import generate_slug

        result = generate_slug("Test & Company!")
        assert "&" not in result
        assert "!" not in result
        assert result == "test-company" or "test" in result

    def test_strips_leading_trailing_dashes(self):
        """Leading/trailing whitespace should be stripped."""
        from src.gateco.utils.security import generate_slug

        result = generate_slug("  Test  ")
        assert not result.startswith("-")
        assert not result.endswith("-")
        assert result == "test"

    def test_handles_unicode(self):
        """Unicode characters should be handled gracefully."""
        from src.gateco.utils.security import generate_slug

        result = generate_slug("Café Shop")
        # Should either transliterate or remove accented chars
        assert "caf" in result.lower() or "shop" in result.lower()

    def test_handles_empty_string(self):
        """Empty string should return empty or raise error."""
        from src.gateco.utils.security import generate_slug

        result = generate_slug("")
        assert result == "" or result is None

    def test_handles_numbers(self):
        """Numbers should be preserved."""
        from src.gateco.utils.security import generate_slug

        result = generate_slug("Company 123")
        assert "123" in result


# ============================================================================
# AuthService Signup Tests
# ============================================================================


class TestAuthServiceSignup:
    """Tests for AuthService.signup method."""

    @pytest.mark.anyio
    async def test_signup_creates_organization_and_user(self, db_session):
        """
        Signup should create both organization and user.

        Given: Valid signup request data
        When: signup() is called
        Then: Organization and user are created, tokens returned
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import SignupRequest

        service = AuthService(db_session)
        request = SignupRequest(
            email="newuser@example.com",
            password="SecurePass123!",
            name="New User",
            organization_name="New Org",
        )

        response = await service.signup(request)

        assert response.user.email == "newuser@example.com"
        assert response.user.name == "New User"
        assert response.user.role == "owner"
        assert response.organization.name == "New Org"
        assert response.tokens.access_token is not None
        assert response.tokens.refresh_token is not None

    @pytest.mark.anyio
    async def test_signup_rejects_duplicate_email(self, db_session, test_user):
        """
        Signup should reject duplicate email addresses.

        Given: A user with email already exists
        When: signup() is called with same email
        Then: ConflictError with AUTH_EMAIL_EXISTS is raised
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import SignupRequest
        from src.gateco.utils.errors import ConflictError

        user, _ = test_user
        service = AuthService(db_session)
        request = SignupRequest(
            email=user["email"],
            password="SecurePass123!",
            name="Another User",
            organization_name="Another Org",
        )

        with pytest.raises(ConflictError) as exc_info:
            await service.signup(request)

        assert exc_info.value.code == "AUTH_EMAIL_EXISTS"

    @pytest.mark.anyio
    async def test_signup_hashes_password(self, db_session):
        """
        Signup should hash password, not store plain text.

        Given: Valid signup request with plain password
        When: signup() is called
        Then: Stored password_hash is bcrypt hash, not plain text
        """
        from sqlalchemy import select
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import SignupRequest
        from src.gateco.database.models import User

        service = AuthService(db_session)
        request = SignupRequest(
            email="hashtest@example.com",
            password="PlainPassword123!",
            name="Hash Test",
            organization_name="Test Org",
        )

        await service.signup(request)

        result = await db_session.execute(
            select(User).where(User.email == "hashtest@example.com")
        )
        user = result.scalar_one()

        assert user.password_hash != "PlainPassword123!"
        assert user.password_hash.startswith("$2b$")  # bcrypt prefix

    @pytest.mark.anyio
    async def test_signup_assigns_owner_role(self, db_session):
        """
        Signup should assign owner role to first user.

        Given: Valid signup request
        When: signup() is called
        Then: Created user has 'owner' role
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import SignupRequest

        service = AuthService(db_session)
        request = SignupRequest(
            email="owner@example.com",
            password="SecurePass123!",
            name="Owner User",
            organization_name="Owner Org",
        )

        response = await service.signup(request)

        assert response.user.role == "owner"

    @pytest.mark.anyio
    async def test_signup_organization_starts_on_free_plan(self, db_session):
        """
        New organizations should start on free plan.

        Given: Valid signup request
        When: signup() is called
        Then: Organization has free plan
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import SignupRequest

        service = AuthService(db_session)
        request = SignupRequest(
            email="freeuser@example.com",
            password="SecurePass123!",
            name="Free User",
            organization_name="Free Org",
        )

        response = await service.signup(request)

        assert response.organization.plan == "free"

    @pytest.mark.anyio
    async def test_signup_email_is_case_insensitive(self, db_session):
        """
        Email comparison should be case-insensitive.

        Given: Existing user with lowercase email
        When: signup() is called with uppercase variant
        Then: ConflictError is raised
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import SignupRequest
        from src.gateco.utils.errors import ConflictError

        service = AuthService(db_session)

        # Create first user
        request1 = SignupRequest(
            email="test@example.com",
            password="SecurePass123!",
            name="User One",
            organization_name="Org One",
        )
        await service.signup(request1)

        # Try to create with uppercase email
        request2 = SignupRequest(
            email="TEST@EXAMPLE.COM",
            password="SecurePass123!",
            name="User Two",
            organization_name="Org Two",
        )

        with pytest.raises(ConflictError) as exc_info:
            await service.signup(request2)

        assert exc_info.value.code == "AUTH_EMAIL_EXISTS"


# ============================================================================
# AuthService Login Tests
# ============================================================================


class TestAuthServiceLogin:
    """Tests for AuthService.login method."""

    @pytest.mark.anyio
    async def test_login_success(self, db_session, test_user):
        """
        Login with valid credentials should return tokens.

        Given: Existing user with known password
        When: login() is called with correct credentials
        Then: User info and tokens are returned
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import LoginRequest

        user, password = test_user
        service = AuthService(db_session)
        request = LoginRequest(email=user["email"], password=password)

        response = await service.login(request)

        assert response.user.email == user["email"]
        assert response.tokens.access_token is not None
        assert response.tokens.refresh_token is not None
        assert response.tokens.expires_in == 900  # 15 minutes

    @pytest.mark.anyio
    async def test_login_invalid_email(self, db_session):
        """
        Login with non-existent email should fail.

        Given: No user with the provided email exists
        When: login() is called
        Then: AuthenticationError is raised
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import LoginRequest
        from src.gateco.utils.errors import AuthenticationError

        service = AuthService(db_session)
        request = LoginRequest(
            email="nonexistent@example.com",
            password="password",
        )

        with pytest.raises(AuthenticationError) as exc_info:
            await service.login(request)

        assert exc_info.value.code == "AUTH_INVALID_CREDENTIALS"

    @pytest.mark.anyio
    async def test_login_invalid_password(self, db_session, test_user):
        """
        Login with wrong password should fail.

        Given: Existing user
        When: login() is called with wrong password
        Then: AuthenticationError is raised
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import LoginRequest
        from src.gateco.utils.errors import AuthenticationError

        user, _ = test_user
        service = AuthService(db_session)
        request = LoginRequest(email=user["email"], password="WrongPassword123!")

        with pytest.raises(AuthenticationError) as exc_info:
            await service.login(request)

        assert exc_info.value.code == "AUTH_INVALID_CREDENTIALS"

    @pytest.mark.anyio
    async def test_login_inactive_user(self, db_session, inactive_user):
        """
        Login as inactive user should fail.

        Given: User with is_active=False
        When: login() is called
        Then: AuthenticationError with AUTH_ACCOUNT_DISABLED is raised
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import LoginRequest
        from src.gateco.utils.errors import AuthenticationError

        user, password = inactive_user
        service = AuthService(db_session)
        request = LoginRequest(email=user["email"], password=password)

        with pytest.raises(AuthenticationError) as exc_info:
            await service.login(request)

        assert exc_info.value.code == "AUTH_ACCOUNT_DISABLED"

    @pytest.mark.anyio
    async def test_login_returns_user_organization(self, db_session, test_user):
        """
        Login response includes user's organization.

        Given: User with organization
        When: login() is called
        Then: Response includes organization details
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import LoginRequest

        user, password = test_user
        service = AuthService(db_session)
        request = LoginRequest(email=user["email"], password=password)

        response = await service.login(request)

        assert response.user.organization is not None
        assert response.user.organization.id == user["organization_id"]


# ============================================================================
# AuthService Refresh Tests
# ============================================================================


class TestAuthServiceRefresh:
    """Tests for AuthService.refresh method."""

    @pytest.mark.anyio
    async def test_refresh_returns_new_tokens(self, db_session, test_user):
        """
        Refresh should return new token pair.

        Given: Valid refresh token from login
        When: refresh() is called
        Then: New access and refresh tokens are returned
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import LoginRequest

        user, password = test_user
        service = AuthService(db_session)

        # First login to get refresh token
        login_response = await service.login(
            LoginRequest(email=user["email"], password=password)
        )
        original_refresh = login_response.tokens.refresh_token

        # Refresh tokens
        new_tokens = await service.refresh(original_refresh)

        assert new_tokens.access_token is not None
        assert new_tokens.refresh_token is not None
        assert new_tokens.refresh_token != original_refresh  # Token rotated

    @pytest.mark.anyio
    async def test_refresh_invalid_token(self, db_session):
        """
        Refresh with invalid token should fail.

        Given: Invalid refresh token
        When: refresh() is called
        Then: AuthenticationError with AUTH_INVALID_REFRESH_TOKEN is raised
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.utils.errors import AuthenticationError

        service = AuthService(db_session)

        with pytest.raises(AuthenticationError) as exc_info:
            await service.refresh("invalid-refresh-token")

        assert exc_info.value.code == "AUTH_INVALID_REFRESH_TOKEN"

    @pytest.mark.anyio
    async def test_refresh_expired_token(self, db_session, test_user):
        """
        Refresh with expired token should fail.

        Given: Expired refresh token
        When: refresh() is called
        Then: AuthenticationError is raised
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import LoginRequest
        from src.gateco.utils.errors import AuthenticationError
        from sqlalchemy import update
        from src.gateco.database.models import Session

        user, password = test_user
        service = AuthService(db_session)

        # Login to get refresh token
        login_response = await service.login(
            LoginRequest(email=user["email"], password=password)
        )
        refresh_token = login_response.tokens.refresh_token

        # Manually expire the session in database
        await db_session.execute(
            update(Session)
            .where(Session.refresh_token == refresh_token)
            .values(expires_at=datetime.now(timezone.utc) - timedelta(days=1))
        )
        await db_session.commit()

        with pytest.raises(AuthenticationError):
            await service.refresh(refresh_token)

    @pytest.mark.anyio
    async def test_refresh_rotates_token(self, db_session, test_user):
        """
        Refresh should invalidate old token after rotation.

        Given: Valid refresh token
        When: refresh() is called
        Then: Old token no longer works
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import LoginRequest
        from src.gateco.utils.errors import AuthenticationError

        user, password = test_user
        service = AuthService(db_session)

        # Login to get refresh token
        login_response = await service.login(
            LoginRequest(email=user["email"], password=password)
        )
        old_refresh = login_response.tokens.refresh_token

        # Refresh once
        await service.refresh(old_refresh)

        # Try to use old token again
        with pytest.raises(AuthenticationError):
            await service.refresh(old_refresh)


# ============================================================================
# AuthService Logout Tests
# ============================================================================


class TestAuthServiceLogout:
    """Tests for AuthService.logout method."""

    @pytest.mark.anyio
    async def test_logout_invalidates_session(self, db_session, test_user):
        """
        Logout should invalidate refresh token.

        Given: Logged in user with valid refresh token
        When: logout() is called
        Then: Subsequent refresh with that token fails
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import LoginRequest
        from src.gateco.utils.errors import AuthenticationError

        user, password = test_user
        service = AuthService(db_session)

        login_response = await service.login(
            LoginRequest(email=user["email"], password=password)
        )
        refresh_token = login_response.tokens.refresh_token

        # Logout
        await service.logout(refresh_token)

        # Try to refresh - should fail
        with pytest.raises(AuthenticationError):
            await service.refresh(refresh_token)

    @pytest.mark.anyio
    async def test_logout_invalid_token_succeeds(self, db_session):
        """
        Logout with invalid token should not raise error.

        Given: Invalid refresh token
        When: logout() is called
        Then: No error is raised (idempotent)
        """
        from src.gateco.services.auth_service import AuthService

        service = AuthService(db_session)

        # Should not raise
        await service.logout("invalid-token")

    @pytest.mark.anyio
    async def test_logout_all_sessions(self, db_session, test_user):
        """
        Logout all should invalidate all user sessions.

        Given: User with multiple active sessions
        When: logout_all() is called
        Then: All refresh tokens are invalidated
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import LoginRequest
        from src.gateco.utils.errors import AuthenticationError

        user, password = test_user
        service = AuthService(db_session)

        # Create multiple sessions
        login1 = await service.login(
            LoginRequest(email=user["email"], password=password)
        )
        login2 = await service.login(
            LoginRequest(email=user["email"], password=password)
        )

        refresh1 = login1.tokens.refresh_token
        refresh2 = login2.tokens.refresh_token

        # Logout all
        await service.logout_all(user["id"])

        # Both tokens should fail
        with pytest.raises(AuthenticationError):
            await service.refresh(refresh1)

        with pytest.raises(AuthenticationError):
            await service.refresh(refresh2)


# ============================================================================
# OAuth Integration Tests
# ============================================================================


class TestOAuthLogin:
    """Tests for OAuth authentication flow."""

    @pytest.mark.anyio
    async def test_oauth_google_creates_user_if_new(self, db_session):
        """
        Google OAuth creates new user if email not in system.

        Given: Valid Google OAuth token for new user
        When: oauth_login() is called
        Then: New user and organization are created
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import OAuthRequest

        service = AuthService(db_session)
        request = OAuthRequest(
            provider="google",
            code="valid_google_code",
            redirect_uri="http://localhost:3000/auth/callback",
        )

        with patch.object(
            service, "_verify_google_token"
        ) as mock_verify:
            mock_verify.return_value = {
                "email": "newgoogleuser@gmail.com",
                "name": "Google User",
                "sub": "google_123",
            }

            response = await service.oauth_login(request)

            assert response.user.email == "newgoogleuser@gmail.com"
            assert response.tokens.access_token is not None
            assert response.is_new_user is True

    @pytest.mark.anyio
    async def test_oauth_google_links_existing_user(self, db_session, test_user):
        """
        Google OAuth links to existing user with same email.

        Given: Valid Google OAuth token for existing user
        When: oauth_login() is called
        Then: Existing user is linked and logged in
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import OAuthRequest

        user, _ = test_user
        service = AuthService(db_session)
        request = OAuthRequest(
            provider="google",
            code="valid_google_code",
            redirect_uri="http://localhost:3000/auth/callback",
        )

        with patch.object(
            service, "_verify_google_token"
        ) as mock_verify:
            mock_verify.return_value = {
                "email": user["email"],
                "name": user["name"],
                "sub": "google_456",
            }

            response = await service.oauth_login(request)

            assert response.user.id == str(user["id"])
            assert response.is_new_user is False

    @pytest.mark.anyio
    async def test_oauth_github_creates_user(self, db_session):
        """
        GitHub OAuth creates new user.

        Given: Valid GitHub OAuth code
        When: oauth_login() is called with provider=github
        Then: User is created with GitHub profile
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import OAuthRequest

        service = AuthService(db_session)
        request = OAuthRequest(
            provider="github",
            code="valid_github_code",
            redirect_uri="http://localhost:3000/auth/callback",
        )

        with patch.object(
            service, "_verify_github_token"
        ) as mock_verify:
            mock_verify.return_value = {
                "email": "githubuser@example.com",
                "name": "GitHub User",
                "id": 12345,
            }

            response = await service.oauth_login(request)

            assert response.user.email == "githubuser@example.com"
            assert response.tokens.access_token is not None

    @pytest.mark.anyio
    async def test_oauth_invalid_provider_raises_error(self, db_session):
        """
        Invalid OAuth provider raises error.

        Given: Unknown provider
        When: oauth_login() is called
        Then: ValidationError is raised
        """
        from src.gateco.services.auth_service import AuthService
        from src.gateco.schemas.auth import OAuthRequest
        from src.gateco.utils.errors import ValidationError

        service = AuthService(db_session)
        request = OAuthRequest(
            provider="unknown_provider",
            code="some_code",
            redirect_uri="http://localhost:3000/auth/callback",
        )

        with pytest.raises(ValidationError):
            await service.oauth_login(request)
