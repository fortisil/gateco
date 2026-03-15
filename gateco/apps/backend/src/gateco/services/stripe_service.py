"""Stripe integration service.

Handles Stripe API calls for checkout sessions, billing portal,
and webhook event processing. All Stripe SDK calls are isolated here.
"""

import logging
import os
from typing import Optional

import stripe

logger = logging.getLogger(__name__)

# Initialize Stripe with secret key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

# Plan ID to Stripe price mapping
PLAN_PRICES = {
    "pro": {
        "monthly": os.getenv("STRIPE_PRO_MONTHLY_PRICE_ID", "price_pro_monthly"),
        "yearly": os.getenv("STRIPE_PRO_YEARLY_PRICE_ID", "price_pro_yearly"),
    },
    "enterprise": {
        "monthly": os.getenv("STRIPE_ENTERPRISE_MONTHLY_PRICE_ID", "price_ent_monthly"),
        "yearly": os.getenv("STRIPE_ENTERPRISE_YEARLY_PRICE_ID", "price_ent_yearly"),
    },
}

# Plan catalog (static, no DB needed)
PLANS = [
    {
        "id": "free",
        "name": "Free",
        "tier": "free",
        "price_monthly_cents": 0,
        "price_yearly_cents": 0,
        "features": {
            "rbac_policies": True, "abac_policies": False, "policy_studio": False,
            "policy_versioning": False, "access_simulator": False, "vendor_iam": False,
            "multi_connector": False, "advanced_analytics": False, "audit_export": False,
            "siem_export": False, "content_ref_mode": False, "custom_kms": False,
            "sso_scim": False, "private_data_plane": False,
        },
        "limits": {
            "secured_retrievals": 100, "connectors": 1, "identity_providers": 1,
            "policies": 3, "team_members": 1, "overage_price_cents": 0,
        },
    },
    {
        "id": "pro",
        "name": "Pro",
        "tier": "pro",
        "price_monthly_cents": 4900,
        "price_yearly_cents": 49000,
        "features": {
            "rbac_policies": True, "abac_policies": True, "policy_studio": True,
            "policy_versioning": True, "access_simulator": True, "vendor_iam": True,
            "multi_connector": True, "advanced_analytics": True, "audit_export": True,
            "siem_export": False, "content_ref_mode": False, "custom_kms": False,
            "sso_scim": False, "private_data_plane": False,
        },
        "limits": {
            "secured_retrievals": 10000, "connectors": 5, "identity_providers": 3,
            "policies": None, "team_members": 10, "overage_price_cents": 50,
        },
    },
    {
        "id": "enterprise",
        "name": "Enterprise",
        "tier": "enterprise",
        "price_monthly_cents": 19900,
        "price_yearly_cents": 199000,
        "features": {
            "rbac_policies": True, "abac_policies": True, "policy_studio": True,
            "policy_versioning": True, "access_simulator": True, "vendor_iam": True,
            "multi_connector": True, "advanced_analytics": True, "audit_export": True,
            "siem_export": True, "content_ref_mode": True, "custom_kms": True,
            "sso_scim": True, "private_data_plane": True,
        },
        "limits": {
            "secured_retrievals": None, "connectors": None, "identity_providers": None,
            "policies": None, "team_members": None, "overage_price_cents": 0,
        },
    },
]


def get_plans() -> list[dict]:
    """Return the static plan catalog."""
    return PLANS


def get_plan_by_id(plan_id: str) -> Optional[dict]:
    """Lookup a plan by ID."""
    for plan in PLANS:
        if plan["id"] == plan_id:
            return plan
    return None


async def create_checkout_session(
    plan_id: str,
    billing_period: str,
    customer_email: str,
    organization_id: str,
    success_url: str = "",
    cancel_url: str = "",
) -> dict:
    """Create a Stripe Checkout Session for plan upgrade.

    Args:
        plan_id: Plan to subscribe to (pro/enterprise).
        billing_period: 'monthly' or 'yearly'.
        customer_email: Customer email for Stripe.
        organization_id: Org ID for metadata.
        success_url: Redirect URL on success.
        cancel_url: Redirect URL on cancel.

    Returns:
        dict with checkout_url and session_id.
    """
    if plan_id not in PLAN_PRICES:
        raise ValueError(f"No Stripe price configured for plan: {plan_id}")

    price_id = PLAN_PRICES[plan_id].get(billing_period)
    if not price_id:
        raise ValueError(f"No price for {plan_id}/{billing_period}")

    base_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    if not success_url:
        success_url = f"{base_url}/usage-billing?checkout=success"
    if not cancel_url:
        cancel_url = f"{base_url}/usage-billing?checkout=canceled"

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=customer_email,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "organization_id": organization_id,
            "plan_id": plan_id,
        },
    )

    return {
        "checkout_url": session.url,
        "session_id": session.id,
    }


async def create_billing_portal_session(
    stripe_customer_id: str,
    return_url: str = "",
) -> dict:
    """Create a Stripe Billing Portal session.

    Args:
        stripe_customer_id: Stripe customer ID.
        return_url: URL to return to after portal.

    Returns:
        dict with portal_url.
    """
    base_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    if not return_url:
        return_url = f"{base_url}/usage-billing"

    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=return_url,
    )

    return {"portal_url": session.url}


def verify_webhook_signature(payload: bytes, sig_header: str) -> dict:
    """Verify and parse a Stripe webhook event.

    Args:
        payload: Raw request body.
        sig_header: Stripe-Signature header value.

    Returns:
        Parsed Stripe event dict.

    Raises:
        ValueError: If signature verification fails.
    """
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        raise ValueError("STRIPE_WEBHOOK_SECRET not configured")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        return event
    except stripe.SignatureVerificationError:
        raise ValueError("Invalid webhook signature")
