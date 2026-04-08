import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

_JSON = JSONB().with_variant(JSON(), "sqlite")

from applire.db.session import Base


class GapAnalysis(Base):
    __tablename__ = "gap_analyses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_analyses.id"), nullable=False, index=True
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("master_profiles.id"), nullable=False, index=True
    )
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    # Cosine similarity of job_analysis.embedding vs master_profile.embedding (migration 0017).
    # NULL if either embedding is absent or noop provider is active.
    embedding_similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    critical_gaps: Mapped[list] = mapped_column(_JSON, nullable=False, default=list)
    minor_gaps: Mapped[list] = mapped_column(_JSON, nullable=False, default=list)
    strengths: Mapped[list] = mapped_column(_JSON, nullable=False, default=list)
    keyword_gaps: Mapped[list] = mapped_column(_JSON, nullable=False, default=list)
    category_a: Mapped[list] = mapped_column(_JSON, nullable=False, default=list)
    category_b: Mapped[list] = mapped_column(_JSON, nullable=False, default=list)
    category_c: Mapped[list] = mapped_column(_JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
