"""Skill enrichment service — deterministic + LLM hybrid (Sprint 28).

Public API:
    enrich_skills(profile, provider) -> MasterProfileData

Pipeline:
  1. Match each technical/soft skill against WorkEntry.technologies (case-insensitive).
     Calculate non-overlapping years from matched date ranges.
     Derive proficiency from years, apply floor (never downgrade).
     Record provenance in work_entry_refs.
  2. For unmatched technical/soft skills, make a single batch LLM call with full
     work history. Apply same floor rule. Source = "llm_estimated".
  3. language/domain skills are passed through unchanged.
"""
from __future__ import annotations

import logging
from datetime import date

from applire.providers.llm.base import LLMProvider
from applire.schemas.profile import MasterProfileData, Skill

logger = logging.getLogger(__name__)

_ELIGIBLE_CATEGORIES = frozenset({"technical", "soft"})

_PROFICIENCY_RANK: dict[str, int] = {
    "basic": 0,
    "intermediate": 1,
    "advanced": 2,
    "expert": 3,
}


def _parse_partial_date(s: str) -> date:
    """Parse a partial date string to a date.

    Accepted formats: "YYYY", "YYYY-MM", "YYYY-MM-DD".
    Partial dates are expanded to the first of the month / year.
    """
    parts = s.strip().split("-")
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 and parts[1] else 1
    day = int(parts[2]) if len(parts) > 2 and parts[2] else 1
    return date(year, month, day)


def _calculate_years(ranges: list[tuple[date, date]]) -> int:
    """Return total non-overlapping experience in years (rounded integer).

    Overlapping ranges are merged before summing — a skill used at two
    concurrent jobs is not double-counted.

    Returns 0 for an empty list. Returns minimum 1 if any entry exists,
    to avoid reporting 0 years for a brief engagement.
    """
    if not ranges:
        return 0

    sorted_ranges = sorted(ranges, key=lambda r: r[0])
    sorted_ranges = [(s, e) for s, e in sorted_ranges if e > s]
    if not sorted_ranges:
        return 1  # ranges existed but all were zero-duration: treat as minimum 1
    merged: list[tuple[date, date]] = []
    cur_start, cur_end = sorted_ranges[0]

    for start, end in sorted_ranges[1:]:
        if start <= cur_end:
            cur_end = max(cur_end, end)
        else:
            merged.append((cur_start, cur_end))
            cur_start, cur_end = start, end
    merged.append((cur_start, cur_end))

    total_days = sum((end - start).days for start, end in merged)
    years = total_days / 365.25
    return max(1, round(years))


def _years_to_proficiency(years: int) -> str:
    """Map years of experience to a proficiency level.

    Thresholds:
        < 1  → basic
        1–2  → intermediate
        3–5  → advanced
        ≥ 6  → expert
    """
    if years < 1:
        return "basic"
    if years < 3:
        return "intermediate"
    if years < 6:
        return "advanced"
    return "expert"


def _apply_floor(calculated: str, existing: str) -> str:
    """Return the higher of two proficiency levels.

    The LLM-extracted proficiency is never lowered by the calculation.
    Uses rank order: basic(0) < intermediate(1) < advanced(2) < expert(3).
    """
    calc_rank = _PROFICIENCY_RANK.get(calculated, 0)
    exist_rank = _PROFICIENCY_RANK.get(existing, 1)  # default intermediate if unknown
    return calculated if calc_rank > exist_rank else existing


def _match_and_enrich(
    profile: MasterProfileData,
) -> tuple[list[Skill], list[Skill]]:
    """Phase 1: Deterministic skill-to-career-step matching.

    Returns:
        enriched:  Matched technical/soft skills (years calculated) +
                   language/domain skills (passed through unchanged).
        unmatched: Technical/soft skills with no match in any WorkEntry.technologies.
    """
    today = date.today()
    enriched: list[Skill] = []
    unmatched: list[Skill] = []

    for skill in profile.skills:
        # language / domain skills: time-based experience is not meaningful — pass through
        if skill.category not in _ELIGIBLE_CATEGORIES:
            enriched.append(skill)
            continue

        matched_ranges: list[tuple[date, date]] = []
        matched_companies: list[str] = []

        for entry in profile.work_experience:
            technologies_lower = [t.lower() for t in (entry.technologies or [])]
            if skill.name.lower() not in technologies_lower:
                continue

            # Parse start date — skip entry if absent or unparseable
            if not entry.start_date:
                continue
            try:
                start = _parse_partial_date(entry.start_date)
            except (ValueError, AttributeError):
                continue

            # Parse end date — null means current role → today
            if entry.end_date is None:
                end = today
            else:
                try:
                    end = _parse_partial_date(entry.end_date)
                except (ValueError, AttributeError):
                    end = today

            matched_ranges.append((start, end))
            if entry.company and entry.company not in matched_companies:
                matched_companies.append(entry.company)

        if matched_ranges:
            years = _calculate_years(matched_ranges)
            calculated_prof = _years_to_proficiency(years)
            final_prof = _apply_floor(calculated_prof, skill.proficiency)
            enriched.append(skill.model_copy(update={
                "years_experience": years,
                "proficiency": final_prof,
                "work_entry_refs": matched_companies,
                "source": "deterministic",
            }))
        else:
            unmatched.append(skill)

    return enriched, unmatched
