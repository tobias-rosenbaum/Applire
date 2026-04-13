# Design Spec: CV Section Editor — The Finetuner

**Date:** 2026-04-03
**Sprint:** 9
**Status:** Approved
**Author:** Claude Code (brainstorming session with Tobias Rosenbaum)
**ADR:** ADR-019

---

## Problem

The current CV flow is forward-only and output-only. After generation, the user can download or regenerate — but cannot edit individual sections. Users who read their generated CV critically and want surgical control over specific text (the "Finetuner" mode) have no path forward except regenerating from scratch.

Additionally, gap completion currently requires entering the interview flow as a separate step. There is no way to close a gap in context — i.e., while looking at the section of the CV where that gap is relevant.

---

## Persona

**Felix — The Finetuner** (Persona 7, documented in `Documents/Product Specifications/Personas/Finetuner.md`)

Felix is a mode, not a distinct user type. Any existing persona (Marcus, Priya, Emma) can become Felix when they open a generated CV and want to edit it rather than accept the AI output as-is.

**JTBD:** *"This CV needs to sound like me, not like an AI."*

---

## Design Decisions (resolved during brainstorming)

| Question | Decision |
|---|---|
| Where do edits live? | User decides per save: "Save to Master Profile" or "Just for this CV" |
| Desktop layout | Split-screen: editor panel left, CV preview right |
| Mobile layout | Section accordion: mini preview top, collapsible section cards below |
| Preview update | Automatic on every section save (Jinja2 re-render, no Playwright) |
| Gap completion path | Dual: manual text edit OR Kaile-assisted (one question → AI suggestion) |
| Data architecture | Approach 1: JSON snapshot + section overrides on GeneratedCV (ADR-019) |

---

## Architecture (Approach 1 — Snapshot + Override)

### Data Model

Two new JSONB columns on `generated_cvs` (one Alembic migration, no new tables):

```sql
content_snapshot  JSONB      -- populated at CV generation time
section_overrides JSONB      -- user edits, keyed by section ID, starts as {}
```

`content_snapshot` shape:
```json
{
  "introduction": "string",
  "positions": [{ "id": "uuid", "title": "...", "company": "...", "period": "...", "bullets": ["..."] }],
  "skills": ["string"],
  "education": [{ "id": "uuid", "degree": "...", "institution": "...", "year": "..." }]
}
```

`section_overrides` shape:
```json
{
  "introduction": "user-edited text",
  "position::{uuid}": "user-edited bullets"
}
```

### New Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/cv/{id}/sections` | Snapshot + overrides + gap hints per section |
| `PATCH` | `/api/cv/{id}/sections/{section_id}` | Write override, trigger Jinja2 re-render, optional `save_to_profile` |
| `POST` | `/api/cv/{id}/sections/{section_id}/assist` | Start Kaile micro-session for gap in this section |
| `GET` | `/api/cv/{id}/html` | **Updated** — now applies overrides before returning HTML |

### Gap Hint Computation

Computed at request time in `GET /api/cv/{id}/sections`:
- Load gap_analysis via `flow_sessions.gap_analysis_id`
- Score each Category B/C gap against each section by keyword overlap
- Return hints under each section; unmapped gaps → `general_gaps` bucket
- No LLM, no stored mapping, ~5ms

### Profile Save Path

`PATCH /api/cv/{id}/sections/{section_id}` with `save_to_profile: true`:
- Calls existing `PATCH /api/profile` merge pipeline (ADR-013)
- Additive enrichment model applies — same as interview answers
- Conflicts surfaced via existing conflict resolution UI

### CV Generation Pipeline Change

At generation time: after LLM content selection, extract structured snapshot → write to `content_snapshot`. Pure data transformation, ~10ms, no additional LLM call.

---

## User Journey

1. CV preview loads → Felix reads critically → clicks "Fine-tune"
2. Split-screen opens (desktop) / accordion (mobile)
3. Felix selects a section → editor opens with current text + gap hints
4. **Path A (manual):** types directly → gap auto-resolves if keyword appears
5. **Path B (Kaile-assist):** clicks "Let Kaile help" → one question → AI suggests text → Felix accepts/edits/rejects
6. Felix saves → prompted: "Save to Profile" or "Just this CV" → preview auto-updates
7. Felix iterates across sections → downloads when satisfied

**Branching:** unsaved changes prompt on navigation; re-render failures show stale-preview banner; all gaps resolved → green indicator + primary download CTA.

---

## New Frontend Components

| Component | Purpose |
|---|---|
| `FineTunePanel.tsx` | Split-screen / accordion container, mounts from CVPreview "Fine-tune" toggle |
| `SectionEditor.tsx` | Textarea + save/cancel for one section |
| `GapHint.tsx` | Contextual gap badge + "Write myself" / "Let Kaile help" actions |
| `AssistMicroSession.tsx` | Kaile-assisted flow: question → answer → suggestion → accept/edit/reject |
| `SaveScopePrompt.tsx` | "Save to Profile" vs "Just this CV" dialog with sensible defaults |

---

## New Backend Files

| File | Purpose |
|---|---|
| `backend/applire/services/cv/section_editor.py` | Override read/write, re-render logic |
| `backend/applire/services/cv/gap_mapper.py` | Keyword-based gap-to-section mapping |
| `backend/alembic/versions/XXXX_add_cv_section_editor_columns.py` | Migration |

---

## Architecture Documents Updated

- `Documents/Architecture/ADR.md` — ADR-019 added
- `Documents/Architecture/arc42.md` — Felix added to stakeholders (1.4); 5.3.4 updated; new 5.3.16 building block; ADR-019 added to index (§9)
- `Documents/Product Specifications/Personas/Finetuner.md` — new persona file

---

## What's Out of Scope (Sprint 9)

- Section reordering (drag-and-drop)
- AI-assisted tone/style rewriting (separate from gap completion)
- Education section editing (introduction + positions + skills are MVP)
- Approach 3 (CVDocument model) — parked in backlog as future migration path

---

## Open Questions for Implementation

1. Should `education` be editable in Sprint 9 or deferred to Sprint 10?
2. Should the Introduction section expose a "Rewrite with different tone" action, or is that a separate epic?
3. Default save scope when Kaile-assist is used: confirm "Save to Profile" is the right default.
