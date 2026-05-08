---
title: Sprint 27 — Responsive Document Views (Cover Letter & CV)
date: 2026-04-16
status: approved
---

# Sprint 27 — Responsive Document Views

## Overview

Two targeted improvements to the Cover Letter and CV preview views that address usability on 14" laptops and smaller screens:

1. **Cover Letter preview scaling fix** — The `CoverLetterDocument` iframe clips A4 content on narrow viewports because it lacks the CSS scaling logic present in `CVDocument`. Fix mirrors the existing `CVDocument` pattern exactly.
2. **Collapsible side panel** — The right-side refinement panel (Inhalt / Design / Aktionen tabs) can be collapsed to a 48px icon rail, giving the document preview more horizontal space. Applies to both the Cover Letter and CV views.

---

## Part 1 — CoverLetterDocument Scaling Fix

### Problem

`CVDocument` measures its container via `ResizeObserver` and applies `transform: scale(containerWidth / 794)` so that A4 content (794px at 96 dpi) is always scaled to fit. `CoverLetterDocument` renders an `<iframe srcDoc={...}>` at full A4 width with no scaling. On a 14" laptop (≈1280px viewport, 50% = 640px container) the right half of the letter is clipped.

### Fix

`CoverLetterDocument.tsx` is refactored to mirror `CVDocument`:

- Add a `containerRef` wrapping `<div>` and a `ResizeObserver` that tracks `containerWidth` and `containerHeight`.
- Compute `scale = containerWidth > 0 ? Math.min(1, containerWidth / CV_WIDTH) : 1` where `CV_WIDTH = 794`.
- Render the iframe at fixed `width={CV_WIDTH}px` and `height={CV_WIDTH * Math.sqrt(2)}px` (A4 aspect ratio), then apply `transform: scale(scale)` with `transformOrigin: "top left"` so the outer div sees the scaled dimensions.
- The outer div sets `height = iframeHeight * scale` to prevent layout collapse.

No API changes. No changes to the backend cover letter HTML endpoint. One file touched: `frontend/components/cover-letter/CoverLetterDocument.tsx`.

---

## Part 2 — Collapsible Side Panel

### Scope

Both views receive the collapsible panel treatment:

| View | Panel component |
|---|---|
| `/flow/[flowId]/cover-letter` | `CoverLetterRefinementPanel` |
| `/flow/[flowId]/cv` (preview phase) | `RefinementPanel` |

### Behavior

**Default state:** Panel is expanded on every page load. No `localStorage` persistence.

**Expanded state:**
- Panel renders at fixed width `w-[380px]` (was `w-1/2 min-w-[340px]`).
- A `❯` chevron button sits in the top-right corner of the panel header.
- Clicking it collapses the panel.

**Collapsed state:**
- Panel shrinks to `w-12` (48px) icon rail.
- Icon rail shows three vertically-stacked icon buttons:
  - ✏️ Inhalt
  - 🎨 Design  
  - ⚡ Aktionen
- A `❮` chevron button sits at the top of the rail.
- Clicking the chevron expands the panel (restoring the previously active tab).
- Clicking a tab icon expands the panel **and** activates that tab.

**Preview pane:**
- Changes from fixed `w-1/2` to `flex-1 min-w-0` so it fills the remaining space automatically in both states.

**Animation:**
- `transition-[width] duration-200 ease-in-out` on the panel div.

### Component changes

#### `CoverLetterRefinementPanel.tsx`

New props:
```ts
collapsed: boolean
onToggleCollapse: () => void
```

When `collapsed === true`: render the 48px icon rail instead of the tab panel.  
When `collapsed === false`: render existing tab UI with the `❯` collapse button added to the tab bar row.

#### `cover-letter/page.tsx`

- Add `const [panelOpen, setPanelOpen] = useState(true)`.
- Pass `collapsed={!panelOpen}` and `onToggleCollapse={() => setPanelOpen(o => !o)}` to `CoverLetterRefinementPanel`.
- Change left preview div from `w-1/2 min-w-0` to `flex-1 min-w-0`.
- Change right panel wrapper from `w-1/2 min-w-[340px]` to `flex-shrink-0` (width managed by panel itself).

#### `RefinementPanel.tsx` (CV)

Same new props: `collapsed: boolean`, `onToggleCollapse: () => void`.  
Same icon rail when collapsed. Same chevron in tab bar when expanded.

#### `cv/page.tsx`

- Add `const [panelOpen, setPanelOpen] = useState(true)`.
- Pass collapse props to `RefinementPanel`.
- Change left preview div from `w-1/2` to `flex-1 min-w-0`.

### Icon rail detail

```
┌────┐
│ ❮  │  ← expand chevron (top)
├────┤
│ ✏️  │  ← Inhalt tab
│ 🎨  │  ← Design tab
│ ⚡  │  ← Aktionen tab
└────┘
```

Each icon button has a tooltip (`title` attribute) for accessibility. The active tab icon receives a subtle highlight (same `bg-blue-50 text-blue-600` as the active tab state).

---

## Files Touched

| File | Change |
|---|---|
| `frontend/components/cover-letter/CoverLetterDocument.tsx` | Add ResizeObserver + CSS scale (mirrors CVDocument) |
| `frontend/components/cover-letter/CoverLetterRefinementPanel.tsx` | Add `collapsed` / `onToggleCollapse` props; icon rail |
| `frontend/app/flow/[flowId]/cover-letter/page.tsx` | `panelOpen` state; flex-1 preview div |
| `frontend/components/cv/RefinementPanel.tsx` | Add `collapsed` / `onToggleCollapse` props; icon rail |
| `frontend/app/flow/[flowId]/cv/page.tsx` | `panelOpen` state; flex-1 preview div |

No backend changes. No new API endpoints. No database migrations.

---

## Testing

| Tier | What |
|---|---|
| Visual / manual | Cover letter preview fits fully on 14" laptop (1280px); A4 letter scales correctly |
| Visual / manual | Panel collapses and expands in CL and CV views; icon rail works; tab icon activates correct tab |
| Vitest unit | `CoverLetterDocument` scale computation: `scale = Math.min(1, containerWidth / 794)` |
| E2E (Playwright) | Collapse toggle present and functional on CL page; preview iframe width increases when collapsed |

Coverage gate: ≥75% backend unit coverage unaffected (no backend changes).

---

## Out of Scope

- Mobile breakpoint layout switch (< 768px) — deferred to a future Navigation sprint
- `localStorage` persistence of panel state — explicitly not included
- Changes to any other page or component
