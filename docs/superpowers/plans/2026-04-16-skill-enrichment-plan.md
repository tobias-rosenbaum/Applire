# Skill Enrichment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic skill-to-career-step matching, date-range-based years_experience calculation, LLM estimation for unmatched skills, provenance tracking via `work_entry_refs`, and wire up the missing `review_and_refine()` layer in `upload_cv()`.

**Architecture:** A new `skill_enrichment.py` service runs as post-processing after profile extraction in all three entry points (`_import_from_text`, `upload_cv`, `patch_profile_section`). Phase 1 deterministically calculates years from `WorkEntry.technologies` date ranges; Phase 2 batches unmatched skills to a single LLM call. A new `review_cv_extraction.py` prompt file mirrors the existing LinkedIn reviewer but uses `work_experience` field names.

**Tech Stack:** Python 3.12, Pydantic v2, FastAPI, pytest + pytest-asyncio, `unittest.mock.AsyncMock`

---

## File Map

| File | Action |
|---|---|
| `backend/applire/schemas/profile.py` | Add `work_entry_refs: list[str]` to `Skill`; add null-coercion validator |
| `backend/applire/services/skill_enrichment.py` | Create — `_parse_partial_date`, `_calculate_years`, `_years_to_proficiency`, `_apply_floor`, `_match_and_enrich`, `enrich_skills` |
| `backend/applire/prompts/skill_estimation.py` | Create — `SKILL_ESTIMATION_SYSTEM_PROMPT`, `build_skill_estimation_prompt` |
| `backend/applire/prompts/review_cv_extraction.py` | Create — `CV_EXTRACTION_REVIEW_SYSTEM_PROMPT`, `build_cv_extraction_review_prompt`, `build_cv_extraction_retry_prompt` |
| `backend/applire/services/profile/__init__.py` | Add `enrich_skills` to `_import_from_text`; add `review_and_refine` + `enrich_skills` to `upload_cv`; add optional `provider` + enrichment to `patch_profile_section` |
| `backend/applire/routers/profile.py` | Add `provider: LLMProvider = Depends(_get_provider)` to `patch_section` endpoint |
| `tests/unit/test_skill_enrichment.py` | Create — full unit test suite |
| `tests/unit/test_cv_upload.py` | Update — patch new `review_and_refine` and `enrich_skills` calls in existing tests |

---

## Task 1: Add `work_entry_refs` to the `Skill` schema

**Files:**
- Modify: `backend/applire/schemas/profile.py:122-155`
- Test: `tests/unit/test_skill_enrichment.py` (new file)

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_skill_enrichment.py`:

```python
"""Unit tests for skill enrichment — schema, date calc, matching, LLM estimation."""
import pytest
from datetime import date


# ---------------------------------------------------------------------------
# Task 1: Skill schema — work_entry_refs field
# ---------------------------------------------------------------------------

class TestSkillWorkEntryRefs:
    def test_work_entry_refs_defaults_to_empty_list(self):
        from applire.schemas.profile import Skill
        skill = Skill(name="Python", category="technical", proficiency="advanced")
        assert skill.work_entry_refs == []

    def test_work_entry_refs_coerces_null_to_empty_list(self):
        from applire.schemas.profile import Skill
        skill = Skill(
            name="Python",
            category="technical",
            proficiency="advanced",
            work_entry_refs=None,
        )
        assert skill.work_entry_refs == []

    def test_work_entry_refs_accepts_list_of_strings(self):
        from applire.schemas.profile import Skill
        skill = Skill(
            name="Python",
            category="technical",
            proficiency="advanced",
            work_entry_refs=["Siemens AG", "BMW Group"],
        )
        assert skill.work_entry_refs == ["Siemens AG", "BMW Group"]

    def test_existing_jsonb_without_field_loads_cleanly(self):
        """Simulate a legacy JSONB record that has no work_entry_refs key."""
        from applire.schemas.profile import Skill
        skill = Skill.model_validate(
            {"name": "Django", "category": "technical", "proficiency": "intermediate"}
        )
        assert skill.work_entry_refs == []
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_skill_enrichment.py::TestSkillWorkEntryRefs -v
```

Expected: `FAILED` — `Skill` has no `work_entry_refs` field yet.

- [ ] **Step 3: Add the field and validator to `Skill`**

In `backend/applire/schemas/profile.py`, the `Skill` class currently ends at line 155. Add `work_entry_refs` field and a null-coercing validator:

```python
class Skill(BaseModel):
    name: str
    category: Literal["technical", "soft", "language", "domain"] = "technical"
    proficiency: Literal["basic", "intermediate", "advanced", "expert"] = "intermediate"
    years_experience: int | None = None
    source: str | None = None  # which role/interview surfaced this
    last_used: date | None = None
    work_entry_refs: list[str] = Field(default_factory=list)

    @field_validator("work_entry_refs", mode="before")
    @classmethod
    def coerce_work_entry_refs(cls, v: object) -> list:
        return v if isinstance(v, list) else []

    @field_validator("category", mode="before")
    # ... (existing validators unchanged)
```

The full updated `Skill` class (replace the existing one at lines 122-154):

```python
class Skill(BaseModel):
    name: str
    category: Literal["technical", "soft", "language", "domain"] = "technical"
    proficiency: Literal["basic", "intermediate", "advanced", "expert"] = "intermediate"
    years_experience: int | None = None
    source: str | None = None  # which role/interview surfaced this
    last_used: date | None = None
    work_entry_refs: list[str] = Field(default_factory=list)

    @field_validator("work_entry_refs", mode="before")
    @classmethod
    def coerce_work_entry_refs(cls, v: object) -> list:
        return v if isinstance(v, list) else []

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, v: object) -> object:
        if isinstance(v, str):
            lowered = v.lower()
            if lowered in {"technical", "soft", "language", "domain"}:
                return lowered
        return v

    @field_validator("proficiency", mode="before")
    @classmethod
    def normalize_proficiency(cls, v: object) -> object:
        if v is None:
            return "intermediate"
        if isinstance(v, str):
            normalized = _PROFICIENCY_ALIASES.get(v.lower())
            if normalized:
                return normalized
            _valid = {"basic", "intermediate", "advanced", "expert"}
            if v.lower() not in _valid:
                return "intermediate"
            return v.lower()
        return v
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_skill_enrichment.py::TestSkillWorkEntryRefs -v
```

Expected: 4 tests PASSED.

- [ ] **Step 5: Run the full unit suite to check for regressions**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/ -v -x
```

Expected: all existing tests PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/applire/schemas/profile.py tests/unit/test_skill_enrichment.py
git commit -m "feat: add work_entry_refs provenance field to Skill schema"
```

---

## Task 2: Date parsing and range calculation helpers

**Files:**
- Create: `backend/applire/services/skill_enrichment.py`
- Test: `tests/unit/test_skill_enrichment.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_skill_enrichment.py`:

```python
# ---------------------------------------------------------------------------
# Task 2: Date parsing and range calculation
# ---------------------------------------------------------------------------

class TestParsPartialDate:
    def test_year_only(self):
        from applire.services.skill_enrichment import _parse_partial_date
        assert _parse_partial_date("2020") == date(2020, 1, 1)

    def test_year_month(self):
        from applire.services.skill_enrichment import _parse_partial_date
        assert _parse_partial_date("2020-06") == date(2020, 6, 1)

    def test_full_date(self):
        from applire.services.skill_enrichment import _parse_partial_date
        assert _parse_partial_date("2020-06-15") == date(2020, 6, 15)


class TestCalculateYears:
    def test_empty_list_returns_zero(self):
        from applire.services.skill_enrichment import _calculate_years
        assert _calculate_years([]) == 0

    def test_single_entry_one_year(self):
        from applire.services.skill_enrichment import _calculate_years
        result = _calculate_years([(date(2020, 1, 1), date(2021, 1, 1))])
        assert result == 1

    def test_minimum_one_for_short_tenure(self):
        from applire.services.skill_enrichment import _calculate_years
        # 3 months — rounds to 0 but minimum is 1
        result = _calculate_years([(date(2020, 1, 1), date(2020, 4, 1))])
        assert result == 1

    def test_non_overlapping_ranges_sum(self):
        from applire.services.skill_enrichment import _calculate_years
        result = _calculate_years([
            (date(2018, 1, 1), date(2019, 1, 1)),  # 1 year
            (date(2020, 1, 1), date(2022, 1, 1)),  # 2 years
        ])
        assert result == 3

    def test_overlapping_ranges_not_double_counted(self):
        from applire.services.skill_enrichment import _calculate_years
        # Two concurrent roles, overlapping 2019-2020
        result = _calculate_years([
            (date(2018, 1, 1), date(2020, 1, 1)),  # 2 years
            (date(2019, 1, 1), date(2021, 1, 1)),  # overlaps — merged to 2018–2021 = 3 yrs
        ])
        assert result == 3

    def test_fully_contained_range_not_double_counted(self):
        from applire.services.skill_enrichment import _calculate_years
        result = _calculate_years([
            (date(2018, 1, 1), date(2022, 1, 1)),  # 4 years
            (date(2019, 1, 1), date(2020, 1, 1)),  # fully inside — no extra time added
        ])
        assert result == 4

    def test_adjacent_ranges_are_summed(self):
        from applire.services.skill_enrichment import _calculate_years
        result = _calculate_years([
            (date(2018, 1, 1), date(2020, 1, 1)),
            (date(2020, 1, 1), date(2022, 1, 1)),
        ])
        assert result == 4

    def test_six_years_rounds_correctly(self):
        from applire.services.skill_enrichment import _calculate_years
        result = _calculate_years([(date(2016, 1, 1), date(2022, 1, 1))])
        assert result == 6
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_skill_enrichment.py::TestParsPartialDate tests/unit/test_skill_enrichment.py::TestCalculateYears -v
```

Expected: `ModuleNotFoundError` — `skill_enrichment` doesn't exist yet.

- [ ] **Step 3: Create `skill_enrichment.py` with the helpers**

Create `backend/applire/services/skill_enrichment.py`:

```python
"""Skill enrichment service — deterministic + LLM hybrid (ADR-XXX, Sprint 28).

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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_skill_enrichment.py::TestParsPartialDate tests/unit/test_skill_enrichment.py::TestCalculateYears -v
```

Expected: all PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/applire/services/skill_enrichment.py tests/unit/test_skill_enrichment.py
git commit -m "feat: add date parsing and range calculation helpers to skill_enrichment"
```

---

## Task 3: Proficiency thresholds and floor rule

**Files:**
- Modify: `backend/applire/services/skill_enrichment.py`
- Test: `tests/unit/test_skill_enrichment.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_skill_enrichment.py`:

```python
# ---------------------------------------------------------------------------
# Task 3: Proficiency thresholds and floor rule
# ---------------------------------------------------------------------------

class TestYearsToProficiency:
    def test_zero_years_is_basic(self):
        from applire.services.skill_enrichment import _years_to_proficiency
        assert _years_to_proficiency(0) == "basic"

    def test_one_year_is_intermediate(self):
        from applire.services.skill_enrichment import _years_to_proficiency
        assert _years_to_proficiency(1) == "intermediate"

    def test_two_years_is_intermediate(self):
        from applire.services.skill_enrichment import _years_to_proficiency
        assert _years_to_proficiency(2) == "intermediate"

    def test_three_years_is_advanced(self):
        from applire.services.skill_enrichment import _years_to_proficiency
        assert _years_to_proficiency(3) == "advanced"

    def test_five_years_is_advanced(self):
        from applire.services.skill_enrichment import _years_to_proficiency
        assert _years_to_proficiency(5) == "advanced"

    def test_six_years_is_expert(self):
        from applire.services.skill_enrichment import _years_to_proficiency
        assert _years_to_proficiency(6) == "expert"

    def test_ten_years_is_expert(self):
        from applire.services.skill_enrichment import _years_to_proficiency
        assert _years_to_proficiency(10) == "expert"


class TestApplyFloor:
    def test_calculated_higher_than_existing(self):
        from applire.services.skill_enrichment import _apply_floor
        # calculated=advanced (rank 2) > existing=basic (rank 0) → use advanced
        assert _apply_floor("advanced", "basic") == "advanced"

    def test_existing_higher_than_calculated(self):
        from applire.services.skill_enrichment import _apply_floor
        # calculated=basic (rank 0) < existing=expert (rank 3) → keep expert
        assert _apply_floor("basic", "expert") == "expert"

    def test_equal_levels_returns_either(self):
        from applire.services.skill_enrichment import _apply_floor
        assert _apply_floor("intermediate", "intermediate") == "intermediate"

    def test_calculated_expert_upgrades_intermediate(self):
        from applire.services.skill_enrichment import _apply_floor
        assert _apply_floor("expert", "intermediate") == "expert"

    def test_never_downgrades_expert_to_advanced(self):
        from applire.services.skill_enrichment import _apply_floor
        assert _apply_floor("advanced", "expert") == "expert"
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_skill_enrichment.py::TestYearsToProficiency tests/unit/test_skill_enrichment.py::TestApplyFloor -v
```

Expected: `ImportError` — functions not defined yet.

- [ ] **Step 3: Add helpers to `skill_enrichment.py`**

Append to `backend/applire/services/skill_enrichment.py` (after `_calculate_years`):

```python
def _years_to_proficiency(years: int) -> str:
    """Map years of experience to a proficiency level.

    Thresholds (spec: skill-enrichment-design.md):
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_skill_enrichment.py::TestYearsToProficiency tests/unit/test_skill_enrichment.py::TestApplyFloor -v
```

Expected: all PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/applire/services/skill_enrichment.py tests/unit/test_skill_enrichment.py
git commit -m "feat: add proficiency threshold mapping and floor rule to skill_enrichment"
```

---

## Task 4: Deterministic match phase

**Files:**
- Modify: `backend/applire/services/skill_enrichment.py`
- Test: `tests/unit/test_skill_enrichment.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_skill_enrichment.py`:

```python
# ---------------------------------------------------------------------------
# Task 4: Deterministic match phase
# ---------------------------------------------------------------------------

class TestMatchAndEnrich:
    def _make_profile(self, skills, work_experience):
        from applire.schemas.profile import MasterProfileData, Skill, WorkEntry
        return MasterProfileData(
            skills=[Skill(**s) for s in skills],
            work_experience=[WorkEntry(**w) for w in work_experience],
        )

    def test_case_insensitive_match(self):
        from applire.services.skill_enrichment import _match_and_enrich
        profile = self._make_profile(
            skills=[{"name": "python", "category": "technical", "proficiency": "intermediate"}],
            work_experience=[{
                "company": "Siemens AG",
                "role": "Engineer",
                "start_date": "2020-01",
                "end_date": "2021-01",
                "technologies": ["Python"],
            }],
        )
        enriched, unmatched = _match_and_enrich(profile)
        assert len(enriched) == 1
        assert len(unmatched) == 0
        skill = enriched[0]
        assert skill.work_entry_refs == ["Siemens AG"]
        assert skill.source == "deterministic"
        assert skill.years_experience == 1

    def test_no_match_goes_to_unmatched(self):
        from applire.services.skill_enrichment import _match_and_enrich
        profile = self._make_profile(
            skills=[{"name": "Kubernetes", "category": "technical", "proficiency": "basic"}],
            work_experience=[{
                "company": "Siemens AG",
                "role": "Engineer",
                "start_date": "2020-01",
                "end_date": "2021-01",
                "technologies": ["Python"],
            }],
        )
        enriched, unmatched = _match_and_enrich(profile)
        assert len(enriched) == 0
        assert len(unmatched) == 1
        assert unmatched[0].name == "Kubernetes"

    def test_multiple_matching_entries_combined(self):
        from applire.services.skill_enrichment import _match_and_enrich
        profile = self._make_profile(
            skills=[{"name": "Python", "category": "technical", "proficiency": "intermediate"}],
            work_experience=[
                {
                    "company": "Siemens AG",
                    "role": "Junior Engineer",
                    "start_date": "2018-01",
                    "end_date": "2020-01",
                    "technologies": ["Python"],
                },
                {
                    "company": "BMW Group",
                    "role": "Senior Engineer",
                    "start_date": "2021-01",
                    "end_date": "2024-01",
                    "technologies": ["Python", "Django"],
                },
            ],
        )
        enriched, unmatched = _match_and_enrich(profile)
        assert len(enriched) == 1
        skill = enriched[0]
        assert set(skill.work_entry_refs) == {"Siemens AG", "BMW Group"}
        assert skill.years_experience == 5  # 2 + 3 non-overlapping
        assert skill.proficiency == "advanced"  # 5 years → advanced

    def test_floor_rule_preserves_higher_existing_proficiency(self):
        from applire.services.skill_enrichment import _match_and_enrich
        profile = self._make_profile(
            skills=[{"name": "Python", "category": "technical", "proficiency": "expert"}],
            work_experience=[{
                "company": "Startup",
                "role": "Dev",
                "start_date": "2023-01",
                "end_date": "2024-01",
                "technologies": ["Python"],
            }],
        )
        enriched, unmatched = _match_and_enrich(profile)
        skill = enriched[0]
        assert skill.years_experience == 1
        # Calculated would be intermediate (1 yr) but existing is expert — floor keeps expert
        assert skill.proficiency == "expert"

    def test_null_end_date_treated_as_current(self):
        from applire.services.skill_enrichment import _match_and_enrich
        from datetime import date
        profile = self._make_profile(
            skills=[{"name": "Python", "category": "technical", "proficiency": "basic"}],
            work_experience=[{
                "company": "Current Corp",
                "role": "Dev",
                "start_date": "2020-01",
                "end_date": None,  # current role
                "technologies": ["Python"],
            }],
        )
        enriched, unmatched = _match_and_enrich(profile)
        skill = enriched[0]
        # years since 2020 — should be >= 5 at time of writing (2026-04-16)
        assert skill.years_experience >= 5
        assert skill.source == "deterministic"

    def test_language_skills_passed_through_unchanged(self):
        from applire.services.skill_enrichment import _match_and_enrich
        profile = self._make_profile(
            skills=[{"name": "German", "category": "language", "proficiency": "expert"}],
            work_experience=[{
                "company": "Siemens AG",
                "role": "Engineer",
                "start_date": "2020-01",
                "end_date": "2021-01",
                "technologies": ["German"],  # even if listed, language skills are skipped
            }],
        )
        enriched, unmatched = _match_and_enrich(profile)
        # Language skills go to enriched (passthrough) with NO modification
        assert len(enriched) == 1
        assert len(unmatched) == 0
        skill = enriched[0]
        assert skill.source is None  # unchanged — no source tag added
        assert skill.work_entry_refs == []

    def test_domain_skills_passed_through_unchanged(self):
        from applire.services.skill_enrichment import _match_and_enrich
        profile = self._make_profile(
            skills=[{"name": "Healthcare", "category": "domain", "proficiency": "advanced"}],
            work_experience=[],
        )
        enriched, unmatched = _match_and_enrich(profile)
        assert len(enriched) == 1
        assert enriched[0].name == "Healthcare"
        assert enriched[0].work_entry_refs == []

    def test_entry_with_null_start_date_skipped(self):
        from applire.services.skill_enrichment import _match_and_enrich
        profile = self._make_profile(
            skills=[{"name": "Python", "category": "technical", "proficiency": "intermediate"}],
            work_experience=[{
                "company": "Siemens AG",
                "role": "Engineer",
                "start_date": None,  # can't calculate a range
                "end_date": "2021-01",
                "technologies": ["Python"],
            }],
        )
        # Entry has no start_date → can't form a range → skill goes to unmatched
        enriched, unmatched = _match_and_enrich(profile)
        assert len(unmatched) == 1
        assert unmatched[0].name == "Python"
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_skill_enrichment.py::TestMatchAndEnrich -v
```

Expected: `ImportError` — `_match_and_enrich` not defined yet.

- [ ] **Step 3: Add `_match_and_enrich` to `skill_enrichment.py`**

Append to `backend/applire/services/skill_enrichment.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_skill_enrichment.py::TestMatchAndEnrich -v
```

Expected: all PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/applire/services/skill_enrichment.py tests/unit/test_skill_enrichment.py
git commit -m "feat: add deterministic skill-to-career-step matching phase"
```

---

## Task 5: Skill estimation prompt

**Files:**
- Create: `backend/applire/prompts/skill_estimation.py`

- [ ] **Step 1: Create the prompt file**

Create `backend/applire/prompts/skill_estimation.py`:

```python
# Prompt version: v1
# Used by: services/skill_enrichment.py → enrich_skills() → LLMProvider.aparse_json
#
# Single batch call: estimates years_experience for skills not found in any
# WorkEntry.technologies list. Receives full work history for context.

import json

SKILL_ESTIMATION_SYSTEM_PROMPT = """\
You are a career analyst. Given a candidate's complete work history and a list of skill names,
estimate how many years of experience the candidate has with each skill based ONLY on the
provided work history.

Rules:
- Base all estimates exclusively on the provided work history — do not fabricate or infer beyond what is stated.
- If a skill is mentioned implicitly by a role's responsibilities or industry context but no specific
  duration can be determined from the dates, use null.
- If there is genuinely no basis for estimating a skill's duration, use null.
- Return integer years only — no fractions, no ranges.
- Do not include skills not present in the input list.

Respond ONLY with a valid JSON object — no markdown, no explanations:
{"SkillName": integer_or_null, ...}"""


def build_skill_estimation_prompt(
    work_experience: list[dict],
    skill_names: list[str],
) -> str:
    """Build the user message for the skill estimation LLM call.

    Args:
        work_experience: List of WorkEntry dicts (serialised via model_dump).
        skill_names:     Skills to estimate — only names, no other metadata.
    """
    work_history_json = json.dumps(work_experience, ensure_ascii=False, indent=2)
    skills_json = json.dumps(skill_names, ensure_ascii=False)
    return (
        f"Work history:\n{work_history_json}\n\n"
        f"Estimate years of experience for each of the following skills:\n{skills_json}\n\n"
        'Return a JSON object: {"SkillName": integer_or_null, ...}'
    )
```

- [ ] **Step 2: Verify the import works**

```bash
cd /home/apliqa/Documents/Applire/Solution
python -c "from applire.prompts.skill_estimation import SKILL_ESTIMATION_SYSTEM_PROMPT, build_skill_estimation_prompt; print('OK')"
```

Expected: prints `OK`.

- [ ] **Step 3: Commit**

```bash
git add backend/applire/prompts/skill_estimation.py
git commit -m "feat: add skill_estimation batch LLM prompt"
```

---

## Task 6: LLM estimation phase and public `enrich_skills()`

**Files:**
- Modify: `backend/applire/services/skill_enrichment.py`
- Test: `tests/unit/test_skill_enrichment.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_skill_enrichment.py`:

```python
# ---------------------------------------------------------------------------
# Task 6: LLM estimation phase and enrich_skills()
# ---------------------------------------------------------------------------

import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_enrich_skills_empty_profile_returns_unchanged():
    from applire.schemas.profile import MasterProfileData
    from applire.services.skill_enrichment import enrich_skills

    profile = MasterProfileData()
    mock_provider = AsyncMock()
    result = await enrich_skills(profile, mock_provider)

    assert result.skills == []
    mock_provider.aparse_json.assert_not_called()


@pytest.mark.asyncio
async def test_enrich_skills_unmatched_calls_llm_estimation():
    from applire.schemas.profile import MasterProfileData, Skill, WorkEntry
    from applire.services.skill_enrichment import enrich_skills

    profile = MasterProfileData(
        skills=[
            Skill(name="Agile", category="soft", proficiency="intermediate"),
        ],
        work_experience=[
            WorkEntry(
                company="Siemens AG",
                role="Scrum Master",
                start_date="2018-01",
                end_date="2021-01",
                technologies=["Jira"],  # "Agile" not in technologies
            )
        ],
    )
    mock_provider = AsyncMock()
    # LLM returns 4 years for Agile
    mock_provider.aparse_json.return_value = {"Agile": 4}

    result = await enrich_skills(profile, mock_provider)

    mock_provider.aparse_json.assert_called_once()
    skill = result.skills[0]
    assert skill.name == "Agile"
    assert skill.years_experience == 4
    assert skill.source == "llm_estimated"
    assert skill.proficiency == "advanced"  # 4 years → advanced
    assert skill.work_entry_refs == []


@pytest.mark.asyncio
async def test_enrich_skills_floor_applied_to_llm_estimate():
    from applire.schemas.profile import MasterProfileData, Skill
    from applire.services.skill_enrichment import enrich_skills

    profile = MasterProfileData(
        skills=[
            Skill(name="Leadership", category="soft", proficiency="expert"),
        ],
        work_experience=[],
    )
    mock_provider = AsyncMock()
    # LLM estimates only 1 year — should not downgrade existing expert
    mock_provider.aparse_json.return_value = {"Leadership": 1}

    result = await enrich_skills(profile, mock_provider)

    skill = result.skills[0]
    assert skill.years_experience == 1
    assert skill.proficiency == "expert"  # floor preserved


@pytest.mark.asyncio
async def test_enrich_skills_null_llm_estimate_leaves_skill_without_years():
    from applire.schemas.profile import MasterProfileData, Skill
    from applire.services.skill_enrichment import enrich_skills

    profile = MasterProfileData(
        skills=[
            Skill(name="Blockchain", category="technical", proficiency="basic"),
        ],
        work_experience=[],
    )
    mock_provider = AsyncMock()
    mock_provider.aparse_json.return_value = {"Blockchain": None}

    result = await enrich_skills(profile, mock_provider)

    skill = result.skills[0]
    assert skill.years_experience is None
    assert skill.source == "llm_estimated"
    assert skill.proficiency == "basic"  # unchanged


@pytest.mark.asyncio
async def test_enrich_skills_does_not_mutate_input():
    from applire.schemas.profile import MasterProfileData, Skill
    from applire.services.skill_enrichment import enrich_skills

    profile = MasterProfileData(
        skills=[Skill(name="Python", category="technical", proficiency="basic")],
        work_experience=[],
    )
    mock_provider = AsyncMock()
    mock_provider.aparse_json.return_value = {"Python": 3}

    result = await enrich_skills(profile, mock_provider)

    # Original profile untouched
    assert profile.skills[0].years_experience is None
    assert profile.skills[0].source is None
    # New profile enriched
    assert result.skills[0].years_experience == 3


@pytest.mark.asyncio
async def test_enrich_skills_language_skills_not_sent_to_llm():
    from applire.schemas.profile import MasterProfileData, Skill
    from applire.services.skill_enrichment import enrich_skills

    profile = MasterProfileData(
        skills=[
            Skill(name="German", category="language", proficiency="expert"),
            Skill(name="Python", category="technical", proficiency="basic"),
        ],
        work_experience=[],
    )
    mock_provider = AsyncMock()
    mock_provider.aparse_json.return_value = {"Python": 2}

    result = await enrich_skills(profile, mock_provider)

    # Only Python sent to LLM — verify the call's arguments
    call_args = mock_provider.aparse_json.call_args
    prompt_arg = call_args[0][0]  # first positional arg is the user prompt
    assert "Python" in prompt_arg
    assert "German" not in prompt_arg

    # German skill passes through unchanged
    german = next(s for s in result.skills if s.name == "German")
    assert german.source is None
    assert german.work_entry_refs == []
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_skill_enrichment.py -k "test_enrich_skills" -v
```

Expected: `ImportError` — `enrich_skills` not defined yet.

- [ ] **Step 3: Add LLM estimation phase and `enrich_skills()` to `skill_enrichment.py`**

Add the import for the prompt at the top of `skill_enrichment.py` (after the existing imports):

```python
from applire.prompts.skill_estimation import (
    SKILL_ESTIMATION_SYSTEM_PROMPT,
    build_skill_estimation_prompt,
)
```

Then append the public function to `skill_enrichment.py`:

```python
async def enrich_skills(
    profile: MasterProfileData,
    provider: LLMProvider,
) -> MasterProfileData:
    """Enrich all skills with deterministic calculation and LLM estimation.

    Phase 1 (deterministic): Match each technical/soft skill against
        WorkEntry.technologies. Calculate non-overlapping years from date ranges.
        Derive proficiency from years, apply floor. Record work_entry_refs.

    Phase 2 (LLM): For unmatched technical/soft skills, make a single batch
        LLM call with the full work history. Apply same floor rule.

    language/domain skills are passed through unchanged in both phases.

    Returns a new MasterProfileData — does not mutate the input.
    """
    if not profile.skills:
        return profile

    enriched_skills, unmatched_skills = _match_and_enrich(profile)

    if unmatched_skills:
        work_exp_dicts = [e.model_dump(mode="json") for e in profile.work_experience]
        skill_names = [s.name for s in unmatched_skills]

        try:
            estimates: dict = await provider.aparse_json(
                build_skill_estimation_prompt(work_exp_dicts, skill_names),
                system=SKILL_ESTIMATION_SYSTEM_PROMPT,
                temperature=0.1,
            )
        except Exception:
            logger.warning(
                "Skill estimation LLM call failed — unmatched skills stored without years."
            )
            estimates = {}

        for skill in unmatched_skills:
            raw = estimates.get(skill.name)
            if isinstance(raw, (int, float)) and raw > 0:
                years = max(1, int(round(raw)))
                calc_prof = _years_to_proficiency(years)
                final_prof = _apply_floor(calc_prof, skill.proficiency)
                enriched_skills.append(skill.model_copy(update={
                    "years_experience": years,
                    "proficiency": final_prof,
                    "work_entry_refs": [],
                    "source": "llm_estimated",
                }))
            else:
                enriched_skills.append(skill.model_copy(update={
                    "work_entry_refs": [],
                    "source": "llm_estimated",
                }))

    return profile.model_copy(update={"skills": enriched_skills})
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_skill_enrichment.py -v
```

Expected: all tests PASSED.

- [ ] **Step 5: Run the full unit suite**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/ -v -x
```

Expected: all PASSED.

- [ ] **Step 6: Commit**

```bash
git add backend/applire/services/skill_enrichment.py tests/unit/test_skill_enrichment.py
git commit -m "feat: add LLM estimation phase and enrich_skills public function"
```

---

## Task 7: CV extraction review and retry prompts

**Files:**
- Create: `backend/applire/prompts/review_cv_extraction.py`
- Test: `tests/unit/test_skill_enrichment.py` (add a small smoke test)

- [ ] **Step 1: Write the failing smoke tests**

Append to `tests/unit/test_skill_enrichment.py`:

```python
# ---------------------------------------------------------------------------
# Task 7: CV extraction review prompt smoke tests
# ---------------------------------------------------------------------------

class TestCVExtractionReviewPrompt:
    def test_review_system_prompt_references_work_experience(self):
        from applire.prompts.review_cv_extraction import CV_EXTRACTION_REVIEW_SYSTEM_PROMPT
        assert "work_experience" in CV_EXTRACTION_REVIEW_SYSTEM_PROMPT
        # Must NOT use the LinkedIn field names
        assert "work_history" not in CV_EXTRACTION_REVIEW_SYSTEM_PROMPT

    def test_review_prompt_includes_source_and_draft(self):
        from applire.prompts.review_cv_extraction import build_cv_extraction_review_prompt
        prompt = build_cv_extraction_review_prompt(
            "Max Mustermann, Software Engineer",
            {"work_experience": [{"company": "Siemens AG", "role": "Engineer"}]},
        )
        assert "Max Mustermann" in prompt
        assert "Siemens AG" in prompt

    def test_retry_prompt_includes_feedback_and_source(self):
        from applire.prompts.review_cv_extraction import build_cv_extraction_retry_prompt
        prompt = build_cv_extraction_retry_prompt(
            raw_cv_text="Max Mustermann CV",
            previous_draft={"work_experience": []},
            feedback="Missing work entries",
        )
        assert "Missing work entries" in prompt
        assert "Max Mustermann CV" in prompt
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_skill_enrichment.py::TestCVExtractionReviewPrompt -v
```

Expected: `ModuleNotFoundError` — `review_cv_extraction` doesn't exist yet.

- [ ] **Step 3: Create `review_cv_extraction.py`**

Create `backend/applire/prompts/review_cv_extraction.py`:

```python
# Prompt version: v1
# Used by: services/profile/__init__.py → upload_cv() → reviewer.review_and_refine
#
# Mirrors review_profile_extraction.py but uses work_experience field names
# (responsibilities, achievements, technologies) instead of work_history/bullets.
# A separate file is required because the LinkedIn reviewer references "work_history"
# in its rules — wiring it to the CV upload path would cause false rejections.

import json
from typing import Any

CV_EXTRACTION_REVIEW_SYSTEM_PROMPT = """\
You are a strict CV data quality auditor. Your task is to verify that an extracted
profile JSON faithfully represents the source CV text — nothing more, nothing less.

Check for ALL of the following:
1. DUPLICATE ENTRIES: Each employer and role must appear exactly once in work_experience.
   Flag any entry that is a duplicate or variant of another entry (same company/role,
   different or missing dates).
2. FABRICATED ENTRIES: Every work_experience entry must have a clear corresponding passage
   in the source text. Flag any entry with no basis in the source.
3. INVENTED DATES: start_date and end_date must match exactly what is stated in the source.
   If a date is absent from the source, the field must be null — never inferred or invented.
4. INVENTED CONTENT: responsibilities, achievements, and technologies must reflect what is
   explicitly stated in the source text. Flag any item that adds content not present in the source.

Respond ONLY with a valid JSON object — no markdown, no explanations:
{
  "approved": true or false,
  "issues": ["list of specific issues with work_experience index and description — empty array if approved"],
  "feedback": "concise instruction for the extractor to correct all issues — empty string if approved"
}"""


def build_cv_extraction_review_prompt(raw_cv_text: str, extracted_json: dict) -> str:
    """Build the reviewer user prompt for CV extraction.

    Args:
        raw_cv_text:    The original CV text the profile was extracted from.
        extracted_json: The profile JSON produced by the extraction agent.
    """
    return (
        "Review this extracted profile against the source CV text.\n\n"
        f"SOURCE CV TEXT:\n{raw_cv_text}\n\n"
        f"EXTRACTED PROFILE:\n{json.dumps(extracted_json, ensure_ascii=False, indent=2)}\n\n"
        "Does the extracted profile faithfully and completely represent the source — "
        "no duplicates, no fabrications, no invented dates, no invented content? "
        "Return your review JSON."
    )


def build_cv_extraction_retry_prompt(
    raw_cv_text: str,
    previous_draft: dict[str, Any],
    feedback: str,
) -> str:
    """Build the retry user prompt after a reviewer rejection of a CV extraction.

    Args:
        raw_cv_text:    The original CV text (source of truth).
        previous_draft: The extraction the reviewer rejected.
        feedback:       The reviewer's critique — used verbatim as the correction instruction.
    """
    return (
        "A quality review of your previous extraction identified the following issues. "
        "Correct them and return the updated JSON.\n\n"
        f"REVIEW FEEDBACK:\n{feedback}\n\n"
        f"PREVIOUS EXTRACTION:\n{json.dumps(previous_draft, ensure_ascii=False, indent=2)}\n\n"
        "SOURCE CV TEXT (the only source of truth):\n"
        "Remember: each position exactly once, only facts present in the source, "
        "null for anything missing. Count the distinct positions again before writing work_experience.\n\n"
        "---\n\n"
        + raw_cv_text
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_skill_enrichment.py::TestCVExtractionReviewPrompt -v
```

Expected: all PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/applire/prompts/review_cv_extraction.py tests/unit/test_skill_enrichment.py
git commit -m "feat: add CV extraction review and retry prompts (work_experience schema)"
```

---

## Task 8: Wire `enrich_skills()` into `_import_from_text()`

**Files:**
- Modify: `backend/applire/services/profile/__init__.py:216-297`

- [ ] **Step 1: Add the import and wire the call**

In `backend/applire/services/profile/__init__.py`, add the import alongside the existing service imports (after line 37, `from applire.services.reviewer import review_and_refine`):

```python
from applire.services.skill_enrichment import enrich_skills
```

In `_import_from_text()` at line 241, the current code is:
```python
incoming = MasterProfileData.model_validate(data)
```

Change it to:
```python
incoming = MasterProfileData.model_validate(data)
incoming = await enrich_skills(incoming, provider)
```

The full updated section (lines 229–244) should read:

```python
    data: dict = await provider.aparse_json(
        build_user_prompt(raw_text),
        system=SYSTEM_PROMPT,
        temperature=0.1,
        max_tokens=8192,
    )
    data = await review_and_refine(
        source=raw_text,
        draft=data,
        generator_prompt_fn=_build_extraction_retry_prompt,
        generator_system=SYSTEM_PROMPT,
        reviewer_prompt_fn=_build_extraction_review_prompt,
        reviewer_system=_EXTRACTION_REVIEW_SYSTEM_PROMPT,
        provider=provider,
        max_retries=LLM_REVIEW_MAX_RETRIES,
        generator_max_tokens=8192,
    )
    incoming = MasterProfileData.model_validate(data)
    incoming = await enrich_skills(incoming, provider)
    now = datetime.now(timezone.utc)
```

- [ ] **Step 2: Run the existing unit tests to check for regressions**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_profile_service.py tests/unit/test_skill_enrichment.py -v
```

Expected: all PASSED. (The profile service tests don't directly call `_import_from_text`, so no mock changes are needed here.)

- [ ] **Step 3: Commit**

```bash
git add backend/applire/services/profile/__init__.py
git commit -m "feat: wire enrich_skills into _import_from_text after review layer"
```

---

## Task 9: Wire `review_and_refine()` + `enrich_skills()` into `upload_cv()`

**Files:**
- Modify: `backend/applire/services/profile/__init__.py:475-656`
- Modify: `tests/unit/test_cv_upload.py` (update existing upload tests)

- [ ] **Step 1: Update existing upload tests to patch the new calls**

The two existing upload tests (`test_upload_cv_first_import` and `test_upload_cv_second_import_triggers_merge`) use `mock_provider.aparse_json.return_value = {...}`. After wiring `review_and_refine` into `upload_cv`, every `aparse_json` call will receive the same dict — the reviewer call will get the profile dict (no `approved` key) and interpret it as rejected, looping incorrectly.

Patch `review_and_refine` and `enrich_skills` at the module level in both tests.

In `tests/unit/test_cv_upload.py`, update `test_upload_cv_first_import`:

```python
@pytest.mark.asyncio
async def test_upload_cv_first_import(sqlite_session, tmp_path):
    """First CV upload creates a MasterProfile and returns CVUploadResponse."""
    from applire.services.profile import upload_cv
    from applire.storage.local import LocalStorageProvider
    from applire.ocr.tesseract import TesseractExtractor

    mock_provider = AsyncMock()
    mock_provider.__class__.__name__ = "MockProvider"
    profile_data = {
        "personal_info": {"name": "Max Mustermann", "email": "max@example.de"},
        "work_experience": [
            {
                "company": "Siemens AG",
                "role": "Software Engineer",
                "start_date": "2019-01",
                "end_date": "2023-06",
                "responsibilities": ["Developed backend services", "Led code reviews"],
                "technologies": ["Python", "Django"],
            }
        ],
        "education": [
            {
                "institution": "TU München",
                "degree": "Bachelor of Science",
                "field": "Computer Science",
                "start_date": "2015",
                "end_date": "2019",
            }
        ],
        "skills": [
            {"name": "Python", "category": "technical", "proficiency": "advanced"},
            {"name": "Django", "category": "technical", "proficiency": "intermediate"},
        ],
        "languages": [
            {"language": "German", "level": "Native"},
            {"language": "English", "level": "C1"},
        ],
    }
    mock_provider.aparse_json.return_value = profile_data
    mock_ocr = AsyncMock()

    with patch("applire.services.cv_parser.extract_text", new=AsyncMock(return_value="Max Mustermann\nSoftware Engineer\nSiemens AG")), \
         patch("applire.services.profile.review_and_refine", new=AsyncMock(side_effect=lambda **kw: kw["draft"])), \
         patch("applire.services.profile.enrich_skills", new=AsyncMock(side_effect=lambda p, _: p)):
        storage = LocalStorageProvider(str(tmp_path))
        response = await upload_cv(
            file_bytes=b"fake-pdf",
            filename="cv.pdf",
            content_type="application/pdf",
            db=sqlite_session,
            provider=mock_provider,
            storage=storage,
            ocr_extractor=mock_ocr,
        )

    assert response.profile_id is not None
    assert response.completeness_score > 0.0
    assert response.expires_at is not None
    assert response.enrichment_record_id is not None
    assert response.conflicts == []
    assert response.completeness_score >= 0.5
    assert response.status == "COMPLETE"
```

Update `test_upload_cv_second_import_triggers_merge`:

```python
@pytest.mark.asyncio
async def test_upload_cv_second_import_triggers_merge(sqlite_session, tmp_path):
    """Second upload with conflicting dates triggers merge_profiles() and flags conflicts."""
    from applire.services.profile import upload_cv
    from applire.storage.local import LocalStorageProvider

    mock_ocr = AsyncMock()
    storage = LocalStorageProvider(str(tmp_path))

    first_profile = {
        "personal_info": {"name": "Anna Schmidt"},
        "work_experience": [
            {
                "company": "BMW Group",
                "role": "Product Manager",
                "start_date": "2018-03",
                "end_date": "2022-01",
                "responsibilities": ["Led product roadmap"],
            }
        ],
        "skills": [{"name": "Product Management", "category": "domain", "proficiency": "advanced"}],
        "languages": [{"language": "German", "level": "Native"}],
    }

    second_profile = {
        "personal_info": {"name": "Anna Schmidt"},
        "work_experience": [
            {
                "company": "BMW Group",
                "role": "Senior Product Manager",
                "start_date": "2017-06",  # different start_date → conflict
                "end_date": "2022-01",
                "responsibilities": ["Managed stakeholder relations"],
            }
        ],
        "skills": [{"name": "Product Management", "category": "domain", "proficiency": "expert"}],
        "languages": [{"language": "German", "level": "Native"}],
    }

    mock_provider = AsyncMock()
    mock_provider.__class__.__name__ = "MockProvider"

    with patch("applire.services.cv_parser.extract_text", new=AsyncMock(return_value="Anna Schmidt\nBMW Group")), \
         patch("applire.services.profile.review_and_refine", new=AsyncMock(side_effect=lambda **kw: kw["draft"])), \
         patch("applire.services.profile.enrich_skills", new=AsyncMock(side_effect=lambda p, _: p)):

        mock_provider.aparse_json.return_value = first_profile
        await upload_cv(
            file_bytes=b"cv1",
            filename="cv1.pdf",
            content_type="application/pdf",
            db=sqlite_session,
            provider=mock_provider,
            storage=storage,
            ocr_extractor=mock_ocr,
        )

        mock_provider.aparse_json.return_value = second_profile
        response = await upload_cv(
            file_bytes=b"cv2",
            filename="cv2.pdf",
            content_type="application/pdf",
            db=sqlite_session,
            provider=mock_provider,
            storage=storage,
            ocr_extractor=mock_ocr,
        )

    assert len(response.conflicts) >= 1
    conflict_fields = [c.field for c in response.conflicts]
    assert "start_date" in conflict_fields
    assert response.status == "DRAFT"
```

- [ ] **Step 2: Run the updated tests to confirm the patches work with current code**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_cv_upload.py::test_upload_cv_first_import tests/unit/test_cv_upload.py::test_upload_cv_second_import_triggers_merge -v
```

Expected: both PASSED (the patches are no-ops with current code — `review_and_refine` and `enrich_skills` don't exist in `upload_cv` yet, but the `with patch(...)` context managers will work because `AsyncMock(side_effect=lambda p, _: p)` for `enrich_skills` returns the profile unchanged).

Note: The patches will raise `AttributeError` if `enrich_skills` is not yet importable from `applire.services.profile`. If so, the import will be wired in the next step and the tests will pass.

- [ ] **Step 3: Wire `review_and_refine` and `enrich_skills` into `upload_cv()`**

In `backend/applire/services/profile/__init__.py`, the `upload_cv()` function currently has this block starting around line 539:

```python
    # 3. LLM extraction
    if job_analysis_dict:
        prompt = build_jd_aware_prompt(raw_text, job_analysis_dict)
        system = JD_AWARE_CV_EXTRACTION_PROMPT
    else:
        prompt = build_generic_prompt(raw_text)
        system = GENERIC_CV_EXTRACTION_PROMPT

    data: dict = await provider.aparse_json(prompt, system=system, temperature=0.1, max_tokens=8192)
    incoming = MasterProfileData.model_validate(data)
    now = datetime.now(timezone.utc)
```

Replace it with:

```python
    # 3. LLM extraction + review layer + skill enrichment
    if job_analysis_dict:
        prompt = build_jd_aware_prompt(raw_text, job_analysis_dict)
        system = JD_AWARE_CV_EXTRACTION_PROMPT
    else:
        prompt = build_generic_prompt(raw_text)
        system = GENERIC_CV_EXTRACTION_PROMPT

    data: dict = await provider.aparse_json(prompt, system=system, temperature=0.1, max_tokens=8192)
    data = await review_and_refine(
        source=raw_text,
        draft=data,
        generator_prompt_fn=_build_cv_extraction_retry_prompt,
        generator_system=system,
        reviewer_prompt_fn=_build_cv_extraction_review_prompt,
        reviewer_system=_CV_EXTRACTION_REVIEW_SYSTEM_PROMPT,
        provider=provider,
        max_retries=LLM_REVIEW_MAX_RETRIES,
        generator_max_tokens=8192,
    )
    incoming = MasterProfileData.model_validate(data)
    incoming = await enrich_skills(incoming, provider)
    now = datetime.now(timezone.utc)
```

Also add the new imports at the top of the file (alongside the existing prompt imports, around lines 17–31):

```python
from applire.prompts.review_cv_extraction import (
    CV_EXTRACTION_REVIEW_SYSTEM_PROMPT as _CV_EXTRACTION_REVIEW_SYSTEM_PROMPT,
    build_cv_extraction_review_prompt as _build_cv_extraction_review_prompt,
    build_cv_extraction_retry_prompt as _build_cv_extraction_retry_prompt,
)
```

- [ ] **Step 4: Run all upload tests**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_cv_upload.py -v
```

Expected: all PASSED.

- [ ] **Step 5: Run the full unit suite**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/ -v --tb=short
```

Expected: all PASSED.

- [ ] **Step 6: Commit**

```bash
git add backend/applire/services/profile/__init__.py tests/unit/test_cv_upload.py
git commit -m "feat: wire review_and_refine and enrich_skills into upload_cv"
```

---

## Task 10: Add `provider` to `patch_profile_section()` and router

**Files:**
- Modify: `backend/applire/services/profile/__init__.py:319-370`
- Modify: `backend/applire/routers/profile.py:341-365`
- Test: `tests/unit/test_skill_enrichment.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_skill_enrichment.py`:

```python
# ---------------------------------------------------------------------------
# Task 10: patch_profile_section with provider
# ---------------------------------------------------------------------------

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch


@pytest_asyncio.fixture
async def sqlite_session_for_patch():
    """In-memory SQLite session with MasterProfile table."""
    from applire.db.session import Base
    from applire.models.profile import MasterProfile
    from applire.models.user import User
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda c: Base.metadata.create_all(
                c,
                tables=[MasterProfile.__table__, User.__table__],
            )
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_patch_profile_section_without_provider_skips_enrichment(sqlite_session_for_patch):
    """Patching without a provider must not call enrich_skills."""
    from applire.schemas.profile import MasterProfileData, ProfileMetadata
    from applire.models.profile import MasterProfile
    from applire.services.profile import patch_profile_section
    from datetime import datetime, timezone
    import json

    # Seed a profile
    profile_data = MasterProfileData(
        skills=[],
        work_experience=[],
    )
    profile_data.metadata = ProfileMetadata(
        completeness_score=0.0,
        created_via="manual",
        created_at=datetime.now(timezone.utc),
        last_updated=datetime.now(timezone.utc),
    )
    record = MasterProfile(profile_json=profile_data.model_dump(mode="json"))
    sqlite_session_for_patch.add(record)
    await sqlite_session_for_patch.commit()

    with patch("applire.services.profile.enrich_skills") as mock_enrich:
        await patch_profile_section(
            section="skills",
            value=[{"name": "Python", "category": "technical", "proficiency": "basic"}],
            db=sqlite_session_for_patch,
        )
        mock_enrich.assert_not_called()


@pytest.mark.asyncio
async def test_patch_profile_section_with_provider_calls_enrich_for_skills(sqlite_session_for_patch):
    """Patching skills with a provider must call enrich_skills."""
    from applire.schemas.profile import MasterProfileData, ProfileMetadata
    from applire.models.profile import MasterProfile
    from applire.services.profile import patch_profile_section
    from datetime import datetime, timezone

    profile_data = MasterProfileData(skills=[], work_experience=[])
    profile_data.metadata = ProfileMetadata(
        completeness_score=0.0,
        created_via="manual",
        created_at=datetime.now(timezone.utc),
        last_updated=datetime.now(timezone.utc),
    )
    record = MasterProfile(profile_json=profile_data.model_dump(mode="json"))
    sqlite_session_for_patch.add(record)
    await sqlite_session_for_patch.commit()

    mock_provider = AsyncMock()

    with patch("applire.services.profile.enrich_skills", new=AsyncMock(side_effect=lambda p, _: p)) as mock_enrich:
        await patch_profile_section(
            section="skills",
            value=[{"name": "Python", "category": "technical", "proficiency": "basic"}],
            db=sqlite_session_for_patch,
            provider=mock_provider,
        )
        mock_enrich.assert_called_once()


@pytest.mark.asyncio
async def test_patch_personal_info_with_provider_does_not_call_enrich(sqlite_session_for_patch):
    """Patching personal_info (non-skills section) must not call enrich_skills even with provider."""
    from applire.schemas.profile import MasterProfileData, ProfileMetadata
    from applire.models.profile import MasterProfile
    from applire.services.profile import patch_profile_section
    from datetime import datetime, timezone

    profile_data = MasterProfileData(skills=[], work_experience=[])
    profile_data.metadata = ProfileMetadata(
        completeness_score=0.0,
        created_via="manual",
        created_at=datetime.now(timezone.utc),
        last_updated=datetime.now(timezone.utc),
    )
    record = MasterProfile(profile_json=profile_data.model_dump(mode="json"))
    sqlite_session_for_patch.add(record)
    await sqlite_session_for_patch.commit()

    mock_provider = AsyncMock()

    with patch("applire.services.profile.enrich_skills") as mock_enrich:
        await patch_profile_section(
            section="personal_info",
            value={"name": "Max Mustermann"},
            db=sqlite_session_for_patch,
            provider=mock_provider,
        )
        mock_enrich.assert_not_called()
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_skill_enrichment.py -k "patch_profile_section" -v
```

Expected: `TypeError` — `patch_profile_section` doesn't accept `provider` yet.

- [ ] **Step 3: Add `provider` parameter to `patch_profile_section()`**

In `backend/applire/services/profile/__init__.py`, update the function signature (line 319):

```python
async def patch_profile_section(
    section: str,
    value: object,
    db: AsyncSession,
    source: str = "manual_edit",
    source_session_id: str | None = None,
    provider: LLMProvider | None = None,
) -> MasterProfileResponse:
```

And add the enrichment call after `validated = MasterProfileData.model_validate(updated_dict)` (before the enrichment record creation block). The updated section (after line 339 in the original):

```python
    updated_dict = profile_data.model_dump(mode="json")
    updated_dict[section] = value
    validated = MasterProfileData.model_validate(updated_dict)

    # Re-run enrichment when skills or work_experience are patched (keeps years fresh)
    if section in {"work_experience", "skills"} and provider is not None:
        validated = await enrich_skills(validated, provider)

    # Build enrichment record
    action = "updated" if old_value else "added"
    enrichment = _make_enrichment_record(
```

- [ ] **Step 4: Add provider to the `patch_section` router endpoint**

In `backend/applire/routers/profile.py`, update the `patch_section` handler (lines 341–365):

```python
@router.patch("/{section}", response_model=MasterProfileResponse, status_code=status.HTTP_200_OK)
async def patch_section(
    section: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
    provider: LLMProvider = Depends(_get_provider),
) -> MasterProfileResponse:
    body = await request.json()
    try:
        return await patch_profile_section(section, body, db, provider=provider)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
```

- [ ] **Step 5: Run the new tests**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_skill_enrichment.py -k "patch_profile_section" -v
```

Expected: all PASSED.

- [ ] **Step 6: Run the full unit suite**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/ -v --tb=short
```

Expected: all PASSED.

- [ ] **Step 7: Check coverage**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/ --cov=applire --cov-report=term-missing --cov-fail-under=75
```

Expected: coverage ≥ 75%, no failures.

- [ ] **Step 8: Final commit**

```bash
git add backend/applire/services/profile/__init__.py backend/applire/routers/profile.py tests/unit/test_skill_enrichment.py
git commit -m "feat: add provider-triggered enrichment to patch_profile_section and router"
```

---

## Final verification

- [ ] **Run the full test suite one last time**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/ -v --cov=applire --cov-fail-under=75
```

Expected: all PASSED, coverage ≥ 75%.

- [ ] **Verify new files exist**

```bash
ls backend/applire/services/skill_enrichment.py \
   backend/applire/prompts/skill_estimation.py \
   backend/applire/prompts/review_cv_extraction.py \
   tests/unit/test_skill_enrichment.py
```

Expected: all four files present.
