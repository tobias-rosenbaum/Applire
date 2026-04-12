import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from applire.db.session import Base

_JSON = JSONB().with_variant(JSON(), "sqlite")


class ColorProfile(Base):
    __tablename__ = "cv_color_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    seed_primary: Mapped[str] = mapped_column(String(7), nullable=False)
    derived: Mapped[dict] = mapped_column(_JSON, nullable=False)
    # 'favicon' | 'meta_tag' | 'llm' | 'user' | 'default'
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
