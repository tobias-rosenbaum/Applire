"""OpenRouter provider — multi-model gateway (Iter 16, ADR 009).

Uses the openai Python SDK pointed at OpenRouter's OpenAI-compatible endpoint.
Two required headers identify us to OpenRouter's usage-ranking and abuse-detection:
  HTTP-Referer  — canonical URL of the application
  X-Title       — human-readable application name

Default model: mistralai/mistral-large-latest
  Rationale: keeps model parity with the direct Mistral provider so our prompts
  behave identically. Switch OPENROUTER_MODEL once the plumbing is validated.

Env vars consumed (see apliqa/config.py):
  OPENROUTER_API_KEY   — required
  OPENROUTER_MODEL     — optional, defaults to mistralai/mistral-large-latest
  OPENROUTER_BASE_URL  — optional override (default: https://openrouter.ai/api/v1)
"""

import asyncio
import json
from typing import Any

import openai
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from apliqa.config import settings
from apliqa.exceptions import LLMRateLimitError, LLMTimeoutError
from apliqa.providers.llm.base import LLMProvider

_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
_HTTP_REFERER = "https://apliqa.community"
_X_TITLE = "Apliqa"

_retry = retry(
    retry=retry_if_exception_type(openai.RateLimitError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=16),
    reraise=True,
)


class OpenRouterProvider(LLMProvider):
    """OpenRouter multi-model gateway provider (ADR 009, Iter 16)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int = 30,
    ) -> None:
        super().__init__(timeout=timeout)
        self._client = openai.AsyncOpenAI(
            api_key=api_key or settings.openrouter_api_key,
            base_url=base_url or settings.openrouter_base_url or _DEFAULT_BASE_URL,
            default_headers={
                "HTTP-Referer": _HTTP_REFERER,
                "X-Title": _X_TITLE,
            },
        )
        self._model = model or settings.openrouter_model or "mistralai/mistral-large-latest"

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
            raise LLMTimeoutError(f"OpenRouter call timed out after {self._timeout}s")
        except openai.RateLimitError as exc:
            raise LLMRateLimitError("OpenRouter rate limit after 3 attempts") from exc
        except openai.APITimeoutError as exc:
            raise LLMTimeoutError("OpenRouter SDK reported timeout") from exc

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
            content = await asyncio.wait_for(
                self._parse_json(messages, temperature, max_tokens),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            raise LLMTimeoutError(f"OpenRouter call timed out after {self._timeout}s")
        except openai.RateLimitError as exc:
            raise LLMRateLimitError("OpenRouter rate limit after 3 attempts") from exc
        except openai.APITimeoutError as exc:
            raise LLMTimeoutError("OpenRouter SDK reported timeout") from exc
        # Strip markdown code fences some models emit
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content.strip())

    @_retry
    async def _complete(self, messages: list, temperature: float, max_tokens: int) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    @_retry
    async def _parse_json(self, messages: list, temperature: float, max_tokens: int) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content


def _build_messages(prompt: str, system: str | None) -> list:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages
