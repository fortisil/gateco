"""Factory for creating test subscriptions and billing data."""

from uuid import uuid4
from datetime import datetime, timezone, timedelta
from typing import Optional
from enum import Enum


class SubscriptionStatus(str, Enum):
    """Stripe subscription statuses."""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    UNPAID = "unpaid"


class BillingPeriod(str, Enum):
    """Billing period options."""
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionFactory:
    """Factory for creating test subscriptions."""

    @staticmethod
    def create(
        organization_id: str = None,
        plan_id: str = "pro",
        stripe_subscription_id: Optional[str] = None,
        stripe_customer_id: Optional[str] = None,
        status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
        billing_period: BillingPeriod = BillingPeriod.MONTHLY,
        current_period_days: int = 30,
        cancel_at_period_end: bool = False,
    ) -> dict:
        """
        Create a test subscription dict.

        Args:
            organization_id: Organization this subscription belongs to
            plan_id: Plan identifier (free, pro, enterprise)
            stripe_subscription_id: Stripe subscription ID
            stripe_customer_id: Stripe customer ID
            status: Subscription status
            billing_period: Monthly or yearly billing
            current_period_days: Days in current billing period
            cancel_at_period_end: Whether subscription cancels at period end

        Returns:
            dict: Subscription data ready for model creation
        """
        sub_id = uuid4()
        now = datetime.now(timezone.utc)

        return {
            "id": sub_id,
            "organization_id": organization_id or uuid4(),
            "plan_id": plan_id,
            "stripe_subscription_id": stripe_subscription_id or f"sub_test_{uuid4().hex[:16]}",
            "stripe_customer_id": stripe_customer_id or f"cus_test_{uuid4().hex[:16]}",
            "status": status.value,
            "billing_period": billing_period.value,
            "current_period_start": now,
            "current_period_end": now + timedelta(days=current_period_days),
            "cancel_at": (now + timedelta(days=current_period_days)) if cancel_at_period_end else None,
            "cancel_at_period_end": cancel_at_period_end,
            "created_at": now,
            "updated_at": now,
        }

    @staticmethod
    def create_active(
        organization_id: str = None,
        plan_id: str = "pro",
        **kwargs,
    ) -> dict:
        """Create an active subscription."""
        return SubscriptionFactory.create(
            organization_id=organization_id,
            plan_id=plan_id,
            status=SubscriptionStatus.ACTIVE,
            **kwargs,
        )

    @staticmethod
    def create_canceled(
        organization_id: str = None,
        plan_id: str = "pro",
        **kwargs,
    ) -> dict:
        """Create a canceled subscription."""
        return SubscriptionFactory.create(
            organization_id=organization_id,
            plan_id=plan_id,
            status=SubscriptionStatus.CANCELED,
            **kwargs,
        )

    @staticmethod
    def create_past_due(
        organization_id: str = None,
        plan_id: str = "pro",
        **kwargs,
    ) -> dict:
        """Create a past-due subscription."""
        return SubscriptionFactory.create(
            organization_id=organization_id,
            plan_id=plan_id,
            status=SubscriptionStatus.PAST_DUE,
            **kwargs,
        )


class PaymentFactory:
    """Factory for creating test payment records."""

    @staticmethod
    def create(
        organization_id: str = None,
        resource_id: Optional[str] = None,
        stripe_payment_intent_id: Optional[str] = None,
        amount_cents: int = 999,
        currency: str = "USD",
        status: str = "succeeded",
    ) -> dict:
        """
        Create a test payment record.

        Args:
            organization_id: Organization that received payment
            resource_id: Resource that was purchased (if applicable)
            stripe_payment_intent_id: Stripe PaymentIntent ID
            amount_cents: Payment amount in cents
            currency: Currency code
            status: Payment status (succeeded, failed, pending)

        Returns:
            dict: Payment data
        """
        payment_id = uuid4()
        return {
            "id": payment_id,
            "organization_id": organization_id or uuid4(),
            "resource_id": resource_id,
            "stripe_payment_intent_id": stripe_payment_intent_id or f"pi_test_{uuid4().hex[:16]}",
            "amount_cents": amount_cents,
            "currency": currency,
            "status": status,
            "created_at": datetime.now(timezone.utc),
        }


class InvoiceFactory:
    """Factory for creating test invoice records."""

    @staticmethod
    def create(
        organization_id: str = None,
        subscription_id: str = None,
        stripe_invoice_id: Optional[str] = None,
        amount_cents: int = 2900,
        currency: str = "USD",
        status: str = "paid",
        period_days: int = 30,
    ) -> dict:
        """
        Create a test invoice record.

        Args:
            organization_id: Organization billed
            subscription_id: Associated subscription
            stripe_invoice_id: Stripe invoice ID
            amount_cents: Invoice amount in cents
            currency: Currency code
            status: Invoice status (paid, open, void)
            period_days: Length of billing period

        Returns:
            dict: Invoice data
        """
        invoice_id = uuid4()
        now = datetime.now(timezone.utc)

        return {
            "id": invoice_id,
            "organization_id": organization_id or uuid4(),
            "subscription_id": subscription_id,
            "stripe_invoice_id": stripe_invoice_id or f"in_test_{uuid4().hex[:16]}",
            "amount_cents": amount_cents,
            "currency": currency,
            "status": status,
            "period_start": now - timedelta(days=period_days),
            "period_end": now,
            "pdf_url": f"https://invoice.stripe.com/{stripe_invoice_id or 'test'}/pdf",
            "created_at": now,
        }


class UsageLogFactory:
    """Factory for creating test usage log records."""

    @staticmethod
    def create(
        organization_id: str = None,
        period_start: datetime = None,
        period_end: datetime = None,
        retrievals: int = 50,
        overage: int = 0,
    ) -> dict:
        """
        Create a test usage log record.

        Args:
            organization_id: Organization this usage belongs to
            period_start: Start of billing period
            period_end: End of billing period
            retrievals: Number of secured retrievals
            overage: Number of retrievals over limit

        Returns:
            dict: Usage log data
        """
        usage_id = uuid4()
        now = datetime.now(timezone.utc)

        return {
            "id": usage_id,
            "organization_id": organization_id or uuid4(),
            "period_start": period_start or (now - timedelta(days=30)),
            "period_end": period_end or now,
            "retrievals": retrievals,
            "overage": overage,
            "created_at": now,
        }


class CouponFactory:
    """Factory for creating test coupon records."""

    @staticmethod
    def create(
        code: str = "TESTCOUPON",
        percent_off: Optional[int] = None,
        amount_off_cents: Optional[int] = None,
        currency: str = "USD",
        duration: str = "once",
        duration_in_months: Optional[int] = None,
        max_redemptions: Optional[int] = None,
        valid: bool = True,
    ) -> dict:
        """
        Create a test coupon record.

        Args:
            code: Coupon code
            percent_off: Percentage discount (0-100)
            amount_off_cents: Fixed discount in cents
            currency: Currency for amount_off
            duration: once, repeating, or forever
            duration_in_months: For repeating coupons
            max_redemptions: Maximum uses
            valid: Whether coupon is currently valid

        Returns:
            dict: Coupon data
        """
        coupon_id = uuid4()
        now = datetime.now(timezone.utc)

        # Default to 20% off if neither specified
        if percent_off is None and amount_off_cents is None:
            percent_off = 20

        return {
            "id": coupon_id,
            "code": code,
            "stripe_coupon_id": f"coupon_test_{uuid4().hex[:8]}",
            "percent_off": percent_off,
            "amount_off_cents": amount_off_cents,
            "currency": currency if amount_off_cents else None,
            "duration": duration,
            "duration_in_months": duration_in_months,
            "max_redemptions": max_redemptions,
            "times_redeemed": 0,
            "valid": valid,
            "created_at": now,
        }
