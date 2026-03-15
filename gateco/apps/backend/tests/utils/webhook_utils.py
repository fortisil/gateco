"""Utilities for testing Stripe webhooks.

This module provides helpers for simulating Stripe webhook events,
generating valid webhook signatures, and creating test event payloads.
"""

import hmac
import hashlib
import time
import json
from typing import Any, Optional
from uuid import uuid4


def generate_stripe_signature(
    payload: str,
    secret: str,
    timestamp: Optional[int] = None,
) -> str:
    """
    Generate a valid Stripe webhook signature.

    Args:
        payload: The raw JSON payload string
        secret: The webhook signing secret (whsec_...)
        timestamp: Unix timestamp (defaults to current time)

    Returns:
        str: The Stripe-Signature header value
    """
    timestamp = timestamp or int(time.time())

    # Stripe signature format: t=timestamp,v1=signature
    signed_payload = f"{timestamp}.{payload}"
    signature = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return f"t={timestamp},v1={signature}"


def create_webhook_headers(
    payload: str,
    secret: str = "whsec_test_secret",
    timestamp: Optional[int] = None,
) -> dict:
    """
    Create headers for a Stripe webhook request.

    Args:
        payload: The raw JSON payload string
        secret: The webhook signing secret
        timestamp: Unix timestamp

    Returns:
        dict: Headers dict with Stripe-Signature
    """
    return {
        "Content-Type": "application/json",
        "Stripe-Signature": generate_stripe_signature(payload, secret, timestamp),
    }


def create_stripe_event(
    event_type: str,
    data_object: dict = None,
    event_id: str = None,
    api_version: str = "2024-01-01",
    created: Optional[int] = None,
) -> dict:
    """
    Create a Stripe event payload for testing.

    Args:
        event_type: The event type (e.g., "checkout.session.completed")
        data_object: The object in data.object
        event_id: Event ID (auto-generated if not provided)
        api_version: Stripe API version
        created: Event creation timestamp

    Returns:
        dict: Complete Stripe event payload
    """
    return {
        "id": event_id or f"evt_test_{uuid4().hex[:16]}",
        "object": "event",
        "api_version": api_version,
        "created": created or int(time.time()),
        "type": event_type,
        "livemode": False,
        "pending_webhooks": 1,
        "request": {
            "id": f"req_test_{uuid4().hex[:8]}",
            "idempotency_key": None,
        },
        "data": {
            "object": data_object or {},
        },
    }


def create_checkout_completed_event(
    organization_id: str,
    customer_id: str = None,
    subscription_id: str = None,
    plan_id: str = "pro",
    billing_period: str = "monthly",
    amount_total: int = 2900,
) -> dict:
    """
    Create a checkout.session.completed event.

    Args:
        organization_id: The organization ID in metadata
        customer_id: Stripe customer ID
        subscription_id: Stripe subscription ID
        plan_id: Plan being purchased
        billing_period: monthly or yearly
        amount_total: Total amount in cents

    Returns:
        dict: Checkout completed event payload
    """
    return create_stripe_event(
        "checkout.session.completed",
        {
            "id": f"cs_test_{uuid4().hex[:16]}",
            "object": "checkout.session",
            "amount_total": amount_total,
            "currency": "usd",
            "customer": customer_id or f"cus_test_{uuid4().hex[:16]}",
            "mode": "subscription",
            "payment_status": "paid",
            "status": "complete",
            "subscription": subscription_id or f"sub_test_{uuid4().hex[:16]}",
            "metadata": {
                "organization_id": str(organization_id),
                "plan_id": plan_id,
                "billing_period": billing_period,
            },
            "customer_details": {
                "email": "customer@example.com",
            },
        },
    )


def create_subscription_updated_event(
    subscription_id: str = None,
    customer_id: str = None,
    status: str = "active",
    plan_id: str = "pro",
    current_period_start: Optional[int] = None,
    current_period_end: Optional[int] = None,
    cancel_at_period_end: bool = False,
) -> dict:
    """
    Create a customer.subscription.updated event.

    Args:
        subscription_id: Stripe subscription ID
        customer_id: Stripe customer ID
        status: Subscription status
        plan_id: Plan ID
        current_period_start: Period start timestamp
        current_period_end: Period end timestamp
        cancel_at_period_end: Whether canceling at period end

    Returns:
        dict: Subscription updated event payload
    """
    now = int(time.time())
    return create_stripe_event(
        "customer.subscription.updated",
        {
            "id": subscription_id or f"sub_test_{uuid4().hex[:16]}",
            "object": "subscription",
            "customer": customer_id or f"cus_test_{uuid4().hex[:16]}",
            "status": status,
            "current_period_start": current_period_start or now,
            "current_period_end": current_period_end or (now + 30 * 24 * 3600),
            "cancel_at_period_end": cancel_at_period_end,
            "items": {
                "data": [
                    {
                        "id": f"si_test_{uuid4().hex[:8]}",
                        "price": {
                            "id": f"price_{plan_id}_monthly",
                            "product": f"prod_{plan_id}",
                        },
                    }
                ]
            },
            "metadata": {
                "plan_id": plan_id,
            },
        },
    )


def create_subscription_deleted_event(
    subscription_id: str = None,
    customer_id: str = None,
) -> dict:
    """
    Create a customer.subscription.deleted event.

    Args:
        subscription_id: Stripe subscription ID
        customer_id: Stripe customer ID

    Returns:
        dict: Subscription deleted event payload
    """
    now = int(time.time())
    return create_stripe_event(
        "customer.subscription.deleted",
        {
            "id": subscription_id or f"sub_test_{uuid4().hex[:16]}",
            "object": "subscription",
            "customer": customer_id or f"cus_test_{uuid4().hex[:16]}",
            "status": "canceled",
            "canceled_at": now,
            "ended_at": now,
        },
    )


def create_invoice_paid_event(
    invoice_id: str = None,
    customer_id: str = None,
    subscription_id: str = None,
    amount_paid: int = 2900,
    currency: str = "usd",
) -> dict:
    """
    Create an invoice.paid event.

    Args:
        invoice_id: Stripe invoice ID
        customer_id: Stripe customer ID
        subscription_id: Associated subscription ID
        amount_paid: Amount paid in cents
        currency: Currency code

    Returns:
        dict: Invoice paid event payload
    """
    now = int(time.time())
    return create_stripe_event(
        "invoice.paid",
        {
            "id": invoice_id or f"in_test_{uuid4().hex[:16]}",
            "object": "invoice",
            "customer": customer_id or f"cus_test_{uuid4().hex[:16]}",
            "subscription": subscription_id or f"sub_test_{uuid4().hex[:16]}",
            "amount_paid": amount_paid,
            "currency": currency,
            "status": "paid",
            "paid": True,
            "period_start": now - 30 * 24 * 3600,
            "period_end": now,
            "invoice_pdf": f"https://pay.stripe.com/invoice/{invoice_id or 'test'}/pdf",
            "hosted_invoice_url": f"https://invoice.stripe.com/{invoice_id or 'test'}",
        },
    )


def create_invoice_payment_failed_event(
    invoice_id: str = None,
    customer_id: str = None,
    subscription_id: str = None,
    amount_due: int = 2900,
    attempt_count: int = 1,
    next_payment_attempt: Optional[int] = None,
) -> dict:
    """
    Create an invoice.payment_failed event.

    Args:
        invoice_id: Stripe invoice ID
        customer_id: Stripe customer ID
        subscription_id: Associated subscription ID
        amount_due: Amount due in cents
        attempt_count: Number of payment attempts
        next_payment_attempt: Timestamp of next attempt

    Returns:
        dict: Invoice payment failed event payload
    """
    now = int(time.time())
    return create_stripe_event(
        "invoice.payment_failed",
        {
            "id": invoice_id or f"in_test_{uuid4().hex[:16]}",
            "object": "invoice",
            "customer": customer_id or f"cus_test_{uuid4().hex[:16]}",
            "subscription": subscription_id or f"sub_test_{uuid4().hex[:16]}",
            "amount_due": amount_due,
            "currency": "usd",
            "status": "open",
            "paid": False,
            "attempt_count": attempt_count,
            "next_payment_attempt": next_payment_attempt or (now + 3 * 24 * 3600),
        },
    )


class WebhookTestClient:
    """Helper class for sending webhook requests in tests."""

    def __init__(self, client, secret: str = "whsec_test_secret"):
        """
        Initialize webhook test client.

        Args:
            client: AsyncClient instance
            secret: Webhook signing secret
        """
        self.client = client
        self.secret = secret
        self.webhook_url = "/api/webhooks/stripe"

    async def send_event(self, event: dict) -> Any:
        """
        Send a webhook event to the API.

        Args:
            event: Stripe event dict

        Returns:
            HTTP response
        """
        payload = json.dumps(event)
        headers = create_webhook_headers(payload, self.secret)

        return await self.client.post(
            self.webhook_url,
            content=payload,
            headers=headers,
        )

    async def send_checkout_completed(
        self,
        organization_id: str,
        **kwargs,
    ) -> Any:
        """Send checkout.session.completed event."""
        event = create_checkout_completed_event(organization_id, **kwargs)
        return await self.send_event(event)

    async def send_subscription_updated(self, **kwargs) -> Any:
        """Send customer.subscription.updated event."""
        event = create_subscription_updated_event(**kwargs)
        return await self.send_event(event)

    async def send_subscription_deleted(self, **kwargs) -> Any:
        """Send customer.subscription.deleted event."""
        event = create_subscription_deleted_event(**kwargs)
        return await self.send_event(event)

    async def send_invoice_paid(self, **kwargs) -> Any:
        """Send invoice.paid event."""
        event = create_invoice_paid_event(**kwargs)
        return await self.send_event(event)

    async def send_invoice_payment_failed(self, **kwargs) -> Any:
        """Send invoice.payment_failed event."""
        event = create_invoice_payment_failed_event(**kwargs)
        return await self.send_event(event)

    async def send_invalid_signature(self, event: dict) -> Any:
        """Send event with invalid signature for testing."""
        payload = json.dumps(event)
        headers = {
            "Content-Type": "application/json",
            "Stripe-Signature": "t=1234567890,v1=invalid_signature",
        }
        return await self.client.post(
            self.webhook_url,
            content=payload,
            headers=headers,
        )
