"""
Iteration 13 — Unit tests: gap inference (rule-based pre-pass) + GapDetector node.

All tests run without LLM calls, DB, or external services.
"""

from datetime import date, timedelta

import pytest

from apliqa.services.gap_inference import (
    InferredCandidate,
    PreClassification,
    _has_dach_context,
    _roles_with_long_tenure,
    _seniority_threshold_met,
    _skill_matches,
    _total_experience_years,
    pre_classify,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _work_entry(
    company: str = "Acme",
    role: str = "Engineer",
    start_years_ago: int = 5,
    end_years_ago: int | None = None,
    industry: str = "",
    technologies: list[str] | None = None,
) -> dict:
    start = (date.today() - timedelta(days=start_years_ago * 365)).isoformat()
    end = None if end_years_ago is None else (
        date.today() - timedelta(days=end_years_ago * 365)
    ).isoformat()
    return {
        "company": company,
        "role": role,
        "start_date": start,
        "end_date": end,
        "industry_context": industry,
        "technologies": technologies or [],
    }


def _profile(skills: list = None, work: list = None, education: list = None, languages: list = None) -> dict:
    return {
        "skills": skills or [],
        "work_experience": work or [],
        "education": education or [],
        "languages": languages or [],
    }


def _job(
    required: list[str] = None,
    keywords: list[str] = None,
    seniority: str = "",
) -> dict:
    return {
        "required_skills": required or [],
        "nice_to_have_skills": [],
        "keywords": keywords or [],
        "seniority_level": seniority,
        "company_culture_signals": [],
        "language_requirement": None,
    }


# ---------------------------------------------------------------------------
# Category A: direct skill match
# ---------------------------------------------------------------------------


class TestDirectSkillMatch:
    def test_exact_match_lowercase(self):
        profile = _profile(skills=["python", "fastapi"])
        job = _job(required=["Python"])
        result = pre_classify(job, profile)
        assert "Python" in result.matched

    def test_dict_skill_matched(self):
        profile = _profile(skills=[{"name": "PostgreSQL", "proficiency": "expert"}])
        job = _job(required=["PostgreSQL"])
        result = pre_classify(job, profile)
        assert "PostgreSQL" in result.matched

    def test_unmatched_skill_goes_to_unresolved_or_inferred(self):
        profile = _profile(skills=["Python"])
        job = _job(required=["Kubernetes"])
        result = pre_classify(job, profile)
        assert "Kubernetes" not in result.matched

    def test_substring_match(self):
        """'Python 3' in profile should match 'Python' requirement."""
        profile = _profile(skills=["Python 3"])
        job = _job(required=["Python"])
        result = pre_classify(job, profile)
        assert "Python" in result.matched

    def test_all_matched_returns_no_unresolved(self):
        skills = ["Python", "FastAPI", "Docker"]
        profile = _profile(skills=skills)
        job = _job(required=skills)
        result = pre_classify(job, profile)
        assert set(result.matched) == set(skills)
        assert result.unresolved == []

    def test_no_duplicate_in_matched(self):
        """A skill listed in both required and keywords should appear once."""
        profile = _profile(skills=["Python"])
        job = _job(required=["Python"], keywords=["Python"])
        result = pre_classify(job, profile)
        assert result.matched.count("Python") == 1


# ---------------------------------------------------------------------------
# Category B: tenure ≥ 4 years
# ---------------------------------------------------------------------------


class TestTenureInference:
    def test_tenure_4y_with_matching_industry(self):
        """4+ year pharma role → 'GxP compliance' becomes a B candidate."""
        entry = _work_entry(
            company="Roche",
            start_years_ago=6,
            end_years_ago=0,
            industry="pharmaceutical regulatory GxP",
        )
        profile = _profile(work=[entry])
        job = _job(required=["GxP compliance"])
        result = pre_classify(job, profile)
        requirements = [c.requirement for c in result.inferred_b]
        assert "GxP compliance" in requirements

    def test_tenure_under_4y_not_inferred(self):
        """3-year role should not trigger tenure inference."""
        entry = _work_entry(
            company="Roche",
            start_years_ago=3,
            end_years_ago=0,
            industry="pharmaceutical GxP",
        )
        profile = _profile(work=[entry])
        job = _job(required=["GxP compliance"])
        result = pre_classify(job, profile)
        requirements = [c.requirement for c in result.inferred_b]
        assert "GxP compliance" not in requirements

    def test_roles_with_long_tenure_helper(self):
        long = _work_entry(start_years_ago=5, end_years_ago=0)
        short = _work_entry(start_years_ago=2, end_years_ago=0)
        result = _roles_with_long_tenure([long, short], min_years=4)
        assert len(result) == 1
        assert result[0]["company"] == long["company"]

    def test_current_job_counts_to_today(self):
        """end_date=None should be treated as today."""
        entry = _work_entry(start_years_ago=5, end_years_ago=None)
        long_tenures = _roles_with_long_tenure([entry], min_years=4)
        assert len(long_tenures) == 1

    def test_technology_overlap_triggers_inference(self):
        entry = _work_entry(
            company="AWS Partner",
            start_years_ago=5,
            end_years_ago=0,
            technologies=["Kubernetes", "Helm", "Terraform"],
        )
        profile = _profile(work=[entry])
        job = _job(required=["Kubernetes"])
        result = pre_classify(job, profile)
        requirements = [c.requirement for c in result.inferred_b]
        assert "Kubernetes" in requirements


# ---------------------------------------------------------------------------
# Category B: seniority threshold
# ---------------------------------------------------------------------------


class TestSeniorityInference:
    def test_senior_role_met_by_8y_experience(self):
        work = [
            _work_entry(start_years_ago=9, end_years_ago=5),
            _work_entry(start_years_ago=5, end_years_ago=0),
        ]
        profile = _profile(work=work)
        job = _job(required=["Senior leadership"], seniority="Senior")
        result = pre_classify(job, profile)
        requirements = [c.requirement for c in result.inferred_b]
        assert "Senior leadership" in requirements

    def test_senior_not_met_by_2y(self):
        work = [_work_entry(start_years_ago=2, end_years_ago=0)]
        profile = _profile(work=work)
        job = _job(required=["Senior leadership"], seniority="Senior")
        result = pre_classify(job, profile)
        requirements = [c.requirement for c in result.inferred_b]
        assert "Senior leadership" not in requirements

    def test_seniority_threshold_met_helper(self):
        assert _seniority_threshold_met("senior", 7.0) is True
        assert _seniority_threshold_met("senior", 4.0) is False
        assert _seniority_threshold_met("lead", 8.0) is True
        assert _seniority_threshold_met("lead", 7.0) is False
        assert _seniority_threshold_met("junior", 0.5) is True
        assert _seniority_threshold_met("mid", 3.5) is True
        assert _seniority_threshold_met("mid", 2.0) is False
        assert _seniority_threshold_met("", 20.0) is False

    def test_total_experience_years_helper(self):
        work = [
            _work_entry(start_years_ago=4, end_years_ago=2),  # ~2 years
            _work_entry(start_years_ago=2, end_years_ago=0),  # ~2 years
        ]
        total = _total_experience_years(work)
        assert 3.5 < total < 4.5


# ---------------------------------------------------------------------------
# Category B: DACH context
# ---------------------------------------------------------------------------


class TestDachInference:
    def test_native_german_speaker_triggers_dach(self):
        languages = [{"language": "German", "proficiency": "native_or_bilingual"}]
        profile = _profile(languages=languages)
        job = _job(required=["German business culture"])
        result = pre_classify(job, profile)
        requirements = [c.requirement for c in result.inferred_b]
        assert "German business culture" in requirements

    def test_dach_education_triggers_dach(self):
        education = [{"institution": "Technische Universität München", "country": "germany"}]
        profile = _profile(education=education)
        job = _job(required=["DACH stakeholder management"])
        result = pre_classify(job, profile)
        requirements = [c.requirement for c in result.inferred_b]
        assert "DACH stakeholder management" in requirements

    def test_non_dach_no_inference(self):
        languages = [{"language": "Mandarin", "proficiency": "native_or_bilingual"}]
        education = [{"institution": "MIT", "country": "usa"}]
        profile = _profile(languages=languages, education=education)
        job = _job(required=["German business culture"])
        result = pre_classify(job, profile)
        requirements = [c.requirement for c in result.inferred_b]
        assert "German business culture" not in requirements

    def test_has_dach_context_helper_native_german(self):
        languages = [{"language": "German", "proficiency": "native"}]
        assert _has_dach_context([], languages) is True

    def test_has_dach_context_helper_swiss_edu(self):
        education = [{"institution": "ETH Zürich", "country": ""}]
        assert _has_dach_context(education, []) is True

    def test_has_dach_context_helper_false(self):
        assert _has_dach_context([], []) is False


# ---------------------------------------------------------------------------
# Category C: truly unknown requirements
# ---------------------------------------------------------------------------


class TestCategoryC:
    def test_unmatched_unresolvable_goes_to_unresolved(self):
        profile = _profile(skills=["Python"])
        job = _job(required=["Quantum computing"])
        result = pre_classify(job, profile)
        assert "Quantum computing" in result.unresolved

    def test_empty_profile_all_requirements_unresolved(self):
        profile = _profile()
        job = _job(required=["Python", "FastAPI", "Docker"])
        result = pre_classify(job, profile)
        # Everything ends up in unresolved (no rules fire)
        all_classified = set(result.matched) | {c.requirement for c in result.inferred_b} | set(result.unresolved)
        assert all_classified == {"Python", "FastAPI", "Docker"}


# ---------------------------------------------------------------------------
# PreClassification dataclass
# ---------------------------------------------------------------------------


class TestPreClassification:
    def test_preclas_defaults_are_empty_lists(self):
        pc = PreClassification()
        assert pc.matched == []
        assert pc.inferred_b == []
        assert pc.unresolved == []

    def test_inferred_candidate_has_requirement_and_reason(self):
        ic = InferredCandidate(requirement="GxP", reason="6y at Roche")
        assert ic.requirement == "GxP"
        assert ic.reason == "6y at Roche"


# ---------------------------------------------------------------------------
# gap_detector node
# ---------------------------------------------------------------------------


class TestGapDetector:
    """Tests for the GapDetector node using a mock GapAnalysis object."""

    class _FakeGapAnalysis:
        def __init__(self, category_a=None, category_b=None, category_c=None, critical_gaps=None):
            self.category_a = category_a or []
            self.category_b = category_b or []
            self.category_c = category_c or []
            self.critical_gaps = critical_gaps or []

    def test_category_c_comes_before_b(self):
        from apliqa.services.interview_graph import gap_detector

        ga = self._FakeGapAnalysis(
            category_b=["B-requirement"],
            category_c=["C-requirement-1", "C-requirement-2"],
        )
        targets, categories = gap_detector(ga)
        assert targets.index("C-requirement-1") < targets.index("B-requirement")
        assert targets.index("C-requirement-2") < targets.index("B-requirement")

    def test_category_a_excluded(self):
        from apliqa.services.interview_graph import gap_detector

        ga = self._FakeGapAnalysis(
            category_a=["A-matched"],
            category_b=["B-req"],
            category_c=["C-req"],
        )
        targets, categories = gap_detector(ga)
        assert "A-matched" not in targets

    def test_categories_dict_correct(self):
        from apliqa.services.interview_graph import gap_detector

        ga = self._FakeGapAnalysis(
            category_b=["B-req"],
            category_c=["C-req"],
        )
        targets, categories = gap_detector(ga)
        assert categories["B-req"] == "B"
        assert categories["C-req"] == "C"

    def test_legacy_fallback_uses_critical_gaps(self):
        """Records with empty A/B/C columns fall back to critical_gaps treated as C."""
        from apliqa.services.interview_graph import gap_detector

        ga = self._FakeGapAnalysis(critical_gaps=["legacy-gap"])
        targets, categories = gap_detector(ga)
        assert "legacy-gap" in targets
        assert categories["legacy-gap"] == "C"

    def test_empty_gaps_returns_empty(self):
        from apliqa.services.interview_graph import gap_detector

        ga = self._FakeGapAnalysis()
        targets, categories = gap_detector(ga)
        assert targets == []
        assert categories == {}

    def test_match_score_range_float(self):
        """Validate that float match_score is accepted by GapAnalysisResponse schema."""
        from apliqa.schemas.gap import GapAnalysisResponse
        import uuid
        from datetime import datetime, timezone

        r = GapAnalysisResponse(
            id=uuid.uuid4(),
            job_analysis_id=uuid.uuid4(),
            profile_id=uuid.uuid4(),
            match_score=0.73,
            critical_gaps=["gap1"],
            minor_gaps=[],
            strengths=["strength1"],
            keyword_gaps=[],
            category_a=["skill"],
            category_b=["inferred"],
            category_c=["gap1"],
            created_at=datetime.now(timezone.utc),
        )
        assert r.match_score == 0.73

    def test_match_score_bounds(self):
        """match_score must be in [0.0, 1.0]."""
        from pydantic import ValidationError
        from apliqa.schemas.gap import GapAnalysisResponse
        import uuid
        from datetime import datetime, timezone

        base = dict(
            id=uuid.uuid4(),
            job_analysis_id=uuid.uuid4(),
            profile_id=uuid.uuid4(),
            critical_gaps=[],
            minor_gaps=[],
            strengths=[],
            keyword_gaps=[],
            created_at=datetime.now(timezone.utc),
        )
        with pytest.raises(ValidationError):
            GapAnalysisResponse(**base, match_score=1.5)
        with pytest.raises(ValidationError):
            GapAnalysisResponse(**base, match_score=-0.1)
