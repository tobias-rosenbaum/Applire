from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Base class for all LLM provider implementations (ADR 009)."""

    @abstractmethod
    async def acomplete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Send a prompt and return the text completion."""

    @abstractmethod
    async def aparse_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Send a prompt and return a parsed JSON dict."""
