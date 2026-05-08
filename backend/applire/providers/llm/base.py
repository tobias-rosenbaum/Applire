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

"""LLM provider ABC — ADR 009.

All concrete implementations live alongside this file:
  mistral.py     — Mistral AI (EU-hosted default)
  openai.py      — OpenAI / OpenAI-compatible (LM Studio, etc.)
  openrouter.py  — OpenRouter (multi-model gateway, Iter 16 addition)
  ollama.py      — Ollama local server (fully offline)

Contract for implementations:
  - Enforce self._timeout on every SDK call via asyncio.wait_for.
  - Retry up to 3 times on provider-specific rate-limit errors (tenacity).
  - After retry exhaustion raise LLMRateLimitError.
  - On timeout raise LLMTimeoutError.
  - Ensure JSON output uses ensure_ascii=False (German umlaut preservation).
"""

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract base class for all LLM provider implementations."""

    def __init__(self, timeout: int = 30) -> None:
        self._timeout = timeout

    @abstractmethod
    async def acomplete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Send a prompt and return the text completion.

        Raises:
            LLMRateLimitError: provider is rate-limiting after all retries.
            LLMTimeoutError: call exceeded self._timeout seconds.
        """

    @abstractmethod
    async def aparse_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Send a prompt and return a parsed JSON dict.

        Raises:
            LLMRateLimitError: provider is rate-limiting after all retries.
            LLMTimeoutError: call exceeded self._timeout seconds.
        """
