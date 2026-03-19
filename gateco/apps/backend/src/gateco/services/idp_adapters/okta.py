"""Okta IDP adapter — fetches users and groups via Okta Management API."""

from __future__ import annotations

import logging

import httpx

from gateco.services.idp_adapters.base import (
    BaseIDPAdapter, SyncResult, SyncedGroup, SyncedPrincipal,
)

logger = logging.getLogger(__name__)

TIMEOUT = 15.0
MAX_PAGES = 10  # Safety bound


class OktaAdapter(BaseIDPAdapter):
    """Sync users and groups from Okta via REST API."""

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.domain = config["domain"]
        self.api_token = config["api_token"]
        self.base_url = f"https://{self.domain}/api/v1"
        self.headers = {
            "Authorization": f"SSWS {self.api_token}",
            "Accept": "application/json",
        }

    async def sync(self) -> SyncResult:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            users = await self._fetch_users(client)
            groups, group_members = await self._fetch_groups(client)

        # Map group memberships onto principals
        principals = []
        for u in users:
            profile = u.get("profile", {})
            uid = u["id"]
            user_groups = [
                gname for gid, gname in groups.items()
                if uid in group_members.get(gid, set())
            ]
            principals.append(SyncedPrincipal(
                external_id=uid,
                display_name=f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip()
                             or profile.get("login", uid),
                email=profile.get("email"),
                groups=user_groups,
                roles=[],
                attributes={
                    k: v for k, v in {
                        "department": profile.get("department"),
                        "organization": profile.get("organization"),
                        "title": profile.get("title"),
                    }.items() if v
                },
            ))

        synced_groups = [
            SyncedGroup(
                external_id=gid,
                name=gname,
                member_count=len(group_members.get(gid, set())),
            )
            for gid, gname in groups.items()
        ]

        return SyncResult(principals=principals, groups=synced_groups)

    async def _fetch_users(self, client: httpx.AsyncClient) -> list[dict]:
        """Paginate through Okta users."""
        users: list[dict] = []
        url = f"{self.base_url}/users?limit=200"
        for _ in range(MAX_PAGES):
            resp = await client.get(url, headers=self.headers)
            resp.raise_for_status()
            users.extend(resp.json())
            next_url = self._parse_next_link(resp.headers.get("link", ""))
            if not next_url:
                break
            url = next_url
        return users

    async def _fetch_groups(self, client: httpx.AsyncClient) -> tuple[dict[str, str], dict[str, set[str]]]:
        """Fetch all groups and their member user IDs."""
        groups: dict[str, str] = {}
        members: dict[str, set[str]] = {}

        url = f"{self.base_url}/groups?limit=200"
        for _ in range(MAX_PAGES):
            resp = await client.get(url, headers=self.headers)
            resp.raise_for_status()
            for g in resp.json():
                gid = g["id"]
                gname = g.get("profile", {}).get("name", gid)
                groups[gid] = gname
                members[gid] = set()
            next_url = self._parse_next_link(resp.headers.get("link", ""))
            if not next_url:
                break
            url = next_url

        for gid in groups:
            url = f"{self.base_url}/groups/{gid}/users?limit=200"
            for _ in range(MAX_PAGES):
                resp = await client.get(url, headers=self.headers)
                resp.raise_for_status()
                for u in resp.json():
                    members[gid].add(u["id"])
                next_url = self._parse_next_link(resp.headers.get("link", ""))
                if not next_url:
                    break
                url = next_url

        return groups, members

    @staticmethod
    def _parse_next_link(link_header: str) -> str | None:
        """Parse Okta Link header for rel='next'."""
        for part in link_header.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
                return url
        return None
