# Copyright (C) 2024-2026 Tobias Rosenbaum
#
# This file is part of Applire.
#
# Applire is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Applire is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Applire. If not, see <https://www.gnu.org/licenses/>.

"""Ollama embedding provider — nomic-embed-text, 768-dim (ADR 009)."""

import httpx

from applire.config import settings
from applire.providers.embedding.base import EmbeddingProvider

DEFAULT_MODEL = "nomic-embed-text"
EMBEDDING_DIM = 768
_CONNECT_TIMEOUT = 5.0


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama local embedding provider — zero cloud dependencies (ADR 009)."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self._base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self._model = model or settings.embedding_model or DEFAULT_MODEL
        self._dim = EMBEDDING_DIM
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=_CONNECT_TIMEOUT)
        )

    async def embed(self, text: str) -> list[float]:
        response = await self._client.post(
            f"{self._base_url}/api/embed",
            json={"model": self._model, "input": text},
        )
        response.raise_for_status()
        return response.json()["embeddings"][0]
