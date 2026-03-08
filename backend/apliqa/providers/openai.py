import json
from typing import Any

import openai

from apliqa.config import settings
from apliqa.providers.base import LLMProvider

class OpenAIProvider(LLMProvider):
    """OpenAI-compatible provider (ADR 009).

    Works with OpenAI, LM Studio, and any other OpenAI-compatible server.
    Set OPENAI_BASE_URL to point at a local server (e.g. http://host.docker.internal:1234/v1).
    """

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
        self._model = model or settings.openai_model

    async def acomplete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def aparse_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
