"""Database models package.

Exports all SQLAlchemy models and base classes for the Gateco platform.

Usage:
    from gateco.database.models import User, Organization
    from gateco.database.models import Base, TimestampMixin
"""

# Phase 2: Resources
from gateco.database.models.access_rule import AccessRule
from gateco.database.models.app_settings import AppSettings

# Phase 4: Permission-aware retrieval layer
from gateco.database.models.audit_event import AuditEvent
from gateco.database.models.base import (
    Base,
    OrganizationScopedMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from gateco.database.models.connector import Connector

# Wave 3: Platform completion
from gateco.database.models.idempotency import IdempotencyRecord

# Phase 3: Billing
from gateco.database.models.coupon import Coupon
from gateco.database.models.identity_provider import IdentityProvider
from gateco.database.models.invite import Invite
from gateco.database.models.invoice import Invoice

# Phase 1: Core Auth
from gateco.database.models.oauth_account import OAuthAccount
from gateco.database.models.organization import Organization
from gateco.database.models.payment import Payment
from gateco.database.models.pipeline import Pipeline
from gateco.database.models.pipeline_run import PipelineRun
from gateco.database.models.policy import Policy
from gateco.database.models.policy_rule import PolicyRule
from gateco.database.models.principal import Principal
from gateco.database.models.principal_group import PrincipalGroup
from gateco.database.models.resource import GatedResource
from gateco.database.models.resource_chunk import ResourceChunk
from gateco.database.models.secured_retrieval import SecuredRetrieval
from gateco.database.models.session import UserSession
from gateco.database.models.stripe_event import StripeEvent
from gateco.database.models.subscription import Subscription
from gateco.database.models.usage import UsageLog
from gateco.database.models.user import User

__all__ = [
    # Legacy
    "AppSettings",
    # Base classes and mixins
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    "UUIDPrimaryKeyMixin",
    "OrganizationScopedMixin",
    # Phase 1: Core Auth Models
    "Organization",
    "User",
    "UserSession",
    "OAuthAccount",
    # Phase 2: Resource Models
    "GatedResource",
    "AccessRule",
    "Invite",
    # Phase 3: Billing Models
    "Subscription",
    "Payment",
    "Invoice",
    "UsageLog",
    "Coupon",
    "StripeEvent",
    # Phase 4: Permission-aware retrieval
    "AuditEvent",
    "Connector",
    "IdentityProvider",
    "Principal",
    "PrincipalGroup",
    "Policy",
    "PolicyRule",
    "ResourceChunk",
    "Pipeline",
    "PipelineRun",
    "SecuredRetrieval",
    # Wave 3: Platform completion
    "IdempotencyRecord",
]
