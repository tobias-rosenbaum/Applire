"""Integration test: interview session → flow artifact FK linkage (19.12).

Verifies arc42 §5.3.14: advancing flow to 'interview' step populates
interview_session_id FK on flow_sessions atomically.

Requires the full stack (backend + postgres) — run with:
    pytest backend/tests/integration/test_flow_interview_linkage.py
"""
import uuid

import pytest
import requests


@pytest.fixture()
def sample_jd_text() -> str:
    return (
        "Senior Python Engineer at FinTech GmbH. "
        "Requirements: Python, FastAPI, PostgreSQL, Docker, REST APIs, "
        "CI/CD experience, 5+ years backend development."
    )


def test_flow_interview_session_fk_populated(api: str, sample_jd_text: str) -> None:
    """Full flow: analyze JD → create flow → create session → advance to interview
    → verify interview_session_id FK is set on the flow record."""

    # 1. Analyze job description
    jd_res = requests.post(
        f"{api}/api/job/analyze",
        json={"text": sample_jd_text},
        timeout=30,
    )
    assert jd_res.status_code == 200, jd_res.text
    job_id = jd_res.json()["id"]

    # 2. Create flow session
    flow_res = requests.post(
        f"{api}/api/flow",
        json={"job_id": job_id},
        timeout=10,
    )
    assert flow_res.status_code in (200, 201), flow_res.text
    flow_id = flow_res.json()["flow_id"]

    # 3. Create interview session (mode=guided works without a profile)
    session_res = requests.post(
        f"{api}/api/session",
        json={"job_id": job_id, "mode": "guided"},
        timeout=30,
    )
    assert session_res.status_code == 201, session_res.text
    session_data = session_res.json()
    session_id = session_data["session_id"]
    assert session_data["mode"] == "guided"

    # 4. Advance flow to 'interview' step with session_id as artifact
    # Walk through the flow DAG to reach gap_analysis, regardless of prior state.
    # POST /api/flow may return an existing flow for the same job_id (idempotent),
    # so the current_step could be anywhere in {jd_analysis, cv_import, gap_analysis}.
    state_res = requests.get(f"{api}/api/flow/{flow_id}/state", timeout=10)
    assert state_res.status_code == 200
    state = state_res.json()

    if state["current_step"] == "jd_analysis":
        requests.post(
            f"{api}/api/flow/{flow_id}/advance",
            json={"step": "cv_import"},
            timeout=10,
        )
        state["current_step"] = "cv_import"

    if state["current_step"] == "cv_import":
        # artifact_id for gap_analysis must reference a real gap_analyses row.
        # Fetch or create the gap analysis for this job to get a valid ID.
        gaps_get = requests.get(f"{api}/api/job/{job_id}/gaps", timeout=10)
        if gaps_get.status_code == 200:
            gap_analysis_id = gaps_get.json()["id"]
        else:
            # No cached gap analysis — create one (requires LLM, may be slow)
            gaps_post = requests.post(f"{api}/api/job/{job_id}/gaps", timeout=60)
            assert gaps_post.status_code in (200, 201), gaps_post.text
            gap_analysis_id = gaps_post.json()["id"]

        requests.post(
            f"{api}/api/flow/{flow_id}/advance",
            json={"step": "gap_analysis", "artifact_id": gap_analysis_id},
            timeout=10,
        )

    # Advance to interview with session_id.
    # 409 is expected if the flow is already at 'interview' (idempotent re-run).
    adv_res = requests.post(
        f"{api}/api/flow/{flow_id}/advance",
        json={"step": "interview", "artifact_id": session_id},
        timeout=10,
    )
    assert adv_res.status_code in (200, 409), adv_res.text

    # 5. Verify via GET /api/flow/{id}/state regardless of advance response
    state_check = requests.get(f"{api}/api/flow/{flow_id}/state", timeout=10)
    assert state_check.status_code == 200
    final_state = state_check.json()

    assert final_state["current_step"] == "interview", (
        f"Expected current_step=interview, got {final_state['current_step']}"
    )
    assert final_state["interview_summary"] is not None, (
        "interview_summary must be populated when flow is at 'interview' step"
    )
