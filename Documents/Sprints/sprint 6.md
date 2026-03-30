# Sprint 6 — Iteration 20: CV Generation UI & Template Selection

**Version:** 1.1
**Date:** 26 March 2026
**Status:** Open

---

## Goal

Deliver the CV generation, preview, and download experience. The user selects a template, triggers generation, watches async progress, previews the rendered CV in a split-screen layout, and downloads a PDF. This completes the new-user happy path end-to-end in the browser.

## User Stories

> **US014** — As a job seeker, I want to generate a tailored CV for this specific role so I can apply with confidence.
> **US041** — As a job seeker, I want to download my tailored CV as a PDF so I can attach it to my application.
> **US048** — As a job seeker, I want to see the generation progress so I know when my CV is ready.

## Architecture References

- **arc42 §5.3.4** — PDF Generator (Jinja2 → Playwright Chromium, async model)
- **ADR 014** — CV Upload Pipeline (CV status lifecycle: pending → generating → ready/failed)
- **UI Design Doc** — "MARCUS: Screen 3" CTAs, CV preview concept (iframe + download)
- **`apliqa/models/cv.py`** — `CVGenerationStatus` enum (pending/generating/ready/failed/expired)

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
| `POST /api/cv/generate` | Trigger async CV generation (`job_id`, `template`) | `CVGenerateResponse` |
| `GET /api/cv/{id}/status` | Poll generation progress | `CVStatusResponse` |
| `GET /api/cv/{id}/html` | Rendered HTML (for iframe preview) | `HTMLResponse` |
| `GET /api/cv/{id}/pdf` | PDF download | `application/pdf` |

---

## Deliverables

### Foundation & API Hardening

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 20.7 | **CV HTML CORS headers**: Ensure `GET /api/cv/{id}/html` returns proper `X-Frame-Options: SAMEORIGIN` and `Content-Security-Policy` headers so the iframe works from `localhost:3000`. Add to CORS config from Sprint 4. | 📋 Ready for Implementation | — | — |
| 20.8 | **CV filename in Content-Disposition**: Update `GET /api/cv/{id}/pdf` to include the role title in the filename: `lebenslauf-{role_title_slug}-{cv_id[:8]}.pdf`. Derive the slug from the associated `JobAnalysis.role_title`. | 📋 Ready for Implementation | — | US041 |
| 20.10 | **Template preview thumbnails**: Generate static PNG thumbnails for both CV templates (screenshot via Playwright with sample data). Store in `backend/static/templates/`. Expose via `GET /static/templates/{template_name}.png`. Referenced by the template picker UI. | 📋 Ready for Implementation | — | US014 |
| 20.11 | **CV list endpoint**: `GET /api/cv?job_id={id}` — returns all generated CVs for a job, sorted by `created_at DESC`. Enables the "previous versions" feature in the preview screen. Schema: `list[CVStatusResponse]`. | 📋 Ready for Implementation | — | US014 |

### Template Selection & Generation

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 20.1 | **Template selection screen**: After flow reaches `cv_generation` step, show template picker. Two cards side by side: "Classic German" (Lebenslauf, traditional, photo-ready) and "Modern Swiss" (clean, single-column, no photo). Each card shows a static preview thumbnail, template name, and a brief description. Radio-select UX. CTA: "Generate CV". | 📋 Ready for Implementation | 20.10, Sprint 5 complete | US014, Iteration 9 |
| 20.2 | **Generation progress**: On "Generate CV" click: `POST /api/cv/generate { job_id, template }`. Show a progress indicator with "Tailoring your CV for [role_title]…". Poll `GET /api/cv/{id}/status` every 3s. Status transitions: `pending` → "Queued…", `generating` → "Rendering your CV…", `ready` → transition to preview. `failed` → error message with retry button. Inline staleness: if polling > 60s without `ready`, show "Taking longer than expected — you can check back later". | 📋 Ready for Implementation | 20.1 | US048 |

### Preview & Download

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 20.3 | **Split-screen CV preview**: Left panel (40%): CV metadata — role title, template used, match score, generation timestamp, expiry date. Right panel (60%): `<iframe src="/api/cv/{id}/html">` showing the live rendered CV. Same Chromium-rendered HTML that produces the PDF — true WYSIWYG. Download button: triggers `GET /api/cv/{id}/pdf` as a blob download with filename `lebenslauf-{role_title}.pdf`. | 📋 Ready for Implementation | 20.2, 20.7 | US014, US041 |
| 20.4 | **Regeneration flow**: "Regenerate with different template" button → returns to template picker. "Regenerate" button → re-triggers `POST /api/cv/generate` with same template (useful if profile was enriched since last generation). Old CV remains accessible until new one is ready. | 📋 Ready for Implementation | 20.3 | US014 |
| 20.6 | **CV expiry notice**: Show the `expires_at` date from `CVStatusResponse` as "This CV will be available until [date]". Style as a subtle info badge. If the CV has expired (status: `expired`), show "This CV has expired. Generate a new one." with a regenerate CTA. | 📋 Ready for Implementation | 20.3 | ADR 005 |

### Flow Completion

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 20.5 | **Flow completion**: After successful preview, show "What's next?" section: "Apply Now" (external — copies a shareable summary to clipboard), "Start New Application" (creates new flow for a different JD), "Back to Dashboard" (if dashboard exists, otherwise "Upload Another JD"). Call `POST /api/flow/{id}/advance { step: "complete" }` to finalize. | 📋 Ready for Implementation | 20.3 | arc42 §5.3.14 |
| 20.9 | **CV generation → flow artifact sync**: When `POST /api/cv/generate` returns a `cv_id`, the frontend must call `advance_flow(step="cv_generation", artifact_id=cv_id)`. Verify this writes `generated_cv_id` on the `FlowSession` record. Add integration test. | 📋 Ready for Implementation | — | arc42 §5.3.14 |

---

## Done When

1. After interview (or skip), user sees template picker → selects "Classic German" → clicks "Generate CV" → progress indicator → split-screen preview loads within ~30s.
2. Download button saves a properly named PDF file.
3. "Modern Swiss" template also renders correctly.
4. Failed generation shows error with retry button.
5. "Complete" flow step is reached — full Marcus happy path works end-to-end: upload CV + paste JD → processing → match score → interview → CV preview → download.
6. CV expiry date is displayed.

## Out of Scope

- CV editing (in-browser content editing — V2.0)
- Third template (V3.0)
- Batch CV generation for multiple jobs (Cloud Edition / Jason's recruiter flow)
- Print-specific CSS optimization (defer)
