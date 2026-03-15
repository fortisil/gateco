"""Unit tests for JWT authentication middleware.

This module tests the JWT authentication middleware that validates
tokens and populates request state with user claims.

Dependencies:
- JWT middleware implementation
- Security utilities for token generation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import os


class TestJWTAuthMiddleware:
    """Tests for JWT authentication middleware."""

    @pytest.fixture
    def mock_app(self):
        """Create mock FastAPI app."""
        return MagicMock()

    @pytest.fixture
    def mock_request(self):
        """Create mock request object."""
        request = MagicMock()
        request.headers = {}
        request.url.path = "/api/protected"
        request.state = type("State", (), {})()
        return request

    @pytest.fixture
    def valid_access_token(self):
        """Generate valid access token for testing."""
        from src.gateco.utils.security import create_access_token

        return create_access_token(
            user_id=str(uuid4()),
            org_id=str(uuid4()),
            role="member",
            plan="free",
        )

    @pytest.fixture
    def expired_access_token(self):
        """Generate expired access token for testing."""
        import jose.jwt

        payload = {
            "sub": str(uuid4()),
            "org_id": str(uuid4()),
            "role": "member",
            "plan": "free",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "jti": str(uuid4()),
        }

        return jose.jwt.encode(
            payload,
            os.environ.get("JWT_SECRET_KEY", "test-key"),
            algorithm="HS256",
        )

    @pytest.mark.anyio
    async def test_valid_token_passes(
        self, mock_app, mock_request, valid_access_token
    ):
        """
        Valid JWT token passes through middleware.

        Given: Request with valid Bearer token
        When: Middleware processes request
        Then: Request passes, user claims in state
        """
        from src.gateco.middleware.jwt_auth import JWTAuthMiddleware

        middleware = JWTAuthMiddleware(mock_app)
        mock_request.headers = {"Authorization": f"Bearer {valid_access_token}"}

        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(mock_request, call_next)

        call_next.assert_called_once()
        assert hasattr(mock_request.state, "user_id")
        assert hasattr(mock_request.state, "org_id")
        assert hasattr(mock_request.state, "role")

    @pytest.mark.anyio
    async def test_missing_token_returns_401(self, mock_app, mock_request):
        """
        Missing token returns 401.

        Given: Request without Authorization header
        When: Middleware processes request to protected route
        Then: 401 response returned
        """
        from src.gateco.middleware.jwt_auth import JWTAuthMiddleware
        from fastapi import HTTPException

        middleware = JWTAuthMiddleware(mock_app)
        mock_request.headers = {}

        call_next = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(mock_request, call_next)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "AUTH_TOKEN_MISSING"

    @pytest.mark.anyio
    async def test_malformed_header_returns_401(self, mock_app, mock_request):
        """
        Malformed Authorization header returns 401.

        Given: Request with malformed header (no Bearer prefix)
        When: Middleware processes request
        Then: 401 response returned
        """
        from src.gateco.middleware.jwt_auth import JWTAuthMiddleware
        from fastapi import HTTPException

        middleware = JWTAuthMiddleware(mock_app)
        mock_request.headers = {"Authorization": "InvalidFormat token"}

        call_next = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(mock_request, call_next)

        assert exc_info.value.status_code == 401

    @pytest.mark.anyio
    async def test_invalid_token_returns_401(self, mock_app, mock_request):
        """
        Invalid token returns 401.

        Given: Request with malformed JWT token
        When: Middleware processes request
        Then: 401 response with AUTH_TOKEN_INVALID
        """
        from src.gateco.middleware.jwt_auth import JWTAuthMiddleware
        from fastapi import HTTPException

        middleware = JWTAuthMiddleware(mock_app)
        mock_request.headers = {"Authorization": "Bearer not.a.valid.jwt"}

        call_next = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(mock_request, call_next)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "AUTH_TOKEN_INVALID"

    @pytest.mark.anyio
    async def test_expired_token_returns_401_with_code(
        self, mock_app, mock_request, expired_access_token
    ):
        """
        Expired token returns 401 with AUTH_TOKEN_EXPIRED.

        Given: Request with expired token
        When: Middleware processes request
        Then: 401 response with AUTH_TOKEN_EXPIRED code
        """
        from src.gateco.middleware.jwt_auth import JWTAuthMiddleware
        from fastapi import HTTPException

        middleware = JWTAuthMiddleware(mock_app)
        mock_request.headers = {"Authorization": f"Bearer {expired_access_token}"}

        call_next = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(mock_request, call_next)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "AUTH_TOKEN_EXPIRED"

    @pytest.mark.anyio
    async def test_wrong_signature_returns_401(self, mock_app, mock_request):
        """
        Token with wrong signature returns 401.

        Given: Token signed with different secret
        When: Middleware processes request
        Then: 401 response with AUTH_TOKEN_INVALID
        """
        from src.gateco.middleware.jwt_auth import JWTAuthMiddleware
        from fastapi import HTTPException
        import jose.jwt

        # Create token with wrong key
        wrong_key_token = jose.jwt.encode(
            {
                "sub": str(uuid4()),
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            "wrong-secret-key",
            algorithm="HS256",
        )

        middleware = JWTAuthMiddleware(mock_app)
        mock_request.headers = {"Authorization": f"Bearer {wrong_key_token}"}

        call_next = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(mock_request, call_next)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "AUTH_TOKEN_INVALID"

    @pytest.mark.anyio
    async def test_public_routes_bypass_auth(self, mock_app, mock_request):
        """
        Public routes don't require authentication.

        Given: Request to public endpoint without token
        When: Middleware processes request
        Then: Request passes without error
        """
        from src.gateco.middleware.jwt_auth import JWTAuthMiddleware

        middleware = JWTAuthMiddleware(mock_app)
        mock_request.headers = {}
        mock_request.url.path = "/api/health"

        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(mock_request, call_next)

        call_next.assert_called_once()

    @pytest.mark.anyio
    async def test_plans_endpoint_is_public(self, mock_app, mock_request):
        """
        Plans endpoint is public.

        Given: Request to /api/plans without token
        When: Middleware processes request
        Then: Request passes without error
        """
        from src.gateco.middleware.jwt_auth import JWTAuthMiddleware

        middleware = JWTAuthMiddleware(mock_app)
        mock_request.headers = {}
        mock_request.url.path = "/api/plans"

        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(mock_request, call_next)

        call_next.assert_called_once()

    @pytest.mark.anyio
    async def test_auth_endpoints_are_public(self, mock_app, mock_request):
        """
        Auth endpoints (login, signup) are public.

        Given: Request to /api/auth/login without token
        When: Middleware processes request
        Then: Request passes without error
        """
        from src.gateco.middleware.jwt_auth import JWTAuthMiddleware

        middleware = JWTAuthMiddleware(mock_app)
        mock_request.headers = {}
        mock_request.url.path = "/api/auth/login"

        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(mock_request, call_next)

        call_next.assert_called_once()

    @pytest.mark.anyio
    async def test_extracts_all_claims(
        self, mock_app, mock_request, valid_access_token
    ):
        """
        All claims extracted to request state.

        Given: Valid token with full claims
        When: Middleware processes request
        Then: user_id, org_id, role, plan in request.state
        """
        from src.gateco.middleware.jwt_auth import JWTAuthMiddleware

        middleware = JWTAuthMiddleware(mock_app)
        mock_request.headers = {"Authorization": f"Bearer {valid_access_token}"}

        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(mock_request, call_next)

        assert hasattr(mock_request.state, "user_id")
        assert hasattr(mock_request.state, "org_id")
        assert hasattr(mock_request.state, "role")
        assert hasattr(mock_request.state, "plan")

    @pytest.mark.anyio
    async def test_user_id_matches_token_sub(
        self, mock_app, mock_request
    ):
        """
        User ID in state matches token subject.

        Given: Valid token with known user_id
        When: Middleware processes request
        Then: request.state.user_id matches token sub
        """
        from src.gateco.middleware.jwt_auth import JWTAuthMiddleware
        from src.gateco.utils.security import create_access_token

        user_id = str(uuid4())
        token = create_access_token(
            user_id=user_id,
            org_id=str(uuid4()),
            role="member",
            plan="free",
        )

        middleware = JWTAuthMiddleware(mock_app)
        mock_request.headers = {"Authorization": f"Bearer {token}"}

        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(mock_request, call_next)

        assert mock_request.state.user_id == user_id


class TestAuthorizationHeader:
    """Tests for Authorization header parsing."""

    @pytest.fixture
    def mock_app(self):
        return MagicMock()

    @pytest.fixture
    def mock_request(self):
        request = MagicMock()
        request.headers = {}
        request.url.path = "/api/protected"
        request.state = type("State", (), {})()
        return request

    @pytest.mark.anyio
    async def test_case_insensitive_bearer(self, mock_app, mock_request):
        """
        Bearer prefix is case-insensitive.

        Given: Request with lowercase 'bearer' prefix
        When: Middleware processes request
        Then: Token is still extracted and validated
        """
        from src.gateco.middleware.jwt_auth import JWTAuthMiddleware
        from src.gateco.utils.security import create_access_token

        token = create_access_token(
            user_id=str(uuid4()),
            org_id=str(uuid4()),
            role="member",
            plan="free",
        )

        middleware = JWTAuthMiddleware(mock_app)
        mock_request.headers = {"Authorization": f"bearer {token}"}

        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(mock_request, call_next)

        call_next.assert_called_once()

    @pytest.mark.anyio
    async def test_extra_whitespace_handled(self, mock_app, mock_request):
        """
        Extra whitespace in header is handled.

        Given: Request with extra spaces after Bearer
        When: Middleware processes request
        Then: Token is extracted correctly
        """
        from src.gateco.middleware.jwt_auth import JWTAuthMiddleware
        from src.gateco.utils.security import create_access_token

        token = create_access_token(
            user_id=str(uuid4()),
            org_id=str(uuid4()),
            role="member",
            plan="free",
        )

        middleware = JWTAuthMiddleware(mock_app)
        mock_request.headers = {"Authorization": f"Bearer  {token}"}  # Extra space

        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(mock_request, call_next)

        call_next.assert_called_once()

    @pytest.mark.anyio
    async def test_empty_token_returns_401(self, mock_app, mock_request):
        """
        Empty token after Bearer returns 401.

        Given: Request with 'Bearer ' but no token
        When: Middleware processes request
        Then: 401 response
        """
        from src.gateco.middleware.jwt_auth import JWTAuthMiddleware
        from fastapi import HTTPException

        middleware = JWTAuthMiddleware(mock_app)
        mock_request.headers = {"Authorization": "Bearer "}

        call_next = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(mock_request, call_next)

        assert exc_info.value.status_code == 401
