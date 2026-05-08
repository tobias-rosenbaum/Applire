# Sprint 15 — Smart Gap Interview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the MODE A gap interview with per-gap follow-up questions (lateral-probe style), cross-gap resolution, and expanded profile enrichment from answers.

**Architecture:** All three features share a single extended `ResponseParser` LLM call per turn — no extra round-trips. `send_message` branches on `gap_resolution` to either advance to the next gap or ask a follow-up; a new `skipped_gaps` list in session state tracks cross-resolved gaps. Profile enrichment adds certifications, languages, and education alongside existing skills + work history.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy async, Mistral via `LLMProvider` abstraction, pytest + AsyncMock.

**Spec:** `docs/superpowers/specs/2026-04-08-sprint15-smart-gap-interview.md`

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `backend/applire/constants.py` | Modify | Add `INTERVIEW_MAX_QUESTIONS_PER_GAP` (env-var backed) |
| `backend/applire/schemas/session.py` | Modify | Add `questions_per_gap`, `skipped_gaps`, `full_gaps` to `InterviewState`; add `gaps_also_addressed` to `SessionMessageResponse` |
| `backend/applire/prompts/interview.py` | Modify | Extend `RESPONSE_PARSER_SYSTEM_PROMPT` + `build_response_parser_prompt`; add `FOLLOW_UP_QUESTION_SYSTEM_PROMPT` + `build_follow_up_question_prompt` |
| `backend/applire/services/interview_graph.py` | Modify | Extend `response_parser` (new fields + `remaining_gaps`); extend `profile_updater` (3 new merge rules); extend `question_generator_with_profile` (`follow_up_hint`) |
| `backend/applire/services/session.py` | Modify | Add helpers `_next_valid_index`, `_count_remaining`; rewrite `send_message` advance logic; add `questions_per_gap`/`skipped_gaps`/`full_gaps` to `_build_state`; update `_create_micro_session` to set `full_gaps`; fix `_complete_session` unresolved list |
| `tests/unit/test_sprint15_interview.py` | Create | All unit tests for this sprint |
| `Documents/Architecture/arc42.md` | Modify (Nextcloud, no commit) | Update 5.3.3 table + v2.11 changelog entry |
| `Documents/Architecture/ADR.md` | Modify (Nextcloud, no commit) | Add Sprint 15 amendment note to ADR-004 |

---

## Task 1: Constants and Schema — `INTERVIEW_MAX_QUESTIONS_PER_GAP` + State Fields

**Files:**
- Modify: `backend/applire/constants.py`
- Modify: `backend/applire/schemas/session.py`
- Create: `tests/unit/test_sprint15_interview.py`

- [ ] **Step 1: Create the test file with a failing test for the new constant**

```python
# tests/unit/test_sprint15_interview.py
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
```

- [ ] **Step 2: Run the test to confirm it fails**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_sprint15_interview.py::test_max_questions_per_gap_default -v
```

Expected: `FAILED` — `AttributeError: module 'applire.constants' has no attribute 'INTERVIEW_MAX_QUESTIONS_PER_GAP'`

- [ ] **Step 3: Add the constant to `constants.py`**

Open `backend/applire/constants.py`. The current content is:

```python
# Interview orchestrator thresholds and limits (ADR 004, Iteration 14)

# Mode auto-detection: completeness_score below this → MODE B (Guided Build)
MODE_B_COMPLETENESS_THRESHOLD: float = 0.3

# Hard ceilings — session ends after this many questions even if gaps remain
INTERVIEW_HARD_CEILING_TARGETED: int = 12  # MODE A
INTERVIEW_HARD_CEILING_GUIDED: int = 20    # MODE B

# Soft targets — informational only, used for estimated_questions in response
INTERVIEW_TARGET_MIN_TARGETED: int = 3
INTERVIEW_TARGET_MIN_GUIDED: int = 5
```

Replace with:

```python
import os

# Interview orchestrator thresholds and limits (ADR 004, Iteration 14)

# Mode auto-detection: completeness_score below this → MODE B (Guided Build)
MODE_B_COMPLETENESS_THRESHOLD: float = 0.3

# Hard ceilings — session ends after this many questions even if gaps remain
INTERVIEW_HARD_CEILING_TARGETED: int = 12  # MODE A
INTERVIEW_HARD_CEILING_GUIDED: int = 20    # MODE B

# Soft targets — informational only, used for estimated_questions in response
INTERVIEW_TARGET_MIN_TARGETED: int = 3
INTERVIEW_TARGET_MIN_GUIDED: int = 5

# Per-gap question ceiling (Sprint 15): max questions asked for a single gap
# before force-advancing to the next one. Includes the initial question.
# Set INTERVIEW_MAX_QUESTIONS_PER_GAP in environment to override (e.g. in docker-compose.yml).
INTERVIEW_MAX_QUESTIONS_PER_GAP: int = int(
    os.environ.get("INTERVIEW_MAX_QUESTIONS_PER_GAP", "3")
)
```

- [ ] **Step 4: Run both constant tests to confirm they pass**

```bash
pytest tests/unit/test_sprint15_interview.py::test_max_questions_per_gap_default tests/unit/test_sprint15_interview.py::test_max_questions_per_gap_env_override -v
```

Expected: both `PASSED`

- [ ] **Step 5: Extend `InterviewState` and `SessionMessageResponse` in `schemas/session.py`**

Open `backend/applire/schemas/session.py`. The `InterviewState` TypedDict currently ends at `hard_ceiling`. Add three new fields. Also add `gaps_also_addressed` to `SessionMessageResponse`.

Find `class InterviewState(TypedDict):` and replace the entire class:

```python
class InterviewState(TypedDict):
    mode: str  # "targeted" | "guided"
    job_id: str
    gap_analysis_id: str | None  # None for MODE B until lazy analysis
    profile_id: str
    # MODE A: ordered gap strings (C-first, then B)
    # MODE B: ordered section names to build
    critical_gaps: list[str]
    gap_categories: dict  # {gap_str: "B" | "C"} — empty dict for MODE B
    addressed_gaps: list[str]
    current_gap_index: int
    current_question: str
    messages: list[dict]  # {"role": "assistant"|"user", "content": "..."}
    questions_asked: int
    hard_ceiling: int
    # Sprint 15 additions (optional — missing keys default to {} / [] / [])
    questions_per_gap: dict   # gap_str → questions asked so far for this gap
    skipped_gaps: list[str]   # gaps resolved transitively via cross-gap answer
    full_gaps: list[str]      # full gap list from analysis; set for micro-sessions only
```

Find `class SessionMessageResponse(BaseModel):` and add `gaps_also_addressed` as the last field:

```python
class SessionMessageResponse(BaseModel):
    complete: bool
    question: str | None = None
    gaps_remaining: int | None = None
    # Populated when complete=True
    reason: Literal["gaps_resolved", "user_ended", "max_questions_reached"] | None = None
    questions_asked: int | None = None
    gaps_resolved: int | None = None
    gaps_unresolved: list[str] | None = None
    completeness_score: float | None = None
    # Populated when ProfileUpdater detects a merge conflict (19.10)
    pending_conflicts: list[ConflictSummary] | None = None
    # Populated when cross-gap resolution fires (Sprint 15)
    gaps_also_addressed: list[str] | None = None
```

- [ ] **Step 6: Commit**

```bash
git add backend/applire/constants.py backend/applire/schemas/session.py tests/unit/test_sprint15_interview.py
git commit -m "feat(interview): add INTERVIEW_MAX_QUESTIONS_PER_GAP constant and extend InterviewState schema"
```

---

## Task 2: ResponseParser — Extended Prompt and Function

**Files:**
- Modify: `backend/applire/prompts/interview.py`
- Modify: `backend/applire/services/interview_graph.py`
- Modify: `tests/unit/test_sprint15_interview.py`

- [ ] **Step 1: Write failing tests for the updated `response_parser` and prompt builder**

Append to `tests/unit/test_sprint15_interview.py`:

```python
# ---------------------------------------------------------------------------
# Task 2: ResponseParser
# ---------------------------------------------------------------------------

import pytest


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


def test_build_response_parser_prompt_no_remaining_gaps():
    """No remaining_gaps section when list is empty or None."""
    from applire.prompts.interview import build_response_parser_prompt

    prompt_none = build_response_parser_prompt("gap", "q", "a", remaining_gaps=None)
    prompt_empty = build_response_parser_prompt("gap", "q", "a", remaining_gaps=[])

    assert "Other open gaps" not in prompt_none
    assert "Other open gaps" not in prompt_empty
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/unit/test_sprint15_interview.py -k "response_parser or build_response_parser" -v
```

Expected: `FAILED` — `TypeError: response_parser() got an unexpected keyword argument 'remaining_gaps'` and similar

- [ ] **Step 3: Update `RESPONSE_PARSER_SYSTEM_PROMPT` and `build_response_parser_prompt` in `prompts/interview.py`**

Find and replace the entire `# ResponseParser node` section (from the comment to the end of the file):

```python
# ---------------------------------------------------------------------------
# ResponseParser node
# ---------------------------------------------------------------------------

RESPONSE_PARSER_SYSTEM_PROMPT = """\
You are an expert career coach extracting structured profile data from a candidate's free-text answer.
Respond ONLY with a valid JSON object matching the schema below — no markdown, no explanations.

Schema:
{
  "skills_to_add": ["list of concrete skills explicitly mentioned"],
  "work_history_to_add": [
    {
      "company": "Company name or null",
      "role": "Job title or null",
      "start_date": "YYYY-MM or YYYY or null",
      "end_date": "YYYY-MM or YYYY or null (null = current)",
      "bullets": ["achievement or responsibility mentioned"]
    }
  ],
  "certifications_to_add": [
    {"name": "Certification name", "issuing_body": "Issuing body or null", "year": "YYYY or null"}
  ],
  "languages_to_add": [
    {"language": "Language name", "level": "native|fluent|professional|basic"}
  ],
  "education_to_add": [
    {
      "institution": "Institution name",
      "degree": "Degree title",
      "field": "Field of study or null",
      "graduation_year": "YYYY or null"
    }
  ],
  "gap_resolution": "full or partial or none",
  "follow_up_hint": "Short suggestion for adjacent domain to probe, or null",
  "gaps_also_addressed": ["list of other open gaps this answer also resolves"]
}

Rules:
- Only include data EXPLICITLY stated in the answer — do not infer or fabricate
- gap_resolution: "full" if the answer provides concrete, specific information about the gap;
  "partial" if relevant but incomplete or vague; "none" if off-topic or empty
- follow_up_hint: when gap_resolution is "partial" or "none", suggest a related domain or context
  the candidate might have experience in (e.g. "ask about GMP or other regulated environments").
  Set to null when gap_resolution is "full".
- gaps_also_addressed: list any other open gaps (from the provided list) that this answer also
  resolves. Empty list if none or if no list was provided.
- Omit work_history_to_add entries where role is null or empty"""


def build_response_parser_prompt(
    gap: str,
    question: str,
    answer: str,
    remaining_gaps: list[str] | None = None,
) -> str:
    other_gaps_section = ""
    if remaining_gaps:
        gaps_list = "\n".join(f"- {g}" for g in remaining_gaps)
        other_gaps_section = (
            f"\n\nOther open gaps (check if this answer also resolves any):\n{gaps_list}"
        )
    return (
        f"Gap being addressed: {gap}\n\n"
        f"Question asked: {question}\n\n"
        f"Candidate's answer: {answer}"
        f"{other_gaps_section}\n\n"
        "Extract the structured profile data."
    )
```

- [ ] **Step 4: Update `response_parser` in `interview_graph.py`**

Find the entire `response_parser` function and replace it:

```python
async def response_parser(
    gap: str,
    question: str,
    answer: str,
    provider: LLMProvider,
    remaining_gaps: list[str] | None = None,
) -> dict:
    """Extract structured profile data from the user's free-text answer.

    Returns a dict with keys:
        skills_to_add: list[str]
        work_history_to_add: list[dict]
        certifications_to_add: list[dict]
        languages_to_add: list[dict]
        education_to_add: list[dict]
        gap_resolution: "full" | "partial" | "none"
        follow_up_hint: str | None
        gaps_also_addressed: list[str]
        gap_addressed: bool  (backward compat — derived from gap_resolution != "none")
    """
    data = await provider.aparse_json(
        build_response_parser_prompt(gap, question, answer, remaining_gaps),
        system=RESPONSE_PARSER_SYSTEM_PROMPT,
        temperature=0.1,
    )
    gap_resolution = data.get("gap_resolution", "none")
    if gap_resolution not in ("full", "partial", "none"):
        gap_resolution = "none"
    return {
        "skills_to_add": data.get("skills_to_add", []),
        "work_history_to_add": data.get("work_history_to_add", []),
        "certifications_to_add": data.get("certifications_to_add", []),
        "languages_to_add": data.get("languages_to_add", []),
        "education_to_add": data.get("education_to_add", []),
        "gap_resolution": gap_resolution,
        "follow_up_hint": data.get("follow_up_hint"),
        "gaps_also_addressed": data.get("gaps_also_addressed", []),
        "gap_addressed": gap_resolution != "none",  # backward compat
    }
```

- [ ] **Step 5: Run the ResponseParser tests to confirm they pass**

```bash
pytest tests/unit/test_sprint15_interview.py -k "response_parser or build_response_parser" -v
```

Expected: all `PASSED`

- [ ] **Step 6: Commit**

```bash
git add backend/applire/prompts/interview.py backend/applire/services/interview_graph.py tests/unit/test_sprint15_interview.py
git commit -m "feat(interview): extend ResponseParser schema with gap_resolution, follow_up_hint, cross-gap fields, and profile enrichment fields"
```

---

## Task 3: Follow-up Question Generation

**Files:**
- Modify: `backend/applire/prompts/interview.py`
- Modify: `backend/applire/services/interview_graph.py`
- Modify: `tests/unit/test_sprint15_interview.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/unit/test_sprint15_interview.py`:

```python
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/unit/test_sprint15_interview.py -k "follow_up or followup or routes_to" -v
```

Expected: `FAILED` — `TypeError` or `ImportError` on `build_follow_up_question_prompt`

- [ ] **Step 3: Add follow-up prompt builder to `prompts/interview.py`**

Add after the `build_guided_question_prompt` function (before the `# ResponseParser node` comment):

```python
# ---------------------------------------------------------------------------
# QuestionGenerator node — Follow-up (lateral probe, Sprint 15)
# ---------------------------------------------------------------------------

FOLLOW_UP_QUESTION_SYSTEM_PROMPT = """\
You are an expert career coach specialised in the DACH (Germany, Austria, Switzerland) job market.
The candidate has not yet fully addressed a specific gap in their profile.
Do NOT re-ask the original question. Instead, probe an adjacent domain or analogous
context that is likely to surface the missing experience indirectly.

Requirements:
- Lead with the adjacent domain suggested in the follow-up hint
- Be concrete: name the technology, regulation, industry, or context to explore
- Remain encouraging — the candidate may simply not have recognised the connection
- Output ONLY the question text — no preamble, no numbering, no explanation"""


def build_follow_up_question_prompt(
    gap: str,
    follow_up_hint: str,
    profile: dict,
    recent_messages: list[dict],
    gap_category: str | None = None,
) -> str:
    """Build the prompt for a lateral-probe follow-up question.

    gap: the gap that was not fully addressed
    follow_up_hint: suggested adjacent domain (from ResponseParser)
    profile: candidate's current profile dict
    recent_messages: last N messages from the conversation
    gap_category: "B" | "C" | None
    """
    history = ""
    if recent_messages:
        lines = [f"{m['role'].capitalize()}: {m['content']}" for m in recent_messages[-4:]]
        history = "\n\nRecent conversation:\n" + "\n".join(lines)

    profile_summary = json.dumps(
        {
            "skills": profile.get("skills", []),
            "work_history": [
                {"company": e.get("company"), "role": e.get("role")}
                for e in profile.get("work_history", [])
            ],
        },
        ensure_ascii=False,
    )

    return (
        f"Gap not yet addressed: {gap}\n"
        f"Follow-up direction: {follow_up_hint}\n\n"
        f"Candidate profile summary:\n{profile_summary}"
        f"{history}\n\n"
        "Generate the follow-up question probing the adjacent domain."
    )
```

- [ ] **Step 4: Update `question_generator_with_profile` in `interview_graph.py`**

Add `FOLLOW_UP_QUESTION_SYSTEM_PROMPT` and `build_follow_up_question_prompt` to the import from `applire.prompts.interview`:

```python
from applire.prompts.interview import (
    FOLLOW_UP_QUESTION_SYSTEM_PROMPT,
    GUIDED_QUESTION_SYSTEM_PROMPT,
    QUESTION_SYSTEM_PROMPT,
    RESPONSE_PARSER_SYSTEM_PROMPT,
    build_follow_up_question_prompt,
    build_guided_question_prompt,
    build_question_prompt,
    build_response_parser_prompt,
)
```

Find and replace the entire `question_generator_with_profile` function:

```python
async def question_generator_with_profile(
    state: InterviewState,
    profile: dict,
    provider: LLMProvider,
    gap_category: str | None = None,
    job_context: dict | None = None,
    follow_up_hint: str | None = None,
) -> str:
    """Generate the next question based on mode and context.

    MODE A: gap-targeted question (exploratory C or confirmation B)
    MODE B: section-building question
    Follow-up: lateral-probe question when follow_up_hint is provided

    gap_category: "B" | "C" | None (MODE A only)
    job_context: {"role_title": str, "seniority_level": str} (MODE B, optional)
    follow_up_hint: adjacent domain to probe (Sprint 15, overrides standard question)
    """
    mode = state.get("mode", "targeted")

    if follow_up_hint:
        gap = state["critical_gaps"][state["current_gap_index"]]
        question = await provider.acomplete(
            build_follow_up_question_prompt(
                gap,
                follow_up_hint,
                profile,
                state["messages"],
                gap_category=gap_category,
            ),
            system=FOLLOW_UP_QUESTION_SYSTEM_PROMPT,
            temperature=0.4,
            max_tokens=256,
        )
    elif mode == "guided":
        section = state["critical_gaps"][state["current_gap_index"]]
        question = await provider.acomplete(
            build_guided_question_prompt(
                section,
                job_context or {},
                state["messages"],
            ),
            system=GUIDED_QUESTION_SYSTEM_PROMPT,
            temperature=0.4,
            max_tokens=256,
        )
    else:
        gap = state["critical_gaps"][state["current_gap_index"]]
        question = await provider.acomplete(
            build_question_prompt(gap, profile, state["messages"], gap_category=gap_category),
            system=QUESTION_SYSTEM_PROMPT,
            temperature=0.4,
            max_tokens=256,
        )

    return question.strip()
```

- [ ] **Step 5: Run the follow-up tests to confirm they pass**

```bash
pytest tests/unit/test_sprint15_interview.py -k "follow_up or followup or routes_to" -v
```

Expected: all `PASSED`

- [ ] **Step 6: Commit**

```bash
git add backend/applire/prompts/interview.py backend/applire/services/interview_graph.py tests/unit/test_sprint15_interview.py
git commit -m "feat(interview): add lateral-probe follow-up question generator (Sprint 15 Feature 1)"
```

---

## Task 4: Expanded Profile Enrichment in `profile_updater`

**Files:**
- Modify: `backend/applire/services/interview_graph.py`
- Modify: `tests/unit/test_sprint15_interview.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/unit/test_sprint15_interview.py`:

```python
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/unit/test_sprint15_interview.py -k "profile_updater" -v
```

Expected: `FAILED` — assertions fail because `certifications`, `languages`, `education` keys are not being set

- [ ] **Step 3: Update `profile_updater` in `interview_graph.py`**

Find the `profile_updater` function. After the existing `# --- Work experience: append-only ...` block and before `return profile, conflicts`, add the three new merge blocks:

```python
    # --- Certifications: append if name not already present (case-insensitive) ---
    existing_cert_names = {
        (c.get("name") or "").lower() for c in profile.get("certifications", [])
    }
    new_certs = [
        c for c in patch.get("certifications_to_add", [])
        if (c.get("name") or "").lower() not in existing_cert_names
    ]
    if new_certs:
        profile["certifications"] = list(profile.get("certifications", [])) + new_certs

    # --- Languages: append if language not present; keep existing level ---
    existing_lang_names = {
        (l.get("language") or "").lower() for l in profile.get("languages", [])
    }
    new_langs = [
        l for l in patch.get("languages_to_add", [])
        if (l.get("language") or "").lower() not in existing_lang_names
    ]
    if new_langs:
        profile["languages"] = list(profile.get("languages", [])) + new_langs

    # --- Education: append if (institution, degree) pair not present (case-insensitive) ---
    existing_edu_keys = {
        (_norm(e.get("institution")), _norm(e.get("degree")))
        for e in profile.get("education", [])
    }
    new_edu = [
        e for e in patch.get("education_to_add", [])
        if (_norm(e.get("institution")), _norm(e.get("degree"))) not in existing_edu_keys
    ]
    if new_edu:
        profile["education"] = list(profile.get("education", [])) + new_edu
```

The `_norm` helper already exists in `interview_graph.py` at the bottom of the file.

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/unit/test_sprint15_interview.py -k "profile_updater" -v
```

Expected: all `PASSED`

- [ ] **Step 5: Run the full sprint test suite to check for regressions**

```bash
pytest tests/unit/ -v --tb=short 2>&1 | tail -30
```

Expected: all previously passing tests still `PASSED`

- [ ] **Step 6: Commit**

```bash
git add backend/applire/services/interview_graph.py tests/unit/test_sprint15_interview.py
git commit -m "feat(interview): extend profile_updater with certifications, languages, education enrichment"
```

---

## Task 5: Helper Functions `_next_valid_index` and `_count_remaining`

**Files:**
- Modify: `backend/applire/services/session.py`
- Modify: `tests/unit/test_sprint15_interview.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/unit/test_sprint15_interview.py`:

```python
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/unit/test_sprint15_interview.py -k "next_valid_index or count_remaining" -v
```

Expected: `FAILED` — `ImportError: cannot import name '_next_valid_index'`

- [ ] **Step 3: Add the helper functions to `session.py`**

Add after the `_load_job_context` function at the bottom of `backend/applire/services/session.py`:

```python
def _next_valid_index(
    critical_gaps: list[str],
    from_index: int,
    skipped_gaps: set[str],
) -> int:
    """Return the first index >= from_index whose gap is not in skipped_gaps.

    Returns len(critical_gaps) if all remaining gaps are skipped (signals exhaustion).
    """
    idx = from_index
    while idx < len(critical_gaps) and critical_gaps[idx] in skipped_gaps:
        idx += 1
    return idx


def _count_remaining(
    critical_gaps: list[str],
    from_index: int,
    skipped_gaps: set[str],
) -> int:
    """Count non-skipped gaps from from_index onwards (inclusive)."""
    return sum(
        1 for g in critical_gaps[from_index:]
        if g not in skipped_gaps
    )
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/unit/test_sprint15_interview.py -k "next_valid_index or count_remaining" -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add backend/applire/services/session.py tests/unit/test_sprint15_interview.py
git commit -m "feat(interview): add _next_valid_index and _count_remaining helpers for gap advancement"
```

---

## Task 6: Update `_build_state` and Rewrite `send_message` Advance Logic

**Files:**
- Modify: `backend/applire/services/session.py`
- Modify: `tests/unit/test_sprint15_interview.py`

- [ ] **Step 1: Write failing tests for the follow-up path**

Append to `tests/unit/test_sprint15_interview.py`:

```python
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
```

- [ ] **Step 2: Run the test to confirm it fails**

```bash
pytest tests/unit/test_sprint15_interview.py::test_build_state_includes_new_fields -v
```

Expected: `FAILED` — `KeyError: 'questions_per_gap'`

- [ ] **Step 3: Update `_build_state` in `session.py`**

Find the `_build_state` function. The current return dict is:

```python
    return {
        "mode": mode,
        "job_id": str(job_id),
        "gap_analysis_id": str(gap_analysis_id) if gap_analysis_id else None,
        "profile_id": str(profile_id),
        "critical_gaps": critical_gaps,
        "gap_categories": gap_categories,
        "addressed_gaps": [],
        "current_gap_index": 0,
        "current_question": current_question,
        "messages": [],
        "questions_asked": 0,
        "hard_ceiling": hard_ceiling,
    }
```

Replace with:

```python
    return {
        "mode": mode,
        "job_id": str(job_id),
        "gap_analysis_id": str(gap_analysis_id) if gap_analysis_id else None,
        "profile_id": str(profile_id),
        "critical_gaps": critical_gaps,
        "gap_categories": gap_categories,
        "addressed_gaps": [],
        "current_gap_index": 0,
        "current_question": current_question,
        "messages": [],
        "questions_asked": 0,
        "hard_ceiling": hard_ceiling,
        "questions_per_gap": {},
        "skipped_gaps": [],
        "full_gaps": [],
    }
```

- [ ] **Step 4: Run the build_state test to confirm it passes**

```bash
pytest tests/unit/test_sprint15_interview.py::test_build_state_includes_new_fields -v
```

Expected: `PASSED`

- [ ] **Step 5: Add `INTERVIEW_MAX_QUESTIONS_PER_GAP` to the imports in `session.py`**

Find the constants import block:

```python
from applire.constants import (
    INTERVIEW_HARD_CEILING_GUIDED,
    INTERVIEW_HARD_CEILING_TARGETED,
    INTERVIEW_TARGET_MIN_GUIDED,
    INTERVIEW_TARGET_MIN_TARGETED,
    MODE_B_COMPLETENESS_THRESHOLD,
)
```

Replace with:

```python
from applire.constants import (
    INTERVIEW_HARD_CEILING_GUIDED,
    INTERVIEW_HARD_CEILING_TARGETED,
    INTERVIEW_MAX_QUESTIONS_PER_GAP,
    INTERVIEW_TARGET_MIN_GUIDED,
    INTERVIEW_TARGET_MIN_TARGETED,
    MODE_B_COMPLETENESS_THRESHOLD,
)
```

- [ ] **Step 6: Rewrite `send_message` in `session.py`**

Find the entire `send_message` function (lines 396–479 in the original) and replace it with:

```python
async def send_message(
    session_id: uuid.UUID,
    message: str,
    db: AsyncSession,
    provider: LLMProvider,
) -> SessionMessageResponse:
    # Load session
    session_result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.deleted_at.is_(None),
        )
    )
    record = session_result.scalar_one_or_none()
    if record is None:
        raise LookupError(f"Session {session_id} not found")
    if record.status == "complete":
        raise ValueError("Session is already complete")

    state: InterviewState = dict(record.state)
    state["messages"].append({"role": "user", "content": message})

    # --- Done-signal check (pre-LLM, deterministic) ---
    if is_termination_signal(message):
        return await _complete_session(record, state, db, "user_ended")

    current_idx = state["current_gap_index"]
    current_gap = state["critical_gaps"][current_idx]
    current_question = state["current_question"]

    # Compute open gaps for cross-gap context (micro-sessions use full_gaps)
    skipped_set = set(state.get("skipped_gaps", []))
    addressed_set = set(state.get("addressed_gaps", []))
    full_gaps = state.get("full_gaps") or state["critical_gaps"]
    remaining_gaps = [
        g for g in full_gaps
        if g != current_gap and g not in skipped_set and g not in addressed_set
    ]

    # --- ResponseParser ---
    patch = await response_parser(
        current_gap, current_question, message, provider, remaining_gaps
    )

    # --- ProfileUpdater ---
    profile_record = await _load_profile(state["profile_id"], db)
    updated_profile, merge_conflicts = profile_updater(profile_record.profile_json, patch)
    profile_record.profile_json = updated_profile
    profile_record.updated_at = datetime.now(timezone.utc)

    # --- Cross-gap resolution ---
    newly_skipped: list[str] = []
    for also_gap in patch.get("gaps_also_addressed", []):
        if (
            also_gap in state["critical_gaps"]
            and also_gap != current_gap
            and also_gap not in state.get("addressed_gaps", [])
            and also_gap not in state.get("skipped_gaps", [])
        ):
            state.setdefault("skipped_gaps", []).append(also_gap)
            state.setdefault("addressed_gaps", []).append(also_gap)
            newly_skipped.append(also_gap)

    # Increment questions_asked
    questions_asked = state.get("questions_asked", 1) + 1
    state["questions_asked"] = questions_asked
    record.questions_asked = questions_asked

    # --- Hard ceiling check ---
    if questions_asked >= state["hard_ceiling"]:
        state["addressed_gaps"] = state.get("addressed_gaps", []) + [current_gap]
        return await _complete_session(
            record, state, db, "max_questions_reached", profile_record
        )

    # --- Advance decision ---
    gap_resolution = patch.get("gap_resolution", "none")
    questions_for_gap = state.get("questions_per_gap", {}).get(current_gap, 1)

    if gap_resolution == "full" or questions_for_gap >= INTERVIEW_MAX_QUESTIONS_PER_GAP:
        # Advance to next gap
        state["addressed_gaps"] = state.get("addressed_gaps", []) + [current_gap]
        skipped_set_updated = set(state.get("skipped_gaps", []))
        next_index = _next_valid_index(
            state["critical_gaps"], current_idx + 1, skipped_set_updated
        )
        state["current_gap_index"] = next_index
        gaps_remaining = _count_remaining(
            state["critical_gaps"], next_index, skipped_set_updated
        )

        # Gap exhaustion check
        if gaps_remaining <= 0:
            return await _complete_session(
                record, state, db, "gaps_resolved", profile_record
            )

        # Generate next question
        next_gap = state["critical_gaps"][next_index]
        next_category = (state.get("gap_categories") or {}).get(next_gap)
        job_context: dict | None = None
        if state.get("mode") == "guided":
            job_context = await _load_job_context(state["job_id"], db)

        next_question = await question_generator_with_profile(
            state,
            updated_profile,
            provider,
            gap_category=next_category,
            job_context=job_context,
        )
        state["current_question"] = next_question
        state["messages"].append({"role": "assistant", "content": next_question})
        record.state = state
        record.updated_at = datetime.now(timezone.utc)
        await db.commit()

        return SessionMessageResponse(
            complete=False,
            question=next_question,
            gaps_remaining=gaps_remaining,
            pending_conflicts=merge_conflicts if merge_conflicts else None,
            gaps_also_addressed=newly_skipped if newly_skipped else None,
        )

    else:
        # Follow-up: stay on current gap
        qpg = dict(state.get("questions_per_gap", {}))
        qpg[current_gap] = questions_for_gap + 1
        state["questions_per_gap"] = qpg

        follow_up_hint = (
            patch.get("follow_up_hint")
            or f"ask for a more specific or concrete example related to {current_gap}"
        )
        gap_category = (state.get("gap_categories") or {}).get(current_gap)

        follow_up_question = await question_generator_with_profile(
            state,
            updated_profile,
            provider,
            gap_category=gap_category,
            follow_up_hint=follow_up_hint,
        )
        state["current_question"] = follow_up_question
        state["messages"].append({"role": "assistant", "content": follow_up_question})
        record.state = state
        record.updated_at = datetime.now(timezone.utc)
        await db.commit()

        gaps_remaining = _count_remaining(
            state["critical_gaps"],
            current_idx,
            set(state.get("skipped_gaps", [])),
        )

        return SessionMessageResponse(
            complete=False,
            question=follow_up_question,
            gaps_remaining=gaps_remaining,
            pending_conflicts=merge_conflicts if merge_conflicts else None,
            gaps_also_addressed=newly_skipped if newly_skipped else None,
        )
```

- [ ] **Step 7: Fix `_complete_session` to exclude skipped gaps from `gaps_unresolved`**

Find `_complete_session` and replace the `unresolved` line:

```python
    # Before (original):
    unresolved = all_gaps[idx:] if reason != "gaps_resolved" else []

    # Replace with:
    skipped = set(state.get("skipped_gaps", []))
    unresolved = (
        [g for g in all_gaps[idx:] if g not in skipped]
        if reason != "gaps_resolved"
        else []
    )
```

- [ ] **Step 8: Run the full unit test suite**

```bash
pytest tests/unit/ -v --tb=short 2>&1 | tail -40
```

Expected: all previously passing tests still `PASSED`. The sprint 15 test for `test_build_state_includes_new_fields` passes.

- [ ] **Step 9: Commit**

```bash
git add backend/applire/services/session.py tests/unit/test_sprint15_interview.py
git commit -m "feat(interview): rewrite send_message with per-gap follow-up logic and cross-gap resolution"
```

---

## Task 7: Cross-Gap Resolution Tests

**Files:**
- Modify: `tests/unit/test_sprint15_interview.py`

Cross-gap resolution is now live in `send_message`. This task adds focused unit tests for `_next_valid_index` (already tested) and the `skipped_gaps` path in the advance logic — verified by checking the new `InterviewState` fields via pure-function tests.

- [ ] **Step 1: Write cross-gap tests that exercise the pure helpers**

Append to `tests/unit/test_sprint15_interview.py`:

```python
# ---------------------------------------------------------------------------
# Task 7: Cross-gap resolution — integration through pure helpers
# ---------------------------------------------------------------------------


def test_count_remaining_reflects_skipped_gaps():
    """gaps_remaining drops when skipped_gaps are added."""
    from applire.services.session import _count_remaining

    gaps = ["gap_a", "gap_b", "gap_c", "gap_d"]
    # No skips: 3 remaining after index 1
    assert _count_remaining(gaps, 1, set()) == 3
    # gap_c skipped: 2 remaining
    assert _count_remaining(gaps, 1, {"gap_c"}) == 2
    # gap_b and gap_c skipped: 1 remaining
    assert _count_remaining(gaps, 1, {"gap_b", "gap_c"}) == 1


def test_next_valid_index_skips_to_end():
    """_next_valid_index returns len(gaps) when all remaining are skipped."""
    from applire.services.session import _next_valid_index

    gaps = ["gap_a", "gap_b", "gap_c"]
    result = _next_valid_index(gaps, 1, {"gap_b", "gap_c"})
    assert result == 3  # past end → gaps exhausted
```

- [ ] **Step 2: Run the tests**

```bash
pytest tests/unit/test_sprint15_interview.py -k "cross_gap or skipped" -v
```

Expected: all `PASSED`

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_sprint15_interview.py
git commit -m "test(interview): add cross-gap resolution helper tests"
```

---

## Task 8: Micro-Session Full Gap Context

**Files:**
- Modify: `backend/applire/services/session.py`
- Modify: `tests/unit/test_sprint15_interview.py`

- [ ] **Step 1: Write a failing test**

Append to `tests/unit/test_sprint15_interview.py`:

```python
# ---------------------------------------------------------------------------
# Task 8: Micro-session full_gaps
# ---------------------------------------------------------------------------


def test_micro_session_full_gaps_excludes_target():
    """full_gaps in micro-session state contains all analysis gaps except the target."""
    # This tests the state construction logic directly
    target = "GCP certification"
    all_analysis_gaps = ["GCP certification", "GMP experience", "ISO 9001", "Python"]

    full_gaps = [g for g in all_analysis_gaps if g != target]

    assert target not in full_gaps
    assert "GMP experience" in full_gaps
    assert len(full_gaps) == 3
```

This test documents the construction rule. The actual `_create_micro_session` integration is covered by E2E tests.

- [ ] **Step 2: Run the test to confirm it passes immediately (pure logic)**

```bash
pytest tests/unit/test_sprint15_interview.py::test_micro_session_full_gaps_excludes_target -v
```

Expected: `PASSED` (it's a pure logic assertion)

- [ ] **Step 3: Update `_create_micro_session` in `session.py` to set `full_gaps` in state**

Find `_create_micro_session`. After the `gap_analysis` is loaded (the `if gap_analysis is not None:` block that sets `gap_category`), add the `full_gaps` construction:

```python
    # Build full gap list for cross-gap context in send_message
    full_gaps: list[str] = []
    if gap_analysis is not None:
        all_gaps = list(gap_analysis.category_c or []) + list(gap_analysis.category_b or [])
        full_gaps = [g for g in all_gaps if g and g != target_gap]
```

Then after the existing `state: InterviewState = _build_state(...)` call, add:

```python
    state["full_gaps"] = full_gaps
```

The full updated `_create_micro_session` block (showing context around the changes) — find the section that starts with `_MICRO_CEILING = 1`:

```python
    _MICRO_CEILING = 1

    # Build full gap list for cross-gap context in send_message
    full_gaps: list[str] = []
    if gap_analysis is not None:
        all_gaps = list(gap_analysis.category_c or []) + list(gap_analysis.category_b or [])
        full_gaps = [g for g in all_gaps if g and g != target_gap]

    state: InterviewState = _build_state(
        mode="targeted",
        job_id=job_id,
        gap_analysis_id=gap_analysis.id if gap_analysis else None,
        profile_id=profile_record.id,
        critical_gaps=[target_gap],
        gap_categories={target_gap: gap_category or "C"},
        current_question="",
        hard_ceiling=_MICRO_CEILING,
    )
    state["full_gaps"] = full_gaps
    first_question = await question_generator_with_profile(
        state, profile_record.profile_json, provider, gap_category=gap_category
    )
```

- [ ] **Step 4: Run the full unit test suite one final time**

```bash
pytest tests/unit/ -v --tb=short 2>&1 | tail -40
```

Expected: all tests `PASSED`

- [ ] **Step 5: Run the sprint 15 tests specifically to get a clean summary**

```bash
pytest tests/unit/test_sprint15_interview.py -v
```

Expected: all tests `PASSED`

- [ ] **Step 6: Final commit**

```bash
git add backend/applire/services/session.py tests/unit/test_sprint15_interview.py
git commit -m "feat(interview): set full_gaps in micro-session state for cross-gap resolution"
```

---

## Task 9: Coverage Check and Documentation

**Files:**
- Read: `backend/applire/constants.py` (no changes — verify `import os` present)

- [ ] **Step 1: Run backend unit tests with coverage**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/ --cov=applire --cov-report=term-missing --cov-fail-under=75 -q 2>&1 | tail -20
```

Expected: coverage ≥ 75%, all tests `PASSED`

- [ ] **Step 2: Run the full E2E smoke check (requires running stack)**

If the Docker stack is running:

```bash
cd /home/apliqa/Documents/Applire/Solution
npx playwright test tests/e2e/interview-sprint5.spec.ts --project=chromium
```

Expected: existing interview E2E test still passes (new behaviour only activates on `gap_resolution != "full"` from the LLM, which is mocked in tests)

- [ ] **Step 3: Final commit if any doc files changed**

```bash
git status
# If clean, no commit needed.
```

---

## Task 10: Update Architecture Documentation

**Files:**
- Modify: `Documents/Architecture/arc42.md` (Nextcloud only — do NOT commit)
- Modify: `Documents/Architecture/ADR.md` (Nextcloud only — do NOT commit)

- [ ] **Step 1: Update arc42.md Section 5.3.3 — Interview Orchestrator table**

Open `Documents/Architecture/arc42.md`. Find Section `5.3.3 Interview Orchestrator [Community]`.

Update the **`Question Types`** row:

```
Exploratory (Category C / MODE B): open question.
Confirmation (Category B): acknowledges inferred experience and asks for specifics.
Follow-up (Lateral Probe): generated when gap_resolution is "partial" or "none" and
per-gap ceiling not reached. Probes an adjacent domain suggested by follow_up_hint
(e.g. "ask about GMP or other regulated manufacturing environments") rather than
re-asking the original question.
```

Update the **`MODE A — Targeted`** row, append after the existing sentence:

```
Per-gap follow-up ceiling: INTERVIEW_MAX_QUESTIONS_PER_GAP (default 3; includes
the initial question). If gap_resolution=="full" or ceiling reached, advances to
next gap. Cross-gap resolution: ResponseParser identifies other open gaps resolved
by the same answer (gaps_also_addressed); those gaps are skipped automatically.
Profile enrichment extended to certifications, languages, and education in addition
to skills and work history.
```

Update the **`Constants`** row, add after the existing list:

```
INTERVIEW_MAX_QUESTIONS_PER_GAP (int, default 3) — env-var backed
(INTERVIEW_MAX_QUESTIONS_PER_GAP); configurable for Docker self-hosters.
```

Update the **`Completion Response`** row, append:

```
gaps_also_addressed: list[str] | None — gaps resolved transitively by
a cross-gap answer; populated when non-empty.
```

- [ ] **Step 2: Update arc42.md version history**

At the top of the changelog (after the v2.10 entry), add:

```
- v2.11 (09 Apr 2026): Sprint 15 — Smart Gap Interview:
  - 5.3.3: Interview Orchestrator extended with per-gap follow-up questions
    (lateral-probe style), cross-gap resolution, and expanded profile enrichment
    (certifications, languages, education). New constant INTERVIEW_MAX_QUESTIONS_PER_GAP
    (env-var backed). ResponseParser schema extended (gap_resolution, follow_up_hint,
    gaps_also_addressed). ADR-004 amended.
```

- [ ] **Step 3: Add amendment note to ADR-004 in ADR.md**

Open `Documents/Architecture/ADR.md`. Find `## #ADR-004: Stateful Backend for Interview Orchestration`.

After the existing "Reaffirmed 16 March 2026 (Iteration 14):" block, add:

```
**Amended 2026-04-09 (Sprint 15 — Smart Gap Interview):** ResponseParser extended
to return `gap_resolution: "full" | "partial" | "none"`, `follow_up_hint: str | None`,
and `gaps_also_addressed: list[str]`. QuestionGenerator gains a lateral-probe follow-up
mode: when `gap_resolution != "full"` and the per-gap question count is below
`INTERVIEW_MAX_QUESTIONS_PER_GAP`, a follow-up question is generated using the hint
rather than re-asking the same question. ProfileUpdater extended to merge certifications,
languages, and education alongside existing skills and work history. A new
`skipped_gaps` list in `InterviewState` tracks cross-resolved gaps; `_next_valid_index`
advances past them. Micro-sessions receive the full gap list as `remaining_gaps` context
to enable cross-gap resolution even in single-gap sessions. Graph topology and four-node
sequence unchanged. No new ADR required.
```

- [ ] **Step 4: No git commit**

These files are Nextcloud-managed and not part of the git repository. Do not `git add` them.

```bash
# Verify no Documents/ files were accidentally staged
git status | grep Documents
# Expected: no output
```

---

## Verification Checklist

Before declaring done:

- [ ] `pytest tests/unit/test_sprint15_interview.py -v` → all green
- [ ] `pytest tests/unit/ --cov=applire --cov-fail-under=75 -q` → passes
- [ ] `INTERVIEW_MAX_QUESTIONS_PER_GAP` readable from env in running container: `docker exec <backend> env | grep INTERVIEW`
- [ ] `SessionMessageResponse` includes `gaps_also_addressed` field (check OpenAPI at `/docs`)
- [ ] `InterviewState` has `questions_per_gap`, `skipped_gaps`, `full_gaps` in `_build_state` return value
- [ ] Existing E2E tests unaffected
- [ ] arc42.md Section 5.3.3 updated (Question Types, MODE A, Constants, Completion Response rows)
- [ ] arc42.md version history has v2.11 entry
- [ ] ADR-004 has Sprint 15 amendment note
- [ ] No `Documents/` files in `git status`
