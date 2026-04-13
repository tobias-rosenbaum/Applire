# Sprint 21 — Color Scheme Admin: Design Spec

**Date:** 2026-04-10  
**Status:** Approved for implementation  
**Sprint:** 21

---

## Overview

Add an admin appearance panel at `/admin/appearance` where the operator can create, preview, name, save, and activate color schemes. The active scheme is applied across the entire app via CSS custom properties injected client-side on load. A `ThemeProvider` wrapper handles scheme delivery to the frontend.

---

## Decisions made during brainstorming

| Topic | Decision |
|---|---|
| Admin access model | Operator-only URL, no role gating (Community = single-user, `NoAuthProvider`) |
| Preview approach | Embedded component mockup panel inside admin page (not whole-app live update) |
| Editing model | 3 seed color pickers + surface lightness slider + preset picker row |
| Preset picker | Ships in sprint 21 alongside the editor (same data, same save flow) |
| Storage | PostgreSQL (`color_schemes` table, new Alembic migration) |
| Runtime delivery | Client-side CSS custom property injection via `ThemeProvider` |
| Semantic colors | Traffic-light colors (success/warning/critical) are excluded from theming |
| Surface control | Lightness slider (88–99%), hue always follows Primary seed |
| Dark mode | Explicitly deferred — slider is constrained to light range |
| Named profiles | Deferred (ADR-022) — themes are instance-wide for sprint 21 |
| Derivation library | No external dependency — plain TypeScript (frontend) + `colorsys` stdlib (backend) |

---

## Data model

New table: `color_schemes`

```sql
CREATE TABLE color_schemes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(64) NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT false,
    is_builtin  BOOLEAN NOT NULL DEFAULT false,
    seed_primary    VARCHAR(7) NOT NULL,   -- hex e.g. #1B4F72
    seed_accent     VARCHAR(7) NOT NULL,   -- hex e.g. #2A8F9D
    seed_secondary  VARCHAR(7) NOT NULL,   -- hex e.g. #C9A84C
    surface_lightness FLOAT NOT NULL DEFAULT 0.97,  -- range 0.88–0.99
    derived     JSONB NOT NULL,            -- computed on save, cached
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Seed "EU Blue"** is inserted as the single builtin row (`is_builtin=true`, `is_active=true`) in the migration's `data_migration` step.

**Activation invariant:** exactly one row has `is_active=true` at all times. Enforced at the service layer (not DB constraint): activating a scheme sets all others to `false` in the same transaction.

**`derived` JSONB structure:**

```json
{
  "--color-primary": "#1B4F72",
  "--color-primary-container": "#D4E6F1",
  "--color-teal": "#2A8F9D",
  "--color-teal-dim": "#003a41",
  "--color-teal-container": "#e3effe",
  "--color-teal-container-light": "#f7f9ff",
  "--color-gold": "#C9A84C",
  "--color-gold-dim": "#755b00",
  "--color-gold-container": "#ffeec5",
  "--color-surface-dim": "#f7f9ff",
  "--color-surface-bright": "#ffffff",
  "--color-surface-container": "#f0f4f9",
  "--color-surface-container-high": "#e3effe",
  "--color-surface-container-highest": "#d9e4f4",
  "--color-neutral-light": "#F5F7FA"
}
```

`--color-neutral-dark` (`#2C3E50`) is fixed and not stored in `derived` — it is never themed.

---

## Color derivation

Implemented in two places with identical logic:

- **`frontend/lib/theme.ts`** — TypeScript, used for live preview (client-side, no server round-trip)
- **`backend/applire/services/color_schemes.py`** — Python using `colorsys` (stdlib), used on save and `/preview` endpoint

### Derivation table

| CSS variable | Source seed | Lightness | Saturation |
|---|---|---|---|
| `--color-primary` | seed_primary | as-is | as-is |
| `--color-primary-container` | primary hue | 90% | 30% |
| `--color-teal` | seed_accent | as-is | as-is |
| `--color-teal-dim` | accent hue | 12% | 100% |
| `--color-teal-container` | accent hue | 92% | 40% |
| `--color-teal-container-light` | accent hue | 97% | 15% |
| `--color-gold` | seed_secondary | as-is | as-is |
| `--color-gold-dim` | secondary hue | 20% | 100% |
| `--color-gold-container` | secondary hue | 92% | 60% |
| `--color-surface-dim` | primary hue | `L` | 8% |
| `--color-surface-bright` | — | 100% | 0% (always white) |
| `--color-surface-container` | primary hue | `L − 0.02` | 10% |
| `--color-surface-container-high` | primary hue | `L − 0.05` | 12% |
| `--color-surface-container-highest` | primary hue | `L − 0.08` | 14% |
| `--color-neutral-light` | primary hue | `L` | 5% |

`L` = `surface_lightness` as stored (float, 0.88–0.99). Arithmetic is in float units; multiply by 100 to get CSS `hsl()` percentage.

Multipliers are starting values, tunable by eye once the live editor is working.

---

## API

All endpoints under `/api/admin/color-schemes`. No auth gating (Community Edition).

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/admin/color-schemes/active` | Returns active scheme's `derived` JSONB — called by `ThemeProvider` on every app load |
| `GET` | `/api/admin/color-schemes` | Returns list of all saved schemes (for preset picker row) |
| `POST` | `/api/admin/color-schemes/preview` | Accepts seeds + `surface_lightness`, returns computed `derived` — debounced from editor, no persistence |
| `POST` | `/api/admin/color-schemes` | Save a named scheme — computes derived server-side, persists to DB |
| `PATCH` | `/api/admin/color-schemes/{id}/activate` | Sets scheme as active (clears all others in same transaction) |
| `DELETE` | `/api/admin/color-schemes/{id}` | Returns 409 if `is_builtin=true` or `is_active=true` |

### Live preview strategy

The editor computes derived values **client-side** (via `frontend/lib/theme.ts`) on every color change — no server round-trip during editing. The `/preview` endpoint is a secondary check called on debounced input (300ms) or on an explicit button, to confirm server and client agree. On save, the server is authoritative.

---

## Frontend

### New files

| File | Purpose |
|---|---|
| `frontend/lib/theme.ts` | `deriveScheme(seeds, surfaceLightness)` utility — pure function, no deps |
| `frontend/components/providers/ThemeProvider.tsx` | Fetches active scheme on mount, injects CSS custom properties on `document.documentElement` |
| `frontend/app/admin/appearance/page.tsx` | Admin appearance page |
| `frontend/components/admin/SchemeEditor.tsx` | Left panel: preset picker + seed pickers + slider + save |
| `frontend/components/admin/ThemePreview.tsx` | Right panel: component mockup that reads CSS variables live |

### Modified files

| File | Change |
|---|---|
| `frontend/components/providers/index.tsx` | Wrap with `ThemeProvider` |
| `frontend/app/settings/page.tsx` | Add "Admin" link in footer pointing to `/admin/appearance` |

### ThemeProvider behaviour

1. On mount: `GET /api/admin/color-schemes/active`
2. For each key in `derived`, call `document.documentElement.style.setProperty(key, value)`
3. While fetching: the CSS variables from `globals.css` remain active (no flash, graceful fallback)
4. The `globals.css` `@theme` block stays as the static fallback — `ThemeProvider` overrides it at runtime

### Admin page layout

- **Left panel (340px):** Saved Schemes row (preset swatches + "New" placeholder) → Seed Colors (3 pickers) → Surface Lightness slider (labelled "Tinted ← → Airy") → Save Scheme (name input + Save + Activate buttons)
- **Right panel (flex):** Live Preview — nav bar, application card, button variants, form input, skill badges, link — all reading CSS custom properties

### Save vs Activate

- **Save:** persists to DB, does not activate. Allows building a library of schemes before committing.
- **Activate:** sets `is_active=true`, immediately propagates to all app pages via `ThemeProvider` re-fetch.

### Preset picker interaction

- Clicking a saved scheme swatch loads its seeds and `surface_lightness` into the editor fields
- Live preview updates immediately (client-side derivation)
- Active scheme shown with a gold ring indicator
- "New" placeholder resets fields to neutral defaults (seed_primary: `#4A4A4A`, seed_accent: `#4A4A4A`, seed_secondary: `#4A4A4A`, surface_lightness: 0.97) — user edits from there

---

## Backend

### New files

| File | Purpose |
|---|---|
| `backend/applire/models/color_scheme.py` | SQLAlchemy `ColorScheme` model |
| `backend/applire/schemas/color_scheme.py` | Pydantic request/response schemas |
| `backend/applire/services/color_schemes.py` | Business logic + derivation function |
| `backend/applire/routers/admin/color_schemes.py` | FastAPI router (mounted at `/api/admin/color-schemes`) |
| `backend/alembic/versions/XXXX_add_color_schemes.py` | Migration + EU Blue seed data |

### Modified files

| File | Change |
|---|---|
| `backend/applire/main.py` | Register admin router |

---

## Testing

| Test | Type | Notes |
|---|---|---|
| `deriveScheme()` output shape and value ranges | Unit (Vitest) | Verify all 15 variables present; lightness/saturation within expected bounds |
| Save → activate → GET active returns correct derived values | Unit (pytest) | Service layer test with in-memory DB |
| DELETE builtin returns 409 | Unit (pytest) | |
| DELETE active scheme returns 409 | Unit (pytest) | |
| `ThemeProvider` injects CSS properties on mount | Unit (Vitest + jsdom) | Mock the API response |
| Admin page renders preset picker and editor | E2E (Playwright) | Basic smoke test; no color-accuracy assertion |

---

## Out of scope for sprint 21

- Dark mode (deferred — slider constrained to light range 88–99%)
- Per-user theme overrides (deferred — see ADR-022 Named Profiles)
- Scheme export/import between instances (noted as a future UX improvement)
- User-facing theme selector (planned for a future sprint once presets are established)
