"""Billing and subscription routes.

Provides endpoints for plan listing, checkout, usage, invoices,
billing portal, and Stripe webhook handling.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gateco.database.connection import get_session
from gateco.database.enums import SubscriptionStatus
from gateco.database.models.invoice import Invoice
from gateco.database.models.organization import Organization
from gateco.database.models.stripe_event import StripeEvent
from gateco.database.models.subscription import Subscription
from gateco.database.models.usage import UsageLog
from gateco.database.models.user import User
from gateco.middleware.jwt_auth import get_current_user_org
from gateco.schemas.common import serialize_invoice_status
from gateco.services.stripe_service import (
    create_billing_portal_session,
    create_checkout_session,
    get_plans,
    verify_webhook_signature,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["billing"])


# ── Schemas ──


class CheckoutRequest(BaseModel):
    """Request to start a checkout session."""

    plan_id: str
    billing_period: str = "monthly"


class CheckoutResponse(BaseModel):
    """Checkout session response."""

    checkout_url: str
    session_id: str


class BillingPortalRequest(BaseModel):
    """Request to create a billing portal session."""

    return_url: Optional[str] = None


class BillingPortalResponse(BaseModel):
    """Billing portal response."""

    portal_url: str


# ── Plans (public) ──


@router.get("/plans")
async def list_plans():
    """List all available plans (public, no auth required)."""
    return {"plans": get_plans()}


# ── Checkout ──


@router.post("/checkout/start", response_model=CheckoutResponse)
async def start_checkout(
    body: CheckoutRequest,
    auth: tuple[User, Organization] = Depends(get_current_user_org),
    session: AsyncSession = Depends(get_session),
):
    """Create a Stripe Checkout Session for plan upgrade."""
    user, org = auth
    try:
        result = await create_checkout_session(
            plan_id=body.plan_id,
            billing_period=body.billing_period,
            customer_email=user.email,
            organization_id=str(org.id),
        )
        return CheckoutResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Checkout session creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


# ── Billing Portal ──


@router.post("/billing/portal", response_model=BillingPortalResponse)
async def billing_portal(
    body: BillingPortalRequest,
    auth: tuple[User, Organization] = Depends(get_current_user_org),
    session: AsyncSession = Depends(get_session),
):
    """Create a Stripe Billing Portal session."""
    user, org = auth
    if not org.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer associated")
    try:
        result = await create_billing_portal_session(
            stripe_customer_id=org.stripe_customer_id,
            return_url=body.return_url or "",
        )
        return BillingPortalResponse(**result)
    except Exception as e:
        logger.error(f"Billing portal creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create billing portal session")


# ── Usage ──


@router.get("/billing/usage")
async def get_usage(
    auth: tuple[User, Organization] = Depends(get_current_user_org),
    session: AsyncSession = Depends(get_session),
):
    """Get current billing period usage for the authenticated organization."""
    user, org = auth
    result = await session.execute(
        select(UsageLog)
        .where(UsageLog.organization_id == org.id)
        .order_by(UsageLog.period_start.desc())
        .limit(1)
    )
    usage = result.scalar_one_or_none()

    if usage:
        return {
            "period_start": usage.period_start.isoformat(),
            "period_end": usage.period_end.isoformat(),
            "secured_retrievals": {
                "used": usage.secured_retrievals,
                "limit": 10000,
                "overage": 0,
            },
            "connectors": {"used": 3, "limit": 5},
            "policies": {"used": 5, "limit": None},
            "estimated_overage_cents": usage.overage_cents,
        }

    return {
        "period_start": "2026-03-01T00:00:00Z",
        "period_end": "2026-03-31T23:59:59Z",
        "secured_retrievals": {"used": 0, "limit": 10000, "overage": 0},
        "connectors": {"used": 0, "limit": 5},
        "policies": {"used": 0, "limit": None},
        "estimated_overage_cents": 0,
    }


# ── Invoices ──


@router.get("/billing/invoices")
async def list_invoices(
    page: int = 1,
    per_page: int = 20,
    auth: tuple[User, Organization] = Depends(get_current_user_org),
    session: AsyncSession = Depends(get_session),
):
    """List invoices for the authenticated organization."""
    user, org = auth
    offset = (page - 1) * per_page
    result = await session.execute(
        select(Invoice)
        .where(Invoice.organization_id == org.id)
        .order_by(Invoice.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    invoices = result.scalars().all()

    data = [
        {
            "id": str(inv.id),
            "stripe_invoice_id": inv.stripe_invoice_id,
            "amount_cents": inv.amount_cents,
            "currency": inv.currency,
            "status": serialize_invoice_status(
                inv.status.value if hasattr(inv.status, "value") else inv.status
            ),
            "period_start": inv.period_start.isoformat() if inv.period_start else None,
            "period_end": inv.period_end.isoformat() if inv.period_end else None,
            "pdf_url": inv.pdf_url or "",
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
        }
        for inv in invoices
    ]

    return {
        "data": data,
        "meta": {
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": len(data),
                "total_pages": 1,
            }
        },
    }


# ── Subscription ──


@router.get("/billing/subscription")
async def get_subscription(
    auth: tuple[User, Organization] = Depends(get_current_user_org),
    session: AsyncSession = Depends(get_session),
):
    """Get current subscription for the authenticated organization."""
    user, org = auth
    result = await session.execute(
        select(Subscription)
        .where(
            Subscription.organization_id == org.id,
            Subscription.status.in_([
                SubscriptionStatus.active,
                SubscriptionStatus.trialing,
                SubscriptionStatus.past_due,
            ]),
        )
        .limit(1)
    )
    sub = result.scalar_one_or_none()

    if not sub:
        return None

    return {
        "id": str(sub.id),
        "plan_id": sub.plan_tier.value,
        "status": sub.status.value,
        "current_period_start": sub.current_period_start.isoformat(),
        "current_period_end": sub.current_period_end.isoformat(),
        "cancel_at_period_end": sub.cancel_at_period_end,
    }


# ── Stripe Webhook (public — no JWT) ──


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = verify_webhook_signature(payload, sig_header)
    except ValueError as e:
        logger.warning(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_id = event.get("id", "")
    event_type = event.get("type", "")

    # Idempotency: check if already processed
    existing = await session.execute(
        select(StripeEvent).where(StripeEvent.stripe_event_id == event_id)
    )
    if existing.scalar_one_or_none():
        return {"status": "already_processed"}

    stripe_event = StripeEvent(
        stripe_event_id=event_id,
        event_type=event_type,
        payload=event,
        processed=False,
    )
    session.add(stripe_event)

    try:
        await _process_webhook_event(event_type, event.get("data", {}).get("object", {}), session)
        stripe_event.mark_processed()
    except Exception as e:
        logger.error(f"Webhook processing error for {event_type}: {e}")
        stripe_event.mark_failed(str(e))

    return {"status": "ok"}


async def _process_webhook_event(event_type: str, data: dict, session: AsyncSession) -> None:
    """Process a specific webhook event type."""
    if event_type == "checkout.session.completed":
        org_id = data.get("metadata", {}).get("organization_id")
        plan_id = data.get("metadata", {}).get("plan_id")
        if org_id and plan_id:
            logger.info(f"Checkout completed for org {org_id}, plan {plan_id}")
            # TODO: Create/update subscription, update org plan tier

    elif event_type == "customer.subscription.updated":
        sub_id = data.get("id")
        status = data.get("status")
        logger.info(f"Subscription {sub_id} updated to {status}")
        # TODO: Sync subscription status

    elif event_type == "customer.subscription.deleted":
        sub_id = data.get("id")
        logger.info(f"Subscription {sub_id} deleted")
        # TODO: Mark canceled, downgrade to free

    elif event_type == "invoice.paid":
        invoice_id = data.get("id")
        logger.info(f"Invoice {invoice_id} paid")
        # TODO: Record payment, store invoice

    elif event_type == "invoice.payment_failed":
        invoice_id = data.get("id")
        logger.warning(f"Invoice {invoice_id} payment failed")
        # TODO: Mark subscription past_due

    else:
        logger.debug(f"Unhandled webhook event type: {event_type}")
