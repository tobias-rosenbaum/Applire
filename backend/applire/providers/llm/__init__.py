"""LLM provider factory — ADR 009.

Controlled by the LLM_PROVIDER environment variable:
  mistral     — Mistral AI (EU-hosted, default)
  openrouter  — OpenRouter multi-model gateway (uses openai SDK)
  openai      — OpenAI or any OpenAI-compatible server (LM Studio, etc.)
  ollama      — Ollama local server (zero cloud dependencies)
"""

from applire.config import settings
from applire.providers.llm.base import LLMProvider


def get_provider() -> LLMProvider:
    """Instantiate the configured LLM provider."""
    provider = settings.llm_provider.lower()

    if provider == "mistral":
        from applire.providers.llm.mistral import MistralProvider
        return MistralProvider()

    if provider == "openrouter":
        from applire.providers.llm.openrouter import OpenRouterProvider
        return OpenRouterProvider()

    if provider == "openai":
        from applire.providers.llm.openai import OpenAIProvider
        return OpenAIProvider()

    if provider == "ollama":
        from applire.providers.llm.ollama import OllamaProvider
        return OllamaProvider()

    if provider == "mock":
        from applire.providers.llm.mock import MockLLMProvider
        return MockLLMProvider()

    raise ValueError(
        f"Unknown LLM_PROVIDER '{settings.llm_provider}'. "
        "Valid values: mistral, openrouter, openai, ollama"
    )
