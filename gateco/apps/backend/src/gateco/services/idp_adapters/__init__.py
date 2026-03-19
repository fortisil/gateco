"""IDP sync adapter dispatch.

Pattern follows connector_adapters.py — dict maps type→adapter class.
"""

from __future__ import annotations

from gateco.services.idp_adapters.base import BaseIDPAdapter, SyncResult
from gateco.services.idp_adapters.stub import StubAdapter

# Lazy imports to avoid pulling in boto3/google-auth when not needed
ADAPTER_CLASSES: dict[str, str] = {
    "okta": "gateco.services.idp_adapters.okta.OktaAdapter",
    "azure_entra_id": "gateco.services.idp_adapters.azure.AzureEntraAdapter",
    "aws_iam": "gateco.services.idp_adapters.aws.AWSIAMAdapter",
    "gcp": "gateco.services.idp_adapters.gcp.GCPAdapter",
}


def _is_stub_config(config: dict) -> bool:
    """Check if config contains placeholder/fake values (use stub instead)."""
    values = str(config).lower()
    return any(marker in values for marker in ["fake", "placeholder", "vh-fake", "vh-test"])


async def sync_from_provider(idp_type: str, config: dict) -> SyncResult:
    """Dispatch sync to the appropriate adapter. Falls back to stub for fake configs."""
    if _is_stub_config(config):
        return await StubAdapter(config).sync()

    dotted = ADAPTER_CLASSES.get(idp_type)
    if not dotted:
        return await StubAdapter(config).sync()

    # Lazy import to avoid dependency issues
    import importlib
    module_path, class_name = dotted.rsplit(".", 1)
    module = importlib.import_module(module_path)
    adapter_cls: type[BaseIDPAdapter] = getattr(module, class_name)
    return await adapter_cls(config).sync()


__all__ = ["sync_from_provider", "SyncResult", "BaseIDPAdapter", "StubAdapter"]
