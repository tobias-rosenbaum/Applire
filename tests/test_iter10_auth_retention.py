"""
Iteration 10 — Auth Abstraction & Retention Worker (integration test)

Done when:
  - AUTH_PROVIDER=none (default): all API endpoints behave identically to MVP —
    no token required, no 401/403.
  - Passing a fake Bearer token does not break anything (token is ignored by
    NoAuthProvider).
  - GET /api/profile returns 200 or 404 — never 401 or 403.
  - The retention worker CLI exits 0 and emits a valid JSON report with the
    expected keys and non-negative integer counts.

The retention subprocess tests require Docker and are guarded by
INTEGRATION_RETENTION=1 to allow CI to run the auth/contract tests without
a running container.

Run all tests (Docker required):
    python -m pytest tests/test_iter10_auth_retention.py -v

Run with retention smoke tests (Docker + running backend container):
    INTEGRATION_RETENTION=1 python -m pytest tests/test_iter10_auth_retention.py -v
"""
import json
import os
import subprocess
from pathlib import Path

import pytest
import requests

_INTEGRATION_RETENTION = os.getenv("INTEGRATION_RETENTION", "").strip() == "1"

JD_FILE = Path(__file__).parent / "files" / "jd.txt"

_RETENTION_KEYS = {
    "run_at",
    "uploads_deleted",
    "interview_sessions_deleted",
    "generated_cvs_deleted",
    "master_profiles_tombstoned",
    "users_tombstoned",
}
_RETENTION_COUNT_KEYS = _RETENTION_KEYS - {"run_at"}


def _run_retention() -> dict:
    """Run the retention worker inside the backend container and return parsed JSON."""
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", "backend", "python", "-m", "apliqa.retention"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result


# ---------------------------------------------------------------------------
# Auth — no enforcement (always run with Docker)
# ---------------------------------------------------------------------------


def test_health_returns_200_without_auth(api):
    """GET /health succeeds with no auth header — NoAuthProvider enforces nothing."""
    r = requests.get(f"{api}/health", timeout=10)
    assert r.status_code == 200


def test_jd_analyze_accepts_request_without_auth_header(api):
    """POST /api/job/analyze with valid JD text returns 200 — MVP behaviour unchanged."""
    r = requests.post(
        f"{api}/api/job/analyze",
        json={"text": JD_FILE.read_text()},
        timeout=90,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body.get("id"), str) and len(body["id"]) == 36


def test_auth_header_is_accepted_but_not_enforced(api):
    """Sending a fake Bearer token must not change the response — token is ignored."""
    r = requests.post(
        f"{api}/api/job/analyze",
        json={"text": JD_FILE.read_text()},
        headers={"Authorization": "Bearer fake-token-should-be-ignored"},
        timeout=90,
    )
    assert r.status_code == 200, r.text


def test_profile_endpoint_does_not_return_401_or_403(api):
    """GET /api/profile returns 200 (existing profile) or 404 (none yet) — never 401/403."""
    r = requests.get(f"{api}/api/profile", timeout=10)
    assert r.status_code in (200, 404), (
        f"Expected 200 or 404 from /api/profile, got {r.status_code}: {r.text}"
    )


def test_profile_endpoint_with_fake_token_still_not_401(api):
    """NoAuthProvider ignores tokens — /api/profile must still return 200 or 404."""
    r = requests.get(
        f"{api}/api/profile",
        headers={"Authorization": "Bearer invalid"},
        timeout=10,
    )
    assert r.status_code in (200, 404), (
        f"Expected 200 or 404 with fake token, got {r.status_code}: {r.text}"
    )


# ---------------------------------------------------------------------------
# Retention worker — subprocess smoke test (INTEGRATION_RETENTION=1)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _INTEGRATION_RETENTION,
    reason="Set INTEGRATION_RETENTION=1 to enable retention subprocess smoke tests",
)
def test_retention_worker_exits_zero():
    """python -m apliqa.retention must exit with code 0."""
    result = _run_retention()
    assert result.returncode == 0, (
        f"Retention worker exited {result.returncode}.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.skipif(
    not _INTEGRATION_RETENTION,
    reason="Set INTEGRATION_RETENTION=1 to enable retention subprocess smoke tests",
)
def test_retention_worker_emits_json_report():
    """stdout must be valid JSON."""
    result = _run_retention()
    assert result.returncode == 0, result.stderr
    try:
        json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(f"Retention worker stdout is not valid JSON: {exc}\nOutput: {result.stdout!r}")


@pytest.mark.skipif(
    not _INTEGRATION_RETENTION,
    reason="Set INTEGRATION_RETENTION=1 to enable retention subprocess smoke tests",
)
def test_retention_json_report_has_required_keys():
    """JSON report must contain all expected top-level keys."""
    result = _run_retention()
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    missing = _RETENTION_KEYS - set(report.keys())
    assert not missing, f"Retention report missing keys: {missing}"


@pytest.mark.skipif(
    not _INTEGRATION_RETENTION,
    reason="Set INTEGRATION_RETENTION=1 to enable retention subprocess smoke tests",
)
def test_retention_json_values_are_non_negative_integers():
    """All count fields in the JSON report must be non-negative integers."""
    result = _run_retention()
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    for key in _RETENTION_COUNT_KEYS:
        value = report.get(key)
        assert isinstance(value, int) and value >= 0, (
            f"Expected non-negative int for '{key}', got {value!r}"
        )
