"""Tests for connector_adapters — vector search for all 9 connector types."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gateco.services.connector_adapters import (
    _validate_identifier,
    execute_vector_search,
)

# ── Identifier validation ──


def test_validate_identifier_valid():
    _validate_identifier("embeddings", "table")
    _validate_identifier("my_table_123", "table")
    _validate_identifier("_private", "table")


def test_validate_identifier_invalid():
    with pytest.raises(ValueError):
        _validate_identifier("DROP TABLE --", "table")
    with pytest.raises(ValueError):
        _validate_identifier("123bad", "table")
    with pytest.raises(ValueError):
        _validate_identifier("table.name", "table")
    with pytest.raises(ValueError):
        _validate_identifier("name;", "table")


# ── Postgres family ──


@pytest.fixture
def pg_config():
    return {
        "host": "localhost", "port": 5432, "database": "test",
        "user": "postgres", "password": "pass",
    }


@pytest.fixture
def pg_search_config():
    return {
        "table_name": "embeddings",
        "vector_column": "embedding",
        "id_column": "id",
        "content_column": "content",
        "metric": "cosine",
    }


@pytest.mark.asyncio
async def test_search_pgvector_success(pg_config, pg_search_config):
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[
        {"id": "vec_1", "score": 0.95, "content": "hello world"},
        {"id": "vec_2", "score": 0.87, "content": "foo bar"},
    ])

    with patch("gateco.services.connector_adapters.asyncpg") as mock_asyncpg:
        mock_asyncpg.connect = AsyncMock(return_value=mock_conn)
        mock_asyncpg.InvalidPasswordError = Exception

        result = await execute_vector_search(
            "pgvector", pg_config, pg_search_config, [0.1] * 1536, 10
        )

    assert result.error_category is None
    assert len(result.results) == 2
    assert result.results[0].vector_id == "vec_1"
    assert result.results[0].score == 0.95
    assert result.results[0].text == "hello world"
    assert result.results[1].vector_id == "vec_2"
    assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_search_pgvector_auth_failure(pg_config, pg_search_config):
    import asyncpg as real_asyncpg

    with patch("gateco.services.connector_adapters.asyncpg") as mock_asyncpg:
        mock_asyncpg.connect = AsyncMock(
            side_effect=real_asyncpg.InvalidPasswordError("bad password"),
        )
        mock_asyncpg.InvalidPasswordError = real_asyncpg.InvalidPasswordError

        result = await execute_vector_search(
            "pgvector", pg_config, pg_search_config, [0.1] * 1536, 10
        )

    assert result.error_category == "connector_auth_failed"
    assert len(result.results) == 0


@pytest.mark.asyncio
async def test_search_pgvector_missing_config():
    result = await execute_vector_search(
        "pgvector", {"host": "x"}, {"table_name": "t"}, [0.1], 10
    )
    # Missing vector_column and id_column
    assert result.error_category == "search_config_invalid"


@pytest.mark.asyncio
async def test_search_pgvector_l2_metric(pg_config):
    """Test L2 distance metric produces correct SQL."""
    search_config = {
        "table_name": "embeddings",
        "vector_column": "embedding",
        "id_column": "id",
        "metric": "l2",
    }
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[
        {"id": "vec_1", "score": 0.5},
    ])

    with patch("gateco.services.connector_adapters.asyncpg") as mock_asyncpg:
        mock_asyncpg.connect = AsyncMock(return_value=mock_conn)
        mock_asyncpg.InvalidPasswordError = Exception

        result = await execute_vector_search("pgvector", pg_config, search_config, [0.1] * 3, 5)

    assert len(result.results) == 1
    # Verify the SQL used <-> operator for L2
    call_args = mock_conn.fetch.call_args
    sql = call_args[0][0]
    assert "<->" in sql


# ── Pinecone ──


@pytest.mark.asyncio
async def test_search_pinecone_success():
    config = {"api_key": "test-key"}
    search_config = {"index_name": "my-index"}

    mock_responses = [
        # GET /indexes/my-index
        MagicMock(
            status_code=200,
            json=MagicMock(return_value={"host": "my-index-abc.svc.pinecone.io"}),
            raise_for_status=MagicMock(),
        ),
        # POST /query
        MagicMock(
            status_code=200,
            json=MagicMock(return_value={
                "matches": [
                    {"id": "p1", "score": 0.92, "metadata": {"text": "hello"}},
                    {"id": "p2", "score": 0.85, "metadata": {"text": "world"}},
                ]
            }),
            raise_for_status=MagicMock(),
        ),
    ]

    with patch("gateco.services.connector_adapters.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_responses[0])
        mock_client.post = AsyncMock(return_value=mock_responses[1])
        mock_client_cls.return_value = mock_client

        result = await execute_vector_search("pinecone", config, search_config, [0.1] * 1536, 10)

    assert result.error_category is None
    assert len(result.results) == 2
    assert result.results[0].score == 0.92


# ── Qdrant ──


@pytest.mark.asyncio
async def test_search_qdrant_success():
    config = {"host": "https://qdrant.example.com"}
    search_config = {"collection_name": "docs"}

    mock_resp = MagicMock(
        status_code=200,
        json=MagicMock(return_value={
            "result": [
                {"id": "q1", "score": 0.91, "payload": {"text": "doc1"}},
                {"id": "q2", "score": 0.88, "payload": {"text": "doc2"}},
            ]
        }),
        raise_for_status=MagicMock(),
    )

    with patch("gateco.services.connector_adapters.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        result = await execute_vector_search("qdrant", config, search_config, [0.1] * 768, 10)

    assert result.error_category is None
    assert len(result.results) == 2
    assert result.results[0].score == 0.91


# ── OpenSearch ──


@pytest.mark.asyncio
async def test_search_opensearch_success():
    config = {"host": "https://opensearch.example.com", "api_key": "test-key"}
    search_config = {"index_name": "vectors", "vector_field": "embedding"}

    mock_resp = MagicMock(
        status_code=200,
        json=MagicMock(return_value={
            "hits": {
                "hits": [
                    {"_id": "os1", "_score": 0.95, "_source": {"text": "result1"}},
                ]
            }
        }),
        raise_for_status=MagicMock(),
    )

    with patch("gateco.services.connector_adapters.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        result = await execute_vector_search("opensearch", config, search_config, [0.1] * 1536, 10)

    assert result.error_category is None
    assert len(result.results) == 1
    assert result.results[0].score == 0.95


# ── Weaviate ──


@pytest.mark.asyncio
async def test_search_weaviate_success():
    config = {"host": "https://weaviate.example.com", "api_key": "key"}
    search_config = {"class_name": "Document", "properties": ["content"]}

    mock_resp = MagicMock(
        status_code=200,
        json=MagicMock(return_value={
            "data": {
                "Get": {
                    "Document": [
                        {"content": "hello", "_additional": {"id": "w1", "distance": 0.1}},
                    ]
                }
            }
        }),
        raise_for_status=MagicMock(),
    )

    with patch("gateco.services.connector_adapters.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        result = await execute_vector_search("weaviate", config, search_config, [0.1] * 1536, 10)

    assert result.error_category is None
    assert len(result.results) == 1
    # score = 1.0 - 0.1 = 0.9
    assert abs(result.results[0].score - 0.9) < 0.01


# ── Chroma ──


@pytest.mark.asyncio
async def test_search_chroma_success():
    config = {"host": "http://localhost:8000"}
    search_config = {"collection_name": "docs"}

    mock_list_resp = MagicMock(
        status_code=200,
        json=MagicMock(return_value=[{"name": "docs", "id": "coll-123"}]),
        raise_for_status=MagicMock(),
    )
    mock_query_resp = MagicMock(
        status_code=200,
        json=MagicMock(return_value={
            "ids": [["c1", "c2"]],
            "distances": [[0.1, 0.5]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{}, {}]],
        }),
        raise_for_status=MagicMock(),
    )

    with patch("gateco.services.connector_adapters.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_list_resp)
        mock_client.post = AsyncMock(return_value=mock_query_resp)
        mock_client_cls.return_value = mock_client

        result = await execute_vector_search("chroma", config, search_config, [0.1] * 384, 10)

    assert result.error_category is None
    assert len(result.results) == 2
    # score = 1/(1+0.1) ≈ 0.909
    assert result.results[0].score > 0.9


# ── Milvus ──


@pytest.mark.asyncio
async def test_search_milvus_success():
    config = {"host": "https://milvus.example.com", "token": "tok"}
    search_config = {"collection_name": "docs"}

    mock_resp = MagicMock(
        status_code=200,
        json=MagicMock(return_value={
            "data": [
                {"id": "m1", "distance": 0.1, "content": "hello"},
                {"id": "m2", "distance": 0.3, "content": "world"},
            ]
        }),
        raise_for_status=MagicMock(),
    )

    with patch("gateco.services.connector_adapters.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        result = await execute_vector_search("milvus", config, search_config, [0.1] * 384, 10)

    assert result.error_category is None
    assert len(result.results) == 2
    # score = 1/(1+0.1) ≈ 0.909
    assert result.results[0].score > 0.9


# ── Timeout handling ──


@pytest.mark.asyncio
async def test_search_timeout():
    async def slow_search(*args, **kwargs):
        await asyncio.sleep(20)

    searchers = {"pgvector": lambda *a: slow_search(*a)}
    with patch("gateco.services.connector_adapters.SEARCHERS", searchers):
        with patch("gateco.services.connector_adapters.OVERALL_TIMEOUT", 0.01):
            result = await execute_vector_search("pgvector", {}, {}, [0.1], 10)

    assert result.error_category == "connector_timeout"


# ── Connection refused ──


@pytest.mark.asyncio
async def test_search_connection_refused():
    import httpx

    with patch("gateco.services.connector_adapters.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client_cls.return_value = mock_client

        result = await execute_vector_search(
            "qdrant",
            {"host": "http://localhost:6333"},
            {"collection_name": "test"},
            [0.1] * 3,
            10,
        )

    assert result.error_category == "connector_unreachable"


# ── Result ordering preservation ──


@pytest.mark.asyncio
async def test_result_ordering_preserved():
    config = {"host": "https://qdrant.example.com"}
    search_config = {"collection_name": "docs"}

    ordered_results = [
        {"id": f"q{i}", "score": 1.0 - i * 0.1, "payload": {"text": f"doc{i}"}}
        for i in range(5)
    ]

    mock_resp = MagicMock(
        status_code=200,
        json=MagicMock(return_value={"result": ordered_results}),
        raise_for_status=MagicMock(),
    )

    with patch("gateco.services.connector_adapters.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        result = await execute_vector_search("qdrant", config, search_config, [0.1] * 768, 10)

    scores = [r.score for r in result.results]
    assert scores == sorted(scores, reverse=True), "Results should preserve descending score order"


# ── Unknown connector type ──


@pytest.mark.asyncio
async def test_unknown_connector_type():
    result = await execute_vector_search("unknown_db", {}, {}, [0.1], 10)
    assert result.error_category == "search_config_invalid"
