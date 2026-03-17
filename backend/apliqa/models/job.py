import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

_JSON = JSONB().with_variant(JSON(), "sqlite")

from apliqa.db.session import Base


class JobAnalysis(Base):
    __tablename__ = "job_analyses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    raw_text_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    role_title: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[list] = mapped_column(_JSON, nullable=False, default=list)
    nice_to_have_skills: Mapped[list] = mapped_column(_JSON, nullable=False, default=list)
    keywords: Mapped[list] = mapped_column(_JSON, nullable=False, default=list)
    seniority_level: Mapped[str] = mapped_column(Text, nullable=False)
    company_culture_signals: Mapped[list] = mapped_column(_JSON, nullable=False, default=list)
    language_requirement: Mapped[str] = mapped_column(Text, nullable=False)
    # LLM-extracted best-effort; nullable (recruiter-anonymised JDs omit company)
    company_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
