"""Azure Entra ID adapter — fetches users and groups via Microsoft Graph API."""

from __future__ import annotations

import logging

import httpx

from gateco.services.idp_adapters.base import (
    BaseIDPAdapter, SyncResult, SyncedGroup, SyncedPrincipal,
)

logger = logging.getLogger(__name__)

TIMEOUT = 15.0
MAX_PAGES = 10
GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class AzureEntraAdapter(BaseIDPAdapter):
    """Sync users and groups from Azure Entra ID via MS Graph API."""

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.tenant_id = config["tenant_id"]
        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]

    async def sync(self) -> SyncResult:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            token = await self._get_token(client)
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

            users = await self._fetch_users(client, headers)
            groups, group_members = await self._fetch_groups(client, headers)

        principals = []
        for u in users:
            uid = u["id"]
            user_groups = [
                gname for gid, gname in groups.items()
                if uid in group_members.get(gid, set())
            ]
            principals.append(SyncedPrincipal(
                external_id=uid,
                display_name=u.get("displayName", uid),
                email=u.get("mail"),
                groups=user_groups,
                roles=[],
                attributes={
                    k: v for k, v in {
                        "department": u.get("department"),
                        "title": u.get("jobTitle"),
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

    async def _get_token(self, client: httpx.AsyncClient) -> str:
        """Acquire OAuth2 token via client credentials flow."""
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        resp = await client.post(url, data={
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default",
        })
        resp.raise_for_status()
        return resp.json()["access_token"]

    async def _fetch_users(self, client: httpx.AsyncClient, headers: dict) -> list[dict]:
        users: list[dict] = []
        url = f"{GRAPH_BASE}/users?$select=id,displayName,mail,department,jobTitle&$top=999"
        for _ in range(MAX_PAGES):
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            users.extend(data.get("value", []))
            url = data.get("@odata.nextLink")
            if not url:
                break
        return users

    async def _fetch_groups(self, client: httpx.AsyncClient, headers: dict) -> tuple[dict[str, str], dict[str, set[str]]]:
        groups: dict[str, str] = {}
        members: dict[str, set[str]] = {}

        url = f"{GRAPH_BASE}/groups?$select=id,displayName&$top=999"
        for _ in range(MAX_PAGES):
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            for g in data.get("value", []):
                gid = g["id"]
                groups[gid] = g.get("displayName", gid)
                members[gid] = set()
            url = data.get("@odata.nextLink")
            if not url:
                break

        for gid in groups:
            url = f"{GRAPH_BASE}/groups/{gid}/members?$select=id"
            for _ in range(MAX_PAGES):
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                for m in data.get("value", []):
                    members[gid].add(m["id"])
                url = data.get("@odata.nextLink")
                if not url:
                    break

        return groups, members
