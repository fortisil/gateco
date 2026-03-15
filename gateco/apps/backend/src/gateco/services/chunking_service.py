"""Text chunking service — splits documents into chunks for embedding."""

import hashlib
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChunkingConfig:
    """Configuration for text chunking."""

    chunk_size: int = 512
    chunk_overlap: int = 50
    strategy: str = "characters"  # "characters" | "tokens"


@dataclass
class Chunk:
    """A single chunk of text."""

    index: int
    text: str
    content_hash: str


def _normalize_text(text: str) -> str:
    """Normalize text for content hashing: lowercase and collapse whitespace."""
    return " ".join(text.lower().split())


def compute_content_hash(text: str) -> str:
    """Compute SHA-256 hash of normalized text."""
    normalized = _normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def chunk_text(text: str, config: ChunkingConfig | None = None) -> list[Chunk]:
    """Split text into chunks with configurable size and overlap.

    Args:
        text: The input text to chunk.
        config: Chunking configuration. Defaults to 512 chars, 50 overlap.

    Returns:
        List of Chunk objects with index, text, and content_hash.
    """
    if config is None:
        config = ChunkingConfig()

    if config.strategy != "characters":
        raise ValueError(f"Unsupported chunking strategy: {config.strategy}")

    if not text or not text.strip():
        return []

    text = text.strip()
    chunks: list[Chunk] = []
    start = 0
    index = 0

    while start < len(text):
        end = start + config.chunk_size
        chunk_text_str = text[start:end]

        if chunk_text_str.strip():
            chunks.append(Chunk(
                index=index,
                text=chunk_text_str,
                content_hash=compute_content_hash(chunk_text_str),
            ))
            index += 1

        if end >= len(text):
            break

        start = end - config.chunk_overlap

    logger.debug("chunked text len=%d into %d chunks (size=%d, overlap=%d)",
                 len(text), len(chunks), config.chunk_size, config.chunk_overlap)
    return chunks
