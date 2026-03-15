"""
Stripe test fixtures.

Provides fixtures for testing Stripe integration including checkout sessions,
subscriptions, webhooks, and billing operations.
"""

import pytest
from typing import Optional
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from tests.mocks.stripe_mock import (
    create_stripe_mock,
    MockStripeCheckoutSession,
    MockStripeSubscription,
    MockStripeCustomer,
    MockStripeInvoice,
    MockStripeBillingPortalSession,
    create_webhook_event,
)
from tests.factories.subscription_factory import (
    SubscriptionFactory,
    PaymentFactory,
    InvoiceFactory,
    UsageLogFactory,
    SubscriptionStatus,
)


@pytest.fixture
def stripe_mock():
    """
    Create a fully mocked Stripe module.

    Returns:
        MagicMock: Mock stripe module with all common methods mocked
    """
    return create_stripe_mock()


@pytest.fixture
def mock_checkout_session():
    """
    Create a mock Stripe checkout session.

    Returns:
        MockStripeCheckoutSession: Mock checkout session
    """
    return MockStripeCheckoutSession()


@pytest.fixture
def mock_subscription():
    """
    Create a mock Stripe subscription.

    Returns:
        MockStripeSubscription: Mock subscription
    """
    return MockStripeSubscription()


@pytest.fixture
def mock_customer():
    """
    Create a mock Stripe customer.

    Returns:
        MockStripeCustomer: Mock customer
    """
    return MockStripeCustomer()


@pytest.fixture
def mock_invoice():
    """
    Create a mock Stripe invoice.

    Returns:
        MockStripeInvoice: Mock invoice
    """
    return MockStripeInvoice()


@pytest.fixture
def mock_billing_portal():
    """
    Create a mock Stripe billing portal session.

    Returns:
        MockStripeBillingPortalSession: Mock portal session
    """
    return MockStripeBillingPortalSession()


# ============================================================================
# Webhook Event Fixtures
# ============================================================================

@pytest.fixture
def checkout_completed_event(test_organization: dict):
    """
    Create a checkout.session.completed webhook event.

    Args:
        test_organization: Test organization fixture

    Returns:
        dict: Webhook event payload
    """
    return create_webhook_event(
        "checkout.session.completed",
        {
            "id": "cs_test_123",
            "customer": "cus_test_123",
            "subscription": "sub_test_123",
            "payment_status": "paid",
            "metadata": {
                "organization_id": str(test_organization["id"]),
                "plan_id": "pro",
                "billing_period": "monthly",
            },
        },
    )


@pytest.fixture
def subscription_updated_event():
    """
    Create a customer.subscription.updated webhook event.

    Returns:
        dict: Webhook event payload
    """
    return create_webhook_event("customer.subscription.updated")


@pytest.fixture
def subscription_deleted_event():
    """
    Create a customer.subscription.deleted webhook event.

    Returns:
        dict: Webhook event payload
    """
    return create_webhook_event("customer.subscription.deleted")


@pytest.fixture
def invoice_paid_event():
    """
    Create an invoice.paid webhook event.

    Returns:
        dict: Webhook event payload
    """
    return create_webhook_event("invoice.paid")


@pytest.fixture
def invoice_payment_failed_event():
    """
    Create an invoice.payment_failed webhook event.

    Returns:
        dict: Webhook event payload
    """
    return create_webhook_event("invoice.payment_failed")


# ============================================================================
# Database Subscription Fixtures
# ============================================================================

@pytest.fixture
async def test_subscription(db_session, test_organization: dict) -> dict:
    """
    Create a test subscription in the database.

    Returns:
        dict: Subscription data
    """
    subscription = SubscriptionFactory.create_active(
        organization_id=test_organization["id"],
        plan_id="pro",
    )
    # In real implementation:
    # from src.gateco.database.models import Subscription
    # sub_model = Subscription(**subscription)
    # db_session.add(sub_model)
    # await db_session.flush()
    return subscription


@pytest.fixture
async def test_subscription_canceled(db_session, test_organization: dict) -> dict:
    """
    Create a canceled test subscription.

    Returns:
        dict: Canceled subscription data
    """
    subscription = SubscriptionFactory.create_canceled(
        organization_id=test_organization["id"],
        plan_id="pro",
    )
    return subscription


@pytest.fixture
async def test_subscription_past_due(db_session, test_organization: dict) -> dict:
    """
    Create a past-due test subscription.

    Returns:
        dict: Past-due subscription data
    """
    subscription = SubscriptionFactory.create_past_due(
        organization_id=test_organization["id"],
        plan_id="pro",
    )
    return subscription


@pytest.fixture
async def test_payment(db_session, test_organization: dict) -> dict:
    """
    Create a test payment record.

    Returns:
        dict: Payment data
    """
    payment = PaymentFactory.create(
        organization_id=test_organization["id"],
        amount_cents=999,
    )
    return payment


@pytest.fixture
async def test_invoice(db_session, test_organization: dict, test_subscription: dict) -> dict:
    """
    Create a test invoice record.

    Returns:
        dict: Invoice data
    """
    invoice = InvoiceFactory.create(
        organization_id=test_organization["id"],
        subscription_id=test_subscription["id"],
        amount_cents=2900,
    )
    return invoice


@pytest.fixture
async def test_usage(db_session, test_organization: dict) -> dict:
    """
    Create a test usage log record.

    Returns:
        dict: Usage log data
    """
    usage = UsageLogFactory.create(
        organization_id=test_organization["id"],
        retrievals=50,
        overage=0,
    )
    return usage


@pytest.fixture
async def test_usage_over_limit(db_session, test_organization: dict) -> dict:
    """
    Create a test usage log with overage.

    Returns:
        dict: Usage log data with overage
    """
    usage = UsageLogFactory.create(
        organization_id=test_organization["id"],
        retrievals=150,  # Over free tier limit of 100
        overage=50,
    )
    return usage


# ============================================================================
# Stripe API Response Fixtures
# ============================================================================

@pytest.fixture
def stripe_checkout_response():
    """
    Mock response for Stripe checkout session creation.

    Returns:
        dict: Expected checkout response
    """
    return {
        "checkout_url": "https://checkout.stripe.com/pay/cs_test_123",
        "session_id": "cs_test_123",
    }


@pytest.fixture
def stripe_portal_response():
    """
    Mock response for Stripe billing portal.

    Returns:
        dict: Expected portal response
    """
    return {
        "portal_url": "https://billing.stripe.com/session/bps_test_123",
    }


# ============================================================================
# Plan Fixtures
# ============================================================================

@pytest.fixture
def plans_data():
    """
    Test data for subscription plans.

    Returns:
        list: List of plan configurations
    """
    return [
        {
            "id": "free",
            "name": "Free",
            "tier": "free",
            "price_monthly_cents": 0,
            "price_yearly_cents": 0,
            "features": {
                "custom_branding": False,
                "custom_domain": False,
                "analytics": False,
                "api_access": False,
                "priority_support": False,
            },
            "limits": {
                "resources": 3,
                "secured_retrievals": 100,
                "team_members": 1,
                "overage_price_cents": 0,
            },
        },
        {
            "id": "pro",
            "name": "Pro",
            "tier": "pro",
            "price_monthly_cents": 2900,
            "price_yearly_cents": 29000,
            "stripe_price_monthly": "price_pro_monthly",
            "stripe_price_yearly": "price_pro_yearly",
            "features": {
                "custom_branding": True,
                "custom_domain": True,
                "analytics": True,
                "api_access": True,
                "priority_support": False,
            },
            "limits": {
                "resources": None,  # Unlimited
                "secured_retrievals": 10000,
                "team_members": 5,
                "overage_price_cents": 500,  # $5 per 1000
            },
        },
        {
            "id": "enterprise",
            "name": "Enterprise",
            "tier": "enterprise",
            "price_monthly_cents": 9900,
            "price_yearly_cents": 99000,
            "stripe_price_monthly": "price_enterprise_monthly",
            "stripe_price_yearly": "price_enterprise_yearly",
            "features": {
                "custom_branding": True,
                "custom_domain": True,
                "analytics": True,
                "api_access": True,
                "priority_support": True,
            },
            "limits": {
                "resources": None,  # Unlimited
                "secured_retrievals": None,  # Unlimited
                "team_members": None,  # Unlimited
                "overage_price_cents": 0,
            },
        },
    ]


# ============================================================================
# Context Manager for Stripe Mocking
# ============================================================================

class StripeTestContext:
    """
    Context manager for Stripe API mocking in tests.

    Usage:
        with StripeTestContext() as stripe:
            stripe.checkout.Session.create.return_value = MockStripeCheckoutSession()
            # ... test code ...
    """

    def __init__(self):
        self.mock = create_stripe_mock()
        self._patcher = None

    def __enter__(self):
        self._patcher = patch("stripe", self.mock)
        self._patcher.start()
        return self.mock

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._patcher:
            self._patcher.stop()
        return False


@pytest.fixture
def stripe_context():
    """
    Fixture providing Stripe mock context manager.

    Usage in tests:
        def test_something(stripe_context):
            with stripe_context as stripe:
                stripe.checkout.Session.create.return_value = ...
    """
    return StripeTestContext()
