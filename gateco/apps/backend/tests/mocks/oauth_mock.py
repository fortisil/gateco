"""Mock OAuth providers for testing."""

from typing import Optional
from unittest.mock import MagicMock, AsyncMock
import secrets


class MockOAuthUserInfo:
    """Mock OAuth user information."""

    def __init__(
        self,
        provider: str = "google",
        provider_user_id: str = None,
        email: str = "oauth@example.com",
        name: str = "OAuth User",
        picture: str = None,
    ):
        self.provider = provider
        self.id = provider_user_id or f"{provider}_user_{secrets.token_hex(8)}"
        self.email = email
        self.name = name
        self.picture = picture or f"https://{provider}.com/avatar/{self.id}.jpg"


class MockOAuthTokens:
    """Mock OAuth tokens."""

    def __init__(
        self,
        access_token: str = None,
        refresh_token: str = None,
        expires_in: int = 3600,
        token_type: str = "Bearer",
    ):
        self.access_token = access_token or f"mock_access_{secrets.token_hex(16)}"
        self.refresh_token = refresh_token or f"mock_refresh_{secrets.token_hex(16)}"
        self.expires_in = expires_in
        self.token_type = token_type


class MockGoogleOAuth:
    """Mock Google OAuth provider."""

    def __init__(
        self,
        user_info: MockOAuthUserInfo = None,
        tokens: MockOAuthTokens = None,
        should_fail: bool = False,
        fail_reason: str = "OAuth error",
    ):
        self.user_info = user_info or MockOAuthUserInfo(provider="google")
        self.tokens = tokens or MockOAuthTokens()
        self.should_fail = should_fail
        self.fail_reason = fail_reason

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        """Generate mock Google authorization URL."""
        return (
            f"https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id=mock_client_id"
            f"&redirect_uri={redirect_uri}"
            f"&state={state}"
            f"&response_type=code"
            f"&scope=openid+email+profile"
        )

    async def exchange_code(self, code: str, redirect_uri: str) -> MockOAuthTokens:
        """Exchange authorization code for tokens."""
        if self.should_fail:
            raise Exception(self.fail_reason)
        return self.tokens

    async def get_user_info(self, access_token: str) -> MockOAuthUserInfo:
        """Get user information from Google."""
        if self.should_fail:
            raise Exception(self.fail_reason)
        return self.user_info


class MockGitHubOAuth:
    """Mock GitHub OAuth provider."""

    def __init__(
        self,
        user_info: MockOAuthUserInfo = None,
        tokens: MockOAuthTokens = None,
        should_fail: bool = False,
        fail_reason: str = "OAuth error",
    ):
        self.user_info = user_info or MockOAuthUserInfo(provider="github")
        self.tokens = tokens or MockOAuthTokens()
        self.should_fail = should_fail
        self.fail_reason = fail_reason

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        """Generate mock GitHub authorization URL."""
        return (
            f"https://github.com/login/oauth/authorize"
            f"?client_id=mock_client_id"
            f"&redirect_uri={redirect_uri}"
            f"&state={state}"
            f"&scope=user:email+read:user"
        )

    async def exchange_code(self, code: str, redirect_uri: str) -> MockOAuthTokens:
        """Exchange authorization code for tokens."""
        if self.should_fail:
            raise Exception(self.fail_reason)
        return self.tokens

    async def get_user_info(self, access_token: str) -> MockOAuthUserInfo:
        """Get user information from GitHub."""
        if self.should_fail:
            raise Exception(self.fail_reason)
        return self.user_info


def create_oauth_mock(provider: str = "google", **kwargs):
    """
    Create a mock OAuth provider.

    Args:
        provider: OAuth provider name (google, github)
        **kwargs: Arguments passed to mock constructor

    Returns:
        Mock OAuth provider instance
    """
    if provider == "google":
        return MockGoogleOAuth(**kwargs)
    elif provider == "github":
        return MockGitHubOAuth(**kwargs)
    else:
        raise ValueError(f"Unknown OAuth provider: {provider}")


def create_oauth_callback_request(
    code: str = "mock_auth_code",
    state: str = "mock_state",
    error: str = None,
    error_description: str = None,
) -> dict:
    """
    Create a mock OAuth callback request.

    Args:
        code: Authorization code
        state: State parameter
        error: OAuth error code (if any)
        error_description: Error description

    Returns:
        dict: Mock callback request data
    """
    if error:
        return {
            "error": error,
            "error_description": error_description or "OAuth error occurred",
            "state": state,
        }

    return {
        "code": code,
        "state": state,
    }


# ============================================================================
# Pre-configured OAuth Mocks
# ============================================================================

def create_successful_google_oauth(
    email: str = "user@gmail.com",
    name: str = "Google User",
) -> MockGoogleOAuth:
    """Create a successful Google OAuth mock."""
    return MockGoogleOAuth(
        user_info=MockOAuthUserInfo(
            provider="google",
            email=email,
            name=name,
        ),
    )


def create_failed_google_oauth(reason: str = "Access denied") -> MockGoogleOAuth:
    """Create a failing Google OAuth mock."""
    return MockGoogleOAuth(should_fail=True, fail_reason=reason)


def create_successful_github_oauth(
    email: str = "user@github.com",
    name: str = "GitHub User",
) -> MockGitHubOAuth:
    """Create a successful GitHub OAuth mock."""
    return MockGitHubOAuth(
        user_info=MockOAuthUserInfo(
            provider="github",
            email=email,
            name=name,
        ),
    )


def create_failed_github_oauth(reason: str = "Access denied") -> MockGitHubOAuth:
    """Create a failing GitHub OAuth mock."""
    return MockGitHubOAuth(should_fail=True, fail_reason=reason)


# ============================================================================
# OAuth State Management Mock
# ============================================================================

class MockOAuthStateStore:
    """
    Mock OAuth state storage for CSRF protection testing.

    In production, this would be Redis or database-backed.
    """

    def __init__(self):
        self._states: dict[str, dict] = {}

    def create_state(
        self,
        provider: str,
        redirect_uri: str,
        extra_data: dict = None,
    ) -> str:
        """Create and store a new state token."""
        state = secrets.token_urlsafe(32)
        self._states[state] = {
            "provider": provider,
            "redirect_uri": redirect_uri,
            "extra_data": extra_data or {},
            "created_at": "2026-02-25T12:00:00Z",
        }
        return state

    def validate_state(self, state: str) -> Optional[dict]:
        """Validate and consume a state token."""
        return self._states.pop(state, None)

    def get_state(self, state: str) -> Optional[dict]:
        """Get state data without consuming it."""
        return self._states.get(state)

    def clear(self):
        """Clear all stored states."""
        self._states.clear()
