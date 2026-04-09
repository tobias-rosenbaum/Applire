"""
Sprint 15 — Smart Gap Interview unit tests.

Tests: response_parser, profile_updater, question_generator_with_profile,
       send_message advance/follow-up/cross-gap logic, _next_valid_index,
       _count_remaining, build_response_parser_prompt, build_follow_up_question_prompt.

No Docker, no real LLM — async tests use mocked providers.

Run:
    pytest tests/unit/test_sprint15_interview.py -v
"""
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

_backend = Path(__file__).parent.parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


# ---------------------------------------------------------------------------
# Task 1: Constants
# ---------------------------------------------------------------------------

def test_max_questions_per_gap_default():
    os.environ.pop("INTERVIEW_MAX_QUESTIONS_PER_GAP", None)
    import importlib
    import applire.constants as c
    importlib.reload(c)
    assert c.INTERVIEW_MAX_QUESTIONS_PER_GAP == 3


def test_max_questions_per_gap_env_override():
    os.environ["INTERVIEW_MAX_QUESTIONS_PER_GAP"] = "5"
    import importlib
    import applire.constants as c
    importlib.reload(c)
    assert c.INTERVIEW_MAX_QUESTIONS_PER_GAP == 5
    os.environ.pop("INTERVIEW_MAX_QUESTIONS_PER_GAP", None)
    importlib.reload(c)  # restore default for subsequent tests
