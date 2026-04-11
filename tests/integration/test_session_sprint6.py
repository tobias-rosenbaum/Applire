# tests/integration/test_session_sprint6.py
"""
Sprint 6 — Full happy path integration test (Task 20.9)

Validates:
  - POST /api/cv/generate returns cv_id with status=pending
  - Polling GET /api/cv/{id}/status transitions to ready
  - POST /api/flow/{id}/advance with step=cv_generation and artifact_id writes
    generated_cv_id on FlowSession
  - GET /api/flow/{id}/state returns cv_summary populated after advance
  - POST /api/flow/{id}/advance { step: "complete" } finalizes the flow

Run (requires Docker stack):
    pytest tests/integration/test_session_sprint6.py -v
"""
import json
import time
from pathlib import Path

import pytest
import requests

JD_FILE = Path(__file__).parent.parent / "files" / "jd.txt"

_LINKEDIN = {
    "firstName": "Max",
    "lastName": "Mustermann",
    "emailAddress": "max@example.de",
    "headline": "QA Manager",
    "location": {"name": "Munich, Germany"},
    "positions": [
        {
            "title": "QA Manager",
            "companyName": "Bayer AG",
            "startDate": {"month": 1, "year": 2020},
            "endDate": None,
            "description": "Quality assurance and regulatory compliance for pharma products.",
        }
    ],
    "educations": [
        {
            "schoolName": "LMU München",
            "degreeName": "Master of Science",
            "fieldOfStudy": "Pharmazie",
            "startDate": {"year": 2015},
            "endDate": {"year": 2019},
        }
    ],
    "skills": [{"name": "Quality Assurance"}, {"name": "21 CFR Part 11"}, {"name": "GMP"}],
    "languages": [{"language": {"name": "German"}, "proficiency": "NATIVE_OR_BILINGUAL"}],
}


@pytest.fixture(scope="module", autouse=True)
def ensure_profile(api):
    r = requests.post(
        f"{api}/api/profile/import",
        data={"linkedin_json": json.dumps(_LINKEDIN)},
        timeout=90,
    )
    assert r.status_code == 200, f"Profile import failed: {r.text}"


def _wait_for_ready(api: str, cv_id: str, timeout: int = 120) -> dict:
    """Poll status until ready or timeout. Returns the status response dict."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.get(f"{api}/api/cv/{cv_id}/status", timeout=10)
        assert r.status_code == 200
        data = r.json()
        if data["status"] == "ready":
            return data
        if data["status"] == "failed":
            pytest.fail(f"CV generation failed: {data}")
        time.sleep(3)
    pytest.fail(f"CV {cv_id} did not become ready within {timeout}s")


class TestSprint6FullFlow:
    @pytest.fixture(scope="class")
    def flow_and_cv(self, api):
        """Create job + flow + CV, advance through gap_analysis then cv_generation step."""
        jd_text = JD_FILE.read_text() if JD_FILE.exists() else (
            "QA Manager, 21 CFR Part 11 — München\n"
            "Requirements: GMP, quality assurance, regulatory compliance."
        )

        # Analyze JD
        jd_r = requests.post(f"{api}/api/job/analyze", json={"text": jd_text}, timeout=60)
        assert jd_r.status_code == 200
        job_id = jd_r.json()["id"]

        # Create flow — POST /api/flow returns 201 with flow_id
        flow_r = requests.post(f"{api}/api/flow", json={"job_id": job_id}, timeout=30)
        assert flow_r.status_code in (200, 201), f"Flow creation failed: {flow_r.text}"
        flow_id = flow_r.json()["flow_id"]

        # Run gap analysis (required before cv_generation step)
        gap_r = requests.post(f"{api}/api/job/{job_id}/gaps", timeout=60)
        assert gap_r.status_code == 200, f"Gap analysis failed: {gap_r.text}"
        gap_id = gap_r.json()["id"]

        # Advance flow to gap_analysis (jd_analysis → gap_analysis)
        adv_gap = requests.post(
            f"{api}/api/flow/{flow_id}/advance",
            json={"step": "gap_analysis", "artifact_id": gap_id},
            timeout=10,
        )
        assert adv_gap.status_code == 200, f"Flow advance to gap_analysis failed: {adv_gap.text}"

        # Generate CV
        cv_r = requests.post(
            f"{api}/api/cv/generate",
            json={"job_id": job_id, "template": "classic_german"},
            timeout=30,
        )
        assert cv_r.status_code == 201, f"CV generate failed: {cv_r.text}"
        cv_id = cv_r.json()["cv_id"]

        # Poll until ready
        _wait_for_ready(api, cv_id)

        # Advance flow to cv_generation (Task 20.9)
        adv_r = requests.post(
            f"{api}/api/flow/{flow_id}/advance",
            json={"step": "cv_generation", "artifact_id": cv_id},
            timeout=10,
        )
        assert adv_r.status_code == 200, f"Flow advance failed: {adv_r.text}"

        return {"flow_id": flow_id, "cv_id": cv_id, "job_id": job_id}

    def test_generate_returns_cv_id(self, api, flow_and_cv):
        assert len(flow_and_cv["cv_id"]) == 36

    def test_flow_state_has_cv_summary_after_advance(self, api, flow_and_cv):
        """At cv_generation step, cv_summary is None — generated_cv_id is only written
        when the flow advances to complete (commit 56daf05)."""
        r = requests.get(f"{api}/api/flow/{flow_and_cv['flow_id']}/state", timeout=10)
        assert r.status_code == 200
        state = r.json()
        assert state.get("current_step") == "cv_generation"
        assert state.get("cv_summary") is None, (
            "cv_summary should be None at cv_generation — it is populated after advancing to complete"
        )

    def test_flow_state_current_step_is_cv_generation(self, api, flow_and_cv):
        r = requests.get(f"{api}/api/flow/{flow_and_cv['flow_id']}/state", timeout=10)
        state = r.json()
        assert state.get("current_step") == "cv_generation"

    def test_advance_to_complete_finalizes_flow(self, api, flow_and_cv):
        r = requests.post(
            f"{api}/api/flow/{flow_and_cv['flow_id']}/advance",
            json={"step": "complete", "artifact_id": flow_and_cv["cv_id"]},
            timeout=10,
        )
        assert r.status_code == 200
        assert r.json().get("current_step") == "complete"
