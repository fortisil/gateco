#!/usr/bin/env python3
"""Idempotent seed script for Okta test data used by the validation harness.

Provisions 5 test users and 2 groups in an Okta org via the Management API.
Uses SSWS API token auth (MVP). Structured to allow future migration to
OAuth 2.0 service-app auth (Okta's recommended long-term model).

Usage:
    python scripts/seed_okta.py --domain dev-12345.okta.com --api-token 00abc...
    python scripts/seed_okta.py --domain dev-12345.okta.com --api-token 00abc... --teardown
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

import click
import httpx

# ---------------------------------------------------------------------------
# Test data contract
# ---------------------------------------------------------------------------

TEST_USERS = [
    {"login_prefix": "vh-alice", "firstName": "Alice", "lastName": "Eng", "department": "engineering", "group": "engineering"},
    {"login_prefix": "vh-bob", "firstName": "Bob", "lastName": "Eng", "department": "engineering", "group": "engineering"},
    {"login_prefix": "vh-carol", "firstName": "Carol", "lastName": "Eng", "department": "engineering", "group": "engineering"},
    {"login_prefix": "vh-dave", "firstName": "Dave", "lastName": "Mkt", "department": "marketing", "group": "marketing"},
    {"login_prefix": "vh-eve", "firstName": "Eve", "lastName": "Mkt", "department": "marketing", "group": "marketing"},
]

TEST_GROUPS = ["engineering", "marketing"]


# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------

@dataclass
class SeedStats:
    users_created: int = 0
    users_existing: int = 0
    groups_created: int = 0
    groups_existing: int = 0
    memberships_added: int = 0
    memberships_existing: int = 0
    users_deleted: int = 0
    groups_deleted: int = 0


# ---------------------------------------------------------------------------
# Okta API helpers
# ---------------------------------------------------------------------------

class OktaClient:
    """Thin wrapper around Okta Management API v1."""

    def __init__(self, domain: str, api_token: str) -> None:
        self.base_url = f"https://{domain}/api/v1"
        self.client = httpx.Client(
            headers={
                "Authorization": f"SSWS {api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    def _get(self, path: str, params: dict | None = None) -> httpx.Response:
        resp = self.client.get(f"{self.base_url}{path}", params=params or {})
        resp.raise_for_status()
        return resp

    def _post(self, path: str, json: dict | None = None) -> httpx.Response:
        resp = self.client.post(f"{self.base_url}{path}", json=json or {})
        resp.raise_for_status()
        return resp

    def _put(self, path: str, json: dict | None = None) -> httpx.Response:
        resp = self.client.put(f"{self.base_url}{path}", json=json or {})
        resp.raise_for_status()
        return resp

    def _delete(self, path: str) -> httpx.Response:
        resp = self.client.delete(f"{self.base_url}{path}")
        resp.raise_for_status()
        return resp

    # -- Users --

    def find_user(self, login: str) -> dict | None:
        resp = self._get("/users", params={"filter": f'profile.login eq "{login}"'})
        users = resp.json()
        return users[0] if users else None

    def create_user(self, login: str, first_name: str, last_name: str,
                    email: str, department: str) -> dict:
        body = {
            "profile": {
                "firstName": first_name,
                "lastName": last_name,
                "email": email,
                "login": login,
                "department": department,
            },
            "credentials": {
                "password": {"value": "Gateco-Test-2024!"},
            },
        }
        resp = self._post("/users?activate=true", json=body)
        return resp.json()

    def deactivate_user(self, user_id: str) -> None:
        try:
            self._post(f"/users/{user_id}/lifecycle/deactivate")
        except httpx.HTTPStatusError:
            pass  # Already deactivated

    def delete_user(self, user_id: str) -> None:
        self.deactivate_user(user_id)
        self._delete(f"/users/{user_id}")

    def list_vh_users(self) -> list[dict]:
        """List all users whose login starts with vh-."""
        resp = self._get("/users", params={"filter": 'profile.login sw "vh-"'})
        return resp.json()

    # -- Groups --

    def find_group(self, name: str) -> dict | None:
        resp = self._get("/groups", params={"q": name})
        for g in resp.json():
            if g["profile"]["name"] == name:
                return g
        return None

    def create_group(self, name: str) -> dict:
        body = {"profile": {"name": name, "description": f"Gateco validation harness test group: {name}"}}
        resp = self._post("/groups", json=body)
        return resp.json()

    def delete_group(self, group_id: str) -> None:
        self._delete(f"/groups/{group_id}")

    # -- Memberships --

    def get_group_members(self, group_id: str) -> list[dict]:
        resp = self._get(f"/groups/{group_id}/users")
        return resp.json()

    def add_user_to_group(self, group_id: str, user_id: str) -> None:
        self._put(f"/groups/{group_id}/users/{user_id}")

    def is_member(self, group_id: str, user_id: str) -> bool:
        members = self.get_group_members(group_id)
        return any(m["id"] == user_id for m in members)


# ---------------------------------------------------------------------------
# Seed & teardown
# ---------------------------------------------------------------------------

def seed(client: OktaClient, email_domain: str) -> SeedStats:
    """Create test users and groups idempotently."""
    stats = SeedStats()

    # 1. Ensure groups exist
    group_ids: dict[str, str] = {}
    for group_name in TEST_GROUPS:
        existing = client.find_group(group_name)
        if existing:
            group_ids[group_name] = existing["id"]
            stats.groups_existing += 1
        else:
            created = client.create_group(group_name)
            group_ids[group_name] = created["id"]
            stats.groups_created += 1

    # 2. Ensure users exist
    user_ids: dict[str, str] = {}
    for u in TEST_USERS:
        login = f"{u['login_prefix']}@{email_domain}"
        existing = client.find_user(login)
        if existing:
            user_ids[login] = existing["id"]
            stats.users_existing += 1
        else:
            created = client.create_user(
                login=login,
                first_name=u["firstName"],
                last_name=u["lastName"],
                email=login,
                department=u["department"],
            )
            user_ids[login] = created["id"]
            stats.users_created += 1

    # 3. Ensure memberships
    for u in TEST_USERS:
        login = f"{u['login_prefix']}@{email_domain}"
        uid = user_ids[login]
        gid = group_ids[u["group"]]
        if client.is_member(gid, uid):
            stats.memberships_existing += 1
        else:
            client.add_user_to_group(gid, uid)
            stats.memberships_added += 1

    return stats


def teardown(client: OktaClient) -> SeedStats:
    """Delete all vh- prefixed test users and test groups."""
    stats = SeedStats()

    # Delete vh- users
    vh_users = client.list_vh_users()
    for user in vh_users:
        client.delete_user(user["id"])
        stats.users_deleted += 1

    # Delete test groups
    for group_name in TEST_GROUPS:
        existing = client.find_group(group_name)
        if existing:
            client.delete_group(existing["id"])
            stats.groups_deleted += 1

    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.command()
@click.option("--domain", required=True, help="Okta org domain (e.g. dev-12345.okta.com)")
@click.option("--api-token", required=True, help="Okta SSWS API token")
@click.option("--email-domain", default=None, help="Email domain for test users (defaults to Okta domain)")
@click.option("--teardown", "do_teardown", is_flag=True, flag_value=True, default=False,
              help="Delete all vh- prefixed test data")
def main(domain: str, api_token: str, email_domain: str | None, do_teardown: bool) -> None:
    """Seed or teardown Okta test data for the Gateco validation harness."""
    if email_domain is None:
        email_domain = domain

    client = OktaClient(domain, api_token)

    if do_teardown:
        click.echo(f"Tearing down vh- test data from {domain}...")
        stats = teardown(client)
        click.echo(f"Users deleted: {stats.users_deleted}")
        click.echo(f"Groups deleted: {stats.groups_deleted}")
    else:
        click.echo(f"Seeding test data into {domain}...")
        stats = seed(client, email_domain)
        total_users = stats.users_created + stats.users_existing
        total_groups = stats.groups_created + stats.groups_existing
        total_memberships = stats.memberships_added + stats.memberships_existing
        click.echo(f"Users: {total_users} present ({stats.users_created} created, {stats.users_existing} existing)")
        click.echo(f"Groups: {total_groups} present ({stats.groups_created} created, {stats.groups_existing} existing)")
        click.echo(f"Memberships: {total_memberships} present ({stats.memberships_added} added, {stats.memberships_existing} existing)")


if __name__ == "__main__":
    main()
