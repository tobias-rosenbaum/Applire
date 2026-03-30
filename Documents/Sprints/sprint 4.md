# Sprint 4 — Iteration 18: Frontend Foundation & New User Happy Path

**Version:** 1.1
**Date:** 26 March 2026
**Status:** Open

---

## Goal

Bootstrap the Next.js frontend and deliver Marcus's complete new-user flow end-to-end: combined CV upload + JD input → processing animation → result screen with match score, gaps, and action CTAs. This is the first time a human can use Apliqa through a browser.
Bootstrap the Next.js frontend and deliver Marcus's complete new-user flow end-to-end: combined CV upload + JD input → processing animation (as an overlay) → result screen with match score, gaps, and action CTAs. This is the first time a human can use Apliqa through a browser.
## User Stories

> **US006** — As a job seeker, I want to submit a job description (URL or paste) so the system can tell me what the role requires.
> **US001** — As a job seeker, I want to upload my CV so the system understands my background.
> **US007** — As a job seeker, I want to see where my profile falls short for this specific role.

## Architecture References

- **arc42 §5.3.14** — Flow Orchestrator (step graph drives UI navigation)
- **arc42 §6.1** — Human Flow Sequence Diagram (the UI follows this sequence exactly)
- **ADR 004** — Stateful Backend (all state lives server-side; frontend is a thin projection of `FlowStateResponse`)
- **ADR 008** — Auth Abstraction (`NoAuthProvider` — no login screen needed for Community Edition)
- **UI Design Doc** — "MARCUS: New User Happy Path", Screens 1–3
- **Apliqa UI Design System & Screen Specifications** — Describes the UI flow, including Screen 2 as an overlay.
## Task Workflow

Each task progresses through these states:

1. **📋 Ready for Implementation** — Task is well-defined, dependencies met, engineer can start.
2. **🔨 In Progress** — Actively being worked on.
3. **🔍 Ready for Review** — Code complete, tested, PR open.
4. **✅ Completed** — Reviewed, approved, merged.

Blockers should be surfaced immediately.

---

## Backend API Surface (reference)

The frontend consumes these existing endpoints. All must be stable and documented before frontend work begins.

| Endpoint | Purpose | Schema |
|----------|---------|--------|
| `POST /api/flow` | Create flow session (resolves `user_type`) | `CreateFlowResponse` |
| `GET /api/flow/{id}/state` | Current step + `available_actions` | `FlowStateResponse` |
| `POST /api/flow/{id}/advance` | Step transition with `artifact_id` | `FlowStateResponse` |
| `POST /api/job/analyze` | JD analysis (text or URL) | `JobAnalysisResponse` |
| `POST /api/profile/upload` | CV upload (multipart, optional `job_id`) | `CVUploadResponse` |
| `POST /api/job/{id}/gaps` | Gap analysis | `GapAnalysisResponse` |
| `GET /api/profile` | Current Master Profile | `MasterProfileResponse` |

---

## Deliverables

### Foundation & Infrastructure

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 18.1 | **Next.js project scaffold**: App Router, TypeScript strict, Tailwind CSS, `src/app/` structure. Docker service `frontend` in `docker-compose.yml` with hot-reload. Proxy `/api/*` to backend (`localhost:8001`). | 🔍 Ready for Review | — | US006 |
| 18.9 | **CORS configuration**: Add `APLIQA_CORS_ORIGINS` env var (default `http://localhost:3000`). Configure FastAPI CORS middleware. Document in `.env.dev`. | 🔍 Ready for Review | — | — |
| 18.11 | **Frontend Docker service**: Add `frontend` service to `docker-compose.yml`. Node 20 image, volume mount for hot-reload, depends_on backend. Expose port 3000. | 🔍 Ready for Review | — | — |
| 18.10 | **OpenAPI schema review**: Verify all response models have complete JSON Schema output. Run `GET /openapi.json`, ensure `FlowStateResponse`, `CVUploadResponse`, `GapAnalysisResponse` are fully specified with all nested models. Fix any `Any` or missing field types. | 🔍 Ready for Review | — | — |
| 18.2 | **Design system tokens**: Implement the brand foundation from the UI Design Doc as Tailwind config — color palette (#1B4F72 primary, #2A8F9D teal, #C9A84C gold, #2D9F6F green, #E5A832 amber, #D94F4F red), typography (Inter/Poppins), spacing (8px grid), border-radius (8px/12px), shadow scale. Create shared Button (primary/secondary/small), Input, Card, Badge components. | 🔍 Ready for Review | 18.1 | UI Design Doc §Brand Foundation |

### New User Flow (Screens 1–3)

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 18.6 | **Flow navigation hook**: `useFlow(flowId)` custom hook. Polls `GET /api/flow/{id}/state`, exposes `currentStep`, `availableActions`, `advance(step, artifactId)`. All screen transitions are driven by this hook — no client-side routing state. If `user_type === "returning"`, skip CV upload screen (handled in Sprint 5). | 🔍 Ready for Review | 18.1, 18.9 | arc42 §5.3.14 |
| 18.3 | **Screen 1 — Combined CV Upload + JD Input**: Two-column layout (60/40). Left: drag-drop zone for CVs (PDF/DOCX/DOC), file chips with remove. Right: tab toggle URL/Paste, URL input field, textarea. CTA "Analyze & Build Profile" disabled until ≥1 CV. On submit: `POST /api/flow` → `POST /api/profile/upload` → `POST /api/job/analyze` (if JD provided) → advance flow. | 🔍 Ready for Review | 18.2, 18.6 | US001, US006, UI Screen 1 |
| 18.4 | **Screen 2 — Processing State**: Centered progress animation. Step-by-step checklist: Uploading CVs → Parsing CVs → Analyzing JD → Building Master Profile → Matching → Detecting gaps. Each step transitions ✓/spinner/○. Progress bar. Real polling: hit `GET /api/flow/{id}/state` every 2s until step advances. Detail text appears as steps complete (e.g., "5 positions, 12 projects found" from profile response). | 🔍 Ready for Review | 18.2, 18.6 | UI Screen 2 |
| 18.5 | **Screen 3 — Combined Result**: Master Profile summary (stat cards: positions, projects, certs, data points). Match score circle badge (animated count-up 0→N%). Gap list with amber dots, gap title, "You have:" context. Three CTAs: "Quick Interview (3 min)" (primary), "Generate CV" (secondary), "Explore Profile" (tertiary link). Wire CTAs to advance flow to `interview` or `cv_generation` step. | 🔍 Ready for Review | 18.2, 18.6 | US007, UI Screen 3 |

### Cross-Cutting & Polish

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 18.7 | **Error handling**: LLM timeout (504) → retry prompt with "This is taking longer than usual". Rate limit (503) → backoff message. Parse failure (502) → "Please try a different JD format". Network error → offline banner. All errors are user-friendly, no raw JSON. | 🔍 Ready for Review | 18.6 | ADR 009 |
| 18.8 | **Responsive layout**: Mobile-first. Screen 1 stacks to single column below 768px. Screen 3 score badge moves above gap list. Touch targets ≥48px. | 🔍 Ready for Review | 18.3, 18.5 | UI Design Doc |

### Testing & Housekeeping

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 18.12 | **API integration test suite**: Create `tests/integration/test_happy_path.py` — automated end-to-end: upload CV → analyze JD → create flow → advance through all steps → verify flow reaches `complete`. Uses real LLM (gated by `INTEGRATION_LLM=1`). Validates the exact sequence the UI will drive. | 🔍 Ready for Review | — | arc42 §6.1 |
| 18.13 | **Mark Iterations 14–17 as Completed**: Update sprint 3 status labels. The backend code for all four iterations is implemented and tested. Update status to ✅ Completed. | 🔍 Ready for Review | — | — |

---

## Done When

1. `docker compose up` starts both `backend` and `frontend` services.
2. Open `http://localhost:3000` → see Screen 1.
3. Upload a real PDF CV + paste a DACH JD → Screen 2 shows animated progress → Screen 3 shows match score, gaps, and CTAs.
4. Clicking "Quick Interview" advances the flow to `interview` step (interview UI is Sprint 5).
5. Clicking "Generate CV" advances to `cv_generation` step (CV UI is Sprint 6).
6. All API errors show user-friendly messages, never raw JSON.

## Out of Scope

- Interview UI (Sprint 5)
- CV preview/download UI (Sprint 6)
- Returning user flow / dashboard (Sprint 7)
- Auth / login screen (Cloud Edition)
- Priya's cultural adaptation screens (Sprint 5 stretch)
