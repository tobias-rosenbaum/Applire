# Sprint 33 — CV Color Profiles: Design Spec

**Date:** 2026-04-12
**Status:** Approved for implementation
**Sprint:** 33
**Epic:** E023 — CV Color Profiles (US091–US096)

---

## Overview

Add per-document accent color profiles to generated CVs. The system automatically detects the target company's brand color from their website at CV generation time and applies it to the document. Users can override the color from a new "🎨 Design" tab in the RefinementPanel. A personal default color can be set in Settings as a fallback.

CV color profiles are a **separate system** from the app-wide `color_schemes` introduced in Sprint 21 (ADR-023). CV colors are per-document artifacts; app colors are instance-wide UI settings.

---

## Decisions Made During Brainstorming

| Topic | Decision |
|---|---|
| Color timing | Auto-detected at generation + user override after (no re-run of LLM required) |
| Detection method | Cascade: cache → favicon+colorgram → meta-tag scraping → LLM fallback |
| Detection trigger | During CV generation (`_render_cv_background` background task) |
| Brandfetch/Clearbit | Deferred to Cloud Edition (ADR-025) |
| CV color variables | One accent color → derives `--cv-accent` + `--cv-accent-tint` (no 3-seed system) |
| Classic German template | Accent applied subtly to section underline rule |
| Template extensibility | Jinja2 `color` context object — all templates read same interface |
| UI location | New "🎨 Design" tab in RefinementPanel (third tab) |
| UI pattern | Swatch bar with detected company color card + preset swatches + custom hex |
| Data model | `color_profiles` table + `companies` registry + `user_settings` table |
| User default storage | New `user_settings` table (extensible for future preferences) |
| App theme separation | `color_schemes` (Sprint 21) and `color_profiles` (Sprint 33) are independent |

---

## Data Model

### New Tables

**`color_profiles`** — reusable palette, shared across all usages:

```sql
CREATE TABLE color_profiles (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seed_primary VARCHAR(7) NOT NULL,   -- hex e.g. #009FE3
    derived      JSONB NOT NULL,        -- { "--cv-accent": "#009FE3", "--cv-accent-tint": "#e8f7fd" }
    source       VARCHAR(20) NOT NULL,  -- 'favicon' | 'meta_tag' | 'llm' | 'user' | 'default'
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

`derived` always contains exactly two keys: `--cv-accent` (the resolved hex) and `--cv-accent-tint` (hue-preserved, lightness ~95%, saturation ~10% — used for skill badge backgrounds).

**`companies`** — domain registry and scrape cache:

```sql
CREATE TABLE companies (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             TEXT NOT NULL,
    domain           TEXT NOT NULL UNIQUE,
    color_profile_id UUID REFERENCES color_profiles(id),
    scraped_at       TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**`user_settings`** — user preferences (extensible for future settings):

```sql
CREATE TABLE user_settings (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                  UUID NOT NULL REFERENCES users(id),
    default_color_profile_id UUID REFERENCES color_profiles(id),
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Modified Tables

- `generated_cvs` + `color_profile_id UUID REFERENCES color_profiles(id)` (nullable)
- `job_analyses` + `company_id UUID REFERENCES companies(id)` (nullable)

### Resolution Cascade at Render Time

1. `generated_cvs.color_profile_id` — CV-specific override (set by user or initial detection)
2. `job_analyses → companies → color_profile_id` — auto-detected company brand color
3. `user_settings.default_color_profile_id` — user's configured fallback
4. System default — `#2b5fa8` (current hardcoded template value; pre-Sprint-33 CVs unchanged)

The `color` Jinja2 context object is always populated (never null); templates require no null checks.

---

## Color Detection Cascade

Runs as a step in `_render_cv_background`, after loading job + profile data and before rendering.

| Step | Mechanism | Trigger condition |
|---|---|---|
| 1 | Cache hit — `companies` by domain | `scraped_at` within 30 days |
| 2 | Favicon extraction — Google CDN + `colorgram.py` | Domain derivable from `source_url` |
| 3 | Meta-tag scraping — `theme-color`, CSS `:root` vars | Favicon yields only grayscale |
| 4 | LLM fallback — ~50 tokens, structured JSON prompt | `company_name` known, scraping failed |
| 5 | User default — `user_settings.default_color_profile_id` | Steps 1–4 all failed or no domain |
| 6 | System default — `#2b5fa8` | No user default set |

Domain is derived from `job_analyses.source_url` via `urllib.parse`. If `source_url` is null, steps 2–3 are skipped. `color_profiles.source` records which step succeeded.

On success (steps 2–4): upsert `companies` by domain, set `color_profile_id` and `scraped_at`. `job_analyses.company_id` is set to the resolved company record. `generated_cvs.color_profile_id` is set to the resolved profile.

---

## Tint Derivation

`--cv-accent-tint` is derived from `--cv-accent`:
- Convert hex → HSL
- Set lightness to 95%, saturation to 10% (hue preserved)
- Convert back to hex

Pure Python function using `colorsys` (stdlib). No external dependency for derivation. `colorgram` is the only new Python dependency (for favicon pixel extraction).

---

## Backend

### New Files

| File | Purpose |
|---|---|
| `backend/applire/models/color_profile.py` | `ColorProfile` SQLAlchemy model |
| `backend/applire/models/company.py` | `Company` SQLAlchemy model |
| `backend/applire/models/user_settings.py` | `UserSettings` SQLAlchemy model |
| `backend/applire/services/color_detection.py` | Detection cascade + `derive_tint()` + `resolve_color_profile()` |
| `backend/applire/routers/cv_color.py` | `PATCH /api/cv/{id}/color` |
| `backend/applire/routers/settings.py` | `GET/PATCH /api/settings` (user default color) |
| `backend/alembic/versions/XXXX_add_color_profiles.py` | Migration for all new tables + FK columns |

### Modified Files

| File | Change |
|---|---|
| `backend/applire/models/cv.py` | Add `color_profile_id` FK |
| `backend/applire/models/job.py` | Add `company_id` FK |
| `backend/applire/services/cv.py` | Call `resolve_color_profile()` in `_render_cv_background`; pass `color` to Jinja2 context |
| `backend/applire/templates/modern_swiss.html.j2` | `:root { --cv-accent: {{ color.accent }}; --cv-accent-tint: {{ color.tint }}; }` replacing hardcoded values |
| `backend/applire/templates/lebenslauf.html.j2` | Same injection; `--cv-accent` drives section rule (dark tint applied in CSS) |
| `backend/applire/main.py` | Register `cv_color` and `settings` routers |
| `backend/requirements.txt` | Add `colorgram.py` |

### API

| Method | Path | Purpose |
|---|---|---|
| `PATCH` | `/api/cv/{cv_id}/color` | Apply accent override. Body: `{ "accent_hex": "#RRGGBB" }`. Returns `{ color_profile_id, derived }`. |
| `GET` | `/api/settings` | Returns user settings incl. `default_color_profile_id` and `default_accent_hex`. |
| `PATCH` | `/api/settings` | Update user settings. Body: `{ "default_accent_hex": "#RRGGBB" }`. |

`PATCH /api/cv/{cv_id}/color`:
- Validates hex (6-digit, with `#`)
- Creates or reuses a `color_profiles` row for the given hex + `source='user'`
- Sets `generated_cvs.color_profile_id`
- Triggers Jinja2 re-render (no Playwright)
- Returns 200 with derived values; 404 if CV not found or not ready; 422 if hex invalid

---

## Frontend

### New Files

| File | Purpose |
|---|---|
| `frontend/components/cv/DesignTab.tsx` | Company color card, preset swatch row, hex input, apply button |

### Modified Files

| File | Change |
|---|---|
| `frontend/components/cv/RefinementPanel.tsx` | Add `"appearance"` to `Tab` type; add "🎨 Design" tab; render `<DesignTab>` |
| `frontend/app/settings/page.tsx` | Add "Standard-Farbe" section with color picker → `PATCH /api/settings` |

### `DesignTab` Props

```ts
interface DesignTabProps {
  cvId: string;
  detectedCompany: { name: string; hex: string } | null;
  currentAccentHex: string;
  savedProfiles: Array<{ id: string; hex: string }>;
  onColorApplied: () => void;  // triggers onHtmlRefresh in parent
}
```

### Apply Flow

1. User clicks swatch or enters hex → local preview state updates (no server call)
2. User clicks "Farbe übernehmen" → `PATCH /api/cv/{id}/color`
3. Server creates/reuses `color_profiles` row, updates `generated_cvs.color_profile_id`, re-renders HTML (Jinja2 only)
4. `onColorApplied()` → parent calls `onHtmlRefresh()` → iframe srcDoc updates

### Design Tab UI Details

- **Company color card** (shown when detected): company name, hex, "automatisch erkannt" badge. Company swatch marked with ✦ in the preset row.
- **Preset swatch row**: up to 6 saved color profiles + custom "+" swatch. Active swatch has border indicator.
- **Custom swatch (+)**: opens native `<input type="color">` picker.
- **Hex input**: editable; syncs with swatch selection.
- **Apply button**: disabled until selection differs from current CV color.

---

## Template Color Integration Pattern

Both existing templates and all future templates follow the same pattern:

```html
<style>
  :root {
    --cv-accent: {{ color.accent }};
    --cv-accent-tint: {{ color.tint }};
    /* all other variables remain hardcoded structural values */
  }
</style>
```

**Modern Swiss** uses `--cv-accent` for:
- `.header` left border strip
- `.section-title-en` text color
- `.skills-grid li` background → `--cv-accent-tint`

**Classic German Lebenslauf** uses `--cv-accent` for:
- `.section-title` bottom border (applied as a dark tinted version to maintain conservative aesthetic)

Template authors adding future templates: receive `color.accent` (full hex) and `color.tint` (light badge background) in context. No other color plumbing needed.

---

## Testing

| Test | Type | Notes |
|---|---|---|
| `resolve_color_profile()` — all 6 cascade steps | Unit (pytest) | Mock HTTP; assert correct fallback at each step |
| `derive_tint()` — output lighter and less saturated than input | Unit (pytest) | Pure function; verify HSL bounds |
| Favicon extraction returns most saturated non-neutral color | Unit (pytest) | Feed test PNG fixture |
| Company domain upsert — second call is cache hit, no HTTP | Unit (pytest) | Assert `scraped_at` unchanged; `httpx` not called |
| `PATCH /api/cv/{id}/color` creates profile, updates CV FK, re-renders | Unit (pytest) | SQLite in-memory |
| CV HTML contains `--cv-accent` value from resolved profile | Unit (pytest) | Render with known color; assert hex in output |
| `DesignTab` renders detected company color card | Unit (Vitest) | Mock API with company data |
| `DesignTab` renders fallback state when no company detected | Unit (Vitest) | Mock API with null detectedCompany |
| Swatch click → hex input updates → apply → iframe re-renders | E2E (Playwright) | Smoke test against running stack |

---

## Out of Scope for Sprint 33

- Brandfetch / Clearbit API integration (Cloud Edition — ADR-025)
- Bulk re-detection of existing CVs (future tooling sprint)
- Dark mode or multi-color CV themes (one accent color is sufficient)
- Named profile color overrides (ADR-022 scope)
- Template switcher in the Design tab (placeholder reserved; implementation deferred)

---

## Architecture References

- ADR-023: CV Color Profiles — Separate System from App Color Schemes
- ADR-024: Companies Registry as First-Class Domain Entity
- ADR-025: Color Detection Cascade — Favicon-First, LLM as Last Resort
- arc42 v2.13: Building blocks 5.3.17 (Color Detection Service) and 5.3.18 (CV Color Profile System)
- Sprint 21 spec: `docs/superpowers/specs/2026-04-10-sprint21-color-schemes-design.md` (app theme — separate system)
