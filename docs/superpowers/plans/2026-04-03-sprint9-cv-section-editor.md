# Sprint 9 — CV Section Editor: Foundation & Core Editing — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete backend foundation (Alembic migration, three new endpoints, HTML render update) and the full frontend editing loop for the Finetuner persona, so Felix can enter Fine-tune mode from the CV preview, edit any section, and see the preview update live on save.

**Architecture:** Two new JSONB columns on `generated_cvs` (`content_snapshot`, `section_overrides`) store structured rendering data and user overrides respectively. Three new backend endpoints handle section listing, override writing, and re-rendering. Five new frontend components implement the split-screen editing experience.

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy / Alembic (backend); Next.js 15 / React 19 / Tailwind CSS v4 / Vitest + RTL (frontend); Playwright (E2E)

---

## File Map

### New backend files
| File | Purpose |
|---|---|
| `backend/alembic/versions/0015_add_cv_section_editor_columns.py` | Alembic migration — adds `content_snapshot` + `section_overrides` to `generated_cvs` |
| `backend/applire/schemas/cv_sections.py` | Pydantic request/response schemas for the section editor API |
| `backend/applire/services/cv_gap_mapper.py` | Keyword-overlap gap-to-section mapper (no LLM) |
| `backend/applire/services/cv_section_editor.py` | Section override read/write, snapshot extraction, profile save, Jinja2 re-render |
| `backend/tests/unit/test_iter23_section_editor.py` | Unit tests for all three new endpoints |

### Modified backend files
| File | What changes |
|---|---|
| `backend/applire/models/cv.py` | Add `content_snapshot` and `section_overrides` mapped columns |
| `backend/applire/services/cv.py` | Call `build_content_snapshot()` after LLM tailoring in `_render_cv_background`; update `get_cv_html()` to apply overrides |
| `backend/applire/routers/cv.py` | Add `GET /{cv_id}/sections` and `PATCH /{cv_id}/sections/{section_id}` routes |

### New frontend files
| File | Purpose |
|---|---|
| `frontend/components/cv/FineTunePanel.tsx` | Split-screen container: section list left, CV preview iframe right |
| `frontend/components/cv/SectionEditor.tsx` | Textarea + Save/Cancel for one section |
| `frontend/components/cv/GapHint.tsx` | Gap hint card with "Write myself" / "Let Kaile help" (disabled) |
| `frontend/components/cv/SaveScopePrompt.tsx` | "Save to Profile" vs "Just this CV" dialog |
| `frontend/components/cv/__tests__/FineTunePanel.test.tsx` | Unit tests for FineTunePanel |
| `frontend/components/cv/__tests__/SectionEditor.test.tsx` | Unit tests for SectionEditor |
| `frontend/components/cv/__tests__/SaveScopePrompt.test.tsx` | Unit tests for SaveScopePrompt |
| `frontend/e2e/finetuner-sprint9.spec.ts` | Playwright E2E test |

### Modified frontend files
| File | What changes |
|---|---|
| `frontend/components/cv/CVPreview.tsx` | Add Fine-tune toggle button and conditional `<FineTunePanel>` mount |

---

## Content encoding convention

All section content is stored and transmitted as **plain text**:
- `introduction` → the summary string as-is
- `position::{uuid}` → bullet points joined with `\n` (one bullet per line)
- `skills` → skill names joined with `\n` (one skill per line)

The section editor textarea uses this same format — the user sees and edits newline-separated bullets for position sections.

---

## Task 1: Alembic migration

**Files:**
- Create: `backend/alembic/versions/0015_add_cv_section_editor_columns.py`

- [ ] **Step 1: Write the migration file**

```python
# backend/alembic/versions/0015_add_cv_section_editor_columns.py
"""Add content_snapshot and section_overrides to generated_cvs

Revision ID: 0015
Revises: 0014
Create Date: 2026-04-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # content_snapshot: structured rendering context populated at generation time.
    # Nullable: pre-existing CVs have no snapshot; section editor gracefully handles NULL.
    op.add_column(
        "generated_cvs",
        sa.Column("content_snapshot", JSONB(), nullable=True),
    )
    # section_overrides: user edits keyed by section ID. Default is empty object.
    # Nullable at DB level; service layer treats NULL as {}.
    op.add_column(
        "generated_cvs",
        sa.Column("section_overrides", JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("generated_cvs", "section_overrides")
    op.drop_column("generated_cvs", "content_snapshot")
```

- [ ] **Step 2: Update the GeneratedCV SQLAlchemy model**

In `backend/applire/models/cv.py`, add two mapped columns after `error_message`:

```python
# After:  error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

content_snapshot: Mapped[dict | None] = mapped_column(_JSON, nullable=True)
section_overrides: Mapped[dict | None] = mapped_column(_JSON, nullable=True)
```

- [ ] **Step 3: Run the migration to verify it applies cleanly**

```bash
cd backend && alembic upgrade head
```

Expected: `Running upgrade 0014 -> 0015, Add content_snapshot and section_overrides to generated_cvs`

- [ ] **Step 4: Commit**

```bash
git add backend/alembic/versions/0015_add_cv_section_editor_columns.py backend/applire/models/cv.py
git commit -m "feat(db): add content_snapshot and section_overrides to generated_cvs (23.1)"
```

---

## Task 2: New schemas for the section editor API

**Files:**
- Create: `backend/applire/schemas/cv_sections.py`

- [ ] **Step 1: Write the schema file**

```python
# backend/applire/schemas/cv_sections.py
"""Pydantic schemas for the CV Section Editor API (Sprint 9, ADR-019)."""
import uuid
from typing import Optional

from pydantic import BaseModel, Field


class SnapshotPosition(BaseModel):
    """One work history entry as stored in content_snapshot."""
    id: str  # stable UUID string assigned at snapshot time
    index: int  # index in tailored_data.work_history — used for override application
    title: str
    company: str
    period: str
    bullets: list[str]


class ContentSnapshot(BaseModel):
    """Structured rendering context captured at CV generation time."""
    introduction: str
    positions: list[SnapshotPosition]
    skills: list[str]


class GapHintItem(BaseModel):
    id: str
    label: str


class SectionItem(BaseModel):
    section_id: str  # e.g. "introduction", "position::uuid", "skills"
    label: str       # Human-readable, e.g. "Introduction", "Senior Engineer — SAP"
    content: str     # Snapshot content merged with override (override wins)
    has_override: bool
    gaps: list[GapHintItem]


class CVSectionsResponse(BaseModel):
    sections: list[SectionItem]
    general_gaps: list[GapHintItem]


class SectionPatchRequest(BaseModel):
    content: str = Field(..., max_length=10_000)
    save_to_profile: bool = False


class SectionPatchResponse(BaseModel):
    html: str
    overrides_applied: list[str]
```

- [ ] **Step 2: Commit**

```bash
git add backend/applire/schemas/cv_sections.py
git commit -m "feat(schema): add CV section editor request/response schemas (23.3 pre)"
```

---

## Task 3: Gap mapper service

**Files:**
- Create: `backend/applire/services/cv_gap_mapper.py`

The gap mapper takes a list of gap labels (strings from `GapAnalysis.category_b` and `category_b`) and maps each one to the section whose content contains the most keyword matches.

- [ ] **Step 1: Write a failing unit test for the gap mapper**

Add this file (we'll populate the full test file in Task 10, but test the mapper logic now):

```python
# backend/tests/unit/test_cv_gap_mapper.py
from applire.services.cv_gap_mapper import map_gaps_to_sections


def test_gap_maps_to_section_with_most_keyword_overlap():
    sections = {
        "introduction": "experienced python developer with django",
        "position::abc": "built rest apis using python flask",
        "skills": "java sql git",
    }
    gaps = ["python", "django"]
    result = map_gaps_to_sections(gaps, sections)
    # "python" appears in both introduction and position::abc; "django" only in introduction
    # introduction has 2 matches, position::abc has 1
    assert result["introduction"] == ["python", "django"]
    assert result.get("position::abc") == ["python"]
    assert "skills" not in result or result["skills"] == []


def test_unmatched_gap_goes_to_general():
    sections = {"introduction": "java developer", "skills": "java"}
    gaps = ["kubernetes"]
    result = map_gaps_to_sections(gaps, sections)
    assert result.get("__general__") == ["kubernetes"]


def test_empty_gaps_returns_empty():
    sections = {"introduction": "some text"}
    result = map_gaps_to_sections([], sections)
    assert result == {}
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd backend && python -m pytest tests/unit/test_cv_gap_mapper.py -v
```

Expected: `ImportError: cannot import name 'map_gaps_to_sections'`

- [ ] **Step 3: Implement the gap mapper**

```python
# backend/applire/services/cv_gap_mapper.py
"""Keyword-based gap-to-section mapper (no LLM, ~5ms).

For each gap label, tokenise it and count how many of its tokens appear
in each section's content. The section with the highest score gets the
gap assigned to it. Ties: first section wins. Zero-score gaps fall into
the __general__ bucket.
"""
import re


def _tokenise(text: str) -> set[str]:
    """Lowercase word tokens, 2+ chars."""
    return {w for w in re.findall(r"\b[a-zA-ZÀ-ÿ0-9.#+\-]{2,}\b", text.lower())}


def map_gaps_to_sections(
    gaps: list[str],
    sections: dict[str, str],  # section_id -> section content
) -> dict[str, list[str]]:
    """Return a dict mapping section_id -> [gap_labels] assigned to that section.

    Unmatched gaps are placed under the key "__general__".
    """
    if not gaps:
        return {}

    # Pre-tokenise section contents once
    section_tokens: dict[str, set[str]] = {
        sid: _tokenise(content) for sid, content in sections.items()
    }

    result: dict[str, list[str]] = {}

    for gap in gaps:
        gap_tokens = _tokenise(gap)
        if not gap_tokens:
            result.setdefault("__general__", []).append(gap)
            continue

        best_section: str | None = None
        best_score = 0

        for sid, tokens in section_tokens.items():
            score = len(gap_tokens & tokens)
            if score > best_score:
                best_score = score
                best_section = sid

        if best_section is None or best_score == 0:
            result.setdefault("__general__", []).append(gap)
        else:
            result.setdefault(best_section, []).append(gap)

    return result
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd backend && python -m pytest tests/unit/test_cv_gap_mapper.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/applire/services/cv_gap_mapper.py backend/tests/unit/test_cv_gap_mapper.py
git commit -m "feat(service): add keyword-based gap-to-section mapper (23.3)"
```

---

## Task 4: Section editor service

**Files:**
- Create: `backend/applire/services/cv_section_editor.py`
- Modify: `backend/applire/services/cv.py` (add `build_content_snapshot`, update `get_cv_html`)

This task implements:
- `build_content_snapshot()` — extracts structured snapshot from `TailoredCVData`
- `get_cv_sections()` — returns merged sections + gap hints
- `patch_cv_section()` — writes override, triggers re-render, optional profile save
- Update `get_cv_html()` — applies overrides before Jinja2 render

- [ ] **Step 1: Write the section editor service**

```python
# backend/applire/services/cv_section_editor.py
"""CV Section Editor service (Sprint 9, ADR-019).

Responsibilities:
- build_content_snapshot: extract structured snapshot from TailoredCVData at generation time
- get_cv_sections: return merged snapshot+overrides+gap hints for GET /api/cv/{id}/sections
- patch_cv_section: write override, re-render, optionally save to profile
- apply_overrides_to_tailored: merge section_overrides on top of TailoredCVData (used by get_cv_html)
"""
import uuid
from copy import deepcopy

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from applire.models.cv import GeneratedCV
from applire.models.flow import FlowSession
from applire.models.gap import GapAnalysis
from applire.models.profile import MasterProfile
from applire.schemas.cv import TailoredCVData, TailoredWorkEntry
from applire.schemas.cv_sections import (
    ContentSnapshot,
    CVSectionsResponse,
    GapHintItem,
    SectionItem,
    SectionPatchResponse,
    SnapshotPosition,
)
from applire.services.cv_gap_mapper import map_gaps_to_sections


# ---------------------------------------------------------------------------
# Snapshot extraction
# ---------------------------------------------------------------------------


def build_content_snapshot(tailored: TailoredCVData) -> dict:
    """Extract a structured snapshot dict from TailoredCVData.

    Called once at generation time. ~5ms, no LLM.
    Returns a plain dict (stored as JSONB).
    """
    positions = []
    for idx, entry in enumerate(tailored.work_history):
        period = entry.start_date
        if entry.end_date:
            period = f"{entry.start_date} – {entry.end_date}"
        positions.append(
            SnapshotPosition(
                id=str(uuid.uuid4()),
                index=idx,
                title=entry.role,
                company=entry.company,
                period=period,
                bullets=list(entry.bullets),
            ).model_dump()
        )

    snapshot = ContentSnapshot(
        introduction=tailored.summary,
        positions=positions,
        skills=list(tailored.skills),
    )
    return snapshot.model_dump()


# ---------------------------------------------------------------------------
# Override application (used by get_cv_html)
# ---------------------------------------------------------------------------


def apply_overrides_to_tailored(
    tailored: TailoredCVData,
    content_snapshot: dict | None,
    section_overrides: dict | None,
) -> TailoredCVData:
    """Return a new TailoredCVData with section_overrides applied.

    If section_overrides is None or empty, returns tailored unchanged (byte-identical render).
    """
    if not section_overrides:
        return tailored

    # Deep-copy so we don't mutate the original
    data = tailored.model_dump()

    for section_id, content in section_overrides.items():
        if section_id == "introduction":
            data["summary"] = content

        elif section_id == "skills":
            data["skills"] = [s.strip() for s in content.split("\n") if s.strip()]

        elif section_id.startswith("position::") and content_snapshot:
            position_uuid = section_id[len("position::"):]
            # Find the position's work_history index from the snapshot
            snapshot_positions = content_snapshot.get("positions", [])
            for snap_pos in snapshot_positions:
                if snap_pos.get("id") == position_uuid:
                    idx = snap_pos.get("index", -1)
                    if 0 <= idx < len(data.get("work_history", [])):
                        data["work_history"][idx]["bullets"] = [
                            b.strip() for b in content.split("\n") if b.strip()
                        ]
                    break

    return TailoredCVData.model_validate(data)


# ---------------------------------------------------------------------------
# GET /api/cv/{id}/sections
# ---------------------------------------------------------------------------


async def get_cv_sections(cv_id: uuid.UUID, db: AsyncSession) -> CVSectionsResponse:
    """Load sections + overrides + gap hints for a CV.

    Returns empty sections list with a hint when content_snapshot is NULL.
    Returns 404 if CV not found.
    """
    record = await _load_cv(cv_id, db)

    # NULL snapshot — CV was generated before this sprint
    if record.content_snapshot is None:
        return CVSectionsResponse(sections=[], general_gaps=[])

    snapshot = ContentSnapshot.model_validate(record.content_snapshot)
    overrides: dict = record.section_overrides or {}

    # Build section content map for gap mapping
    section_contents: dict[str, str] = {
        "introduction": overrides.get("introduction", snapshot.introduction),
        "skills": overrides.get("skills", "\n".join(snapshot.skills)),
    }
    for pos in snapshot.positions:
        sid = f"position::{pos.id}"
        section_contents[sid] = overrides.get(sid, "\n".join(pos.bullets))

    # Load gap analysis via FlowSession
    gap_map: dict[str, list[str]] = {}
    general_gaps: list[str] = []

    flow_result = await db.execute(
        select(FlowSession)
        .where(
            FlowSession.generated_cv_id == cv_id,
            FlowSession.deleted_at.is_(None),
        )
        .limit(1)
    )
    flow = flow_result.scalar_one_or_none()

    if flow and flow.gap_analysis_id:
        gap_analysis = await db.get(GapAnalysis, flow.gap_analysis_id)
        if gap_analysis:
            all_gaps: list[str] = (
                list(gap_analysis.category_b) + list(gap_analysis.category_c)
            )
            raw_map = map_gaps_to_sections(all_gaps, section_contents)
            gap_map = {k: v for k, v in raw_map.items() if k != "__general__"}
            general_gaps = raw_map.get("__general__", [])

    # Build section items
    sections: list[SectionItem] = []

    # Introduction
    intro_content = overrides.get("introduction", snapshot.introduction)
    sections.append(
        SectionItem(
            section_id="introduction",
            label="Introduction",
            content=intro_content,
            has_override="introduction" in overrides,
            gaps=[
                GapHintItem(id=g, label=g)
                for g in gap_map.get("introduction", [])
            ],
        )
    )

    # Positions
    for pos in snapshot.positions:
        sid = f"position::{pos.id}"
        pos_content = overrides.get(sid, "\n".join(pos.bullets))
        label = f"{pos.title} — {pos.company}"
        sections.append(
            SectionItem(
                section_id=sid,
                label=label,
                content=pos_content,
                has_override=sid in overrides,
                gaps=[GapHintItem(id=g, label=g) for g in gap_map.get(sid, [])],
            )
        )

    # Skills
    skills_content = overrides.get("skills", "\n".join(snapshot.skills))
    sections.append(
        SectionItem(
            section_id="skills",
            label="Skills",
            content=skills_content,
            has_override="skills" in overrides,
            gaps=[GapHintItem(id=g, label=g) for g in gap_map.get("skills", [])],
        )
    )

    return CVSectionsResponse(
        sections=sections,
        general_gaps=[GapHintItem(id=g, label=g) for g in general_gaps],
    )


# ---------------------------------------------------------------------------
# PATCH /api/cv/{id}/sections/{section_id}
# ---------------------------------------------------------------------------

_VALID_STATIC_SECTION_IDS = {"introduction", "skills"}


async def patch_cv_section(
    cv_id: uuid.UUID,
    section_id: str,
    content: str,
    save_to_profile: bool,
    db: AsyncSession,
) -> SectionPatchResponse:
    """Write a section override and re-render the CV HTML.

    Validates section_id against snapshot. Optionally saves to profile.
    Returns updated HTML and list of all applied overrides.
    """
    from applire.services.cv import _jinja_env, _TEMPLATE_FILES
    from applire.schemas.cv import TailoredCVData

    record = await _load_cv(cv_id, db)

    # Validate section_id
    valid_position_ids: set[str] = set()
    if record.content_snapshot:
        for pos in record.content_snapshot.get("positions", []):
            valid_position_ids.add(f"position::{pos['id']}")

    if section_id not in _VALID_STATIC_SECTION_IDS and section_id not in valid_position_ids:
        raise ValueError(f"Unknown section_id: {section_id!r}")

    # Write override
    overrides = dict(record.section_overrides or {})
    overrides[section_id] = content
    record.section_overrides = overrides
    await db.commit()
    await db.refresh(record)

    # Optional profile save
    if save_to_profile:
        await _save_section_to_profile(cv_id, section_id, content, record, db)

    # Jinja2 re-render with overrides applied
    tailored = TailoredCVData.model_validate(record.tailored_data)
    tailored_with_overrides = apply_overrides_to_tailored(
        tailored, record.content_snapshot, overrides
    )
    template_file = _TEMPLATE_FILES.get(record.template, "lebenslauf.html.j2")
    template = _jinja_env.get_template(template_file)
    html = template.render(cv=tailored_with_overrides)

    return SectionPatchResponse(
        html=html,
        overrides_applied=list(overrides.keys()),
    )


async def _save_section_to_profile(
    cv_id: uuid.UUID,
    section_id: str,
    content: str,
    record: GeneratedCV,
    db: AsyncSession,
) -> None:
    """Additively merge the edited section content into the Master Profile (ADR-013)."""
    from applire.schemas.profile import MasterProfileData

    profile = await db.get(MasterProfile, record.profile_id)
    if profile is None:
        return

    profile_data = MasterProfileData.model_validate(profile.profile_json)

    if section_id == "introduction":
        if profile_data.professional_summary is None:
            from applire.schemas.profile import ProfessionalSummary
            profile_data.professional_summary = ProfessionalSummary()
        profile_data.professional_summary.de = content

    elif section_id == "skills":
        new_skills_raw = [s.strip() for s in content.split("\n") if s.strip()]
        existing = {s.name.lower() for s in (profile_data.skills or [])}
        from applire.schemas.profile import Skill
        for skill_name in new_skills_raw:
            if skill_name.lower() not in existing:
                profile_data.skills = list(profile_data.skills or []) + [
                    Skill(name=skill_name, level=None, years=None)
                ]

    elif section_id.startswith("position::") and record.content_snapshot:
        position_uuid = section_id[len("position::"):]
        snapshot_positions = record.content_snapshot.get("positions", [])
        snap_pos = next(
            (p for p in snapshot_positions if p.get("id") == position_uuid), None
        )
        if snap_pos and profile_data.work_history:
            new_bullets = [b.strip() for b in content.split("\n") if b.strip()]
            # Match by company + approximate title
            for entry in profile_data.work_history:
                if entry.company.lower() == snap_pos.get("company", "").lower():
                    entry.bullets = new_bullets
                    break

    profile.profile_json = profile_data.model_dump()
    await db.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _load_cv(cv_id: uuid.UUID, db: AsyncSession) -> GeneratedCV:
    from sqlalchemy import select
    result = await db.execute(
        select(GeneratedCV).where(
            GeneratedCV.id == cv_id,
            GeneratedCV.deleted_at.is_(None),
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise LookupError(f"Generated CV {cv_id} not found")
    return record
```

- [ ] **Step 2: Update `get_cv_html` in `services/cv.py` to apply overrides**

In `backend/applire/services/cv.py`, replace the existing `get_cv_html` function:

```python
async def get_cv_html(cv_id: uuid.UUID, db: AsyncSession) -> str:
    from applire.services.cv_section_editor import apply_overrides_to_tailored
    record = await _load_cv_ready(cv_id, db)
    tailored = TailoredCVData.model_validate(record.tailored_data)
    tailored = apply_overrides_to_tailored(
        tailored, record.content_snapshot, record.section_overrides
    )
    template_file = _TEMPLATE_FILES.get(record.template, "lebenslauf.html.j2")
    template = _jinja_env.get_template(template_file)
    return template.render(cv=tailored)
```

- [ ] **Step 3: Populate content_snapshot in `_render_cv_background`**

In `backend/applire/services/cv.py`, after `tailored = TailoredCVData.model_validate(tailored_raw)` and before `record.tailored_data = tailored.model_dump()`, add:

```python
            from applire.services.cv_section_editor import build_content_snapshot
            record.content_snapshot = build_content_snapshot(tailored)
```

The full block after the change (for clarity — replace existing lines 292-295):

```python
            tailored = TailoredCVData.model_validate(tailored_raw)

            from applire.services.cv_section_editor import build_content_snapshot
            record.content_snapshot = build_content_snapshot(tailored)

            record.tailored_data = tailored.model_dump()
            record.status = CVGenerationStatus.ready.value
            record.error_message = None
            await db.commit()
```

- [ ] **Step 4: Commit**

```bash
git add backend/applire/services/cv_section_editor.py backend/applire/services/cv.py
git commit -m "feat(service): add section editor service, snapshot extraction, override application (23.2, 23.3, 23.4, 23.5)"
```

---

## Task 5: New routes — GET /sections and PATCH /sections/{section_id}

**Files:**
- Modify: `backend/applire/routers/cv.py`

- [ ] **Step 1: Add the two new routes to `routers/cv.py`**

Add this import at the top of the existing imports section:

```python
from applire.schemas.cv_sections import CVSectionsResponse, SectionPatchRequest, SectionPatchResponse
from applire.services.cv_section_editor import get_cv_sections, patch_cv_section
```

Add these two route handlers at the end of the file (before the closing):

```python
@router.get("/{cv_id}/sections", response_model=CVSectionsResponse)
async def get_sections(
    cv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> CVSectionsResponse:
    """Return structured sections with gap hints (23.3). Empty sections if no snapshot yet."""
    try:
        return await get_cv_sections(cv_id, db)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.patch(
    "/{cv_id}/sections/{section_id:path}",
    response_model=SectionPatchResponse,
)
async def patch_section(
    cv_id: uuid.UUID,
    section_id: str,
    body: SectionPatchRequest,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> SectionPatchResponse:
    """Write section override and re-render CV HTML (23.4).

    Returns updated HTML and the full list of applied overrides.
    422 if section_id is unknown or content > 10,000 chars.
    """
    try:
        return await patch_cv_section(
            cv_id, section_id, body.content, body.save_to_profile, db
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
```

Note: `section_id:path` captures `position::uuid` correctly (the `::` would otherwise be misrouted).

- [ ] **Step 2: Start the backend dev server and smoke-test the new routes appear**

```bash
cd backend && uvicorn applire.main:app --reload --port 8001
```

In a second terminal:
```bash
curl -s http://localhost:8001/openapi.json | python -m json.tool | grep -A2 '"sections"'
```

Expected: the two new paths appear in the OpenAPI spec.

- [ ] **Step 3: Commit**

```bash
git add backend/applire/routers/cv.py
git commit -m "feat(api): add GET /sections and PATCH /sections/{section_id} routes (23.3, 23.4)"
```

---

## Task 6: Backend unit tests

**Files:**
- Create: `backend/tests/unit/test_iter23_section_editor.py`

This uses the same `TestClient` + `AsyncMock` pattern as `test_cv_html_headers.py`.

- [ ] **Step 1: Write the unit tests**

```python
# backend/tests/unit/test_iter23_section_editor.py
"""Unit tests for Sprint 9 CV Section Editor endpoints (23.14)."""
import uuid
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from applire.auth import get_auth_provider
from applire.db.session import get_db
from applire.routers.cv import router

_CV_ID = str(uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
_SECTION_ID = "introduction"
_POSITION_UUID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
_POSITION_SECTION_ID = f"position::{_POSITION_UUID}"


async def _stub_db():
    yield None


@pytest.fixture()
def client():
    app = FastAPI()
    app.dependency_overrides[get_auth_provider] = lambda: None
    app.dependency_overrides[get_db] = _stub_db
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# GET /api/cv/{id}/sections
# ---------------------------------------------------------------------------


def test_get_sections_returns_200_with_sections(client):
    from applire.schemas.cv_sections import CVSectionsResponse, SectionItem, GapHintItem
    mock_response = CVSectionsResponse(
        sections=[
            SectionItem(
                section_id="introduction",
                label="Introduction",
                content="Experienced developer",
                has_override=False,
                gaps=[GapHintItem(id="Python", label="Python")],
            )
        ],
        general_gaps=[],
    )
    with patch(
        "applire.routers.cv.get_cv_sections",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = client.get(f"/api/cv/{_CV_ID}/sections")

    assert response.status_code == 200
    data = response.json()
    assert len(data["sections"]) == 1
    assert data["sections"][0]["section_id"] == "introduction"
    assert data["sections"][0]["gaps"][0]["label"] == "Python"


def test_get_sections_returns_404_when_cv_not_found(client):
    with patch(
        "applire.routers.cv.get_cv_sections",
        new_callable=AsyncMock,
        side_effect=LookupError("CV not found"),
    ):
        response = client.get(f"/api/cv/{_CV_ID}/sections")

    assert response.status_code == 404


def test_get_sections_returns_empty_list_when_no_snapshot(client):
    from applire.schemas.cv_sections import CVSectionsResponse
    mock_response = CVSectionsResponse(sections=[], general_gaps=[])
    with patch(
        "applire.routers.cv.get_cv_sections",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = client.get(f"/api/cv/{_CV_ID}/sections")

    assert response.status_code == 200
    assert response.json()["sections"] == []


# ---------------------------------------------------------------------------
# PATCH /api/cv/{id}/sections/{section_id}
# ---------------------------------------------------------------------------


def test_patch_section_returns_html_and_overrides_applied(client):
    from applire.schemas.cv_sections import SectionPatchResponse
    mock_response = SectionPatchResponse(
        html="<html><body>Updated CV</body></html>",
        overrides_applied=["introduction"],
    )
    with patch(
        "applire.routers.cv.patch_cv_section",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = client.patch(
            f"/api/cv/{_CV_ID}/sections/{_SECTION_ID}",
            json={"content": "My edited summary", "save_to_profile": False},
        )

    assert response.status_code == 200
    data = response.json()
    assert "<html>" in data["html"]
    assert "introduction" in data["overrides_applied"]


def test_patch_section_returns_422_for_invalid_section_id(client):
    with patch(
        "applire.routers.cv.patch_cv_section",
        new_callable=AsyncMock,
        side_effect=ValueError("Unknown section_id: 'nonexistent'"),
    ):
        response = client.patch(
            f"/api/cv/{_CV_ID}/sections/nonexistent",
            json={"content": "text", "save_to_profile": False},
        )

    assert response.status_code == 422


def test_patch_section_rejects_content_over_10000_chars(client):
    """Pydantic max_length=10_000 validation fires before the service is called."""
    long_content = "x" * 10_001
    response = client.patch(
        f"/api/cv/{_CV_ID}/sections/{_SECTION_ID}",
        json={"content": long_content, "save_to_profile": False},
    )
    assert response.status_code == 422


def test_patch_section_passes_save_to_profile_flag(client):
    from applire.schemas.cv_sections import SectionPatchResponse
    mock_service = AsyncMock(
        return_value=SectionPatchResponse(
            html="<html></html>",
            overrides_applied=["introduction"],
        )
    )
    with patch("applire.routers.cv.patch_cv_section", new=mock_service):
        client.patch(
            f"/api/cv/{_CV_ID}/sections/{_SECTION_ID}",
            json={"content": "text", "save_to_profile": True},
        )

    mock_service.assert_called_once()
    _, kwargs = mock_service.call_args
    # save_to_profile is the 4th positional arg
    call_args = mock_service.call_args.args
    assert call_args[3] is True  # save_to_profile


# ---------------------------------------------------------------------------
# GET /api/cv/{id}/html — regression: overrides don't break existing behaviour
# ---------------------------------------------------------------------------


def test_html_endpoint_still_returns_html_with_overrides_applied(client):
    """Regression: get_cv_html now calls apply_overrides internally — still returns HTML."""
    test_html = "<html><body>Patched CV</body></html>"
    with patch("applire.routers.cv.get_cv_html", new_callable=AsyncMock, return_value=test_html):
        response = client.get(f"/api/cv/{_CV_ID}/html")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Patched CV" in response.text


# ---------------------------------------------------------------------------
# Unit tests for build_content_snapshot
# ---------------------------------------------------------------------------


def test_build_content_snapshot_extracts_all_fields():
    from applire.services.cv_section_editor import build_content_snapshot
    from applire.schemas.cv import TailoredCVData, TailoredWorkEntry, TailoredContact

    tailored = TailoredCVData(
        contact=TailoredContact(name="Max"),
        summary="Experienced Python developer",
        work_history=[
            TailoredWorkEntry(
                company="ACME",
                role="Engineer",
                start_date="2020-01",
                end_date="2023-12",
                bullets=["Built APIs", "Led team"],
            )
        ],
        skills=["Python", "FastAPI"],
    )

    snapshot = build_content_snapshot(tailored)

    assert snapshot["introduction"] == "Experienced Python developer"
    assert snapshot["skills"] == ["Python", "FastAPI"]
    assert len(snapshot["positions"]) == 1
    pos = snapshot["positions"][0]
    assert pos["title"] == "Engineer"
    assert pos["company"] == "ACME"
    assert pos["bullets"] == ["Built APIs", "Led team"]
    assert pos["index"] == 0
    # ID is a valid UUID string
    uuid.UUID(pos["id"])  # raises ValueError if not valid UUID


def test_apply_overrides_replaces_introduction():
    from applire.services.cv_section_editor import apply_overrides_to_tailored
    from applire.schemas.cv import TailoredCVData, TailoredContact

    tailored = TailoredCVData(
        contact=TailoredContact(name="Max"),
        summary="Original summary",
        work_history=[],
        skills=[],
    )
    result = apply_overrides_to_tailored(
        tailored,
        content_snapshot=None,
        section_overrides={"introduction": "My new summary"},
    )
    assert result.summary == "My new summary"


def test_apply_overrides_replaces_skills():
    from applire.services.cv_section_editor import apply_overrides_to_tailored
    from applire.schemas.cv import TailoredCVData, TailoredContact

    tailored = TailoredCVData(
        contact=TailoredContact(name="Max"),
        summary="",
        work_history=[],
        skills=["Java"],
    )
    result = apply_overrides_to_tailored(
        tailored,
        content_snapshot=None,
        section_overrides={"skills": "Python\nFastAPI\nPostgreSQL"},
    )
    assert result.skills == ["Python", "FastAPI", "PostgreSQL"]


def test_apply_overrides_with_no_overrides_returns_unchanged():
    from applire.services.cv_section_editor import apply_overrides_to_tailored
    from applire.schemas.cv import TailoredCVData, TailoredContact

    tailored = TailoredCVData(
        contact=TailoredContact(name="Max"),
        summary="Original",
        work_history=[],
        skills=["Java"],
    )
    result = apply_overrides_to_tailored(tailored, None, None)
    assert result.summary == "Original"
    assert result is tailored  # exact same object — no copy made
```

- [ ] **Step 2: Run the unit tests**

```bash
cd backend && python -m pytest tests/unit/test_iter23_section_editor.py -v
```

Expected: all tests pass. If any test fails due to import order, check that `cv_section_editor.py` imports from `cv.py` only inside functions (lazy import) to avoid circular imports — this is already done in the service file above.

- [ ] **Step 3: Run the full unit test suite to check for regressions**

```bash
cd backend && python -m pytest tests/unit/ -v
```

Expected: all previously passing tests still pass.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/unit/test_iter23_section_editor.py backend/tests/unit/test_cv_gap_mapper.py
git commit -m "test(unit): add section editor and gap mapper unit tests (23.14)"
```

---

## Task 7: Fine-tune toggle on CVPreview

**Files:**
- Modify: `frontend/components/cv/CVPreview.tsx`

The toggle adds a "Fine-tune" button to the action bar. When active, it renders `<FineTunePanel>` instead of the standard single-column view.

- [ ] **Step 1: Add `fineTuneOpen` state and Fine-tune button to CVPreview**

At the top of the `CVPreview` function body, after the existing state declarations, add:

```tsx
const [fineTuneOpen, setFineTuneOpen] = useState(false);
```

In the `CVPreviewProps` interface, there's no change needed — `FineTunePanel` will receive `cvId` and `htmlContent` directly.

Replace the "PDF herunterladen" button and its siblings block with:

```tsx
<div className="flex flex-col gap-2 mt-auto">
  <button
    type="button"
    onClick={() => void handleDownload()}
    data-testid="download-button"
    className="w-full bg-success text-white font-semibold py-3 rounded-lg text-sm hover:opacity-90 transition-opacity"
  >
    PDF herunterladen
  </button>
  <button
    type="button"
    onClick={() => setFineTuneOpen((o) => !o)}
    data-testid="finetune-toggle"
    className={`w-full font-semibold py-2.5 rounded-lg text-sm transition-opacity hover:opacity-90 ${
      fineTuneOpen
        ? "bg-teal text-white"
        : "border border-teal text-teal"
    }`}
  >
    {fineTuneOpen ? "Fine-tune schließen" : "Fine-tune"}
  </button>
  {!fineTuneOpen && (
    <>
      <button
        type="button"
        onClick={onRegenerateSame}
        className="w-full border border-teal text-teal font-semibold py-2.5 rounded-lg text-sm hover:opacity-90 transition-opacity"
      >
        Neu generieren
      </button>
      <button
        type="button"
        onClick={onRegenerateDifferent}
        className="w-full border border-teal text-teal font-semibold py-2.5 rounded-lg text-sm hover:opacity-90 transition-opacity"
      >
        Andere Vorlage
      </button>
      <button
        type="button"
        onClick={onNext}
        className="w-full bg-teal text-white font-semibold py-3 rounded-lg text-sm hover:opacity-90 transition-colors"
      >
        Was nun? →
      </button>
    </>
  )}
</div>
```

Add the import for `FineTunePanel` at the top of the file (after the existing imports):

```tsx
import { FineTunePanel } from "./FineTunePanel";
```

Replace the outer container `<div className="flex flex-col md:flex-row gap-4 md:gap-6 animate-fade-in">` and its children with:

```tsx
<div className="flex flex-col md:flex-row gap-4 md:gap-6 animate-fade-in">
  {/* Left metadata panel */}
  <div className="w-full md:w-64 md:h-[75vh] flex flex-col gap-4 bg-neutral-light rounded-xl p-5 overflow-y-auto shrink-0">
    {/* ... all existing metadata content unchanged ... */}
    {/* action buttons block (updated above) */}
  </div>

  {fineTuneOpen ? (
    <FineTunePanel
      cvId={cvId}
      initialHtml={htmlContent}
      onClose={() => setFineTuneOpen(false)}
    />
  ) : (
    {/* existing preview panel — unchanged */}
  )}
</div>
```

The key structural change: when `fineTuneOpen`, the right panel shows `<FineTunePanel>` instead of the CV iframe directly. The Fine-tune panel internally hosts its own iframe.

- [ ] **Step 2: Commit**

```bash
git add frontend/components/cv/CVPreview.tsx
git commit -m "feat(frontend): add Fine-tune toggle to CVPreview (23.6)"
```

---

## Task 8: FineTunePanel — container and section list

**Files:**
- Create: `frontend/components/cv/FineTunePanel.tsx`

This implements tasks 23.7 and 23.8 together (the panel hosts the section list).

- [ ] **Step 1: Write FineTunePanel.tsx**

```tsx
// frontend/components/cv/FineTunePanel.tsx
"use client";

import { useState, useEffect } from "react";
import { SectionEditor } from "./SectionEditor";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

interface GapHintItem {
  id: string;
  label: string;
}

interface SectionItem {
  section_id: string;
  label: string;
  content: string;
  has_override: boolean;
  gaps: GapHintItem[];
}

interface CVSectionsResponse {
  sections: SectionItem[];
  general_gaps: GapHintItem[];
}

interface FineTunePanelProps {
  cvId: string;
  initialHtml: string | null;
  onClose: () => void;
}

export function FineTunePanel({ cvId, initialHtml, onClose }: FineTunePanelProps) {
  const [sections, setSections] = useState<SectionItem[]>([]);
  const [generalGaps, setGeneralGaps] = useState<GapHintItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [activeSection, setActiveSection] = useState<SectionItem | null>(null);
  const [htmlContent, setHtmlContent] = useState<string | null>(initialHtml);
  const [pendingSection, setPendingSection] = useState<SectionItem | null>(null);
  const [showDiscardDialog, setShowDiscardDialog] = useState(false);
  const [hasUnsaved, setHasUnsaved] = useState(false);

  useEffect(() => {
    loadSections();
  }, [cvId]);

  async function loadSections() {
    setLoading(true);
    setError(false);
    try {
      const res = await fetch(`${API_BASE}/api/cv/${cvId}/sections`);
      if (!res.ok) throw new Error("Failed");
      const data: CVSectionsResponse = await res.json();
      setSections(data.sections);
      setGeneralGaps(data.general_gaps);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  function requestSectionSwitch(section: SectionItem) {
    if (hasUnsaved) {
      setPendingSection(section);
      setShowDiscardDialog(true);
    } else {
      setActiveSection(section);
    }
  }

  function handleDiscard() {
    setShowDiscardDialog(false);
    setHasUnsaved(false);
    setActiveSection(pendingSection);
    setPendingSection(null);
  }

  function handleKeepEditing() {
    setShowDiscardDialog(false);
    setPendingSection(null);
  }

  function handleSaved(updatedHtml: string, savedContent: string) {
    setHtmlContent(updatedHtml);
    setHasUnsaved(false);
    // Update local section content so re-opening shows the saved state
    setSections((prev) =>
      prev.map((s) =>
        s.section_id === activeSection?.section_id
          ? { ...s, content: savedContent, has_override: true }
          : s
      )
    );
  }

  const allGapsClosed =
    sections.length > 0 && sections.every((s) => s.gaps.length === 0);

  return (
    <div className="flex-1 flex flex-row gap-4 h-[75vh]">
      {/* Unsaved changes dialog */}
      {showDiscardDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl p-6 shadow-xl max-w-sm w-full mx-4">
            <p className="text-sm font-semibold text-neutral-dark mb-4">
              Ungespeicherte Änderungen verwerfen?
            </p>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleDiscard}
                className="flex-1 bg-critical text-white font-semibold py-2 rounded-lg text-sm hover:opacity-90"
                data-testid="discard-confirm"
              >
                Verwerfen
              </button>
              <button
                type="button"
                onClick={handleKeepEditing}
                className="flex-1 border border-teal text-teal font-semibold py-2 rounded-lg text-sm hover:opacity-90"
                data-testid="keep-editing"
              >
                Weiter bearbeiten
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Left: editor panel (42%) */}
      <div className="w-[42%] flex flex-col bg-neutral-light rounded-xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
          <span className="text-sm font-bold text-neutral-dark">
            {allGapsClosed ? (
              <span className="text-success" data-testid="all-gaps-closed">
                ✓ Alle Lücken geschlossen
              </span>
            ) : (
              "Abschnitte bearbeiten"
            )}
          </span>
          <button
            type="button"
            onClick={onClose}
            className="text-xs text-gray-500 hover:text-gray-700"
          >
            Schließen ✕
          </button>
        </div>

        {/* Section list */}
        <div className="overflow-y-auto flex-1 p-2">
          {loading && (
            <div className="space-y-2 p-2">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-12 rounded-lg bg-gray-200 animate-pulse"
                  data-testid="section-skeleton"
                />
              ))}
            </div>
          )}

          {error && !loading && (
            <div className="p-4 text-center">
              <p className="text-sm text-gray-500 mb-2">Abschnitte konnten nicht geladen werden.</p>
              <button
                type="button"
                onClick={() => void loadSections()}
                className="text-sm text-teal underline hover:opacity-80"
              >
                Erneut versuchen
              </button>
            </div>
          )}

          {!loading && !error && sections.map((section) => (
            <button
              key={section.section_id}
              type="button"
              onClick={() => requestSectionSwitch(section)}
              data-testid="section-list-item"
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg mb-1 text-left transition-colors ${
                activeSection?.section_id === section.section_id
                  ? "bg-teal text-white"
                  : "hover:bg-gray-100 text-neutral-dark"
              }`}
            >
              <span className="text-sm font-medium truncate">{section.label}</span>
              <span className="ml-2 shrink-0">
                {section.gaps.length > 0 ? (
                  <span
                    data-testid="gap-badge"
                    className="bg-warning text-white text-xs font-bold px-1.5 py-0.5 rounded-full"
                  >
                    {section.gaps.length}
                  </span>
                ) : (
                  <span className="text-success text-xs">✓</span>
                )}
              </span>
            </button>
          ))}
        </div>

        {/* Section editor */}
        {activeSection && !loading && (
          <div className="border-t border-gray-200">
            <SectionEditor
              cvId={cvId}
              section={activeSection}
              onSaved={handleSaved}
              onUnsavedChange={setHasUnsaved}
            />
          </div>
        )}
      </div>

      {/* Right: CV preview iframe (58%) */}
      <div className="flex-1 bg-white rounded-xl shadow-soft overflow-hidden relative">
        {htmlContent ? (
          <iframe
            srcDoc={htmlContent}
            sandbox="allow-same-origin"
            title="Lebenslauf Vorschau"
            className="w-full h-full border-0"
            data-testid="finetune-preview-iframe"
          />
        ) : (
          <div className="w-full h-full animate-pulse bg-gray-100 rounded" />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/cv/FineTunePanel.tsx
git commit -m "feat(frontend): add FineTunePanel split-screen container with section list (23.7, 23.8)"
```

---

## Task 9: SectionEditor component

**Files:**
- Create: `frontend/components/cv/SectionEditor.tsx`
- Create: `frontend/components/cv/SaveScopePrompt.tsx`
- Create: `frontend/components/cv/GapHint.tsx`

These implement tasks 23.9, 23.10, 23.11, and 23.12.

- [ ] **Step 1: Write GapHint.tsx**

```tsx
// frontend/components/cv/GapHint.tsx
"use client";

interface GapHintItem {
  id: string;
  label: string;
}

interface GapHintProps {
  gap: GapHintItem;
  onDismiss: (gapId: string) => void;
}

export function GapHint({ gap, onDismiss }: GapHintProps) {
  return (
    <div className="flex items-center justify-between bg-warning-container border border-warning/30 rounded-lg px-3 py-2 mb-1">
      <span className="text-xs text-neutral-dark font-medium">{gap.label}</span>
      <div className="flex gap-1 ml-2 shrink-0">
        <button
          type="button"
          onClick={() => onDismiss(gap.id)}
          className="text-xs text-teal border border-teal px-2 py-0.5 rounded hover:bg-teal hover:text-white transition-colors"
          data-testid="write-myself-btn"
        >
          Selbst schreiben
        </button>
        <div className="relative group">
          <button
            type="button"
            disabled
            className="text-xs text-gray-400 border border-gray-300 px-2 py-0.5 rounded cursor-not-allowed"
            data-testid="kaile-help-btn"
          >
            Kaile hilft
          </button>
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-gray-800 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity">
            Kommt in Sprint 10
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Write SaveScopePrompt.tsx**

```tsx
// frontend/components/cv/SaveScopePrompt.tsx
"use client";

import { useState } from "react";

interface SaveScopePromptProps {
  onConfirm: (saveToProfile: boolean) => void;
  onCancel: () => void;
}

export function SaveScopePrompt({ onConfirm, onCancel }: SaveScopePromptProps) {
  const [remember, setRemember] = useState(false);

  function handleChoice(saveToProfile: boolean) {
    if (remember) {
      sessionStorage.setItem("finetune_save_scope", saveToProfile ? "profile" : "cv");
    }
    onConfirm(saveToProfile);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl p-6 shadow-xl max-w-sm w-full mx-4">
        <h3 className="text-sm font-bold text-neutral-dark mb-1">Wo soll die Änderung gespeichert werden?</h3>
        <p className="text-xs text-gray-500 mb-4">
          Im Masterprofil bleibt die Änderung dauerhaft erhalten. Nur für diesen Lebenslauf bleibt sie auf diesen Lebenslauf beschränkt.
        </p>
        <div className="flex flex-col gap-2 mb-4">
          <button
            type="button"
            onClick={() => handleChoice(true)}
            data-testid="save-to-profile-btn"
            className="w-full bg-teal text-white font-semibold py-2.5 rounded-lg text-sm hover:opacity-90"
          >
            Im Masterprofil speichern
          </button>
          <button
            type="button"
            onClick={() => handleChoice(false)}
            data-testid="save-cv-only-btn"
            className="w-full border border-teal text-teal font-semibold py-2.5 rounded-lg text-sm hover:opacity-90"
          >
            Nur für diesen Lebenslauf
          </button>
        </div>
        <label className="flex items-center gap-2 text-xs text-gray-500 cursor-pointer">
          <input
            type="checkbox"
            checked={remember}
            onChange={(e) => setRemember(e.target.checked)}
            data-testid="remember-choice-checkbox"
            className="rounded"
          />
          Meine Wahl für diese Sitzung merken
        </label>
        <button
          type="button"
          onClick={onCancel}
          className="mt-3 w-full text-xs text-gray-400 hover:text-gray-600"
        >
          Abbrechen
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Write SectionEditor.tsx**

```tsx
// frontend/components/cv/SectionEditor.tsx
"use client";

import { useState, useEffect } from "react";
import { GapHint } from "./GapHint";
import { SaveScopePrompt } from "./SaveScopePrompt";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

interface GapHintItem {
  id: string;
  label: string;
}

interface SectionItem {
  section_id: string;
  label: string;
  content: string;
  has_override: boolean;
  gaps: GapHintItem[];
}

interface SectionEditorProps {
  cvId: string;
  section: SectionItem;
  onSaved: (updatedHtml: string, savedContent: string) => void;
  onUnsavedChange: (hasUnsaved: boolean) => void;
}

export function SectionEditor({ cvId, section, onSaved, onUnsavedChange }: SectionEditorProps) {
  const [content, setContent] = useState(section.content);
  const [savedContent, setSavedContent] = useState(section.content);
  const [visibleGaps, setVisibleGaps] = useState<GapHintItem[]>(section.gaps);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [showPreviewStale, setShowPreviewStale] = useState(false);
  const [showScopePrompt, setShowScopePrompt] = useState(false);

  // Reset when section changes
  useEffect(() => {
    setContent(section.content);
    setSavedContent(section.content);
    setVisibleGaps(section.gaps);
    setSaveError(null);
    setShowPreviewStale(false);
    onUnsavedChange(false);
  }, [section.section_id]);

  function handleContentChange(value: string) {
    setContent(value);
    onUnsavedChange(value !== savedContent);
  }

  function handleCancel() {
    setContent(savedContent);
    setSaveError(null);
    onUnsavedChange(false);
  }

  function handleSaveClick() {
    // Check for a remembered session scope
    const remembered = sessionStorage.getItem("finetune_save_scope");
    if (remembered !== null) {
      void executeSave(remembered === "profile");
    } else {
      setShowScopePrompt(true);
    }
  }

  async function executeSave(saveToProfile: boolean) {
    setShowScopePrompt(false);
    setSaving(true);
    setSaveError(null);
    setShowPreviewStale(false);

    try {
      const res = await fetch(
        `${API_BASE}/api/cv/${cvId}/sections/${section.section_id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content, save_to_profile: saveToProfile }),
        }
      );

      if (!res.ok) {
        throw new Error(`Save failed: ${res.status}`);
      }

      const data: { html: string; overrides_applied: string[] } = await res.json();
      setSavedContent(content);
      onUnsavedChange(false);
      onSaved(data.html, content);
    } catch (err) {
      setSaveError("Speichern fehlgeschlagen. Bitte erneut versuchen.");
      setShowPreviewStale(true);
    } finally {
      setSaving(false);
    }
  }

  function handleDismissGap(gapId: string) {
    setVisibleGaps((prev) => prev.filter((g) => g.id !== gapId));
  }

  const hasUnsaved = content !== savedContent;

  return (
    <div className="p-3 flex flex-col gap-2">
      {showScopePrompt && (
        <SaveScopePrompt
          onConfirm={(saveToProfile) => void executeSave(saveToProfile)}
          onCancel={() => setShowScopePrompt(false)}
        />
      )}

      <p className="text-xs font-semibold text-neutral-dark">{section.label}</p>

      <textarea
        value={content}
        onChange={(e) => handleContentChange(e.target.value)}
        data-testid="section-textarea"
        className="w-full min-h-[180px] resize-y text-sm font-mono border border-gray-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-teal"
      />

      {saveError && (
        <p className="text-xs text-critical">{saveError}</p>
      )}

      {showPreviewStale && (
        <p className="text-xs text-warning">Vorschau könnte veraltet sein.</p>
      )}

      <div className="flex gap-2">
        <button
          type="button"
          onClick={handleSaveClick}
          disabled={saving || !hasUnsaved}
          data-testid="section-save"
          className="flex-1 bg-teal text-white font-semibold py-2 rounded-lg text-sm hover:opacity-90 disabled:opacity-40 transition-opacity"
        >
          {saving ? "Speichern…" : "Speichern"}
        </button>
        <button
          type="button"
          onClick={handleCancel}
          disabled={saving || !hasUnsaved}
          data-testid="section-cancel"
          className="flex-1 border border-gray-300 text-gray-600 font-semibold py-2 rounded-lg text-sm hover:opacity-90 disabled:opacity-40 transition-opacity"
        >
          Abbrechen
        </button>
      </div>

      {/* Gap hints */}
      {visibleGaps.length > 0 && (
        <div className="mt-1">
          <p className="text-xs text-gray-500 mb-1">Lücken in diesem Abschnitt:</p>
          {visibleGaps.map((gap) => (
            <GapHint key={gap.id} gap={gap} onDismiss={handleDismissGap} />
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/components/cv/SectionEditor.tsx frontend/components/cv/SaveScopePrompt.tsx frontend/components/cv/GapHint.tsx
git commit -m "feat(frontend): add SectionEditor, GapHint, SaveScopePrompt components (23.9–23.12)"
```

---

## Task 10: Unsaved changes guard on section switch

The unsaved changes guard is already wired in Task 8 (`FineTunePanel.tsx` checks `hasUnsaved` before switching sections). This task adds the "Exit Fine-tune" guard.

**Files:**
- Modify: `frontend/components/cv/FineTunePanel.tsx`

The `onClose` prop is called from the "Schließen" button. We need to intercept it when there are unsaved changes.

- [ ] **Step 1: Update the "Schließen" button in FineTunePanel to check for unsaved changes**

Replace the close button's `onClick`:

```tsx
<button
  type="button"
  onClick={() => {
    if (hasUnsaved) {
      setPendingSection(null);
      setShowDiscardDialog(true);
    } else {
      onClose();
    }
  }}
  className="text-xs text-gray-500 hover:text-gray-700"
>
  Schließen ✕
</button>
```

And update `handleDiscard` to also call `onClose` when `pendingSection` is null (meaning the user was trying to close):

```tsx
function handleDiscard() {
  setShowDiscardDialog(false);
  setHasUnsaved(false);
  if (pendingSection === null) {
    // User was trying to close the panel
    onClose();
  } else {
    setActiveSection(pendingSection);
    setPendingSection(null);
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/cv/FineTunePanel.tsx
git commit -m "feat(frontend): add unsaved changes guard on exit Fine-tune (23.13)"
```

---

## Task 11: Frontend unit tests

**Files:**
- Create: `frontend/components/cv/__tests__/FineTunePanel.test.tsx`
- Create: `frontend/components/cv/__tests__/SectionEditor.test.tsx`
- Create: `frontend/components/cv/__tests__/SaveScopePrompt.test.tsx`

- [ ] **Step 1: Write FineTunePanel.test.tsx**

```tsx
// frontend/components/cv/__tests__/FineTunePanel.test.tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { FineTunePanel } from "../FineTunePanel";

const MOCK_SECTIONS_RESPONSE = {
  sections: [
    {
      section_id: "introduction",
      label: "Introduction",
      content: "Original intro",
      has_override: false,
      gaps: [{ id: "Python", label: "Python" }],
    },
    {
      section_id: "skills",
      label: "Skills",
      content: "Java\nSQL",
      has_override: false,
      gaps: [],
    },
  ],
  general_gaps: [],
};

const BASE_PROPS = {
  cvId: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  initialHtml: "<html><body>CV</body></html>",
  onClose: vi.fn(),
};

describe("FineTunePanel", () => {
  beforeEach(() => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => MOCK_SECTIONS_RESPONSE,
    } as Response);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows loading skeleton while fetching sections", () => {
    vi.spyOn(globalThis, "fetch").mockReturnValue(new Promise(() => {}));
    render(<FineTunePanel {...BASE_PROPS} />);
    expect(document.querySelectorAll("[data-testid='section-skeleton']").length).toBeGreaterThan(0);
  });

  it("renders section list items after loading", async () => {
    render(<FineTunePanel {...BASE_PROPS} />);
    const items = await screen.findAllByTestId("section-list-item");
    expect(items).toHaveLength(2);
    expect(screen.getByText("Introduction")).toBeTruthy();
    expect(screen.getByText("Skills")).toBeTruthy();
  });

  it("shows gap badge with count for sections with gaps", async () => {
    render(<FineTunePanel {...BASE_PROPS} />);
    await screen.findAllByTestId("section-list-item");
    const badge = screen.getByTestId("gap-badge");
    expect(badge.textContent).toBe("1");
  });

  it("shows retry button on fetch error", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network error"));
    render(<FineTunePanel {...BASE_PROPS} />);
    await screen.findByText("Erneut versuchen");
  });

  it("shows 'all gaps closed' when all section gaps are empty", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        sections: [
          { section_id: "introduction", label: "Introduction", content: "text", has_override: false, gaps: [] },
        ],
        general_gaps: [],
      }),
    } as Response);
    render(<FineTunePanel {...BASE_PROPS} />);
    await screen.findByTestId("all-gaps-closed");
  });
});
```

- [ ] **Step 2: Write SectionEditor.test.tsx**

```tsx
// frontend/components/cv/__tests__/SectionEditor.test.tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { SectionEditor } from "../SectionEditor";

const MOCK_SECTION = {
  section_id: "introduction",
  label: "Introduction",
  content: "Original content",
  has_override: false,
  gaps: [{ id: "Python", label: "Python" }],
};

const BASE_PROPS = {
  cvId: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  section: MOCK_SECTION,
  onSaved: vi.fn(),
  onUnsavedChange: vi.fn(),
};

describe("SectionEditor", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    sessionStorage.clear();
  });

  it("pre-fills textarea with section content", () => {
    render(<SectionEditor {...BASE_PROPS} />);
    const textarea = screen.getByTestId("section-textarea") as HTMLTextAreaElement;
    expect(textarea.value).toBe("Original content");
  });

  it("disables Save and Cancel when content is unchanged", () => {
    render(<SectionEditor {...BASE_PROPS} />);
    expect((screen.getByTestId("section-save") as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByTestId("section-cancel") as HTMLButtonElement).disabled).toBe(true);
  });

  it("enables Save and Cancel when content changes", () => {
    render(<SectionEditor {...BASE_PROPS} />);
    fireEvent.change(screen.getByTestId("section-textarea"), { target: { value: "New content" } });
    expect((screen.getByTestId("section-save") as HTMLButtonElement).disabled).toBe(false);
    expect((screen.getByTestId("section-cancel") as HTMLButtonElement).disabled).toBe(false);
  });

  it("Cancel reverts textarea to original content", () => {
    render(<SectionEditor {...BASE_PROPS} />);
    fireEvent.change(screen.getByTestId("section-textarea"), { target: { value: "New content" } });
    fireEvent.click(screen.getByTestId("section-cancel"));
    const textarea = screen.getByTestId("section-textarea") as HTMLTextAreaElement;
    expect(textarea.value).toBe("Original content");
  });

  it("Save shows scope prompt when no remembered choice", () => {
    render(<SectionEditor {...BASE_PROPS} />);
    fireEvent.change(screen.getByTestId("section-textarea"), { target: { value: "New content" } });
    fireEvent.click(screen.getByTestId("section-save"));
    expect(screen.getByTestId("save-cv-only-btn")).toBeTruthy();
    expect(screen.getByTestId("save-to-profile-btn")).toBeTruthy();
  });

  it("Save calls PATCH with correct payload on scope selection", async () => {
    const mockFetch = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ html: "<html>updated</html>", overrides_applied: ["introduction"] }),
    } as Response);

    render(<SectionEditor {...BASE_PROPS} />);
    fireEvent.change(screen.getByTestId("section-textarea"), { target: { value: "New content" } });
    fireEvent.click(screen.getByTestId("section-save"));
    fireEvent.click(screen.getByTestId("save-cv-only-btn"));

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/sections/introduction"),
        expect.objectContaining({
          method: "PATCH",
          body: JSON.stringify({ content: "New content", save_to_profile: false }),
        })
      );
    });
  });

  it("shows error message when PATCH fails", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network error"));
    sessionStorage.setItem("finetune_save_scope", "cv");

    render(<SectionEditor {...BASE_PROPS} />);
    fireEvent.change(screen.getByTestId("section-textarea"), { target: { value: "New content" } });
    fireEvent.click(screen.getByTestId("section-save"));

    await screen.findByText("Speichern fehlgeschlagen. Bitte erneut versuchen.");
  });

  it("renders gap hints", () => {
    render(<SectionEditor {...BASE_PROPS} />);
    expect(screen.getByText("Python")).toBeTruthy();
    expect(screen.getByTestId("write-myself-btn")).toBeTruthy();
    expect(screen.getByTestId("kaile-help-btn")).toBeTruthy();
  });

  it("'Let Kaile help' button is disabled", () => {
    render(<SectionEditor {...BASE_PROPS} />);
    expect((screen.getByTestId("kaile-help-btn") as HTMLButtonElement).disabled).toBe(true);
  });

  it("dismissing a gap removes it from the list", () => {
    render(<SectionEditor {...BASE_PROPS} />);
    fireEvent.click(screen.getByTestId("write-myself-btn"));
    expect(screen.queryByText("Python")).toBeNull();
  });
});
```

- [ ] **Step 3: Write SaveScopePrompt.test.tsx**

```tsx
// frontend/components/cv/__tests__/SaveScopePrompt.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { SaveScopePrompt } from "../SaveScopePrompt";

describe("SaveScopePrompt", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("renders both save options", () => {
    render(<SaveScopePrompt onConfirm={vi.fn()} onCancel={vi.fn()} />);
    expect(screen.getByTestId("save-to-profile-btn")).toBeTruthy();
    expect(screen.getByTestId("save-cv-only-btn")).toBeTruthy();
  });

  it("'Im Masterprofil speichern' calls onConfirm with true", () => {
    const onConfirm = vi.fn();
    render(<SaveScopePrompt onConfirm={onConfirm} onCancel={vi.fn()} />);
    fireEvent.click(screen.getByTestId("save-to-profile-btn"));
    expect(onConfirm).toHaveBeenCalledWith(true);
  });

  it("'Nur für diesen Lebenslauf' calls onConfirm with false", () => {
    const onConfirm = vi.fn();
    render(<SaveScopePrompt onConfirm={onConfirm} onCancel={vi.fn()} />);
    fireEvent.click(screen.getByTestId("save-cv-only-btn"));
    expect(onConfirm).toHaveBeenCalledWith(false);
  });

  it("when remember-choice is checked, saves scope to sessionStorage", () => {
    render(<SaveScopePrompt onConfirm={vi.fn()} onCancel={vi.fn()} />);
    fireEvent.click(screen.getByTestId("remember-choice-checkbox"));
    fireEvent.click(screen.getByTestId("save-cv-only-btn"));
    expect(sessionStorage.getItem("finetune_save_scope")).toBe("cv");
  });

  it("when remember-choice is checked and profile selected, stores 'profile'", () => {
    render(<SaveScopePrompt onConfirm={vi.fn()} onCancel={vi.fn()} />);
    fireEvent.click(screen.getByTestId("remember-choice-checkbox"));
    fireEvent.click(screen.getByTestId("save-to-profile-btn"));
    expect(sessionStorage.getItem("finetune_save_scope")).toBe("profile");
  });

  it("Cancel calls onCancel", () => {
    const onCancel = vi.fn();
    render(<SaveScopePrompt onConfirm={vi.fn()} onCancel={onCancel} />);
    fireEvent.click(screen.getByRole("button", { name: "Abbrechen" }));
    expect(onCancel).toHaveBeenCalledOnce();
  });
});
```

- [ ] **Step 4: Run all frontend unit tests**

```bash
cd frontend && npx vitest run components/cv/__tests__/
```

Expected: all tests pass. If a test fails due to missing `sessionStorage` in the test environment, check that Vitest is configured with `environment: 'jsdom'` in `vitest.config.ts`.

- [ ] **Step 5: Commit**

```bash
git add frontend/components/cv/__tests__/FineTunePanel.test.tsx frontend/components/cv/__tests__/SectionEditor.test.tsx frontend/components/cv/__tests__/SaveScopePrompt.test.tsx
git commit -m "test(frontend): add unit tests for FineTunePanel, SectionEditor, SaveScopePrompt (23.15)"
```

---

## Task 12: E2E test (Playwright)

**Files:**
- Create: `frontend/e2e/finetuner-sprint9.spec.ts`

This test requires a running stack (backend + frontend + DB with a CV already generated). Check the existing Playwright config for how other E2E tests are set up.

- [ ] **Step 1: Check the existing E2E test structure**

```bash
ls frontend/e2e/ 2>/dev/null || ls frontend/tests/ 2>/dev/null || find frontend -name "*.spec.ts" -not -path "*/node_modules/*"
```

Note the base URL and how other specs navigate — match that pattern.

- [ ] **Step 2: Write the E2E spec**

```typescript
// frontend/e2e/finetuner-sprint9.spec.ts
import { test, expect } from "@playwright/test";

// Adjust this to match how your E2E tests create/navigate to a CV.
// The test assumes a CV has been generated and is accessible at /flow/{flowId}/cv
// with a known CV ID. If your E2E fixtures work differently, adapt accordingly.

test.describe("Finetuner — Sprint 9", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to a CV preview page. Replace with your actual E2E navigation/fixture.
    // If you have a helper like `createFlowWithCV()`, use that here.
    await page.goto("/flow/test-flow-id/cv");
    // Wait for the CV iframe to be visible (CV is ready)
    await page.waitForSelector('[data-testid="cv-iframe"]', { timeout: 30_000 });
  });

  test("(23.6) clicking Fine-tune opens the panel", async ({ page }) => {
    await page.click('[data-testid="finetune-toggle"]');
    await expect(page.locator('[data-testid="section-list-item"]').first()).toBeVisible({ timeout: 10_000 });
  });

  test("(23.7, 23.8) section list shows gap badges", async ({ page }) => {
    await page.click('[data-testid="finetune-toggle"]');
    // At least one section should be visible
    await expect(page.locator('[data-testid="section-list-item"]').first()).toBeVisible({ timeout: 10_000 });
  });

  test("(23.9) clicking a section opens the textarea with content", async ({ page }) => {
    await page.click('[data-testid="finetune-toggle"]');
    await page.locator('[data-testid="section-list-item"]').first().click();
    const textarea = page.locator('[data-testid="section-textarea"]');
    await expect(textarea).toBeVisible({ timeout: 5_000 });
    const value = await textarea.inputValue();
    expect(value.length).toBeGreaterThan(0);
  });

  test("(23.9, 23.10, 23.12) editing, saving, and preview update", async ({ page }) => {
    await page.click('[data-testid="finetune-toggle"]');

    // Click Introduction section
    const introItem = page.locator('[data-testid="section-list-item"]', { hasText: "Introduction" });
    await introItem.click();

    const textarea = page.locator('[data-testid="section-textarea"]');
    await expect(textarea).toBeVisible({ timeout: 5_000 });

    // Edit the text
    await textarea.fill("My edited introduction text for E2E test");
    await expect(page.locator('[data-testid="section-save"]')).toBeEnabled();

    // Click Save — scope prompt should appear
    await page.click('[data-testid="section-save"]');
    await expect(page.locator('[data-testid="save-cv-only-btn"]')).toBeVisible({ timeout: 3_000 });

    // Choose "Just this CV"
    await page.click('[data-testid="save-cv-only-btn"]');

    // Preview iframe should update (no longer shows the old HTML)
    await expect(page.locator('[data-testid="finetune-preview-iframe"]')).toBeVisible({ timeout: 5_000 });
  });

  test("(23.13) switching sections with unsaved changes shows guard", async ({ page }) => {
    await page.click('[data-testid="finetune-toggle"]');

    const items = page.locator('[data-testid="section-list-item"]');
    await expect(items.first()).toBeVisible({ timeout: 10_000 });

    // Click first section
    await items.first().click();
    const textarea = page.locator('[data-testid="section-textarea"]');
    await expect(textarea).toBeVisible({ timeout: 5_000 });

    // Make an edit without saving
    await textarea.fill("Unsaved edit");

    // Click second section
    await items.nth(1).click();

    // Discard dialog should appear
    await expect(page.locator('[data-testid="discard-confirm"]')).toBeVisible({ timeout: 3_000 });
  });
});
```

- [ ] **Step 3: Commit**

```bash
git add frontend/e2e/finetuner-sprint9.spec.ts
git commit -m "test(e2e): add Finetuner Sprint 9 Playwright spec (23.16)"
```

---

## Self-review notes

**Spec coverage check:**

| Sprint 9 task | Covered in plan |
|---|---|
| 23.1 Alembic migration | Task 1 |
| 23.2 Populate content_snapshot | Task 4, Step 3 |
| 23.3 GET /sections | Task 4 (service) + Task 5 (route) |
| 23.4 PATCH /sections/{id} | Task 4 (service) + Task 5 (route) |
| 23.5 Update GET /html | Task 4, Step 2 |
| 23.6 Fine-tune toggle | Task 7 |
| 23.7 FineTunePanel container | Task 8 |
| 23.8 Section list with gap badges | Task 8 |
| 23.9 SectionEditor | Task 9, Step 3 |
| 23.10 Live preview refresh | Task 9, Step 3 (`onSaved` callback) |
| 23.11 Gap hints (GapHint.tsx, "Let Kaile help" disabled) | Task 9, Steps 1 + 3 |
| 23.12 SaveScopePrompt | Task 9, Step 2 |
| 23.13 Unsaved changes guard | Task 10 |
| 23.14 Backend unit tests | Task 6 |
| 23.15 Frontend unit tests | Task 11 |
| 23.16 E2E test | Task 12 |

**Type consistency:**
- `SectionItem` interface defined consistently in `FineTunePanel.tsx` and `SectionEditor.tsx` (both inline — acceptable for co-located components; extract to a shared types file in Sprint 10 if needed)
- `apply_overrides_to_tailored` return value: returns `TailoredCVData` (same type as input), used correctly in both `get_cv_html` and `patch_cv_section`
- `patch_cv_section` imports `_jinja_env` and `_TEMPLATE_FILES` from `services/cv.py` — these are module-level constants, no issue
- `_load_cv` defined in `cv_section_editor.py` (not `cv.py`) to avoid circular imports — consistent with its usage

**Potential issue flagged:** The E2E test in Task 12 uses `test-flow-id` as a placeholder. The engineer must adapt the `beforeEach` to match the actual E2E fixture pattern. Check existing E2E test files for the correct navigation helper.
