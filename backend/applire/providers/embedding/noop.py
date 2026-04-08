"""Noop embedding provider — Community Edition default.

Returns a zero-vector of the configured dimension.
Allows the rest of the application to function without any embedding API key.
Vector similarity scoring is effectively disabled (all scores = 0).
"""

from applire.providers.embedding.base import EmbeddingProvider

EMBEDDING_DIM = 1024


class NoopEmbeddingProvider(EmbeddingProvider):
    """Returns a zero-vector — no API calls, no configuration required."""

    def __init__(self, dim: int = EMBEDDING_DIM) -> None:
        self._dim = dim

    async def embed(self, text: str) -> list[float]:
        return [0.0] * self._dim
