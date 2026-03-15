"""Embedding provider abstraction — generates vector embeddings from text.

Initial implementation: OpenAI text-embedding-3-small / text-embedding-3-large.
Architecture supports future providers (cohere, bedrock, etc.).
"""

import logging
import os
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

EMBEDDING_TIMEOUT = 30.0


@dataclass
class EmbeddingConfig:
    """Configuration for an embedding provider."""

    provider: str = "openai"
    model: str = "text-embedding-3-small"
    dimensions: int | None = None
    api_key: str | None = None
    timeout: float = EMBEDDING_TIMEOUT


@dataclass
class EmbeddingResult:
    """Result from embedding generation."""

    embeddings: list[list[float]]
    model: str
    dimensions: int
    token_count: int | None = None


async def generate_embeddings(
    texts: list[str],
    config: EmbeddingConfig | None = None,
) -> EmbeddingResult:
    """Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.
        config: Embedding provider configuration. Uses env defaults if not provided.

    Returns:
        EmbeddingResult with embeddings, model info, and dimensions.

    Raises:
        ValueError: If provider is unsupported or API key is missing.
        RuntimeError: If the embedding API call fails.
    """
    if config is None:
        config = EmbeddingConfig()

    if config.provider != "openai":
        raise ValueError(f"Unsupported embedding provider: {config.provider}")

    api_key = config.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenAI API key required. Set OPENAI_API_KEY env var or pass api_key in config."
        )

    return await _embed_openai(texts, config, api_key)


async def _embed_openai(
    texts: list[str],
    config: EmbeddingConfig,
    api_key: str,
) -> EmbeddingResult:
    """Generate embeddings via OpenAI API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body: dict = {
        "input": texts,
        "model": config.model,
    }
    if config.dimensions is not None:
        body["dimensions"] = config.dimensions

    async with httpx.AsyncClient(timeout=config.timeout) as client:
        try:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json=body,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = ""
            try:
                detail = e.response.json().get("error", {}).get("message", "")
            except Exception:
                detail = e.response.text[:200]
            logger.error("embedding_api_error status=%d detail=%s", e.response.status_code, detail)
            raise RuntimeError(f"Embedding API error ({e.response.status_code}): {detail}") from e
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.error("embedding_api_connection_error: %s", str(e))
            raise RuntimeError(f"Embedding API connection error: {e}") from e

    data = resp.json()
    embeddings_data = sorted(data.get("data", []), key=lambda x: x["index"])
    embeddings = [item["embedding"] for item in embeddings_data]

    if not embeddings:
        raise RuntimeError("Embedding API returned no embeddings")

    dimensions = len(embeddings[0])
    token_count = data.get("usage", {}).get("total_tokens")

    logger.info(
        "embeddings_generated model=%s count=%d dimensions=%d",
        config.model, len(embeddings), dimensions,
    )

    return EmbeddingResult(
        embeddings=embeddings,
        model=config.model,
        dimensions=dimensions,
        token_count=token_count,
    )
