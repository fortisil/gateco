"""In-memory rate limiter for auth endpoints (D6).

Dev-only, single-process. Resets on restart.
# TODO: Replace with Redis-backed rate limiter for production
"""

import os
import time
from collections import defaultdict

from gateco.exceptions import RateLimitError

_MAX_ATTEMPTS = 50 if os.getenv("DEBUG", "").lower() in ("true", "1") else 5
_WINDOW_SECONDS = 15 * 60  # 15 minutes

# key: email, value: list of timestamps
_attempts: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(email: str) -> None:
    """Raise RateLimitError if email has exceeded login/signup attempt limit."""
    now = time.time()
    cutoff = now - _WINDOW_SECONDS

    # Prune old entries
    _attempts[email] = [t for t in _attempts[email] if t > cutoff]

    if len(_attempts[email]) >= _MAX_ATTEMPTS:
        raise RateLimitError(detail="Too many attempts. Please try again later.")

    _attempts[email].append(now)


def reset_rate_limits() -> None:
    """Reset all rate limits (for testing)."""
    _attempts.clear()
