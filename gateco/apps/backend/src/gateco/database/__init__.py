"""
Database package.

Re-exports core database components for convenient access.

Usage:
    from gateco.database import get_session, User, UserRole
    from gateco.database import Organization, PlanTier
"""

from .connection import check_db_connection, engine, get_session

# Re-export enums
from .enums import (
    AccessRuleType,
    AnalyticsEventType,
    BillingPeriod,
    DiscountType,
    DomainStatus,
    InvoiceStatus,
    LeadSource,
    OAuthProvider,
    PaymentStatus,
    PlanTier,
    ResourceType,
    SSLStatus,
    SubscriptionStatus,
    UserRole,
)

# Re-export from original models.py for backward compatibility
# Re-export models from models package
from .models import (
    # Phase 2: Resources
    AccessRule,
    AppSettings,
    # Base classes
    Base,
    # Phase 3: Billing
    Coupon,
    GatedResource,
    Invite,
    Invoice,
    # Phase 1: Auth
    OAuthAccount,
    Organization,
    OrganizationScopedMixin,
    Payment,
    SoftDeleteMixin,
    StripeEvent,
    Subscription,
    TimestampMixin,
    UsageLog,
    User,
    UserSession,
    UUIDPrimaryKeyMixin,
)
from .models import Base as LegacyBase
from .models import TimestampMixin as LegacyTimestampMixin

__all__ = [
    # Connection
    "engine",
    "get_session",
    "check_db_connection",
    # Legacy (backward compatibility)
    "LegacyBase",
    "LegacyTimestampMixin",
    "AppSettings",
    # Base classes and mixins
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    "UUIDPrimaryKeyMixin",
    "OrganizationScopedMixin",
    # Enums
    "UserRole",
    "PlanTier",
    "SubscriptionStatus",
    "BillingPeriod",
    "PaymentStatus",
    "InvoiceStatus",
    "ResourceType",
    "AccessRuleType",
    "OAuthProvider",
    "DomainStatus",
    "SSLStatus",
    "LeadSource",
    "AnalyticsEventType",
    "DiscountType",
    # Phase 1 Models
    "Organization",
    "User",
    "UserSession",
    "OAuthAccount",
    # Phase 2 Models
    "GatedResource",
    "AccessRule",
    "Invite",
    # Phase 3 Models
    "Subscription",
    "Payment",
    "Invoice",
    "UsageLog",
    "Coupon",
    "StripeEvent",
]
