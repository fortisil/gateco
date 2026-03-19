"""AWS IAM Identity Center adapter — fetches users and groups via Identity Store API."""

from __future__ import annotations

import asyncio
import logging
from functools import partial

import boto3

from gateco.services.idp_adapters.base import (
    BaseIDPAdapter, SyncResult, SyncedGroup, SyncedPrincipal,
)

logger = logging.getLogger(__name__)


class AWSIAMAdapter(BaseIDPAdapter):
    """Sync users and groups from AWS IAM Identity Center."""

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.identity_store_id = config["identity_store_id"]
        self.client = boto3.client(
            "identitystore",
            region_name=config.get("region", "us-east-1"),
            aws_access_key_id=config.get("aws_access_key_id"),
            aws_secret_access_key=config.get("aws_secret_access_key"),
        )

    async def sync(self) -> SyncResult:
        loop = asyncio.get_running_loop()

        users_raw = await loop.run_in_executor(None, self._list_users)
        groups_raw = await loop.run_in_executor(None, self._list_groups)

        group_map: dict[str, str] = {g["GroupId"]: g["DisplayName"] for g in groups_raw}
        user_groups: dict[str, list[str]] = {}

        for u in users_raw:
            uid = u["UserId"]
            memberships = await loop.run_in_executor(
                None, partial(self._get_user_groups, uid)
            )
            user_groups[uid] = [
                group_map[gid] for gid in memberships if gid in group_map
            ]

        principals = []
        for u in users_raw:
            uid = u["UserId"]
            name_obj = u.get("Name", {})
            display = u.get("DisplayName") or f"{name_obj.get('GivenName', '')} {name_obj.get('FamilyName', '')}".strip() or u.get("UserName", uid)
            emails = u.get("Emails", [])
            email = next((e["Value"] for e in emails if e.get("Primary")), emails[0]["Value"] if emails else None)
            principals.append(SyncedPrincipal(
                external_id=uid,
                display_name=display,
                email=email,
                groups=user_groups.get(uid, []),
                roles=[],
                # Gateco test convention: AWS Identity Store has no native "department"
                # field. The UserType field is used to store department for test data.
                attributes={
                    k: v for k, v in {
                        "title": u.get("Title"),
                        "department": u.get("UserType"),
                    }.items() if v
                },
            ))

        synced_groups = [
            SyncedGroup(
                external_id=g["GroupId"],
                name=g["DisplayName"],
                member_count=sum(
                    1 for uid_groups in user_groups.values()
                    if g["DisplayName"] in uid_groups
                ),
            )
            for g in groups_raw
        ]

        return SyncResult(principals=principals, groups=synced_groups)

    def _list_users(self) -> list[dict]:
        users: list[dict] = []
        paginator = self.client.get_paginator("list_users")
        for page in paginator.paginate(IdentityStoreId=self.identity_store_id):
            users.extend(page.get("Users", []))
        return users

    def _list_groups(self) -> list[dict]:
        groups: list[dict] = []
        paginator = self.client.get_paginator("list_groups")
        for page in paginator.paginate(IdentityStoreId=self.identity_store_id):
            groups.extend(page.get("Groups", []))
        return groups

    def _get_user_groups(self, user_id: str) -> list[str]:
        group_ids: list[str] = []
        paginator = self.client.get_paginator("list_group_memberships_for_member")
        for page in paginator.paginate(
            IdentityStoreId=self.identity_store_id,
            MemberId={"UserId": user_id},
        ):
            for m in page.get("GroupMemberships", []):
                group_ids.append(m["GroupId"])
        return group_ids
