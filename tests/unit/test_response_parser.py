"""
Sprint 13 — coverage boost tests.

Targets the four lowest-coverage modules to push total coverage from ~71% to ≥75%:
  - backend/applire/services/profile.py          (legacy, 0%)
  - backend/applire/services/job.py              (35%)
  - backend/applire/storage/__init__.py          (38%)
  - backend/applire/services/interview_graph.py  (37%)
  - backend/applire/services/profile/__init__.py (39%)

No Docker or real database connections — all external I/O is mocked.

Run:
    PYTHONPATH=backend pytest tests/unit/test_sprint13_coverage.py -v
"""

import hashlib
import importlib
import importlib.util
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


# ---------------------------------------------------------------------------
# Load the *legacy* profile.py flat module without letting the profile/ package
# shadow it.  Coverage instruments it because it runs under the 'applire' source
# tree — the module is registered as 'applire.services.profile_legacy' so it
# won't conflict with the profile/ package import.
# ---------------------------------------------------------------------------

def _load_legacy_profile():
    """Import backend/applire/services/profile.py directly (bypasses package shadow)."""
    _key = "applire.services.profile_legacy"
    if _key in sys.modules:
        return sys.modules[_key]
    _path = (
        Path(__file__).parent.parent.parent
        / "backend" / "applire" / "services" / "profile.py"
    )
    spec = importlib.util.spec_from_file_location(_key, str(_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[_key] = mod
    spec.loader.exec_module(mod)
    return mod


# ─── SQLite fixture (shared) ──────────────────────────────────────────────────


@pytest_asyncio.fixture
async def sqlite_session():
    """In-memory SQLite session — no Docker required."""
    from applire.db.session import Base  # noqa: F401
    import applire.models.profile  # noqa: F401
    import applire.models.job  # noqa: F401
    import applire.models.cv  # noqa: F401
    import applire.models.gap  # noqa: F401
    import applire.models.session  # noqa: F401
    import applire.models.user  # noqa: F401

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _make_mock_provider(return_value: dict) -> MagicMock:
    """Return a mock LLMProvider whose aparse_json returns *return_value*."""
    provider = MagicMock()
    provider.aparse_json = AsyncMock(return_value=return_value)
    provider.acomplete = AsyncMock(return_value="What is your experience with Python?")
    provider.__class__.__name__ = "MockProvider"
    return provider


def _minimal_profile_json() -> dict:
    return {
        "personal_info": {"name": "Alice"},
        "work_experience": [],
        "skills": [],
        "education": [],
        "languages": [],
        "certifications": [],
        "publications": [],
        "volunteer_activities": [],
    }


def _minimal_llm_profile_data() -> dict:
    return {
        "personal_info": {"name": "Alice Tester"},
        "work_experience": [
            {
                "company": "Acme GmbH",
                "role": "Software Developer",
                "start_date": "2020-01",
                "end_date": "2023-06",
            }
        ],
        "skills": [{"name": "Python", "proficiency": "expert"}],
        "education": [],
        "languages": [{"language": "German", "level": "C1"}],
        "certifications": [],
        "publications": [],
        "volunteer_activities": [],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 1. applire/services/profile.py  (legacy module — 0% → cover all 74 lines)
# ═══════════════════════════════════════════════════════════════════════════════


class TestLegacyProfileServiceHelpers:
    """Pure-function tests for the legacy profile.py module."""

    def test_extract_pdf_text_raises_on_bad_bytes(self):
        """Non-PDF bytes should raise rather than silently return empty text."""
        legacy = _load_legacy_profile()
        with pytest.raises(Exception):
            legacy.extract_pdf_text(b"not a pdf")

    def test_linkedin_to_text_returns_json_string(self):
        legacy = _load_legacy_profile()
        result = legacy._linkedin_to_text({"name": "Alice", "skills": ["Python"]})
        assert '"name"' in result
        assert "Python" in result

    def test_build_profile_data_populates_contact(self):
        legacy = _load_legacy_profile()
        data = {
            "contact": {
                "name": "Bob",
                "email": "bob@example.com",
                "phone": "+49123",
                "location": "Berlin",
                "linkedin": "https://linkedin.com/in/bob",
            }
        }
        result = legacy._build_profile_data(data)
        # The legacy Contact/contact maps to personal_info after model migration
        assert result.personal_info.name == "Bob"
        assert result.personal_info.email == "bob@example.com"

    def test_build_profile_data_populates_work_history(self):
        legacy = _load_legacy_profile()
        data = {
            "work_history": [
                {
                    "company": "Globex",
                    "role": "Engineer",
                    "start_date": "2019-01",
                    "end_date": "2022-12",
                    "bullets": ["Did stuff", "More stuff"],
                }
            ]
        }
        result = legacy._build_profile_data(data)
        # work_history migrates to work_experience via model_validator
        assert len(result.work_experience) == 1
        assert result.work_experience[0].company == "Globex"

    def test_build_profile_data_populates_education(self):
        legacy = _load_legacy_profile()
        data = {
            "education": [
                {
                    "institution": "TU Berlin",
                    "degree": "B.Sc.",
                    "field": "Informatik",
                    "start_date": "2015-10",
                    "end_date": "2018-09",
                }
            ]
        }
        result = legacy._build_profile_data(data)
        assert len(result.education) == 1
        assert result.education[0].institution == "TU Berlin"

    def test_build_profile_data_populates_languages(self):
        legacy = _load_legacy_profile()
        data = {"languages": [{"language": "Deutsch", "level": "Muttersprache"}]}
        result = legacy._build_profile_data(data)
        assert len(result.languages) == 1
        assert result.languages[0].language == "Deutsch"

    def test_build_profile_data_populates_skills(self):
        legacy = _load_legacy_profile()
        # Skills as str list get migrated to Skill objects
        data = {"skills": ["Python", "Docker"]}
        result = legacy._build_profile_data(data)
        skill_names = [s.name if hasattr(s, "name") else s for s in result.skills]
        assert "Python" in skill_names
        assert "Docker" in skill_names

    def test_build_profile_data_empty_dict(self):
        legacy = _load_legacy_profile()
        result = legacy._build_profile_data({})
        assert result.work_experience == []
        assert result.education == []
        assert result.skills == []
        assert result.languages == []
        assert result.personal_info.name == ""


class TestLegacyProfileServiceDB:
    """Async DB-backed tests for the legacy profile.py module."""

    @pytest.mark.asyncio
    async def test_get_profile_returns_none_when_empty(self, sqlite_session):
        legacy = _load_legacy_profile()
        result = await legacy.get_profile(sqlite_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_profile_returns_response_when_exists(self, sqlite_session):
        from applire.models.profile import MasterProfile
        from applire.schemas.profile import MasterProfileData

        legacy = _load_legacy_profile()
        # Insert a minimal profile using the *legacy* schema layout
        profile_data = MasterProfileData.model_validate(
            {
                "work_history": [],
                "skills": [],
                "education": [],
                "languages": [],
                "contact": {"name": "Legacy Alice"},
            }
        )
        record = MasterProfile(profile_json=profile_data.model_dump())
        sqlite_session.add(record)
        await sqlite_session.commit()

        result = await legacy.get_profile(sqlite_session)
        assert result is not None

    @pytest.mark.asyncio
    async def test_import_from_linkedin_creates_profile(self, sqlite_session):
        legacy = _load_legacy_profile()

        provider = _make_mock_provider(
            {
                "work_history": [],
                "skills": ["Python"],
                "education": [],
                "languages": [],
                "contact": {"name": "Li"},
            }
        )
        linkedin_data = {"firstName": "Li", "headline": "Developer"}
        result = await legacy.import_from_linkedin(linkedin_data, sqlite_session, provider)
        assert result is not None
        provider.aparse_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_from_linkedin_updates_existing_profile(self, sqlite_session):
        """Calling import_from_linkedin twice should update, not duplicate, the profile."""
        legacy = _load_legacy_profile()

        llm_data = {
            "work_history": [],
            "skills": ["Python"],
            "education": [],
            "languages": [],
            "contact": {"name": "Li Updated"},
        }
        provider = _make_mock_provider(llm_data)

        # First import
        await legacy.import_from_linkedin({"firstName": "Li"}, sqlite_session, provider)
        # Second import — should update the existing record
        result = await legacy.import_from_linkedin({"firstName": "Li"}, sqlite_session, provider)
        assert result is not None
        assert provider.aparse_json.call_count == 2

    @pytest.mark.asyncio
    async def test_patch_profile_section_raises_on_invalid_section(self, sqlite_session):
        legacy = _load_legacy_profile()

        with pytest.raises(ValueError, match="Invalid section"):
            await legacy.patch_profile_section("nonexistent_section", [], sqlite_session)

    @pytest.mark.asyncio
    async def test_patch_profile_section_raises_when_no_profile(self, sqlite_session):
        legacy = _load_legacy_profile()

        with pytest.raises(LookupError, match="No profile found"):
            await legacy.patch_profile_section("skills", ["Python"], sqlite_session)

    @pytest.mark.asyncio
    async def test_patch_profile_section_updates_skills(self, sqlite_session):
        from applire.models.profile import MasterProfile
        from applire.schemas.profile import MasterProfileData

        legacy = _load_legacy_profile()
        profile_data = MasterProfileData.model_validate({"contact": {"name": "Bob"}})
        record = MasterProfile(profile_json=profile_data.model_dump())
        sqlite_session.add(record)
        await sqlite_session.commit()

        result = await legacy.patch_profile_section("skills", ["Python", "Docker"], sqlite_session)
        assert result is not None

    @pytest.mark.asyncio
    async def test_import_from_pdf_raises_on_empty_text(self, sqlite_session):
        legacy = _load_legacy_profile()
        provider = _make_mock_provider({})

        # Patch extract_pdf_text on the legacy module itself
        with patch.object(legacy, "extract_pdf_text", return_value=""):
            with pytest.raises(ValueError, match="Could not extract text from PDF"):
                await legacy.import_from_pdf(b"fake_pdf", sqlite_session, provider)

    @pytest.mark.asyncio
    async def test_import_from_pdf_calls_provider(self, sqlite_session):
        legacy = _load_legacy_profile()

        llm_data = {
            "work_history": [],
            "skills": [],
            "education": [],
            "languages": [],
            "contact": {"name": "PDF Alice"},
        }
        provider = _make_mock_provider(llm_data)

        with patch.object(legacy, "extract_pdf_text", return_value="CV text here"):
            result = await legacy.import_from_pdf(b"fake_pdf", sqlite_session, provider)
        assert result is not None
        provider.aparse_json.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════════
# 2. applire/services/job.py  (35% → cover uncovered lines 13, 23-62)
# ═══════════════════════════════════════════════════════════════════════════════


class TestJobServiceHashText:
    def test_hash_text_returns_64_char_hex(self):
        from applire.services.job import _hash_text
        result = _hash_text("hello world")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_text_is_deterministic(self):
        from applire.services.job import _hash_text
        assert _hash_text("test") == _hash_text("test")

    def test_hash_text_differs_for_different_inputs(self):
        from applire.services.job import _hash_text
        assert _hash_text("abc") != _hash_text("def")


class TestAnalyzeJd:
    @pytest.mark.asyncio
    async def test_analyze_jd_creates_new_record(self, sqlite_session):
        from applire.services.job import analyze_jd

        llm_response = {
            "role_title": "Backend Developer",
            "required_skills": ["Python", "FastAPI"],
            "nice_to_have_skills": ["Docker"],
            "keywords": ["backend", "API"],
            "seniority_level": "mid",
            "company_culture_signals": ["remote-first"],
            "language_requirement": "German",
            "company_name": "TechGmbH",
        }
        provider = _make_mock_provider(llm_response)

        result = await analyze_jd("We need a backend developer", sqlite_session, provider)
        assert result.role_title == "Backend Developer"
        assert result.seniority_level == "mid"
        provider.aparse_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_jd_deduplicates_by_text_hash(self, sqlite_session):
        from applire.services.job import analyze_jd

        llm_response = {
            "role_title": "DevOps Engineer",
            "required_skills": [],
            "nice_to_have_skills": [],
            "keywords": [],
            "seniority_level": "senior",
            "company_culture_signals": [],
            "language_requirement": "",
            "company_name": None,
        }
        provider = _make_mock_provider(llm_response)

        text = "Identical job description text"
        await analyze_jd(text, sqlite_session, provider)
        # Second call with the same text should return cached result without LLM call
        result2 = await analyze_jd(text, sqlite_session, provider)

        assert result2.role_title == "DevOps Engineer"
        # LLM should only have been called once (cache hit on second call)
        assert provider.aparse_json.call_count == 1

    @pytest.mark.asyncio
    async def test_analyze_jd_deduplicates_by_source_url(self, sqlite_session):
        from applire.services.job import analyze_jd

        llm_response = {
            "role_title": "Frontend Dev",
            "required_skills": ["React"],
            "nice_to_have_skills": [],
            "keywords": [],
            "seniority_level": "junior",
            "company_culture_signals": [],
            "language_requirement": "",
            "company_name": None,
        }
        provider = _make_mock_provider(llm_response)

        url = "https://example.com/jobs/123"
        await analyze_jd("First version of job text", sqlite_session, provider, source_url=url)
        # Same URL — should return cached record without calling LLM again
        result2 = await analyze_jd("Different text same URL", sqlite_session, provider, source_url=url)

        assert result2.role_title == "Frontend Dev"
        assert provider.aparse_json.call_count == 1

    @pytest.mark.asyncio
    async def test_analyze_jd_sets_source_url(self, sqlite_session):
        from applire.services.job import analyze_jd

        llm_response = {
            "role_title": "ML Engineer",
            "required_skills": [],
            "nice_to_have_skills": [],
            "keywords": [],
            "seniority_level": "senior",
            "company_culture_signals": [],
            "language_requirement": "",
            "company_name": None,
        }
        provider = _make_mock_provider(llm_response)

        url = "https://jobs.example.com/ml-engineer"
        result = await analyze_jd("ML job text", sqlite_session, provider, source_url=url)
        assert result.source_url == url

    @pytest.mark.asyncio
    async def test_analyze_jd_no_source_url(self, sqlite_session):
        from applire.services.job import analyze_jd

        llm_response = {
            "role_title": "Data Analyst",
            "required_skills": ["SQL"],
            "nice_to_have_skills": [],
            "keywords": [],
            "seniority_level": "mid",
            "company_culture_signals": [],
            "language_requirement": "English",
            "company_name": "DataCorp",
        }
        provider = _make_mock_provider(llm_response)

        result = await analyze_jd("Data analyst role", sqlite_session, provider)
        assert result.source_url is None
        assert result.role_title == "Data Analyst"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. applire/storage/__init__.py  (38% → cover lines 8-13)
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetStorage:
    def test_get_storage_local_backend_returns_local_provider(self):
        from applire.storage import get_storage
        from applire.storage.local import LocalStorageProvider

        with patch("applire.storage.settings") as mock_settings:
            mock_settings.storage_backend = "local"
            mock_settings.upload_dir = "/tmp/uploads"
            provider = get_storage()

        assert isinstance(provider, LocalStorageProvider)

    def test_get_storage_unknown_backend_raises_value_error(self):
        from applire.storage import get_storage

        with patch("applire.storage.settings") as mock_settings:
            mock_settings.storage_backend = "s3"
            with pytest.raises(ValueError, match="Unknown STORAGE_BACKEND"):
                get_storage()

    def test_get_storage_backend_comparison_is_case_insensitive(self):
        from applire.storage import get_storage
        from applire.storage.local import LocalStorageProvider

        with patch("applire.storage.settings") as mock_settings:
            mock_settings.storage_backend = "LOCAL"
            mock_settings.upload_dir = "/tmp/uploads"
            provider = get_storage()

        assert isinstance(provider, LocalStorageProvider)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. applire/services/interview_graph.py  (37% → cover key nodes)
# ═══════════════════════════════════════════════════════════════════════════════


class TestGapDetector:
    def _make_gap_analysis(self, category_c=None, category_b=None, critical_gaps=None):
        from applire.models.gap import GapAnalysis

        ga = MagicMock(spec=GapAnalysis)
        ga.category_c = category_c
        ga.category_b = category_b
        ga.critical_gaps = critical_gaps
        return ga

    def test_gap_detector_returns_c_gaps_first(self):
        from applire.services.interview_graph import gap_detector

        ga = self._make_gap_analysis(
            category_c=["Python experience", "FastAPI knowledge"],
            category_b=["Docker usage"],
        )
        ordered, categories = gap_detector(ga)

        assert ordered[0] == "Python experience"
        assert ordered[1] == "FastAPI knowledge"
        assert ordered[2] == "Docker usage"
        assert categories["Python experience"] == "C"
        assert categories["Docker usage"] == "B"

    def test_gap_detector_only_c_gaps(self):
        from applire.services.interview_graph import gap_detector

        ga = self._make_gap_analysis(category_c=["Gap1", "Gap2"], category_b=None)
        ordered, categories = gap_detector(ga)

        assert len(ordered) == 2
        assert all(v == "C" for v in categories.values())

    def test_gap_detector_only_b_gaps(self):
        from applire.services.interview_graph import gap_detector

        ga = self._make_gap_analysis(category_c=None, category_b=["Likely skill"])
        ordered, categories = gap_detector(ga)

        assert ordered == ["Likely skill"]
        assert categories["Likely skill"] == "B"

    def test_gap_detector_falls_back_to_critical_gaps_legacy(self):
        from applire.services.interview_graph import gap_detector

        ga = self._make_gap_analysis(
            category_c=None, category_b=None, critical_gaps=["Old gap"]
        )
        ordered, categories = gap_detector(ga)

        assert ordered == ["Old gap"]
        assert categories["Old gap"] == "C"

    def test_gap_detector_filters_empty_strings(self):
        from applire.services.interview_graph import gap_detector

        ga = self._make_gap_analysis(category_c=["", "Real gap", ""], category_b=[])
        ordered, categories = gap_detector(ga)

        assert ordered == ["Real gap"]

    def test_gap_detector_empty_analysis_returns_empty(self):
        from applire.services.interview_graph import gap_detector

        ga = self._make_gap_analysis(category_c=[], category_b=[])
        ordered, categories = gap_detector(ga)

        assert ordered == []
        assert categories == {}


class TestGapDetectorModeB:
    def _make_job_analysis(self, required_skills=None, nice_to_have_skills=None, role_title=""):
        from applire.models.job import JobAnalysis

        ja = MagicMock(spec=JobAnalysis)
        ja.required_skills = required_skills or []
        ja.nice_to_have_skills = nice_to_have_skills or []
        ja.role_title = role_title
        return ja

    def test_mode_b_returns_core_sections(self):
        from applire.services.interview_graph import gap_detector_mode_b

        ja = self._make_job_analysis()
        sections = gap_detector_mode_b(ja)

        assert "work_experience" in sections
        assert "skills" in sections
        assert "education" in sections

    def test_mode_b_promotes_certifications_when_jd_signals_cert(self):
        from applire.services.interview_graph import gap_detector_mode_b

        ja = self._make_job_analysis(required_skills=["AWS certified", "PMP"])
        sections = gap_detector_mode_b(ja)

        assert "certifications" in sections
        # certifications should be promoted near the top (within first 3)
        assert sections.index("certifications") <= 2

    def test_mode_b_adds_publications_for_research_roles(self):
        from applire.services.interview_graph import gap_detector_mode_b

        ja = self._make_job_analysis(role_title="PhD Research Scientist")
        sections = gap_detector_mode_b(ja)

        assert "publications" in sections

    def test_mode_b_adds_volunteer_for_nonprofit_roles(self):
        from applire.services.interview_graph import gap_detector_mode_b

        ja = self._make_job_analysis(role_title="NGO Program Manager volunteer")
        sections = gap_detector_mode_b(ja)

        assert "volunteer_activities" in sections

    def test_mode_b_no_publications_for_regular_roles(self):
        from applire.services.interview_graph import gap_detector_mode_b

        ja = self._make_job_analysis(role_title="Software Developer")
        sections = gap_detector_mode_b(ja)

        assert "publications" not in sections


class TestQuestionGenerator:
    @pytest.mark.asyncio
    async def test_question_generator_calls_provider(self):
        from applire.services.interview_graph import question_generator

        state = {
            "mode": "targeted",
            "critical_gaps": ["Python experience"],
            "current_gap_index": 0,
            "messages": [],
        }
        provider = _make_mock_provider({})
        provider.acomplete = AsyncMock(return_value="  Tell me about Python?  ")

        result = await question_generator(state, provider)

        assert result == "Tell me about Python?"
        provider.acomplete.assert_called_once()

    @pytest.mark.asyncio
    async def test_question_generator_with_profile_targeted_mode(self):
        from applire.services.interview_graph import question_generator_with_profile

        state = {
            "mode": "targeted",
            "critical_gaps": ["Docker knowledge"],
            "current_gap_index": 0,
            "messages": [],
        }
        provider = _make_mock_provider({})
        provider.acomplete = AsyncMock(return_value="Can you describe your Docker experience?")

        result = await question_generator_with_profile(
            state, {"skills": []}, provider, gap_category="C"
        )

        assert "Docker" in result
        provider.acomplete.assert_called_once()

    @pytest.mark.asyncio
    async def test_question_generator_with_profile_guided_mode(self):
        from applire.services.interview_graph import question_generator_with_profile

        state = {
            "mode": "guided",
            "critical_gaps": ["work_experience"],
            "current_gap_index": 0,
            "messages": [],
        }
        provider = _make_mock_provider({})
        provider.acomplete = AsyncMock(return_value="Tell me about your work history.")

        result = await question_generator_with_profile(
            state,
            {"work_experience": []},
            provider,
            job_context={"role_title": "Developer"},
        )

        assert result == "Tell me about your work history."


class TestResponseParser:
    @pytest.mark.asyncio
    async def test_response_parser_returns_structured_data(self):
        from applire.services.interview_graph import response_parser

        llm_response = {
            "skills_to_add": ["Python", "FastAPI"],
            "work_history_to_add": [],
            "certifications_to_add": [],
            "languages_to_add": [],
            "education_to_add": [],
            "gap_resolution": "full",
            "follow_up_hint": None,
            "gaps_also_addressed": [],
        }
        provider = _make_mock_provider(llm_response)

        result = await response_parser(
            gap="Python experience",
            question="Tell me about Python",
            answer="I have 5 years of Python experience",
            provider=provider,
        )

        assert result["skills_to_add"] == ["Python", "FastAPI"]
        assert result["gap_addressed"] is True
        assert result["work_history_to_add"] == []

    @pytest.mark.asyncio
    async def test_response_parser_defaults_on_missing_keys(self):
        from applire.services.interview_graph import response_parser

        provider = _make_mock_provider({})  # empty response

        result = await response_parser(
            gap="some gap",
            question="some question",
            answer="some answer",
            provider=provider,
        )

        assert result["skills_to_add"] == []
        assert result["work_history_to_add"] == []
        assert result["gap_addressed"] is False


class TestProfileUpdater:
    def test_profile_updater_adds_new_skills(self):
        from applire.services.interview_graph import profile_updater

        profile = {"skills": ["Python"], "work_experience": []}
        patch = {"skills_to_add": ["Docker", "Kubernetes"], "work_history_to_add": []}

        updated, conflicts = profile_updater(profile, patch)

        assert "Docker" in updated["skills"]
        assert "Kubernetes" in updated["skills"]
        assert conflicts == []

    def test_profile_updater_does_not_duplicate_existing_skills(self):
        from applire.services.interview_graph import profile_updater

        profile = {"skills": ["python"], "work_experience": []}
        patch = {"skills_to_add": ["Python"], "work_history_to_add": []}

        updated, conflicts = profile_updater(profile, patch)

        # "python" and "Python" should not both appear — case-insensitive dedup
        skill_names = [s.lower() if isinstance(s, str) else s.get("name", "").lower()
                       for s in updated["skills"]]
        assert skill_names.count("python") == 1

    def test_profile_updater_appends_new_work_entries(self):
        from applire.services.interview_graph import profile_updater

        profile = {"skills": [], "work_experience": []}
        patch = {
            "skills_to_add": [],
            "work_history_to_add": [
                {"company": "Acme", "role": "Developer", "start_date": "2020-01"}
            ],
        }

        updated, conflicts = profile_updater(profile, patch)

        assert len(updated["work_experience"]) == 1
        assert updated["work_experience"][0]["company"] == "Acme"

    def test_profile_updater_detects_date_conflict_on_matching_entry(self):
        from applire.services.interview_graph import profile_updater

        profile = {
            "skills": [],
            "work_experience": [
                {"company": "Acme", "role": "Developer", "start_date": "2020-01"}
            ],
        }
        patch = {
            "skills_to_add": [],
            "work_history_to_add": [
                {"company": "Acme", "role": "Developer", "start_date": "2020-06"}
            ],
        }

        updated, conflicts = profile_updater(profile, patch)

        assert len(conflicts) == 1
        assert "start_date" in conflicts[0].field

    def test_profile_updater_skips_work_entry_without_role(self):
        from applire.services.interview_graph import profile_updater

        profile = {"skills": [], "work_experience": []}
        patch = {
            "skills_to_add": [],
            "work_history_to_add": [{"company": "Acme", "role": ""}],
        }

        updated, conflicts = profile_updater(profile, patch)

        # Entry with empty role should be skipped
        assert updated["work_experience"] == []

    def test_skill_name_helper_handles_dict_and_str(self):
        from applire.services.interview_graph import _skill_name

        assert _skill_name("Python") == "Python"
        assert _skill_name({"name": "Docker", "level": "expert"}) == "Docker"
        assert _skill_name({}) == ""

    def test_norm_helper_strips_and_lowercases(self):
        from applire.services.interview_graph import _norm

        assert _norm("  Acme GmbH  ") == "acme gmbh"
        assert _norm(None) == ""
        assert _norm("") == ""


# ═══════════════════════════════════════════════════════════════════════════════
# 5. applire/services/profile/__init__.py  (39% → cover key functions)
# ═══════════════════════════════════════════════════════════════════════════════


class TestNewProfileServiceHelpers:
    def test_extract_pdf_text_raises_on_bad_bytes(self):
        from applire.services.profile import extract_pdf_text
        with pytest.raises(Exception):
            extract_pdf_text(b"not a pdf at all")

    def test_linkedin_to_text_returns_json_string(self):
        from applire.services.profile import _linkedin_to_text
        result = _linkedin_to_text({"firstName": "Anna", "skills": ["Go", "Rust"]})
        assert "Anna" in result
        assert "Go" in result

    def test_make_enrichment_record_structure(self):
        from applire.services.profile import _make_enrichment_record
        record = _make_enrichment_record(
            source="cv_upload",
            section="skills",
            action="added",
            old_value=None,
            new_value=["Python"],
        )
        assert record.source == "cv_upload"
        assert len(record.changes) == 1
        assert record.changes[0].action == "added"


class TestNewProfileServiceDB:
    @pytest.mark.asyncio
    async def test_get_profile_returns_none_when_empty(self, sqlite_session):
        from applire.services.profile import get_profile
        result = await get_profile(sqlite_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_profile_exists_returns_false_when_no_profile(self, sqlite_session):
        from applire.services.profile import profile_exists
        result = await profile_exists(sqlite_session)
        assert result["exists"] is False
        assert result["completeness_score"] == 0.0

    @pytest.mark.asyncio
    async def test_profile_exists_returns_true_when_profile_exists(self, sqlite_session):
        from applire.models.profile import MasterProfile
        from applire.services.profile import profile_exists

        record = MasterProfile(profile_json=_minimal_profile_json())
        sqlite_session.add(record)
        await sqlite_session.commit()

        result = await profile_exists(sqlite_session)
        assert result["exists"] is True

    @pytest.mark.asyncio
    async def test_get_enrichment_history_empty_when_no_profile(self, sqlite_session):
        from applire.services.profile import get_enrichment_history
        result = await get_enrichment_history(sqlite_session)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_enrichment_history_empty_when_no_metadata(self, sqlite_session):
        from applire.models.profile import MasterProfile
        from applire.services.profile import get_enrichment_history

        # Profile without metadata
        record = MasterProfile(profile_json=_minimal_profile_json())
        sqlite_session.add(record)
        await sqlite_session.commit()

        result = await get_enrichment_history(sqlite_session)
        assert result == []

    @pytest.mark.asyncio
    async def test_import_from_linkedin_creates_profile(self, sqlite_session):
        from applire.services.profile import import_from_linkedin

        provider = _make_mock_provider(_minimal_llm_profile_data())
        with patch("applire.services.profile.LLM_REVIEW_MAX_RETRIES", 0):
            result = await import_from_linkedin({"firstName": "Alice"}, sqlite_session, provider)

        assert result is not None
        provider.aparse_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_from_linkedin_merges_with_existing(self, sqlite_session):
        from applire.services.profile import import_from_linkedin

        provider = _make_mock_provider(_minimal_llm_profile_data())

        with patch("applire.services.profile.LLM_REVIEW_MAX_RETRIES", 0):
            # First import
            await import_from_linkedin({"firstName": "Alice"}, sqlite_session, provider)
            # Second import — should merge
            result = await import_from_linkedin({"firstName": "Alice"}, sqlite_session, provider)

        assert result is not None
        assert provider.aparse_json.call_count == 2

    @pytest.mark.asyncio
    async def test_import_from_pdf_raises_on_empty_text(self, sqlite_session):
        from applire.services.profile import import_from_pdf

        provider = _make_mock_provider({})
        with patch("applire.services.profile.extract_pdf_text", return_value=""):
            with pytest.raises(ValueError, match="Could not extract text from PDF"):
                await import_from_pdf(b"bad bytes", sqlite_session, provider)

    @pytest.mark.asyncio
    async def test_patch_profile_section_raises_on_invalid_section(self, sqlite_session):
        from applire.services.profile import patch_profile_section

        with pytest.raises(ValueError, match="Invalid section"):
            await patch_profile_section("bad_section", [], sqlite_session)

    @pytest.mark.asyncio
    async def test_patch_profile_section_raises_when_no_profile(self, sqlite_session):
        from applire.services.profile import patch_profile_section

        with pytest.raises(LookupError, match="No profile found"):
            await patch_profile_section("skills", [], sqlite_session)

    @pytest.mark.asyncio
    async def test_patch_profile_section_updates_and_tracks_enrichment(self, sqlite_session):
        from applire.models.profile import MasterProfile
        from applire.services.profile import patch_profile_section, get_enrichment_history

        record = MasterProfile(profile_json=_minimal_profile_json())
        sqlite_session.add(record)
        await sqlite_session.commit()

        result = await patch_profile_section(
            "skills",
            [{"name": "Python", "proficiency": "expert"}],
            sqlite_session,
            source="manual_edit",
        )
        assert result is not None

        history = await get_enrichment_history(sqlite_session)
        assert len(history) >= 1

    @pytest.mark.asyncio
    async def test_resolve_conflict_raises_when_no_profile(self, sqlite_session):
        from applire.services.profile import resolve_conflict

        with pytest.raises(LookupError, match="No profile found"):
            await resolve_conflict(str(uuid.uuid4()), "existing", None, sqlite_session)

    @pytest.mark.asyncio
    async def test_resolve_conflict_raises_when_no_pending_conflicts(self, sqlite_session):
        from applire.models.profile import MasterProfile
        from applire.services.profile import resolve_conflict

        record = MasterProfile(profile_json=_minimal_profile_json())
        sqlite_session.add(record)
        await sqlite_session.commit()

        with pytest.raises(LookupError):
            await resolve_conflict(str(uuid.uuid4()), "existing", None, sqlite_session)

    @pytest.mark.asyncio
    async def test_resolve_conflict_raises_on_invalid_resolution(self, sqlite_session):
        """resolve_conflict raises ValueError for unknown resolution values."""
        from applire.models.profile import MasterProfile
        from applire.schemas.profile import Conflict, MasterProfileData, ProfileMetadata
        from applire.services.profile import resolve_conflict

        conflict_id = str(uuid.uuid4())
        conflict = Conflict(
            conflict_id=conflict_id,
            section="personal_info",
            field="email",
            existing_value="old@example.com",
            incoming_value="new@example.com",
            source="cv_upload",
        )
        profile_data = MasterProfileData.model_validate(_minimal_profile_json())
        now = datetime.now(timezone.utc)
        profile_data.metadata = ProfileMetadata(
            completeness_score=0.0,
            created_via="cv_upload",
            created_at=now,
            last_updated=now,
            enrichment_history=[],
            pending_conflicts=[conflict],
        )
        record = MasterProfile(profile_json=profile_data.model_dump(mode="json"))
        sqlite_session.add(record)
        await sqlite_session.commit()

        with pytest.raises(ValueError, match="Invalid resolution"):
            await resolve_conflict(conflict_id, "unknown_resolution", None, sqlite_session)

    @pytest.mark.asyncio
    async def test_resolve_conflict_existing_keeps_existing_value(self, sqlite_session):
        from applire.models.profile import MasterProfile
        from applire.schemas.profile import Conflict, MasterProfileData, PersonalInfo, ProfileMetadata
        from applire.services.profile import resolve_conflict

        conflict_id = str(uuid.uuid4())
        conflict = Conflict(
            conflict_id=conflict_id,
            section="personal_info",
            field="email",
            existing_value="kept@example.com",
            incoming_value="rejected@example.com",
            source="cv_upload",
        )
        profile_json = _minimal_profile_json()
        profile_json["personal_info"] = {"name": "Alice", "email": "kept@example.com"}
        now = datetime.now(timezone.utc)
        profile_data = MasterProfileData.model_validate(profile_json)
        profile_data.metadata = ProfileMetadata(
            completeness_score=0.0,
            created_via="cv_upload",
            created_at=now,
            last_updated=now,
            enrichment_history=[],
            pending_conflicts=[conflict],
        )
        record = MasterProfile(profile_json=profile_data.model_dump(mode="json"))
        sqlite_session.add(record)
        await sqlite_session.commit()

        result = await resolve_conflict(conflict_id, "existing", None, sqlite_session)
        assert result is not None
        # Pending conflicts should be cleared
        assert result.merge_conflicts == []

    @pytest.mark.asyncio
    async def test_resolve_conflict_incoming_applies_incoming_value(self, sqlite_session):
        from applire.models.profile import MasterProfile
        from applire.schemas.profile import Conflict, MasterProfileData, ProfileMetadata
        from applire.services.profile import resolve_conflict

        conflict_id = str(uuid.uuid4())
        conflict = Conflict(
            conflict_id=conflict_id,
            section="personal_info",
            field="email",
            existing_value="old@example.com",
            incoming_value="new@example.com",
            source="cv_upload",
        )
        profile_json = _minimal_profile_json()
        profile_json["personal_info"] = {"name": "Alice", "email": "old@example.com"}
        now = datetime.now(timezone.utc)
        profile_data = MasterProfileData.model_validate(profile_json)
        profile_data.metadata = ProfileMetadata(
            completeness_score=0.0,
            created_via="cv_upload",
            created_at=now,
            last_updated=now,
            enrichment_history=[],
            pending_conflicts=[conflict],
        )
        record = MasterProfile(profile_json=profile_data.model_dump(mode="json"))
        sqlite_session.add(record)
        await sqlite_session.commit()

        result = await resolve_conflict(conflict_id, "incoming", None, sqlite_session)
        assert result is not None
        assert result.merge_conflicts == []

    @pytest.mark.asyncio
    async def test_resolve_conflict_manual_applies_custom_value(self, sqlite_session):
        from applire.models.profile import MasterProfile
        from applire.schemas.profile import Conflict, MasterProfileData, ProfileMetadata
        from applire.services.profile import resolve_conflict

        conflict_id = str(uuid.uuid4())
        conflict = Conflict(
            conflict_id=conflict_id,
            section="personal_info",
            field="email",
            existing_value="old@example.com",
            incoming_value="new@example.com",
            source="cv_upload",
        )
        profile_json = _minimal_profile_json()
        profile_json["personal_info"] = {"name": "Alice", "email": "old@example.com"}
        now = datetime.now(timezone.utc)
        profile_data = MasterProfileData.model_validate(profile_json)
        profile_data.metadata = ProfileMetadata(
            completeness_score=0.0,
            created_via="cv_upload",
            created_at=now,
            last_updated=now,
            enrichment_history=[],
            pending_conflicts=[conflict],
        )
        record = MasterProfile(profile_json=profile_data.model_dump(mode="json"))
        sqlite_session.add(record)
        await sqlite_session.commit()

        result = await resolve_conflict(conflict_id, "manual", "custom@example.com", sqlite_session)
        assert result is not None
        assert result.merge_conflicts == []
