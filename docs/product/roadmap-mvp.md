# Development Roadmap — Apliqa MVP

**Version:** 1.0
**Date:** 06 March 2026
**Status:** DRAFT

---

## Philosophy

Ship working vertical slices. Each iteration delivers a testable, end-to-end user value increment. The backend (Community Edition) is built first; the Next.js frontend is introduced in Iteration 5 where visual preview makes it essential.

All iterations target the **Community Edition** (AGPL-3.0). Cloud-only features (multi-tenancy, billing, Recruiter Intelligence) are out of scope for the MVP.

---

## Iteration 0: Walking Skeleton

**Goal:** A running, deployable application with no features — just the bones.

### Deliverables

| # | Task |
|---|------|
| 0.1 | Docker Compose: `backend` (FastAPI) + `postgres` (PG 16) services |
| 0.2 | Project structure: `apliqa/` package with `routers/`, `services/`, `models/`, `schemas/` |
| 0.3 | Alembic migrations scaffold + initial `users` table |
| 0.4 | LLM Provider Abstraction (ADR 009): `MistralProvider` as default, `LLMProvider` base class |
| 0.5 | Environment config: `.env.dev` with `APLIQA_EDITION`, `LLM_PROVIDER`, `DATABASE_URL` |
| 0.6 | `GET /health` endpoint returning `{ status: "ok", edition: "community" }` |

### Done When
`docker compose up` starts cleanly, `GET /health` returns 200.

---

## Iteration 1: JD Intake & Analysis

**Goal:** User pastes a job description; the system extracts structured elements.

### User Story
> As a job seeker, I want to paste a job description so the system can tell me exactly what the role requires.

### Deliverables

| # | Task |
|---|------|
| 1.1 | `JobAnalysis` Pydantic schema: `role_title`, `required_skills[]`, `nice_to_have_skills[]`, `keywords[]`, `seniority_level`, `company_culture_signals[]`, `language_requirement` |
| 1.2 | `job_analyses` DB table + Alembic migration |
| 1.3 | JD Analysis LLM prompt (structured JSON output, Mistral) |
| 1.4 | Deduplication: `raw_text_hash` (SHA-256) prevents re-analysis of identical JDs |
| 1.5 | `POST /api/job/analyze` — accepts `{ text: string }`, returns `JobAnalysis` |
| 1.6 | Basic error handling: empty input, LLM timeout, parse failure |

### Done When
`POST /api/job/analyze` with a real DACH job description returns a well-structured `JobAnalysis` JSON.

### Out of Scope
URL scraping (Tier 1/2) — text paste only for MVP iteration.

---

## Iteration 2: Profile Import

**Goal:** User provides a CV (PDF) or LinkedIn export; the system extracts a structured Master Profile.

### User Story
> As a job seeker, I want to upload my CV so the system understands my background without me re-entering everything manually.

### Deliverables

| # | Task |
|---|------|
| 2.1 | `MasterProfile` Pydantic schema: `work_history[]` (company, role, dates, bullets), `skills[]`, `education[]`, `languages[]`, `contact` |
| 2.2 | `master_profiles` DB table (JSONB `profile_json`) + Alembic migration |
| 2.3 | PDF text extraction (`pypdf`) |
| 2.4 | LinkedIn JSON export parser (from LinkedIn "Export Data" ZIP) |
| 2.5 | Profile extraction LLM prompt: raw text → structured `MasterProfile` |
| 2.6 | `POST /api/profile/import` — accepts multipart PDF upload or `{ linkedin_json: object }` |
| 2.7 | `GET /api/profile` — returns current `MasterProfile` |
| 2.8 | `PATCH /api/profile/{section}` — manual correction of any section |
| 2.9 | `calculate_completeness()` method on the profile model |

### Done When
Upload a real CV PDF → `GET /api/profile` returns a structured `MasterProfile` JSON with all major sections populated.

---

## Iteration 3: Gap Analysis

**Goal:** The system compares the JD to the user's profile and produces a prioritised gap report.

### User Story
> As a job seeker, I want to know exactly where my profile falls short for this specific role, so I can focus on what matters.

### Deliverables

| # | Task |
|---|------|
| 3.1 | `GapAnalysis` Pydantic schema: `match_score` (0–100), `critical_gaps[]`, `minor_gaps[]`, `strengths[]`, `keyword_gaps[]` |
| 3.2 | Gap analysis LLM prompt: `JobAnalysis` + `MasterProfile` → `GapAnalysis` |
| 3.3 | `POST /api/job/{job_id}/gaps` — returns `GapAnalysis` for current profile vs. given job |
| 3.4 | Store `GapAnalysis` alongside `JobAnalysis` in the DB |

### Done When
`POST /api/job/{job_id}/gaps` returns a gap report with a realistic match score and specific, actionable gaps.

---

## Iteration 4: Gap-Fill Interview

**Goal:** The system asks targeted questions to fill the identified gaps; answers enrich the Master Profile.

### User Story
> As a job seeker, I want the system to ask me targeted questions about my experience so my profile accurately reflects what I've done.

### Deliverables

| # | Task |
|---|------|
| 4.1 | `interview_sessions` DB table (session state as JSONB) + Alembic migration |
| 4.2 | LangGraph state machine with nodes: `GapDetector → QuestionGenerator → ResponseParser → ProfileUpdater` |
| 4.3 | `POST /api/session` — creates a new interview session for a `job_id`, returns `session_id` + first question |
| 4.4 | `POST /api/session/{session_id}/message` — accepts user reply, returns next question or `{ complete: true }` |
| 4.5 | `ResponseParser` node: extract structured profile data from free-text answers |
| 4.6 | `ProfileUpdater` node: merge new data into `MasterProfile` using Intelligent Merge logic (no overwrites, conflict flagging) |
| 4.7 | Session completion when all critical gaps are addressed or user explicitly ends |

### Done When
Start a session tied to a job with known gaps → receive a targeted question → answer it → see `GET /api/profile` updated with the new data → receive the next question → session completes.

---

## Iteration 5: CV Generation, Preview & Download

**Goal:** The system generates a tailored CV, the user can preview it live in the browser and download as PDF.

### User Story
> As a job seeker, I want to see my tailored CV and download it as a PDF I can send directly to a recruiter.

### Deliverables

**Backend**

| # | Task |
|---|------|
| 5.1 | CV Tailoring Engine: LLM-driven section reordering, bullet rewriting, keyword alignment for the given `job_id` |
| 5.2 | `GeneratedCV` DB model + `generated_cvs` table (90-day TTL) + Alembic migration |
| 5.3 | Jinja2 template: "Classic German" Lebenslauf (HTML/CSS) |
| 5.4 | `GET /api/cv/{cv_id}/html` — returns rendered HTML (used for browser preview) |
| 5.5 | `GET /api/cv/{cv_id}/pdf` — Playwright headless Chromium renders the same HTML → returns PDF bytes |
| 5.6 | `POST /api/cv/generate` — triggers tailoring + rendering, returns `{ cv_id, html_url, pdf_url }` |

**Frontend (Next.js — minimum viable)**

| # | Task |
|---|------|
| 5.7 | Single-page flow: JD input → profile status → generate button → preview panel |
| 5.8 | CV preview: `<iframe>` loading `GET /api/cv/{cv_id}/html` (live WYSIWYG, same Chromium engine as PDF) |
| 5.9 | Download button: triggers `GET /api/cv/{cv_id}/pdf` |

### Done When
End-to-end: paste JD → import CV → run gap interview → click "Generate" → see the tailored CV in the browser preview panel → download PDF.

---

## Cross-Cutting Concerns (Ongoing)

These are addressed continuously across all iterations, not as a separate iteration:

| Concern | Approach |
|---------|----------|
| Structured logging | JSON logs with `job_id`/`session_id` correlation from Iteration 1 |
| Input validation | Pydantic schemas at all API boundaries |
| LLM prompt versioning | Prompts stored as constants in `apliqa/prompts/`, versioned in git |
| No auth for MVP dev | Single-user local mode; Auth Abstraction (ADR 008) scaffolded but not enforced until Cloud prep |
| GDPR retention | Retention Worker scaffolded in Iteration 0, TTL fields on all models from the start |

---

## Post-MVP (V2 Scope)

The following are explicitly out of scope for the MVP iterations above:

- URL scraping (Tier 1: `httpx`, Tier 2: Playwright)
- Auth enforcement (Zitadel/OIDC)
- Second CV template ("Modern Swiss")
- MCP Server (agent interface)
- Cloud Edition features (billing, multi-tenancy, Recruiter Intelligence)
- WebSocket for interview (REST polling acceptable for MVP)
- Analytics dashboard
