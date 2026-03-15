"""Factory for creating test users and organizations."""

from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    """User roles for RBAC."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class PlanTier(str, Enum):
    """Subscription plan tiers."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class OrganizationFactory:
    """Factory for creating test organizations."""

    @staticmethod
    def create(
        name: str = "Test Organization",
        slug: Optional[str] = None,
        plan: PlanTier = PlanTier.FREE,
        stripe_customer_id: Optional[str] = None,
    ) -> dict:
        """
        Create a test organization dict.

        Args:
            name: Organization name
            slug: URL slug (auto-generated if not provided)
            plan: Subscription plan tier
            stripe_customer_id: Stripe customer ID

        Returns:
            dict: Organization data ready for model creation
        """
        org_id = uuid4()
        return {
            "id": org_id,
            "name": name,
            "slug": slug or f"test-org-{uuid4().hex[:8]}",
            "plan": plan.value,
            "stripe_customer_id": stripe_customer_id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }


class UserFactory:
    """Factory for creating test users."""

    @staticmethod
    def create(
        email: Optional[str] = None,
        password: str = "TestPassword123!",
        name: str = "Test User",
        role: UserRole = UserRole.MEMBER,
        organization_id: Optional[str] = None,
        is_active: bool = True,
    ) -> tuple[dict, str]:
        """
        Create a test user dict.

        Args:
            email: User email (auto-generated if not provided)
            password: Plain text password (returned separately)
            name: User display name
            role: User role in organization
            organization_id: Associated organization ID
            is_active: Whether user account is active

        Returns:
            Tuple of (user_dict, plain_password) for testing login
        """
        user_id = uuid4()
        return {
            "id": user_id,
            "email": email or f"test-{uuid4().hex[:8]}@example.com",
            "password_hash": f"hashed_{password}",  # Placeholder, real impl uses bcrypt
            "name": name,
            "role": role.value,
            "organization_id": organization_id,
            "is_active": is_active,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }, password

    @staticmethod
    def create_with_org(
        email: Optional[str] = None,
        password: str = "TestPassword123!",
        name: str = "Test User",
        role: UserRole = UserRole.OWNER,
        org_name: str = "Test Organization",
        plan: PlanTier = PlanTier.FREE,
    ) -> tuple[dict, dict, str]:
        """
        Create a test user with their organization.

        Args:
            email: User email
            password: Plain text password
            name: User display name
            role: User role
            org_name: Organization name
            plan: Organization plan tier

        Returns:
            Tuple of (user_dict, organization_dict, plain_password)
        """
        org = OrganizationFactory.create(name=org_name, plan=plan)
        user, plain_password = UserFactory.create(
            email=email,
            password=password,
            name=name,
            role=role,
            organization_id=org["id"],
        )
        return user, org, plain_password
