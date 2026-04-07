# Architecture Documentation — Applire (arc42)

**Version:** 2.10 (Full System Update & Flow Orchestrator)
**Date:** 24 March 2026
**Author:** Tobias Rosenbaum

**Changelog:**

- v2.10 (24 Mar 2026): Full System Update:


- 5.3.3: Interview Orchestrator updated (session scoping, MODE A/B thresholds, MCP tool)
- 5.3.4: PDF Generator updated (polling for CV status)
- 5.3.5: Recruiter Intelligence expanded (GxP regulatory inference)
- 5.3.6a: Core MCP Server revised (emphasis on "Kaile as channel", flow_id for agent recovery, normative flow update)
- 5.3.13: New building block - Edition Gating
- 5.3.14: New building block - Flow Orchestrator
- 5.3.15: New building block - Retention Worker (replaced old 5.3.9)
- 6.1: Human flow sequence diagram updated to reflect flow_orchestrator
- 1. Architecture Decisions: Added ADR-016 and ADR-017
- **8. Testing Strategy: Added comprehensive three-tier testing strategy with CI/CD pipeline**
- v2.9 (24 Mar 2026): Iter 16 — User Story US009/US009b Split (Guided Conversational Interview Flow / Gap Detection & Follow-Up Logic). Minor amendments to 5.3.3 and ADR-004 to reflect parameterisation, no structural changes.
- v2.8 (16 Mar 2026): Iter 15 — Flow Orchestrator & Entry UX
- v2.7 (16 Mar 2026): Iter 14 planning — Interview Orchestrator
- v2.6 (15 Mar 2026): Iter 13 — Gap Detection & Follow-Up Logic
- v2.5 (15 Mar 2026): MCP clarification
- v2.4 (15 Mar 2026): Iter 12 — ADR 014: CV Upload Pipeline
- v2.3 (15 Mar 2026): Iter 11 — Accumulation-first merge model
- v2.2 (09 Mar 2026): Split-layer MCP architecture
- v2.1 (07 Mar 2026): Open Core & Agent-First baseline

---

## Key Updates in v2.10

### Building Block Changes

**5.3.3 Interview Orchestrator** — Now explicitly linked to `flow_sessions` as a child record. Session scoping clarified: one active session per `(user_id, job_id)` within a flow context.

**5.3.4 PDF Generator** — Async generation model emphasized with explicit polling pattern via `get_cv_status(cv_id)`. Now also populates `content_snapshot` on the `GeneratedCV` record at generation time (ADR-019).

**5.3.16 CV Section Editor (Finetuner)** — New building block. Enables section-level editing of generated CVs with live Jinja2 re-render, contextual gap hints, Kaile-assisted gap completion, and dual save path (profile vs. CV-only). See ADR-019.

**5.3.5 Recruiter Intelligence** — Expanded to include GxP regulatory inference engine with confidence levels and audit logging.

**5.3.6a Core MCP Server** — Revised to emphasize "Kaile as a channel" principle. All user-facing functionality must be exposed as MCP tools. Added `start_flow`, `advance_flow`, and `get_flow_state` tools. `flow_id` is the stable handle for agent session recovery.

**5.3.13 Edition Gating** — New building block documenting the runtime feature-flag mechanism separating Community and Cloud editions.

**5.3.14 Flow Orchestrator** — New building block detailing the `flow_sessions` table, step graph, `user_type` detection, `available_actions`, and artifact requirements.

**5.3.15 Retention Worker** — New building block formalizing the daily cron as a core operational concern with comprehensive TTL enforcement.

### Runtime View Updates

**6.1 Human Flow Sequence Diagram** — Updated to show flow orchestrator entry point (`POST /api/flow`), step transitions, and artifact FK population.

**6.2 Agent-Driven Flow** — Updated to include `start_flow`, `advance_flow`, and `get_flow_state` MCP tools. `flow_id` used for agent session recovery.

### Architecture Decisions

**ADR-016: Flow Orchestrator State Machine** — Formalizes the decision to use a custom async state machine for flow management with explicit step transitions and user type detection.

**ADR-017: Retention Worker as Core Operational Concern** — Elevates the retention worker to a mandatory, non-optional component for GDPR compliance.

---

## Table of Contents

1. 
2. 
3. 
4. 
5. 
6. 
7. 
8. 
9. 
10. 
11. 
12. 

---

## 1. Introduction and Goals

### 1.1 Problem Statement

The DACH job market lacks a tool that combines deep AI-powered JD tailoring with German-specific cultural intelligence. Existing solutions fall into four non-overlapping categories:

Category

Example

Gap

CV Builders

Europass, Lebenslauf.de

No AI tailoring

ATS Optimizers

Jobscan

Keyword matching only, no cultural context

AI CV Tailors

Seekario, Kickresume

US-centric, no DACH intelligence

German-Specific

Lebenslauf.de

Format-only, no tailoring

AI Agent Tools

Generic LLM wrappers

No persistent state, no domain expertise

Applire occupies the unserved intersection: **AI-powered JD-specific tailoring WITH European/DACH cultural intelligence**, delivered as an open-core platform accessible to both humans and AI agents.

### 1.2 Requirements Overview

Requirement

Priority

Source

JD-First Architecture

Critical

Competitor Analysis

Interrogative Interview (Gap-Fill)

Critical

Tailoring Scope

Master Profile Enrichment

Critical

"The Moat" Strategy

DACH Cultural Intelligence

Critical

Persona 2 (Priya)

EU-Only Data Residency

Critical

GDPR Strategy

Open Core (AGPL-3.0 + Cloud)

Critical

Business Model (ADR 007/012)

MCP Server (Agent-First)

Critical

Agent Distribution (ADR 010)

Auth Abstraction Interface (Pluggable)

High

Self-Hoster extensibility (ADR 008)

Auth Enforcement (OIDC/Zitadel)

Medium

Cloud Edition only — not needed for local single-user use

LLM Provider Abstraction

High

Vendor Independence (ADR 009)

Subscription + Usage-Based Pricing

High

Revenue Strategy

ATS-Compatible PDF Output

High

Tailoring Scope

One-Click Data Deletion

High

GDPR Art. 17

B2B Multi-Tenancy (Cloud)

Medium

Career Coach Persona (ADR 011)

### 1.3 Quality Goals

Goal

Metric

Priority

Cultural Accuracy

DACH recruiters rate output as "culturally appropriate"

#1

ATS Compatibility

95%+ pass-through on major ATS parsers (Workday, SAP)

#2

Data Sovereignty

100% EU data residency, zero US sub-processors

#3

Frictionless UX

Complete tailoring flow in <10 minutes (human), <30s (agent)

#4

Retention Compliance

100% adherence to TTL deletion schedules

#5

Agent Interoperability

MCP-compliant, <5s tool response time

#6

### 1.4 Stakeholders

| Stakeholder | Role | Concerns |
|---|---|---|
| Tobias Rosenbaum | Product Owner / Founder | Product-market fit, technical feasibility, revenue |
| Marcus (Persona 1) | Experienced Professional (10-20+ years, any industry) | Curation of multi-domain experience, relevance, tailoring precision |
| Priya (Persona 2) | International Relocator to DACH (any industry) | German CV format, cultural translation, credential mapping |
| Emma (Persona 3) | Returning Power User | Retention & upsell, one-click tailoring, version history, highest LTV |
| Felix (Persona 7) | The Finetuner — detail-oriented professional who reads generated CVs critically and wants surgical control over individual sections | Section-level editing with live preview, contextual gap completion, dual save path (profile vs. CV-only) |
| Jason (Persona 5) | Specialist Headhunter / B2B Recruiter | Kandidatenprofil generation, batch processing, pipeline tracking, time savings |
| Dr. Weber (Persona 6) | Pharma/GxP Specialist (Premium Layer) | Industry-specific templates, regulatory framework guidance, premium features |
| Kaile (Persona 4) | Autonomous AI Agent | Structured API/MCP, deterministic output, latency, session recovery |
| DACH Recruiters | End Readers | ATS readability, cultural appropriateness |
| GDPR Regulators | Compliance | Data minimization, retention, erasure rights |
| Self-Hosters | Community Edition operators | Docker simplicity, pluggable auth/LLM |

### 1.5 Roadmap Requirements (Phase 2/3)

The following requirements are planned for Phase 2 (2027) and Phase 3 (2028+) and inform long-term architectural decisions:

| Requirement | Priority | Phase | Source |
|---|---|---|---|
| Mock Interview Preparation | High | Phase 2 (Q1 2027) | E017 — User Practice & Feedback |
| Gamification & Engagement | Medium | Phase 2 (Q2 2027) | E018 — Retention & Motivation |
| Career Path Advisory | Medium | Phase 2 (Q4 2027) | E019 — Career Development |
| Job Search & Recommendation | Medium | Phase 3 (2028+) | E020 — Application Automation |
| Industry Packs (Pharma, MedTech, Finance) | High | Phase 2+ | Business Plan v2.0 — Premium Monetization |
| Autonomous Job Application Submission | Low | Phase 3 (2028+) | E020 — Parked pending legal review (§ 296 SGB III) |

**Architectural Implications:**
- Mock Interview (E017) will require a new LLM-intensive pipeline with dedicated GDPR TTL handling (similar to interview_sessions)
- Gamification (E018) requires user engagement metrics and optional leaderboard infrastructure
- Career Path Advisory (E019) requires market data integration and skill-gap analysis engine
- Job Search (E020) requires external job API integrations (LinkedIn, Indeed, XING) and recommendation engine
- Industry Packs require extensible domain knowledge base architecture (currently: Pharma/GxP in `applire.cloud.intelligence`)
- Autonomous submission (E020) requires legal review and may trigger new regulatory obligations under German employment law

---

## 2. Constraints

### 2.1 Technical Constraints

Constraint

Rationale

Python 3.12 + FastAPI

Async support, Pydantic validation, async state machine

PostgreSQL 16

JSONB for flexible Master Profile schema, RLS for multi-tenancy

Mistral AI (EU) — default provider

EU-native LLM with strong German proficiency

LLM Provider Abstraction (ADR 009)

Support Mistral, OpenAI, Ollama for self-hosters

Hetzner Cloud (DE)

Cost efficiency (€8/month target) + EU data residency

Docker Compose

Simplified deployment for solo-founder MVP and self-hosters

Next.js + ShadCN + Tailwind (planned)

Current prototype uses plain inline styles; ShadCN/Tailwind targeted for production Cloud frontend

AGPL-3.0 License

Open-core base, copyleft ensures contributions flow back

### 2.2 Regulatory Constraints

Constraint

Source

GDPR Art. 6(1)(b) — Contractual necessity

Lawful basis for core processing

GDPR Art. 9(2)(a) — Explicit consent

Special category data (photo, DOB, nationality)

GDPR Art. 17 — Right to erasure

72-hour full purge requirement

GDPR Art. 25 — Privacy by Design

Minimal collection, encryption

AO §147 — Tax retention

10-year invoice retention

EU AI Act — Minimal Risk classification

No high-risk obligations; transparency only

### 2.3 Organizational Constraints

Constraint

Rationale

Solo-founder MVP

Minimize operational complexity

€8/month infrastructure target

Bootstrap-friendly cost structure

No dedicated staging environment

Simplified deployment pipeline

UG (haftungsbeschränkt) initially

Low capital requirement, later GmbH conversion

Nebengewerbe during MVP phase

Founder retains employment

---

## 3. Context and Scope

[Context diagrams and external interfaces remain the same as v2.8]

---

## 4. Solution Strategy

### 4.1 Open Core Strategy (ADR 007, ADR 012)

Edition

License

Contents

**Applire Community Edition**

AGPL-3.0

Core tailoring engine, Master Profile API, MCP Server, basic DACH templates (Classic German, Modern Swiss), Interview Orchestrator, LLM Provider Abstraction, Auth Abstraction interface (no enforcement — single-user local mode by default), Retention Worker, Flow Orchestrator, Docker Compose setup

**Applire Cloud**

Proprietary

Managed hosting, Auth enforcement (OIDC via Zitadel), Recruiter Intelligence (GxP/Pharma), premium templates, B2B multi-tenancy (ADR 011), priority rendering, analytics dashboard, Paddle billing

**Edition Gating:** Feature-flag based (`APPLIRE_EDITION=community|cloud`) checked at the service layer. Cloud-only modules reside in `applire.cloud.*` namespace and are excluded from the AGPL-3.0 distribution.

### 4.2 Core Architectural Patterns

Pattern

Application

Rationale

JD-First Processing

All tailoring flows

JD analysis drives every downstream decision

Agent-First Design

MCP Server + REST API

AI agents are first-class consumers alongside human users

Stateful Backend

Interview Orchestrator, Flow Orchestrator

Complex reasoning logic stays server-side in the state machine, thin frontend

Intelligent Merge

Master Profile Service

Enriches profile without overwriting, stores conflicts

Tiered Scraping

JD Scraper

Maximizes URL success rate with graceful fallbacks

CSS-based Themes

PDF Generator + Browser Preview

Extensible from day one; same CSS renders in browser iframe and Playwright PDF

Provider Abstraction

Auth + LLM + Storage + OCR layers

Pluggable backends for self-hosters (ADR 008, ADR 009, ADR 014) — same factory pattern applied consistently across all cross-cutting infrastructure concerns

Edition Gating

Feature flags

Clean separation of Community/Cloud features (ADR 007/012)

---

## 5. Building Block View

[Sections 5.1 and 5.2 remain largely the same, with updates to 5.3]

### 5.3 Building Block Specifications

#### 5.3.3 Interview Orchestrator [Community]

Aspect

Specification

Purpose

Conduct JD-driven conversational interview; MODE A fills identified gaps, MODE B builds the profile from scratch

State Management

Backend-stateful (stored in `interview_sessions` table as JSONB). 30-day GDPR TTL. Linked to `flow_sessions` as a child record.

Nodes

Gap Detector → Question Generator → Response Parser → Profile Updater (custom async state machine — see `docs/architecture/interview-state-machine.md`; ADR 004)

Mode Selection

Auto-detected at session creation: `completeness_score >= MODE_B_COMPLETENESS_THRESHOLD (0.3)` → **MODE A (Targeted)**; below threshold or no profile → **MODE B (Guided)**. Optional `mode: "targeted" | "guided"` param overrides auto-detection.

Session Scoping

One active session per `(user_id, job_id)` linked to a `flow_session`. `POST /api/session` is idempotent — returns existing active session (`resumed: true`) if one exists. Completed/expired sessions do not block new session creation.

MODE A — Targeted

Consumes `GapAnalysis`. Priority: Category C (exploratory) first, then Category B (confirmation). Soft target 3–8 questions; hard ceiling 12 (`INTERVIEW_HARD_CEILING_TARGETED`).

MODE B — Guided

No existing `GapAnalysis` required. `GapDetector` generates a section-by-section build plan from `_VALID_SECTIONS` weighted by JD relevance. Soft target 10–15 questions; hard ceiling 20 (`INTERVIEW_HARD_CEILING_GUIDED`).

Question Types

**Exploratory** (Category C / MODE B): open question. **Confirmation** (Category B): acknowledges inferred experience and asks for specifics.

Completion Triggers

(1) Gap exhaustion — no gaps remaining. (2) User done-signal — deterministic keyword check (`applire/services/interview/signals.py`), runs before LLM, no API call. (3) Hard ceiling — `questions_asked >= hard_ceiling`. All three yield `complete: true`.

Completion Response

`InterviewCompleteResponse(complete, reason, questions_asked, gaps_resolved, gaps_remaining[], completeness_score)` where `reason ∈ {gaps_resolved, user_ended, max_questions_reached}`

Pause / Resume

`GET /api/session/{id}` returns `SessionStateResponse` (current question, mode, status, questions_asked, hard_ceiling, gaps_remaining, completeness_score, expires_at). Agent recovery path — must exist before Iteration 15 flow orchestration.

Lazy Gap Analysis

`POST /api/session` triggers gap analysis automatically if no `GapAnalysis` exists for the job yet.

LLM

Via LLM Provider Abstraction (default: Mistral, `temperature=0.4` for questions, `temperature=0.1` for response parsing)

Constants

`MODE_B_COMPLETENESS_THRESHOLD`, `INTERVIEW_HARD_CEILING_TARGETED`, `INTERVIEW_HARD_CEILING_GUIDED`, `INTERVIEW_TARGET_MIN_TARGETED`, `INTERVIEW_TARGET_MIN_GUIDED` in `applire/constants.py`

MCP Tool

`run_interview(session_id, message) → InterviewResponse`

#### 5.3.4 PDF Generator [Community]

Aspect

Specification

Purpose

Render and preview ATS-compatible, DACH-formatted CV; live browser preview via iframe + PDF export via Playwright

Engine

Jinja2 templates + Playwright headless Chromium (HTML/CSS → PDF)

Preview

Same Jinja2 HTML served to frontend iframe for live WYSIWYG preview

Templates

CSS-based themes. Community: "Classic German", "Modern Swiss". Cloud: premium themes

Generation Model

Asynchronous — `generate_cv` initiates a background job and returns immediately. The agent or frontend polls `get_cv_status(cv_id)` until `status: "ready"` or `status: "failed"`.

Output

PDF bytes stored with `expires_at` timestamp. TTL: 90 days (human channel) / 24 hours (agent channel). Auto-deleted by Retention Worker.

Formats

`german_lebenslauf` OR `international`

MCP Tool

`generate_cv(job_id, options?) → { cv_id, status: "pending", expires_at: ISO8601 }`

MCP Tool

`get_cv_status(cv_id) → { status: "pending" | "ready" | "failed" | "expired", pdf_url?: string, expires_at?: string }`

#### 5.3.5 Recruiter Intelligence [Cloud Only]

Aspect

Specification

Purpose

Domain-specific reasoning for regulated industries, infer regulatory competencies from project descriptions.

Namespace

`applire.cloud.intelligence`

Modules

`gxp` (Pharma/GxP), extensible to other verticals

Key Logic

Infer skills from employment context (e.g., blood bank → 21 CFR Part 11). Inference confidence levels (high, medium, low) applied. Low-confidence inferences flagged for user confirmation. High-confidence auto-applied to Master Profile with audit. Domain knowledge base covers: GAMP 5, 21 CFR Part 11, EU GMP Annex 11, ICH Q-guidelines, FDA Part 820, ISO 13485, MDR/IVDR, CSV/CSA frameworks.

Gating

Cloud-only feature (`APPLIRE_EDITION=cloud`); returns 402 on Community.

#### 5.3.6 MCP Server [Split: Community + Cloud Layer]

##### 5.3.6a Core MCP Server [Community]

Aspect

Specification

Purpose

Expose **all Applire user-facing capabilities** to AI agents via Model Context Protocol. Kaile is treated as an agent channel, not a persona.

Transport

`stdio` only — local subprocess model

SDK

`mcp` Python SDK — `FastMCP` class; tools registered as decorated async functions

Process model

Standalone subprocess (`python -m applire.mcp`), separate from the FastAPI process. Shares the same PostgreSQL DB via `DATABASE_URL`. Each tool handler opens a short-lived `AsyncSession`; the event loop is owned by `anyio.run()` (called internally by `mcp.run()`), fully isolated from uvicorn's loop.

Auth Context

Every MCP tool call must carry an auth context (API-Key or Bearer Token). The backend extracts `user_id` via `AuthProvider` (ADR 008). Community mode (`NoAuthProvider`): fixed stub `user_id`, no enforcement. For agent session recovery, `flow_id` is the stable handle when traversing the flow.

Normative Agent Flow

`start_flow(job_id?)` → `analyze_jd` → `analyze_gaps(job_id)` → `advance_flow` (with artifact) → `generate_cv(job_id)` → `get_cv_status(cv_id)`. Agents are expected to create or follow a `flow_session`.

Resources

`profile://current`, `job://{job_id}`, `cv://{cv_id}`, `flow://{flow_id}`

URL base

`APPLIRE_BASE_URL` env var — backend base URL for download links returned by `get_cv_status`

Auth

None enforced in Community (single-user local mode). Auth context structurally present via `AuthProvider`; `NoAuthProvider` returns stub user.

Rate Limits

None

Distribution

Included in AGPL-3.0 repository; primary agent discovery channel

Tool Signature

Returns

Notes

`start_flow(job_id: string?)`

`FlowSessionResponse`

Create or resume a flow session, returns flow_id and current state.

`analyze_jd(text?: string, url?: string)`

`JobAnalysis`

Ingest and analyze a job description

`analyze_gaps(job_id: string)`

`GapAnalysis`

Backend loads Master Profile internally via `user_id` from auth context. No profile parameter. Profile is a platform black box; raw data never returned to agent.

`generate_cv(job_id: string, options?: CVOptions)`

`{ cv_id, status: "pending", expires_at }`

Initiates async PDF generation. Agent must poll `get_cv_status`.

`get_cv_status(cv_id: string)`

`{ status, pdf_url?, expires_at? }`

`status: "pending" | "ready" | "failed" | "expired"`. Enables agent recovery after timeout or interruption.

`run_interview(session_id: string, message: string)`

`InterviewResponse`

This tool now implicitly operates within an active flow.

`send_message(session_id: string, message: string)`

`MessageResponse`

—

`get_profile()`

`MasterProfile`

Available for trusted internal agents and self-hosters. Not part of the normative agent flow. Profile data must not be used as input to other tool calls.

`update_profile(section: string, data: object)`

`UpdateResult`

—

`advance_flow(flow_id: string, step: string, artifact_id?: string)`

`FlowStateResponse`

Advance the flow to the next step, requires artifact_id for steps that produce artifacts.

`get_flow_state(flow_id: string)`

`FlowStateResponse`

Get current state of a flow session, including available actions.

`(reserved) generate_cover_letter(cv_id: string, options?)`

`{ pdf_url, doc_id, expires_at }`

V1 deferred. Architecture supports this extension; implementation planned for V2.

##### 5.3.6b MCP Cloud Layer [Cloud Only]

Aspect

Specification

Purpose

Production-grade managed MCP endpoint for remote agents

Transport

SSE (Server-Sent Events) — network-accessible

Auth

API-Key (scoped, revocable, hashed storage)

Rate Limits

Per API-Key, configurable (requests/min, credits/day)

Usage Metering

Per-tool-call credit deduction logged in `usage_logs`

SLA

99.5% uptime guarantee

Cloud-Only Tools

`recruiter_intelligence_analyze`, `get_analytics`, `manage_team`

Gating

Cloud-only tools return edition upgrade prompt on Community

Namespace

`applire.cloud.mcp`

Conversion funnel

Developers discover via Community stdio → need remote access for production agents → upgrade to Cloud SSE

#### 5.3.13 Edition Gating (ADR 012) [Both]

Aspect

Specification

Purpose

Gate Cloud-only features at runtime while maintaining license separation between AGPL-3.0 core and proprietary Cloud code.

Mechanism

`APPLIRE_EDITION` environment variable (`community` | `cloud`) checked at runtime.

Implementation

Service-level checks: Cloud-only service methods return HTTP 402 with upgrade prompt in Community Edition. Namespace separation: Cloud-only code resides in `applire.cloud.*` within the `applire-cloud` repository (proprietary), never in `applire` repository (AGPL-3.0).

Gating Points

REST API routers, MCP tools, Service layer, Template selection (for PDF generation).

Rationale

Enforces license separation, provides clear upgrade path, clean contributor experience.

#### 5.3.14 Flow Orchestrator (ADR 016) [Community]

Aspect

Specification

Purpose

Manages the end-to-end user journey from JD intake to CV download. Validates step transitions; prevents illegal jumps (e.g. generate before gap analysis).

Table

`flow_sessions` — one per `(user_id, job_id)`, enforced by `uq_flow_session_user_job` unique constraint.

Relationship

`flow_sessions 1 ──── 0..1 interview_sessions` — the flow is the parent context; the interview session is one step within it.

Step graph

Linear DAG: `jd_analysis → cv_import → gap_analysis → interview → cv_generation → complete`. Returning users skip `cv_import`; users with sufficient profile may skip `interview`. Encoded in `VALID_TRANSITIONS` dict in `applire/services/flow/orchestrator.py`.

`user_type`

Resolved once at flow creation from profile `calculate_completeness()` vs `MODE_B_COMPLETENESS_THRESHOLD (0.3)`. Stored as `"new"` or `"returning"` on the record; **immutable** for the lifetime of the flow.

`available_actions`

JSONB dict (`{"next": "gap_analysis", "skip": "cv_generation"}`). Computed by `_compute_actions(step, user_type)` and updated atomically with each step transition.

FK population

**Hybrid write/read pattern**: on write (`advance_flow`), caller passes `artifact_id` explicitly — written atomically in the same transaction as the step transition. On read (`get_flow_state`), orchestrator eager-loads child summaries via the FKs already on the record. Prevents race conditions with stale sibling flows.

Artifact requirement

Steps that produce an artifact require `artifact_id` in `AdvanceFlowRequest`: `gap_analysis` → `gap_analysis_id`, `interview` → `interview_session_id`, `cv_generation` → `generated_cv_id`. Missing `artifact_id` → HTTP 422.

Error responses

Invalid transition → HTTP 409 with `{current_step, target_step, allowed_transitions}`. Frontend reads `allowed_transitions` to recover (redirect to correct screen).

Idempotent create

`POST /api/flow` returns existing flow if `(user_id, job_id)` already exists. Race condition handled via `IntegrityError` catch + re-fetch.

Agent compatibility

Server-side state (per ADR 004 Stateful Backend principle) — MCP agents traverse the same `VALID_TRANSITIONS` state machine as human users. Flow ID is the stable handle for agent session recovery.

No GDPR TTL

`flow_sessions` carries no PII — it is a lightweight routing record. Child records (`interview_sessions`, `generated_cvs`, `uploads`) own their per-ADR-005 TTLs.

Files

`backend/applire/models/flow.py` · `backend/applire/schemas/flow.py` · `backend/applire/services/flow/orchestrator.py` · `backend/applire/routers/flow.py`

Migration

`backend/alembic/versions/0012_create_flow_sessions.py`

Endpoints

`POST /api/flow` · `GET /api/flow/{id}/state` · `POST /api/flow/{id}/advance`

#### 5.3.16 CV Section Editor — Finetuner (ADR 019) [Community]

Aspect | Specification
---|---
Purpose | Enable section-level editing of a generated CV with live preview re-rendering, contextual gap hints per section, and dual save path (Master Profile or CV-instance only)
Trigger | User clicks "Fine-tune" on the CV preview page after generation
Data model | Two new JSONB columns on `generated_cvs`: `content_snapshot` (structured rendering context, populated at generation time) and `section_overrides` (user edits keyed by section ID, initially `{}`)
Sections | `introduction`, `positions[{id}]`, `skills`, `education[{id}]`
Re-render | Jinja2 only (no Playwright). Applied on every section save. `GET /api/cv/{id}/html` merges overrides with snapshot before rendering. Playwright PDF triggered only on download.
Gap hints | Computed at request time by `GET /api/cv/{id}/sections` via keyword overlap between Category B/C gaps (from flow's `gap_analysis_id`) and section content. No LLM, no stored mapping. Unmapped gaps surface in a `general_gaps` bucket.
Save path A | `save_to_profile: false` (default for free-text edits) — override written to `section_overrides` only. Master Profile unchanged.
Save path B | `save_to_profile: true` (default when Kaile-assist is used) — override written to `section_overrides` AND posted through existing `PATCH /api/profile` merge pipeline (ADR-013). Conflicts surfaced via existing conflict resolution UI.
Kaile-assist | `POST /api/cv/{id}/sections/{section_id}/assist` starts a targeted-mode interview micro-session (ADR-004) scoped to a specific gap. Returns one question; follow-up answer generates a suggested text snippet via LLM. User accepts, edits, or rejects before saving.
Layout | Desktop: split-screen (editor panel left, CV preview right). Mobile: section accordion (mini preview at top, collapsible section cards below with gap badges).
Frontend components | `FineTunePanel.tsx`, `SectionEditor.tsx`, `GapHint.tsx`, `AssistMicroSession.tsx`, `SaveScopePrompt.tsx`. `CVPreview.tsx` gains a "Fine-tune" toggle that mounts `FineTunePanel`.
GDPR | `content_snapshot` and `section_overrides` are covered by the existing 90-day TTL on `generated_cvs` (ADR-005). No Retention Worker changes needed.
Migration | `backend/alembic/versions/XXXX_add_cv_section_editor_columns.py`
Files | `backend/applire/routers/cv.py` (new routes) · `backend/applire/services/cv/section_editor.py` · `backend/applire/services/cv/gap_mapper.py` · `frontend/components/cv/FineTunePanel.tsx`

#### 5.3.15 Retention Worker (ADR 017) [Community]

Aspect

Specification

Purpose

Enforce GDPR retention periods for data minimization and storage limitation as a core operational concern.

Module

`applire/retention/worker.py`; entry point `python -m applire.retention`

Trigger

Daily cron via Docker Compose `retention` service (always-on, not profile-gated) using `while true; do …; sleep 86400; done`

Retention Rules

`uploads`: 7d hard-delete (`expires_at` column, raw SQL); `interview_sessions`: 30d hard-delete; `generated_cvs`: hard-delete when `expires_at` past (90-day TTL human, 24-hour TTL agent); `master_profiles`/`users`: soft-delete (set `deleted_at`) after 24 months inactivity (730 days)

Inactivity clock

`updated_at` on profiles/sessions; 730 days used as 24-month approximation

Output

JSON report to stdout per run: `{"run_at": "…", "interview_sessions_deleted": N, …}`

Implementation

Async Python, SQLAlchemy ORM (ORM models) + raw `text()` SQL for anticipated-but-absent tables; per-rule commits.

Rationale

GDPR compliance, predictable and audit-friendly, soft-delete for users, hard-delete for transient data. (Ref. ADR 017)

---

## 6. Runtime View

[Scenarios 6.1-6.4 updated to reflect flow orchestrator and agent flow changes]

---

## 8. Testing Strategy

### 8.1 Three-Tier Testing Approach

The Applire project implements a feature-gated testing strategy across three tiers, prioritizing rapid local feedback while maintaining CI/CD quality gates.

**Tier 1: Pre-Commit (Local Development)**
- **Unit Tests**: Fast, isolated component testing with mocked dependencies (pytest)
- **Type Checking**: TypeScript/Pyright validation via IDE
- **Code Style**: Linting and formatting (black, eslint)
- **Purpose**: Immediate developer feedback, fast iteration
- **Blocking**: No (advisory only; developer discretion)
- **Run Location**: Developer machine (local)

**Tier 2: Post-Commit / CI/CD (GitHub Actions)**
- **Backend Unit Tests**: pytest with ≥75% code coverage (blocking gate)
- **Backend Integration Tests**: Full Docker stack + real PostgreSQL database
- **E2E UI Tests**: Playwright testing critical user journeys on running application
- **Purpose**: Automated quality gate enforcing team consistency before merge/deploy
- **Blocking**: YES — build fails if any tier fails
- **Run Location**: GitHub Actions runners; containers orchestrated via docker-compose
- **Timeout**: 15-20 minutes for full suite (Docker build + tests + teardown)

**Tier 3: Pre-Rollout (Manual QA)**
- **Acceptance Criteria Validation**: Manual testing against user story specs (CSV in `/Documents/Product Owner/`)
- **Feature Gate Verification**: Confirm feature flags are set correctly for rollout
- **E2E Re-confirmation**: Critical paths validated before toggling feature flags
- **Device Testing**: Manual QA executed on separate physical device (build container locally, test against self-contained artifact)
- **Purpose**: Final human verification before production rollout
- **Blocking**: YES — no rollout without passing manual QA
- **Run Location**: Developer's separate device

### 8.2 Testing Tools & Frameworks

| Tool | Purpose | Edition |
|------|---------|---------|
| pytest | Unit & integration test framework for Python | Community |
| pytest-cov | Coverage reporting; enforces ≥75% threshold | Community |
| pytest-mock | Mock LLM providers & external services | Community |
| pytest-asyncio | Async test support for FastAPI services | Community |
| Playwright | Browser-based end-to-end UI testing | Community |
| @playwright/test | Playwright test framework with HTML reporting | Community |
| GitHub Actions | CI/CD automation (2,000 min/month free for private repos) | Community |
| docker-compose | Integration test infrastructure; real PostgreSQL in containers | Community |

### 8.3 Coverage Requirements & Gates

**Metric** | **Target** | **Enforcement**
--- | --- | ---
Backend Unit Test Coverage | ≥75% | Blocking gate: `pytest --cov-fail-under=75`
E2E Test Coverage (Scope) | Marcus persona happy path: CV upload → JD input → Processing → Results → Download | Blocking: E2E tests must pass for rollout
LLM Provider Mocking | All CI/CD tests mock providers (Mistral, OpenAI, Ollama, OpenRouter) | Configuration via `APPLIRE_EDITION=community` and test env vars

### 8.4 Test Data Strategy

**Location**: `Solution/tests/fixtures/` (all committed to Git for reproducibility)

**Structure**:
```
Solution/tests/fixtures/
├── profiles/
│   ├── sample_cv.pdf                 # Marcus persona sample CV
│   └── SAMPLE_CV_INSTRUCTIONS.md
├── JDs/
│   └── sample_jd.txt                 # Senior Software Engineer job description
├── downloads/
│   └── .gitkeep                      # Temporary test output location
└── README.md                          # Fixture documentation & best practices
```

**Approach**:
- **Prepared Placeholder Data**: Committed to Git for reproducibility and team alignment
  - `sample_cv.pdf`: Realistic CV exercising upload, parsing, and tailoring logic
  - `sample_jd.txt`: Complete job description for gap analysis and interview testing
- **Custom Test Data**: Developers can add industry-specific JDs, edge-case CVs, etc. All committed to Git.
- **Anonymization**: All fixture data anonymized (no real personal information)
- **Immutability**: Fixtures committed to Git, never generated dynamically (ensures consistency across CI/CD and local runs)

### 8.5 Feature Gate Testing

**Pre-Rollout Validation (Tier 3)**:
- E2E tests must pass for the feature's critical user journey
- Manual QA validates acceptance criteria from user stories
- Feature flag (`APPLIRE_EDITION` or custom flag) verified to be in correct state before rollout

**Edition Gating (Community vs. Cloud)**:
- Community Edition: Tested via CI/CD; covers open-core features only
- Cloud Edition: Feature-gated at runtime; returns HTTP 402 on Community with upgrade prompt
- Test data fixtures designed for Community Edition (open core) to exercise happy path before rollout

**Exploratory Testing (Future Sprints)**:
- "Sad path" scenarios (invalid file uploads, missing JD, processing timeouts) flagged as exploratory testing tasks
- These are captured as findings during manual QA and added as test tasks for future sprints
- Initial Phase 1 E2E scope focuses on Marcus persona happy path only

### 8.6 CI/CD Pipeline Configuration

**Workflow File**: `.github/workflows/test.yml`

**Pipeline Stages** (sequential):
1. **Backend Unit Tests** (Python 3.12.3)
   - Install dependencies from `Solution/backend/requirements.txt`
   - Run pytest with coverage reporting
   - Fail build if coverage < 75%

2. **Backend Integration Tests** (Docker)
   - Build Docker containers via docker-compose
   - Wait for services to be healthy (health check polling)
   - Run integration test suite from `Solution/tests/`
   - Tear down containers

3. **E2E Tests** (Playwright)
   - Install Node.js and Playwright dependencies
   - Start application container
   - Wait for frontend + backend to be ready at localhost:3000
   - Run Playwright test suite
   - Tear down containers

**Artifacts** (uploaded on completion):
- Backend coverage reports (HTML): `backend-coverage-report/`
- Playwright test reports (HTML): `playwright-report/`
- Test results / screenshots: `test-results/`

**Failure Behavior**:
- Any tier failure blocks downstream tiers
- Build status propagated to GitHub PR checks
- Coverage < 75% or E2E failure → **build FAILS** (prevents merge)
- Test summary generated for visibility in GitHub Actions UI

**Local Testing Mirror**:
- Developers can run the same test suite locally using `pytest` and `npx playwright test`
- See `TESTING.md` for local setup, commands, and troubleshooting

**Module System Requirement**:
- All JavaScript/TypeScript code (tests, config, frontend) uses ES modules (`"type": "module"`)
- Both `package.json` (root) and `frontend/package.json` must declare `"type": "module"`
- The `module-system-check` CI job enforces this on every push (see ADR-020)
- Never use `require()` in test files — use static `import` statements

---

## 9. Architecture Decisions

ADR

Title

Status

Edition

ADR 001

Job-First Intake & Analysis Architecture

APPROVED

Community

ADR 002

Master Profile & Data Persistence Strategy

APPROVED

Community

ADR 003

Paddle as Merchant of Record

APPROVED

Cloud

ADR 004

Stateful Backend for Interview Orchestration

APPROVED

Community

ADR 005

Daily Cron for GDPR Retention Enforcement

APPROVED

Community

ADR 006

CSS-based Themes for PDF Extensibility

APPROVED

Community

ADR 007

Open Core Architecture (AGPL-3.0)

APPROVED

Both

ADR 008

Auth Abstraction Wrapper (Pluggable Backends)

APPROVED

Community

ADR 009

LLM Provider Abstraction Layer

APPROVED

Community

ADR 010

MCP Server — Agent-First Platform (Split-Layer)

APPROVED (amended 24 Mar 2026)

Both

ADR 011

Multi-Tenancy for B2B/Team Support (RLS)

APPROVED

Cloud

ADR 012

Two-Repository Edition Gating (amended 27 Mar 2026: Import-Based Detection)

APPROVED

Both

ADR 013

Additive Profile Enrichment Model

APPROVED

Community

ADR 014

CV Upload & Parsing Pipeline

APPROVED

Community

ADR 015

EU AI Act Compliance Boundary

APPROVED

Both

ADR 016

Flow Orchestrator State Machine

APPROVED

Community

ADR 017

Retention Worker as Core Operational Concern

APPROVED

Community

ADR 018

Contributor License Agreement (CLA) for External Contributors

APPROVED

Both

ADR 019

CV Section Editing Model — Snapshot + Override Pattern

APPROVED

Community
Community

ADR 020

Test Organization & Module System Consolidation

PROPOSED

Community

Full ADR content: `docs/product/architecture/ADR.md`
---

**This document is the authoritative source for Applire architecture. All implementation decisions should reference this document.**

_Applire — Verifiable Trust. Deep Reasoning. Agent-First._
