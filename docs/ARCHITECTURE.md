# Applire — Architecture Reference

**Audience:** Contributors, self-hosters, AI agents working on the codebase.

This document explains the *why* behind Applire's key architectural choices. It is a condensed public version of the internal arc42 + ADR documentation. When in doubt about a design decision, this document is the reference.

---

## 1. System Overview

Applire is a JD-driven CV tailoring platform with three first-class consumers:

| Consumer | Entry Point | Auth |
|---|---|---|
| Human (browser) | Next.js frontend → nginx → FastAPI | `NoAuthProvider` in Community (single-user) |
| AI Agent (local) | MCP stdio server (`python -m applire.mcp`) | `NoAuthProvider` in Community |
| Developer | REST API at `:8001/docs` | `NoAuthProvider` in Community |

The core workflow is always: **JD analysis → CV import → Gap analysis → Interview → CV generation**.

---

## 2. Design Principles

Every architecture decision traces back to one or more of these principles. If a proposed change violates them, it needs a new ADR.

| Principle | What it means in practice |
|---|---|
| **JD-First** | Job description drives all downstream logic. No tailoring without a JD. |
| **Stateful Backend** | Complex reasoning lives server-side. The frontend is a thin UI. Never move interview or flow logic to the client. |
| **Accumulate, Don't Overwrite** | The Master Profile grows richer over time. New data enriches it; it is never replaced. |
| **Provider Abstraction** | Auth, LLM, Storage, and OCR are all pluggable via the same factory pattern. Community ships sensible defaults; Cloud overrides without touching Community code. |
| **GDPR by Design** | Every model that stores personal data carries `expires_at` or `updated_at` + `deleted_at` from the start. Retention is automated, not manual. |
| **MCP Agent Parity** | All user-facing features must be accessible as MCP tools. Agents are a first-class consumer, not an afterthought. |
| **Open Core Discipline** | Community code (`applire.*`) and Cloud code (`applire.cloud.*`) live in separate repositories. They never mix at the source level. |

---

## 3. Architecture Decisions

### ADR-001 — JD-First Intake & Analysis

**Decision:** JD analysis happens before CV parsing. Everything downstream is informed by the JD.

**Scraping tiers:**
1. httpx + BeautifulSoup (fast, most sites)
2. Playwright/Chromium (JS-heavy sites)
3. Manual paste fallback (login-gated or hostile sites — we deliberately skip server-side scraping of these)

**Why:** Higher tailoring quality. Extracting JD requirements first lets gap detection and interview questioning be precise rather than generic. Tiered scraping maximises URL success rate without legal risk (no LinkedIn scraping).

**Consequence to watch:** Playwright adds ~400MB to the Docker image. This is intentional and shared with the PDF generation pipeline.

---

### ADR-002 — Master Profile & JSONB Persistence

**Decision:** One `master_profiles` row per user, with the full profile stored as PostgreSQL JSONB in `profile_json`. 1:1 relationship (`users` ↔ `master_profiles`).

**Why JSONB:** The profile schema evolves rapidly (new sections, sub-fields, metadata). JSONB avoids migration churn for schema additions while enabling structured queries via JSON operators. PostgreSQL 16 is required; SQLite is used only in unit tests (via `JSONB().with_variant(JSON(), "sqlite")`).

**Why 1:1:** Multi-user tenancy is Cloud-only (ADR-011). The Community Edition is single-user by design, and the data model reflects this cleanly.

**Conflict handling:** True conflicts (e.g., contradicting `start_date` for the same job) are stored in `profile_json.metadata.pending_conflicts` and must be resolved via `POST /api/profile/conflicts/{id}/resolve`. They are never auto-resolved.

---

### ADR-004 — Stateful Backend for Interview Orchestration

**Decision:** All interview state is stored in the `interview_sessions` table. The backend owns the conversation loop via a custom 4-node async state machine:

```
GapDetector → QuestionGenerator → ResponseParser → ProfileUpdater
```

**Why not LangGraph:** LangGraph was evaluated and deemed over-engineered for a 4-node linear graph. The custom state machine is simpler, has no additional dependencies, and is independently testable per node. LangGraph may be revisited if the workflow grows to 8+ nodes with conditional back-edges.

**Two modes:**
- **MODE A (Targeted):** User has profile data. Focuses on filling specific gaps from gap analysis. 3–12 questions.
- **MODE B (Guided):** New user, no CV. Builds the profile section by section. 10–20 questions.

Mode is auto-detected at session creation from `completeness_score` vs `MODE_B_COMPLETENESS_THRESHOLD` (0.3), but can be overridden.

**Key invariant:** One active session per `(user_id, job_id)`. `POST /api/session` is idempotent — returns the existing session with `resumed: true` if one exists.

---

### ADR-005 — GDPR Retention Worker

**Decision:** A dedicated `retention` service in Docker Compose runs `python -m applire.retention` daily and enforces four TTL rules:

| Entity | TTL | Action |
|---|---|---|
| `uploads` | 7 days | Hard delete |
| `interview_sessions` | 30 days | Hard delete |
| `generated_cvs` / `generated_cover_letters` | 90 days (human) / 24 hours (agent) | Hard delete at `expires_at` |
| `master_profiles` / `users` | 730 days inactivity | Soft delete (`deleted_at`) |

**Why a separate service:** Data hygiene is a core operational concern, not an optional feature. The retention service is never profile-gated.

**Consequence:** Every model that holds personal data must carry `expires_at` (transient data) or `updated_at` + `deleted_at` (permanent data) from the first migration. This is non-negotiable.

All TTL values are configurable via environment variables in `applire/constants.py` — self-hosters can adjust them for jurisdiction-specific requirements.

---

### ADR-006 — CSS-Based Themes for PDF Generation

**Decision:** CVs are rendered via Jinja2 HTML + embedded CSS, with Playwright/Chromium producing the final PDF. The **same HTML is served to the frontend for live browser preview** (via `GET /api/cv/{id}/html`, injected into an `<iframe srcDoc=...>`).

**Why this matters:** There is no separate preview renderer. The preview and the PDF are guaranteed to be identical because they use the same Jinja2 template. This means:
- Theme changes only require CSS.
- Community contributors can add themes without touching Python code.
- Never use `<iframe src=...>` for CV preview — cross-origin framing is blocked by Firefox CSP. Always use `srcDoc`.

**PDF generation is async:** `generate_cv` returns immediately with `status: "pending"`. The frontend/agent polls `GET /api/cv/{id}/status` until `status: "ready"`.

**Page break control:** `avoid_page_breaks: bool` (default `True`) gates CSS rules that prevent entries from splitting across page boundaries. Can be disabled for compact layouts.

---

### ADR-007 — Open Core Architecture (AGPL-3.0)

**Decision:** Community Edition is AGPL-3.0. AGPL was chosen over MIT/Apache specifically to close the "SaaS loophole" — anyone hosting a modified version as a network service must release their modifications.

**API consumers are not derivative works:** An AI agent or application calling the MCP or REST API is not creating a derivative work under AGPL. The license restriction applies to hosting and distributing the software itself.

---

### ADR-008 — Auth Abstraction (Pluggable Backends)

**Decision:** An `AuthProvider` abstract base class lives in `applire/auth/base.py`. The factory in `applire/auth/__init__.py` instantiates the correct backend from `AUTH_PROVIDER`.

| `AUTH_PROVIDER` | Implementation | When to use |
|---|---|---|
| `none` (default) | `NoAuthProvider` — returns a fixed stub user | Community Edition, local single-user |
| `zitadel` | `ZitadelProvider` (Cloud only) | Cloud Edition, OIDC via self-hosted Zitadel |
| `oidc` | Generic OIDC (Cloud only) | Keycloak, Authentik, etc. |

**Router convention:** All routers declare `_auth: AuthProvider = Depends(get_auth_provider)`. The `_` prefix signals "infrastructure present, enforcement deferred" — the dependency is wired but unused in Community handlers. This allows Cloud backends to override without touching router code.

**Community stub:** `NoAuthProvider` returns a constant `User(id=<fixed UUID>, email="local@applire.community")`. There is one user, no login required.

---

### ADR-009 — LLM Provider Abstraction

**Decision:** An `LLMProvider` abstract base class with `acomplete()` and `aparse_json()` methods. Backend selected via `LLM_PROVIDER` environment variable.

| `LLM_PROVIDER` | Provider | Notes |
|---|---|---|
| `openrouter` (default) | OpenRouter API | Multi-model gateway; access Mistral, Claude, and others with one key |
| `mistral` | Mistral AI SDK | EU-hosted, GDPR-native, strong German proficiency |
| `openai` | OpenAI SDK | Also supports LM Studio and any OpenAI-compatible endpoint via `OPENAI_BASE_URL` |
| `ollama` | Ollama REST API | Fully offline, no API costs |

**Why direct SDKs over LangChain:** Consistent with the decision not to use LangGraph (ADR-004). Reduces the dependency surface and keeps the provider contract narrow and testable.

**Temperature defaults:** `0.4` for question generation, `0.1` for structured JSON parsing.

---

### ADR-012 — Edition Gating (Import-Based Detection)

**Decision:** Edition detection uses Python import presence, not an environment variable:

```python
# applire/edition.py
try:
    import applire.cloud
    HAS_CLOUD_EDITION = True
except ImportError:
    HAS_CLOUD_EDITION = False
```

All runtime checks use `if HAS_CLOUD_EDITION`. Cloud-only service methods return HTTP 402 with an upgrade prompt in Community Edition.

**Why import-based, not env-var:** An env-var (`APPLIRE_EDITION=cloud`) creates the false impression that setting it unlocks Cloud features in a Community install. It doesn't — the code doesn't exist. The import approach is honest: if the module isn't installed, the feature doesn't exist.

**Two-repository model:**
- `applire` (this repo, AGPL-3.0): Community Edition, `applire.*` namespace only.
- `applire-cloud` (private, proprietary): Imports `applire` as a dependency, adds `applire.cloud.*`.

Cloud code **never appears** in this repository.

---

### ADR-013 — Additive Profile Enrichment

**Decision:** The Master Profile uses an **accumulation-first** merge model. The conflict bar is deliberately high.

| Scenario | Action |
|---|---|
| Different job titles for the same position | Accumulate into `role_aliases[]` |
| Different responsibility bullets | Union into `responsibilities[]` |
| Different `start_date` for the same position | **Flag as conflict** |
| Same skill, different proficiency levels | Keep higher, no conflict |
| Company name variant ("Siemens AG" vs "Siemens") | Normalise, no conflict |

**Rule of thumb:** If both values can be true simultaneously, accumulate. If only one can be true, flag.

**Why:** A professional legitimately describes the same role differently across CVs targeting different audiences. "Team Lead" and "2nd Level Support Engineer" for the same job are both true. Treating them as a conflict creates friction and discards valid data. `role_aliases[]` gives the CV tailoring engine a rich palette to select from per application.

Source tracking (an `EnrichmentRecord` for every change) is mandatory — every field value is always traceable to its origin.

---

### ADR-014 — CV Upload & Parsing Pipeline

**Decision:** Two semantically distinct endpoints:
- `POST /api/profile/upload` — Human-facing, multipart file ingestion (PDF, DOCX, images, plain text).
- `POST /api/profile/import` — Structured data ingestion (LinkedIn ZIP exports, XING OAuth responses, JSON).

**OCR backends** (same factory pattern as LLM/Auth/Storage):

| `OCR_BACKEND` | Implementation | Notes |
|---|---|---|
| `mistral_vision` (default) | Mistral `pixtral-12b` via vision payload | Zero system deps, works out of the box |
| `tesseract` | `pytesseract` + local Tesseract | Fully offline; requires system dep via `docker-compose.override.yml` |

**JD context is optional on upload.** Requiring a JD before uploading a CV would block new-user onboarding. A JD-aware extraction prompt is used when `job_id` is provided; a generic prompt is used otherwise.

---

### ADR-016 — Flow Orchestrator State Machine

**Decision:** A `flow_sessions` table tracks the end-to-end user journey. Step transitions are validated against a `VALID_TRANSITIONS` dict in `applire/services/flow/orchestrator.py`.

**Linear DAG:**
```
jd_analysis → cv_import → gap_analysis → interview → cv_generation → complete
```

Key invariants:
- One `flow_session` per `(user_id, job_id)`, enforced by a unique constraint.
- `user_type` (`"new"` | `"returning"`) is resolved once at flow creation and is **immutable** for the lifetime of the flow.
- Steps that produce artifacts (gap analysis, interview, cv generation) require `artifact_id` in `AdvanceFlowRequest` — missing `artifact_id` returns HTTP 422.
- Invalid step transitions return HTTP 409 with `allowed_transitions` for client recovery.
- `flow_sessions` carries no PII — it is a routing record. GDPR TTLs live on child records.

---

### ADR-019 — CV Section Editor (Snapshot + Override)

**Decision:** Two JSONB columns on `generated_cvs`:
- `content_snapshot`: the structured rendering context, populated at generation time.
- `section_overrides`: user edits keyed by section ID, initially `{}`.

Re-rendering on section save uses Jinja2 only (fast, no Playwright). Playwright is only invoked on final PDF download.

**Dual save path:**
- `save_to_profile: false` (default for free-text edits) → writes to `section_overrides` only; Master Profile unchanged.
- `save_to_profile: true` (default for Kaile-assisted edits) → writes to `section_overrides` AND posts through the existing profile merge pipeline (ADR-013).

**Why not a separate `cv_documents` table:** JSONB columns on `generated_cvs` are proportional to the use case and keep the profile as the single source of truth. A new first-class model would add schema overhead for a feature that is fundamentally about transient display edits.

---

### ADR on Frontend API Routing (arc42 §7.1)

**Decision:** `NEXT_PUBLIC_API_URL` is set to `""` (empty string) in Docker Compose. All frontend `fetch()` calls use relative paths (e.g. `/api/profile/exists`). The browser resolves these against the current origin — no configuration needed regardless of hostname, IP, or DHCP lease.

**Why this matters:** Self-hosters do not need to know or configure their server's IP address. The nginx reverse proxy at port 80 routes `/api/*` to the backend container. This is the recommended access point for the full stack.

| Host port | Purpose |
|---|---|
| **80** | nginx — primary entry point (recommended) |
| 3000 | Next.js frontend (dev convenience) |
| 8001 | FastAPI backend (dev convenience) |
| 5433 | PostgreSQL (dev convenience) |

---

## 4. Data Model Highlights

### Master Profile JSONB Shape

```json
{
  "personal_info": { "name": "string", "email": "string", "phone": "string", ... },
  "work_experience": [{
    "id": "uuid",
    "company": "string",
    "role": "string (primary title)",
    "role_aliases": ["Team Lead", "2nd Level Support Engineer"],
    "start_date": "2020-01",
    "end_date": "2023-06",
    "responsibilities": ["bullet 1", "bullet 2"],
    "achievements": ["achievement 1"],
    "technologies": ["Python", "FastAPI"]
  }],
  "skills": [{ "name": "Python", "proficiency": "expert", "years_experience": 8 }],
  "education": [{ "id": "uuid", "degree": "M.Sc.", "institution": "string", "year": 2015 }],
  "certifications": [],
  "languages": [],
  "metadata": {
    "completeness_score": 0.85,
    "pending_conflicts": [],
    "enrichment_history": []
  }
}
```

### Key Tables

| Table | Purpose | GDPR TTL |
|---|---|---|
| `users` | Identity record | Soft-delete after 730d inactivity |
| `master_profiles` | JSONB career data | Soft-delete after 730d inactivity |
| `job_analyses` | Parsed JD data | No TTL (not PII) |
| `gap_analyses` | Gap detection results | No TTL (linked to job) |
| `interview_sessions` | Interview state (JSONB) | 30-day hard delete |
| `flow_sessions` | Journey routing record | No TTL (no PII) |
| `generated_cvs` | PDF + snapshot + overrides | 90d (human) / 24h (agent) |
| `uploads` | Raw uploaded files | 7-day hard delete |

---

## 5. Community vs. Cloud Boundary

This repository is the Community Edition. The table below documents what is and is not in scope.

| Feature | Community | Cloud |
|---|---|---|
| Master Profile (JSONB, enrichment, conflicts) | ✅ | ✅ |
| JD analysis + gap detection | ✅ | ✅ |
| Interview Orchestrator (Mode A + B) | ✅ | ✅ |
| CV generation (Classic German, Modern Swiss) | ✅ | ✅ (+ premium themes) |
| CV Section Editor (Finetuner) | ✅ | ✅ |
| Cover letter generation | ✅ | ✅ |
| MCP Server (stdio) | ✅ | ✅ |
| Flow Orchestrator | ✅ | ✅ |
| GDPR Retention Worker | ✅ | ✅ |
| Auth enforcement (OIDC/Zitadel) | Interface only | ✅ |
| Managed hosting | ❌ | ✅ |
| MCP Cloud Layer (SSE + auth + metering) | ❌ | ✅ |
| B2B multi-tenancy (RLS) | ❌ | ✅ |
| Recruiter Intelligence | ❌ | ✅ |
| S3 storage backend | ❌ | ✅ |
| Analytics dashboard + billing (Paddle) | ❌ | ✅ |

---

## 6. Testing Strategy Summary

Three tiers (see `docs/TESTING.md` for full details):

| Tier | When | Blocking |
|---|---|---|
| Unit tests (`pytest tests/unit/`) | Local, pre-commit | No (advisory) |
| CI: unit + integration + E2E | GitHub Actions, post-commit | **Yes** |
| Manual QA | Pre-rollout | **Yes** |

Coverage gate: `≥75%` backend unit coverage (`--cov-fail-under=75`).

**All CI tests mock LLM providers** — never call real Mistral/OpenAI/OpenRouter in CI. Unit tests run without Docker. Integration tests spin up the full Docker stack automatically.

**Module system:** All JavaScript/TypeScript uses ES modules (`"type": "module"` in both root and `frontend/package.json`). Never use `require()` in test files.

---

## 7. Key Files Quick Reference

| File | Purpose |
|---|---|
| `backend/applire/constants.py` | All thresholds, TTLs, edition flags |
| `backend/applire/services/flow/orchestrator.py` | Flow state machine — `VALID_TRANSITIONS` |
| `backend/applire/services/interview/signals.py` | Done-signal detection (deterministic, no LLM) |
| `backend/applire/auth/base.py` | `AuthProvider` ABC |
| `backend/applire/providers/` | LLM, OCR, Storage factories |
| `backend/applire/routers/cv.py` | CV HTML + PDF endpoints |
| `backend/applire/edition.py` | `HAS_CLOUD_EDITION` import-based detection |
| `frontend/components/cv/CVPreview.tsx` | CV preview (`srcDoc` pattern — never `src`) |
| `nginx/dev.conf.template` | nginx routing: `/api/*` → backend, `/*` → frontend |
