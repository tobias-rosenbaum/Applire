import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from applire.db.session import Base

_JSON = JSONB().with_variant(JSON(), "sqlite")


class ColorScheme(Base):
    __tablename__ = "color_schemes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_builtin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    seed_primary: Mapped[str] = mapped_column(String(7), nullable=False)
    seed_accent: Mapped[str] = mapped_column(String(7), nullable=False)
    seed_secondary: Mapped[str] = mapped_column(String(7), nullable=False)
    surface_lightness: Mapped[float] = mapped_column(Float, nullable=False, default=0.97)
    derived: Mapped[dict] = mapped_column(_JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
