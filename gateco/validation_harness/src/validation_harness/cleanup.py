"""Manifest-based cleanup with prefix-based fallback recovery."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from validation_harness.models import CreatedResource

logger = logging.getLogger(__name__)


class CleanupManager:
    """Manages resource cleanup via manifests and prefix-based fallback."""

    def __init__(self, output_dir: str) -> None:
        self.output_dir = Path(output_dir)

    def manifest_path(self, run_id: str) -> Path:
        """Return the manifest file path for a run (may not exist yet)."""
        return self.output_dir / run_id / "created_resources.json"

    def save_manifest(
        self, run_id: str, resources: list[CreatedResource]
    ) -> Path:
        """Save cleanup manifest for a run."""
        path = self.manifest_path(run_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = [r.model_dump(mode="json") for r in resources]
        path.write_text(json.dumps(data, indent=2))
        return path

    def load_manifest(self, manifest_path: str | Path) -> list[CreatedResource]:
        """Load a cleanup manifest from disk."""
        path = Path(manifest_path)
        if not path.exists():
            return []

        raw = json.loads(path.read_text())
        return [CreatedResource.model_validate(item) for item in raw]

    async def cleanup_from_manifest(
        self, client: Any, manifest_path: str | Path
    ) -> list[CreatedResource]:
        """Delete resources listed in a manifest.

        Returns updated resource list with deletion status.
        """
        resources = self.load_manifest(manifest_path)
        if not resources:
            logger.info("No resources in manifest to clean up")
            return resources

        # Process in reverse order (last created → first deleted)
        for resource in reversed(resources):
            try:
                await self._delete_resource(client, resource)
                resource.deletion_attempted = True
                resource.deletion_status = "success"
            except Exception as exc:
                logger.warning(
                    "Failed to delete %s %s: %s",
                    resource.resource_type,
                    resource.resource_id,
                    exc,
                )
                resource.deletion_attempted = True
                resource.deletion_status = "failed"

        return resources

    async def cleanup_by_prefix(
        self, client: Any, prefix: str = "vh-"
    ) -> int:
        """Recovery fallback: delete all resources with the given prefix.

        Returns count of resources deleted.
        """
        deleted = 0

        # Try to clean up connectors with prefix
        try:
            page = await client.connectors.list(per_page=100)
            for connector in page.items:
                if hasattr(connector, "name") and connector.name.startswith(prefix):
                    try:
                        await client.connectors.delete(connector.id)
                        deleted += 1
                        logger.info("Deleted connector: %s", connector.name)
                    except Exception as exc:
                        logger.warning("Failed to delete connector %s: %s", connector.name, exc)
        except Exception as exc:
            logger.warning("Failed to list connectors for prefix cleanup: %s", exc)

        # Try to clean up policies with prefix
        try:
            page = await client.policies.list(per_page=100)
            for policy in page.items:
                if hasattr(policy, "name") and policy.name.startswith(prefix):
                    try:
                        await client.policies.delete(policy.id)
                        deleted += 1
                        logger.info("Deleted policy: %s", policy.name)
                    except Exception as exc:
                        logger.warning("Failed to delete policy %s: %s", policy.name, exc)
        except Exception as exc:
            logger.warning("Failed to list policies for prefix cleanup: %s", exc)

        return deleted

    async def _delete_resource(self, client: Any, resource: CreatedResource) -> None:
        """Delete a single resource by type."""
        rtype = resource.resource_type
        rid = resource.resource_id

        if rtype == "connector":
            await client.connectors.delete(rid)
        elif rtype == "policy":
            await client.policies.delete(rid)
        elif rtype == "resource":
            # Resources are typically cleaned up with their connector
            logger.info("Resource %s cleanup deferred to connector deletion", rid)
        else:
            logger.warning("Unknown resource type for cleanup: %s", rtype)
