# Development Roadmap — Apliqa V1.1

**Version:** 1.0
**Date:** 07 March 2026
**Status:** Completed

---

## Philosophy

V1.1 extends the MVP with three strategic pillars:

1. **Agent-First Distribution** — The MCP Server makes Apliqa a first-class tool for AI agents (Claude, Cursor, OpenClaw). This is the primary growth channel for the Community Edition.
2. **Self-Hoster Completeness** — Ollama support enables fully offline, zero-cloud operation. Auth Abstraction scaffolds the pluggable interface cloud backends will use.
3. **Intake & Output Polish** — URL scraping removes the copy-paste friction from JD intake. A second CV template and completed LinkedIn import round out the user-facing surface.

All iterations target the **Community Edition** (AGPL-3.0). Cloud features (multi-tenancy, billing, Recruiter Intelligence, Zitadel auth enforcement) remain out of scope.

---

## Iteration 6: LLM Provider Choice

**Status:** ✅ Completed

**Goal:** Self-hosters can run Apliqa with any LLM — including fully local, zero-cloud operation via Ollama.

### User Story
> As a self-hoster, I want to choose my LLM provider so I can run fully local or use my existing OpenAI subscription without being locked into Mistral.

### Deliverables

| # | Task |
|---|------|
| 6.1 | `OpenAIProvider`: implements `LLMProvider` base; `acomplete()` + `aparse_json()` via `openai` SDK |
| 6.2 | `OllamaProvider`: implements `LLMProvider` base; calls Ollama REST API (`/api/chat`) |
| 6.3 | Provider factory in `apliqa/providers/__init__.py`: instantiate correct provider from `LLM_PROVIDER` env var |
| 6.4 | `.env.dev` additions: `OPENAI_API_KEY`, `OLLAMA_BASE_URL` (default `http://ollama:11434`) |
| 6.5 | `ollama` service added to `docker-compose.yml` (optional, profile-gated) |
| 6.6 | Tests: provider factory, OpenAI + Ollama adapters with mocked HTTP |

### Done When
Set `LLM_PROVIDER=ollama` in `.env.dev`, run `docker compose up` — all API endpoints work against a local Ollama instance with no external LLM calls.

---

## Iteration 7: MCP Server

**Status:** ✅ Completed

**Goal:** AI agents can drive the full Apliqa tailoring workflow via the Model Context Protocol.

### User Story
> As an AI agent, I want to call Apliqa's capabilities as MCP tools so I can automate the full JD → profile → gap-fill → CV workflow without human interaction.

### Deliverables

| # | Task |
|---|------|
| 7.1 | `apliqa/mcp/server.py`: MCP server using `mcp` Python SDK, `stdio` transport |
| 7.2 | Tool: `analyze_jd(text: str) → JobAnalysis` |
| 7.3 | Tool: `get_profile() → MasterProfile` |
| 7.4 | Tool: `update_profile(section: str, data: dict) → MasterProfile` |
| 7.5 | Tool: `analyze_gaps(job_id: str) → GapAnalysis` |
| 7.6 | Tool: `run_interview(job_id: str) → session_id + first question` — creates session |
| 7.7 | Tool: `send_message(session_id: str, message: str) → question | { complete: true }` |
| 7.8 | Tool: `generate_cv(job_id: str) → { cv_id, html_url, pdf_url }` |
| 7.9 | Resource: `profile://current` → current `MasterProfile` JSON |
| 7.10 | Resource: `job://{job_id}` → `JobAnalysis` JSON |
| 7.11 | Resource: `cv://{cv_id}` → `GeneratedCV` metadata |
| 7.12 | MCP server entry point: `python -m apliqa.mcp` (runs as a subprocess, shares DB with the FastAPI backend) |
| 7.13 | `docker-compose.yml`: optional `mcp` service that starts the stdio server |
| 7.14 | `docs/mcp.md`: usage guide with example Claude Desktop / Cursor config |
| 7.15 | Tests: each tool with mocked services; resource resolution |

### Done When
Configure Claude Desktop to use the Apliqa MCP server → instruct it to "analyse this JD, run the interview, generate my CV" → agent completes the full flow autonomously and returns a download URL.

### Out of Scope
SSE transport (Cloud Edition). API-Key auth on MCP (Cloud Edition). Rate limiting (Cloud Edition).

---

## Iteration 8: JD URL Intake

**Status:** ✅ Completed

**Goal:** User pastes a job URL; the system fetches and extracts the JD text automatically.

### User Story
> As a job seeker, I want to paste a job posting URL so I don't have to manually copy the text from the page.

### Deliverables

| # | Task |
|---|------|
| 8.1 | `apliqa/services/scraper.py`: tiered scraping strategy |
| 8.2 | Tier 1 (`httpx`): plain HTTP fetch + `BeautifulSoup` main-content extraction; covers most job boards |
| 8.3 | Tier 2 (`playwright`): headless Chromium for JS-rendered pages (StepStone, Indeed DACH) |
| 8.4 | Fallback: return structured error `{ scrape_failed: true, instructions: "..." }` prompting manual paste |
| 8.5 | `POST /api/job/analyze` extended: accepts `{ url: string }` in addition to `{ text: string }` |
| 8.6 | Frontend: URL input field alongside the existing JD textarea; auto-detects paste of a URL vs. raw text |
| 8.7 | Deduplication: URL-based jobs hash the scraped `raw_text` — same deduplication path as text input |
| 8.8 | Tests: Tier 1 + Tier 2 with mocked HTTP; fallback path |

### Done When
Paste a StepStone or Indeed DACH job URL → `POST /api/job/analyze` returns a valid `JobAnalysis` without the user touching the raw text. LinkedIn/XING return the fallback gracefully.

### Out of Scope
Authentication-required job boards. Bulk URL processing.

---

## Iteration 9: Second CV Template & LinkedIn Import

**Status:** ✅ Completed

**Goal:** Users have a second CV style choice and can import their LinkedIn export directly.

### User Story (Template)
> As a job seeker, I want to choose a "Modern Swiss" CV style so my application matches Swiss employer expectations rather than the classic German format.

### User Story (LinkedIn)
> As a job seeker, I want to import my LinkedIn data — either as the "Export Data" ZIP or as a profile PDF — so I can quickly populate my Master Profile without re-entering everything manually.

### Deliverables

**Template**

| # | Task |
|---|------|
| 9.1 | `apliqa/templates/modern_swiss.html.j2`: clean, single-column Swiss style; no photo field; EN/DE header |
| 9.2 | `POST /api/cv/generate` extended: accepts `{ job_id, template: "classic_german" | "modern_swiss" }` |
| 9.3 | `GET /api/cv/{cv_id}/html` renders with the template stored on the `GeneratedCV` record |
| 9.4 | Frontend: template selector dropdown on the "Generate" step |

**LinkedIn Import**

| # | Task |
|---|------|
| 9.5 | `apliqa/services/linkedin.py`: `parse_linkedin_zip()` parses LinkedIn "Export Data" ZIP (CSV files); `parse_linkedin_pdf()` extracts text from LinkedIn profile PDF via `pypdf` → both produce raw text for LLM structuring |
| 9.6 | `POST /api/profile/import`: detect ZIP by content-type/extension → `import_from_linkedin_zip()`; detect PDF by content-type/extension → `import_from_linkedin_pdf()`; both paths feed into the same LLM extraction pipeline |
| 9.7 | Frontend: two upload paths — `.zip` (LinkedIn "Export Data" download) and `.pdf` (LinkedIn profile "Save as PDF") |
| 9.8 | Tests: ZIP parser unit tests + PDF parser unit tests (mocked `PdfReader`); integration tests for both upload paths including content-type detection |

### Done When
Select "Modern Swiss" → generate → preview renders the correct template. Upload a LinkedIn export ZIP **or** a LinkedIn profile PDF → `GET /api/profile` returns a populated `MasterProfile`.

---

## Iteration 10: Auth Abstraction Scaffold & Retention Worker

**Status:** ✅ Completed

**Goal:** Lay the technical groundwork for pluggable auth (Cloud prep) and GDPR-compliant data lifecycle management for multi-user self-hosted deployments.

### Rationale
Neither feature delivers end-user value in single-user local mode. They are included here because:
- The Auth Abstraction interface must exist in the Community codebase for Cloud backends to implement (ADR 008)
- The Retention Worker is required the moment a self-hoster serves more than one user — deferring it beyond V2 creates GDPR exposure

### Deliverables

**Auth Abstraction (ADR 008)**

| # | Task |
|---|------|
| 10.1 | `apliqa/auth/base.py`: `AuthProvider` abstract base class with `get_current_user() → User \| None` |
| 10.2 | `apliqa/auth/no_auth.py`: `NoAuthProvider` — returns a fixed single-user stub; zero enforcement |
| 10.3 | Provider factory: `AUTH_PROVIDER=none` (default) instantiates `NoAuthProvider` |
| 10.4 | FastAPI dependency `get_auth_provider()` injected at router level (no functional change for Community) |
| 10.5 | `AUTH_PROVIDER` added to `.env.dev`; docs note that `zitadel` / `oidc` / `apikey` backends ship with Cloud Edition |

**Retention Worker (ADR 005)**

| # | Task |
|---|------|
| 10.6 | `apliqa/retention/worker.py`: async script; runs TTL sweeps in sequence |
| 10.7 | Rule: delete `uploads` (files) older than 7 days |
| 10.8 | Rule: delete `interview_sessions` with `updated_at` older than 30 days |
| 10.9 | Rule: delete `generated_cvs` with `expires_at` in the past (90-day TTL set at creation) |
| 10.10 | Rule: soft-delete `master_profiles` / `users` inactive for 24 months (tombstone, not hard delete, for backup audit trail) |
| 10.11 | `docker-compose.yml`: `retention` service runs `python -m apliqa.retention` on a daily cron schedule |
| 10.12 | Structured log output: JSON report per run (rows affected per table) |
| 10.13 | Tests: each TTL rule with in-memory SQLite fixtures |

### Done When
`AUTH_PROVIDER=none` (default) — behaviour identical to MVP. `docker compose up` starts the `retention` service; next day's cron run purges seeded expired records and logs a JSON report.

---

## Cross-Cutting Concerns (Ongoing)

| Concern | Approach |
|---------|----------|
| Structured logging | JSON logs with `job_id` / `session_id` correlation extended to MCP tool calls |
| MCP error codes | Standard MCP error responses; tool errors surfaced as structured `CallToolResult` errors |
| Prompt versioning | All new prompts (if any) added to `apliqa/prompts/`, versioned in git |
| Provider parity | New providers tested against the same fixture JD / profile to verify output quality |
| Template ATS compliance | Both templates validated against ATS parsers (Workday, SAP) before release |

---

## Post-V2 (V3 / Cloud Scope)

The following remain explicitly out of scope for V2.0:

- SSE transport for MCP (Cloud Edition)
- API-Key auth on MCP (Cloud Edition)
- Auth enforcement (Zitadel / OIDC) — Cloud Edition
- Multi-tenancy (ADR 011) — Cloud Edition
- Paddle billing — Cloud Edition
- Recruiter Intelligence (GxP) — Cloud Edition
- WebSocket for interview (REST polling sufficient through V2)
- Analytics dashboard
- Third CV template
- Bulk URL processing

---

## Summary

| Iteration | Theme | Key Deliverable |
|-----------|-------|-----------------|
| 6 | LLM Provider Choice | OpenAI + Ollama providers; fully local operation |
| 7 | MCP Server | Agent-driven full tailoring workflow via stdio |
| 8 | JD URL Intake | Tiered scraping; URL input in frontend |
| 9 | Second Template + LinkedIn | "Modern Swiss" template; LinkedIn ZIP + PDF import |
| 10 | Auth Abstraction + Retention | Cloud prep scaffolding; GDPR lifecycle enforcement |
