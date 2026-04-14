"""
Sprint 25 — Cover Letter Generation (unit tests)
No Docker, no LLM, no external services.

Run:
    pytest tests/unit/test_cover_letter.py -v
"""
import sys
from pathlib import Path

import pytest

_backend = Path(__file__).parent.parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


# ---------------------------------------------------------------------------
# Task 2 — TTL constants
# ---------------------------------------------------------------------------

def test_generated_documents_ttl_default():
    from applire.constants import GENERATED_DOCUMENTS_TTL_DAYS
    assert GENERATED_DOCUMENTS_TTL_DAYS == 90


def test_interview_session_ttl_default():
    from applire.constants import INTERVIEW_SESSION_TTL_DAYS
    assert INTERVIEW_SESSION_TTL_DAYS == 30


def test_upload_ttl_default():
    from applire.constants import UPLOAD_TTL_DAYS
    assert UPLOAD_TTL_DAYS == 7


def test_profile_inactivity_ttl_default():
    from applire.constants import PROFILE_INACTIVITY_TTL_DAYS
    assert PROFILE_INACTIVITY_TTL_DAYS == 730


# ---------------------------------------------------------------------------
# Task 3 — GeneratedCoverLetter model
# ---------------------------------------------------------------------------

import uuid
from datetime import datetime, timedelta, timezone

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def db():
    """In-memory SQLite session with all models registered."""
    from applire.db.session import Base
    import applire.models.user
    import applire.models.job
    import applire.models.profile
    import applire.models.gap
    import applire.models.cv
    import applire.models.cover_letter
    import applire.models.session
    import applire.models.application
    import applire.models.flow
    import applire.models.uploads

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_cover_letter_model_creates_with_defaults(db):
    from applire.models.cover_letter import GeneratedCoverLetter, CoverLetterStatus

    cl = GeneratedCoverLetter(
        job_analysis_id=uuid.uuid4(),
        profile_id=uuid.uuid4(),
        template="classic_german",
        letter_data={},
        pre_gen_inputs={},
    )
    db.add(cl)
    await db.commit()
    await db.refresh(cl)

    assert cl.id is not None
    assert cl.status == CoverLetterStatus.pending.value
    # SQLite returns offset-naive datetimes; strip tz for comparison
    expires = cl.expires_at.replace(tzinfo=None) if cl.expires_at.tzinfo else cl.expires_at
    assert expires > datetime.now()
    assert cl.deleted_at is None


@pytest.mark.asyncio
async def test_cover_letter_expires_at_is_90_days_out(db):
    from applire.models.cover_letter import GeneratedCoverLetter

    cl = GeneratedCoverLetter(
        job_analysis_id=uuid.uuid4(),
        profile_id=uuid.uuid4(),
        template="executive",
        letter_data={},
        pre_gen_inputs={},
    )
    db.add(cl)
    await db.commit()
    await db.refresh(cl)

    # SQLite returns offset-naive datetimes; strip tz for comparison
    expires = cl.expires_at.replace(tzinfo=None) if cl.expires_at.tzinfo else cl.expires_at
    delta = expires - datetime.now()
    assert 88 < delta.days <= 91


# ---------------------------------------------------------------------------
# Task 4 — FlowSession cover letter FK
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_flow_session_has_cover_letter_fk(db):
    from applire.models.flow import FlowSession
    import sqlalchemy as sa
    from applire.db.session import Base

    inspector = sa.inspect(Base.metadata.tables["flow_sessions"])
    col_names = [c.name for c in inspector.columns]
    assert "generated_cover_letter_id" in col_names


# ---------------------------------------------------------------------------
# Task 5 — Pydantic schemas
# ---------------------------------------------------------------------------

def test_cover_letter_generate_request_validates_tone():
    from applire.schemas.cover_letter import CoverLetterGenerateRequest
    req = CoverLetterGenerateRequest(job_id=uuid.uuid4(), tone="formal")
    assert req.tone == "formal"


def test_cover_letter_generate_request_rejects_invalid_tone():
    from pydantic import ValidationError
    from applire.schemas.cover_letter import CoverLetterGenerateRequest
    with pytest.raises(ValidationError):
        CoverLetterGenerateRequest(job_id=uuid.uuid4(), tone="aggressive")


def test_flow_state_response_has_cover_letter_summary_field():
    from applire.schemas.flow import FlowStateResponse
    fields = FlowStateResponse.model_fields
    assert "cover_letter_summary" in fields


# ---------------------------------------------------------------------------
# Task 6 — Recipient extraction
# ---------------------------------------------------------------------------

def test_extract_recipient_finds_anrede_pattern():
    from applire.utils.recipient_extraction import extract_recipient_from_jd
    jd = "Bitte richten Sie Ihre Bewerbung an Dr. Sarah Müller, HR-Abteilung."
    result = extract_recipient_from_jd(jd)
    assert result["name"] == "Dr. Sarah Müller"


def test_extract_recipient_finds_english_pattern():
    from applire.utils.recipient_extraction import extract_recipient_from_jd
    jd = "Please address your application to Ms. Anna Schmidt, Talent Acquisition."
    result = extract_recipient_from_jd(jd)
    assert result["name"] == "Ms. Anna Schmidt"


def test_extract_recipient_returns_none_when_not_found():
    from applire.utils.recipient_extraction import extract_recipient_from_jd
    result = extract_recipient_from_jd("We are looking for a senior engineer.")
    assert result["name"] is None


# ---------------------------------------------------------------------------
# Task 7 — LLM prompt builder
# ---------------------------------------------------------------------------

def test_build_cover_letter_prompt_includes_salary():
    from applire.prompts.cover_letter import build_cover_letter_prompt
    prompt = build_cover_letter_prompt(
        cv_data={"contact": {"name": "Marcus Bauer"}, "summary": "QA expert"},
        jd_text="We are hiring a QA Manager at Roche Diagnostics.",
        pre_gen_inputs={"salary": "95.000 €", "tone": "formal"},
        detected_language="de",
    )
    assert "Gehaltswunsch" in prompt
    assert "95.000 €" in prompt


def test_build_cover_letter_prompt_includes_availability():
    from applire.prompts.cover_letter import build_cover_letter_prompt
    prompt = build_cover_letter_prompt(
        cv_data={"contact": {"name": "Marcus Bauer"}, "summary": "QA expert"},
        jd_text="We are hiring a QA Manager.",
        pre_gen_inputs={"availability": "3 months notice", "tone": "professional"},
        detected_language="en",
    )
    assert "3 months notice" in prompt


def test_build_cover_letter_prompt_returns_system_and_user():
    from applire.prompts.cover_letter import build_cover_letter_prompt, SYSTEM_PROMPT
    prompt = build_cover_letter_prompt(
        cv_data={"contact": {"name": "A. Test"}, "summary": "Engineer"},
        jd_text="Test JD",
        pre_gen_inputs={"tone": "conversational"},
        detected_language="de",
    )
    assert isinstance(SYSTEM_PROMPT, str)
    assert len(prompt) > 100


# ---------------------------------------------------------------------------
# Task 8 — Generation service
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_cover_letter_creates_pending_record(db):
    """generate_cover_letter should create a GeneratedCoverLetter with status=pending."""
    from unittest.mock import AsyncMock, MagicMock
    from applire.models.cover_letter import GeneratedCoverLetter, CoverLetterStatus
    from applire.models.cv import GeneratedCV
    from applire.models.flow import FlowSession
    from applire.models.job import JobAnalysis
    from applire.models.profile import MasterProfile
    from applire.models.user import User
    from applire.schemas.cover_letter import CoverLetterGenerateRequest

    # Seed minimal DB records
    user = User(id=uuid.uuid4(), email="test@test.com")
    db.add(user)
    job = JobAnalysis(
        id=uuid.uuid4(),
        raw_text_hash="abc123",
        raw_text="QA Manager at Roche",
        role_title="QA Manager",
        required_skills=[],
        nice_to_have_skills=[],
        keywords=[],
        seniority_level="senior",
        company_culture_signals=[],
        language_requirement="de",
    )
    db.add(job)
    profile = MasterProfile(profile_json={
        "contact": {"name": "Marcus Bauer", "email": "m@test.com"},
        "summary": "QA Expert",
        "work_history": [],
        "skills": [],
        "education": [],
        "languages": [],
    })
    db.add(profile)
    await db.flush()

    cv = GeneratedCV(
        job_analysis_id=job.id,
        profile_id=profile.id,
        tailored_data={
            "contact": {"name": "Marcus Bauer", "email": "m@test.com"},
            "summary": "QA Expert",
            "work_history": [],
            "skills": [],
            "education": [],
            "languages": [],
        },
        template="executive",
        status="ready",
    )
    db.add(cv)

    flow = FlowSession(
        user_id=user.id,
        job_id=job.id,
        generated_cv_id=cv.id,
        available_actions={},
    )
    db.add(flow)
    await db.commit()

    # Mock BackgroundTasks and LLM provider
    bg = MagicMock()
    bg.add_task = MagicMock()
    mock_provider = AsyncMock()

    from applire.services.cover_letter import generate_cover_letter
    request = CoverLetterGenerateRequest(
        job_id=job.id,
        tone="formal",
    )
    response = await generate_cover_letter(request, db, mock_provider, bg, "http://localhost:8001")

    assert response.cover_letter_id is not None
    assert response.status == CoverLetterStatus.pending
    bg.add_task.assert_called_once()

    # FlowSession should be updated
    await db.refresh(flow)
    assert flow.generated_cover_letter_id == response.cover_letter_id
