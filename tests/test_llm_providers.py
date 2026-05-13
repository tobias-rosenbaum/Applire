"""
Iteration 6 — LLM Provider Choice (integration tests)
Verifies that the provider factory is correctly wired into the running app
and that switching providers does not break the API surface.

Deeper provider behaviour (OpenAI / Ollama adapters, factory routing) is
covered by mock-based unit tests in tests/unit/.
"""
import requests


def test_health_still_returns_200_after_provider_refactor(api):
    """Factory wiring must not break app startup or the health endpoint."""
    r = requests.get(f"{api}/health")
    assert r.status_code == 200


def test_health_reports_community_edition(api):
    r = requests.get(f"{api}/health")
    body = r.json()
    assert body["edition"] == "community"


def test_health_reports_version(api):
    """Version field was added alongside the provider refactor."""
    r = requests.get(f"{api}/health")
    body = r.json()
    assert "version" in body
    assert body["version"]  # non-empty
