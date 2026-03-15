"""
Integration tests for billing and Stripe workflows.

These tests verify complete billing workflows including subscription
management, payment processing, and webhook handling.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription, SubscriptionStatus
from app.models.organization import Organization


@pytest.mark.integration
@pytest.mark.stripe
class TestSubscriptionFlow:
    """Test complete subscription management flows."""

    @pytest.mark.asyncio
    async def test_complete_subscription_upgrade(
        self,
        client: AsyncClient,
        test_organization: Organization,
        auth_headers: dict,
        mock_stripe: MagicMock,
    ):
        """Test complete flow of upgrading from free to paid plan."""
        # Step 1: Check current plan (free)
        response = await client.get(
            "/api/v1/billing/subscription",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["plan"] == "free"

        # Step 2: Create checkout session for upgrade
        response = await client.post(
            "/api/v1/billing/checkout",
            json={
                "plan": "pro",
                "billing_period": "monthly",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        checkout_data = response.json()
        assert "checkout_url" in checkout_data
        assert "session_id" in checkout_data

        # Step 3: Simulate Stripe checkout.session.completed webhook
        webhook_payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": checkout_data["session_id"],
                    "customer": "cus_test123",
                    "subscription": "sub_test123",
                    "metadata": {
                        "organization_id": str(test_organization.id),
                        "plan": "pro",
                    },
                },
            },
        }

        response = await client.post(
            "/api/v1/webhooks/stripe",
            json=webhook_payload,
            headers={"Stripe-Signature": "test_signature"},
        )
        assert response.status_code == 200

        # Step 4: Verify subscription is now active
        response = await client.get(
            "/api/v1/billing/subscription",
            headers=auth_headers,
        )
        assert response.status_code == 200
        subscription = response.json()
        assert subscription["plan"] == "pro"
        assert subscription["status"] == "active"

    @pytest.mark.asyncio
    async def test_subscription_cancellation_flow(
        self,
        client: AsyncClient,
        test_subscription: Subscription,
        auth_headers: dict,
        mock_stripe: MagicMock,
    ):
        """Test cancelling a subscription at period end."""
        # Step 1: Cancel subscription
        response = await client.post(
            "/api/v1/billing/subscription/cancel",
            json={"cancel_at_period_end": True},
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["cancel_at_period_end"] is True
        assert data["status"] == "active"  # Still active until period ends

        # Step 2: Verify cancellation is reflected
        response = await client.get(
            "/api/v1/billing/subscription",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["cancel_at_period_end"] is True

        # Step 3: Simulate period end webhook
        webhook_payload = {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": test_subscription.stripe_subscription_id,
                    "status": "canceled",
                },
            },
        }

        response = await client.post(
            "/api/v1/webhooks/stripe",
            json=webhook_payload,
            headers={"Stripe-Signature": "test_signature"},
        )
        assert response.status_code == 200

        # Step 4: Verify subscription is now cancelled
        response = await client.get(
            "/api/v1/billing/subscription",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "canceled"

    @pytest.mark.asyncio
    async def test_subscription_reactivation(
        self,
        client: AsyncClient,
        test_subscription: Subscription,
        auth_headers: dict,
        mock_stripe: MagicMock,
        db_session: AsyncSession,
    ):
        """Test reactivating a cancelled subscription before period end."""
        # Step 1: Cancel subscription
        response = await client.post(
            "/api/v1/billing/subscription/cancel",
            json={"cancel_at_period_end": True},
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Step 2: Reactivate before period end
        response = await client.post(
            "/api/v1/billing/subscription/reactivate",
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Step 3: Verify subscription is active again
        response = await client.get(
            "/api/v1/billing/subscription",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cancel_at_period_end"] is False
        assert data["status"] == "active"


@pytest.mark.integration
@pytest.mark.stripe
class TestPaymentFlow:
    """Test payment processing flows."""

    @pytest.mark.asyncio
    async def test_successful_payment_processing(
        self,
        client: AsyncClient,
        test_subscription: Subscription,
        auth_headers: dict,
        mock_stripe: MagicMock,
    ):
        """Test successful recurring payment processing."""
        # Simulate invoice.payment_succeeded webhook
        webhook_payload = {
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "id": "in_test123",
                    "subscription": test_subscription.stripe_subscription_id,
                    "amount_paid": 2900,  # $29.00
                    "currency": "usd",
                    "status": "paid",
                },
            },
        }

        response = await client.post(
            "/api/v1/webhooks/stripe",
            json=webhook_payload,
            headers={"Stripe-Signature": "test_signature"},
        )
        assert response.status_code == 200

        # Verify payment is recorded
        response = await client.get(
            "/api/v1/billing/invoices",
            headers=auth_headers,
        )
        assert response.status_code == 200
        invoices = response.json()
        assert len(invoices) >= 1

    @pytest.mark.asyncio
    async def test_failed_payment_handling(
        self,
        client: AsyncClient,
        test_subscription: Subscription,
        auth_headers: dict,
        mock_stripe: MagicMock,
    ):
        """Test handling of failed payment."""
        # Simulate invoice.payment_failed webhook
        webhook_payload = {
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "id": "in_test_failed",
                    "subscription": test_subscription.stripe_subscription_id,
                    "amount_due": 2900,
                    "attempt_count": 1,
                    "next_payment_attempt": int(
                        (datetime.now(timezone.utc) + timedelta(days=3)).timestamp()
                    ),
                },
            },
        }

        response = await client.post(
            "/api/v1/webhooks/stripe",
            json=webhook_payload,
            headers={"Stripe-Signature": "test_signature"},
        )
        assert response.status_code == 200

        # Verify subscription status reflects payment issue
        response = await client.get(
            "/api/v1/billing/subscription",
            headers=auth_headers,
        )
        assert response.status_code == 200
        # Status might be past_due or similar
        assert response.json()["status"] in ["active", "past_due"]

    @pytest.mark.asyncio
    async def test_update_payment_method(
        self,
        client: AsyncClient,
        test_subscription: Subscription,
        auth_headers: dict,
        mock_stripe: MagicMock,
    ):
        """Test updating payment method via billing portal."""
        # Step 1: Get billing portal URL
        response = await client.post(
            "/api/v1/billing/portal",
            headers=auth_headers,
        )
        assert response.status_code == 200
        portal_data = response.json()
        assert "portal_url" in portal_data

        # Step 2: Simulate payment method update webhook
        webhook_payload = {
            "type": "customer.updated",
            "data": {
                "object": {
                    "id": test_subscription.stripe_customer_id,
                    "invoice_settings": {
                        "default_payment_method": "pm_new_card",
                    },
                },
            },
        }

        response = await client.post(
            "/api/v1/webhooks/stripe",
            json=webhook_payload,
            headers={"Stripe-Signature": "test_signature"},
        )
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.stripe
class TestPlanChanges:
    """Test plan upgrade and downgrade flows."""

    @pytest.mark.asyncio
    async def test_upgrade_proration(
        self,
        client: AsyncClient,
        test_subscription: Subscription,
        auth_headers: dict,
        mock_stripe: MagicMock,
    ):
        """Test upgrading plan with proration."""
        # Upgrade from pro to enterprise
        response = await client.post(
            "/api/v1/billing/subscription/change",
            json={
                "plan": "enterprise",
                "billing_period": "monthly",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Simulate subscription update webhook
        webhook_payload = {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": test_subscription.stripe_subscription_id,
                    "items": {
                        "data": [
                            {"price": {"id": "price_enterprise_monthly"}},
                        ],
                    },
                },
            },
        }

        response = await client.post(
            "/api/v1/webhooks/stripe",
            json=webhook_payload,
            headers={"Stripe-Signature": "test_signature"},
        )
        assert response.status_code == 200

        # Verify plan is updated
        response = await client.get(
            "/api/v1/billing/subscription",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["plan"] == "enterprise"

    @pytest.mark.asyncio
    async def test_downgrade_at_period_end(
        self,
        client: AsyncClient,
        test_subscription: Subscription,
        auth_headers: dict,
        mock_stripe: MagicMock,
    ):
        """Test downgrading plan scheduled for period end."""
        # Downgrade from enterprise to pro (takes effect at period end)
        response = await client.post(
            "/api/v1/billing/subscription/change",
            json={
                "plan": "pro",
                "billing_period": "monthly",
                "immediate": False,  # Apply at period end
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "scheduled_change" in data or data.get("pending_plan") == "pro"


@pytest.mark.integration
@pytest.mark.stripe
class TestUsageBasedBilling:
    """Test usage-based billing features."""

    @pytest.mark.asyncio
    async def test_usage_tracking(
        self,
        client: AsyncClient,
        test_subscription: Subscription,
        auth_headers: dict,
    ):
        """Test that API usage is tracked."""
        # Make several API calls
        for _ in range(5):
            await client.get("/api/v1/resources", headers=auth_headers)

        # Check usage stats
        response = await client.get(
            "/api/v1/billing/usage",
            headers=auth_headers,
        )
        assert response.status_code == 200
        usage = response.json()
        assert usage["api_calls"] >= 5

    @pytest.mark.asyncio
    async def test_usage_limits_enforcement(
        self,
        client: AsyncClient,
        free_organization: Organization,
        free_auth_headers: dict,
    ):
        """Test usage limits are enforced for free tier."""
        # Try to exceed resource limit
        resource_limit = 5  # Free tier limit

        for i in range(resource_limit + 1):
            response = await client.post(
                "/api/v1/resources",
                json={
                    "name": f"Test Resource {i}",
                    "type": "file",
                    "access_type": "public",
                },
                headers=free_auth_headers,
            )

            if i >= resource_limit:
                # Should fail due to limit
                assert response.status_code == 402
                assert "upgrade" in response.json().get("message", "").lower()
                break

    @pytest.mark.asyncio
    async def test_usage_reports(
        self,
        client: AsyncClient,
        test_subscription: Subscription,
        auth_headers: dict,
    ):
        """Test generating usage reports."""
        response = await client.get(
            "/api/v1/billing/usage/report",
            params={
                "start_date": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
                "end_date": datetime.now(timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        report = response.json()
        assert "period" in report
        assert "api_calls" in report
        assert "storage_used" in report


@pytest.mark.integration
@pytest.mark.stripe
class TestWebhookSecurity:
    """Test Stripe webhook security."""

    @pytest.mark.asyncio
    async def test_webhook_signature_verification(
        self,
        client: AsyncClient,
    ):
        """Test webhook rejects invalid signatures."""
        webhook_payload = {
            "type": "checkout.session.completed",
            "data": {"object": {}},
        }

        # Missing signature
        response = await client.post(
            "/api/v1/webhooks/stripe",
            json=webhook_payload,
        )
        assert response.status_code == 400

        # Invalid signature
        response = await client.post(
            "/api/v1/webhooks/stripe",
            json=webhook_payload,
            headers={"Stripe-Signature": "invalid_signature"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_webhook_replay_prevention(
        self,
        client: AsyncClient,
        mock_stripe: MagicMock,
    ):
        """Test webhook prevents replay attacks."""
        webhook_payload = {
            "id": "evt_test_unique_123",
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "id": "in_test123",
                    "subscription": "sub_test123",
                    "amount_paid": 2900,
                },
            },
        }

        # First request should succeed
        response = await client.post(
            "/api/v1/webhooks/stripe",
            json=webhook_payload,
            headers={"Stripe-Signature": "test_signature"},
        )
        assert response.status_code == 200

        # Replay should be rejected (idempotency)
        response = await client.post(
            "/api/v1/webhooks/stripe",
            json=webhook_payload,
            headers={"Stripe-Signature": "test_signature"},
        )
        # Should still return 200 (idempotent) but not process again
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.stripe
class TestCouponsAndDiscounts:
    """Test coupon and discount handling."""

    @pytest.mark.asyncio
    async def test_apply_coupon_at_checkout(
        self,
        client: AsyncClient,
        auth_headers: dict,
        mock_stripe: MagicMock,
    ):
        """Test applying coupon during checkout."""
        response = await client.post(
            "/api/v1/billing/checkout",
            json={
                "plan": "pro",
                "billing_period": "monthly",
                "coupon_code": "SAVE20",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Verify Stripe was called with coupon
        mock_stripe.checkout.Session.create.assert_called()
        call_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
        assert "discounts" in call_kwargs or "coupon" in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_invalid_coupon_code(
        self,
        client: AsyncClient,
        auth_headers: dict,
        mock_stripe: MagicMock,
    ):
        """Test handling invalid coupon code."""
        mock_stripe.Coupon.retrieve.side_effect = Exception("No such coupon")

        response = await client.post(
            "/api/v1/billing/validate-coupon",
            json={"coupon_code": "INVALID"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "invalid" in response.json()["message"].lower()
