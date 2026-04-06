"""Application-wide exception hierarchy.

LLM errors are raised by provider implementations and caught by routers.
Providers translate vendor-specific errors (openai.RateLimitError, httpx 429, etc.)
into these unified types so routers never import SDK-specific exceptions.
"""


class LLMError(Exception):
    """Base class for all LLM provider errors."""


class LLMRateLimitError(LLMError):
    """Provider returned 429 after all retries exhausted.

    Retry strategy: 3 attempts, exponential backoff starting at 2s (tenacity).
    Routers should surface this as HTTP 503 with Retry-After guidance.
    """


class LLMTimeoutError(LLMError):
    """A single LLM call exceeded the provider's configured timeout.

    Default timeout is 30s per call (set on LLMProvider.__init__).
    Routers should surface this as HTTP 504.
    """
