from apliqa.config import settings
from apliqa.providers.base import LLMProvider


def get_provider() -> LLMProvider:
    """Factory: instantiate the configured LLM provider (ADR 009).

    Controlled by the LLM_PROVIDER environment variable:
      mistral  — Mistral AI (EU-hosted, default)
      openai   — OpenAI (gpt-4o by default)
      ollama   — Ollama local server (zero cloud dependencies)
    """
    provider = settings.llm_provider.lower()

    if provider == "mistral":
        from apliqa.providers.mistral import MistralProvider
        return MistralProvider()

    if provider == "openai":
        from apliqa.providers.openai import OpenAIProvider
        return OpenAIProvider()

    if provider == "ollama":
        from apliqa.providers.ollama import OllamaProvider
        return OllamaProvider()

    raise ValueError(
        f"Unknown LLM_PROVIDER '{settings.llm_provider}'. "
        "Valid values: mistral, openai, ollama"
    )
