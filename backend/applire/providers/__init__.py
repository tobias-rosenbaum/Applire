# Compatibility re-export — canonical factory lives in applire.providers.llm
from applire.providers.llm import get_provider
from applire.providers.llm.base import LLMProvider

__all__ = ["get_provider", "LLMProvider"]
