"""Integration tests for billing routes."""

import pytest
from unittest.mock import patch
from httpx import AsyncClient

from tests.mocks.stripe_mock import (
    MockStripeCheckoutSession,
    create_webhook_event,
)


class TestPlansRoute:
    """Tests for GET /api/plans."""

    @pytest.mark.anyio
    async def test_plans_public_access(self, client: AsyncClient):
        """
        Plans endpoint doesn't require authentication.

        Given: No auth token
        When: GET /api/plans is called
        Then: 200 status with plan list
        """
        response = await client.get("/api/plans")

        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert len(data["plans"]) >= 3  # Free, Pro, Enterprise

    @pytest.mark.anyio
    async def test_plans_returns_pricing(self, client: AsyncClient):
        """
        Plans include pricing information.

        Given: Public request
        When: GET /api/plans is called
        Then: Each plan has pricing details
        """
        response = await client.get("/api/plans")
        data = response.json()

        for plan in data["plans"]:
            assert "id" in plan
            assert "name" in plan
            assert "features" in plan
            if plan["id"] != "free":
                assert "price_monthly" in plan
                assert "price_yearly" in plan


class TestCheckoutRoute:
    """Tests for POST /api/checkout/start."""

    @pytest.mark.anyio
    @patch("gateco.routes.checkout.stripe")
    async def test_checkout_start_success(
        self, mock_stripe, client: AsyncClient, auth_headers: dict
    ):
        """
        Checkout start returns session URL.

        Given: Authenticated user
        When: POST /api/checkout/start is called
        Then: 200 status with checkout URL
        """
        mock_stripe.checkout.Session.create.return_value = MockStripeCheckoutSession()

        response = await client.post(
            "/api/checkout/start",
            headers=auth_headers,
            json={
                "plan_id": "pro",
                "billing_period": "monthly",
                "success_url": "https://app.example.com/success",
                "cancel_url": "https://app.example.com/cancel",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data
        assert "session_id" in data

    @pytest.mark.anyio
    async def test_checkout_requires_auth(self, client: AsyncClient):
        """
        Checkout requires authentication.

        Given: No auth token
        When: POST /api/checkout/start is called
        Then: 401 status
        """
        response = await client.post(
            "/api/checkout/start",
            json={
                "plan_id": "pro",
                "billing_period": "monthly",
                "success_url": "https://app.example.com/success",
                "cancel_url": "https://app.example.com/cancel",
            },
        )

        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_checkout_invalid_plan(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        Invalid plan returns 400.

        Given: Non-existent plan ID
        When: POST /api/checkout/start is called
        Then: 400 status with error
        """
        response = await client.post(
            "/api/checkout/start",
            headers=auth_headers,
            json={
                "plan_id": "invalid_plan",
                "billing_period": "monthly",
                "success_url": "https://app.example.com/success",
                "cancel_url": "https://app.example.com/cancel",
            },
        )

        assert response.status_code == 400


class TestBillingUsageRoute:
    """Tests for GET /api/billing/usage."""

    @pytest.mark.anyio
    async def test_usage_returns_current_month(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        Usage returns current month stats.

        Given: Authenticated user
        When: GET /api/billing/usage is called
        Then: 200 status with usage data
        """
        response = await client.get(
            "/api/billing/usage",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "period_start" in data
        assert "period_end" in data
        assert "secured_retrievals" in data
        assert "used" in data["secured_retrievals"]
        assert "limit" in data["secured_retrievals"]

    @pytest.mark.anyio
    async def test_usage_requires_auth(self, client: AsyncClient):
        """
        Usage endpoint requires authentication.

        Given: No auth token
        When: GET /api/billing/usage is called
        Then: 401 status
        """
        response = await client.get("/api/billing/usage")
        assert response.status_code == 401


class TestInvoicesRoute:
    """Tests for GET /api/billing/invoices."""

    @pytest.mark.anyio
    async def test_invoices_list(
        self, client: AsyncClient, auth_headers: dict
    ):
        """
        Returns list of invoices.

        Given: Authenticated user with subscription
        When: GET /api/billing/invoices is called
        Then: 200 status with invoice list
        """
        response = await client.get(
            "/api/billing/invoices",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "invoices" in data
        assert isinstance(data["invoices"], list)


class TestWebhookRoute:
    """Tests for POST /api/webhooks/stripe."""

    @pytest.mark.anyio
    @patch("gateco.routes.webhooks.stripe")
    async def test_webhook_valid_signature(
        self, mock_stripe, client: AsyncClient, test_organization
    ):
        """
        Valid webhook processes event.

        Given: Valid Stripe signature
        When: POST /api/webhooks/stripe is called
        Then: 200 status with received=True
        """
        mock_stripe.Webhook.construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer": "cus_test_123",
                    "subscription": "sub_test_123",
                    "metadata": {"organization_id": str(test_organization["id"])},
                }
            },
        }

        response = await client.post(
            "/api/webhooks/stripe",
            content=b'{"type": "checkout.session.completed"}',
            headers={
                "Stripe-Signature": "valid_signature",
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200
        assert response.json() == {"received": True}

    @pytest.mark.anyio
    @patch("gateco.routes.webhooks.stripe")
    async def test_webhook_invalid_signature(self, mock_stripe, client: AsyncClient):
        """
        Invalid signature returns 400.

        Given: Invalid Stripe signature
        When: POST /api/webhooks/stripe is called
        Then: 400 status
        """

        class MockSignatureError(Exception):
            pass

        mock_stripe.error.SignatureVerificationError = MockSignatureError
        mock_stripe.Webhook.construct_event.side_effect = MockSignatureError(
            "Invalid signature"
        )

        response = await client.post(
            "/api/webhooks/stripe",
            content=b'{"type": "test"}',
            headers={
                "Stripe-Signature": "invalid_signature",
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 400

    @pytest.mark.anyio
    @patch("gateco.routes.webhooks.stripe")
    async def test_webhook_handles_subscription_events(
        self, mock_stripe, client: AsyncClient
    ):
        """
        Webhook handles subscription lifecycle events.

        Given: Subscription updated event
        When: POST /api/webhooks/stripe is called
        Then: Event is processed successfully
        """
        mock_stripe.Webhook.construct_event.return_value = create_webhook_event(
            "customer.subscription.updated"
        )

        response = await client.post(
            "/api/webhooks/stripe",
            content=b'{"type": "customer.subscription.updated"}',
            headers={
                "Stripe-Signature": "valid_signature",
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200

    @pytest.mark.anyio
    @patch("gateco.routes.webhooks.stripe")
    async def test_webhook_handles_invoice_events(
        self, mock_stripe, client: AsyncClient
    ):
        """
        Webhook handles invoice events.

        Given: invoice.paid event
        When: POST /api/webhooks/stripe is called
        Then: Event is processed, payment recorded
        """
        mock_stripe.Webhook.construct_event.return_value = create_webhook_event(
            "invoice.paid"
        )

        response = await client.post(
            "/api/webhooks/stripe",
            content=b'{"type": "invoice.paid"}',
            headers={
                "Stripe-Signature": "valid_signature",
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200
