"""Mistral embedding provider — text-embedding-mistral-embed, 1024-dim (ADR 009)."""

from mistralai import Mistral

from applire.config import settings
from applire.providers.embedding.base import EmbeddingProvider

DEFAULT_MODEL = "mistral-embed"
EMBEDDING_DIM = 1024


class MistralEmbeddingProvider(EmbeddingProvider):
    """Mistral AI embedding provider (EU-hosted default, ADR 009)."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._client = Mistral(api_key=api_key or settings.mistral_api_key)
        self._model = model or settings.embedding_model or DEFAULT_MODEL
        self._dim = EMBEDDING_DIM

    async def embed(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(
            model=self._model,
            inputs=[text],
        )
        return response.data[0].embedding
