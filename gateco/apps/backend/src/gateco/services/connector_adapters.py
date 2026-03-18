"""Vector search adapters for all supported connector types.

Each adapter executes a bounded vector search against the external vector DB
and returns normalized results (higher score = better, 0.0-1.0 range preferred).
Mirrors connector_testers.py structure.
"""

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field

import asyncpg
import httpx

from gateco.services.connector_testers import _build_pgvector_dsn

logger = logging.getLogger(__name__)

PER_CALL_TIMEOUT = 4.0
OVERALL_TIMEOUT = 10.0

# Identifier validation for SQL injection prevention
_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def _validate_identifier(name: str, label: str = "identifier") -> None:
    """Validate a SQL identifier against injection."""
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid {label}: {name!r}")


@dataclass
class VectorSearchResult:
    """A single result from a vector search."""

    vector_id: str
    score: float  # normalized: higher = better
    text: str | None = None
    metadata: dict | None = None


@dataclass
class VectorSearchResponse:
    """Aggregated response from a vector search."""

    results: list[VectorSearchResult] = field(default_factory=list)
    latency_ms: int = 0
    warnings: list[str] = field(default_factory=list)
    error_category: str | None = None


def _error_response(category: str, warning: str) -> VectorSearchResponse:
    return VectorSearchResponse(error_category=category, warnings=[warning])


# ── Postgres family (pgvector, supabase, neon) ──


async def _search_postgres(
    config: dict, search_config: dict, query_vector: list[float], top_k: int,
) -> VectorSearchResponse:
    """Shared searcher for all Postgres-based connectors (pgvector, supabase, neon)."""
    table_name = search_config.get("table_name")
    vector_column = search_config.get("vector_column")
    id_column = search_config.get("id_column")
    content_column = search_config.get("content_column")
    metric = search_config.get("metric", "cosine")

    if not table_name or not vector_column or not id_column:
        return _error_response(
            "search_config_invalid",
            "Missing table_name, vector_column, or id_column",
        )

    _validate_identifier(table_name, "table_name")
    _validate_identifier(vector_column, "vector_column")
    _validate_identifier(id_column, "id_column")
    if content_column:
        _validate_identifier(content_column, "content_column")

    # Build DSN
    if "connection_string" in config:
        dsn = config["connection_string"]
    else:
        dsn = _build_pgvector_dsn(config)

    # Build query based on metric
    content_select = f", {content_column}" if content_column else ""
    if metric == "l2":
        score_expr = f"1.0 / (1.0 + ({vector_column} <-> $1::vector))"
        order_expr = f"{vector_column} <-> $1::vector"
    elif metric == "inner_product":
        score_expr = f"({vector_column} <#> $1::vector) * -1"
        order_expr = f"{vector_column} <#> $1::vector"
    else:
        # cosine (default)
        score_expr = f"1 - ({vector_column} <=> $1::vector)"
        order_expr = f"{vector_column} <=> $1::vector"

    # Optional metadata columns for inline resolution
    metadata_columns = search_config.get("metadata_columns") or []
    meta_select = ""
    if metadata_columns:
        for mc in metadata_columns:
            _validate_identifier(mc, "metadata_column")
        meta_select = ", " + ", ".join(metadata_columns)

    sql = (
        f"SELECT {id_column}, {score_expr} AS score{content_select}{meta_select} "
        f"FROM {table_name} "
        f"ORDER BY {order_expr} LIMIT $2"
    )

    conn = await asyncpg.connect(dsn, timeout=PER_CALL_TIMEOUT)
    try:
        vector_str = f"[{','.join(str(v) for v in query_vector)}]"
        rows = await conn.fetch(sql, vector_str, top_k)

        results = []
        for row in rows:
            text = row.get(content_column) if content_column else None
            meta = None
            if metadata_columns:
                meta = {mc: row.get(mc) for mc in metadata_columns if row.get(mc) is not None}
            results.append(VectorSearchResult(
                vector_id=str(row[id_column]),
                score=float(row["score"]),
                text=text,
                metadata=meta if meta else None,
            ))
        return VectorSearchResponse(results=results)
    finally:
        await conn.close()


async def _search_pgvector(
    config: dict, search_config: dict, query_vector: list[float], top_k: int,
) -> VectorSearchResponse:
    return await _search_postgres(config, search_config, query_vector, top_k)


async def _search_supabase(
    config: dict, search_config: dict, query_vector: list[float], top_k: int,
) -> VectorSearchResponse:
    return await _search_postgres(config, search_config, query_vector, top_k)


async def _search_neon(
    config: dict, search_config: dict, query_vector: list[float], top_k: int,
) -> VectorSearchResponse:
    return await _search_postgres(config, search_config, query_vector, top_k)


# ── Pinecone ──


async def _search_pinecone(
    config: dict, search_config: dict, query_vector: list[float], top_k: int,
) -> VectorSearchResponse:
    api_key = config["api_key"]
    index_name = search_config.get("index_name") or config.get("index_name")
    namespace = search_config.get("namespace", "")

    if not index_name:
        return _error_response("search_config_invalid", "Missing index_name")

    headers = {"Api-Key": api_key, "X-Pinecone-API-Version": "2024-07"}

    async with httpx.AsyncClient(timeout=PER_CALL_TIMEOUT) as client:
        # Get index host
        resp = await client.get(f"https://api.pinecone.io/indexes/{index_name}", headers=headers)
        resp.raise_for_status()
        index_host = resp.json().get("host")
        if not index_host:
            return _error_response(
                "search_config_invalid",
                f"Cannot resolve host for index {index_name}",
            )

        # Query
        body: dict = {"vector": query_vector, "topK": top_k, "includeMetadata": True}
        if namespace:
            body["namespace"] = namespace

        query_resp = await client.post(f"https://{index_host}/query", headers=headers, json=body)
        query_resp.raise_for_status()
        matches = query_resp.json().get("matches", [])

        results = [
            VectorSearchResult(
                vector_id=m["id"],
                score=float(m.get("score", 0)),
                text=m.get("metadata", {}).get("text"),
                metadata=m.get("metadata"),
            )
            for m in matches
        ]
        return VectorSearchResponse(results=results)


# ── Qdrant ──


async def _search_qdrant(
    config: dict, search_config: dict, query_vector: list[float], top_k: int,
) -> VectorSearchResponse:
    host = config["host"].rstrip("/")
    api_key = config.get("api_key")
    collection_name = search_config.get("collection_name") or config.get("collection_name")

    if not collection_name:
        return _error_response("search_config_invalid", "Missing collection_name")

    headers = {}
    if api_key:
        headers["api-key"] = api_key

    async with httpx.AsyncClient(timeout=PER_CALL_TIMEOUT) as client:
        resp = await client.post(
            f"{host}/collections/{collection_name}/points/search",
            headers=headers,
            json={"vector": query_vector, "limit": top_k, "with_payload": True},
        )
        resp.raise_for_status()
        points = resp.json().get("result", [])

        results = [
            VectorSearchResult(
                vector_id=str(p["id"]),
                score=float(p.get("score", 0)),
                text=p.get("payload", {}).get("text"),
                metadata=p.get("payload"),
            )
            for p in points
        ]
        return VectorSearchResponse(results=results)


# ── Weaviate ──


async def _search_weaviate(
    config: dict, search_config: dict, query_vector: list[float], top_k: int,
) -> VectorSearchResponse:
    host = config["host"].rstrip("/")
    api_key = config.get("api_key")
    class_name = search_config.get("class_name") or config.get("class_name")
    properties = search_config.get("properties", ["content"])

    if not class_name:
        return _error_response("search_config_invalid", "Missing class_name")

    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    props_str = " ".join(properties)
    gql = (
        "{ Get { " + class_name + "("
        f"nearVector: {{vector: {query_vector}}}, limit: {top_k}"
        ") { " + props_str + " _additional { id distance } } } }"
    )

    async with httpx.AsyncClient(timeout=PER_CALL_TIMEOUT) as client:
        resp = await client.post(f"{host}/v1/graphql", headers=headers, json={"query": gql})
        resp.raise_for_status()
        data = resp.json().get("data", {}).get("Get", {}).get(class_name, [])

        results = []
        for obj in data:
            additional = obj.get("_additional", {})
            distance = float(additional.get("distance", 1.0))
            score = 1.0 - distance  # cosine: score = 1 - distance
            text = obj.get(properties[0]) if properties else None
            results.append(VectorSearchResult(
                vector_id=str(additional.get("id", "")),
                score=max(0.0, score),
                text=text,
                metadata={k: v for k, v in obj.items() if k != "_additional"},
            ))
        return VectorSearchResponse(results=results)


# ── Milvus ──


async def _search_milvus(
    config: dict, search_config: dict, query_vector: list[float], top_k: int,
) -> VectorSearchResponse:
    host = config["host"].rstrip("/")
    port = config.get("port", 19530)
    token = config.get("token")
    collection_name = search_config.get("collection_name") or config.get("collection_name")
    vector_field = search_config.get("vector_field", "embedding")
    output_fields = search_config.get("output_fields", ["content"])

    if not collection_name:
        return _error_response("search_config_invalid", "Missing collection_name")

    if "://" not in host:
        host = f"https://{host}"
    base = f"{host}:{port}" if ":" not in host.split("://")[1] else host

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = {
        "collectionName": collection_name,
        "data": [query_vector],
        "limit": top_k,
        "outputFields": output_fields,
        "annsField": vector_field,
    }

    async with httpx.AsyncClient(timeout=PER_CALL_TIMEOUT) as client:
        resp = await client.post(f"{base}/v2/vectordb/entities/search", headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json().get("data", [])

        results = []
        for item in data:
            distance = float(item.get("distance", 0))
            score = 1.0 / (1.0 + abs(distance)) if distance >= 0 else abs(distance)
            text = item.get("content") or item.get(output_fields[0]) if output_fields else None
            results.append(VectorSearchResult(
                vector_id=str(item.get("id", "")),
                score=score,
                text=text,
                metadata={k: v for k, v in item.items() if k not in ("id", "distance")},
            ))
        return VectorSearchResponse(results=results)


# ── Chroma ──


async def _search_chroma(
    config: dict, search_config: dict, query_vector: list[float], top_k: int,
) -> VectorSearchResponse:
    host = config["host"].rstrip("/")
    api_key = config.get("api_key")
    tenant = config.get("tenant", "default_tenant")
    database = config.get("database", "default_database")
    collection_name = search_config.get("collection_name")

    if not collection_name:
        return _error_response("search_config_invalid", "Missing collection_name")

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async with httpx.AsyncClient(timeout=PER_CALL_TIMEOUT) as client:
        # Resolve collection ID
        coll_resp = await client.get(
            f"{host}/api/v2/tenants/{tenant}/databases/{database}/collections",
            headers=headers,
        )
        coll_resp.raise_for_status()
        collections = coll_resp.json()
        coll_id = None
        for c in collections:
            if c.get("name") == collection_name:
                coll_id = c.get("id")
                break
        if not coll_id:
            return _error_response(
                "search_config_invalid",
                f"Collection {collection_name!r} not found",
            )

        # Query
        query_resp = await client.post(
            f"{host}/api/v2/tenants/{tenant}/databases/{database}/collections/{coll_id}/query",
            headers=headers,
            json={"query_embeddings": [query_vector], "n_results": top_k},
        )
        query_resp.raise_for_status()
        resp_data = query_resp.json()

        ids = (resp_data.get("ids") or [[]])[0]
        distances = (resp_data.get("distances") or [[]])[0]
        documents = (resp_data.get("documents") or [[]])[0]
        metadatas = (resp_data.get("metadatas") or [[]])[0]

        results = []
        for i, vid in enumerate(ids):
            dist = distances[i] if i < len(distances) else 0
            score = 1.0 / (1.0 + dist)
            text = documents[i] if i < len(documents) else None
            meta = metadatas[i] if i < len(metadatas) else None
            results.append(VectorSearchResult(
                vector_id=str(vid),
                score=score,
                text=text,
                metadata=meta,
            ))
        return VectorSearchResponse(results=results)


# ── OpenSearch ──


async def _search_opensearch(
    config: dict, search_config: dict, query_vector: list[float], top_k: int,
) -> VectorSearchResponse:
    host = config["host"].rstrip("/")
    api_key = config["api_key"]
    index_name = search_config.get("index_name") or config.get("index_name")
    vector_field = search_config.get("vector_field")

    if not index_name:
        return _error_response("search_config_invalid", "Missing index_name")
    if not vector_field:
        return _error_response("search_config_invalid", "Missing vector_field")

    headers = {"Authorization": f"ApiKey {api_key}"}

    body = {
        "size": top_k,
        "query": {
            "knn": {
                vector_field: {
                    "vector": query_vector,
                    "k": top_k,
                }
            }
        },
    }

    async with httpx.AsyncClient(timeout=PER_CALL_TIMEOUT) as client:
        resp = await client.post(f"{host}/{index_name}/_search", headers=headers, json=body)
        resp.raise_for_status()
        hits = resp.json().get("hits", {}).get("hits", [])

        results = []
        for hit in hits:
            source = hit.get("_source", {})
            results.append(VectorSearchResult(
                vector_id=str(hit.get("_id", "")),
                score=float(hit.get("_score", 0)),
                text=source.get("text") or source.get("content"),
                metadata={k: v for k, v in source.items() if k != vector_field},
            ))
        return VectorSearchResponse(results=results)


# ── Dispatch ──


SEARCHERS: dict[str, callable] = {
    "pgvector": _search_pgvector,
    "supabase": _search_supabase,
    "neon": _search_neon,
    "pinecone": _search_pinecone,
    "opensearch": _search_opensearch,
    "weaviate": _search_weaviate,
    "qdrant": _search_qdrant,
    "milvus": _search_milvus,
    "chroma": _search_chroma,
}


async def list_vector_ids(
    connector_type: str,
    config: dict,
    search_config: dict,
    scan_limit: int = 1000,
) -> list[str]:
    """List vector IDs from a Tier 1 connector for retroactive registration.

    Args:
        connector_type: Type of the connector (e.g. "pgvector").
        config: Decrypted connector config.
        search_config: Connector search configuration.
        scan_limit: Maximum number of IDs to return.

    Returns:
        List of vector ID strings.

    Raises:
        ValueError: If connector type is not supported for listing.
    """
    lister = LISTERS.get(connector_type)
    if not lister:
        raise ValueError(
            f"Connector type '{connector_type}' is not supported for retroactive registration"
        )
    return await lister(config, search_config, scan_limit)


# ── List vector IDs adapters ──


async def _list_postgres_ids(
    config: dict, search_config: dict, scan_limit: int,
) -> list[str]:
    """List vector IDs from a Postgres-based connector."""
    table_name = search_config.get("table_name")
    id_column = search_config.get("id_column")

    if not table_name or not id_column:
        raise ValueError("Missing table_name or id_column in search_config")

    _validate_identifier(table_name, "table_name")
    _validate_identifier(id_column, "id_column")

    if "connection_string" in config:
        dsn = config["connection_string"]
    else:
        dsn = _build_pgvector_dsn(config)

    conn = await asyncpg.connect(dsn, timeout=PER_CALL_TIMEOUT)
    try:
        sql = f"SELECT {id_column} FROM {table_name} LIMIT $1"
        rows = await conn.fetch(sql, scan_limit)
        return [str(row[id_column]) for row in rows]
    finally:
        await conn.close()


async def _list_pinecone_ids(
    config: dict, search_config: dict, scan_limit: int,
) -> list[str]:
    """List vector IDs from Pinecone using the list endpoint with pagination."""
    api_key = config["api_key"]
    index_name = search_config.get("index_name") or config.get("index_name")
    namespace = search_config.get("namespace", "")

    if not index_name:
        raise ValueError("Missing index_name in search_config")

    headers = {"Api-Key": api_key, "X-Pinecone-API-Version": "2024-07"}

    async with httpx.AsyncClient(timeout=PER_CALL_TIMEOUT) as client:
        # Get index host
        resp = await client.get(
            f"https://api.pinecone.io/indexes/{index_name}", headers=headers,
        )
        resp.raise_for_status()
        index_host = resp.json().get("host")
        if not index_host:
            raise ValueError(f"Cannot resolve host for Pinecone index {index_name}")

        # List vectors with pagination
        all_ids: list[str] = []
        params: dict = {"limit": min(scan_limit, 100)}
        if namespace:
            params["namespace"] = namespace

        while len(all_ids) < scan_limit:
            list_resp = await client.get(
                f"https://{index_host}/vectors/list",
                headers=headers,
                params=params,
            )
            list_resp.raise_for_status()
            data = list_resp.json()
            vectors = data.get("vectors", [])
            for v in vectors:
                all_ids.append(v.get("id", ""))
                if len(all_ids) >= scan_limit:
                    break

            pagination = data.get("pagination")
            if not pagination or not pagination.get("next"):
                break
            params["paginationToken"] = pagination["next"]

        return all_ids[:scan_limit]


async def _list_qdrant_ids(
    config: dict, search_config: dict, scan_limit: int,
) -> list[str]:
    """List vector IDs from Qdrant using the scroll endpoint."""
    host = config["host"].rstrip("/")
    api_key = config.get("api_key")
    collection_name = search_config.get("collection_name") or config.get("collection_name")

    if not collection_name:
        raise ValueError("Missing collection_name in search_config")

    headers = {}
    if api_key:
        headers["api-key"] = api_key

    all_ids: list[str] = []
    offset = None

    async with httpx.AsyncClient(timeout=PER_CALL_TIMEOUT) as client:
        while len(all_ids) < scan_limit:
            body: dict = {
                "limit": min(scan_limit - len(all_ids), 100),
                "with_payload": False,
                "with_vector": False,
            }
            if offset is not None:
                body["offset"] = offset

            resp = await client.post(
                f"{host}/collections/{collection_name}/points/scroll",
                headers=headers,
                json=body,
            )
            if resp.status_code == 404:
                return []  # Collection does not exist yet
            resp.raise_for_status()
            result = resp.json().get("result", {})
            points = result.get("points", [])

            for p in points:
                all_ids.append(str(p["id"]))

            next_offset = result.get("next_page_offset")
            if not next_offset or not points:
                break
            offset = next_offset

    return all_ids[:scan_limit]


LISTERS: dict[str, callable] = {
    "pgvector": _list_postgres_ids,
    "supabase": _list_postgres_ids,
    "neon": _list_postgres_ids,
    "pinecone": _list_pinecone_ids,
    "qdrant": _list_qdrant_ids,
}


async def execute_vector_search(
    connector_type: str,
    config: dict,
    search_config: dict,
    query_vector: list[float],
    top_k: int = 10,
) -> VectorSearchResponse:
    """Execute a vector search through the appropriate connector adapter."""
    searcher = SEARCHERS.get(connector_type)
    if not searcher:
        return _error_response("search_config_invalid", f"Unknown connector type: {connector_type}")

    start = time.monotonic()
    try:
        result = await asyncio.wait_for(
            searcher(config, search_config, query_vector, top_k),
            timeout=OVERALL_TIMEOUT,
        )
        result.latency_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "vector_search type=%s results=%d latency_ms=%d",
            connector_type, len(result.results), result.latency_ms,
        )
        return result
    except asyncio.TimeoutError:
        latency = int((time.monotonic() - start) * 1000)
        logger.error("vector_search_timeout type=%s", connector_type)
        return VectorSearchResponse(
            latency_ms=latency,
            error_category="connector_timeout",
            warnings=["Vector search timed out after 10s"],
        )
    except asyncpg.InvalidPasswordError:
        latency = int((time.monotonic() - start) * 1000)
        logger.error("vector_search_auth_fail type=%s", connector_type)
        return VectorSearchResponse(
            latency_ms=latency,
            error_category="connector_auth_failed",
            warnings=["Authentication failed — check credentials"],
        )
    except httpx.HTTPStatusError as e:
        latency = int((time.monotonic() - start) * 1000)
        if e.response.status_code in (401, 403):
            logger.error("vector_search_auth_fail type=%s", connector_type)
            return VectorSearchResponse(
                latency_ms=latency,
                error_category="connector_auth_failed",
                warnings=["Authentication failed — check API key"],
            )
        logger.error(
            "vector_search_http_error type=%s status=%d",
            connector_type, e.response.status_code,
        )
        return VectorSearchResponse(
            latency_ms=latency,
            error_category="search_execution_failed",
            warnings=[f"HTTP error {e.response.status_code}"],
        )
    except (OSError, ConnectionRefusedError, httpx.ConnectError):
        latency = int((time.monotonic() - start) * 1000)
        logger.error("vector_search_connect_fail type=%s", connector_type)
        return VectorSearchResponse(
            latency_ms=latency,
            error_category="connector_unreachable",
            warnings=["Connection refused — check host and port"],
        )
    except ValueError as e:
        latency = int((time.monotonic() - start) * 1000)
        logger.error("vector_search_validation_error type=%s error=%s", connector_type, str(e))
        return VectorSearchResponse(
            latency_ms=latency,
            error_category="search_config_invalid",
            warnings=[str(e)],
        )
    except Exception as e:
        latency = int((time.monotonic() - start) * 1000)
        logger.error("vector_search_error type=%s error=%s", connector_type, str(e))
        return VectorSearchResponse(
            latency_ms=latency,
            error_category="search_execution_failed",
            warnings=[str(e)],
        )
