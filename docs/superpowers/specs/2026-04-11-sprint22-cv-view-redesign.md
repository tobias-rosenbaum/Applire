# Sprint 22 — CV View Redesign: Design Spec

**Date:** 2026-04-11
**Status:** Awaiting user review
**Sprint:** 22

---

## Overview

Redesign the CV view (`/flow/[flowId]/cv`) to eliminate dead space, fix the inaccessible editing panel, and introduce a modern 70/30 split layout based on Stitch reference designs. The CV document stays in an iframe (ADR-005 preserved). Editing moves into a persistent right-side RefinementPanel that never displaces the CV. The existing Kaile gap-question flow is replaced by a single-turn directed rewrite (KaileChat).

---

## Decisions made during brainstorming

| Topic | Decision |
|---|---|
| CV rendering | Keep iframe (ADR-005 — same HTML serves preview and Playwright PDF, CSS isolation required) |
| Layout | 70/30 split: CV iframe left, RefinementPanel right. Full viewport width, no max-width cap. |
| Dead space fix | CV column `flex-1`, panel `w-[28%] min-w-[220px] max-w-[360px]`, both `h-[calc(100vh-56px)]` |
| Editing UX | Panel stays visible alongside CV at all times — editor lives in the panel, never replaces the iframe |
| AI assist model | Replace 2-step Kaile question flow + no "blind regenerate" — single-turn directed rewrite (user gives directions, Kaile rewrites) |
| AI assist scope | Single-turn only for sprint 22. Multi-turn deferred. |
| Version history | Deferred — out of scope |
| Send to Recruiter | Deferred — out of scope |
| AI toolbar (Rewrite/Concise/Tone) | Replaced by KaileChat free-text directions. "Recreate section" is the single rewrite action. |
| Panel extensibility | Tab strip with named slots — new features (e.g. Appearance/color matching) added as new tabs without modifying existing ones |
| Mobile | Desktop-first for complex editing flows (ADR-023). Vertical stacking on narrow screens, no bespoke mobile accordion. |

---

## ADR-023 — Desktop-First for Complex Editing Flows

**Context:** The CV editing workflow (section editing, gap analysis, AI assist) requires significant screen real estate. The CV document is 794px wide (A4). No prior ADR addressed mobile vs desktop strategy.

**Decision:** Complex editing flows (CV view, interview, gap analysis) are **desktop-first**. On narrow screens these flows stack vertically and show a simplified read-only view; full editing requires a desktop-width viewport. Read/browse flows (dashboard, job list, history) remain fully responsive.

**Consequences:** Mobile editing is explicitly deferred until user research justifies the investment. Beta testers are expected to use desktop. This avoids building half-baked mobile UX for interactions that don't translate well to small screens.

---

## Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Navbar (56px, sticky)                                          │
├────────────────────────────────────┬────────────────────────────┤
│                                    │  Tab strip                 │
│  CV Document area                  │  [✦ Content] [↓ Actions]  │
│  flex-1, h-[calc(100vh-56px)]      │                            │
│  overflow-hidden                   │  RefinementPanel           │
│                                    │  w-[28%]                   │
│  ┌──────────────────────────────┐  │  min-w-[220px]             │
│  │ "Document Preview" header    │  │  max-w-[360px]             │
│  │ + last-saved timestamp       │  │  h-[calc(100vh-56px)]      │
│  ├──────────────────────────────┤  │  overflow-y-auto           │
│  │                              │  │                            │
│  │   <iframe srcDoc={html}>     │  │                            │
│  │   ResizeObserver + scale     │  │                            │
│  │   flex-1, fills all height   │  │                            │
│  │                              │  │                            │
│  └──────────────────────────────┘  │                            │
│                                    │                            │
└────────────────────────────────────┴────────────────────────────┘
```

Page wrapper: `w-full px-6 py-4` — no `max-w-*` constraint.

---

## Component Map

### New components

| Component | File | Responsibility |
|---|---|---|
| `CVDocument` | `frontend/components/cv/CVDocument.tsx` | Fetches HTML from `GET /api/cv/{id}/html`, renders iframe with ResizeObserver + scale logic. Exposes an imperative `refresh()` method via `useImperativeHandle` — called by the parent after a section save. |
| `RefinementPanel` | `frontend/components/cv/RefinementPanel.tsx` | Tab strip (Content, Actions). Owns `activeSection` state. Renders `ContentTab` or `ActionsTab` based on selected tab. |
| `ContentTab` | `frontend/components/cv/ContentTab.tsx` | Two sub-states: **Browse** (gap cards + section list) and **Edit** (SectionEditor + KaileChat). Handles Browse↔Edit transitions and unsaved-changes guard. |
| `ActionsTab` | `frontend/components/cv/ActionsTab.tsx` | Match score, template label, expiry warning, Download PDF, Regenerate same, Change template, Was nun? |
| `KaileChat` | `frontend/components/cv/KaileChat.tsx` | Free-text direction input + optional gap chips + "Rewrite section" submit. Shows suggestion with Apply / Edit first / Discard. Single-turn, stateless. |

### Kept unchanged

| Component | Reason |
|---|---|
| `SectionEditor` | Textarea, save/cancel, gap hints — well-tested internals, no layout changes needed |
| `GapHint` | Minor modification: remove internal `AssistMicroSession` state, replace with an `onAddressGap(gapId)` callback. The "Kaile hilft" button calls `onAddressGap`; `ContentTab` handles it by transitioning to Edit state for the owning section with that chip pre-selected. |
| `SaveScopePrompt` | Save-to-profile prompt — reused as-is |
| `GenerationProgress` | Not touched |
| `TemplateSelector` | Not touched |
| `PhotoPromptStep` | Not touched |
| `WhatNext` | Not touched |

### Retired

| Component | Replaced by |
|---|---|
| `CVPreview.tsx` | Layout absorbed into `cv/page.tsx` + `CVDocument` + `RefinementPanel` |
| `FineTunePanel.tsx` | `RefinementPanel` + `ContentTab` |
| `AssistMicroSession.tsx` | `KaileChat` |

---

## RefinementPanel — Content Tab States

### State 1: Browse

- Kaile section: avatar + intro text ("N gaps found for [role]") + gap cards
- Each gap card: gap label, gap title, "⚡ Address this gap" button
- Divider
- "Edit Sections" list: one row per section, label + gap count badge (or ✓)
- Clicking a gap card → transitions to Edit state for the section that owns that gap (known from `section.gaps[]` in the API response), with that gap's chip pre-selected in KaileChat
- Clicking a section row → transitions to Edit state, no pre-selected chip

### State 2: Edit

- "← Back to overview" button (triggers unsaved-changes guard if textarea dirty)
- Section label + title
- `SectionEditor` (textarea + Save/Cancel buttons)
- `KaileChat` below the editor

### State 3: After KaileChat rewrite

- Same as State 2, but KaileChat shows the suggestion result
- "Apply" → copies suggestion text into `SectionEditor` textarea (does not save — user must press Save)
- "Edit first" → copies suggestion into textarea and focuses it
- "Discard" → dismisses suggestion, returns to KaileChat input state
- CV iframe does NOT refresh until the user explicitly saves

---

## KaileChat Component

```
┌─────────────────────────────────────────┐
│ 🤖 Kaile                                │
│    Give directions to rewrite           │
│                                         │
│  Gaps (optional):                       │
│  [EU GMP Audit] [Post-Brexit]           │  ← chips, toggleable
│                                         │
│  ┌──────────────────────────────────┐   │
│  │ I also did chromatography...     │   │  ← free-text textarea
│  └──────────────────────────────────┘   │
│                                         │
│  [↺ Rewrite section]  [Cancel]          │
└─────────────────────────────────────────┘
```

**Behaviour:**
- Gap chips are shown only when the active section has gaps. Clicking a chip toggles it.
- Free-text input is always available regardless of chip selection.
- Both are optional — user can submit with chips only, text only, or both.
- On submit: calls `POST /api/cv/{id}/sections/{section_id}/rewrite`, shows loading state, then renders suggestion.
- Suggestion display replaces the input form (not a separate step — same component area).

---

## Actions Tab Content

- **Match score** (`ScoreCircle`) — reused from current left sidebar
- **Template label** — e.g. "Klassischer Lebenslauf"
- **Expiry notice** — warning/critical banner (reused)
- **Download PDF** — primary CTA (teal/primary bg)
- **Regenerate same template** — secondary outline button
- **Change template** → `onRegenerateDifferent`
- **Was nun? →** → `onNext`

---

## Backend Changes

### New endpoint

**`POST /api/cv/{cv_id}/sections/{section_id}/rewrite`**

Added to `cv_assist.py` as `rewrite_section()`.

Request body:
```json
{ "directions": "I also did chromatography analysis", "gap_ids": ["EU GMP Audit"] }
```

Response:
```json
{ "suggestion": "..." }
```

Logic:
1. Load section content + label (same `_load_cv_and_section` helper already used by assist)
2. Load job description via `FlowSession → job_id → JobPost`
3. Single LLM call: prompt includes section label, current content, JD excerpt, user directions, selected gap labels
4. Return suggestion text

No session state stored. ~40 lines added to `cv_assist.py`, ~15 lines in router.

### Modified endpoint

`POST /api/cv/{cv_id}/sections/{section_id}/assist` — **unchanged**. The existing 2-step question flow is retired on the frontend (`AssistMicroSession` removed) but the endpoint stays in place until confirmed unused.

---

## Frontend — page.tsx changes

The CV page phase state machine is unchanged (`photo_prompt → template_select → generating → preview → complete`). In the `preview` phase, the current `<CVPreview>` is replaced with:

```tsx
<div className="flex w-full h-[calc(100vh-56px)] gap-0">
  <div className="flex-1 flex flex-col min-w-0 px-6 py-4 gap-3 bg-neutral-light overflow-hidden">
    {/* header: "Document Preview" + last-saved */}
    <CVDocument
      cvId={cvId}
      ref={cvDocRef}
      className="flex-1"
    />
  </div>
  <RefinementPanel
    cvId={cvId}
    jobSummary={flowState?.job_summary ?? null}
    gapSummary={flowState?.gap_summary ?? null}
    cvSummary={flowState?.cv_summary ?? null}
    template={template}
    onHtmlRefresh={() => cvDocRef.current?.refresh()}
    onRegenerateDifferent={onRegenerateDifferent}
    onRegenerateSame={onRegenerateSame}
    onNext={onNext}
  />
</div>
```

The unsaved-changes leave guard (currently in `CVPreview`) moves into `ContentTab`. The `beforeunload` handler stays.

---

## Mobile behaviour (ADR-023)

On viewports narrower than `md` (768px):
- Layout stacks vertically: CV area on top, RefinementPanel below
- CV iframe: fixed height `h-[50vh]`, scale logic unchanged
- RefinementPanel: full width, `h-auto`, scrollable
- No bespoke accordion — the section list in ContentTab remains a flat list
- No editing gating (user can still edit on mobile, UX just isn't optimised)

---

## Testing

| Test | Type | Notes |
|---|---|---|
| `CVDocument` fetches HTML and renders iframe | Unit (Vitest) | Mock fetch; assert `srcDoc` set |
| `CVDocument` retries on error | Unit (Vitest) | |
| `ContentTab` Browse→Edit transition on section click | Unit (Vitest) | |
| `ContentTab` Browse→Edit with gap chip pre-selected | Unit (Vitest) | |
| `ContentTab` unsaved-changes guard on Back | Unit (Vitest) | |
| `KaileChat` submit calls rewrite endpoint | Unit (Vitest) | Mock fetch |
| `KaileChat` Apply copies suggestion to textarea | Unit (Vitest) | |
| `KaileChat` gap chips toggle | Unit (Vitest) | |
| `ActionsTab` Download button triggers PDF fetch | Unit (Vitest) | Existing test migrated from CVPreview |
| `RefinementPanel` tab switching Content↔Actions | Unit (Vitest) | |
| `POST /api/cv/{id}/sections/{section_id}/rewrite` returns suggestion | Unit (pytest) | Mock LLM provider |
| `rewrite_section` loads JD from FlowSession | Unit (pytest) | |
| `rewrite_section` returns 404 for unknown section_id | Unit (pytest) | |
| CV view renders and allows section edit end-to-end | E2E (Playwright) | Covers golden path: load → edit section → save → iframe refresh |

---

## Out of scope for sprint 22

- Version history / draft comparison
- Send to Recruiter
- AI toolbar (Make More Concise, Change Tone) — replaced by KaileChat free-text
- Multi-turn KaileChat conversation
- Appearance tab (color matching to company brand) — tab slot reserved, not implemented
- Mobile-optimised editing UX
- Navigation menu redesign — **decided**: left sidebar rail (icons + labels) to accommodate future services (Cover Letter, Interview Prep, etc.). Implementation deferred to a dedicated Navigation sprint. Sprint 22 keeps the current top navbar unchanged.
