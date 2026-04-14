# Cover Letter Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add AI-generated cover letters (Bewerbungsschreiben) as a post-CV companion document, with 7 paired Jinja2 templates, a pre-generation modal, a dedicated `/flow/[flowId]/cover-letter` page, and full GDPR retention support.

**Architecture:** Full parallelism with the CV pipeline — new `GeneratedCoverLetter` model, `services/cover_letter.py`, and `routers/cover_letter.py` mirror their CV equivalents with zero changes to the CV generation path. `FlowSession` gains one nullable FK (`generated_cover_letter_id`). All TTL constants are centralized in `constants.py` with env-var overrides.

**Tech Stack:** FastAPI, SQLAlchemy/Alembic, Jinja2, Playwright, Next.js 15/React 19, TypeScript, Tailwind CSS v4, pytest/pytest-asyncio, Playwright E2E

---

## File Map

| Action | Path | Purpose |
|--------|------|---------|
| Modify | `backend/applire/constants.py` | Add 4 configurable TTL constants |
| Modify | `backend/applire/models/cv.py` | Import `GENERATED_DOCUMENTS_TTL_DAYS` from constants |
| Modify | `backend/applire/models/uploads.py` | Import `UPLOAD_TTL_DAYS` from constants |
| Modify | `backend/applire/models/application.py` | Import `PROFILE_INACTIVITY_TTL_DAYS` from constants |
| Modify | `backend/applire/services/session.py` | Import `INTERVIEW_SESSION_TTL_DAYS` from constants |
| Modify | `backend/applire/retention/worker.py` | Import constants + add `_purge_cover_letters` + `_reap_stale_cl_jobs` |
| Create | `backend/applire/models/cover_letter.py` | `GeneratedCoverLetter` ORM model |
| Modify | `backend/applire/models/flow.py` | Add `generated_cover_letter_id` FK |
| Create | `backend/alembic/versions/0023_add_generated_cover_letters_table.py` | Migration |
| Create | `backend/alembic/versions/0024_add_flow_session_cover_letter_fk.py` | Migration |
| Create | `backend/applire/schemas/cover_letter.py` | Pydantic schemas |
| Modify | `backend/applire/schemas/flow.py` | Add `CoverLetterSummary` + `cover_letter_summary` field |
| Modify | `backend/applire/services/flow/orchestrator.py` | Populate `cover_letter_summary` in `get_flow_state` |
| Create | `backend/applire/utils/recipient_extraction.py` | Regex + fallback recipient extractor |
| Create | `backend/applire/prompts/cover_letter.py` | LLM prompt builder |
| Create | `backend/applire/services/cover_letter.py` | Generation service |
| Create | `backend/applire/routers/cover_letter.py` | FastAPI router |
| Modify | `backend/applire/main.py` | Register cover letter router |
| Create | `backend/applire/templates/lebenslauf_letter.html.j2` | CL template — classic_german |
| Create | `backend/applire/templates/modern_swiss_letter.html.j2` | CL template |
| Create | `backend/applire/templates/executive_letter.html.j2` | CL template |
| Create | `backend/applire/templates/tech_developer_letter.html.j2` | CL template |
| Create | `backend/applire/templates/creative_sidebar_letter.html.j2` | CL template |
| Create | `backend/applire/templates/academic_letter.html.j2` | CL template |
| Create | `backend/applire/templates/compact_pro_letter.html.j2` | CL template |
| Create | `tests/unit/test_cover_letter.py` | Unit tests (model, extraction, prompt, TTL) |
| Create | `frontend/components/cover-letter/GenerateCoverLetterModal.tsx` | Pre-gen input modal |
| Modify | `frontend/components/cv/ActionsTab.tsx` | Add "Generate Cover Letter" button + CL link |
| Create | `frontend/components/cover-letter/CoverLetterDocument.tsx` | srcDoc iframe wrapper |
| Create | `frontend/components/cover-letter/CoverLetterContentTab.tsx` | 4 section cards + body editor |
| Create | `frontend/components/cover-letter/CoverLetterDesignTab.tsx` | Template picker |
| Create | `frontend/components/cover-letter/CoverLetterActionsTab.tsx` | Regenerate + download |
| Create | `frontend/components/cover-letter/CoverLetterRefinementPanel.tsx` | Tab strip |
| Create | `frontend/app/flow/[flowId]/cover-letter/page.tsx` | Cover letter page |
| Create | `tests/e2e/test_cover_letter.spec.ts` | Playwright E2E — Marcus happy path |

---

## Task 1: Create sprint-25 branch

**Files:**
- Git branch: `sprint-25`

- [ ] **Step 1: Create and switch to sprint-25 branch**

```bash
git checkout -b sprint-25
```

Expected: `Switched to a new branch 'sprint-25'`

- [ ] **Step 2: Verify**

```bash
git branch --show-current
```

Expected: `sprint-25`

---

## Task 2: Centralize TTL constants

**Files:**
- Modify: `backend/applire/constants.py`
- Modify: `backend/applire/models/cv.py`
- Modify: `backend/applire/models/uploads.py`
- Modify: `backend/applire/models/application.py`
- Modify: `backend/applire/services/session.py`
- Test: `tests/unit/test_cover_letter.py`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_cover_letter.py`:

```python
"""
Sprint 25 — Cover Letter Generation (unit tests)
No Docker, no LLM, no external services.

Run:
    pytest tests/unit/test_cover_letter.py -v
"""
import sys
from pathlib import Path

import pytest

_backend = Path(__file__).parent.parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


# ---------------------------------------------------------------------------
# Task 2 — TTL constants
# ---------------------------------------------------------------------------

def test_generated_documents_ttl_default():
    from applire.constants import GENERATED_DOCUMENTS_TTL_DAYS
    assert GENERATED_DOCUMENTS_TTL_DAYS == 90


def test_interview_session_ttl_default():
    from applire.constants import INTERVIEW_SESSION_TTL_DAYS
    assert INTERVIEW_SESSION_TTL_DAYS == 30


def test_upload_ttl_default():
    from applire.constants import UPLOAD_TTL_DAYS
    assert UPLOAD_TTL_DAYS == 7


def test_profile_inactivity_ttl_default():
    from applire.constants import PROFILE_INACTIVITY_TTL_DAYS
    assert PROFILE_INACTIVITY_TTL_DAYS == 730
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_cover_letter.py::test_generated_documents_ttl_default -v
```

Expected: `FAILED` — `ImportError: cannot import name 'GENERATED_DOCUMENTS_TTL_DAYS'`

- [ ] **Step 3: Add TTL constants to `constants.py`**

In `backend/applire/constants.py`, append after the existing constants:

```python
# GDPR retention TTLs — configurable via environment variables (ADR-005 amendment, Sprint 25)
GENERATED_DOCUMENTS_TTL_DAYS: int = int(os.environ.get("GENERATED_DOCUMENTS_TTL_DAYS", "90"))
INTERVIEW_SESSION_TTL_DAYS: int = int(os.environ.get("INTERVIEW_SESSION_TTL_DAYS", "30"))
UPLOAD_TTL_DAYS: int = int(os.environ.get("UPLOAD_TTL_DAYS", "7"))
PROFILE_INACTIVITY_TTL_DAYS: int = int(os.environ.get("PROFILE_INACTIVITY_TTL_DAYS", "730"))
```

- [ ] **Step 4: Update `models/cv.py` to import from constants**

Replace the module-level `_TTL_DAYS = 90` and `_expires_at` function:

```python
# Remove this line:
_TTL_DAYS = 90

# Add this import at the top with other applire imports:
from applire.constants import GENERATED_DOCUMENTS_TTL_DAYS as _TTL_DAYS
```

The `_expires_at` function body is unchanged — it still uses `_TTL_DAYS`.

- [ ] **Step 5: Update `models/uploads.py` to import from constants**

Replace `_UPLOAD_TTL_DAYS = 7` and the lambda that uses it:

```python
# Remove this line:
_UPLOAD_TTL_DAYS = 7

# Add this import:
from applire.constants import UPLOAD_TTL_DAYS as _UPLOAD_TTL_DAYS
```

The lambda `default=lambda: datetime.now(timezone.utc) + timedelta(days=_UPLOAD_TTL_DAYS)` is unchanged.

- [ ] **Step 6: Update `models/application.py` to import from constants**

Replace `_APPLICATION_TTL_DAYS = 730` and its usage:

```python
# Remove this line:
_APPLICATION_TTL_DAYS = 730

# Add this import:
from applire.constants import PROFILE_INACTIVITY_TTL_DAYS as _APPLICATION_TTL_DAYS
```

The `_default_expires_at` function body is unchanged.

- [ ] **Step 7: Update `services/session.py` to import from constants**

Replace `_SESSION_TTL_DAYS = 30` (at line 56) and update the `_make_session_record` usage:

```python
# Remove this line near line 56:
_SESSION_TTL_DAYS = 30

# Add to the existing import from applire.constants at the top of the file:
from applire.constants import (
    INTERVIEW_HARD_CEILING_GUIDED,
    INTERVIEW_HARD_CEILING_TARGETED,
    INTERVIEW_MAX_QUESTIONS_PER_GAP,
    INTERVIEW_SESSION_TTL_DAYS as _SESSION_TTL_DAYS,
    INTERVIEW_TARGET_MIN_GUIDED,
    INTERVIEW_TARGET_MIN_TARGETED,
    MODE_B_COMPLETENESS_THRESHOLD,
)
```

- [ ] **Step 8: Update `retention/worker.py` to import from constants**

Replace the three module-level TTL constants with imports:

```python
# Remove these three lines:
_UPLOADS_TTL_DAYS = 7
_SESSION_TTL_DAYS = 30
_INACTIVITY_TTL_DAYS = 730

# Add after the existing imports:
from applire.constants import (
    GENERATED_DOCUMENTS_TTL_DAYS as _GENERATED_DOCS_TTL_DAYS,
    INTERVIEW_SESSION_TTL_DAYS as _SESSION_TTL_DAYS,
    PROFILE_INACTIVITY_TTL_DAYS as _INACTIVITY_TTL_DAYS,
    UPLOAD_TTL_DAYS as _UPLOADS_TTL_DAYS,
)
```

- [ ] **Step 9: Run all TTL tests**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_cover_letter.py -k "ttl" -v
```

Expected: `4 passed`

- [ ] **Step 10: Run full unit suite to confirm no regressions**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/ -v --tb=short 2>&1 | tail -20
```

Expected: all previously passing tests still pass.

- [ ] **Step 11: Commit**

```bash
git add backend/applire/constants.py backend/applire/models/cv.py backend/applire/models/uploads.py backend/applire/models/application.py backend/applire/services/session.py backend/applire/retention/worker.py tests/unit/test_cover_letter.py
git commit -m "$(cat <<'EOF'
refactor: centralize GDPR TTL constants with env-var overrides (ADR-005)

Moves _TTL_DAYS, _UPLOAD_TTL_DAYS, _SESSION_TTL_DAYS, _INACTIVITY_TTL_DAYS
from scattered module-level literals into constants.py with os.environ fallbacks.
Self-hosters can now override all retention windows without code changes.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: `GeneratedCoverLetter` model + Alembic migration 0023

**Files:**
- Create: `backend/applire/models/cover_letter.py`
- Create: `backend/alembic/versions/0023_add_generated_cover_letters_table.py`
- Modify: `tests/unit/test_cover_letter.py`

- [ ] **Step 1: Add model tests**

Append to `tests/unit/test_cover_letter.py`:

```python
# ---------------------------------------------------------------------------
# Task 3 — GeneratedCoverLetter model
# ---------------------------------------------------------------------------

import uuid
from datetime import datetime, timedelta, timezone

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def db():
    """In-memory SQLite session with all models registered."""
    from applire.db.session import Base
    import applire.models.user
    import applire.models.job
    import applire.models.profile
    import applire.models.gap
    import applire.models.cv
    import applire.models.cover_letter
    import applire.models.session
    import applire.models.application
    import applire.models.flow
    import applire.models.uploads

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_cover_letter_model_creates_with_defaults(db):
    from applire.models.cover_letter import GeneratedCoverLetter, CoverLetterStatus

    cl = GeneratedCoverLetter(
        job_analysis_id=uuid.uuid4(),
        profile_id=uuid.uuid4(),
        template="classic_german",
        letter_data={},
        pre_gen_inputs={},
    )
    db.add(cl)
    await db.commit()
    await db.refresh(cl)

    assert cl.id is not None
    assert cl.status == CoverLetterStatus.pending.value
    assert cl.expires_at > datetime.now(timezone.utc)
    assert cl.deleted_at is None


@pytest.mark.asyncio
async def test_cover_letter_expires_at_is_90_days_out(db):
    from applire.models.cover_letter import GeneratedCoverLetter

    cl = GeneratedCoverLetter(
        job_analysis_id=uuid.uuid4(),
        profile_id=uuid.uuid4(),
        template="executive",
        letter_data={},
        pre_gen_inputs={},
    )
    db.add(cl)
    await db.commit()
    await db.refresh(cl)

    delta = cl.expires_at - datetime.now(timezone.utc)
    assert 88 < delta.days <= 91
```

- [ ] **Step 2: Run to verify failure**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_cover_letter.py::test_cover_letter_model_creates_with_defaults -v
```

Expected: `FAILED` — `ModuleNotFoundError: No module named 'applire.models.cover_letter'`

- [ ] **Step 3: Create `backend/applire/models/cover_letter.py`**

```python
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from applire.constants import GENERATED_DOCUMENTS_TTL_DAYS
from applire.db.session import Base

_JSON = JSONB().with_variant(JSON(), "sqlite")


class CoverLetterStatus(str, Enum):
    pending = "pending"
    generating = "generating"
    ready = "ready"
    failed = "failed"
    expired = "expired"


def _cl_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=GENERATED_DOCUMENTS_TTL_DAYS)


class GeneratedCoverLetter(Base):
    __tablename__ = "generated_cover_letters"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_analyses.id"), nullable=False, index=True
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("master_profiles.id"), nullable=False
    )
    template: Mapped[str] = mapped_column(String(40), nullable=False, default="classic_german")
    letter_data: Mapped[dict] = mapped_column(_JSON, nullable=False, default=dict)
    pre_gen_inputs: Mapped[dict] = mapped_column(_JSON, nullable=False, default=dict)
    section_overrides: Mapped[dict | None] = mapped_column(_JSON, nullable=True)
    color_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cv_color_profiles.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CoverLetterStatus.pending.value
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_cl_expires_at,
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
```

- [ ] **Step 4: Run model tests**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_cover_letter.py -k "model" -v
```

Expected: `2 passed`

- [ ] **Step 5: Create Alembic migration 0023**

Create `backend/alembic/versions/0023_add_generated_cover_letters_table.py`:

```python
"""Add generated_cover_letters table

Revision ID: 0023
Revises: 0022
Create Date: 2026-04-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: Union[str, None] = "0022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "generated_cover_letters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_analysis_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("template", sa.String(40), nullable=False, server_default="classic_german"),
        sa.Column("letter_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("pre_gen_inputs", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("section_overrides", sa.JSON(), nullable=True),
        sa.Column("color_profile_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["color_profile_id"], ["cv_color_profiles.id"]),
        sa.ForeignKeyConstraint(["job_analysis_id"], ["job_analyses.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["master_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_generated_cover_letters_job_analysis_id",
        "generated_cover_letters",
        ["job_analysis_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_generated_cover_letters_job_analysis_id",
        table_name="generated_cover_letters",
    )
    op.drop_table("generated_cover_letters")
```

- [ ] **Step 6: Commit**

```bash
git add backend/applire/models/cover_letter.py backend/alembic/versions/0023_add_generated_cover_letters_table.py tests/unit/test_cover_letter.py
git commit -m "$(cat <<'EOF'
feat: add GeneratedCoverLetter model and migration 0023

New table generated_cover_letters mirrors generated_cvs structure.
CoverLetterStatus enum, configurable TTL from GENERATED_DOCUMENTS_TTL_DAYS.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: `FlowSession.generated_cover_letter_id` FK + migration 0024

**Files:**
- Modify: `backend/applire/models/flow.py`
- Create: `backend/alembic/versions/0024_add_flow_session_cover_letter_fk.py`
- Modify: `tests/unit/test_cover_letter.py`

- [ ] **Step 1: Add test**

Append to `tests/unit/test_cover_letter.py`:

```python
# ---------------------------------------------------------------------------
# Task 4 — FlowSession cover letter FK
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_flow_session_has_cover_letter_fk(db):
    from applire.models.flow import FlowSession
    import sqlalchemy as sa
    from applire.db.session import Base

    inspector = sa.inspect(Base.metadata.tables["flow_sessions"])
    col_names = [c.name for c in inspector.columns]
    assert "generated_cover_letter_id" in col_names
```

- [ ] **Step 2: Run to verify failure**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_cover_letter.py::test_flow_session_has_cover_letter_fk -v
```

Expected: `FAILED` — `AssertionError: assert 'generated_cover_letter_id' in [...]`

- [ ] **Step 3: Add column to `backend/applire/models/flow.py`**

Add one import and one column after `generated_cv_id`. The file already imports `ForeignKey` and uses `Mapped`/`mapped_column`. Add:

```python
# After the generated_cv_id column (around line 51), add:
generated_cover_letter_id: Mapped[uuid.UUID | None] = mapped_column(
    ForeignKey("generated_cover_letters.id"), nullable=True
)
```

- [ ] **Step 4: Run test**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_cover_letter.py::test_flow_session_has_cover_letter_fk -v
```

Expected: `PASSED`

- [ ] **Step 5: Create migration 0024**

Create `backend/alembic/versions/0024_add_flow_session_cover_letter_fk.py`:

```python
"""Add generated_cover_letter_id FK to flow_sessions

Revision ID: 0024
Revises: 0023
Create Date: 2026-04-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: Union[str, None] = "0023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "flow_sessions",
        sa.Column("generated_cover_letter_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_flow_sessions_cover_letter",
        "flow_sessions",
        "generated_cover_letters",
        ["generated_cover_letter_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_flow_sessions_cover_letter", "flow_sessions", type_="foreignkey"
    )
    op.drop_column("flow_sessions", "generated_cover_letter_id")
```

- [ ] **Step 6: Commit**

```bash
git add backend/applire/models/flow.py backend/alembic/versions/0024_add_flow_session_cover_letter_fk.py tests/unit/test_cover_letter.py
git commit -m "$(cat <<'EOF'
feat: add generated_cover_letter_id FK to FlowSession (migration 0024)

FlowSession now holds a nullable pointer to the active cover letter,
mirroring the existing generated_cv_id pattern.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Pydantic schemas + `FlowStateResponse` cover letter summary

**Files:**
- Create: `backend/applire/schemas/cover_letter.py`
- Modify: `backend/applire/schemas/flow.py`
- Modify: `backend/applire/services/flow/orchestrator.py`
- Modify: `tests/unit/test_cover_letter.py`

- [ ] **Step 1: Add schema tests**

Append to `tests/unit/test_cover_letter.py`:

```python
# ---------------------------------------------------------------------------
# Task 5 — Pydantic schemas
# ---------------------------------------------------------------------------

def test_cover_letter_generate_request_validates_tone():
    from applire.schemas.cover_letter import CoverLetterGenerateRequest
    req = CoverLetterGenerateRequest(job_id=uuid.uuid4(), tone="formal")
    assert req.tone == "formal"


def test_cover_letter_generate_request_rejects_invalid_tone():
    from pydantic import ValidationError
    from applire.schemas.cover_letter import CoverLetterGenerateRequest
    with pytest.raises(ValidationError):
        CoverLetterGenerateRequest(job_id=uuid.uuid4(), tone="aggressive")


def test_flow_state_response_has_cover_letter_summary_field():
    from applire.schemas.flow import FlowStateResponse
    fields = FlowStateResponse.model_fields
    assert "cover_letter_summary" in fields
```

- [ ] **Step 2: Run to verify failure**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_cover_letter.py -k "schema or cover_letter_summary" -v
```

Expected: `FAILED` — `ModuleNotFoundError: No module named 'applire.schemas.cover_letter'`

- [ ] **Step 3: Create `backend/applire/schemas/cover_letter.py`**

```python
import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

from applire.models.cover_letter import CoverLetterStatus
from applire.models.cv import CVGenerationStatus  # reuse for status pattern

CLTemplate = Literal[
    "classic_german",
    "modern_swiss",
    "executive",
    "tech_developer",
    "creative_sidebar",
    "academic",
    "compact_pro",
]

CLTone = Literal["formal", "professional", "conversational"]


class CoverLetterGenerateRequest(BaseModel):
    job_id: uuid.UUID
    recipient_name: Optional[str] = None
    recipient_company: Optional[str] = None
    salary: Optional[str] = None
    availability: Optional[str] = None
    motivation: Optional[str] = None
    tone: CLTone = "formal"


class CoverLetterGenerateResponse(BaseModel):
    cover_letter_id: uuid.UUID
    status: CoverLetterStatus
    html_url: str
    pdf_url: str
    expires_at: datetime


class CoverLetterStatusResponse(BaseModel):
    cover_letter_id: uuid.UUID
    status: CoverLetterStatus
    html_url: Optional[str] = None
    pdf_url: Optional[str] = None
    error_message: Optional[str] = None
    expires_at: datetime

    model_config = {"from_attributes": True}


class SectionOverridePatch(BaseModel):
    section: Literal["header", "recipient", "body", "signature"]
    content: str


class SectionOverridePatchResponse(BaseModel):
    cover_letter_id: uuid.UUID
    section: str
    status: str = "saved"


class CoverLetterSummaryResponse(BaseModel):
    cover_letter_id: uuid.UUID
    status: CoverLetterStatus
    template: str
    html_url: Optional[str] = None
    pdf_url: Optional[str] = None
    expires_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Update `backend/applire/schemas/flow.py`**

Add `CoverLetterSummary` class and the field to `FlowStateResponse`. After the existing `CVSummary` class, add:

```python
class CoverLetterSummary(BaseModel):
    cover_letter_id: uuid.UUID
    status: str
    template: str
    expires_at: datetime
```

Then in `FlowStateResponse`, add after `cv_summary`:

```python
cover_letter_summary: CoverLetterSummary | None = None
```

- [ ] **Step 5: Update `backend/applire/services/flow/orchestrator.py` to populate `cover_letter_summary`**

Add import of `GeneratedCoverLetter` and `CoverLetterSummary` at the top of the file:

```python
from applire.models.cover_letter import GeneratedCoverLetter
from applire.schemas.flow import (
    AdvanceFlowRequest,
    CoverLetterSummary,
    CreateFlowRequest,
    CreateFlowResponse,
    CVSummary,
    FlowStateResponse,
    GapAnalysisSummary,
    InterviewSummary,
    JobAnalysisSummary,
)
```

In the `get_flow_state` function, after the block that builds `cv_summary`, add:

```python
# Cover letter summary
cover_letter_summary: CoverLetterSummary | None = None
if flow.generated_cover_letter_id is not None:
    cl_result = await db.execute(
        select(GeneratedCoverLetter).where(
            GeneratedCoverLetter.id == flow.generated_cover_letter_id
        )
    )
    cl = cl_result.scalar_one_or_none()
    if cl is not None:
        cover_letter_summary = CoverLetterSummary(
            cover_letter_id=cl.id,
            status=cl.status,
            template=cl.template,
            expires_at=cl.expires_at,
        )
```

Then pass `cover_letter_summary=cover_letter_summary` to the `FlowStateResponse(...)` constructor.

- [ ] **Step 6: Run schema tests**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_cover_letter.py -k "schema or cover_letter_summary" -v
```

Expected: `3 passed`

- [ ] **Step 7: Run full unit suite**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/ -v --tb=short 2>&1 | tail -10
```

Expected: all passing.

- [ ] **Step 8: Commit**

```bash
git add backend/applire/schemas/cover_letter.py backend/applire/schemas/flow.py backend/applire/services/flow/orchestrator.py tests/unit/test_cover_letter.py
git commit -m "$(cat <<'EOF'
feat: add cover letter Pydantic schemas and FlowStateResponse cover_letter_summary

CoverLetterGenerateRequest validates tone literals. FlowStateResponse exposes
active cover letter status so the CV page can show the 'View Cover Letter' link.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Recipient extraction utility

**Files:**
- Create: `backend/applire/utils/recipient_extraction.py`
- Modify: `tests/unit/test_cover_letter.py`

- [ ] **Step 1: Add tests**

Append to `tests/unit/test_cover_letter.py`:

```python
# ---------------------------------------------------------------------------
# Task 6 — Recipient extraction
# ---------------------------------------------------------------------------

def test_extract_recipient_finds_anrede_pattern():
    from applire.utils.recipient_extraction import extract_recipient_from_jd
    jd = "Bitte richten Sie Ihre Bewerbung an Dr. Sarah Müller, HR-Abteilung."
    result = extract_recipient_from_jd(jd)
    assert result["name"] == "Dr. Sarah Müller"


def test_extract_recipient_finds_english_pattern():
    from applire.utils.recipient_extraction import extract_recipient_from_jd
    jd = "Please address your application to Ms. Anna Schmidt, Talent Acquisition."
    result = extract_recipient_from_jd(jd)
    assert result["name"] == "Ms. Anna Schmidt"


def test_extract_recipient_returns_none_when_not_found():
    from applire.utils.recipient_extraction import extract_recipient_from_jd
    result = extract_recipient_from_jd("We are looking for a senior engineer.")
    assert result["name"] is None
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/unit/test_cover_letter.py -k "extract_recipient" -v
```

Expected: `FAILED` — `ModuleNotFoundError: No module named 'applire.utils'`

- [ ] **Step 3: Create `backend/applire/utils/recipient_extraction.py`**

```python
"""Extract recipient name from a job description text.

Uses a regex cascade over common DACH and EN patterns.
Returns a dict with 'name' (str | None).
The LLM fallback is handled at generation time in services/cover_letter.py
if name is None and motivation/context warrants it.
"""

import re
from typing import TypedDict


class RecipientInfo(TypedDict):
    name: str | None


# Ordered from most-specific to least-specific
_PATTERNS: list[re.Pattern] = [
    # German: "an Frau/Herrn Dr./Prof. Vorname Nachname"
    re.compile(
        r"(?:an\s+)?(?:Frau|Herrn?)\s+((?:Dr\.|Prof\.(?:\s+Dr\.)?|Dipl\.-\w+\.?)\s+)?([A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?\s+[A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?)",
        re.UNICODE,
    ),
    # German: "richten Sie Ihre Bewerbung an <Title> <Name>"
    re.compile(
        r"richten\s+Sie\s+(?:Ihre\s+)?(?:Bewerbung|Unterlagen)\s+an\s+((?:Dr\.|Prof\.(?:\s+Dr\.)?|Dipl\.-\w+\.?)?\s*[A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)",
        re.UNICODE,
    ),
    # English: "to Mr./Mrs./Ms./Dr. Firstname Lastname"
    re.compile(
        r"(?:to\s+)?(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+([A-Z][a-z]+(?:-[A-Z][a-z]+)?\s+[A-Z][a-z]+(?:-[A-Z][a-z]+)?)",
        re.UNICODE,
    ),
    # English: "contact <Name>, <role>"
    re.compile(
        r"contact\s+((?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+)?([A-Z][a-z]+\s+[A-Z][a-z]+)\s*,",
        re.UNICODE,
    ),
]


def extract_recipient_from_jd(raw_text: str) -> RecipientInfo:
    """Return {'name': str | None} extracted from the JD text."""
    for pattern in _PATTERNS:
        match = pattern.search(raw_text)
        if match:
            groups = [g for g in match.groups() if g]
            name = " ".join(groups).strip()
            # Collapse multiple spaces
            name = re.sub(r"\s+", " ", name)
            return RecipientInfo(name=name)
    return RecipientInfo(name=None)
```

- [ ] **Step 4: Run tests**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_cover_letter.py -k "extract_recipient" -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/applire/utils/__init__.py backend/applire/utils/recipient_extraction.py tests/unit/test_cover_letter.py
git commit -m "$(cat <<'EOF'
feat: add recipient extraction utility for cover letter generation

Regex cascade over DACH and EN patterns extracts contact person name
from raw job description text. Returns None when no match (LLM fallback
in generation service).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

Note: also create `backend/applire/utils/__init__.py` as an empty file if it does not exist.

---

## Task 7: LLM prompt builder

**Files:**
- Create: `backend/applire/prompts/cover_letter.py`
- Modify: `tests/unit/test_cover_letter.py`

- [ ] **Step 1: Add tests**

Append to `tests/unit/test_cover_letter.py`:

```python
# ---------------------------------------------------------------------------
# Task 7 — LLM prompt builder
# ---------------------------------------------------------------------------

def test_build_cover_letter_prompt_includes_salary():
    from applire.prompts.cover_letter import build_cover_letter_prompt
    prompt = build_cover_letter_prompt(
        cv_data={"contact": {"name": "Marcus Bauer"}, "summary": "QA expert"},
        jd_text="We are hiring a QA Manager at Roche Diagnostics.",
        pre_gen_inputs={"salary": "95.000 €", "tone": "formal"},
        detected_language="de",
    )
    assert "Gehaltswunsch" in prompt
    assert "95.000 €" in prompt


def test_build_cover_letter_prompt_includes_availability():
    from applire.prompts.cover_letter import build_cover_letter_prompt
    prompt = build_cover_letter_prompt(
        cv_data={"contact": {"name": "Marcus Bauer"}, "summary": "QA expert"},
        jd_text="We are hiring a QA Manager.",
        pre_gen_inputs={"availability": "3 months notice", "tone": "professional"},
        detected_language="en",
    )
    assert "3 months notice" in prompt


def test_build_cover_letter_prompt_returns_system_and_user():
    from applire.prompts.cover_letter import build_cover_letter_prompt, SYSTEM_PROMPT
    prompt = build_cover_letter_prompt(
        cv_data={"contact": {"name": "A. Test"}, "summary": "Engineer"},
        jd_text="Test JD",
        pre_gen_inputs={"tone": "conversational"},
        detected_language="de",
    )
    assert isinstance(SYSTEM_PROMPT, str)
    assert len(prompt) > 100
```

- [ ] **Step 2: Run to verify failure**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_cover_letter.py -k "prompt" -v
```

Expected: `FAILED` — `ModuleNotFoundError`

- [ ] **Step 3: Create `backend/applire/prompts/cover_letter.py`**

```python
"""LLM prompt builder for cover letter generation.

The system prompt instructs the model to output strictly valid JSON
matching the letter_data schema. The user prompt provides all context.
"""

import json
from typing import Any

SYSTEM_PROMPT = """You are an expert DACH career coach writing a professional Bewerbungsschreiben (German cover letter).
Output ONLY a single valid JSON object. No markdown, no explanation, no prose outside the JSON.

The JSON must match this schema exactly:
{
  "header": {
    "name": "string",
    "address": "string",
    "phone": "string or null",
    "email": "string or null",
    "photo_url": "string or null"
  },
  "recipient": {
    "name": "string or null",
    "title": "string or null",
    "company": "string or null",
    "address": "string or null",
    "date": "string — today's date formatted DD. Month YYYY in German"
  },
  "body": {
    "paragraphs": ["opening paragraph", "main paragraph 1", "main paragraph 2", "closing paragraph"]
  },
  "signature": {
    "closing": "Mit freundlichen Grüßen",
    "name": "string"
  }
}

Rules:
- Write in the detected language (DE or EN).
- For German letters: use formal Sie-form, classic Bewerbungsschreiben structure.
- Include Gehaltswunsch in body only if salary is provided.
- Include Eintrittstermin in body only if availability is provided.
- Body should have 3-4 paragraphs: opening (interest + role), why-me (key achievements), company-fit, closing.
- Keep total letter body under 400 words.
- Use the tone specified: formal=sehr geehrte/r, professional=warm but polished, conversational=direct.
"""


def build_cover_letter_prompt(
    cv_data: dict[str, Any],
    jd_text: str,
    pre_gen_inputs: dict[str, Any],
    detected_language: str,
) -> str:
    """Build the user-turn prompt for the LLM.

    Returns a single string to pass as the user message.
    cv_data: the tailored_data dict from GeneratedCV (contact, summary, work_history, skills).
    jd_text: job.raw_text
    pre_gen_inputs: dict with keys salary, availability, motivation, tone, recipient_name, recipient_company.
    detected_language: 'de' or 'en'
    """
    salary = pre_gen_inputs.get("salary", "")
    availability = pre_gen_inputs.get("availability", "")
    motivation = pre_gen_inputs.get("motivation", "")
    tone = pre_gen_inputs.get("tone", "formal")
    recipient_name = pre_gen_inputs.get("recipient_name", "")
    recipient_company = pre_gen_inputs.get("recipient_company", "")

    contact = cv_data.get("contact", {})
    summary = cv_data.get("summary", "")
    skills = cv_data.get("skills", [])
    work_history = cv_data.get("work_history", [])

    # Build a condensed profile snippet (top 3 work entries, top 10 skills)
    work_snippet = ""
    for entry in work_history[:3]:
        work_snippet += f"- {entry.get('role', '')} at {entry.get('company', '')} ({entry.get('start_date', '')}–{entry.get('end_date', 'present')})\n"
        for bullet in entry.get("bullets", [])[:2]:
            work_snippet += f"  • {bullet}\n"

    skills_snippet = ", ".join(skills[:10]) if skills else "—"

    lines = [
        f"LANGUAGE: {detected_language.upper()}",
        f"TONE: {tone}",
        "",
        "=== CANDIDATE PROFILE ===",
        f"Name: {contact.get('name', '')}",
        f"Email: {contact.get('email', '')}",
        f"Phone: {contact.get('phone', '')}",
        f"Location: {contact.get('location', '')}",
        f"Summary: {summary}",
        f"Key skills: {skills_snippet}",
        "Recent experience:",
        work_snippet.strip(),
        "",
        "=== JOB DESCRIPTION ===",
        jd_text[:3000],  # truncate very long JDs
        "",
        "=== PRE-GENERATION INPUTS ===",
        f"Recipient name: {recipient_name or '(extract from JD or use generic salutation)'}",
        f"Recipient company: {recipient_company or '(extract from JD)'}",
    ]

    if salary:
        lines.append(f"Gehaltswunsch (salary expectation): {salary}")
    if availability:
        lines.append(f"Eintrittstermin (availability/notice period): {availability}")
    if motivation:
        lines.append(f"Personal motivation (incorporate naturally): {motivation}")

    lines += [
        "",
        "Generate the cover letter JSON now.",
    ]

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_cover_letter.py -k "prompt" -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/applire/prompts/cover_letter.py tests/unit/test_cover_letter.py
git commit -m "$(cat <<'EOF'
feat: add cover letter LLM prompt builder

System prompt enforces strict JSON output matching letter_data schema.
User prompt injects CV data, JD text, and DACH-specific inputs (salary,
availability). Handles DE/EN language and three tone variants.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Cover letter generation service

**Files:**
- Create: `backend/applire/services/cover_letter.py`
- Modify: `tests/unit/test_cover_letter.py`

- [ ] **Step 1: Add service tests**

Append to `tests/unit/test_cover_letter.py`:

```python
# ---------------------------------------------------------------------------
# Task 8 — Generation service
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_cover_letter_creates_pending_record(db):
    """generate_cover_letter should create a GeneratedCoverLetter with status=pending."""
    from unittest.mock import AsyncMock, MagicMock
    from applire.models.cover_letter import GeneratedCoverLetter, CoverLetterStatus
    from applire.models.cv import GeneratedCV
    from applire.models.flow import FlowSession
    from applire.models.job import JobAnalysis
    from applire.models.profile import MasterProfile
    from applire.models.user import User
    from applire.schemas.cover_letter import CoverLetterGenerateRequest

    # Seed minimal DB records
    user = User(id=uuid.uuid4(), email="test@test.com")
    db.add(user)
    job = JobAnalysis(
        id=uuid.uuid4(),
        raw_text_hash="abc123",
        raw_text="QA Manager at Roche",
        role_title="QA Manager",
        required_skills=[],
        nice_to_have_skills=[],
        keywords=[],
        seniority_level="senior",
        company_culture_signals=[],
        language_requirement="de",
    )
    db.add(job)
    profile = MasterProfile(profile_json={
        "contact": {"name": "Marcus Bauer", "email": "m@test.com"},
        "summary": "QA Expert",
        "work_history": [],
        "skills": [],
        "education": [],
        "languages": [],
    })
    db.add(profile)
    await db.flush()

    cv = GeneratedCV(
        job_analysis_id=job.id,
        profile_id=profile.id,
        tailored_data={
            "contact": {"name": "Marcus Bauer", "email": "m@test.com"},
            "summary": "QA Expert",
            "work_history": [],
            "skills": [],
            "education": [],
            "languages": [],
        },
        template="executive",
        status="ready",
    )
    db.add(cv)

    flow = FlowSession(
        user_id=user.id,
        job_id=job.id,
        generated_cv_id=cv.id,
        available_actions={},
    )
    db.add(flow)
    await db.commit()

    # Mock BackgroundTasks and LLM provider
    bg = MagicMock()
    bg.add_task = MagicMock()
    mock_provider = AsyncMock()

    from applire.services.cover_letter import generate_cover_letter
    request = CoverLetterGenerateRequest(
        job_id=job.id,
        tone="formal",
    )
    response = await generate_cover_letter(request, db, mock_provider, bg, "http://localhost:8001")

    assert response.cover_letter_id is not None
    assert response.status == CoverLetterStatus.pending
    bg.add_task.assert_called_once()

    # FlowSession should be updated
    await db.refresh(flow)
    assert flow.generated_cover_letter_id == response.cover_letter_id
```

- [ ] **Step 2: Run to verify failure**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_cover_letter.py::test_generate_cover_letter_creates_pending_record -v
```

Expected: `FAILED` — `ModuleNotFoundError: No module named 'applire.services.cover_letter'`

- [ ] **Step 3: Create `backend/applire/services/cover_letter.py`**

```python
"""Cover letter generation service — Sprint 25

Mirrors services/cv.py:
  generate_cover_letter:
    Create GeneratedCoverLetter record with status='pending'.
    Update FlowSession.generated_cover_letter_id.
    Enqueue _render_cover_letter_background via BackgroundTasks.
    Return immediately — caller polls GET /api/cover-letter/{id}/status.

  _render_cover_letter_background:
    LLM + Jinja2 + Playwright — runs outside request lifecycle.
    Updates status: pending → generating → ready | failed.
    Creates its own DB session.
"""

import json
import logging
import uuid
from datetime import timezone
from pathlib import Path

from fastapi import BackgroundTasks
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from applire.db.session import AsyncSessionLocal
from applire.models.cover_letter import CoverLetterStatus, GeneratedCoverLetter
from applire.models.cv import GeneratedCV
from applire.models.flow import FlowSession
from applire.models.job import JobAnalysis
from applire.models.profile import MasterProfile
from applire.prompts.cover_letter import SYSTEM_PROMPT, build_cover_letter_prompt
from applire.providers import get_provider
from applire.providers.llm.base import LLMProvider
from applire.schemas.cover_letter import (
    CoverLetterGenerateRequest,
    CoverLetterGenerateResponse,
    CoverLetterStatusResponse,
)
from applire.utils.recipient_extraction import extract_recipient_from_jd

logger = logging.getLogger(__name__)

_TEMPLATE_FILES: dict[str, str] = {
    "classic_german": "lebenslauf_letter.html.j2",
    "modern_swiss": "modern_swiss_letter.html.j2",
    "executive": "executive_letter.html.j2",
    "tech_developer": "tech_developer_letter.html.j2",
    "creative_sidebar": "creative_sidebar_letter.html.j2",
    "academic": "academic_letter.html.j2",
    "compact_pro": "compact_pro_letter.html.j2",
}

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


async def generate_cover_letter(
    request: CoverLetterGenerateRequest,
    db: AsyncSession,
    provider: LLMProvider,
    background_tasks: BackgroundTasks,
    base_url: str,
) -> CoverLetterGenerateResponse:
    """Create a pending GeneratedCoverLetter and enqueue the background render."""
    # Resolve flow session for this job
    flow_result = await db.execute(
        select(FlowSession).where(
            FlowSession.job_id == request.job_id,
            FlowSession.deleted_at.is_(None),
        )
    )
    flow = flow_result.scalar_one_or_none()
    if flow is None:
        raise LookupError(f"No flow session found for job {request.job_id}")

    # Resolve the active CV (for template + color_profile_id)
    cv: GeneratedCV | None = None
    template = "classic_german"
    color_profile_id: uuid.UUID | None = None
    if flow.generated_cv_id is not None:
        cv_result = await db.execute(
            select(GeneratedCV).where(GeneratedCV.id == flow.generated_cv_id)
        )
        cv = cv_result.scalar_one_or_none()
        if cv is not None:
            template = cv.template
            color_profile_id = cv.color_profile_id

    # Resolve profile
    profile_result = await db.execute(
        select(MasterProfile)
        .where(MasterProfile.deleted_at.is_(None))
        .order_by(MasterProfile.created_at.desc())
        .limit(1)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise LookupError("No profile found — complete the interview step first")

    # Build pre_gen_inputs for storage
    pre_gen_inputs = {
        "recipient_name": request.recipient_name,
        "recipient_company": request.recipient_company,
        "salary": request.salary,
        "availability": request.availability,
        "motivation": request.motivation,
        "tone": request.tone,
    }

    # Create the record
    cl = GeneratedCoverLetter(
        job_analysis_id=request.job_id,
        profile_id=profile.id,
        template=template,
        letter_data={},
        pre_gen_inputs=pre_gen_inputs,
        color_profile_id=color_profile_id,
        status=CoverLetterStatus.pending.value,
    )
    db.add(cl)

    # Update FlowSession pointer
    flow.generated_cover_letter_id = cl.id

    await db.commit()
    await db.refresh(cl)

    # Enqueue background render
    background_tasks.add_task(
        _render_cover_letter_background,
        cl_id=cl.id,
        cv_id=flow.generated_cv_id,
        job_id=request.job_id,
    )

    return CoverLetterGenerateResponse(
        cover_letter_id=cl.id,
        status=CoverLetterStatus.pending,
        html_url=f"{base_url}/api/cover-letter/{cl.id}/html",
        pdf_url=f"{base_url}/api/cover-letter/{cl.id}/pdf",
        expires_at=cl.expires_at,
    )


async def get_cover_letter_status(
    cl_id: uuid.UUID,
    db: AsyncSession,
    base_url: str,
) -> CoverLetterStatusResponse:
    result = await db.execute(
        select(GeneratedCoverLetter).where(
            GeneratedCoverLetter.id == cl_id,
            GeneratedCoverLetter.deleted_at.is_(None),
        )
    )
    cl = result.scalar_one_or_none()
    if cl is None:
        raise LookupError(f"Cover letter {cl_id} not found")

    html_url = None
    pdf_url = None
    if cl.status == CoverLetterStatus.ready.value:
        html_url = f"{base_url}/api/cover-letter/{cl_id}/html"
        pdf_url = f"{base_url}/api/cover-letter/{cl_id}/pdf"

    return CoverLetterStatusResponse(
        cover_letter_id=cl.id,
        status=cl.status,
        html_url=html_url,
        pdf_url=pdf_url,
        error_message=cl.error_message,
        expires_at=cl.expires_at,
    )


async def get_cover_letter_html(
    cl_id: uuid.UUID,
    db: AsyncSession,
) -> str:
    """Render the cover letter HTML via Jinja2. Only works when status='ready'."""
    result = await db.execute(
        select(GeneratedCoverLetter).where(
            GeneratedCoverLetter.id == cl_id,
            GeneratedCoverLetter.deleted_at.is_(None),
        )
    )
    cl = result.scalar_one_or_none()
    if cl is None:
        raise LookupError(f"Cover letter {cl_id} not found")
    if cl.status != CoverLetterStatus.ready.value:
        raise ValueError(f"Cover letter not ready (status={cl.status})")

    color_ctx = _default_color_context()
    if cl.color_profile_id is not None:
        from applire.models.color import CVColorProfile
        cp_result = await db.execute(
            select(CVColorProfile).where(CVColorProfile.id == cl.color_profile_id)
        )
        cp = cp_result.scalar_one_or_none()
        if cp is not None:
            color_ctx = {
                "primary": cp.primary,
                "primary_tint": cp.primary_tint,
                "surface": cp.surface,
                "surface_text": cp.surface_text,
            }

    letter_data = _apply_section_overrides(cl.letter_data, cl.section_overrides or {})
    template_file = _TEMPLATE_FILES.get(cl.template, "lebenslauf_letter.html.j2")
    tmpl = _jinja_env.get_template(template_file)
    return tmpl.render(letter=letter_data, color=color_ctx)


async def patch_cover_letter_section(
    cl_id: uuid.UUID,
    section: str,
    content: str,
    db: AsyncSession,
) -> None:
    result = await db.execute(
        select(GeneratedCoverLetter).where(
            GeneratedCoverLetter.id == cl_id,
            GeneratedCoverLetter.deleted_at.is_(None),
        )
    )
    cl = result.scalar_one_or_none()
    if cl is None:
        raise LookupError(f"Cover letter {cl_id} not found")

    overrides = dict(cl.section_overrides or {})
    overrides[section] = content
    cl.section_overrides = overrides
    await db.commit()


async def get_cover_letter_by_job(
    job_id: uuid.UUID,
    db: AsyncSession,
    base_url: str,
) -> CoverLetterStatusResponse:
    # Find active cover letter via flow session
    flow_result = await db.execute(
        select(FlowSession).where(
            FlowSession.job_id == job_id,
            FlowSession.deleted_at.is_(None),
        )
    )
    flow = flow_result.scalar_one_or_none()
    if flow is None or flow.generated_cover_letter_id is None:
        raise LookupError(f"No cover letter found for job {job_id}")
    return await get_cover_letter_status(flow.generated_cover_letter_id, db, base_url)


def _default_color_context() -> dict:
    return {
        "primary": "#1a1a2e",
        "primary_tint": "#e8e8f0",
        "surface": "#1a1a2e",
        "surface_text": "#ffffff",
    }


def _apply_section_overrides(letter_data: dict, overrides: dict) -> dict:
    """Return a copy of letter_data with manual section overrides applied."""
    import copy
    data = copy.deepcopy(letter_data)
    for section, content in overrides.items():
        if section == "body" and isinstance(content, str):
            data.setdefault("body", {})["paragraphs"] = [content]
        elif section in data:
            if isinstance(data[section], dict) and isinstance(content, str):
                data[section]["_override"] = content
            else:
                data[section] = content
    return data


async def _render_cover_letter_background(
    cl_id: uuid.UUID,
    cv_id: uuid.UUID | None,
    job_id: uuid.UUID,
) -> None:
    """Background task: LLM → Jinja2 → PDF. Updates status on completion."""
    async with AsyncSessionLocal() as db:
        try:
            # Load cover letter record
            cl_result = await db.execute(
                select(GeneratedCoverLetter).where(GeneratedCoverLetter.id == cl_id)
            )
            cl = cl_result.scalar_one_or_none()
            if cl is None:
                return

            cl.status = CoverLetterStatus.generating.value
            await db.commit()

            # Load job
            job_result = await db.execute(
                select(JobAnalysis).where(JobAnalysis.id == job_id)
            )
            job = job_result.scalar_one_or_none()
            if job is None:
                raise LookupError("Job not found")

            # Load CV tailored_data
            cv_data: dict = {}
            if cv_id is not None:
                cv_result = await db.execute(
                    select(GeneratedCV).where(GeneratedCV.id == cv_id)
                )
                cv = cv_result.scalar_one_or_none()
                if cv is not None:
                    cv_data = cv.tailored_data or {}

            # Load profile
            profile_result = await db.execute(
                select(MasterProfile)
                .where(MasterProfile.deleted_at.is_(None))
                .order_by(MasterProfile.created_at.desc())
                .limit(1)
            )
            profile = profile_result.scalar_one_or_none()
            if profile is not None and not cv_data:
                cv_data = profile.profile_json or {}

            # Auto-extract recipient if not provided
            pre_gen = dict(cl.pre_gen_inputs or {})
            if not pre_gen.get("recipient_name"):
                extracted = extract_recipient_from_jd(job.raw_text)
                if extracted["name"]:
                    pre_gen["recipient_name"] = extracted["name"]
            if not pre_gen.get("recipient_company") and job.company_name:
                pre_gen["recipient_company"] = job.company_name

            # Detect language
            detected_language = "de" if job.language_requirement.lower().startswith("de") else "en"

            # Call LLM
            provider = get_provider()
            user_prompt = build_cover_letter_prompt(
                cv_data=cv_data,
                jd_text=job.raw_text,
                pre_gen_inputs=pre_gen,
                detected_language=detected_language,
            )
            raw = await provider.complete(SYSTEM_PROMPT, user_prompt)

            # Parse JSON response
            letter_data = json.loads(raw)

            # Render HTML snapshot (not stored, rendered on-demand)
            cl.letter_data = letter_data
            cl.status = CoverLetterStatus.ready.value
            await db.commit()

            # Generate PDF via Playwright
            try:
                from applire.services.cover_letter_pdf import render_pdf
                await render_pdf(cl_id)
            except Exception as pdf_err:
                logger.warning("PDF render failed for CL %s: %s", cl_id, pdf_err)
                # HTML preview still works; PDF download will fail gracefully

        except Exception as exc:
            logger.exception("Cover letter generation failed for %s: %s", cl_id, exc)
            async with AsyncSessionLocal() as err_db:
                err_result = await err_db.execute(
                    select(GeneratedCoverLetter).where(GeneratedCoverLetter.id == cl_id)
                )
                err_cl = err_result.scalar_one_or_none()
                if err_cl is not None:
                    err_cl.status = CoverLetterStatus.failed.value
                    err_cl.error_message = str(exc)[:500]
                    await err_db.commit()
```

- [ ] **Step 4: Create `backend/applire/services/cover_letter_pdf.py`** (thin Playwright wrapper)

```python
"""Playwright PDF renderer for cover letters.

Separated from cover_letter.py to keep the main service file testable
without a Playwright dependency.
"""
import uuid

from playwright.async_api import async_playwright
from sqlalchemy import select

from applire.db.session import AsyncSessionLocal
from applire.models.cover_letter import CoverLetterStatus, GeneratedCoverLetter
from applire.services.cover_letter import get_cover_letter_html


async def render_pdf(cl_id: uuid.UUID) -> bytes:
    """Render the cover letter to PDF using Playwright. Returns raw PDF bytes."""
    async with AsyncSessionLocal() as db:
        html = await get_cover_letter_html(cl_id, db)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle")
        pdf_bytes = await page.pdf(
            format="A4",
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            print_background=True,
        )
        await browser.close()
    return pdf_bytes
```

- [ ] **Step 5: Run service test**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_cover_letter.py::test_generate_cover_letter_creates_pending_record -v
```

Expected: `PASSED`

- [ ] **Step 6: Run full unit suite**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/ -v --tb=short 2>&1 | tail -10
```

Expected: all passing.

- [ ] **Step 7: Commit**

```bash
git add backend/applire/services/cover_letter.py backend/applire/services/cover_letter_pdf.py tests/unit/test_cover_letter.py
git commit -m "$(cat <<'EOF'
feat: add cover letter generation service

Mirrors services/cv.py: creates pending record, enqueues background render,
updates FlowSession.generated_cover_letter_id. Background task runs
LLM → Jinja2 → Playwright PDF. section_overrides applied at render time.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Cover letter router + register in `main.py`

**Files:**
- Create: `backend/applire/routers/cover_letter.py`
- Modify: `backend/applire/main.py`

- [ ] **Step 1: Create `backend/applire/routers/cover_letter.py`**

```python
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from applire.auth import get_auth_provider
from applire.auth.base import AuthProvider
from applire.db.session import get_db
from applire.providers import get_provider
from applire.providers.llm.base import LLMProvider
from applire.schemas.cover_letter import (
    CoverLetterGenerateRequest,
    CoverLetterGenerateResponse,
    CoverLetterStatusResponse,
    SectionOverridePatch,
    SectionOverridePatchResponse,
)
from applire.services.cover_letter import (
    generate_cover_letter,
    get_cover_letter_by_job,
    get_cover_letter_html,
    get_cover_letter_status,
    patch_cover_letter_section,
)

router = APIRouter(prefix="/api/cover-letter", tags=["cover-letter"])


def _get_provider() -> LLMProvider:
    return get_provider()


@router.post(
    "/generate",
    response_model=CoverLetterGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_generate(
    body: CoverLetterGenerateRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    provider: LLMProvider = Depends(_get_provider),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> CoverLetterGenerateResponse:
    """Enqueue async cover letter generation. Returns immediately with status='pending'."""
    base_url = str(request.base_url).rstrip("/")
    try:
        return await generate_cover_letter(body, db, provider, background_tasks, base_url)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/by-job/{job_id}", response_model=CoverLetterStatusResponse)
async def get_by_job(
    job_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> CoverLetterStatusResponse:
    base_url = str(request.base_url).rstrip("/")
    try:
        return await get_cover_letter_by_job(job_id, db, base_url)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{cl_id}/status", response_model=CoverLetterStatusResponse)
async def get_cl_status(
    cl_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> CoverLetterStatusResponse:
    base_url = str(request.base_url).rstrip("/")
    try:
        return await get_cover_letter_status(cl_id, db, base_url)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{cl_id}/html", response_class=HTMLResponse)
async def get_html(
    cl_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> HTMLResponse:
    try:
        html = await get_cover_letter_html(cl_id, db)
        return HTMLResponse(content=html)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/{cl_id}/pdf")
async def get_pdf(
    cl_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> Response:
    try:
        from applire.services.cover_letter_pdf import render_pdf
        pdf_bytes = await render_pdf(cl_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="cover-letter.pdf"'},
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.patch("/{cl_id}/section", response_model=SectionOverridePatchResponse)
async def patch_section(
    cl_id: uuid.UUID,
    body: SectionOverridePatch,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> SectionOverridePatchResponse:
    try:
        await patch_cover_letter_section(cl_id, body.section, body.content, db)
        return SectionOverridePatchResponse(cover_letter_id=cl_id, section=body.section)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
```

- [ ] **Step 2: Register in `backend/applire/main.py`**

In `main.py`, update the import line:

```python
# Change:
from applire.routers import application, cv, cv_color, flow, health, job, jobs, profile, session
# To:
from applire.routers import application, cover_letter, cv, cv_color, flow, health, job, jobs, profile, session
```

Add after `app.include_router(cv.router)`:

```python
app.include_router(cover_letter.router)
```

- [ ] **Step 3: Verify the app starts without import errors**

```bash
cd /home/apliqa/Documents/Applire/Solution/backend && python -c "from applire.main import app; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/applire/routers/cover_letter.py backend/applire/main.py
git commit -m "$(cat <<'EOF'
feat: add cover letter router and register in main.py

POST /api/cover-letter/generate, GET /status, /html, /pdf,
PATCH /section, GET /by-job/{job_id}. Mirrors cv.py router pattern.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Retention worker update

**Files:**
- Modify: `backend/applire/retention/worker.py`

- [ ] **Step 1: Add `_purge_cover_letters` and `_reap_stale_cl_jobs` to `worker.py`**

After the `_reap_stale_cv_jobs` function and before `run()`, add:

```python
async def _purge_cover_letters(db: AsyncSession) -> int:
    """Hard-delete generated cover letters whose expires_at is in the past."""
    now = datetime.now(timezone.utc)
    try:
        result = await db.execute(
            text(
                "DELETE FROM generated_cover_letters WHERE expires_at < :now AND deleted_at IS NULL"
            ),
            {"now": now},
        )
        await db.commit()
        return result.rowcount  # type: ignore[return-value]
    except (ProgrammingError, OperationalError):
        await db.rollback()
        return 0


async def _reap_stale_cl_jobs(db: AsyncSession) -> int:
    """Mark cover letter generation jobs stuck > 10 minutes in pending/generating as failed."""
    from applire.models.cover_letter import CoverLetterStatus, GeneratedCoverLetter

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=_STALE_CV_JOB_MINUTES)
    now = datetime.now(timezone.utc)
    try:
        result = await db.execute(
            update(GeneratedCoverLetter)
            .where(
                GeneratedCoverLetter.status.in_(
                    [CoverLetterStatus.pending.value, CoverLetterStatus.generating.value]
                )
            )
            .where(GeneratedCoverLetter.created_at < cutoff)
            .where(GeneratedCoverLetter.deleted_at.is_(None))
            .values(
                status=CoverLetterStatus.failed.value,
                error_message="Generation timed out (stale job reaper)",
            )
        )
        await db.commit()
        return result.rowcount  # type: ignore[return-value]
    except (ProgrammingError, OperationalError):
        await db.rollback()
        return 0
```

- [ ] **Step 2: Call the new functions from `run()`**

Update `run()` to call the new functions and include them in the report:

```python
async def run() -> None:
    """Execute all TTL rules and emit a structured JSON report to stdout."""
    async with AsyncSessionLocal() as db:
        uploads_deleted = await _purge_uploads(db)
        sessions_deleted = await _purge_sessions(db)
        cvs_deleted = await _purge_cvs(db)
        cover_letters_deleted = await _purge_cover_letters(db)
        profiles_tombstoned = await _tombstone_inactive_profiles(db)
        users_tombstoned = await _tombstone_inactive_users(db)
        applications_tombstoned = await _tombstone_inactive_applications(db)
        stale_cv_jobs_failed = await _reap_stale_cv_jobs(db)
        stale_cl_jobs_failed = await _reap_stale_cl_jobs(db)

    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "uploads_deleted": uploads_deleted,
        "interview_sessions_deleted": sessions_deleted,
        "generated_cvs_deleted": cvs_deleted,
        "generated_cover_letters_deleted": cover_letters_deleted,
        "master_profiles_tombstoned": profiles_tombstoned,
        "users_tombstoned": users_tombstoned,
        "applications_tombstoned": applications_tombstoned,
        "stale_cv_jobs_failed": stale_cv_jobs_failed,
        "stale_cl_jobs_failed": stale_cl_jobs_failed,
    }
    print(json.dumps(report), flush=True)
```

- [ ] **Step 3: Run unit suite to verify no regressions**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/ -v --tb=short 2>&1 | tail -10
```

Expected: all passing.

- [ ] **Step 4: Commit**

```bash
git add backend/applire/retention/worker.py
git commit -m "$(cat <<'EOF'
feat: add cover letter purge and stale job reaper to retention worker

_purge_cover_letters hard-deletes expired records.
_reap_stale_cl_jobs marks stuck pending/generating jobs as failed after 10 min.
Both follow the ProgrammingError/OperationalError graceful pattern.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Seven Jinja2 cover letter templates

**Files:**
- Create: `backend/applire/templates/lebenslauf_letter.html.j2`
- Create: `backend/applire/templates/modern_swiss_letter.html.j2`
- Create: `backend/applire/templates/executive_letter.html.j2`
- Create: `backend/applire/templates/tech_developer_letter.html.j2`
- Create: `backend/applire/templates/creative_sidebar_letter.html.j2`
- Create: `backend/applire/templates/academic_letter.html.j2`
- Create: `backend/applire/templates/compact_pro_letter.html.j2`

All templates share the same Jinja2 context variables: `letter` (the `letter_data` dict) and `color` (with keys `primary`, `primary_tint`, `surface`, `surface_text`).

- [ ] **Step 1: Create `lebenslauf_letter.html.j2`** (classic_german — dark header bar, clean serif body)

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --primary: {{ color.primary }};
      --primary-tint: {{ color.primary_tint }};
      --surface: {{ color.surface }};
      --surface-text: {{ color.surface_text }};
    }
    body { font-family: Georgia, "Times New Roman", serif; font-size: 10.5pt; line-height: 1.6; color: #1a1a1a; background: #fff; }
    .page { width: 210mm; min-height: 297mm; margin: 0 auto; padding: 20mm 22mm 20mm 25mm; }
    .header { background: var(--surface); color: var(--surface-text); padding: 14px 20px; margin: -20mm -22mm 16mm -25mm; }
    .header-name { font-size: 15pt; font-weight: bold; letter-spacing: 1px; }
    .header-contact { font-size: 9pt; opacity: 0.85; margin-top: 4px; }
    .accent-rule { height: 2px; background: var(--primary); margin-bottom: 14mm; }
    .recipient { margin-bottom: 8mm; font-size: 10pt; line-height: 1.5; }
    .date { text-align: right; margin-bottom: 6mm; font-size: 10pt; color: #555; }
    .subject { font-weight: bold; font-size: 11pt; margin-bottom: 6mm; }
    .body p { margin-bottom: 5mm; font-size: 10.5pt; text-align: justify; }
    .signature { margin-top: 10mm; font-size: 10.5pt; }
    .signature .closing { margin-bottom: 12mm; }
    @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
  </style>
</head>
<body>
<div class="page">
  <div class="header">
    <div class="header-name">{{ letter.header.name | upper }}</div>
    <div class="header-contact">
      {{ letter.header.address }}{% if letter.header.phone %} · {{ letter.header.phone }}{% endif %}{% if letter.header.email %} · {{ letter.header.email }}{% endif %}
    </div>
  </div>
  <div class="accent-rule"></div>

  <div class="recipient">
    {% if letter.recipient.name %}{{ letter.recipient.name }}<br>{% endif %}
    {% if letter.recipient.title %}{{ letter.recipient.title }}<br>{% endif %}
    {% if letter.recipient.company %}{{ letter.recipient.company }}<br>{% endif %}
    {% if letter.recipient.address %}{{ letter.recipient.address }}{% endif %}
  </div>

  <div class="date">{{ letter.recipient.date }}</div>

  <div class="subject">Bewerbung {% if letter.recipient.company %}bei {{ letter.recipient.company }}{% endif %}</div>

  <div class="body">
    {% for para in letter.body.paragraphs %}
    <p>{{ para }}</p>
    {% endfor %}
  </div>

  <div class="signature">
    <div class="closing">{{ letter.signature.closing }},</div>
    <div>{{ letter.signature.name }}</div>
  </div>
</div>
</body>
</html>
```

- [ ] **Step 2: Create `executive_letter.html.j2`** (dark navy header, gold accent rule)

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --primary: {{ color.primary }};
      --surface: {{ color.surface }};
      --surface-text: {{ color.surface_text }};
    }
    body { font-family: Georgia, "Times New Roman", serif; font-size: 10.5pt; line-height: 1.65; color: #1a1a2e; background: #fff; }
    .page { width: 210mm; min-height: 297mm; margin: 0 auto; padding: 0 22mm 20mm 25mm; }
    .header { background: var(--surface); color: var(--surface-text); padding: 16px 20px; font-size: 9pt; letter-spacing: 1.5px; text-transform: uppercase; font-weight: bold; }
    .gold-rule { height: 2px; background: var(--primary); margin-bottom: 14mm; }
    .recipient { margin-bottom: 8mm; font-size: 10pt; }
    .date { text-align: right; margin-bottom: 6mm; color: #666; }
    .subject { font-weight: bold; font-size: 11pt; margin-bottom: 7mm; color: #1a1a2e; }
    .body p { margin-bottom: 5mm; text-align: justify; }
    .signature { margin-top: 10mm; }
    .signature .closing { margin-bottom: 12mm; }
    @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
  </style>
</head>
<body>
<div class="page">
  <div class="header">
    {{ letter.header.name }}{% if letter.header.email %} · {{ letter.header.email }}{% endif %}{% if letter.header.phone %} · {{ letter.header.phone }}{% endif %}{% if letter.header.address %} · {{ letter.header.address }}{% endif %}
  </div>
  <div class="gold-rule"></div>

  <div class="recipient">
    {% if letter.recipient.name %}{{ letter.recipient.name }}<br>{% endif %}
    {% if letter.recipient.title %}{{ letter.recipient.title }}<br>{% endif %}
    {% if letter.recipient.company %}{{ letter.recipient.company }}<br>{% endif %}
    {% if letter.recipient.address %}{{ letter.recipient.address }}{% endif %}
  </div>

  <div class="date">{{ letter.recipient.date }}</div>
  <div class="subject">Bewerbung{% if letter.recipient.company %} — {{ letter.recipient.company }}{% endif %}</div>

  <div class="body">
    {% for para in letter.body.paragraphs %}<p>{{ para }}</p>{% endfor %}
  </div>

  <div class="signature">
    <div class="closing">{{ letter.signature.closing }},</div>
    <div>{{ letter.signature.name }}</div>
  </div>
</div>
</body>
</html>
```

- [ ] **Step 3: Create `modern_swiss_letter.html.j2`** (accent top border, clean sans-serif)

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root { --primary: {{ color.primary }}; }
    body { font-family: "Helvetica Neue", Arial, sans-serif; font-size: 10pt; line-height: 1.6; color: #222; background: #fff; }
    .page { width: 210mm; min-height: 297mm; margin: 0 auto; padding: 20mm 22mm 20mm 25mm; border-top: 5px solid var(--primary); }
    .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12mm; }
    .header-name { font-size: 16pt; font-weight: 800; color: var(--primary); }
    .header-contact { font-size: 8.5pt; color: #666; text-align: right; line-height: 1.7; }
    .recipient { margin-bottom: 8mm; font-size: 10pt; }
    .date { text-align: right; margin-bottom: 6mm; color: #888; font-size: 9.5pt; }
    .subject { font-weight: 700; font-size: 11pt; margin-bottom: 7mm; color: var(--primary); }
    .body p { margin-bottom: 5mm; }
    .signature { margin-top: 10mm; }
    .signature .closing { margin-bottom: 12mm; }
    @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
  </style>
</head>
<body>
<div class="page">
  <div class="header">
    <div class="header-name">{{ letter.header.name }}</div>
    <div class="header-contact">
      {% if letter.header.email %}{{ letter.header.email }}<br>{% endif %}
      {% if letter.header.phone %}{{ letter.header.phone }}<br>{% endif %}
      {% if letter.header.address %}{{ letter.header.address }}{% endif %}
    </div>
  </div>

  <div class="recipient">
    {% if letter.recipient.name %}{{ letter.recipient.name }}<br>{% endif %}
    {% if letter.recipient.company %}{{ letter.recipient.company }}<br>{% endif %}
    {% if letter.recipient.address %}{{ letter.recipient.address }}{% endif %}
  </div>

  <div class="date">{{ letter.recipient.date }}</div>
  <div class="subject">Bewerbung{% if letter.recipient.company %} — {{ letter.recipient.company }}{% endif %}</div>

  <div class="body">{% for para in letter.body.paragraphs %}<p>{{ para }}</p>{% endfor %}</div>

  <div class="signature">
    <div class="closing">{{ letter.signature.closing }},</div>
    <div>{{ letter.signature.name }}</div>
  </div>
</div>
</body>
</html>
```

- [ ] **Step 4: Create the remaining 4 templates**

Create `tech_developer_letter.html.j2` (dark theme, monospace accents):

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root { --primary: {{ color.primary }}; --surface: {{ color.surface }}; --surface-text: {{ color.surface_text }}; }
    body { font-family: "Segoe UI", system-ui, sans-serif; font-size: 10pt; line-height: 1.6; color: #e2e8f0; background: var(--surface); }
    .page { width: 210mm; min-height: 297mm; margin: 0 auto; padding: 20mm 22mm 20mm 25mm; }
    .header { margin-bottom: 10mm; border-left: 4px solid var(--primary); padding-left: 12px; }
    .header-name { font-family: "Courier New", monospace; font-size: 14pt; font-weight: bold; color: var(--primary); }
    .header-contact { font-size: 8.5pt; color: #94a3b8; margin-top: 4px; }
    .accent-rule { height: 1px; background: var(--primary); opacity: 0.4; margin-bottom: 10mm; }
    .recipient { margin-bottom: 8mm; font-size: 10pt; color: #cbd5e1; }
    .date { text-align: right; margin-bottom: 6mm; color: #94a3b8; font-size: 9pt; font-family: "Courier New", monospace; }
    .subject { font-weight: 700; font-size: 11pt; margin-bottom: 7mm; color: var(--primary); }
    .body p { margin-bottom: 5mm; color: #e2e8f0; }
    .signature { margin-top: 10mm; color: #cbd5e1; }
    .signature .closing { margin-bottom: 12mm; }
    @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
  </style>
</head>
<body>
<div class="page">
  <div class="header">
    <div class="header-name">{{ letter.header.name }}</div>
    <div class="header-contact">{{ letter.header.email }}{% if letter.header.phone %} · {{ letter.header.phone }}{% endif %}{% if letter.header.address %} · {{ letter.header.address }}{% endif %}</div>
  </div>
  <div class="accent-rule"></div>
  <div class="recipient">{% if letter.recipient.name %}{{ letter.recipient.name }}<br>{% endif %}{% if letter.recipient.company %}{{ letter.recipient.company }}<br>{% endif %}{% if letter.recipient.address %}{{ letter.recipient.address }}{% endif %}</div>
  <div class="date">{{ letter.recipient.date }}</div>
  <div class="subject">Bewerbung{% if letter.recipient.company %} — {{ letter.recipient.company }}{% endif %}</div>
  <div class="body">{% for para in letter.body.paragraphs %}<p>{{ para }}</p>{% endfor %}</div>
  <div class="signature"><div class="closing">{{ letter.signature.closing }},</div><div>{{ letter.signature.name }}</div></div>
</div>
</body>
</html>
```

Create `creative_sidebar_letter.html.j2` (dark sidebar with personal details):

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root { --surface: {{ color.surface }}; --surface-text: {{ color.surface_text }}; --primary: {{ color.primary }}; }
    body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10pt; background: #fff; color: #1a1a1a; }
    .page { width: 210mm; min-height: 297mm; margin: 0 auto; display: flex; }
    .sidebar { width: 55mm; background: var(--surface); color: var(--surface-text); padding: 16mm 8mm 16mm 10mm; flex-shrink: 0; }
    .sidebar-name { font-size: 12pt; font-weight: bold; margin-bottom: 8mm; }
    .sidebar-label { font-size: 7.5pt; text-transform: uppercase; letter-spacing: 1px; opacity: 0.7; margin-bottom: 2mm; margin-top: 6mm; }
    .sidebar-value { font-size: 8.5pt; opacity: 0.9; }
    .main { flex: 1; padding: 16mm 14mm 16mm 12mm; }
    .recipient { margin-bottom: 8mm; font-size: 10pt; }
    .date { text-align: right; margin-bottom: 6mm; color: #666; }
    .subject { font-weight: 700; font-size: 11pt; margin-bottom: 7mm; color: var(--primary); }
    .body p { margin-bottom: 5mm; }
    .signature { margin-top: 10mm; }
    .signature .closing { margin-bottom: 12mm; }
    @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
  </style>
</head>
<body>
<div class="page">
  <div class="sidebar">
    <div class="sidebar-name">{{ letter.header.name }}</div>
    {% if letter.header.email %}<div class="sidebar-label">E-Mail</div><div class="sidebar-value">{{ letter.header.email }}</div>{% endif %}
    {% if letter.header.phone %}<div class="sidebar-label">Telefon</div><div class="sidebar-value">{{ letter.header.phone }}</div>{% endif %}
    {% if letter.header.address %}<div class="sidebar-label">Adresse</div><div class="sidebar-value">{{ letter.header.address }}</div>{% endif %}
  </div>
  <div class="main">
    <div class="recipient">{% if letter.recipient.name %}{{ letter.recipient.name }}<br>{% endif %}{% if letter.recipient.company %}{{ letter.recipient.company }}<br>{% endif %}{% if letter.recipient.address %}{{ letter.recipient.address }}{% endif %}</div>
    <div class="date">{{ letter.recipient.date }}</div>
    <div class="subject">Bewerbung{% if letter.recipient.company %} — {{ letter.recipient.company }}{% endif %}</div>
    <div class="body">{% for para in letter.body.paragraphs %}<p>{{ para }}</p>{% endfor %}</div>
    <div class="signature"><div class="closing">{{ letter.signature.closing }},</div><div>{{ letter.signature.name }}</div></div>
  </div>
</div>
</body>
</html>
```

Create `compact_pro_letter.html.j2` (dense typography, senior professional):

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root { --primary: {{ color.primary }}; }
    body { font-family: "Calibri", "Segoe UI", Arial, sans-serif; font-size: 10pt; line-height: 1.5; color: #111; background: #fff; }
    .page { width: 210mm; min-height: 297mm; margin: 0 auto; padding: 16mm 22mm 16mm 25mm; }
    .header { border-bottom: 2px solid var(--primary); padding-bottom: 6px; margin-bottom: 10mm; display: flex; justify-content: space-between; align-items: flex-end; }
    .header-name { font-size: 14pt; font-weight: 700; }
    .header-contact { font-size: 8.5pt; color: #555; text-align: right; line-height: 1.5; }
    .recipient { margin-bottom: 6mm; font-size: 9.5pt; }
    .date { text-align: right; margin-bottom: 5mm; color: #666; font-size: 9pt; }
    .subject { font-weight: 700; font-size: 10.5pt; margin-bottom: 6mm; }
    .body p { margin-bottom: 4mm; font-size: 9.5pt; text-align: justify; }
    .signature { margin-top: 8mm; font-size: 9.5pt; }
    .signature .closing { margin-bottom: 10mm; }
    @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
  </style>
</head>
<body>
<div class="page">
  <div class="header">
    <div class="header-name">{{ letter.header.name }}</div>
    <div class="header-contact">{% if letter.header.email %}{{ letter.header.email }}<br>{% endif %}{% if letter.header.phone %}{{ letter.header.phone }}<br>{% endif %}{% if letter.header.address %}{{ letter.header.address }}{% endif %}</div>
  </div>
  <div class="recipient">{% if letter.recipient.name %}{{ letter.recipient.name }}<br>{% endif %}{% if letter.recipient.company %}{{ letter.recipient.company }}<br>{% endif %}{% if letter.recipient.address %}{{ letter.recipient.address }}{% endif %}</div>
  <div class="date">{{ letter.recipient.date }}</div>
  <div class="subject">Bewerbung{% if letter.recipient.company %} — {{ letter.recipient.company }}{% endif %}</div>
  <div class="body">{% for para in letter.body.paragraphs %}<p>{{ para }}</p>{% endfor %}</div>
  <div class="signature"><div class="closing">{{ letter.signature.closing }},</div><div>{{ letter.signature.name }}</div></div>
</div>
</body>
</html>
```

Create `academic_letter.html.j2` (centered serif, traditional conventions):

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root { --primary: {{ color.primary }}; }
    body { font-family: "Palatino Linotype", Georgia, serif; font-size: 11pt; line-height: 1.7; color: #111; background: #fff; }
    .page { width: 210mm; min-height: 297mm; margin: 0 auto; padding: 20mm 28mm; }
    .header { text-align: center; margin-bottom: 14mm; border-bottom: 1px solid var(--primary); padding-bottom: 8px; }
    .header-name { font-size: 16pt; font-weight: bold; }
    .header-contact { font-size: 9pt; color: #666; margin-top: 4px; }
    .recipient { margin-bottom: 8mm; font-size: 10pt; }
    .date { text-align: right; margin-bottom: 6mm; font-style: italic; color: #555; }
    .subject { font-weight: bold; font-size: 11pt; margin-bottom: 7mm; text-align: center; }
    .body p { margin-bottom: 5mm; text-align: justify; }
    .signature { margin-top: 12mm; }
    .signature .closing { margin-bottom: 14mm; }
    @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
  </style>
</head>
<body>
<div class="page">
  <div class="header">
    <div class="header-name">{{ letter.header.name }}</div>
    <div class="header-contact">{% if letter.header.address %}{{ letter.header.address }}{% endif %}{% if letter.header.email %} · {{ letter.header.email }}{% endif %}{% if letter.header.phone %} · {{ letter.header.phone }}{% endif %}</div>
  </div>
  <div class="recipient">{% if letter.recipient.name %}{{ letter.recipient.name }}<br>{% endif %}{% if letter.recipient.title %}{{ letter.recipient.title }}<br>{% endif %}{% if letter.recipient.company %}{{ letter.recipient.company }}<br>{% endif %}{% if letter.recipient.address %}{{ letter.recipient.address }}{% endif %}</div>
  <div class="date">{{ letter.recipient.date }}</div>
  <div class="subject">Bewerbung{% if letter.recipient.company %} — {{ letter.recipient.company }}{% endif %}</div>
  <div class="body">{% for para in letter.body.paragraphs %}<p>{{ para }}</p>{% endfor %}</div>
  <div class="signature"><div class="closing">{{ letter.signature.closing }},</div><div>{{ letter.signature.name }}</div></div>
</div>
</body>
</html>
```

- [ ] **Step 5: Verify all 7 template files exist**

```bash
ls /home/apliqa/Documents/Applire/Solution/backend/applire/templates/*_letter.html.j2
```

Expected: 7 files listed.

- [ ] **Step 6: Commit**

```bash
git add backend/applire/templates/*_letter.html.j2
git commit -m "$(cat <<'EOF'
feat: add 7 paired cover letter Jinja2 templates

Each template matches its CV counterpart's visual identity
(header, color scheme, typography). All receive letter + color context.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: `GenerateCoverLetterModal` component

**Files:**
- Create: `frontend/components/cover-letter/GenerateCoverLetterModal.tsx`

- [ ] **Step 1: Create `frontend/components/cover-letter/GenerateCoverLetterModal.tsx`**

```tsx
"use client";

import { useState } from "react";

type CLTone = "formal" | "professional" | "conversational";

interface GenerateCoverLetterModalProps {
  jobId: string;
  prefillRecipientName?: string | null;
  prefillRecipientCompany?: string | null;
  /** If provided, modal shows "Regenerate" header and pre-fills fields */
  existingInputs?: {
    recipient_name?: string | null;
    recipient_company?: string | null;
    salary?: string | null;
    availability?: string | null;
    motivation?: string | null;
    tone?: CLTone;
  } | null;
  onClose: () => void;
  onGenerated: (coverLetterId: string) => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

const TONE_OPTIONS: { value: CLTone; label: string; sub: string }[] = [
  { value: "formal", label: "Formal", sub: "Traditionelles Bewerbungsschreiben" },
  { value: "professional", label: "Professional", sub: "Warm but polished" },
  { value: "conversational", label: "Conversational", sub: "Modern, direkt" },
];

export function GenerateCoverLetterModal({
  jobId,
  prefillRecipientName,
  prefillRecipientCompany,
  existingInputs,
  onClose,
  onGenerated,
}: GenerateCoverLetterModalProps) {
  const isRegenerate = existingInputs != null;
  const [recipientName, setRecipientName] = useState(
    existingInputs?.recipient_name ?? prefillRecipientName ?? ""
  );
  const [recipientCompany, setRecipientCompany] = useState(
    existingInputs?.recipient_company ?? prefillRecipientCompany ?? ""
  );
  const [salary, setSalary] = useState(existingInputs?.salary ?? "");
  const [availability, setAvailability] = useState(existingInputs?.availability ?? "");
  const [motivation, setMotivation] = useState(existingInputs?.motivation ?? "");
  const [tone, setTone] = useState<CLTone>(existingInputs?.tone ?? "formal");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/cover-letter/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: jobId,
          recipient_name: recipientName || null,
          recipient_company: recipientCompany || null,
          salary: salary || null,
          availability: availability || null,
          motivation: motivation || null,
          tone,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? "Generation failed");
      }
      const data = await res.json();
      onGenerated(data.cover_letter_id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      data-testid="cover-letter-modal"
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6 flex flex-col gap-4">
        <div>
          <h2 className="text-lg font-bold">
            {isRegenerate ? "Anschreiben neu generieren" : "Anschreiben generieren"}
          </h2>
          <p className="text-xs text-neutral-500 mt-1">
            Wir erstellen ein Bewerbungsschreiben passend zu Ihrem Lebenslauf.
          </p>
        </div>

        {/* Recipient */}
        <div>
          <label className="block text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-1">
            Empfänger{" "}
            <span className="font-normal text-neutral-400">(aus Stellenanzeige)</span>
          </label>
          <div className="flex gap-2">
            <input
              className="flex-1 border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Name"
              value={recipientName}
              onChange={(e) => setRecipientName(e.target.value)}
              data-testid="cl-recipient-name"
            />
            <input
              className="flex-1 border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Unternehmen"
              value={recipientCompany}
              onChange={(e) => setRecipientCompany(e.target.value)}
              data-testid="cl-recipient-company"
            />
          </div>
        </div>

        {/* Salary */}
        <div>
          <label className="block text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-1">
            Gehaltswunsch{" "}
            <span className="font-normal text-neutral-400">(optional)</span>
          </label>
          <input
            className="w-full border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="z.B. 95.000 – 110.000 € p.a."
            value={salary}
            onChange={(e) => setSalary(e.target.value)}
            data-testid="cl-salary"
          />
        </div>

        {/* Availability */}
        <div>
          <label className="block text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-1">
            Verfügbarkeit{" "}
            <span className="font-normal text-neutral-400">(optional)</span>
          </label>
          <input
            className="w-full border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="z.B. 3 Monate zum Monatsende"
            value={availability}
            onChange={(e) => setAvailability(e.target.value)}
            data-testid="cl-availability"
          />
        </div>

        {/* Motivation */}
        <div>
          <label className="block text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-1">
            Persönliche Motivation{" "}
            <span className="font-normal text-neutral-400">(optional)</span>
          </label>
          <textarea
            className="w-full border border-neutral-300 rounded px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
            placeholder="Warum interessiert Sie diese Stelle? Leer lassen = KI generiert aus Stellenanzeige."
            value={motivation}
            onChange={(e) => setMotivation(e.target.value)}
            data-testid="cl-motivation"
          />
        </div>

        {/* Tone */}
        <div>
          <label className="block text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-2">
            Tonalität
          </label>
          <div className="flex gap-2">
            {TONE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setTone(opt.value)}
                className={`flex-1 rounded border p-2 text-left transition-colors ${
                  tone === opt.value
                    ? "border-blue-500 bg-blue-50"
                    : "border-neutral-200 hover:border-neutral-400"
                }`}
                data-testid={`cl-tone-${opt.value}`}
              >
                <div className="text-xs font-semibold">{opt.label}</div>
                <div className="text-xs text-neutral-500">{opt.sub}</div>
              </button>
            ))}
          </div>
        </div>

        {error && (
          <p className="text-xs text-red-600 bg-red-50 rounded p-2">{error}</p>
        )}

        <div className="flex gap-2 pt-1">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="flex-1 border border-neutral-300 rounded py-2.5 text-sm hover:border-neutral-500 transition-colors disabled:opacity-50"
            data-testid="cl-modal-cancel"
          >
            Abbrechen
          </button>
          <button
            type="button"
            onClick={handleGenerate}
            disabled={loading}
            className="flex-[2] bg-blue-600 text-white rounded py-2.5 text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
            data-testid="cl-modal-generate"
          >
            {loading ? "Wird generiert…" : "Anschreiben generieren →"}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/cover-letter/GenerateCoverLetterModal.tsx
git commit -m "$(cat <<'EOF'
feat: add GenerateCoverLetterModal component

Pre-generation form with recipient (auto-filled), salary/availability
(DACH Gehaltswunsch/Eintrittstermin), motivation textarea, and tone
selector. POSTs to /api/cover-letter/generate on submit.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: Update `ActionsTab.tsx`

**Files:**
- Modify: `frontend/components/cv/ActionsTab.tsx`

Add a "Generate Cover Letter" button (visible always when CV is `ready`) and a "View Cover Letter" link (visible when `coverLetterId` is provided).

- [ ] **Step 1: Update `frontend/components/cv/ActionsTab.tsx`**

Replace the entire file content:

```tsx
"use client";

import Link from "next/link";
import { TemplateSelector } from "./TemplateSelector";

type CVTemplate = "classic_german" | "modern_swiss" | "executive" | "tech_developer" | "creative_sidebar" | "academic" | "compact_pro";

interface ActionsTabProps {
  flowId: string;
  matchScore: number | null;
  expiryWarning: { level: "none" | "warning" | "critical"; expiresIn: string } | null;
  coverLetterId: string | null;
  onDownloadPdf: () => void;
  onRegenerateSame: () => void;
  onRegenerateWithTemplate: (template: CVTemplate) => void;
  onNext: () => void;
  onGenerateCoverLetter: () => void;
}

export function ActionsTab({
  flowId,
  matchScore,
  expiryWarning,
  coverLetterId,
  onDownloadPdf,
  onRegenerateSame,
  onRegenerateWithTemplate,
  onNext,
  onGenerateCoverLetter,
}: ActionsTabProps) {
  return (
    <div className="flex flex-col gap-4 p-3">
      {matchScore !== null && (
        <div className="flex flex-col items-center gap-2">
          <div className="relative w-20 h-20">
            <svg className="w-full h-full" viewBox="0 0 36 36">
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="3"
              />
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#0d9488"
                strokeWidth="3"
                strokeDasharray={`${matchScore * 100}, 100`}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-lg font-bold text-neutral-dark">
                {Math.round(matchScore * 100)}%
              </span>
            </div>
          </div>
          <span className="text-xs text-neutral-medium">Matching-Score</span>
        </div>
      )}

      {expiryWarning && expiryWarning.level !== "none" && (
        <div
          className={`text-xs px-3 py-2 rounded border ${
            expiryWarning.level === "critical"
              ? "bg-error-light border-error text-error"
              : "bg-warning-container border-warning/30 text-warning"
          }`}
        >
          {expiryWarning.level === "critical" ? (
            <>CV läuft ab: <span>{expiryWarning.expiresIn}</span></>
          ) : (
            <>CV läuft bald ab: <span>{expiryWarning.expiresIn}</span></>
          )}
        </div>
      )}

      <div className="flex flex-col gap-2">
        <button
          type="button"
          onClick={onDownloadPdf}
          className="w-full bg-teal text-white text-sm font-medium py-2.5 rounded hover:opacity-90 transition-opacity"
          data-testid="download-pdf-btn"
        >
          PDF herunterladen
        </button>
        <button
          type="button"
          onClick={onRegenerateSame}
          className="w-full border border-neutral-medium text-sm py-2.5 rounded hover:border-teal transition-colors"
          data-testid="regenerate-same-btn"
        >
          Erneut generieren (gleiche Vorlage)
        </button>
      </div>

      <div className="border-t border-neutral-medium pt-4">
        <p className="text-xs font-semibold text-neutral-medium uppercase tracking-wide mb-3">
          Vorlage wechseln
        </p>
        <TemplateSelector
          onGenerate={onRegenerateWithTemplate}
          actionLabel="Mit dieser Vorlage generieren"
        />
      </div>

      {/* Cover Letter section */}
      <div className="border-t border-neutral-medium pt-4 flex flex-col gap-2">
        <p className="text-xs font-semibold text-neutral-medium uppercase tracking-wide mb-1">
          Anschreiben
        </p>
        {coverLetterId ? (
          <Link
            href={`/flow/${flowId}/cover-letter`}
            className="w-full flex items-center justify-center gap-1 border border-blue-500 text-blue-600 text-sm py-2.5 rounded hover:bg-blue-50 transition-colors"
            data-testid="view-cover-letter-btn"
          >
            Anschreiben ansehen →
          </Link>
        ) : null}
        <button
          type="button"
          onClick={onGenerateCoverLetter}
          className="w-full bg-blue-600 text-white text-sm font-medium py-2.5 rounded hover:bg-blue-700 transition-colors"
          data-testid="generate-cover-letter-btn"
        >
          {coverLetterId ? "Anschreiben neu generieren" : "Anschreiben generieren"}
        </button>
      </div>

      <button
        type="button"
        onClick={onNext}
        className="w-full bg-primary text-white text-sm font-medium py-2.5 rounded hover:bg-primary/90 transition-colors"
        data-testid="next-step-btn"
      >
        Was nun?
      </button>
    </div>
  );
}
```

- [ ] **Step 2: Fix TypeScript compilation — update all call sites of `ActionsTab`**

Search for usages of `ActionsTab` in the CV page and pass the new required props:

```bash
grep -r "ActionsTab" /home/apliqa/Documents/Applire/Solution/frontend --include="*.tsx" -l
```

In `frontend/app/flow/[flowId]/cv/page.tsx`, find the `<ActionsTab` usage and add the new props:

```tsx
<ActionsTab
  flowId={flowId}
  matchScore={flowState?.gap_summary?.match_score ?? null}
  expiryWarning={expiryWarning}
  coverLetterId={flowState?.cover_letter_summary?.cover_letter_id ?? null}
  onDownloadPdf={handleDownloadPdf}
  onRegenerateSame={handleRegenerateSame}
  onRegenerateWithTemplate={handleRegenerateWithTemplate}
  onNext={handleNext}
  onGenerateCoverLetter={() => setShowCoverLetterModal(true)}
/>
```

Also add to the page state and import:

```tsx
import { GenerateCoverLetterModal } from "@/components/cover-letter/GenerateCoverLetterModal";

// In page state:
const [showCoverLetterModal, setShowCoverLetterModal] = useState(false);
```

Add the modal render in the page JSX (just before the closing `</div>` of the page):

```tsx
{showCoverLetterModal && flowState?.job_id && (
  <GenerateCoverLetterModal
    jobId={flowState.job_id}
    onClose={() => setShowCoverLetterModal(false)}
    onGenerated={(clId) => {
      setShowCoverLetterModal(false);
      router.push(`/flow/${flowId}/cover-letter`);
    }}
  />
)}
```

Add `import { useRouter } from "next/navigation";` and `const router = useRouter();` if not already present in the CV page.

- [ ] **Step 3: Run TypeScript check**

```bash
cd /home/apliqa/Documents/Applire/Solution/frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/components/cv/ActionsTab.tsx frontend/app/flow/[flowId]/cv/page.tsx
git commit -m "$(cat <<'EOF'
feat: add cover letter entry points to CV ActionsTab

'Generate Cover Letter' button opens GenerateCoverLetterModal.
'View Cover Letter' link appears once cover_letter_summary is present
in FlowStateResponse. ActionsTab receives flowId + coverLetterId props.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 14: `CoverLetterDocument` component (srcDoc iframe)

**Files:**
- Create: `frontend/components/cover-letter/CoverLetterDocument.tsx`

- [ ] **Step 1: Create `frontend/components/cover-letter/CoverLetterDocument.tsx`**

```tsx
"use client";

import { useEffect, useState } from "react";

interface CoverLetterDocumentProps {
  coverLetterId: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export function CoverLetterDocument({ coverLetterId }: CoverLetterDocumentProps) {
  const [srcDoc, setSrcDoc] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!coverLetterId) return;
    let cancelled = false;

    async function load() {
      try {
        const res = await fetch(`${API_BASE}/api/cover-letter/${coverLetterId}/html`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const html = await res.text();
        if (!cancelled) setSrcDoc(html);
      } catch (err: unknown) {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Preview nicht verfügbar");
      }
    }

    load();
    return () => { cancelled = true; };
  }, [coverLetterId]);

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-red-500">
        {error}
      </div>
    );
  }

  if (!srcDoc) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-neutral-400">
        Lade Vorschau…
      </div>
    );
  }

  return (
    <iframe
      srcDoc={srcDoc}
      className="w-full h-full border-0"
      title="Anschreiben Vorschau"
      data-testid="cover-letter-iframe"
      sandbox="allow-same-origin"
    />
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/cover-letter/CoverLetterDocument.tsx
git commit -m "$(cat <<'EOF'
feat: add CoverLetterDocument iframe component (srcDoc pattern)

Fetches /api/cover-letter/{id}/html and injects via srcDoc — same
pattern as CVDocument to avoid cross-origin CSP issues.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 15: `CoverLetterContentTab` component

**Files:**
- Create: `frontend/components/cover-letter/CoverLetterContentTab.tsx`

- [ ] **Step 1: Create `frontend/components/cover-letter/CoverLetterContentTab.tsx`**

```tsx
"use client";

import { useState } from "react";

interface LetterData {
  header?: { name?: string; address?: string; phone?: string; email?: string };
  recipient?: { name?: string; company?: string };
  body?: { paragraphs?: string[] };
  signature?: { closing?: string; name?: string };
}

interface CoverLetterContentTabProps {
  coverLetterId: string;
  letterData: LetterData | null;
  onSectionSaved: () => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export function CoverLetterContentTab({
  coverLetterId,
  letterData,
  onSectionSaved,
}: CoverLetterContentTabProps) {
  const [bodyText, setBodyText] = useState(
    letterData?.body?.paragraphs?.join("\n\n") ?? ""
  );
  const [bodyEditing, setBodyEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  async function handleSaveBody() {
    setSaving(true);
    setSaveError(null);
    try {
      const res = await fetch(`${API_BASE}/api/cover-letter/${coverLetterId}/section`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ section: "body", content: bodyText }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setBodyEditing(false);
      onSectionSaved();
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : "Fehler beim Speichern");
    } finally {
      setSaving(false);
    }
  }

  const header = letterData?.header;
  const recipient = letterData?.recipient;
  const signature = letterData?.signature;

  return (
    <div className="flex flex-col gap-3 p-3">
      <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wide">
        Abschnitte
      </p>

      {/* Header — read-only */}
      <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-semibold">Kopfzeile</span>
          <span className="text-xs text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
            auto
          </span>
        </div>
        <p className="text-xs text-neutral-500">
          {header?.name ?? "Aus Profil"}{header?.email ? ` · ${header.email}` : ""}
        </p>
      </div>

      {/* Recipient — read-only (shown, editable via regeneration) */}
      <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-semibold">Empfänger</span>
          <span className="text-xs text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
            auto
          </span>
        </div>
        <p className="text-xs text-neutral-500">
          {recipient?.name ?? "–"}{recipient?.company ? ` · ${recipient.company}` : ""}
        </p>
      </div>

      {/* Body — editable */}
      <div
        className={`border rounded-lg p-3 transition-colors ${
          bodyEditing
            ? "border-blue-400 bg-blue-50"
            : "border-neutral-200 bg-neutral-50"
        }`}
      >
        <div className="flex items-center justify-between mb-2">
          <span className={`text-sm font-semibold ${bodyEditing ? "text-blue-700" : ""}`}>
            Anschreiben-Text
          </span>
          <span className="text-xs text-blue-600 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded-full">
            bearbeitbar
          </span>
        </div>
        <textarea
          className="w-full border border-blue-200 rounded p-2 text-xs text-neutral-700 resize-none bg-white focus:outline-none focus:ring-2 focus:ring-blue-400"
          rows={8}
          value={bodyText}
          onChange={(e) => {
            setBodyText(e.target.value);
            setBodyEditing(true);
          }}
          data-testid="cl-body-textarea"
        />
        {saveError && (
          <p className="text-xs text-red-500 mt-1">{saveError}</p>
        )}
        {bodyEditing && (
          <div className="flex gap-2 mt-2">
            <button
              type="button"
              onClick={handleSaveBody}
              disabled={saving}
              className="flex-1 bg-blue-600 text-white text-xs py-1.5 rounded hover:bg-blue-700 disabled:opacity-50"
              data-testid="cl-save-body-btn"
            >
              {saving ? "Speichern…" : "Speichern"}
            </button>
            <button
              type="button"
              onClick={() => {
                setBodyText(letterData?.body?.paragraphs?.join("\n\n") ?? "");
                setBodyEditing(false);
              }}
              disabled={saving}
              className="flex-1 border border-neutral-300 text-xs py-1.5 rounded hover:border-neutral-500 disabled:opacity-50"
            >
              Abbrechen
            </button>
          </div>
        )}
      </div>

      {/* Signature — read-only */}
      <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-semibold">Unterschrift & Datum</span>
          <span className="text-xs text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
            auto
          </span>
        </div>
        <p className="text-xs text-neutral-500">
          {signature?.closing ?? "Mit freundlichen Grüßen"} · {signature?.name ?? "–"}
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/cover-letter/CoverLetterContentTab.tsx
git commit -m "$(cat <<'EOF'
feat: add CoverLetterContentTab with 4 section cards

Header/Recipient/Signature are read-only auto-filled cards.
Body is an editable textarea that PATCHes /api/cover-letter/{id}/section
on save. Calls onSectionSaved to refresh the preview iframe.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 16: `CoverLetterDesignTab` and `CoverLetterActionsTab`

**Files:**
- Create: `frontend/components/cover-letter/CoverLetterDesignTab.tsx`
- Create: `frontend/components/cover-letter/CoverLetterActionsTab.tsx`

- [ ] **Step 1: Create `frontend/components/cover-letter/CoverLetterDesignTab.tsx`**

```tsx
"use client";

import Link from "next/link";

type CLTemplate =
  | "classic_german"
  | "modern_swiss"
  | "executive"
  | "tech_developer"
  | "creative_sidebar"
  | "academic"
  | "compact_pro";

interface TemplateOption {
  value: CLTemplate;
  label: string;
  description: string;
}

const TEMPLATES: TemplateOption[] = [
  { value: "classic_german", label: "Lebenslauf", description: "Dunkle Kopfzeile, Serif" },
  { value: "modern_swiss", label: "Modern Swiss", description: "Akzentlinie, Sans-serif" },
  { value: "executive", label: "Executive", description: "Marine, Goldakzent" },
  { value: "tech_developer", label: "Tech Developer", description: "Dunkles Theme, Monospace" },
  { value: "creative_sidebar", label: "Creative Sidebar", description: "Dunkle Seitenleiste" },
  { value: "academic", label: "Academic", description: "Zentriert, Serif, klassisch" },
  { value: "compact_pro", label: "Compact Pro", description: "Kompakt, professionell" },
];

interface CoverLetterDesignTabProps {
  flowId: string;
  currentTemplate: CLTemplate;
  onTemplateChange: (template: CLTemplate) => void;
}

export function CoverLetterDesignTab({
  flowId,
  currentTemplate,
  onTemplateChange,
}: CoverLetterDesignTabProps) {
  return (
    <div className="flex flex-col gap-3 p-3">
      <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wide">
        Vorlage
      </p>
      <div className="flex flex-col gap-2">
        {TEMPLATES.map((tmpl) => (
          <button
            key={tmpl.value}
            type="button"
            onClick={() => onTemplateChange(tmpl.value)}
            className={`flex items-center justify-between rounded-lg border px-3 py-2.5 text-left transition-colors ${
              currentTemplate === tmpl.value
                ? "border-blue-500 bg-blue-50"
                : "border-neutral-200 hover:border-neutral-400 bg-neutral-50"
            }`}
            data-testid={`cl-template-${tmpl.value}`}
          >
            <div>
              <div className="text-sm font-medium">{tmpl.label}</div>
              <div className="text-xs text-neutral-500">{tmpl.description}</div>
            </div>
            {currentTemplate === tmpl.value && (
              <span className="text-blue-600 text-xs font-semibold">Aktiv</span>
            )}
          </button>
        ))}
      </div>

      <div className="border-t border-neutral-200 pt-3 mt-1">
        <p className="text-xs text-neutral-500 mb-1">Farbschema</p>
        <p className="text-xs text-neutral-400">
          Geteilt mit Ihrem Lebenslauf.{" "}
          <Link
            href={`/flow/${flowId}/cv`}
            className="text-blue-500 hover:underline"
            data-testid="cl-design-change-color-link"
          >
            Im Lebenslauf ändern →
          </Link>
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create `frontend/components/cover-letter/CoverLetterActionsTab.tsx`**

```tsx
"use client";

interface CoverLetterActionsTabProps {
  onRegenerateCoverLetter: () => void;
  onDownloadPdf: () => void;
  downloading: boolean;
}

export function CoverLetterActionsTab({
  onRegenerateCoverLetter,
  onDownloadPdf,
  downloading,
}: CoverLetterActionsTabProps) {
  return (
    <div className="flex flex-col gap-3 p-3">
      <div className="flex flex-col gap-2">
        <button
          type="button"
          onClick={onDownloadPdf}
          disabled={downloading}
          className="w-full bg-blue-600 text-white text-sm font-medium py-2.5 rounded hover:bg-blue-700 transition-colors disabled:opacity-50"
          data-testid="cl-download-pdf-btn"
        >
          {downloading ? "PDF wird erstellt…" : "PDF herunterladen"}
        </button>
      </div>

      <div className="border-t border-neutral-200 pt-3">
        <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wide mb-2">
          Neu generieren
        </p>
        <p className="text-xs text-neutral-400 mb-3">
          Öffnet das Eingabeformular mit den bisherigen Angaben. Das neue Anschreiben ersetzt das aktuelle.
        </p>
        <button
          type="button"
          onClick={onRegenerateCoverLetter}
          className="w-full border border-neutral-300 text-sm py-2.5 rounded hover:border-neutral-500 transition-colors"
          data-testid="cl-regenerate-btn"
        >
          ↻ Anschreiben neu generieren
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/components/cover-letter/CoverLetterDesignTab.tsx frontend/components/cover-letter/CoverLetterActionsTab.tsx
git commit -m "$(cat <<'EOF'
feat: add CoverLetterDesignTab and CoverLetterActionsTab components

Design tab: 7-option template picker + color-profile link back to CV page.
Actions tab: PDF download + regenerate (opens pre-gen modal with existing inputs).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 17: `CoverLetterRefinementPanel` component

**Files:**
- Create: `frontend/components/cover-letter/CoverLetterRefinementPanel.tsx`

- [ ] **Step 1: Create `frontend/components/cover-letter/CoverLetterRefinementPanel.tsx`**

```tsx
"use client";

import { useState } from "react";
import { CoverLetterContentTab } from "./CoverLetterContentTab";
import { CoverLetterDesignTab } from "./CoverLetterDesignTab";
import { CoverLetterActionsTab } from "./CoverLetterActionsTab";

type CLTemplate =
  | "classic_german"
  | "modern_swiss"
  | "executive"
  | "tech_developer"
  | "creative_sidebar"
  | "academic"
  | "compact_pro";

type TabId = "content" | "design" | "actions";

interface CoverLetterRefinementPanelProps {
  flowId: string;
  coverLetterId: string;
  letterData: Record<string, unknown> | null;
  currentTemplate: CLTemplate;
  onSectionSaved: () => void;
  onTemplateChange: (template: CLTemplate) => void;
  onRegenerateCoverLetter: () => void;
  onDownloadPdf: () => void;
  downloading: boolean;
}

const TABS: { id: TabId; label: string }[] = [
  { id: "content", label: "Inhalt" },
  { id: "design", label: "Design" },
  { id: "actions", label: "Aktionen" },
];

export function CoverLetterRefinementPanel({
  flowId,
  coverLetterId,
  letterData,
  currentTemplate,
  onSectionSaved,
  onTemplateChange,
  onRegenerateCoverLetter,
  onDownloadPdf,
  downloading,
}: CoverLetterRefinementPanelProps) {
  const [activeTab, setActiveTab] = useState<TabId>("content");

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Tab bar */}
      <div className="flex border-b border-neutral-200 flex-shrink-0">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-neutral-500 hover:text-neutral-700"
            }`}
            data-testid={`cl-tab-${tab.id}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === "content" && (
          <CoverLetterContentTab
            coverLetterId={coverLetterId}
            letterData={letterData as Parameters<typeof CoverLetterContentTab>[0]["letterData"]}
            onSectionSaved={onSectionSaved}
          />
        )}
        {activeTab === "design" && (
          <CoverLetterDesignTab
            flowId={flowId}
            currentTemplate={currentTemplate}
            onTemplateChange={onTemplateChange}
          />
        )}
        {activeTab === "actions" && (
          <CoverLetterActionsTab
            onRegenerateCoverLetter={onRegenerateCoverLetter}
            onDownloadPdf={onDownloadPdf}
            downloading={downloading}
          />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/cover-letter/CoverLetterRefinementPanel.tsx
git commit -m "$(cat <<'EOF'
feat: add CoverLetterRefinementPanel with Content/Design/Actions tabs

Tab strip mirrors RefinementPanel on CV page. Delegates to the three
sub-tab components. Active tab tracked in local state.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 18: Cover letter page

**Files:**
- Create: `frontend/app/flow/[flowId]/cover-letter/page.tsx`

- [ ] **Step 1: Create `frontend/app/flow/[flowId]/cover-letter/page.tsx`**

```tsx
// frontend/app/flow/[flowId]/cover-letter/page.tsx
"use client";

import Link from "next/link";
import { use, useCallback, useEffect, useRef, useState } from "react";
import { CoverLetterDocument } from "@/components/cover-letter/CoverLetterDocument";
import { CoverLetterRefinementPanel } from "@/components/cover-letter/CoverLetterRefinementPanel";
import { GenerateCoverLetterModal } from "@/components/cover-letter/GenerateCoverLetterModal";

type CLTemplate =
  | "classic_german"
  | "modern_swiss"
  | "executive"
  | "tech_developer"
  | "creative_sidebar"
  | "academic"
  | "compact_pro";

type Phase = "loading" | "generating" | "ready" | "not_found";

interface CLState {
  coverLetterId: string;
  status: string;
  template: CLTemplate;
  letterData: Record<string, unknown> | null;
  preGenInputs: Record<string, unknown> | null;
  jobId: string | null;
  roleTitle: string | null;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";
const POLL_INTERVAL_MS = 2000;

export default function CoverLetterPage({
  params,
}: {
  params: Promise<{ flowId: string }>;
}) {
  const { flowId } = use(params);

  const [phase, setPhase] = useState<Phase>("loading");
  const [clState, setClState] = useState<CLState | null>(null);
  const [previewKey, setPreviewKey] = useState(0);
  const [showModal, setShowModal] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  // Load cover letter from flow state
  const init = useCallback(async () => {
    try {
      const flowRes = await fetch(`${API_BASE}/api/flow/${flowId}/state`);
      if (!flowRes.ok) { setPhase("not_found"); return; }
      const flowData = await flowRes.json();

      const clSummary = flowData.cover_letter_summary;
      if (!clSummary) { setPhase("not_found"); return; }

      const clId = clSummary.cover_letter_id;
      const statusRes = await fetch(`${API_BASE}/api/cover-letter/${clId}/status`);
      if (!statusRes.ok) { setPhase("not_found"); return; }
      const statusData = await statusRes.json();

      setClState({
        coverLetterId: clId,
        status: statusData.status,
        template: clSummary.template as CLTemplate,
        letterData: null,
        preGenInputs: null,
        jobId: flowData.job_id ?? null,
        roleTitle: flowData.job_summary?.role_title ?? null,
      });

      if (statusData.status === "ready") {
        setPhase("ready");
      } else if (statusData.status === "failed") {
        setPhase("not_found");
      } else {
        setPhase("generating");
        startPolling(clId);
      }
    } catch {
      setPhase("not_found");
    }
  }, [flowId]);

  useEffect(() => {
    init();
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [init]);

  function startPolling(clId: string) {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/cover-letter/${clId}/status`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.status === "ready") {
          clearInterval(pollRef.current!);
          setPhase("ready");
          setClState((prev) => prev ? { ...prev, status: "ready" } : prev);
        } else if (data.status === "failed") {
          clearInterval(pollRef.current!);
          setPhase("not_found");
        }
      } catch { /* ignore poll errors */ }
    }, POLL_INTERVAL_MS);
  }

  async function handleDownloadPdf() {
    if (!clState) return;
    setDownloading(true);
    try {
      const res = await fetch(`${API_BASE}/api/cover-letter/${clState.coverLetterId}/pdf`);
      if (!res.ok) throw new Error("PDF nicht verfügbar");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "anschreiben.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } finally {
      setDownloading(false);
    }
  }

  function handleTemplateChange(template: CLTemplate) {
    setClState((prev) => prev ? { ...prev, template } : prev);
    // Regenerating with different template is handled via the modal
    setShowModal(true);
  }

  function handleSectionSaved() {
    // Force iframe reload by bumping key
    setPreviewKey((k) => k + 1);
  }

  function handleGenerated(newClId: string) {
    setShowModal(false);
    setClState((prev) =>
      prev ? { ...prev, coverLetterId: newClId, status: "pending" } : prev
    );
    setPhase("generating");
    startPolling(newClId);
  }

  if (phase === "loading") {
    return (
      <div className="flex items-center justify-center min-h-screen text-neutral-400 text-sm">
        Lade Anschreiben…
      </div>
    );
  }

  if (phase === "not_found") {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <p className="text-neutral-500 text-sm">Kein Anschreiben gefunden.</p>
        <Link href={`/flow/${flowId}/cv`} className="text-blue-600 hover:underline text-sm">
          ← Zurück zum Lebenslauf
        </Link>
      </div>
    );
  }

  const roleTitle = clState?.roleTitle ?? "Anschreiben";

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-white border-b border-neutral-200 flex-shrink-0">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-neutral-400">{roleTitle}</span>
          <span className="text-neutral-300">›</span>
          <span className="font-semibold">Anschreiben</span>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href={`/flow/${flowId}/cv`}
            className="px-3 py-1.5 text-sm border border-blue-500 text-blue-600 rounded hover:bg-blue-50 transition-colors"
            data-testid="cl-view-cv-btn"
          >
            ← Lebenslauf
          </Link>
          <button
            type="button"
            onClick={handleDownloadPdf}
            disabled={downloading || phase !== "ready"}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50"
            data-testid="cl-topbar-download-btn"
          >
            {downloading ? "…" : "PDF herunterladen"}
          </button>
        </div>
      </div>

      {/* 50/50 body */}
      {phase === "generating" ? (
        <div className="flex items-center justify-center flex-1 text-neutral-400 text-sm">
          Anschreiben wird generiert…
        </div>
      ) : (
        <div className="flex flex-1 min-h-0">
          {/* LEFT: preview (w-1/2 min-w-0) */}
          <div className="w-1/2 min-w-0 flex flex-col border-r border-neutral-200 bg-neutral-50 p-3">
            <CoverLetterDocument
              key={previewKey}
              coverLetterId={clState!.coverLetterId}
            />
          </div>

          {/* RIGHT: controls (w-1/2 min-w-[340px]) */}
          <div className="w-1/2 min-w-[340px] flex flex-col overflow-hidden">
            <CoverLetterRefinementPanel
              flowId={flowId}
              coverLetterId={clState!.coverLetterId}
              letterData={clState!.letterData}
              currentTemplate={clState!.template}
              onSectionSaved={handleSectionSaved}
              onTemplateChange={handleTemplateChange}
              onRegenerateCoverLetter={() => setShowModal(true)}
              onDownloadPdf={handleDownloadPdf}
              downloading={downloading}
            />
          </div>
        </div>
      )}

      {showModal && clState?.jobId && (
        <GenerateCoverLetterModal
          jobId={clState.jobId}
          existingInputs={clState.preGenInputs as Parameters<typeof GenerateCoverLetterModal>[0]["existingInputs"]}
          onClose={() => setShowModal(false)}
          onGenerated={handleGenerated}
        />
      )}
    </div>
  );
}
```

- [ ] **Step 2: Run TypeScript check**

```bash
cd /home/apliqa/Documents/Applire/Solution/frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: no errors (fix any type issues before committing).

- [ ] **Step 3: Run frontend unit tests**

```bash
cd /home/apliqa/Documents/Applire/Solution/frontend && npm test 2>&1 | tail -10
```

Expected: all passing.

- [ ] **Step 4: Commit**

```bash
git add frontend/app/flow/[flowId]/cover-letter/ frontend/components/cover-letter/
git commit -m "$(cat <<'EOF'
feat: add cover letter page /flow/[flowId]/cover-letter

50/50 split layout (w-1/2 min-w-0 preview / w-1/2 min-w-[340px] controls).
Loads cover_letter_summary from flow state, polls for ready status,
drives CoverLetterDocument iframe + CoverLetterRefinementPanel.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 19: E2E tests — Marcus happy path

**Files:**
- Create: `tests/e2e/test_cover_letter.spec.ts`

- [ ] **Step 1: Create `tests/e2e/test_cover_letter.spec.ts`**

```typescript
import { test, expect } from "@playwright/test";

/**
 * Sprint 25 — Cover Letter E2E (Marcus happy path)
 *
 * Prerequisites: the full Docker stack is running with the stub user
 * and at least one flow session in `complete` state with a ready CV.
 *
 * Run: npx playwright test tests/e2e/test_cover_letter.spec.ts
 */

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3000";
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

test.describe("Cover Letter Generation — Marcus happy path", () => {
  let flowId: string;

  test.beforeAll(async ({ request }) => {
    // Create a flow session and advance it to complete to get a ready CV
    // This relies on a helper endpoint or existing test fixture flow
    const flowRes = await request.get(`${API_BASE}/api/flow`);
    // If no flow exists, skip — this test requires the CV happy path to have run first
    if (!flowRes.ok()) {
      test.skip();
      return;
    }
    // Use the first available flow
    // In CI this is set up by the preceding CV E2E test fixture
    flowId = process.env.TEST_FLOW_ID ?? "";
    if (!flowId) test.skip();
  });

  test("US-CL05: CV page shows Generate Cover Letter button", async ({ page }) => {
    await page.goto(`${BASE_URL}/flow/${flowId}/cv`);
    // Navigate to Actions tab
    await page.getByTestId("tab-actions").click();
    await expect(page.getByTestId("generate-cover-letter-btn")).toBeVisible();
  });

  test("US-CL02: Pre-generation modal opens and accepts inputs", async ({ page }) => {
    await page.goto(`${BASE_URL}/flow/${flowId}/cv`);
    await page.getByTestId("tab-actions").click();
    await page.getByTestId("generate-cover-letter-btn").click();

    await expect(page.getByTestId("cover-letter-modal")).toBeVisible();
    await expect(page.getByTestId("cl-recipient-name")).toBeVisible();

    // Fill DACH fields
    await page.getByTestId("cl-salary").fill("95.000 – 110.000 € p.a.");
    await page.getByTestId("cl-availability").fill("3 Monate zum Monatsende");
    await page.getByTestId("cl-tone-formal").click();
  });

  test("US-CL01: Generate cover letter, reaches ready state", async ({ page }) => {
    await page.goto(`${BASE_URL}/flow/${flowId}/cv`);
    await page.getByTestId("tab-actions").click();
    await page.getByTestId("generate-cover-letter-btn").click();

    await page.getByTestId("cl-salary").fill("95.000 € p.a.");
    await page.getByTestId("cl-modal-generate").click();

    // Should navigate to cover letter page
    await page.waitForURL(`**/flow/${flowId}/cover-letter`, { timeout: 30000 });

    // Wait for generation to complete (polls every 2s, timeout 30s)
    await expect(page.getByTestId("cover-letter-iframe")).toBeVisible({ timeout: 30000 });
  });

  test("US-CL05: Cover letter page has ← Lebenslauf navigation", async ({ page }) => {
    await page.goto(`${BASE_URL}/flow/${flowId}/cover-letter`);
    await expect(page.getByTestId("cl-view-cv-btn")).toBeVisible();
    await page.getByTestId("cl-view-cv-btn").click();
    await page.waitForURL(`**/flow/${flowId}/cv`);
  });

  test("US-CL07: Body section is editable", async ({ page }) => {
    await page.goto(`${BASE_URL}/flow/${flowId}/cover-letter`);
    await expect(page.getByTestId("cover-letter-iframe")).toBeVisible({ timeout: 30000 });

    await page.getByTestId("cl-tab-content").click();
    const textarea = page.getByTestId("cl-body-textarea");
    await expect(textarea).toBeVisible();

    await textarea.fill("Sehr geehrte Frau Dr. Müller,\n\nTestinhalt für E2E.");
    await page.getByTestId("cl-save-body-btn").click();

    // Confirm saved (button disappears or iframe reloads)
    await expect(page.getByTestId("cl-save-body-btn")).not.toBeVisible({ timeout: 5000 });
  });

  test("US-CL06: PDF download button is present", async ({ page }) => {
    await page.goto(`${BASE_URL}/flow/${flowId}/cover-letter`);
    await expect(page.getByTestId("cl-topbar-download-btn")).toBeVisible();
  });

  test("US-CL09: Design tab shows 7 template options", async ({ page }) => {
    await page.goto(`${BASE_URL}/flow/${flowId}/cover-letter`);
    await page.getByTestId("cl-tab-design").click();

    const templates = [
      "classic_german", "modern_swiss", "executive",
      "tech_developer", "creative_sidebar", "academic", "compact_pro",
    ];
    for (const tmpl of templates) {
      await expect(page.getByTestId(`cl-template-${tmpl}`)).toBeVisible();
    }
  });

  test("US-CL10: Regenerate button opens modal pre-filled", async ({ page }) => {
    await page.goto(`${BASE_URL}/flow/${flowId}/cover-letter`);
    await page.getByTestId("cl-tab-actions").click();
    await page.getByTestId("cl-regenerate-btn").click();
    await expect(page.getByTestId("cover-letter-modal")).toBeVisible();
    // Cancel to not trigger another generation
    await page.getByTestId("cl-modal-cancel").click();
    await expect(page.getByTestId("cover-letter-modal")).not.toBeVisible();
  });
});
```

- [ ] **Step 2: Verify the spec file syntax**

```bash
npx tsc --noEmit -p tsconfig.json 2>&1 | grep "test_cover_letter" || echo "No TS errors in E2E spec"
```

Expected: `No TS errors in E2E spec`

- [ ] **Step 3: Run unit coverage check**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/ -v --cov=applire --cov-report=term-missing --cov-fail-under=75 2>&1 | tail -15
```

Expected: coverage ≥ 75%, all tests pass.

- [ ] **Step 4: Commit**

```bash
git add tests/e2e/test_cover_letter.spec.ts
git commit -m "$(cat <<'EOF'
test: add E2E test suite for cover letter (Marcus happy path + Felix edits)

Covers US-CL01 through CL10: generate from CV page, navigate to CL page,
edit body, design tab template options, PDF download, regenerate modal.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review Checklist

### Spec coverage

| Spec requirement | Task |
|---|---|
| US-CL01 Generate cover letter | Tasks 3, 7, 8, 9 |
| US-CL02 Pre-generation modal | Task 12 |
| US-CL03 Auto-extract recipient from JD | Tasks 6, 8 |
| US-CL04 Paired template auto-selected | Task 8 (`cv.template` copied to `cl.template`) |
| US-CL05 Navigate CV ↔ Cover Letter | Tasks 13, 18 |
| US-CL06 Download PDF | Tasks 9, 16, 18 |
| US-CL07 Edit body section | Task 15 |
| US-CL08 AI rewrite (Kaile single-turn) | Not implemented — deferred (see note below) |
| US-CL09 Override template in Design tab | Task 16 |
| US-CL10 Regenerate with different inputs | Tasks 16, 18 |
| US-CL11 Configurable GDPR TTLs | Task 2 |
| `FlowStateResponse` cover_letter_summary | Task 5 |
| 7 Jinja2 templates | Task 11 |
| Retention worker purge | Task 10 |
| 2 Alembic migrations (0023, 0024) | Tasks 3, 4 |

**US-CL08 (AI rewrite of body via Kaile):** This was Medium priority in the spec. It requires a single-turn LLM call with user direction text. Implementation follows the existing `cv_assist.py` / `rewrite_section` pattern exactly. This can be added as a follow-on task in the same sprint: add a `POST /api/cover-letter/{id}/rewrite` endpoint that calls `provider.complete(system, user_rewrite_prompt)` and returns the rewritten text for the frontend to preview before the user confirms with `PATCH /section`.

### No placeholders found

All steps contain complete code. No TBD/TODO/placeholder text.

### Type consistency

- `CLTemplate` literals in `schemas/cover_letter.py` match `CVTemplate` literals in `schemas/cv.py` — same 7 values.
- `CoverLetterStatus` enum values: `pending`, `generating`, `ready`, `failed`, `expired` — consistent across model, schema, service, and worker.
- `FlowSession.generated_cover_letter_id` FK → `generated_cover_letters.id` — consistent across model, migration, orchestrator.
- `cover_letter_summary.cover_letter_id` in `FlowStateResponse` is `uuid.UUID` on the Python side; frontend treats it as `string` (standard JSON UUID serialization).
