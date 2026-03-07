# Architecture Documentation — Apliqa (arc42)

**Version:** 2.1 (Open Core & Agent-First)
**Date:** 07 March 2026
**Author:** Tobias Rosenbaum

---

## Table of Contents

1. [Introduction and Goals](#1-introduction-and-goals)
2. [Constraints](#2-constraints)
3. [Context and Scope](#3-context-and-scope)
4. [Solution Strategy](#4-solution-strategy)
5. [Building Block View](#5-building-block-view)
6. [Runtime View](#6-runtime-view)
7. [Deployment View](#7-deployment-view)
8. [Cross-cutting Concepts](#8-cross-cutting-concepts)
9. [Architecture Decisions](#9-architecture-decisions)
10. [Quality Requirements](#10-quality-requirements)
11. [Risks and Technical Debt](#11-risks-and-technical-debt)
12. [Glossary](#12-glossary)

---

## 1. Introduction and Goals

### 1.1 Problem Statement

The DACH job market lacks a tool that combines deep AI-powered JD tailoring with German-specific cultural intelligence. Existing solutions fall into four non-overlapping categories:

| Category          | Example              | Gap                                        |
|-------------------|----------------------|--------------------------------------------|
| CV Builders       | Europass, Lebenslauf.de | No AI tailoring                          |
| ATS Optimizers    | Jobscan              | Keyword matching only, no cultural context |
| AI CV Tailors     | Seekario, Kickresume | US-centric, no DACH intelligence           |
| German-Specific   | Lebenslauf.de        | Format-only, no tailoring                  |
| AI Agent Tools    | Generic LLM wrappers | No persistent state, no domain expertise   |

Apliqa occupies the unserved intersection: **AI-powered JD-specific tailoring WITH European/DACH cultural intelligence**, delivered as an open-core platform accessible to both humans and AI agents.

### 1.2 Requirements Overview

| Requirement                          | Priority | Source                        |
|--------------------------------------|----------|-------------------------------|
| JD-First Architecture                | Critical | Competitor Analysis           |
| Interrogative Interview (Gap-Fill)   | Critical | Tailoring Scope               |
| Master Profile Enrichment            | Critical | "The Moat" Strategy           |
| DACH Cultural Intelligence           | Critical | Persona 2 (Priya)            |
| EU-Only Data Residency               | Critical | GDPR Strategy                 |
| Open Core (AGPL-3.0 + Cloud)        | Critical | Business Model (ADR 007/012)  |
| MCP Server (Agent-First)            | Critical | Agent Distribution (ADR 010)  |
| Auth Abstraction Interface (Pluggable) | High  | Self-Hoster extensibility (ADR 008) |
| Auth Enforcement (OIDC/Zitadel)     | Medium   | Cloud Edition only — not needed for local single-user use |
| LLM Provider Abstraction            | High     | Vendor Independence (ADR 009) |
| Subscription + Usage-Based Pricing   | High     | Revenue Strategy              |
| ATS-Compatible PDF Output            | High     | Tailoring Scope               |
| One-Click Data Deletion              | High     | GDPR Art. 17                  |
| B2B Multi-Tenancy (Cloud)           | Medium   | Career Coach Persona (ADR 011)|

### 1.3 Quality Goals

| Goal                  | Metric                                                        | Priority |
|-----------------------|---------------------------------------------------------------|----------|
| Cultural Accuracy     | DACH recruiters rate output as "culturally appropriate"       | #1       |
| ATS Compatibility     | 95%+ pass-through on major ATS parsers (Workday, SAP)        | #2       |
| Data Sovereignty      | 100% EU data residency, zero US sub-processors               | #3       |
| Frictionless UX       | Complete tailoring flow in <10 minutes (human), <30s (agent)  | #4       |
| Retention Compliance  | 100% adherence to TTL deletion schedules                      | #5       |
| Agent Interoperability| MCP-compliant, <5s tool response time                         | #6       |

### 1.4 Stakeholders

| Stakeholder          | Role                                  | Concerns                                          |
|----------------------|---------------------------------------|---------------------------------------------------|
| Tobias Rosenbaum     | Product Owner / Founder               | Product-market fit, technical feasibility, revenue |
| Marcus (Persona 1)   | Seasoned Multi-Domain Professional   | Curation of 20+ years experience, relevance       |
| Priya (Persona 2)    | International Relocator              | German CV format, cultural translation            |
| Wei (Persona 3)      | International Graduate               | Modern aesthetics, credential translation (V2)    |
| AI Agent (Persona 4) | Autonomous agent (e.g., OpenClaw)    | Structured API/MCP, deterministic output, latency |
| DACH Recruiters       | End Readers                          | ATS readability, cultural appropriateness         |
| GDPR Regulators       | Compliance                           | Data minimization, retention, erasure rights      |
| Self-Hosters          | Community Edition operators          | Docker simplicity, pluggable auth/LLM             |
| Career Coaches (B2B)  | Team/multi-tenant users              | Shared templates, client management               |

---

## 2. Constraints

### 2.1 Technical Constraints

| Constraint                        | Rationale                                                    |
|-----------------------------------|--------------------------------------------------------------|
| Python 3.12 + FastAPI             | Async support, Pydantic validation, LangGraph integration    |
| PostgreSQL 16                     | JSONB for flexible Master Profile schema, RLS for multi-tenancy |
| Mistral AI (EU) — default provider| EU-native LLM with strong German proficiency                 |
| LLM Provider Abstraction (ADR 009)| Support Mistral, OpenAI, Ollama for self-hosters             |
| Hetzner Cloud (DE)                | Cost efficiency (€8/month target) + EU data residency        |
| Docker Compose                    | Simplified deployment for solo-founder MVP and self-hosters  |
| Next.js 16 + ShadCN              | Modern, accessible component library                         |
| AGPL-3.0 License                  | Open-core base, copyleft ensures contributions flow back     |

### 2.2 Regulatory Constraints

| Constraint                                  | Source                                      |
|---------------------------------------------|---------------------------------------------|
| GDPR Art. 6(1)(b) — Contractual necessity   | Lawful basis for core processing            |
| GDPR Art. 9(2)(a) — Explicit consent        | Special category data (photo, DOB, nationality) |
| GDPR Art. 17 — Right to erasure             | 72-hour full purge requirement              |
| GDPR Art. 25 — Privacy by Design            | Minimal collection, encryption              |
| AO §147 — Tax retention                     | 10-year invoice retention                   |
| EU AI Act — Minimal Risk classification     | No high-risk obligations; transparency only |

### 2.3 Organizational Constraints

| Constraint                        | Rationale                                    |
|-----------------------------------|----------------------------------------------|
| Solo-founder MVP                  | Minimize operational complexity              |
| €8/month infrastructure target    | Bootstrap-friendly cost structure             |
| No dedicated staging environment  | Simplified deployment pipeline               |
| UG (haftungsbeschränkt) initially | Low capital requirement, later GmbH conversion|
| Nebengewerbe during MVP phase     | Founder retains employment                   |

---

## 3. Context and Scope

### 3.1 Business Context Diagram

┌──────────────────────────────────────────────────────────────────────────────┐ │ │ │ ┌──────────┐ ┌──────────────────────────┐ ┌──────────┐ │ │ │ │ HTTPS │ │ │ │ │ │ │ Human │────────▶│ APLIQA │◀───────│ Paddle │ │ │ │ Users │ │ │ │ (MoR) │ │ │ │ (Marcus/ │◀────────│ - JD Analysis │───────▶│ Payments │ │ │ │ Priya/ │ PDF │ - CV Tailoring │ Credits│ │ │ │ │ Wei) │ │ - Master Profile │ └──────────┘ │ │ └──────────┘ │ - Recruiter Intelligence│ │ │ │ │ │ │ ┌──────────┐ MCP/ │ │ ┌──────────┐ │ │ │ │ REST │ │ Auth │ │ │ │ │ AI Agents│────────▶│ │◀───────▶│ Auth │ │ │ │(OpenClaw,│ │ │ OIDC/ │ Provider │ │ │ │ Cursor, │◀────────│ │ API-Key│(Zitadel/ │ │ │ │ Claude) │ JSON │ │ │ Generic) │ │ │ └──────────┘ └──────────────────────────┘ └──────────┘ │ │ │ │ │ ┌──────────┐ │ LLM API │ │ │ JD │ HTTP(S) ▼ │ │ │ Sources │───────▶ ┌──────────────────┐ │ │ │(StepStone│ │ LLM Provider │ │ │ │ Indeed, │◀────────│ (Mistral/OpenAI/│ │ │ │ Careers) │ Scraped │ Ollama) │ │ │ └──────────┘ └──────────────────┘ │ │ │ └──────────────────────────────────────────────────────────────────────────────┘


### 3.2 Technical Context Diagram

┌──────────────────────────────────────────────────────────────────────────────┐ │ APLIQA SYSTEM │ │ │ │ ┌────────────────────────────────────────────────────────────────────────┐ │ │ │ FRONTEND (Next.js) — Cloud Only │ │ │ │ - Chat Interface (Interview) │ │ │ │ - JD Input (Text/URL) │ │ │ │ - CV Upload │ │ │ │ - PDF Preview & Download │ │ │ └──────────────────────────┬─────────────────────────────────────────────┘ │ │ │ REST API (JSON) │ │ ▼ │ │ ┌────────────────────────────────────────────────────────────────────────┐ │ │ │ BACKEND (FastAPI) │ │ │ │ │ │ │ │ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ │ │ │ │ │ MCP Server │ │ REST API │ │ Edition Gate │ │ │ │ │ │ (Agent Interface)│ │ (Human + Agent) │ │ (Feature Flags) │ │ │ │ │ └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘ │ │ │ │ │ │ │ │ │ │ │ └─────────────────────┼──────────────────────┘ │ │ │ │ ▼ │ │ │ │ ┌──────────────────────────────────────────────────────────────────┐ │ │ │ │ │ SERVICE LAYER │ │ │ │ │ │ │ │ │ │ │ │ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │ │ │ │ │ │ │ Job Intake & │ │ Master Profile │ │ Interview │ │ │ │ │ │ │ │ Analysis Engine │ │ Service │ │ Orchestrator │ │ │ │ │ │ │ │ [Community] │ │ [Community] │ │ (LangGraph) │ │ │ │ │ │ │ └─────────────────┘ └─────────────────┘ │ [Community] │ │ │ │ │ │ │ └─────────────────┘ │ │ │ │ │ │ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │ │ │ │ │ │ │ CV Tailoring │ │ PDF Generator │ │ Recruiter │ │ │ │ │ │ │ │ Engine │ │ [Community] │ │ Intelligence │ │ │ │ │ │ │ │ [Community] │ │ │ │ [Cloud Only] │ │ │ │ │ │ │ └─────────────────┘ └─────────────────┘ └─────────────────┘ │ │ │ │ │ │ │ │ │ │ │ │ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │ │ │ │ │ │ │ Retention │ │ Auth Abstraction│ │ LLM Provider │ │ │ │ │ │ │ │ Worker │ │ (ADR 008) │ │ Abstraction │ │ │ │ │ │ │ │ [Community] │ │ [Community] │ │ (ADR 009) │ │ │ │ │ │ │ └─────────────────┘ └─────────────────┘ │ [Community] │ │ │ │ │ │ │ └─────────────────┘ │ │ │ │ │ └──────────────────────────────────────────────────────────────────┘ │ │ │ │ │ │ │ │ │ ▼ │ │ │ │ ┌──────────────────────────────────────────────────────────────────┐ │ │ │ │ │ DATA LAYER (Models) │ │ │ │ │ │ │ │ │ │ │ │ User │ MasterProfile │ JobAnalysis │ GeneratedCV │ Session │ │ │ │ │ │ Tenant [Cloud] │ ApiKey │ UsageLog │ │ │ │ │ └──────────────────────────────────────────────────────────────────┘ │ │ │ │ │ │ │ │ └─────────────────────────────────┼──────────────────────────────────────┘ │ │ │ SQLAlchemy + asyncpg │ │ ▼ │ │ ┌────────────────────────────────────────────────────────────────────────┐ │ │ │ DATABASE (PostgreSQL 16) │ │ │ │ - users (id, email, credits, tenant_id [Cloud], created_at) │ │ │ │ - master_profiles (user_id, profile_json JSONB, metadata) │ │ │ │ - job_analyses (job_id, raw_text_hash, analysis_json JSONB) │ │ │ │ - generated_cvs (cv_id, user_id, pdf_bytes, expires_at) │ │ │ │ - interview_sessions (session_id, state, messages) │ │ │ │ - api_keys (key_hash, user_id, rate_limit, created_at) [Cloud] │ │ │ │ - usage_logs (id, user_id, action, credits_used, timestamp) [Cloud] │ │ │ └────────────────────────────────────────────────────────────────────────┘ │ │ │ └──────────────────────────────────────────────────────────────────────────────┘ │ │ │ LLM API │ Auth (OIDC / API-Key) ▼ ▼ ┌─────────────────────┐ ┌─────────────────────┐ │ LLM Provider │ │ Auth Provider │ │ (Mistral AI / │ │ (Zitadel Cloud / │ │ OpenAI / Ollama) │ │ Generic OIDC / │ │ │ │ API-Key) │ └─────────────────────┘ └─────────────────────┘


### 3.3 External Interfaces

| Interface        | Type                  | Direction     | Data                              | Edition     |
|------------------|-----------------------|---------------|-----------------------------------|-------------|
| Auth Provider    | OIDC/OAuth2           | Inbound       | User identity, tokens             | Cloud       |
| No Auth (Local)  | —                     | —             | Single-user local mode, no enforcement | Community |
| Paddle           | REST API + Webhooks   | Bidirectional | Payments, subscriptions, VAT      | Cloud       |
| LLM Provider     | REST API              | Outbound      | Prompts, LLM responses            | Both        |
| JD Sources       | HTTP(S)               | Outbound      | Scraped job descriptions          | Both        |
| User Browser     | HTTPS                 | Bidirectional | CV uploads, PDF downloads         | Cloud       |
| MCP Protocol     | MCP (JSON-RPC/stdio)  | Bidirectional | Tool calls, structured responses  | Both        |
| REST API         | HTTPS + API-Key       | Bidirectional | Programmatic access for agents    | Both        |

---

## 4. Solution Strategy

### 4.1 Open Core Strategy (ADR 007, ADR 012)

| Edition                        | License       | Contents                                                                 |
|--------------------------------|---------------|--------------------------------------------------------------------------|
| **Apliqa Community Edition**   | AGPL-3.0      | Core tailoring engine, Master Profile API, MCP Server, basic DACH templates (Classic German, Modern Swiss), Interview Orchestrator, LLM Provider Abstraction, Auth Abstraction interface (no enforcement — single-user local mode by default), Retention Worker, Docker Compose setup |
| **Apliqa Cloud**               | Proprietary   | Managed hosting, Auth enforcement (OIDC via Zitadel), Recruiter Intelligence (GxP/Pharma), premium templates, B2B multi-tenancy (ADR 011), priority rendering, analytics dashboard, Paddle billing |

**Edition Gating:** Feature-flag based (`APLIQA_EDITION=community|cloud`) checked at the service layer. Cloud-only modules reside in `apliqa.cloud.*` namespace and are excluded from the AGPL-3.0 distribution.

### 4.2 Core Architectural Patterns

| Pattern                  | Application                | Rationale                                                    |
|--------------------------|----------------------------|--------------------------------------------------------------|
| JD-First Processing      | All tailoring flows        | JD analysis drives every downstream decision                 |
| Agent-First Design       | MCP Server + REST API      | AI agents are first-class consumers alongside human users    |
| Stateful Backend         | Interview Orchestrator     | Complex reasoning logic stays in LangGraph, thin frontend    |
| Intelligent Merge        | Master Profile Service     | Enriches profile without overwriting, stores conflicts       |
| Tiered Scraping          | JD Scraper                 | Maximizes URL success rate with graceful fallbacks           |
| CSS-based Themes         | PDF Generator + Browser Preview | Extensible from day one; same CSS renders in browser iframe and Playwright PDF |
| Provider Abstraction     | Auth + LLM layers          | Pluggable backends for self-hosters (ADR 008, ADR 009)      |
| Edition Gating           | Feature flags              | Clean separation of Community/Cloud features (ADR 007/012)  |

### 4.3 Technology Decisions

| Layer              | Technology                          | Rationale                                                    |
|--------------------|-------------------------------------|--------------------------------------------------------------|
| Frontend           | Next.js 16 + ShadCN + Tailwind     | Rapid UI development, accessibility built-in                 |
| Backend            | FastAPI + Pydantic + SQLAlchemy     | Async-native, strong typing, LangGraph compatibility         |
| AI Orchestration   | LangGraph + langchain-mistralai     | Structured agent workflows, native Mistral integration       |
| LLM (Default)      | Mistral AI (EU-hosted)             | EU-native, strong German proficiency, GDPR-compliant         |
| LLM (Abstraction)  | Provider interface (ADR 009)       | Supports Mistral, OpenAI, Ollama for self-hosters            |
| Database           | PostgreSQL 16 + JSONB              | Flexible schema evolution, RLS for multi-tenancy             |
| PDF Generation     | Jinja2 + Playwright (Chromium)     | HTML/CSS templates rendered in headless Chromium; same engine as browser preview |
| Auth (Community)   | No enforcement — single-user local mode | Self-hosters run locally; no identity provider required  |
| Auth (Cloud)       | Zitadel Cloud SaaS (ADR 008)       | EU-hosted, OIDC-compliant; enforced in Cloud Edition only    |
| Auth (Abstraction) | `AuthProvider` base class (ADR 008) | Interface lives in Community; Cloud ships Zitadel + OIDC backends; self-hosters can plug in their own |
| Payments           | Paddle (Merchant of Record)        | VAT compliance handled, EU-focused                           |
| Agent Protocol     | Model Context Protocol (MCP)       | Agentic interoperability standard (ADR 010)                  |
| Infrastructure     | Hetzner Cloud (DE)                 | €8/month target, EU data residency                           |

### 4.4 Key Design Principles

1. **Spec-First Development:** Every feature defined in ADRs before implementation.
2. **Privacy by Design:** Minimal collection, encryption everywhere, no tracking.
3. **Graceful Degradation:** Scraping fallbacks, manual copy-paste alternatives.
4. **Audit-Ready:** Structured logging, retention enforcement, DPIA documentation.
5. **Agent-First:** Every human-facing feature must also be accessible via MCP/API.
6. **Open by Default:** Core functionality is open-source; monetize convenience and intelligence.

---

## 5. Building Block View

### 5.1 Level 1: System Overview (Whitebox)

┌──────────────────────────────────────────────────────────────────────────────┐ │ APLIQA SYSTEM │ │ │ │ ┌─────────────────┐ ┌──────────────────┐ ┌─────────────────┐ │ │ │ │ │ │ │ │ │ │ │ FRONTEND │ │ BACKEND │ │ DATABASE │ │ │ │ (Next.js) │◀──▶│ (FastAPI) │◀──▶│ (PostgreSQL) │ │ │ │ [Cloud] │ │ [Community] │ │ [Community] │ │ │ │ │ │ │ │ │ │ │ │ - Chat UI │ │ - REST API │ │ - Users │ │ │ │ - JD Input │ │ - MCP Server │ │ - Profiles │ │ │ │ - CV Upload │ │ - LangGraph │ │ - Jobs │ │ │ │ - PDF View │ │ - Services │ │ - Sessions │ │ │ │ │ │ - Edition Gate │ │ - API Keys │ │ │ └─────────────────┘ └──────────────────┘ │ - Usage Logs │ │ │ │ └─────────────────┘ │ │ │ │ │ ┌──────┴──────┐ │ │ │ │ │ │ ┌────▼────┐ ┌────▼────┐ │ │ │ MCP │ │ REST │ │ │ │ Server │ │ API │ │ │ │(stdio/ │ │(HTTPS) │ │ │ │ SSE) │ │ │ │ │ └────┬────┘ └────┬────┘ │ │ │ │ │ │ ┌────▼─────────────▼────┐ │ │ │ AI AGENTS │ │ │ │ (OpenClaw, Cursor, │ │ │ │ Claude, Custom) │ │ │ └──────────────────────┘ │ │ │ └──────────────────────────────────────────────────────────────────────────────┘


### 5.2 Level 2: Backend Decomposition

┌──────────────────────────────────────────────────────────────────────────────┐ │ BACKEND (FastAPI) │ │ │ │ ┌────────────────────────────────────────────────────────────────────────┐ │ │ │ INTERFACE LAYER │ │ │ │ │ │ │ │ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ │ │ │ │ │ REST API Routers │ │ MCP Server │ │ Webhook Handlers │ │ │ │ │ │ /api/job/* │ │ (ADR 010) │ │ (Paddle) │ │ │ │ │ │ /api/profile/* │ │ │ │ [Cloud] │ │ │ │ │ │ /api/interview/* │ │ Tools: │ │ │ │ │ │ │ │ /api/cv/* │ │ - analyze_jd │ └──────────────────┘ │ │ │ │ │ /api/session/* │ │ - get_profile │ │ │ │ │ │ /api/auth/* │ │ - run_interview │ │ │ │ │ │ /api/credits/* │ │ - generate_cv │ │ │ │ │ │ │ │ - get_gaps │ │ │ │ │ └──────────────────┘ └──────────────────┘ │ │ │ └────────────────────────────────┬───────────────────────────────────────┘ │ │ │ │ │ ┌────────────────────────────────▼───────────────────────────────────────┐ │ │ │ EDITION GATE (Feature Flags) │ │ │ │ │ │ │ │ APLIQA_EDITION=community|cloud │ │ │ │ Checks at service entry points; Cloud features return 402/upgrade │ │ │ └────────────────────────────────┬───────────────────────────────────────┘ │ │ │ │ │ ┌────────────────────────────────▼───────────────────────────────────────┐ │ │ │ SERVICE LAYER │ │ │ │ │ │ │ │ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │ │ │ │ │ Job Intake & │ │ Master Profile │ │ Interview │ │ │ │ │ │ Analysis Engine │ │ Service │ │ Orchestrator │ │ │ │ │ │ [Community] │ │ [Community] │ │ (LangGraph) │ │ │ │ │ │ │ │ │ │ [Community] │ │ │ │ │ │ - URL Scraping │ │ - CRUD │ │ │ │ │ │ │ │ - JD Analysis │ │ - Merge Logic │ │ - Gap Detection │ │ │ │ │ │ - Deduplication │ │ - Conflicts │ │ - Question Gen │ │ │ │ │ └─────────────────┘ └─────────────────┘ └─────────────────┘ │ │ │ │ │ │ │ │ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │ │ │ │ │ CV Tailoring │ │ PDF Generator │ │ Recruiter │ │ │ │ │ │ Engine │ │ [Community] │ │ Intelligence │ │ │ │ │ │ [Community] │ │ │ │ [Cloud Only] │ │ │ │ │ │ │ │ - Jinja2 │ │ │ │ │ │ │ │ - Section Order │ │ - WeasyPrint │ │ - GxP/Pharma │ │ │ │ │ │ - Bullet Rewrite│ │ - CSS Themes │ │ - Industry Maps │ │ │ │ │ │ - Keyword Align │ │ │ │ │ │ │ │ │ └─────────────────┘ └─────────────────┘ └─────────────────┘ │ │ │ │ │ │ │ │ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │ │ │ │ │ Retention │ │ Auth Abstraction│ │ LLM Provider │ │ │ │ │ │ Worker │ │ (ADR 008) │ │ Abstraction │ │ │ │ │ │ [Community] │ │ [Community] │ │ (ADR 009) │ │ │ │ │ │ │ │ │ │ [Community] │ │ │ │ │ │ - Daily Cron │ │ - Zitadel │ │ │ │ │ │ │ │ - TTL Enforce │ │ - Generic OIDC │ │ - Mistral │ │ │ │ │ │ │ │ - API-Key │ │ - OpenAI │ │ │ │ │ └─────────────────┘ └─────────────────┘ │ - Ollama │ │ │ │ │ └─────────────────┘ │ │ │ │ ┌─────────────────┐ │ │ │ │ │ Multi-Tenancy │ │ │ │ │ │ (ADR 011) │ │ │ │ │ │ [Cloud Only] │ │ │ │ │ │ │ │ │ │ │ │ - RLS │ │ │ │ │ │ - tenant_id │ │ │ │ │ │ - Coach Portal │ │ │ │ │ └─────────────────┘ │ │ │ └────────────────────────────────────────────────────────────────────────┘ │ │ │ │ │ ┌────────────────────────────────▼───────────────────────────────────────┐ │ │ │ DATA LAYER (Models) │ │ │ │ │ │ │ │ User │ MasterProfile │ JobAnalysis │ GeneratedCV │ Session │ │ │ │ Tenant [Cloud] │ ApiKey [Cloud] │ UsageLog [Cloud] │ │ │ └────────────────────────────────────────────────────────────────────────┘ │ │ │ └──────────────────────────────────────────────────────────────────────────────┘


### 5.3 Building Block Specifications

#### 5.3.1 Job Intake & Analysis Engine [Community]

| Aspect        | Specification                                                    |
|---------------|------------------------------------------------------------------|
| Purpose       | Ingest JD (text/URL) and produce structured JobAnalysis          |
| Input         | Raw text OR URL (scraped via Tier 1/2)                           |
| Output        | JobAnalysis JSON (6-category schema)                             |
| Dependencies  | LLM Provider (default: Mistral AI), JD Scraper, PostgreSQL      |
| Key Features  | Deduplication via `raw_text_hash`, confidence scoring            |
| MCP Tool      | `analyze_jd(text?: string, url?: string) → JobAnalysis`         |

#### 5.3.2 Master Profile Service [Community]

| Aspect        | Specification                                                    |
|---------------|------------------------------------------------------------------|
| Purpose       | Store and evolve user's comprehensive career autobiography       |
| Storage       | PostgreSQL JSONB (`profile_json` column)                         |
| Key Logic     | Intelligent Merge (company/role identity), Conflict Resolution   |
| API Endpoints | `GET /api/profile`, `PATCH /api/profile/{section}`, `POST /api/profile/conflicts/{id}/resolve` |
| MCP Tool      | `get_profile() → MasterProfile`, `update_profile(section, data)` |
| Completeness  | `calculate_completeness()` method standardized across layers     |

#### 5.3.3 Interview Orchestrator (LangGraph) [Community]

| Aspect           | Specification                                                 |
|------------------|---------------------------------------------------------------|
| Purpose          | Conduct JD-driven conversational gap-fill interview           |
| State Management | Backend-stateful (stored in `interview_sessions` table)       |
| Nodes            | Gap Detector → Question Generator → Response Parser → Profile Updater |
| LLM              | Via LLM Provider Abstraction (default: Mistral, `temperature=0.2`) |
| Output           | Enriched Master Profile section data                          |
| MCP Tool         | `run_interview(session_id, message) → InterviewResponse`      |

#### 5.3.4 PDF Generator [Community]

| Aspect    | Specification                                                      |
|-----------|--------------------------------------------------------------------|
| Purpose   | Render and preview ATS-compatible, DACH-formatted CV; live browser preview via iframe + PDF export via Playwright |
| Engine    | Jinja2 templates + Playwright headless Chromium (HTML/CSS → PDF)   |
| Preview   | Same Jinja2 HTML served to frontend iframe for live WYSIWYG preview |
| Templates | CSS-based themes. Community: "Classic German", "Modern Swiss". Cloud: premium themes |
| Output    | PDF bytes (stored 90 days, then auto-deleted)                      |
| Formats   | `german_lebenslauf` OR `international`                             |
| MCP Tool  | `generate_cv(job_id, options?) → { pdf_url, cv_id }`              |

#### 5.3.5 Recruiter Intelligence [Cloud Only]

| Aspect    | Specification                                                      |
|-----------|--------------------------------------------------------------------|
| Purpose   | Domain-specific reasoning for regulated industries                 |
| Namespace | `apliqa.cloud.intelligence`                                        |
| Modules   | `gxp` (Pharma/GxP), extensible to other verticals                 |
| Key Logic | Infer skills from employment context (e.g., blood bank → 21 CFR Part 11) |
| Gating    | Feature flag `APLIQA_EDITION=cloud`; returns 402 on Community      |

#### 5.3.6 MCP Server (ADR 010) [Community]

| Aspect       | Specification                                                   |
|--------------|-----------------------------------------------------------------|
| Purpose      | Expose Apliqa capabilities to AI agents via Model Context Protocol |
| Transport    | stdio (local), SSE (remote/Cloud)                               |
| Tools        | `analyze_jd`, `get_profile`, `update_profile`, `run_interview`, `analyze_gaps`, `generate_cv` |
| Resources    | `profile://current`, `job://{job_id}`, `cv://{cv_id}`          |
| Auth         | API-Key (Cloud), local session (Community)                      |
| Rate Limits  | Per API-Key, configurable (Cloud)                               |

#### 5.3.7 Auth Abstraction (ADR 008) [Community]

| Aspect              | Specification                                                            |
|---------------------|--------------------------------------------------------------------------|
| Purpose             | Pluggable authentication for diverse deployment scenarios                 |
| Interface           | `AuthProvider` base class — lives in Community codebase                  |
| Default (Community) | `NoAuthProvider` — no enforcement; single-user local mode assumed         |
| Backends (Cloud)    | Zitadel Cloud (OIDC), Generic OIDC, API-Key — shipped with Cloud Edition |
| Config              | `AUTH_PROVIDER=none\|zitadel\|oidc\|apikey` in environment               |
| Rationale           | Self-hosters running locally don't need identity management; enforcement is a Cloud/multi-user concern |

#### 5.3.8 LLM Provider Abstraction (ADR 009) [Community]

| Aspect    | Specification                                                      |
|-----------|--------------------------------------------------------------------|
| Purpose   | Standardize LLM calls across providers                             |
| Interface | `LLMProvider` base class with `acomplete()`, `aparse_json()`      |
| Backends  | Mistral AI (default), OpenAI, Ollama (self-hosted)                 |
| Config    | `LLM_PROVIDER=mistral|openai|ollama` + provider-specific env vars  |

#### 5.3.9 Retention Worker [Community]

| Aspect          | Specification                                                |
|-----------------|--------------------------------------------------------------|
| Purpose         | Enforce GDPR retention periods                               |
| Trigger         | Daily Cron job (predictable, audit-friendly)                 |
| Retention Rules | Files: 7d, Sessions: 30d, CVs: 90d, Inactive Accounts: 24m |
| Implementation  | Python script, SQLAlchemy ORM, tombstone marking for backups |

#### 5.3.10 Multi-Tenancy (ADR 011) [Cloud Only]

| Aspect    | Specification                                                      |
|-----------|--------------------------------------------------------------------|
| Purpose   | B2B/Team support for career coaches                                |
| Mechanism | Row-Level Security (RLS) + `tenant_id` column on cloud-only tables |
| Namespace | `apliqa.cloud.tenancy`                                             |
| Gating    | Feature flag `APLIQA_EDITION=cloud`                                |

---

## 6. Runtime View

### 6.1 Scenario 1: Complete Tailoring Flow — Human User (Happy Path)

┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │ User │ │Frontend │ │ Backend │ │ LLM │ │Database │ │(Marcus) │ │(Next.js)│ │(FastAPI)│ │Provider │ │(Postgres)│ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ │ │ │ │ │ │ 1. Paste JD URL │ │ │ │──────────────▶│ │ │ │ │ │ 2. POST /api/job/analyze │ │ │ │──────────────▶│ │ │ │ │ │ 3. Scrape URL (Tiered) │ │ │ │──────────────▶│ │ │ │ │◀──────────────│ │ │ │ │ 4. Analyze JD (LLM) │ │ │ │──────────────▶│ │ │ │ │◀──────────────│ │ │ │ │ 5. Store JobAnalysis │ │ │ │──────────────────────────────▶│ │ │◀──────────────│ │ │ │◀──────────────│ 6. Return job_id + gaps │ │ │ │ │ │ │ │ 7. Interview starts │ │ │ │──────────────▶│ │ │ │ │ │ 8. POST /api/session/{id}/interview/message │ │ │──────────────▶│ │ │ │ │ │ 9. LangGraph loop │ │ │ │──────────────▶│ │ │ │ │◀──────────────│ │ │ │ │ 10. Update Master Profile │ │ │ │──────────────────────────────▶│ │ │◀──────────────│ │ │ │◀──────────────│ 11. Question / completion │ │ │ │ │ │ │ │ ... (repeat until gaps filled) ... │ │ │ │ │ │ │ │ 12. Request CV generation │ │ │ │──────────────▶│ │ │ │ │ │ 13. POST /api/cv/generate │ │ │ │──────────────▶│ │ │ │ │ │ 14. Tailor CV (LangGraph) │ │ │ │──────────────▶│ │ │ │ │◀──────────────│ │ │ │ │ 15. Generate PDF (WeasyPrint) │ │ │ │ 16. Store PDF │ │ │ │──────────────────────────────▶│ │ │◀──────────────│ │ │ │◀──────────────│ 17. Return PDF download URL │ │ │ │ │ │ │


### 6.2 Scenario 2: Agent-Driven Tailoring Flow (MCP)

┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │ AI Agent │ │ MCP │ │ Backend │ │ LLM │ │ Database │ │(OpenClaw)│ │ Server │ │ (FastAPI)│ │ Provider │ │(Postgres)│ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │ │ │ │ │ │ 1. tools/call: analyze_jd │ │ │ │ { url: "https://..." } │ │ │ │───────────────▶│ │ │ │ │ │ 2. Invoke JD Intake Service │ │ │ │──────────────▶│ │ │ │ │ │ 3. Scrape + Analyze (LLM) │ │ │ │───────────────▶│ │ │ │ │◀───────────────│ │ │ │ │ 4. Store │ │ │ │───────────────────────────────▶│ │ │◀──────────────│ │ │ │◀───────────────│ 5. Return JobAnalysis JSON │ │ │ │ │ │ │ │ 6. tools/call: get_profile │ │ │ │───────────────▶│ │ │ │ │ │──────────────▶│ │ │ │ │ │───────────────────────────────▶│ │ │ │◀───────────────────────────────│ │ │◀──────────────│ │ │ │◀───────────────│ 7. Return MasterProfile JSON │ │ │ │ │ │ │ │ 8. tools/call: analyze_gaps │ │ │ │ { job_id: "...", profile } │ │ │ │───────────────▶│ │ │ │ │ │──────────────▶│ │ │ │ │ │───────────────▶│ │ │ │ │◀───────────────│ │ │ │◀──────────────│ │ │ │◀───────────────│ 9. Return GapAnalysis │ │ │ │ │ │ │ │ 10. tools/call: generate_cv │ │ │ │ { job_id, options } │ │ │ │───────────────▶│ │ │ │ │ │──────────────▶│ │ │ │ │ │ 11. Tailor + PDF │ │ │ │───────────────▶│ │ │ │ │◀───────────────│ │ │ │ │───────────────────────────────▶│ │ │◀──────────────│ │ │ │◀───────────────│ 12. Return { pdf_url, cv_id } │ │ │ │ │ │ │ │ 13. Agent delivers PDF to human user │ │ │ │ │ │ │


### 6.3 Scenario 3: JD Scraping Fallback (LinkedIn/XING)

┌─────────┐ ┌─────────┐ ┌─────────┐ │ User │ │Frontend │ │ Backend │ └────┬────┘ └────┬────┘ └────┬────┘ │ │ │ │ 1. Paste LinkedIn JD URL │ │──────────────▶│ │ │ │ 2. POST /api/job/analyze │ │──────────────▶│ │ │ │ 3. Tier 1: httpx → FAIL │ │ │ 4. Tier 2: Playwright → FAIL │ │◀──────────────│ │◀──────────────│ 5. Fallback: "Copy-paste instructions" │ │ │ │ 6. Manually paste JD text │ │──────────────▶│ │ │ │──────────────▶│ │ │ │ 7. Process as raw text │ │◀──────────────│ │◀──────────────│ 8. Success │


### 6.4 Scenario 4: GDPR Data Deletion (Daily Cron)

┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │ Cron Scheduler │ │ Retention Worker│ │ PostgreSQL │ └────────┬────────┘ └────────┬────────┘ └────────┬────────┘ │ │ │ │ 1. Daily trigger (00:00 UTC) │ │──────────────────────▶│ │ │ │ 2. DELETE expired files (7d) │ │ │──────────────────────▶│ │ │ 3. DELETE expired sessions (30d) │ │ │──────────────────────▶│ │ │ 4. DELETE expired CVs (90d) │ │ │──────────────────────▶│ │ │ 5. Mark inactive users (24m) │ │ │──────────────────────▶│ │ │ 6. Log retention report │ │◀──────────────────────│ │


---

## 7. Deployment View

### 7.1 Community Edition (Self-Hosted)

┌──────────────────────────────────────────────────────────────────┐ │ USER'S INFRASTRUCTURE │ │ │ │ ┌────────────────────────────────────────────────────────────┐ │ │ │ DOCKER COMPOSE │ │ │ │ │ │ │ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │ │ │ │ backend │ │ postgres │ │ ollama │ │ │ │ │ │ (FastAPI │ │ (PG 16) │ │ (optional │ │ │ │ │ │ + MCP) │ │ :5432 │ │ local LLM)│ │ │ │ │ │ :8000 │ │ │ │ :11434 │ │ │ │ │ └─────────────┘ └─────────────┘ └─────────────┘ │ │ │ │ │ │ │ │ Config: .env (AUTH_PROVIDER, LLM_PROVIDER, APLIQA_EDITION)│ │ │ └────────────────────────────────────────────────────────────┘ │ │ │ └──────────────────────────────────────────────────────────────────┘


### 7.2 Apliqa Cloud (Managed)

┌──────────────────────────────────────────────────────────────────────────────┐ │ HETZNER CLOUD (GERMANY) │ │ │ │ ┌────────────────────────────────────────────────────────────────────────┐ │ │ │ LINUX VPS (€8/month initial) │ │ │ │ │ │ │ │ ┌──────────────────────────────────────────────────────────────────┐ │ │ │ │ │ DOCKER COMPOSE │ │ │ │ │ │ │ │ │ │ │ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │ │ │ │ │ │ frontend │ │ backend │ │ postgres │ │ │ │ │ │ │ │ (Next.js) │ │ (FastAPI │ │ (PG 16) │ │ │ │ │ │ │ │ :3000 │ │ + MCP SSE) │ │ :5432 │ │ │ │ │ │ │ └─────────────┘ │ :8000 │ └─────────────┘ │ │ │ │ │ │ └─────────────┘ │ │ │ │ │ │ ┌─────────────┐ ┌─────────────┐ │ │ │ │ │ │ │ nginx │ │ retention │ │ │ │ │ │ │ │ (reverse │ │ (cron) │ │ │ │ │ │ │ │ proxy) │ │ │ │ │ │ │ │ │ │ :80/:443 │ │ │ │ │ │ │ │ │ └─────────────┘ └─────────────┘ │ │ │ │ │ │ │ │ │ │ │ └───────────────────────────────────────────────────────────────────┘ │ │ │ │ │ │ │ │ Volumes: │ │ │ │ - postgres_data:/var/lib/postgresql/data │ │ │ │ - uploads:/app/uploads (ephemeral, 7-day TTL) │ │ │ │ - generated_pdfs:/app/pdfs (90-day TTL) │ │ │ └────────────────────────────────────────────────────────────────────────┘ │ │ │ └──────────────────────────────────────────────────────────────────────────────┘ │ │ │ │ LLM API │ Auth (OIDC) │ Payments ▼ ▼ ▼ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │ Mistral AI │ │ Zitadel Cloud │ │ Paddle (MoR) │ │ (Paris, EU) │ │ (EU-hosted) │ │ (VAT handling) │ └─────────────────┘ └─────────────────┘ └─────────────────┘


### 7.3 Deployment Process (Cloud)

| Step | Action                          | Tool                                              |
|------|---------------------------------|----------------------------------------------------|
| 1    | Build Docker images locally     | `docker compose build`                             |
| 2    | Export as gzipped tarball       | `docker save \| gzip > release.tar.gz`             |
| 3    | SCP to Hetzner VPS              | `scp release.tar.gz user@hetzner:`                 |
| 4    | Load and restart                | `docker load < release.tar.gz && docker compose up -d` |
| 5    | Run Alembic migrations          | `docker compose exec backend alembic upgrade head` |

### 7.4 Environment Configuration

| Environment | File        | Purpose                              |
|-------------|-------------|--------------------------------------|
| Development | `.env.dev`  | Local Docker Compose, debug mode     |
| Production  | `.env.prod` | Hetzner VPS, production secrets      |

**Key Environment Variables:**

| Variable              | Values                        | Description                          |
|-----------------------|-------------------------------|--------------------------------------|
| `APLIQA_EDITION`      | `community` \| `cloud`        | Edition gating (ADR 007/012)         |
| `AUTH_PROVIDER`        | `none` \| `zitadel` \| `oidc` \| `apikey` | Auth backend (ADR 008); default `none` for Community (local mode) |
| `LLM_PROVIDER`        | `mistral` \| `openai` \| `ollama` | LLM backend selection (ADR 009) |
| `MCP_TRANSPORT`        | `stdio` \| `sse`              | MCP server transport (ADR 010)       |
| `DATABASE_URL`         | PostgreSQL connection string  | Database connection                  |

---

## 8. Cross-cutting Concepts

### 8.1 GDPR Compliance

| Concept                | Implementation                                              |
|------------------------|-------------------------------------------------------------|
| Lawful Basis           | Art. 6(1)(b) for core processing, Art. 9(2)(a) for special category |
| Data Minimization      | All Master Profile sections optional                        |
| Retention Enforcement  | Daily Cron job with TTL rules                               |
| Right to Erasure       | One-click deletion, 72-hour purge, tombstone for backups    |
| Data Residency         | 100% EU (Germany + France) for Cloud                        |
| Encryption             | TLS in transit, disk encryption at rest                     |
| Agent Data Handling    | API-Key scoped; agent requests inherit user's GDPR context  |

### 8.2 DACH Cultural Intelligence

| Concept              | Implementation                                                |
|----------------------|---------------------------------------------------------------|
| Lebenslauf Format    | Structured template with photo, personal details, reverse-chronological |
| Photo Guidance       | Optional field with cultural context tooltip                  |
| Personal Details     | DOB, nationality, marital status with explicit consent        |
| Bilingual Support    | Prompts in de/en, output language selectable (V2: simultaneous) |
| Community Templates  | "Classic German", "Modern Swiss" included in AGPL-3.0        |

### 8.3 ATS Compatibility

| Concept            | Implementation                                    |
|--------------------|---------------------------------------------------|
| Clean Layout       | Single-column, no tables, no graphics             |
| Standard Fonts     | Arial, Calibri, or system fonts                   |
| Keyword Placement  | Natural integration, no stuffing                  |
| File Format        | PDF/A compliant, text-selectable                  |

### 8.4 Error Handling & Logging

| Concept              | Implementation                                              |
|----------------------|-------------------------------------------------------------|
| Structured Logging   | JSON logs with `job_id` / `session_id` correlation          |
| No PII in Logs       | Pseudonymization for user references                        |
| Graceful Degradation | Scraping fallbacks, manual input alternatives               |
| User-Friendly Errors | German + English error messages                             |
| MCP Error Codes      | Standard MCP error responses for agent consumers            |

### 8.5 Edition Gating

| Concept              | Implementation                                              |
|----------------------|-------------------------------------------------------------|
| Feature Flags        | `APLIQA_EDITION` environment variable                       |
| Service-Level Check  | Decorator/middleware on Cloud-only service methods           |
| Upgrade Prompt       | Community users receive 402 with upgrade instructions       |
| Namespace Separation | Cloud-only code in `apliqa.cloud.*` (excluded from OSS dist)|

### 8.6 Agent Interoperability

| Concept              | Implementation                                              |
|----------------------|-------------------------------------------------------------|
| MCP Compliance       | Full Model Context Protocol implementation (tools, resources)|
| API-Key Auth         | Scoped keys with rate limits for agent consumers            |
| Structured Output    | All MCP tools return Pydantic-validated JSON                |
| Usage Tracking       | Per-call credit deduction logged in `usage_logs`            |
| Idempotency          | Deduplication via `raw_text_hash` prevents duplicate charges|

---

## 9. Architecture Decisions

| ADR     | Title                                              | Status      | Edition   |
|---------|----------------------------------------------------|-------------|-----------|
| ADR 001 | Job-First Intake & Analysis Architecture           | APPROVED    | Community |
| ADR 002 | Master Profile & Data Persistence Strategy         | APPROVED    | Community |
| ADR 003 | Paddle as Merchant of Record                       | APPROVED    | Cloud     |
| ADR 004 | Stateful Backend for Interview Orchestration       | APPROVED    | Community |
| ADR 005 | Daily Cron for GDPR Retention Enforcement          | APPROVED    | Community |
| ADR 006 | CSS-based Themes for PDF Extensibility             | APPROVED    | Community |
| ADR 007 | Open Core Architecture (AGPL-3.0)                  | APPROVED    | Both      |
| ADR 008 | Auth Abstraction Wrapper (Pluggable Backends)      | APPROVED    | Community |
| ADR 009 | LLM Provider Abstraction Layer                     | APPROVED    | Community |
| ADR 010 | MCP Server — Agent-First Platform                  | APPROVED    | Community |
| ADR 011 | Multi-Tenancy for B2B/Team Support (RLS)           | APPROVED    | Cloud     |
| ADR 012 | Feature-Flag Based Edition Gating                  | APPROVED    | Both      |

Full ADR content: `docs/adr/ADR.md`

---

## 10. Quality Requirements

### 10.1 Performance

| Requirement          | Target       | Measurement                           |
|----------------------|--------------|---------------------------------------|
| JD Analysis          | <30 seconds  | End-to-end from URL submission        |
| Interview Response   | <5 seconds   | Per question generation               |
| PDF Generation       | <10 seconds  | From "Generate" click to download     |
| Page Load            | <3 seconds   | Initial frontend load                 |
| MCP Tool Response    | <5 seconds   | Per tool call (agent channel)         |
| Agent Full Flow      | <30 seconds  | End-to-end tailored CV via MCP        |

### 10.2 Reliability

| Requirement            | Target | Measurement                    |
|------------------------|--------|--------------------------------|
| Uptime (Cloud)         | 99.5%  | Monthly average                |
| Scraping Success       | >80%   | Tier 1 + Tier 2 combined      |
| LLM Response Quality   | >90%   | Human review sampling          |
| MCP Availability       | 99.5%  | Agent endpoint uptime          |

### 10.3 Security

| Requirement        | Implementation                                    |
|--------------------|---------------------------------------------------|
| Authentication     | Community: no enforcement (single-user local mode, `NoAuthProvider`); Cloud: Zitadel OIDC enforced (ADR 008) |
| Authorization      | User-scoped data access, RLS for multi-tenancy    |
| Encryption         | TLS 1.3, AES-256 at rest                          |
| Input Validation   | Pydantic schemas, SQL injection prevention         |
| API-Key Management | Hashed storage, scoped permissions, revocable      |
| Rate Limiting      | Per API-Key limits for agent channel               |

---

## 11. Risks and Technical Debt

### 11.1 Known Risks

| Risk                              | Likelihood | Impact | Mitigation                                              |
|-----------------------------------|------------|--------|---------------------------------------------------------|
| LLM Hallucination                 | Medium     | High   | LangGraph validation nodes, structured output           |
| Scraping Instability              | High       | Medium | Tiered approach, manual fallback UI                     |
| Paddle Integration Complexity     | Medium     | Medium | Early sandbox testing, webhook testing                  |
| Solo-Founder Burnout              | Medium     | High   | MVP scope discipline, automation                        |
| OSS Cannibalization               | Low        | Medium | Monetize convenience + Recruiter Intelligence           |
| Platform Risk (LinkedIn/OpenAI)   | Medium     | Medium | Vertical specialization (GxP), persistent Master Profile|
| Agent Channel Abuse               | Medium     | Medium | Rate limiting, API-Key scoping, usage monitoring        |
| AGPL Compliance Burden            | Low        | Low    | Clear namespace separation, legal review                |

### 11.2 Technical Debt

| Item                        | Rationale              | Payoff Timeline     |
|-----------------------------|------------------------|---------------------|
| Single VPS Deployment       | MVP cost               | Post-revenue        |
| No Staging Environment      | Cost                   | Post-revenue        |
| Basic Analytics             | Privacy-first          | V2 (Plausible)      |
| No Skill Taxonomy           | Free-text acceptable   | V2                  |
| Limited PDF Templates (2)   | MVP speed              | V2 (Q3 2026)        |
| No WebSocket for Interview  | REST polling acceptable| V2                  |

---

## 12. Glossary

| Term                    | Definition                                                                 |
|-------------------------|----------------------------------------------------------------------------|
| ATS                     | Applicant Tracking System — software used by recruiters to parse CVs       |
| DACH                    | Germany (DE), Austria (AT), Switzerland (CH) market region                 |
| Edition Gate            | Feature-flag mechanism separating Community and Cloud functionality         |
| GDPR                    | General Data Protection Regulation — EU privacy law                        |
| JD                      | Job Description — the target document for tailoring                        |
| LangGraph               | Framework for building stateful, multi-actor applications with LLMs        |
| Lebenslauf              | German-style CV format with specific conventions                           |
| Master Profile          | User's comprehensive career autobiography, enriched over time              |
| MCP                     | Model Context Protocol — standard for AI agent tool interoperability       |
| MoR                     | Merchant of Record — handles payments, VAT, compliance (Paddle)            |
| Open Core               | Business model: open-source base (AGPL-3.0) + proprietary cloud features  |
| Recruiter Intelligence  | Domain-specific reasoning (e.g., GxP, industry conventions) — Cloud only   |
| RLS                     | Row-Level Security — PostgreSQL feature for multi-tenant data isolation    |
| Tailored CV             | JD-specific output emphasizing relevant experience                         |

---

---

## Appendix A: Edition Feature Matrix

| Feature                          | Community (AGPL-3.0) | Cloud (Proprietary) |
|----------------------------------|:--------------------:|:-------------------:|
| JD Intake & Analysis Engine      | ✅                   | ✅                  |
| Master Profile Service           | ✅                   | ✅                  |
| Interview Orchestrator           | ✅                   | ✅                  |
| CV Tailoring Engine              | ✅                   | ✅                  |
| PDF Generator                    | ✅                   | ✅                  |
| MCP Server                       | ✅                   | ✅                  |
| REST API                         | ✅                   | ✅                  |
| Auth Abstraction (interface)     | ✅                   | ✅                  |
| Auth Enforcement (OIDC/Zitadel) | ❌                   | ✅                  |
| LLM Provider Abstraction         | ✅                   | ✅                  |
| Retention Worker                 | ✅                   | ✅                  |
| Basic Templates (Classic DE, CH) | ✅                   | ✅                  |
| Docker Compose Setup             | ✅                   | ✅                  |
| Recruiter Intelligence (GxP)     | ❌                   | ✅                  |
| Premium Templates                | ❌                   | ✅                  |
| Multi-Tenancy (B2B)              | ❌                   | ✅                  |
| Managed Hosting                  | ❌                   | ✅                  |
| Priority Rendering               | ❌                   | ✅                  |
| Analytics Dashboard              | ❌                   | ✅                  |
| Paddle Billing Integration       | ❌                   | ✅                  |
| Next.js Frontend                 | ❌                   | ✅                  |

---

**This document is the authoritative source for Apliqa architecture. All implementation decisions should reference this document.**

*Apliqa — Verifiable Trust. Deep Reasoning. Agent-First.*


