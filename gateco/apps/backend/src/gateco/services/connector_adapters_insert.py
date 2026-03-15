"""Vector insert adapters for Tier 1 connectors.

Each adapter inserts vectors into the target vector DB.
Non-Tier-1 adapters raise ConnectorNotIngestionCapable.
"""

import logging

import asyncpg
import httpx

from gateco.services.connector_testers import _build_pgvector_dsn

logger = logging.getLogger(__name__)

INSERT_TIMEOUT = 30.0


async def insert_vectors(
    connector_type: str,
    config: dict,
    ingestion_config: dict,
    vectors: list[dict],
) -> None:
    """Insert vectors into the target connector.

    Args:
        connector_type: Type of the connector (e.g. "pgvector").
        config: Decrypted connector config.
        ingestion_config: Write-specific configuration.
        vectors: List of dicts with keys: id, vector, payload.

    Raises:
        ValueError: If connector type is not ingestion-capable.
        RuntimeError: If insertion fails.
    """
    inserter = INSERTERS.get(connector_type)
    if not inserter:
        raise ValueError(
            f"Connector type '{connector_type}' does not support ingestion"
        )

    await inserter(config, ingestion_config, vectors)


# ── Postgres family (pgvector, supabase, neon) ──


async def _insert_postgres(
    config: dict, ingestion_config: dict, vectors: list[dict],
) -> None:
    """Insert vectors into a Postgres-based vector DB (pgvector, supabase, neon)."""
    table_name = ingestion_config.get("target_table")
    id_field = ingestion_config.get("id_field", "id")
    content_field = ingestion_config.get("content_field", "content")
    upsert_mode = ingestion_config.get("upsert_mode", "upsert")

    if not table_name:
        raise ValueError("ingestion_config.target_table is required for Postgres connectors")

    from gateco.services.connector_adapters import _validate_identifier
    _validate_identifier(table_name, "target_table")
    _validate_identifier(id_field, "id_field")
    _validate_identifier(content_field, "content_field")

    # Build DSN
    if "connection_string" in config:
        dsn = config["connection_string"]
    else:
        dsn = _build_pgvector_dsn(config)

    conn = await asyncpg.connect(dsn, timeout=INSERT_TIMEOUT)
    try:
        for vec in vectors:
            vector_str = f"[{','.join(str(v) for v in vec['vector'])}]"
            text_content = vec.get("payload", {}).get("text", "")

            if upsert_mode == "upsert":
                sql = (
                    f"INSERT INTO {table_name} ({id_field}, {content_field}, embedding) "
                    f"VALUES ($1, $2, $3::vector) "
                    f"ON CONFLICT ({id_field}) DO UPDATE "
                    f"SET {content_field} = EXCLUDED.{content_field}, "
                    f"embedding = EXCLUDED.embedding"
                )
            else:
                sql = (
                    f"INSERT INTO {table_name} ({id_field}, {content_field}, embedding) "
                    f"VALUES ($1, $2, $3::vector)"
                )

            await conn.execute(sql, vec["id"], text_content, vector_str)
    finally:
        await conn.close()

    logger.info("postgres_insert count=%d table=%s", len(vectors), table_name)


async def _insert_pgvector(
    config: dict, ingestion_config: dict, vectors: list[dict],
) -> None:
    await _insert_postgres(config, ingestion_config, vectors)


async def _insert_supabase(
    config: dict, ingestion_config: dict, vectors: list[dict],
) -> None:
    await _insert_postgres(config, ingestion_config, vectors)


async def _insert_neon(
    config: dict, ingestion_config: dict, vectors: list[dict],
) -> None:
    await _insert_postgres(config, ingestion_config, vectors)


# ── Pinecone ──


async def _insert_pinecone(
    config: dict, ingestion_config: dict, vectors: list[dict],
) -> None:
    """Insert vectors into Pinecone."""
    api_key = config["api_key"]
    index_name = ingestion_config.get("target_index") or config.get("index_name")
    namespace = ingestion_config.get("namespace", "")

    if not index_name:
        raise ValueError("ingestion_config.target_index is required for Pinecone")

    headers = {"Api-Key": api_key, "X-Pinecone-API-Version": "2024-07"}

    async with httpx.AsyncClient(timeout=INSERT_TIMEOUT) as client:
        # Get index host
        resp = await client.get(
            f"https://api.pinecone.io/indexes/{index_name}", headers=headers,
        )
        resp.raise_for_status()
        index_host = resp.json().get("host")
        if not index_host:
            raise RuntimeError(f"Cannot resolve host for Pinecone index {index_name}")

        # Upsert vectors
        pinecone_vectors = []
        for vec in vectors:
            pv: dict = {"id": vec["id"], "values": vec["vector"]}
            if vec.get("payload"):
                pv["metadata"] = vec["payload"]
            pinecone_vectors.append(pv)

        body: dict = {"vectors": pinecone_vectors}
        if namespace:
            body["namespace"] = namespace

        upsert_resp = await client.post(
            f"https://{index_host}/vectors/upsert", headers=headers, json=body,
        )
        upsert_resp.raise_for_status()

    logger.info("pinecone_insert count=%d index=%s", len(vectors), index_name)


# ── Qdrant ──


async def _insert_qdrant(
    config: dict, ingestion_config: dict, vectors: list[dict],
) -> None:
    """Insert vectors into Qdrant."""
    host = config["host"].rstrip("/")
    api_key = config.get("api_key")
    collection_name = (
        ingestion_config.get("target_collection")
        or config.get("collection_name")
    )

    if not collection_name:
        raise ValueError("ingestion_config.target_collection is required for Qdrant")

    headers = {}
    if api_key:
        headers["api-key"] = api_key

    points = []
    for vec in vectors:
        point: dict = {
            "id": vec["id"],
            "vector": vec["vector"],
        }
        if vec.get("payload"):
            point["payload"] = vec["payload"]
        points.append(point)

    async with httpx.AsyncClient(timeout=INSERT_TIMEOUT) as client:
        resp = await client.put(
            f"{host}/collections/{collection_name}/points",
            headers=headers,
            json={"points": points},
        )
        resp.raise_for_status()

    logger.info("qdrant_insert count=%d collection=%s", len(vectors), collection_name)


# ── Dispatch ──


INSERTERS: dict[str, callable] = {
    "pgvector": _insert_pgvector,
    "supabase": _insert_supabase,
    "neon": _insert_neon,
    "pinecone": _insert_pinecone,
    "qdrant": _insert_qdrant,
}
