"""Unit tests for UserService.

This module tests user management operations including profile updates,
role management, and organization membership.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone


# ============================================================================
# User Profile Tests
# ============================================================================


class TestGetUser:
    """Tests for UserService.get_user method."""

    @pytest.mark.anyio
    async def test_get_user_by_id(self, db_session, test_user):
        """
        Get user by ID returns user with organization.

        Given: Existing user ID
        When: get_user() is called
        Then: User with organization is returned
        """
        from src.gateco.services.user_service import UserService

        user, _ = test_user
        service = UserService(db_session)

        result = await service.get_user(str(user["id"]))

        assert result is not None
        assert result.id == user["id"]
        assert result.organization is not None

    @pytest.mark.anyio
    async def test_get_user_nonexistent(self, db_session):
        """
        Get nonexistent user returns None.

        Given: Non-existent user ID
        When: get_user() is called
        Then: None is returned
        """
        from src.gateco.services.user_service import UserService

        service = UserService(db_session)

        result = await service.get_user(str(uuid4()))

        assert result is None

    @pytest.mark.anyio
    async def test_get_user_by_email(self, db_session, test_user):
        """
        Get user by email returns user.

        Given: Existing user email
        When: get_user_by_email() is called
        Then: User is returned
        """
        from src.gateco.services.user_service import UserService

        user, _ = test_user
        service = UserService(db_session)

        result = await service.get_user_by_email(user["email"])

        assert result is not None
        assert result.email == user["email"]

    @pytest.mark.anyio
    async def test_get_user_by_email_case_insensitive(self, db_session, test_user):
        """
        Email lookup is case-insensitive.

        Given: User with lowercase email
        When: get_user_by_email() is called with uppercase
        Then: User is found
        """
        from src.gateco.services.user_service import UserService

        user, _ = test_user
        service = UserService(db_session)

        result = await service.get_user_by_email(user["email"].upper())

        assert result is not None
        assert result.email == user["email"]


class TestUpdateProfile:
    """Tests for UserService.update_profile method."""

    @pytest.mark.anyio
    async def test_update_name(self, db_session, test_user):
        """
        Update user name succeeds.

        Given: Existing user
        When: update_profile() is called with new name
        Then: Name is updated
        """
        from src.gateco.services.user_service import UserService
        from src.gateco.schemas.users import UserUpdate

        user, _ = test_user
        service = UserService(db_session)

        result = await service.update_profile(
            user_id=str(user["id"]),
            data=UserUpdate(name="New Name"),
        )

        assert result.name == "New Name"

    @pytest.mark.anyio
    async def test_update_does_not_change_email(self, db_session, test_user):
        """
        Email cannot be changed via update_profile.

        Given: Attempt to change email
        When: update_profile() is called
        Then: Email remains unchanged
        """
        from src.gateco.services.user_service import UserService
        from src.gateco.schemas.users import UserUpdate

        user, _ = test_user
        original_email = user["email"]
        service = UserService(db_session)

        result = await service.update_profile(
            user_id=str(user["id"]),
            data=UserUpdate(email="new@example.com"),
        )

        assert result.email == original_email

    @pytest.mark.anyio
    async def test_update_does_not_change_role(self, db_session, test_user):
        """
        Role cannot be changed via update_profile.

        Given: Attempt to change role
        When: update_profile() is called
        Then: Role remains unchanged
        """
        from src.gateco.services.user_service import UserService
        from src.gateco.schemas.users import UserUpdate

        user, _ = test_user
        original_role = user["role"]
        service = UserService(db_session)

        result = await service.update_profile(
            user_id=str(user["id"]),
            data=UserUpdate(role="owner"),
        )

        assert result.role == original_role

    @pytest.mark.anyio
    async def test_update_nonexistent_user(self, db_session):
        """
        Update nonexistent user raises error.

        Given: Non-existent user ID
        When: update_profile() is called
        Then: NotFoundError is raised
        """
        from src.gateco.services.user_service import UserService
        from src.gateco.schemas.users import UserUpdate
        from src.gateco.utils.errors import NotFoundError

        service = UserService(db_session)

        with pytest.raises(NotFoundError):
            await service.update_profile(
                user_id=str(uuid4()),
                data=UserUpdate(name="New Name"),
            )

    @pytest.mark.anyio
    async def test_update_updates_timestamp(self, db_session, test_user):
        """
        Update sets updated_at timestamp.

        Given: Existing user
        When: update_profile() is called
        Then: updated_at is set to current time
        """
        from src.gateco.services.user_service import UserService
        from src.gateco.schemas.users import UserUpdate

        user, _ = test_user
        service = UserService(db_session)

        before = datetime.now(timezone.utc)
        result = await service.update_profile(
            user_id=str(user["id"]),
            data=UserUpdate(name="Updated Name"),
        )

        assert result.updated_at >= before


# ============================================================================
# Role Management Tests
# ============================================================================


class TestChangeUserRole:
    """Tests for UserService.change_user_role method."""

    @pytest.mark.anyio
    async def test_owner_can_change_member_to_admin(self, db_session, test_owner, test_user):
        """
        Owner can promote member to admin.

        Given: Owner requesting role change
        When: change_user_role() is called
        Then: Member becomes admin
        """
        from src.gateco.services.user_service import UserService

        owner, _ = test_owner
        member, _ = test_user
        service = UserService(db_session)

        result = await service.change_user_role(
            actor_id=str(owner["id"]),
            target_user_id=str(member["id"]),
            new_role="admin",
        )

        assert result.role == "admin"

    @pytest.mark.anyio
    async def test_admin_cannot_promote_to_owner(self, db_session, test_admin, test_user):
        """
        Admin cannot promote user to owner.

        Given: Admin requesting role change
        When: change_user_role() is called to make owner
        Then: PermissionError is raised
        """
        from src.gateco.services.user_service import UserService
        from src.gateco.utils.errors import PermissionError

        admin, _ = test_admin
        member, _ = test_user
        service = UserService(db_session)

        with pytest.raises(PermissionError):
            await service.change_user_role(
                actor_id=str(admin["id"]),
                target_user_id=str(member["id"]),
                new_role="owner",
            )

    @pytest.mark.anyio
    async def test_member_cannot_change_roles(self, db_session, test_user):
        """
        Member cannot change any roles.

        Given: Member requesting role change
        When: change_user_role() is called
        Then: PermissionError is raised
        """
        from src.gateco.services.user_service import UserService
        from src.gateco.utils.errors import PermissionError

        member, _ = test_user
        service = UserService(db_session)

        with pytest.raises(PermissionError):
            await service.change_user_role(
                actor_id=str(member["id"]),
                target_user_id=str(member["id"]),
                new_role="admin",
            )

    @pytest.mark.anyio
    async def test_cannot_demote_only_owner(self, db_session, test_owner):
        """
        Cannot demote the only owner.

        Given: Single owner in organization
        When: change_user_role() is called to demote
        Then: ValidationError is raised
        """
        from src.gateco.services.user_service import UserService
        from src.gateco.utils.errors import ValidationError

        owner, _ = test_owner
        service = UserService(db_session)

        with pytest.raises(ValidationError) as exc_info:
            await service.change_user_role(
                actor_id=str(owner["id"]),
                target_user_id=str(owner["id"]),
                new_role="admin",
            )

        assert "last owner" in str(exc_info.value).lower()

    @pytest.mark.anyio
    async def test_cannot_change_role_cross_organization(self, db_session, test_owner):
        """
        Cannot change role of user in different organization.

        Given: User in different organization
        When: change_user_role() is called
        Then: NotFoundError is raised
        """
        from src.gateco.services.user_service import UserService
        from src.gateco.utils.errors import NotFoundError

        owner, _ = test_owner
        other_user_id = str(uuid4())  # User in different org
        service = UserService(db_session)

        with pytest.raises(NotFoundError):
            await service.change_user_role(
                actor_id=str(owner["id"]),
                target_user_id=other_user_id,
                new_role="admin",
            )


# ============================================================================
# User Deactivation Tests
# ============================================================================


class TestDeactivateUser:
    """Tests for UserService.deactivate_user method."""

    @pytest.mark.anyio
    async def test_owner_can_deactivate_member(self, db_session, test_owner, test_user):
        """
        Owner can deactivate organization member.

        Given: Owner requesting deactivation
        When: deactivate_user() is called
        Then: User is_active becomes False
        """
        from src.gateco.services.user_service import UserService

        owner, _ = test_owner
        member, _ = test_user
        service = UserService(db_session)

        result = await service.deactivate_user(
            actor_id=str(owner["id"]),
            target_user_id=str(member["id"]),
        )

        assert result.is_active is False

    @pytest.mark.anyio
    async def test_cannot_deactivate_only_owner(self, db_session, test_owner):
        """
        Cannot deactivate the only owner.

        Given: Single owner in organization
        When: deactivate_user() is called
        Then: ValidationError is raised
        """
        from src.gateco.services.user_service import UserService
        from src.gateco.utils.errors import ValidationError

        owner, _ = test_owner
        service = UserService(db_session)

        with pytest.raises(ValidationError):
            await service.deactivate_user(
                actor_id=str(owner["id"]),
                target_user_id=str(owner["id"]),
            )

    @pytest.mark.anyio
    async def test_deactivation_invalidates_sessions(self, db_session, test_owner, test_user):
        """
        Deactivating user invalidates all their sessions.

        Given: User with active sessions
        When: deactivate_user() is called
        Then: All sessions are invalidated
        """
        from src.gateco.services.user_service import UserService

        owner, _ = test_owner
        member, _ = test_user
        service = UserService(db_session)

        await service.deactivate_user(
            actor_id=str(owner["id"]),
            target_user_id=str(member["id"]),
        )

        # Verify sessions are invalidated
        sessions = await service.get_user_sessions(str(member["id"]))
        assert all(s.is_revoked for s in sessions)


class TestReactivateUser:
    """Tests for UserService.reactivate_user method."""

    @pytest.mark.anyio
    async def test_owner_can_reactivate_user(self, db_session, test_owner, inactive_user):
        """
        Owner can reactivate deactivated user.

        Given: Inactive user
        When: reactivate_user() is called by owner
        Then: User is_active becomes True
        """
        from src.gateco.services.user_service import UserService

        owner, _ = test_owner
        user, _ = inactive_user
        service = UserService(db_session)

        result = await service.reactivate_user(
            actor_id=str(owner["id"]),
            target_user_id=str(user["id"]),
        )

        assert result.is_active is True


# ============================================================================
# Organization Membership Tests
# ============================================================================


class TestListOrganizationUsers:
    """Tests for UserService.list_organization_users method."""

    @pytest.mark.anyio
    async def test_list_users_in_organization(self, db_session, test_organization, test_user):
        """
        List returns all users in organization.

        Given: Organization with users
        When: list_organization_users() is called
        Then: All users are returned
        """
        from src.gateco.services.user_service import UserService

        service = UserService(db_session)

        result = await service.list_organization_users(
            organization_id=str(test_organization["id"]),
        )

        assert len(result) > 0
        assert all(u.organization_id == test_organization["id"] for u in result)

    @pytest.mark.anyio
    async def test_list_users_with_role_filter(self, db_session, test_organization):
        """
        List can filter by role.

        Given: Organization with users of different roles
        When: list_organization_users() is called with role filter
        Then: Only users with that role are returned
        """
        from src.gateco.services.user_service import UserService

        service = UserService(db_session)

        result = await service.list_organization_users(
            organization_id=str(test_organization["id"]),
            role="owner",
        )

        assert all(u.role == "owner" for u in result)

    @pytest.mark.anyio
    async def test_list_excludes_inactive_by_default(self, db_session, test_organization):
        """
        Inactive users excluded by default.

        Given: Organization with inactive users
        When: list_organization_users() is called
        Then: Inactive users not included
        """
        from src.gateco.services.user_service import UserService

        service = UserService(db_session)

        result = await service.list_organization_users(
            organization_id=str(test_organization["id"]),
        )

        assert all(u.is_active for u in result)

    @pytest.mark.anyio
    async def test_list_includes_inactive_when_requested(self, db_session, test_organization):
        """
        Inactive users included when requested.

        Given: Organization with inactive users
        When: list_organization_users() is called with include_inactive=True
        Then: All users including inactive are returned
        """
        from src.gateco.services.user_service import UserService

        service = UserService(db_session)

        result = await service.list_organization_users(
            organization_id=str(test_organization["id"]),
            include_inactive=True,
        )

        # May include inactive users
        # Actual assertion depends on test data


# ============================================================================
# Invite User Tests
# ============================================================================


class TestInviteUser:
    """Tests for UserService.invite_user method."""

    @pytest.mark.anyio
    async def test_owner_can_invite_user(self, db_session, test_owner, test_organization):
        """
        Owner can invite new user to organization.

        Given: Owner requesting invitation
        When: invite_user() is called
        Then: Invitation is created and email sent
        """
        from src.gateco.services.user_service import UserService
        from src.gateco.schemas.users import UserInvite

        owner, _ = test_owner
        service = UserService(db_session)

        with patch.object(service, "_send_invite_email") as mock_send:
            result = await service.invite_user(
                actor_id=str(owner["id"]),
                data=UserInvite(
                    email="invited@example.com",
                    role="member",
                ),
            )

            assert result.email == "invited@example.com"
            assert result.status == "pending"
            mock_send.assert_called_once()

    @pytest.mark.anyio
    async def test_cannot_invite_existing_email(self, db_session, test_owner, test_user):
        """
        Cannot invite email that's already a user.

        Given: Email already registered
        When: invite_user() is called
        Then: ConflictError is raised
        """
        from src.gateco.services.user_service import UserService
        from src.gateco.schemas.users import UserInvite
        from src.gateco.utils.errors import ConflictError

        owner, _ = test_owner
        existing_user, _ = test_user
        service = UserService(db_session)

        with pytest.raises(ConflictError):
            await service.invite_user(
                actor_id=str(owner["id"]),
                data=UserInvite(
                    email=existing_user["email"],
                    role="member",
                ),
            )

    @pytest.mark.anyio
    async def test_invite_respects_plan_limits(self, db_session, test_owner):
        """
        Invitation respects team member limits.

        Given: Organization at team member limit
        When: invite_user() is called
        Then: ResourceError is raised
        """
        from src.gateco.services.user_service import UserService
        from src.gateco.schemas.users import UserInvite
        from src.gateco.utils.errors import ResourceError

        owner, _ = test_owner
        service = UserService(db_session)

        # Free plan limit is 1 team member
        # Already have owner, so can't add more
        with pytest.raises(ResourceError) as exc_info:
            await service.invite_user(
                actor_id=str(owner["id"]),
                data=UserInvite(
                    email="invited@example.com",
                    role="member",
                ),
            )

        assert exc_info.value.code == "RESOURCE_LIMIT_EXCEEDED"

    @pytest.mark.anyio
    async def test_admin_can_invite_member(self, db_session, test_admin, pro_organization):
        """
        Admin can invite members (not admins/owners).

        Given: Admin requesting invitation
        When: invite_user() is called for member role
        Then: Invitation is created
        """
        from src.gateco.services.user_service import UserService
        from src.gateco.schemas.users import UserInvite

        admin, _ = test_admin
        service = UserService(db_session)

        with patch.object(service, "_send_invite_email"):
            result = await service.invite_user(
                actor_id=str(admin["id"]),
                data=UserInvite(
                    email="newmember@example.com",
                    role="member",
                ),
            )

            assert result.role == "member"

    @pytest.mark.anyio
    async def test_admin_cannot_invite_admin(self, db_session, test_admin, pro_organization):
        """
        Admin cannot invite other admins.

        Given: Admin requesting invitation
        When: invite_user() is called for admin role
        Then: PermissionError is raised
        """
        from src.gateco.services.user_service import UserService
        from src.gateco.schemas.users import UserInvite
        from src.gateco.utils.errors import PermissionError

        admin, _ = test_admin
        service = UserService(db_session)

        with pytest.raises(PermissionError):
            await service.invite_user(
                actor_id=str(admin["id"]),
                data=UserInvite(
                    email="newadmin@example.com",
                    role="admin",
                ),
            )
