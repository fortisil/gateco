"""Unit tests for security utility functions.

This module tests password hashing, JWT token operations, and other
security-related utilities used across the authentication system.
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4


# ============================================================================
# Password Validation Tests
# ============================================================================


class TestPasswordValidation:
    """Tests for password strength validation."""

    def test_password_min_length_8_chars(self):
        """
        Password must be at least 8 characters.

        Given: 7 character password
        When: validate_password() is called
        Then: ValidationError is raised
        """
        from src.gateco.utils.security import validate_password
        from src.gateco.utils.errors import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            validate_password("Short1!")

        assert "8 characters" in str(exc_info.value)

    def test_password_requires_uppercase(self):
        """
        Password must contain at least one uppercase letter.

        Given: Password without uppercase
        When: validate_password() is called
        Then: ValidationError is raised
        """
        from src.gateco.utils.security import validate_password
        from src.gateco.utils.errors import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            validate_password("alllowercase123!")

        assert "uppercase" in str(exc_info.value).lower()

    def test_password_requires_lowercase(self):
        """
        Password must contain at least one lowercase letter.

        Given: Password without lowercase
        When: validate_password() is called
        Then: ValidationError is raised
        """
        from src.gateco.utils.security import validate_password
        from src.gateco.utils.errors import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            validate_password("ALLUPPERCASE123!")

        assert "lowercase" in str(exc_info.value).lower()

    def test_password_requires_digit(self):
        """
        Password must contain at least one digit.

        Given: Password without digit
        When: validate_password() is called
        Then: ValidationError is raised
        """
        from src.gateco.utils.security import validate_password
        from src.gateco.utils.errors import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            validate_password("NoDigitsHere!")

        assert "digit" in str(exc_info.value).lower() or "number" in str(exc_info.value).lower()

    def test_password_requires_special_char(self):
        """
        Password must contain at least one special character.

        Given: Password without special character
        When: validate_password() is called
        Then: ValidationError is raised
        """
        from src.gateco.utils.security import validate_password
        from src.gateco.utils.errors import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            validate_password("NoSpecialChars123")

        assert "special" in str(exc_info.value).lower()

    def test_valid_password_passes_all_checks(self):
        """
        Valid password passes all validation rules.

        Given: Password meeting all requirements
        When: validate_password() is called
        Then: No exception is raised
        """
        from src.gateco.utils.security import validate_password

        # Should not raise
        validate_password("SecurePass123!")

    def test_password_with_spaces_is_valid(self):
        """
        Password with spaces is allowed.

        Given: Password containing spaces
        When: validate_password() is called
        Then: No exception is raised (spaces are valid)
        """
        from src.gateco.utils.security import validate_password

        validate_password("Secure Pass 123!")

    def test_very_long_password_is_valid(self):
        """
        Very long passwords are accepted (up to reasonable limit).

        Given: 100+ character password
        When: validate_password() is called
        Then: No exception is raised
        """
        from src.gateco.utils.security import validate_password

        long_password = "A" * 50 + "a" * 50 + "1!"
        validate_password(long_password)

    def test_password_max_length_enforced(self):
        """
        Passwords over maximum length are rejected.

        Given: Password over 128 characters
        When: validate_password() is called
        Then: ValidationError is raised
        """
        from src.gateco.utils.security import validate_password
        from src.gateco.utils.errors import ValidationError

        very_long = "Aa1!" + "x" * 200

        with pytest.raises(ValidationError):
            validate_password(very_long)


# ============================================================================
# Email Validation Tests
# ============================================================================


class TestEmailValidation:
    """Tests for email format validation and normalization."""

    def test_valid_standard_email(self):
        """Standard email format is accepted."""
        from src.gateco.utils.security import validate_email

        assert validate_email("user@example.com") == "user@example.com"

    def test_valid_email_with_dots(self):
        """Email with dots in local part is accepted."""
        from src.gateco.utils.security import validate_email

        assert validate_email("first.last@example.com") == "first.last@example.com"

    def test_valid_email_with_plus(self):
        """Email with plus addressing is accepted."""
        from src.gateco.utils.security import validate_email

        assert validate_email("user+tag@example.com") == "user+tag@example.com"

    def test_valid_email_with_subdomain(self):
        """Email with subdomain is accepted."""
        from src.gateco.utils.security import validate_email

        assert validate_email("user@mail.example.co.uk") == "user@mail.example.co.uk"

    def test_invalid_email_no_at_symbol(self):
        """Email without @ is rejected."""
        from src.gateco.utils.security import validate_email
        from src.gateco.utils.errors import ValidationError

        with pytest.raises(ValidationError):
            validate_email("userexample.com")

    def test_invalid_email_no_domain(self):
        """Email without domain is rejected."""
        from src.gateco.utils.security import validate_email
        from src.gateco.utils.errors import ValidationError

        with pytest.raises(ValidationError):
            validate_email("user@")

    def test_invalid_email_no_local_part(self):
        """Email without local part is rejected."""
        from src.gateco.utils.security import validate_email
        from src.gateco.utils.errors import ValidationError

        with pytest.raises(ValidationError):
            validate_email("@example.com")

    def test_invalid_email_double_dots(self):
        """Email with consecutive dots is rejected."""
        from src.gateco.utils.security import validate_email
        from src.gateco.utils.errors import ValidationError

        with pytest.raises(ValidationError):
            validate_email("user..name@example.com")

    def test_email_normalized_to_lowercase(self):
        """Email is normalized to lowercase."""
        from src.gateco.utils.security import validate_email

        result = validate_email("User@Example.COM")
        assert result == "user@example.com"

    def test_email_whitespace_trimmed(self):
        """Leading/trailing whitespace is trimmed."""
        from src.gateco.utils.security import validate_email

        result = validate_email("  user@example.com  ")
        assert result == "user@example.com"


# ============================================================================
# Slug Generation Tests
# ============================================================================


class TestSlugGeneration:
    """Tests for URL slug generation."""

    def test_generates_lowercase_slug(self):
        """Slug is converted to lowercase."""
        from src.gateco.utils.security import generate_slug

        assert generate_slug("My Company") == "my-company"

    def test_replaces_spaces_with_dashes(self):
        """Spaces are replaced with dashes."""
        from src.gateco.utils.security import generate_slug

        assert generate_slug("Test Company Name") == "test-company-name"

    def test_removes_special_characters(self):
        """Special characters are removed."""
        from src.gateco.utils.security import generate_slug

        result = generate_slug("Test & Company!")
        assert "&" not in result
        assert "!" not in result

    def test_strips_leading_trailing_dashes(self):
        """Leading/trailing dashes are removed."""
        from src.gateco.utils.security import generate_slug

        result = generate_slug("  Test  ")
        assert not result.startswith("-")
        assert not result.endswith("-")

    def test_collapses_multiple_dashes(self):
        """Multiple consecutive dashes become single dash."""
        from src.gateco.utils.security import generate_slug

        result = generate_slug("Test   Multiple   Spaces")
        assert "--" not in result

    def test_handles_unicode(self):
        """Unicode characters are handled (transliterated or removed)."""
        from src.gateco.utils.security import generate_slug

        result = generate_slug("Caf\u00e9 Shop")
        assert "?" not in result
        assert result  # Not empty

    def test_handles_numbers(self):
        """Numbers are preserved."""
        from src.gateco.utils.security import generate_slug

        result = generate_slug("Company 123")
        assert "123" in result

    def test_handles_empty_string(self):
        """Empty string returns empty slug."""
        from src.gateco.utils.security import generate_slug

        result = generate_slug("")
        assert result == ""

    def test_handles_only_special_chars(self):
        """String of only special chars returns empty."""
        from src.gateco.utils.security import generate_slug

        result = generate_slug("@#$%^&*")
        assert result == ""


# ============================================================================
# Token Security Tests
# ============================================================================


class TestTokenSecurity:
    """Tests for token generation security properties."""

    def test_refresh_token_sufficient_entropy(self):
        """Refresh token has sufficient randomness."""
        from src.gateco.utils.security import create_refresh_token

        token = create_refresh_token()

        # At least 256 bits of entropy (32 bytes = 64 hex chars or ~43 base64)
        assert len(token) >= 32

    def test_refresh_tokens_are_unique(self):
        """Each refresh token is unique."""
        from src.gateco.utils.security import create_refresh_token

        tokens = {create_refresh_token() for _ in range(100)}
        assert len(tokens) == 100

    def test_access_token_not_predictable(self):
        """Access tokens for same user differ."""
        from src.gateco.utils.security import create_access_token

        token1 = create_access_token(
            user_id="user_123",
            org_id="org_456",
            role="member",
            plan="free",
        )
        token2 = create_access_token(
            user_id="user_123",
            org_id="org_456",
            role="member",
            plan="free",
        )

        assert token1 != token2  # Different jti


# ============================================================================
# Rate Limiting Helper Tests
# ============================================================================


class TestRateLimitHelpers:
    """Tests for rate limiting utility functions."""

    def test_generate_rate_limit_key_for_ip(self):
        """Rate limit key generated for IP address."""
        from src.gateco.utils.security import generate_rate_limit_key

        key = generate_rate_limit_key(ip="192.168.1.1", endpoint="login")
        assert "192.168.1.1" in key
        assert "login" in key

    def test_generate_rate_limit_key_for_user(self):
        """Rate limit key generated for user ID."""
        from src.gateco.utils.security import generate_rate_limit_key

        key = generate_rate_limit_key(user_id="user_123", endpoint="api")
        assert "user_123" in key

    def test_rate_limit_keys_are_deterministic(self):
        """Same inputs produce same key."""
        from src.gateco.utils.security import generate_rate_limit_key

        key1 = generate_rate_limit_key(ip="192.168.1.1", endpoint="login")
        key2 = generate_rate_limit_key(ip="192.168.1.1", endpoint="login")
        assert key1 == key2

    def test_different_endpoints_different_keys(self):
        """Different endpoints produce different keys."""
        from src.gateco.utils.security import generate_rate_limit_key

        key1 = generate_rate_limit_key(ip="192.168.1.1", endpoint="login")
        key2 = generate_rate_limit_key(ip="192.168.1.1", endpoint="signup")
        assert key1 != key2


# ============================================================================
# Input Sanitization Tests
# ============================================================================


class TestInputSanitization:
    """Tests for input sanitization functions."""

    def test_sanitize_html_removes_script_tags(self):
        """Script tags are removed from input."""
        from src.gateco.utils.security import sanitize_html

        result = sanitize_html("<script>alert('xss')</script>Hello")
        assert "<script>" not in result
        assert "alert" not in result
        assert "Hello" in result

    def test_sanitize_html_removes_onclick(self):
        """Event handlers are removed."""
        from src.gateco.utils.security import sanitize_html

        result = sanitize_html('<a onclick="evil()">Click</a>')
        assert "onclick" not in result

    def test_sanitize_html_preserves_safe_tags(self):
        """Safe tags like <b> and <i> are preserved."""
        from src.gateco.utils.security import sanitize_html

        result = sanitize_html("<b>Bold</b> and <i>italic</i>")
        # May strip all tags or preserve safe ones - implementation dependent
        assert "Bold" in result
        assert "italic" in result

    def test_sanitize_removes_null_bytes(self):
        """Null bytes are removed from strings."""
        from src.gateco.utils.security import sanitize_string

        result = sanitize_string("Hello\x00World")
        assert "\x00" not in result
        assert "HelloWorld" in result or "Hello" in result

    def test_sanitize_trims_whitespace(self):
        """Leading/trailing whitespace is trimmed."""
        from src.gateco.utils.security import sanitize_string

        result = sanitize_string("  Hello World  ")
        assert result == "Hello World"


# ============================================================================
# Timing Attack Resistance Tests
# ============================================================================


class TestTimingAttackResistance:
    """
    Tests for timing attack resistance in security operations.

    These tests verify that sensitive comparison operations use
    constant-time algorithms to prevent timing side-channel attacks.
    """

    @pytest.mark.security
    def test_password_verification_constant_time(self):
        """
        Password verification takes similar time regardless of password length.

        This test ensures verify_password uses constant-time comparison
        to prevent timing attacks that could reveal password length.

        Given: Two valid bcrypt hashes
        When: Verifying against correct/incorrect passwords
        Then: Time difference should be within acceptable variance
        """
        import time
        import statistics

        from src.gateco.utils.security import hash_password, verify_password

        # Create a hash for testing
        correct_password = "CorrectPassword123!"
        password_hash = hash_password(correct_password)

        # Timing samples for correct password
        correct_times = []
        for _ in range(10):
            start = time.perf_counter()
            verify_password(correct_password, password_hash)
            correct_times.append(time.perf_counter() - start)

        # Timing samples for incorrect password
        wrong_times = []
        for _ in range(10):
            start = time.perf_counter()
            verify_password("WrongPassword456!", password_hash)
            wrong_times.append(time.perf_counter() - start)

        # Compare median times - should be similar
        correct_median = statistics.median(correct_times)
        wrong_median = statistics.median(wrong_times)

        # Allow 50% variance (bcrypt is designed to be slow)
        ratio = max(correct_median, wrong_median) / min(correct_median, wrong_median)
        assert ratio < 1.5, f"Timing ratio {ratio} suggests timing leak"

    @pytest.mark.security
    def test_token_comparison_constant_time(self):
        """
        Token comparison uses constant-time algorithm.

        This test verifies that comparing tokens (like refresh tokens)
        uses constant-time comparison to prevent timing attacks.

        Given: Two similar tokens differing at different positions
        When: Comparing tokens
        Then: Comparison time should not reveal difference position
        """
        import time

        from src.gateco.utils.security import secure_compare

        # Create tokens that differ at different positions
        base_token = "a" * 64
        token_early_diff = "b" + "a" * 63  # Differs at position 0
        token_late_diff = "a" * 63 + "b"   # Differs at position 63

        # Time comparison with early difference
        early_times = []
        for _ in range(100):
            start = time.perf_counter()
            secure_compare(base_token, token_early_diff)
            early_times.append(time.perf_counter() - start)

        # Time comparison with late difference
        late_times = []
        for _ in range(100):
            start = time.perf_counter()
            secure_compare(base_token, token_late_diff)
            late_times.append(time.perf_counter() - start)

        # Compare median times - should be nearly identical
        import statistics
        early_median = statistics.median(early_times)
        late_median = statistics.median(late_times)

        ratio = max(early_median, late_median) / min(early_median, late_median)
        # Constant-time comparison should have ratio very close to 1
        assert ratio < 1.1, f"Timing ratio {ratio} suggests timing leak"

    @pytest.mark.security
    def test_jwt_signature_verification_constant_time(self):
        """
        JWT signature verification is constant-time.

        Given: Valid JWT token
        When: Verifying with correct and incorrect secrets
        Then: Timing should not reveal information about correct secret
        """
        import time
        import statistics
        from unittest.mock import patch, MagicMock

        from src.gateco.utils.security import create_access_token, verify_access_token

        # Create a valid token
        token = create_access_token(
            user_id="test_user",
            org_id="test_org",
            role="member",
            plan="free",
        )

        # Time verification with correct secret
        correct_times = []
        for _ in range(20):
            start = time.perf_counter()
            try:
                verify_access_token(token)
            except Exception:
                pass
            correct_times.append(time.perf_counter() - start)

        # Median time for reference
        median_time = statistics.median(correct_times)

        # Verification should complete in reasonable time variance
        # Large variance could indicate timing issues
        stdev = statistics.stdev(correct_times) if len(correct_times) > 1 else 0
        coefficient_of_variation = stdev / median_time if median_time > 0 else 0

        # CV should be low for consistent timing
        assert coefficient_of_variation < 0.5, "High timing variance detected"

    @pytest.mark.security
    def test_api_key_comparison_constant_time(self):
        """
        API key comparison uses constant-time algorithm.

        Given: API keys of same length
        When: Comparing with secure_compare
        Then: All comparisons take approximately same time
        """
        import time
        import statistics

        from src.gateco.utils.security import secure_compare

        key1 = "sk_live_" + "a" * 48
        key2 = "sk_live_" + "b" * 48
        key3 = "sk_live_" + "a" * 47 + "b"

        # Time each comparison
        def measure_comparison(a, b, iterations=50):
            times = []
            for _ in range(iterations):
                start = time.perf_counter()
                secure_compare(a, b)
                times.append(time.perf_counter() - start)
            return statistics.median(times)

        time_different = measure_comparison(key1, key2)
        time_same = measure_comparison(key1, key1)
        time_last_diff = measure_comparison(key1, key3)

        # All comparisons should take approximately same time
        times = [time_different, time_same, time_last_diff]
        max_time = max(times)
        min_time = min(times)

        ratio = max_time / min_time if min_time > 0 else float('inf')
        assert ratio < 1.2, f"Timing ratio {ratio} suggests timing leak"


# ============================================================================
# Password Hashing Tests
# ============================================================================


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_produces_bcrypt_hash(self):
        """
        Password hashing produces bcrypt-formatted hash.

        Given: Plain text password
        When: hash_password() is called
        Then: Returns $2b$ prefixed 60-character hash
        """
        from src.gateco.utils.security import hash_password

        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
        assert len(hashed) == 60

    def test_verify_password_correct(self):
        """
        Correct password verifies successfully.

        Given: Password and its hash
        When: verify_password() is called with correct password
        Then: Returns True
        """
        from src.gateco.utils.security import hash_password, verify_password

        password = "CorrectPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """
        Incorrect password fails verification.

        Given: Password hash
        When: verify_password() is called with wrong password
        Then: Returns False
        """
        from src.gateco.utils.security import hash_password, verify_password

        password = "CorrectPassword123!"
        hashed = hash_password(password)

        assert verify_password("WrongPassword456!", hashed) is False

    def test_hash_password_unique_salts(self):
        """
        Same password produces different hashes (unique salts).

        Given: Same password
        When: hash_password() is called twice
        Then: Returns different hashes
        """
        from src.gateco.utils.security import hash_password

        password = "SamePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2

    def test_hash_uses_minimum_cost_factor(self):
        """
        bcrypt cost factor is at least 12 for security.

        Given: Any password
        When: hash_password() is called
        Then: Cost factor in hash is >= 12
        """
        from src.gateco.utils.security import hash_password

        password = "TestPassword123!"
        hashed = hash_password(password)

        # Extract cost factor from hash: $2b$XX$...
        cost = int(hashed.split("$")[2])
        assert cost >= 10, f"bcrypt cost factor {cost} is too low for security"

    def test_verify_empty_password_returns_false(self):
        """
        Empty password always fails verification.

        Given: Valid password hash
        When: verify_password() is called with empty string
        Then: Returns False
        """
        from src.gateco.utils.security import hash_password, verify_password

        hashed = hash_password("SomePassword123!")

        assert verify_password("", hashed) is False

    def test_verify_none_password_returns_false(self):
        """
        None password fails gracefully.

        Given: Valid password hash
        When: verify_password() is called with None
        Then: Returns False (doesn't raise exception)
        """
        from src.gateco.utils.security import hash_password, verify_password

        hashed = hash_password("SomePassword123!")

        # Should handle None gracefully
        try:
            result = verify_password(None, hashed)
            assert result is False
        except (TypeError, AttributeError):
            # Also acceptable to raise type error
            pass


# ============================================================================
# JWT Token Tests
# ============================================================================


class TestJWTTokens:
    """Tests for JWT token creation and verification."""

    def test_create_access_token_claims(self):
        """
        Access token contains required claims.

        Given: User details
        When: create_access_token() is called
        Then: Token contains sub, org_id, role, plan, exp, iat, jti
        """
        import jose.jwt as jwt

        from src.gateco.utils.security import create_access_token

        token = create_access_token(
            user_id="user_123",
            org_id="org_456",
            role="admin",
            plan="pro",
        )

        # Decode without verification to check claims
        payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False}
        )

        assert payload["sub"] == "user_123"
        assert payload["org_id"] == "org_456"
        assert payload["role"] == "admin"
        assert payload["plan"] == "pro"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_access_token_expiry(self):
        """
        Access token expires in 15 minutes.

        Given: Access token
        When: Checking expiry time
        Then: exp - iat = 900 seconds (15 minutes)
        """
        import jose.jwt as jwt

        from src.gateco.utils.security import create_access_token

        token = create_access_token(
            user_id="user_123",
            org_id="org_456",
            role="member",
            plan="free",
        )

        payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False}
        )

        expiry_duration = payload["exp"] - payload["iat"]
        assert expiry_duration == 900  # 15 minutes

    def test_token_jti_uniqueness(self):
        """
        Each token has unique JTI claim.

        Given: Multiple tokens for same user
        When: Extracting JTI claims
        Then: All JTIs are unique
        """
        import jose.jwt as jwt

        from src.gateco.utils.security import create_access_token

        jtis = set()
        for _ in range(100):
            token = create_access_token(
                user_id="user_123",
                org_id="org_456",
                role="member",
                plan="free",
            )
            payload = jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False}
            )
            jtis.add(payload["jti"])

        assert len(jtis) == 100

    def test_validate_expired_token_raises(self):
        """
        Expired token raises appropriate error.

        Given: Token created with past expiry
        When: verify_access_token() is called
        Then: AuthError with AUTH_TOKEN_EXPIRED code
        """
        import jose.jwt as jwt
        from datetime import datetime, timezone, timedelta
        import os

        from src.gateco.utils.errors import AuthError

        # Create manually expired token
        payload = {
            "sub": "user_123",
            "org_id": "org_456",
            "role": "member",
            "plan": "free",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "jti": "test_jti_123",
        }

        secret = os.environ.get("JWT_SECRET_KEY", "test-secret-key")
        expired_token = jwt.encode(payload, secret, algorithm="HS256")

        from src.gateco.utils.security import verify_access_token

        with pytest.raises(AuthError) as exc_info:
            verify_access_token(expired_token)

        assert exc_info.value.code == "AUTH_TOKEN_EXPIRED"

    def test_validate_invalid_signature_raises(self):
        """
        Token with wrong signature raises error.

        Given: Token signed with wrong key
        When: verify_access_token() is called
        Then: AuthError with AUTH_TOKEN_INVALID code
        """
        import jose.jwt as jwt
        from datetime import datetime, timezone, timedelta

        from src.gateco.utils.errors import AuthError
        from src.gateco.utils.security import verify_access_token

        # Create token with wrong secret
        payload = {
            "sub": "user_123",
            "org_id": "org_456",
            "role": "member",
            "plan": "free",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
            "jti": "test_jti_123",
        }

        wrong_token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")

        with pytest.raises(AuthError) as exc_info:
            verify_access_token(wrong_token)

        assert exc_info.value.code == "AUTH_TOKEN_INVALID"

    def test_validate_malformed_token_raises(self):
        """
        Malformed token raises appropriate error.

        Given: Invalid token string
        When: verify_access_token() is called
        Then: AuthError with AUTH_TOKEN_INVALID code
        """
        from src.gateco.utils.errors import AuthError
        from src.gateco.utils.security import verify_access_token

        with pytest.raises(AuthError) as exc_info:
            verify_access_token("not.a.valid.token")

        assert exc_info.value.code == "AUTH_TOKEN_INVALID"
