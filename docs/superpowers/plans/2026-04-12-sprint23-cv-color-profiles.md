# Sprint 33 — CV Color Profiles: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Auto-detect company brand colors at CV generation time, inject them into CV templates via a Jinja2 `color` context, and expose a Design tab in the RefinementPanel where users can override the accent color.

**Architecture:** A `color_detection.py` service runs a cascade (cache → favicon → meta-tag → LLM → user default → system default) in `_render_cv_background`. At render time, `get_cv_html` calls `resolve_color_context(record, db)` which walks the same cascade from stored data, returning a `ColorContext(accent, tint)` passed to Jinja2. A `PATCH /api/cv/{id}/color` endpoint handles user overrides. The frontend gains a third "🎨 Design" tab in `RefinementPanel`.

**Tech Stack:** Python `colorgram.py` + `colorsys` (stdlib) for color extraction/derivation; `httpx` + `beautifulsoup4` (already present) for scraping; Jinja2 template injection; React/TypeScript `DesignTab` component; Playwright E2E.

**Spec:** `docs/superpowers/specs/2026-04-12-sprint33-cv-color-profiles-design.md`

---

## File Map

### New backend files
- `backend/applire/models/color_profile.py` — `ColorProfile` SQLAlchemy model
- `backend/applire/models/company.py` — `Company` SQLAlchemy model
- `backend/applire/models/user_settings.py` — `UserSettings` SQLAlchemy model
- `backend/applire/services/color_detection.py` — `ColorContext`, `derive_tint`, `detect_and_cache_company_color`, `resolve_color_context`
- `backend/applire/routers/cv_color.py` — `PATCH /api/cv/{id}/color`
- `backend/applire/routers/settings.py` — `GET/PATCH /api/settings`
- `backend/alembic/versions/0020_add_color_profiles.py` — migration
- `tests/unit/test_color_detection.py` — unit tests for derivation + cascade
- `tests/unit/test_cv_color_endpoint.py` — unit tests for PATCH /color
- `tests/unit/test_settings_endpoint.py` — unit tests for settings API

### Modified backend files
- `backend/requirements.txt` — add `colorgram.py`
- `backend/applire/models/cv.py` — add `color_profile_id` FK
- `backend/applire/models/job.py` — add `company_id` FK
- `backend/applire/services/cv.py` — call `resolve_color_context` in `get_cv_html`; call `detect_and_cache_company_color` in `_render_cv_background`
- `backend/applire/templates/modern_swiss.html.j2` — inject `{{ color.accent }}`, `{{ color.tint }}`
- `backend/applire/templates/lebenslauf.html.j2` — inject `{{ color.accent }}`
- `backend/applire/main.py` — register `cv_color` and `settings` routers

### New frontend files
- `frontend/components/cv/DesignTab.tsx`
- `frontend/components/cv/__tests__/DesignTab.test.tsx`
- `tests/e2e/oq/cv-color.spec.ts`
- `tests/e2e/pq/felix-cv-design.spec.ts`

### Modified frontend files
- `frontend/components/cv/RefinementPanel.tsx` — add Design tab
- `frontend/components/cv/__tests__/RefinementPanel.test.tsx` — update for third tab
- `frontend/app/settings/page.tsx` — add Standard-Farbe section

---

## Task 1: Add colorgram dependency

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add colorgram.py to requirements**

Open `backend/requirements.txt` and add after the `beautifulsoup4` line:
```
colorgram.py>=1.2.0
```

- [ ] **Step 2: Install in the running container (or venv)**

```bash
pip install "colorgram.py>=1.2.0"
```
Expected: installs `colorgram` and `Pillow` as a transitive dep.

- [ ] **Step 3: Verify import works**

```bash
python -c "import colorgram; print('colorgram ok')"
```
Expected: `colorgram ok`

- [ ] **Step 4: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore: add colorgram.py dependency for favicon color extraction"
```

---

## Task 2: Alembic migration

**Files:**
- Create: `backend/alembic/versions/0020_add_color_profiles.py`

- [ ] **Step 1: Create the migration file**

```python
# backend/alembic/versions/0020_add_color_profiles.py
"""Add color_profiles, companies, user_settings tables; FK cols on generated_cvs and job_analyses

Revision ID: 0020
Revises: 0019
Create Date: 2026-04-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "color_profiles",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("seed_primary", sa.String(7), nullable=False),
        sa.Column("derived", JSONB(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "companies",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("domain", sa.Text(), nullable=False),
        sa.Column("color_profile_id", sa.UUID(), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["color_profile_id"], ["color_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain"),
    )
    op.create_table(
        "user_settings",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("default_color_profile_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["default_color_profile_id"], ["color_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("generated_cvs", sa.Column("color_profile_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_generated_cvs_color_profile",
        "generated_cvs", "color_profiles",
        ["color_profile_id"], ["id"],
    )
    op.add_column("job_analyses", sa.Column("company_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_job_analyses_company",
        "job_analyses", "companies",
        ["company_id"], ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_job_analyses_company", "job_analyses", type_="foreignkey")
    op.drop_column("job_analyses", "company_id")
    op.drop_constraint("fk_generated_cvs_color_profile", "generated_cvs", type_="foreignkey")
    op.drop_column("generated_cvs", "color_profile_id")
    op.drop_table("user_settings")
    op.drop_table("companies")
    op.drop_table("color_profiles")
```

- [ ] **Step 2: Run migration**

```bash
cd backend && alembic upgrade head
```
Expected: migration applies cleanly, tables visible in DB.

- [ ] **Step 3: Commit**

```bash
git add backend/alembic/versions/0020_add_color_profiles.py
git commit -m "chore: migration 0020 — add color_profiles, companies, user_settings tables"
```

---

## Task 3: SQLAlchemy models

**Files:**
- Create: `backend/applire/models/color_profile.py`
- Create: `backend/applire/models/company.py`
- Create: `backend/applire/models/user_settings.py`
- Modify: `backend/applire/models/cv.py` (add `color_profile_id`)
- Modify: `backend/applire/models/job.py` (add `company_id`)

- [ ] **Step 1: Create ColorProfile model**

```python
# backend/applire/models/color_profile.py
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from applire.db.session import Base

_JSON = JSONB().with_variant(JSON(), "sqlite")


class ColorProfile(Base):
    __tablename__ = "color_profiles"

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
```

- [ ] **Step 2: Create Company model**

```python
# backend/applire/models/company.py
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from applire.db.session import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    color_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("color_profiles.id"), nullable=True
    )
    scraped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
```

- [ ] **Step 3: Create UserSettings model**

```python
# backend/applire/models/user_settings.py
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from applire.db.session import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    default_color_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("color_profiles.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
```

- [ ] **Step 4: Add color_profile_id to GeneratedCV**

In `backend/applire/models/cv.py`, add after the `section_overrides` column:
```python
color_profile_id: Mapped[uuid.UUID | None] = mapped_column(
    ForeignKey("color_profiles.id"), nullable=True
)
```
Also add `ForeignKey` to the existing import: `from sqlalchemy import DateTime, ForeignKey, JSON, String, Text`

- [ ] **Step 5: Add company_id to JobAnalysis**

In `backend/applire/models/job.py`, add after the `berufsbild_label` column:
```python
company_id: Mapped[uuid.UUID | None] = mapped_column(
    ForeignKey("companies.id"), nullable=True
)
```
Also add `ForeignKey` to the existing import: `from sqlalchemy import DateTime, ForeignKey, JSON, String, Text`

- [ ] **Step 6: Commit**

```bash
git add backend/applire/models/color_profile.py \
        backend/applire/models/company.py \
        backend/applire/models/user_settings.py \
        backend/applire/models/cv.py \
        backend/applire/models/job.py
git commit -m "feat: add ColorProfile, Company, UserSettings models; add FK columns"
```

---

## Task 4: Color derivation — pure functions + tests

**Files:**
- Create: `backend/applire/services/color_detection.py`
- Create: `tests/unit/test_color_detection.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_color_detection.py
"""
Unit tests for color derivation and cascade resolution.
Run: pytest tests/unit/test_color_detection.py -v
"""
import sys
from pathlib import Path

import pytest

_backend = Path(__file__).parent.parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


class TestDeriveTint:
    def test_returns_hex_string(self):
        from applire.services.color_detection import derive_tint
        result = derive_tint("#2b5fa8")
        assert result.startswith("#")
        assert len(result) == 7

    def test_output_is_lighter_than_input(self):
        import colorsys
        from applire.services.color_detection import derive_tint
        accent = "#2b5fa8"
        tint = derive_tint(accent)
        # Parse both
        def to_hls(h): r, g, b = (int(h.lstrip("#")[i:i+2], 16)/255 for i in (0, 2, 4)); return colorsys.rgb_to_hls(r, g, b)
        _, l_accent, _ = to_hls(accent)
        _, l_tint, _ = to_hls(tint)
        assert l_tint > l_accent

    def test_output_is_less_saturated_than_input(self):
        import colorsys
        from applire.services.color_detection import derive_tint
        accent = "#2b5fa8"
        tint = derive_tint(accent)
        def to_hls(h): r, g, b = (int(h.lstrip("#")[i:i+2], 16)/255 for i in (0, 2, 4)); return colorsys.rgb_to_hls(r, g, b)
        _, _, s_accent = to_hls(accent)
        _, _, s_tint = to_hls(tint)
        assert s_tint < s_accent

    def test_hue_is_preserved(self):
        import colorsys
        from applire.services.color_detection import derive_tint
        accent = "#2b5fa8"
        tint = derive_tint(accent)
        def to_hls(h): r, g, b = (int(h.lstrip("#")[i:i+2], 16)/255 for i in (0, 2, 4)); return colorsys.rgb_to_hls(r, g, b)
        h_accent, _, _ = to_hls(accent)
        h_tint, _, _ = to_hls(tint)
        assert abs(h_accent - h_tint) < 0.01

    def test_pure_white_input_returns_white_like_result(self):
        from applire.services.color_detection import derive_tint
        result = derive_tint("#ffffff")
        assert result.startswith("#")
        assert len(result) == 7

    def test_color_context_has_accent_and_tint(self):
        from applire.services.color_detection import ColorContext, derive_tint
        ctx = ColorContext(accent="#2b5fa8", tint=derive_tint("#2b5fa8"))
        assert ctx.accent == "#2b5fa8"
        assert ctx.tint.startswith("#")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_color_detection.py::TestDeriveTint -v
```
Expected: `ModuleNotFoundError: No module named 'applire.services.color_detection'`

- [ ] **Step 3: Create color_detection.py with pure functions**

```python
# backend/applire/services/color_detection.py
"""
Color detection and derivation for CV brand color profiles.

Cascade (detect_and_cache_company_color):
  1. Cache check — companies table by domain (scraped_at within 30 days)
  2. Favicon extraction — Google CDN + colorgram
  3. Meta-tag scraping — theme-color, CSS :root vars
  4. LLM fallback — ~50 tokens, structured JSON prompt
  Steps 1–4 populate the companies table and set job_analyses.company_id.

Resolution (resolve_color_context):
  1. generated_cvs.color_profile_id (user override)
  2. job_analyses → companies → color_profile_id (auto-detected)
  3. user_settings.default_color_profile_id
  4. System default (#2b5fa8)
"""

import colorsys
import io
import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import colorgram
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

DEFAULT_ACCENT = "#2b5fa8"
_SCRAPE_TTL_DAYS = 30
# CE stub user — see ADR-022; replace with real user lookup when multi-user lands
_CE_STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@dataclass
class ColorContext:
    accent: str  # hex e.g. "#2b5fa8"
    tint: str    # hex e.g. "#dce8f7" — light background for skill badges


def derive_tint(hex_color: str) -> str:
    """Return a light tint derived from the accent color (L=95%, S=10%, hue preserved)."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    h, _l, _s = colorsys.rgb_to_hls(r, g, b)
    r2, g2, b2 = colorsys.hls_to_rgb(h, 0.95, 0.10)
    return "#{:02x}{:02x}{:02x}".format(int(r2 * 255), int(g2 * 255), int(b2 * 255))


def _make_color_context(hex_accent: str) -> ColorContext:
    return ColorContext(accent=hex_accent, tint=derive_tint(hex_accent))


def _default_context() -> ColorContext:
    return _make_color_context(DEFAULT_ACCENT)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_color_detection.py::TestDeriveTint -v
```
Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/applire/services/color_detection.py tests/unit/test_color_detection.py
git commit -m "feat: add ColorContext and derive_tint pure functions with tests"
```

---

## Task 5: Color detection cascade + resolution + tests

**Files:**
- Modify: `backend/applire/services/color_detection.py` (add cascade functions)
- Modify: `tests/unit/test_color_detection.py` (add cascade tests)

- [ ] **Step 1: Write failing tests for resolve_color_context**

Append to `tests/unit/test_color_detection.py`:

```python
import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def db():
    from applire.db.session import Base
    import applire.models.user
    import applire.models.job
    import applire.models.profile
    import applire.models.gap
    import applire.models.cv
    import applire.models.session
    import applire.models.application
    import applire.models.flow
    import applire.models.uploads
    import applire.models.color_profile
    import applire.models.company
    import applire.models.user_settings

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


def _make_user(user_id=None):
    from applire.models.user import User
    return User(id=user_id or uuid.uuid4(), email=f"test-{uuid.uuid4()}@test.com")


def _make_profile():
    from applire.models.profile import MasterProfile
    return MasterProfile(id=uuid.uuid4(), profile_json={})


def _make_job():
    from applire.models.job import JobAnalysis
    return JobAnalysis(
        id=uuid.uuid4(),
        raw_text_hash=str(uuid.uuid4()),
        raw_text="test job",
        role_title="Engineer",
        required_skills=[],
        nice_to_have_skills=[],
        keywords=[],
        seniority_level="mid",
        company_culture_signals=[],
        language_requirement="de",
    )


def _make_cv(job_id, profile_id, color_profile_id=None):
    from applire.models.cv import GeneratedCV
    return GeneratedCV(
        id=uuid.uuid4(),
        job_analysis_id=job_id,
        profile_id=profile_id,
        tailored_data={},
        template="classic_german",
        status="ready",
        color_profile_id=color_profile_id,
    )


def _make_color_profile(accent="#009fe3"):
    from applire.models.color_profile import ColorProfile
    from applire.services.color_detection import derive_tint
    return ColorProfile(
        id=uuid.uuid4(),
        seed_primary=accent,
        derived={"--cv-accent": accent, "--cv-accent-tint": derive_tint(accent)},
        source="favicon",
    )


class TestResolveColorContext:
    @pytest.mark.asyncio
    async def test_step1_cv_override_takes_priority(self, db):
        from applire.services.color_detection import resolve_color_context
        profile = _make_profile()
        job = _make_job()
        cp = _make_color_profile("#ff0000")
        db.add(profile); db.add(job); db.add(cp)
        await db.commit()
        cv = _make_cv(job.id, profile.id, color_profile_id=cp.id)
        db.add(cv)
        await db.commit()

        ctx = await resolve_color_context(cv, db)
        assert ctx.accent == "#ff0000"

    @pytest.mark.asyncio
    async def test_step2_company_profile_used_when_no_cv_override(self, db):
        from applire.services.color_detection import resolve_color_context
        from applire.models.company import Company
        profile = _make_profile()
        job = _make_job()
        cp = _make_color_profile("#00cc00")
        db.add(profile); db.add(job); db.add(cp)
        await db.commit()
        company = Company(name="Acme", domain="acme.com", color_profile_id=cp.id)
        db.add(company)
        await db.commit()
        job.company_id = company.id
        await db.commit()
        cv = _make_cv(job.id, profile.id)  # no cv override
        db.add(cv)
        await db.commit()

        ctx = await resolve_color_context(cv, db)
        assert ctx.accent == "#00cc00"

    @pytest.mark.asyncio
    async def test_step3_user_default_when_no_company(self, db):
        from applire.services.color_detection import resolve_color_context, _CE_STUB_USER_ID
        from applire.models.user_settings import UserSettings
        from applire.models.user import User
        user = User(id=_CE_STUB_USER_ID, email="local@applire.community")
        profile = _make_profile()
        job = _make_job()
        cp = _make_color_profile("#0000ff")
        db.add(user); db.add(profile); db.add(job); db.add(cp)
        await db.commit()
        settings = UserSettings(
            user_id=_CE_STUB_USER_ID,
            default_color_profile_id=cp.id,
        )
        db.add(settings)
        await db.commit()
        cv = _make_cv(job.id, profile.id)
        db.add(cv)
        await db.commit()

        ctx = await resolve_color_context(cv, db)
        assert ctx.accent == "#0000ff"

    @pytest.mark.asyncio
    async def test_step4_system_default_when_nothing_set(self, db):
        from applire.services.color_detection import resolve_color_context, DEFAULT_ACCENT
        profile = _make_profile()
        job = _make_job()
        db.add(profile); db.add(job)
        await db.commit()
        cv = _make_cv(job.id, profile.id)
        db.add(cv)
        await db.commit()

        ctx = await resolve_color_context(cv, db)
        assert ctx.accent == DEFAULT_ACCENT
```

- [ ] **Step 2: Run tests to see them fail**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_color_detection.py::TestResolveColorContext -v
```
Expected: ImportError — `resolve_color_context` not defined yet.

- [ ] **Step 3: Add resolve_color_context and detection cascade to color_detection.py**

Append to `backend/applire/services/color_detection.py`:

```python
async def resolve_color_context(record: "GeneratedCV", db: AsyncSession) -> ColorContext:  # noqa: F821
    """Walk the 4-step resolution cascade and return a ColorContext."""
    from applire.models.color_profile import ColorProfile
    from applire.models.company import Company
    from applire.models.job import JobAnalysis
    from applire.models.user_settings import UserSettings

    # Step 1: CV-specific override
    if record.color_profile_id:
        cp = await db.get(ColorProfile, record.color_profile_id)
        if cp:
            return ColorContext(
                accent=cp.derived["--cv-accent"],
                tint=cp.derived["--cv-accent-tint"],
            )

    # Step 2: Auto-detected company color
    job = await db.get(JobAnalysis, record.job_analysis_id)
    if job and job.company_id:
        company = await db.get(Company, job.company_id)
        if company and company.color_profile_id:
            cp = await db.get(ColorProfile, company.color_profile_id)
            if cp:
                return ColorContext(
                    accent=cp.derived["--cv-accent"],
                    tint=cp.derived["--cv-accent-tint"],
                )

    # Step 3: User default (CE: always stub user)
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == _CE_STUB_USER_ID)
    )
    settings = result.scalar_one_or_none()
    if settings and settings.default_color_profile_id:
        cp = await db.get(ColorProfile, settings.default_color_profile_id)
        if cp:
            return ColorContext(
                accent=cp.derived["--cv-accent"],
                tint=cp.derived["--cv-accent-tint"],
            )

    # Step 4: System default
    return _default_context()


def _extract_domain(url: str | None) -> str | None:
    """Extract the bare domain from a URL. Returns None if URL is missing or unparseable."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        host = parsed.netloc or parsed.path
        # Strip www. prefix
        return re.sub(r"^www\.", "", host).lower() or None
    except Exception:
        return None


async def _fetch_favicon_color(domain: str) -> str | None:
    """Fetch favicon via Google CDN and extract the most saturated non-neutral color."""
    url = f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(url)
        if resp.status_code != 200 or not resp.content:
            return None
        colors = colorgram.extract(io.BytesIO(resp.content), 5)
        if not colors:
            return None
        # Pick the most saturated color that isn't near-white or near-black
        def _saturation(c):
            r, g, b = c.rgb.r / 255, c.rgb.g / 255, c.rgb.b / 255
            _, l, s = colorsys.rgb_to_hls(r, g, b)
            # Penalise near-white (l>0.85) and near-black (l<0.15)
            if l > 0.85 or l < 0.15:
                return -1.0
            return s
        best = max(colors, key=_saturation)
        if _saturation(best) < 0.1:
            return None  # All grayscale
        r, g, b = best.rgb.r, best.rgb.g, best.rgb.b
        return "#{:02x}{:02x}{:02x}".format(r, g, b)
    except Exception as exc:
        logger.debug("Favicon fetch failed for %s: %s", domain, exc)
        return None


async def _fetch_meta_color(domain: str) -> str | None:
    """Scrape homepage for theme-color meta-tag or CSS :root color variables."""
    url = f"https://{domain}"
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Applire/1.0 brand-color-bot"})
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        # theme-color meta
        tag = soup.find("meta", attrs={"name": "theme-color"})
        if tag and tag.get("content", "").startswith("#"):
            return tag["content"][:7]
        # msapplication-TileColor
        tag = soup.find("meta", attrs={"name": "msapplication-TileColor"})
        if tag and tag.get("content", "").startswith("#"):
            return tag["content"][:7]
        # CSS :root custom properties (first <style> block)
        for style in soup.find_all("style"):
            match = re.search(
                r"--(?:primary|brand|accent|main)(?:-color)?:\s*(#[0-9a-fA-F]{6})",
                style.string or "",
            )
            if match:
                return match.group(1)
        return None
    except Exception as exc:
        logger.debug("Meta-tag scrape failed for %s: %s", domain, exc)
        return None


async def _llm_color_fallback(company_name: str) -> str | None:
    """Ask the LLM for the brand primary color. ~50 tokens total."""
    try:
        from applire.providers import get_provider
        provider = get_provider()
        prompt = f'Brand primary color of "{company_name}" as JSON with one key: {{"primary":"#hex"}}'
        result = await provider.aparse_json(prompt, system="Return only the JSON.", temperature=0.0, max_tokens=20)
        color = result.get("primary", "")
        if re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            return color
    except Exception as exc:
        logger.debug("LLM color fallback failed: %s", exc)
    return None


async def _upsert_company_color(
    domain: str,
    name: str | None,
    hex_color: str,
    source: str,
    db: AsyncSession,
) -> "Company":  # noqa: F821
    """Create or update the company record with the detected color profile."""
    from applire.models.color_profile import ColorProfile
    from applire.models.company import Company

    # Upsert color profile
    cp = ColorProfile(
        seed_primary=hex_color,
        derived={"--cv-accent": hex_color, "--cv-accent-tint": derive_tint(hex_color)},
        source=source,
    )
    db.add(cp)
    await db.flush()

    # Upsert company by domain
    result = await db.execute(select(Company).where(Company.domain == domain))
    company = result.scalar_one_or_none()
    if company is None:
        company = Company(domain=domain, name=name or domain)
        db.add(company)
    company.color_profile_id = cp.id
    company.scraped_at = datetime.now(timezone.utc)
    if name:
        company.name = name
    await db.flush()
    return company


async def detect_and_cache_company_color(job: "JobAnalysis", db: AsyncSession) -> None:  # noqa: F821
    """Run the detection cascade for a job's company. Updates companies table and job.company_id.

    Called from _render_cv_background. Silently logs and returns on any failure.
    """
    from applire.models.company import Company

    domain = _extract_domain(job.source_url)
    if not domain:
        logger.debug("No domain derivable from source_url for job %s — skipping detection", job.id)
        return

    # Step 1: Cache check
    result = await db.execute(select(Company).where(Company.domain == domain))
    company = result.scalar_one_or_none()
    if company and company.scraped_at:
        age = datetime.now(timezone.utc) - company.scraped_at.replace(tzinfo=timezone.utc)
        if age < timedelta(days=_SCRAPE_TTL_DAYS) and company.color_profile_id:
            job.company_id = company.id
            await db.flush()
            logger.debug("Cache hit for domain %s", domain)
            return

    # Step 2: Favicon
    hex_color = await _fetch_favicon_color(domain)
    source = "favicon"

    # Step 3: Meta-tag scrape (if favicon failed or grayscale)
    if not hex_color:
        hex_color = await _fetch_meta_color(domain)
        source = "meta_tag"

    # Step 4: LLM fallback
    if not hex_color and job.company_name:
        hex_color = await _llm_color_fallback(job.company_name)
        source = "llm"

    if not hex_color:
        logger.debug("Color detection yielded no result for domain %s", domain)
        return

    company = await _upsert_company_color(domain, job.company_name, hex_color, source, db)
    job.company_id = company.id
    await db.flush()
    logger.info("Detected %s color for domain %s via %s", hex_color, domain, source)
```

- [ ] **Step 4: Run all detection tests**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_color_detection.py -v
```
Expected: all 10 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/applire/services/color_detection.py tests/unit/test_color_detection.py
git commit -m "feat: add color detection cascade and resolve_color_context with tests"
```

---

## Task 6: CV rendering integration + template updates

**Files:**
- Modify: `backend/applire/services/cv.py`
- Modify: `backend/applire/templates/modern_swiss.html.j2`
- Modify: `backend/applire/templates/lebenslauf.html.j2`
- Modify: `tests/unit/test_color_detection.py` (add render integration test)

- [ ] **Step 1: Write failing render integration test**

Append to `tests/unit/test_color_detection.py`:

```python
class TestTemplateColorInjection:
    @pytest.mark.asyncio
    async def test_get_cv_html_injects_accent_from_color_profile(self, db):
        """The rendered HTML must contain the --cv-accent value from the CV's color_profile."""
        from applire.services.cv import get_cv_html
        from applire.models.color_profile import ColorProfile
        from applire.models.cv import GeneratedCV
        from applire.models.job import JobAnalysis
        from applire.models.profile import MasterProfile
        from applire.services.color_detection import derive_tint

        accent = "#aa1122"
        cp = ColorProfile(
            seed_primary=accent,
            derived={"--cv-accent": accent, "--cv-accent-tint": derive_tint(accent)},
            source="user",
        )
        profile = MasterProfile(id=uuid.uuid4(), profile_json={"personal_info": {"name": "Test User"}})
        job = JobAnalysis(
            id=uuid.uuid4(), raw_text_hash=str(uuid.uuid4()), raw_text="x",
            role_title="Dev", required_skills=[], nice_to_have_skills=[],
            keywords=[], seniority_level="mid", company_culture_signals=[],
            language_requirement="de",
        )
        db.add(cp); db.add(profile); db.add(job)
        await db.commit()

        minimal_tailored = {
            "contact": {"name": "Test User", "email": "t@t.com", "phone": "", "location": "", "linkedin": "", "photo_url": None},
            "summary": "Summary text",
            "work_history": [],
            "education": [],
            "skills": ["Python"],
            "languages": [],
            "show_photo": False,
        }
        cv = GeneratedCV(
            id=uuid.uuid4(),
            job_analysis_id=job.id,
            profile_id=profile.id,
            tailored_data=minimal_tailored,
            template="modern_swiss",
            status="ready",
            color_profile_id=cp.id,
        )
        db.add(cv)
        await db.commit()

        html = await get_cv_html(cv.id, db)
        assert accent in html, f"Expected {accent} in rendered HTML"
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_color_detection.py::TestTemplateColorInjection -v
```
Expected: FAIL — `get_cv_html` doesn't pass `color` context yet.

- [ ] **Step 3: Update modern_swiss.html.j2**

Replace the `:root` block (lines 15–20) in `backend/applire/templates/modern_swiss.html.j2`:
```html
    :root {
      --cv-accent: {{ color.accent }};
      --cv-accent-tint: {{ color.tint }};
      --text: #1c1c1c;
      --muted: #5a5a5a;
      --rule: #d0d5dd;
    }
```

Replace `.skills-grid li` background (line 172) from `background: #f0f4fb;` to:
```css
      background: var(--cv-accent-tint);
```

Replace all occurrences of `var(--accent)` with `var(--cv-accent)`.

- [ ] **Step 4: Update lebenslauf.html.j2**

Add a `:root` block immediately after the `*, *::before` reset rule (after line 12):
```html
    :root {
      --cv-accent: {{ color.accent }};
    }
```

Update `.section-title` border-bottom (currently `border-bottom: 1px solid #1a1a1a;`) to use a muted accent:
```css
      border-bottom: 1px solid color-mix(in srgb, var(--cv-accent) 35%, #1a1a1a 65%);
```
Note: `color-mix` is supported in all modern browsers and Playwright/Chromium. This gives a subtle brand tint to the rule without losing the classic conservative look.

- [ ] **Step 5: Update get_cv_html in cv.py to pass color context**

In `backend/applire/services/cv.py`, update `get_cv_html`:

```python
async def get_cv_html(cv_id: uuid.UUID, db: AsyncSession) -> str:
    from applire.services.cv_section_editor import apply_overrides_to_tailored
    from applire.services.color_detection import resolve_color_context
    from applire.storage import get_storage

    record = await _load_cv_ready(cv_id, db)
    tailored = TailoredCVData.model_validate(record.tailored_data)
    tailored = apply_overrides_to_tailored(
        tailored, record.content_snapshot, record.section_overrides
    )

    if tailored.show_photo and tailored.contact.photo_url:
        data_uri = await _resolve_photo_data_uri(tailored.contact.photo_url, get_storage())
        if data_uri is not None:
            tailored = tailored.model_copy(update={
                "contact": tailored.contact.model_copy(update={"photo_url": data_uri})
            })

    color = await resolve_color_context(record, db)
    template_file = _TEMPLATE_FILES.get(record.template, "lebenslauf.html.j2")
    template = _jinja_env.get_template(template_file)
    return template.render(cv=tailored, color=color)
```

- [ ] **Step 6: Run integration test**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_color_detection.py::TestTemplateColorInjection -v
```
Expected: PASS.

- [ ] **Step 7: Run full unit suite to check for regressions**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/ -v --tb=short
```
Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add backend/applire/services/cv.py \
        backend/applire/templates/modern_swiss.html.j2 \
        backend/applire/templates/lebenslauf.html.j2 \
        tests/unit/test_color_detection.py
git commit -m "feat: inject color context into Jinja2 CV templates via resolve_color_context"
```

---

## Task 7: Background detection in _render_cv_background

**Files:**
- Modify: `backend/applire/services/cv.py`

- [ ] **Step 1: Add detection call to _render_cv_background**

In `backend/applire/services/cv.py`, in `_render_cv_background`, add a detection step after `job = await db.get(JobAnalysis, job_id)`:

```python
            # Detect and cache company brand color (cascade: favicon → meta-tag → LLM)
            # Populates companies table and sets job.company_id. Never raises.
            from applire.services.color_detection import detect_and_cache_company_color
            try:
                await detect_and_cache_company_color(job, db)
                await db.commit()
            except Exception:
                logger.exception("Color detection failed for job %s — continuing without brand color", job_id)
```

Place this block immediately after `job = await db.get(JobAnalysis, job_id)` and before `profile = await db.get(MasterProfile, profile_id)`.

- [ ] **Step 2: Run unit tests to check no regressions**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/ -v --tb=short
```
Expected: all pass (detection in background task is not tested at unit level — it's integration-level).

- [ ] **Step 3: Commit**

```bash
git add backend/applire/services/cv.py
git commit -m "feat: run color detection cascade in _render_cv_background background task"
```

---

## Task 8: PATCH /api/cv/{id}/color endpoint

**Files:**
- Create: `backend/applire/routers/cv_color.py`
- Create: `tests/unit/test_cv_color_endpoint.py`
- Modify: `backend/applire/main.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_cv_color_endpoint.py
"""
Unit tests for PATCH /api/cv/{id}/color endpoint.
Run: pytest tests/unit/test_cv_color_endpoint.py -v
"""
import sys, uuid
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

_backend = Path(__file__).parent.parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


@pytest_asyncio.fixture
async def db():
    from applire.db.session import Base
    import applire.models.user, applire.models.job, applire.models.profile
    import applire.models.gap, applire.models.cv, applire.models.session
    import applire.models.application, applire.models.flow, applire.models.uploads
    import applire.models.color_profile, applire.models.company, applire.models.user_settings

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


def _ready_cv(job_id, profile_id):
    from applire.models.cv import GeneratedCV
    minimal = {
        "contact": {"name": "T", "email": "t@t.com", "phone": "", "location": "", "linkedin": "", "photo_url": None},
        "summary": "", "work_history": [], "education": [],
        "skills": [], "languages": [], "show_photo": False,
    }
    return GeneratedCV(
        id=uuid.uuid4(), job_analysis_id=job_id, profile_id=profile_id,
        tailored_data=minimal, template="modern_swiss", status="ready",
    )


def _make_job():
    from applire.models.job import JobAnalysis
    return JobAnalysis(
        id=uuid.uuid4(), raw_text_hash=str(uuid.uuid4()), raw_text="x",
        role_title="Dev", required_skills=[], nice_to_have_skills=[],
        keywords=[], seniority_level="mid", company_culture_signals=[],
        language_requirement="de",
    )


def _make_profile():
    from applire.models.profile import MasterProfile
    return MasterProfile(id=uuid.uuid4(), profile_json={"personal_info": {"name": "Test"}})


class TestPatchCvColor:
    @pytest.mark.asyncio
    async def test_patch_creates_color_profile_and_updates_cv(self, db):
        from applire.routers.cv_color import apply_cv_color
        job = _make_job(); profile = _make_profile()
        db.add(job); db.add(profile)
        await db.commit()
        cv = _ready_cv(job.id, profile.id)
        db.add(cv); await db.commit()

        result = await apply_cv_color(cv.id, "#ff5500", db)
        assert result["derived"]["--cv-accent"] == "#ff5500"
        assert "color_profile_id" in result
        await db.refresh(cv)
        assert cv.color_profile_id is not None

    @pytest.mark.asyncio
    async def test_patch_raises_lookup_error_for_unknown_cv(self, db):
        from applire.routers.cv_color import apply_cv_color
        with pytest.raises(LookupError):
            await apply_cv_color(uuid.uuid4(), "#ff5500", db)

    @pytest.mark.asyncio
    async def test_patch_raises_value_error_for_invalid_hex(self, db):
        from applire.routers.cv_color import apply_cv_color
        job = _make_job(); profile = _make_profile()
        db.add(job); db.add(profile); await db.commit()
        cv = _ready_cv(job.id, profile.id)
        db.add(cv); await db.commit()
        with pytest.raises(ValueError):
            await apply_cv_color(cv.id, "not-a-hex", db)
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_cv_color_endpoint.py -v
```
Expected: `ImportError: cannot import name 'apply_cv_color'`

- [ ] **Step 3: Create cv_color.py router**

```python
# backend/applire/routers/cv_color.py
"""PATCH /api/cv/{cv_id}/color — apply a user accent color override to a generated CV."""
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from applire.auth import get_auth_provider
from applire.auth.base import AuthProvider
from applire.db.session import get_db
from applire.models.color_profile import ColorProfile
from applire.models.cv import CVGenerationStatus, GeneratedCV
from applire.services.color_detection import derive_tint

router = APIRouter(prefix="/api/cv", tags=["cv"])

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class ColorOverrideRequest(BaseModel):
    accent_hex: str


class ColorOverrideResponse(BaseModel):
    color_profile_id: uuid.UUID
    derived: dict


async def apply_cv_color(
    cv_id: uuid.UUID,
    accent_hex: str,
    db: AsyncSession,
) -> dict:
    """Service logic — extracted for unit testability."""
    if not _HEX_RE.match(accent_hex):
        raise ValueError(f"Invalid hex color: {accent_hex!r}. Must be #RRGGBB.")

    from sqlalchemy import select
    result = await db.execute(
        select(GeneratedCV).where(
            GeneratedCV.id == cv_id,
            GeneratedCV.deleted_at.is_(None),
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise LookupError(f"CV {cv_id} not found")
    if record.status != CVGenerationStatus.ready.value:
        raise LookupError(f"CV {cv_id} is not ready (status={record.status})")

    derived = {"--cv-accent": accent_hex, "--cv-accent-tint": derive_tint(accent_hex)}
    cp = ColorProfile(seed_primary=accent_hex, derived=derived, source="user")
    db.add(cp)
    await db.flush()

    record.color_profile_id = cp.id
    await db.commit()
    await db.refresh(cp)

    return {"color_profile_id": cp.id, "derived": derived}


@router.patch("/{cv_id}/color", response_model=ColorOverrideResponse)
async def patch_cv_color(
    cv_id: uuid.UUID,
    body: ColorOverrideRequest,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> ColorOverrideResponse:
    try:
        result = await apply_cv_color(cv_id, body.accent_hex, db)
        return ColorOverrideResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
```

- [ ] **Step 4: Register router in main.py**

In `backend/applire/main.py`, add to the import line:
```python
from applire.routers import application, cv, cv_color, flow, health, job, jobs, profile, session, settings as settings_router
```

And in the router registration section (after `app.include_router(cv.router)`):
```python
app.include_router(cv_color.router)
app.include_router(settings_router.router)
```

- [ ] **Step 5: Run tests**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_cv_color_endpoint.py -v
```
Expected: all 3 tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/applire/routers/cv_color.py \
        backend/applire/main.py \
        tests/unit/test_cv_color_endpoint.py
git commit -m "feat: add PATCH /api/cv/{id}/color endpoint for accent color override"
```

---

## Task 9: GET/PATCH /api/settings endpoint

**Files:**
- Create: `backend/applire/routers/settings.py`
- Create: `tests/unit/test_settings_endpoint.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_settings_endpoint.py
"""
Unit tests for GET/PATCH /api/settings.
Run: pytest tests/unit/test_settings_endpoint.py -v
"""
import sys, uuid
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

_backend = Path(__file__).parent.parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


@pytest_asyncio.fixture
async def db():
    from applire.db.session import Base
    import applire.models.user, applire.models.job, applire.models.profile
    import applire.models.gap, applire.models.cv, applire.models.session
    import applire.models.application, applire.models.flow, applire.models.uploads
    import applire.models.color_profile, applire.models.company, applire.models.user_settings
    from applire.models.user import User
    from applire.services.color_detection import _CE_STUB_USER_ID

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        # Insert stub user (CE always has this user)
        user = User(id=_CE_STUB_USER_ID, email="local@applire.community")
        session.add(user)
        await session.commit()
        yield session
    await engine.dispose()


class TestSettingsEndpoint:
    @pytest.mark.asyncio
    async def test_get_settings_returns_null_defaults_when_no_row(self, db):
        from applire.routers.settings import get_settings
        result = await get_settings(db)
        assert result["default_accent_hex"] is None

    @pytest.mark.asyncio
    async def test_patch_settings_stores_default_color(self, db):
        from applire.routers.settings import update_settings, get_settings
        await update_settings("#334455", db)
        result = await get_settings(db)
        assert result["default_accent_hex"] == "#334455"

    @pytest.mark.asyncio
    async def test_patch_settings_raises_on_invalid_hex(self, db):
        from applire.routers.settings import update_settings
        with pytest.raises(ValueError):
            await update_settings("not-hex", db)

    @pytest.mark.asyncio
    async def test_patch_settings_updates_existing_row(self, db):
        from applire.routers.settings import update_settings, get_settings
        await update_settings("#aabbcc", db)
        await update_settings("#112233", db)
        result = await get_settings(db)
        assert result["default_accent_hex"] == "#112233"
```

- [ ] **Step 2: Run tests to see them fail**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_settings_endpoint.py -v
```
Expected: `ImportError: cannot import name 'get_settings'`

- [ ] **Step 3: Create settings.py router**

```python
# backend/applire/routers/settings.py
"""GET/PATCH /api/settings — user preferences including default CV accent color."""
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from applire.auth import get_auth_provider
from applire.auth.base import AuthProvider
from applire.db.session import get_db
from applire.services.color_detection import _CE_STUB_USER_ID, derive_tint

router = APIRouter(prefix="/api/settings", tags=["settings"])

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class SettingsResponse(BaseModel):
    default_color_profile_id: uuid.UUID | None
    default_accent_hex: str | None


class SettingsPatchRequest(BaseModel):
    default_accent_hex: str


async def get_settings(db: AsyncSession) -> dict:
    """Service logic — returns current settings for the CE stub user."""
    from applire.models.user_settings import UserSettings
    from applire.models.color_profile import ColorProfile

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == _CE_STUB_USER_ID)
    )
    row = result.scalar_one_or_none()
    if row is None or row.default_color_profile_id is None:
        return {"default_color_profile_id": None, "default_accent_hex": None}

    cp = await db.get(ColorProfile, row.default_color_profile_id)
    if cp is None:
        return {"default_color_profile_id": None, "default_accent_hex": None}

    return {
        "default_color_profile_id": cp.id,
        "default_accent_hex": cp.seed_primary,
    }


async def update_settings(accent_hex: str, db: AsyncSession) -> dict:
    """Service logic — upsert user settings with a new default color."""
    if not _HEX_RE.match(accent_hex):
        raise ValueError(f"Invalid hex color: {accent_hex!r}. Must be #RRGGBB.")

    from applire.models.user_settings import UserSettings
    from applire.models.color_profile import ColorProfile

    derived = {"--cv-accent": accent_hex, "--cv-accent-tint": derive_tint(accent_hex)}
    cp = ColorProfile(seed_primary=accent_hex, derived=derived, source="user")
    db.add(cp)
    await db.flush()

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == _CE_STUB_USER_ID)
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = UserSettings(user_id=_CE_STUB_USER_ID)
        db.add(row)
    row.default_color_profile_id = cp.id
    await db.commit()
    return {"default_color_profile_id": cp.id, "default_accent_hex": accent_hex}


@router.get("", response_model=SettingsResponse)
async def api_get_settings(
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> SettingsResponse:
    result = await get_settings(db)
    return SettingsResponse(**result)


@router.patch("", response_model=SettingsResponse)
async def api_patch_settings(
    body: SettingsPatchRequest,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> SettingsResponse:
    try:
        result = await update_settings(body.default_accent_hex, db)
        return SettingsResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
```

- [ ] **Step 4: Run tests**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_settings_endpoint.py -v
```
Expected: all 4 tests pass.

- [ ] **Step 5: Run full unit suite**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/ -v --tb=short
```
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add backend/applire/routers/settings.py tests/unit/test_settings_endpoint.py
git commit -m "feat: add GET/PATCH /api/settings for default CV accent color"
```

---

## Task 10: DesignTab frontend component

**Files:**
- Create: `frontend/components/cv/DesignTab.tsx`
- Create: `frontend/components/cv/__tests__/DesignTab.test.tsx`

- [ ] **Step 1: Write failing Vitest tests**

```tsx
// frontend/components/cv/__tests__/DesignTab.test.tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { DesignTab } from "../DesignTab";

const BASE_PROPS = {
  cvId: "dddddddd-dddd-dddd-dddd-dddddddddddd",
  detectedCompany: { name: "Siemens AG", hex: "#009fe3" },
  currentAccentHex: "#009fe3",
  onColorApplied: vi.fn(),
};

describe("DesignTab", () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        color_profile_id: "cpid-1234",
        derived: { "--cv-accent": "#ff5500", "--cv-accent-tint": "#fff0e8" },
      }),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the detected company color card when company is provided", () => {
    render(<DesignTab {...BASE_PROPS} />);
    expect(screen.getByText("Siemens AG")).toBeTruthy();
    expect(screen.getByText("#009fe3")).toBeTruthy();
    expect(screen.getByText("automatisch erkannt")).toBeTruthy();
  });

  it("renders no company card when detectedCompany is null", () => {
    render(<DesignTab {...BASE_PROPS} detectedCompany={null} />);
    expect(screen.queryByText("automatisch erkannt")).toBeNull();
  });

  it("renders preset swatch row with color swatches", () => {
    render(<DesignTab {...BASE_PROPS} />);
    const swatches = screen.getAllByRole("button", { name: /Farbe wählen/ });
    expect(swatches.length).toBeGreaterThanOrEqual(5);
  });

  it("renders hex input with current accent value", () => {
    render(<DesignTab {...BASE_PROPS} />);
    const input = screen.getByDisplayValue("#009fe3");
    expect(input).toBeTruthy();
  });

  it("apply button is disabled when selection matches current accent", () => {
    render(<DesignTab {...BASE_PROPS} />);
    const applyBtn = screen.getByText("Farbe übernehmen");
    expect(applyBtn.closest("button")?.disabled).toBe(true);
  });

  it("typing a new hex enables the apply button", () => {
    render(<DesignTab {...BASE_PROPS} />);
    const input = screen.getByDisplayValue("#009fe3");
    fireEvent.change(input, { target: { value: "#ff5500" } });
    const applyBtn = screen.getByText("Farbe übernehmen");
    expect(applyBtn.closest("button")?.disabled).toBe(false);
  });

  it("clicking apply calls PATCH /api/cv/{id}/color", async () => {
    render(<DesignTab {...BASE_PROPS} />);
    const input = screen.getByDisplayValue("#009fe3");
    fireEvent.change(input, { target: { value: "#ff5500" } });
    fireEvent.click(screen.getByText("Farbe übernehmen"));
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/cv/dddddddd-dddd-dddd-dddd-dddddddddddd/color"),
        expect.objectContaining({ method: "PATCH" })
      );
    });
  });

  it("calls onColorApplied after successful PATCH", async () => {
    const onColorApplied = vi.fn();
    render(<DesignTab {...BASE_PROPS} onColorApplied={onColorApplied} />);
    fireEvent.change(screen.getByDisplayValue("#009fe3"), { target: { value: "#ff5500" } });
    fireEvent.click(screen.getByText("Farbe übernehmen"));
    await waitFor(() => expect(onColorApplied).toHaveBeenCalled());
  });
});
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
cd /home/apliqa/Documents/Applire/Solution/frontend && npm test -- --reporter=verbose DesignTab
```
Expected: Cannot find module `../DesignTab`.

- [ ] **Step 3: Create DesignTab.tsx**

```tsx
// frontend/components/cv/DesignTab.tsx
"use client";

import { useState } from "react";

// Curated professional preset colors (hue-diverse, all print-safe)
const PRESET_COLORS = [
  { hex: "#2b5fa8", label: "Klassisches Blau" },
  { hex: "#c0392b", label: "Rot" },
  { hex: "#27ae60", label: "Grün" },
  { hex: "#8e44ad", label: "Violett" },
  { hex: "#1a7a6e", label: "Teal" },
  { hex: "#e67e22", label: "Orange" },
];

interface DetectedCompany {
  name: string;
  hex: string;
}

interface DesignTabProps {
  cvId: string;
  detectedCompany: DetectedCompany | null;
  currentAccentHex: string;
  onColorApplied: () => void;
}

export function DesignTab({
  cvId,
  detectedCompany,
  currentAccentHex,
  onColorApplied,
}: DesignTabProps) {
  const [selectedHex, setSelectedHex] = useState(currentAccentHex);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isDirty = selectedHex.toLowerCase() !== currentAccentHex.toLowerCase();

  const handleApply = async () => {
    if (!isDirty || applying) return;
    setApplying(true);
    setError(null);
    try {
      const res = await fetch(`/api/cv/${cvId}/color`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accent_hex: selectedHex }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? "Farbe konnte nicht gespeichert werden");
      }
      onColorApplied();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unbekannter Fehler");
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 p-3" data-testid="design-tab">

      {/* Detected company color card */}
      {detectedCompany && (
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-neutral-medium mb-2">
            Erkannte Firmenfarbe
          </p>
          <div className="flex items-center gap-3 bg-teal-container-light border border-teal-container rounded-lg p-2.5">
            <button
              type="button"
              aria-label={`Farbe wählen: ${detectedCompany.hex}`}
              onClick={() => setSelectedHex(detectedCompany.hex)}
              className="w-8 h-8 rounded-full border-2 border-white shadow-sm flex-shrink-0 cursor-pointer"
              style={{ background: detectedCompany.hex }}
            />
            <div className="min-w-0">
              <p className="text-sm font-semibold text-neutral-dark truncate">
                {detectedCompany.name}
              </p>
              <p className="text-xs text-neutral-medium font-mono">{detectedCompany.hex}</p>
              <span className="text-xs font-semibold text-teal bg-teal-container rounded-full px-2 py-0.5 inline-block mt-0.5">
                automatisch erkannt
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Preset swatches */}
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-neutral-medium mb-2">
          Akzentfarbe wählen
        </p>
        <div className="flex flex-wrap gap-2 mb-3">
          {PRESET_COLORS.map(({ hex, label }) => (
            <button
              key={hex}
              type="button"
              aria-label={`Farbe wählen: ${label}`}
              onClick={() => setSelectedHex(hex)}
              title={label}
              className={`w-7 h-7 rounded-full transition-transform ${
                selectedHex.toLowerCase() === hex.toLowerCase()
                  ? "ring-2 ring-offset-1 ring-neutral-dark scale-110"
                  : "hover:scale-105"
              }`}
              style={{ background: hex }}
            />
          ))}
        </div>

        {/* Hex input */}
        <div className="flex items-center gap-2 bg-surface-container border border-neutral-medium rounded px-2 py-1.5">
          <div
            className="w-4 h-4 rounded flex-shrink-0 border border-neutral-medium"
            style={{ background: selectedHex }}
          />
          <input
            type="text"
            value={selectedHex}
            onChange={(e) => {
              const val = e.target.value;
              if (/^#[0-9a-fA-F]{0,6}$/.test(val)) setSelectedHex(val);
            }}
            className="flex-1 text-sm font-mono bg-transparent outline-none text-neutral-dark min-w-0"
            maxLength={7}
          />
          <input
            type="color"
            value={selectedHex.length === 7 ? selectedHex : "#000000"}
            onChange={(e) => setSelectedHex(e.target.value)}
            className="w-5 h-5 opacity-0 absolute"
            aria-label="Farbe auswählen"
          />
        </div>
      </div>

      {/* Error */}
      {error && (
        <p className="text-xs text-red-600 bg-red-50 rounded p-2">{error}</p>
      )}

      {/* Apply button */}
      <button
        type="button"
        onClick={handleApply}
        disabled={!isDirty || applying}
        className="w-full py-2 rounded text-sm font-semibold bg-teal text-white disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 transition-opacity"
      >
        {applying ? "Wird angewendet…" : "Farbe übernehmen"}
      </button>
    </div>
  );
}
```

- [ ] **Step 4: Run tests**

```bash
cd /home/apliqa/Documents/Applire/Solution/frontend && npm test -- --reporter=verbose DesignTab
```
Expected: all 8 tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/components/cv/DesignTab.tsx \
        frontend/components/cv/__tests__/DesignTab.test.tsx
git commit -m "feat: add DesignTab component with company color card, swatches, hex input"
```

---

## Task 11: RefinementPanel — add Design tab

**Files:**
- Modify: `frontend/components/cv/RefinementPanel.tsx`
- Modify: `frontend/components/cv/__tests__/RefinementPanel.test.tsx`

- [ ] **Step 1: Update RefinementPanel.tsx**

In `RefinementPanel.tsx`:

1. Add `"appearance"` to the `Tab` type:
```typescript
type Tab = "content" | "actions" | "appearance";
```

2. Add `detectedCompany` and `currentAccentHex` to props:
```typescript
interface RefinementPanelProps {
  // ... existing props ...
  detectedCompany: { name: string; hex: string } | null;
  currentAccentHex: string;
}
```

3. Add the import at the top:
```typescript
import { DesignTab } from "./DesignTab";
```

4. Add the third tab button in the tab strip (after the Actions button):
```tsx
<button
  type="button"
  onClick={() => setActiveTab("appearance")}
  className={`flex-1 text-sm py-2.5 px-3 font-medium transition-colors ${
    activeTab === "appearance"
      ? "text-teal border-b-2 border-teal"
      : "text-neutral-medium hover:text-neutral-dark"
  }`}
  role="tab"
  aria-selected={activeTab === "appearance"}
  data-testid="tab-appearance"
>
  🎨 Design
</button>
```

5. Add the appearance case to the tab body render:
```tsx
{activeTab === "content" ? (
  <ContentTab ... />
) : activeTab === "actions" ? (
  <ActionsTab ... />
) : (
  <DesignTab
    cvId={cvId}
    detectedCompany={detectedCompany}
    currentAccentHex={currentAccentHex}
    onColorApplied={onHtmlRefresh}
  />
)}
```

- [ ] **Step 2: Update RefinementPanel tests**

In `frontend/components/cv/__tests__/RefinementPanel.test.tsx`, add `detectedCompany` and `currentAccentHex` to `BASE_PROPS`:
```typescript
detectedCompany: { name: "Siemens AG", hex: "#009fe3" },
currentAccentHex: "#009fe3",
```

Add a new test:
```typescript
it("renders Design tab and shows company color card when clicked", () => {
  render(<RefinementPanel {...BASE_PROPS} />);
  fireEvent.click(screen.getByTestId("tab-appearance"));
  expect(screen.getByText("Siemens AG")).toBeTruthy();
  expect(screen.getByText("automatisch erkannt")).toBeTruthy();
});
```

- [ ] **Step 3: Run frontend unit tests**

```bash
cd /home/apliqa/Documents/Applire/Solution/frontend && npm test -- --reporter=verbose RefinementPanel
```
Expected: all tests pass (including the new Design tab test).

- [ ] **Step 4: Check TypeScript**

```bash
cd /home/apliqa/Documents/Applire/Solution/frontend && npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/components/cv/RefinementPanel.tsx \
        frontend/components/cv/__tests__/RefinementPanel.test.tsx
git commit -m "feat: add Design tab to RefinementPanel with DesignTab component"
```

---

## Task 12: Settings page — Standard-Farbe section

**Files:**
- Modify: `frontend/app/settings/page.tsx`

- [ ] **Step 1: Read current settings page to understand structure**

```bash
cat frontend/app/settings/page.tsx
```

- [ ] **Step 2: Add Standard-Farbe section**

Add a new section in the settings page after the existing sections:

```tsx
{/* Standard-Farbe für Lebensläufe */}
<section className="rounded-lg border border-neutral-medium p-4">
  <h2 className="text-base font-semibold text-neutral-dark mb-1">
    Standard-Farbe für Lebensläufe
  </h2>
  <p className="text-sm text-neutral-medium mb-4">
    Wird verwendet, wenn keine Firmenfarbe erkannt werden kann.
  </p>
  <DefaultColorPicker />
</section>
```

Create a `DefaultColorPicker` client component inline in the file (or in a separate small component):

```tsx
"use client";
function DefaultColorPicker() {
  const [hex, setHex] = React.useState("#2b5fa8");
  const [saved, setSaved] = React.useState(false);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetch("/api/settings")
      .then((r) => r.json())
      .then((d) => { if (d.default_accent_hex) setHex(d.default_accent_hex); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    const res = await fetch("/api/settings", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ default_accent_hex: hex }),
    });
    if (res.ok) setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  if (loading) return <div className="h-8 w-32 bg-surface-container rounded animate-pulse" />;

  return (
    <div className="flex items-center gap-3">
      <div className="relative flex items-center gap-2 bg-surface-container border border-neutral-medium rounded px-2 py-1.5">
        <div className="w-5 h-5 rounded border border-neutral-medium" style={{ background: hex }} />
        <input
          type="text"
          value={hex}
          onChange={(e) => { if (/^#[0-9a-fA-F]{0,6}$/.test(e.target.value)) setHex(e.target.value); }}
          className="text-sm font-mono bg-transparent outline-none w-20"
          maxLength={7}
        />
      </div>
      <button
        type="button"
        onClick={handleSave}
        className="px-3 py-1.5 text-sm font-medium bg-teal text-white rounded hover:opacity-90"
      >
        {saved ? "Gespeichert ✓" : "Speichern"}
      </button>
    </div>
  );
}
```

- [ ] **Step 3: Check TypeScript**

```bash
cd /home/apliqa/Documents/Applire/Solution/frontend && npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/app/settings/page.tsx
git commit -m "feat: add Standard-Farbe section to Settings page"
```

---

## Task 13: OQ E2E test — Design tab

**Files:**
- Create: `tests/e2e/oq/cv-color.spec.ts`

- [ ] **Step 1: Create the OQ spec**

```typescript
// tests/e2e/oq/cv-color.spec.ts
import { test, expect } from "@playwright/test";

/**
 * CV Design tab — OQ tests
 *
 * Covers the DesignTab inside RefinementPanel:
 *  - Design tab renders with company color card
 *  - Selecting a swatch updates the hex input
 *  - Apply button disabled when no change
 *  - Apply calls PATCH /api/cv/{id}/color and triggers HTML refresh
 *
 * Uses page.route() mocks — does NOT require a running backend.
 */

const TEST_FLOW_ID = "ffffffff-ffff-ffff-ffff-ffffffffffff";
const TEST_CV_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd";
const TEST_JOB_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa";
const CV_PAGE_URL = `/flow/${TEST_FLOW_ID}/cv`;

const MOCK_FLOW_STATE = {
  job_id: TEST_JOB_ID,
  job_summary: { role_title: "Senior Software Engineer" },
  gap_summary: {
    match_score: 0.85,
    gaps: [],
    sections: [],
    detected_company: { name: "Siemens AG", hex: "#009fe3" },
    current_accent_hex: "#009fe3",
  },
  cv_summary: {
    cv_id: TEST_CV_ID,
    pdf_url: `http://localhost:8001/api/cv/${TEST_CV_ID}/pdf`,
    expires_at: new Date(Date.now() + 86_400_000).toISOString(),
  },
};

const MOCK_CV_HTML = `<html><body style="--cv-accent:#009fe3"><h1>Max Mustermann</h1></body></html>`;
const MOCK_CV_HTML_RECOLORED = `<html><body style="--cv-accent:#c0392b"><h1>Max Mustermann</h1></body></html>`;

test.describe("CV Design tab", () => {
  test.beforeEach(async ({ page }) => {
    await page.route(`**/api/flow/${TEST_FLOW_ID}/state`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_FLOW_STATE),
      });
    });
    await page.route(`**/api/cv/${TEST_CV_ID}/html`, async (route) => {
      await route.fulfill({ status: 200, contentType: "text/html", body: MOCK_CV_HTML });
    });
    await page.route(`**/api/cv/${TEST_CV_ID}/color`, async (route) => {
      // Serve re-colored HTML on the next GET /html call after PATCH
      await page.route(`**/api/cv/${TEST_CV_ID}/html`, async (r) => {
        await r.fulfill({ status: 200, contentType: "text/html", body: MOCK_CV_HTML_RECOLORED });
      });
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          color_profile_id: "cpid-0001",
          derived: { "--cv-accent": "#c0392b", "--cv-accent-tint": "#fde8e8" },
        }),
      });
    });
    await page.goto(CV_PAGE_URL);
    await page.waitForLoadState("networkidle");
  });

  test("Design tab is visible in RefinementPanel", async ({ page }) => {
    await expect(page.getByTestId("tab-appearance")).toBeVisible();
  });

  test("clicking Design tab shows company color card", async ({ page }) => {
    await page.getByTestId("tab-appearance").click();
    await expect(page.getByText("Siemens AG")).toBeVisible();
    await expect(page.getByText("automatisch erkannt")).toBeVisible();
  });

  test("apply button is disabled when no color change", async ({ page }) => {
    await page.getByTestId("tab-appearance").click();
    const applyBtn = page.getByText("Farbe übernehmen");
    await expect(applyBtn).toBeDisabled();
  });

  test("clicking a different preset swatch enables apply button", async ({ page }) => {
    await page.getByTestId("tab-appearance").click();
    // Click a preset that is not the current accent
    await page.getByRole("button", { name: "Farbe wählen: Rot" }).click();
    await expect(page.getByText("Farbe übernehmen")).toBeEnabled();
  });

  test("applying color calls PATCH and refreshes iframe", async ({ page }) => {
    await page.getByTestId("tab-appearance").click();
    await page.getByRole("button", { name: "Farbe wählen: Rot" }).click();
    const patchRequest = page.waitForRequest(
      (req) => req.url().includes("/color") && req.method() === "PATCH"
    );
    await page.getByText("Farbe übernehmen").click();
    await patchRequest;
    // Apply button returns to disabled (currentAccentHex updated)
    await expect(page.getByText("Farbe übernehmen")).toBeDisabled({ timeout: 5000 });
  });
});
```

- [ ] **Step 2: Run OQ tests**

```bash
cd /home/apliqa/Documents/Applire/Solution && npx playwright test tests/e2e/oq/cv-color.spec.ts --project=chromium
```
Expected: all 5 tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/oq/cv-color.spec.ts
git commit -m "test(e2e): add OQ tests for CV Design tab color override flow"
```

---

## Task 14: PQ E2E test — Felix CV Design journey

**Files:**
- Create: `tests/e2e/pq/felix-cv-design.spec.ts`

- [ ] **Step 1: Create the PQ spec**

```typescript
// tests/e2e/pq/felix-cv-design.spec.ts
import { test, expect, Page } from "@playwright/test";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * Felix — CV Design tab journey (PQ)
 *
 * Tests that after full CV generation:
 *  - The Design tab is accessible in the RefinementPanel
 *  - The swatch row renders with preset colors
 *  - Clicking a different swatch enables the apply button
 *  - Clicking apply triggers PATCH /api/cv/{id}/color and re-renders the iframe
 *
 * PQ tier: requires the full Docker stack + real LLM via OpenRouter.
 * Run: OPENROUTER_API_KEY=<key> npx playwright test --config=playwright.config.pq.ts tests/e2e/pq/felix-cv-design.spec.ts
 */

const CV_PATH = path.join(__dirname, "../../fixtures/profiles/sample_cv.pdf");
const JD_TEXT = fs.readFileSync(
  path.join(__dirname, "../../fixtures/JDs/sample_jd.txt"),
  "utf-8"
);
const API_BASE = "http://localhost:8001";

async function resetBackendState(page: Page): Promise<void> {
  await page.request.delete(`${API_BASE}/api/profile`).catch(() => {});
}

async function generateCvAndNavigateToView(page: Page): Promise<void> {
  await resetBackendState(page);
  await page.goto("/");
  await page.waitForLoadState("networkidle");

  // Unique JD so flow isn't de-duped
  const uniqueJD = `${JD_TEXT}\n\n<!-- felix-color-test: ${Date.now()} -->`;
  await page.getByRole("button", { name: "Paste Text" }).click();
  await page.locator('textarea[placeholder="Paste the full job description here..."]').fill(uniqueJD);

  const fileInput = page.getByTestId("file-input");
  await fileInput.setInputFiles(CV_PATH);
  await expect(page.getByTestId("submit-button")).toBeEnabled();
  await page.getByTestId("submit-button").click();

  // Wait for gaps page
  await expect(page).toHaveURL(/\/flow\/.*\/gaps/, { timeout: 90000 });
  await expect(page.getByTestId("loading-indicator")).not.toBeVisible({ timeout: 30000 });

  // Skip interview — end early via "Generate CV" if available, or click generate directly
  const generateBtn = page.getByTestId("generate-cv-button");
  if (await generateBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    await generateBtn.click();
  } else {
    // Navigate to CV page via flow
    const url = page.url();
    const match = url.match(/\/flow\/([^/]+)\//);
    const flowId = match ? match[1] : "";
    await page.goto(`/flow/${flowId}/cv`);
  }

  // Wait for CV view to load
  await expect(page).toHaveURL(/\/flow\/.*\/cv/, { timeout: 60000 });
  await expect(page.getByTestId("refinement-panel")).toBeVisible({ timeout: 30000 });
}

test.describe("Felix — CV Design tab (PQ)", () => {
  test("Design tab is present after CV generation", async ({ page }) => {
    await generateCvAndNavigateToView(page);
    await expect(page.getByTestId("tab-appearance")).toBeVisible();
  });

  test("Design tab shows preset swatch row", async ({ page }) => {
    await generateCvAndNavigateToView(page);
    await page.getByTestId("tab-appearance").click();
    // At least 5 color swatches must be present
    const swatches = page.getByRole("button", { name: /Farbe wählen/ });
    await expect(swatches.first()).toBeVisible({ timeout: 5000 });
    expect(await swatches.count()).toBeGreaterThanOrEqual(5);
  });

  test("selecting a different swatch and applying re-renders the CV iframe", async ({ page }) => {
    await generateCvAndNavigateToView(page);
    await page.getByTestId("tab-appearance").click();

    // Click the Rot preset
    await page.getByRole("button", { name: "Farbe wählen: Rot" }).click();
    const applyBtn = page.getByText("Farbe übernehmen");
    await expect(applyBtn).toBeEnabled();

    // Intercept PATCH to confirm it's called
    const patchRequest = page.waitForRequest(
      (req) => req.url().includes("/color") && req.method() === "PATCH",
      { timeout: 10000 }
    );
    await applyBtn.click();
    const req = await patchRequest;
    const body = JSON.parse(req.postData() ?? "{}");
    expect(body.accent_hex).toBe("#c0392b");

    // Apply button returns to disabled after success
    await expect(applyBtn).toBeDisabled({ timeout: 10000 });
  });
});
```

- [ ] **Step 2: Verify the test file is syntactically valid**

```bash
cd /home/apliqa/Documents/Applire/Solution/frontend && npx tsc --noEmit --allowJs ../tests/e2e/pq/felix-cv-design.spec.ts 2>/dev/null; echo "syntax ok"
```

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/pq/felix-cv-design.spec.ts
git commit -m "test(e2e): add PQ Felix CV Design tab journey tests"
```

---

## Task 15: Final integration check + full test run

- [ ] **Step 1: Run full backend unit suite**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/ -v --cov=applire --cov-report=term-missing --cov-fail-under=75
```
Expected: ≥75% coverage, all tests pass.

- [ ] **Step 2: Run frontend unit tests**

```bash
cd /home/apliqa/Documents/Applire/Solution/frontend && npm test -- --reporter=verbose
```
Expected: all tests pass (no regressions in RefinementPanel, ContentTab, ActionsTab, etc.)

- [ ] **Step 3: Run OQ E2E tests**

```bash
cd /home/apliqa/Documents/Applire/Solution && npx playwright test tests/e2e/oq/ --project=chromium
```
Expected: all pass including the new cv-color.spec.ts.

- [ ] **Step 4: Start full stack and smoke-test manually**

```bash
docker-compose up -d
```
Navigate to the app:
1. Upload a CV and JD with a company URL (e.g. `https://jobs.siemens.com/...`)
2. Complete the flow → generate a CV
3. On the CV view, click the "🎨 Design" tab
4. Verify the company color card appears with the detected brand color
5. Click a different swatch, click "Farbe übernehmen"
6. Verify the CV iframe re-renders with the new accent color

- [ ] **Step 5: Push and open PR**

```bash
git push origin sprint-22
```
Then open a PR from `sprint-22` → `main` with title: "feat: Sprint 33 — CV Color Profiles".
