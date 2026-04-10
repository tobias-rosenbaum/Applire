"""
Smoke tests for review prompt builders — verify they render without error.

No LLM calls. No Docker.

Run:
    pytest tests/unit/test_review_prompts.py -v
"""
import sys
from pathlib import Path

import pytest

_backend = Path(__file__).parent.parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


_SAMPLE_PROFILE = {
    "work_history": [
        {
            "company": "Acme GmbH",
            "role": "Software Developer",
            "start_date": "2020-01",
            "end_date": "2022-12",
            "bullets": ["Built APIs", "Led migrations"],
        }
    ],
    "skills": ["Python", "FastAPI"],
    "education": [],
    "languages": [{"language": "German", "level": "Native"}],
    "contact": {"name": "Max Muster", "email": None, "phone": None, "location": "Berlin", "linkedin": None},
}

_SAMPLE_RAW_CV = "Acme GmbH — Software Developer (Jan 2020 – Dec 2022)\n- Built APIs\n- Led migrations"


class TestProfileExtractionReviewPrompts:
    def test_build_review_prompt_returns_nonempty_string(self):
        from applire.prompts.review_profile_extraction import build_review_prompt

        result = build_review_prompt(_SAMPLE_RAW_CV, _SAMPLE_PROFILE)
        assert isinstance(result, str)
        assert len(result) > 50

    def test_build_review_prompt_includes_source_text(self):
        from applire.prompts.review_profile_extraction import build_review_prompt

        result = build_review_prompt(_SAMPLE_RAW_CV, _SAMPLE_PROFILE)
        assert "Acme GmbH" in result

    def test_build_review_prompt_includes_extracted_json(self):
        from applire.prompts.review_profile_extraction import build_review_prompt

        result = build_review_prompt(_SAMPLE_RAW_CV, _SAMPLE_PROFILE)
        assert "Software Developer" in result

    def test_review_system_prompt_is_nonempty_string(self):
        from applire.prompts.review_profile_extraction import REVIEW_SYSTEM_PROMPT

        assert isinstance(REVIEW_SYSTEM_PROMPT, str)
        assert len(REVIEW_SYSTEM_PROMPT) > 100


class TestProfileExtractionGeneratorPrompts:
    def test_build_user_prompt_includes_raw_text(self):
        from applire.prompts.profile_extraction import build_user_prompt

        result = build_user_prompt("Max Muster — Acme GmbH")
        assert "Max Muster" in result
        assert "exactly once" in result  # grounding reminder

    def test_build_retry_prompt_includes_feedback(self):
        from applire.prompts.profile_extraction import build_retry_prompt

        result = build_retry_prompt(
            raw_text="Acme GmbH 2020-2022",
            previous_draft={"work_history": []},
            feedback="Remove duplicate at index 1",
        )
        assert "Remove duplicate at index 1" in result
        assert "Acme GmbH 2020-2022" in result

    def test_build_retry_prompt_includes_previous_draft(self):
        from applire.prompts.profile_extraction import build_retry_prompt

        previous = {"work_history": [{"company": "Acme"}]}
        result = build_retry_prompt(
            raw_text="source",
            previous_draft=previous,
            feedback="fix it",
        )
        assert "Acme" in result
