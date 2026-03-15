"""Tests for the chunking service."""

import pytest

from gateco.services.chunking_service import (
    ChunkingConfig,
    chunk_text,
    compute_content_hash,
)


class TestComputeContentHash:
    def test_deterministic(self):
        h1 = compute_content_hash("hello world")
        h2 = compute_content_hash("hello world")
        assert h1 == h2

    def test_normalized_whitespace(self):
        h1 = compute_content_hash("hello   world")
        h2 = compute_content_hash("hello world")
        assert h1 == h2

    def test_case_insensitive(self):
        h1 = compute_content_hash("Hello World")
        h2 = compute_content_hash("hello world")
        assert h1 == h2

    def test_sha256_length(self):
        h = compute_content_hash("test")
        assert len(h) == 64

    def test_different_text_different_hash(self):
        h1 = compute_content_hash("hello")
        h2 = compute_content_hash("world")
        assert h1 != h2


class TestChunkText:
    def test_short_text_single_chunk(self):
        chunks = chunk_text("short text")
        assert len(chunks) == 1
        assert chunks[0].index == 0
        assert chunks[0].text == "short text"
        assert len(chunks[0].content_hash) == 64

    def test_empty_text(self):
        chunks = chunk_text("")
        assert chunks == []

    def test_whitespace_only(self):
        chunks = chunk_text("   \n\t  ")
        assert chunks == []

    def test_exact_chunk_size(self):
        text = "a" * 512
        chunks = chunk_text(text, ChunkingConfig(chunk_size=512, chunk_overlap=0))
        assert len(chunks) == 1

    def test_multiple_chunks(self):
        text = "a" * 1024
        config = ChunkingConfig(chunk_size=512, chunk_overlap=0)
        chunks = chunk_text(text, config)
        assert len(chunks) == 2
        assert chunks[0].index == 0
        assert chunks[1].index == 1
        assert len(chunks[0].text) == 512
        assert len(chunks[1].text) == 512

    def test_overlap(self):
        text = "a" * 1000
        config = ChunkingConfig(chunk_size=512, chunk_overlap=50)
        chunks = chunk_text(text, config)
        assert len(chunks) >= 2
        # Second chunk starts at 512 - 50 = 462
        assert chunks[1].text == text[462:462 + 512]

    def test_default_config(self):
        text = "a" * 2000
        chunks = chunk_text(text)
        assert len(chunks) > 1
        # Default: 512 chars, 50 overlap

    def test_chunk_indices_sequential(self):
        text = "x" * 3000
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            assert chunk.index == i

    def test_each_chunk_has_content_hash(self):
        text = "hello " * 500
        chunks = chunk_text(text)
        for chunk in chunks:
            assert chunk.content_hash
            assert len(chunk.content_hash) == 64

    def test_unsupported_strategy(self):
        with pytest.raises(ValueError, match="Unsupported chunking strategy"):
            chunk_text("text", ChunkingConfig(strategy="tokens"))

    def test_custom_sizes(self):
        text = "word " * 100
        config = ChunkingConfig(chunk_size=100, chunk_overlap=10)
        chunks = chunk_text(text, config)
        assert all(len(c.text) <= 100 for c in chunks)
