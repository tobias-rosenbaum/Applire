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
    month = int(parts[1]) if len(parts) > 1 else 1
    day = int(parts[2]) if len(parts) > 2 else 1
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
