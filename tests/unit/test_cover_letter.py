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
