# Architecture Decision Records — Apliqa

This file contains the full content of all ADRs. The ADR index is maintained in [arc42.md](../product/architecture/arc42.md#9-architecture-decisions).

---

## #ADR-001: JD Intake & Analysis Architecture
**Date:** 2026-03-23  
**Status:** Accepted

### Context
As part of our user journeys, users need to provide both JD and CV / LinkedIN Profile for the creation of our tailored CV. 

### Decision
We implemented a "Job-First" architecture where JD intake is processed before the CV analysis, assuming both have been provided. This analysis informs all subsequent steps (CV parsing, gap detection, interview).

1. **Ingestion:** Supports Raw Text and a tiered automated URL pipeline.
2. **Tiered Scraping:** 
   - Tier 1: httpx + BeautifulSoup (Fast/Cheap)
   - Tier 2: Playwright/Chromium (JS-heavy sites)
   - Tier 3: Polished Fallback (LinkedIn/XING). We skip server-side scraping for hostile/login-gated sites to reduce risk.
3. **Analysis:** Mistral (mistral-large-latest) extracts into a structured 6-category schema.

### Consequences
- **Positive:** Higher tailoring quality.
- **Positive:** Reduced legal risk (no LinkedIn scraping).
- **Negative:** Minor friction for LinkedIn URL users (copy-paste required).
- **Infrastructure:** Docker image size increased by ~400MB for Playwright.

---

## #ADR-002: Master Profile & Data Persistence Strategy
**Date:** 2026-02-26  
**Status:** Accepted

### Context
The user's professional history must be stored in a "Master Profile" that acts as a career memory, enriched incrementally with every application. The same job position will naturally surface differently across CVs written for different audiences — "Team Lead" in a leadership-focused CV, "2nd Level Support Engineer" in a technical CV. Both are factually true simultaneously; they are different perspectives, not contradictions.

### Decision
1. **Persistence:** Use PostgreSQL **JSONB** for the `profile_json` storage. This allows for deep nesting and flexible schema evolution without frequent migrations.
2. **Model:** 1:1 relationship between `User` and `MasterProfileRecord`.
3. **Merge Logic — Accumulation First:** The primary merge behaviour is **accumulation, not conflict detection**. For a given position (matched by company + overlapping dates):
   - `responsibilities`, `achievements`, `technologies`: union of all values, deduplicated case-insensitively
   - `role_aliases`: every job title ever used for this position across CVs is preserved (e.g. `["Team Lead", "2nd Level Support"]`); the CV tailoring engine picks the most relevant one per application
   - Gap fields (`industry_context`, `team_size`, `budget_managed`, optional `personal_info` fields): filled silently if empty, never overwritten if already set
   - Skills: higher proficiency wins; higher `years_experience` wins — no conflict raised

   A **true conflict** is only raised for factual irreconcilabilities — values where only one can be correct at a time (e.g. contradicting `start_date` or `end_date`). The bar is high: if both values can be true simultaneously, they are accumulated, not flagged.

4. **Testing Strategy:** SQLAlchemy's `JSONB().with_variant(JSON(), "sqlite")` is used on the `profile_json` column so `Base.metadata.create_all` works with SQLite in unit tests, maintaining production integrity on PostgreSQL.
5. **Conflict Persistence:** True conflicts (date contradictions, irreconcilable field values) are stored persistently in `metadata.pending_conflicts` within the JSONB profile. Users resolve these via `POST /api/profile/conflicts/{id}/resolve` with `{ "resolution": "existing" | "incoming" | "manual", "value": any }`.
6. **Interface Standardization:** All completeness-related methods are standardized as `calculate_completeness` across Service and Router layers for consistency.

### Consequences
- **Positive:** Extreme flexibility for evolving CV sections (Skills, Volunteer work, etc.).
- **Positive:** Full audit trail via enrichment logs.
- **Positive:** `role_aliases` gives the CV tailoring engine a rich palette — leadership CV picks team-lead bullets; technical CV picks engineering bullets — from a single Master Profile.
- **Positive:** Dramatically fewer false-positive conflicts (most apparent differences are accumulation, not contradiction), reducing user friction.
- **Negative:** Requires PostgreSQL for full integration testing of JSONB-specific operators.

## #ADR-003: Paddle as Merchant of Record
**Date:** 2026-02-26
**Status:** Accepted

### Context
Apliqa Cloud needs to accept payments from EU customers. As a German UG
(haftungsbeschränkt) operating as a Nebengewerbe, handling VAT compliance across
multiple EU member states is operationally prohibitive for a solo founder.

### Decision
Use **Paddle** as Merchant of Record (MoR). Paddle handles:
- Payment processing (credit card, PayPal, etc.)
- VAT calculation, collection, and remittance for all EU jurisdictions
- Invoice generation compliant with AO §147 (10-year retention)
- Subscription management and usage-based billing

Credit management is handled in PostgreSQL via Paddle webhooks:
- `subscription.created` / `subscription.updated` → update `users.credits`
- `transaction.completed` → credit top-up for usage-based purchases
- Webhook signature verification on all inbound events

### Rationale
1. MoR model eliminates VAT registration burden across EU member states.
2. Paddle is EU-friendly and supports EU-based entities.
3. Webhook-driven credit management keeps billing state in our database,
   enabling offline credit checks without Paddle API calls.
4. AO §147 compliance is handled by Paddle's invoice retention.

### Consequences
- **Positive:** Zero VAT compliance overhead for the founder.
- **Positive:** Paddle handles refunds, chargebacks, and tax audits.
- **Negative:** Paddle takes a revenue share (~5-10%).
- **Negative:** Webhook reliability must be monitored; idempotent handlers required.
- **Edition:** Cloud only — Community Edition has no billing.

---

## #ADR-004: Stateful Backend for Interview Orchestration
**Date:** 2026-02-26
**Status:** Accepted

### Context
The interview process is a multi-turn conversational flow that must:
- Persist state across page reloads and device switches
- Support pause/resume (users may leave and return)
- Drive JD-aware, gap-targeted questioning
- Update the Master Profile incrementally with each answer

A frontend-stateful approach would lose state on navigation and prevent
multi-device continuity.

### Decision
All interview state is stored in the `interview_sessions` database table.
The backend owns the conversation loop via a custom 4-node async state machine
(`apliqa/services/interview_graph.py`):

1. **GapDetector** — loads current gaps from JD analysis vs. Master Profile
2. **QuestionGenerator** — produces the next targeted question
3. **ResponseParser** — extracts structured data from user's free-text answer
4. **ProfileUpdater** — merges extracted data into Master Profile

LangGraph was evaluated but deemed over-engineered for this 4-node workflow.
The custom state machine is simpler, has no additional dependencies, and
covers all current use cases. LangGraph may be revisited if the interview
workflow grows significantly in complexity (e.g., conditional back-edges,
8+ nodes).

**Reaffirmed 16 March 2026 (Iteration 14):** MODE B (Guided Build) does not
change the graph topology — it adds a dual-mode entry to the GapDetector node
(consumes GapAnalysis in MODE A; generates a section plan in MODE B), but the
four nodes and their linear sequence are unchanged. ADR 004 rationale stands.

Two operating modes:
- **Targeted Gap-Fill:** For users with existing CVs — focuses on unstated
  or ambiguous qualifications identified by gap analysis.
- **Guided Build:** For new users (no CV) — systematically builds the
  Master Profile section by section.

The chat API (`POST /api/session/{id}/message`) targets <3s response time
per turn.

### Rationale
1. Backend-stateful design enables pause/resume and multi-device continuity.
2. Custom state machine keeps dependencies minimal while covering current workflow.
3. Each answer enriches the Master Profile, creating compounding value.
4. Interview sessions are subject to 30-day GDPR retention (ADR 005).

### Consequences
- **Positive:** Complex reasoning logic stays server-side; frontend is a thin chat UI.
- **Positive:** Session state survives browser crashes, device switches.
- **Positive:** Each state machine node is independently testable.
- **Negative:** Backend must handle concurrent sessions per user.
- **Negative:** <3s target requires careful LLM prompt optimization.
- **Negative:** Custom state machine means no built-in LangGraph tooling (graph visualization, tracing) unless adopted later.
- **Edition:** Community — available to all users and agents.

---


### ADR 005: Daily Cron for GDPR Retention Enforcement

**Status:** APPROVED

**Context:**
Apliqa stores personal data (profiles, CVs, interview transcripts). GDPR Art. 5(1)(e)
requires data minimisation and storage limitation. Self-hosters serving multiple users
need automated enforcement — manual deletion is not reliable.

**Decision:**
A dedicated `retention` service runs `python -m apliqa.retention` on a daily schedule
inside Docker Compose. The worker applies four TTL rules in sequence and emits a JSON
report to stdout for audit purposes.

TTL rules:
- `uploads`: hard-delete files older than 7 days (raw SQL; graceful no-op if table absent)
- `interview_sessions`: hard-delete records with `updated_at` older than 30 days
- `generated_cvs`: hard-delete records where `expires_at` is in the past (90-day TTL set at creation)
- `master_profiles` / `users`: soft-delete (set `deleted_at`) when `updated_at` older than 730 days (≈ 24 months); tombstone preserved for backup audit trail

**Rationale:**
1. A cron-based approach is predictable and audit-friendly (exact run timestamps in logs).
2. Soft-delete for user accounts satisfies GDPR's right-to-erasure traceability requirement.
3. Hard-delete for session data and CVs minimises storage and exposure surface.
4. The `retention` service is not profile-gated — data hygiene is a core operational concern, not an optional feature.
5. 730 days is the standard approximation for 24 calendar months in Python stdlib (no native month arithmetic).

**Consequences:**
- All models must carry `expires_at` or `updated_at` + `deleted_at` fields from the start (enforced from Iteration 0).
- The `uploads` rule uses raw `text()` SQL with a graceful `ProgrammingError` catch so the worker runs cleanly even before an `uploads` table exists.
- The `retention` service starts automatically with `docker compose up`; operators who want to disable it must explicitly remove the service.

---

## #ADR-006: CSS-based Themes for PDF Extensibility
**Date:** 2026-02-26
**Status:** Accepted

### Context
Apliqa generates ATS-compatible, DACH-market-appropriate CVs as PDFs.
The PDF generation pipeline must support multiple visual themes from day one,
be extensible by the community, and produce identical output in both the
browser preview (iframe) and the final PDF export.

### Decision
Use **Jinja2 HTML templates** with **embedded CSS** rendered by **Playwright
headless Chromium** for PDF generation. The same HTML/CSS is served to the
frontend iframe for live WYSIWYG preview.

Template structure:
- `backend/src/templates/cv_template.html` — Jinja2 HTML with CSS theme variables
- Themes are pure CSS overrides (colors, fonts, spacing, layout)
- Template handles both `german_lebenslauf` and `international` format variants

Initial themes:
- **Universal ATS** — MVP default, maximum ATS compatibility
- **Classic German** — Traditional Lebenslauf styling (Community)
- **Modern Swiss** — Clean, contemporary Swiss market style (Community)
- Premium themes available in Cloud Edition

The `PDFGenerator` service uses `Jinja2` for template rendering and
`asyncio.run_in_executor()` to run Playwright's synchronous PDF generation
without blocking the event loop. Generated PDFs are stored with a 90-day
TTL before auto-deletion (ADR 005).

### Rationale
1. CSS-based themes are the simplest extensibility model — no code changes needed.
2. Single rendering engine (Playwright/Chromium) ensures pixel-perfect parity
   between preview and export.
3. Community contributors can add themes by submitting CSS files.
4. Jinja2 is already in the stack (FastAPI ecosystem).

### Consequences
- **Positive:** Theme creation requires only CSS knowledge.
- **Positive:** Browser preview and PDF export are guaranteed identical.
- **Positive:** Community can contribute themes without touching Python code.
- **Negative:** Playwright/Chromium adds ~400MB to Docker image (shared with ADR 001 scraping).
- **Negative:** Complex layouts may require careful CSS-for-print testing.
- **Edition:** Core engine and basic themes in Community; premium themes in Cloud.

---


## #ADR-007: Open Core Architecture (AGPL-3.0)
**Date:** 2026-03-06
**Status:** Accepted

### Context
Apliqa needs a business model that balances open-source adoption with
sustainable revenue. The "SaaS loophole" in permissive licenses (MIT, Apache)
allows competitors to host the software as a service without contributing back.

### Decision
Adopt an **Open Core** model:

- **Community Edition (AGPL-3.0):** Core tailoring engine, Master Profile API,
  MCP Server (stdio), basic DACH templates, Interview Orchestrator, LLM Provider
  Abstraction, Auth Abstraction interface, Retention Worker, Docker Compose setup.
- **Cloud Edition (Proprietary):** Managed hosting, Auth enforcement (Zitadel OIDC),
  Recruiter Intelligence (GxP/Pharma), premium templates, B2B multi-tenancy,
  priority rendering, analytics dashboard, Paddle billing, MCP Cloud Layer
  (SSE + Auth + Metering).

The AGPL-3.0 license is deliberately chosen over MIT/Apache to close the
"SaaS loophole": any party hosting a modified version as a network service
must release their modifications under AGPL-3.0.

Cloud-only modules reside in the `apliqa.cloud.*` namespace and are excluded
from the AGPL-3.0 distribution.

### Rationale
1. AGPL-3.0 protects against "Cloud Cloning" — competitors cannot host a
   proprietary fork as SaaS without sharing modifications.
2. "Verifiable Trust" — users can audit the open-source core for GDPR compliance.
3. AI agents using the API/MCP are not creating derivative works — AGPL does
   not restrict API consumers.
4. Natural upgrade path: developers try Community locally, upgrade to Cloud
   for production (the "Ollama Effect").
5. Despite potential blanket AGPL bans in some large enterprises, the target
   market (individual professionals, career coaches, AI agents) is unaffected.

### Consequences
- **Positive:** Strong copyleft protection against SaaS competitors.
- **Positive:** Auditable codebase builds trust with privacy-conscious users.
- **Positive:** Community contributions flow back under AGPL-3.0.
- **Negative:** Some enterprises have blanket AGPL policies — mitigated by
  Cloud Edition offering.
- **Negative:** Requires disciplined namespace separation (`apliqa.cloud.*`).
- **Edition:** Defines the boundary between both editions.

---

### #ADR-008: Auth Abstraction Wrapper (Pluggable Backends)

**Status:** APPROVED

**Context:**
Community Edition self-hosters run Apliqa locally as a single user and need zero auth
friction. Cloud Edition requires Zitadel OIDC enforcement for multi-tenant SaaS.
The interface must live in the Community codebase so Cloud backends can implement it
without forking.

**Decision:**
An `AuthProvider` abstract base class lives in `apliqa/auth/base.py` with a single
async method `get_current_user(request) → User | None`. The factory in
`apliqa/auth/__init__.py` instantiates the correct backend from the `AUTH_PROVIDER`
environment variable (mirrors the LLM provider pattern from ADR 009).

Community ships one implementation:
- `NoAuthProvider` (`apliqa/auth/no_auth.py`): returns a fixed hardcoded stub `User`
  (constant UUID, email `local@apliqa.community`). Zero enforcement.

Cloud Edition ships additional backends (proprietary):
- `ZitadelProvider`: validates Zitadel OIDC JWTs
- `OIDCProvider`: generic OIDC (Keycloak, Authentik, etc.)
- `APIKeyProvider`: static or DB-backed API-key validation

**FastAPI wiring convention:**
All routers declare `_auth: AuthProvider = Depends(get_auth_provider)`. The `_` prefix
signals "infrastructure wired, enforcement deferred" — the parameter is unused in
Community handlers but present in the dependency graph so Cloud backends can override
it without touching router code.

**Rationale:**
1. Community self-hosters running locally don't need identity management.
2. The interface must exist in Community so Cloud backends implement a stable contract.
3. Mirroring the LLM provider pattern keeps the codebase consistent and learnable.
4. The `_auth` parameter convention avoids linter warnings while communicating intent.

**Consequences:**
- `AUTH_PROVIDER=none` is the default; behaviour is identical to the MVP (no breaking change).
- Cloud backends implement `AuthProvider` and register via the factory — no router changes needed.
- `NoAuthProvider.get_current_user()` is `async def` even though it does no I/O, to satisfy the ABC and FastAPI's `Depends()` contract.

---


## #ADR-009: LLM Provider Abstraction Layer
**Date:** 2026-03-06
**Status:** Accepted

### Context
Apliqa uses Mistral AI as the default LLM provider (EU-hosted, strong German
proficiency). However, self-hosters may prefer OpenAI or local models via Ollama.
The system must support multiple LLM backends without changing service code.

### Decision
Implement an `LLMProvider` abstract base class that standardizes all LLM
interactions across the application:

```python
class LLMProvider(ABC):
    @abstractmethod
    async def acomplete(self, messages, **kwargs) -> str: ...

    @abstractmethod
    async def aparse_json(self, messages, schema, **kwargs) -> dict: ...
```

Backend selection via `LLM_PROVIDER` environment variable:
- `mistral` (default) — `mistralai` SDK directly, EU-hosted
- `openai` — `openai` SDK; `OPENAI_BASE_URL` can point to any OpenAI-compatible endpoint (LM Studio, etc.)
- `ollama` — Ollama REST API (`/api/chat`) called via `httpx`; fully offline

Each provider implementation handles:
- Provider-specific API authentication (env vars: `MISTRAL_API_KEY`,
  `OPENAI_API_KEY`, `OLLAMA_BASE_URL`)
- Temperature defaults (`0.2` for structured extraction)
- JSON parsing with `ensure_ascii=False` for German umlauts
- Error handling and timeout enforcement (`asyncio.wait_for`)

### Rationale
1. Vendor independence — no lock-in to a single LLM provider.
2. Self-hosters can run fully offline with Ollama.
3. Mirrors the Auth Abstraction pattern (ADR 008) for consistency.
4. Direct SDKs preferred over LangChain wrappers — aligns with the decision
   not to use LangGraph (ADR 004); reduces dependency surface.

### Consequences
- **Positive:** Self-hosters can use free local models (Ollama).
- **Positive:** Easy to add new providers (Anthropic, Groq, etc.).
- **Positive:** Consistent interface across all services.
- **Negative:** Provider-specific features (e.g., Mistral's function calling
  nuances) may require adapter logic.
- **Negative:** Testing requires mocking the provider interface.
- **Edition:** Community — available to all deployments.

---

### #ADR-010: MCP Server — Agent-First Platform

**Status:** APPROVED (amended 09 March 2026)

**Context:**
The MCP Server is Apliqa's primary distribution channel for AI agent consumers.
The question arose whether to place MCP entirely in Community, entirely in Cloud,
or to split it across editions.

**Decision:**
Split-layer architecture:
- **Layer 1 (Community):** Core MCP tools + stdio transport. No auth, no rate
  limiting. This is the discovery and adoption channel.
- **Layer 2 (Cloud):** SSE transport, API-Key auth, rate limiting, usage metering.
  This is the production and revenue channel.
- **Layer 3 (Cloud):** Cloud-only tools (`recruiter_intelligence_analyze`,
  `get_analytics`, `manage_team`). These expose proprietary Cloud features
  to agents.

**Rationale:**
1. The Community MCP server is the top-of-funnel for agent adoption (the "Ollama
   effect" — developers try locally, then upgrade for production).
2. AGPL-3.0 protects against cloud cloning of the core tools.
3. Revenue is captured at the transport layer (SSE + auth + metering), not the
   tool layer.
4. Agents calling tools via stdio/SSE are not derivative works under AGPL.

**Consequences:**
- The `apliqa.mcp` module is part of the AGPL-3.0 distribution.
- The `apliqa.cloud.mcp` module (SSE adapter, auth middleware, metering,
  cloud-only tool registrations) is proprietary.
- MCP marketplace listings can advertise "free & open-source" with a Cloud
  upgrade path.

---

## #ADR-011: Multi-Tenancy for B2B/Team Support (RLS)
**Date:** 2026-03-06
**Status:** Accepted

### Context
Specialist recruiters (Jason persona) and B2B customers need to manage multiple
candidates and mandates under a single agency account. Data isolation between
tenants is critical for GDPR compliance and client confidentiality. The B2B
recruiter workflow requires team member management (admin, recruiter, viewer roles)
and per-mandate candidate filtering.

### Decision
Implement multi-tenancy using PostgreSQL **Row-Level Security (RLS)** with a
`tenant_id` column on cloud-only data tables.

- The `tenant_id` is added to the `users` table (nullable — `NULL` for
  individual B2C users, populated for B2B team members).
- RLS policies enforce that queries only return rows matching the current
  session's `tenant_id`.
- The tenant context is set per-request via `SET LOCAL apliqa.tenant_id = '...'`
  in the database session.
- Cloud-only module: `apliqa.cloud.tenancy` handles tenant provisioning,
  member management, and RLS policy setup.

### Rationale
1. RLS provides database-level isolation — even application bugs cannot
   leak data across tenants.
2. `tenant_id` on the `users` table is the minimal schema change needed.
3. PostgreSQL RLS is battle-tested and requires no application-level
   query filtering.
4. Career coaches (B2B persona) are a key revenue segment.

### Consequences
- **Positive:** Strong data isolation at the database level.
- **Positive:** No application-level tenant filtering needed — RLS handles it.
- **Positive:** Scales to many tenants without schema changes.
- **Negative:** RLS policies add complexity to database migrations.
- **Negative:** Debugging tenant-scoped queries requires awareness of RLS context.
- **Edition:** Cloud only — Community Edition is single-user, no tenancy needed.

---
## #ADR-012: Feature-Flag Based Edition Gating
**Date:** 2026-03-06
**Status:** Accepted

### Context
Apliqa operates as an Open Core product with Community and Cloud editions
(ADR 007). A clean mechanism is needed to gate Cloud-only features at runtime
while maintaining strict license separation between the AGPL-3.0 core and
proprietary Cloud code.

### Decision
**Two-repository model** with a shared edition-gating mechanism:

- **`apliqa`** repository (AGPL-3.0): Contains the complete Community Edition.
  All core modules live under the `apliqa.*` namespace. The environment variable
  `APLIQA_EDITION` defaults to `community`.
- **`apliqa-cloud`** repository (Proprietary): Depends on `apliqa` as a
  package/base layer and extends it with the `apliqa.cloud.*` namespace.
  Sets `APLIQA_EDITION=cloud`.

**Runtime gating** via `APLIQA_EDITION` environment variable (`community` | `cloud`):

- **Service-level checks:** Cloud-only service methods are annotated with an
  edition check. In the Community Edition (where Cloud code is absent), these
  entry points return HTTP 402 (Payment Required) with an upgrade prompt
  pointing to Apliqa Cloud.
- **Namespace separation:** All Cloud-only code resides in `apliqa.cloud.*`
  within the `apliqa-cloud` repository. This namespace never exists in the
  `apliqa` repository — there is no build-time stripping.
- **Feature matrix:** Appendix A of the arc42 document maintains the
  authoritative feature-by-edition matrix.

Gating points:
1. REST API routers — Cloud-only endpoints return 402 with upgrade URL
2. MCP tools — Cloud-only tools return edition upgrade prompt
3. Service layer — Cloud-only service methods check `APLIQA_EDITION`
4. Template selection — Premium templates gated at PDF Generator

### Rationale
1. Two repositories enforce license separation at the source level — no risk
   of accidentally shipping proprietary code under AGPL-3.0.
2. The `apliqa-cloud` repo imports `apliqa` as a dependency, ensuring Cloud
   always builds on the latest Community core (upstream-first development).
3. `APLIQA_EDITION` remains the single runtime toggle — the same gating code
   works regardless of which repo built the deployment artifact.
4. 402 status code communicates "upgrade available" semantically.
5. Contributors to the AGPL-3.0 repo never see or interact with proprietary
   code — clean contributor experience.

### Consequences
- **Positive:** License separation is structural (repo boundary), not procedural
  (build-step exclusion). Eliminates accidental AGPL contamination of Cloud code
  or proprietary leakage into the open-source repo.
- **Positive:** Clear upgrade path for Community users (402 responses include
  Cloud signup URL).
- **Positive:** `apliqa` repo is self-contained and fully functional — no
  "gutted" feeling for Community users.
- **Positive:** Clean open-source contributor experience — no proprietary
  markers or `<!-- cloud-only -->` sections in the core repo.
- **Negative:** Two repos require coordinated releases when shared interfaces
  change (e.g., `AuthProvider` ABC, `LLMProvider` ABC).
- **Negative:** `apliqa-cloud` must track `apliqa` as an upstream dependency —
  version pinning and integration testing needed.
- **Negative:** Developers working on Cloud features need both repos checked out.
- **Edition:** Defines the gating mechanism and repository boundary for both editions.

### Amendment (2026-03-27): Import-Based Detection Replaces `APLIQA_EDITION` Flag

**Rationale:** The `APLIQA_EDITION` environment variable was a runtime toggle, but it created a false impression that switching the flag would unlock Cloud features in the Community Edition (it does not — the code does not exist). The two-repository model already provides structural separation: `apliqa.cloud.*` modules are physically absent in Community Edition.

**Updated Decision:**

Edition detection is now **import-based** rather than environment-variable-based:

```python
# In apliqa/config.py or a dedicated apliqa/edition.py module
try:
    import apliqa.cloud  # This import succeeds only in apliqa-cloud repo
    HAS_CLOUD_EDITION = True
except ImportError:
    HAS_CLOUD_EDITION = False
```

All runtime checks that previously used `if settings.APLIQA_EDITION == "cloud"` are replaced with `if HAS_CLOUD_EDITION`.

**Consequences of the amendment:**
- **Positive:** Edition detection is now tied to code presence, not configuration. No risk of misconfiguration (e.g., setting `APLIQA_EDITION=cloud` in Community Edition and expecting features to work).
- **Positive:** Clearer mental model: "If the module can be imported, the feature exists."
- **Positive:** Eliminates the `APLIQA_EDITION` environment variable entirely, reducing configuration surface.
- **Negative:** Requires a one-time refactor of all edition checks across the codebase (service layer, routers, MCP tools). This is a non-breaking change if done correctly.
- **Implementation:** Sprint 5 Task 19.13 handles the refactor.

---

## #ADR-013: Additive Profile Enrichment Model
**Date:** 2026-03-15
**Status:** Accepted

### Context
The Master Profile is enriched incrementally from multiple sources over time:
CV uploads, guided interviews, LinkedIn/XING PDF imports, and MCP agent calls.
A naive merge implementation would treat differences between sources as conflicts
requiring user resolution — e.g. "Team Lead" from one CV vs. "2nd Level Support
Engineer" from another CV for the same position.

This is incorrect. A professional applies to different roles and naturally
emphasises different facets of the same experience depending on the target
position. Both titles and both sets of responsibilities can be simultaneously
true. Treating them as a conflict creates unnecessary friction and, worse,
causes the system to discard valid information.

The system needs a principled, documented rule for when to accumulate vs. when
to flag a conflict, so that all engineers building importers, the interview
flow, and the CV tailoring engine operate from the same mental model.

### Decision
The Master Profile uses an **accumulation-first** merge model. New information
from any source extends existing entries rather than replacing them. A conflict
is only flagged when two values are **factually irreconcilable** — i.e. both
cannot simultaneously be true.

#### Rule 1 — Accumulate by default
List-type fields on `WorkEntry` are unioned across all imports:
- `responsibilities[]` — all bullet points from all sources, deduplicated
- `achievements[]` — all achievement statements, deduplicated
- `technologies[]` — set union, case-normalised
- `role_aliases[]` — every job title ever used for this position is preserved

The `role_aliases[]` field is the canonical mechanism for preserving multiple
titles for the same position. The primary `role` field holds the most recently
imported or user-confirmed title. The CV tailoring engine selects the most
relevant title and bullet set per application from this accumulated pool.

#### Rule 2 — Conflict bar is high
A conflict is only raised for values where only one can be correct:

| Scenario | Action |
|---|---|
| Different role titles, same position | Accumulate into `role_aliases[]` |
| Different responsibility bullets | Union into `responsibilities[]` |
| Different `start_date` for same position | Flag as conflict |
| Different `end_date` for same position | Flag as conflict |
| Different degree type, same institution/period | Flag as conflict |
| Same skill, different proficiency level | Keep higher proficiency, no conflict |
| Company name variant ("Siemens AG" vs "Siemens") | Normalise, no conflict |
| Degree abbreviation variant ("M.Sc." vs "Master of Science") | Normalise, no conflict |

The rule of thumb: **if both values can be true at the same time, accumulate.
If only one can be true, flag.**

#### Rule 3 — Semantic deduplication
Bullet points and responsibilities are deduplicated by semantic similarity
before storage, not by exact string match. Near-duplicate bullets from two
CVs describing the same activity are collapsed into one canonical form.
The deduplication strategy (embedding similarity or LLM-based) is an
implementation detail left to the service layer.

#### Rule 4 — Source tracking is mandatory
Every addition to the profile — whether accumulation or conflict resolution —
must produce an `EnrichmentRecord` with `source`, `source_session_id`,
`changes[]`, and `confidence`. The origin of every field value is always
traceable. This is non-negotiable.

#### Rule 5 — No auto-resolution
Flagged conflicts are never resolved automatically. They are stored in
`ProfileMetadata.pending_conflicts` and surface to the user via
`GET /api/profile`. Resolution requires an explicit call to
`POST /api/profile/conflicts/{conflict_id}/resolve` with payload:

```json
{
  "resolution": "existing" | "incoming" | "manual",
  "value": null | <any>
}
```

`value` is required when `resolution` is `"manual"`. Resolved conflicts
are retained in history with a `resolved_at` timestamp — they are never
deleted.

#### MergeStrategy implementation contract
The `MergeStrategy` class in `apliqa/services/profile/merge.py` must
implement this model. The key method signatures are:

```python
def merge_work_experience(
    self,
    existing: list[WorkEntry],
    incoming: list[WorkEntry]
) -> MergeResult:
    """
    Matching rule: same company + overlapping date range = same position.
    Action: accumulate responsibilities, achievements, technologies, role_aliases.
    Only flag start_date / end_date contradictions as conflicts.
    Different company OR non-overlapping dates = new entry, append.
    """

def merge_skills(
    self,
    existing: list[Skill],
    incoming: list[Skill]
) -> MergeResult:
    """
    Matching rule: same skill name (case-normalised).
    Action: keep higher proficiency, keep higher years_experience, union sources.
    No conflicts raised for skills — higher value always wins.
    """

def detect_contradictions(
    self,
    existing: WorkEntry,
    incoming: WorkEntry
) -> list[Conflict]:
    """
    Only checks factually irreconcilable fields: start_date, end_date.
    Does NOT flag role title differences — those go to role_aliases.
    """
```

### Rationale
1. A professional's career history is multi-faceted, not single-valued. The
   same experience is legitimately described differently depending on the
   audience. Discarding any of these descriptions reduces the quality of
   future CV tailoring.
2. Accumulating `role_aliases[]` and a rich bullet pool gives the CV tailoring
   engine (Iteration 5 / CV Generation) the raw material to produce genuinely
   personalised output per application — selecting the most relevant title and
   bullets for each target role.
3. A low conflict bar creates user fatigue. If the system flags every
   difference as a conflict, users will either abandon the flow or blindly
   dismiss conflicts, defeating the purpose.
4. Source tracking (Rule 4) ensures the accumulated model does not become
   opaque. Users and auditors can always trace where a bullet or title came from.
5. This model aligns with how experienced professionals actually manage their
   careers — they maintain a "master CV" with everything in it and tailor
   per application. Apliqa automates exactly that workflow.

### Consequences
- **Positive:** Significantly fewer conflicts surfaced to the user — only
  genuine factual contradictions require resolution.
- **Positive:** The CV tailoring engine has a richer, more accurate data pool
  to select from per application.
- **Positive:** Multiple CV imports feel additive and intelligent rather than
  destructive.
- **Positive:** Aligns with the product's core value proposition: the system
  learns about the user over time.
- **Negative:** `WorkEntry` carries more fields (`role_aliases[]`,
  accumulated list fields) — the schema is more complex than a naive model.
- **Negative:** Semantic deduplication of bullet points requires either an
  embedding similarity check or an LLM call — adds latency and cost to the
  import pipeline.
- **Negative:** The matching rule (same company + overlapping dates) must be
  robust to messy real-world data (company name variants, approximate dates).
  Normalisation logic in `detect_contradictions()` must be carefully tested.
- **Edition:** Community — the accumulation model applies to all editions.
  Cloud Edition inherits this behaviour unchanged.

---

## #ADR-014: CV Upload & Parsing Pipeline
**Date:** 2026-03-15
**Status:** Accepted

### Context
Iteration 12 introduces the ability to upload CVs in any common format (PDF, DOCX, image, plain text).
Several architectural decisions are needed before implementation can begin:

1. How does the new `/upload` endpoint relate to the existing `/import` endpoint?
2. How are scanned/image CVs handled without mandating heavy system dependencies for all deployers?
3. Is a JD analysis required before a CV can be uploaded, or optional?
4. How is the transient "DRAFT" state of a freshly uploaded profile represented — DB column or schema-level?
5. Where are uploaded files stored, and what metadata is tracked for billing and GDPR purposes?

### Decision

#### 1 — Endpoint Separation: `/upload` vs `/import`

Two endpoints with distinct semantic roles:

- **`POST /api/profile/upload`** — General-purpose, multipart CV ingestion. Accepts any file format a
  human might provide (PDF, DOCX, DOCX/DOC, JPEG/PNG, plain text). This is the canonical human-facing
  entry point for Iteration 12 and beyond.
- **`POST /api/profile/import`** — Structured data ingestor. Accepts LinkedIn ZIP exports, XING OAuth
  responses, and structured JSON. This is the target for V2.0 Iteration 14. Any PDF/DOCX handling
  currently stubbed in the `/import` router must migrate to `/upload`.

These are semantically different operations (file parsing vs structured data ingestion) and must not be
merged. Single Responsibility applies at the router level.

#### 2 — OCR Backend: Abstraction with Configurable Default

Image CV parsing is handled via a `CVImageExtractor` abstraction with two concrete implementations,
following the pattern of `LLMProvider` (ADR 009) and `AuthProvider` (ADR 008):

- **`MistralVisionExtractor`** (default): calls `pixtral-12b` via the existing `LLMProvider.acomplete()`
  interface with a vision payload. Zero system dependencies. Works out-of-the-box in Community Edition.
- **`TesseractExtractor`** (opt-in): uses `pytesseract` + a local Tesseract installation. Self-hosters
  who need fully offline OCR enable this via `OCR_BACKEND=tesseract` and install the system dependency
  via `docker-compose.override.yml`.

`OCR_BACKEND` environment variable: `mistral_vision` (default) | `tesseract`.

This falls under ADR 009's provider abstraction pattern — no new ADR needed for the OCR backend itself.

#### 3 — JD Context: Optional `job_id` Query Parameter

JD context is **optional** on `POST /api/profile/upload`. "Job-First" (ADR 001) is a quality preference
for tailoring, not a hard gate on profile ingestion. Requiring a JD analysis before CV upload would break
the new-user onboarding flow (CV import precedes gap analysis in the Iteration 15 flow).

Two prompt variants are defined in `apliqa/prompts/cv_extraction.py`:

- **Generic**: `GENERIC_CV_EXTRACTION_PROMPT` — used when no `job_id` is provided
- **JD-aware**: `JD_AWARE_CV_EXTRACTION_PROMPT` — injects `JobAnalysis` context when a valid `job_id`
  is provided; yields higher relevance scoring for JD-aligned sections

Both paths produce a valid `MasterProfileData`. The JD-aware path may yield a higher `completeness_score`
for JD-relevant sections — this is expected and desirable.

#### 4 — Upload Response: Dedicated `CVUploadResponse` Schema

`POST /api/profile/upload` returns a `CVUploadResponse` Pydantic schema, not the standard
`MasterProfileResponse`. No new database column is added.

```python
class CVUploadResponse(BaseModel):
    profile_id: UUID
    status: Literal["DRAFT", "COMPLETE"]
    completeness_score: float
    conflicts: list[ConflictSummary]
    enrichment_record_id: UUID   # traceability back to the EnrichmentRecord
    expires_at: datetime         # GDPR-aligned file TTL (7 days from upload)
```

`status` is computed inline in the endpoint handler:

```python
status = "DRAFT" if (response.completeness_score < 0.5 or bool(response.conflicts)) else "COMPLETE"
```

`MasterProfileResponse` is unchanged. `GET /api/profile` always returns the current profile state —
it does not expose a `status` field. This is consistent with ADR 013's enrichment model (the profile
is truth; upload state is transient).

#### 5 — File Storage: Local Default with `StorageProvider` Abstraction

Original uploaded files are stored during processing and subject to the 7-day GDPR TTL from ADR 005
(the Retention Worker already handles this via the `uploads` table).

**`StorageProvider` abstraction** (same pattern as `LLMProvider`, `AuthProvider`):
- **`LocalStorageProvider`** (Community default): writes to `UPLOAD_DIR` (env var, default `./data/uploads/`)
- **`S3StorageProvider`** (Cloud Edition): writes to S3-compatible storage — lives in `apliqa.cloud.*`

**`uploads` table schema:**

| Column             | Type        | Notes                                         |
|--------------------|-------------|-----------------------------------------------|
| `id`               | UUID PK     |                                               |
| `original_filename`| TEXT        | User-provided filename                        |
| `content_hash`     | TEXT        | SHA-256 of raw bytes (dedup, integrity check) |
| `mime_type`        | TEXT        | Detected MIME type                            |
| `file_path`        | TEXT        | Relative path within `UPLOAD_DIR`             |
| `byte_size`        | INTEGER     |                                               |
| `llm_tokens_used`  | INTEGER     | Token cost of extraction call                 |
| `llm_provider`     | TEXT        | Which provider handled extraction             |
| `created_at`       | TIMESTAMPTZ |                                               |
| `expires_at`       | TIMESTAMPTZ | `created_at + 7 days` (GDPR TTL)             |

`llm_tokens_used` and `llm_provider` feed into Cloud Edition unit economics (Paddle billing, ADR 003)
and provide cost visibility for self-hosters.

### Rationale
1. **Endpoint separation** keeps `/upload` and `/import` independently evolvable. CV parsing is complex
   enough to own its own router surface without sharing state with structured-data import.
2. **Mistral Vision as default** avoids adding Tesseract (~100MB + system libs) to the Community Docker
   image for a minority use case, while `OCR_BACKEND=tesseract` satisfies offline self-hosters.
3. **Optional JD context** unblocks the new-user flow — forcing JD-first at the upload gate would create
   a dead end for users who want to explore the tool without a specific job in mind.
4. **Dedicated response schema** keeps `MasterProfileResponse` stable and avoids polluting the profile
   model with transient upload state. The `status` field is computed, not persisted — there is nothing
   to migrate.
5. **`StorageProvider` abstraction** follows the established Open Core pattern: Community gets a working
   default, Cloud overrides without touching Community code.

### Consequences
- **Positive:** `/upload` is a clean, focused endpoint with predictable behaviour across all file types.
- **Positive:** No Docker image bloat for the majority of Community users (Mistral Vision default).
- **Positive:** `CVUploadResponse` gives callers immediate actionable feedback (completeness, conflicts,
  GDPR expiry) without requiring a subsequent `GET /api/profile`.
- **Positive:** `llm_tokens_used` in the `uploads` table enables cost analysis from day one.
- **Positive:** The Retention Worker's existing graceful `uploads` table catch is resolved — the table
  now exists, and the 7-day TTL is enforced automatically.
- **Negative:** Two extraction prompts must be maintained in sync (`GENERIC_CV_EXTRACTION_PROMPT` and
  `JD_AWARE_CV_EXTRACTION_PROMPT`). Changes to the output schema must be applied to both.
- **Negative:** `StorageProvider` is a new abstraction in the dependency graph — adds a factory function
  to `apliqa/storage/__init__.py` (same boilerplate pattern as `auth/` and `providers/`).
- **Negative:** `CVImageExtractor` is a third abstraction of the same pattern — worth documenting the
  pattern in `CONTRIBUTING.md` to prevent proliferation.
- **Edition:** Community — `LocalStorageProvider` and `MistralVisionExtractor` are the Community
  defaults. `S3StorageProvider` and any cloud-only OCR backends are `apliqa.cloud.*`.

## #ADR-015: EU AI Act Compliance Boundary

**Date:** 2026-03-17 **Status:** Accepted

### Context

The EU AI Act (Regulation (EU) 2024/1689) classifies AI systems used in recruitment as **high-risk** under Annex III, Category 4. This classification applies to AI systems that:

- Place targeted job advertisements
- Analyse and filter job applications
- Evaluate candidates during interviews or tests
- Rank or score candidates
- Make decisions affecting employment relationships

High-risk classification triggers stringent obligations: conformity assessment, CE marking, EU database registration, bias testing, human oversight mechanisms, and detailed technical documentation. Core requirements become enforceable on **2 August 2026**.

However, **Article 6.3** provides an exemption from high-risk classification if the AI system:

1. Performs a **narrow procedural task** (e.g., classifying documents, parsing CVs, transforming unstructured data to structured data)
2. **Improves the result** of a previously completed human activity (e.g., improving document style)
3. Detects decision-making patterns **without replacing or influencing** human assessment
4. Performs a **preparatory task** to an assessment (e.g., file indexing, document translation)

The exemption applies only if the system **does not materially influence the outcome of decision-making** and **does not profile natural persons**.

Apliqa serves two distinct user categories with different risk profiles:

|User Category|Primary Personas|AI System Role|
|---|---|---|
|**Candidates**|Marcus, Emma, Priya|AI assists the candidate in tailoring their own CV — candidate controls the process, no employer decision is influenced|
|**Recruiters**|Jason (B2B)|AI assists a recruiter in presenting candidates to clients — recruiter is the data controller, output may influence hiring decisions|

The candidate-side use case is clearly **minimal risk** — the candidate is the data subject and the controller of the process. The recruiter-side use case requires careful classification.

### Decision

Apliqa implements a **two-tier feature architecture** for recruiter-facing functionality:

#### Tier 1: Safe Zone (Art. 6.3 Exempt)

These features are classified as **narrow procedural tasks** or **preparatory tasks** that do not materially influence employment decisions and do not profile natural persons:

|Feature|Classification Basis|Art. 6.3 Criterion|
|---|---|---|
|**Kandidatenprofil generation**|Transforms CV structure into branded template; does not evaluate candidate suitability|Narrow procedural task|
|**CV anonymisation**|Removes PII fields; no evaluation or scoring|Narrow procedural task|
|**Agency branding**|Template rendering; not AI|N/A|
|**Batch CV parsing**|Extracts structured data from documents for human review|Preparatory task|
|**Pipeline dashboard**|CRUD operations; displays data; no AI inference|Not AI|
|**Mandate tracking**|Status management; no AI inference|Not AI|

**MVP scope:** Tier 1 features only for Jason persona. All Tier 1 features are available immediately in Cloud Edition.

#### Tier 2: Regulated Zone (High-Risk)

These features involve **profiling natural persons** or **materially influencing employment decisions** — no Art. 6.3 exemption possible:

|Feature|Classification Basis|Trigger|
|---|---|---|
|**Candidate-mandate matching**|Profiles candidates against job requirements; influences which candidates are considered|Profiling (Art. 6.3 exemption excluded)|
|**Candidate ranking/scoring**|Assigns comparative scores to candidates; directly influences selection|Profiling + decision influence|
|**Automated shortlisting**|Filters candidates without human review; gates access to opportunity|Decision influence|
|**Fit percentage calculation**|Quantifies candidate-job compatibility; influences recruiter judgment|Profiling|

**V2 scope:** Tier 2 features require full EU AI Act compliance before deployment. They are **not part of MVP** and will be developed as a separate, clearly scoped module.

### Compliance Documentation

For each Tier 1 feature, Apliqa maintains a documented **Article 6.3 exemption assessment** containing:

1. **Feature description** — what the system does
2. **Classification analysis** — which Art. 6.3 criterion applies
3. **Risk assessment** — why the feature does not materially influence employment decisions
4. **Profiling confirmation** — confirmation that no profiling of natural persons occurs
5. **Human oversight** — how humans remain in control of the output

This documentation is available to competent authorities on request.

### Runtime Gating

A feature flag `AI_ACT_TIER` controls access to Tier 2 features:

|Value|Behaviour|
|---|---|
|`safe_zone` (default)|Only Tier 1 features available; Tier 2 endpoints return HTTP 403 with compliance message|
|`regulated`|Tier 2 features available; requires compliance module to be implemented and registered|

Tier 2 features return a structured error response:

json

FileEditView

```json
{
  "error": "AI_ACT_COMPLIANCE_REQUIRED",
  "message": "This feature requires EU AI Act high-risk compliance. Contact support for enterprise access.",
  "tier": "regulated",
  "compliance_status": "not_implemented"
}
```

### Rationale

1. **MVP scope protection** — Clear boundary prevents accidental scope creep into high-risk territory
2. **Competitive moat** — Most small recruitment tools will not invest in EU AI Act compliance; Apliqa's documented compliance posture becomes a trust signal
3. **Regulatory preparedness** — Documentation is ready before regulators ask; demonstrates good faith compliance
4. **Gradual capability expansion** — Tier 1 delivers immediate value to Jason persona; Tier 2 can be developed with proper compliance framework when market demands it
5. **Candidate-side clarity** — Marcus, Emma, and Priya workflows remain minimal risk regardless of recruiter-side classification

### Consequences

- **Positive:** Clear compliance posture from day one; no ambiguity about which features require what level of compliance
- **Positive:** Jason's MVP workflow (Kandidatenprofil generation, anonymisation, pipeline tracking) is fully deliverable in safe zone
- **Positive:** Competitive differentiation — Apliqa can market "EU AI Act compliant by design" to regulated-industry recruiters
- **Positive:** Candidate-side features (Marcus, Emma, Priya) are unaffected — minimal risk classification stands
- **Negative:** Tier 2 features (matching, ranking) require significant compliance investment before deployment
- **Negative:** Must maintain exemption documentation for each Tier 1 feature; adds documentation overhead
- **Edition:** Cloud only — Jason persona and recruiter features are Cloud Edition; Community Edition is candidate-side only (minimal risk)

### References

- EU AI Act, Article 6(3) — Exemption from high-risk classification
- EU AI Act, Annex III, Category 4 — Employment, workers management, access to self-employment
- EU AI Act, Article 5 — Prohibited AI practices (not applicable to Apliqa's feature set)
- EU AI Act, Articles 9-15 — High-risk AI system obligations (reference for Tier 2 implementation)

---

## #ADR-018: Contributor License Agreement (CLA) for External Contributors
**Date:** 2026-03-27
**Status:** Approved

### Context
Apliqa uses a two-repository Open Core model (ADR 007, ADR 012):

- **`apliqa`** (AGPL-3.0): Community Edition, public on GitHub
- **`apliqa-cloud`** (Proprietary): Cloud Edition, imports `apliqa` as dependency

As sole copyright holder, Tobias Rosenbaum can license the `apliqa` codebase
under both AGPL-3.0 (Community) and proprietary terms (Cloud) simultaneously —
this is standard **dual licensing**.

However, once external contributors submit code to the AGPL-3.0 repository,
their contributions are licensed exclusively under AGPL-3.0. Without a CLA,
Apliqa cannot incorporate contributor code into the proprietary `apliqa-cloud`
edition because the contributor retains copyright and has only granted an
AGPL-3.0 license — not a proprietary one.

This is a well-documented problem in Open Core projects. Plane (makeplane),
GitLab, Grafana, and most other AGPL Open Core companies require CLAs for
exactly this reason.

### Decision
Require a **Contributor License Agreement (CLA)** for all external contributions
to the `apliqa` AGPL-3.0 repository. The CLA grants Apliqa (the legal entity)
a perpetual, worldwide, non-exclusive, royalty-free license to use, reproduce,
modify, and sublicense the contributed code — including under proprietary terms.

**Key terms:**
1. The contributor retains copyright of their contribution.
2. The contributor grants Apliqa a broad license to use the contribution under
   any license, including proprietary.
3. The contributor confirms that the contribution is their original work (or
   they have the right to submit it).
4. The AGPL-3.0 license on the public repository is unaffected — the
   contribution remains available to the community under AGPL-3.0.

**Implementation:**
- Use a lightweight **DCO + CLA hybrid** approach:
  - **Developer Certificate of Origin (DCO)**: `Signed-off-by` trailer on
    every commit (enforced by CI via `dco-check` GitHub Action). This is the
    low-friction gate for casual contributors.
  - **CLA**: Required for contributions that touch core service logic (anything
    in `apliqa/services/`, `apliqa/models/`, `apliqa/routers/`). Signed once
    via CLA Assistant (GitHub App) on first qualifying PR.
- Template: Apache-style Individual CLA (same template used by GitLab, Grafana,
  and other AGPL projects). No copyright assignment — license grant only.
- Store signed CLAs in a private `apliqa-legal` repository for audit purposes.

**Timing:** The CLA must be in place before the first external Pull Request is
merged. Until then, all code is authored by the founder (sole copyright holder)
and no CLA is needed.

### Considered Options

| Option | Verdict |
|--------|---------|
| **No CLA** | Contributor code is AGPL-only. Cannot be used in `apliqa-cloud`. Progressively limits the Cloud Edition to diverge from Community. Not viable for an Open Core business. |
| **Full Copyright Assignment (CLA)** | Contributors transfer all copyright to Apliqa. Maximally flexible but creates contributor resistance — many developers refuse to sign copyright assignment CLAs. Used by few modern projects. |
| **DCO only (no CLA)** | Confirms authorship but grants no additional license rights beyond AGPL-3.0. Insufficient for dual licensing. |
| **DCO + CLA hybrid (chosen)** | Low friction for most contributions (DCO via commit sign-off). CLA only for core logic that is likely to be incorporated into Cloud Edition. Balances contributor experience with business needs. |

### Consequences
- **Positive:** Apliqa retains the ability to dual-license all contributed code,
  preserving the Open Core business model indefinitely.
- **Positive:** Contributors retain their copyright — the CLA is a license
  grant, not a copyright transfer. This is the community-accepted norm.
- **Positive:** The DCO provides a low-friction entry point for documentation
  fixes, typos, and minor contributions without requiring a full CLA.
- **Negative:** Some contributors may decline to sign the CLA. Their
  contributions cannot be merged into core service logic. This is an accepted
  trade-off — the same one GitLab, Grafana, and Plane accept.
- **Negative:** CLA management adds operational overhead (CLA Assistant setup,
  signed CLA storage, PR-level enforcement).
- **Risk:** If a contribution is merged without a signed CLA, that code becomes
  AGPL-only and cannot be used in `apliqa-cloud`. CI enforcement via GitHub
  Actions must be a hard gate (PR cannot merge without CLA check passing).
- **Edition:** Both — the CLA protects the boundary between editions.

### References
- Apache Individual Contributor License Agreement v2.0
- GitLab CLA (DCO + CLA model)
- Grafana Labs CLA
- GitHub CLA Assistant: https://github.com/cla-assistant/cla-assistant
- DCO enforcement: https://github.com/apps/dco

---

**Author:** Carla Coder (Software Architect) **Review Date:** 2 August 2026 (enforcement date for high-risk AI systems)