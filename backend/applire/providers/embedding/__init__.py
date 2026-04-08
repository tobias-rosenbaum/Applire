"""Embedding provider factory — ADR 009.

Controlled by the EMBEDDING_PROVIDER environment variable:
  noop    — zero-vector, no API key (Community default)
  mistral — Mistral text-embedding-mistral-embed, 1024-dim
  openai  — OpenAI text-embedding-3-small, 1536-dim
  ollama  — Ollama nomic-embed-text, 768-dim
"""

from applire.config import settings
from applire.providers.embedding.base import EmbeddingProvider


def get_embedding_provider() -> EmbeddingProvider:
    """Instantiate the configured embedding provider."""
    provider = settings.embedding_provider.lower()

    if provider == "noop":
        from applire.providers.embedding.noop import NoopEmbeddingProvider
        return NoopEmbeddingProvider()

    if provider == "mistral":
        from applire.providers.embedding.mistral import MistralEmbeddingProvider
        return MistralEmbeddingProvider()

    if provider == "openai":
        from applire.providers.embedding.openai import OpenAIEmbeddingProvider
        return OpenAIEmbeddingProvider()

    if provider == "ollama":
        from applire.providers.embedding.ollama import OllamaEmbeddingProvider
        return OllamaEmbeddingProvider()

    raise ValueError(
        f"Unknown EMBEDDING_PROVIDER '{settings.embedding_provider}'. "
        "Valid values: noop, mistral, openai, ollama"
    )


__all__ = ["get_embedding_provider", "EmbeddingProvider"]
