# Sprint 7 — Iteration 21: Dashboard, Returning User Flow & Application Pipeline

**Version:** 1.1
**Date:** 26 March 2026
**Status:** Open

---

## Goal

Deliver Emma's power-user experience: a dashboard showing active applications, returning-user fast path (skip CV upload, go straight to gap analysis), application tracking with user-managed statuses, and the GDPR self-service surface. After this sprint, Apliqa is feature-complete for Community Edition V1.

## User Stories

> **US015** — As a returning user, I want to see all my active applications at a glance so I can manage my pipeline.
> **US016** — As a returning user, I want to add a new job to my pipeline without re-uploading my CV.
> **US017** — As a returning user, I want to update the status of my applications (applied, rejected, offer) to reflect real-world progress.
> **US044** — As a user, I want my flow session to remember where I left off so I can resume.

## Architecture References

- **arc42 §5.3.14** — Flow Orchestrator (`user_type: "returning"` skips `cv_import` step)
- **UI Design Doc** — "EMMA: Power User Dashboard" (Screen 1), Application cards, footer navigation
- **`apliqa/routers/application.py`** — Full CRUD + workflow bridge (6 endpoints, Iteration 17)
- **`apliqa/models/application.py`** — `UserStatus` (tracking/applied/rejected/offer) + `WorkflowStatus` (analyzing/interviewing/cv_generating/completed)
- **ADR 005** — GDPR retention & self-service (DELETE /api/profile, GET /api/profile/export)

## Task Workflow

Each task progresses through these states:

1. **📋 Ready for Implementation** — Task is well-defined, dependencies met, engineer can start.
2. **🔨 In Progress** — Actively being worked on.
3. **🔍 Ready for Review** — Code complete, tested, PR open.
4. **✅ Completed** — Reviewed, approved, merged.

Blockers should be surfaced immediately.

---

## Backend API Surface (reference)

| Endpoint | Purpose | Schema |
|----------|---------|--------|
| `GET /api/applications` | List user's pipeline (filterable by status) | `ApplicationListResponse` |
| `POST /api/applications` | Add job to tracking | `ApplicationResponse` |
| `GET /api/applications/{id}` | Detail with flow state | `ApplicationResponse` |
| `PATCH /api/applications/{id}` | Update status, notes, deadline | `ApplicationResponse` |
| `DELETE /api/applications/{id}` | Remove from pipeline (soft-delete) | `204 No Content` |
| `POST /api/applications/{id}/start` | Create FlowSession for this application | `ApplicationResponse` |
| `DELETE /api/profile` | GDPR full erasure (Art. 17) | `202 Accepted` |
| `GET /api/profile/export` | GDPR data portability (Art. 20) | JSON download |

---

## Deliverables

### Dashboard & Routing

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 21.11 | **Dashboard detection endpoint**: `GET /api/profile/exists` — lightweight check (no payload) returning `{ exists: true/false, completeness_score: float }`. Needed for the routing decision (new user → Screen 1 vs returning user → Dashboard) without loading the full profile. | 📋 Ready for Implementation | — | US016 |
| 21.10 | **Application list performance**: Ensure `GET /api/applications` eager-loads `job_analysis` (for role_title, company_name) and `flow_session` (for current_step). N+1 query elimination. Target: <100ms for 50 applications. Add SQLAlchemy `selectinload` joins. | 📋 Ready for Implementation | — | US015 |
| 21.9 | **Routing & navigation**: Implement proper App Router navigation. `/` → Dashboard (if profile exists) or Screen 1 (new user). `/flow/{id}` → Flow UI (screens 1-3, interview, CV preview). `/profile` → Profile management. `/settings` → Settings with GDPR. Persist `flowId` in URL for bookmarkability and session recovery. | 📋 Ready for Implementation | 21.11, Sprint 6 complete | — |
| 21.1 | **Dashboard screen**: Landing page for returning users. Header: "Welcome back, [name]" + profile completeness pill badge. Section: "Active Applications (N)" with application cards. Each card: role title, company name, applied date, status badge (workflow-derived + user-managed), action buttons (Resume/View CV/Resubmit). "New Application" CTA button centered below. Footer: "My Profile", "Settings", "Help" links. | 📋 Ready for Implementation | 21.9, 21.10 | US015, UI EMMA Screen 1 |

### Application Pipeline

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 21.2 | **Application card logic**: Status badge combines `workflow_status` and `user_status`. Workflow statuses use teal (#2A8F9D) — "Analyzing", "Interviewing", "Generating CV", "CV Ready". User statuses use contextual colors — "Tracking" (gray), "Applied" (blue), "Rejected" (red), "Offer" (green). Action buttons context-sensitive: "Resume" appears when flow is incomplete (links to the current flow step). "View CV" appears when `generated_cv_id` exists. "Resubmit" (re-generate) when CV is expired or user wants fresh version. | 📋 Ready for Implementation | 21.1 | US015, US017 |
| 21.3 | **New Application flow (returning user)**: "New Application" button → JD input only (no CV upload — profile already exists). On submit: `POST /api/applications { job_analysis_id, start_workflow: true }` → flow auto-detects `user_type: "returning"` → skips cv_import → goes straight to gap_analysis. Result screen shows match score + gaps. Entire flow is ≤5 minutes. | 📋 Ready for Implementation | 21.1 | US016, arc42 §5.3.14 |
| 21.4 | **Application detail view**: Click an application card → expand or navigate to detail. Shows: role title, company, full gap analysis summary, interview transcript (if completed), generated CV link, user notes field, deadline picker, status dropdown. PATCH on save. | 📋 Ready for Implementation | 21.1 | US015, US017 |
| 21.5 | **Status management**: User-managed status dropdown on each application: Tracking → Applied → Rejected/Offer. `PATCH /api/applications/{id} { user_status: "applied", notes: "Sent via email", applied_at: "2026-03-25" }`. Deadline field with date picker — shows countdown on card ("3 days left"). | 📋 Ready for Implementation | 21.4 | US017 |
| 21.6 | **Delete application**: Swipe-to-delete on mobile, trash icon on desktop. Confirmation dialog: "Remove [role_title] from your pipeline? This cannot be undone." `DELETE /api/applications/{id}`. Card animates out. | 📋 Ready for Implementation | 21.1 | US015 |
| 21.12 | **Application notes search**: Add `q` query parameter to `GET /api/applications` for full-text search across `role_title`, `company_name`, `notes`. Simple `ILIKE` filter is sufficient for V1. | 📋 Ready for Implementation | 21.10 | US015 |

### Profile & GDPR

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 21.7 | **Profile management screen**: Accessible from dashboard footer "My Profile". Shows current Master Profile in editable sections: Personal Info, Work History, Skills, Education, Languages, Certifications. Each section is a collapsible card with edit button. Edit mode: fields become editable, save calls `PATCH /api/profile/{section}`. Completeness gauge at top. Enrichment history timeline (from `GET /api/profile/enrichment-history`). | 📋 Ready for Implementation | 21.9 | US004 |
| 21.8 | **GDPR self-service**: In Settings (or Profile) screen: "Delete All My Data" button (red, requires confirmation dialog with typed confirmation "DELETE"). Calls `DELETE /api/profile`. "Export My Data" button → `GET /api/profile/export` → triggers JSON file download. Both features required for GDPR Art. 17/20 compliance. | 📋 Ready for Implementation | 21.9 | ADR 005 |
| 21.13 | **GDPR cascade verification**: Integration test for `DELETE /api/profile` cascade: verify that all child records (applications, flow_sessions, interview_sessions, generated_cvs, uploaded_files) are soft-deleted. Verify `GET /api/profile/export` returns complete user data. | 📋 Ready for Implementation | 21.8 | ADR 005 |

### MCP Integration

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 21.14 | **MCP tool update**: Add `list_applications` and `get_application` MCP tools so agents can query the user's pipeline. Update `mcp/server.py`. Update MCP Tool Registry companion document (from Iteration 17.15). | 📋 Ready for Implementation | — | arc42 §5.3.6a |

---

## Done When

1. Returning user opens `localhost:3000` → sees Dashboard with previous applications listed.
2. "New Application" → paste JD → gap analysis shows within 60s (no CV upload needed).
3. Application cards show correct status badges and action buttons.
4. Status dropdown updates persist (applied, rejected, offer).
5. Notes and deadline are editable and saved.
6. Profile screen shows all sections, editable inline.
7. "Delete All My Data" erases everything. "Export My Data" downloads complete JSON.
8. Full end-to-end: New user completes Sprint 4-6 flow → returns → Dashboard shows the application → starts a second application for a different role → fast path works.

## Out of Scope

- Priya's cultural readiness dashboard (V1.1 — after community feedback)
- Jason's recruiter batch matrix / Kanban (Cloud Edition)
- WebSocket notifications for CV generation completion
- OAuth / social login (Cloud Edition)
- Analytics / statistics dashboard

---

## Sprint Summary

| Sprint | Theme | Key Deliverable |
|--------|-------|-----------------|
| **4** | Frontend Foundation | New user flow in browser (Screens 1-3) |
| **5** | Interview UI | Full interview + Gap-Click interaction |
| **6** | CV Generation | Template picker, preview, PDF download |
| **7** | Dashboard & Pipeline | Returning user experience, GDPR |

After Sprint 7, **Apliqa Community Edition V1 is feature-complete** for human browser users. The MCP agent path (Iteration 7) already works. All four personas (Marcus, Priya, Emma, Jason-partial) are served.
