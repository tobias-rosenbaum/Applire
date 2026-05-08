# Progress Indicator Unification + Cover Letter Bug Fix

**Date:** 2026-04-27  
**Sprint:** 31  
**Status:** Approved

---

## Problem

Three different progress experiences exist today:

| Flow | Current UI | Quality |
|---|---|---|
| CV + JD upload | Full-screen overlay, animated spinning SVG per step + linear bar | Best |
| CV generation | Inline static circles, spinner on current step, no bar | Inconsistent |
| Cover letter generation | Static text "Anschreiben wird erstellt…" only | Broken + no UX |

Additionally, the cover letter content tab never receives data — `letterData` is always `null` because the backend status endpoint does not return `letter_data` and the frontend never fetches it.

---

## Goals

1. Unified, polished progress widget used across all three flows.
2. Upload overlay: dynamic CV steps (one step per uploaded file).
3. Cover letter: add progress widget + fix the `letterData` null bug.
4. All new UI strings available in German and English via `next-intl`.

---

## Design Decisions

- **Placement:** Overlay for upload (existing pattern); **inline** for CV generation and cover letter.
- **Ring style:** Step-derived percentage — `Math.round(doneCount / total * 100)` — ring arc jumps per step. Not indeterminate.
- **Dynamic upload steps:** `[JD analysis] + [CV upload × N] + [Profile creation] + [Gap detection]` where N = number of uploaded files.

---

## Architecture

### 1. Shared component: `ProgressWidget`

**File:** `frontend/components/ui/progress-widget.tsx`

Fully controlled (no internal state). Props:

```ts
type ProgressStep = {
  label: string
  status: 'done' | 'active' | 'pending'
}

type ProgressWidgetProps = {
  steps: ProgressStep[]
  title: string
  subtitle?: string
  className?: string
}
```

Renders:
- SVG ring showing `Math.round(doneCount / steps.length * 100)%` in the center.
- Title + optional subtitle below the ring.
- Step list: each step has a status icon (done = filled primary circle with ✓, active = gold-bordered circle with pulsing dot + gold shimmer row, pending = gray bordered circle, dimmed).
- Uses Tailwind theme tokens (`text-primary`, `bg-surface-container`, `border-primary`, etc.) — no hardcoded hex.

The widget is purely presentational. Callers own the step array and drive status changes.

---

### 2. Upload overlay (`ProcessingOverlay`)

**File:** `frontend/components/processing-overlay.tsx`

**Change:** Keep modal overlay shell. Replace internal step icons + linear bar with `<ProgressWidget>`.

**Dynamic steps** — built before `runPipeline()` starts, using the list of uploaded CV files:

```
steps = [
  { label: t('stepJd'),      status: 'pending' },   // fixed
  ...cvFiles.map((f, i) => ({
    label: t('stepCv', { n: i + 1, total: cvFiles.length }),
    status: 'pending',
  })),
  { label: t('stepProfile'), status: 'pending' },   // fixed
  { label: t('stepGaps'),    status: 'pending' },   // fixed
]
```

As each pipeline call resolves, flip the corresponding step to `done` and the next to `active`. Ring % = `doneCount / steps.length * 100`.

When `cvFiles.length === 1` the label is the singular form (no numbering).

---

### 3. CV generation (`GenerationProgress`)

**File:** `frontend/components/cv/GenerationProgress.tsx`

**Change:** Replace current static-circles markup with `<ProgressWidget>` inline. Keep existing polling logic unchanged.

Status → step mapping:

| Backend `status` | Steps done | Ring % |
|---|---|---|
| `queued` | 0 | 0% |
| `rendering` | 1 | 33% |
| `ready` | 2 | 67% |
| Transition out | 3 | 100% |

Fixed three steps: queued, rendering, done.

---

### 4. Cover letter — progress + `letterData` bug fix

#### 4a. Backend

**File:** `backend/applire/schemas/cover_letter.py`

Add optional field to `CoverLetterStatusResponse`:

```python
letter_data: Optional[dict] = None
```

**File:** `backend/applire/services/cover_letter.py`

In `get_cover_letter_status()`: when `cover_letter.status == CoverLetterStatus.ready`, populate `letter_data` from `cover_letter.letter_data`.

#### 4b. Frontend — progress widget

**File:** `frontend/app/(shell)/flow/[flowId]/cover-letter/page.tsx`

Replace the `phase === "generating"` branch (currently just a text div) with `<ProgressWidget>` inline.

Three fixed steps mapped from polled status:

| Backend `status` | Steps done | Ring % |
|---|---|---|
| `pending` | 0 | 0% |
| `generating` | 1 | 33% |
| `ready` | 2 | 67% |
| Transition out | 3 | 100% |

#### 4c. Frontend — `letterData` fix

When the polling loop detects `status === 'ready'`:

```ts
setClState(prev => ({
  ...prev!,
  status: 'ready',
  letterData: data.letter_data ?? null,
}))
```

`data.letter_data` is now present in the response. `CoverLetterContentTab` receives real data and can render editable sections.

---

### 5. i18n

Both `messages/de.json` and `messages/en.json` updated. New/changed keys:

**`processing` namespace:**

| Key | DE | EN |
|---|---|---|
| `stepJd` | `Stellenbeschreibung wird analysiert` | `Analysing job description` |
| `stepCv` | `Lebenslauf wird hochgeladen` (singular) | `Uploading CV` |
| `stepCvN` | `Lebenslauf {n} von {total} wird hochgeladen` | `Uploading CV {n} of {total}` |
| `stepProfile` | `Profil wird erstellt` | `Building profile` |
| `stepGaps` | `Lücken werden erkannt` | `Detecting gaps` |
| `title` | `Wir analysieren Ihre Unterlagen` | `Analysing your documents` |
| `subtitle` | `Das dauert meist unter einer Minute` | `This usually takes under a minute` |

**`cv` namespace:**

| Key | DE | EN |
|---|---|---|
| `progressTitle` | `Lebenslauf wird erstellt` | `Creating your CV` |
| `progressSubtitle` | `KI rendert Ihren Lebenslauf` | `AI is rendering your CV` |
| `stepQueued` | `In der Warteschlange` | `Queued` |
| `stepRendering` | `Lebenslauf wird gerendert` | `Rendering CV` |
| `stepDone` | `Fertig` | `Done` |

**`coverLetter` namespace:**

| Key | DE | EN |
|---|---|---|
| `progressTitle` | `Anschreiben wird erstellt` | `Creating cover letter` |
| `progressSubtitle` | `KI formuliert Ihr Anschreiben` | `AI is writing your cover letter` |
| `stepPreparing` | `Daten werden aufbereitet` | `Preparing data` |
| `stepGenerating` | `Anschreiben wird generiert` | `Generating cover letter` |
| `stepReady` | `Fertig` | `Done` |

---

## Files Changed

| File | Change |
|---|---|
| `frontend/components/ui/progress-widget.tsx` | **New** — shared widget |
| `frontend/components/processing-overlay.tsx` | Refactor internals; dynamic CV steps |
| `frontend/components/cv/GenerationProgress.tsx` | Replace circles with `ProgressWidget` |
| `frontend/app/(shell)/flow/[flowId]/cover-letter/page.tsx` | Add progress widget; fix letterData |
| `backend/applire/schemas/cover_letter.py` | Add `letter_data` to status response |
| `backend/applire/services/cover_letter.py` | Populate `letter_data` when ready |
| `frontend/messages/de.json` | New/updated keys |
| `frontend/messages/en.json` | New/updated keys |

---

## Out of Scope

- PDF rendering progress (no backend signal available).
- Animated percentage counter (number ticks up smoothly) — the jump-per-step approach is sufficient.
- Any changes to the CV editor or cover letter editor UI beyond the progress/data fix.
