"""Embedding provider ABC — mirrors LLM provider pattern (ADR 009).

All concrete implementations live alongside this file:
  noop.py     — returns zero-vector (Community default, no API key needed)
  mistral.py  — text-embedding-mistral-embed, 1024-dim
  openai.py   — text-embedding-3-small, 1536-dim
  ollama.py   — nomic-embed-text, 768-dim

Contract for implementations:
  - async embed(text: str) -> list[float]
  - Must not raise on empty text (return zero-vector or equivalent).
"""

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract base class for all embedding provider implementations."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Embed text and return a list of floats.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
