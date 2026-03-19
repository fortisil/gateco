"""Stub IDP adapter — returns hardcoded test principals (backward compat)."""

from __future__ import annotations

from gateco.services.idp_adapters.base import (
    BaseIDPAdapter, SyncResult, SyncedGroup, SyncedPrincipal,
)


class StubAdapter(BaseIDPAdapter):
    """Returns the same 5 mock principals as the original trigger_sync()."""

    async def sync(self) -> SyncResult:
        mock_names = ["Alice", "Bob", "Carol", "Dave", "Eve"]
        principals = []
        for i, name in enumerate(mock_names):
            principals.append(SyncedPrincipal(
                external_id=f"stub-{i}",
                display_name=name,
                email=f"{name.lower()}@example.com",
                groups=["engineering"] if i < 3 else ["marketing"],
                roles=["viewer"],
                attributes={"department": "engineering" if i < 3 else "marketing"},
            ))
        groups = [
            SyncedGroup(external_id="grp-engineering", name="engineering", member_count=3),
            SyncedGroup(external_id="grp-marketing", name="marketing", member_count=2),
        ]
        return SyncResult(principals=principals, groups=groups)
