"""
Iteration 11 unit tests — Master Profile Data Foundation.

Coverage:
- Pydantic model validation + legacy field migration
- calculate_completeness() weighted scoring
- Merge logic: accumulation model (not conflict model)
  - Work experience: same company+dates → accumulate bullets & role_aliases
  - Work experience: date contradictions → flag as conflict
  - Skills: higher proficiency wins, no conflicts
  - Personal info: gap-fill + conflict on populated-vs-different
- Conflict resolution: existing / incoming / manual
- SQLite persistence via Base.metadata.create_all (uses with_variant JSON fallback)

Follows the pattern from iter 10: SQLite + raw ORM session, no external services.
"""
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apliqa.models.profile import MasterProfile
from apliqa.db.session import Base
from apliqa.schemas.profile import (
    Conflict,
    EducationEntry,
    EnrichmentRecord,
    FieldChange,
    Language,
    MasterProfileData,
    PersonalInfo,
    ProfileMetadata,
    ProfessionalSummary,
    Skill,
    WorkEntry,
)
from apliqa.services.profile.merge import (
    MergeResult,
    _dates_contradict,
    _dates_overlap,
    _merge_str_lists,
    _merge_work_experience,
    _merge_skills,
    merge_profiles,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def sqlite_session():
    """In-memory SQLite async session using Base.metadata (with_variant JSON fallback)."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


def _work_entry(**kwargs) -> WorkEntry:
    defaults = dict(company="Acme GmbH", role="Software Engineer", start_date="2020-01", end_date="2022-12")
    return WorkEntry(**(defaults | kwargs))


def _profile(**kwargs) -> MasterProfileData:
    return MasterProfileData(**kwargs)


# ─── Pydantic model validation ────────────────────────────────────────────────

class TestSchemaModels:
    def test_work_entry_defaults(self):
        e = WorkEntry(company="X", role="Dev")
        assert e.responsibilities == []
        assert e.achievements == []
        assert e.technologies == []
        assert e.role_aliases == []

    def test_skill_defaults(self):
        s = Skill(name="Python")
        assert s.category == "technical"
        assert s.proficiency == "intermediate"
        assert s.years_experience is None

    def test_master_profile_empty_defaults(self):
        p = MasterProfileData()
        assert p.work_experience == []
        assert p.skills == []
        assert p.metadata is None

    def test_personal_info_optional_fields(self):
        pi = PersonalInfo(name="Max Muster")
        assert pi.email is None
        assert pi.xing_url is None
        assert pi.nationality is None


class TestLegacyMigration:
    def test_work_history_migrated_to_work_experience(self):
        data = {
            "work_history": [
                {"company": "OldCo", "role": "Dev", "bullets": ["did stuff"]}
            ]
        }
        p = MasterProfileData.model_validate(data)
        assert len(p.work_experience) == 1
        assert p.work_experience[0].company == "OldCo"
        assert p.work_experience[0].responsibilities == ["did stuff"]

    def test_contact_migrated_to_personal_info(self):
        data = {
            "contact": {"name": "Anna", "email": "a@b.com", "linkedin": "https://li.com/anna"}
        }
        p = MasterProfileData.model_validate(data)
        assert p.personal_info.name == "Anna"
        assert p.personal_info.linkedin_url == "https://li.com/anna"

    def test_skills_list_of_strings_migrated(self):
        data = {"skills": ["Python", "Docker"]}
        p = MasterProfileData.model_validate(data)
        assert len(p.skills) == 2
        assert all(isinstance(s, Skill) for s in p.skills)
        assert p.skills[0].name == "Python"
        assert p.skills[0].proficiency == "intermediate"

    def test_mixed_skills_list(self):
        data = {
            "skills": [
                "Python",
                {"name": "Go", "category": "technical", "proficiency": "advanced"},
            ]
        }
        p = MasterProfileData.model_validate(data)
        assert p.skills[0].name == "Python"
        assert p.skills[1].proficiency == "advanced"


# ─── Completeness scoring ─────────────────────────────────────────────────────

class TestCompletenessScore:
    def test_empty_profile_scores_zero(self):
        assert MasterProfileData().calculate_completeness() == 0.0

    def test_full_profile_scores_one(self):
        p = MasterProfileData(
            personal_info=PersonalInfo(name="Max", email="m@m.de"),
            professional_summary=ProfessionalSummary(de="Erfahrener Entwickler"),
            work_experience=[_work_entry()],
            education=[EducationEntry(institution="TU Berlin", degree="M.Sc.", field="CS")],
            skills=[Skill(name="Python")],
            languages=[Language(language="German", level="Native")],
            certifications=[],
            publications=[],
            volunteer_activities=[],
        )
        score = p.calculate_completeness()
        # work(0.30) + edu(0.20) + skills(0.20) + personal(0.15) + lang(0.10) + summary(0.03) = 0.98
        assert score == pytest.approx(0.98, abs=0.01)

    def test_work_experience_dominates(self):
        p = MasterProfileData(work_experience=[_work_entry()])
        assert p.calculate_completeness() == pytest.approx(0.30)

    def test_education_weight(self):
        p = MasterProfileData(
            education=[EducationEntry(institution="LMU", degree="B.Sc.", field="Inf")]
        )
        assert p.calculate_completeness() == pytest.approx(0.20)

    def test_score_rounds_to_two_decimals(self):
        p = MasterProfileData(
            work_experience=[_work_entry()],
            education=[EducationEntry(institution="LMU", degree="B.Sc.", field="Inf")],
            skills=[Skill(name="Python")],
        )
        score = p.calculate_completeness()
        assert score == round(score, 2)


# ─── Date helpers ─────────────────────────────────────────────────────────────

class TestDateHelpers:
    def test_overlap_normal(self):
        assert _dates_overlap("2019-01", "2021-12", "2020-06", "2022-06") is True

    def test_no_overlap(self):
        assert _dates_overlap("2019-01", "2019-12", "2020-01", "2021-12") is False

    def test_overlap_missing_start(self):
        assert _dates_overlap(None, "2021-12", "2020-06", None) is True

    def test_contradict_different_months(self):
        assert _dates_contradict("2020-01", "2020-06") is True

    def test_no_contradict_same(self):
        assert _dates_contradict("2020-01", "2020-01") is False

    def test_no_contradict_missing(self):
        assert _dates_contradict(None, "2020-01") is False
        assert _dates_contradict("2020-01", None) is False

    def test_no_contradict_year_vs_yearmonth(self):
        # "2020" normalises to "2020-01"; "2020-01" also "2020-01" → same
        assert _dates_contradict("2020", "2020-01") is False

    def test_str_list_merge_dedup(self):
        result = _merge_str_lists(["Python", "Go"], ["go", "Rust"])
        assert "Python" in result
        assert "Go" in result
        assert "Rust" in result
        assert result.count("Go") == 1  # no duplicate despite case difference


# ─── Work experience merge ────────────────────────────────────────────────────

class TestMergeWorkExperience:
    def _run(self, existing_entries, incoming_entries, source="cv_upload"):
        return _merge_work_experience(existing_entries, incoming_entries, source)

    def test_different_company_appended(self):
        ex = [_work_entry(company="Acme GmbH", role="Dev")]
        inc = [_work_entry(company="BigCorp", role="Lead")]
        result, added, conflicts = self._run(ex, inc)
        assert len(result) == 2
        assert len(conflicts) == 0
        assert any("BigCorp" in a for a in added)

    def test_same_company_non_overlapping_dates_appended(self):
        ex = [_work_entry(start_date="2018-01", end_date="2019-12")]
        inc = [_work_entry(start_date="2020-01", end_date="2021-12")]
        result, added, conflicts = self._run(ex, inc)
        assert len(result) == 2
        assert len(conflicts) == 0

    def test_same_company_overlap_role_accumulates_not_conflicts(self):
        """Core test: 'Team Lead' vs '2nd Level Support' at same job → accumulate."""
        ex = [_work_entry(role="Team Lead", start_date="2020-01", end_date="2022-12")]
        inc = [_work_entry(role="2nd Level Support", start_date="2020-01", end_date="2022-12")]
        result, added, conflicts = self._run(ex, inc)
        assert len(result) == 1
        assert len(conflicts) == 0
        entry = result[0]
        assert entry.role == "Team Lead"  # primary role unchanged
        assert "2nd Level Support" in entry.role_aliases

    def test_same_company_overlap_bullets_merged(self):
        ex = [_work_entry(
            responsibilities=["Led team of 5"],
            achievements=["Shipped product X"],
            technologies=["Python"],
        )]
        inc = [_work_entry(
            responsibilities=["Handled on-call rotation"],
            achievements=["Shipped product X"],  # duplicate
            technologies=["Docker"],
        )]
        result, _, _ = self._run(ex, inc)
        entry = result[0]
        assert "Led team of 5" in entry.responsibilities
        assert "Handled on-call rotation" in entry.responsibilities
        assert entry.achievements.count("Shipped product X") == 1  # no duplicate
        assert "Python" in entry.technologies
        assert "Docker" in entry.technologies

    def test_date_contradiction_flagged(self):
        ex = [_work_entry(start_date="2019-03", end_date="2021-12")]
        inc = [_work_entry(start_date="2019-06", end_date="2021-12")]  # start differs
        result, _, conflicts = self._run(ex, inc)
        assert len(result) == 1  # still merged (not duplicated)
        assert len(conflicts) == 1
        assert conflicts[0].field == "start_date"
        assert conflicts[0].existing_value == "2019-03"
        assert conflicts[0].incoming_value == "2019-06"

    def test_end_date_contradiction_flagged(self):
        ex = [_work_entry(start_date="2019-01", end_date="2021-06")]
        inc = [_work_entry(start_date="2019-01", end_date="2021-12")]
        _, _, conflicts = self._run(ex, inc)
        assert any(c.field == "end_date" for c in conflicts)

    def test_role_alias_not_duplicated(self):
        ex = [_work_entry(role="Team Lead", role_aliases=["2nd Level Support"])]
        inc = [_work_entry(role="2nd Level Support")]
        result, _, _ = self._run(ex, inc)
        # "2nd Level Support" already in aliases — should not be added again
        aliases = result[0].role_aliases
        assert aliases.count("2nd Level Support") == 1

    def test_gap_fill_industry_context(self):
        ex = [_work_entry(industry_context=None)]
        inc = [_work_entry(industry_context="FinTech")]
        result, added, _ = self._run(ex, inc)
        assert result[0].industry_context == "FinTech"
        assert any("industry_context" in a for a in added)

    def test_no_overwrite_industry_context_if_exists(self):
        ex = [_work_entry(industry_context="E-Commerce")]
        inc = [_work_entry(industry_context="FinTech")]
        result, _, _ = self._run(ex, inc)
        assert result[0].industry_context == "E-Commerce"


# ─── Skills merge ─────────────────────────────────────────────────────────────

class TestMergeSkills:
    def test_new_skill_added(self):
        ex = [Skill(name="Python", proficiency="advanced")]
        inc = [Skill(name="Go", proficiency="intermediate")]
        result, added, conflicts = _merge_skills(ex, inc, "cv_upload")
        assert len(result) == 2
        assert len(conflicts) == 0
        assert any("Go" in a for a in added)

    def test_higher_proficiency_wins(self):
        ex = [Skill(name="Python", proficiency="intermediate")]
        inc = [Skill(name="Python", proficiency="advanced")]
        result, _, _ = _merge_skills(ex, inc, "cv_upload")
        assert len(result) == 1
        assert result[0].proficiency == "advanced"

    def test_lower_proficiency_does_not_downgrade(self):
        ex = [Skill(name="Python", proficiency="expert")]
        inc = [Skill(name="Python", proficiency="basic")]
        result, _, _ = _merge_skills(ex, inc, "cv_upload")
        assert result[0].proficiency == "expert"

    def test_higher_years_experience_wins(self):
        ex = [Skill(name="Python", years_experience=3)]
        inc = [Skill(name="Python", years_experience=5)]
        result, _, _ = _merge_skills(ex, inc, "cv_upload")
        assert result[0].years_experience == 5

    def test_case_insensitive_dedup(self):
        ex = [Skill(name="python", proficiency="advanced")]
        inc = [Skill(name="Python", proficiency="intermediate")]
        result, added, _ = _merge_skills(ex, inc, "cv_upload")
        assert len(result) == 1
        assert added == []  # no new skill added

    def test_no_conflicts_generated(self):
        ex = [Skill(name="Python", proficiency="expert")]
        inc = [Skill(name="Python", proficiency="basic")]
        _, _, conflicts = _merge_skills(ex, inc, "cv_upload")
        assert conflicts == []


# ─── Full profile merge ───────────────────────────────────────────────────────

class TestMergeProfiles:
    def test_personal_info_gap_fill(self):
        existing = _profile(personal_info=PersonalInfo(name="Max"))
        incoming = _profile(personal_info=PersonalInfo(name="Max", email="max@example.com"))
        result = merge_profiles(existing, incoming, "cv_upload")
        assert result.merged_profile.personal_info.email == "max@example.com"
        assert len(result.conflicts) == 0

    def test_personal_info_conflict_on_email_change(self):
        existing = _profile(personal_info=PersonalInfo(name="Max", email="old@x.com"))
        incoming = _profile(personal_info=PersonalInfo(name="Max", email="new@x.com"))
        result = merge_profiles(existing, incoming, "cv_upload")
        conflict = next((c for c in result.conflicts if c.field == "email"), None)
        assert conflict is not None
        assert conflict.existing_value == "old@x.com"
        assert conflict.incoming_value == "new@x.com"

    def test_professional_summary_fills_missing_language(self):
        existing = _profile(professional_summary=ProfessionalSummary(de="Erfahrener Dev"))
        incoming = _profile(professional_summary=ProfessionalSummary(en="Experienced Dev"))
        result = merge_profiles(existing, incoming, "cv_upload")
        assert result.merged_profile.professional_summary.de == "Erfahrener Dev"
        assert result.merged_profile.professional_summary.en == "Experienced Dev"

    def test_education_dedup(self):
        edu = EducationEntry(institution="TU Berlin", degree="M.Sc.", field="CS")
        existing = _profile(education=[edu])
        incoming = _profile(education=[edu])
        result = merge_profiles(existing, incoming, "cv_upload")
        assert len(result.merged_profile.education) == 1

    def test_education_different_degree_appended(self):
        existing = _profile(education=[EducationEntry(institution="TU Berlin", degree="M.Sc.", field="CS")])
        incoming = _profile(education=[EducationEntry(institution="TU Berlin", degree="B.Sc.", field="CS")])
        result = merge_profiles(existing, incoming, "cv_upload")
        assert len(result.merged_profile.education) == 2

    def test_language_new_added(self):
        existing = _profile(languages=[Language(language="German", level="Native")])
        incoming = _profile(languages=[Language(language="English", level="C1")])
        result = merge_profiles(existing, incoming, "cv_upload")
        assert len(result.merged_profile.languages) == 2

    def test_language_duplicate_not_added(self):
        lang = Language(language="German", level="Native")
        existing = _profile(languages=[lang])
        incoming = _profile(languages=[lang])
        result = merge_profiles(existing, incoming, "cv_upload")
        assert len(result.merged_profile.languages) == 1

    def test_added_list_tracks_enrichments(self):
        existing = _profile()
        incoming = _profile(
            skills=[Skill(name="Rust")],
            languages=[Language(language="French", level="B2")],
        )
        result = merge_profiles(existing, incoming, "linkedin_import")
        assert any("Rust" in a for a in result.added)
        assert any("French" in a for a in result.added)


# ─── SQLite persistence ───────────────────────────────────────────────────────

class TestSQLitePersistence:
    @pytest.mark.asyncio
    async def test_create_and_retrieve_profile(self, sqlite_session: AsyncSession):
        profile_data = MasterProfileData(
            personal_info=PersonalInfo(name="Lena Müller", email="lena@example.de"),
            work_experience=[_work_entry(company="StartupX", role="CTO")],
            skills=[Skill(name="Python", proficiency="expert")],
        )
        record = MasterProfile(profile_json=profile_data.model_dump(mode="json"))
        sqlite_session.add(record)
        await sqlite_session.commit()
        await sqlite_session.refresh(record)

        assert record.id is not None
        loaded = MasterProfileData.model_validate(record.profile_json)
        assert loaded.personal_info.name == "Lena Müller"
        assert loaded.work_experience[0].company == "StartupX"
        assert loaded.skills[0].proficiency == "expert"

    @pytest.mark.asyncio
    async def test_role_aliases_persisted(self, sqlite_session: AsyncSession):
        entry = _work_entry(role="Team Lead", role_aliases=["2nd Level Support", "Tech Lead"])
        profile_data = MasterProfileData(work_experience=[entry])
        record = MasterProfile(profile_json=profile_data.model_dump(mode="json"))
        sqlite_session.add(record)
        await sqlite_session.commit()
        await sqlite_session.refresh(record)

        loaded = MasterProfileData.model_validate(record.profile_json)
        assert loaded.work_experience[0].role_aliases == ["2nd Level Support", "Tech Lead"]

    @pytest.mark.asyncio
    async def test_enrichment_history_persisted(self, sqlite_session: AsyncSession):
        enrichment = EnrichmentRecord(
            timestamp=datetime.now(timezone.utc),
            source="cv_upload",
            changes=[FieldChange(section="skills", field="skills", action="added", new_value="Python")],
        )
        meta = ProfileMetadata(
            completeness_score=0.3,
            created_via="cv_upload",
            enrichment_history=[enrichment],
        )
        profile_data = MasterProfileData(metadata=meta)
        record = MasterProfile(profile_json=profile_data.model_dump(mode="json"))
        sqlite_session.add(record)
        await sqlite_session.commit()
        await sqlite_session.refresh(record)

        loaded = MasterProfileData.model_validate(record.profile_json)
        assert len(loaded.metadata.enrichment_history) == 1
        assert loaded.metadata.enrichment_history[0].source == "cv_upload"

    @pytest.mark.asyncio
    async def test_pending_conflicts_persisted(self, sqlite_session: AsyncSession):
        conflict = Conflict(
            section="work_experience",
            field="start_date",
            existing_value="2019-03",
            incoming_value="2019-06",
            source="cv_upload",
        )
        meta = ProfileMetadata(created_via="cv_upload", pending_conflicts=[conflict])
        profile_data = MasterProfileData(metadata=meta)
        record = MasterProfile(profile_json=profile_data.model_dump(mode="json"))
        sqlite_session.add(record)
        await sqlite_session.commit()
        await sqlite_session.refresh(record)

        loaded = MasterProfileData.model_validate(record.profile_json)
        assert len(loaded.metadata.pending_conflicts) == 1
        assert loaded.metadata.pending_conflicts[0].field == "start_date"
        cid = loaded.metadata.pending_conflicts[0].conflict_id
        assert cid  # UUID was assigned


# ─── Conflict resolution (service layer, no DB) ───────────────────────────────

class TestConflictSchema:
    """Test the Conflict model and ConflictResolutionRequest schema."""

    def test_conflict_gets_uuid(self):
        c = Conflict(
            section="personal_info",
            field="email",
            existing_value="a@a.com",
            incoming_value="b@b.com",
            source="cv_upload",
        )
        assert c.conflict_id
        assert len(c.conflict_id) == 36  # UUID4 string

    def test_conflict_resolution_request_valid(self):
        from apliqa.schemas.profile import ConflictResolutionRequest
        req = ConflictResolutionRequest(resolution="manual", value="custom@email.com")
        assert req.resolution == "manual"
        assert req.value == "custom@email.com"

    def test_conflict_resolution_request_existing(self):
        from apliqa.schemas.profile import ConflictResolutionRequest
        req = ConflictResolutionRequest(resolution="existing")
        assert req.value is None
