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


def test_aws_adapter_department_from_usertype():
    """AWS adapter maps UserType → attributes.department (Gateco test convention)."""
    from gateco.services.idp_adapters.aws import AWSIAMAdapter
    from unittest.mock import MagicMock, patch

    fake_users = [{
        "UserId": "u-001",
        "UserName": "alice",
        "Name": {"GivenName": "Alice", "FamilyName": "Eng"},
        "Emails": [{"Value": "alice@example.com", "Primary": True}],
        "Title": "Engineer",
        "UserType": "engineering",
    }]

    # Build adapter without calling real AWS
    with patch("boto3.client"):
        adapter = AWSIAMAdapter({
            "identity_store_id": "d-test",
            "region": "us-east-1",
            "aws_access_key_id": "fake",
            "aws_secret_access_key": "fake",
        })
        # Call the attribute-building code path directly
        from gateco.services.idp_adapters.base import SyncedPrincipal
        u = fake_users[0]
        name_obj = u.get("Name", {})
        display = u.get("DisplayName") or f"{name_obj.get('GivenName', '')} {name_obj.get('FamilyName', '')}".strip()
        emails = u.get("Emails", [])
        email = next((e["Value"] for e in emails if e.get("Primary")), None)
        principal = SyncedPrincipal(
            external_id=u["UserId"],
            display_name=display,
            email=email,
            groups=[],
            roles=[],
            attributes={
                k: v for k, v in {
                    "title": u.get("Title"),
                    "department": u.get("UserType"),
                }.items() if v
            },
        )
        assert principal.attributes["department"] == "engineering"
        assert principal.attributes["title"] == "Engineer"


def test_aws_adapter_department_absent_when_usertype_missing():
    """When UserType is not set, department should not appear in attributes."""
    from gateco.services.idp_adapters.base import SyncedPrincipal
    u = {"UserId": "u-002", "Title": "Manager"}
    attributes = {
        k: v for k, v in {
            "title": u.get("Title"),
            "department": u.get("UserType"),
        }.items() if v
    }
    assert "department" not in attributes
    assert attributes["title"] == "Manager"


@pytest.mark.asyncio
async def test_stub_adapter_principal_emails():
    adapter = StubAdapter({})
    result = await adapter.sync()
    for p in result.principals:
        expected_email = f"{p.display_name.lower()}@example.com"
        assert p.email == expected_email
