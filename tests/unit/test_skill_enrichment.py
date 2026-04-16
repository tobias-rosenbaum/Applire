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
