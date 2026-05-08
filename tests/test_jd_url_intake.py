"""
Iteration 8 — JD URL Intake (integration test)

Done when:
  - POST /api/job/analyze with { "url": "..." } scrapes the page and returns
    a valid JobAnalysis JSON without manual text extraction.
  - Submitting the same URL twice returns the same record (URL-based dedup).
  - Invalid / missing inputs return appropriate error codes.
  - The existing { "text": "..." } path is unaffected.

Real-network scraping tests are guarded by INTEGRATION_SCRAPE=1 because live
job board pages are unavailable in CI and may change over time.

Run all tests (Docker + real network required):
    INTEGRATION_SCRAPE=1 python -m pytest tests/test_iter8_jd_url_intake.py -v

Run contract-only tests (Docker required, no real network):
    python -m pytest tests/test_iter8_jd_url_intake.py -v
"""
import os
from pathlib import Path

import pytest
import requests

_INTEGRATION_SCRAPE = os.getenv("INTEGRATION_SCRAPE", "").strip() == "1"

# A stable DACH job URL for real-network smoke tests.
# Replace with a current posting if this URL becomes stale.
_STEPSTONE_URL = (
    "https://www.stepstone.de/stellenangebote/"
    "senior-python-developer-remote-acme-gmbh--12345678.html"
)

JD_FILE = Path(__file__).parent / "files" / "jd.txt"
VALID_SENIORITY_LEVELS = {"Junior", "Mid", "Senior", "Lead", "Executive"}


def _post_analyze(api: str, **kwargs) -> requests.Response:
    return requests.post(f"{api}/api/job/analyze", json=kwargs, timeout=90)


# ---------------------------------------------------------------------------
# Input validation (no scraping — always run)
# ---------------------------------------------------------------------------


def test_analyze_rejects_empty_body(api):
    """POST with neither text nor url must return 422."""
    r = requests.post(f"{api}/api/job/analyze", json={}, timeout=10)
    assert r.status_code == 422


def test_analyze_rejects_file_scheme_url(api):
    """Non-http(s) URL scheme must be rejected with 422."""
    r = _post_analyze(api, url="file:///etc/passwd")
    assert r.status_code == 422


def test_analyze_rejects_ftp_scheme_url(api):
    """FTP URL must be rejected with 422."""
    r = _post_analyze(api, url="ftp://jobs.example.com/job.txt")
    assert r.status_code == 422


def test_analyze_rejects_malformed_url(api):
    """A string that is not a URL must be rejected with 422."""
    r = _post_analyze(api, url="not-a-url-at-all")
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Text path regression (always run)
# ---------------------------------------------------------------------------


def test_text_path_still_returns_200(api):
    """Regression: the existing { text } path must remain functional."""
    r = _post_analyze(api, text=JD_FILE.read_text())
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body.get("id"), str) and len(body["id"]) == 36
    assert isinstance(body.get("role_title"), str) and body["role_title"]
    assert isinstance(body.get("required_skills"), list) and body["required_skills"]


def test_text_path_source_url_is_null(api):
    """Jobs submitted via the text path must have source_url=null in the response."""
    r = _post_analyze(api, text=JD_FILE.read_text())
    assert r.status_code == 200, r.text
    assert r.json().get("source_url") is None


def test_text_path_rejects_blank_text(api):
    """Regression: blank text must still return 422."""
    r = _post_analyze(api, text="   ")
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# URL intake — real network (guarded by INTEGRATION_SCRAPE=1)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _INTEGRATION_SCRAPE,
    reason="Set INTEGRATION_SCRAPE=1 to enable real-network scraping tests",
)
def test_url_intake_returns_valid_job_analysis(api):
    """POST with a real StepStone URL returns a well-structured JobAnalysis."""
    r = _post_analyze(api, url=_STEPSTONE_URL)
    assert r.status_code == 200, r.text

    body = r.json()
    assert isinstance(body.get("id"), str) and len(body["id"]) == 36
    assert isinstance(body.get("role_title"), str) and body["role_title"]
    assert isinstance(body.get("required_skills"), list) and body["required_skills"]
    assert isinstance(body.get("nice_to_have_skills"), list)
    assert isinstance(body.get("keywords"), list) and body["keywords"]
    assert body.get("seniority_level") in VALID_SENIORITY_LEVELS
    assert isinstance(body.get("raw_text_hash"), str) and len(body["raw_text_hash"]) == 64
    assert body.get("source_url") == _STEPSTONE_URL


@pytest.mark.skipif(
    not _INTEGRATION_SCRAPE,
    reason="Set INTEGRATION_SCRAPE=1 to enable real-network scraping tests",
)
def test_url_deduplication_returns_same_id(api):
    """Submitting the same URL twice must return the same record id."""
    first = _post_analyze(api, url=_STEPSTONE_URL)
    assert first.status_code == 200, first.text

    second = _post_analyze(api, url=_STEPSTONE_URL)
    assert second.status_code == 200, second.text

    assert first.json()["id"] == second.json()["id"]


@pytest.mark.skipif(
    not _INTEGRATION_SCRAPE,
    reason="Set INTEGRATION_SCRAPE=1 to enable real-network scraping tests",
)
def test_url_intake_source_url_stored_in_response(api):
    """source_url in the response must echo back the submitted URL."""
    r = _post_analyze(api, url=_STEPSTONE_URL)
    assert r.status_code == 200, r.text
    assert r.json().get("source_url") == _STEPSTONE_URL
