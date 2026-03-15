"""Tests for the embedding service (mocked provider)."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from gateco.services.embedding_service import (
    EmbeddingConfig,
    generate_embeddings,
)


@pytest.fixture
def mock_openai_response():
    """Mock successful OpenAI embeddings response."""
    return {
        "data": [
            {"index": 0, "embedding": [0.1, 0.2, 0.3]},
            {"index": 1, "embedding": [0.4, 0.5, 0.6]},
        ],
        "model": "text-embedding-3-small",
        "usage": {"total_tokens": 10},
    }


class TestGenerateEmbeddings:
    @pytest.mark.asyncio
    async def test_successful_embedding(self, mock_openai_response):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_openai_response
        mock_resp.raise_for_status = MagicMock()

        with patch("gateco.services.embedding_service.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_resp
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = mock_instance

            config = EmbeddingConfig(api_key="test-key")
            result = await generate_embeddings(["hello", "world"], config)

            assert len(result.embeddings) == 2
            assert result.embeddings[0] == [0.1, 0.2, 0.3]
            assert result.embeddings[1] == [0.4, 0.5, 0.6]
            assert result.dimensions == 3
            assert result.model == "text-embedding-3-small"
            assert result.token_count == 10

    @pytest.mark.asyncio
    async def test_missing_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            config = EmbeddingConfig(api_key=None)
            with pytest.raises(ValueError, match="API key required"):
                await generate_embeddings(["test"], config)

    @pytest.mark.asyncio
    async def test_unsupported_provider(self):
        config = EmbeddingConfig(provider="unsupported", api_key="key")
        with pytest.raises(ValueError, match="Unsupported embedding provider"):
            await generate_embeddings(["test"], config)

    @pytest.mark.asyncio
    async def test_api_error(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = "Rate limit exceeded"
        mock_resp.json.return_value = {"error": {"message": "Rate limit exceeded"}}
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429", request=MagicMock(), response=mock_resp,
        )

        with patch("gateco.services.embedding_service.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_resp
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = mock_instance

            config = EmbeddingConfig(api_key="test-key")
            with pytest.raises(RuntimeError, match="Embedding API error"):
                await generate_embeddings(["test"], config)

    @pytest.mark.asyncio
    async def test_custom_dimensions(self, mock_openai_response):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_openai_response
        mock_resp.raise_for_status = MagicMock()

        with patch("gateco.services.embedding_service.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_resp
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = mock_instance

            config = EmbeddingConfig(api_key="test-key", dimensions=256)
            await generate_embeddings(["hello"], config)

            # Verify dimensions param was passed
            call_args = mock_instance.post.call_args
            assert call_args[1]["json"]["dimensions"] == 256

    @pytest.mark.asyncio
    async def test_results_sorted_by_index(self):
        """Ensure embeddings are returned in input order even if API returns unordered."""
        response = {
            "data": [
                {"index": 1, "embedding": [0.4, 0.5]},
                {"index": 0, "embedding": [0.1, 0.2]},
            ],
            "model": "text-embedding-3-small",
            "usage": {"total_tokens": 5},
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = response
        mock_resp.raise_for_status = MagicMock()

        with patch("gateco.services.embedding_service.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_resp
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = mock_instance

            config = EmbeddingConfig(api_key="test-key")
            result = await generate_embeddings(["first", "second"], config)

            assert result.embeddings[0] == [0.1, 0.2]
            assert result.embeddings[1] == [0.4, 0.5]
