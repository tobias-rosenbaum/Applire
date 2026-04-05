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
