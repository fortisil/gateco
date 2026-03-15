"""Unit tests for connector testers — all I/O is mocked."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from gateco.services.connector_testers import (
    ConnectorTestResult,
    DiscoveredResource,
    run_connection_test,
)

# ── Helpers ──

def _mock_asyncpg_conn(version="PostgreSQL 16.2", tables=None):
    """Return a mock asyncpg connection."""
    conn = AsyncMock()
    conn.fetchval = AsyncMock(return_value=version)

    if tables is None:
        tables = [{"relname": "embeddings", "approx_count": 1000}]

    async def _fetch(query, *args):
        if "pg_class" in query and "LIMIT" in query:
            return tables
        return []

    async def _fetchval_fn(query, *args):
        if "SELECT version()" in query:
            return version
        if "SELECT count(*)" in query:
            return len(tables)
        return None

    conn.fetch = AsyncMock(side_effect=_fetch)
    conn.fetchval = AsyncMock(side_effect=_fetchval_fn)
    conn.close = AsyncMock()
    return conn


# ── Postgres family ──


@pytest.mark.asyncio
async def test_pgvector_success():
    conn = _mock_asyncpg_conn()
    with patch("gateco.services.connector_testers.asyncpg") as mock_asyncpg:
        mock_asyncpg.connect = AsyncMock(return_value=conn)
        mock_asyncpg.InvalidPasswordError = Exception
        result = await run_connection_test("pgvector", {
            "host": "localhost", "port": 5432, "database": "test_db"
        })
    assert result.success is True
    assert result.health_status == "ok"
    assert result.authenticated is True
    assert result.vector_ready is True
    assert result.resource_kind == "table"
    assert len(result.resources) == 1
    assert result.resources[0].name == "embeddings"


@pytest.mark.asyncio
async def test_pgvector_auth_fail():
    import asyncpg as real_asyncpg
    with patch("gateco.services.connector_testers.asyncpg") as mock_asyncpg:
        mock_asyncpg.connect = AsyncMock(
            side_effect=real_asyncpg.InvalidPasswordError("")
        )
        mock_asyncpg.InvalidPasswordError = real_asyncpg.InvalidPasswordError
        result = await run_connection_test("pgvector", {
            "host": "localhost", "port": 5432, "database": "test_db"
        })
    assert result.success is False
    assert result.health_status == "failed"
    assert result.authenticated is False
    assert "Authentication failed" in result.error


@pytest.mark.asyncio
async def test_pgvector_no_vector_tables():
    conn = _mock_asyncpg_conn(tables=[])
    with patch("gateco.services.connector_testers.asyncpg") as mock_asyncpg:
        mock_asyncpg.connect = AsyncMock(return_value=conn)
        mock_asyncpg.InvalidPasswordError = Exception
        result = await run_connection_test("pgvector", {
            "host": "localhost", "port": 5432, "database": "test_db"
        })
    assert result.success is True
    assert result.health_status == "degraded"
    assert result.vector_ready is False
    assert any("No vector-enabled tables" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_supabase_success():
    conn = _mock_asyncpg_conn()
    with patch("gateco.services.connector_testers.asyncpg") as mock_asyncpg:
        mock_asyncpg.connect = AsyncMock(return_value=conn)
        mock_asyncpg.InvalidPasswordError = Exception
        result = await run_connection_test("supabase", {
            "host": "db.abc.supabase.co", "database": "postgres", "password": "secret"
        })
    assert result.success is True
    assert result.health_status == "ok"


@pytest.mark.asyncio
async def test_neon_success():
    conn = _mock_asyncpg_conn()
    with patch("gateco.services.connector_testers.asyncpg") as mock_asyncpg:
        mock_asyncpg.connect = AsyncMock(return_value=conn)
        mock_asyncpg.InvalidPasswordError = Exception
        result = await run_connection_test("neon", {
            "connection_string": "postgresql://user:pass@ep-xyz.neon.tech/db"
        })
    assert result.success is True
    assert result.health_status == "ok"


@pytest.mark.asyncio
async def test_pgvector_timeout():
    async def _slow(*args, **kwargs):
        await asyncio.sleep(15)

    with patch("gateco.services.connector_testers.asyncpg") as mock_asyncpg:
        mock_asyncpg.connect = AsyncMock(side_effect=_slow)
        mock_asyncpg.InvalidPasswordError = Exception
        result = await run_connection_test("pgvector", {
            "host": "unreachable", "port": 5432, "database": "db"
        })
    assert result.success is False
    assert result.health_status == "failed"
    assert "timed out" in result.error


# ── Pinecone ──


@pytest.mark.asyncio
async def test_pinecone_success():
    indexes_response = httpx.Response(
        200,
        json={
            "indexes": [
                {
                    "name": "idx1", "dimension": 1536,
                    "metric": "cosine", "host": "idx1.svc.pinecone.io",
                }
            ]
        },
        request=httpx.Request("GET", "https://api.pinecone.io/indexes"),
    )
    stats_response = httpx.Response(
        200,
        json={"totalRecordCount": 50000, "dimension": 1536},
        request=httpx.Request("POST", "https://idx1.svc.pinecone.io/describe_index_stats"),
    )

    with patch("gateco.services.connector_testers.httpx.AsyncClient") as mock_client:
        client = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        client.get = AsyncMock(return_value=indexes_response)
        client.post = AsyncMock(return_value=stats_response)
        mock_client.return_value = client

        result = await run_connection_test("pinecone", {"api_key": "test-key"})

    assert result.success is True
    assert result.health_status == "ok"
    assert result.resource_kind == "index"
    assert len(result.resources) == 1
    assert result.resources[0].dimension == 1536


@pytest.mark.asyncio
async def test_pinecone_auth_fail():
    resp = httpx.Response(
        401,
        json={"error": "Unauthorized"},
        request=httpx.Request("GET", "https://api.pinecone.io/indexes"),
    )

    with patch("gateco.services.connector_testers.httpx.AsyncClient") as mock_client:
        client = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        client.get = AsyncMock(return_value=resp)
        # Make the response raise on raise_for_status
        resp.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("", request=resp.request, response=resp)
        )
        mock_client.return_value = client

        result = await run_connection_test("pinecone", {"api_key": "bad-key"})

    assert result.success is False
    assert result.authenticated is False


# ── OpenSearch ──


@pytest.mark.asyncio
async def test_opensearch_success():
    info_resp = httpx.Response(
        200,
        json={"version": {"number": "2.11.0"}, "cluster_name": "test"},
        request=httpx.Request("GET", "https://os.example.com/"),
    )
    cat_resp = httpx.Response(
        200,
        json=[{"index": "vectors", "docs.count": "10000"}],
        request=httpx.Request("GET", "https://os.example.com/_cat/indices"),
    )
    mapping_resp = httpx.Response(
        200,
        json={"vectors": {"mappings": {"properties": {"embedding": {"type": "knn_vector"}}}}},
        request=httpx.Request("GET", "https://os.example.com/vectors/_mapping"),
    )

    with patch("gateco.services.connector_testers.httpx.AsyncClient") as mock_client:
        client = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)

        async def _get(url, **kwargs):
            if url.endswith("/"):
                return info_resp
            if "_cat" in url:
                return cat_resp
            if "_mapping" in url:
                return mapping_resp
            return info_resp

        client.get = AsyncMock(side_effect=_get)
        mock_client.return_value = client

        result = await run_connection_test("opensearch", {
            "host": "https://os.example.com", "api_key": "test-key"
        })

    assert result.success is True
    assert result.health_status == "ok"
    assert result.vector_ready is True
    assert result.server_version == "2.11.0"


# ── Weaviate ──


@pytest.mark.asyncio
async def test_weaviate_success():
    meta_resp = httpx.Response(
        200,
        json={"version": "1.24.0", "hostname": "test"},
        request=httpx.Request("GET", "https://wv.example.com/v1/meta"),
    )
    schema_resp = httpx.Response(
        200,
        json={"classes": [{"class": "Document", "properties": []}]},
        request=httpx.Request("GET", "https://wv.example.com/v1/schema"),
    )
    gql_resp = httpx.Response(
        200,
        json={"data": {"Aggregate": {"Document": [{"meta": {"count": 500}}]}}},
        request=httpx.Request("POST", "https://wv.example.com/v1/graphql"),
    )

    with patch("gateco.services.connector_testers.httpx.AsyncClient") as mock_client:
        client = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)

        async def _get(url, **kwargs):
            if "meta" in url:
                return meta_resp
            return schema_resp

        client.get = AsyncMock(side_effect=_get)
        client.post = AsyncMock(return_value=gql_resp)
        mock_client.return_value = client

        result = await run_connection_test("weaviate", {
            "host": "https://wv.example.com", "api_key": "test-key"
        })

    assert result.success is True
    assert result.health_status == "ok"
    assert result.resource_kind == "class"
    assert result.resources[0].record_count == 500


# ── Qdrant ──


@pytest.mark.asyncio
async def test_qdrant_success():
    list_resp = httpx.Response(
        200,
        json={"result": {"collections": [{"name": "my-coll"}]}},
        request=httpx.Request("GET", "https://qdrant.example.com/collections"),
    )
    detail_resp = httpx.Response(
        200,
        json={
            "result": {
                "points_count": 2000,
                "config": {"params": {"vectors": {"size": 768, "distance": "Cosine"}}},
            }
        },
        request=httpx.Request("GET", "https://qdrant.example.com/collections/my-coll"),
    )

    with patch("gateco.services.connector_testers.httpx.AsyncClient") as mock_client:
        client = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)

        async def _get(url, **kwargs):
            if url.endswith("/collections"):
                return list_resp
            return detail_resp

        client.get = AsyncMock(side_effect=_get)
        mock_client.return_value = client

        result = await run_connection_test("qdrant", {
            "host": "https://qdrant.example.com"
        })

    assert result.success is True
    assert result.health_status == "ok"
    assert result.resource_kind == "collection"
    assert result.resources[0].dimension == 768


# ── Milvus ──


@pytest.mark.asyncio
async def test_milvus_success():
    list_resp = httpx.Response(
        200,
        json={"data": ["docs"]},
        request=httpx.Request("POST", "https://milvus.example.com:19530/v2/vectordb/collections/list"),
    )
    desc_resp = httpx.Response(
        200,
        json={
            "data": {
                "schema": {
                    "fields": [{"name": "vector", "type_params": {"dim": "384"}}]
                }
            }
        },
        request=httpx.Request("POST", "https://milvus.example.com:19530/v2/vectordb/collections/describe"),
    )

    with patch("gateco.services.connector_testers.httpx.AsyncClient") as mock_client:
        client = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        client.post = AsyncMock(side_effect=[list_resp, desc_resp])
        mock_client.return_value = client

        result = await run_connection_test("milvus", {
            "host": "https://milvus.example.com", "port": 19530
        })

    assert result.success is True
    assert result.health_status == "ok"
    assert result.resource_kind == "collection"


@pytest.mark.asyncio
async def test_milvus_v2_not_available():
    resp_404 = httpx.Response(
        404,
        json={},
        request=httpx.Request("POST", "https://milvus.example.com:19530/v2/vectordb/collections/list"),
    )

    with patch("gateco.services.connector_testers.httpx.AsyncClient") as mock_client:
        client = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        client.post = AsyncMock(return_value=resp_404)
        mock_client.return_value = client

        result = await run_connection_test("milvus", {
            "host": "https://milvus.example.com", "port": 19530
        })

    assert result.success is True
    assert result.health_status == "degraded"
    assert any("v2 not available" in w for w in result.warnings)


# ── Chroma ──


@pytest.mark.asyncio
async def test_chroma_success():
    ver_resp = httpx.Response(
        200,
        json={"version": "0.4.15"},
        request=httpx.Request("GET", "http://localhost:8000/api/v2/version"),
    )
    coll_resp = httpx.Response(
        200,
        json=[{"name": "docs", "id": "abc-123"}],
        request=httpx.Request("GET", "http://localhost:8000/api/v2/tenants/default_tenant/databases/default_database/collections"),
    )
    count_resp = httpx.Response(
        200,
        json=42,
        request=httpx.Request("GET", "http://localhost:8000/api/v2/tenants/default_tenant/databases/default_database/collections/abc-123/count"),
    )
    heartbeat_resp = httpx.Response(
        200,
        json={"nanosecond heartbeat": 1234},
        request=httpx.Request("GET", "http://localhost:8000/api/v2/heartbeat"),
    )

    with patch("gateco.services.connector_testers.httpx.AsyncClient") as mock_client:
        client = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)

        async def _get(url, **kwargs):
            if "heartbeat" in url:
                return heartbeat_resp
            if "version" in url:
                return ver_resp
            if "count" in url:
                return count_resp
            if "collections" in url:
                return coll_resp
            return heartbeat_resp

        client.get = AsyncMock(side_effect=_get)
        mock_client.return_value = client

        result = await run_connection_test("chroma", {
            "host": "http://localhost:8000"
        })

    assert result.success is True
    assert result.health_status == "ok"
    assert result.resource_kind == "collection"
    assert result.resources[0].record_count == 42


# ── Edge cases ──


@pytest.mark.asyncio
async def test_unknown_connector_type():
    result = await run_connection_test("nonexistent", {})
    assert result.success is False
    assert result.health_status == "failed"
    assert "Unknown" in result.error


@pytest.mark.asyncio
async def test_connection_refused():
    with patch("gateco.services.connector_testers.httpx.AsyncClient") as mock_client:
        client = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        client.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        mock_client.return_value = client

        result = await run_connection_test("qdrant", {
            "host": "https://unreachable:6333"
        })

    assert result.success is False
    assert result.health_status == "failed"
    assert "Connection refused" in result.error


@pytest.mark.asyncio
async def test_to_dict_no_secrets():
    result = ConnectorTestResult(
        success=True,
        health_status="ok",
        authenticated=True,
        schema_discovered=True,
        vector_ready=True,
        resources=[
            DiscoveredResource(name="test", record_count=100, dimension=768)
        ],
        resource_kind="collection",
    )
    d = result.to_dict()
    assert "api_key" not in str(d)
    assert "password" not in str(d)
    assert d["resources"][0]["name"] == "test"
    assert d["resources"][0]["dimension"] == 768
