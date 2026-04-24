# Sprint 29 — Power User Dashboard Design Spec

**Date:** 2026-04-24  
**Sprint:** 29  
**Author:** Tobias Rosenbaum  
**Status:** Approved for implementation

---

## Goal

Replace the current single-page mock dashboard with a full navigation shell and two purpose-built pages — Dashboard and My Documents — that serve Emma (the recurring power user) who juggles multiple active applications and needs to move between them efficiently.

**In scope:** Shell layout, Dashboard page, My Documents page, one new backend endpoint.  
**Out of scope:** Profile page content overhaul, Settings content overhaul, cover letter artifacts in My Documents, billing/upgrade features.

---

## 1. Routing Architecture

Introduce a Next.js App Router **route group** `(shell)` that owns its own `layout.tsx` rendering the persistent sidebar and topbar. All authenticated app pages live inside this group.

### Page moves

| Current path | New path | Notes |
|---|---|---|
| `app/page.tsx` | stays at root | Keeps new/returning user split; returning users redirected to `/dashboard` |
| `app/profile/` | `app/(shell)/profile/` | Content unchanged this sprint |
| `app/(shell)/settings/` | stays, moves into group | Content unchanged this sprint |
| `app/flow/[flowId]/` | `app/(shell)/flow/[flowId]/` | All flow sub-pages move with it |
| `app/applications/` | `app/(shell)/applications/` | Existing detail page |
| *(new)* | `app/(shell)/dashboard/page.tsx` | Replaces the inline `<Dashboard>` rendered by root page |
| *(new)* | `app/(shell)/documents/page.tsx` | My Documents page |

The root `app/page.tsx` continues to check `GET /api/profile/exists`. If the user has a profile it redirects to `/dashboard`; if not it shows the onboarding screen. Onboarding never sees the sidebar.

### Shell layout (`app/(shell)/layout.tsx`)

Renders `<AppSidebar>` + `<AppTopbar>` + `{children}`. No per-page logic here — just the chrome. Both components are created as new files under `frontend/components/shell/`.

---

## 2. Sidebar (`AppSidebar`)

**Width:** 240px, always visible (no collapse this sprint).  
**Background:** white, `border-right: 1px solid #e2e5f0`.

Structure top-to-bottom:

1. **Logo row** — Applire wordmark with branded icon
2. **User row** — avatar initials, display name, plan tier (read from profile API)
3. **Nav items** — four entries, active state uses blue right-border indicator (`border-right: 3px solid #003399`) + `#eef1ff` background:
   - Dashboard (`/dashboard`)
   - Master Profile (`/profile`)
   - My Documents (`/documents`)
   - Settings (`/settings`)
4. **Footer** — Help Center link only (no upgrade CTA this sprint)

Active item is determined by `usePathname()` prefix match.

---

## 3. Topbar (`AppTopbar`)

**Height:** 52px, white, `border-bottom: 1px solid #e8ebf8`.

- Left: breadcrumb (section name from current route)
- Centre: search input (styled pill, `background: #f1f3ff`) — scoped to current section; wired up for My Documents, no-op elsewhere this sprint
- Right: notification bell icon + user avatar (navigates to `/settings`)

---

## 4. Dashboard Page (`/dashboard`)

### Layout

Two distinct zones stacked vertically:

**Zone 1 — Top row (side by side):**
- Left: Quick Tailor widget (fluid width)
- Right: Profile Strength card (fixed 260px)

**Zone 2 — Active Applications grid (2 columns)**

### 4a. Quick Tailor Widget

Replaces `NewApplicationModal`. The modal component is removed.

**Visual:** white card with a 3px gradient top-border (`#fecb00 → #003399 → #fecb00`), label "Quick Tailor", subtitle "Paste a job link or full description — Applire analyses it and starts your CV flow."

**Input:** URL / Paste Text tab toggle — same `JdMode = "url" | "text"` pattern as the existing `NewApplicationModal`, reusing the same API calls (`POST /api/job/analyze` → `POST /api/applications`). Tab active state shown with a `2px solid #003399` underline on the active tab, matching the existing modal's teal underline pattern.

- URL panel: single-line input + **Analyse →** button
- Text panel: `min-height: 88px` resizable textarea + **Analyse →** button (aligned to bottom-right of textarea)

On success: navigate to `/(shell)/flow/[flowId]/import` to start the flow (same behaviour as the existing modal's `onSuccess` callback).

### 4b. Profile Strength Card

**Visual:** `linear-gradient(145deg, #002068, #003399)`, white text, 260px wide.

Displays:
- Section label "Profile Strength"
- Large score number (e.g. "78") in white, unit "%" omitted for visual weight
- Progress bar (`#fecb00` fill on `rgba(255,255,255,0.18)` track)
- Up to 4 checklist items: done items in muted white with green `check_circle` icon; missing items in dim white with `radio_button_unchecked` icon
- "Complete Profile →" CTA link navigating to `/profile`

Score comes from the `completeness_score` field already returned by the existing `GET /api/profile/exists` endpoint — no extra API call needed since the dashboard already fetches this to determine user type. The checklist items (which sections are missing) are derived client-side from `GET /api/profile` (the full profile payload). If either call fails, the card shows a skeleton state and must not block the dashboard render.

### 4c. Active Applications Grid

**Section header:** "Active Applications" (left) + "View all in My Documents →" link (right, navigates to `/documents`).

2-column grid of `ApplicationCard` components. Each card shows:

| Field | Source |
|---|---|
| Company initial avatar | `application.company_name[0]` |
| Role title | `application.role_title` |
| Company + location | `application.company_name` |
| Progress bar | Derived from `workflow_status` |
| Status chip | `workflow_status` mapped to label |
| Date | `application.updated_at` relative |
| Action button | Depends on state (see below) |

**Card states and actions:**

| `workflow_status` | Chip | Border | Progress colour | Button |
|---|---|---|---|---|
| `in_progress` (at interview/gap step) | "In Progress" blue | solid | `#003399` | **Resume** → `/flow/[flowId]/interview` |
| `cv_generated` / `complete` | "CV Ready" green | solid green | `#2e7d32` full | **Open** → `/flow/[flowId]/cv` |
| interrupted (in_progress, last activity > 48h) | "Interrupted" amber | dashed | `#fecb00` | **Continue** → appropriate flow step |
| no flow started | "Tracking" grey | solid | empty | **Start Flow** → calls `POST /api/applications/{id}/start`, then navigates to `/flow/[flowId]/import` |

Cards are populated from the existing `GET /api/applications` endpoint (already returns `flow_session_id`, `workflow_status`, `company_name`, `role_title`). Show a maximum of **6 cards** on the dashboard; the rest are in My Documents.

---

## 5. My Documents Page (`/documents`)

Archive and download centre for all generated CV artifacts across all applications.

### 5a. Stats Strip

3-card row above the table:

| Card | Value source |
|---|---|
| Total documents | `total` from `GET /api/documents` response |
| Downloads this month | Client-side count not tracked yet — show `—` for now |
| Expiring within 7 days | Count of rows where `expires_at < now + 7d` |

### 5b. Filter Bar

Left-aligned row: status chips → text search → spacer → sort dropdown.

**Status chips:** All (default) · Ready · Generating · Expiring soon  
Chips filter the displayed rows client-side (no extra API calls).

**Text search:** pill input (`border: 1.5px solid #e2e5f0`, focus ring `#003399`), placeholder "Filter by role or company…". Filters client-side against role title and company name, case-insensitive substring match.

**Sort dropdown:** Newest first (default) · Oldest first · By company

### 5c. Document Table

Columns: **Document** | **Template** | **Status** | **Expires** | *(action)*

**Document cell:** file icon + role title (bold) + "Company · Generated [date]" subtitle.

**Template badge:** small pill showing the template name (e.g. "Classic German", "Modern Swiss").

**Status badge:**
- `ready` → green "Ready" with `check_circle` icon
- `generating` → amber "Generating…" with `hourglass_top` icon  
- `expired` → grey "Expired"

**Expires column:**
- More than 7 days away: plain grey date string
- 7 days or fewer: amber warning with `warning` icon and "Expires in N days"

**Action column (rightmost, no header):**
- `ready` rows: **Open** button (outlined, `border: 1.5px solid #e2e5f0`) → navigates to `/(shell)/flow/[flowId]/cv`
- `generating` rows: disabled **Generating…** button

The `flow_id` comes from the `GET /api/documents` response (see §6).

**Pagination:** 10 rows per page, standard prev/next + page number controls.

---

## 6. New Backend Endpoint: `GET /api/documents`

No existing endpoint lists generated CVs cross-job for the current user. A new endpoint is required.

**Route:** `GET /api/documents`  
**Auth:** current user (same pattern as all other authed routes)  
**Router file:** `backend/applire/routers/documents.py` (new)  
**Registered at:** `/api/documents` in `main.py`

**Query params:** `page` (default 1), `page_size` (default 10), `status` (optional filter).

**Response schema (`DocumentListResponse`):**

```python
class DocumentItem(BaseModel):
    cv_id: uuid.UUID
    flow_id: uuid.UUID | None          # flow_session_id from the application
    role_title: str | None
    company_name: str | None
    template: str
    status: CVGenerationStatus
    created_at: datetime
    expires_at: datetime

class DocumentListResponse(BaseModel):
    items: list[DocumentItem]
    total: int
```

**Join logic:**

```
generated_cvs
  → profile_id  → master_profiles.user_id  (ownership check)
  → job_analysis_id → job_analyses.id      (role_title, company_name)
  → job_analysis_id → applications.job_analysis_id
                     → applications.flow_session_id  (flow_id)
```

Where a job has multiple applications (edge case), take the most recently updated one. Filter out `deleted_at IS NOT NULL` rows at both the CV and profile level.

Order by `generated_cvs.created_at DESC` by default.

---

## 7. Component Inventory

| Component | File | New / Modified |
|---|---|---|
| Shell layout | `app/(shell)/layout.tsx` | New |
| `AppSidebar` | `components/shell/AppSidebar.tsx` | New |
| `AppTopbar` | `components/shell/AppTopbar.tsx` | New |
| Dashboard page | `app/(shell)/dashboard/page.tsx` | New (replaces inline Dashboard) |
| `QuickTailorWidget` | `components/dashboard/QuickTailorWidget.tsx` | New (extracts logic from `NewApplicationModal`) |
| `ProfileStrengthCard` | `components/dashboard/ProfileStrengthCard.tsx` | New |
| `ApplicationCard` | `components/dashboard/ApplicationCard.tsx` | New (replaces existing card) |
| `NewApplicationModal` | `components/dashboard/NewApplicationModal.tsx` | **Deleted** |
| My Documents page | `app/(shell)/documents/page.tsx` | New |
| `DocumentsTable` | `components/documents/DocumentsTable.tsx` | New |
| Documents router | `backend/applire/routers/documents.py` | New |
| `DocumentItem` / `DocumentListResponse` schemas | `backend/applire/schemas/documents.py` | New |
| Root `app/page.tsx` | `app/page.tsx` | Modified — redirect to `/dashboard` |

---

## 8. Testing

**Backend unit tests** (`tests/unit/test_sprint29_documents.py`):
- `GET /api/documents` returns correct items for the authenticated user
- Items from other users are not returned
- `flow_id` is correctly resolved from the application join
- `status` query param filters correctly
- Pagination works (total, page, page_size)

**Frontend unit tests** (Vitest):
- `QuickTailorWidget`: tab switching, URL submit, text submit, error display
- `ProfileStrengthCard`: renders skeleton when API unavailable
- `DocumentsTable`: text filter hides non-matching rows, chip filter works, sort changes order

**E2E tests** (`tests/e2e/sprint29-dashboard.spec.ts`):
- Returning user lands on `/dashboard` after login
- Onboarding user does NOT see the sidebar
- Quick Tailor URL submission starts a flow and navigates to import step
- My Documents page loads, Open button navigates to the CV flow page
- Active sidebar item highlights correctly when navigating

---

## 9. Open Questions (resolved)

| Question | Decision |
|---|---|
| Navigation shell type | Wide labeled sidebar, 240px |
| Sprint scope | Shell + Dashboard + My Documents; Profile/Settings content deferred |
| Dashboard CTA | Inline Quick Tailor widget replaces modal |
| Dashboard vs Documents split | Dashboard = active pipeline; My Documents = all generated artifacts |
| Routing strategy | `(shell)` route group |
| Preview / Re-tailor actions | Single **Open** button → existing CV flow page (handles both) |
| Upgrade CTA in sidebar | Deferred — not in this sprint |
