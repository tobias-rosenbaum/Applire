"""
Iteration 1 — JD Intake & Analysis
Done when: POST /api/job/analyze with a real DACH job description returns
           a well-structured JobAnalysis JSON.
"""
from pathlib import Path

import requests

JD_FILE = Path(__file__).parent / "files" / "jd.txt"
VALID_SENIORITY_LEVELS = {"Junior", "Mid", "Senior", "Lead", "Executive"}


def _post_analyze(api: str, text: str) -> requests.Response:
    return requests.post(
        f"{api}/api/job/analyze",
        json={"text": text},
        timeout=60,
    )


def test_analyze_returns_200(api):
    r = _post_analyze(api, JD_FILE.read_text())
    assert r.status_code == 200, r.text


def test_analyze_response_structure(api):
    body = _post_analyze(api, JD_FILE.read_text()).json()

    assert isinstance(body.get("id"), str) and len(body["id"]) == 36  # UUID format
    assert isinstance(body.get("role_title"), str) and body["role_title"]
    assert isinstance(body.get("required_skills"), list) and body["required_skills"]
    assert isinstance(body.get("nice_to_have_skills"), list)
    assert isinstance(body.get("keywords"), list) and body["keywords"]
    assert body.get("seniority_level") in VALID_SENIORITY_LEVELS
    assert isinstance(body.get("company_culture_signals"), list)
    assert isinstance(body.get("language_requirement"), str) and body["language_requirement"]
    assert isinstance(body.get("raw_text_hash"), str) and len(body["raw_text_hash"]) == 64


def test_analyze_deduplication(api):
    """Submitting the same JD twice must return the same record (same id)."""
    text = JD_FILE.read_text()
    first = _post_analyze(api, text).json()
    second = _post_analyze(api, text).json()
    assert first["id"] == second["id"]


def test_analyze_rejects_empty_text(api):
    r = _post_analyze(api, "   ")
    assert r.status_code == 422
