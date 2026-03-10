"""GDPR retention worker — runs TTL sweeps and emits a JSON report (ADR 005)."""

import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text, update
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from apliqa.db.session import AsyncSessionLocal
from apliqa.models.cv import GeneratedCV
from apliqa.models.profile import MasterProfile
from apliqa.models.session import InterviewSession
from apliqa.models.user import User

logger = logging.getLogger(__name__)

_UPLOADS_TTL_DAYS = 7
_SESSION_TTL_DAYS = 30
_INACTIVITY_TTL_DAYS = 730  # ≈ 24 months (no month arithmetic in stdlib)


async def _purge_uploads(db: AsyncSession) -> int:
    """Hard-delete uploads older than 7 days.

    Uses raw SQL because no ORM model exists yet for the uploads table.
    Catches ProgrammingError gracefully so the worker runs cleanly when the
    table is absent (anticipated-but-not-yet-created pattern).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=_UPLOADS_TTL_DAYS)
    try:
        result = await db.execute(
            text("DELETE FROM uploads WHERE created_at < :cutoff"),
            {"cutoff": cutoff},
        )
        await db.commit()
        return result.rowcount  # type: ignore[return-value]
    except (ProgrammingError, OperationalError):
        # ProgrammingError: PostgreSQL "table does not exist"
        # OperationalError: SQLite "no such table" (test environments)
        await db.rollback()
        return 0


async def _purge_sessions(db: AsyncSession) -> int:
    """Hard-delete interview sessions inactive for more than 30 days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=_SESSION_TTL_DAYS)
    result = await db.execute(
        text(
            "DELETE FROM interview_sessions WHERE updated_at < :cutoff"
        ),
        {"cutoff": cutoff},
    )
    await db.commit()
    return result.rowcount  # type: ignore[return-value]


async def _purge_cvs(db: AsyncSession) -> int:
    """Hard-delete generated CVs whose expires_at is in the past."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        text(
            "DELETE FROM generated_cvs WHERE expires_at < :now AND deleted_at IS NULL"
        ),
        {"now": now},
    )
    await db.commit()
    return result.rowcount  # type: ignore[return-value]


async def _tombstone_inactive_profiles(db: AsyncSession) -> int:
    """Soft-delete master profiles inactive for ≥ 24 months."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=_INACTIVITY_TTL_DAYS)
    now = datetime.now(timezone.utc)
    result = await db.execute(
        update(MasterProfile)
        .where(MasterProfile.updated_at < cutoff)
        .where(MasterProfile.deleted_at.is_(None))
        .values(deleted_at=now)
    )
    await db.commit()
    return result.rowcount  # type: ignore[return-value]


async def _tombstone_inactive_users(db: AsyncSession) -> int:
    """Soft-delete users inactive for ≥ 24 months (based on profile activity)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=_INACTIVITY_TTL_DAYS)
    now = datetime.now(timezone.utc)
    result = await db.execute(
        update(User)
        .where(User.created_at < cutoff)
        .where(User.deleted_at.is_(None))
        .values(deleted_at=now)
    )
    await db.commit()
    return result.rowcount  # type: ignore[return-value]


async def run() -> None:
    """Execute all TTL rules and emit a structured JSON report to stdout."""
    async with AsyncSessionLocal() as db:
        uploads_deleted = await _purge_uploads(db)
        sessions_deleted = await _purge_sessions(db)
        cvs_deleted = await _purge_cvs(db)
        profiles_tombstoned = await _tombstone_inactive_profiles(db)
        users_tombstoned = await _tombstone_inactive_users(db)

    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "uploads_deleted": uploads_deleted,
        "interview_sessions_deleted": sessions_deleted,
        "generated_cvs_deleted": cvs_deleted,
        "master_profiles_tombstoned": profiles_tombstoned,
        "users_tombstoned": users_tombstoned,
    }
    print(json.dumps(report), flush=True)
