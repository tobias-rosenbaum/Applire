"""LLM provider factory — ADR 009.

Controlled by the LLM_PROVIDER environment variable:
  mistral     — Mistral AI (EU-hosted, default)
  openrouter  — OpenRouter multi-model gateway (uses openai SDK)
  openai      — OpenAI or any OpenAI-compatible server (LM Studio, etc.)
  ollama      — Ollama local server (zero cloud dependencies)
"""

from apliqa.config import settings
from apliqa.providers.llm.base import LLMProvider


def get_provider() -> LLMProvider:
    """Instantiate the configured LLM provider."""
    provider = settings.llm_provider.lower()

    if provider == "mistral":
        from apliqa.providers.llm.mistral import MistralProvider
        return MistralProvider()

    if provider == "openrouter":
        from apliqa.providers.llm.openrouter import OpenRouterProvider
        return OpenRouterProvider()

    if provider == "openai":
        from apliqa.providers.llm.openai import OpenAIProvider
        return OpenAIProvider()

    if provider == "ollama":
        from apliqa.providers.llm.ollama import OllamaProvider
        return OllamaProvider()

    if provider == "mock":
        from apliqa.providers.llm.mock import MockLLMProvider
        return MockLLMProvider()

    raise ValueError(
        f"Unknown LLM_PROVIDER '{settings.llm_provider}'. "
        "Valid values: mistral, openrouter, openai, ollama"
    )
