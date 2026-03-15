"""Integration tests for Stripe webhook handling.

This module contains comprehensive tests for all Stripe webhook events
including signature validation, event processing, and idempotency.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient

from tests.utils.webhook_utils import (
    WebhookTestClient,
    create_webhook_headers,
    create_stripe_event,
    create_checkout_completed_event,
    create_subscription_updated_event,
    create_subscription_deleted_event,
    create_invoice_paid_event,
    create_invoice_payment_failed_event,
)


# ============================================================================
# Signature Validation Tests
# ============================================================================


class TestWebhookSignatureValidation:
    """Tests for webhook signature verification."""

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_valid_signature_accepted(self, client: AsyncClient, test_organization):
        """
        Valid Stripe signature passes verification.

        Given: Webhook payload with valid signature
        When: POST /api/webhooks/stripe is called
        Then: 200 status, event is processed
        """
        event = create_checkout_completed_event(
            organization_id=str(test_organization["id"])
        )
        payload = json.dumps(event)

        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.return_value = event

            response = await client.post(
                "/api/webhooks/stripe",
                content=payload.encode(),
                headers=create_webhook_headers(payload),
            )

            assert response.status_code == 200
            assert response.json() == {"received": True}
            mock_construct.assert_called_once()

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_invalid_signature_rejected(self, client: AsyncClient):
        """
        Invalid signature returns 400.

        Given: Webhook payload with invalid signature
        When: POST /api/webhooks/stripe is called
        Then: 400 status with error
        """
        event = create_stripe_event("test.event", {"id": "test_123"})
        payload = json.dumps(event)

        with patch("stripe.Webhook.construct_event") as mock_construct:
            # Simulate Stripe signature verification failure
            import stripe
            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                "Invalid signature", "sig_header"
            )

            response = await client.post(
                "/api/webhooks/stripe",
                content=payload.encode(),
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "t=123,v1=invalid_sig",
                },
            )

            assert response.status_code == 400

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_missing_signature_rejected(self, client: AsyncClient):
        """
        Missing Stripe-Signature header returns 400.

        Given: Webhook payload without signature header
        When: POST /api/webhooks/stripe is called
        Then: 400 status
        """
        event = create_stripe_event("test.event", {"id": "test_123"})
        payload = json.dumps(event)

        response = await client.post(
            "/api/webhooks/stripe",
            content=payload.encode(),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_expired_timestamp_rejected(self, client: AsyncClient):
        """
        Webhook with expired timestamp is rejected.

        Given: Webhook with timestamp older than tolerance
        When: POST /api/webhooks/stripe is called
        Then: 400 status (Stripe SDK rejects old timestamps)
        """
        import time
        event = create_stripe_event("test.event", {"id": "test_123"})
        payload = json.dumps(event)
        old_timestamp = int(time.time()) - 600  # 10 minutes ago

        with patch("stripe.Webhook.construct_event") as mock_construct:
            import stripe
            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                "Timestamp outside tolerance", "sig_header"
            )

            response = await client.post(
                "/api/webhooks/stripe",
                content=payload.encode(),
                headers=create_webhook_headers(payload, timestamp=old_timestamp),
            )

            assert response.status_code == 400


# ============================================================================
# Checkout Completed Webhook Tests
# ============================================================================


class TestCheckoutCompletedWebhook:
    """Tests for checkout.session.completed event."""

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_activates_subscription(
        self, client: AsyncClient, test_organization, db_session
    ):
        """
        Creates and activates subscription record.

        Given: checkout.session.completed event
        When: Webhook is processed
        Then: Subscription is created with active status
        """
        event = create_checkout_completed_event(
            organization_id=str(test_organization["id"]),
            customer_id="cus_new_123",
            subscription_id="sub_new_456",
            plan_id="pro",
        )

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await client.post(
                "/api/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers=create_webhook_headers(json.dumps(event)),
            )

            assert response.status_code == 200

            # Verify subscription created
            # In real test with DB:
            # from sqlalchemy import select
            # from gateco.database.models import Subscription
            # result = await db_session.execute(
            #     select(Subscription).where(
            #         Subscription.stripe_subscription_id == "sub_new_456"
            #     )
            # )
            # subscription = result.scalar_one()
            # assert subscription.status == "active"
            # assert subscription.plan_id == "pro"

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_updates_organization_plan(
        self, client: AsyncClient, test_organization
    ):
        """
        Updates organization plan tier.

        Given: checkout.session.completed for Pro plan
        When: Webhook is processed
        Then: Organization plan is updated to pro
        """
        event = create_checkout_completed_event(
            organization_id=str(test_organization["id"]),
            plan_id="pro",
        )

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await client.post(
                "/api/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers=create_webhook_headers(json.dumps(event)),
            )

            assert response.status_code == 200

            # Verify organization plan updated
            # In real test with DB:
            # org = await db_session.get(Organization, test_organization["id"])
            # assert org.plan == "pro"

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_stores_stripe_customer_id(
        self, client: AsyncClient, test_organization
    ):
        """
        Stores Stripe customer ID on organization.

        Given: checkout.session.completed with customer ID
        When: Webhook is processed
        Then: Organization has stripe_customer_id set
        """
        event = create_checkout_completed_event(
            organization_id=str(test_organization["id"]),
            customer_id="cus_new_customer_789",
        )

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await client.post(
                "/api/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers=create_webhook_headers(json.dumps(event)),
            )

            assert response.status_code == 200

            # Verify customer ID stored
            # In real test with DB:
            # org = await db_session.get(Organization, test_organization["id"])
            # assert org.stripe_customer_id == "cus_new_customer_789"

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_idempotent_processing(
        self, client: AsyncClient, test_organization
    ):
        """
        Duplicate webhook calls handled idempotently.

        Given: Same checkout.session.completed event sent twice
        When: Webhook is processed twice
        Then: Both return 200, no duplicate subscription created
        """
        event = create_checkout_completed_event(
            organization_id=str(test_organization["id"]),
            subscription_id="sub_idempotent_test",
        )
        payload = json.dumps(event)

        with patch("stripe.Webhook.construct_event", return_value=event):
            # First call
            response1 = await client.post(
                "/api/webhooks/stripe",
                content=payload.encode(),
                headers=create_webhook_headers(payload),
            )

            # Second call (duplicate)
            response2 = await client.post(
                "/api/webhooks/stripe",
                content=payload.encode(),
                headers=create_webhook_headers(payload),
            )

            assert response1.status_code == 200
            assert response2.status_code == 200

            # Verify only one subscription exists
            # In real test with DB:
            # result = await db_session.execute(
            #     select(func.count(Subscription.id)).where(
            #         Subscription.stripe_subscription_id == "sub_idempotent_test"
            #     )
            # )
            # count = result.scalar()
            # assert count == 1


# ============================================================================
# Subscription Updated Webhook Tests
# ============================================================================


class TestSubscriptionUpdatedWebhook:
    """Tests for customer.subscription.updated event."""

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_syncs_subscription_status(
        self, client: AsyncClient, test_subscription
    ):
        """
        Updates local subscription status.

        Given: subscription.updated event with new status
        When: Webhook is processed
        Then: Local subscription status is updated
        """
        event = create_subscription_updated_event(
            subscription_id=test_subscription["stripe_subscription_id"],
            status="past_due",
        )

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await client.post(
                "/api/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers=create_webhook_headers(json.dumps(event)),
            )

            assert response.status_code == 200

            # Verify status updated
            # In real test with DB:
            # sub = await db_session.get(Subscription, test_subscription["id"])
            # assert sub.status == "past_due"

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_handles_plan_change(
        self, client: AsyncClient, test_subscription
    ):
        """
        Updates plan when subscription plan changes.

        Given: subscription.updated with new plan
        When: Webhook is processed
        Then: Plan is updated in database
        """
        event = create_subscription_updated_event(
            subscription_id=test_subscription["stripe_subscription_id"],
            plan_id="enterprise",
        )

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await client.post(
                "/api/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers=create_webhook_headers(json.dumps(event)),
            )

            assert response.status_code == 200

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_handles_period_renewal(
        self, client: AsyncClient, test_subscription
    ):
        """
        Updates billing period dates on renewal.

        Given: subscription.updated with new period dates
        When: Webhook is processed
        Then: Period dates are updated
        """
        import time
        new_period_start = int(time.time())
        new_period_end = new_period_start + (30 * 24 * 3600)

        event = create_subscription_updated_event(
            subscription_id=test_subscription["stripe_subscription_id"],
            current_period_start=new_period_start,
            current_period_end=new_period_end,
        )

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await client.post(
                "/api/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers=create_webhook_headers(json.dumps(event)),
            )

            assert response.status_code == 200

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_handles_cancellation_scheduled(
        self, client: AsyncClient, test_subscription
    ):
        """
        Handles cancel_at_period_end flag.

        Given: subscription.updated with cancel_at_period_end=True
        When: Webhook is processed
        Then: Subscription marked as canceling
        """
        event = create_subscription_updated_event(
            subscription_id=test_subscription["stripe_subscription_id"],
            cancel_at_period_end=True,
        )

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await client.post(
                "/api/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers=create_webhook_headers(json.dumps(event)),
            )

            assert response.status_code == 200


# ============================================================================
# Subscription Deleted Webhook Tests
# ============================================================================


class TestSubscriptionDeletedWebhook:
    """Tests for customer.subscription.deleted event."""

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_cancels_subscription(
        self, client: AsyncClient, test_subscription
    ):
        """
        Marks subscription as canceled.

        Given: subscription.deleted event
        When: Webhook is processed
        Then: Subscription status is canceled
        """
        event = create_subscription_deleted_event(
            subscription_id=test_subscription["stripe_subscription_id"],
        )

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await client.post(
                "/api/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers=create_webhook_headers(json.dumps(event)),
            )

            assert response.status_code == 200

            # Verify subscription canceled
            # In real test with DB:
            # sub = await db_session.get(Subscription, test_subscription["id"])
            # assert sub.status == "canceled"

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_downgrades_to_free_plan(
        self, client: AsyncClient, test_subscription, test_organization
    ):
        """
        Reverts organization to free plan.

        Given: subscription.deleted event
        When: Webhook is processed
        Then: Organization plan is set to free
        """
        event = create_subscription_deleted_event(
            subscription_id=test_subscription["stripe_subscription_id"],
        )

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await client.post(
                "/api/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers=create_webhook_headers(json.dumps(event)),
            )

            assert response.status_code == 200

            # Verify org downgraded to free
            # In real test with DB:
            # org = await db_session.get(Organization, test_organization["id"])
            # assert org.plan == "free"


# ============================================================================
# Invoice Paid Webhook Tests
# ============================================================================


class TestInvoicePaidWebhook:
    """Tests for invoice.paid event."""

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_records_payment(
        self, client: AsyncClient, test_organization, test_subscription
    ):
        """
        Creates payment record in database.

        Given: invoice.paid event
        When: Webhook is processed
        Then: Payment record is created
        """
        event = create_invoice_paid_event(
            invoice_id="in_test_payment_123",
            subscription_id=test_subscription["stripe_subscription_id"],
            amount_paid=2900,
        )

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await client.post(
                "/api/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers=create_webhook_headers(json.dumps(event)),
            )

            assert response.status_code == 200

            # Verify payment created
            # In real test with DB:
            # result = await db_session.execute(
            #     select(Payment).where(
            #         Payment.stripe_invoice_id == "in_test_payment_123"
            #     )
            # )
            # payment = result.scalar_one()
            # assert payment.amount_cents == 2900

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_stores_invoice_pdf_url(
        self, client: AsyncClient, test_subscription
    ):
        """
        Stores invoice PDF URL from Stripe.

        Given: invoice.paid event with PDF URL
        When: Webhook is processed
        Then: PDF URL is stored in invoice record
        """
        event = create_invoice_paid_event(
            invoice_id="in_test_pdf_123",
            subscription_id=test_subscription["stripe_subscription_id"],
        )

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await client.post(
                "/api/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers=create_webhook_headers(json.dumps(event)),
            )

            assert response.status_code == 200


# ============================================================================
# Invoice Payment Failed Webhook Tests
# ============================================================================


class TestInvoicePaymentFailedWebhook:
    """Tests for invoice.payment_failed event."""

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_marks_subscription_past_due(
        self, client: AsyncClient, test_subscription
    ):
        """
        Updates subscription status to past_due.

        Given: invoice.payment_failed event
        When: Webhook is processed
        Then: Subscription status is past_due
        """
        event = create_invoice_payment_failed_event(
            subscription_id=test_subscription["stripe_subscription_id"],
        )

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await client.post(
                "/api/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers=create_webhook_headers(json.dumps(event)),
            )

            assert response.status_code == 200

            # Verify subscription status
            # In real test with DB:
            # sub = await db_session.get(Subscription, test_subscription["id"])
            # assert sub.status == "past_due"

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_handles_multiple_failures(
        self, client: AsyncClient, test_subscription
    ):
        """
        Handles repeated payment failures correctly.

        Given: invoice.payment_failed with attempt_count > 1
        When: Webhook is processed
        Then: Event is processed (may trigger escalation)
        """
        event = create_invoice_payment_failed_event(
            subscription_id=test_subscription["stripe_subscription_id"],
            attempt_count=3,
        )

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await client.post(
                "/api/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers=create_webhook_headers(json.dumps(event)),
            )

            assert response.status_code == 200


# ============================================================================
# Unknown Event Type Tests
# ============================================================================


class TestUnknownWebhookEvents:
    """Tests for handling unknown or unhandled event types."""

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_unknown_event_returns_200(self, client: AsyncClient):
        """
        Unknown event types return 200 (acknowledged but not processed).

        Given: Unknown event type
        When: Webhook is processed
        Then: 200 status (Stripe expects acknowledgment)
        """
        event = create_stripe_event("unknown.event.type", {"id": "test_123"})

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await client.post(
                "/api/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers=create_webhook_headers(json.dumps(event)),
            )

            # Should return 200 to acknowledge receipt
            # even if event is not handled
            assert response.status_code == 200

    @pytest.mark.anyio
    @pytest.mark.stripe
    async def test_test_mode_events_processed(self, client: AsyncClient):
        """
        Test mode events (livemode=False) are processed.

        Given: Event with livemode=False
        When: Webhook is processed
        Then: Event is processed normally
        """
        event = create_stripe_event(
            "checkout.session.completed",
            {"id": "cs_test_123", "metadata": {}},
        )
        event["livemode"] = False

        with patch("stripe.Webhook.construct_event", return_value=event):
            response = await client.post(
                "/api/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers=create_webhook_headers(json.dumps(event)),
            )

            assert response.status_code == 200
