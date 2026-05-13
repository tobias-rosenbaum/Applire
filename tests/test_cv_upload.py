"""
Iteration 12 — CV Upload & Parsing Pipeline (integration tests)

Done when:
  - POST /api/profile/upload with a real DACH CV PDF
    → completeness_score > 0.6, all major sections populated.
  - Upload a second CV → conflicts are flagged, no data lost
    (GET /api/profile work_experience is non-empty).
  - Upload with invalid format → 422.
  - Uploading a file to POST /api/profile/import → 422 with redirect hint.
  - LLM timeout → 504.

Run (Docker required):
    python -m pytest tests/test_iter12_cv_upload.py -v

Fixture files:
    tests/files/Profile.pdf — LinkedIn PDF export (already present from iter 9)
"""

from pathlib import Path

import pytest
import requests

_BASE = "http://localhost:8001"
_UPLOAD_URL = f"{_BASE}/api/profile/upload"
_IMPORT_URL = f"{_BASE}/api/profile/import"
_PROFILE_URL = f"{_BASE}/api/profile"

_PDF_FILE = Path(__file__).parent / "files" / "Profile.pdf"
_JD_FILE = Path(__file__).parent / "files" / "jd.txt"


# ---------------------------------------------------------------------------
# 12.1 — Upload a DACH PDF → completeness > 0.6
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_upload_pdf_returns_cvupload_response():
    assert _PDF_FILE.exists(), f"Fixture missing: {_PDF_FILE}"
    with open(_PDF_FILE, "rb") as f:
        resp = requests.post(
            _UPLOAD_URL,
            files={"file": ("Profile.pdf", f, "application/pdf")},
            timeout=120,
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "profile_id" in body
    assert "completeness_score" in body
    assert "status" in body
    assert body["status"] in ("DRAFT", "COMPLETE")
    assert "expires_at" in body
    assert "enrichment_record_id" in body


@pytest.mark.integration
def test_upload_pdf_completeness_above_threshold():
    assert _PDF_FILE.exists()
    with open(_PDF_FILE, "rb") as f:
        resp = requests.post(
            _UPLOAD_URL,
            files={"file": ("Profile.pdf", f, "application/pdf")},
            timeout=120,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["completeness_score"] > 0.6, (
        f"Expected completeness > 0.6, got {body['completeness_score']}"
    )


@pytest.mark.integration
def test_upload_pdf_populates_profile():
    with open(_PDF_FILE, "rb") as f:
        requests.post(
            _UPLOAD_URL,
            files={"file": ("Profile.pdf", f, "application/pdf")},
            timeout=120,
        )
    profile_resp = requests.get(_PROFILE_URL, timeout=30)
    assert profile_resp.status_code == 200
    profile = profile_resp.json()["profile"]
    assert len(profile.get("work_experience", [])) > 0
    assert profile.get("personal_info", {}).get("name", "") != ""


# ---------------------------------------------------------------------------
# 12.2 — Second upload triggers merge, no data lost
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_second_upload_does_not_lose_work_experience():
    # Upload twice (same file — idempotent merge)
    for _ in range(2):
        with open(_PDF_FILE, "rb") as f:
            requests.post(
                _UPLOAD_URL,
                files={"file": ("Profile.pdf", f, "application/pdf")},
                timeout=120,
            )

    profile_resp = requests.get(_PROFILE_URL, timeout=30)
    assert profile_resp.status_code == 200
    assert len(profile_resp.json()["profile"].get("work_experience", [])) > 0


# ---------------------------------------------------------------------------
# 12.3 — Upload with optional job_id parameter
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_upload_with_job_id_query_param():
    """Passing a non-existent job_id falls back gracefully to generic extraction."""
    fake_job_id = "00000000-0000-0000-0000-000000000000"
    with open(_PDF_FILE, "rb") as f:
        resp = requests.post(
            _UPLOAD_URL,
            params={"job_id": fake_job_id},
            files={"file": ("Profile.pdf", f, "application/pdf")},
            timeout=120,
        )
    # Non-existent job_id should not fail — falls back to generic extraction
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 12.4 — Invalid / unsupported format → 422
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_upload_empty_file_returns_422():
    resp = requests.post(
        _UPLOAD_URL,
        files={"file": ("empty.pdf", b"", "application/pdf")},
        timeout=30,
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 12.5 — /import rejects plain PDF with redirect hint
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_import_rejects_unsupported_format_with_helpful_error():
    """Non-ZIP, non-PDF files sent to /import must return 422 with a redirect hint."""
    resp = requests.post(
        _IMPORT_URL,
        files={"file": ("cv.txt", b"plain text content", "text/plain")},
        timeout=30,
    )
    assert resp.status_code == 422
    assert "linkedin" in resp.json().get("detail", "").lower()
