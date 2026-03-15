"""Tests for database constraints.

Tests unique constraints, foreign keys, and check constraints.
These tests require an actual database connection.
"""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.gateco.database.enums import (
    AccessRuleType,
    OAuthProvider,
    PlanTier,
    UserRole,
)
from src.gateco.database.models import (
    AccessRule,
    GatedResource,
    OAuthAccount,
    Organization,
    User,
    UserSession,
)


@pytest.mark.asyncio
class TestOrganizationConstraints:
    """Tests for Organization constraints."""

    async def test_slug_uniqueness(self, db_session):
        """Test that slug must be unique."""
        org1 = Organization(
            id=uuid.uuid4(),
            name="Org One",
            slug="unique-slug",
            plan=PlanTier.free,
        )
        db_session.add(org1)
        await db_session.flush()

        org2 = Organization(
            id=uuid.uuid4(),
            name="Org Two",
            slug="unique-slug",  # Same slug - should fail
            plan=PlanTier.free,
        )
        db_session.add(org2)

        with pytest.raises(IntegrityError):
            await db_session.flush()

    async def test_stripe_customer_id_uniqueness(self, db_session):
        """Test that stripe_customer_id must be unique."""
        org1 = Organization(
            id=uuid.uuid4(),
            name="Org One",
            slug="org-one",
            plan=PlanTier.free,
            stripe_customer_id="cus_123",
        )
        db_session.add(org1)
        await db_session.flush()

        org2 = Organization(
            id=uuid.uuid4(),
            name="Org Two",
            slug="org-two",
            plan=PlanTier.free,
            stripe_customer_id="cus_123",  # Same customer ID - should fail
        )
        db_session.add(org2)

        with pytest.raises(IntegrityError):
            await db_session.flush()


@pytest.mark.asyncio
class TestUserConstraints:
    """Tests for User constraints."""

    async def test_email_unique_per_org(self, db_session):
        """Test that email must be unique within an organization."""
        org = Organization(
            id=uuid.uuid4(),
            name="Test Org",
            slug="test-org",
            plan=PlanTier.free,
        )
        db_session.add(org)
        await db_session.flush()

        user1 = User(
            id=uuid.uuid4(),
            organization_id=org.id,
            email="duplicate@example.com",
            name="User One",
            role=UserRole.member,
        )
        db_session.add(user1)
        await db_session.flush()

        user2 = User(
            id=uuid.uuid4(),
            organization_id=org.id,
            email="duplicate@example.com",  # Same email in same org
            name="User Two",
            role=UserRole.member,
        )
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            await db_session.flush()

    async def test_same_email_different_orgs(self, db_session):
        """Test that same email can exist in different organizations."""
        org1 = Organization(
            id=uuid.uuid4(),
            name="Org One",
            slug="org-one",
            plan=PlanTier.free,
        )
        org2 = Organization(
            id=uuid.uuid4(),
            name="Org Two",
            slug="org-two",
            plan=PlanTier.free,
        )
        db_session.add_all([org1, org2])
        await db_session.flush()

        user1 = User(
            id=uuid.uuid4(),
            organization_id=org1.id,
            email="shared@example.com",
            name="User One",
            role=UserRole.member,
        )
        user2 = User(
            id=uuid.uuid4(),
            organization_id=org2.id,
            email="shared@example.com",  # Same email, different org - OK
            name="User Two",
            role=UserRole.member,
        )
        db_session.add_all([user1, user2])
        await db_session.flush()  # Should not raise

        # Verify both users exist
        result = await db_session.execute(
            select(User).where(User.email == "shared@example.com")
        )
        users = result.scalars().all()
        assert len(users) == 2


@pytest.mark.asyncio
class TestCascadeDeletes:
    """Tests for cascade delete behavior."""

    async def test_user_deleted_with_org(self, db_session):
        """Test that users are deleted when organization is deleted."""
        org = Organization(
            id=uuid.uuid4(),
            name="Test Org",
            slug="test-org",
            plan=PlanTier.free,
        )
        db_session.add(org)
        await db_session.flush()

        user = User(
            id=uuid.uuid4(),
            organization_id=org.id,
            email="user@example.com",
            name="Test User",
            role=UserRole.member,
        )
        db_session.add(user)
        await db_session.flush()

        # Delete the organization
        await db_session.delete(org)
        await db_session.flush()

        # User should be deleted too
        result = await db_session.execute(select(User).where(User.id == user.id))
        assert result.scalar_one_or_none() is None

    async def test_session_deleted_with_user(self, db_session):
        """Test that sessions are deleted when user is deleted."""
        import datetime

        org = Organization(
            id=uuid.uuid4(),
            name="Test Org",
            slug="test-org",
            plan=PlanTier.free,
        )
        db_session.add(org)
        await db_session.flush()

        user = User(
            id=uuid.uuid4(),
            organization_id=org.id,
            email="user@example.com",
            name="Test User",
            role=UserRole.member,
        )
        db_session.add(user)
        await db_session.flush()

        now = datetime.datetime.now(datetime.timezone.utc)
        session = UserSession(
            id=uuid.uuid4(),
            user_id=user.id,
            refresh_token_hash="token_hash",
            expires_at=now + datetime.timedelta(days=7),
        )
        db_session.add(session)
        await db_session.flush()

        # Delete the user
        await db_session.delete(user)
        await db_session.flush()

        # Session should be deleted too
        result = await db_session.execute(
            select(UserSession).where(UserSession.id == session.id)
        )
        assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
class TestOAuthConstraints:
    """Tests for OAuth account constraints."""

    async def test_provider_user_uniqueness(self, db_session):
        """Test that provider + provider_user_id must be unique."""
        org = Organization(
            id=uuid.uuid4(),
            name="Test Org",
            slug="test-org",
            plan=PlanTier.free,
        )
        db_session.add(org)
        await db_session.flush()

        user1 = User(
            id=uuid.uuid4(),
            organization_id=org.id,
            email="user1@example.com",
            name="User One",
            role=UserRole.member,
        )
        user2 = User(
            id=uuid.uuid4(),
            organization_id=org.id,
            email="user2@example.com",
            name="User Two",
            role=UserRole.member,
        )
        db_session.add_all([user1, user2])
        await db_session.flush()

        oauth1 = OAuthAccount(
            id=uuid.uuid4(),
            user_id=user1.id,
            provider=OAuthProvider.google,
            provider_user_id="google_123",
        )
        db_session.add(oauth1)
        await db_session.flush()

        # Try to link same Google account to another user
        oauth2 = OAuthAccount(
            id=uuid.uuid4(),
            user_id=user2.id,
            provider=OAuthProvider.google,
            provider_user_id="google_123",  # Same provider + ID
        )
        db_session.add(oauth2)

        with pytest.raises(IntegrityError):
            await db_session.flush()


@pytest.mark.asyncio
class TestAccessRuleConstraints:
    """Tests for AccessRule constraints."""

    async def test_one_rule_per_resource(self, db_session):
        """Test that each resource can only have one access rule."""
        from src.gateco.database.enums import ResourceType

        org = Organization(
            id=uuid.uuid4(),
            name="Test Org",
            slug="test-org",
            plan=PlanTier.free,
        )
        db_session.add(org)
        await db_session.flush()

        resource = GatedResource(
            id=uuid.uuid4(),
            organization_id=org.id,
            type=ResourceType.link,
            title="Test Resource",
            content_url="https://example.com",
        )
        db_session.add(resource)
        await db_session.flush()

        rule1 = AccessRule(
            id=uuid.uuid4(),
            resource_id=resource.id,
            type=AccessRuleType.public,
        )
        db_session.add(rule1)
        await db_session.flush()

        # Try to add second rule to same resource
        rule2 = AccessRule(
            id=uuid.uuid4(),
            resource_id=resource.id,  # Same resource
            type=AccessRuleType.paid,
            price_cents=999,
        )
        db_session.add(rule2)

        with pytest.raises(IntegrityError):
            await db_session.flush()
