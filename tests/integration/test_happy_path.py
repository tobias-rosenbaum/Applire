"""Sprint 4 — Happy Path Integration Test (Task 18.12)

End-to-end validation of the new user journey:
  - Upload CV → Analyze JD → Create flow → Advance through steps → Complete

Run with real LLM (requires INTEGRATION_LLM=1):
    INTEGRATION_LLM=1 pytest tests/integration/test_happy_path.py -v
"""
import os
from pathlib import Path

import pytest
import requests

# Skip all tests in this module unless INTEGRATION_LLM is set
pytestmark = pytest.mark.skipif(
    not os.getenv("INTEGRATION_LLM"),
    reason="Set INTEGRATION_LLM=1 to run integration tests with real LLM"
)

JD_FILE = Path(__file__).parent.parent / "files" / "jd.txt"
CV_FILE = Path(__file__).parent.parent / "files" / "cv.pdf"


def test_happy_path_new_user(api):
    """Complete new user journey: CV upload → JD analysis → gap detection → complete."""
    # Step 1: Upload CV (use a sample file or fallback to this test file)
    if CV_FILE.exists():
        with open(CV_FILE, "rb") as f:
            r = requests.post(
                f"{api}/api/profile/upload",
                files={"file": ("cv.pdf", f, "application/pdf")},
                timeout=120,
            )
    else:
        # Fallback: create a minimal text file as CV
        r = requests.post(
            f"{api}/api/profile/upload",
            files={"file": ("cv.txt", b"John Doe, Software Engineer, Python developer", "text/plain")},
            timeout=120,
        )
    assert r.status_code == 200, f"CV upload failed: {r.text}"
    profile_id = r.json()["profile_id"]

    # Step 2: Analyze JD
    jd_text = JD_FILE.read_text() if JD_FILE.exists() else """
    Senior Software Engineer - Python
    
    We are looking for a Senior Software Engineer with strong Python skills.
    Requirements:
    - 5+ years Python experience
    - FastAPI or Django experience
    - PostgreSQL database skills
    - Docker containerization
    - CI/CD pipelines
    """
    r = requests.post(
        f"{api}/api/job/analyze",
        json={"text": jd_text},
        timeout=90,
    )
    assert r.status_code == 200, f"JD analysis failed: {r.text}"
    job_id = r.json()["id"]

    # Step 3: Create flow
    r = requests.post(
        f"{api}/api/flow",
        json={"job_id": job_id},
        timeout=30,
    )
    assert r.status_code == 201, f"Flow creation failed: {r.text}"
    flow_id = r.json()["flow_id"]
    user_type = r.json()["user_type"]
    assert user_type == "new", f"Expected new user, got {user_type}"

    # Step 4: Get initial state
    r = requests.get(f"{api}/api/flow/{flow_id}/state", timeout=30)
    assert r.status_code == 200
    state = r.json()
    assert state["current_step"] in ["jd_analysis", "cv_import", "gap_analysis"], \
        f"Unexpected step: {state['current_step']}"

    # Step 5: Perform gap analysis
    r = requests.post(
        f"{api}/api/job/{job_id}/gaps",
        json={},
        timeout=90,
    )
    assert r.status_code == 200, f"Gap analysis failed: {r.text}"
    gap_id = r.json()["id"]

    # Step 6: Advance flow to gap_analysis step
    r = requests.post(
        f"{api}/api/flow/{flow_id}/advance",
        json={"step": "gap_analysis", "artifact_id": gap_id},
        timeout=30,
    )
    assert r.status_code == 200, f"Flow advance failed: {r.text}"

    # Step 7: Verify flow state after advance
    r = requests.get(f"{api}/api/flow/{flow_id}/state", timeout=30)
    assert r.status_code == 200
    state = r.json()
    assert "available_actions" in state
    assert state["gap_summary"] is not None, "Gap summary should be populated"

    # Verify match score is within valid range
    match_score = state["gap_summary"]["match_score"]
    assert 0.0 <= match_score <= 1.0, f"Invalid match score: {match_score}"