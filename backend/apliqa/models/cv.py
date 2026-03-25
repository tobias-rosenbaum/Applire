import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

_JSON = JSONB().with_variant(JSON(), "sqlite")

from apliqa.db.session import Base

_TTL_DAYS = 90


class CVGenerationStatus(str, Enum):
    """Lifecycle of an async CV generation job."""
    pending = "pending"       # Record created, background task not yet started
    generating = "generating" # Background task picked it up
    ready = "ready"           # PDF rendered, html/pdf endpoints are live
    failed = "failed"         # Rendering error; see error_message
    expired = "expired"       # Past expires_at; Retention Worker will clean up


def _expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=_TTL_DAYS)


class GeneratedCV(Base):
    __tablename__ = "generated_cvs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_analyses.id"), nullable=False, index=True
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("master_profiles.id"), nullable=False
    )
    tailored_data: Mapped[dict] = mapped_column(_JSON, nullable=False)
    template: Mapped[str] = mapped_column(default="classic_german", nullable=False)
    # Async generation lifecycle (default 'ready' for pre-iter17 rows)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CVGenerationStatus.ready.value
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_expires_at,
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
