"""Mock Stripe API for testing."""

from unittest.mock import MagicMock
from datetime import datetime, timezone
from typing import Optional


class MockStripeCheckoutSession:
    """Mock Stripe checkout session."""

    def __init__(
        self,
        session_id: str = "cs_test_123",
        customer: str = "cus_test_123",
        subscription: str = "sub_test_123",
        payment_status: str = "paid",
    ):
        self.id = session_id
        self.url = f"https://checkout.stripe.com/pay/{session_id}"
        self.customer = customer
        self.subscription = subscription
        self.payment_status = payment_status
        self.metadata = {}


class MockStripeSubscription:
    """Mock Stripe subscription."""

    def __init__(
        self,
        subscription_id: str = "sub_test_123",
        status: str = "active",
        customer: str = "cus_test_123",
        price_id: str = "price_test_pro_monthly",
    ):
        self.id = subscription_id
        self.status = status
        self.customer = customer
        self.current_period_start = int(datetime.now(timezone.utc).timestamp())
        self.current_period_end = int(
            datetime.now(timezone.utc).timestamp() + 30 * 24 * 3600
        )
        self.cancel_at = None
        self.cancel_at_period_end = False
        self.items = MagicMock()
        self.items.data = [MagicMock(price=MagicMock(id=price_id))]


class MockStripeCustomer:
    """Mock Stripe customer."""

    def __init__(
        self,
        customer_id: str = "cus_test_123",
        email: str = "test@example.com",
    ):
        self.id = customer_id
        self.email = email
        self.name = "Test Customer"


class MockStripeInvoice:
    """Mock Stripe invoice."""

    def __init__(
        self,
        invoice_id: str = "in_test_123",
        customer: str = "cus_test_123",
        subscription: str = "sub_test_123",
        amount_paid: int = 2900,
        status: str = "paid",
    ):
        self.id = invoice_id
        self.customer = customer
        self.subscription = subscription
        self.amount_paid = amount_paid
        self.status = status
        self.currency = "usd"
        self.hosted_invoice_url = f"https://invoice.stripe.com/{invoice_id}"
        self.invoice_pdf = f"https://invoice.stripe.com/{invoice_id}/pdf"
        self.period_start = int(datetime.now(timezone.utc).timestamp())
        self.period_end = int(
            datetime.now(timezone.utc).timestamp() + 30 * 24 * 3600
        )


class MockStripeBillingPortalSession:
    """Mock Stripe billing portal session."""

    def __init__(self, session_id: str = "bps_test_123"):
        self.id = session_id
        self.url = f"https://billing.stripe.com/session/{session_id}"


def create_stripe_mock():
    """
    Create a mock stripe module for testing.

    Returns:
        MagicMock: Mock stripe module with common methods mocked
    """
    mock_stripe = MagicMock()

    # Mock checkout session creation
    mock_stripe.checkout.Session.create = MagicMock(
        return_value=MockStripeCheckoutSession()
    )

    # Mock customer operations
    mock_stripe.Customer.create = MagicMock(
        return_value=MockStripeCustomer()
    )
    mock_stripe.Customer.retrieve = MagicMock(
        return_value=MockStripeCustomer()
    )

    # Mock subscription operations
    mock_stripe.Subscription.retrieve = MagicMock(
        return_value=MockStripeSubscription()
    )
    mock_stripe.Subscription.modify = MagicMock(
        return_value=MockStripeSubscription()
    )

    # Mock billing portal
    mock_stripe.billing_portal.Session.create = MagicMock(
        return_value=MockStripeBillingPortalSession()
    )

    # Mock webhook signature verification
    def mock_construct_event(payload, sig, secret):
        """Mock webhook event construction."""
        return {
            "type": "checkout.session.completed",
            "data": {"object": MockStripeCheckoutSession().__dict__},
        }

    mock_stripe.Webhook.construct_event = MagicMock(
        side_effect=mock_construct_event
    )

    # Mock error classes
    mock_stripe.error = MagicMock()
    mock_stripe.error.SignatureVerificationError = Exception
    mock_stripe.error.CardError = Exception
    mock_stripe.error.InvalidRequestError = Exception

    return mock_stripe


def create_webhook_event(
    event_type: str,
    data: Optional[dict] = None,
) -> dict:
    """
    Create a mock Stripe webhook event.

    Args:
        event_type: Stripe event type (e.g., "checkout.session.completed")
        data: Event data object

    Returns:
        dict: Mock webhook event
    """
    if data is None:
        if event_type == "checkout.session.completed":
            data = MockStripeCheckoutSession().__dict__
        elif event_type == "customer.subscription.updated":
            data = MockStripeSubscription().__dict__
        elif event_type == "customer.subscription.deleted":
            data = MockStripeSubscription(status="canceled").__dict__
        elif event_type == "invoice.paid":
            data = MockStripeInvoice().__dict__
        elif event_type == "invoice.payment_failed":
            data = MockStripeInvoice(status="open").__dict__
        else:
            data = {}

    return {
        "id": f"evt_test_{event_type.replace('.', '_')}",
        "type": event_type,
        "data": {"object": data},
        "created": int(datetime.now(timezone.utc).timestamp()),
    }
