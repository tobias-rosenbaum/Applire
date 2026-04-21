import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

_JSON = JSONB().with_variant(JSON(), "sqlite")

from applire.db.session import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("job_analyses.id"), nullable=True, index=True
    )
    gap_analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("gap_analyses.id"), nullable=True
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("master_profiles.id"), nullable=False
    )
    # "targeted" (MODE A) | "guided" (MODE B)
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="targeted")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # "active" | "complete"
    state: Mapped[dict] = mapped_column(_JSON, nullable=False)
    questions_asked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hard_ceiling: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
