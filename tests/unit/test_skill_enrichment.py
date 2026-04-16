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


# ---------------------------------------------------------------------------
# Task 2: Date parsing and range calculation
# ---------------------------------------------------------------------------

class TestParsePartialDate:
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
