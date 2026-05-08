---
title: Sprint 25 — Cover Letter Generation
date: 2026-04-13
status: approved
---

# Sprint 25 — Cover Letter Generation

## Overview

Applire gains AI-generated cover letters as a companion document to the generated CV. A cover letter shares the job context, user profile, and color profile of its paired CV, but is a distinct artifact with its own sections, LLM prompt, Jinja2 templates, and lifecycle.

---

## Decisions

| # | Decision | Rationale |
|---|---|---|
| 1 | Post-CV add-on, not a flow step | Keeps the core flow clean for CV-only users; cover letter is optional and surfaces as a clear upsell after CV completion |
| 2 | One cover letter per application | Mirrors effective behavior of CVs (FlowSession points at one active record) |
| 3 | Paired templates (7 matching sets) | Produces a coherent Bewerbungsmappe; minimal template decision for the user |
| 4 | Minimal guided pre-gen input | Recipient auto-extracted from JD; salary, availability, motivation, tone collected in a modal |
| 5 | Sections: Header, Recipient, Body, Signature & Date | Classic Bewerbungsschreiben structure; maps cleanly to editable units |
| 6 | Dedicated page `/cover-letter/[id]` with CV↔CL navigation | User can review both documents together before sending |
| 7 | Full parallelism with CV pipeline | Zero risk to existing CV code; clean separation of concerns (ADR-027) |
| 8 | Configurable GDPR TTLs via environment variables | Self-hosters can comply with jurisdiction-specific retention requirements (ADR-005 amendment) |

---

## Architecture

### New DB Table: `generated_cover_letters`

```
GeneratedCoverLetter
  id                    UUID PK
  job_analysis_id       FK → job_analyses (indexed)
  profile_id            FK → master_profiles
  template              str  — mirrors CV template name (e.g. "executive")
  letter_data           JSONB  { header, recipient, body, signature }
  pre_gen_inputs        JSONB  { salary, availability, motivation, tone, recipient_name, recipient_company }
  section_overrides     JSONB  — manual edits, same pattern as GeneratedCV
  color_profile_id      FK → cv_color_profiles (nullable, shared with paired CV)
  status                str  — pending | generating | ready | failed | expired
  error_message         text (nullable)
  created_at            timestamptz
  expires_at            timestamptz  — GENERATED_DOCUMENTS_TTL_DAYS (default 90d, env-configurable)
  deleted_at            timestamptz (nullable)
```

`FlowSession` gains one new nullable FK column: `generated_cover_letter_id → generated_cover_letters`.

Two Alembic migrations required:
1. `add_generated_cover_letters_table`
2. `add_flow_session_cover_letter_fk`

### Configurable TTL Constants (`applire/constants.py`)

All retention TTL values moved from scattered hardcoded module-level constants to `constants.py` with environment variable overrides:

```python
GENERATED_DOCUMENTS_TTL_DAYS: int = int(os.environ.get("GENERATED_DOCUMENTS_TTL_DAYS", "90"))
INTERVIEW_SESSION_TTL_DAYS: int = int(os.environ.get("INTERVIEW_SESSION_TTL_DAYS", "30"))
UPLOAD_TTL_DAYS: int = int(os.environ.get("UPLOAD_TTL_DAYS", "7"))
PROFILE_INACTIVITY_TTL_DAYS: int = int(os.environ.get("PROFILE_INACTIVITY_TTL_DAYS", "730"))
```

Files updated to import from `constants`: `models/cv.py`, `models/uploads.py`, `models/application.py`, `services/session.py`, `retention/worker.py`.

### New API Router: `/api/cover-letter/`

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/cover-letter/generate` | Enqueue async generation; returns `{ id, status: "pending" }` immediately |
| `GET` | `/api/cover-letter/{id}/status` | Poll for `ready` / `failed` |
| `GET` | `/api/cover-letter/{id}/html` | Render HTML via Jinja2 (iframe srcDoc preview) |
| `GET` | `/api/cover-letter/{id}/pdf` | Playwright → PDF download |
| `PATCH` | `/api/cover-letter/{id}/section` | Manual section override — `{ section: "body", content: "..." }` |
| `GET` | `/api/cover-letter/by-job/{job_id}` | Fetch active cover letter for a job |

### Generation Service (`services/cover_letter.py`)

Mirrors `services/cv.py`:

1. Create `GeneratedCoverLetter` record with `status=pending`
2. Enqueue `_render_cover_letter_background` via FastAPI `BackgroundTasks`
3. Background task:
   - Load `JobAnalysis` + `MasterProfile` + linked `GeneratedCV` (for `tailored_data`)
   - Extract recipient name and company from `job_analysis.raw_jd` (regex + LLM fallback)
   - Build LLM prompt: tailored CV data + JD text + `pre_gen_inputs`
   - LLM returns structured JSON → stored in `letter_data`
   - Render Jinja2 template → HTML snapshot
   - Playwright → PDF via `StorageProvider`
   - Status: `pending → generating → ready | failed`

**LLM prompt inputs:**
- Tailored CV data (name, contact, career summary, key achievements from `tailored_data`)
- Full job description text
- `pre_gen_inputs`: salary, availability, motivation, tone, recipient override
- Target language: DE or EN (detected from JD)
- DACH conventions flag: include Gehaltswunsch + Eintrittstermin if salary/availability provided

**`letter_data` JSONB schema:**
```json
{
  "header":    { "name", "address", "phone", "email", "photo_url" },
  "recipient": { "name", "title", "company", "address", "date" },
  "body":      { "paragraphs": ["...", "...", "..."] },
  "signature": { "closing", "name", "date" }
}
```

### Jinja2 Templates (7 paired templates)

| CV Template | Cover Letter Template | Notes |
|---|---|---|
| `lebenslauf` | `lebenslauf_letter.html.j2` | Dark header bar, clean serif body |
| `modern_swiss` | `modern_swiss_letter.html.j2` | Accent top border, sans-serif |
| `executive` | `executive_letter.html.j2` | Dark navy header, gold accent rule |
| `creative_sidebar` | `creative_sidebar_letter.html.j2` | Dark sidebar keeps personal details |
| `compact_pro` | `compact_pro_letter.html.j2` | Dense typography, senior professional tone |
| `tech_developer` | `tech_developer_letter.html.j2` | Dark theme, monospace accents |
| `academic` | `academic_letter.html.j2` | Centered serif, traditional conventions |

All templates receive the same `color_profile` Jinja2 context as their paired CV template. Template is auto-selected to match the CV template at generation time; user can override in the Design tab.

### Retention Worker

`retention/worker.py` gains one new purge function `_purge_cover_letters` that hard-deletes records where `expires_at < now`. Reads `GENERATED_DOCUMENTS_TTL_DAYS` from `constants` (same value as CVs).

---

## Frontend

### Entry Point

**CV page → Actions tab** gains a "Generate Cover Letter" button (visible once CV status is `ready`). Clicking opens the pre-generation modal.

### Pre-Generation Modal

Fields:
- **Recipient name** — pre-filled from JD extraction, editable
- **Company** — pre-filled from JD extraction, editable
- **Expected salary** (optional) — free text, included as Gehaltswunsch if provided
- **Availability / notice period** (optional) — free text, included as Eintrittstermin if provided
- **Personal motivation** (optional) — textarea; LLM improvises from JD if blank
- **Tone** — segmented control: Formal / Professional / Conversational

### Cover Letter Page (`/cover-letter/[id]`)

Route: `app/flow/[flowId]/cover-letter/page.tsx`

Layout mirrors the CV page preview phase:
- **Left 50% (`w-1/2 min-w-0`)**: cover letter iframe preview (`srcDoc` pattern, same as CV)
- **Right 50% (`w-1/2 min-w-[340px]`)**: `CoverLetterRefinementPanel` with three tabs

**Top bar navigation:**
- Breadcrumb: `{role title} › Cover Letter`
- `← View CV` button (links to `/flow/[flowId]/cv`)
- `Download PDF` button

**Content tab — section cards:**

| Section | Behavior |
|---|---|
| Header | Auto-filled from profile; read-only card |
| Recipient | Auto-filled from JD extraction; editable fields (name, company) |
| Body | Editable textarea + "AI Rewrite" button (Kaile single-turn, same pattern as CV section rewrite) |
| Signature & Date | Auto-filled (today's date + profile name); read-only card |

**Design tab:**
- Template picker (7 options, current shown as selected)
- Color profile (shared with CV — shows same accent color, links to CV page to change)

**Actions tab:**
- Regenerate Cover Letter (opens pre-gen modal pre-filled with current inputs)
- Download PDF

---

## User Journeys

### Marcus — "Fastest path to a complete Bewerbungsmappe"

After downloading the CV (Step 7 of existing journey), Marcus sees the "Generate Cover Letter" button in the Actions tab. He fills in salary expectation and availability, leaves motivation blank, picks Formal tone. Recipient is pre-filled from the JD. Clicks Generate.

15 seconds later he lands on `/cover-letter/[id]`. The Executive cover letter matches his CV — dark navy header, gold accent, his photo. He reads the letter, is satisfied, downloads the PDF.

**Emotional beat:** *"I just produced a complete Bewerbungsmappe in 25 minutes. CV + Anschreiben, both professional and consistent. That would have taken me an evening."*

**Total journey time with cover letter: ~25 minutes** (was ~18 minutes for CV alone)

### Felix — "Surgical control over every word"

Felix generates the cover letter and reads the body critically. The opening paragraph doesn't capture his specific motivation for the company. He clicks the Body section card, edits the textarea directly, then uses "AI Rewrite" to let Kaile rephrase a specific paragraph with his direction. He reviews the suggestion, applies it, saves, and downloads.

**Emotional beat:** *"This sounds like me now. The structure was right — I just needed to add my voice."*

---

## Epics & User Stories

### Epic E010 — Cover Letter Generation

**Marcus track — "Fastest path to a complete Bewerbungsmappe"**

| Story ID | Title | Priority |
|---|---|---|
| US-CL01 | Generate cover letter from CV + JD | High |
| US-CL02 | Pre-generation input form (salary, availability, motivation, tone) | High |
| US-CL03 | Auto-extract recipient name and company from JD | High |
| US-CL04 | Paired template auto-selected to match CV | High |
| US-CL05 | Navigate between CV and cover letter pages | High |
| US-CL06 | Download cover letter as PDF | High |

**Felix track — "Surgical control over every word"**

| Story ID | Title | Priority |
|---|---|---|
| US-CL07 | Edit cover letter body with direct text input | Medium |
| US-CL08 | AI rewrite of cover letter body (Kaile single-turn) | Medium |
| US-CL09 | Override cover letter template in Design tab | Medium |
| US-CL10 | Regenerate cover letter with different pre-gen inputs | Medium |

**Cross-cutting**

| Story ID | Title | Priority |
|---|---|---|
| US-CL11 | Configurable GDPR retention TTLs via environment variables | High |

---

## Testing

| Tier | What |
|---|---|
| Unit | `GeneratedCoverLetter` model, TTL constant resolution, recipient extraction, `letter_data` schema validation |
| Integration | Full generation flow (mock LLM), section override persistence, retention worker purge |
| E2E | Marcus happy path: modal → generate → preview → download; Felix path: body edit → AI rewrite → save → download |

Coverage gate: ≥75% backend unit coverage maintained.

---

## ADR References

- **ADR-005 (amended)**: TTL values now configurable via environment variables; `generated_cover_letters` added to retention schedule
- **ADR-027 (new)**: Cover Letter as a Parallel First-Class Document Artifact — rationale for full parallelism approach
