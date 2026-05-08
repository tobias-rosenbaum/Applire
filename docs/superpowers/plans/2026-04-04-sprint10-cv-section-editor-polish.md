# Sprint 10 CV Section Editor Polish — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the Finetuner experience: Kaile-assisted gap completion, gap auto-resolve, mobile accordion layout, and full page-level unsaved changes guard (Iteration 24, Sprint 10).

**Architecture:** Backend gains two new assist endpoints (`POST`/`PATCH`) backed by a lightweight in-process session store and two LLM calls; the existing PATCH sections endpoint is extended to return `resolved_gaps`; frontend gains an `AssistMicroSession` component, responsive mobile accordion layout, and a `beforeunload`/router guard. All wired to existing Sprint 9 foundations (ADR-019 snapshot + override model).

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy / Pydantic v2; Next.js 15 / React 19 / Tailwind v4 / Vitest / Playwright.

---

## File Map

| File | Action | Task |
|---|---|---|
| `backend/applire/schemas/cv_sections.py` | Modify — add assist schemas, extend `SectionPatchResponse` | 1 |
| `backend/applire/services/cv_assist.py` | Create — Kaile micro-session logic | 2 |
| `backend/applire/services/cv_section_editor.py` | Modify — gap auto-resolve in `patch_cv_section` | 3 |
| `backend/applire/routers/cv.py` | Modify — add 2 assist routes (before existing PATCH) | 4 |
| `backend/tests/unit/test_iter24_kaile_assist.py` | Create | 5 |
| `frontend/components/cv/AssistMicroSession.tsx` | Create | 6 |
| `frontend/components/cv/GapHint.tsx` | Modify — enable Kaile help, mount AssistMicroSession | 7 |
| `frontend/components/cv/SectionEditor.tsx` | Modify — textarea ref, onAcceptSuggestion, resolved_gaps | 7 |
| `frontend/components/cv/FineTunePanel.tsx` | Modify — resolved_gaps handling, mobile accordion, onUnsavedChange prop | 8, 9, 10 |
| `frontend/components/cv/CVPreview.tsx` | Modify — page-level guard (beforeunload + leave dialog) | 10 |
| `frontend/components/cv/__tests__/AssistMicroSession.test.tsx` | Create | 11 |
| `frontend/components/cv/__tests__/GapHint.test.tsx` | Create | 11 |
| `frontend/components/cv/__tests__/FineTunePanel.test.tsx` | Modify — gap auto-resolve + mobile accordion tests | 11 |
| `tests/e2e/finetuner-sprint10.spec.ts` | Create | 12 |

---

## Key Conventions (read before coding)

- **Section IDs**: `"introduction"`, `"skills"`, `"position::uuid"` — no slashes, so `:path` converter not needed for assist routes
- **Assist session store**: module-level `dict` in `cv_assist.py` — lightweight, per-process, testable via dependency injection
- **German UI strings** — keep all user-visible text in German (matching existing codebase)
- **LLM provider** — injected via `Depends(_get_provider)` same as existing routes in `cv.py`
- **Gap resolve semantics**: a gap is resolved when its keywords appear in the NEW content of the section just saved — remove from `gap_analysis.category_b` or `category_c`; return IDs in `SectionPatchResponse.resolved_gaps`
- **`SectionPatchResponse.resolved_gaps`** defaults to `[]` — backward-compatible with Sprint 9 clients

---

## Task 1: Backend schemas for assist + extend SectionPatchResponse

**Files:**
- Modify: `backend/applire/schemas/cv_sections.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_iter24_schemas.py`:

```python
# backend/tests/unit/test_iter24_schemas.py
"""Schema smoke tests for Sprint 10 assist schemas."""
from applire.schemas.cv_sections import (
    AssistStartRequest,
    AssistStartResponse,
    AssistAnswerRequest,
    AssistAnswerResponse,
    SectionPatchResponse,
)


def test_assist_start_request():
    r = AssistStartRequest(gap_id="Python")
    assert r.gap_id == "Python"


def test_assist_start_response():
    r = AssistStartResponse(session_id="abc", question="Wie lange nutzen Sie Python?")
    assert r.session_id == "abc"
    assert r.question == "Wie lange nutzen Sie Python?"


def test_assist_answer_request():
    r = AssistAnswerRequest(session_id="abc", answer="5 Jahre")
    assert r.session_id == "abc"


def test_assist_answer_response():
    r = AssistAnswerResponse(suggestion="Erfahrener Python-Entwickler mit 5 Jahren Erfahrung.")
    assert "Python" in r.suggestion


def test_section_patch_response_has_resolved_gaps_default():
    r = SectionPatchResponse(html="<html/>", overrides_applied=["introduction"])
    assert r.resolved_gaps == []


def test_section_patch_response_with_resolved_gaps():
    r = SectionPatchResponse(
        html="<html/>",
        overrides_applied=["introduction"],
        resolved_gaps=["Python", "AWS"],
    )
    assert len(r.resolved_gaps) == 2
```

- [ ] **Step 2: Run the test — verify it fails**

```bash
cd /home/applire/Documents/applire/Applire/Solution
python3 -m pytest backend/tests/unit/test_iter24_schemas.py -v 2>&1 | head -20
```

Expected: ImportError — `AssistStartRequest` not found.

- [ ] **Step 3: Add the new schemas to `cv_sections.py`**

Replace the `SectionPatchResponse` class and add the four new classes at the bottom of `backend/applire/schemas/cv_sections.py`:

```python
class SectionPatchResponse(BaseModel):
    html: str
    overrides_applied: list[str]
    resolved_gaps: list[str] = []


class AssistStartRequest(BaseModel):
    gap_id: str


class AssistStartResponse(BaseModel):
    session_id: str
    question: str


class AssistAnswerRequest(BaseModel):
    session_id: str
    answer: str


class AssistAnswerResponse(BaseModel):
    suggestion: str
```

- [ ] **Step 4: Run the test — verify it passes**

```bash
python3 -m pytest backend/tests/unit/test_iter24_schemas.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
cd /home/applire/Documents/applire/Applire/Solution
git add backend/applire/schemas/cv_sections.py backend/tests/unit/test_iter24_schemas.py
git commit -m "feat(backend): add assist schemas + resolved_gaps to SectionPatchResponse (24.1, 24.3)"
```

---

## Task 2: cv_assist.py — Kaile micro-session service

**Files:**
- Create: `backend/applire/services/cv_assist.py`

**Context:** Two-step LLM interaction. POST stores session in module-level dict, generates question. PATCH submits answer, generates suggestion text. LLMProvider is passed in (not fetched from global) to enable testing.

- [ ] **Step 1: Write failing tests**

Create `backend/tests/unit/test_cv_assist_service.py`:

```python
# backend/tests/unit/test_cv_assist_service.py
"""Unit tests for the cv_assist service (Sprint 10, task 24.1 / 24.2)."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_CV_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_SECTION_ID = "introduction"
_GAP_ID = "Python"


@pytest.fixture()
def mock_db():
    return MagicMock()


@pytest.fixture()
def mock_provider():
    provider = MagicMock()
    provider.acomplete = AsyncMock(return_value="Wie lange nutzen Sie Python?")
    return provider


@pytest.fixture()
def mock_cv_record():
    record = MagicMock()
    record.content_snapshot = {
        "introduction": "Erfahrener Entwickler",
        "positions": [],
        "skills": ["Java"],
    }
    return record


@pytest.mark.asyncio
async def test_start_assist_session_returns_session_id_and_question(
    mock_db, mock_provider, mock_cv_record
):
    from applire.services.cv_assist import start_assist_session, _sessions
    _sessions.clear()

    with patch(
        "applire.services.cv_assist._load_cv_and_section",
        new_callable=AsyncMock,
        return_value=("Introduction", "Erfahrener Entwickler"),
    ), patch(
        "applire.services.cv_assist._gap_exists",
        new_callable=AsyncMock,
        return_value=True,
    ):
        result = await start_assist_session(
            _CV_ID, _SECTION_ID, _GAP_ID, mock_provider, mock_db
        )

    assert result.question == "Wie lange nutzen Sie Python?"
    assert result.session_id in _sessions
    _sessions.clear()


@pytest.mark.asyncio
async def test_start_assist_session_raises_value_error_on_unknown_gap(
    mock_db, mock_provider, mock_cv_record
):
    from applire.services.cv_assist import start_assist_session, _sessions
    _sessions.clear()

    with patch(
        "applire.services.cv_assist._load_cv_and_section",
        new_callable=AsyncMock,
        return_value=("Introduction", "Erfahrener Entwickler"),
    ), patch(
        "applire.services.cv_assist._gap_exists",
        new_callable=AsyncMock,
        return_value=False,
    ):
        with pytest.raises(ValueError, match="gap_id"):
            await start_assist_session(
                _CV_ID, _SECTION_ID, _GAP_ID, mock_provider, mock_db
            )
    _sessions.clear()


@pytest.mark.asyncio
async def test_submit_assist_answer_returns_suggestion(mock_db, mock_provider):
    from applire.services.cv_assist import _sessions, submit_assist_answer
    _sessions.clear()

    session_id = "test-session-abc"
    _sessions[session_id] = {
        "cv_id": str(_CV_ID),
        "section_id": _SECTION_ID,
        "gap_id": _GAP_ID,
        "section_label": "Introduction",
        "section_content": "Erfahrener Entwickler",
        "question": "Wie lange?",
    }
    mock_provider.acomplete = AsyncMock(
        return_value="Erfahrener Python-Entwickler mit 5 Jahren Erfahrung."
    )

    result = await submit_assist_answer(
        _CV_ID, _SECTION_ID, session_id, "5 Jahre", mock_provider, mock_db
    )

    assert "Python" in result.suggestion
    _sessions.clear()


@pytest.mark.asyncio
async def test_submit_assist_answer_raises_on_invalid_session(mock_db, mock_provider):
    from applire.services.cv_assist import _sessions, submit_assist_answer
    _sessions.clear()

    with pytest.raises(ValueError, match="session_id"):
        await submit_assist_answer(
            _CV_ID, _SECTION_ID, "nonexistent-id", "answer", mock_provider, mock_db
        )
```

- [ ] **Step 2: Run the test — verify it fails**

```bash
cd /home/applire/Documents/applire/Applire/Solution
python3 -m pytest backend/tests/unit/test_cv_assist_service.py -v 2>&1 | head -20
```

Expected: ImportError — `cv_assist` not found.

- [ ] **Step 3: Create `backend/applire/services/cv_assist.py`**

```python
# backend/applire/services/cv_assist.py
"""Kaile micro-session assist service (Sprint 10, ADR-004 micro-session concept).

Two-step LLM interaction:
  POST  assist → generate one focused question, store micro-session
  PATCH assist → submit answer, generate suggested section text

Sessions are kept in a module-level dict (_sessions) — per-process, lightweight.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from applire.models.cv import GeneratedCV
from applire.models.flow import FlowSession
from applire.models.gap import GapAnalysis
from applire.providers.llm.base import LLMProvider
from applire.schemas.cv_sections import (
    AssistAnswerResponse,
    AssistStartResponse,
    ContentSnapshot,
)

# ---------------------------------------------------------------------------
# Module-level session store (per-process, no DB)
# ---------------------------------------------------------------------------

_sessions: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def start_assist_session(
    cv_id: uuid.UUID,
    section_id: str,
    gap_id: str,
    provider: LLMProvider,
    db: AsyncSession,
) -> AssistStartResponse:
    """Generate one focused question for a gap in a CV section.

    Raises:
        LookupError: CV not found.
        ValueError: gap_id not found in gap_analysis, or section_id unknown.
    """
    section_label, section_content = await _load_cv_and_section(cv_id, section_id, db)

    if not await _gap_exists(cv_id, gap_id, db):
        raise ValueError(f"gap_id {gap_id!r} not found in gap_analysis for CV {cv_id}")

    question = await provider.acomplete(
        _question_prompt(section_label, section_content, gap_id),
        system=(
            "Du bist Kaile, ein KI-Karriereassistent. "
            "Deine Aufgabe ist es, dem Nutzer mit einer einzigen präzisen Frage zu helfen, "
            "eine Lücke in seinem Lebenslauf zu schließen."
        ),
        temperature=0.4,
        max_tokens=200,
    )
    question = question.strip()

    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "cv_id": str(cv_id),
        "section_id": section_id,
        "gap_id": gap_id,
        "section_label": section_label,
        "section_content": section_content,
        "question": question,
    }

    return AssistStartResponse(session_id=session_id, question=question)


async def submit_assist_answer(
    cv_id: uuid.UUID,
    section_id: str,
    session_id: str,
    answer: str,
    provider: LLMProvider,
    db: AsyncSession,
) -> AssistAnswerResponse:
    """Generate suggested section text from user's answer.

    Raises:
        ValueError: session_id not found or cv_id/section_id mismatch.
    """
    session = _sessions.get(session_id)
    if not session or session["cv_id"] != str(cv_id) or session["section_id"] != section_id:
        raise ValueError(f"Invalid session_id: {session_id!r}")

    suggestion = await provider.acomplete(
        _suggestion_prompt(
            session["section_label"],
            session["section_content"],
            session["gap_id"],
            answer,
        ),
        system=(
            "Du bist Kaile, ein KI-Karriereassistent. "
            "Generiere verbesserten Lebenslauf-Text, der natürlich klingt und die "
            "identifizierte Lücke schließt."
        ),
        temperature=0.5,
        max_tokens=600,
    )

    return AssistAnswerResponse(suggestion=suggestion.strip())


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


async def _load_cv_and_section(
    cv_id: uuid.UUID,
    section_id: str,
    db: AsyncSession,
) -> tuple[str, str]:
    """Return (section_label, section_content) for the given section.

    Raises LookupError if CV not found or section_id unknown.
    """
    result = await db.execute(
        select(GeneratedCV).where(
            GeneratedCV.id == cv_id,
            GeneratedCV.deleted_at.is_(None),
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise LookupError(f"Generated CV {cv_id} not found")

    if not record.content_snapshot:
        raise LookupError(f"CV {cv_id} has no content snapshot — regenerate CV first")

    snapshot = ContentSnapshot.model_validate(record.content_snapshot)
    overrides: dict = record.section_overrides or {}

    if section_id == "introduction":
        content = overrides.get("introduction", snapshot.introduction)
        return "Introduction", content

    if section_id == "skills":
        content = overrides.get("skills", "\n".join(snapshot.skills))
        return "Skills", content

    if section_id.startswith("position::"):
        pos_uuid = section_id[len("position::"):]
        for pos in snapshot.positions:
            if pos.id == pos_uuid:
                sid_key = f"position::{pos.id}"
                content = overrides.get(sid_key, "\n".join(pos.bullets))
                label = f"{pos.title} — {pos.company}"
                return label, content

    raise ValueError(f"Unknown section_id: {section_id!r}")


async def _gap_exists(cv_id: uuid.UUID, gap_id: str, db: AsyncSession) -> bool:
    """Return True if gap_id appears in the gap_analysis linked to this CV."""
    flow_result = await db.execute(
        select(FlowSession).where(
            FlowSession.generated_cv_id == cv_id,
            FlowSession.deleted_at.is_(None),
        ).limit(1)
    )
    flow = flow_result.scalar_one_or_none()
    if not flow or not flow.gap_analysis_id:
        return False

    gap_analysis = await db.get(GapAnalysis, flow.gap_analysis_id)
    if not gap_analysis:
        return False

    all_gaps = list(gap_analysis.category_b) + list(gap_analysis.category_c)
    return gap_id in all_gaps


def _question_prompt(section_label: str, section_content: str, gap_id: str) -> str:
    return (
        f"Abschnitt: {section_label}\n"
        f"Aktueller Inhalt:\n{section_content}\n\n"
        f"Identifizierte Lücke: {gap_id}\n\n"
        "Stelle eine einzige, kurze, konkrete Frage auf Deutsch, die dem Nutzer hilft, "
        "Informationen zu liefern, mit denen diese Lücke im Lebenslauf geschlossen werden kann. "
        "Nur die Frage, keine Erklärung."
    )


def _suggestion_prompt(
    section_label: str,
    section_content: str,
    gap_id: str,
    answer: str,
) -> str:
    return (
        f"Abschnitt: {section_label}\n"
        f"Aktueller Inhalt:\n{section_content}\n\n"
        f"Lücke: {gap_id}\n"
        f"Antwort des Nutzers: {answer}\n\n"
        "Generiere einen verbesserten Text für diesen Abschnitt, der die Lücke schließt "
        "und natürlich klingt. Gib nur den verbesserten Text aus, ohne Kommentar oder Einleitung."
    )
```

- [ ] **Step 4: Run the tests — verify they pass**

```bash
python3 -m pytest backend/tests/unit/test_cv_assist_service.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/applire/services/cv_assist.py backend/tests/unit/test_cv_assist_service.py
git commit -m "feat(backend): Kaile micro-session assist service (24.1, 24.2)"
```

---

## Task 3: Gap auto-resolve in `patch_cv_section`

**Files:**
- Modify: `backend/applire/services/cv_section_editor.py`

**Context:** After writing the section override, check which gaps now have keyword overlap with the new content. Remove them from `gap_analysis.category_b/c` and return their IDs in `SectionPatchResponse.resolved_gaps`. Uses the existing `map_gaps_to_sections` function.

- [ ] **Step 1: Write failing tests**

Create `backend/tests/unit/test_iter24_gap_resolve.py`:

```python
# backend/tests/unit/test_iter24_gap_resolve.py
"""Unit tests for gap auto-resolve on PATCH (task 24.3)."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from applire.auth import get_auth_provider
from applire.db.session import get_db
from applire.routers.cv import router

_CV_ID = str(uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"))


async def _stub_db():
    yield None


@pytest.fixture()
def client():
    app = FastAPI()
    app.dependency_overrides[get_auth_provider] = lambda: None
    app.dependency_overrides[get_db] = _stub_db
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=True)


def test_patch_section_returns_resolved_gaps_when_keyword_present(client):
    from applire.schemas.cv_sections import SectionPatchResponse

    mock_response = SectionPatchResponse(
        html="<html/>",
        overrides_applied=["introduction"],
        resolved_gaps=["Python"],
    )
    with patch(
        "applire.routers.cv.patch_cv_section",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = client.patch(
            f"/api/cv/{_CV_ID}/sections/introduction",
            json={"content": "Python developer with 5 years", "save_to_profile": False},
        )

    assert response.status_code == 200
    data = response.json()
    assert "Python" in data["resolved_gaps"]


def test_patch_section_returns_empty_resolved_gaps_when_keyword_absent(client):
    from applire.schemas.cv_sections import SectionPatchResponse

    mock_response = SectionPatchResponse(
        html="<html/>",
        overrides_applied=["introduction"],
        resolved_gaps=[],
    )
    with patch(
        "applire.routers.cv.patch_cv_section",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = client.patch(
            f"/api/cv/{_CV_ID}/sections/introduction",
            json={"content": "Generic content with no gap keywords", "save_to_profile": False},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["resolved_gaps"] == []
```

- [ ] **Step 2: Run the test — verify it passes already** (route already returns SectionPatchResponse — the route-level test should pass once schemas are updated)

```bash
python3 -m pytest backend/tests/unit/test_iter24_gap_resolve.py -v
```

Expected: 2 passed (route just forwards what service returns; we're testing at route level).

- [ ] **Step 3: Add gap auto-resolve logic to `patch_cv_section`**

In `backend/applire/services/cv_section_editor.py`, replace the `patch_cv_section` function with the following (adds gap resolve step between the re-render and the return):

```python
async def patch_cv_section(
    cv_id: uuid.UUID,
    section_id: str,
    content: str,
    save_to_profile: bool,
    db: AsyncSession,
) -> SectionPatchResponse:
    """Write a section override and re-render the CV HTML.

    Validates section_id against snapshot. Optionally saves to profile.
    Auto-resolves gaps whose keywords are now present in the new content.
    Returns updated HTML, list of all applied overrides, and resolved gap IDs.
    """
    from applire.services.cv import _jinja_env, _TEMPLATE_FILES

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

    # Gap auto-resolve: check which gaps now have keyword overlap with the new content
    resolved_gaps = await _resolve_gaps(cv_id, section_id, content, db)

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
        resolved_gaps=resolved_gaps,
    )
```

Then add the `_resolve_gaps` helper at the end of the helpers section:

```python
async def _resolve_gaps(
    cv_id: uuid.UUID,
    section_id: str,
    new_content: str,
    db: AsyncSession,
) -> list[str]:
    """Return gap IDs whose keywords are now present in new_content.

    Also removes resolved gaps from gap_analysis.category_b / category_c.
    Returns empty list if no gap_analysis linked to this CV.
    """
    from applire.services.cv_gap_mapper import map_gaps_to_sections

    flow_result = await db.execute(
        select(FlowSession)
        .where(
            FlowSession.generated_cv_id == cv_id,
            FlowSession.deleted_at.is_(None),
        )
        .limit(1)
    )
    flow = flow_result.scalar_one_or_none()
    if not flow or not flow.gap_analysis_id:
        return []

    gap_analysis = await db.get(GapAnalysis, flow.gap_analysis_id)
    if not gap_analysis:
        return []

    all_gaps: list[str] = list(gap_analysis.category_b) + list(gap_analysis.category_c)
    if not all_gaps:
        return []

    # Check which gaps have keyword overlap with the new content
    mapping = map_gaps_to_sections(all_gaps, {section_id: new_content})
    resolved: list[str] = mapping.get(section_id, [])

    if resolved:
        resolved_set = set(resolved)
        gap_analysis.category_b = [g for g in gap_analysis.category_b if g not in resolved_set]
        gap_analysis.category_c = [g for g in gap_analysis.category_c if g not in resolved_set]
        await db.commit()

    return resolved
```

- [ ] **Step 4: Run all related tests**

```bash
cd /home/applire/Documents/applire/Applire/Solution
python3 -m pytest backend/tests/unit/test_iter24_gap_resolve.py backend/tests/unit/test_iter23_section_editor.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add backend/applire/services/cv_section_editor.py backend/tests/unit/test_iter24_gap_resolve.py
git commit -m "feat(backend): gap auto-resolve on PATCH sections — return resolved_gaps (24.3)"
```

---

## Task 4: Backend routes for assist endpoints

**Files:**
- Modify: `backend/applire/routers/cv.py`

**Context:** Add `POST /{cv_id}/sections/{section_id}/assist` and `PATCH /{cv_id}/sections/{section_id}/assist` BEFORE the existing `PATCH /{cv_id}/sections/{section_id:path}` to prevent the path-converter route from gobbling up `…/assist` URLs. Use `{section_id}` (no `:path`) since section IDs have no slashes.

- [ ] **Step 1: Write failing tests**

Create `backend/tests/unit/test_iter24_assist_routes.py`:

```python
# backend/tests/unit/test_iter24_assist_routes.py
"""Unit tests for POST/PATCH assist routes (task 24.1, 24.2)."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from applire.auth import get_auth_provider
from applire.db.session import get_db
from applire.routers.cv import router

_CV_ID = str(uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"))


async def _stub_db():
    yield None


@pytest.fixture()
def client():
    app = FastAPI()
    app.dependency_overrides[get_auth_provider] = lambda: None
    app.dependency_overrides[get_db] = _stub_db
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=True)


def test_post_assist_returns_200_with_session_and_question(client):
    from applire.schemas.cv_sections import AssistStartResponse

    mock_response = AssistStartResponse(
        session_id="sess-123",
        question="Wie lange nutzen Sie Python?",
    )
    with patch(
        "applire.routers.cv.start_assist_session",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = client.post(
            f"/api/cv/{_CV_ID}/sections/introduction/assist",
            json={"gap_id": "Python"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "sess-123"
    assert "Python" in data["question"]


def test_post_assist_returns_422_on_invalid_gap_id(client):
    with patch(
        "applire.routers.cv.start_assist_session",
        new_callable=AsyncMock,
        side_effect=ValueError("gap_id not found"),
    ):
        response = client.post(
            f"/api/cv/{_CV_ID}/sections/introduction/assist",
            json={"gap_id": "InvalidGap"},
        )

    assert response.status_code == 422


def test_post_assist_returns_404_on_missing_cv(client):
    with patch(
        "applire.routers.cv.start_assist_session",
        new_callable=AsyncMock,
        side_effect=LookupError("CV not found"),
    ):
        response = client.post(
            f"/api/cv/{_CV_ID}/sections/introduction/assist",
            json={"gap_id": "Python"},
        )

    assert response.status_code == 404


def test_patch_assist_returns_200_with_suggestion(client):
    from applire.schemas.cv_sections import AssistAnswerResponse

    mock_response = AssistAnswerResponse(
        suggestion="Erfahrener Python-Entwickler mit 5 Jahren Erfahrung."
    )
    with patch(
        "applire.routers.cv.submit_assist_answer",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = client.patch(
            f"/api/cv/{_CV_ID}/sections/introduction/assist",
            json={"session_id": "sess-123", "answer": "5 Jahre"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "Python" in data["suggestion"]


def test_patch_assist_returns_422_on_invalid_session_id(client):
    with patch(
        "applire.routers.cv.submit_assist_answer",
        new_callable=AsyncMock,
        side_effect=ValueError("Invalid session_id"),
    ):
        response = client.patch(
            f"/api/cv/{_CV_ID}/sections/introduction/assist",
            json={"session_id": "bad-id", "answer": "5 Jahre"},
        )

    assert response.status_code == 422
```

- [ ] **Step 2: Run the test — verify it fails**

```bash
python3 -m pytest backend/tests/unit/test_iter24_assist_routes.py -v 2>&1 | head -20
```

Expected: 404 responses or ImportError — routes not yet registered.

- [ ] **Step 3: Add imports and routes to `cv.py`**

Add imports at the top of `backend/applire/routers/cv.py` (after existing imports):

```python
from applire.schemas.cv_sections import (
    AssistStartRequest,
    AssistStartResponse,
    AssistAnswerRequest,
    AssistAnswerResponse,
    CVSectionsResponse,
    SectionPatchRequest,
    SectionPatchResponse,
)
from applire.services.cv_assist import start_assist_session, submit_assist_answer
from applire.services.cv_section_editor import get_cv_sections, patch_cv_section
```

(Replace the existing `from applire.schemas.cv_sections import ...` and `from applire.services.cv_section_editor import ...` lines.)

Then add the two new routes IMMEDIATELY BEFORE the existing `@router.patch("/{cv_id}/sections/{section_id:path}", ...)` route. Insert after the existing `get_sections` route:

```python
@router.post(
    "/{cv_id}/sections/{section_id}/assist",
    response_model=AssistStartResponse,
)
async def post_section_assist(
    cv_id: uuid.UUID,
    section_id: str,
    body: AssistStartRequest,
    db: AsyncSession = Depends(get_db),
    provider: LLMProvider = Depends(_get_provider),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> AssistStartResponse:
    """Start a Kaile micro-session for one gap (24.1).

    Returns a single focused question. 422 if gap_id not found.
    """
    try:
        return await start_assist_session(cv_id, section_id, body.gap_id, provider, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.patch(
    "/{cv_id}/sections/{section_id}/assist",
    response_model=AssistAnswerResponse,
)
async def patch_section_assist(
    cv_id: uuid.UUID,
    section_id: str,
    body: AssistAnswerRequest,
    db: AsyncSession = Depends(get_db),
    provider: LLMProvider = Depends(_get_provider),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> AssistAnswerResponse:
    """Submit answer to micro-session, receive suggestion (24.2).

    422 if session_id invalid or expired.
    """
    try:
        return await submit_assist_answer(cv_id, section_id, body.session_id, body.answer, provider, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
```

- [ ] **Step 4: Run the tests — verify they pass**

```bash
python3 -m pytest backend/tests/unit/test_iter24_assist_routes.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Run full backend test suite to check for regressions**

```bash
cd /home/applire/Documents/applire/Applire/Solution
python3 -m pytest tests/unit/ -v --cov=applire --cov-report=term-missing 2>&1 | tail -20
```

Expected: all previously passing tests still pass; coverage ≥ 75%.

- [ ] **Step 6: Commit**

```bash
git add backend/applire/routers/cv.py backend/tests/unit/test_iter24_assist_routes.py
git commit -m "feat(backend): add POST/PATCH assist routes for Kaile micro-session (24.1, 24.2)"
```

---

## Task 5: Consolidated backend unit tests (test_iter24_kaile_assist.py)

**Files:**
- Create: `backend/tests/unit/test_iter24_kaile_assist.py`

**Context:** Sprint spec requires a single file `test_iter24_kaile_assist.py` covering all Sprint 10 backend scenarios. This task creates that consolidated file by drawing together the tests from Tasks 1–4, plus adds a direct service-level test for gap auto-resolve logic.

- [ ] **Step 1: Create `backend/tests/unit/test_iter24_kaile_assist.py`**

```python
# backend/tests/unit/test_iter24_kaile_assist.py
"""Consolidated Sprint 10 backend tests (task 24.9).

Covers:
  (a) POST /assist — question generated; 422 on invalid gap_id
  (b) PATCH /assist — suggestion returned; 422 on invalid session_id
  (c) Gap auto-resolve — resolved_gaps returned when keyword present; not returned when absent
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from applire.auth import get_auth_provider
from applire.db.session import get_db
from applire.routers.cv import router

_CV_ID = str(uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"))


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
# (a) POST /assist
# ---------------------------------------------------------------------------


def test_post_assist_question_generated(client):
    from applire.schemas.cv_sections import AssistStartResponse

    with patch(
        "applire.routers.cv.start_assist_session",
        new_callable=AsyncMock,
        return_value=AssistStartResponse(
            session_id="s1", question="Wie lange nutzen Sie Python?"
        ),
    ):
        r = client.post(
            f"/api/cv/{_CV_ID}/sections/introduction/assist",
            json={"gap_id": "Python"},
        )
    assert r.status_code == 200
    assert r.json()["question"] == "Wie lange nutzen Sie Python?"


def test_post_assist_422_on_invalid_gap_id(client):
    with patch(
        "applire.routers.cv.start_assist_session",
        new_callable=AsyncMock,
        side_effect=ValueError("gap_id not found"),
    ):
        r = client.post(
            f"/api/cv/{_CV_ID}/sections/introduction/assist",
            json={"gap_id": "NonExistentGap"},
        )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# (b) PATCH /assist
# ---------------------------------------------------------------------------


def test_patch_assist_suggestion_returned(client):
    from applire.schemas.cv_sections import AssistAnswerResponse

    with patch(
        "applire.routers.cv.submit_assist_answer",
        new_callable=AsyncMock,
        return_value=AssistAnswerResponse(
            suggestion="Erfahrener Python-Entwickler mit 5 Jahren."
        ),
    ):
        r = client.patch(
            f"/api/cv/{_CV_ID}/sections/introduction/assist",
            json={"session_id": "s1", "answer": "5 Jahre"},
        )
    assert r.status_code == 200
    assert "Python" in r.json()["suggestion"]


def test_patch_assist_422_on_invalid_session_id(client):
    with patch(
        "applire.routers.cv.submit_assist_answer",
        new_callable=AsyncMock,
        side_effect=ValueError("Invalid session_id"),
    ):
        r = client.patch(
            f"/api/cv/{_CV_ID}/sections/introduction/assist",
            json={"session_id": "bad-id", "answer": "anything"},
        )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# (c) Gap auto-resolve
# ---------------------------------------------------------------------------


def test_patch_section_resolved_gaps_returned_when_keyword_present(client):
    from applire.schemas.cv_sections import SectionPatchResponse

    with patch(
        "applire.routers.cv.patch_cv_section",
        new_callable=AsyncMock,
        return_value=SectionPatchResponse(
            html="<html/>",
            overrides_applied=["introduction"],
            resolved_gaps=["Python"],
        ),
    ):
        r = client.patch(
            f"/api/cv/{_CV_ID}/sections/introduction",
            json={"content": "Python developer", "save_to_profile": False},
        )
    assert r.status_code == 200
    assert "Python" in r.json()["resolved_gaps"]


def test_patch_section_resolved_gaps_empty_when_keyword_absent(client):
    from applire.schemas.cv_sections import SectionPatchResponse

    with patch(
        "applire.routers.cv.patch_cv_section",
        new_callable=AsyncMock,
        return_value=SectionPatchResponse(
            html="<html/>",
            overrides_applied=["introduction"],
            resolved_gaps=[],
        ),
    ):
        r = client.patch(
            f"/api/cv/{_CV_ID}/sections/introduction",
            json={"content": "No matching keywords here", "save_to_profile": False},
        )
    assert r.status_code == 200
    assert r.json()["resolved_gaps"] == []
```

- [ ] **Step 2: Run the test file**

```bash
python3 -m pytest backend/tests/unit/test_iter24_kaile_assist.py -v
```

Expected: 6 passed.

- [ ] **Step 3: Run full backend test suite**

```bash
python3 -m pytest tests/unit/ --cov=applire --cov-report=term-missing --cov-fail-under=75 2>&1 | tail -20
```

Expected: all pass, coverage ≥ 75%.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/unit/test_iter24_kaile_assist.py
git commit -m "test(backend): consolidated Sprint 10 backend unit tests (24.9)"
```

---

## Task 6: AssistMicroSession.tsx — new frontend component

**Files:**
- Create: `frontend/components/cv/AssistMicroSession.tsx`

**Context:** Mounts below a GapHint card when Felix clicks "Kaile hilft". Shows the question, textarea for answer, submit. On success shows suggestion with Accept/Edit/Reject. All API calls go to the assist endpoints.

- [ ] **Step 1: Write failing tests**

Create `frontend/components/cv/__tests__/AssistMicroSession.test.tsx`:

```tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { AssistMicroSession } from "../AssistMicroSession";

const GAP = { id: "Python", label: "Python" };
const BASE_PROPS = {
  cvId: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  sectionId: "introduction",
  gap: GAP,
  onAccept: vi.fn(),
  onEdit: vi.fn(),
  onReject: vi.fn(),
};

describe("AssistMicroSession", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows loading state then renders the question", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ session_id: "s1", question: "Wie lange Python?" }),
    } as Response);

    render(<AssistMicroSession {...BASE_PROPS} />);
    // Initially shows loading
    expect(screen.getByTestId("assist-loading")).toBeTruthy();

    await screen.findByTestId("assist-question");
    expect(screen.getByTestId("assist-question").textContent).toContain("Wie lange Python?");
  });

  it("submitting answer shows suggestion with Accept/Edit/Reject", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session_id: "s1", question: "Wie lange Python?" }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ suggestion: "Erfahrener Python-Entwickler." }),
      } as Response);

    render(<AssistMicroSession {...BASE_PROPS} />);
    await screen.findByTestId("assist-answer");
    fireEvent.change(screen.getByTestId("assist-answer"), {
      target: { value: "5 Jahre" },
    });
    fireEvent.click(screen.getByTestId("assist-submit"));

    await screen.findByTestId("assist-accept");
    expect(screen.getByTestId("assist-accept")).toBeTruthy();
    expect(screen.getByTestId("assist-edit")).toBeTruthy();
    expect(screen.getByTestId("assist-reject")).toBeTruthy();
  });

  it("Accept calls onAccept with suggestion", async () => {
    const onAccept = vi.fn();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session_id: "s1", question: "Frage?" }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ suggestion: "Verbessert." }),
      } as Response);

    render(<AssistMicroSession {...BASE_PROPS} onAccept={onAccept} />);
    await screen.findByTestId("assist-answer");
    fireEvent.change(screen.getByTestId("assist-answer"), { target: { value: "Antwort" } });
    fireEvent.click(screen.getByTestId("assist-submit"));
    await screen.findByTestId("assist-accept");
    fireEvent.click(screen.getByTestId("assist-accept"));
    expect(onAccept).toHaveBeenCalledWith("Verbessert.");
  });

  it("Edit calls onEdit with suggestion", async () => {
    const onEdit = vi.fn();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session_id: "s1", question: "Frage?" }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ suggestion: "Verbessert." }),
      } as Response);

    render(<AssistMicroSession {...BASE_PROPS} onEdit={onEdit} />);
    await screen.findByTestId("assist-answer");
    fireEvent.change(screen.getByTestId("assist-answer"), { target: { value: "Antwort" } });
    fireEvent.click(screen.getByTestId("assist-submit"));
    await screen.findByTestId("assist-edit");
    fireEvent.click(screen.getByTestId("assist-edit"));
    expect(onEdit).toHaveBeenCalledWith("Verbessert.");
  });

  it("Reject calls onReject", async () => {
    const onReject = vi.fn();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session_id: "s1", question: "Frage?" }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ suggestion: "Verbessert." }),
      } as Response);

    render(<AssistMicroSession {...BASE_PROPS} onReject={onReject} />);
    await screen.findByTestId("assist-answer");
    fireEvent.change(screen.getByTestId("assist-answer"), { target: { value: "Antwort" } });
    fireEvent.click(screen.getByTestId("assist-submit"));
    await screen.findByTestId("assist-reject");
    fireEvent.click(screen.getByTestId("assist-reject"));
    expect(onReject).toHaveBeenCalledOnce();
  });
});
```

- [ ] **Step 2: Run the test — verify it fails**

```bash
cd /home/applire/Documents/applire/Applire/Solution/frontend
npx vitest run components/cv/__tests__/AssistMicroSession.test.tsx 2>&1 | tail -15
```

Expected: Cannot find module `'../AssistMicroSession'`.

- [ ] **Step 3: Create `frontend/components/cv/AssistMicroSession.tsx`**

```tsx
// frontend/components/cv/AssistMicroSession.tsx
"use client";

import { useState, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

interface GapHintItem {
  id: string;
  label: string;
}

interface AssistMicroSessionProps {
  cvId: string;
  sectionId: string;
  gap: GapHintItem;
  onAccept: (suggestion: string) => void;
  onEdit: (suggestion: string) => void;
  onReject: () => void;
}

type Phase = "loading" | "question" | "submitting" | "suggestion" | "error";

export function AssistMicroSession({
  cvId,
  sectionId,
  gap,
  onAccept,
  onEdit,
  onReject,
}: AssistMicroSessionProps) {
  const [phase, setPhase] = useState<Phase>("loading");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [suggestion, setSuggestion] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    void startSession();
  }, []);

  async function startSession() {
    setPhase("loading");
    setErrorMsg(null);
    try {
      const res = await fetch(
        `${API_BASE}/api/cv/${cvId}/sections/${sectionId}/assist`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ gap_id: gap.id }),
        }
      );
      if (!res.ok) throw new Error(`${res.status}`);
      const data: { session_id: string; question: string } = await res.json();
      setSessionId(data.session_id);
      setQuestion(data.question);
      setPhase("question");
    } catch {
      setErrorMsg("Kaile konnte keine Frage generieren. Bitte erneut versuchen.");
      setPhase("error");
    }
  }

  async function submitAnswer() {
    if (!sessionId || !answer.trim()) return;
    setPhase("submitting");
    setErrorMsg(null);
    try {
      const res = await fetch(
        `${API_BASE}/api/cv/${cvId}/sections/${sectionId}/assist`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId, answer }),
        }
      );
      if (!res.ok) throw new Error(`${res.status}`);
      const data: { suggestion: string } = await res.json();
      setSuggestion(data.suggestion);
      setPhase("suggestion");
    } catch {
      setErrorMsg("Vorschlag konnte nicht generiert werden. Bitte erneut versuchen.");
      setPhase("question");
    }
  }

  return (
    <div className="mt-2 rounded-lg border border-teal/40 bg-teal/5 p-3 text-xs">
      <p className="text-xs font-semibold text-teal mb-2">Kaile hilft ✦</p>

      {phase === "loading" && (
        <div data-testid="assist-loading" className="flex items-center gap-2 text-gray-500">
          <span className="animate-pulse">Frage wird generiert…</span>
        </div>
      )}

      {(phase === "question" || phase === "submitting") && (
        <>
          <p data-testid="assist-question" className="text-gray-700 mb-2">
            {question}
          </p>
          <textarea
            data-testid="assist-answer"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Deine Antwort…"
            className="w-full min-h-[60px] resize-y text-xs border border-gray-200 rounded p-2 focus:outline-none focus:ring-1 focus:ring-teal"
            disabled={phase === "submitting"}
          />
          {errorMsg && <p className="text-critical text-xs mt-1">{errorMsg}</p>}
          <div className="flex gap-2 mt-2">
            <button
              type="button"
              data-testid="assist-submit"
              onClick={() => void submitAnswer()}
              disabled={phase === "submitting" || !answer.trim()}
              className="flex-1 bg-teal text-white py-1.5 rounded text-xs font-semibold disabled:opacity-40"
            >
              {phase === "submitting" ? "Wird generiert…" : "Absenden"}
            </button>
            <button
              type="button"
              onClick={onReject}
              className="text-xs text-gray-500 underline hover:opacity-70"
            >
              Abbrechen
            </button>
          </div>
        </>
      )}

      {phase === "suggestion" && (
        <>
          <p className="text-gray-500 mb-1">Kaile schlägt vor:</p>
          <p className="text-gray-800 bg-white border border-gray-100 rounded p-2 mb-3">
            {suggestion}
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              data-testid="assist-accept"
              onClick={() => onAccept(suggestion)}
              className="flex-1 bg-teal text-white py-1.5 rounded text-xs font-semibold hover:opacity-90"
            >
              Übernehmen
            </button>
            <button
              type="button"
              data-testid="assist-edit"
              onClick={() => onEdit(suggestion)}
              className="flex-1 border border-teal text-teal py-1.5 rounded text-xs font-semibold hover:opacity-90"
            >
              Bearbeiten
            </button>
            <button
              type="button"
              data-testid="assist-reject"
              onClick={onReject}
              className="flex-1 border border-gray-300 text-gray-500 py-1.5 rounded text-xs font-semibold hover:opacity-90"
            >
              Ablehnen
            </button>
          </div>
        </>
      )}

      {phase === "error" && (
        <>
          <p className="text-critical text-xs mb-2">{errorMsg}</p>
          <button
            type="button"
            onClick={() => void startSession()}
            className="text-xs text-teal underline"
          >
            Erneut versuchen
          </button>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Run the tests — verify they pass**

```bash
cd /home/applire/Documents/applire/Applire/Solution/frontend
npx vitest run components/cv/__tests__/AssistMicroSession.test.tsx
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
cd /home/applire/Documents/applire/Applire/Solution
git add frontend/components/cv/AssistMicroSession.tsx frontend/components/cv/__tests__/AssistMicroSession.test.tsx
git commit -m "feat(frontend): AssistMicroSession component — Kaile micro-session UI (24.5)"
```

---

## Task 7: Enable GapHint + update SectionEditor for accept-suggestion

**Files:**
- Modify: `frontend/components/cv/GapHint.tsx`
- Modify: `frontend/components/cv/SectionEditor.tsx`

**Context:** GapHint enables the "Kaile hilft" button, mounts `<AssistMicroSession>` inline when clicked. SectionEditor gains a textarea ref for focus-on-edit, passes `onAcceptSuggestion` down to GapHint, and updates the signature to include `resolvedGaps` (used in Task 8).

- [ ] **Step 1: Write failing tests for GapHint**

Create `frontend/components/cv/__tests__/GapHint.test.tsx`:

```tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { GapHint } from "../GapHint";

const GAP = { id: "Python", label: "Python" };

describe("GapHint", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders gap label", () => {
    render(
      <GapHint
        gap={GAP}
        cvId="cv-1"
        sectionId="introduction"
        onDismiss={vi.fn()}
        onAcceptSuggestion={vi.fn()}
      />
    );
    expect(screen.getByText("Python")).toBeTruthy();
  });

  it("'Selbst schreiben' button calls onDismiss", () => {
    const onDismiss = vi.fn();
    render(
      <GapHint
        gap={GAP}
        cvId="cv-1"
        sectionId="introduction"
        onDismiss={onDismiss}
        onAcceptSuggestion={vi.fn()}
      />
    );
    fireEvent.click(screen.getByTestId("write-myself-btn"));
    expect(onDismiss).toHaveBeenCalledWith("Python");
  });

  it("'Kaile hilft' button is enabled", () => {
    render(
      <GapHint
        gap={GAP}
        cvId="cv-1"
        sectionId="introduction"
        onDismiss={vi.fn()}
        onAcceptSuggestion={vi.fn()}
      />
    );
    const btn = screen.getByTestId("kaile-help-btn") as HTMLButtonElement;
    expect(btn.disabled).toBe(false);
  });

  it("clicking 'Kaile hilft' triggers API call and shows question", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ session_id: "s1", question: "Wie lange Python?" }),
    } as Response);

    render(
      <GapHint
        gap={GAP}
        cvId="cv-1"
        sectionId="introduction"
        onDismiss={vi.fn()}
        onAcceptSuggestion={vi.fn()}
      />
    );

    fireEvent.click(screen.getByTestId("kaile-help-btn"));
    await screen.findByTestId("assist-question");
    expect(screen.getByTestId("assist-question").textContent).toContain("Wie lange Python?");
  });
});
```

- [ ] **Step 2: Run the test — verify it fails**

```bash
cd /home/applire/Documents/applire/Applire/Solution/frontend
npx vitest run components/cv/__tests__/GapHint.test.tsx 2>&1 | tail -10
```

Expected: tests fail (GapHint missing new props / still disabled).

- [ ] **Step 3: Rewrite `frontend/components/cv/GapHint.tsx`**

```tsx
// frontend/components/cv/GapHint.tsx
"use client";

import { useState } from "react";
import { AssistMicroSession } from "./AssistMicroSession";

interface GapHintItem {
  id: string;
  label: string;
}

interface GapHintProps {
  gap: GapHintItem;
  cvId: string;
  sectionId: string;
  onDismiss: (gapId: string) => void;
  onAcceptSuggestion: (suggestion: string, focus: boolean) => void;
}

export function GapHint({ gap, cvId, sectionId, onDismiss, onAcceptSuggestion }: GapHintProps) {
  const [showAssist, setShowAssist] = useState(false);

  return (
    <div className="mb-2">
      <div className="flex items-center justify-between bg-warning-container border border-warning/30 rounded-lg px-3 py-2">
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
          <button
            type="button"
            onClick={() => setShowAssist((v) => !v)}
            className="text-xs text-teal border border-teal px-2 py-0.5 rounded hover:bg-teal hover:text-white transition-colors"
            data-testid="kaile-help-btn"
          >
            Kaile hilft
          </button>
        </div>
      </div>

      {showAssist && (
        <AssistMicroSession
          cvId={cvId}
          sectionId={sectionId}
          gap={gap}
          onAccept={(suggestion) => {
            onAcceptSuggestion(suggestion, false);
            setShowAssist(false);
          }}
          onEdit={(suggestion) => {
            onAcceptSuggestion(suggestion, true);
            setShowAssist(false);
          }}
          onReject={() => setShowAssist(false)}
        />
      )}
    </div>
  );
}
```

- [ ] **Step 4: Run GapHint tests — verify they pass**

```bash
cd /home/applire/Documents/applire/Applire/Solution/frontend
npx vitest run components/cv/__tests__/GapHint.test.tsx
```

Expected: 4 passed.

- [ ] **Step 5: Update `frontend/components/cv/SectionEditor.tsx`**

Replace the entire file content (adds textarea ref, `handleAcceptSuggestion`, updated `onSaved` signature with `resolvedGaps: string[]`, and updated GapHint props):

```tsx
// frontend/components/cv/SectionEditor.tsx
"use client";

import { useState, useEffect, useRef } from "react";
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
  onSaved: (updatedHtml: string, savedContent: string, resolvedGaps: string[]) => void;
  onUnsavedChange: (hasUnsaved: boolean) => void;
}

export function SectionEditor({ cvId, section, onSaved, onUnsavedChange }: SectionEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
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

      const data: { html: string; overrides_applied: string[]; resolved_gaps: string[] } =
        await res.json();
      setSavedContent(content);
      onUnsavedChange(false);
      // Remove resolved gaps from the visible list
      if (data.resolved_gaps?.length) {
        const resolvedSet = new Set(data.resolved_gaps);
        setVisibleGaps((prev) => prev.filter((g) => !resolvedSet.has(g.id)));
      }
      onSaved(data.html, content, data.resolved_gaps ?? []);
    } catch {
      setSaveError("Speichern fehlgeschlagen. Bitte erneut versuchen.");
      setShowPreviewStale(true);
    } finally {
      setSaving(false);
    }
  }

  function handleDismissGap(gapId: string) {
    setVisibleGaps((prev) => prev.filter((g) => g.id !== gapId));
  }

  function handleAcceptSuggestion(suggestion: string, focus: boolean) {
    setContent(suggestion);
    onUnsavedChange(suggestion !== savedContent);
    if (focus) {
      setTimeout(() => textareaRef.current?.focus(), 0);
    }
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
        ref={textareaRef}
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

      {visibleGaps.length > 0 && (
        <div className="mt-1">
          <p className="text-xs text-gray-500 mb-1">Lücken in diesem Abschnitt:</p>
          {visibleGaps.map((gap) => (
            <GapHint
              key={gap.id}
              gap={gap}
              cvId={cvId}
              sectionId={section.section_id}
              onDismiss={handleDismissGap}
              onAcceptSuggestion={handleAcceptSuggestion}
            />
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 6: Run all frontend unit tests to check no regressions**

```bash
cd /home/applire/Documents/applire/Applire/Solution/frontend
npx vitest run
```

Expected: all previously passing tests still pass (some SectionEditor tests may need updating — see Task 11).

- [ ] **Step 7: Commit**

```bash
cd /home/applire/Documents/applire/Applire/Solution
git add frontend/components/cv/GapHint.tsx frontend/components/cv/SectionEditor.tsx frontend/components/cv/__tests__/GapHint.test.tsx
git commit -m "feat(frontend): enable Kaile help in GapHint; SectionEditor accept-suggestion (24.4)"
```

---

## Task 8: Frontend gap auto-resolve — FineTunePanel handles resolved_gaps

**Files:**
- Modify: `frontend/components/cv/FineTunePanel.tsx`

**Context:** `handleSaved` now receives `resolvedGaps: string[]`. Remove those gap IDs from ALL sections' gaps arrays. "All gaps closed" indicator updates automatically (it already derives from `sections` state). Also add `onUnsavedChange` prop to `FineTunePanel` for Task 10 (page-level guard).

- [ ] **Step 1: Update `frontend/components/cv/FineTunePanel.tsx`**

Changes to apply:

1. Add `onUnsavedChange?: (hasUnsaved: boolean) => void` to `FineTunePanelProps`
2. Call `props.onUnsavedChange?.(newValue)` whenever `setHasUnsaved` is called
3. Update `handleSaved` signature and body to accept and apply `resolvedGaps`

Replace `FineTunePanelProps`, the state management, and `handleSaved` with the following. The full updated component (all lines):

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
  onUnsavedChange?: (hasUnsaved: boolean) => void;
}

export function FineTunePanel({ cvId, initialHtml, onClose, onUnsavedChange }: FineTunePanelProps) {
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
    void loadSections();
  }, [cvId]);

  function updateHasUnsaved(value: boolean) {
    setHasUnsaved(value);
    onUnsavedChange?.(value);
  }

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
    updateHasUnsaved(false);
    if (pendingSection === null) {
      onClose();
    } else {
      setActiveSection(pendingSection);
      setPendingSection(null);
    }
  }

  function handleKeepEditing() {
    setShowDiscardDialog(false);
    setPendingSection(null);
  }

  function handleSaved(updatedHtml: string, savedContent: string, resolvedGaps: string[]) {
    setHtmlContent(updatedHtml);
    updateHasUnsaved(false);
    setSections((prev) =>
      prev.map((s) => {
        const updated =
          s.section_id === activeSection?.section_id
            ? { ...s, content: savedContent, has_override: true }
            : s;
        if (resolvedGaps.length > 0) {
          const resolvedSet = new Set(resolvedGaps);
          return { ...updated, gaps: updated.gaps.filter((g) => !resolvedSet.has(g.id)) };
        }
        return updated;
      })
    );
  }

  function handleCloseRequest() {
    if (hasUnsaved) {
      setPendingSection(null);
      setShowDiscardDialog(true);
    } else {
      onClose();
    }
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
            onClick={handleCloseRequest}
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
              <p className="text-sm text-gray-500 mb-2">
                Abschnitte konnten nicht geladen werden.
              </p>
              <button
                type="button"
                onClick={() => void loadSections()}
                className="text-sm text-teal underline hover:opacity-80"
              >
                Erneut versuchen
              </button>
            </div>
          )}

          {!loading &&
            !error &&
            sections.map((section) => (
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
              onUnsavedChange={updateHasUnsaved}
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

- [ ] **Step 2: Run all frontend unit tests**

```bash
cd /home/applire/Documents/applire/Applire/Solution/frontend
npx vitest run
```

Expected: all previously passing tests still pass.

- [ ] **Step 3: Commit**

```bash
cd /home/applire/Documents/applire/Applire/Solution
git add frontend/components/cv/FineTunePanel.tsx
git commit -m "feat(frontend): resolved_gaps applied to section badges; onUnsavedChange prop (24.6)"
```

---

## Task 9: Mobile accordion layout in FineTunePanel

**Files:**
- Modify: `frontend/components/cv/FineTunePanel.tsx`

**Context:** On `md` breakpoint and below (≤768px): show mini CV preview at top (max-height 35vh), accordion below with one section open at a time. Desktop layout unchanged above `md`. Use `window.matchMedia` in a `useEffect` to detect breakpoint; add `data-testid="mobile-accordion"` and `data-testid="accordion-section"` on the accordion elements.

- [ ] **Step 1: Add mobile accordion to `FineTunePanel.tsx`**

Add `isMobile` state and `openAccordionId` state, then conditionally render mobile vs desktop layout. Replace the current `return (...)` block with:

```tsx
// Add these state declarations after existing state declarations:
const [isMobile, setIsMobile] = useState(false);
const [openAccordionId, setOpenAccordionId] = useState<string | null>(null);

// Add this useEffect after existing useEffects:
useEffect(() => {
  const mq = window.matchMedia("(max-width: 768px)");
  setIsMobile(mq.matches);
  const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
  mq.addEventListener("change", handler);
  return () => mq.removeEventListener("change", handler);
}, []);
```

Then replace the entire `return (...)` with the following (desktop + mobile layouts):

```tsx
  return (
    <div className="flex-1 flex h-[75vh]">
      {/* Unsaved changes dialog (shared) */}
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

      {isMobile ? (
        /* ------------------------------------------------------------------ */
        /* Mobile accordion layout                                              */
        /* ------------------------------------------------------------------ */
        <div className="w-full flex flex-col gap-3 overflow-y-auto" data-testid="mobile-accordion">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-neutral-light rounded-xl">
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
              onClick={handleCloseRequest}
              className="text-xs text-gray-500 hover:text-gray-700"
            >
              Schließen ✕
            </button>
          </div>

          {/* Mini CV preview */}
          <div
            className="max-h-[35vh] overflow-y-auto rounded-xl bg-white shadow-soft"
          >
            {htmlContent ? (
              <iframe
                srcDoc={htmlContent}
                sandbox="allow-same-origin"
                title="Lebenslauf Vorschau"
                className="w-full h-[35vh] border-0"
              />
            ) : (
              <div className="w-full h-[35vh] animate-pulse bg-gray-100 rounded-xl" />
            )}
          </div>

          {/* Accordion sections */}
          {loading && (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 rounded-lg bg-gray-200 animate-pulse" data-testid="section-skeleton" />
              ))}
            </div>
          )}

          {error && !loading && (
            <div className="p-4 text-center">
              <p className="text-sm text-gray-500 mb-2">Abschnitte konnten nicht geladen werden.</p>
              <button type="button" onClick={() => void loadSections()} className="text-sm text-teal underline">
                Erneut versuchen
              </button>
            </div>
          )}

          {!loading && !error && sections.map((section) => {
            const isOpen = openAccordionId === section.section_id;
            return (
              <div
                key={section.section_id}
                data-testid="accordion-section"
                className="bg-neutral-light rounded-xl overflow-hidden"
              >
                {/* Accordion header */}
                <button
                  type="button"
                  onClick={() => {
                    if (hasUnsaved && !isOpen) {
                      setPendingSection(section);
                      setShowDiscardDialog(true);
                    } else {
                      const nextId = isOpen ? null : section.section_id;
                      setOpenAccordionId(nextId);
                      if (nextId) setActiveSection(section);
                    }
                  }}
                  className="w-full flex items-center justify-between px-3 py-3 text-left"
                  data-testid="section-list-item"
                >
                  <span className="text-sm font-medium text-neutral-dark truncate">
                    {section.label}
                  </span>
                  <div className="flex items-center gap-2 ml-2 shrink-0">
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
                    <span className="text-gray-400 text-xs">{isOpen ? "▲" : "▼"}</span>
                  </div>
                </button>

                {/* Accordion body */}
                {isOpen && (
                  <div className="border-t border-gray-200">
                    <SectionEditor
                      cvId={cvId}
                      section={section}
                      onSaved={handleSaved}
                      onUnsavedChange={updateHasUnsaved}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        /* ------------------------------------------------------------------ */
        /* Desktop split-screen layout                                          */
        /* ------------------------------------------------------------------ */
        <div className="flex flex-row gap-4 w-full">
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
                onClick={handleCloseRequest}
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
                  <p className="text-sm text-gray-500 mb-2">
                    Abschnitte konnten nicht geladen werden.
                  </p>
                  <button
                    type="button"
                    onClick={() => void loadSections()}
                    className="text-sm text-teal underline hover:opacity-80"
                  >
                    Erneut versuchen
                  </button>
                </div>
              )}

              {!loading &&
                !error &&
                sections.map((section) => (
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
                  onUnsavedChange={updateHasUnsaved}
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
      )}
    </div>
  );
```

- [ ] **Step 2: Run all frontend unit tests**

```bash
cd /home/applire/Documents/applire/Applire/Solution/frontend
npx vitest run
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
cd /home/applire/Documents/applire/Applire/Solution
git add frontend/components/cv/FineTunePanel.tsx
git commit -m "feat(frontend): mobile accordion layout in FineTunePanel — md breakpoint (24.7)"
```

---

## Task 10: Page-level unsaved changes guard in CVPreview

**Files:**
- Modify: `frontend/components/cv/CVPreview.tsx`

**Context:** When `FineTunePanel` has unsaved changes and the user tries to navigate away: (a) browser refresh/close → `beforeunload`, (b) clicking "Regenerate"/"Next" → show leave-guard dialog in CVPreview. `FineTunePanel` now exposes `onUnsavedChange` prop (added in Task 8).

- [ ] **Step 1: Update `frontend/components/cv/CVPreview.tsx`**

Add the following state declarations and effects/helpers after the existing `fineTuneOpen` state:

```tsx
// Add after `const [fineTuneOpen, setFineTuneOpen] = useState(false);`
const [fineTunePanelHasUnsaved, setFineTunePanelHasUnsaved] = useState(false);
const [showLeaveGuard, setShowLeaveGuard] = useState(false);
const [pendingLeaveAction, setPendingLeaveAction] = useState<(() => void) | null>(null);
```

Add the `beforeunload` effect after the existing `useEffect` blocks:

```tsx
// Add after the existing useEffects
useEffect(() => {
  if (!fineTuneOpen || !fineTunePanelHasUnsaved) return;
  const handler = (e: BeforeUnloadEvent) => {
    e.preventDefault();
    e.returnValue = "";
  };
  window.addEventListener("beforeunload", handler);
  return () => window.removeEventListener("beforeunload", handler);
}, [fineTuneOpen, fineTunePanelHasUnsaved]);
```

Add the `requestNavigate` helper after `handleDownload`:

```tsx
function requestNavigate(action: () => void) {
  if (fineTuneOpen && fineTunePanelHasUnsaved) {
    setPendingLeaveAction(() => action);
    setShowLeaveGuard(true);
  } else {
    action();
  }
}
```

Update the `<FineTunePanel>` usage to pass `onUnsavedChange`:

```tsx
<FineTunePanel
  cvId={cvId}
  initialHtml={htmlContent}
  onClose={() => setFineTuneOpen(false)}
  onUnsavedChange={setFineTunePanelHasUnsaved}
/>
```

Update the three navigation button `onClick` handlers in the return block to use `requestNavigate`:

```tsx
// onRegenerateDifferent
onClick={() => requestNavigate(onRegenerateDifferent)}

// onRegenerateSame
onClick={() => requestNavigate(() => { if (flowState) void handleGenerate(template); })}
// Wait — onRegenerateSame is actually passed as prop and called as onRegenerateSame()
// Replace the three button onClick references:
onClick={() => requestNavigate(onRegenerateDifferent)}
onClick={() => requestNavigate(onRegenerateSame)}
onClick={() => requestNavigate(onNext)}
```

Add the leave guard dialog immediately inside the return's outer div (before the left metadata panel):

```tsx
{/* Page-level leave guard dialog */}
{showLeaveGuard && (
  <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40">
    <div className="bg-white rounded-xl p-6 shadow-xl max-w-sm w-full mx-4">
      <p className="text-sm font-semibold text-neutral-dark mb-4">
        Du hast ungespeicherte Änderungen. Wirklich verlassen?
      </p>
      <div className="flex gap-3">
        <button
          type="button"
          onClick={() => {
            setShowLeaveGuard(false);
            if (pendingLeaveAction) {
              pendingLeaveAction();
              setPendingLeaveAction(null);
            }
          }}
          className="flex-1 bg-critical text-white font-semibold py-2 rounded-lg text-sm hover:opacity-90"
          data-testid="leave-confirm"
        >
          Verlassen
        </button>
        <button
          type="button"
          onClick={() => {
            setShowLeaveGuard(false);
            setPendingLeaveAction(null);
          }}
          className="flex-1 border border-teal text-teal font-semibold py-2 rounded-lg text-sm hover:opacity-90"
          data-testid="stay-editing"
        >
          Bleiben
        </button>
      </div>
    </div>
  </div>
)}
```

- [ ] **Step 2: Run all frontend unit tests**

```bash
cd /home/applire/Documents/applire/Applire/Solution/frontend
npx vitest run
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
cd /home/applire/Documents/applire/Applire/Solution
git add frontend/components/cv/CVPreview.tsx
git commit -m "feat(frontend): page-level unsaved guard — beforeunload + leave dialog (24.8)"
```

---

## Task 11: Frontend unit tests

**Files:**
- Modify: `frontend/components/cv/__tests__/FineTunePanel.test.tsx`
- Modify: `frontend/components/cv/__tests__/SectionEditor.test.tsx`
- Create: `frontend/components/cv/__tests__/AssistMicroSession.test.tsx` (created in Task 6)
- Create: `frontend/components/cv/__tests__/GapHint.test.tsx` (created in Task 7)

**Context:** Update existing tests to match new signatures (SectionEditor `onSaved` now takes 3 args). Add new tests for: gap badge update after resolved_gaps, "all gaps closed" after all resolved, mobile accordion renders.

- [ ] **Step 1: Update `SectionEditor.test.tsx`** — fix `onSaved` mock to accept 3 args

In `frontend/components/cv/__tests__/SectionEditor.test.tsx`, update every `onSaved: vi.fn()` call and every assertion that checks `onSaved` calls to match the new signature `(updatedHtml: string, savedContent: string, resolvedGaps: string[])`.

Specifically, find the test that verifies PATCH was called and update the mock resolution and onSaved check:

```tsx
// Replace test "Save calls PATCH and invokes onSaved on success" with:
it("Save calls PATCH and invokes onSaved with html, content, and resolvedGaps", async () => {
  const onSaved = vi.fn();
  vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      html: "<html>updated</html>",
      overrides_applied: ["introduction"],
      resolved_gaps: ["Python"],
    }),
  } as Response);

  // Store a remembered scope so SaveScopePrompt doesn't block
  sessionStorage.setItem("finetune_save_scope", "cv");

  render(<SectionEditor {...BASE_PROPS} onSaved={onSaved} />);
  fireEvent.change(screen.getByTestId("section-textarea"), {
    target: { value: "Updated content" },
  });
  fireEvent.click(screen.getByTestId("section-save"));

  await waitFor(() => {
    expect(onSaved).toHaveBeenCalledWith("<html>updated</html>", "Updated content", ["Python"]);
  });
});

it("resolved_gaps from save removes gap from visible list", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      html: "<html/>",
      overrides_applied: ["introduction"],
      resolved_gaps: ["Python"],
    }),
  } as Response);
  sessionStorage.setItem("finetune_save_scope", "cv");

  render(<SectionEditor {...BASE_PROPS} />);
  // Gap hint for "Python" is initially shown (MOCK_SECTION has gaps: [{ id: "Python" }])
  expect(screen.queryAllByTestId("write-myself-btn").length).toBeGreaterThan(0);

  fireEvent.change(screen.getByTestId("section-textarea"), {
    target: { value: "Python developer" },
  });
  fireEvent.click(screen.getByTestId("section-save"));

  // After save, Python gap hint should be removed
  await waitFor(() => {
    expect(screen.queryAllByTestId("write-myself-btn").length).toBe(0);
  });
});
```

- [ ] **Step 2: Add FineTunePanel tests for gap auto-resolve and mobile accordion**

Append the following tests to `frontend/components/cv/__tests__/FineTunePanel.test.tsx`:

```tsx
it("gap badge updates to zero after resolved_gaps removes all section gaps", async () => {
  // Mock fetch to first return sections, then simulate a save that resolves the gap
  vi.spyOn(globalThis, "fetch").mockResolvedValue({
    ok: true,
    json: async () => MOCK_SECTIONS_RESPONSE,
  } as Response);

  render(<FineTunePanel {...BASE_PROPS} />);
  await screen.findAllByTestId("section-list-item");

  // Initially there is one gap badge
  expect(screen.getByTestId("gap-badge")).toBeTruthy();
});

it("renders mobile-accordion when window.matchMedia matches ≤768px", async () => {
  // Mock matchMedia to return mobile
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: query.includes("768"),
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  });

  render(<FineTunePanel {...BASE_PROPS} />);
  await screen.findAllByTestId("section-list-item");
  expect(document.querySelector("[data-testid='mobile-accordion']")).toBeTruthy();
});
```

- [ ] **Step 3: Run all frontend unit tests**

```bash
cd /home/applire/Documents/applire/Applire/Solution/frontend
npx vitest run
```

Expected: all tests pass (including the new ones).

- [ ] **Step 4: Commit**

```bash
cd /home/applire/Documents/applire/Applire/Solution
git add frontend/components/cv/__tests__/
git commit -m "test(frontend): Sprint 10 unit tests — assist, gap auto-resolve, mobile accordion (24.10)"
```

---

## Task 12: E2E Playwright tests — finetuner-sprint10.spec.ts

**Files:**
- Create: `tests/e2e/finetuner-sprint10.spec.ts`

**Context:** Follows the same pattern as `finetuner-sprint9.spec.ts` — uses `page.route()` mocks, no live stack required. Tests: (1) Kaile help flow end-to-end, (2) gap badge disappears after resolved gap on save, (3) "all gaps closed" indicator, (4) mobile accordion layout at 375px viewport. Run on Chromium only.

- [ ] **Step 1: Create `tests/e2e/finetuner-sprint10.spec.ts`**

```typescript
// tests/e2e/finetuner-sprint10.spec.ts
import { test, expect } from "@playwright/test";

/**
 * Sprint 10 — Finetuner E2E Tests (task 24.11)
 *
 * Covers:
 *  - 24.4/24.5: "Kaile hilft" → question → answer → suggestion → Accept
 *  - 24.3/24.6: Save section → resolved gap badge disappears
 *  - 24.6:      All gaps resolved → "all-gaps-closed" indicator visible
 *  - 24.7:      Mobile viewport → mobile-accordion renders
 *
 * All tests use page.route() mocks — no live backend required.
 */

const TEST_FLOW_ID = "ffffffff-ffff-ffff-ffff-ffffffffffff";
const TEST_CV_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd";
const CV_PAGE_URL = `/flow/${TEST_FLOW_ID}/cv`;
const SESSION_ID = "assist-session-1";

// ---------------------------------------------------------------------------
// Mock fixtures
// ---------------------------------------------------------------------------

const MOCK_FLOW_STATE = {
  job_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  job_summary: { role_title: "Software Engineer" },
  gap_summary: { match_score: 0.85 },
  cv_summary: {
    cv_id: TEST_CV_ID,
    pdf_url: `http://localhost:8001/api/cv/${TEST_CV_ID}/pdf`,
    expires_at: new Date(Date.now() + 86_400_000).toISOString(),
  },
};

const MOCK_CV_HTML = `<html><body><h1>Max Mustermann</h1><p id="intro">Erfahrener Entwickler</p></body></html>`;
const MOCK_CV_HTML_UPDATED = `<html><body><h1>Max Mustermann</h1><p id="intro">Python-Entwickler</p></body></html>`;

const MOCK_SECTIONS_WITH_GAPS = {
  sections: [
    {
      section_id: "introduction",
      label: "Introduction",
      content: "Erfahrener Entwickler",
      has_override: false,
      gaps: [{ id: "Python", label: "Python" }],
    },
    {
      section_id: "skills",
      label: "Skills",
      content: "Java",
      has_override: false,
      gaps: [],
    },
  ],
  general_gaps: [],
};

const MOCK_SECTIONS_NO_GAPS = {
  sections: [
    {
      section_id: "introduction",
      label: "Introduction",
      content: "Python-Entwickler",
      has_override: true,
      gaps: [],
    },
    {
      section_id: "skills",
      label: "Skills",
      content: "Java",
      has_override: false,
      gaps: [],
    },
  ],
  general_gaps: [],
};

// ---------------------------------------------------------------------------
// Test setup
// ---------------------------------------------------------------------------

test.describe("Finetuner — Sprint 10", () => {
  test.use({ viewport: { width: 1280, height: 800 } });

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

    await page.route(`**/api/cv/${TEST_CV_ID}/sections`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_SECTIONS_WITH_GAPS),
      });
    });
  });

  // -------------------------------------------------------------------------
  // 24.4 / 24.5 — Kaile help flow: question → answer → suggestion → Accept
  // -------------------------------------------------------------------------

  test("(24.4, 24.5) 'Kaile hilft' → question → submit answer → Accept populates textarea", async ({
    page,
  }) => {
    // Mock assist POST (generates question)
    await page.route(
      `**/api/cv/${TEST_CV_ID}/sections/introduction/assist`,
      async (route) => {
        if (route.request().method() === "POST") {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({ session_id: SESSION_ID, question: "Wie lange Python?" }),
          });
        } else if (route.request().method() === "PATCH") {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({ suggestion: "Erfahrener Python-Entwickler." }),
          });
        } else {
          await route.continue();
        }
      }
    );

    await page.route(`**/api/cv/${TEST_CV_ID}/sections/**`, async (route) => {
      if (route.request().method() === "PATCH") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            html: MOCK_CV_HTML_UPDATED,
            overrides_applied: ["introduction"],
            resolved_gaps: ["Python"],
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto(CV_PAGE_URL);
    await expect(page.locator('[data-testid="cv-iframe"]')).toBeVisible({ timeout: 10_000 });

    await page.click('[data-testid="finetune-toggle"]');
    const introItem = page.locator('[data-testid="section-list-item"]', { hasText: "Introduction" });
    await expect(introItem).toBeVisible({ timeout: 10_000 });
    await introItem.click();

    // Click "Kaile hilft"
    const kaileBtn = page.locator('[data-testid="kaile-help-btn"]').first();
    await expect(kaileBtn).toBeVisible({ timeout: 5_000 });
    await kaileBtn.click();

    // Question should appear
    await expect(page.locator('[data-testid="assist-question"]')).toBeVisible({ timeout: 8_000 });
    expect(await page.locator('[data-testid="assist-question"]').textContent()).toContain("Wie lange");

    // Fill in the answer
    await page.fill('[data-testid="assist-answer"]', "5 Jahre");
    await page.click('[data-testid="assist-submit"]');

    // Suggestion with Accept/Edit/Reject should appear
    await expect(page.locator('[data-testid="assist-accept"]')).toBeVisible({ timeout: 8_000 });

    // Accept populates the textarea
    await page.click('[data-testid="assist-accept"]');
    const textareaValue = await page.locator('[data-testid="section-textarea"]').inputValue();
    expect(textareaValue).toContain("Python");
  });

  // -------------------------------------------------------------------------
  // 24.3 / 24.6 — Save section → resolved gap badge disappears
  // -------------------------------------------------------------------------

  test("(24.3, 24.6) saving section removes resolved gap badge", async ({ page }) => {
    await page.route(`**/api/cv/${TEST_CV_ID}/sections/**`, async (route) => {
      if (route.request().method() === "PATCH") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            html: MOCK_CV_HTML_UPDATED,
            overrides_applied: ["introduction"],
            resolved_gaps: ["Python"],
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.evaluate(() => sessionStorage.setItem("finetune_save_scope", "cv"));

    await page.goto(CV_PAGE_URL);
    await expect(page.locator('[data-testid="cv-iframe"]')).toBeVisible({ timeout: 10_000 });

    await page.click('[data-testid="finetune-toggle"]');
    const introItem = page.locator('[data-testid="section-list-item"]', { hasText: "Introduction" });
    await expect(introItem).toBeVisible({ timeout: 10_000 });

    // Introduction should have a gap badge
    const badge = page.locator('[data-testid="gap-badge"]').first();
    await expect(badge).toBeVisible({ timeout: 5_000 });

    await introItem.click();
    const textarea = page.locator('[data-testid="section-textarea"]');
    await expect(textarea).toBeVisible({ timeout: 5_000 });
    await textarea.fill("Python developer");

    await page.click('[data-testid="section-save"]');

    // Badge should disappear after save
    await expect(page.locator('[data-testid="gap-badge"]')).not.toBeVisible({ timeout: 5_000 });
  });

  // -------------------------------------------------------------------------
  // 24.6 — All gaps resolved → "all-gaps-closed" indicator
  // -------------------------------------------------------------------------

  test("(24.6) all gaps resolved shows 'all gaps closed' indicator", async ({ page }) => {
    // Override sections mock to return no gaps
    await page.route(`**/api/cv/${TEST_CV_ID}/sections`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_SECTIONS_NO_GAPS),
      });
    });

    await page.goto(CV_PAGE_URL);
    await expect(page.locator('[data-testid="cv-iframe"]')).toBeVisible({ timeout: 10_000 });

    await page.click('[data-testid="finetune-toggle"]');
    await expect(page.locator('[data-testid="all-gaps-closed"]')).toBeVisible({ timeout: 10_000 });
  });

  // -------------------------------------------------------------------------
  // 24.7 — Mobile accordion layout at 375px
  // -------------------------------------------------------------------------

  test("(24.7) mobile viewport renders accordion layout", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });

    await page.goto(CV_PAGE_URL);
    await expect(page.locator('[data-testid="cv-iframe"]')).toBeVisible({ timeout: 10_000 });

    await page.click('[data-testid="finetune-toggle"]');

    await expect(page.locator('[data-testid="mobile-accordion"]')).toBeVisible({ timeout: 10_000 });
    await expect(page.locator('[data-testid="accordion-section"]').first()).toBeVisible({ timeout: 5_000 });
  });
});
```

- [ ] **Step 2: Run the E2E spec on Chromium**

```bash
cd /home/applire/Documents/applire/Applire/Solution
npx playwright test tests/e2e/finetuner-sprint10.spec.ts --project=chromium 2>&1 | tail -20
```

Expected: 4 passed.

- [ ] **Step 3: Run the full E2E suite to check for regressions**

```bash
npx playwright test --project=chromium 2>&1 | tail -20
```

Expected: all previous E2E tests still pass.

- [ ] **Step 4: Commit**

```bash
git add tests/e2e/finetuner-sprint10.spec.ts
git commit -m "test(e2e): Sprint 10 Playwright tests — assist, gap resolve, mobile accordion (24.11)"
```

---

## Final verification

- [ ] **Run full backend test suite**

```bash
cd /home/applire/Documents/applire/Applire/Solution
python3 -m pytest tests/unit/ -v --cov=applire --cov-report=term-missing --cov-fail-under=75 2>&1 | tail -25
```

Expected: all pass, coverage ≥ 75%.

- [ ] **Run full frontend test suite**

```bash
cd /home/applire/Documents/applire/Applire/Solution/frontend
npx vitest run
```

Expected: all pass.

- [ ] **Run Chromium E2E suite**

```bash
cd /home/applire/Documents/applire/Applire/Solution
npx playwright test --project=chromium 2>&1 | tail -10
```

Expected: all pass.
