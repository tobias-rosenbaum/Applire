"""Unit tests for structured error_code in POST /api/job/analyze (Sprint 26).

Both tests mock scrape_job_url so no real HTTP calls are made.
Run with: pytest tests/unit/test_job_router_url_errors.py -v
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from applire.main import app
from applire.services.scraper import ScraperError


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# jd_url_invalid — ValueError from _validate_url
# ---------------------------------------------------------------------------


def test_analyze_invalid_url_returns_structured_error_code(client: TestClient) -> None:
    """scrape_job_url raising ValueError must return 422 with error_code='jd_url_invalid'.

    The Pydantic schema catches truly malformed URLs before the router runs.
    This test covers the case where the scraper's own validation rejects the URL
    (e.g. a redirect that ends on an ftp:// target) by mocking scrape_job_url
    to raise ValueError directly.
    """
    with patch(
        "applire.routers.job.scrape_job_url",
        new_callable=AsyncMock,
        side_effect=ValueError("Only http and https URLs are supported, got scheme: 'ftp'"),
    ):
        res = client.post("/api/job/analyze", json={"url": "https://example.com/job"})

    assert res.status_code == 422
    detail = res.json()["detail"]
    assert isinstance(detail, dict), f"Expected dict, got: {detail!r}"
    assert detail["error_code"] == "jd_url_invalid"
    assert "message" in detail
    assert len(detail["message"]) > 0


# ---------------------------------------------------------------------------
# jd_fetch_failed — ScraperError from scrape_job_url
# ---------------------------------------------------------------------------


def test_analyze_blocked_url_returns_structured_error_code(client: TestClient) -> None:
    """A blocked / thin-content URL must return 422 with error_code='jd_fetch_failed'."""
    with patch(
        "applire.routers.job.scrape_job_url",
        new_callable=AsyncMock,
        side_effect=ScraperError(
            url="https://blocked.example.com/job",
            reason="Could not extract job text from this page. Please paste the job description manually.",
        ),
    ):
        res = client.post("/api/job/analyze", json={"url": "https://blocked.example.com/job"})

    assert res.status_code == 422
    detail = res.json()["detail"]
    assert isinstance(detail, dict), f"Expected dict, got: {detail!r}"
    assert detail["error_code"] == "jd_fetch_failed"
    assert "message" in detail
    assert len(detail["message"]) > 0
