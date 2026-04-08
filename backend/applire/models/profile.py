import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from applire.db.session import Base

# JSONB on PostgreSQL (binary, indexed); falls back to JSON on SQLite for unit tests.
_ProfileJSON = JSONB().with_variant(JSON(), "sqlite")
# VECTOR(1024) on PostgreSQL; TEXT (always NULL) on SQLite — see migration 0016.
_VECTOR_1024 = Vector(1024).with_variant(sa.Text(), "sqlite")


class MasterProfile(Base):
    __tablename__ = "master_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    profile_json: Mapped[dict] = mapped_column(_ProfileJSON, nullable=False)
    # Embedding vector for job-profile similarity scoring (migration 0016).
    # Re-computed on every upsert; NULL until first pass; always NULL on SQLite.
    embedding: Mapped[list[float] | None] = mapped_column(_VECTOR_1024, nullable=True)
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
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
