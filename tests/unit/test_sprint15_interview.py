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


# ---------------------------------------------------------------------------
# Task 2: ResponseParser
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_response_parser_full_resolution():
    """gap_resolution=full → gap_addressed=True, follow_up_hint=None."""
    from applire.services.interview_graph import response_parser

    provider = MagicMock()
    provider.aparse_json = AsyncMock(return_value={
        "skills_to_add": ["Python"],
        "work_history_to_add": [],
        "certifications_to_add": [],
        "languages_to_add": [],
        "education_to_add": [],
        "gap_resolution": "full",
        "follow_up_hint": None,
        "gaps_also_addressed": [],
    })

    result = await response_parser("Python", "Do you know Python?", "Yes, 5 years.", provider)

    assert result["gap_resolution"] == "full"
    assert result["gap_addressed"] is True  # backward compat
    assert result["follow_up_hint"] is None
    assert result["gaps_also_addressed"] == []
    assert result["skills_to_add"] == ["Python"]


@pytest.mark.asyncio
async def test_response_parser_partial_resolution():
    """gap_resolution=partial → gap_addressed=True (partial counts), follow_up_hint set."""
    from applire.services.interview_graph import response_parser

    provider = MagicMock()
    provider.aparse_json = AsyncMock(return_value={
        "skills_to_add": [],
        "work_history_to_add": [],
        "certifications_to_add": [],
        "languages_to_add": [],
        "education_to_add": [],
        "gap_resolution": "partial",
        "follow_up_hint": "ask about GMP or other regulated environments",
        "gaps_also_addressed": [],
    })

    result = await response_parser("GCP experience", "Any question?", "I've worked in pharma.", provider)

    assert result["gap_resolution"] == "partial"
    assert result["gap_addressed"] is True
    assert result["follow_up_hint"] == "ask about GMP or other regulated environments"


@pytest.mark.asyncio
async def test_response_parser_none_resolution():
    """gap_resolution=none → gap_addressed=False."""
    from applire.services.interview_graph import response_parser

    provider = MagicMock()
    provider.aparse_json = AsyncMock(return_value={
        "skills_to_add": [],
        "work_history_to_add": [],
        "certifications_to_add": [],
        "languages_to_add": [],
        "education_to_add": [],
        "gap_resolution": "none",
        "follow_up_hint": "ask about adjacent regulated industries",
        "gaps_also_addressed": [],
    })

    result = await response_parser("GCP experience", "Any?", "I don't know.", provider)

    assert result["gap_resolution"] == "none"
    assert result["gap_addressed"] is False


@pytest.mark.asyncio
async def test_response_parser_cross_gap_populated():
    """gaps_also_addressed is forwarded from LLM response."""
    from applire.services.interview_graph import response_parser

    provider = MagicMock()
    provider.aparse_json = AsyncMock(return_value={
        "skills_to_add": [],
        "work_history_to_add": [],
        "certifications_to_add": [],
        "languages_to_add": [],
        "education_to_add": [],
        "gap_resolution": "full",
        "follow_up_hint": None,
        "gaps_also_addressed": ["GMP certification", "regulated environment experience"],
    })

    result = await response_parser(
        "GCP experience", "Question?", "I worked in pharma with GMP.", provider,
        remaining_gaps=["GMP certification", "regulated environment experience"]
    )

    assert result["gaps_also_addressed"] == ["GMP certification", "regulated environment experience"]


@pytest.mark.asyncio
async def test_response_parser_invalid_gap_resolution_defaults_to_none():
    """Unexpected gap_resolution value from LLM defaults to 'none'."""
    from applire.services.interview_graph import response_parser

    provider = MagicMock()
    provider.aparse_json = AsyncMock(return_value={
        "skills_to_add": [],
        "work_history_to_add": [],
        "certifications_to_add": [],
        "languages_to_add": [],
        "education_to_add": [],
        "gap_resolution": "yes",  # invalid
        "follow_up_hint": None,
        "gaps_also_addressed": [],
    })

    result = await response_parser("gap", "q", "a", provider)
    assert result["gap_resolution"] == "none"
    assert result["gap_addressed"] is False


def test_build_response_parser_prompt_includes_remaining_gaps():
    """remaining_gaps appear in the prompt when provided."""
    from applire.prompts.interview import build_response_parser_prompt

    prompt = build_response_parser_prompt(
        "GCP experience",
        "Tell me about GCP?",
        "I've done some pharma work.",
        remaining_gaps=["GMP certification", "ISO 9001"],
    )

    assert "GMP certification" in prompt
    assert "ISO 9001" in prompt
    assert "Other open gaps" in prompt


def test_build_response_parser_prompt_no_remaining_gaps():
    """No remaining_gaps section when list is empty or None."""
    from applire.prompts.interview import build_response_parser_prompt

    prompt_none = build_response_parser_prompt("gap", "q", "a", remaining_gaps=None)
    prompt_empty = build_response_parser_prompt("gap", "q", "a", remaining_gaps=[])

    assert "Other open gaps" not in prompt_none
    assert "Other open gaps" not in prompt_empty


@pytest.mark.asyncio
async def test_response_parser_returns_enrichment_fields():
    """certifications, languages, education are returned from the parser."""
    from applire.services.interview_graph import response_parser

    provider = MagicMock()
    provider.aparse_json = AsyncMock(return_value={
        "skills_to_add": [],
        "work_history_to_add": [],
        "certifications_to_add": [{"name": "Certified Mediator", "issuing_body": "IHK", "year": "2022"}],
        "languages_to_add": [{"language": "Spanish", "level": "professional"}],
        "education_to_add": [{"institution": "TU Berlin", "degree": "M.Sc.", "field": "Informatik", "graduation_year": "2019"}],
        "gap_resolution": "full",
        "follow_up_hint": None,
        "gaps_also_addressed": [],
    })

    result = await response_parser("mediation skills", "Tell me about certifications.", "I'm a certified mediator.", provider)

    assert result["certifications_to_add"] == [{"name": "Certified Mediator", "issuing_body": "IHK", "year": "2022"}]
    assert result["languages_to_add"] == [{"language": "Spanish", "level": "professional"}]
    assert result["education_to_add"] == [{"institution": "TU Berlin", "degree": "M.Sc.", "field": "Informatik", "graduation_year": "2019"}]
