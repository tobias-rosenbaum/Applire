# Development Roadmap — Apliqa Core Features

## Version: 1.0 
## Date: 15 March 2026 
## Status: In Progress

## Philosophy

Ship working vertical slices. Each iteration delivers a testable, end-to-end user value increment. The Master Profile is the central data artifact — every iteration either builds it, enriches it, or consumes it.

All iterations target the Community Edition (AGPL-3.0). Cloud-only features (Recruiter Intelligence, multi-tenancy, billing) are out of scope.
Iteration 11: Master Profile — Data Foundation

**Status:** ✅ Completed

Goal: A fully specified, production-ready Master Profile schema with SQLAlchemy persistence, intelligent merge logic, and enrichment tracking. This is the data backbone all subsequent iterations depend on.
User Story

    As a job seeker, I want my profile to accurately represent my full professional history — even when imported from multiple sources — without losing data or creating duplicates.

Deliverables

Schema & Persistence
Task	Ref
11.1	MasterProfileRecord SQLAlchemy model with JSONB variant (with_variant for PG/SQLite) + 1:1 User relationship	#2910
11.2	Alembic migration for master_profiles table	#2910
11.3	Full Pydantic model hierarchy in apliqa/schemas/master_profile.py: PersonalInfo, ProfessionalSummary (de/en), WorkEntry, EducationEntry, Certification, Skill, LanguageSkill, Publication, VolunteerActivity, ProfileMetadata	#2913
11.4	_VALID_SECTIONS updated to all 9 sections	#2913
11.5	PersonalInfo extended: address, nationality, date_of_birth, photo_url, xing_url, linkedin_url, website_url	#2907
11.6	WorkEntry extended: location, responsibilities[], achievements[], technologies[], industry_context, team_size, budget_managed	#2907
11.7	EducationEntry extended: grade, thesis_title, relevant_coursework[]	#2907
11.8	Skill as structured model: category, proficiency, years_experience, source, last_used	#2907

Merge & Enrichment Logic
Task	Ref
11.9	MergeStrategy class in apliqa/services/profile/merge.py: merge_work_experience(), merge_skills(), detect_contradictions()	#2914
11.10	MergeResult + Conflict dataclasses; conflicts flagged in ProfileMetadata.pending_conflicts, never auto-resolved	#2914
11.11	EnrichmentRecord model: timestamp, source, source_session_id, changes[], confidence	#2907
11.12	FieldChange model: section, field, action, old_value, new_value	#2907
11.13	enrichment_history[] appended on every PATCH	#2914

API & Scoring
Task	Ref
11.14	GET /api/profile — returns MasterProfileResponse including merge_conflicts	#2915
11.15	PATCH /api/profile/{section} — validates section, creates EnrichmentRecord, merges	#2915
11.16	GET /api/profile/enrichment-history — returns full audit trail	#2915
11.17	POST /api/profile/conflicts/{conflict_id}/resolve — user resolves flagged conflict	#2915
11.18	calculate_completeness() — weighted float score (0.0–1.0) with architect-defined weights	#2916
11.19	Unit tests: Pydantic models, SQLite persistence, merge logic, conflict detection, completeness score	#2916
Done When

GET /api/profile returns a fully structured MasterProfileResponse. Uploading two conflicting CVs flags a conflict without data loss. enrichment_history reflects every change. All unit tests pass.

# Iteration 12: CV Upload & Parsing Pipeline

**Status:** ✅ Completed

## Goal:
Users can upload CVs in any common format; the system extracts a structured MasterProfile using JD-context-aware LLM extraction.
## User Story

    As a job seeker, I want to upload my existing CV so the system understands my background without me re-entering everything manually.

## Deliverables
###	Task	Ref
12.1	Format detection layer: PDF (text + OCR), DOCX/DOC, JPG/PNG, plain text	#2904
12.2	PDF text extraction (pymupdf) + OCR fallback for scanned documents	#2904
12.3	DOCX extraction (python-docx)	#2904
12.4	Image OCR extraction (pytesseract or Mistral vision)	#2904
12.5	JD-context-aware LLM extraction prompt: raw text + JobAnalysis context → MasterProfile	#2904
12.6	Confidence scoring per extracted field	#2904
12.7	Multi-CV merge: invoke MergeStrategy from Iteration 6 on each subsequent upload	#2904
12.8	POST /api/profile/upload — multipart/form-data, async, returns { profile_id, status: "DRAFT", completeness_score, conflicts[] }	#2904
12.9	LinkedIn/XING "Save as PDF" parsing: LinkedIn/XING-specific extraction prompt variant	#2908
12.10	Original file stored (S3/local) with cost tracking metadata	#2904
## Done When

Upload a real DACH CV PDF → GET /api/profile returns a structured MasterProfile with all major sections populated and a completeness_score > 0.6. Upload a second CV → conflicts are flagged, no data is lost.
Out of Scope

LinkedIn ZIP import, XING OAuth — deferred to V2.0 Iteration 14.

# Iteration 13: Gap Detection & Follow-Up Logic

**Status:** ✅ Completed

## Goal:
The system compares the analysed JD against the Master Profile and produces a three-category gap report with inference rules for implicit experience.
## User Story

    As a job seeker, I want to know exactly where my profile falls short for this specific role — and where I probably qualify even if I haven't stated it explicitly.

## Deliverables
###	Task	Ref
13.1	GapAnalysis Pydantic schema: match_score (0.0–1.0), critical_gaps[], minor_gaps[], strengths[], keyword_gaps[], category_a[], category_b[], category_c[]	#2911
13.2	Hybrid gap analysis: rule-based pre-pass + LLM refinement	#2911
13.3	Category A — MATCHED: direct skill/experience mapping	#2911
13.4	Category B — LIKELY BUT UNSTATED: inference rules (employer context, seniority, tenure ≥4y, adjacent skills, DACH context)	#2911
13.5	Category C — UNKNOWN: JD requirements with no signal in profile	#2911
13.6	POST /api/session/{id}/analyze-gaps — target response time <10s, returns GapAnalysis	#2911
13.7	Store GapAnalysis in DB alongside JobAnalysis	#2911
13.8	Unit tests: all three category classifications, DACH inference rules, match score range	#2911
## Done When

POST /api/session/{id}/analyze-gaps returns a gap report with a realistic match score, correctly classified A/B/C requirements, and specific actionable gaps. Response time <10s on a standard Hetzner VPS.

# Iteration 14: Guided Conversational Interview

**Status:** ✅ Completed

## Goal:
The system asks targeted, JD-driven questions to fill identified gaps; answers are parsed and merged back into the Master Profile.

## User Story

    As a job seeker, I want the system to ask me smart, targeted questions about my experience so my profile accurately reflects what I've actually done — without wasting my time on irrelevant questions.

## Deliverables
###	Task	Ref
14.1	interview_sessions DB — audit existing schema; add `mode`, `questions_asked`, `hard_ceiling`, `expires_at` if missing; write/update Alembic migration; verify 30-day GDPR TTL	#2905
14.2	Custom async state machine: extend existing 4-node graph (GapDetector → QuestionGenerator → ResponseParser → ProfileUpdater) with MODE A/B routing. GapDetector gains dual-mode entry: MODE A consumes GapAnalysis (C-first, then B); MODE B generates section-by-section build plan from `_VALID_SECTIONS` weighted by JD relevance. **No LangGraph adoption — ADR 004 rationale unchanged.**	#2905
14.3	MODE A — Targeted Gap-Fill: activated when `completeness_score >= 0.3`. Soft target 3–8 questions, hard ceiling 12. Focuses on Category C gaps, then Category B confirmations.	#2905
14.4	MODE B — Guided Build: activated when no Master Profile or `completeness_score < 0.3`. Soft target 10–15 questions, hard ceiling 20. JD-focused full profile construction section by section.	#2905
14.5	Mode auto-detection: `POST /api/session` checks profile completeness (threshold `MODE_B_COMPLETENESS_THRESHOLD = 0.3` in `apliqa/constants.py`). Optional `mode: "targeted" \| "guided"` override param takes precedence. Response includes resolved `mode` and `estimated_questions`.	#2905
14.6	Session scoping: one active session per `(user_id, job_id)`. Partial unique index on `interview_sessions`. Idempotent `POST /api/session` — returns existing active session (with `resumed: true`) instead of creating a duplicate.	#2905
14.7	QuestionGenerator enhancements: undersell detection, achievement extraction, seniority-aware tone, industry-aware probing	#2905
14.8	ResponseParser enhancements: deterministic done-signal detection (keyword check, no LLM) in `apliqa/services/interview/signals.py` before parser runs; richer structured extraction	#2905
14.9	ProfileUpdater: invoke MergeStrategy from Iteration 11 — no overwrites, conflict flagging	#2905
14.10	Cultural sensitivity: DACH-appropriate tone, German/English multilingual input	#2905
14.11	POST /api/session — `CreateSessionRequest(job_id, mode?)`, returns `CreateSessionResponse(session_id, mode, first_question, estimated_questions, resumed)`	#2905
14.12	POST /api/session/{id}/message — on completion returns `InterviewCompleteResponse(complete, reason, questions_asked, gaps_resolved, gaps_remaining, completeness_score)` where `reason ∈ {gaps_resolved, user_ended, max_questions_reached}`	#2905
14.13	GET /api/session/{id} — returns `SessionStateResponse(session_id, job_id, mode, status, questions_asked, hard_ceiling, current_question, gaps_remaining, completeness_score, created_at, updated_at, expires_at)` for agent recovery and pause/resume	#2905
14.14	Add hard ceiling constants to `apliqa/constants.py`: `MODE_B_COMPLETENESS_THRESHOLD`, `INTERVIEW_HARD_CEILING_TARGETED`, `INTERVIEW_HARD_CEILING_GUIDED`, `INTERVIEW_TARGET_MIN_TARGETED`, `INTERVIEW_TARGET_MIN_GUIDED`	#2905
14.15	Create `docs/architecture/interview-state-machine.md` — formal state diagram: 4 nodes, MODE A/B branching, three completion triggers	#2905

## Done When

Start a `targeted` session (MODE A) tied to a job with known Category C gaps → receive a targeted, culturally appropriate question → answer in German or English → `GET /api/profile` reflects the new data → session completes after all critical gaps are addressed (or hard ceiling reached). Start a `guided` session (MODE B) with no prior profile → answer 10+ section-building questions → `GET /api/profile` returns a substantially populated profile (`completeness_score >= 0.5`). `GET /api/session/{id}` returns current state for agent recovery.

# Iteration 15: Flow Orchestrator & Entry UX

**Status:** ✅ Completed

## Goal:
A coherent, end-to-end user journey from JD intake to CV generation, with clear routing for new vs. returning users and session persistence.
## User Story

    As a job seeker, I want a guided, intelligent flow that takes me from a job posting to a tailored CV in under 15 minutes — without having to figure out what to do next.

## Deliverables

### Backend
###	Task	Ref
15.1	Session model: user_id + analyzed_jd_id as composite session key	#2909
15.2	New user flow routing: JD analysis → CV import → gap analysis → interview → CV generation → optional post-generation enrichment	#2909
15.3	Returning user flow routing: JD analysis → gap analysis → CV generation	#2909
15.4	GET /api/session/{id}/state — returns current flow step and available actions	#2909
15.5	Flow state transitions: validated, no illegal jumps (e.g. generate before gap analysis)	#2909

### Frontend (Next.js)
###	Task	Ref
15.6	Screen 1: JD intake (URL/paste) with tiered scraping awareness	#2909
15.7	Screen 2: "Do you have an existing CV?" — Upload / LinkedIn PDF / Start Fresh routing	#2909
15.8	Profile status indicator: completeness gauge, conflict badge	#2909
15.9	Interview screen: real-time question/answer flow, JD context toggle	#2909
15.10	Gap visualizer: A/B/C category cards, match score gauge	#2909
15.11	CV preview + download (reuses Iteration 5 iframe + PDF endpoint)	#2909
## Done When

New user: paste JD → upload CV → complete interview → generate CV — all in under 15 minutes, with no dead ends. Returning user: paste JD → gap analysis → generate CV — in under 5 minutes.
Cross-Cutting Concerns (Ongoing)
Concern	Approach
Structured logging	job_id / session_id correlation on all log lines
Input validation	Pydantic at all API boundaries, section validation in _VALID_SECTIONS
GDPR retention	TTL fields on all new models from the start; interview_sessions 30d, files 7d, CVs 90d
LLM prompt versioning	All prompts as constants in apliqa/prompts/, versioned in git
No auth for dev	Single-user local mode; NoAuthProvider stub from ADR 008
Test coverage	SQLite fallback for all persistence tests; no external services in unit tests
Post-Core-Features (V2.0 Scope)

# Explicitly out of scope for these iterations:

    LinkedIn ZIP / XING OAuth import
    Second CV template ("Modern Swiss")
    LLM Provider Choice (OpenAI / Ollama) — ADR 009 Iteration 6 V2.0
    MCP Server — ADR 010 Iteration 7 V2.0
    Auth enforcement (Zitadel/OIDC)
    Cloud Edition (billing, multi-tenancy, Recruiter Intelligence)
    WebSocket for interview (REST polling acceptable)

Das ist die vollständige Roadmap für alle Core Feature Tasks. Die Iterationsnummern schließen direkt an die MVP-Roadmap (Iter. 0–5) und die V2.0-Roadmap an, sodass alle drei Dokumente eine konsistente Nummerierung bilden. Soll ich die Roadmap noch in Linear oder als Dokument ablegen, sobald der MCP wieder läuft?

# Iteration 16: LLM Provider Abstraction & OpenRouter Integration

**Status:** ✅ Completed

## Goal:
Decouple the backend from a single LLM provider to bypass rate limiting and ensure architectural resilience using a Factory pattern. This unblocks development by allowing us to use OpenRouter, OpenAI, or local instances (Ollama) as fallbacks.

## User Story
    As a developer, I want to swap LLM providers via environment variables so that I can unblock development when one provider is unstable or rate-limited.

## Deliverables
###	Task	Ref
16.1	LLMProvider ABC (Abstract Base Class) defined in `apliqa/services/llm/base.py`	#2898
16.2	MistralProvider implementation (migrating existing logic into the new interface)	#2898
16.3	OpenRouterProvider utilizing the `openai` Python SDK (compatible with OpenRouter/OpenAI/Ollama)	#2898
16.4	LLMService Factory for dynamic provider instantiation based on `LLM_PROVIDER` env var	#2898
16.5	Standardized error handling for provider-specific rate limits (429s) and timeout logic	#2898

## Done When

Changing `LLM_PROVIDER=openrouter` in the `.env` file allows the full "JD Intake → CV Tailoring" flow to function perfectly without any changes to the business logic code.


# Iteration 17: API Hardening & Application Entity

**Status:** ✅ Completed
## Goal:

Harden the backend API based on the 19-endpoint review (2026-03-17). Introduce the Application as a first-class domain entity with its own table, enabling pre-workflow job tracking, user-managed statuses, and a proper pipeline view. Fill missing retrieval endpoints, add GDPR self-service surface, and document the MCP tool registry.
## User Story

    As a job seeker, I want to track multiple jobs I'm interested in — add notes, set deadlines, and see my pipeline at a glance — before I commit to the full CV tailoring workflow for any of them.

## Architectural Decision: Application Entity

The engineers identified a structural tension: FlowSession conflates application tracking and workflow execution. JobAnalysis is globally deduped (keyed by raw_text_hash, no user_id) — there is no "User X is interested in Job Y" record until a FlowSession is created.

Decision: Introduce a dedicated applications table. FlowSession becomes a 1:0..1 child of Application, created only when the user enters the workflow. This enables pre-workflow tracking, user-managed statuses, notes, and deadlines.

Application (1) ──── (0..1) FlowSession
     │
     └──── (1) JobAnalysis (shared/global)

Status model (two layers):

    Workflow-derived (analyzing, interviewing, cv_generating, completed) — synced from FlowSession.current_step automatically.
    User-managed (tracking, applied, rejected, offer) — set via PATCH, representing real-world state outside Apliqa.

## Deliverables
Application Entity & Migration
#	Task	Ref
17.1	applications table: id (UUID PK), user_id (FK → users), job_analysis_id (FK → job_analyses), status (enum), company_name (denormalized), role_title (denormalized), notes (TEXT nullable), applied_at (nullable), deadline (nullable), flow_session_id (FK → flow_sessions, nullable 1:0..1), created_at, updated_at, expires_at (GDPR TTL). UNIQUE constraint on (user_id, job_analysis_id). Alembic migration.	#2970
17.2	Application SQLAlchemy model + ApplicationStatus enum (tracking, analyzing, interviewing, cv_generating, completed, applied, rejected, offer)	#2970
17.3	ApplicationService: create, list (with eager-loaded job + flow state), get detail, update (status/notes/deadline), delete (soft), attach flow session. Workflow-derived status sync on flow advance.	#2970
17.4	ApplicationResponse / ApplicationListResponse Pydantic DTOs with nested job, progress, artifacts projections	#2970
Application API
#	Task	Ref
17.5	GET /api/applications — list all applications for current user, sorted updated_at DESC, filterable by status	#2970
17.6	POST /api/applications — add job to tracking (creates Application record; optionally starts flow if start_workflow: true)	#2970
17.7	GET /api/applications/{id} — detail view including flow state as nested object, HATEOAS next_actions	#2975
17.8	PATCH /api/applications/{id} — update user-managed status, notes, deadline	#2975
17.9	DELETE /api/applications/{id} — remove from pipeline (cascade: soft-delete flow session if attached)	#2975
17.10	POST /api/applications/{id}/start — create FlowSession for this application (bridge from tracking to workflow, delegates to Flow Orchestrator)	NEW
Missing Retrieval Endpoints
#	Task	Ref
17.11	GET /api/job/{job_id} — retrieve stored JobAnalysis without re-triggering LLM. Auth-scoped, 404 if not found.	#2969
17.12	GET /api/cv/{cv_id}/status — CV generation polling (pending, generating, completed, failed). Required by both frontend spinner and MCP agent flow.	#2968
GDPR Self-Service Surface
#	Task	Ref
17.13	DELETE /api/profile — user-initiated full data erasure (Art. 17). Cascades through applications, flow sessions, interviews, CVs, files. Returns 202 Accepted. Audit log before deletion. 72-hour purge commitment.	#2971
17.14	GET /api/profile/export — data portability (Art. 20). Complete user data as JSON download. Excludes internal system state.	#2972
Documentation & ADRs
#	Task	Ref
17.15	MCP Tool Registry companion document: all MCP tools with input/output schemas, cross-referenced to REST endpoints, transport info (stdio/SSE)	#2978
17.16	ADR 015: API Versioning Strategy — evaluate URL prefix (/api/v1/) vs. header-based. Decision only, implementation deferred to pre-Cloud hardening.	#2974
17.17	Update arc42 to v2.7: Application entity, new endpoints (19 → 27), GDPR surface, ADR 015, MCP registry cross-reference	#2976
## Done When

POST /api/applications with a job_analysis_id creates a tracking record. GET /api/applications returns the user's full pipeline with denormalized job info, status badges, and match scores. POST /api/applications/{id}/start creates a FlowSession and the workflow proceeds as before. PATCH /api/applications/{id} allows setting status: "applied" with a note and deadline. GET /api/job/{job_id} returns a stored analysis. GET /api/cv/{cv_id}/status returns generation progress. DELETE /api/profile triggers full cascade erasure. Endpoint count: 19 → 27. All unit tests pass with SQLite fallback.
## Execution Phases

Phase 1 — Foundation (parallel):
  Backend:  17.1–17.4 (Application entity + migration)
            17.11, 17.12 (missing retrieval endpoints — quick wins)

Phase 2 — Application API (sequential):
  Backend:  17.5–17.10 (full CRUD + workflow bridge)

Phase 3 — GDPR + Docs (parallel):
  Backend:  17.13, 17.14 (erasure + export)
  Docs:     17.15, 17.16, 17.17 (MCP registry, ADR 015, arc42 v2.7)

## Out of Scope

    Frontend screens (deferred to Iteration 18 — frontend now depends on the hardened API)
    Auth enforcement (Zitadel/OIDC — V2.0)
    API versioning implementation (ADR 015 is decision-only)
    MCP Server implementation (#2900 — separate iteration)