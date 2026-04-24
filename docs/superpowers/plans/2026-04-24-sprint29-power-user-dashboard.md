# Sprint 29 — Power User Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current headerless mock dashboard with a full navigation shell (sidebar + topbar), a redesigned Dashboard page (Quick Tailor widget + Profile Strength card + application grid), and a new My Documents page (CV artifact table with search/filter).

**Architecture:** A Next.js `(shell)` route group owns a `layout.tsx` that renders `<AppSidebar>` and `<AppTopbar>` — all authenticated pages move inside it. The root `app/page.tsx` keeps the new/returning user split but now redirects returning users to `/dashboard` instead of rendering inline. A new backend endpoint `GET /api/documents` joins `generated_cvs → applications` to produce a cross-job document list with `flow_id` included so the Open button can link straight to the CV page.

**Tech Stack:** FastAPI, SQLAlchemy async, pytest-asyncio, aiosqlite; Next.js 15, React 19, TypeScript, Tailwind CSS v4, next-intl, Vitest, Playwright.

**Spec:** `docs/superpowers/specs/2026-04-24-sprint29-power-user-dashboard-design.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `backend/applire/schemas/documents.py` | Create | `DocumentItem`, `DocumentListResponse` Pydantic schemas |
| `backend/applire/services/documents.py` | Create | `list_documents()` service — cross-job CV query |
| `backend/applire/routers/documents.py` | Create | `GET /api/documents` endpoint |
| `backend/applire/main.py` | Modify | Register documents router |
| `tests/unit/test_sprint29_documents.py` | Create | Backend unit tests |
| `frontend/app/(shell)/layout.tsx` | Create | Shell layout — renders sidebar + topbar + children |
| `frontend/app/(shell)/dashboard/page.tsx` | Create | Dashboard page |
| `frontend/app/(shell)/documents/page.tsx` | Create | My Documents page |
| `frontend/app/(shell)/profile/page.tsx` | Create | Thin re-export of existing profile page |
| `frontend/app/(shell)/settings/page.tsx` | Create | Thin re-export of existing settings page |
| `frontend/app/(shell)/flow/[flowId]/layout.tsx` | Create | Thin wrapper — flow layout unchanged inside shell |
| `frontend/app/(shell)/flow/[flowId]/page.tsx` | Create | Pass-through to existing flow page |
| `frontend/app/(shell)/applications/[appId]/page.tsx` | Create | Pass-through to existing applications page |
| `frontend/app/page.tsx` | Modify | Redirect returning users to `/dashboard` |
| `frontend/app/profile/page.tsx` | Modify | Add redirect to `/(shell)/profile` |
| `frontend/app/settings/page.tsx` | Modify | Add redirect to `/(shell)/settings` |
| `frontend/components/shell/AppSidebar.tsx` | Create | 240px labeled sidebar with nav + user strip |
| `frontend/components/shell/AppTopbar.tsx` | Create | 52px topbar with breadcrumb + search + avatar |
| `frontend/components/dashboard/QuickTailorWidget.tsx` | Create | Inline URL/text tab widget (extracted from NewApplicationModal) |
| `frontend/components/dashboard/ProfileStrengthCard.tsx` | Create | Gradient card with score + checklist |
| `frontend/components/dashboard/DashboardApplicationCard.tsx` | Create | New bento-style card for dashboard grid |
| `frontend/components/documents/DocumentsTable.tsx` | Create | Filter bar + table + pagination for My Documents |
| `frontend/messages/de.json` | Modify | Add `shell`, `quickTailor`, `documents` translation keys |
| `frontend/messages/en.json` | Modify | Add matching English keys |
| `Documents/Product Specifications/Personas/poweruser.md` | Modify | Update Emma's touchpoint inventory, happy path, resolve Open Q1 (not committed to git) |
| `Documents/Product Specifications/Epic_and_User_Story_Tracker.csv` | Modify | Add Epic E009 with US041–US044 for Sprint 29 (not committed to git) |
| `Documents/Architecture/ADR.md` | Modify | Add ADR for (shell) route group decision (not committed to git) |
| `Documents/Architecture/arc42.md` | Modify | Update building block view, runtime view, data retention section (not committed to git) |

---

## Task 1: Backend schemas

**Files:**
- Create: `backend/applire/schemas/documents.py`
- Test: `tests/unit/test_sprint29_documents.py`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_sprint29_documents.py`:

```python
"""Sprint 29 — My Documents backend (unit tests)

Run:
    pytest tests/unit/test_sprint29_documents.py -v
"""
import uuid
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Task 1 — Schema
# ---------------------------------------------------------------------------

def test_document_item_schema():
    """DocumentItem validates correctly and accepts None flow_id."""
    from applire.schemas.documents import DocumentItem
    from applire.models.cv import CVGenerationStatus

    now = datetime.now(timezone.utc)
    item = DocumentItem(
        cv_id=uuid.uuid4(),
        flow_id=None,
        role_title="Senior Engineer",
        company_name="Roche",
        template="classic_german",
        status=CVGenerationStatus.ready,
        created_at=now,
        expires_at=now,
    )
    assert item.role_title == "Senior Engineer"
    assert item.flow_id is None


def test_document_list_response_schema():
    """DocumentListResponse wraps items and total."""
    from applire.schemas.documents import DocumentItem, DocumentListResponse
    from applire.models.cv import CVGenerationStatus

    now = datetime.now(timezone.utc)
    item = DocumentItem(
        cv_id=uuid.uuid4(),
        flow_id=uuid.uuid4(),
        role_title="QA Lead",
        company_name="Bayer",
        template="modern_swiss",
        status=CVGenerationStatus.ready,
        created_at=now,
        expires_at=now,
    )
    resp = DocumentListResponse(items=[item], total=1)
    assert resp.total == 1
    assert len(resp.items) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_sprint29_documents.py::test_document_item_schema \
       tests/unit/test_sprint29_documents.py::test_document_list_response_schema -v
```

Expected: `FAILED` — `No module named 'applire.schemas.documents'`

- [ ] **Step 3: Create `backend/applire/schemas/documents.py`**

```python
"""My Documents — response schemas for GET /api/documents."""
import uuid
from datetime import datetime

from pydantic import BaseModel

from applire.models.cv import CVGenerationStatus


class DocumentItem(BaseModel):
    cv_id: uuid.UUID
    flow_id: uuid.UUID | None
    role_title: str | None
    company_name: str | None
    template: str
    status: CVGenerationStatus
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentItem]
    total: int
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/unit/test_sprint29_documents.py::test_document_item_schema \
       tests/unit/test_sprint29_documents.py::test_document_list_response_schema -v
```

Expected: both `PASSED`

- [ ] **Step 5: Commit**

```bash
git add backend/applire/schemas/documents.py tests/unit/test_sprint29_documents.py
git commit -m "feat(schema): add DocumentItem and DocumentListResponse for My Documents"
```

---

## Task 2: Backend service — `list_documents()`

**Files:**
- Create: `backend/applire/services/documents.py`
- Test: `tests/unit/test_sprint29_documents.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_sprint29_documents.py`:

```python
# ---------------------------------------------------------------------------
# Task 2 — Service
# ---------------------------------------------------------------------------
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

_USER_A = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
_USER_B = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000002")


@pytest_asyncio.fixture
async def db():
    from applire.db.session import Base
    # Import all models so Base knows about them
    import applire.models.user  # noqa
    import applire.models.profile  # noqa
    import applire.models.application  # noqa
    import applire.models.cv  # noqa
    import applire.models.job  # noqa
    import applire.models.flow  # noqa

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


async def _seed_cv(db, user_id, role_title, company_name, template="classic_german", status="ready"):
    """Helper: seed the minimum rows needed for list_documents to return a result."""
    from applire.models.user import User
    from applire.models.profile import MasterProfile
    from applire.models.job import JobAnalysis
    from applire.models.application import Application, WorkflowStatus, UserStatus
    from applire.models.cv import GeneratedCV
    from applire.models.flow import FlowSession
    from applire.schemas.profile import MasterProfileData, PersonalInfo
    from datetime import timedelta

    now = datetime.now(timezone.utc)

    user = await db.get(User, user_id)
    if user is None:
        user = User(id=user_id, email=f"{user_id}@test.de")
        db.add(user)

    profile = MasterProfile(
        user_id=user_id,
        profile_json=MasterProfileData(
            personal_info=PersonalInfo(name="Test User")
        ).model_dump(mode="json"),
    )
    db.add(profile)

    job = JobAnalysis(
        id=uuid.uuid4(),
        raw_text=role_title,
        role_title=role_title,
        company_name=company_name,
    )
    db.add(job)

    flow = FlowSession(
        user_type="returning",
        current_step="cv_generation",
    )
    db.add(flow)
    await db.flush()

    app = Application(
        user_id=user_id,
        job_analysis_id=job.id,
        workflow_status=WorkflowStatus.completed,
        user_status=UserStatus.tracking,
        role_title=role_title,
        company_name=company_name,
        flow_session_id=flow.id,
    )
    db.add(app)

    cv = GeneratedCV(
        job_analysis_id=job.id,
        profile_id=profile.id,
        tailored_data={},
        template=template,
        status=status,
        expires_at=now + timedelta(days=90),
    )
    db.add(cv)
    await db.commit()
    return cv


@pytest.mark.asyncio
async def test_list_documents_returns_own_cvs(db):
    """list_documents returns CVs belonging to the requesting user."""
    from applire.services.documents import list_documents

    cv = await _seed_cv(db, _USER_A, "Senior Engineer", "Roche")
    result = await list_documents(user_id=_USER_A, db=db)

    assert result.total == 1
    assert result.items[0].cv_id == cv.id
    assert result.items[0].role_title == "Senior Engineer"
    assert result.items[0].company_name == "Roche"
    assert result.items[0].flow_id is not None


@pytest.mark.asyncio
async def test_list_documents_excludes_other_users(db):
    """list_documents never leaks CVs from another user."""
    from applire.services.documents import list_documents

    await _seed_cv(db, _USER_B, "QA Lead", "Bayer")
    result = await list_documents(user_id=_USER_A, db=db)

    assert result.total == 0
    assert result.items == []


@pytest.mark.asyncio
async def test_list_documents_pagination(db):
    """page and page_size parameters work correctly."""
    from applire.services.documents import list_documents

    await _seed_cv(db, _USER_A, "Role A", "Company A")
    await _seed_cv(db, _USER_A, "Role B", "Company B")
    await _seed_cv(db, _USER_A, "Role C", "Company C")

    page1 = await list_documents(user_id=_USER_A, db=db, page=1, page_size=2)
    assert len(page1.items) == 2
    assert page1.total == 3

    page2 = await list_documents(user_id=_USER_A, db=db, page=2, page_size=2)
    assert len(page2.items) == 1


@pytest.mark.asyncio
async def test_list_documents_status_filter(db):
    """status query param filters by CVGenerationStatus."""
    from applire.services.documents import list_documents

    await _seed_cv(db, _USER_A, "Role A", "Co A", status="ready")
    await _seed_cv(db, _USER_A, "Role B", "Co B", status="generating")

    ready = await list_documents(user_id=_USER_A, db=db, status="ready")
    assert ready.total == 1
    assert ready.items[0].role_title == "Role A"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/unit/test_sprint29_documents.py::test_list_documents_returns_own_cvs -v
```

Expected: `FAILED` — `No module named 'applire.services.documents'`

- [ ] **Step 3: Create `backend/applire/services/documents.py`**

```python
"""My Documents service — list generated CVs across all jobs for a user."""
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from applire.models.application import Application
from applire.models.cv import GeneratedCV
from applire.schemas.documents import DocumentItem, DocumentListResponse


async def list_documents(
    *,
    user_id: uuid.UUID,
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    status: str | None = None,
) -> DocumentListResponse:
    """Return all non-deleted CVs for *user_id*, newest first.

    Joins generated_cvs → applications to get role_title, company_name and
    flow_session_id without touching master_profiles.
    """
    base = (
        select(GeneratedCV, Application)
        .join(Application, GeneratedCV.job_analysis_id == Application.job_analysis_id)
        .where(
            Application.user_id == user_id,
            GeneratedCV.deleted_at.is_(None),
            Application.deleted_at.is_(None),
        )
    )
    if status:
        base = base.where(GeneratedCV.status == status)

    # Total count
    count_q = select(func.count()).select_from(base.subquery())
    total: int = (await db.execute(count_q)).scalar_one()

    # Paginated rows, newest first
    rows_q = (
        base.order_by(GeneratedCV.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(rows_q)).all()

    items = [
        DocumentItem(
            cv_id=cv.id,
            flow_id=app.flow_session_id,
            role_title=app.role_title,
            company_name=app.company_name,
            template=cv.template,
            status=cv.status,
            created_at=cv.created_at,
            expires_at=cv.expires_at,
        )
        for cv, app in rows
    ]
    return DocumentListResponse(items=items, total=total)
```

- [ ] **Step 4: Run all service tests**

```bash
pytest tests/unit/test_sprint29_documents.py -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add backend/applire/services/documents.py tests/unit/test_sprint29_documents.py
git commit -m "feat(service): add list_documents() — cross-job CV listing for My Documents"
```

---

## Task 3: Backend router + main.py registration

**Files:**
- Create: `backend/applire/routers/documents.py`
- Modify: `backend/applire/main.py`

- [ ] **Step 1: Create `backend/applire/routers/documents.py`**

```python
"""My Documents router — GET /api/documents."""
import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from applire.auth import get_auth_provider
from applire.auth.base import AuthProvider
from applire.db.session import get_db
from applire.schemas.documents import DocumentListResponse
from applire.services.documents import list_documents

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
async def get_documents(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    auth: AuthProvider = Depends(get_auth_provider),
) -> DocumentListResponse:
    """List all generated CVs for the current user, newest first.

    Includes flow_id so the frontend can build Open links without a second call.
    """
    user = await auth.get_current_user(request)
    return await list_documents(
        user_id=user.id,
        db=db,
        page=page,
        page_size=page_size,
        status=status,
    )
```

- [ ] **Step 2: Register in `backend/applire/main.py`**

Open `backend/applire/main.py`. Find the imports block:

```python
from applire.routers import application, cover_letter, cv, cv_color, flow, health, job, jobs, profile, profile_enrich, session
```

Replace with:

```python
from applire.routers import application, cover_letter, cv, cv_color, documents as documents_router, flow, health, job, jobs, profile, profile_enrich, session
```

Then find the `app.include_router(application.router)` line and add after it:

```python
app.include_router(documents_router.router)
```

- [ ] **Step 3: Smoke-test the endpoint**

```bash
cd backend && uvicorn applire.main:app --reload --port 8001 &
sleep 2
curl -s http://localhost:8001/api/documents | python3 -m json.tool
# Expected: {"items": [], "total": 0}  (or auth redirect depending on auth mode)
kill %1
```

- [ ] **Step 4: Commit**

```bash
git add backend/applire/routers/documents.py backend/applire/main.py
git commit -m "feat(api): add GET /api/documents endpoint"
```

---

## Task 4: i18n strings

**Files:**
- Modify: `frontend/messages/de.json`
- Modify: `frontend/messages/en.json`

- [ ] **Step 1: Add German strings to `frontend/messages/de.json`**

Open the file and add three new top-level namespaces at the end of the JSON object (before the final `}`):

```json
  "shell": {
    "dashboard": "Dashboard",
    "profile": "Masterprofil",
    "documents": "Meine Dokumente",
    "settings": "Einstellungen",
    "help": "Hilfe & Support",
    "userFreePlan": "Free Plan"
  },
  "quickTailor": {
    "title": "Quick Tailor",
    "subtitle": "Job-Link oder Beschreibung einfügen — Applire analysiert und startet deinen Lebenslauf-Flow.",
    "tabUrl": "Job-URL",
    "tabText": "Text einfügen",
    "urlPlaceholder": "https://www.stepstone.de/stellenangebote/…",
    "textPlaceholder": "Vollständige Stellenbeschreibung hier einfügen…",
    "analyseButton": "Analysieren →",
    "analysing": "Analysiert…"
  },
  "documents": {
    "title": "Meine Dokumente",
    "subtitle": "Alle generierten Lebensläufe deiner Bewerbungen",
    "totalDocs": "Dokumente gesamt",
    "expiringCount": "Ablaufend in 7 Tagen",
    "filterAll": "Alle",
    "filterReady": "Bereit",
    "filterGenerating": "Wird erstellt",
    "filterExpiring": "Bald ablaufend",
    "sortNewest": "Neueste zuerst",
    "sortOldest": "Älteste zuerst",
    "sortCompany": "Nach Unternehmen",
    "searchPlaceholder": "Nach Stelle oder Unternehmen filtern…",
    "colDocument": "Dokument",
    "colTemplate": "Vorlage",
    "colStatus": "Status",
    "colExpires": "Ablauf",
    "statusReady": "Bereit",
    "statusGenerating": "Wird erstellt…",
    "statusExpired": "Abgelaufen",
    "expiresIn": "Läuft in {days} Tagen ab",
    "expiresToday": "Läuft heute ab",
    "openButton": "Öffnen",
    "generatingButton": "Wird erstellt…",
    "noDocuments": "Noch keine Dokumente. Starte eine neue Bewerbung.",
    "generatedOn": "Erstellt am {date}",
    "page": "Seite {page} von {total}",
    "showing": "{from}–{to} von {total} Dokumenten"
  }
```

- [ ] **Step 2: Add English strings to `frontend/messages/en.json`**

Add the same three namespaces:

```json
  "shell": {
    "dashboard": "Dashboard",
    "profile": "Master Profile",
    "documents": "My Documents",
    "settings": "Settings",
    "help": "Help & Support",
    "userFreePlan": "Free Plan"
  },
  "quickTailor": {
    "title": "Quick Tailor",
    "subtitle": "Paste a job link or full description — Applire analyses it and starts your CV flow.",
    "tabUrl": "Job URL",
    "tabText": "Paste Text",
    "urlPlaceholder": "https://www.stepstone.de/stellenangebote/…",
    "textPlaceholder": "Paste the full job description here…",
    "analyseButton": "Analyse →",
    "analysing": "Analysing…"
  },
  "documents": {
    "title": "My Documents",
    "subtitle": "All generated CVs across your applications",
    "totalDocs": "Total documents",
    "expiringCount": "Expiring within 7 days",
    "filterAll": "All",
    "filterReady": "Ready",
    "filterGenerating": "Generating",
    "filterExpiring": "Expiring soon",
    "sortNewest": "Newest first",
    "sortOldest": "Oldest first",
    "sortCompany": "By company",
    "searchPlaceholder": "Filter by role or company…",
    "colDocument": "Document",
    "colTemplate": "Template",
    "colStatus": "Status",
    "colExpires": "Expires",
    "statusReady": "Ready",
    "statusGenerating": "Generating…",
    "statusExpired": "Expired",
    "expiresIn": "Expires in {days} days",
    "expiresToday": "Expires today",
    "openButton": "Open",
    "generatingButton": "Generating…",
    "noDocuments": "No documents yet. Start a new application.",
    "generatedOn": "Generated {date}",
    "page": "Page {page} of {total}",
    "showing": "{from}–{to} of {total} documents"
  }
```

- [ ] **Step 3: Verify JSON is valid**

```bash
cd frontend && node -e "JSON.parse(require('fs').readFileSync('messages/de.json','utf8')); console.log('DE ok')"
cd frontend && node -e "JSON.parse(require('fs').readFileSync('messages/en.json','utf8')); console.log('EN ok')"
```

Expected: `DE ok` / `EN ok`

- [ ] **Step 4: Commit**

```bash
git add frontend/messages/de.json frontend/messages/en.json
git commit -m "feat(i18n): add shell, quickTailor, documents translation keys (DE + EN)"
```

---

## Task 5: AppSidebar component

**Files:**
- Create: `frontend/components/shell/AppSidebar.tsx`

- [ ] **Step 1: Create `frontend/components/shell/AppSidebar.tsx`**

```tsx
"use client";

import { usePathname, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

interface NavItem {
  key: "dashboard" | "profile" | "documents" | "settings";
  href: string;
  icon: string; // Material Symbols name
}

const NAV_ITEMS: NavItem[] = [
  { key: "dashboard", href: "/dashboard", icon: "dashboard" },
  { key: "profile",   href: "/profile",   icon: "person_book" },
  { key: "documents", href: "/documents", icon: "description" },
  { key: "settings",  href: "/settings",  icon: "settings" },
];

interface AppSidebarProps {
  userName?: string | null;
}

export function AppSidebar({ userName }: AppSidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const t = useTranslations("shell");

  const initials = userName
    ? userName.split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase()
    : "?";

  return (
    <aside className="w-60 min-w-[240px] bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-[18px] border-b border-gray-100">
        <div className="w-[34px] h-[34px] rounded-[9px] bg-gradient-to-br from-[#003399] to-[#002068] flex items-center justify-center flex-shrink-0">
          <span className="material-symbols-outlined text-white" style={{ fontSize: 18 }}>view_cozy</span>
        </div>
        <span className="text-[16px] font-extrabold text-[#003399] tracking-tight font-manrope">
          Applire
        </span>
      </div>

      {/* User strip */}
      <div className="flex items-center gap-2.5 px-5 py-3 border-b border-gray-100">
        <div className="w-[34px] h-[34px] rounded-full bg-gradient-to-br from-[#b5c4ff] to-[#dce1ff] flex items-center justify-center text-[13px] font-bold text-[#003399] flex-shrink-0">
          {initials}
        </div>
        <div className="min-w-0">
          <p className="text-[13px] font-bold text-gray-900 truncate">
            {userName ?? "—"}
          </p>
          <p className="text-[11px] text-gray-400 mt-0.5">{t("userFreePlan")}</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-2.5 flex flex-col gap-0.5">
        {NAV_ITEMS.map(({ key, href, icon }) => {
          const active = pathname.startsWith(href);
          return (
            <button
              key={key}
              onClick={() => router.push(href)}
              className={cn(
                "flex items-center gap-2.5 w-full px-3 py-2.5 rounded-lg text-[13px] font-medium transition-colors text-left",
                active
                  ? "bg-[#eef1ff] text-[#003399] font-bold border-r-[3px] border-[#003399] rounded-r-none"
                  : "text-gray-600 hover:bg-[#f1f3ff] hover:text-[#003399]"
              )}
            >
              <span
                className="material-symbols-outlined flex-shrink-0"
                style={{ fontSize: 20, fontVariationSettings: active ? "'FILL' 1" : "'FILL' 0" }}
              >
                {icon}
              </span>
              {t(key)}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-gray-100">
        <button
          onClick={() => router.push("/help")}
          className="flex items-center gap-2 text-[12.5px] text-gray-400 hover:text-[#003399] transition-colors w-full"
        >
          <span className="material-symbols-outlined" style={{ fontSize: 18 }}>help</span>
          {t("help")}
        </button>
      </div>
    </aside>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "AppSidebar\|error" | head -20
```

Expected: no errors mentioning AppSidebar

- [ ] **Step 3: Commit**

```bash
git add frontend/components/shell/AppSidebar.tsx
git commit -m "feat(shell): add AppSidebar component"
```

---

## Task 6: AppTopbar component

**Files:**
- Create: `frontend/components/shell/AppTopbar.tsx`

- [ ] **Step 1: Create `frontend/components/shell/AppTopbar.tsx`**

```tsx
"use client";

import { usePathname, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";

interface AppTopbarProps {
  onSearchChange?: (q: string) => void;
  searchValue?: string;
  searchPlaceholder?: string;
  showSearch?: boolean;
}

const SECTION_LABELS: Record<string, string> = {
  "/dashboard": "shell.dashboard",
  "/profile":   "shell.profile",
  "/documents": "shell.documents",
  "/settings":  "shell.settings",
};

export function AppTopbar({
  onSearchChange,
  searchValue = "",
  searchPlaceholder,
  showSearch = false,
}: AppTopbarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const t = useTranslations("shell");

  const sectionKey = Object.keys(SECTION_LABELS).find((k) => pathname.startsWith(k));
  const sectionLabel = sectionKey
    ? t(SECTION_LABELS[sectionKey].split(".")[1] as Parameters<typeof t>[0])
    : "";

  return (
    <header className="h-[52px] bg-white/90 backdrop-blur border-b border-gray-200 flex items-center px-6 gap-4 flex-shrink-0">
      {/* Breadcrumb */}
      <div className="flex items-center gap-1.5 flex-1 text-[13px] text-gray-400 font-manrope">
        <span>Applire</span>
        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>chevron_right</span>
        <span className="text-gray-900 font-bold">{sectionLabel}</span>
      </div>

      {/* Search — only shown when parent opts in */}
      {showSearch && (
        <div className="flex items-center gap-2 bg-[#f1f3ff] border border-gray-200 rounded-full px-3.5 py-1.5 w-52">
          <span className="material-symbols-outlined text-gray-400" style={{ fontSize: 16 }}>search</span>
          <input
            type="text"
            value={searchValue}
            onChange={(e) => onSearchChange?.(e.target.value)}
            placeholder={searchPlaceholder ?? ""}
            className="bg-transparent border-none outline-none text-[12.5px] text-gray-800 placeholder:text-gray-400 w-full"
          />
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button className="w-8 h-8 rounded-full flex items-center justify-center text-gray-600 hover:bg-[#f1f3ff] hover:text-[#003399] transition-colors">
          <span className="material-symbols-outlined" style={{ fontSize: 20 }}>notifications</span>
        </button>
        <button
          onClick={() => router.push("/settings")}
          className="w-[30px] h-[30px] rounded-full bg-gradient-to-br from-[#b5c4ff] to-[#dce1ff] flex items-center justify-center text-[12px] font-bold text-[#003399] cursor-pointer"
        >
          A
        </button>
      </div>
    </header>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "AppTopbar\|error" | head -20
```

Expected: no errors mentioning AppTopbar

- [ ] **Step 3: Commit**

```bash
git add frontend/components/shell/AppTopbar.tsx
git commit -m "feat(shell): add AppTopbar component"
```

---

## Task 7: Shell layout + route moves

**Files:**
- Create: `frontend/app/(shell)/layout.tsx`
- Create: `frontend/app/(shell)/dashboard/page.tsx` (placeholder)
- Create: `frontend/app/(shell)/documents/page.tsx` (placeholder)
- Create: `frontend/app/(shell)/profile/page.tsx`
- Create: `frontend/app/(shell)/settings/page.tsx`
- Create: `frontend/app/(shell)/flow/[flowId]/layout.tsx`
- Create: `frontend/app/(shell)/applications/[appId]/page.tsx`

The strategy is to **copy** existing page content into `(shell)/` first and then update `app/page.tsx` to redirect. This keeps all existing pages working while the shell is built around them.

- [ ] **Step 1: Create `frontend/app/(shell)/layout.tsx`**

```tsx
import { AppSidebar } from "@/components/shell/AppSidebar";

export default function ShellLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-[#f9f9ff]">
      <AppSidebar />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {children}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create placeholder dashboard page**

Create `frontend/app/(shell)/dashboard/page.tsx`:

```tsx
export default function DashboardPage() {
  return (
    <div className="flex-1 flex items-center justify-center text-gray-400">
      Dashboard — coming in Task 10
    </div>
  );
}
```

- [ ] **Step 3: Create placeholder documents page**

Create `frontend/app/(shell)/documents/page.tsx`:

```tsx
export default function DocumentsPage() {
  return (
    <div className="flex-1 flex items-center justify-center text-gray-400">
      My Documents — coming in Task 12
    </div>
  );
}
```

- [ ] **Step 4: Move profile page into shell**

Read `frontend/app/profile/page.tsx` fully. Copy its full contents into the new file `frontend/app/(shell)/profile/page.tsx` unchanged.

Then replace `frontend/app/profile/page.tsx` with a redirect:

```tsx
import { redirect } from "next/navigation";
export default function ProfileRedirect() {
  redirect("/profile");
}
```

(The `(shell)/profile/page.tsx` IS at the path `/profile` — the route group `(shell)` is invisible in URLs.)

- [ ] **Step 5: Move settings page into shell**

Read `frontend/app/settings/page.tsx` fully. Copy its contents into `frontend/app/(shell)/settings/page.tsx`.

Replace `frontend/app/settings/page.tsx`:

```tsx
import { redirect } from "next/navigation";
export default function SettingsRedirect() {
  redirect("/settings");
}
```

- [ ] **Step 6: Create shell flow layout wrapper**

Create `frontend/app/(shell)/flow/[flowId]/layout.tsx`:

```tsx
export { default } from "@/app/(shell)/flow/[flowId]/layout-inner";
```

Wait — the flow layout is complex. The simpler approach: copy the existing `app/flow/[flowId]/layout.tsx` content into `app/(shell)/flow/[flowId]/layout.tsx` unchanged, and delete the original once the shell is the canonical location.

Read `frontend/app/flow/[flowId]/layout.tsx` fully and copy its contents verbatim to `frontend/app/(shell)/flow/[flowId]/layout.tsx`.

Also copy every sub-page from `frontend/app/flow/[flowId]/` into `frontend/app/(shell)/flow/[flowId]/` (cv/, gaps/, import/, interview/, cover-letter/, processing/).

- [ ] **Step 7: Create shell applications page**

Read `frontend/app/applications/` and copy any `page.tsx` files into `frontend/app/(shell)/applications/[appId]/page.tsx`.

- [ ] **Step 8: Update `frontend/app/page.tsx` to redirect returning users**

Find the section:

```tsx
  // Returning user → Dashboard
  if (isReturningUser) {
    return <Dashboard />;
  }
```

Replace with:

```tsx
  // Returning user → Dashboard
  if (isReturningUser) {
    router.replace("/dashboard");
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-dim">
        <p className="text-gray-500">{tCommon("loading")}</p>
      </div>
    );
  }
```

Also remove the `Dashboard` import and `NewApplicationModal` import from `app/page.tsx` since they are no longer used there.

- [ ] **Step 9: Verify the app loads**

```bash
cd frontend && npm run dev &
sleep 5
curl -s http://localhost:3000 | grep -i "applire\|loading\|error" | head -5
kill %1
```

Expected: responds without 500 errors

- [ ] **Step 10: Commit**

```bash
git add frontend/app/\(shell\)/ frontend/app/page.tsx frontend/app/profile/page.tsx frontend/app/settings/page.tsx
git commit -m "feat(routing): add (shell) route group with sidebar layout; redirect returning users to /dashboard"
```

---

## Task 8: QuickTailorWidget

**Files:**
- Create: `frontend/components/dashboard/QuickTailorWidget.tsx`

- [ ] **Step 1: Create `frontend/components/dashboard/QuickTailorWidget.tsx`**

This extracts and adapts the logic from `NewApplicationModal`. The API call sequence is identical (`POST /api/job/analyze` → `POST /api/applications`); only the UI wrapper changes.

```tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";
type JdMode = "url" | "text";

export function QuickTailorWidget() {
  const t = useTranslations("quickTailor");
  const router = useRouter();
  const [mode, setMode] = useState<JdMode>("url");
  const [url, setUrl] = useState("");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const canSubmit = (mode === "url" && url.trim()) || (mode === "text" && text.trim());

  async function handleSubmit() {
    if (!canSubmit) return;
    setLoading(true);
    setError("");
    try {
      const jdPayload = mode === "url" ? { url } : { text };
      const analyzeRes = await fetch(`${API_BASE}/api/job/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(jdPayload),
      });
      if (!analyzeRes.ok) {
        const err = await analyzeRes.json();
        setError(err.detail ?? "Analysis failed");
        return;
      }
      const jobData = await analyzeRes.json();

      const createRes = await fetch(`${API_BASE}/api/applications`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_analysis_id: jobData.id, start_workflow: true }),
      });
      if (!createRes.ok) {
        const err = await createRes.json();
        setError(createRes.status === 409 ? "Application already exists." : (err.detail ?? "Failed to create application"));
        return;
      }
      const appData = await createRes.json();
      router.push(`/flow/${appData.flow_session_id}/import`);
    } catch {
      setError("An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white rounded-[14px] border border-gray-200 shadow-sm px-[22px] py-5 relative overflow-hidden">
      {/* gradient top-border */}
      <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-[#fecb00] via-[#003399] to-[#fecb00]" />

      <p className="font-extrabold text-[15px] text-[#141b2b] mb-1 font-manrope flex items-center gap-1.5">
        <span className="material-symbols-outlined text-[#fecb00]" style={{ fontSize: 18 }}>auto_awesome</span>
        {t("title")}
      </p>
      <p className="text-[12px] text-gray-500 mb-3.5">{t("subtitle")}</p>

      {error && (
        <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2 mb-3">
          {error}
        </p>
      )}

      {/* Tab toggle */}
      <div className="flex border-b-2 border-gray-100 mb-3.5">
        {(["url", "text"] as JdMode[]).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={cn(
              "px-4 pb-2 text-[13px] font-semibold relative font-manrope transition-colors",
              mode === m ? "text-[#003399]" : "text-gray-500 hover:text-gray-800"
            )}
          >
            {m === "url" ? t("tabUrl") : t("tabText")}
            {mode === m && (
              <span className="absolute bottom-[-2px] left-0 right-0 h-[2px] bg-[#003399] rounded-t" />
            )}
          </button>
        ))}
      </div>

      {/* Inputs */}
      <div className="flex gap-2.5 items-end">
        {mode === "url" ? (
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            placeholder={t("urlPlaceholder")}
            disabled={loading}
            className="flex-1 h-10 border-[1.5px] border-gray-300 rounded-lg px-3.5 text-[13px] outline-none focus:border-[#003399] focus:ring-2 focus:ring-[#003399]/10 disabled:opacity-50"
          />
        ) : (
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={t("textPlaceholder")}
            disabled={loading}
            className="flex-1 min-h-[88px] resize-y border-[1.5px] border-gray-300 rounded-lg px-3.5 py-2.5 text-[13px] outline-none focus:border-[#003399] focus:ring-2 focus:ring-[#003399]/10 disabled:opacity-50"
          />
        )}
        <button
          onClick={handleSubmit}
          disabled={!canSubmit || loading}
          className="h-10 px-5 bg-[#003399] text-white rounded-lg text-[13px] font-bold font-manrope self-end whitespace-nowrap hover:bg-[#002068] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? t("analysing") : t("analyseButton")}
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "QuickTailor\|error" | head -20
```

Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/components/dashboard/QuickTailorWidget.tsx
git commit -m "feat(dashboard): add QuickTailorWidget with URL/text tabs"
```

---

## Task 9: ProfileStrengthCard

**Files:**
- Create: `frontend/components/dashboard/ProfileStrengthCard.tsx`

- [ ] **Step 1: Create `frontend/components/dashboard/ProfileStrengthCard.tsx`**

```tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

interface ChecklistItem {
  label: string;
  done: boolean;
}

function buildChecklist(profile: Record<string, unknown> | null): ChecklistItem[] {
  if (!profile) return [];
  const pi = (profile.personal_info as Record<string, unknown>) ?? {};
  const work = (profile.work_experience as unknown[]) ?? [];
  const skills = (profile.skills as unknown[]) ?? [];
  const edu = (profile.education as unknown[]) ?? [];
  return [
    { label: "Berufserfahrung", done: work.length > 0 },
    { label: "Fähigkeiten", done: skills.length > 0 },
    { label: "Ausbildung", done: edu.length > 0 },
    { label: "Zusammenfassung", done: !!(pi.summary as string) },
  ];
}

export function ProfileStrengthCard() {
  const router = useRouter();
  const [score, setScore] = useState<number | null>(null);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const [existsRes, profileRes] = await Promise.all([
          fetch(`${API_BASE}/api/profile/exists`),
          fetch(`${API_BASE}/api/profile`),
        ]);
        if (existsRes.ok) {
          const d = await existsRes.json();
          setScore(Math.round((d.completeness_score ?? 0) * 100));
        }
        if (profileRes.ok) {
          const d = await profileRes.json();
          setChecklist(buildChecklist(d.profile ?? null));
        }
      } catch {
        // non-fatal — card stays in skeleton state
      }
    }
    void load();
  }, []);

  const barWidth = score !== null ? `${score}%` : "0%";

  return (
    <div className="rounded-[14px] p-5 text-white flex flex-col bg-gradient-to-br from-[#002068] to-[#003399] shadow-lg shadow-[#002068]/20">
      <p className="text-[11px] font-bold uppercase tracking-widest text-white/60 mb-1.5">
        Profile Strength
      </p>

      {score === null ? (
        <div className="h-12 w-20 rounded bg-white/10 animate-pulse mb-3" />
      ) : (
        <p className="text-[46px] font-extrabold leading-none font-manrope mb-2.5">{score}</p>
      )}

      {/* Progress bar */}
      <div className="h-[5px] bg-white/20 rounded-full mb-2">
        <div
          className="h-[5px] bg-[#fecb00] rounded-full transition-all duration-700"
          style={{ width: barWidth }}
        />
      </div>
      <p className="text-[11.5px] text-white/60 mb-3">
        Add missing sections to improve gap matching.
      </p>

      {/* Checklist */}
      <div className="flex flex-col gap-1.5 mb-4">
        {checklist.map((item) => (
          <div key={item.label} className="flex items-center gap-2 text-[11.5px]">
            <span
              className="material-symbols-outlined"
              style={{
                fontSize: 14,
                color: item.done ? "#4ade80" : "rgba(255,255,255,0.25)",
              }}
            >
              {item.done ? "check_circle" : "radio_button_unchecked"}
            </span>
            <span className={item.done ? "text-white/75" : "text-white/40"}>{item.label}</span>
          </div>
        ))}
      </div>

      <button
        onClick={() => router.push("/profile")}
        className="mt-auto text-[12px] font-bold text-[#fecb00] flex items-center gap-1 hover:opacity-80 transition-opacity"
      >
        <span className="material-symbols-outlined" style={{ fontSize: 15 }}>arrow_forward</span>
        Complete Profile
      </button>
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "ProfileStrength\|error" | head -20
```

Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/components/dashboard/ProfileStrengthCard.tsx
git commit -m "feat(dashboard): add ProfileStrengthCard component"
```

---

## Task 10: DashboardApplicationCard

**Files:**
- Create: `frontend/components/dashboard/DashboardApplicationCard.tsx`

- [ ] **Step 1: Create `frontend/components/dashboard/DashboardApplicationCard.tsx`**

```tsx
"use client";

import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";

export type CardStatus = "in_progress" | "cv_ready" | "interrupted" | "tracking";

export interface DashboardApplicationCardProps {
  applicationId: string;
  roleTitle: string | null;
  companyName: string | null;
  workflowStatus: string;
  flowSessionId: string | null;
  updatedAt: string;
  onStartFlow?: () => void;
}

function deriveCardStatus(workflowStatus: string, updatedAt: string): CardStatus {
  if (workflowStatus === "completed") return "cv_ready";
  if (workflowStatus === "none") return "tracking";
  const hoursAgo = (Date.now() - new Date(updatedAt).getTime()) / 36e5;
  if (workflowStatus === "analyzing" || workflowStatus === "interviewing" || workflowStatus === "cv_generating") {
    return hoursAgo > 48 ? "interrupted" : "in_progress";
  }
  return "in_progress";
}

const PROGRESS: Record<CardStatus, number> = {
  in_progress: 50,
  cv_ready: 100,
  interrupted: 65,
  tracking: 0,
};

const CHIP: Record<CardStatus, { label: string; className: string }> = {
  in_progress:  { label: "In Progress",  className: "bg-[#e9edff] text-[#003399]" },
  cv_ready:     { label: "CV Ready",     className: "bg-[#dcfce7] text-[#166534]" },
  interrupted:  { label: "Interrupted",  className: "bg-[#fef9c3] text-[#854d0e]" },
  tracking:     { label: "Tracking",     className: "bg-[#f1f5f9] text-[#64748b]" },
};

const PROGRESS_COLOR: Record<CardStatus, string> = {
  in_progress: "bg-[#003399]",
  cv_ready:    "bg-[#22c55e]",
  interrupted: "bg-[#eab308]",
  tracking:    "bg-[#e2e5f0]",
};

export function DashboardApplicationCard({
  applicationId,
  roleTitle,
  companyName,
  workflowStatus,
  flowSessionId,
  updatedAt,
  onStartFlow,
}: DashboardApplicationCardProps) {
  const router = useRouter();
  const status = deriveCardStatus(workflowStatus, updatedAt);
  const chip = CHIP[status];
  const initial = (companyName ?? roleTitle ?? "?")[0].toUpperCase();

  const relativeTime = (() => {
    const h = Math.floor((Date.now() - new Date(updatedAt).getTime()) / 36e5);
    if (h < 1) return "just now";
    if (h < 24) return `${h}h ago`;
    return `${Math.floor(h / 24)}d ago`;
  })();

  function handleAction(e: React.MouseEvent) {
    e.stopPropagation();
    if (status === "tracking") {
      onStartFlow?.();
    } else if (flowSessionId) {
      const dest = status === "cv_ready" ? `/flow/${flowSessionId}/cv` : `/flow/${flowSessionId}/interview`;
      router.push(dest);
    }
  }

  const ACTION_LABEL: Record<CardStatus, string> = {
    in_progress: "Resume",
    cv_ready:    "Open",
    interrupted: "Continue",
    tracking:    "Start Flow",
  };

  return (
    <div
      className={cn(
        "bg-white rounded-xl border-[1.5px] p-4 cursor-pointer transition-all",
        status === "interrupted" ? "border-dashed border-gray-300" : "border-gray-200",
        status === "cv_ready" ? "border-green-200 bg-green-50/30" : "",
        "hover:shadow-md hover:border-[#b5c4ff]"
      )}
      onClick={() => router.push(`/applications/${applicationId}`)}
    >
      <div className="flex items-start justify-between mb-2.5">
        <div
          className={cn(
            "w-[34px] h-[34px] rounded-lg flex items-center justify-center text-[14px] font-extrabold font-manrope",
            status === "cv_ready"    ? "bg-[#e6f4ea] text-[#1e6b3a]" :
            status === "interrupted" ? "bg-[#fff3cc] text-[#584400]" :
            status === "tracking"    ? "bg-gray-100 text-gray-500" :
                                       "bg-[#eef1ff] text-[#003399]"
          )}
        >
          {initial}
        </div>
        <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide", chip.className)}>
          {chip.label}
        </span>
      </div>

      <p className="text-[14px] font-bold text-gray-900 font-manrope leading-snug truncate">
        {roleTitle ?? "Unknown role"}
      </p>
      <p className="text-[12px] text-gray-500 mt-0.5 truncate">{companyName ?? ""}</p>

      {/* Progress bar */}
      <div className="h-1 bg-gray-100 rounded-full mt-3 mb-3 overflow-hidden">
        <div
          className={cn("h-1 rounded-full", PROGRESS_COLOR[status])}
          style={{ width: `${PROGRESS[status]}%` }}
        />
      </div>

      <div className="flex items-center justify-between">
        <span className="text-[11.5px] text-gray-400">{relativeTime}</span>
        <button
          onClick={handleAction}
          className={cn(
            "text-[12px] font-bold px-3 py-1.5 rounded-lg flex items-center gap-1 transition-colors",
            status === "cv_ready"
              ? "bg-[#dcfce7] text-[#166534] hover:bg-[#bbf7d0]"
              : "bg-[#002068] text-white hover:bg-[#003399]"
          )}
        >
          <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
            {status === "cv_ready" ? "open_in_new" : status === "tracking" ? "bolt" : "play_arrow"}
          </span>
          {ACTION_LABEL[status]}
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "DashboardApplication\|error" | head -20
```

Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/components/dashboard/DashboardApplicationCard.tsx
git commit -m "feat(dashboard): add DashboardApplicationCard with status-derived styling"
```

---

## Task 11: Dashboard page

**Files:**
- Modify: `frontend/app/(shell)/dashboard/page.tsx`

- [ ] **Step 1: Replace placeholder with full dashboard**

Replace the contents of `frontend/app/(shell)/dashboard/page.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { AppTopbar } from "@/components/shell/AppTopbar";
import { QuickTailorWidget } from "@/components/dashboard/QuickTailorWidget";
import { ProfileStrengthCard } from "@/components/dashboard/ProfileStrengthCard";
import { DashboardApplicationCard } from "@/components/dashboard/DashboardApplicationCard";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";
const MAX_CARDS = 6;

interface Application {
  id: string;
  role_title: string | null;
  company_name: string | null;
  workflow_status: string;
  flow_session_id: string | null;
  updated_at: string;
}

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const router = useRouter();
  const [applications, setApplications] = useState<Application[]>([]);
  const [userName, setUserName] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [appsRes, profileRes] = await Promise.all([
          fetch(`${API_BASE}/api/applications`),
          fetch(`${API_BASE}/api/profile`),
        ]);
        if (appsRes.ok) {
          const d = await appsRes.json();
          setApplications(d.items ?? []);
        }
        if (profileRes.ok) {
          const d = await profileRes.json();
          setUserName(d.profile?.personal_info?.name ?? null);
        }
      } catch {
        // non-fatal
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  async function handleStartFlow(appId: string) {
    try {
      const res = await fetch(`${API_BASE}/api/applications/${appId}/start`, { method: "POST" });
      if (res.ok) {
        const d = await res.json();
        if (d.flow_session_id) router.push(`/flow/${d.flow_session_id}/import`);
      }
    } catch {
      // non-fatal
    }
  }

  const firstName = userName?.split(" ")[0] ?? null;
  const inProgress = applications.filter((a) => a.workflow_status !== "none").length;

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <AppTopbar />

      <main className="flex-1 overflow-y-auto px-8 py-7">
        {/* Page header */}
        <div className="mb-5">
          <h1 className="text-[22px] font-extrabold text-[#141b2b] font-manrope tracking-tight">
            {firstName ? `Welcome back, ${firstName} 👋` : t("welcomeBack")}
          </h1>
          <p className="text-[13px] text-gray-500 mt-0.5">
            {inProgress} active {inProgress === 1 ? "application" : "applications"}
          </p>
        </div>

        {/* Top row: Quick Tailor + Profile Strength */}
        <div className="grid grid-cols-[1fr_260px] gap-4 mb-6">
          <QuickTailorWidget />
          <ProfileStrengthCard />
        </div>

        {/* Active applications */}
        <div className="flex items-center justify-between mb-3.5">
          <h2 className="text-[15px] font-extrabold text-[#141b2b] font-manrope">
            {t("activeApplications", { count: applications.length })}
          </h2>
          {applications.length > MAX_CARDS && (
            <button
              onClick={() => router.push("/documents")}
              className="text-[12px] font-bold text-[#3557bc] hover:underline"
            >
              View all in My Documents →
            </button>
          )}
        </div>

        {loading ? (
          <div className="grid grid-cols-2 gap-3.5">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-36 bg-white rounded-xl border border-gray-200 animate-pulse" />
            ))}
          </div>
        ) : applications.length === 0 ? (
          <div className="flex items-center justify-center h-40 bg-white rounded-xl border border-dashed border-gray-300">
            <p className="text-[13px] text-gray-400">{t("noApplications")}</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3.5">
            {applications.slice(0, MAX_CARDS).map((app) => (
              <DashboardApplicationCard
                key={app.id}
                applicationId={app.id}
                roleTitle={app.role_title}
                companyName={app.company_name}
                workflowStatus={app.workflow_status}
                flowSessionId={app.flow_session_id}
                updatedAt={app.updated_at}
                onStartFlow={() => handleStartFlow(app.id)}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
```

- [ ] **Step 2: Start dev server and verify dashboard renders**

```bash
cd frontend && npm run dev &
sleep 5
# Open http://localhost:3000 in a browser — should redirect to /dashboard
# /dashboard should show the sidebar + Quick Tailor + Profile Strength card + application grid
kill %1
```

Expected: page loads without runtime errors; sidebar is visible on the left; Quick Tailor widget shows URL/Text tabs.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/\(shell\)/dashboard/page.tsx
git commit -m "feat(dashboard): build Dashboard page with QuickTailor, ProfileStrength, and application grid"
```

---

## Task 12: DocumentsTable + My Documents page

**Files:**
- Create: `frontend/components/documents/DocumentsTable.tsx`
- Modify: `frontend/app/(shell)/documents/page.tsx`

- [ ] **Step 1: Create `frontend/components/documents/DocumentsTable.tsx`**

```tsx
"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";

export interface DocumentItem {
  cv_id: string;
  flow_id: string | null;
  role_title: string | null;
  company_name: string | null;
  template: string;
  status: "ready" | "generating" | "expired" | "pending" | "failed";
  created_at: string;
  expires_at: string;
}

type StatusFilter = "all" | "ready" | "generating" | "expiring";
type SortMode = "newest" | "oldest" | "company";

const TEMPLATE_LABELS: Record<string, string> = {
  classic_german:   "Classic German",
  modern_swiss:     "Modern Swiss",
  executive:        "Executive",
  tech_developer:   "Tech Developer",
  creative_sidebar: "Creative Sidebar",
  academic:         "Academic",
  compact_pro:      "Compact Pro",
};

function daysUntilExpiry(expiresAt: string): number {
  return Math.ceil((new Date(expiresAt).getTime() - Date.now()) / 864e5);
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("de-DE", { day: "numeric", month: "short", year: "numeric" });
}

interface DocumentsTableProps {
  items: DocumentItem[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (p: number) => void;
}

export function DocumentsTable({ items, total, page, pageSize, onPageChange }: DocumentsTableProps) {
  const t = useTranslations("documents");
  const router = useRouter();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [sort, setSort] = useState<SortMode>("newest");

  const filtered = useMemo(() => {
    let rows = [...items];

    // Status filter
    if (statusFilter === "ready")      rows = rows.filter((r) => r.status === "ready");
    if (statusFilter === "generating") rows = rows.filter((r) => r.status === "generating" || r.status === "pending");
    if (statusFilter === "expiring")   rows = rows.filter((r) => r.status === "ready" && daysUntilExpiry(r.expires_at) <= 7);

    // Text search
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      rows = rows.filter(
        (r) =>
          (r.role_title ?? "").toLowerCase().includes(q) ||
          (r.company_name ?? "").toLowerCase().includes(q)
      );
    }

    // Sort
    if (sort === "oldest")  rows.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    if (sort === "company") rows.sort((a, b) => (a.company_name ?? "").localeCompare(b.company_name ?? ""));
    // newest is default order from API

    return rows;
  }, [items, statusFilter, searchQuery, sort]);

  const totalPages = Math.ceil(total / pageSize);
  const from = (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div>
      {/* Filter bar */}
      <div className="flex items-center gap-2.5 mb-3.5 flex-wrap">
        {(["all", "ready", "generating", "expiring"] as StatusFilter[]).map((f) => (
          <button
            key={f}
            onClick={() => setStatusFilter(f)}
            className={cn(
              "px-3.5 py-1 rounded-full text-[12px] font-bold border-[1.5px] transition-colors",
              statusFilter === f
                ? "bg-[#003399] text-white border-[#003399]"
                : "bg-white text-gray-500 border-gray-200 hover:border-[#b5c4ff] hover:text-[#003399]"
            )}
          >
            {t(f === "all" ? "filterAll" : f === "ready" ? "filterReady" : f === "generating" ? "filterGenerating" : "filterExpiring")}
          </button>
        ))}

        {/* Text search */}
        <div className="flex items-center gap-1.5 bg-white border-[1.5px] border-gray-200 rounded-full px-3.5 py-1 focus-within:border-[#003399] focus-within:ring-2 focus-within:ring-[#003399]/8 transition-all">
          <span className="material-symbols-outlined text-gray-400" style={{ fontSize: 15 }}>search</span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={t("searchPlaceholder")}
            className="border-none outline-none bg-transparent text-[12px] text-gray-800 placeholder:text-gray-400 w-36"
          />
        </div>

        <div className="flex-1" />

        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as SortMode)}
          className="text-[12px] text-gray-500 border-[1.5px] border-gray-200 rounded-lg px-2.5 py-1 bg-white outline-none cursor-pointer"
        >
          <option value="newest">{t("sortNewest")}</option>
          <option value="oldest">{t("sortOldest")}</option>
          <option value="company">{t("sortCompany")}</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-[14px] border-[1.5px] border-gray-200 overflow-hidden">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-[#f9f9ff] border-b-[1.5px] border-gray-100">
              <th className="text-left px-4 py-2.5 text-[11px] font-bold text-gray-500 uppercase tracking-wider">{t("colDocument")}</th>
              <th className="text-left px-4 py-2.5 text-[11px] font-bold text-gray-500 uppercase tracking-wider">{t("colTemplate")}</th>
              <th className="text-left px-4 py-2.5 text-[11px] font-bold text-gray-500 uppercase tracking-wider">{t("colStatus")}</th>
              <th className="text-left px-4 py-2.5 text-[11px] font-bold text-gray-500 uppercase tracking-wider">{t("colExpires")}</th>
              <th className="px-4 py-2.5" />
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center py-12 text-[13px] text-gray-400">
                  {t("noDocuments")}
                </td>
              </tr>
            ) : (
              filtered.map((item) => {
                const days = daysUntilExpiry(item.expires_at);
                const isReady = item.status === "ready";
                const isGenerating = item.status === "generating" || item.status === "pending";
                return (
                  <tr
                    key={item.cv_id}
                    className="border-b border-gray-50 last:border-none hover:bg-[#f5f7ff] transition-colors cursor-pointer group"
                  >
                    {/* Document */}
                    <td className="px-4 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          "w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0",
                          isGenerating ? "bg-amber-50" : "bg-[#e9edff]"
                        )}>
                          <span
                            className="material-symbols-outlined"
                            style={{ fontSize: 20, color: isGenerating ? "#8b5000" : "#003399" }}
                          >
                            description
                          </span>
                        </div>
                        <div>
                          <p className="text-[13.5px] font-semibold text-gray-900 leading-tight">
                            {item.role_title ?? "Unknown role"}
                          </p>
                          <p className="text-[11.5px] text-gray-500 mt-0.5">
                            {item.company_name ?? ""} · {t("generatedOn", { date: formatDate(item.created_at) })}
                          </p>
                        </div>
                      </div>
                    </td>

                    {/* Template */}
                    <td className="px-4 py-3.5">
                      <span className="text-[11px] font-semibold px-2 py-1 rounded-md bg-[#f1f3ff] text-gray-600">
                        {TEMPLATE_LABELS[item.template] ?? item.template}
                      </span>
                    </td>

                    {/* Status */}
                    <td className="px-4 py-3.5">
                      {isReady && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-1 rounded-full bg-[#e6f4ea] text-[#1e6b3a]">
                          <span className="material-symbols-outlined" style={{ fontSize: 13 }}>check_circle</span>
                          {t("statusReady")}
                        </span>
                      )}
                      {isGenerating && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-1 rounded-full bg-amber-50 text-amber-700">
                          <span className="material-symbols-outlined" style={{ fontSize: 13 }}>hourglass_top</span>
                          {t("statusGenerating")}
                        </span>
                      )}
                      {item.status === "expired" && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-1 rounded-full bg-gray-100 text-gray-500">
                          {t("statusExpired")}
                        </span>
                      )}
                    </td>

                    {/* Expires */}
                    <td className="px-4 py-3.5">
                      {isReady && days <= 7 ? (
                        <span className="flex items-center gap-1 text-[12px] font-semibold text-amber-600">
                          <span className="material-symbols-outlined" style={{ fontSize: 14 }}>warning</span>
                          {days <= 0 ? t("expiresToday") : t("expiresIn", { days })}
                        </span>
                      ) : isReady ? (
                        <span className="text-[12px] text-gray-500">{formatDate(item.expires_at)}</span>
                      ) : (
                        <span className="text-[12px] text-gray-300">—</span>
                      )}
                    </td>

                    {/* Action */}
                    <td className="px-4 py-3.5 text-right">
                      {isReady && item.flow_id ? (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/flow/${item.flow_id}/cv`);
                          }}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 border-[1.5px] border-gray-200 rounded-lg text-[12px] font-semibold text-gray-600 hover:border-[#003399] hover:text-[#003399] hover:bg-[#f1f3ff] transition-all"
                        >
                          <span className="material-symbols-outlined" style={{ fontSize: 15 }}>open_in_new</span>
                          {t("openButton")}
                        </button>
                      ) : isGenerating ? (
                        <button
                          disabled
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 border-[1.5px] border-gray-200 rounded-lg text-[12px] font-semibold text-gray-400 opacity-50 cursor-not-allowed"
                        >
                          <span className="material-symbols-outlined" style={{ fontSize: 15 }}>hourglass_top</span>
                          {t("generatingButton")}
                        </button>
                      ) : null}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {total > pageSize && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 text-[12px] text-gray-500">
            <span>{t("showing", { from, to, total })}</span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => onPageChange(page - 1)}
                disabled={page === 1}
                className="w-[30px] h-[30px] rounded-md border-[1.5px] border-gray-200 flex items-center justify-center disabled:opacity-40 hover:border-[#003399] hover:text-[#003399] transition-colors"
              >
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>chevron_left</span>
              </button>
              {[...Array(totalPages)].map((_, i) => (
                <button
                  key={i}
                  onClick={() => onPageChange(i + 1)}
                  className={cn(
                    "w-[30px] h-[30px] rounded-md border-[1.5px] text-[12px] font-semibold transition-colors",
                    page === i + 1
                      ? "bg-[#003399] text-white border-[#003399]"
                      : "border-gray-200 text-gray-500 hover:border-[#003399] hover:text-[#003399]"
                  )}
                >
                  {i + 1}
                </button>
              ))}
              <button
                onClick={() => onPageChange(page + 1)}
                disabled={page === totalPages}
                className="w-[30px] h-[30px] rounded-md border-[1.5px] border-gray-200 flex items-center justify-center disabled:opacity-40 hover:border-[#003399] hover:text-[#003399] transition-colors"
              >
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>chevron_right</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Replace placeholder in `frontend/app/(shell)/documents/page.tsx`**

```tsx
"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { AppTopbar } from "@/components/shell/AppTopbar";
import { DocumentsTable, type DocumentItem } from "@/components/documents/DocumentsTable";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";
const PAGE_SIZE = 10;

export default function DocumentsPage() {
  const t = useTranslations("documents");
  const [items, setItems] = useState<DocumentItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [searchValue, setSearchValue] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const res = await fetch(
          `${API_BASE}/api/documents?page=${page}&page_size=${PAGE_SIZE}`
        );
        if (res.ok) {
          const d = await res.json();
          setItems(d.items ?? []);
          setTotal(d.total ?? 0);
        }
      } catch {
        // non-fatal
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [page]);

  const expiringCount = items.filter(
    (i) => i.status === "ready" && Math.ceil((new Date(i.expires_at).getTime() - Date.now()) / 864e5) <= 7
  ).length;

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <AppTopbar
        showSearch
        searchValue={searchValue}
        onSearchChange={setSearchValue}
        searchPlaceholder={t("searchPlaceholder")}
      />

      <main className="flex-1 overflow-y-auto px-8 py-7">
        <div className="mb-5">
          <h1 className="text-[22px] font-extrabold text-[#141b2b] font-manrope">{t("title")}</h1>
          <p className="text-[13px] text-gray-500 mt-0.5">{t("subtitle")}</p>
        </div>

        {/* Stats strip */}
        <div className="grid grid-cols-3 gap-3.5 mb-5">
          {[
            { icon: "description", label: t("totalDocs"),     value: total,         bg: "bg-[#e9edff]", iconColor: "#003399" },
            { icon: "schedule",    label: t("expiringCount"),  value: expiringCount, bg: "bg-amber-50",  iconColor: "#8b5000" },
          ].map(({ icon, label, value, bg, iconColor }) => (
            <div key={label} className="bg-white rounded-xl border-[1.5px] border-gray-200 px-4 py-3.5 flex items-center gap-3.5">
              <div className={`w-10 h-10 rounded-[10px] ${bg} flex items-center justify-center flex-shrink-0`}>
                <span className="material-symbols-outlined" style={{ fontSize: 22, color: iconColor }}>{icon}</span>
              </div>
              <div>
                <p className="text-[24px] font-extrabold text-gray-900 font-manrope leading-none">{value}</p>
                <p className="text-[12px] text-gray-500 mt-0.5">{label}</p>
              </div>
            </div>
          ))}
        </div>

        {loading ? (
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-14 bg-white rounded-xl border border-gray-200 animate-pulse" />
            ))}
          </div>
        ) : (
          <DocumentsTable
            items={items}
            total={total}
            page={page}
            pageSize={PAGE_SIZE}
            onPageChange={setPage}
          />
        )}
      </main>
    </div>
  );
}
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "DocumentsTable\|DocumentsPage\|error" | head -20
```

Expected: no errors

- [ ] **Step 4: Start dev server and verify My Documents renders**

```bash
cd frontend && npm run dev &
sleep 5
# Navigate to http://localhost:3000/documents
# Should show sidebar, topbar with search, stats strip, and table
kill %1
```

- [ ] **Step 5: Commit**

```bash
git add frontend/components/documents/DocumentsTable.tsx \
        frontend/app/\(shell\)/documents/page.tsx
git commit -m "feat(documents): add DocumentsTable component and My Documents page"
```

---

## Task 13: Frontend unit tests (Vitest)

**Files:**
- Create: `frontend/components/dashboard/__tests__/QuickTailorWidget.test.tsx`
- Create: `frontend/components/documents/__tests__/DocumentsTable.test.tsx`

- [ ] **Step 1: Create `frontend/components/dashboard/__tests__/QuickTailorWidget.test.tsx`**

```tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QuickTailorWidget } from "../QuickTailorWidget";

// next-intl mock
vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("QuickTailorWidget", () => {
  it("renders URL tab by default", () => {
    render(<QuickTailorWidget />);
    expect(screen.getByPlaceholderText("urlPlaceholder")).toBeInTheDocument();
  });

  it("switches to text textarea when Paste Text tab is clicked", () => {
    render(<QuickTailorWidget />);
    fireEvent.click(screen.getByText("tabText"));
    expect(screen.getByPlaceholderText("textPlaceholder")).toBeInTheDocument();
  });

  it("Analyse button is disabled when input is empty", () => {
    render(<QuickTailorWidget />);
    expect(screen.getByText("analyseButton")).toBeDisabled();
  });

  it("Analyse button enables when URL is typed", () => {
    render(<QuickTailorWidget />);
    fireEvent.change(screen.getByPlaceholderText("urlPlaceholder"), {
      target: { value: "https://example.de/job/123" },
    });
    expect(screen.getByText("analyseButton")).not.toBeDisabled();
  });

  it("shows error message on API failure", async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: "Bad URL" }),
    });
    render(<QuickTailorWidget />);
    fireEvent.change(screen.getByPlaceholderText("urlPlaceholder"), {
      target: { value: "https://example.de/job" },
    });
    fireEvent.click(screen.getByText("analyseButton"));
    await waitFor(() => expect(screen.getByText("Bad URL")).toBeInTheDocument());
  });
});
```

- [ ] **Step 2: Create `frontend/components/documents/__tests__/DocumentsTable.test.tsx`**

```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DocumentsTable, type DocumentItem } from "../DocumentsTable";

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, params?: Record<string, unknown>) => {
    if (params) return `${key}:${JSON.stringify(params)}`;
    return key;
  },
}));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const FAR_FUTURE = new Date(Date.now() + 60 * 24 * 36e5).toISOString();
const NEAR_FUTURE = new Date(Date.now() + 3 * 24 * 36e5).toISOString();

const ITEMS: DocumentItem[] = [
  {
    cv_id: "cv-1",
    flow_id: "flow-1",
    role_title: "Head of Validation",
    company_name: "Roche",
    template: "classic_german",
    status: "ready",
    created_at: new Date().toISOString(),
    expires_at: FAR_FUTURE,
  },
  {
    cv_id: "cv-2",
    flow_id: "flow-2",
    role_title: "QA Lead",
    company_name: "Bayer",
    template: "modern_swiss",
    status: "ready",
    created_at: new Date().toISOString(),
    expires_at: NEAR_FUTURE,
  },
  {
    cv_id: "cv-3",
    flow_id: null,
    role_title: "Director of QA",
    company_name: "Novartis",
    template: "classic_german",
    status: "generating",
    created_at: new Date().toISOString(),
    expires_at: FAR_FUTURE,
  },
];

function renderTable(overrides?: Partial<React.ComponentProps<typeof DocumentsTable>>) {
  return render(
    <DocumentsTable
      items={ITEMS}
      total={3}
      page={1}
      pageSize={10}
      onPageChange={vi.fn()}
      {...overrides}
    />
  );
}

describe("DocumentsTable", () => {
  it("renders all rows by default", () => {
    renderTable();
    expect(screen.getByText("Head of Validation")).toBeInTheDocument();
    expect(screen.getByText("QA Lead")).toBeInTheDocument();
    expect(screen.getByText("Director of QA")).toBeInTheDocument();
  });

  it("text search filters rows by company", () => {
    renderTable();
    fireEvent.change(screen.getByPlaceholderText("searchPlaceholder"), {
      target: { value: "Roche" },
    });
    expect(screen.getByText("Head of Validation")).toBeInTheDocument();
    expect(screen.queryByText("QA Lead")).not.toBeInTheDocument();
  });

  it("text search is case-insensitive", () => {
    renderTable();
    fireEvent.change(screen.getByPlaceholderText("searchPlaceholder"), {
      target: { value: "bayer" },
    });
    expect(screen.getByText("QA Lead")).toBeInTheDocument();
    expect(screen.queryByText("Head of Validation")).not.toBeInTheDocument();
  });

  it("Generating filter hides ready rows", () => {
    renderTable();
    fireEvent.click(screen.getByText("filterGenerating"));
    expect(screen.getByText("Director of QA")).toBeInTheDocument();
    expect(screen.queryByText("Head of Validation")).not.toBeInTheDocument();
  });

  it("Expiring filter shows only rows expiring within 7 days", () => {
    renderTable();
    fireEvent.click(screen.getByText("filterExpiring"));
    expect(screen.getByText("QA Lead")).toBeInTheDocument();
    expect(screen.queryByText("Head of Validation")).not.toBeInTheDocument();
  });

  it("Open button is disabled for generating rows", () => {
    renderTable();
    const buttons = screen.getAllByRole("button");
    const generatingBtn = buttons.find((b) => b.textContent?.includes("generatingButton"));
    expect(generatingBtn).toBeDisabled();
  });
});
```

- [ ] **Step 3: Run Vitest tests**

```bash
cd frontend && npm test -- --reporter verbose 2>&1 | grep -E "PASS|FAIL|✓|✗|QuickTailor|DocumentsTable" | head -30
```

Expected: all tests in both files `PASS`

- [ ] **Step 4: Commit**

```bash
git add frontend/components/dashboard/__tests__/QuickTailorWidget.test.tsx \
        frontend/components/documents/__tests__/DocumentsTable.test.tsx
git commit -m "test(frontend): add Vitest tests for QuickTailorWidget and DocumentsTable"
```

---

## Task 14: Backend unit tests — full coverage

**Files:**
- Modify: `tests/unit/test_sprint29_documents.py`

- [ ] **Step 1: Run all sprint 29 backend tests**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_sprint29_documents.py -v
```

Expected: all 6 tests `PASSED`

- [ ] **Step 2: Run full backend unit test suite to check for regressions**

```bash
pytest tests/unit/ -v --cov=applire --cov-report=term-missing 2>&1 | tail -30
```

Expected: coverage ≥ 75%, no test failures outside of pre-existing skips

- [ ] **Step 3: Commit if any fixes were needed**

```bash
git add tests/unit/test_sprint29_documents.py
git commit -m "test(backend): verify full unit test suite passes with ≥75% coverage"
```

---

## Task 15: E2E tests

**Files:**
- Create: `tests/e2e/sprint29-dashboard.spec.ts`

- [ ] **Step 1: Start full stack**

```bash
cd /home/apliqa/Documents/Applire/Solution
docker-compose up -d
sleep 10
```

- [ ] **Step 2: Create `tests/e2e/sprint29-dashboard.spec.ts`**

```typescript
import { test, expect } from "@playwright/test";

test.describe("Sprint 29 — Power User Dashboard", () => {

  test("returning user is redirected to /dashboard", async ({ page }) => {
    // Set up: ensure a profile exists (via stub user from fixture)
    await page.goto("/");
    // Either lands on /dashboard immediately or shows loading then redirects
    await page.waitForURL("**/dashboard", { timeout: 8000 });
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("sidebar renders with all four nav items", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.getByRole("button", { name: /Dashboard/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Profile|Masterprofil/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Documents|Dokumente/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Settings|Einstellungen/i })).toBeVisible();
  });

  test("Quick Tailor widget has URL and Text tabs", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.getByText(/Quick Tailor/i)).toBeVisible();
    await expect(page.getByText(/Job URL|Job-URL/i)).toBeVisible();
    await expect(page.getByText(/Paste Text|Text einfügen/i)).toBeVisible();
  });

  test("Quick Tailor text tab shows textarea", async ({ page }) => {
    await page.goto("/dashboard");
    await page.click("text=/Paste Text|Text einfügen/");
    await expect(page.locator("textarea")).toBeVisible();
  });

  test("sidebar active item highlights on navigation", async ({ page }) => {
    await page.goto("/dashboard");
    await page.click("text=/Documents|Meine Dokumente/");
    await page.waitForURL("**/documents");
    // The Documents nav item should have the active style (bg-[#eef1ff])
    const docsBtn = page.getByRole("button", { name: /Documents|Meine Dokumente/i });
    await expect(docsBtn).toHaveClass(/bg-\[#eef1ff\]|font-bold/);
  });

  test("My Documents page loads with stats strip and table", async ({ page }) => {
    await page.goto("/documents");
    // Stats strip labels visible
    await expect(page.getByText(/Total documents|Dokumente gesamt/i)).toBeVisible();
    await expect(page.getByText(/Expiring|Ablaufend/i)).toBeVisible();
    // Table headers
    await expect(page.getByText(/Document|Dokument/i).first()).toBeVisible();
  });

  test("My Documents text filter hides non-matching rows", async ({ page }) => {
    // Only run if there are documents; skip gracefully if table is empty
    await page.goto("/documents");
    const rows = page.locator("tbody tr");
    const count = await rows.count();
    if (count < 2) {
      test.skip();
      return;
    }
    const firstRole = await rows.first().locator("td").first().innerText();
    const searchInput = page.getByPlaceholder(/Filter by role|Nach Stelle/i);
    await searchInput.fill("XXXXXXXXXNOTFOUND");
    await expect(page.getByText(/No documents|Noch keine/i)).toBeVisible();
    await searchInput.fill("");
    await expect(rows.first()).toBeVisible();
  });

  test("Open button on a ready document navigates to flow CV page", async ({ page }) => {
    await page.goto("/documents");
    const openBtn = page.getByRole("button", { name: /^Open$|^Öffnen$/i }).first();
    if (await openBtn.isVisible()) {
      await openBtn.click();
      await expect(page).toHaveURL(/\/flow\/.+\/cv/);
    }
  });

});
```

- [ ] **Step 3: Run E2E tests**

```bash
cd /home/apliqa/Documents/Applire/Solution
npx playwright test tests/e2e/sprint29-dashboard.spec.ts --reporter=list
```

Expected: all tests pass (or skip gracefully if no data)

- [ ] **Step 4: Commit**

```bash
git add tests/e2e/sprint29-dashboard.spec.ts
git commit -m "test(e2e): add Sprint 29 dashboard and My Documents E2E tests"
```

---

## Task 16: Cleanup

**Files:**
- Delete: `frontend/components/dashboard/Dashboard.tsx`
- Delete: `frontend/components/dashboard/NewApplicationModal.tsx`

- [ ] **Step 1: Verify nothing imports the old files**

```bash
cd frontend && grep -rn "from.*Dashboard\b\|from.*NewApplicationModal" --include="*.tsx" --include="*.ts" app/ components/ | grep -v "__tests__"
```

Expected: no results (the root `app/page.tsx` should have already had these imports removed in Task 7)

- [ ] **Step 2: Delete old files**

```bash
rm frontend/components/dashboard/Dashboard.tsx
rm frontend/components/dashboard/NewApplicationModal.tsx
```

- [ ] **Step 3: Run TypeScript check**

```bash
cd frontend && npx tsc --noEmit 2>&1 | grep "error" | head -20
```

Expected: no errors

- [ ] **Step 4: Run full test suite one final time**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/ -v --cov=applire --cov-fail-under=75 -q
cd frontend && npm test -- --reporter verbose 2>&1 | tail -20
```

Expected: backend ≥ 75% coverage, all Vitest tests pass

- [ ] **Step 5: Commit**

```bash
git add -u frontend/components/dashboard/Dashboard.tsx \
           frontend/components/dashboard/NewApplicationModal.tsx
git commit -m "chore: remove Dashboard.tsx and NewApplicationModal.tsx (replaced by shell dashboard)"
```

---

## Task 17: Documentation updates

**Files:**
- Modify: `Documents/Product Specifications/Personas/poweruser.md`
- Modify: `Documents/Product Specifications/Epic_and_User_Story_Tracker.csv`
- Modify: `Documents/Architecture/arc42.md`
- Modify: `Documents/Architecture/ADR.md`

> Note: `Documents/` is synced to Nextcloud and is **not** committed to git. Do not run `git add` on any of these files.

- [ ] **Step 1: Update Emma's user journey (poweruser.md)**

Open `Documents/Product Specifications/Personas/poweruser.md` and apply these changes:

1. **Touchpoint Inventory** — update the Dashboard row and add My Documents row:

| Screen/Component | Purpose | Emma Interaction | Technical Reference |
|---|---|---|---|
| Dashboard | Landing, personalized greeting, Quick Tailor widget, Profile Strength card, active applications grid | Paste JD URL or text directly in Quick Tailor, resume in-progress flows | `GET /api/profile/exists`, `GET /api/applications`, `POST /api/job/analyze`, `POST /api/applications` |
| My Documents | All generated CV artifacts with status, expiry, filter/search | Browse past CVs, open CV preview, track expiry | `GET /api/documents` |
| Navigation Shell | Persistent 240px sidebar with Dashboard / Profile / My Documents / Settings links | Click sidebar nav items | `AppSidebar`, `AppTopbar` |

2. **Happy Path Flow** — replace "JD Input Modal" reference with "Quick Tailor widget (inline on dashboard)":

```
Emma opens Applire → Dashboard loads with personalized greeting and profile completeness card.
She pastes a JD URL directly into the Quick Tailor widget (inline on dashboard, no modal).
The system scrapes and analyzes the JD, creates an application, and redirects her to the flow.
...
After CV download, the flow marks complete and the dashboard application card updates to "CV Ready".
Past generated CVs are accessible in My Documents (sidebar nav).
```

3. **Open Questions** — resolve Q1:

```
1 | Dashboard layout: Does Emma see a "quick action" panel (New Application) or a full pipeline view first?
  → RESOLVED (Sprint 29): Inline Quick Tailor widget at top of dashboard, Profile Strength card beside it,
    active application grid below. No modal.
```

- [ ] **Step 2: Update Epic and User Story Tracker (CSV)**

Open `Documents/Product Specifications/Epic_and_User_Story_Tracker.csv` and add the following rows (or update existing ones if a matching epic/story is found):

```
E009,Navigation Shell & Power User Dashboard,Emma (Returning Power User),US041,Persistent navigation shell,"As a returning user, I want a persistent sidebar so I can navigate between Dashboard, My Documents, Profile, and Settings without losing context.","- 240px labeled sidebar renders on all authenticated pages
- Active page highlighted with teal left border
- Sidebar shows on desktop; mobile support deferred
- Implemented as Next.js (shell) route group",High,Done,5,Sprint 29,
E009,Navigation Shell & Power User Dashboard,Emma (Returning Power User),US042,Inline Quick Tailor widget,"As a power user, I want to paste a JD URL or text directly on the dashboard without opening a modal, so I can start a new application with fewer clicks.","- Quick Tailor widget replaces New Application modal on dashboard
- URL and Text tabs available
- Submitting analyzes JD, creates application, and navigates to flow
- Duplicate application returns 409 with inline error",High,Done,3,Sprint 29,
E009,Navigation Shell & Power User Dashboard,Emma (Returning Power User),US043,Profile Strength card,"As a returning user, I want to see my profile completeness at a glance on the dashboard so I know if I need to update it before tailoring.","- Card shows percentage score from GET /api/profile/exists
- Visual indicator (color-coded) for low/medium/high completeness
- Links to /profile for editing",Medium,Done,2,Sprint 29,
E009,Navigation Shell & Power User Dashboard,Emma (Returning Power User),US044,My Documents page,"As a power user managing multiple applications, I want a dedicated page listing all my generated CVs with status and expiry dates so I can find and re-open any past CV.","- Table shows: role title, company, template, status, expiry date, Open button
- Filter by status chip (All / Ready / Generating / Expiring Soon)
- Text search filters by role title or company name
- Sort by created date (newest first by default)
- Expiry warning (amber) for CVs expiring within 7 days
- Open button navigates to /flow/[flowId]/cv
- Powered by GET /api/documents",High,Done,5,Sprint 29,
```

- [ ] **Step 3: Add ADR entry (ADR.md)**

Open `Documents/Architecture/ADR.md` and append the following ADR:

```markdown
## ADR-0XX: Next.js (shell) Route Group for Navigation Shell

**Date:** 2026-04-24
**Status:** Accepted
**Sprint:** 29

### Context
Sprint 29 introduced a persistent navigation shell (240px sidebar + 52px topbar) required across all authenticated pages. The previous architecture had pages at top-level (`/profile`, `/settings`, `/flow/[flowId]`) with no shared authenticated layout. A mechanism was needed to wrap all authenticated pages in the shell without affecting URL structure.

### Decision
Use a Next.js App Router **route group** `(shell)` to own a `layout.tsx` that renders `<AppSidebar>` and `<AppTopbar>`. All authenticated pages (dashboard, profile, settings, flow, applications, documents) move inside `app/(shell)/`. The route group parentheses are invisible in URLs, so `/dashboard`, `/profile`, etc. remain unchanged. Old top-level page files are replaced with redirect stubs to avoid 404s during migration.

### Consequences
- **Positive:** Clean separation between authenticated shell layout and unauthenticated pages (onboarding, root landing). Easy to extend — new authenticated pages just go inside `(shell)/`.
- **Positive:** No URL changes for existing bookmarks or external links.
- **Negative:** Requires moving/recreating files for every page; redirect stubs add minor boilerplate.
- **Neutral:** The existing flow layout (`flow/[flowId]/layout.tsx`) sits inside the shell group but continues to render its own step-tracker topbar; the shell topbar is still rendered above it via the group layout.

### Alternatives Considered
- **Middleware-based redirect** to inject shell: rejected — would require client-side shell injection or server component gymnastics.
- **Top-level `layout.tsx` for all pages:** rejected — unauthenticated pages (onboarding, `/`) would inherit the shell.
```

Replace `ADR-0XX` with the next sequential ADR number found at the end of `ADR.md`.

- [ ] **Step 4: Update arc42 (arc42.md)**

Open `Documents/Architecture/arc42.md` and update the following sections:

1. **Section 5 (Building Block View) — Frontend:**
   Add `AppSidebar` and `AppTopbar` as new shell components. Add `(shell)` route group entry. Add `QuickTailorWidget`, `ProfileStrengthCard`, `DashboardApplicationCard`, `DocumentsTable` to the component inventory.

2. **Section 6 (Runtime View) — or equivalent "New Application" flow:**
   Update to show the Quick Tailor widget as the entry point instead of NewApplicationModal. The flow is: Dashboard (`QuickTailorWidget`) → `POST /api/job/analyze` → `POST /api/applications` → `GET /flow/[flowId]`.

3. **Section 8 (Cross-Cutting Concepts) — or Data Retention:**
   Add note about `GET /api/documents` joining `generated_cvs → applications` on `job_analysis_id` to surface per-user CV artifacts with role metadata. Cross-reference GDPR TTL (90-day CV expiry, expiry warnings at ≤7 days).

4. **Navigation Architecture (if present as a dedicated section or ADR reference):**
   Update to reflect the `(shell)` route group decision (ADR-0XX from Step 3 above).

- [ ] **Step 5: Confirm no git commits for Documents/**

```bash
git status Documents/
```

Expected: `Documents/` does not appear in `git status` output (it is excluded from git tracking per project conventions).

---

## Self-Review Checklist

**Spec coverage:**
- [x] (shell) route group with layout.tsx — Task 7
- [x] AppSidebar — Task 5
- [x] AppTopbar — Task 6
- [x] Dashboard page (greeting, Quick Tailor, Profile Strength, app grid) — Tasks 8–11
- [x] QuickTailorWidget with URL/Text tabs — Task 8
- [x] ProfileStrengthCard from profile/exists + profile API — Task 9
- [x] DashboardApplicationCard (5 states, correct navigation) — Task 10
- [x] My Documents page with stats, filter bar, table — Task 12
- [x] DocumentsTable text search + chip filter + sort — Task 12
- [x] Open button → /flow/[flowId]/cv — Task 12
- [x] Expiry warning ≤ 7 days — Task 12
- [x] GET /api/documents — Tasks 1–3
- [x] profile/settings page moves — Task 7
- [x] root page redirect — Task 7
- [x] NewApplicationModal removed — Task 16
- [x] i18n strings — Task 4
- [x] Backend unit tests — Tasks 1–2, 14
- [x] Frontend Vitest tests — Task 13
- [x] E2E tests — Task 15
- [x] Documentation updates (journey, epics, ADR, arc42) — Task 17

**Type consistency:**
- `DocumentItem` defined in Task 1, used in Tasks 2, 12 ✓
- `DocumentListResponse` defined in Task 1, returned by Task 2 service and Task 3 router ✓
- `DashboardApplicationCardProps` defined in Task 10, used in Task 11 ✓
- `DocumentsTable` props defined in Task 12, consumed by documents page in Task 12 ✓
- `list_documents()` signature: `(user_id, db, page, page_size, status)` — matches router call in Task 3 ✓
