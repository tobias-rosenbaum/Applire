"""
Sprint 22 — Directed rewrite unit tests

Covers:
  - RewriteRequest / RewriteResponse Pydantic schemas
  - rewrite_section() service function (async, mocked LLM + SQLite)

No Docker, no real LLM.

Run:
    pytest tests/unit/test_cv_assist_rewrite.py -v
"""
import sys
from pathlib import Path

_backend = Path(__file__).parent.parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


def test_rewrite_request_schema_defaults():
    from applire.schemas.cv_sections import RewriteRequest
    req = RewriteRequest()
    assert req.directions == ""
    assert req.gap_ids == []


def test_rewrite_request_schema_with_values():
    from applire.schemas.cv_sections import RewriteRequest
    req = RewriteRequest(directions="I also did chromatography", gap_ids=["EU GMP Audit"])
    assert req.directions == "I also did chromatography"
    assert req.gap_ids == ["EU GMP Audit"]


def test_rewrite_response_schema():
    from applire.schemas.cv_sections import RewriteResponse
    resp = RewriteResponse(suggestion="Updated section text")
    assert resp.suggestion == "Updated section text"
