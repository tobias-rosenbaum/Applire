"""Unit tests for services/job.py — analyze_jd validation.

Covers:
  - LLM returns null role_title (cookie wall / non-JD content) → ValueError raised
  - LLM returns null seniority_level → stored as empty string, no DB crash
  - LLM returns valid JD → stored correctly

No Docker, no real LLM. Uses SQLite in-memory + stub LLM provider.
"""

import uuid
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from applire.services.job import analyze_jd


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def db():
    """In-memory SQLite session with all models registered."""
    from applire.db.session import Base  # noqa: F401
    import applire.models.user          # noqa: F401
    import applire.models.job           # noqa: F401
    import applire.models.profile       # noqa: F401
    import applire.models.gap           # noqa: F401
    import applire.models.cv            # noqa: F401
    import applire.models.session       # noqa: F401
    import applire.models.flow          # noqa: F401
    import applire.models.uploads       # noqa: F401
    import applire.models.application   # noqa: F401
    import applire.models.color_profile # noqa: F401
    import applire.models.company       # noqa: F401
    import applire.models.user_settings # noqa: F401
    import applire.models.cover_letter  # noqa: F401

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()


def _make_provider(response: dict):
    """Stub LLM provider that returns a fixed dict from aparse_json."""
    provider = AsyncMock()
    provider.aparse_json = AsyncMock(return_value=response)
    return provider


_VALID_JD_RESPONSE = {
    "company_name": "BioNTech SE",
    "role_title": "Director QC Processes",
    "required_skills": ["GMP", "LIMS"],
    "nice_to_have_skills": ["SAP"],
    "keywords": ["QC", "pharmaceutical"],
    "seniority_level": "Director",
    "company_culture_signals": ["international"],
    "language_requirement": "German (C1)",
    "berufsbild_code": None,
    "berufsbild_label": None,
}


# ---------------------------------------------------------------------------
# Null role_title guard
# ---------------------------------------------------------------------------


class TestNullRoleTitleGuard:
    """
    When the scraped content is a cookie wall or other non-JD page, the LLM
    returns null for role_title. The service must raise ValueError before
    attempting the DB insert so the router can surface a 422 instead of a 500.
    """

    @pytest.mark.asyncio
    async def test_null_role_title_raises_value_error(self, db):
        response = {**_VALID_JD_RESPONSE, "role_title": None}
        provider = _make_provider(response)
        with pytest.raises(ValueError, match="job description"):
            await analyze_jd("cookie consent page content", db, provider)

    @pytest.mark.asyncio
    async def test_empty_string_role_title_raises_value_error(self, db):
        """Empty string after strip should also be rejected."""
        response = {**_VALID_JD_RESPONSE, "role_title": "   "}
        provider = _make_provider(response)
        with pytest.raises(ValueError, match="job description"):
            await analyze_jd("some scraped text", db, provider)

    @pytest.mark.asyncio
    async def test_valid_role_title_does_not_raise(self, db):
        provider = _make_provider(_VALID_JD_RESPONSE)
        result = await analyze_jd("full job description text", db, provider)
        assert result.role_title == "Director QC Processes"


# ---------------------------------------------------------------------------
# Null seniority_level handling
# ---------------------------------------------------------------------------


class TestNullSeniorityLevel:
    """
    The LLM sometimes returns null for seniority_level (e.g. when it cannot
    determine level from context). The service must not crash; null should be
    stored as an empty string to satisfy the NOT NULL DB constraint.
    """

    @pytest.mark.asyncio
    async def test_null_seniority_level_stored_as_empty_string(self, db):
        response = {**_VALID_JD_RESPONSE, "seniority_level": None}
        provider = _make_provider(response)
        result = await analyze_jd("full job description text", db, provider)
        assert result.seniority_level == ""

    @pytest.mark.asyncio
    async def test_valid_seniority_level_stored_correctly(self, db):
        provider = _make_provider(_VALID_JD_RESPONSE)
        result = await analyze_jd("full job description text", db, provider)
        assert result.seniority_level == "Director"
