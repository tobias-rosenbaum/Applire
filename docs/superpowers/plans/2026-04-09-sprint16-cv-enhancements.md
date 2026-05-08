# Sprint 16 — CV Template Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an extensible icon set registry and a page-break avoidance toggle to the CV generation pipeline, persisted on the `generated_cvs` table and rendered via both Jinja2 templates.

**Architecture:** A new `icon_sets.py` module holds all SVG icon sets as Python dicts keyed by set name; `resolve_icon_set()` picks the right set at render time. Both new features (`icon_set`, `avoid_page_breaks`) are added to the Pydantic request schema, persisted as DB columns, passed through the service layer, and consumed by the Jinja2 templates.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy (async), Alembic, Jinja2, Playwright/Chromium, pytest

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| **Create** | `backend/applire/icon_sets.py` | Icon set registry — `ICON_SETS`, `TEMPLATE_DEFAULT_ICON_SET`, `resolve_icon_set` |
| **Modify** | `backend/applire/schemas/cv.py` | Add `CVIconSet`, update `CVGenerateRequest` |
| **Modify** | `backend/applire/models/cv.py` | Add `icon_set` and `avoid_page_breaks` columns to `GeneratedCV` |
| **Create** | `backend/alembic/versions/0020_icon_set_and_page_breaks.py` | DB migration — two new columns on `generated_cvs` |
| **Modify** | `backend/applire/services/cv.py` | Pass new fields to DB record; resolve icons and page-break flag at render |
| **Modify** | `backend/applire/routers/cv.py` | Forward `icon_set` and `avoid_page_breaks` from request body |
| **Modify** | `backend/applire/templates/lebenslauf.html.j2` | `.no-breaks` CSS class gate + `{{ icons.* \| safe }}` in contact and sections |
| **Modify** | `backend/applire/templates/modern_swiss.html.j2` | Same as above |
| **Create** | `tests/unit/test_sprint16_cv_enhancements.py` | Unit tests for all new behaviour |

---

## Task 1: Icon Set Registry

**Files:**
- Create: `backend/applire/icon_sets.py`
- Test: `tests/unit/test_sprint16_cv_enhancements.py`

- [ ] **Step 1.1: Write the failing tests**

Create `tests/unit/test_sprint16_cv_enhancements.py`:

```python
"""Sprint 16 — CV template enhancements: icon sets + page break toggle.

Run:
    PYTHONPATH=backend pytest tests/unit/test_sprint16_cv_enhancements.py -v
"""
import re
import uuid
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Task 1 — Icon set registry
# ---------------------------------------------------------------------------

def test_resolve_icon_set_modern_swiss_default_returns_outline():
    """modern_swiss with no explicit choice → outline set (non-empty SVGs)."""
    from applire.icon_sets import resolve_icon_set

    icons = resolve_icon_set("modern_swiss", None)
    assert icons["phone"] != ""


def test_resolve_icon_set_classic_german_default_returns_none_set():
    """classic_german with no explicit choice → none set (all empty strings)."""
    from applire.icon_sets import resolve_icon_set

    icons = resolve_icon_set("classic_german", None)
    assert all(v == "" for v in icons.values())


def test_resolve_icon_set_explicit_override_trumps_template_default():
    """Explicit icon_set="filled" overrides the classic_german default of "none"."""
    from applire.icon_sets import resolve_icon_set

    icons = resolve_icon_set("classic_german", "filled")
    assert icons["phone"] != ""


def test_resolve_icon_set_unknown_template_falls_back_to_none():
    """Unknown template name → none set (graceful degradation)."""
    from applire.icon_sets import resolve_icon_set

    icons = resolve_icon_set("unknown_future_template", None)
    assert all(v == "" for v in icons.values())


def test_resolve_icon_set_unknown_set_name_falls_back_to_none():
    """Unknown icon_set name → none set (graceful degradation)."""
    from applire.icon_sets import resolve_icon_set

    icons = resolve_icon_set("modern_swiss", "not_a_real_set")
    assert all(v == "" for v in icons.values())


def test_all_non_none_svgs_use_currentcolor_not_hex():
    """All SVGs in outline/filled sets use currentColor — no hardcoded hex colours."""
    from applire.icon_sets import ICON_SETS

    hex_pattern = re.compile(r'#[0-9a-fA-F]{3,6}')
    for set_name, icons in ICON_SETS.items():
        if set_name == "none":
            continue
        for key, svg in icons.items():
            assert "currentColor" in svg, (
                f"ICON_SETS['{set_name}']['{key}'] is missing currentColor"
            )
            assert not hex_pattern.search(svg), (
                f"ICON_SETS['{set_name}']['{key}'] contains a hardcoded hex colour"
            )


def test_none_set_all_empty_strings():
    """The 'none' icon set has empty strings for every key (no SVG rendered)."""
    from applire.icon_sets import ICON_SETS

    for key, val in ICON_SETS["none"].items():
        assert val == "", f"ICON_SETS['none']['{key}'] should be empty string"
```

- [ ] **Step 1.2: Run to verify they fail**

```bash
cd /home/apliqa/Documents/Applire/Solution
PYTHONPATH=backend pytest tests/unit/test_sprint16_cv_enhancements.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'applire.icon_sets'`

- [ ] **Step 1.3: Create the icon set registry**

Create `backend/applire/icon_sets.py`:

```python
"""CV icon set registry.

Defines selectable icon sets for Jinja2 CV templates. All SVGs use
stroke="currentColor" or fill="currentColor" so they inherit the
template's CSS accent colour — future colour scheme changes are free.

Adding a new icon set: add one entry to ICON_SETS and (optionally)
declare a per-template default in TEMPLATE_DEFAULT_ICON_SET.
"""

ICON_KEYS = (
    "phone", "email", "location", "linkedin",
    "profile", "experience", "education", "skills", "languages",
)

_SVG_OUTLINE: dict[str, str] = {
    "phone": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
        ' stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07'
        "A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.62 3.59 2 2 0 0 1 3.59 1.41h3"
        "a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91"
        'a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7'
        'A2 2 0 0 1 22 16.92z"/></svg>'
    ),
    "email": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
        ' stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>'
        '<polyline points="22,6 12,13 2,6"/></svg>'
    ),
    "location": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
        ' stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>'
        '<circle cx="12" cy="10" r="3"/></svg>'
    ),
    "linkedin": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
        ' stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7'
        'a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/>'
        '<circle cx="4" cy="4" r="2"/></svg>'
    ),
    "profile": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
        ' stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
        '<circle cx="12" cy="7" r="4"/></svg>'
    ),
    "experience": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
        ' stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>'
        '<path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>'
    ),
    "education": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
        ' stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<path d="M22 10v6M2 10l10-5 10 5-10 5z"/>'
        '<path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>'
    ),
    "skills": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
        ' stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<polyline points="16 18 22 12 16 6"/>'
        '<polyline points="8 6 2 12 8 18"/></svg>'
    ),
    "languages": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
        ' stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>'
        '<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10'
        ' 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'
    ),
}

_SVG_FILLED: dict[str, str] = {
    "phone": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="currentColor" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24'
        " 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17"
        ' 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>'
    ),
    "email": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="currentColor" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2z'
        'm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>'
    ),
    "location": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="currentColor" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z'
        'm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>'
    ),
    "linkedin": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="currentColor" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14'
        "m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.32 1.3v-1.11h-2.79v8.37h2.79"
        "v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.79M6.88 8.56a1.68 1.68 0 0 0"
        " 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68"
        'm1.39 9.94v-8.37H5.5v8.37h2.77z"/></svg>'
    ),
    "profile": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="currentColor" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4z'
        'm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>'
    ),
    "experience": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="currentColor" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<path d="M20 6h-4V4c0-1.11-.89-2-2-2h-4c-1.11 0-2 .89-2 2v2H4c-1.11 0-1.99.89-1.99 2'
        'L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-6 0h-4V4h4v2z"/></svg>'
    ),
    "education": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="currentColor" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<path d="M5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82zM12 3L1 9l11 6 9-4.91V17h2V9L12 3z"/></svg>'
    ),
    "skills": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="currentColor" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<path d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6'
        '-6 6-1.4-1.4z"/></svg>'
    ),
    "languages": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"'
        ' fill="currentColor" style="display:inline-block;vertical-align:middle;margin-right:3pt">'
        '<path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2'
        " 11.99 2zm6.93 6h-2.95c-.32-1.25-.78-2.45-1.38-3.56 1.84.63 3.37 1.91 4.33 3.56zM12"
        " 4.04c.83 1.2 1.48 2.53 1.91 3.96h-3.82c.43-1.43 1.08-2.76 1.91-3.96zM4.26 14C4.1"
        " 13.36 4 12.69 4 12s.1-1.36.26-2h3.38c-.08.66-.14 1.32-.14 2 0 .68.06 1.34.14 2H4.26z"
        "m.82 2h2.95c.32 1.25.78 2.45 1.38 3.56-1.84-.63-3.37-1.9-4.33-3.56zm2.95-8H5.08"
        "c.96-1.66 2.49-2.93 4.33-3.56C8.81 5.55 8.35 6.75 8.03 8zM12 19.96c-.83-1.2-1.48-2.53"
        "-1.91-3.96h3.82c-.43 1.43-1.08 2.76-1.91 3.96zM14.34 14H9.66c-.09-.66-.16-1.32-.16-2"
        " 0-.68.07-1.35.16-2h4.68c.09.65.16 1.32.16 2 0 .68-.07 1.34-.16 2zm.25 5.56"
        "c.6-1.11 1.06-2.31 1.38-3.56h2.95c-.96 1.65-2.49 2.93-4.33 3.56zM16.36 14"
        "c.08-.66.14-1.32.14-2 0-.68-.06-1.34-.14-2h3.38c.16.64.26 1.31.26 2s-.1 1.36-.26 2h-3.38z"
        '"/></svg>'
    ),
}

ICON_SETS: dict[str, dict[str, str]] = {
    "none":    {key: "" for key in ICON_KEYS},
    "outline": _SVG_OUTLINE,
    "filled":  _SVG_FILLED,
}

# Per-template defaults — new templates declare their default here.
TEMPLATE_DEFAULT_ICON_SET: dict[str, str] = {
    "classic_german": "none",
    "modern_swiss":   "outline",
}


def resolve_icon_set(template: str, icon_set: str | None) -> dict[str, str]:
    """Return the icon dict for the chosen set, falling back to the template default.

    Args:
        template:  The CV template name (e.g. "modern_swiss").
        icon_set:  Explicit override, or None to use the template default.

    Returns:
        Dict mapping icon key → SVG HTML string (empty string for the "none" set).
    """
    chosen = icon_set or TEMPLATE_DEFAULT_ICON_SET.get(template, "none")
    return ICON_SETS.get(chosen, ICON_SETS["none"])
```

- [ ] **Step 1.4: Run tests — should pass**

```bash
cd /home/apliqa/Documents/Applire/Solution
PYTHONPATH=backend pytest tests/unit/test_sprint16_cv_enhancements.py -v
```

Expected: all 7 tests pass.

- [ ] **Step 1.5: Commit**

```bash
git add backend/applire/icon_sets.py tests/unit/test_sprint16_cv_enhancements.py
git commit -m "feat(cv): add icon set registry with outline and filled SVG sets"
```

---

## Task 2: Schema — CVIconSet + Updated CVGenerateRequest

**Files:**
- Modify: `backend/applire/schemas/cv.py`
- Test: `tests/unit/test_sprint16_cv_enhancements.py` (append)

- [ ] **Step 2.1: Append schema tests to the test file**

Append to `tests/unit/test_sprint16_cv_enhancements.py`:

```python
# ---------------------------------------------------------------------------
# Task 2 — Schema changes
# ---------------------------------------------------------------------------

def test_cv_generate_request_accepts_icon_set_and_avoid_page_breaks():
    """CVGenerateRequest accepts the two new optional fields."""
    from applire.schemas.cv import CVGenerateRequest

    req = CVGenerateRequest(
        job_id=uuid.uuid4(),
        icon_set="outline",
        avoid_page_breaks=False,
    )
    assert req.icon_set == "outline"
    assert req.avoid_page_breaks is False


def test_cv_generate_request_defaults():
    """icon_set defaults to None (template default); avoid_page_breaks defaults to True."""
    from applire.schemas.cv import CVGenerateRequest

    req = CVGenerateRequest(job_id=uuid.uuid4())
    assert req.icon_set is None
    assert req.avoid_page_breaks is True


def test_cv_generate_request_rejects_invalid_icon_set():
    """icon_set only accepts 'none', 'outline', 'filled', or None."""
    import pydantic
    from applire.schemas.cv import CVGenerateRequest

    with pytest.raises(pydantic.ValidationError):
        CVGenerateRequest(job_id=uuid.uuid4(), icon_set="sparkles")
```

- [ ] **Step 2.2: Run to verify they fail**

```bash
PYTHONPATH=backend pytest tests/unit/test_sprint16_cv_enhancements.py::test_cv_generate_request_accepts_icon_set_and_avoid_page_breaks -v
```

Expected: FAIL — `CVGenerateRequest` does not accept `icon_set`.

- [ ] **Step 2.3: Update `backend/applire/schemas/cv.py`**

Replace the top of the file (after the imports) with the updated schema. The full new content of `backend/applire/schemas/cv.py`:

```python
import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

from applire.models.cv import CVGenerationStatus

CVTemplate = Literal["classic_german", "modern_swiss"]
CVIconSet = Literal["none", "outline", "filled"]


class CVGenerateRequest(BaseModel):
    job_id: uuid.UUID
    template: CVTemplate = "classic_german"
    icon_set: CVIconSet | None = None        # None = use template default
    avoid_page_breaks: bool = True


class CVGenerateResponse(BaseModel):
    """Returned immediately by POST /api/cv/generate (async path)."""
    cv_id: uuid.UUID
    status: CVGenerationStatus
    html_url: str  # stable URL — usable once status='ready'
    pdf_url: str
    expires_at: datetime


class CVStatusResponse(BaseModel):
    """Returned by GET /api/cv/{cv_id}/status."""
    cv_id: uuid.UUID
    status: CVGenerationStatus
    html_url: Optional[str] = None
    pdf_url: Optional[str] = None
    error_message: Optional[str] = None
    expires_at: datetime

    model_config = {"from_attributes": True}


class TailoredWorkEntry(BaseModel):
    company: str
    role: str
    start_date: str
    end_date: str | None = None
    bullets: list[str] = []


class TailoredEducationEntry(BaseModel):
    institution: str
    degree: str
    field: str = ""
    start_date: str = ""
    end_date: str | None = None


class TailoredLanguage(BaseModel):
    language: str
    level: str


class TailoredContact(BaseModel):
    name: str = ""
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    photo_url: str | None = None  # ADR-021; file path resolved to base64 URI at render time


class TailoredCVData(BaseModel):
    contact: TailoredContact
    summary: str = ""
    work_history: list[TailoredWorkEntry] = []
    skills: list[str] = []
    education: list[TailoredEducationEntry] = []
    languages: list[TailoredLanguage] = []
    show_photo: bool = True  # country-aware photo rendering hook (ADR-021); True for all DACH jobs


class GeneratedCVResponse(BaseModel):
    id: uuid.UUID
    job_analysis_id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2.4: Run tests — should pass**

```bash
PYTHONPATH=backend pytest tests/unit/test_sprint16_cv_enhancements.py -v -k "schema or request or default or invalid"
```

Expected: 3 new tests pass.

- [ ] **Step 2.5: Commit**

```bash
git add backend/applire/schemas/cv.py tests/unit/test_sprint16_cv_enhancements.py
git commit -m "feat(cv): add CVIconSet type and icon_set/avoid_page_breaks to CVGenerateRequest"
```

---

## Task 3: DB Model + Migration

**Files:**
- Modify: `backend/applire/models/cv.py`
- Create: `backend/alembic/versions/0020_icon_set_and_page_breaks.py`
- Test: `tests/unit/test_sprint16_cv_enhancements.py` (append)

- [ ] **Step 3.1: Append model tests**

Append to `tests/unit/test_sprint16_cv_enhancements.py`:

```python
# ---------------------------------------------------------------------------
# Task 3 — DB model columns
# ---------------------------------------------------------------------------

def test_generated_cv_model_has_icon_set_column():
    """GeneratedCV ORM model declares the icon_set column."""
    from applire.models.cv import GeneratedCV
    assert hasattr(GeneratedCV, "icon_set")


def test_generated_cv_model_has_avoid_page_breaks_column():
    """GeneratedCV ORM model declares the avoid_page_breaks column."""
    from applire.models.cv import GeneratedCV
    assert hasattr(GeneratedCV, "avoid_page_breaks")


def test_generated_cv_avoid_page_breaks_defaults_true():
    """avoid_page_breaks defaults to True on new GeneratedCV instances."""
    from applire.models.cv import GeneratedCV
    record = GeneratedCV()
    assert record.avoid_page_breaks is True
```

- [ ] **Step 3.2: Run to verify they fail**

```bash
PYTHONPATH=backend pytest tests/unit/test_sprint16_cv_enhancements.py -v -k "model_has"
```

Expected: FAIL — attribute not found.

- [ ] **Step 3.3: Add columns to `backend/applire/models/cv.py`**

Add two new mapped columns after the `section_overrides` column (line ~47). The updated `GeneratedCV` class body (show only the new lines in context):

```python
    content_snapshot: Mapped[dict | None] = mapped_column(_JSON, nullable=True)
    section_overrides: Mapped[dict | None] = mapped_column(_JSON, nullable=True)
    icon_set: Mapped[str | None] = mapped_column(String(32), nullable=True)
    avoid_page_breaks: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
```

- [ ] **Step 3.4: Run model tests — should pass**

```bash
PYTHONPATH=backend pytest tests/unit/test_sprint16_cv_enhancements.py -v -k "model_has or defaults_true"
```

Expected: 3 tests pass.

- [ ] **Step 3.5: Create the Alembic migration**

Create `backend/alembic/versions/0020_icon_set_and_page_breaks.py`:

```python
"""Add icon_set and avoid_page_breaks to generated_cvs

Revision ID: 0020
Revises: 0019
Create Date: 2026-04-09
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "generated_cvs",
        sa.Column("icon_set", sa.String(32), nullable=True),
    )
    op.add_column(
        "generated_cvs",
        sa.Column(
            "avoid_page_breaks",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )


def downgrade() -> None:
    op.drop_column("generated_cvs", "avoid_page_breaks")
    op.drop_column("generated_cvs", "icon_set")
```

- [ ] **Step 3.6: Run all tests so far**

```bash
PYTHONPATH=backend pytest tests/unit/test_sprint16_cv_enhancements.py -v
```

Expected: all tests pass (no new failures from previous tasks).

- [ ] **Step 3.7: Commit**

```bash
git add backend/applire/models/cv.py backend/alembic/versions/0020_icon_set_and_page_breaks.py tests/unit/test_sprint16_cv_enhancements.py
git commit -m "feat(cv): add icon_set and avoid_page_breaks columns to generated_cvs"
```

---

## Task 4: CV Service Wiring

**Files:**
- Modify: `backend/applire/services/cv.py`
- Test: `tests/unit/test_sprint16_cv_enhancements.py` (append)

- [ ] **Step 4.1: Append service tests**

Append to `tests/unit/test_sprint16_cv_enhancements.py`:

```python
# ---------------------------------------------------------------------------
# Task 4 — Template rendering (direct Jinja2 tests, no DB)
# ---------------------------------------------------------------------------

def _make_jinja_env():
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    templates_dir = (
        Path(__file__).parent.parent.parent / "backend" / "applire" / "templates"
    )
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html"]),
    )


def _make_cv():
    from applire.schemas.cv import TailoredCVData, TailoredContact, TailoredWorkEntry, TailoredLanguage
    return TailoredCVData(
        contact=TailoredContact(
            name="Anna Müller",
            phone="+49 89 123",
            email="anna@example.com",
            location="München",
            linkedin="linkedin.com/in/anna",
        ),
        summary="Erfahrene Entwicklerin.",
        work_history=[TailoredWorkEntry(company="Acme", role="Developer", start_date="2021")],
        languages=[TailoredLanguage(language="Deutsch", level="Muttersprache")],
    )


def test_modern_swiss_with_outline_renders_svg_icons():
    """modern_swiss + outline icon set → SVG tags present in rendered HTML."""
    from applire.icon_sets import resolve_icon_set

    env = _make_jinja_env()
    template = env.get_template("modern_swiss.html.j2")
    icons = resolve_icon_set("modern_swiss", "outline")
    html = template.render(cv=_make_cv(), icons=icons, avoid_page_breaks=True)

    assert "<svg" in html


def test_modern_swiss_with_none_set_renders_no_svg_icons():
    """modern_swiss + none icon set → no SVG tags."""
    from applire.icon_sets import resolve_icon_set

    env = _make_jinja_env()
    template = env.get_template("modern_swiss.html.j2")
    icons = resolve_icon_set("modern_swiss", "none")
    html = template.render(cv=_make_cv(), icons=icons, avoid_page_breaks=False)

    assert "<svg" not in html


def test_avoid_page_breaks_true_adds_no_breaks_class():
    """avoid_page_breaks=True → body element has class 'no-breaks'."""
    from applire.icon_sets import resolve_icon_set

    env = _make_jinja_env()
    template = env.get_template("modern_swiss.html.j2")
    icons = resolve_icon_set("modern_swiss", "none")
    html = template.render(cv=_make_cv(), icons=icons, avoid_page_breaks=True)

    assert "no-breaks" in html


def test_avoid_page_breaks_false_omits_no_breaks_class():
    """avoid_page_breaks=False → no 'no-breaks' class anywhere in output."""
    from applire.icon_sets import resolve_icon_set

    env = _make_jinja_env()
    template = env.get_template("modern_swiss.html.j2")
    icons = resolve_icon_set("modern_swiss", "none")
    html = template.render(cv=_make_cv(), icons=icons, avoid_page_breaks=False)

    assert "no-breaks" not in html


def test_lebenslauf_with_filled_renders_svg_icons():
    """lebenslauf template + filled icon set → SVG tags present."""
    from applire.icon_sets import resolve_icon_set

    env = _make_jinja_env()
    template = env.get_template("lebenslauf.html.j2")
    icons = resolve_icon_set("classic_german", "filled")
    html = template.render(cv=_make_cv(), icons=icons, avoid_page_breaks=True)

    assert "<svg" in html


def test_lebenslauf_default_no_icons():
    """lebenslauf with template default (none) → no SVG tags."""
    from applire.icon_sets import resolve_icon_set

    env = _make_jinja_env()
    template = env.get_template("lebenslauf.html.j2")
    icons = resolve_icon_set("classic_german", None)
    html = template.render(cv=_make_cv(), icons=icons, avoid_page_breaks=False)

    assert "<svg" not in html
```

- [ ] **Step 4.2: Run to verify they fail**

```bash
PYTHONPATH=backend pytest tests/unit/test_sprint16_cv_enhancements.py -v -k "renders_svg or no_breaks or omits"
```

Expected: FAIL — Jinja2 `UndefinedError: 'icons' is undefined`.

- [ ] **Step 4.3: Update `backend/applire/services/cv.py` — `generate_cv` signature**

Replace the `generate_cv` function signature and record creation block:

```python
async def generate_cv(
    job_id: uuid.UUID,
    db: AsyncSession,
    provider: LLMProvider,
    background_tasks: BackgroundTasks,
    template: CVTemplate = "classic_german",
    base_url: str = "http://localhost:8001",
    icon_set: "CVIconSet | None" = None,
    avoid_page_breaks: bool = True,
) -> CVGenerateResponse:
    """Create a pending GeneratedCV record and enqueue background rendering."""
```

And update the import at the top of the function to include `CVIconSet`:

```python
from applire.schemas.cv import CVGenerateResponse, CVStatusResponse, CVTemplate, CVIconSet, TailoredCVData
```

And update the `GeneratedCV` record creation inside `generate_cv`:

```python
    record = GeneratedCV(
        job_analysis_id=job_id,
        profile_id=profile.id,
        tailored_data={},  # populated by background task
        template=template,
        icon_set=icon_set,
        avoid_page_breaks=avoid_page_breaks,
        status=CVGenerationStatus.pending.value,
    )
```

- [ ] **Step 4.4: Update `get_cv_html` to resolve icons and pass to template**

Replace the last three lines of `get_cv_html` (the template.render call) with:

```python
    from applire.icon_sets import resolve_icon_set
    icons = resolve_icon_set(record.template, record.icon_set)
    template_file = _TEMPLATE_FILES.get(record.template, "lebenslauf.html.j2")
    template = _jinja_env.get_template(template_file)
    return template.render(cv=tailored, icons=icons, avoid_page_breaks=record.avoid_page_breaks)
```

The full updated `get_cv_html` function body after the photo resolution block:

```python
    from applire.icon_sets import resolve_icon_set
    icons = resolve_icon_set(record.template, record.icon_set)
    template_file = _TEMPLATE_FILES.get(record.template, "lebenslauf.html.j2")
    template = _jinja_env.get_template(template_file)
    return template.render(cv=tailored, icons=icons, avoid_page_breaks=record.avoid_page_breaks)
```

Note: Remove the old two-line block that was:
```python
    template_file = _TEMPLATE_FILES.get(record.template, "lebenslauf.html.j2")
    template = _jinja_env.get_template(template_file)
    return template.render(cv=tailored)
```

- [ ] **Step 4.5: Run template rendering tests — they should still fail (templates not yet updated)**

```bash
PYTHONPATH=backend pytest tests/unit/test_sprint16_cv_enhancements.py -v -k "renders_svg or no_breaks or omits"
```

Expected: FAIL — Jinja2 `UndefinedError` is gone but the SVG assertions fail because templates don't use `icons` yet.

- [ ] **Step 4.6: Commit service changes before touching templates**

```bash
git add backend/applire/services/cv.py backend/applire/schemas/cv.py
git commit -m "feat(cv): wire icon_set and avoid_page_breaks through generate_cv and get_cv_html"
```

---

## Task 5: Router Wiring

**Files:**
- Modify: `backend/applire/routers/cv.py`

- [ ] **Step 5.1: Update the router call in `post_generate`**

Replace the `return await generate_cv(...)` call in `post_generate` (line 52):

```python
        return await generate_cv(
            body.job_id,
            db,
            provider,
            background_tasks,
            template=body.template,
            base_url=base_url,
            icon_set=body.icon_set,
            avoid_page_breaks=body.avoid_page_breaks,
        )
```

- [ ] **Step 5.2: Run all tests to confirm nothing broken**

```bash
PYTHONPATH=backend pytest tests/unit/test_sprint16_cv_enhancements.py -v
```

Expected: registry tests and schema tests and model tests pass; template rendering tests still fail (templates not yet updated — expected at this stage).

- [ ] **Step 5.3: Commit**

```bash
git add backend/applire/routers/cv.py
git commit -m "feat(cv): pass icon_set and avoid_page_breaks from request to generate_cv service"
```

---

## Task 6: Update `lebenslauf.html.j2`

**Files:**
- Modify: `backend/applire/templates/lebenslauf.html.j2`

- [ ] **Step 6.1: Add `.no-breaks` CSS block**

Insert the following CSS block immediately before the `/* Print */` comment (before `@media print`):

```css
    /* Page break avoidance — active only when .no-breaks class is on <body> */
    .no-breaks .entry {
      break-inside: avoid;
      page-break-inside: avoid;
    }
    .no-breaks .section-title {
      break-after: avoid;
      page-break-after: avoid;
    }
    .no-breaks p,
    .no-breaks li {
      widows: 2;
      orphans: 2;
    }
```

- [ ] **Step 6.2: Update the `<body>` tag**

Replace:
```html
<body>
```
With:
```html
<body class="{{ 'no-breaks' if avoid_page_breaks else '' }}">
```

- [ ] **Step 6.3: Update contact items to include icons**

Replace the entire `<div class="header-contact">` block:

```html
      <div class="header-contact">
        {% if cv.contact.location %}<span>{{ icons.location | safe }}{{ cv.contact.location }}</span>{% endif %}
        {% if cv.contact.phone %}<span>{{ icons.phone | safe }}{{ cv.contact.phone }}</span>{% endif %}
        {% if cv.contact.email %}<span>{{ icons.email | safe }}{{ cv.contact.email }}</span>{% endif %}
        {% if cv.contact.linkedin %}<span>{{ icons.linkedin | safe }}{{ cv.contact.linkedin }}</span>{% endif %}
      </div>
```

- [ ] **Step 6.4: Update section titles to include icons**

Replace each `<h2 class="section-title">` line with the icon-prefixed version:

```html
  <!-- BERUFLICHES PROFIL -->
    <h2 class="section-title">{{ icons.profile | safe }}Berufliches Profil</h2>

  <!-- BERUFSERFAHRUNG -->
    <h2 class="section-title">{{ icons.experience | safe }}Berufserfahrung</h2>

  <!-- AUSBILDUNG -->
    <h2 class="section-title">{{ icons.education | safe }}Ausbildung</h2>

  <!-- KENNTNISSE -->
    <h2 class="section-title">{{ icons.skills | safe }}Kenntnisse</h2>

  <!-- SPRACHEN -->
    <h2 class="section-title">{{ icons.languages | safe }}Sprachkenntnisse</h2>
```

- [ ] **Step 6.5: Run lebenslauf template tests**

```bash
PYTHONPATH=backend pytest tests/unit/test_sprint16_cv_enhancements.py -v -k "lebenslauf"
```

Expected: `test_lebenslauf_with_filled_renders_svg_icons` passes; `test_lebenslauf_default_no_icons` passes.

- [ ] **Step 6.6: Commit**

```bash
git add backend/applire/templates/lebenslauf.html.j2
git commit -m "feat(cv): add icon set support and page break avoidance to lebenslauf template"
```

---

## Task 7: Update `modern_swiss.html.j2`

**Files:**
- Modify: `backend/applire/templates/modern_swiss.html.j2`

- [ ] **Step 7.1: Add `.no-breaks` CSS block**

Insert immediately before `/* ---- Print ---- */`:

```css
    /* ---- Page break avoidance ---- */
    .no-breaks .entry {
      break-inside: avoid;
      page-break-inside: avoid;
    }
    .no-breaks .section-header {
      break-after: avoid;
      page-break-after: avoid;
    }
    .no-breaks p,
    .no-breaks li {
      widows: 2;
      orphans: 2;
    }
```

- [ ] **Step 7.2: Update `<body>` tag**

Replace:
```html
<body>
```
With:
```html
<body class="{{ 'no-breaks' if avoid_page_breaks else '' }}">
```

- [ ] **Step 7.3: Update contact items**

Replace the entire `<div class="header-contact">` block:

```html
        <div class="header-contact">
          {% if cv.contact.location %}<div>{{ icons.location | safe }}{{ cv.contact.location }}</div>{% endif %}
          {% if cv.contact.phone %}<div>{{ icons.phone | safe }}{{ cv.contact.phone }}</div>{% endif %}
          {% if cv.contact.email %}<div>{{ icons.email | safe }}{{ cv.contact.email }}</div>{% endif %}
          {% if cv.contact.linkedin %}<div>{{ icons.linkedin | safe }}{{ cv.contact.linkedin }}</div>{% endif %}
        </div>
```

- [ ] **Step 7.4: Update section header spans to include icons**

For each section, add the icon before the English title. Replace each `<span class="section-title-en">` line:

```html
  <!-- Profile section -->
      <span class="section-title-en">{{ icons.profile | safe }}Profile</span>

  <!-- Experience section -->
      <span class="section-title-en">{{ icons.experience | safe }}Experience</span>

  <!-- Education section -->
      <span class="section-title-en">{{ icons.education | safe }}Education</span>

  <!-- Skills section -->
      <span class="section-title-en">{{ icons.skills | safe }}Skills</span>

  <!-- Languages section -->
      <span class="section-title-en">{{ icons.languages | safe }}Languages</span>
```

- [ ] **Step 7.5: Run all template tests**

```bash
PYTHONPATH=backend pytest tests/unit/test_sprint16_cv_enhancements.py -v
```

Expected: all tests pass.

- [ ] **Step 7.6: Commit**

```bash
git add backend/applire/templates/modern_swiss.html.j2
git commit -m "feat(cv): add icon set support and page break avoidance to modern_swiss template"
```

---

## Task 8: Full Test Run + Coverage Check

- [ ] **Step 8.1: Run the full unit test suite**

```bash
cd /home/apliqa/Documents/Applire/Solution
PYTHONPATH=backend pytest tests/unit/ -v --cov=applire --cov-report=term-missing 2>&1 | tail -20
```

Expected: all tests pass; coverage ≥ 75%.

- [ ] **Step 8.2: Confirm migration chain is correct**

```bash
cd backend && python -c "
from alembic.config import Config
from alembic.script import ScriptDirectory
cfg = Config('alembic.ini')
sd = ScriptDirectory.from_config(cfg)
revs = list(sd.walk_revisions())
print([r.revision for r in revs[:5]])
"
```

Expected output includes `['0020', '0019', ...]` — migration chain is intact.

- [ ] **Step 8.3: Final commit**

```bash
cd /home/apliqa/Documents/Applire/Solution
git add tests/unit/test_sprint16_cv_enhancements.py
git commit -m "test(cv): complete sprint 16 unit test suite for icon sets and page break toggle"
```

---

## Self-Review Checklist

**Spec coverage:**
- ✅ Page break avoidance CSS — Tasks 6 & 7
- ✅ Page break toggle (`avoid_page_breaks`) — Tasks 2, 3, 4, 5, 6, 7
- ✅ Icon set registry with `outline` and `filled` — Task 1
- ✅ `none` set as default for `classic_german` — Task 1 (`TEMPLATE_DEFAULT_ICON_SET`)
- ✅ `outline` set as default for `modern_swiss` — Task 1 (`TEMPLATE_DEFAULT_ICON_SET`)
- ✅ User-selectable at generation time — Tasks 2 & 5 (schema + router)
- ✅ Persisted on `generated_cvs` — Tasks 3 & 4
- ✅ `currentColor` SVGs — Task 1 (enforced by test)
- ✅ Both templates updated — Tasks 6 & 7
- ✅ Alembic migration — Task 3
- ✅ Coverage gate maintained — Task 8

**Type consistency:**
- `CVIconSet` defined in Task 2, used in Tasks 3, 4, 5 — consistent
- `resolve_icon_set(template, icon_set)` defined in Task 1, called in Task 4 — consistent
- `avoid_page_breaks` field name consistent across schema (Task 2), model (Task 3), service (Task 4), router (Task 5), templates (Tasks 6 & 7)
