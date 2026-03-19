"""Unit tests for IDP adapter dispatch and stub adapter."""

import pytest

from gateco.services.idp_adapters import sync_from_provider, _is_stub_config
from gateco.services.idp_adapters.base import SyncedPrincipal, SyncedGroup, SyncResult
from gateco.services.idp_adapters.stub import StubAdapter


@pytest.mark.asyncio
async def test_stub_adapter_returns_5_principals_2_groups():
    adapter = StubAdapter({})
    result = await adapter.sync()
    assert len(result.principals) == 5
    assert len(result.groups) == 2
    assert result.principals[0].display_name == "Alice"
    assert result.principals[4].display_name == "Eve"
    # Check group assignments
    eng = [p for p in result.principals if "engineering" in p.groups]
    mkt = [p for p in result.principals if "marketing" in p.groups]
    assert len(eng) == 3
    assert len(mkt) == 2


@pytest.mark.asyncio
async def test_dispatch_uses_stub_for_fake_config():
    result = await sync_from_provider("okta", {"domain": "vh-test.okta.com", "api_token": "vh-fake-token"})
    assert len(result.principals) == 5
    assert len(result.groups) == 2


@pytest.mark.asyncio
async def test_dispatch_uses_stub_for_unknown_type():
    result = await sync_from_provider("unknown_provider", {})
    assert len(result.principals) == 5
    assert len(result.groups) == 2


def test_is_stub_config_detects_fake_markers():
    assert _is_stub_config({"api_token": "vh-fake-token"}) is True
    assert _is_stub_config({"domain": "vh-test.okta.com"}) is True
    assert _is_stub_config({"key": "placeholder-value"}) is True
    assert _is_stub_config({"domain": "dev-12345.okta.com", "api_token": "real-token"}) is False
    assert _is_stub_config({}) is False


def test_synced_principal_dataclass_defaults():
    p = SyncedPrincipal(external_id="1", display_name="Test")
    assert p.email is None
    assert p.groups == []
    assert p.roles == []
    assert p.attributes == {}


def test_synced_group_dataclass_defaults():
    g = SyncedGroup(external_id="1", name="test-group")
    assert g.member_count == 0


def test_sync_result_empty_by_default():
    r = SyncResult()
    assert r.principals == []
    assert r.groups == []
    assert r.warnings == []


@pytest.mark.asyncio
async def test_stub_adapter_principal_attributes():
    adapter = StubAdapter({})
    result = await adapter.sync()
    for p in result.principals:
        assert "department" in p.attributes
        if "engineering" in p.groups:
            assert p.attributes["department"] == "engineering"
        else:
            assert p.attributes["department"] == "marketing"


@pytest.mark.asyncio
async def test_stub_adapter_principal_emails():
    adapter = StubAdapter({})
    result = await adapter.sync()
    for p in result.principals:
        expected_email = f"{p.display_name.lower()}@example.com"
        assert p.email == expected_email
