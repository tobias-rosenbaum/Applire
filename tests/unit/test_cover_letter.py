"""
Sprint 25 — Cover Letter Generation (unit tests)
No Docker, no LLM, no external services.

Run:
    pytest tests/unit/test_cover_letter.py -v
"""
import sys
from pathlib import Path

import pytest

_backend = Path(__file__).parent.parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


# ---------------------------------------------------------------------------
# Task 2 — TTL constants
# ---------------------------------------------------------------------------

def test_generated_documents_ttl_default():
    from applire.constants import GENERATED_DOCUMENTS_TTL_DAYS
    assert GENERATED_DOCUMENTS_TTL_DAYS == 90


def test_interview_session_ttl_default():
    from applire.constants import INTERVIEW_SESSION_TTL_DAYS
    assert INTERVIEW_SESSION_TTL_DAYS == 30


def test_upload_ttl_default():
    from applire.constants import UPLOAD_TTL_DAYS
    assert UPLOAD_TTL_DAYS == 7


def test_profile_inactivity_ttl_default():
    from applire.constants import PROFILE_INACTIVITY_TTL_DAYS
    assert PROFILE_INACTIVITY_TTL_DAYS == 730
