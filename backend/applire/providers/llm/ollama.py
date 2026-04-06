"""Ollama local LLM provider — zero cloud dependencies (ADR 009)."""

import asyncio
import json
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from applire.config import settings
from applire.exceptions import LLMRateLimitError, LLMTimeoutError
from applire.providers.llm.base import LLMProvider

_CONNECT_TIMEOUT = 5.0   # fail fast if Ollama is not running


def _is_rate_limit(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
        return True
    return False


_retry = retry(
    retry=retry_if_exception(_is_rate_limit),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=16),
    reraise=True,
)


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider — zero cloud dependencies (ADR 009)."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 30,
    ) -> None:
        super().__init__(timeout=timeout)
        self._base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self._model = model or settings.ollama_model

    async def acomplete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        messages = _build_messages(prompt, system)
        try:
            return await asyncio.wait_for(
                self._complete(messages, temperature, max_tokens),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            raise LLMTimeoutError(f"Ollama call timed out after {self._timeout}s")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise LLMRateLimitError("Ollama rate limit after 3 attempts") from exc
            raise

    async def aparse_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        messages = _build_messages(prompt, system)
        try:
            raw = await asyncio.wait_for(
                self._parse_json(messages, temperature, max_tokens),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            raise LLMTimeoutError(f"Ollama call timed out after {self._timeout}s")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise LLMRateLimitError("Ollama rate limit after 3 attempts") from exc
            raise
        return json.loads(raw)

    @_retry
    async def _complete(self, messages: list, temperature: float, max_tokens: int) -> str:
        async with httpx.AsyncClient(timeout=self._timeout + _CONNECT_TIMEOUT) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                },
            )
            response.raise_for_status()
        return response.json()["message"]["content"]

    @_retry
    async def _parse_json(self, messages: list, temperature: float, max_tokens: int) -> str:
        async with httpx.AsyncClient(timeout=self._timeout + _CONNECT_TIMEOUT) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": messages,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                },
            )
            response.raise_for_status()
        return response.json()["message"]["content"]


def _build_messages(prompt: str, system: str | None) -> list:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages
