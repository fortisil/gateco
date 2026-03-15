"""Export and normalize the Gateco OpenAPI spec."""

import json
import os
import sys
from collections import OrderedDict
from pathlib import Path

# Resolve paths
SCRIPT_DIR = Path(__file__).resolve().parent
CONTRACTS_DIR = SCRIPT_DIR.parent
ROOT_DIR = CONTRACTS_DIR.parent.parent  # gateco/
BACKEND_SRC = ROOT_DIR / "apps" / "backend" / "src"

# Add backend source to path
sys.path.insert(0, str(BACKEND_SRC))

# Set minimal env vars so app can import without a real DB
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://localhost/dummy")
os.environ.setdefault("JWT_SECRET_KEY", "dummy-key-for-openapi-export-only")

from gateco.main import app  # noqa: E402


# Prefixes/paths to prune from public contract
PRUNE_PREFIXES = ("/api/admin", "/health")
PRUNE_PATHS = ("/health", "/")


def normalize_spec(spec: dict) -> dict:
    """Normalize the raw FastAPI OpenAPI spec."""
    # 1. Prune internal routes
    paths = spec.get("paths", {})
    pruned_paths = {}
    for path, operations in paths.items():
        if any(path.startswith(prefix) for prefix in PRUNE_PREFIXES):
            continue
        if path in PRUNE_PATHS:
            continue
        pruned_paths[path] = operations
    spec["paths"] = pruned_paths

    # 2. Set explicit operationId from function names
    for path, operations in spec["paths"].items():
        for method, operation in operations.items():
            if method in ("get", "post", "put", "patch", "delete", "head", "options"):
                # FastAPI sets operationId as "{function_name}_{path}_{method}"
                # We want just the function name
                if "operationId" in operation:
                    # Find matching route to get the actual endpoint name
                    for route in app.routes:
                        if hasattr(route, "methods") and hasattr(route, "path"):
                            if route.path == path and method.upper() in route.methods:
                                operation["operationId"] = route.name
                                break

    # 3. Enforce consistent tags from path prefix
    tag_map = {
        "/api/auth": "auth",
        "/api/users": "users",
        "/api/connectors": "connectors",
        "/api/policies": "policies",
        "/api/data-catalog": "data-catalog",
        "/api/identity-providers": "identity-providers",
        "/api/principals": "principals",
        "/api/pipelines": "pipelines",
        "/api/retrievals": "retrievals",
        "/api/v1/ingest": "ingestion",
        "/api/simulator": "simulator",
        "/api/dashboard": "dashboard",
        "/api/audit-log": "audit",
        "/api/plans": "billing",
        "/api/checkout": "billing",
        "/api/billing": "billing",
        "/api/webhooks": "billing",
    }
    for path, operations in spec["paths"].items():
        for method, operation in operations.items():
            if method in ("get", "post", "put", "patch", "delete"):
                for prefix, tag in tag_map.items():
                    if path.startswith(prefix):
                        operation["tags"] = [tag]
                        break

    # 4. Clean up schema refs - remove "Body_" prefixed schemas FastAPI generates
    # and simplify names
    if "components" in spec and "schemas" in spec["components"]:
        schemas = spec["components"]["schemas"]
        # Remove schemas that are just wrappers
        to_remove = []
        for name in list(schemas.keys()):
            if name.startswith("Body_"):
                to_remove.append(name)
            # Clean up "Input" suffix FastAPI adds to some models
            elif name.endswith("-Input") and name[:-6] in schemas:
                to_remove.append(name)

    # 5. Sort everything for deterministic output
    return sort_dict(spec)


def sort_dict(obj):
    """Recursively sort dictionary keys."""
    if isinstance(obj, dict):
        return OrderedDict(
            (k, sort_dict(v)) for k, v in sorted(obj.items())
        )
    if isinstance(obj, list):
        return [sort_dict(item) for item in obj]
    return obj


def main():
    spec = app.openapi()
    spec = normalize_spec(spec)

    output_path = CONTRACTS_DIR / "openapi.json"
    with open(output_path, "w") as f:
        json.dump(spec, f, indent=2)
        f.write("\n")

    print(f"OpenAPI spec written to {output_path}")
    print(f"  Paths: {len(spec.get('paths', {}))}")
    print(f"  Schemas: {len(spec.get('components', {}).get('schemas', {}))}")


if __name__ == "__main__":
    main()
