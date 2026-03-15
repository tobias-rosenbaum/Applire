"""
Interview state machine — four nodes matching the LangGraph architecture (ADR / Iteration 4).

Node flow:
    GapDetector → QuestionGenerator → [REST break] → ResponseParser → ProfileUpdater
                       ↑_______________________________________________|
                       (loop until all critical gaps addressed or session ends)

State is persisted as JSONB in interview_sessions.state between HTTP calls.
"""

from apliqa.models.gap import GapAnalysis
from apliqa.prompts.interview import (
    QUESTION_SYSTEM_PROMPT,
    RESPONSE_PARSER_SYSTEM_PROMPT,
    build_question_prompt,
    build_response_parser_prompt,
)
from apliqa.providers.base import LLMProvider
from apliqa.schemas.session import InterviewState


# ---------------------------------------------------------------------------
# Node: GapDetector
# ---------------------------------------------------------------------------


def gap_detector(gap_analysis: GapAnalysis) -> tuple[list[str], dict[str, str]]:
    """
    Return (ordered_gaps, gap_categories) from a GapAnalysis.

    Priority order:
      1. Category C (UNKNOWN) — highest value; interview must ask about these
      2. Category B (LIKELY BUT UNSTATED) — confirm inferred experience
      Category A items are excluded — already matched, no interview action needed.

    Falls back to critical_gaps (legacy records without A/B/C columns).

    Returns:
        ordered_gaps: list[str] ordered C-first then B
        gap_categories: dict mapping each gap string to "B" or "C"
    """
    targets: list[str] = []
    categories: dict[str, str] = {}

    if gap_analysis.category_c or gap_analysis.category_b:
        for gap in (gap_analysis.category_c or []):
            if gap:
                targets.append(gap)
                categories[gap] = "C"
        for gap in (gap_analysis.category_b or []):
            if gap:
                targets.append(gap)
                categories[gap] = "B"
    else:
        # Legacy fallback: records created before A/B/C columns existed
        for gap in (gap_analysis.critical_gaps or []):
            if gap:
                targets.append(gap)
                categories[gap] = "C"

    return targets, categories


# ---------------------------------------------------------------------------
# Node: QuestionGenerator
# ---------------------------------------------------------------------------


async def question_generator(
    state: InterviewState,
    provider: LLMProvider,
) -> str:
    """Generate a targeted question for the current gap."""
    gap = state["critical_gaps"][state["current_gap_index"]]
    # profile is not stored in state — caller passes it in
    # we embed a minimal profile summary via the prompt builder
    question = await provider.acomplete(
        build_question_prompt(gap, {}, state["messages"]),
        system=QUESTION_SYSTEM_PROMPT,
        temperature=0.4,
        max_tokens=256,
    )
    return question.strip()


async def question_generator_with_profile(
    state: InterviewState,
    profile: dict,
    provider: LLMProvider,
    gap_category: str | None = None,
) -> str:
    """Generate a targeted question, including the full profile for context.

    gap_category: "B" (confirmation) | "C" (exploratory) | None (legacy fallback to C behaviour)
    """
    gap = state["critical_gaps"][state["current_gap_index"]]
    question = await provider.acomplete(
        build_question_prompt(gap, profile, state["messages"], gap_category=gap_category),
        system=QUESTION_SYSTEM_PROMPT,
        temperature=0.4,
        max_tokens=256,
    )
    return question.strip()


# ---------------------------------------------------------------------------
# Node: ResponseParser
# ---------------------------------------------------------------------------


async def response_parser(
    gap: str,
    question: str,
    answer: str,
    provider: LLMProvider,
) -> dict:
    """Extract structured profile data from the user's free-text answer.

    Returns a dict with keys:
        skills_to_add: list[str]
        work_history_to_add: list[dict]
        gap_addressed: bool
    """
    data = await provider.aparse_json(
        build_response_parser_prompt(gap, question, answer),
        system=RESPONSE_PARSER_SYSTEM_PROMPT,
        temperature=0.1,
    )
    return {
        "skills_to_add": data.get("skills_to_add", []),
        "work_history_to_add": data.get("work_history_to_add", []),
        "gap_addressed": bool(data.get("gap_addressed", False)),
    }


# ---------------------------------------------------------------------------
# Node: ProfileUpdater  (intelligent merge — 4.6)
# ---------------------------------------------------------------------------


def profile_updater(current_profile: dict, patch: dict) -> dict:
    """Merge extracted data into the MasterProfile using intelligent merge rules.

    Rules (4.6):
    - skills: union — add new skills, never remove existing ones
    - work_experience: append entries whose (company, role) pair is not already present
    - No field is ever overwritten if it already has a non-empty value
    - Conflicts (same company, different dates) are appended as new entries
      so the user can review them manually
    """
    profile = dict(current_profile)

    # --- Skills: union merge ---
    # Skills in profile_json may be Skill dicts (iter 11+) or plain strings.
    existing_skills = {_skill_name(s).lower() for s in profile.get("skills", [])}
    new_skills = [
        s for s in patch.get("skills_to_add", []) if s.lower() not in existing_skills
    ]
    if new_skills:
        profile["skills"] = list(profile.get("skills", [])) + new_skills

    # --- Work experience: append-only, deduplicate by (company, role) ---
    existing_work = profile.get("work_experience", [])
    existing_keys = {
        (_norm(e.get("company")), _norm(e.get("role"))) for e in existing_work
    }
    additions = []
    for entry in patch.get("work_history_to_add", []):
        key = (_norm(entry.get("company")), _norm(entry.get("role")))
        if key not in existing_keys and (key[0] or key[1]):
            additions.append(entry)
            existing_keys.add(key)
    if additions:
        profile["work_experience"] = list(existing_work) + additions

    return profile


def _skill_name(s: str | dict) -> str:
    """Extract a comparable skill name from either a plain string or a Skill dict."""
    if isinstance(s, dict):
        return s.get("name", "")
    return str(s)


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()
