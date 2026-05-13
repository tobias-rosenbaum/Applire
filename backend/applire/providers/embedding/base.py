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
