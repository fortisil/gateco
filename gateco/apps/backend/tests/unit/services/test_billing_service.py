"""Unit tests for BillingService.

This module tests billing operations including plan management,
entitlement checks, and subscription lifecycle.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone, timedelta


# ============================================================================
# Plan Retrieval Tests
# ============================================================================


class TestGetPlans:
    """Tests for BillingService.get_plans method."""

    @pytest.mark.anyio
    async def test_get_all_plans(self, db_session):
        """
        Get all available plans.

        Given: Plans configured in system
        When: get_plans() is called
        Then: All plans are returned with correct structure
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        plans = await service.get_plans()

        assert len(plans) == 3
        tiers = [p.tier for p in plans]
        assert "free" in tiers
        assert "pro" in tiers
        assert "enterprise" in tiers

    @pytest.mark.anyio
    async def test_plan_includes_pricing(self, db_session):
        """
        Each plan includes monthly and yearly pricing.

        Given: Plans in system
        When: get_plans() is called
        Then: Each plan has pricing information
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        plans = await service.get_plans()

        for plan in plans:
            assert hasattr(plan, "price_monthly_cents")
            assert hasattr(plan, "price_yearly_cents")
            assert plan.price_monthly_cents >= 0
            assert plan.price_yearly_cents >= 0

    @pytest.mark.anyio
    async def test_plan_includes_features(self, db_session):
        """
        Each plan includes feature flags.

        Given: Plans in system
        When: get_plans() is called
        Then: Each plan has features dict
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        plans = await service.get_plans()

        for plan in plans:
            assert hasattr(plan, "features")
            assert "custom_branding" in plan.features
            assert "analytics" in plan.features
            assert "api_access" in plan.features

    @pytest.mark.anyio
    async def test_plan_includes_limits(self, db_session):
        """
        Each plan includes usage limits.

        Given: Plans in system
        When: get_plans() is called
        Then: Each plan has limits dict
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        plans = await service.get_plans()

        for plan in plans:
            assert hasattr(plan, "limits")
            assert "resources" in plan.limits
            assert "secured_retrievals" in plan.limits
            assert "team_members" in plan.limits


class TestGetPlanByTier:
    """Tests for BillingService.get_plan method."""

    @pytest.mark.anyio
    async def test_get_free_plan(self, db_session):
        """Get free plan by tier."""
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        plan = await service.get_plan("free")

        assert plan is not None
        assert plan.tier == "free"
        assert plan.price_monthly_cents == 0

    @pytest.mark.anyio
    async def test_get_pro_plan(self, db_session):
        """Get pro plan by tier."""
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        plan = await service.get_plan("pro")

        assert plan is not None
        assert plan.tier == "pro"
        assert plan.price_monthly_cents == 2900  # $29

    @pytest.mark.anyio
    async def test_get_nonexistent_plan(self, db_session):
        """
        Get nonexistent plan returns None.

        Given: Invalid tier name
        When: get_plan() is called
        Then: None is returned
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        plan = await service.get_plan("invalid")

        assert plan is None


# ============================================================================
# Entitlement Check Tests
# ============================================================================


class TestCheckEntitlement:
    """Tests for BillingService.check_entitlement method."""

    @pytest.mark.anyio
    async def test_free_plan_no_custom_branding(self, db_session, test_organization):
        """
        Free plan does not have custom branding.

        Given: Organization on free plan
        When: check_entitlement() is called for custom_branding
        Then: Returns False
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        has_feature = await service.check_entitlement(
            organization_id=str(test_organization["id"]),
            feature="custom_branding",
        )

        assert has_feature is False

    @pytest.mark.anyio
    async def test_pro_plan_has_custom_branding(self, db_session, pro_organization):
        """
        Pro plan has custom branding.

        Given: Organization on pro plan
        When: check_entitlement() is called for custom_branding
        Then: Returns True
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        has_feature = await service.check_entitlement(
            organization_id=str(pro_organization["id"]),
            feature="custom_branding",
        )

        assert has_feature is True

    @pytest.mark.anyio
    async def test_pro_plan_no_priority_support(self, db_session, pro_organization):
        """
        Pro plan does not have priority support.

        Given: Organization on pro plan
        When: check_entitlement() is called for priority_support
        Then: Returns False
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        has_feature = await service.check_entitlement(
            organization_id=str(pro_organization["id"]),
            feature="priority_support",
        )

        assert has_feature is False

    @pytest.mark.anyio
    async def test_enterprise_has_all_features(self, db_session, enterprise_organization):
        """
        Enterprise plan has all features.

        Given: Organization on enterprise plan
        When: check_entitlement() is called for any feature
        Then: Returns True
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)

        features = ["custom_branding", "analytics", "api_access", "priority_support"]

        for feature in features:
            has_feature = await service.check_entitlement(
                organization_id=str(enterprise_organization["id"]),
                feature=feature,
            )
            assert has_feature is True, f"Expected {feature} to be True"

    @pytest.mark.anyio
    async def test_unknown_feature_returns_false(self, db_session, test_organization):
        """
        Unknown feature returns False.

        Given: Unknown feature name
        When: check_entitlement() is called
        Then: Returns False
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        has_feature = await service.check_entitlement(
            organization_id=str(test_organization["id"]),
            feature="unknown_feature",
        )

        assert has_feature is False


# ============================================================================
# Limit Check Tests
# ============================================================================


class TestCheckLimit:
    """Tests for BillingService.check_limit method."""

    @pytest.mark.anyio
    async def test_free_plan_resource_limit(self, db_session, test_organization):
        """
        Free plan has 3 resource limit.

        Given: Organization on free plan
        When: check_limit() is called for resources
        Then: Returns 3
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        limit = await service.get_limit(
            organization_id=str(test_organization["id"]),
            limit_type="resources",
        )

        assert limit == 3

    @pytest.mark.anyio
    async def test_pro_plan_unlimited_resources(self, db_session, pro_organization):
        """
        Pro plan has unlimited resources.

        Given: Organization on pro plan
        When: check_limit() is called for resources
        Then: Returns None (unlimited)
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        limit = await service.get_limit(
            organization_id=str(pro_organization["id"]),
            limit_type="resources",
        )

        assert limit is None  # Unlimited

    @pytest.mark.anyio
    async def test_free_plan_retrieval_limit(self, db_session, test_organization):
        """
        Free plan has 100 retrieval limit.

        Given: Organization on free plan
        When: check_limit() is called for secured_retrievals
        Then: Returns 100
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        limit = await service.get_limit(
            organization_id=str(test_organization["id"]),
            limit_type="secured_retrievals",
        )

        assert limit == 100

    @pytest.mark.anyio
    async def test_is_within_limit_true(self, db_session, test_organization):
        """
        Check returns True when within limit.

        Given: Organization with 2 resources (limit 3)
        When: is_within_limit() is called
        Then: Returns True
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        within = await service.is_within_limit(
            organization_id=str(test_organization["id"]),
            limit_type="resources",
            current_count=2,
        )

        assert within is True

    @pytest.mark.anyio
    async def test_is_within_limit_false(self, db_session, test_organization):
        """
        Check returns False when at limit.

        Given: Organization with 3 resources (limit 3)
        When: is_within_limit() is called for adding one more
        Then: Returns False
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        within = await service.is_within_limit(
            organization_id=str(test_organization["id"]),
            limit_type="resources",
            current_count=3,
        )

        assert within is False

    @pytest.mark.anyio
    async def test_unlimited_always_within_limit(self, db_session, pro_organization):
        """
        Unlimited plans are always within limit.

        Given: Organization on pro plan (unlimited resources)
        When: is_within_limit() is called with any count
        Then: Returns True
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        within = await service.is_within_limit(
            organization_id=str(pro_organization["id"]),
            limit_type="resources",
            current_count=1000,
        )

        assert within is True


# ============================================================================
# Subscription Management Tests
# ============================================================================


class TestGetSubscription:
    """Tests for BillingService.get_subscription method."""

    @pytest.mark.anyio
    async def test_get_active_subscription(self, db_session, pro_organization):
        """
        Get active subscription for organization.

        Given: Organization with active subscription
        When: get_subscription() is called
        Then: Subscription details returned
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        subscription = await service.get_subscription(
            organization_id=str(pro_organization["id"]),
        )

        assert subscription is not None
        assert subscription.status == "active"
        assert subscription.plan_tier == "pro"

    @pytest.mark.anyio
    async def test_get_subscription_free_plan(self, db_session, test_organization):
        """
        Free plan organization has no subscription.

        Given: Organization on free plan
        When: get_subscription() is called
        Then: None is returned
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        subscription = await service.get_subscription(
            organization_id=str(test_organization["id"]),
        )

        assert subscription is None

    @pytest.mark.anyio
    async def test_subscription_includes_billing_period(self, db_session, pro_organization):
        """
        Subscription includes billing period dates.

        Given: Organization with subscription
        When: get_subscription() is called
        Then: current_period_start and current_period_end are set
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        subscription = await service.get_subscription(
            organization_id=str(pro_organization["id"]),
        )

        assert subscription.current_period_start is not None
        assert subscription.current_period_end is not None
        assert subscription.current_period_end > subscription.current_period_start


class TestCancelSubscription:
    """Tests for BillingService.cancel_subscription method."""

    @pytest.mark.anyio
    async def test_cancel_at_period_end(self, db_session, pro_organization):
        """
        Cancel schedules cancellation at period end.

        Given: Organization with active subscription
        When: cancel_subscription() is called
        Then: Subscription marked for cancellation at period end
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)

        with patch("stripe.Subscription.modify") as mock_modify:
            from tests.mocks.stripe_mock import MockStripeSubscription

            mock_sub = MockStripeSubscription()
            mock_sub.cancel_at_period_end = True
            mock_modify.return_value = mock_sub

            result = await service.cancel_subscription(
                organization_id=str(pro_organization["id"]),
            )

            assert result.cancel_at_period_end is True
            mock_modify.assert_called_once()

    @pytest.mark.anyio
    async def test_cancel_free_plan_raises_error(self, db_session, test_organization):
        """
        Cannot cancel non-existent subscription.

        Given: Organization on free plan
        When: cancel_subscription() is called
        Then: Error is raised
        """
        from src.gateco.services.billing_service import BillingService
        from src.gateco.utils.errors import ValidationError

        service = BillingService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.cancel_subscription(
                organization_id=str(test_organization["id"]),
            )

        assert "no active subscription" in str(exc_info.value).lower()


class TestReactivateSubscription:
    """Tests for BillingService.reactivate_subscription method."""

    @pytest.mark.anyio
    async def test_reactivate_cancelled_subscription(self, db_session, pro_organization):
        """
        Can reactivate subscription scheduled for cancellation.

        Given: Subscription marked for cancellation at period end
        When: reactivate_subscription() is called
        Then: Cancellation is undone
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)

        with patch("stripe.Subscription.modify") as mock_modify:
            from tests.mocks.stripe_mock import MockStripeSubscription

            mock_sub = MockStripeSubscription()
            mock_sub.cancel_at_period_end = False
            mock_modify.return_value = mock_sub

            result = await service.reactivate_subscription(
                organization_id=str(pro_organization["id"]),
            )

            assert result.cancel_at_period_end is False


# ============================================================================
# Plan Change Tests
# ============================================================================


class TestChangePlan:
    """Tests for BillingService.change_plan method."""

    @pytest.mark.anyio
    async def test_upgrade_pro_to_enterprise(self, db_session, pro_organization):
        """
        Upgrade from Pro to Enterprise.

        Given: Organization on Pro plan
        When: change_plan() is called for Enterprise
        Then: Plan is upgraded immediately
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)

        with patch("stripe.Subscription.modify") as mock_modify:
            from tests.mocks.stripe_mock import MockStripeSubscription

            mock_sub = MockStripeSubscription(price_id="price_enterprise_monthly")
            mock_modify.return_value = mock_sub

            result = await service.change_plan(
                organization_id=str(pro_organization["id"]),
                new_plan="enterprise",
            )

            assert result.plan_tier == "enterprise"

    @pytest.mark.anyio
    async def test_downgrade_scheduled_for_period_end(self, db_session, pro_organization):
        """
        Downgrade is scheduled for end of billing period.

        Given: Organization on Pro plan
        When: change_plan() is called for Free
        Then: Downgrade scheduled for period end
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)

        result = await service.change_plan(
            organization_id=str(pro_organization["id"]),
            new_plan="free",
        )

        assert result.scheduled_plan == "free"
        assert result.effective_at is not None

    @pytest.mark.anyio
    async def test_cannot_change_to_current_plan(self, db_session, pro_organization):
        """
        Cannot change to current plan.

        Given: Organization on Pro plan
        When: change_plan() is called for Pro
        Then: ValidationError is raised
        """
        from src.gateco.services.billing_service import BillingService
        from src.gateco.utils.errors import ValidationError

        service = BillingService(db_session)

        with pytest.raises(ValidationError):
            await service.change_plan(
                organization_id=str(pro_organization["id"]),
                new_plan="pro",
            )


# ============================================================================
# Invoice Tests
# ============================================================================


class TestGetInvoices:
    """Tests for BillingService.get_invoices method."""

    @pytest.mark.anyio
    async def test_get_invoices_paginated(self, db_session, pro_organization):
        """
        Get paginated invoice list.

        Given: Organization with invoices
        When: get_invoices() is called
        Then: Paginated list returned
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        result = await service.get_invoices(
            organization_id=str(pro_organization["id"]),
            page=1,
            per_page=10,
        )

        assert hasattr(result, "data")
        assert hasattr(result, "pagination")
        assert isinstance(result.data, list)

    @pytest.mark.anyio
    async def test_invoice_includes_required_fields(self, db_session, pro_organization):
        """
        Each invoice has required fields.

        Given: Organization with invoices
        When: get_invoices() is called
        Then: Invoices have id, amount, status, period
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        result = await service.get_invoices(
            organization_id=str(pro_organization["id"]),
        )

        for invoice in result.data:
            assert hasattr(invoice, "id")
            assert hasattr(invoice, "amount_cents")
            assert hasattr(invoice, "status")
            assert hasattr(invoice, "period_start")
            assert hasattr(invoice, "period_end")

    @pytest.mark.anyio
    async def test_free_plan_no_invoices(self, db_session, test_organization):
        """
        Free plan organization has no invoices.

        Given: Organization on free plan
        When: get_invoices() is called
        Then: Empty list returned
        """
        from src.gateco.services.billing_service import BillingService

        service = BillingService(db_session)
        result = await service.get_invoices(
            organization_id=str(test_organization["id"]),
        )

        assert result.data == []
