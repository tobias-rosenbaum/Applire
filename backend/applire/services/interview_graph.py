"""
Interview state machine — four nodes (ADR 004, Iteration 14).

Node flow:
    GapDetector → QuestionGenerator → [REST break] → ResponseParser → ProfileUpdater
                       ↑_______________________________________________|
                       (loop until all gaps addressed, done-signal, or hard ceiling)

MODE A (Targeted Gap-Fill):
    GapDetector consumes a GapAnalysis — returns C-first, then B gaps.
    QuestionGenerator produces gap-targeted questions.

MODE B (Guided Build):
    GapDetector produces a section build-plan from _VALID_SECTIONS weighted by JD relevance.
    QuestionGenerator produces section-building questions.

State is persisted as JSONB in interview_sessions.state between HTTP calls.
"""

import hashlib

from applire.models.gap import GapAnalysis
from applire.models.job import JobAnalysis
from applire.prompts.interview import (
    GUIDED_QUESTION_SYSTEM_PROMPT,
    QUESTION_SYSTEM_PROMPT,
    RESPONSE_PARSER_SYSTEM_PROMPT,
    build_guided_question_prompt,
    build_question_prompt,
    build_response_parser_prompt,
)
from applire.providers.llm.base import LLMProvider
from applire.schemas.session import ConflictSummary, InterviewState

# Sections included in a MODE B guided build, in default priority order.
# JD-relevance weighting is applied in gap_detector_mode_b() at session creation.
_MODE_B_CORE_SECTIONS = [
    "work_experience",
    "skills",
    "education",
    "personal_info",
    "languages",
    "certifications",
    "professional_summary",
]

# Sections added to MODE B only when the JD signals relevance
_MODE_B_EXTENDED_SECTIONS = ["publications", "volunteer_activities"]


# ---------------------------------------------------------------------------
# Node: GapDetector — MODE A
# ---------------------------------------------------------------------------


def gap_detector(gap_analysis: GapAnalysis) -> tuple[list[str], dict[str, str]]:
    """Return (ordered_gaps, gap_categories) from a GapAnalysis.

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
# Node: GapDetector — MODE B
# ---------------------------------------------------------------------------


def gap_detector_mode_b(job_analysis: JobAnalysis) -> list[str]:
    """Return ordered section names for a MODE B guided build.

    Starts from _MODE_B_CORE_SECTIONS and promotes sections that are
    directly signalled by the JD (certifications, publications, languages).

    Returns:
        sections: ordered list of _VALID_SECTIONS keys to ask about
    """
    sections = list(_MODE_B_CORE_SECTIONS)

    jd_text = " ".join(
        (job_analysis.required_skills or [])
        + (job_analysis.nice_to_have_skills or [])
        + [job_analysis.role_title or ""]
    ).lower()

    # Promote certifications if JD mentions cert keywords
    cert_signals = {"certif", "zertif", "pmp", "aws certified", "azure certified", "cissp"}
    if any(sig in jd_text for sig in cert_signals) and "certifications" not in sections[:3]:
        sections.remove("certifications")
        sections.insert(2, "certifications")

    # Add extended sections if JD signals academic/research context
    research_signals = {"phd", "doktor", "publikation", "publication", "research", "forschung"}
    if any(sig in jd_text for sig in research_signals):
        sections.append("publications")

    # Add volunteer only for nonprofit/social-impact roles
    social_signals = {"ngo", "nonprofit", "gemeinnützig", "ehrenamt", "volunteer"}
    if any(sig in jd_text for sig in social_signals):
        sections.append("volunteer_activities")

    return sections


# ---------------------------------------------------------------------------
# Node: QuestionGenerator
# ---------------------------------------------------------------------------


async def question_generator_with_profile(
    state: InterviewState,
    profile: dict,
    provider: LLMProvider,
    gap_category: str | None = None,
    job_context: dict | None = None,
) -> str:
    """Generate the next question based on mode.

    MODE A: gap-targeted question (exploratory C or confirmation B)
    MODE B: section-building question

    gap_category: "B" | "C" | None (MODE A only)
    job_context: {"role_title": str, "seniority_level": str} (MODE B, optional)
    """
    mode = state.get("mode", "targeted")

    if mode == "guided":
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


async def question_generator(
    state: InterviewState,
    provider: LLMProvider,
) -> str:
    """Generate a targeted question for the current gap (no profile context).

    Kept for backwards compatibility — prefer question_generator_with_profile.
    """
    gap = state["critical_gaps"][state["current_gap_index"]]
    question = await provider.acomplete(
        build_question_prompt(gap, {}, state["messages"]),
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
        "follow_up_hint": data.get("follow_up_hint") if isinstance(data.get("follow_up_hint"), str) else None,
        "gaps_also_addressed": data.get("gaps_also_addressed", []),
        "gap_addressed": gap_resolution != "none",  # backward compat
    }


# ---------------------------------------------------------------------------
# Node: ProfileUpdater
# ---------------------------------------------------------------------------


def profile_updater(
    current_profile: dict, patch: dict
) -> tuple[dict, list[ConflictSummary]]:
    """Merge extracted data into the MasterProfile using intelligent merge rules.

    Returns (updated_profile, conflicts) — conflicts are surfaced when a
    work-experience entry for the same (company, role) carries contradicting dates.

    Rules (ADR 013):
    - skills: union — add new skills, never remove existing ones
    - work_experience: append entries whose (company, role) pair is not already present;
      date contradictions on matching entries are reported as ConflictSummary records
    - No field is ever overwritten if it already has a non-empty value
    """
    profile = dict(current_profile)
    conflicts: list[ConflictSummary] = []

    # --- Skills: union merge ---
    existing_skills = {_skill_name(s).lower() for s in profile.get("skills", [])}
    new_skills = [
        s for s in patch.get("skills_to_add", []) if _skill_name(s).lower() not in existing_skills
    ]
    if new_skills:
        profile["skills"] = list(profile.get("skills", [])) + new_skills

    # --- Work experience: append-only, detect date conflicts on matching entries ---
    existing_work = profile.get("work_experience", [])
    existing_by_key: dict[tuple[str, str], dict] = {
        (_norm(e.get("company")), _norm(e.get("role"))): e for e in existing_work
    }
    additions = []
    for entry in patch.get("work_history_to_add", []):
        key = (_norm(entry.get("company")), _norm(entry.get("role")))
        if not key[1]:
            continue
        if key in existing_by_key:
            existing_entry = existing_by_key[key]
            # Detect contradicting start_date
            old_start = existing_entry.get("start_date") or ""
            new_start = entry.get("start_date") or ""
            if old_start and new_start and (old_start + "-01")[:7] != (new_start + "-01")[:7]:
                field = f"{key[0]} / {key[1]} start_date"
                conflict_id = hashlib.md5(f"{field}:{old_start}".encode()).hexdigest()[:12]
                conflicts.append(
                    ConflictSummary(
                        conflict_id=conflict_id,
                        field=field,
                        old_value=old_start,
                        new_value=new_start,
                    )
                )
        else:
            additions.append(entry)
            existing_by_key[key] = entry

    if additions:
        profile["work_experience"] = list(existing_work) + additions

    return profile, conflicts


def _skill_name(s: str | dict) -> str:
    if isinstance(s, dict):
        return s.get("name", "")
    return str(s)


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()
