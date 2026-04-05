# Compatibility re-export — canonical factory lives in apliqa.providers.llm
from apliqa.providers.llm import get_provider
from apliqa.providers.llm.base import LLMProvider

__all__ = ["get_provider", "LLMProvider"]
