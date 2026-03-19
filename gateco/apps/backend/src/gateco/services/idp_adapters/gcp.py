"""GCP Cloud Identity adapter — fetches users and groups via Admin SDK."""

from __future__ import annotations

import asyncio
import json
import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build

from gateco.services.idp_adapters.base import (
    BaseIDPAdapter, SyncResult, SyncedGroup, SyncedPrincipal,
)

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.user.readonly",
    "https://www.googleapis.com/auth/admin.directory.group.readonly",
    "https://www.googleapis.com/auth/admin.directory.group.member.readonly",
]


class GCPAdapter(BaseIDPAdapter):
    """Sync users and groups from Google Workspace / Cloud Identity via Admin SDK."""

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.domain = config["domain"]
        self.admin_email = config["admin_email"]

        sa_json = config["service_account_json"]
        if isinstance(sa_json, str):
            sa_json = json.loads(sa_json)

        creds = service_account.Credentials.from_service_account_info(
            sa_json, scopes=SCOPES
        )
        self.creds = creds.with_subject(self.admin_email)

    async def sync(self) -> SyncResult:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_all)

    def _sync_all(self) -> SyncResult:
        """Run all API calls synchronously with a single service instance."""
        service = build("admin", "directory_v1", credentials=self.creds)

        users_raw = self._list_users(service)
        groups_raw = self._list_groups(service)

        group_members: dict[str, set[str]] = {}
        for g in groups_raw:
            gemail = g["email"]
            group_members[gemail] = self._list_group_members(service, gemail)

        principals = []
        for u in users_raw:
            uid = u["id"]
            email = u.get("primaryEmail", "")
            user_groups = [
                g.get("name", g["email"])
                for g in groups_raw
                if email in group_members.get(g["email"], set())
            ]
            orgs = u.get("organizations", [{}])
            org = orgs[0] if orgs else {}
            principals.append(SyncedPrincipal(
                external_id=uid,
                display_name=u.get("name", {}).get("fullName", email),
                email=email,
                groups=user_groups,
                roles=[],
                attributes={
                    k: v for k, v in {
                        "department": org.get("department"),
                        "title": org.get("title"),
                    }.items() if v
                },
            ))

        synced_groups = [
            SyncedGroup(
                external_id=g["id"],
                name=g.get("name", g["email"]),
                member_count=len(group_members.get(g["email"], set())),
            )
            for g in groups_raw
        ]

        return SyncResult(principals=principals, groups=synced_groups)

    def _list_users(self, service) -> list[dict]:
        users: list[dict] = []
        request = service.users().list(domain=self.domain, maxResults=500)
        while request:
            resp = request.execute()
            users.extend(resp.get("users", []))
            request = service.users().list_next(request, resp)
        return users

    def _list_groups(self, service) -> list[dict]:
        groups: list[dict] = []
        request = service.groups().list(domain=self.domain, maxResults=200)
        while request:
            resp = request.execute()
            groups.extend(resp.get("groups", []))
            request = service.groups().list_next(request, resp)
        return groups

    def _list_group_members(self, service, group_email: str) -> set[str]:
        members: set[str] = set()
        try:
            request = service.members().list(groupKey=group_email, maxResults=200)
            while request:
                resp = request.execute()
                for m in resp.get("members", []):
                    members.add(m.get("email", ""))
                request = service.members().list_next(request, resp)
        except Exception as exc:
            logger.warning("Failed to list members for group %s: %s", group_email, exc)
        return members
