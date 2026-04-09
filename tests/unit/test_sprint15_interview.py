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


# ---------------------------------------------------------------------------
# Task 3: Follow-up question generation
# ---------------------------------------------------------------------------


def test_build_follow_up_question_prompt_contains_hint():
    """Follow-up prompt includes the gap and the hint."""
    from applire.prompts.interview import build_follow_up_question_prompt

    prompt = build_follow_up_question_prompt(
        gap="GCP certification",
        follow_up_hint="ask about GMP or other regulated manufacturing environments",
        profile={"skills": [], "work_history": []},
        recent_messages=[],
    )

    assert "GCP certification" in prompt
    assert "GMP or other regulated" in prompt


def test_build_follow_up_question_prompt_includes_conversation_history():
    """Last 4 messages appear in the follow-up prompt."""
    from applire.prompts.interview import build_follow_up_question_prompt

    messages = [
        {"role": "assistant", "content": "Tell me about your GCP experience."},
        {"role": "user", "content": "I've worked in pharma."},
    ]
    prompt = build_follow_up_question_prompt(
        gap="GCP certification",
        follow_up_hint="ask about GMP",
        profile={},
        recent_messages=messages,
    )

    assert "I've worked in pharma." in prompt


@pytest.mark.asyncio
async def test_question_generator_routes_to_followup_when_hint_present():
    """question_generator_with_profile calls follow-up prompt when follow_up_hint is set."""
    from applire.services.interview_graph import question_generator_with_profile

    provider = MagicMock()
    provider.acomplete = AsyncMock(return_value="Have you worked in GMP-regulated environments?")

    state = {
        "mode": "targeted",
        "critical_gaps": ["GCP certification"],
        "current_gap_index": 0,
        "messages": [],
    }

    result = await question_generator_with_profile(
        state,
        profile={},
        provider=provider,
        follow_up_hint="ask about GMP or other regulated environments",
    )

    assert result == "Have you worked in GMP-regulated environments?"
    # Confirm it was called with the follow-up system prompt
    call_kwargs = provider.acomplete.call_args.kwargs
    assert "follow" in call_kwargs.get("system", "").lower() or "adjacent" in call_kwargs.get("system", "").lower()


@pytest.mark.asyncio
async def test_question_generator_routes_to_standard_when_no_hint():
    """question_generator_with_profile uses standard prompt when follow_up_hint is None."""
    from applire.services.interview_graph import question_generator_with_profile

    provider = MagicMock()
    provider.acomplete = AsyncMock(return_value="Tell me about your GCP experience.")

    state = {
        "mode": "targeted",
        "critical_gaps": ["GCP certification"],
        "current_gap_index": 0,
        "messages": [],
    }

    result = await question_generator_with_profile(
        state,
        profile={},
        provider=provider,
        follow_up_hint=None,
    )

    assert result == "Tell me about your GCP experience."


# ---------------------------------------------------------------------------
# Task 4: profile_updater — certifications, languages, education
# ---------------------------------------------------------------------------


def test_profile_updater_adds_certification():
    """New certification is appended to profile."""
    from applire.services.interview_graph import profile_updater

    profile = {"skills": [], "work_experience": [], "certifications": []}
    patch = {
        "skills_to_add": [],
        "work_history_to_add": [],
        "certifications_to_add": [
            {"name": "Certified Mediator", "issuing_body": "IHK", "year": "2022"}
        ],
        "languages_to_add": [],
        "education_to_add": [],
    }

    updated, conflicts = profile_updater(profile, patch)

    assert len(updated["certifications"]) == 1
    assert updated["certifications"][0]["name"] == "Certified Mediator"
    assert conflicts == []


def test_profile_updater_skips_duplicate_certification():
    """Certification with same name (case-insensitive) is not duplicated."""
    from applire.services.interview_graph import profile_updater

    profile = {
        "skills": [],
        "work_experience": [],
        "certifications": [{"name": "Certified Mediator", "issuing_body": "IHK", "year": "2022"}],
    }
    patch = {
        "skills_to_add": [],
        "work_history_to_add": [],
        "certifications_to_add": [{"name": "certified mediator", "issuing_body": None, "year": None}],
        "languages_to_add": [],
        "education_to_add": [],
    }

    updated, _ = profile_updater(profile, patch)

    assert len(updated["certifications"]) == 1  # no duplicate


def test_profile_updater_adds_language():
    """New language is appended to profile."""
    from applire.services.interview_graph import profile_updater

    profile = {"skills": [], "work_experience": [], "languages": []}
    patch = {
        "skills_to_add": [],
        "work_history_to_add": [],
        "certifications_to_add": [],
        "languages_to_add": [{"language": "Spanish", "level": "professional"}],
        "education_to_add": [],
    }

    updated, _ = profile_updater(profile, patch)

    assert len(updated["languages"]) == 1
    assert updated["languages"][0]["language"] == "Spanish"


def test_profile_updater_skips_duplicate_language():
    """Existing language is not duplicated (existing level kept)."""
    from applire.services.interview_graph import profile_updater

    profile = {
        "skills": [],
        "work_experience": [],
        "languages": [{"language": "German", "level": "native"}],
    }
    patch = {
        "skills_to_add": [],
        "work_history_to_add": [],
        "certifications_to_add": [],
        "languages_to_add": [{"language": "german", "level": "basic"}],
        "education_to_add": [],
    }

    updated, _ = profile_updater(profile, patch)

    assert len(updated["languages"]) == 1
    assert updated["languages"][0]["level"] == "native"  # existing level preserved


def test_profile_updater_adds_education():
    """New education entry is appended."""
    from applire.services.interview_graph import profile_updater

    profile = {"skills": [], "work_experience": [], "education": []}
    patch = {
        "skills_to_add": [],
        "work_history_to_add": [],
        "certifications_to_add": [],
        "languages_to_add": [],
        "education_to_add": [
            {"institution": "TU Berlin", "degree": "M.Sc.", "field": "Informatik", "graduation_year": "2019"}
        ],
    }

    updated, _ = profile_updater(profile, patch)

    assert len(updated["education"]) == 1
    assert updated["education"][0]["degree"] == "M.Sc."


def test_profile_updater_skips_duplicate_education():
    """Same institution+degree pair is not duplicated (case-insensitive)."""
    from applire.services.interview_graph import profile_updater

    profile = {
        "skills": [],
        "work_experience": [],
        "education": [{"institution": "TU Berlin", "degree": "M.Sc.", "field": "Informatik", "graduation_year": "2019"}],
    }
    patch = {
        "skills_to_add": [],
        "work_history_to_add": [],
        "certifications_to_add": [],
        "languages_to_add": [],
        "education_to_add": [
            {"institution": "tu berlin", "degree": "m.sc.", "field": None, "graduation_year": None}
        ],
    }

    updated, _ = profile_updater(profile, patch)

    assert len(updated["education"]) == 1


def test_profile_updater_missing_new_fields_safe():
    """profile_updater handles patches without new fields (old format)."""
    from applire.services.interview_graph import profile_updater

    profile = {"skills": [], "work_experience": []}
    patch = {
        "skills_to_add": ["Python"],
        "work_history_to_add": [],
        # No certifications_to_add / languages_to_add / education_to_add
    }

    updated, conflicts = profile_updater(profile, patch)

    assert "Python" in [s if isinstance(s, str) else s.get("name") for s in updated["skills"]]
    assert conflicts == []


# ---------------------------------------------------------------------------
# Task 5: _next_valid_index and _count_remaining
# ---------------------------------------------------------------------------


def test_next_valid_index_no_skipped():
    """Returns from_index unchanged when nothing is skipped."""
    from applire.services.session import _next_valid_index

    gaps = ["gap_a", "gap_b", "gap_c"]
    assert _next_valid_index(gaps, 1, set()) == 1


def test_next_valid_index_skips_one():
    """Skips a single skipped gap."""
    from applire.services.session import _next_valid_index

    gaps = ["gap_a", "gap_b", "gap_c"]
    assert _next_valid_index(gaps, 1, {"gap_b"}) == 2


def test_next_valid_index_skips_multiple():
    """Skips consecutive skipped gaps."""
    from applire.services.session import _next_valid_index

    gaps = ["gap_a", "gap_b", "gap_c", "gap_d"]
    assert _next_valid_index(gaps, 1, {"gap_b", "gap_c"}) == 3


def test_next_valid_index_all_remaining_skipped():
    """Returns len(gaps) when all remaining gaps are skipped (signals exhaustion)."""
    from applire.services.session import _next_valid_index

    gaps = ["gap_a", "gap_b", "gap_c"]
    assert _next_valid_index(gaps, 1, {"gap_b", "gap_c"}) == 3


def test_count_remaining_no_skipped():
    """Counts all gaps from from_index when nothing is skipped."""
    from applire.services.session import _count_remaining

    gaps = ["gap_a", "gap_b", "gap_c"]
    assert _count_remaining(gaps, 1, set()) == 2


def test_count_remaining_with_skipped():
    """Excludes skipped gaps from count."""
    from applire.services.session import _count_remaining

    gaps = ["gap_a", "gap_b", "gap_c", "gap_d"]
    assert _count_remaining(gaps, 1, {"gap_c"}) == 2  # gap_b and gap_d


def test_count_remaining_all_skipped():
    """Returns 0 when all remaining gaps are skipped."""
    from applire.services.session import _count_remaining

    gaps = ["gap_a", "gap_b", "gap_c"]
    assert _count_remaining(gaps, 1, {"gap_b", "gap_c"}) == 0


# ---------------------------------------------------------------------------
# Task 6: send_message advance logic (Feature 1 — multi-question per gap)
# ---------------------------------------------------------------------------

import uuid


def _make_state(
    gaps: list[str],
    current_index: int = 0,
    questions_asked: int = 1,
    hard_ceiling: int = 12,
    questions_per_gap: dict | None = None,
    skipped_gaps: list[str] | None = None,
    addressed_gaps: list[str] | None = None,
) -> dict:
    """Build a minimal InterviewState for testing send_message logic."""
    return {
        "mode": "targeted",
        "job_id": str(uuid.uuid4()),
        "gap_analysis_id": None,
        "profile_id": str(uuid.uuid4()),
        "critical_gaps": gaps,
        "gap_categories": {},
        "addressed_gaps": addressed_gaps or [],
        "current_gap_index": current_index,
        "current_question": "Tell me about your GCP experience.",
        "messages": [{"role": "assistant", "content": "Tell me about your GCP experience."}],
        "questions_asked": questions_asked,
        "hard_ceiling": hard_ceiling,
        "questions_per_gap": questions_per_gap or {},
        "skipped_gaps": skipped_gaps or [],
        "full_gaps": [],
    }


def test_build_state_includes_new_fields():
    """_build_state initialises questions_per_gap, skipped_gaps, full_gaps."""
    from applire.services.session import _build_state

    state = _build_state(
        mode="targeted",
        job_id=uuid.uuid4(),
        gap_analysis_id=None,
        profile_id=uuid.uuid4(),
        critical_gaps=["gap_a"],
        gap_categories={},
        current_question="",
        hard_ceiling=12,
    )

    assert state["questions_per_gap"] == {}
    assert state["skipped_gaps"] == []
    assert state["full_gaps"] == []
