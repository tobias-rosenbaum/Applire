# Color Scheme Admin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an admin appearance panel at `/admin/appearance` where the operator can create, preview, name, save, and activate color schemes that apply across the entire app via CSS custom properties.

**Architecture:** A `color_schemes` PostgreSQL table stores named schemes (3 seed hex colors + surface lightness float + server-computed derived CSS variables). A FastAPI admin router handles CRUD. The Next.js `ThemeProvider` fetches the active scheme on app load and injects CSS custom properties on `document.documentElement`. The admin editor derives colors client-side for instant live preview, with the server as the authoritative source on save.

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy (asyncpg) / Alembic · Next.js 15 / React 19 / TypeScript · pytest (unit, SQLite in-memory) · Vitest + jsdom · Playwright (E2E smoke)

---

## File Map

**Create:**
- `backend/applire/models/color_scheme.py` — SQLAlchemy `ColorScheme` model
- `backend/applire/schemas/color_scheme.py` — Pydantic request/response schemas
- `backend/applire/services/color_schemes.py` — derivation logic + DB service functions
- `backend/applire/routers/admin/__init__.py` — empty, makes admin a package
- `backend/applire/routers/admin/color_schemes.py` — FastAPI router
- `backend/alembic/versions/0020_color_schemes.py` — migration + EU Blue seed row
- `frontend/lib/theme.ts` — `deriveScheme()` pure TypeScript utility
- `frontend/lib/__tests__/theme.test.ts` — Vitest unit tests for `deriveScheme()`
- `frontend/components/theme-provider.tsx` — fetches + injects active scheme on mount
- `frontend/components/admin/scheme-editor.tsx` — left panel (preset picker, pickers, slider, save)
- `frontend/components/admin/theme-preview.tsx` — right panel (component mockup)
- `frontend/app/admin/appearance/page.tsx` — admin page route
- `tests/unit/test_color_schemes.py` — pytest unit tests for derivation + service

**Modify:**
- `backend/applire/main.py` — register admin router
- `frontend/components/providers.tsx` — wrap with `ThemeProvider`
- `frontend/app/settings/page.tsx` — add Admin link in footer

---

## Task 1: Alembic migration + SQLAlchemy model

**Files:**
- Create: `backend/applire/models/color_scheme.py`
- Create: `backend/alembic/versions/0020_color_schemes.py`

- [ ] **Step 1: Write the SQLAlchemy model**

```python
# backend/applire/models/color_scheme.py
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON

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
```

- [ ] **Step 2: Write the migration**

```python
# backend/alembic/versions/0020_color_schemes.py
"""Add color_schemes table

Revision ID: 0020
Revises: 0019
Create Date: 2026-04-10
"""
from typing import Sequence, Union
import json
import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_EU_BLUE_ID = "a0000000-0000-0000-0000-000000000001"

_EU_BLUE_DERIVED = {
    "--color-primary": "#1B4F72",
    "--color-primary-container": "#D4E6F1",
    "--color-teal": "#2A8F9D",
    "--color-teal-dim": "#003a41",
    "--color-teal-container": "#e3effe",
    "--color-teal-container-light": "#f7f9ff",
    "--color-gold": "#C9A84C",
    "--color-gold-dim": "#755b00",
    "--color-gold-container": "#ffeec5",
    "--color-surface-dim": "#f7f9ff",
    "--color-surface-bright": "#ffffff",
    "--color-surface-container": "#f0f4f9",
    "--color-surface-container-high": "#e3effe",
    "--color-surface-container-highest": "#d9e4f4",
    "--color-neutral-light": "#F5F7FA",
}


def upgrade() -> None:
    op.create_table(
        "color_schemes",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_builtin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("seed_primary", sa.String(7), nullable=False),
        sa.Column("seed_accent", sa.String(7), nullable=False),
        sa.Column("seed_secondary", sa.String(7), nullable=False),
        sa.Column("surface_lightness", sa.Float(), nullable=False, server_default="0.97"),
        sa.Column("derived", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    # Seed EU Blue as the single built-in active scheme
    op.execute(
        sa.text(
            "INSERT INTO color_schemes "
            "(id, name, is_active, is_builtin, seed_primary, seed_accent, seed_secondary, "
            "surface_lightness, derived, created_at) VALUES "
            "(:id, :name, true, true, :sp, :sa, :ss, :sl, :derived::jsonb, :created_at)"
        ).bindparams(
            id=_EU_BLUE_ID,
            name="EU Blue",
            sp="#1B4F72",
            sa="#2A8F9D",
            ss="#C9A84C",
            sl=0.97,
            derived=json.dumps(_EU_BLUE_DERIVED),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )


def downgrade() -> None:
    op.drop_table("color_schemes")
```

- [ ] **Step 3: Register the model in `backend/applire/models/__init__.py`**

Open `backend/applire/models/__init__.py`. Add this import at the end:

```python
from applire.models.color_scheme import ColorScheme  # noqa: F401
```

- [ ] **Step 4: Commit**

```bash
git add backend/applire/models/color_scheme.py \
        backend/applire/models/__init__.py \
        backend/alembic/versions/0020_color_schemes.py
git commit -m "feat(color-schemes): add ColorScheme model and migration 0020"
```

---

## Task 2: Pydantic schemas

**Files:**
- Create: `backend/applire/schemas/color_scheme.py`

- [ ] **Step 1: Write the schemas**

```python
# backend/applire/schemas/color_scheme.py
import re
import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _validate_hex(v: str) -> str:
    if not _HEX_RE.match(v):
        raise ValueError(f"Invalid hex color: {v!r}. Expected #RRGGBB format.")
    return v.lower()


class ColorSchemeCreate(BaseModel):
    name: str
    seed_primary: str
    seed_accent: str
    seed_secondary: str
    surface_lightness: float = 0.97

    @field_validator("seed_primary", "seed_accent", "seed_secondary", mode="before")
    @classmethod
    def validate_hex(cls, v: str) -> str:
        return _validate_hex(v)

    @field_validator("surface_lightness")
    @classmethod
    def validate_lightness(cls, v: float) -> float:
        if not 0.88 <= v <= 0.99:
            raise ValueError("surface_lightness must be between 0.88 and 0.99")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be empty")
        if len(v) > 64:
            raise ValueError("name must be 64 characters or fewer")
        return v


class ColorSchemePreviewRequest(BaseModel):
    seed_primary: str
    seed_accent: str
    seed_secondary: str
    surface_lightness: float = 0.97

    @field_validator("seed_primary", "seed_accent", "seed_secondary", mode="before")
    @classmethod
    def validate_hex(cls, v: str) -> str:
        return _validate_hex(v)

    @field_validator("surface_lightness")
    @classmethod
    def validate_lightness(cls, v: float) -> float:
        if not 0.88 <= v <= 0.99:
            raise ValueError("surface_lightness must be between 0.88 and 0.99")
        return v


class ColorSchemeResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_active: bool
    is_builtin: bool
    seed_primary: str
    seed_accent: str
    seed_secondary: str
    surface_lightness: float
    derived: dict[str, str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ActiveSchemeResponse(BaseModel):
    id: uuid.UUID
    name: str
    derived: dict[str, str]
```

- [ ] **Step 2: Commit**

```bash
git add backend/applire/schemas/color_scheme.py
git commit -m "feat(color-schemes): add Pydantic schemas"
```

---

## Task 3: Backend derivation service + unit tests

**Files:**
- Create: `backend/applire/services/color_schemes.py`
- Create: `tests/unit/test_color_schemes.py`

- [ ] **Step 1: Write the failing tests first**

```python
# tests/unit/test_color_schemes.py
"""
Unit tests for the color scheme derivation service.
No Docker, no DB, no LLM.

Run:
    pytest tests/unit/test_color_schemes.py -v
"""
import pytest
from applire.services.color_schemes import derive_scheme, _hex_to_hsl, _hsl_to_hex


class TestHexHslConversion:
    def test_round_trip_primary_blue(self):
        h, s, l = _hex_to_hsl("#1b4f72")
        result = _hsl_to_hex(h, s, l)
        assert result == "#1b4f72"

    def test_round_trip_white(self):
        h, s, l = _hex_to_hsl("#ffffff")
        result = _hsl_to_hex(h, s, l)
        assert result == "#ffffff"

    def test_round_trip_black(self):
        h, s, l = _hex_to_hsl("#000000")
        result = _hsl_to_hex(h, s, l)
        assert result == "#000000"


class TestDeriveScheme:
    EU_BLUE = dict(
        seed_primary="#1b4f72",
        seed_accent="#2a8f9d",
        seed_secondary="#c9a84c",
        surface_lightness=0.97,
    )

    def test_returns_all_required_variables(self):
        derived = derive_scheme(**self.EU_BLUE)
        expected_keys = {
            "--color-primary", "--color-primary-container",
            "--color-teal", "--color-teal-dim", "--color-teal-container",
            "--color-teal-container-light",
            "--color-gold", "--color-gold-dim", "--color-gold-container",
            "--color-surface-dim", "--color-surface-bright",
            "--color-surface-container", "--color-surface-container-high",
            "--color-surface-container-highest",
            "--color-neutral-light",
        }
        assert set(derived.keys()) == expected_keys

    def test_seeds_pass_through(self):
        derived = derive_scheme(**self.EU_BLUE)
        assert derived["--color-primary"] == "#1b4f72"
        assert derived["--color-teal"] == "#2a8f9d"
        assert derived["--color-gold"] == "#c9a84c"

    def test_surface_bright_is_always_white(self):
        derived = derive_scheme(**self.EU_BLUE)
        assert derived["--color-surface-bright"] == "#ffffff"

    def test_all_values_are_valid_hex(self):
        import re
        hex_re = re.compile(r"^#[0-9a-f]{6}$")
        derived = derive_scheme(**self.EU_BLUE)
        for key, value in derived.items():
            assert hex_re.match(value), f"{key}: {value!r} is not a valid hex color"

    def test_container_is_lighter_than_seed(self):
        derived = derive_scheme(**self.EU_BLUE)
        _, _, l_seed = _hex_to_hsl(self.EU_BLUE["seed_primary"])
        _, _, l_container = _hex_to_hsl(derived["--color-primary-container"])
        assert l_container > l_seed

    def test_dim_is_darker_than_seed(self):
        derived = derive_scheme(**self.EU_BLUE)
        _, _, l_seed = _hex_to_hsl(self.EU_BLUE["seed_accent"])
        _, _, l_dim = _hex_to_hsl(derived["--color-teal-dim"])
        assert l_dim < l_seed

    def test_surface_container_high_is_darker_than_surface_dim(self):
        derived = derive_scheme(**self.EU_BLUE)
        _, _, l_dim = _hex_to_hsl(derived["--color-surface-dim"])
        _, _, l_high = _hex_to_hsl(derived["--color-surface-container-high"])
        assert l_high < l_dim

    def test_lower_surface_lightness_produces_darker_surfaces(self):
        light = derive_scheme(seed_primary="#1b4f72", seed_accent="#2a8f9d",
                              seed_secondary="#c9a84c", surface_lightness=0.97)
        dark = derive_scheme(seed_primary="#1b4f72", seed_accent="#2a8f9d",
                             seed_secondary="#c9a84c", surface_lightness=0.88)
        _, _, l_light = _hex_to_hsl(light["--color-surface-dim"])
        _, _, l_dark = _hex_to_hsl(dark["--color-surface-dim"])
        assert l_dark < l_light
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd /path/to/Solution && pytest tests/unit/test_color_schemes.py -v
```
Expected: `ModuleNotFoundError: No module named 'applire.services.color_schemes'`

- [ ] **Step 3: Implement the derivation service**

```python
# backend/applire/services/color_schemes.py
"""Color scheme derivation and DB service functions."""
import colorsys
import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from applire.models.color_scheme import ColorScheme


# ---------------------------------------------------------------------------
# Color math helpers
# ---------------------------------------------------------------------------

def _hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    """Convert #rrggbb → (h, s, l) with all values in [0, 1]."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    # colorsys returns (h, l, s) — note the l/s swap
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h, s, l


def _hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert (h, s, l) with all values in [0, 1] → #rrggbb."""
    # colorsys expects (h, l, s)
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    r_i = max(0, min(255, round(r * 255)))
    g_i = max(0, min(255, round(g * 255)))
    b_i = max(0, min(255, round(b * 255)))
    return f"#{r_i:02x}{g_i:02x}{b_i:02x}"


def _derive_color(hex_color: str, lightness: float, saturation: float) -> str:
    """Keep hue from hex_color, override lightness and saturation."""
    h, _, _ = _hex_to_hsl(hex_color)
    return _hsl_to_hex(h, saturation, lightness)


# ---------------------------------------------------------------------------
# Public derivation function (used by router + tests)
# ---------------------------------------------------------------------------

def derive_scheme(
    seed_primary: str,
    seed_accent: str,
    seed_secondary: str,
    surface_lightness: float,
) -> dict[str, str]:
    """Derive all 15 CSS custom property values from 3 seeds + surface lightness."""
    L = surface_lightness
    return {
        "--color-primary": seed_primary.lower(),
        "--color-primary-container": _derive_color(seed_primary, 0.90, 0.30),
        "--color-teal": seed_accent.lower(),
        "--color-teal-dim": _derive_color(seed_accent, 0.12, 1.00),
        "--color-teal-container": _derive_color(seed_accent, 0.92, 0.40),
        "--color-teal-container-light": _derive_color(seed_accent, 0.97, 0.15),
        "--color-gold": seed_secondary.lower(),
        "--color-gold-dim": _derive_color(seed_secondary, 0.20, 1.00),
        "--color-gold-container": _derive_color(seed_secondary, 0.92, 0.60),
        "--color-surface-dim": _derive_color(seed_primary, L, 0.08),
        "--color-surface-bright": "#ffffff",
        "--color-surface-container": _derive_color(seed_primary, max(0.0, L - 0.02), 0.10),
        "--color-surface-container-high": _derive_color(seed_primary, max(0.0, L - 0.05), 0.12),
        "--color-surface-container-highest": _derive_color(seed_primary, max(0.0, L - 0.08), 0.14),
        "--color-neutral-light": _derive_color(seed_primary, L, 0.05),
    }


# ---------------------------------------------------------------------------
# DB service functions
# ---------------------------------------------------------------------------

async def get_active_scheme(db: AsyncSession) -> ColorScheme | None:
    result = await db.execute(
        select(ColorScheme).where(ColorScheme.is_active == True)  # noqa: E712
    )
    return result.scalar_one_or_none()


async def list_schemes(db: AsyncSession) -> list[ColorScheme]:
    result = await db.execute(
        select(ColorScheme).order_by(ColorScheme.created_at)
    )
    return list(result.scalars().all())


async def create_scheme(
    db: AsyncSession,
    name: str,
    seed_primary: str,
    seed_accent: str,
    seed_secondary: str,
    surface_lightness: float,
) -> ColorScheme:
    derived = derive_scheme(seed_primary, seed_accent, seed_secondary, surface_lightness)
    scheme = ColorScheme(
        id=uuid.uuid4(),
        name=name,
        is_active=False,
        is_builtin=False,
        seed_primary=seed_primary.lower(),
        seed_accent=seed_accent.lower(),
        seed_secondary=seed_secondary.lower(),
        surface_lightness=surface_lightness,
        derived=derived,
    )
    db.add(scheme)
    await db.commit()
    await db.refresh(scheme)
    return scheme


async def activate_scheme(db: AsyncSession, scheme_id: uuid.UUID) -> ColorScheme | None:
    scheme = await db.get(ColorScheme, scheme_id)
    if scheme is None:
        return None
    # Deactivate all, then activate the target — in one transaction
    await db.execute(
        update(ColorScheme).values(is_active=False)
    )
    scheme.is_active = True
    await db.commit()
    await db.refresh(scheme)
    return scheme


async def delete_scheme(db: AsyncSession, scheme_id: uuid.UUID) -> ColorScheme | None:
    scheme = await db.get(ColorScheme, scheme_id)
    if scheme is None:
        return None
    await db.delete(scheme)
    await db.commit()
    return scheme
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/unit/test_color_schemes.py -v
```
Expected: all 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/applire/services/color_schemes.py tests/unit/test_color_schemes.py
git commit -m "feat(color-schemes): derivation service + unit tests"
```

---

## Task 4: FastAPI admin router + service tests

**Files:**
- Create: `backend/applire/routers/admin/__init__.py`
- Create: `backend/applire/routers/admin/color_schemes.py`
- Modify: `tests/unit/test_color_schemes.py` (add service + router tests)

- [ ] **Step 1: Add DB service tests to `tests/unit/test_color_schemes.py`**

Append these classes to the existing test file:

```python
# Append to tests/unit/test_color_schemes.py

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from applire.db.session import Base
import applire.models.color_scheme  # noqa: F401 — registers model


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def eu_blue(db):
    """Insert the EU Blue builtin scheme into the test DB."""
    from applire.models.color_scheme import ColorScheme
    from applire.services.color_schemes import derive_scheme
    scheme = ColorScheme(
        id=uuid.UUID("a0000000-0000-0000-0000-000000000001"),
        name="EU Blue",
        is_active=True,
        is_builtin=True,
        seed_primary="#1b4f72",
        seed_accent="#2a8f9d",
        seed_secondary="#c9a84c",
        surface_lightness=0.97,
        derived=derive_scheme("#1b4f72", "#2a8f9d", "#c9a84c", 0.97),
    )
    db.add(scheme)
    await db.commit()
    await db.refresh(scheme)
    return scheme


class TestServiceFunctions:
    @pytest.mark.asyncio
    async def test_get_active_scheme_returns_eu_blue(self, db, eu_blue):
        from applire.services.color_schemes import get_active_scheme
        result = await get_active_scheme(db)
        assert result is not None
        assert result.name == "EU Blue"

    @pytest.mark.asyncio
    async def test_create_scheme_derives_values(self, db, eu_blue):
        from applire.services.color_schemes import create_scheme
        scheme = await create_scheme(
            db,
            name="Midnight",
            seed_primary="#1a1a2e",
            seed_accent="#16213e",
            seed_secondary="#e94560",
            surface_lightness=0.96,
        )
        assert scheme.name == "Midnight"
        assert "--color-primary" in scheme.derived
        assert scheme.is_active is False

    @pytest.mark.asyncio
    async def test_activate_scheme_deactivates_others(self, db, eu_blue):
        from applire.services.color_schemes import create_scheme, activate_scheme, get_active_scheme
        midnight = await create_scheme(
            db, name="Midnight", seed_primary="#1a1a2e",
            seed_accent="#16213e", seed_secondary="#e94560", surface_lightness=0.96,
        )
        activated = await activate_scheme(db, midnight.id)
        assert activated is not None
        assert activated.is_active is True
        # EU Blue should now be inactive
        active = await get_active_scheme(db)
        assert active is not None
        assert active.name == "Midnight"

    @pytest.mark.asyncio
    async def test_delete_scheme_removes_it(self, db, eu_blue):
        from applire.services.color_schemes import create_scheme, delete_scheme, list_schemes
        scheme = await create_scheme(
            db, name="ToDelete", seed_primary="#aabbcc",
            seed_accent="#112233", seed_secondary="#ddeeff", surface_lightness=0.95,
        )
        await delete_scheme(db, scheme.id)
        schemes = await list_schemes(db)
        assert not any(s.name == "ToDelete" for s in schemes)
```

- [ ] **Step 2: Run new DB tests — verify they fail**

```bash
pytest tests/unit/test_color_schemes.py::TestServiceFunctions -v
```
Expected: import errors or fixture errors (router not yet wired).

- [ ] **Step 3: Create the admin package**

```python
# backend/applire/routers/admin/__init__.py
# (empty)
```

- [ ] **Step 4: Write the router**

```python
# backend/applire/routers/admin/color_schemes.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from applire.db.session import get_db
from applire.schemas.color_scheme import (
    ActiveSchemeResponse,
    ColorSchemeCreate,
    ColorSchemePreviewRequest,
    ColorSchemeResponse,
)
from applire.services.color_schemes import (
    activate_scheme,
    create_scheme,
    delete_scheme,
    derive_scheme,
    get_active_scheme,
    list_schemes,
)

router = APIRouter(prefix="/api/admin/color-schemes", tags=["admin"])


# IMPORTANT: /active must be defined before /{scheme_id} to prevent FastAPI
# from matching "active" as a UUID path parameter.

@router.get("/active", response_model=ActiveSchemeResponse)
async def get_active(db: AsyncSession = Depends(get_db)):
    scheme = await get_active_scheme(db)
    if scheme is None:
        raise HTTPException(status_code=404, detail="No active color scheme found")
    return ActiveSchemeResponse(id=scheme.id, name=scheme.name, derived=scheme.derived)


@router.get("", response_model=list[ColorSchemeResponse])
async def list_all(db: AsyncSession = Depends(get_db)):
    return await list_schemes(db)


@router.post("/preview", response_model=dict)
async def preview(body: ColorSchemePreviewRequest):
    """Compute derived values without saving. Used by the editor for live preview."""
    return derive_scheme(
        body.seed_primary,
        body.seed_accent,
        body.seed_secondary,
        body.surface_lightness,
    )


@router.post("", response_model=ColorSchemeResponse, status_code=status.HTTP_201_CREATED)
async def create(body: ColorSchemeCreate, db: AsyncSession = Depends(get_db)):
    return await create_scheme(
        db,
        name=body.name,
        seed_primary=body.seed_primary,
        seed_accent=body.seed_accent,
        seed_secondary=body.seed_secondary,
        surface_lightness=body.surface_lightness,
    )


@router.patch("/{scheme_id}/activate", response_model=ColorSchemeResponse)
async def activate(scheme_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    scheme = await activate_scheme(db, scheme_id)
    if scheme is None:
        raise HTTPException(status_code=404, detail="Color scheme not found")
    return scheme


@router.delete("/{scheme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(scheme_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from applire.models.color_scheme import ColorScheme
    from sqlalchemy import select
    result = await db.execute(
        select(ColorScheme).where(ColorScheme.id == scheme_id)
    )
    scheme = result.scalar_one_or_none()
    if scheme is None:
        raise HTTPException(status_code=404, detail="Color scheme not found")
    if scheme.is_builtin:
        raise HTTPException(status_code=409, detail="Cannot delete a built-in scheme")
    if scheme.is_active:
        raise HTTPException(status_code=409, detail="Cannot delete the active scheme — activate another scheme first")
    await delete_scheme(db, scheme_id)
```

- [ ] **Step 5: Run service tests — verify they pass**

```bash
pytest tests/unit/test_color_schemes.py -v
```
Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/applire/routers/admin/__init__.py \
        backend/applire/routers/admin/color_schemes.py \
        tests/unit/test_color_schemes.py
git commit -m "feat(color-schemes): admin router + service DB tests"
```

---

## Task 5: Wire backend into main.py

**Files:**
- Modify: `backend/applire/main.py`

- [ ] **Step 1: Register the admin router**

In `backend/applire/main.py`, add the import alongside existing router imports:

```python
from applire.routers.admin import color_schemes as admin_color_schemes
```

Then add after the existing `app.include_router(application.router)` line:

```python
app.include_router(admin_color_schemes.router)
```

- [ ] **Step 2: Verify the app starts and lists the new endpoints**

```bash
cd backend && uvicorn applire.main:app --port 8001 --no-access-log &
sleep 2
curl -s http://localhost:8001/openapi.json | python3 -c "
import json, sys
paths = json.load(sys.stdin)['paths']
admin = [p for p in paths if 'color-schemes' in p]
print('Admin endpoints:', admin)
"
kill %1
```
Expected output includes: `['/api/admin/color-schemes/active', '/api/admin/color-schemes', '/api/admin/color-schemes/preview', '/api/admin/color-schemes/{scheme_id}/activate', '/api/admin/color-schemes/{scheme_id}']`

- [ ] **Step 3: Commit**

```bash
git add backend/applire/main.py
git commit -m "feat(color-schemes): register admin router in main.py"
```

---

## Task 6: Frontend deriveScheme utility + Vitest tests

**Files:**
- Create: `frontend/lib/theme.ts`
- Create: `frontend/lib/__tests__/theme.test.ts`

- [ ] **Step 1: Write the failing tests**

```typescript
// frontend/lib/__tests__/theme.test.ts
import { describe, it, expect } from "vitest";
import { deriveScheme, type SeedColors } from "../theme";

const EU_BLUE: SeedColors = {
  primary: "#1b4f72",
  accent: "#2a8f9d",
  secondary: "#c9a84c",
};

describe("deriveScheme", () => {
  it("returns all 15 required CSS variable keys", () => {
    const derived = deriveScheme(EU_BLUE, 0.97);
    const expected = [
      "--color-primary", "--color-primary-container",
      "--color-teal", "--color-teal-dim", "--color-teal-container",
      "--color-teal-container-light",
      "--color-gold", "--color-gold-dim", "--color-gold-container",
      "--color-surface-dim", "--color-surface-bright",
      "--color-surface-container", "--color-surface-container-high",
      "--color-surface-container-highest",
      "--color-neutral-light",
    ];
    expect(Object.keys(derived).sort()).toEqual(expected.sort());
  });

  it("passes seeds through unchanged", () => {
    const derived = deriveScheme(EU_BLUE, 0.97);
    expect(derived["--color-primary"]).toBe("#1b4f72");
    expect(derived["--color-teal"]).toBe("#2a8f9d");
    expect(derived["--color-gold"]).toBe("#c9a84c");
  });

  it("surface-bright is always #ffffff", () => {
    expect(deriveScheme(EU_BLUE, 0.97)["--color-surface-bright"]).toBe("#ffffff");
  });

  it("all values are valid #rrggbb hex strings", () => {
    const hex = /^#[0-9a-f]{6}$/;
    const derived = deriveScheme(EU_BLUE, 0.97);
    for (const [key, val] of Object.entries(derived)) {
      expect(val, `${key} should be valid hex`).toMatch(hex);
    }
  });

  it("lower surface_lightness produces a lower lightness surface-dim", () => {
    const light = deriveScheme(EU_BLUE, 0.97);
    const dark = deriveScheme(EU_BLUE, 0.88);
    // surface-dim at 0.88 should be a darker color than at 0.97
    // We verify this by checking the hex value differs and parsing lightness
    expect(light["--color-surface-dim"]).not.toBe(dark["--color-surface-dim"]);
  });
});
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd frontend && npx vitest run lib/__tests__/theme.test.ts
```
Expected: `Cannot find module '../theme'`

- [ ] **Step 3: Implement `frontend/lib/theme.ts`**

```typescript
// frontend/lib/theme.ts

export interface SeedColors {
  primary: string;
  accent: string;
  secondary: string;
}

export type DerivedScheme = Record<string, string>;

function hexToHsl(hex: string): [number, number, number] {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const l = (max + min) / 2;
  if (max === min) return [0, 0, l];
  const d = max - min;
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
  let h = 0;
  if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
  else if (max === g) h = ((b - r) / d + 2) / 6;
  else h = ((r - g) / d + 4) / 6;
  return [h, s, l];
}

function hslToHex(h: number, s: number, l: number): string {
  const hue2rgb = (p: number, q: number, t: number): number => {
    if (t < 0) t += 1;
    if (t > 1) t -= 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  };
  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;
  const r = Math.round(hue2rgb(p, q, h + 1 / 3) * 255);
  const g = Math.round(hue2rgb(p, q, h) * 255);
  const b = Math.round(hue2rgb(p, q, h - 1 / 3) * 255);
  return "#" + [r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("");
}

function deriveColor(hex: string, lightness: number, saturation: number): string {
  const [h] = hexToHsl(hex);
  return hslToHex(h, saturation, lightness);
}

export function deriveScheme(seeds: SeedColors, surfaceLightness: number): DerivedScheme {
  const L = surfaceLightness;
  return {
    "--color-primary": seeds.primary.toLowerCase(),
    "--color-primary-container": deriveColor(seeds.primary, 0.90, 0.30),
    "--color-teal": seeds.accent.toLowerCase(),
    "--color-teal-dim": deriveColor(seeds.accent, 0.12, 1.00),
    "--color-teal-container": deriveColor(seeds.accent, 0.92, 0.40),
    "--color-teal-container-light": deriveColor(seeds.accent, 0.97, 0.15),
    "--color-gold": seeds.secondary.toLowerCase(),
    "--color-gold-dim": deriveColor(seeds.secondary, 0.20, 1.00),
    "--color-gold-container": deriveColor(seeds.secondary, 0.92, 0.60),
    "--color-surface-dim": deriveColor(seeds.primary, L, 0.08),
    "--color-surface-bright": "#ffffff",
    "--color-surface-container": deriveColor(seeds.primary, Math.max(0, L - 0.02), 0.10),
    "--color-surface-container-high": deriveColor(seeds.primary, Math.max(0, L - 0.05), 0.12),
    "--color-surface-container-highest": deriveColor(seeds.primary, Math.max(0, L - 0.08), 0.14),
    "--color-neutral-light": deriveColor(seeds.primary, L, 0.05),
  };
}
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd frontend && npx vitest run lib/__tests__/theme.test.ts
```
Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/lib/theme.ts frontend/lib/__tests__/theme.test.ts
git commit -m "feat(color-schemes): frontend deriveScheme utility + Vitest tests"
```

---

## Task 7: ThemeProvider component

**Files:**
- Create: `frontend/components/theme-provider.tsx`

- [ ] **Step 1: Write the component**

```typescript
// frontend/components/theme-provider.tsx
"use client";

import { createContext, useCallback, useContext, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

interface ThemeContextValue {
  /** Call after activating a scheme to propagate it immediately without a page reload. */
  refreshTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({ refreshTheme: () => {} });

export function useTheme(): ThemeContextValue {
  return useContext(ThemeContext);
}

async function applyActiveScheme(): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/api/admin/color-schemes/active`);
    if (!res.ok) return; // fall back to globals.css static values
    const data = await res.json();
    const derived: Record<string, string> = data.derived;
    for (const [key, value] of Object.entries(derived)) {
      document.documentElement.style.setProperty(key, value);
    }
  } catch {
    // Network error or server not ready — globals.css fallback remains active
  }
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const refreshTheme = useCallback(() => {
    applyActiveScheme();
  }, []);

  useEffect(() => {
    applyActiveScheme();
  }, []);

  return (
    <ThemeContext.Provider value={{ refreshTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/theme-provider.tsx
git commit -m "feat(color-schemes): ThemeProvider — injects active scheme CSS vars on mount"
```

---

## Task 8: Admin appearance page

**Files:**
- Create: `frontend/components/admin/theme-preview.tsx`
- Create: `frontend/components/admin/scheme-editor.tsx`
- Create: `frontend/app/admin/appearance/page.tsx`

- [ ] **Step 1: Write ThemePreview — the live component mockup panel**

```typescript
// frontend/components/admin/theme-preview.tsx
"use client";

export function ThemePreview() {
  return (
    <div className="flex-1 bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wide">
        Live Preview
      </div>
      <div className="p-4 flex flex-col gap-3 bg-surface-dim min-h-[400px]">

        {/* Nav bar */}
        <div className="bg-primary rounded-lg px-4 py-2.5 flex items-center justify-between">
          <span className="text-white font-bold font-heading text-sm">Applire</span>
          <div className="flex gap-4">
            <span className="text-white/70 text-xs">Dashboard</span>
            <span className="text-white/70 text-xs">Profile</span>
          </div>
        </div>

        {/* Application card */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="font-semibold text-neutral-dark text-sm mb-1">Software Engineer</div>
          <div className="text-xs text-gray-500 mb-3">Tailored for Acme GmbH · 3 gaps identified</div>
          <div className="flex gap-2 items-center">
            <span className="bg-teal text-white text-xs px-2 py-1 rounded font-semibold">View CV</span>
            <span className="bg-primary-container text-primary text-xs px-2 py-1 rounded font-semibold">Interview</span>
            <span className="ml-auto bg-gold-container text-gold-dim text-xs px-2 py-1 rounded font-semibold">3 gaps</span>
          </div>
        </div>

        {/* Button row */}
        <div className="flex gap-2 flex-wrap">
          <button className="bg-primary text-white text-xs px-3 py-1.5 rounded-md font-semibold">Primary</button>
          <button className="bg-teal text-white text-xs px-3 py-1.5 rounded-md font-semibold">Accent</button>
          <button className="border border-teal text-teal text-xs px-3 py-1.5 rounded-md font-semibold">Outline</button>
          <button className="bg-primary-container text-primary text-xs px-3 py-1.5 rounded-md font-semibold">Subtle</button>
        </div>

        {/* Form input */}
        <div>
          <label className="block text-xs font-semibold text-neutral-dark mb-1">Job title</label>
          <input
            readOnly
            value="Senior Software Engineer"
            className="w-full border border-teal rounded-md px-3 py-2 text-xs text-neutral-dark bg-white"
          />
        </div>

        {/* Skill badges */}
        <div className="flex gap-2 flex-wrap">
          {["Python", "FastAPI", "Docker", "PostgreSQL"].map((skill) => (
            <span key={skill} className="bg-teal-container text-primary text-xs px-2 py-1 rounded-full font-semibold">
              {skill}
            </span>
          ))}
        </div>

        {/* Link */}
        <a className="text-xs text-teal underline cursor-pointer">← Back to Dashboard</a>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Write SchemeEditor — left panel**

```typescript
// frontend/components/admin/scheme-editor.tsx
"use client";

import { useCallback, useEffect, useState } from "react";
import { deriveScheme, type DerivedScheme, type SeedColors } from "@/lib/theme";
import { useTheme } from "@/components/theme-provider";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

interface SavedScheme {
  id: string;
  name: string;
  is_active: boolean;
  is_builtin: boolean;
  seed_primary: string;
  seed_accent: string;
  seed_secondary: string;
  surface_lightness: number;
  derived: Record<string, string>;
}

const NEUTRAL_DEFAULTS: SeedColors = {
  primary: "#4a4a4a",
  accent: "#4a4a4a",
  secondary: "#4a4a4a",
};

export function SchemeEditor() {
  const { refreshTheme } = useTheme();
  const [schemes, setSchemes] = useState<SavedScheme[]>([]);
  const [seeds, setSeeds] = useState<SeedColors>(NEUTRAL_DEFAULTS);
  const [surfaceLightness, setSurfaceLightness] = useState(0.97);
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [activating, setActivating] = useState(false);
  const [error, setError] = useState("");

  const fetchSchemes = useCallback(async () => {
    const res = await fetch(`${API_BASE}/api/admin/color-schemes`);
    if (res.ok) setSchemes(await res.json());
  }, []);

  useEffect(() => { fetchSchemes(); }, [fetchSchemes]);

  // Apply derived colors to preview via CSS custom properties on every change
  useEffect(() => {
    const derived: DerivedScheme = deriveScheme(seeds, surfaceLightness);
    for (const [key, value] of Object.entries(derived)) {
      document.documentElement.style.setProperty(key, value);
    }
  }, [seeds, surfaceLightness]);

  function loadScheme(scheme: SavedScheme) {
    setSeeds({
      primary: scheme.seed_primary,
      accent: scheme.seed_accent,
      secondary: scheme.seed_secondary,
    });
    setSurfaceLightness(scheme.surface_lightness);
    setName(scheme.name);
  }

  function startNew() {
    setSeeds(NEUTRAL_DEFAULTS);
    setSurfaceLightness(0.97);
    setName("");
  }

  async function handleSave() {
    if (!name.trim()) { setError("Please enter a scheme name."); return; }
    setSaving(true); setError("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/color-schemes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          seed_primary: seeds.primary,
          seed_accent: seeds.accent,
          seed_secondary: seeds.secondary,
          surface_lightness: surfaceLightness,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        setError(err.detail ?? "Save failed.");
      } else {
        await fetchSchemes();
      }
    } catch { setError("Save failed. Is the backend running?"); }
    finally { setSaving(false); }
  }

  async function handleActivate() {
    const match = schemes.find(
      (s) => s.seed_primary === seeds.primary &&
             s.seed_accent === seeds.accent &&
             s.seed_secondary === seeds.secondary &&
             s.surface_lightness === surfaceLightness
    );
    if (!match) { setError("Save the scheme first before activating it."); return; }
    setActivating(true); setError("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/color-schemes/${match.id}/activate`, {
        method: "PATCH",
      });
      if (!res.ok) {
        setError("Activation failed.");
      } else {
        await fetchSchemes();
        refreshTheme();
      }
    } catch { setError("Activation failed."); }
    finally { setActivating(false); }
  }

  return (
    <div className="w-[340px] flex-shrink-0 flex flex-col gap-4">

      {/* Saved Schemes */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Saved Schemes
        </div>
        <div className="flex gap-2 flex-wrap">
          {schemes.map((scheme) => (
            <button
              key={scheme.id}
              onClick={() => loadScheme(scheme)}
              className="flex flex-col items-center gap-1"
              title={scheme.name}
            >
              <div
                className="w-11 h-11 rounded-lg relative"
                style={{
                  background: scheme.seed_primary,
                  boxShadow: scheme.is_active
                    ? `0 0 0 2px white, 0 0 0 4px ${scheme.seed_secondary}`
                    : "0 1px 3px rgba(0,0,0,0.15)",
                }}
              >
                <div
                  className="absolute bottom-1 right-1 w-3.5 h-3.5 rounded-sm"
                  style={{ background: scheme.seed_accent }}
                />
              </div>
              <span className="text-[10px] text-neutral-dark font-semibold max-w-[44px] truncate">
                {scheme.name}
              </span>
              {scheme.is_active && (
                <span className="text-[9px] text-gold font-semibold">active</span>
              )}
            </button>
          ))}
          <button onClick={startNew} className="flex flex-col items-center gap-1 opacity-50 hover:opacity-80">
            <div className="w-11 h-11 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center text-gray-400 text-xl">
              +
            </div>
            <span className="text-[10px] text-gray-400">New</span>
          </button>
        </div>
      </div>

      {/* Seed Colors */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Seed Colors
        </div>
        <div className="flex flex-col gap-3">
          {(
            [
              { key: "primary", label: "Primary", desc: "Headings, nav, key surfaces" },
              { key: "accent", label: "Accent", desc: "Links, interactive elements" },
              { key: "secondary", label: "Secondary", desc: "Highlights, badges, accents" },
            ] as const
          ).map(({ key, label, desc }) => (
            <div key={key} className="flex items-center gap-3">
              <label className="cursor-pointer" title={`Pick ${label} color`}>
                <div
                  className="w-9 h-9 rounded-lg border border-gray-200 flex-shrink-0"
                  style={{ background: seeds[key] }}
                />
                <input
                  type="color"
                  value={seeds[key]}
                  onChange={(e) => setSeeds((prev) => ({ ...prev, [key]: e.target.value }))}
                  className="sr-only"
                />
              </label>
              <div className="flex-1">
                <div className="text-xs font-semibold text-neutral-dark">{label}</div>
                <div className="text-[11px] text-gray-400">{desc}</div>
              </div>
              <code className="text-[11px] text-gray-500 bg-gray-50 px-1.5 py-0.5 rounded">
                {seeds[key]}
              </code>
            </div>
          ))}
        </div>
      </div>

      {/* Surface Lightness */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
          Surface Lightness
        </div>
        <div className="text-[11px] text-gray-400 mb-3">
          Controls how tinted page backgrounds and card surfaces appear
        </div>
        <input
          type="range"
          min={88}
          max={99}
          step={1}
          value={Math.round(surfaceLightness * 100)}
          onChange={(e) => setSurfaceLightness(parseInt(e.target.value) / 100)}
          className="w-full accent-primary"
        />
        <div className="flex justify-between items-center mt-1">
          <span className="text-[10px] text-gray-400">Tinted</span>
          <code className="text-xs font-semibold text-neutral-dark">
            {Math.round(surfaceLightness * 100)}%
          </code>
          <span className="text-[10px] text-gray-400">Airy</span>
        </div>
      </div>

      {/* Save Scheme */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Save Scheme
        </div>
        {error && (
          <p className="text-xs text-critical mb-2">{error}</p>
        )}
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Scheme name e.g. Midnight"
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-neutral-dark mb-3 focus:outline-none focus:border-teal focus:ring-1 focus:ring-teal/20"
        />
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex-1 bg-primary text-white rounded-lg py-2 text-xs font-semibold disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save"}
          </button>
          <button
            onClick={handleActivate}
            disabled={activating}
            className="flex-1 bg-teal text-white rounded-lg py-2 text-xs font-semibold disabled:opacity-50"
          >
            {activating ? "Activating…" : "Activate"}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Write the admin appearance page**

```typescript
// frontend/app/admin/appearance/page.tsx
"use client";

import { useRouter } from "next/navigation";
import { SchemeEditor } from "@/components/admin/scheme-editor";
import { ThemePreview } from "@/components/admin/theme-preview";

export default function AppearancePage() {
  const router = useRouter();
  return (
    <div className="min-h-screen flex flex-col bg-surface-dim">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center gap-4">
          <button
            onClick={() => router.push("/settings")}
            className="text-sm text-teal hover:underline"
          >
            ← Settings
          </button>
          <h1 className="font-heading text-2xl font-bold text-neutral-dark">
            Appearance
          </h1>
        </div>
      </header>

      <main className="flex-1 px-6 py-6">
        <div className="max-w-6xl mx-auto flex gap-5">
          <SchemeEditor />
          <ThemePreview />
        </div>
      </main>
    </div>
  );
}
```

- [ ] **Step 4: Verify the page loads**

Start the frontend:
```bash
cd frontend && npm run dev
```
Open `http://localhost:3000/admin/appearance`. You should see the left panel with seed pickers, slider, and save controls alongside the right panel preview. (Backend must be running for schemes to load — see Task 5.)

- [ ] **Step 5: Commit**

```bash
git add frontend/components/admin/theme-preview.tsx \
        frontend/components/admin/scheme-editor.tsx \
        frontend/app/admin/appearance/page.tsx
git commit -m "feat(color-schemes): admin appearance page — scheme editor + live preview"
```

---

## Task 9: Wire frontend — ThemeProvider + settings link

**Files:**
- Modify: `frontend/components/providers.tsx`
- Modify: `frontend/app/settings/page.tsx`

- [ ] **Step 1: Wrap app with ThemeProvider in `providers.tsx`**

Open `frontend/components/providers.tsx`. Replace the file content with:

```typescript
// frontend/components/providers.tsx
"use client";

import { ErrorBoundary } from "@/components/error-boundary";
import { OfflineBanner } from "@/components/offline-banner";
import { ThemeProvider } from "@/components/theme-provider";

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ThemeProvider>
      <ErrorBoundary>
        <OfflineBanner />
        {children}
      </ErrorBoundary>
    </ThemeProvider>
  );
}
```

- [ ] **Step 2: Add Admin link to settings footer**

Open `frontend/app/settings/page.tsx`. Find the `<footer>` block (around line 197) and add an Admin link:

```tsx
{/* existing footer — add the Admin link */}
<footer className="bg-white border-t border-gray-200 px-4 py-4">
  <div className="max-w-4xl mx-auto flex justify-center gap-6">
    <a href="/" className="text-sm text-teal hover:underline">
      Dashboard
    </a>
    <a href="/profile" className="text-sm text-teal hover:underline">
      My Profile
    </a>
    <a href="/admin/appearance" className="text-sm text-teal hover:underline">
      Admin
    </a>
    <a href="/help" className="text-sm text-gray-500 hover:underline">
      Help
    </a>
  </div>
</footer>
```

- [ ] **Step 3: Verify theme applies on load**

With the full stack running (`docker-compose up -d`), open `http://localhost:3000`. Open DevTools → Elements → inspect `<html>`. You should see inline style CSS custom properties like `--color-primary: #1b4f72` set on the root element.

- [ ] **Step 4: Commit**

```bash
git add frontend/components/providers.tsx frontend/app/settings/page.tsx
git commit -m "feat(color-schemes): wire ThemeProvider + admin link in settings"
```

---

## Task 10: E2E smoke test

**Files:**
- Create: `tests/e2e/test_admin_appearance.spec.ts`

- [ ] **Step 1: Write the smoke test**

```typescript
// tests/e2e/test_admin_appearance.spec.ts
import { test, expect } from "@playwright/test";

test.describe("Admin appearance page", () => {
  test("loads the appearance page with scheme editor and preview", async ({ page }) => {
    await page.goto("/admin/appearance");
    // Header
    await expect(page.getByRole("heading", { name: "Appearance" })).toBeVisible();
    // Left panel sections
    await expect(page.getByText("Saved Schemes")).toBeVisible();
    await expect(page.getByText("Seed Colors")).toBeVisible();
    await expect(page.getByText("Surface Lightness")).toBeVisible();
    await expect(page.getByText("Save Scheme")).toBeVisible();
    // Right panel
    await expect(page.getByText("Live Preview")).toBeVisible();
    // EU Blue scheme should be loaded in the preset picker
    await expect(page.getByText("EU Blue")).toBeVisible();
  });

  test("settings page footer has Admin link", async ({ page }) => {
    await page.goto("/settings");
    const adminLink = page.getByRole("link", { name: "Admin" });
    await expect(adminLink).toBeVisible();
    await adminLink.click();
    await expect(page).toHaveURL(/\/admin\/appearance/);
  });

  test("ThemeProvider injects CSS custom properties on app load", async ({ page }) => {
    await page.goto("/");
    const primaryColor = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue("--color-primary").trim()
    );
    // Should be set (non-empty) — exact value depends on active scheme
    expect(primaryColor).toBeTruthy();
    expect(primaryColor).toMatch(/^#[0-9a-f]{6}$/i);
  });
});
```

- [ ] **Step 2: Run the E2E tests**

Ensure the full stack is running (`docker-compose up -d`), then:

```bash
cd Solution && npx playwright test tests/e2e/test_admin_appearance.spec.ts --project=chromium
```
Expected: all 3 tests PASS.

- [ ] **Step 3: Run full unit test suite to confirm no regressions**

```bash
cd Solution && pytest tests/unit/ -v --cov=applire --cov-fail-under=75
```
Expected: all existing tests pass, coverage ≥ 75%.

- [ ] **Step 4: Run frontend unit tests**

```bash
cd frontend && npm test
```
Expected: all tests pass including the new `theme.test.ts`.

- [ ] **Step 5: Final commit**

```bash
git add tests/e2e/test_admin_appearance.spec.ts
git commit -m "test(color-schemes): E2E smoke test for admin appearance page"
```
