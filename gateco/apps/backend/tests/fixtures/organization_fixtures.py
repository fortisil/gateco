"""
Organization test fixtures.

Provides fixtures for creating test organizations with various
plans, configurations, and states for integration testing.
"""

import pytest
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta

from tests.factories.organization_factory import (
    OrganizationFactory,
    PlanTier,
)


@pytest.fixture
async def free_organization(db_session) -> dict:
    """
    Create an organization on the Free plan.

    Returns:
        dict: Organization data with free plan
    """
    org = OrganizationFactory.create(plan=PlanTier.FREE)
    # In real implementation with models:
    # from src.gateco.database.models import Organization
    # org_model = Organization(**org)
    # db_session.add(org_model)
    # await db_session.flush()
    return org


@pytest.fixture
async def pro_organization_with_customer(db_session) -> dict:
    """
    Create a Pro plan organization with Stripe customer ID.

    Returns:
        dict: Organization data with Pro plan and Stripe customer
    """
    org = OrganizationFactory.create(
        plan=PlanTier.PRO,
        stripe_customer_id=f"cus_pro_{OrganizationFactory._generate_id()[:8]}",
    )
    return org


@pytest.fixture
async def enterprise_organization_with_custom_domain(db_session) -> dict:
    """
    Create an Enterprise organization with custom domain.

    Returns:
        dict: Organization data with Enterprise plan and custom domain
    """
    org = OrganizationFactory.create(
        plan=PlanTier.ENTERPRISE,
        stripe_customer_id=f"cus_ent_{OrganizationFactory._generate_id()[:8]}",
        custom_domain="custom.example.com",
    )
    return org


@pytest.fixture
async def organization_near_limit(db_session) -> dict:
    """
    Create an organization approaching usage limits.

    Returns:
        dict: Organization data with high usage
    """
    org = OrganizationFactory.create(
        plan=PlanTier.FREE,
        current_month_retrievals=95,  # Near 100 limit
    )
    return org


@pytest.fixture
async def organization_over_limit(db_session) -> dict:
    """
    Create an organization that has exceeded limits.

    Returns:
        dict: Organization data with usage over limit
    """
    org = OrganizationFactory.create(
        plan=PlanTier.FREE,
        current_month_retrievals=150,  # Over 100 limit
    )
    return org


@pytest.fixture
async def organization_with_branding(db_session) -> dict:
    """
    Create an organization with custom branding.

    Returns:
        dict: Organization data with branding settings
    """
    org = OrganizationFactory.create(
        plan=PlanTier.PRO,
        branding={
            "primary_color": "#FF5500",
            "logo_url": "https://example.com/logo.png",
            "company_name": "Custom Brand Co",
        },
    )
    return org


@pytest.fixture
async def organization_suspended(db_session) -> dict:
    """
    Create a suspended organization.

    Returns:
        dict: Organization data with suspended status
    """
    org = OrganizationFactory.create(
        plan=PlanTier.PRO,
        status="suspended",
        suspended_at=datetime.now(timezone.utc),
        suspended_reason="payment_failed",
    )
    return org


@pytest.fixture
async def organization_trial(db_session) -> dict:
    """
    Create an organization on trial.

    Returns:
        dict: Organization data with trial status
    """
    org = OrganizationFactory.create(
        plan=PlanTier.PRO,
        status="trial",
        trial_ends_at=datetime.now(timezone.utc) + timedelta(days=14),
    )
    return org


@pytest.fixture
async def organization_trial_expired(db_session) -> dict:
    """
    Create an organization with expired trial.

    Returns:
        dict: Organization data with expired trial
    """
    org = OrganizationFactory.create(
        plan=PlanTier.PRO,
        status="trial_expired",
        trial_ends_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    return org


# ============================================================================
# Multi-Organization Fixtures
# ============================================================================


@pytest.fixture
async def multiple_organizations(db_session) -> list[dict]:
    """
    Create multiple organizations for testing multi-tenancy.

    Returns:
        list[dict]: List of organization data
    """
    orgs = []
    for i in range(5):
        org = OrganizationFactory.create(
            name=f"Organization {i + 1}",
            slug=f"org-{i + 1}",
            plan=PlanTier.FREE if i < 3 else PlanTier.PRO,
        )
        orgs.append(org)
    return orgs


@pytest.fixture
async def organization_hierarchy(db_session) -> dict:
    """
    Create organizations with different plans for entitlement testing.

    Returns:
        dict: Dictionary with free, pro, and enterprise organizations
    """
    free_org = OrganizationFactory.create(
        name="Free Org",
        slug="free-org",
        plan=PlanTier.FREE,
    )
    pro_org = OrganizationFactory.create(
        name="Pro Org",
        slug="pro-org",
        plan=PlanTier.PRO,
        stripe_customer_id="cus_pro_hierarchy",
    )
    enterprise_org = OrganizationFactory.create(
        name="Enterprise Org",
        slug="enterprise-org",
        plan=PlanTier.ENTERPRISE,
        stripe_customer_id="cus_ent_hierarchy",
    )

    return {
        "free": free_org,
        "pro": pro_org,
        "enterprise": enterprise_org,
    }


# ============================================================================
# Isolation Testing Fixtures
# ============================================================================


@pytest.fixture
async def isolated_organizations(db_session) -> tuple[dict, dict]:
    """
    Create two isolated organizations for testing data isolation.

    Returns:
        tuple: Two organization dictionaries
    """
    org_a = OrganizationFactory.create(
        name="Organization A",
        slug="org-a",
        plan=PlanTier.PRO,
    )
    org_b = OrganizationFactory.create(
        name="Organization B",
        slug="org-b",
        plan=PlanTier.PRO,
    )
    return org_a, org_b


# ============================================================================
# Helper Functions
# ============================================================================


async def create_organization_with_users(
    db_session,
    num_users: int = 3,
    plan: PlanTier = PlanTier.FREE,
) -> tuple[dict, list[dict]]:
    """
    Helper to create an organization with multiple users.

    Args:
        db_session: Database session
        num_users: Number of users to create
        plan: Organization plan

    Returns:
        tuple: (organization, list of users)
    """
    from tests.factories.user_factory import UserFactory, UserRole

    org = OrganizationFactory.create(plan=plan)
    users = []

    # First user is always owner
    owner, _ = UserFactory.create(
        organization_id=org["id"],
        role=UserRole.OWNER,
    )
    users.append(owner)

    # Create additional members
    for _ in range(num_users - 1):
        user, _ = UserFactory.create(
            organization_id=org["id"],
            role=UserRole.MEMBER,
        )
        users.append(user)

    return org, users


async def get_organization_entitlements(org: dict) -> dict:
    """
    Get entitlements for an organization based on plan.

    Args:
        org: Organization dictionary

    Returns:
        dict: Entitlements for the organization's plan
    """
    plan = org.get("plan", PlanTier.FREE)

    entitlements = {
        PlanTier.FREE: {
            "resources": 3,
            "secured_retrievals": 100,
            "team_members": 1,
            "custom_branding": False,
            "custom_domain": False,
            "analytics": False,
            "api_access": False,
            "priority_support": False,
        },
        PlanTier.PRO: {
            "resources": None,  # Unlimited
            "secured_retrievals": 10000,
            "team_members": 5,
            "custom_branding": True,
            "custom_domain": True,
            "analytics": True,
            "api_access": True,
            "priority_support": False,
        },
        PlanTier.ENTERPRISE: {
            "resources": None,
            "secured_retrievals": None,
            "team_members": None,
            "custom_branding": True,
            "custom_domain": True,
            "analytics": True,
            "api_access": True,
            "priority_support": True,
        },
    }

    return entitlements.get(plan, entitlements[PlanTier.FREE])
