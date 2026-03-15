"""Unit tests for ResourceService.

This module contains comprehensive unit tests for the resource service,
covering CRUD operations, access verification, and plan limit enforcement.

These tests are designed to run once the ResourceService is implemented.
They follow the test patterns defined in the QA Implementation Plan.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from tests.factories.resource_factory import (
    ResourceFactory,
    AccessRuleFactory,
    ResourceType,
    AccessType,
)


# ============================================================================
# Resource Creation Tests
# ============================================================================


class TestResourceServiceCreate:
    """Tests for resource creation functionality."""

    @pytest.mark.anyio
    async def test_create_link_resource(self, db_session, test_organization):
        """
        Create link resource successfully.

        Given: Valid link resource data
        When: create_resource() is called
        Then: Resource is created with correct type and access rule
        """
        # from src.gateco.services.resource_service import ResourceService
        # from src.gateco.schemas.resource import CreateResourceRequest

        # service = ResourceService(db_session)
        # request = CreateResourceRequest(
        #     type="link",
        #     title="My Link",
        #     content_url="https://example.com/content",
        #     access_rule={"type": "public"},
        # )

        # result = await service.create_resource(
        #     organization_id=test_organization["id"],
        #     user_id=str(uuid4()),
        #     request=request,
        # )

        # assert result.type == "link"
        # assert result.title == "My Link"
        # assert result.access_rule.type == "public"
        pass

    @pytest.mark.anyio
    async def test_create_file_resource(self, db_session, test_organization):
        """
        Create file resource successfully.

        Given: Valid file resource data with S3 URL
        When: create_resource() is called
        Then: File resource is created
        """
        # service = ResourceService(db_session)
        # request = CreateResourceRequest(
        #     type="file",
        #     title="My Document",
        #     content_url="https://s3.example.com/files/doc.pdf",
        #     access_rule={"type": "public"},
        # )

        # result = await service.create_resource(...)

        # assert result.type == "file"
        pass

    @pytest.mark.anyio
    async def test_create_video_resource(self, db_session, test_organization):
        """
        Create video resource successfully.

        Given: Valid video resource data with thumbnail
        When: create_resource() is called
        Then: Video resource is created with thumbnail
        """
        # request = CreateResourceRequest(
        #     type="video",
        #     title="My Video",
        #     content_url="https://example.com/video.mp4",
        #     thumbnail_url="https://example.com/thumb.jpg",
        #     access_rule={"type": "public"},
        # )

        # result = await service.create_resource(...)

        # assert result.type == "video"
        # assert result.thumbnail_url is not None
        pass

    @pytest.mark.anyio
    async def test_create_resource_with_paid_access(self, db_session, test_organization):
        """
        Create resource with paid access rule.

        Given: Resource data with paid access type
        When: create_resource() is called
        Then: Resource has paid access rule with price
        """
        # request = CreateResourceRequest(
        #     type="link",
        #     title="Premium Content",
        #     content_url="https://example.com/premium",
        #     access_rule={
        #         "type": "paid",
        #         "price_cents": 999,
        #         "currency": "USD",
        #     },
        # )

        # result = await service.create_resource(...)

        # assert result.access_rule.type == "paid"
        # assert result.access_rule.price_cents == 999
        pass

    @pytest.mark.anyio
    async def test_create_resource_with_invite_access(
        self, db_session, test_organization
    ):
        """
        Create resource with invite-only access rule.

        Given: Resource data with invite-only access
        When: create_resource() is called
        Then: Resource has invite-only access with allowed emails
        """
        # request = CreateResourceRequest(
        #     type="link",
        #     title="VIP Content",
        #     content_url="https://example.com/vip",
        #     access_rule={
        #         "type": "invite_only",
        #         "allowed_emails": ["vip1@example.com", "vip2@example.com"],
        #     },
        # )

        # result = await service.create_resource(...)

        # assert result.access_rule.type == "invite_only"
        # assert len(result.access_rule.allowed_emails) == 2
        pass

    @pytest.mark.anyio
    async def test_create_resource_validates_url_format(
        self, db_session, test_organization
    ):
        """
        Invalid content URL is rejected.

        Given: Resource data with invalid URL
        When: create_resource() is called
        Then: ValidationError is raised
        """
        # from src.gateco.utils.errors import ValidationError

        # request = CreateResourceRequest(
        #     type="link",
        #     title="Bad Link",
        #     content_url="not-a-valid-url",
        #     access_rule={"type": "public"},
        # )

        # with pytest.raises(ValidationError) as exc_info:
        #     await service.create_resource(...)

        # assert "content_url" in str(exc_info.value)
        pass

    @pytest.mark.anyio
    async def test_create_resource_validates_minimum_price(
        self, db_session, test_organization
    ):
        """
        Price below minimum ($0.50) is rejected.

        Given: Paid resource with price < 50 cents
        When: create_resource() is called
        Then: ValidationError is raised
        """
        # request = CreateResourceRequest(
        #     type="link",
        #     title="Too Cheap",
        #     content_url="https://example.com/cheap",
        #     access_rule={
        #         "type": "paid",
        #         "price_cents": 25,  # $0.25, below minimum
        #         "currency": "USD",
        #     },
        # )

        # with pytest.raises(ValidationError) as exc_info:
        #     await service.create_resource(...)

        # assert "price" in str(exc_info.value).lower()
        pass


# ============================================================================
# Plan Limit Tests
# ============================================================================


class TestResourceServicePlanLimits:
    """Tests for plan limit enforcement."""

    @pytest.mark.anyio
    async def test_create_resource_free_plan_limit(
        self, db_session, test_organization, max_free_resources
    ):
        """
        Free plan resource limit enforced.

        Given: Free plan organization with 3 resources (max)
        When: create_resource() is called
        Then: RESOURCE_LIMIT_EXCEEDED error is raised
        """
        # from src.gateco.utils.errors import PlanLimitError

        # service = ResourceService(db_session)
        # request = CreateResourceRequest(
        #     type="link",
        #     title="One Too Many",
        #     content_url="https://example.com/extra",
        #     access_rule={"type": "public"},
        # )

        # with pytest.raises(PlanLimitError) as exc_info:
        #     await service.create_resource(
        #         organization_id=test_organization["id"],
        #         user_id=str(uuid4()),
        #         request=request,
        #     )

        # assert exc_info.value.code == "RESOURCE_LIMIT_EXCEEDED"
        pass

    @pytest.mark.anyio
    async def test_create_resource_pro_plan_unlimited(
        self, db_session, pro_organization
    ):
        """
        Pro plan has unlimited resources.

        Given: Pro plan organization with many resources
        When: create_resource() is called
        Then: Resource is created successfully
        """
        # Create 100 resources for pro organization - should all succeed
        # for i in range(100):
        #     request = CreateResourceRequest(...)
        #     result = await service.create_resource(
        #         organization_id=pro_organization["id"],
        #         ...
        #     )
        #     assert result is not None
        pass

    @pytest.mark.anyio
    async def test_check_resource_limit_returns_correct_counts(
        self, db_session, test_organization
    ):
        """
        Check limit returns accurate used and remaining counts.

        Given: Organization with 2 of 3 resources used
        When: check_resource_limit() is called
        Then: Used=2, Limit=3, Remaining=1
        """
        # result = await service.check_resource_limit(test_organization["id"])

        # assert result.used == 2
        # assert result.limit == 3
        # assert result.remaining == 1
        pass


# ============================================================================
# Resource Update Tests
# ============================================================================


class TestResourceServiceUpdate:
    """Tests for resource updates."""

    @pytest.mark.anyio
    async def test_update_resource_title(self, db_session, test_resource):
        """
        Update resource title successfully.

        Given: Existing resource
        When: update_resource() is called with new title
        Then: Title is updated
        """
        # from src.gateco.schemas.resource import UpdateResourceRequest

        # service = ResourceService(db_session)
        # request = UpdateResourceRequest(title="Updated Title")

        # result = await service.update_resource(
        #     resource_id=test_resource["id"],
        #     organization_id=test_resource["organization_id"],
        #     request=request,
        # )

        # assert result.title == "Updated Title"
        pass

    @pytest.mark.anyio
    async def test_update_resource_description(self, db_session, test_resource):
        """
        Update resource description successfully.

        Given: Existing resource
        When: update_resource() is called with new description
        Then: Description is updated
        """
        # request = UpdateResourceRequest(description="New description")
        # result = await service.update_resource(...)
        # assert result.description == "New description"
        pass

    @pytest.mark.anyio
    async def test_update_resource_access_rule(self, db_session, public_resource):
        """
        Update resource from public to paid access.

        Given: Public access resource
        When: update_resource() is called with paid access rule
        Then: Access rule is updated to paid
        """
        # request = UpdateResourceRequest(
        #     access_rule={
        #         "type": "paid",
        #         "price_cents": 999,
        #         "currency": "USD",
        #     }
        # )

        # result = await service.update_resource(...)

        # assert result.access_rule.type == "paid"
        # assert result.access_rule.price_cents == 999
        pass

    @pytest.mark.anyio
    async def test_update_resource_not_found(self, db_session, test_organization):
        """
        Update non-existent resource raises error.

        Given: Non-existent resource ID
        When: update_resource() is called
        Then: NotFoundError is raised
        """
        # from src.gateco.utils.errors import NotFoundError

        # with pytest.raises(NotFoundError) as exc_info:
        #     await service.update_resource(
        #         resource_id=str(uuid4()),  # Doesn't exist
        #         organization_id=test_organization["id"],
        #         request=UpdateResourceRequest(title="New"),
        #     )

        # assert exc_info.value.code == "RESOURCE_NOT_FOUND"
        pass

    @pytest.mark.anyio
    async def test_update_resource_different_org_denied(
        self, db_session, test_resource, another_organization
    ):
        """
        Cannot update resource from different organization.

        Given: Resource belongs to org A
        When: update_resource() is called with org B context
        Then: NotFoundError is raised (resource not visible)
        """
        # from src.gateco.utils.errors import NotFoundError

        # with pytest.raises(NotFoundError):
        #     await service.update_resource(
        #         resource_id=test_resource["id"],
        #         organization_id=another_organization["id"],  # Different org
        #         request=UpdateResourceRequest(title="Hacked"),
        #     )
        pass

    @pytest.mark.anyio
    async def test_update_resource_partial_update(self, db_session, test_resource):
        """
        Partial update only changes specified fields.

        Given: Resource with title and description
        When: update_resource() is called with only title
        Then: Only title is updated, description unchanged
        """
        # original_description = test_resource["description"]

        # result = await service.update_resource(
        #     resource_id=test_resource["id"],
        #     organization_id=test_resource["organization_id"],
        #     request=UpdateResourceRequest(title="New Title"),
        # )

        # assert result.title == "New Title"
        # assert result.description == original_description
        pass


# ============================================================================
# Resource Delete Tests
# ============================================================================


class TestResourceServiceDelete:
    """Tests for resource deletion."""

    @pytest.mark.anyio
    async def test_delete_resource_success(self, db_session, test_resource):
        """
        Delete resource successfully.

        Given: Existing resource
        When: delete_resource() is called
        Then: Resource is deleted
        """
        # service = ResourceService(db_session)

        # await service.delete_resource(
        #     resource_id=test_resource["id"],
        #     organization_id=test_resource["organization_id"],
        # )

        # # Verify deletion
        # result = await service.get_resource(test_resource["id"])
        # assert result is None
        pass

    @pytest.mark.anyio
    async def test_delete_resource_not_found(self, db_session, test_organization):
        """
        Delete non-existent resource raises error.

        Given: Non-existent resource ID
        When: delete_resource() is called
        Then: NotFoundError is raised
        """
        # from src.gateco.utils.errors import NotFoundError

        # with pytest.raises(NotFoundError):
        #     await service.delete_resource(
        #         resource_id=str(uuid4()),
        #         organization_id=test_organization["id"],
        #     )
        pass

    @pytest.mark.anyio
    async def test_delete_resource_with_access_logs_soft_delete(
        self, db_session, resource_with_access_logs
    ):
        """
        Resource with access history is soft deleted.

        Given: Resource with access log records
        When: delete_resource() is called
        Then: Resource is soft deleted (marked as deleted, not removed)
        """
        # resource, access_logs = resource_with_access_logs

        # await service.delete_resource(
        #     resource_id=resource["id"],
        #     organization_id=resource["organization_id"],
        # )

        # # Resource should be soft deleted
        # result = await db_session.execute(
        #     select(GatedResource).where(GatedResource.id == resource["id"])
        # )
        # resource_model = result.scalar_one()
        # assert resource_model.deleted_at is not None

        # # But access logs should still exist for analytics
        # logs = await db_session.execute(
        #     select(ResourceAccess).where(ResourceAccess.resource_id == resource["id"])
        # )
        # assert len(logs.scalars().all()) == len(access_logs)
        pass

    @pytest.mark.anyio
    async def test_delete_resource_cascades_access_rule(
        self, db_session, test_resource
    ):
        """
        Deleting resource removes its access rule.

        Given: Resource with access rule
        When: delete_resource() is called
        Then: Access rule is also deleted
        """
        # await service.delete_resource(...)

        # # Access rule should be gone
        # result = await db_session.execute(
        #     select(AccessRule).where(AccessRule.resource_id == test_resource["id"])
        # )
        # assert result.scalar_one_or_none() is None
        pass


# ============================================================================
# Access Verification Tests
# ============================================================================


class TestResourceServiceVerifyAccess:
    """Tests for resource access verification."""

    @pytest.mark.anyio
    async def test_verify_access_public_resource(self, db_session, public_resource):
        """
        Public resource grants access without token.

        Given: Public access resource
        When: verify_access() is called without token
        Then: Access is granted with content URL
        """
        # service = ResourceService(db_session)

        # result = await service.verify_access(
        #     resource_id=public_resource["id"],
        #     token=None,
        #     email=None,
        # )

        # assert result.has_access is True
        # assert result.content_url == public_resource["content_url"]
        # assert result.gate_type == "none"
        pass

    @pytest.mark.anyio
    async def test_verify_access_paid_without_payment(self, db_session, paid_resource):
        """
        Paid resource without payment returns payment URL.

        Given: Paid access resource
        When: verify_access() is called without token
        Then: Access denied, payment URL returned
        """
        # result = await service.verify_access(
        #     resource_id=paid_resource["id"],
        #     token=None,
        #     email=None,
        # )

        # assert result.has_access is False
        # assert result.content_url is None
        # assert result.gate_type == "payment"
        # assert result.payment_url is not None
        # assert "checkout.stripe.com" in result.payment_url
        pass

    @pytest.mark.anyio
    async def test_verify_access_paid_with_valid_token(self, db_session, paid_resource):
        """
        Paid resource with valid payment token grants access.

        Given: Paid resource with existing payment
        When: verify_access() is called with valid payment token
        Then: Access is granted
        """
        # Create a payment record first
        # payment = PaymentFactory.create(
        #     resource_id=paid_resource["id"],
        #     status="completed",
        # )

        # result = await service.verify_access(
        #     resource_id=paid_resource["id"],
        #     token=payment["access_token"],
        #     email=None,
        # )

        # assert result.has_access is True
        # assert result.content_url == paid_resource["content_url"]
        pass

    @pytest.mark.anyio
    async def test_verify_access_paid_with_invalid_token(
        self, db_session, paid_resource
    ):
        """
        Paid resource with invalid token denies access.

        Given: Paid access resource
        When: verify_access() is called with invalid token
        Then: Access denied, payment URL returned
        """
        # result = await service.verify_access(
        #     resource_id=paid_resource["id"],
        #     token="invalid_token_123",
        #     email=None,
        # )

        # assert result.has_access is False
        # assert result.gate_type == "payment"
        pass

    @pytest.mark.anyio
    async def test_verify_access_invite_only_valid_email(
        self, db_session, invite_resource
    ):
        """
        Invite-only resource grants access to allowed email.

        Given: Invite-only resource with allowed_emails
        When: verify_access() is called with allowed email
        Then: Access is granted
        """
        # invite_resource has allowed_emails = ["allowed@example.com", "vip@example.com"]

        # result = await service.verify_access(
        #     resource_id=invite_resource["id"],
        #     token=None,
        #     email="allowed@example.com",
        # )

        # assert result.has_access is True
        # assert result.content_url == invite_resource["content_url"]
        pass

    @pytest.mark.anyio
    async def test_verify_access_invite_only_invalid_email(
        self, db_session, invite_resource
    ):
        """
        Invite-only resource denies access to non-allowed email.

        Given: Invite-only resource
        When: verify_access() is called with non-allowed email
        Then: Access denied
        """
        # result = await service.verify_access(
        #     resource_id=invite_resource["id"],
        #     token=None,
        #     email="notallowed@example.com",
        # )

        # assert result.has_access is False
        # assert result.gate_type == "email"
        pass

    @pytest.mark.anyio
    async def test_verify_access_invite_email_case_insensitive(
        self, db_session, invite_resource
    ):
        """
        Invite email matching is case-insensitive.

        Given: Invite-only resource with lowercase email
        When: verify_access() is called with uppercase variant
        Then: Access is granted
        """
        # allowed_emails has "allowed@example.com"

        # result = await service.verify_access(
        #     resource_id=invite_resource["id"],
        #     token=None,
        #     email="ALLOWED@EXAMPLE.COM",
        # )

        # assert result.has_access is True
        pass

    @pytest.mark.anyio
    async def test_verify_access_records_access_log(self, db_session, public_resource):
        """
        Successful access is logged.

        Given: Public resource
        When: verify_access() is called
        Then: Access log record is created
        """
        # result = await service.verify_access(
        #     resource_id=public_resource["id"],
        #     accessor_ip="192.168.1.1",
        #     referrer="https://google.com",
        # )

        # # Check access log was created
        # from sqlalchemy import select
        # logs = await db_session.execute(
        #     select(ResourceAccess).where(
        #         ResourceAccess.resource_id == public_resource["id"]
        #     )
        # )
        # log = logs.scalars().first()
        # assert log is not None
        # assert log.accessor_ip == "192.168.1.1"
        pass


# ============================================================================
# Resource Listing Tests
# ============================================================================


class TestResourceServiceList:
    """Tests for resource listing functionality."""

    @pytest.mark.anyio
    async def test_list_resources_for_organization(
        self, db_session, test_organization, max_free_resources
    ):
        """
        List returns only organization's resources.

        Given: Organization with 3 resources
        When: list_resources() is called
        Then: All 3 resources are returned
        """
        # service = ResourceService(db_session)

        # result = await service.list_resources(
        #     organization_id=test_organization["id"],
        #     page=1,
        #     per_page=20,
        # )

        # assert len(result.data) == 3
        # assert result.meta.pagination.total == 3
        pass

    @pytest.mark.anyio
    async def test_list_resources_pagination(
        self, db_session, test_organization, many_resources
    ):
        """
        List supports pagination.

        Given: Organization with 25 resources
        When: list_resources() is called with per_page=10
        Then: Only 10 resources returned, pagination correct
        """
        # result = await service.list_resources(
        #     organization_id=test_organization["id"],
        #     page=1,
        #     per_page=10,
        # )

        # assert len(result.data) == 10
        # assert result.meta.pagination.page == 1
        # assert result.meta.pagination.total == 25
        # assert result.meta.pagination.total_pages == 3
        pass

    @pytest.mark.anyio
    async def test_list_resources_filter_by_type(
        self, db_session, test_organization, test_resource, test_file_resource
    ):
        """
        List can filter by resource type.

        Given: Mix of link and file resources
        When: list_resources() is called with type=file
        Then: Only file resources returned
        """
        # result = await service.list_resources(
        #     organization_id=test_organization["id"],
        #     type_filter="file",
        # )

        # assert len(result.data) == 1
        # assert all(r.type == "file" for r in result.data)
        pass

    @pytest.mark.anyio
    async def test_list_resources_filter_by_access_type(
        self, db_session, test_organization, public_resource, paid_resource
    ):
        """
        List can filter by access type.

        Given: Mix of public and paid resources
        When: list_resources() is called with access_type=paid
        Then: Only paid resources returned
        """
        # result = await service.list_resources(
        #     organization_id=test_organization["id"],
        #     access_type_filter="paid",
        # )

        # assert len(result.data) == 1
        # assert all(r.access_rule.type == "paid" for r in result.data)
        pass

    @pytest.mark.anyio
    async def test_list_resources_search(self, db_session, test_organization):
        """
        List can search by title/description.

        Given: Resources with various titles
        When: list_resources() is called with search query
        Then: Only matching resources returned
        """
        # Create resources with specific titles
        # resource1 = await service.create_resource(title="Python Tutorial")
        # resource2 = await service.create_resource(title="JavaScript Guide")
        # resource3 = await service.create_resource(title="Python Advanced")

        # result = await service.list_resources(
        #     organization_id=test_organization["id"],
        #     search="Python",
        # )

        # assert len(result.data) == 2
        # assert all("Python" in r.title for r in result.data)
        pass

    @pytest.mark.anyio
    async def test_list_resources_sort_by_created_desc(
        self, db_session, test_organization, many_resources
    ):
        """
        List sorts by created_at descending by default.

        Given: Multiple resources
        When: list_resources() is called without sort param
        Then: Resources are sorted newest first
        """
        # result = await service.list_resources(
        #     organization_id=test_organization["id"],
        # )

        # # Verify descending order
        # dates = [r.created_at for r in result.data]
        # assert dates == sorted(dates, reverse=True)
        pass

    @pytest.mark.anyio
    async def test_list_resources_excludes_deleted(
        self, db_session, test_organization, test_resource
    ):
        """
        List excludes soft-deleted resources.

        Given: Organization with deleted resource
        When: list_resources() is called
        Then: Deleted resource is not included
        """
        # Delete the resource
        # await service.delete_resource(test_resource["id"], ...)

        # result = await service.list_resources(
        #     organization_id=test_organization["id"],
        # )

        # assert test_resource["id"] not in [r.id for r in result.data]
        pass

    @pytest.mark.anyio
    async def test_list_resources_empty_organization(
        self, db_session, test_organization
    ):
        """
        List returns empty for organization with no resources.

        Given: Organization with no resources
        When: list_resources() is called
        Then: Empty list returned with correct pagination
        """
        # result = await service.list_resources(
        #     organization_id=test_organization["id"],
        # )

        # assert result.data == []
        # assert result.meta.pagination.total == 0
        pass


# ============================================================================
# Resource Statistics Tests
# ============================================================================


class TestResourceServiceStatistics:
    """Tests for resource statistics functionality."""

    @pytest.mark.anyio
    async def test_get_resource_stats(self, db_session, popular_resource):
        """
        Get resource returns statistics.

        Given: Resource with view history
        When: get_resource() is called
        Then: Response includes accurate stats
        """
        # result = await service.get_resource(
        #     resource_id=popular_resource["id"],
        #     organization_id=popular_resource["organization_id"],
        # )

        # assert result.stats.view_count > 0
        # assert result.stats.unique_viewers > 0
        pass

    @pytest.mark.anyio
    async def test_increment_view_count(self, db_session, test_resource):
        """
        View count increments on access.

        Given: Resource with 0 views
        When: Resource is accessed
        Then: View count is incremented
        """
        # initial_views = test_resource["stats"]["view_count"]

        # await service.verify_access(
        #     resource_id=test_resource["id"],
        #     accessor_ip="192.168.1.1",
        # )

        # result = await service.get_resource(test_resource["id"], ...)
        # assert result.stats.view_count == initial_views + 1
        pass

    @pytest.mark.anyio
    async def test_unique_viewers_counted_correctly(self, db_session, test_resource):
        """
        Unique viewers are counted by IP/email.

        Given: Resource accessed by same IP multiple times
        When: Stats are retrieved
        Then: Unique viewers = 1, total views > 1
        """
        # Access same resource 5 times from same IP
        # for _ in range(5):
        #     await service.verify_access(
        #         resource_id=test_resource["id"],
        #         accessor_ip="192.168.1.1",
        #     )

        # result = await service.get_resource(test_resource["id"], ...)
        # assert result.stats.view_count == 5
        # assert result.stats.unique_viewers == 1
        pass


# ============================================================================
# Multi-tenancy Tests
# ============================================================================


class TestResourceServiceMultiTenancy:
    """Tests for multi-tenancy isolation."""

    @pytest.mark.anyio
    async def test_get_resource_different_org_not_found(
        self, db_session, test_resource, another_organization
    ):
        """
        Cannot get resource from different organization.

        Given: Resource belongs to org A
        When: get_resource() is called with org B context
        Then: NotFoundError is raised
        """
        # from src.gateco.utils.errors import NotFoundError

        # with pytest.raises(NotFoundError):
        #     await service.get_resource(
        #         resource_id=test_resource["id"],
        #         organization_id=another_organization["id"],
        #     )
        pass

    @pytest.mark.anyio
    async def test_list_resources_only_own_organization(
        self, db_session, test_organization, another_organization
    ):
        """
        List only returns own organization's resources.

        Given: Resources in both org A and org B
        When: list_resources() is called for org A
        Then: Only org A resources returned
        """
        # Create resource in another org
        # await service.create_resource(organization_id=another_organization["id"], ...)

        # result = await service.list_resources(
        #     organization_id=test_organization["id"],
        # )

        # # All results should be from test_organization
        # for resource in result.data:
        #     assert resource.organization_id == test_organization["id"]
        pass
