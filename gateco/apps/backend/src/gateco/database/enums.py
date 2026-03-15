"""Database enums for Gateco platform.

All enums inherit from (str, Enum) for PostgreSQL compatibility and JSON serialization.
Enum values use lowercase snake_case for consistency.
"""

from enum import Enum


class UserRole(str, Enum):
    """User roles within an organization (D1 aligned with FE)."""

    org_admin = "org_admin"
    security_admin = "security_admin"
    data_owner = "data_owner"
    developer = "developer"


class PlanTier(str, Enum):
    """Subscription plan tiers."""

    free = "free"
    pro = "pro"
    enterprise = "enterprise"


class SubscriptionStatus(str, Enum):
    """Stripe subscription statuses."""

    active = "active"
    past_due = "past_due"
    canceled = "canceled"
    incomplete = "incomplete"
    incomplete_expired = "incomplete_expired"
    trialing = "trialing"
    unpaid = "unpaid"


class BillingPeriod(str, Enum):
    """Billing cycle periods."""

    monthly = "monthly"
    yearly = "yearly"


class PaymentStatus(str, Enum):
    """Payment transaction statuses."""

    succeeded = "succeeded"
    pending = "pending"
    failed = "failed"
    refunded = "refunded"


class InvoiceStatus(str, Enum):
    """Invoice statuses."""

    draft = "draft"
    open = "open"
    paid = "paid"
    void = "void"
    uncollectible = "uncollectible"


class ResourceType(str, Enum):
    """Types of gated resources."""

    link = "link"
    file = "file"
    video = "video"


class AccessRuleType(str, Enum):
    """Access control types for resources."""

    public = "public"
    paid = "paid"
    invite_only = "invite_only"


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""

    google = "google"
    github = "github"


class DomainStatus(str, Enum):
    """Custom domain verification status."""

    pending = "pending"
    verified = "verified"
    failed = "failed"


class SSLStatus(str, Enum):
    """SSL certificate status."""

    pending = "pending"
    active = "active"
    failed = "failed"


class LeadSource(str, Enum):
    """Marketing lead sources."""

    contact = "contact"
    newsletter = "newsletter"
    demo_request = "demo_request"


class AnalyticsEventType(str, Enum):
    """Types of analytics events."""

    resource_view = "resource_view"
    resource_access = "resource_access"
    payment_completed = "payment_completed"
    invite_sent = "invite_sent"
    invite_accepted = "invite_accepted"


class DiscountType(str, Enum):
    """Coupon discount types."""

    percentage = "percentage"
    fixed_amount = "fixed_amount"


# ── New enums for permission-aware retrieval layer ──


class ConnectorType(str, Enum):
    """Supported vector database connector types."""

    pgvector = "pgvector"
    pinecone = "pinecone"
    opensearch = "opensearch"
    supabase = "supabase"
    neon = "neon"
    weaviate = "weaviate"
    qdrant = "qdrant"
    milvus = "milvus"
    chroma = "chroma"


class ConnectorStatus(str, Enum):
    """Connector connection status."""

    connected = "connected"
    error = "error"
    syncing = "syncing"
    disconnected = "disconnected"


class IdentityProviderType(str, Enum):
    """Supported identity provider types."""

    azure_entra_id = "azure_entra_id"
    aws_iam = "aws_iam"
    gcp = "gcp"
    okta = "okta"


class IdentityProviderStatus(str, Enum):
    """Identity provider connection status."""

    connected = "connected"
    error = "error"
    syncing = "syncing"
    disconnected = "disconnected"


class PipelineStatus(str, Enum):
    """Pipeline operational status."""

    active = "active"
    paused = "paused"
    error = "error"
    running = "running"


class PipelineRunStatus(str, Enum):
    """Pipeline run execution status."""

    completed = "completed"
    failed = "failed"
    running = "running"


class PolicyType(str, Enum):
    """Access policy types."""

    rbac = "rbac"
    abac = "abac"
    rebac = "rebac"


class PolicyStatus(str, Enum):
    """Policy lifecycle status."""

    draft = "draft"
    active = "active"
    archived = "archived"


class PolicyEffect(str, Enum):
    """Policy evaluation effect."""

    allow = "allow"
    deny = "deny"


class Classification(str, Enum):
    """Data classification levels."""

    public = "public"
    internal = "internal"
    confidential = "confidential"
    restricted = "restricted"


class Sensitivity(str, Enum):
    """Data sensitivity levels."""

    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class EncryptionMode(str, Enum):
    """Encryption modes for data at rest."""

    none = "none"
    at_rest = "at_rest"
    envelope = "envelope"
    full = "full"


class AuditEventType(str, Enum):
    """Audit event types for the audit trail."""

    user_login = "user_login"
    user_logout = "user_logout"
    settings_changed = "settings_changed"
    connector_added = "connector_added"
    connector_updated = "connector_updated"
    connector_tested = "connector_tested"
    connector_removed = "connector_removed"
    connector_sync_started = "connector_sync_started"
    connector_synced = "connector_synced"
    connector_sync_failed = "connector_sync_failed"
    idp_added = "idp_added"
    idp_updated = "idp_updated"
    idp_removed = "idp_removed"
    idp_sync_started = "idp_sync_started"
    idp_synced = "idp_synced"
    idp_sync_failed = "idp_sync_failed"
    policy_created = "policy_created"
    policy_updated = "policy_updated"
    policy_activated = "policy_activated"
    policy_archived = "policy_archived"
    policy_deleted = "policy_deleted"
    resource_updated = "resource_updated"
    pipeline_created = "pipeline_created"
    pipeline_updated = "pipeline_updated"
    pipeline_run = "pipeline_run"
    pipeline_error = "pipeline_error"
    retrieval_allowed = "retrieval_allowed"
    retrieval_denied = "retrieval_denied"
    metadata_bound = "metadata_bound"
    document_ingested = "document_ingested"
    batch_ingested = "batch_ingested"
    ingestion_failed = "ingestion_failed"
    retroactive_registered = "retroactive_registered"


class RetrievalOutcome(str, Enum):
    """Secured retrieval evaluation outcome."""

    allowed = "allowed"
    partial = "partial"
    denied = "denied"


class PrincipalStatus(str, Enum):
    """Identity principal status."""

    active = "active"
    inactive = "inactive"
    suspended = "suspended"


__all__ = [
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
    "ConnectorType",
    "ConnectorStatus",
    "IdentityProviderType",
    "IdentityProviderStatus",
    "PipelineStatus",
    "PipelineRunStatus",
    "PolicyType",
    "PolicyStatus",
    "PolicyEffect",
    "Classification",
    "Sensitivity",
    "EncryptionMode",
    "AuditEventType",
    "RetrievalOutcome",
    "PrincipalStatus",
]
