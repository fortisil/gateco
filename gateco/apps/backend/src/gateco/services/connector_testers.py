"""Real connection testers for all supported connector types.

Each tester performs bounded, read-only health checks separating:
reachability, authentication, schema discovery, and vector readiness.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Literal

import asyncpg
import httpx

logger = logging.getLogger(__name__)

MAX_RESOURCES = 25
PER_CALL_TIMEOUT = 4.0
OVERALL_TIMEOUT = 10.0


@dataclass
class DiscoveredResource:
    """A discovered vector resource (table, index, collection, etc.)."""

    name: str
    record_count: int | None = None
    dimension: int | None = None
    metric: str | None = None
    metadata: dict | None = None


@dataclass
class ConnectorTestResult:
    """Normalized result from testing a connector connection."""

    success: bool
    health_status: Literal["ok", "degraded", "failed"]
    authenticated: bool = False
    schema_discovered: bool = False
    vector_ready: bool = False
    server_version: str | None = None
    resources: list[DiscoveredResource] | None = None
    resource_kind: str | None = None
    total_records: int | None = None
    approximate_counts: bool = False
    warnings: list[str] = field(default_factory=list)
    error: str | None = None
    latency_ms: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict for JSON storage. Never includes secrets."""
        return {
            "success": self.success,
            "health_status": self.health_status,
            "authenticated": self.authenticated,
            "schema_discovered": self.schema_discovered,
            "vector_ready": self.vector_ready,
            "server_version": self.server_version,
            "resources": [
                {
                    "name": r.name,
                    "record_count": r.record_count,
                    "dimension": r.dimension,
                    "metric": r.metric,
                }
                for r in (self.resources or [])
            ],
            "resource_kind": self.resource_kind,
            "total_records": self.total_records,
            "approximate_counts": self.approximate_counts,
            "warnings": self.warnings,
            "error": self.error,
            "latency_ms": self.latency_ms,
        }


def _failed(error: str, **kwargs) -> ConnectorTestResult:
    return ConnectorTestResult(
        success=False, health_status="failed", error=error, **kwargs
    )


# ── Postgres family (pgvector, supabase, neon) ──


async def _test_postgres(dsn: str, schema: str = "public") -> ConnectorTestResult:
    """Shared tester for all Postgres-based connectors."""
    conn = await asyncpg.connect(dsn, timeout=PER_CALL_TIMEOUT)
    try:
        version_raw = await conn.fetchval("SELECT version()")
        server_version = version_raw.split(",")[0] if version_raw else None

        # Discover vector-enabled tables
        tables = await conn.fetch(
            """
            SELECT c.relname, c.reltuples::bigint AS approx_count
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = $1
              AND c.relkind = 'r'
              AND EXISTS (
                  SELECT 1 FROM pg_attribute a
                  JOIN pg_type t ON a.atttypid = t.oid
                  WHERE a.attrelid = c.oid
                    AND a.attnum > 0
                    AND NOT a.attisdropped
                    AND t.typname = 'vector'
              )
            LIMIT $2
            """,
            schema,
            MAX_RESOURCES,
        )

        resources = [
            DiscoveredResource(
                name=row["relname"],
                record_count=max(0, row["approx_count"]) if row["approx_count"] >= 0 else None,
            )
            for row in tables
        ]

        warnings = []
        total_count = await conn.fetchval(
            """
            SELECT count(*) FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = $1
              AND c.relkind = 'r'
              AND EXISTS (
                  SELECT 1 FROM pg_attribute a
                  JOIN pg_type t ON a.atttypid = t.oid
                  WHERE a.attrelid = c.oid
                    AND a.attnum > 0
                    AND NOT a.attisdropped
                    AND t.typname = 'vector'
              )
            """,
            schema,
        )
        if total_count > MAX_RESOURCES:
            warnings.append(
                f"More than {MAX_RESOURCES} vector tables — showing first {MAX_RESOURCES}"
            )

        vector_ready = len(resources) > 0
        if not vector_ready:
            warnings.append("No vector-enabled tables found in schema")

        total_records = sum(r.record_count for r in resources if r.record_count is not None)

        return ConnectorTestResult(
            success=True,
            health_status="ok" if vector_ready else "degraded",
            authenticated=True,
            schema_discovered=True,
            vector_ready=vector_ready,
            server_version=server_version,
            resources=resources,
            resource_kind="table",
            total_records=total_records if resources else None,
            approximate_counts=True,
            warnings=warnings,
        )
    finally:
        await conn.close()


def _build_pgvector_dsn(config: dict) -> str:
    user = config.get("user", "postgres")
    password = config.get("password", "")
    host = config["host"]
    port = config.get("port", 5432)
    database = config["database"]
    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    return f"postgresql://{user}@{host}:{port}/{database}"


async def _test_pgvector(config: dict) -> ConnectorTestResult:
    dsn = _build_pgvector_dsn(config)
    schema = config.get("schema", "public")
    return await _test_postgres(dsn, schema)


async def _test_supabase(config: dict) -> ConnectorTestResult:
    dsn = _build_pgvector_dsn(config)
    schema = config.get("schema", "public")
    return await _test_postgres(dsn, schema)


async def _test_neon(config: dict) -> ConnectorTestResult:
    dsn = config["connection_string"]
    schema = config.get("schema", "public")
    return await _test_postgres(dsn, schema)


# ── REST / Vector-Native family ──


async def _test_pinecone(config: dict) -> ConnectorTestResult:
    api_key = config["api_key"]
    index_filter = config.get("index_name")
    headers = {"Api-Key": api_key, "X-Pinecone-API-Version": "2024-07"}

    async with httpx.AsyncClient(timeout=PER_CALL_TIMEOUT) as client:
        resp = await client.get("https://api.pinecone.io/indexes", headers=headers)
        resp.raise_for_status()
        indexes = resp.json().get("indexes", [])

        if index_filter:
            indexes = [idx for idx in indexes if idx.get("name") == index_filter]

        resources = []
        warnings = []
        if len(indexes) > MAX_RESOURCES:
            warnings.append(
                f"More than {MAX_RESOURCES} indexes — showing first {MAX_RESOURCES}"
            )

        for idx in indexes[:MAX_RESOURCES]:
            resource = DiscoveredResource(
                name=idx["name"],
                dimension=idx.get("dimension"),
                metric=idx.get("metric"),
            )
            host = idx.get("host")
            if host:
                try:
                    stats_resp = await client.post(
                        f"https://{host}/describe_index_stats",
                        headers=headers,
                        json={},
                    )
                    if stats_resp.is_success:
                        stats = stats_resp.json()
                        resource.record_count = stats.get("totalRecordCount")
                except Exception:
                    warnings.append(f"Stats unavailable for index {idx['name']}")
            resources.append(resource)

        vector_ready = len(resources) > 0
        if not vector_ready:
            warnings.append("No indexes found")

        total = sum(r.record_count for r in resources if r.record_count is not None)

        return ConnectorTestResult(
            success=True,
            health_status="ok" if vector_ready else "degraded",
            authenticated=True,
            schema_discovered=True,
            vector_ready=vector_ready,
            resources=resources,
            resource_kind="index",
            total_records=total if resources else None,
            approximate_counts=False,
            warnings=warnings,
        )


async def _test_opensearch(config: dict) -> ConnectorTestResult:
    host = config["host"].rstrip("/")
    api_key = config["api_key"]
    index_filter = config.get("index_name")
    headers = {"Authorization": f"ApiKey {api_key}"}

    async with httpx.AsyncClient(timeout=PER_CALL_TIMEOUT) as client:
        # Cluster info
        info_resp = await client.get(f"{host}/", headers=headers)
        info_resp.raise_for_status()
        info = info_resp.json()
        server_version = info.get("version", {}).get("number")

        # List indices
        cat_resp = await client.get(
            f"{host}/_cat/indices", headers=headers, params={"format": "json"}
        )
        cat_resp.raise_for_status()
        indices = cat_resp.json()

        if index_filter:
            indices = [idx for idx in indices if idx.get("index") == index_filter]

        # Filter out system indices
        indices = [idx for idx in indices if not idx.get("index", "").startswith(".")]

        resources = []
        warnings = []
        vector_ready_flag = False

        if len(indices) > MAX_RESOURCES:
            warnings.append(
                f"More than {MAX_RESOURCES} indices — showing first {MAX_RESOURCES}"
            )

        for idx in indices[:MAX_RESOURCES]:
            idx_name = idx.get("index", "")
            doc_count = None
            try:
                doc_count = int(idx.get("docs.count", 0))
            except (ValueError, TypeError):
                pass

            # Check for knn_vector mappings
            try:
                mapping_resp = await client.get(
                    f"{host}/{idx_name}/_mapping", headers=headers
                )
                if mapping_resp.is_success:
                    mappings = mapping_resp.json()
                    mapping_str = str(mappings)
                    if "knn_vector" in mapping_str:
                        vector_ready_flag = True
            except Exception:
                pass

            resources.append(
                DiscoveredResource(name=idx_name, record_count=doc_count)
            )

        if resources and not vector_ready_flag:
            warnings.append(
                "Indexes found, vector field capability not verified"
            )
        if not resources:
            warnings.append("No indices found")

        total = sum(r.record_count for r in resources if r.record_count is not None)

        return ConnectorTestResult(
            success=True,
            health_status="ok" if (resources and vector_ready_flag) else "degraded",
            authenticated=True,
            schema_discovered=len(resources) > 0,
            vector_ready=vector_ready_flag,
            server_version=server_version,
            resources=resources,
            resource_kind="index",
            total_records=total if resources else None,
            approximate_counts=False,
            warnings=warnings,
        )


async def _test_weaviate(config: dict) -> ConnectorTestResult:
    host = config["host"].rstrip("/")
    api_key = config["api_key"]
    class_filter = config.get("class_name")
    headers = {"Authorization": f"Bearer {api_key}"}

    async with httpx.AsyncClient(timeout=PER_CALL_TIMEOUT) as client:
        # Meta
        meta_resp = await client.get(f"{host}/v1/meta", headers=headers)
        meta_resp.raise_for_status()
        meta = meta_resp.json()
        server_version = meta.get("version")

        # Schema
        schema_resp = await client.get(f"{host}/v1/schema", headers=headers)
        schema_resp.raise_for_status()
        classes = schema_resp.json().get("classes", [])

        if class_filter:
            classes = [c for c in classes if c.get("class") == class_filter]

        resources = []
        warnings = []

        if len(classes) > MAX_RESOURCES:
            warnings.append(
                f"More than {MAX_RESOURCES} classes — showing first {MAX_RESOURCES}"
            )

        for cls in classes[:MAX_RESOURCES]:
            class_name = cls.get("class", "")
            resource = DiscoveredResource(name=class_name)

            # Try to get counts via GraphQL aggregate
            try:
                gql_resp = await client.post(
                    f"{host}/v1/graphql",
                    headers=headers,
                    json={
                        "query": (
                            "{ Aggregate { "
                            + class_name
                            + " { meta { count } } } }"
                        )
                    },
                )
                if gql_resp.is_success:
                    gql_data = gql_resp.json()
                    count = (
                        gql_data.get("data", {})
                        .get("Aggregate", {})
                        .get(class_name, [{}])[0]
                        .get("meta", {})
                        .get("count")
                    )
                    resource.record_count = count
            except Exception:
                warnings.append(f"Counts unavailable for class {class_name}")

            resources.append(resource)

        vector_ready = len(resources) > 0
        if not vector_ready:
            warnings.append("No classes found")

        total = sum(r.record_count for r in resources if r.record_count is not None)

        return ConnectorTestResult(
            success=True,
            health_status="ok" if vector_ready else "degraded",
            authenticated=True,
            schema_discovered=True,
            vector_ready=vector_ready,
            server_version=server_version,
            resources=resources,
            resource_kind="class",
            total_records=total if resources else None,
            approximate_counts=False,
            warnings=warnings,
        )


async def _test_qdrant(config: dict) -> ConnectorTestResult:
    host = config["host"].rstrip("/")
    api_key = config.get("api_key")
    collection_filter = config.get("collection_name")
    headers = {}
    if api_key:
        headers["api-key"] = api_key

    async with httpx.AsyncClient(timeout=PER_CALL_TIMEOUT) as client:
        # List collections
        resp = await client.get(f"{host}/collections", headers=headers)
        resp.raise_for_status()
        collections = resp.json().get("result", {}).get("collections", [])

        if collection_filter:
            collections = [
                c for c in collections if c.get("name") == collection_filter
            ]

        resources = []
        warnings = []

        if len(collections) > MAX_RESOURCES:
            warnings.append(
                f"More than {MAX_RESOURCES} collections — showing first {MAX_RESOURCES}"
            )

        for coll in collections[:MAX_RESOURCES]:
            coll_name = coll.get("name", "")
            resource = DiscoveredResource(name=coll_name)

            try:
                detail_resp = await client.get(
                    f"{host}/collections/{coll_name}", headers=headers
                )
                if detail_resp.is_success:
                    result = detail_resp.json().get("result", {})
                    resource.record_count = result.get("points_count")
                    config_data = result.get("config", {})
                    params = config_data.get("params", {})
                    vectors_config = params.get("vectors", {})
                    if isinstance(vectors_config, dict) and "size" in vectors_config:
                        resource.dimension = vectors_config.get("size")
                        resource.metric = vectors_config.get("distance")
            except Exception:
                warnings.append(f"Details unavailable for collection {coll_name}")

            resources.append(resource)

        vector_ready = len(resources) > 0
        if not vector_ready:
            warnings.append("No collections found")

        total = sum(r.record_count for r in resources if r.record_count is not None)

        return ConnectorTestResult(
            success=True,
            health_status="ok" if vector_ready else "degraded",
            authenticated=True,
            schema_discovered=True,
            vector_ready=vector_ready,
            resources=resources,
            resource_kind="collection",
            total_records=total if resources else None,
            approximate_counts=True,
            warnings=warnings,
        )


async def _test_milvus(config: dict) -> ConnectorTestResult:
    host = config["host"].rstrip("/")
    port = config.get("port", 19530)
    token = config.get("token")
    collection_filter = config.get("collection_name")

    # Build base URL
    if "://" not in host:
        host = f"https://{host}"
    base = f"{host}:{port}" if ":" not in host.split("://")[1] else host

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=PER_CALL_TIMEOUT) as client:
        # List collections (v2 API)
        resp = await client.post(
            f"{base}/v2/vectordb/collections/list",
            headers=headers,
            json={},
        )
        if resp.status_code == 404:
            return ConnectorTestResult(
                success=True,
                health_status="degraded",
                authenticated=True,
                schema_discovered=False,
                warnings=[
                    "Milvus REST API v2 not available — upgrade to Milvus 2.3+ recommended"
                ],
            )
        resp.raise_for_status()
        collection_names = resp.json().get("data", [])

        if collection_filter:
            collection_names = [
                n for n in collection_names if n == collection_filter
            ]

        resources = []
        warnings = []

        if len(collection_names) > MAX_RESOURCES:
            warnings.append(
                f"More than {MAX_RESOURCES} collections — showing first {MAX_RESOURCES}"
            )

        for coll_name in collection_names[:MAX_RESOURCES]:
            resource = DiscoveredResource(name=coll_name)
            try:
                desc_resp = await client.post(
                    f"{base}/v2/vectordb/collections/describe",
                    headers=headers,
                    json={"collectionName": coll_name},
                )
                if desc_resp.is_success:
                    data = desc_resp.json().get("data", {})
                    # Try to extract vector dimension from schema
                    for f in data.get("schema", {}).get("fields", []):
                        params = f.get("type_params", {})
                        if "dim" in params:
                            resource.dimension = int(params["dim"])
                            break
            except Exception:
                warnings.append(f"Details unavailable for collection {coll_name}")

            resources.append(resource)

        vector_ready = len(resources) > 0
        if not vector_ready:
            warnings.append("No collections found")

        return ConnectorTestResult(
            success=True,
            health_status="ok" if vector_ready else "degraded",
            authenticated=True,
            schema_discovered=True,
            vector_ready=vector_ready,
            resources=resources,
            resource_kind="collection",
            total_records=None,
            approximate_counts=False,
            warnings=warnings,
        )


async def _test_chroma(config: dict) -> ConnectorTestResult:
    host = config["host"].rstrip("/")
    api_key = config.get("api_key")
    tenant = config.get("tenant", "default_tenant")
    database = config.get("database", "default_database")

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async with httpx.AsyncClient(timeout=PER_CALL_TIMEOUT) as client:
        # Health check
        try:
            _health_resp = await client.get(
                f"{host}/api/v2/heartbeat", headers=headers
            )
        except Exception:
            pass

        # Version
        server_version = None
        try:
            ver_resp = await client.get(f"{host}/api/v2/version", headers=headers)
            if ver_resp.is_success:
                ver_data = ver_resp.json()
                server_version = (
                    ver_data if isinstance(ver_data, str) else ver_data.get("version")
                )
        except Exception:
            pass

        # List collections
        try:
            coll_resp = await client.get(
                f"{host}/api/v2/tenants/{tenant}/databases/{database}/collections",
                headers=headers,
            )
        except Exception:
            return ConnectorTestResult(
                success=True,
                health_status="degraded",
                authenticated=True,
                schema_discovered=False,
                server_version=server_version,
                warnings=[
                    "Chroma API v2 not available — check server version"
                ],
            )

        if coll_resp.status_code == 404:
            return ConnectorTestResult(
                success=True,
                health_status="degraded",
                authenticated=True,
                schema_discovered=False,
                server_version=server_version,
                warnings=[
                    "Chroma API v2 not available — check server version"
                ],
            )
        coll_resp.raise_for_status()
        collections = coll_resp.json()

        resources = []
        warnings = []

        if len(collections) > MAX_RESOURCES:
            warnings.append(
                f"More than {MAX_RESOURCES} collections — showing first {MAX_RESOURCES}"
            )

        for coll in collections[:MAX_RESOURCES]:
            coll_name = coll.get("name", "")
            coll_id = coll.get("id", "")
            resource = DiscoveredResource(name=coll_name)

            if coll_id:
                try:
                    count_resp = await client.get(
                        f"{host}/api/v2/tenants/{tenant}/databases/{database}/collections/{coll_id}/count",
                        headers=headers,
                    )
                    if count_resp.is_success:
                        resource.record_count = count_resp.json()
                except Exception:
                    warnings.append(f"Count unavailable for collection {coll_name}")

            resources.append(resource)

        vector_ready = len(resources) > 0
        if not vector_ready:
            warnings.append("No collections found")

        total = sum(r.record_count for r in resources if r.record_count is not None)

        return ConnectorTestResult(
            success=True,
            health_status="ok" if vector_ready else "degraded",
            authenticated=True,
            schema_discovered=True,
            vector_ready=vector_ready,
            server_version=server_version,
            resources=resources,
            resource_kind="collection",
            total_records=total if resources else None,
            approximate_counts=False,
            warnings=warnings,
        )


# ── Dispatch ──

TESTERS = {
    "pgvector": _test_pgvector,
    "supabase": _test_supabase,
    "neon": _test_neon,
    "pinecone": _test_pinecone,
    "opensearch": _test_opensearch,
    "weaviate": _test_weaviate,
    "qdrant": _test_qdrant,
    "milvus": _test_milvus,
    "chroma": _test_chroma,
}


async def run_connection_test(
    connector_type: str, config: dict
) -> ConnectorTestResult:
    """Run a bounded, read-only connection test for the given connector type."""
    tester = TESTERS.get(connector_type)
    if not tester:
        return _failed(f"Unknown connector type: {connector_type}")

    start = time.monotonic()
    try:
        result = await asyncio.wait_for(tester(config), timeout=OVERALL_TIMEOUT)
        result.latency_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "connector_test type=%s success=%s latency_ms=%d",
            connector_type,
            result.success,
            result.latency_ms,
        )
        if result.health_status == "degraded":
            logger.warning(
                "connector_test_degraded type=%s warnings=%s",
                connector_type,
                result.warnings,
            )
        return result
    except asyncio.TimeoutError:
        latency = int((time.monotonic() - start) * 1000)
        logger.error("connector_test_timeout type=%s", connector_type)
        return ConnectorTestResult(
            success=False,
            health_status="failed",
            error="Connection timed out after 10s",
            latency_ms=latency,
        )
    except asyncpg.InvalidPasswordError:
        latency = int((time.monotonic() - start) * 1000)
        logger.error("connector_test_auth_fail type=%s", connector_type)
        return ConnectorTestResult(
            success=False,
            health_status="failed",
            authenticated=False,
            error="Authentication failed — check credentials",
            latency_ms=latency,
        )
    except httpx.HTTPStatusError as e:
        latency = int((time.monotonic() - start) * 1000)
        if e.response.status_code in (401, 403):
            logger.error("connector_test_auth_fail type=%s", connector_type)
            return ConnectorTestResult(
                success=False,
                health_status="failed",
                authenticated=False,
                error="Authentication failed — check API key",
                latency_ms=latency,
            )
        logger.error(
            "connector_test_http_error type=%s status=%d",
            connector_type,
            e.response.status_code,
        )
        return ConnectorTestResult(
            success=False,
            health_status="failed",
            error=f"HTTP error {e.response.status_code}",
            latency_ms=latency,
        )
    except (OSError, ConnectionRefusedError, httpx.ConnectError):
        latency = int((time.monotonic() - start) * 1000)
        logger.error("connector_test_connect_fail type=%s", connector_type)
        return ConnectorTestResult(
            success=False,
            health_status="failed",
            error="Connection refused — check host and port",
            latency_ms=latency,
        )
    except Exception as e:
        latency = int((time.monotonic() - start) * 1000)
        logger.error(
            "connector_test_error type=%s error=%s", connector_type, str(e)
        )
        return ConnectorTestResult(
            success=False,
            health_status="failed",
            error=str(e),
            latency_ms=latency,
        )
