"""OpenAI embedding provider — text-embedding-3-small, 1536-dim (ADR 009)."""

import openai

from applire.config import settings
from applire.providers.embedding.base import EmbeddingProvider

DEFAULT_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI or OpenAI-compatible embedding provider (ADR 009)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        resolved_base_url = base_url or settings.openai_base_url or None
        self._client = openai.AsyncOpenAI(
            api_key=api_key or settings.openai_api_key or "local",
            base_url=resolved_base_url,
        )
        self._model = model or settings.embedding_model or DEFAULT_MODEL
        self._dim = EMBEDDING_DIM

    async def embed(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding
