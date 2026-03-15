"""Tests for database models.

Tests model instantiation, properties, and basic operations.
"""

import datetime
import uuid

import pytest

from src.gateco.database.enums import (
    AccessRuleType,
    BillingPeriod,
    OAuthProvider,
    PaymentStatus,
    PlanTier,
    ResourceType,
    SubscriptionStatus,
    UserRole,
)
from src.gateco.database.models import (
    AccessRule,
    GatedResource,
    Invite,
    OAuthAccount,
    Organization,
    Payment,
    Subscription,
    User,
    UserSession,
)


class TestOrganization:
    """Tests for Organization model."""

    def test_create_organization(self):
        """Test creating an organization instance."""
        org = Organization(
            id=uuid.uuid4(),
            name="Test Corp",
            slug="test-corp",
            plan=PlanTier.free,
        )
        assert org.name == "Test Corp"
        assert org.slug == "test-corp"
        assert org.plan == PlanTier.free
        assert org.is_free_tier is True
        assert org.is_paid_tier is False

    def test_organization_pro_tier(self):
        """Test organization on pro tier."""
        org = Organization(
            id=uuid.uuid4(),
            name="Pro Corp",
            slug="pro-corp",
            plan=PlanTier.pro,
        )
        assert org.is_free_tier is False
        assert org.is_paid_tier is True

    def test_organization_soft_delete(self):
        """Test soft delete functionality."""
        org = Organization(
            id=uuid.uuid4(),
            name="Test Corp",
            slug="test-corp",
        )
        assert org.is_deleted is False
        org.soft_delete()
        assert org.is_deleted is True
        assert org.deleted_at is not None

    def test_organization_restore(self):
        """Test restore after soft delete."""
        org = Organization(
            id=uuid.uuid4(),
            name="Test Corp",
            slug="test-corp",
        )
        org.soft_delete()
        assert org.is_deleted is True
        org.restore()
        assert org.is_deleted is False
        assert org.deleted_at is None

    def test_organization_repr(self):
        """Test organization string representation."""
        org = Organization(
            id=uuid.uuid4(),
            name="Test Corp",
            slug="test-corp",
            plan=PlanTier.pro,
        )
        repr_str = repr(org)
        assert "Organization" in repr_str
        assert "test-corp" in repr_str
        assert "pro" in repr_str


class TestUser:
    """Tests for User model."""

    def test_create_user(self):
        """Test creating a user instance."""
        user = User(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            email="test@example.com",
            name="Test User",
            role=UserRole.member,
        )
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.role == UserRole.member
        assert user.has_password is False

    def test_user_with_password(self):
        """Test user with password hash."""
        user = User(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            email="test@example.com",
            name="Test User",
            password_hash="$2b$12$...",
        )
        assert user.has_password is True

    def test_user_roles(self):
        """Test user role properties."""
        owner = User(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            email="owner@example.com",
            name="Owner",
            role=UserRole.owner,
        )
        assert owner.is_owner is True
        assert owner.is_admin is True

        admin = User(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            email="admin@example.com",
            name="Admin",
            role=UserRole.admin,
        )
        assert admin.is_owner is False
        assert admin.is_admin is True

        member = User(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            email="member@example.com",
            name="Member",
            role=UserRole.member,
        )
        assert member.is_owner is False
        assert member.is_admin is False

    def test_user_email_verification(self):
        """Test email verification."""
        user = User(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            email="test@example.com",
            name="Test User",
        )
        assert user.is_email_verified is False
        user.verify_email()
        assert user.is_email_verified is True
        assert user.email_verified_at is not None

    def test_user_last_login(self):
        """Test last login update."""
        user = User(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            email="test@example.com",
            name="Test User",
        )
        assert user.last_login_at is None
        user.update_last_login()
        assert user.last_login_at is not None


class TestUserSession:
    """Tests for UserSession model."""

    def test_create_session(self):
        """Test creating a session instance."""
        now = datetime.datetime.now(datetime.timezone.utc)
        expires = now + datetime.timedelta(days=7)
        session = UserSession(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            refresh_token_hash="token_hash_here",
            expires_at=expires,
        )
        assert session.is_valid is True
        assert session.is_expired is False
        assert session.is_revoked is False

    def test_session_revocation(self):
        """Test session revocation."""
        now = datetime.datetime.now(datetime.timezone.utc)
        expires = now + datetime.timedelta(days=7)
        session = UserSession(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            refresh_token_hash="token_hash_here",
            expires_at=expires,
        )
        assert session.is_valid is True
        session.revoke()
        assert session.is_valid is False
        assert session.is_revoked is True
        assert session.revoked_at is not None

    def test_expired_session(self):
        """Test expired session."""
        now = datetime.datetime.now(datetime.timezone.utc)
        expired = now - datetime.timedelta(hours=1)
        session = UserSession(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            refresh_token_hash="token_hash_here",
            expires_at=expired,
        )
        assert session.is_valid is False
        assert session.is_expired is True


class TestOAuthAccount:
    """Tests for OAuthAccount model."""

    def test_create_oauth_account(self):
        """Test creating an OAuth account."""
        account = OAuthAccount(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            provider=OAuthProvider.google,
            provider_user_id="google_user_123",
        )
        assert account.provider == OAuthProvider.google
        assert account.provider_user_id == "google_user_123"

    def test_token_expiration(self):
        """Test token expiration checking."""
        now = datetime.datetime.now(datetime.timezone.utc)
        expired = now - datetime.timedelta(hours=1)
        account = OAuthAccount(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            provider=OAuthProvider.github,
            provider_user_id="github_user_123",
            expires_at=expired,
        )
        assert account.is_token_expired is True

    def test_update_tokens(self):
        """Test updating OAuth tokens."""
        account = OAuthAccount(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            provider=OAuthProvider.google,
            provider_user_id="google_user_123",
        )
        account.update_tokens(
            access_token="new_access_token",
            refresh_token="new_refresh_token",
            expires_in=3600,
        )
        assert account.access_token == "new_access_token"
        assert account.refresh_token == "new_refresh_token"
        assert account.expires_at is not None


class TestGatedResource:
    """Tests for GatedResource model."""

    def test_create_resource(self):
        """Test creating a gated resource."""
        resource = GatedResource(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            type=ResourceType.link,
            title="Test Resource",
            content_url="https://example.com/content",
        )
        assert resource.type == ResourceType.link
        assert resource.is_link is True
        assert resource.is_file is False
        assert resource.view_count == 0

    def test_resource_counters(self):
        """Test resource view counting."""
        resource = GatedResource(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            type=ResourceType.file,
            title="Test File",
            content_url="https://example.com/file.pdf",
        )
        resource.increment_views()
        assert resource.view_count == 1
        assert resource.unique_viewers == 0

        resource.increment_views(is_unique=True)
        assert resource.view_count == 2
        assert resource.unique_viewers == 1

    def test_resource_revenue(self):
        """Test resource revenue tracking."""
        resource = GatedResource(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            type=ResourceType.video,
            title="Premium Video",
            content_url="https://example.com/video",
        )
        assert resource.revenue_cents == 0
        assert resource.revenue_dollars == 0.0

        resource.add_revenue(999)
        assert resource.revenue_cents == 999
        assert resource.revenue_dollars == 9.99


class TestAccessRule:
    """Tests for AccessRule model."""

    def test_create_public_rule(self):
        """Test creating a public access rule."""
        rule = AccessRule(
            id=uuid.uuid4(),
            resource_id=uuid.uuid4(),
            type=AccessRuleType.public,
        )
        assert rule.is_public is True
        assert rule.is_paid is False
        assert rule.price_cents is None

    def test_create_paid_rule(self):
        """Test creating a paid access rule."""
        rule = AccessRule(
            id=uuid.uuid4(),
            resource_id=uuid.uuid4(),
            type=AccessRuleType.paid,
            price_cents=999,
            currency="USD",
        )
        assert rule.is_paid is True
        assert rule.price_cents == 999
        assert rule.price_dollars == 9.99

    def test_invite_only_rule(self):
        """Test invite-only access rule."""
        rule = AccessRule(
            id=uuid.uuid4(),
            resource_id=uuid.uuid4(),
            type=AccessRuleType.invite_only,
            allowed_emails=["user1@example.com", "user2@example.com"],
        )
        assert rule.is_invite_only is True
        assert rule.is_email_allowed("user1@example.com") is True
        assert rule.is_email_allowed("User1@Example.com") is True  # Case insensitive
        assert rule.is_email_allowed("unknown@example.com") is False

    def test_add_remove_allowed_email(self):
        """Test adding and removing allowed emails."""
        rule = AccessRule(
            id=uuid.uuid4(),
            resource_id=uuid.uuid4(),
            type=AccessRuleType.invite_only,
            allowed_emails=["user1@example.com"],
        )
        rule.add_allowed_email("user2@example.com")
        assert len(rule.allowed_emails) == 2
        assert "user2@example.com" in rule.allowed_emails

        rule.remove_allowed_email("user1@example.com")
        assert len(rule.allowed_emails) == 1
        assert "user1@example.com" not in rule.allowed_emails


class TestInvite:
    """Tests for Invite model."""

    def test_create_invite(self):
        """Test creating an invite."""
        now = datetime.datetime.now(datetime.timezone.utc)
        expires = now + datetime.timedelta(days=7)
        invite = Invite(
            id=uuid.uuid4(),
            resource_id=uuid.uuid4(),
            email="invited@example.com",
            token="test_token_123",
            expires_at=expires,
        )
        assert invite.is_valid is True
        assert invite.is_used is False

    def test_use_invite(self):
        """Test using an invite."""
        now = datetime.datetime.now(datetime.timezone.utc)
        expires = now + datetime.timedelta(days=7)
        invite = Invite(
            id=uuid.uuid4(),
            resource_id=uuid.uuid4(),
            email="invited@example.com",
            token="test_token_123",
            expires_at=expires,
        )
        invite.use()
        assert invite.is_valid is False
        assert invite.is_used is True
        assert invite.used_at is not None

    def test_expired_invite(self):
        """Test expired invite."""
        now = datetime.datetime.now(datetime.timezone.utc)
        expired = now - datetime.timedelta(days=1)
        invite = Invite(
            id=uuid.uuid4(),
            resource_id=uuid.uuid4(),
            email="invited@example.com",
            token="test_token_123",
            expires_at=expired,
        )
        assert invite.is_valid is False
        assert invite.is_expired is True


class TestSubscription:
    """Tests for Subscription model."""

    def test_create_subscription(self):
        """Test creating a subscription."""
        now = datetime.datetime.now(datetime.timezone.utc)
        subscription = Subscription(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            plan_tier=PlanTier.pro,
            status=SubscriptionStatus.active,
            billing_period=BillingPeriod.monthly,
            current_period_start=now,
            current_period_end=now + datetime.timedelta(days=30),
        )
        assert subscription.is_active is True
        assert subscription.is_canceled is False

    def test_cancel_subscription(self):
        """Test canceling a subscription."""
        now = datetime.datetime.now(datetime.timezone.utc)
        subscription = Subscription(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            plan_tier=PlanTier.pro,
            status=SubscriptionStatus.active,
            billing_period=BillingPeriod.monthly,
            current_period_start=now,
            current_period_end=now + datetime.timedelta(days=30),
        )
        subscription.cancel(at_period_end=True)
        assert subscription.is_canceled is True
        assert subscription.cancel_at_period_end is True


class TestPayment:
    """Tests for Payment model."""

    def test_create_payment(self):
        """Test creating a payment."""
        payment = Payment(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            amount_cents=999,
            currency="USD",
            status=PaymentStatus.succeeded,
        )
        assert payment.amount_cents == 999
        assert payment.amount_dollars == 9.99
        assert payment.is_succeeded is True
        assert payment.is_pending is False
