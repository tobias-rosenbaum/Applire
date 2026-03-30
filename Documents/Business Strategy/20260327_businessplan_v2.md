# Businessplan: Apliqa UG (haftungsbeschränkt)

**Version:** 2.0
**Founding Project:** Apliqa — The Open-Source CV Intelligence Platform
**Founder:** Tobias Rosenbaum
**Location:** Mainz, Germany
**Status:** Pre-incorporation (i.G.)
**Date:** March 2026
**Changelog v2.0 (2026-03-27):**
- Broadened target market positioning: "All DACH applicants" with regulated industries as premium differentiation layer (previously: exclusive focus on regulated industries)
- Added Product Vision section (§11) with future scope expansion: Mock Interviews, Gamification, Career Development, Job Search & Application Automation
- Updated USP framing: Pharma/GxP expertise as competitive advantage ("sword"), not as market restriction ("fence")
- Updated Roadmap (§10) to reflect new product phases
- Updated Risk Analysis (§9) to address scope expansion risks

---

## 1. Executive Summary

Apliqa is an AI-powered Career Intelligence platform for **all applicants in the DACH market**. Unlike generic CV builders, Apliqa combines a persistent **Master Profile** with deep **"Recruiter Intelligence"** to automate the high-quality tailoring of job application documents. While Apliqa serves job seekers across all industries, it offers **unmatched depth in regulated sectors** (Pharma, GxP, Medtech) — a specialization that no competitor can match and that serves as proof of quality for all users.

Operating on an **"open core"** model, Apliqa provides a verifiable, privacy-first open source version for developers and AI agents (via MCP), while monetizing convenience and advanced reasoning through the **Apliqa Cloud**.

Long-term, Apliqa will evolve from a CV-focused tool into a comprehensive **Career Intelligence Platform**, adding mock interviews, career path guidance, and intelligent job search to its capabilities.

---

## 2. Business Idea & USP

### 2.1 The Problem

- **Maintenance Effort:** Experienced professionals need an excessive amount of time fine-tuning their CVs to demanding job offers.
- **Cultural Mismatch:** International candidates fail to meet DACH-specific CV norms despite being highly qualified.
- **Low-Quality AI:** Generic AI CV tools lack workflows for in-depth profile and gap analysis.
- **Statelessness:** Users must re-upload data for every application, creating friction.
- **Trust Deficit:** Users are wary of uploading sensitive career data to closed-source "thin wrappers."

### 2.2 The Solution: Apliqa

- **Master Profile:** A central, enriching career data vault that gets better with every use.
- **Recruiter Intelligence:** Extract important information from JD, match JD against profile, interview candidate to close gaps.
- **DACH-Native:** Built-in cultural rules for German/Austrian/Swiss application standards.
- **Agent-First:** Accessible to AI assistants via the Model Context Protocol (MCP).

### 2.3 Unique Selling Proposition (USP)

- **Verifiable Trust:** Open-source core (AGPL-3.0) for auditable GDPR compliance.
- **Deep Reasoning for Everyone, Unmatched in Regulated Industries:** Apliqa's core intelligence serves all job seekers in the DACH market. Its additional specialization in regulated industries (Pharma, GxP, Medtech) is a proof of precision that benefits every user — not a market restriction.
- **Synergistic Distribution:** The first platform optimized for the "AI agents as customers" wave.

### 2.4 Market Positioning: Layers, Not Barriers

Apliqa's market approach follows a layered model:

```
┌─────────────────────────────────────────────────────┐
│  🔵 Industry Specialization Layer (Premium)          │
│     → Pharma/GxP/Medtech deep knowledge              │
│     → Compliance-aware CV formatting                  │
│     → Industry-specific interview preparation         │
├─────────────────────────────────────────────────────┤
│  🟢 DACH Career Intelligence (Core — for everyone)   │
│     → Master Profile, CV-Tailoring                    │
│     → Cultural rules, multilingual support            │
│     → Agent-First (MCP/API)                           │
│     → Mock Interviews, Gamification                   │
└─────────────────────────────────────────────────────┘
```

**Pharma expertise is our sword, not our fence.** "Apliqa is so precise, it works for regulated industries" makes the platform attractive for *every* user — similar to how automotive safety standards proven in emergency vehicles build trust for all drivers.

---

## 3. Market Analysis

### 3.1 Market Size & Growth

- **Global Resume Builder Market:** $2.35B (2025), growing to $5B (2035).
- **AI Segment:** Growing at 20% CAGR ($1.8B by 2032).
- **DACH Market:** Europe's largest job market, with 300,000+ international relocators annually needing cultural CV adaptation.
- **Total Addressable Market (TAM):** All job seekers in DACH — millions of applications written annually. Pharma/GxP alone accounts for 50,000–100,000 specialized applications per year, but the broader DACH market is orders of magnitude larger.

### 3.2 Target Personas

[[personas]]

**Primary (Broad Market):**
- **"Marcus" (The Expert):** Experienced professional across any industry, high willingness to pay for precision. *Includes but is not limited to* regulated industry professionals.
- **"Priya" (The Relocator):** Moving to DACH from abroad, needs cultural "translation" of career history. Could be a software developer applying at SAP, an engineer at Bosch, or a scientist at Bayer.

**Specialized:**
- **"Jason" (The Recruiter):** Wants to efficiently generate well-made CVs for his clients across various industries.
- **"Kaile" (AI Agent):** Calling the Apliqa API/MCP on behalf of its human user.

**Premium (Industry Layer):**
- **"Dr. Weber" (The Pharma/GxP Specialist):** Needs CVs that reflect GMP experience, validation projects, and compliance language. Willing to pay premium for industry-specific intelligence.

---

## 4. Business Model & Revenue Strategy

### 4.1 Open Core Strategy

- **Community (Free):** Core engine, Master Profile API, basic templates, Docker setup.
- **Apliqa Cloud (Paid):** Zero-setup hosting, Recruiter Intelligence, premium templates, priority rendering, multi-tenancy, usage by AI agents.
- **Industry Packs (Future):** Specialized knowledge layers (e.g., "Pharma Career Pack") as add-on upsells.

### 4.2 Revenue Streams

- **B2C Subscriptions:** €9.99/mo or €99/year for cloud users (Freemium: 1–2 CVs free).
- **Usage-Based (Agent Channel):** €0.50–€2.00 per tailored CV via API/MCP (typical: €20 for 20 credits).
- **B2B / Team:** Career coach portal, shared templates (€29.99/mo base + €2–€5 per profile, 14-day pilot).
- **Future: Mock Interview Credits:** Pay-per-session for AI-powered interview preparation.

---

## 5. Marketing & Distribution

- **Organic Engine:** GitHub stars and developer community contributions.
- **Agent Channel:** Listing on MCP marketplaces (Anthropic, OpenAI, Cursor).
- **SEO/Niche (Broad + Specialized):**
  - Broad: "Lebenslauf erstellen", "Bewerbung DACH", "CV for Germany"
  - Specialized: "Bewerbung in regulierten Branchen", "Pharma CV Germany"
  - Relocator: "Moving to Germany CV", "DACH application guide"
- **Partnerships:** Relocation agencies, university international offices, industry associations.
- **Community:** Reddit, Hacker News, LinkedIn (organic), developer communities.
- **Persona-specific Messaging:** Tailored communication strategy per persona (efficiency for Marcus, cultural safety for Priya, ROI for Jason, technical precision for Kaile).

---

## 6. Implementation & Technology

- **Backend:** FastAPI (Python), robust and MCP-ready.
- **Orchestration:** LangGraph (agentic workflows for complex tailoring).
- **LLM:** Mistral AI (EU-hosted, high reasoning, GDPR native).
- **PDF Engine:** WeasyPrint (CSS-based high-quality rendering).
- **Protocol:** Model Context Protocol (MCP) for agentic interoperability.
- **Hosting:** Hetzner (Germany) initially; Kubernetes migration planned for Year 2 or at 50,000 requests/month.

---

## 7. Company Structure & Legal

- **Legal Form:** UG (haftungsbeschränkt), later converting to GmbH.
- **Shareholders:** Tobias Rosenbaum (100%).
- **Governance:** Managed as a "Nebengewerbe" during the MVP phase.
- **Compliance:** DSGVO (GDPR) by design, VVT maintained from Day 1.
- **Merchant of Record:** Paddle (handles VAT compliance in 100+ countries).
- **Trademark:** "Apliqa" registered as Wortmarke at DPMA (€290).
- **Domains:** apliqa.de, apliqa.com, apliqa.eu secured.

---

## 8. Financial Plan (Year 1)

### 8.1 Capital Requirements

| Position | Cost |
|---|---|
| Total Initial Budget (Self-funded) | €10,000 |
| Formation Costs (Notary, Handelsregister, Gewerbe) | ~€800 |
| Trademark (DPMA) | €290 |
| Infrastructure (Hetzner, Mistral, Email) | ~€100/mo |
| Bookkeeping/SB | ~€2,500/year |

### 8.2 Revenue Projections (Conservative)

| Year | Projection | Focus |
|---|---|---|
| Year 1 | €5,000–€15,000 | Validation (broad DACH market + regulated industry early adopters) |
| Year 2 | €50,000–€150,000 | Agent channel scaling, Mock Interviews launch |
| Year 3 | €300,000+ | Market leadership in "Agentic Career Intelligence", Career Platform expansion |

---

## 9. Risk Analysis & Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| **Platform Risk (LinkedIn/OpenAI)** | High | Vertical depth in regulated industries + persistent Master Profile state + open-source community lock-in |
| **OSS Cannibalization** | Medium | Monetizing convenience, premium reasoning, managed agent endpoint, and industry-specific knowledge packs |
| **Bureaucracy Lag** | Low | Early filing (USt-IdNr, ELSTER) and sidebar roadmap tasks |
| **Scope Creep (Product Vision)** | Medium | Strict phasing: MVP first (CV Tailoring), then Mock Interviews, then Career features. No feature ships before the previous one is validated. |
| **Regulatory Risk (Career Services)** | Medium | Career path features positioned as "information service", not professional career counseling (§§ 288 ff. SGB III). Job search features only after legal review and seed funding. |
| **Affiliate Trust Conflict** | Low | Any future monetized recommendations (e.g., training courses) will be transparently labeled. Open-source ethos demands honesty. |

---

## 10. Roadmap

### Phase 1: Foundation & MVP (2026)

| Quarter | Milestone |
|---|---|
| Q1 2026 | Domain registration (apliqa.de/.com/.eu), ELSTER registration, OSS repo preparation |
| Q2 2026 | UG incorporation, Paddle setup, MVP launch (Human Cloud + OSS), SEO & Content Marketing start |
| Q3 2026 | REST API launch, developer documentation |
| Q4 2026 | MCP Server launch, listing on agent marketplaces |

### Phase 2: Product Expansion (2027)

| Quarter | Milestone |
|---|---|
| Q1 2027 | Mock Interview feature (Beta) — AI-generated questions based on JD + Master Profile |
| Q2 2027 | Gamification elements (Profile Completeness Score, Interview Readiness Score) |
| Q3 2027 | Industry Packs (Pharma Career Pack as first premium add-on) |
| Q4 2027 | Career Path Advisory (informational, non-regulated) |

### Phase 3: Platform Vision (2028+)

| Quarter | Milestone |
|---|---|
| 2028 H1 | Job Search & Recommendation Engine (curated job suggestions based on Master Profile) |
| 2028 H2 | One-Click Application Preparation (full document package generation) |
| 2028+ | Active Job Application Automation (requires legal review, seed funding, and API partnerships with job platforms) |

### Key Metrics Targets

| Metric | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| Paying Cloud Users | 100 | 1,000 | 5,000 |
| Agent API Calls/month | 500 | 10,000 | 50,000 |
| GitHub Stars | 500 | 2,000 | 5,000 |

---

## 11. Product Vision: From CV Tool to Career Intelligence Platform

Apliqa's long-term vision extends beyond CV tailoring into a comprehensive Career Intelligence Platform. The following features are planned in strict sequence, each building on validated demand from the previous phase:

### 11.1 Mock Interviews (Phase 2 — Q1 2027) ⭐ Priority

AI-powered interview preparation using the candidate's Master Profile and the target Job Description.

- **How it works:** Generates role-specific questions, evaluates candidate responses, provides targeted improvement suggestions.
- **Monetization:** Included in Cloud subscription (limited sessions), additional sessions as pay-per-use (€2–5/session).
- **Risk:** Low. Natural extension of existing data and AI capabilities. No regulatory concerns as long as clearly communicated as AI-based practice tool.

### 11.2 Gamification (Phase 2 — Q2 2027)

UX enhancement layer to improve user engagement and retention.

- **Elements:** Profile Completeness Score, Interview Readiness Score, application streaks, achievement badges (e.g., "First German CV", "Pharma Specialist").
- **Monetization:** Indirect — improves retention and data quality (more complete profiles = better AI output).
- **Caveat:** Must not undermine brand positioning of trust and precision. Gamification supports, never replaces, professional quality. Not suitable as external marketing message for the regulated industry persona.

### 11.3 Career Path Advisory (Phase 2 — Q4 2027)

Informational career guidance based on the Master Profile and market data.

- **How it works:** Suggests career trajectories, identifies skill gaps, recommends relevant training/certifications.
- **Monetization:** Potential affiliate revenue from training providers (must be transparently labeled).
- **Risk:** Medium. Must be positioned as "information service" to avoid private career counseling regulations (§§ 288 ff. SGB III). Affiliate model must not compromise trust (transparent labeling mandatory).

### 11.4 Job Search & Application Automation (Phase 3 — 2028+)

The end-to-end vision: find matching jobs, prepare all documents, submit with one click.

- **How it works:** Agent autonomously searches job listings, matches against Master Profile, prepares tailored CV + cover letter, awaits user confirmation before submission.
- **Monetization:** Premium subscription tier or per-application fee.
- **Risk:** High. Requires:
  - Legal review regarding private employment placement (§ 296 SGB III)
  - API partnerships with job platforms (scraping prohibited by most ToS)
  - Enhanced DSGVO framework for autonomous application submission
  - Significant capital investment (seed round recommended)
- **Decision:** Parked until significant traction and funding. Mentioned as long-term vision only.

---

*This document is version-controlled. Previous version: v1.0 (2026-03-24). For detailed change history, see the changelog at the top of this document.*
