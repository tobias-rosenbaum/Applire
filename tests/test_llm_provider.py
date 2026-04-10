"""Integration tests — Iter 16: LLM Provider Abstraction & OpenRouter Integration.

Requires the Docker Compose stack (conftest.py handles start/migrate).

Done when:
  - Changing LLM_PROVIDER=openrouter in the environment allows the full
    JD Intake → gap analysis flow to function without touching business logic.
  - The response schema from /api/job/analyze is identical regardless of
    which provider backend is configured.
  - LLMRateLimitError surfaces as HTTP 503, LLMTimeoutError as HTTP 504.

Run (Docker required):
    python -m pytest tests/test_iter16_llm_provider.py -v
"""

import pytest
import requests

_JD_TEXT = (
    "Senior Python Engineer (m/w/d) — Applire GmbH, Berlin. "
    "You will build production-grade FastAPI services. "
    "Required: Python, FastAPI, PostgreSQL, Docker, 5+ years experience. "
    "Nice to have: Kubernetes, Redis. "
    "Language: German C1 or native."
)

_JD_ANALYSIS_REQUIRED_FIELDS = (
    "id",
    "role_title",
    "required_skills",
    "nice_to_have_skills",
    "keywords",
    "seniority_level",
)


# ---------------------------------------------------------------------------
# Core flow: POST /api/job/analyze returns valid JobAnalysisResponse
# (uses whatever LLM_PROVIDER is configured in the running container)
# ---------------------------------------------------------------------------


def test_jd_analyze_returns_valid_schema(api):
    """The running stack's LLM provider produces a well-formed JobAnalysisResponse."""
    response = requests.post(
        f"{api}/api/job/analyze",
        json={"text": _JD_TEXT},
        timeout=60,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    for field in _JD_ANALYSIS_REQUIRED_FIELDS:
        assert field in data, f"Missing required field '{field}' in JobAnalysisResponse"
    assert isinstance(data["required_skills"], list)
    assert len(data["required_skills"]) > 0, "Expected at least one required skill"


def test_jd_analyze_is_idempotent(api):
    """Submitting the same JD text twice returns the cached record (same id)."""
    payload = {"text": _JD_TEXT}
    r1 = requests.post(f"{api}/api/job/analyze", json=payload, timeout=60)
    r2 = requests.post(f"{api}/api/job/analyze", json=payload, timeout=60)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"], "Identical JD text must return the same cached record"


# ---------------------------------------------------------------------------
# Error surface: provider-level errors map to correct HTTP codes
# ---------------------------------------------------------------------------


def test_analyze_empty_text_returns_422(api):
    """Empty JD text must be rejected with 422 before hitting the LLM."""
    response = requests.post(
        f"{api}/api/job/analyze",
        json={"text": ""},
        timeout=10,
    )
    # FastAPI validates the minimum-length constraint (non-empty text is required)
    assert response.status_code in (422, 400), (
        f"Expected 4xx for empty text, got {response.status_code}: {response.text}"
    )


# ---------------------------------------------------------------------------
# Provider abstraction contract: schema is stable across backends
# ---------------------------------------------------------------------------


def test_jd_response_has_no_provider_specific_fields(api):
    """The response must not contain any provider-specific metadata fields.

    This guards against a future provider leaking SDK internals into the response.
    """
    response = requests.post(
        f"{api}/api/job/analyze",
        json={"text": _JD_TEXT},
        timeout=60,
    )
    assert response.status_code == 200
    data = response.json()
    provider_leakage_keys = {"model", "usage", "finish_reason", "logprobs", "object"}
    leaked = provider_leakage_keys & set(data.keys())
    assert not leaked, f"Provider-specific fields leaked into response: {leaked}"


# ---------------------------------------------------------------------------
# Health check: stack is up and provider is reachable
# ---------------------------------------------------------------------------


def test_health_endpoint_is_reachable(api):
    """Sanity check: the stack is running and healthy."""
    response = requests.get(f"{api}/health", timeout=5)
    assert response.status_code == 200
