# Design: CV Templates Expansion + Multi-Color Schema (Sprint 24)

**Date:** 2026-04-13  
**Status:** Implemented (Sprint 24)  
**Branch:** sprint-24

---

## Problem

Applire currently has two CV templates (`classic_german`, `modern_swiss`) and a single-color system (`color.accent` + auto-derived `color.tint`). The goal is to expand to seven templates and introduce a multi-slot color schema so users and company brand profiles can control multiple visual dimensions of a CV.

---

## Color Schema

### Slots

| Slot | Type | Phase | Description |
|---|---|---|---|
| `color.primary` | user/detected | 1 | Main brand color — section headings, icons, lines, tag text. Replaces `color.accent` semantically. |
| `color.primary_tint` | auto | 1 | Light hue of primary (L=95%, S=10%) — tag backgrounds, hover states. Replaces `color.tint`. |
| `color.surface` | user/detected | 2 | Sidebar or header background. Defaults to `primary` in Phase 1. |
| `color.surface_text` | auto | 1 | White or black, WCAG-computed from `surface` luminance. Never set manually. |
| `color.secondary` | user/detected | 2 | Second accent — dates, highlight tags, decorative elements. Defaults to `primary` in Phase 1. |

### Auto-Contrast Formula (`surface_text`)

```
luminance = 0.2126·R_lin + 0.7152·G_lin + 0.0722·B_lin
(R_lin = (R/255)^2.2 approximation)

surface_text = "#ffffff" if luminance < 0.179 else "#1a1a1a"
```

The 0.179 threshold is the geometric mean of the WCAG 4.5:1 contrast ratio against both pure black and pure white.

### Backward Compatibility

Existing templates use `{{ color.accent }}` and `{{ color.tint }}`. These remain on `ColorContext` as aliases pointing to `primary` and `primary_tint` respectively. No template migration needed.

### ColorContext (extended dataclass)

```python
@dataclass
class ColorContext:
    primary: str        # hex — main brand color
    primary_tint: str   # hex — light version of primary
    surface: str        # hex — sidebar/header bg (= primary in Phase 1)
    surface_text: str   # "#ffffff" or "#1a1a1a" — auto-computed
    secondary: str      # hex — second accent (= primary in Phase 1)
    # backward-compat aliases
    accent: str         # = primary
    tint: str           # = primary_tint
```

**No DB migration required for Phase 1.** `seed_primary` remains the single stored value; all new slots are computed at render time from it. Phase 2 adds `seed_secondary` and `seed_surface` columns.

---

## Five New Templates

### 1. `executive` — Executive / Premium
- **Audience:** C-Level, Führungskräfte, Senior-Profile
- **Style:** Dark navy header (`surface`), two-column body, serif (Georgia), gold/cream accent strip
- **Color usage:** `surface` → header bg, `surface_text` → header name/title, `primary` → section lines and entry titles

### 2. `tech_developer` — Tech / Developer
- **Audience:** Software Engineers, DevOps, ML Engineers
- **Style:** Dark background (`#0d1117`), monospace font, code-aesthetic, skill tags
- **Color usage:** `primary` → name, links, skill tag text; `primary_tint` used as tag border; `surface` → optional left accent strip

### 3. `creative_sidebar` — Creative / Sidebar
- **Audience:** UX/UI Design, Marketing, Creative roles
- **Style:** Two-column with colored left sidebar, circular avatar, sans-serif
- **Color usage:** `surface` → sidebar bg, `surface_text` → all sidebar text (auto-contrast), `primary` → main column headings and tags

### 4. `academic` — Academic / Scientific
- **Audience:** Research, Academia, Medicine, Law
- **Style:** Conservative, centered header, dense serif body, publication list section
- **Color usage:** `primary` → minimal — only rule lines; typography-dominant design

### 5. `compact_pro` — Compact Pro
- **Audience:** Experienced professionals with long careers (10+ years)
- **Style:** Dense two-column grid, no photo, maximum information density, sans-serif
- **Color usage:** `primary` → column headers and dividers; `primary_tint` → row zebra (optional)

---

## Template Registration

Each new template requires:
1. `backend/applire/templates/<key>.html.j2` — Jinja2 HTML template
2. Entry in `_TEMPLATE_FILES` dict in `backend/applire/services/cv.py`
3. Literal added to `CVTemplate` in `backend/applire/schemas/cv.py`
4. Thumbnail PNG at `backend/data/static/templates/<key>.png` (for template picker UI)

---

## Implementation Notes

- All templates are **A4, print-optimised** (Playwright PDF rendering, `format="A4"`)
- Templates receive `cv` (TailoredCVData) and `color` (ColorContext) — no other context variables
- `tech_developer` uses a **dark background** — Playwright's `print_background=True` already set, no change needed
- Photo (`show_photo` flag) is supported in `executive` and `creative_sidebar`; not shown in `academic`, `tech_developer`, `compact_pro`
- Section headers are bilingual (DE/EN) where relevant, consistent with `modern_swiss` pattern
- Thumbnails are 400×566 px PNG (A4 ratio ~1:√2), generated via Playwright screenshot of the template with sample data

---

## Out of Scope (Phase 2)

- UI color picker for `secondary` and `surface` slots
- Company multi-color detection (logo color sets)
- Per-section color overrides
- Template builder / admin UI

---

## Testing

| Layer | What |
|---|---|
| Unit | `derive_surface_text()` luminance math (pytest, parametrized with edge cases) |
| Unit | `ColorContext` field computation from a single seed hex |
| Unit | All 7 templates render without Jinja2 errors given minimal `TailoredCVData` fixture |
| E2E | Template picker: generate CV with each new template, verify PDF downloads |
| Manual QA | Visual review of each template at A4 in browser and PDF |
