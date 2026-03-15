"""
Middleware package.

Re-exports authentication dependencies.
"""

from .admin_auth import require_admin_token

__all__ = ["require_admin_token"]
