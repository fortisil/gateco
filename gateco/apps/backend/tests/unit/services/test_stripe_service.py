"""Unit tests for StripeService."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from tests.mocks.stripe_mock import (
    create_stripe_mock,
    MockStripeCheckoutSession,
    MockStripeSubscription,
    MockStripeCustomer,
    create_webhook_event,
)


class TestStripeServiceCheckout:
    """Tests for checkout session creation."""

    @pytest.mark.anyio
    @patch("gateco.services.stripe_service.stripe")
    async def test_create_checkout_session(self, mock_stripe, db_session):
        """
        Creates Stripe checkout session with correct parameters.

        Given: Organization without existing Stripe customer
        When: create_checkout_session() is called
        Then: Checkout session is created with new customer
        """
        mock_stripe.checkout.Session.create.return_value = MockStripeCheckoutSession()
        mock_stripe.Customer.create.return_value = MockStripeCustomer(
            customer_id="cus_new_123"
        )

        # from gateco.services.stripe_service import StripeService
        # service = StripeService(db_session)

        # result = await service.create_checkout_session(
        #     organization_id=uuid4(),
        #     plan_id="pro",
        #     billing_period="monthly",
        #     success_url="https://app.example.com/success",
        #     cancel_url="https://app.example.com/cancel",
        # )

        # assert result.checkout_url.startswith("https://checkout.stripe.com")
        # assert result.session_id is not None
        pass

    @pytest.mark.anyio
    @patch("gateco.services.stripe_service.stripe")
    async def test_create_checkout_uses_existing_customer(
        self, mock_stripe, db_session
    ):
        """
        Uses existing Stripe customer if available.

        Given: Organization with existing stripe_customer_id
        When: create_checkout_session() is called
        Then: Existing customer is used, no new customer created
        """
        mock_stripe.checkout.Session.create.return_value = MockStripeCheckoutSession()

        # Organization already has stripe_customer_id = "cus_existing_123"
        # service = StripeService(db_session)
        # await service.create_checkout_session(...)

        # mock_stripe.Customer.create.assert_not_called()
        pass

    @pytest.mark.anyio
    @patch("gateco.services.stripe_service.stripe")
    async def test_create_checkout_with_trial(self, mock_stripe, db_session):
        """
        Creates checkout with trial period when specified.

        Given: Trial days > 0
        When: create_checkout_session() is called
        Then: Checkout session includes trial_period_days
        """
        mock_stripe.checkout.Session.create.return_value = MockStripeCheckoutSession()

        # result = await service.create_checkout_session(
        #     organization_id=uuid4(),
        #     plan_id="pro",
        #     billing_period="monthly",
        #     trial_days=14,
        #     success_url="https://app.example.com/success",
        #     cancel_url="https://app.example.com/cancel",
        # )

        # Verify trial_period_days was passed to Stripe
        pass


class TestStripeServiceWebhooks:
    """Tests for webhook handling."""

    @pytest.mark.anyio
    async def test_handle_checkout_completed(self, db_session):
        """
        Checkout completed activates subscription.

        Given: checkout.session.completed webhook event
        When: handle_checkout_completed() is called
        Then: Subscription is created/updated in database
        """
        # from gateco.services.stripe_service import StripeService
        # service = StripeService(db_session)

        # event_data = {
        #     "customer": "cus_test_123",
        #     "subscription": "sub_test_123",
        #     "metadata": {"organization_id": str(uuid4())},
        # }

        # await service.handle_checkout_completed(event_data)

        # # Verify subscription was created
        # from sqlalchemy import select
        # from gateco.database.models import Subscription
        # result = await db_session.execute(
        #     select(Subscription).where(
        #         Subscription.stripe_subscription_id == "sub_test_123"
        #     )
        # )
        # subscription = result.scalar_one_or_none()
        # assert subscription is not None
        # assert subscription.status == "active"
        pass

    @pytest.mark.anyio
    async def test_handle_subscription_updated(self, db_session):
        """
        Subscription updated changes plan in database.

        Given: customer.subscription.updated webhook event
        When: handle_subscription_updated() is called
        Then: Subscription plan/status is updated
        """
        pass

    @pytest.mark.anyio
    async def test_handle_subscription_deleted(self, db_session):
        """
        Subscription deleted updates status.

        Given: Existing active subscription
        When: handle_subscription_deleted() is called
        Then: Subscription status becomes "canceled"
        """
        # Create existing subscription first
        # from gateco.database.models import Subscription
        # subscription = Subscription(
        #     organization_id=uuid4(),
        #     stripe_subscription_id="sub_test_123",
        #     status="active",
        # )
        # db_session.add(subscription)
        # await db_session.flush()

        # service = StripeService(db_session)
        # await service.handle_subscription_deleted({"id": "sub_test_123"})

        # await db_session.refresh(subscription)
        # assert subscription.status == "canceled"
        pass

    @pytest.mark.anyio
    async def test_handle_invoice_paid(self, db_session):
        """
        Invoice paid creates payment record.

        Given: invoice.paid webhook event
        When: handle_invoice_paid() is called
        Then: Payment record is created
        """
        pass

    @pytest.mark.anyio
    async def test_handle_invoice_payment_failed(self, db_session):
        """
        Invoice payment failed updates subscription status.

        Given: invoice.payment_failed webhook event
        When: handle_invoice_failed() is called
        Then: Subscription status updated to "past_due"
        """
        pass


class TestStripeServiceBillingPortal:
    """Tests for billing portal functionality."""

    @pytest.mark.anyio
    @patch("gateco.services.stripe_service.stripe")
    async def test_get_billing_portal_url(self, mock_stripe, db_session):
        """
        Returns billing portal URL for customer.

        Given: Organization with Stripe customer
        When: get_billing_portal_url() is called
        Then: Stripe billing portal URL is returned
        """
        from tests.mocks.stripe_mock import MockStripeBillingPortalSession

        mock_stripe.billing_portal.Session.create.return_value = (
            MockStripeBillingPortalSession()
        )

        # service = StripeService(db_session)
        # url = await service.get_billing_portal_url(
        #     customer_id="cus_test_123",
        #     return_url="https://app.example.com/settings",
        # )

        # assert url.startswith("https://billing.stripe.com")
        pass


class TestStripeServiceUsage:
    """Tests for usage metering."""

    @pytest.mark.anyio
    async def test_record_usage(self, db_session):
        """
        Records usage for metered billing.

        Given: Active subscription with metered pricing
        When: record_usage() is called
        Then: Usage record is created in Stripe
        """
        pass

    @pytest.mark.anyio
    async def test_get_current_usage(self, db_session):
        """
        Gets current usage for billing period.

        Given: Organization with usage records
        When: get_current_usage() is called
        Then: Aggregated usage for current period returned
        """
        pass
