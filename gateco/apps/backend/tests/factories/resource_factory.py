"""Factory for creating test resources and access rules."""

from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional
from enum import Enum


class ResourceType(str, Enum):
    """Types of gated resources."""
    LINK = "link"
    FILE = "file"
    VIDEO = "video"


class AccessType(str, Enum):
    """Types of access control."""
    PUBLIC = "public"
    PAID = "paid"
    INVITE_ONLY = "invite_only"


class ResourceFactory:
    """Factory for creating test resources."""

    @staticmethod
    def create(
        organization_id: str = None,
        created_by: str = None,
        resource_type: ResourceType = ResourceType.LINK,
        title: str = "Test Resource",
        description: str = "A test gated resource",
        content_url: str = "https://example.com/content",
        thumbnail_url: Optional[str] = None,
    ) -> dict:
        """
        Create a test resource dict.

        Args:
            organization_id: Owning organization ID
            created_by: User ID who created the resource
            resource_type: Type of resource
            title: Resource title
            description: Resource description
            content_url: URL to the gated content
            thumbnail_url: Optional thumbnail URL

        Returns:
            dict: Resource data ready for model creation
        """
        resource_id = uuid4()
        return {
            "id": resource_id,
            "organization_id": organization_id or uuid4(),
            "created_by": created_by,
            "type": resource_type.value,
            "title": title,
            "description": description,
            "content_url": content_url,
            "thumbnail_url": thumbnail_url,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

    @staticmethod
    def create_with_access_rule(
        organization_id: str = None,
        created_by: str = None,
        resource_type: ResourceType = ResourceType.LINK,
        title: str = "Test Resource",
        access_type: AccessType = AccessType.PUBLIC,
        price_cents: Optional[int] = None,
        currency: str = "USD",
        allowed_emails: Optional[list[str]] = None,
        **kwargs,
    ) -> tuple[dict, dict]:
        """
        Create a test resource with its access rule.

        Args:
            organization_id: Owning organization ID
            created_by: User ID who created the resource
            resource_type: Type of resource
            title: Resource title
            access_type: Type of access control
            price_cents: Price in cents (for paid access)
            currency: Currency code (for paid access)
            allowed_emails: List of allowed emails (for invite-only)

        Returns:
            Tuple of (resource_dict, access_rule_dict)
        """
        resource = ResourceFactory.create(
            organization_id=organization_id,
            created_by=created_by,
            resource_type=resource_type,
            title=title,
            **kwargs,
        )

        access_rule = AccessRuleFactory.create(
            resource_id=resource["id"],
            access_type=access_type,
            price_cents=price_cents,
            currency=currency,
            allowed_emails=allowed_emails,
        )

        return resource, access_rule


class AccessRuleFactory:
    """Factory for creating test access rules."""

    @staticmethod
    def create(
        resource_id: str = None,
        access_type: AccessType = AccessType.PUBLIC,
        price_cents: Optional[int] = None,
        currency: str = "USD",
        allowed_emails: Optional[list[str]] = None,
    ) -> dict:
        """
        Create a test access rule dict.

        Args:
            resource_id: Associated resource ID
            access_type: Type of access control
            price_cents: Price in cents (for paid access)
            currency: Currency code (for paid access)
            allowed_emails: List of allowed emails (for invite-only)

        Returns:
            dict: Access rule data ready for model creation
        """
        rule_id = uuid4()

        # Set defaults based on access type
        if access_type == AccessType.PAID and price_cents is None:
            price_cents = 999  # $9.99 default
        elif access_type == AccessType.INVITE_ONLY and allowed_emails is None:
            allowed_emails = ["allowed@example.com"]

        return {
            "id": rule_id,
            "resource_id": resource_id or uuid4(),
            "type": access_type.value,
            "price_cents": price_cents if access_type == AccessType.PAID else None,
            "currency": currency if access_type == AccessType.PAID else None,
            "allowed_emails": allowed_emails if access_type == AccessType.INVITE_ONLY else None,
            "created_at": datetime.now(timezone.utc),
        }


class ResourceAccessFactory:
    """Factory for creating test resource access records."""

    @staticmethod
    def create(
        resource_id: str = None,
        accessor_email: Optional[str] = None,
        accessor_ip: str = "127.0.0.1",
        referrer: Optional[str] = None,
        country: str = "US",
        payment_id: Optional[str] = None,
    ) -> dict:
        """
        Create a test resource access record.

        Args:
            resource_id: Accessed resource ID
            accessor_email: Email of accessor (if known)
            accessor_ip: IP address of accessor
            referrer: Referrer URL
            country: Country code
            payment_id: Associated payment ID (for paid access)

        Returns:
            dict: Resource access data
        """
        access_id = uuid4()
        return {
            "id": access_id,
            "resource_id": resource_id or uuid4(),
            "accessor_email": accessor_email,
            "accessor_ip": accessor_ip,
            "referrer": referrer,
            "country": country,
            "payment_id": payment_id,
            "created_at": datetime.now(timezone.utc),
        }


class InviteFactory:
    """Factory for creating test invites."""

    @staticmethod
    def create(
        resource_id: str = None,
        email: str = "invited@example.com",
        used: bool = False,
        expires_in_days: int = 7,
    ) -> dict:
        """
        Create a test invite dict.

        Args:
            resource_id: Resource the invite is for
            email: Invited email address
            used: Whether the invite has been used
            expires_in_days: Days until expiration

        Returns:
            dict: Invite data
        """
        from datetime import timedelta
        import secrets

        invite_id = uuid4()
        return {
            "id": invite_id,
            "resource_id": resource_id or uuid4(),
            "email": email,
            "token": secrets.token_urlsafe(32),
            "used": used,
            "expires_at": datetime.now(timezone.utc) + timedelta(days=expires_in_days),
            "created_at": datetime.now(timezone.utc),
        }
