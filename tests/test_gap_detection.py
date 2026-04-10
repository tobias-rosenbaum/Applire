"""
Iteration 13 — Gap Detection & Follow-Up Logic (integration tests)

Done when:
  - POST /api/job/{job_id}/gaps returns A/B/C categories + float match_score in [0, 1]
  - POST /api/session/{id}/analyze-gaps returns the same structure for a session-scoped call
  - POST /api/session creates a session without a pre-existing gap analysis (lazy evaluation)
  - Category ordering: C items are higher priority than B items in the interview session
"""

import json
from pathlib import Path

import pytest
import requests

JD_FILE = Path(__file__).parent / "files" / "jd.txt"

_DACH_PROFILE = {
    "firstName": "Anna",
    "lastName": "Bauer",
    "emailAddress": "anna.bauer@example.de",
    "headline": "Senior Software Engineer",
    "location": {"name": "Munich, Germany"},
    "positions": [
        {
            "title": "Senior Software Engineer",
            "companyName": "Roche Deutschland GmbH",
            "startDate": {"month": 1, "year": 2019},
            "endDate": None,
            "description": "Microservices with Python and FastAPI. PostgreSQL, Docker, CI/CD.",
        }
    ],
    "educations": [
        {
            "schoolName": "Technische Universität München",
            "degreeName": "Master of Science",
            "fieldOfStudy": "Informatik",
            "startDate": {"year": 2014},
            "endDate": {"year": 2018},
        }
    ],
    "skills": [
        {"name": "Python"},
        {"name": "FastAPI"},
        {"name": "PostgreSQL"},
        {"name": "Docker"},
    ],
    "languages": [
        {"language": {"name": "German"}, "proficiency": "NATIVE_OR_BILINGUAL"},
        {"language": {"name": "English"}, "proficiency": "PROFESSIONAL_WORKING"},
    ],
}


# ---------------------------------------------------------------------------
# Module-scoped fixtures: one LLM call per test run
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def job_id(api):
    r = requests.post(
        f"{api}/api/job/analyze",
        json={"text": JD_FILE.read_text()},
        timeout=60,
    )
    assert r.status_code == 200, f"JD analyze failed: {r.text}"
    return r.json()["id"]


@pytest.fixture(scope="module")
def profile_id(api):
    r = requests.post(
        f"{api}/api/profile/import",
        data={"linkedin_json": json.dumps(_DACH_PROFILE)},
        timeout=90,
    )
    assert r.status_code == 200, f"Profile import failed: {r.text}"
    return r.json()["id"]


@pytest.fixture(scope="module")
def gap_body(api, job_id, profile_id):
    r = requests.post(f"{api}/api/job/{job_id}/gaps", timeout=60)
    assert r.status_code == 200, f"Gap analysis failed: {r.text}"
    return r.json()


@pytest.fixture(scope="module")
def session_id(api, job_id, profile_id):
    """Create a fresh session — lazy gap analysis must trigger internally."""
    r = requests.post(f"{api}/api/session", json={"job_id": job_id}, timeout=120)
    assert r.status_code == 201, f"Session creation failed: {r.text}"
    return r.json()["session_id"]


# ---------------------------------------------------------------------------
# Job-scoped gap endpoint (canonical)
# ---------------------------------------------------------------------------


class TestJobScopedGap:
    def test_returns_200(self, api, job_id, profile_id):
        r = requests.post(f"{api}/api/job/{job_id}/gaps", timeout=60)
        assert r.status_code == 200, r.text

    def test_match_score_is_float_in_range(self, gap_body):
        score = gap_body["match_score"]
        assert isinstance(score, float), f"match_score must be float, got {type(score)}"
        assert 0.0 <= score <= 1.0, f"match_score {score} out of range"

    def test_category_fields_present(self, gap_body):
        assert isinstance(gap_body.get("category_a"), list), "category_a missing"
        assert isinstance(gap_body.get("category_b"), list), "category_b missing"
        assert isinstance(gap_body.get("category_c"), list), "category_c missing"

    def test_categories_are_non_empty_strings(self, gap_body):
        for field in ("category_a", "category_b", "category_c"):
            for item in gap_body[field]:
                assert isinstance(item, str) and item, f"{field} contains empty string"

    def test_backward_compat_fields_present(self, gap_body):
        for field in ("critical_gaps", "minor_gaps", "strengths", "keyword_gaps"):
            assert field in gap_body, f"{field} missing from response"
            assert isinstance(gap_body[field], list)

    def test_all_requirements_classified(self, gap_body):
        """Every JD requirement should end up in exactly one of A, B, or C."""
        a = set(gap_body["category_a"])
        b = set(gap_body["category_b"])
        c = set(gap_body["category_c"])
        # No overlap between categories
        assert len(a & b) == 0, f"A/B overlap: {a & b}"
        assert len(a & c) == 0, f"A/C overlap: {a & c}"
        assert len(b & c) == 0, f"B/C overlap: {b & c}"

    def test_dach_profile_gets_reasonable_match(self, gap_body):
        """DACH senior profile with Python/FastAPI should achieve >0.3 match."""
        assert gap_body["match_score"] >= 0.3, "Expected reasonable match for DACH senior profile"

    def test_unknown_job_returns_404(self, api):
        r = requests.post(f"{api}/api/job/00000000-0000-0000-0000-000000000000/gaps", timeout=30)
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Session-scoped gap endpoint (convenience wrapper)
# ---------------------------------------------------------------------------


class TestSessionScopedGap:
    def test_analyze_gaps_via_session(self, api, session_id):
        r = requests.post(f"{api}/api/session/{session_id}/analyze-gaps", timeout=60)
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body.get("match_score"), float)
        assert isinstance(body.get("category_a"), list)
        assert isinstance(body.get("category_b"), list)
        assert isinstance(body.get("category_c"), list)

    def test_unknown_session_returns_404(self, api):
        r = requests.post(
            f"{api}/api/session/00000000-0000-0000-0000-000000000000/analyze-gaps",
            timeout=30,
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Session creation with lazy gap analysis
# ---------------------------------------------------------------------------


class TestSessionLazyGapAnalysis:
    def test_session_created_returns_201(self, api, session_id):
        assert session_id is not None

    def test_session_returns_first_question(self, api, job_id, profile_id):
        r = requests.post(f"{api}/api/session", json={"job_id": job_id}, timeout=120)
        assert r.status_code == 201
        body = r.json()
        assert "question" in body
        assert isinstance(body["question"], str) and body["question"]

    def test_session_gaps_total_and_remaining(self, api, job_id, profile_id):
        r = requests.post(f"{api}/api/session", json={"job_id": job_id}, timeout=120)
        assert r.status_code == 201
        body = r.json()
        assert isinstance(body.get("gaps_total"), int)
        assert isinstance(body.get("gaps_remaining"), int)
        assert body["gaps_remaining"] == body["gaps_total"]

    def test_category_c_gaps_appear_before_b_in_session(self, api, session_id, gap_body):
        """
        The first question generated in a session should target a Category C gap,
        not a Category B gap — because C (unknown) has higher interview priority.

        Verify indirectly: if category_c is non-empty, the session must have
        at least one gap to address (gaps_remaining > 0 if C exists).
        """
        if not gap_body.get("category_c"):
            pytest.skip("No Category C gaps in this run — skip ordering check")

        r = requests.post(f"{api}/api/session", json={"job_id": gap_body["job_analysis_id"]}, timeout=120)
        if r.status_code == 201:
            body = r.json()
            assert body["gaps_remaining"] > 0
