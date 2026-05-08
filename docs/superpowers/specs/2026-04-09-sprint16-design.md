# Sprint 16 Design — CV Template Enhancements

**Date:** 2026-04-09  
**Author:** Tobias Rosenbaum  
**Status:** Approved

---

## Overview

Two enhancements to the CV rendering pipeline:

1. **Page break avoidance** — prevent entries and section headers from splitting across PDF pages; user-toggleable.
2. **Icon sets** — inline SVG icons for contact fields and section headers; extensible registry; user-selectable per CV; per-template defaults.

---

## Feature 1: Page Break Avoidance

### What it does

Adds CSS rules that prevent Chromium (Playwright) from splitting a work/education entry or orphaning a section header across a page boundary. Controlled by a boolean flag on the CV record so users can turn it off if they prefer compact spacing over clean breaks.

### Implementation

**Templates (`lebenslauf.html.j2`, `modern_swiss.html.j2`)**

A `.no-breaks` class is conditionally applied to `<body>` based on the `avoid_page_breaks` template variable:

```html
<body class="{{ 'no-breaks' if avoid_page_breaks else '' }}">
```

CSS added to both templates:

```css
.no-breaks .entry {
  break-inside: avoid;
  page-break-inside: avoid;
}
.no-breaks .section-title,
.no-breaks .section-header {
  break-after: avoid;
  page-break-after: avoid;
}
.no-breaks p,
.no-breaks li {
  widows: 2;
  orphans: 2;
}
```

**Behaviour:** If an entry is too tall for the remaining page space, Chromium pushes the whole entry to the next page, leaving whitespace at the bottom of the previous page. This is the correct trade-off.

**Schema (`schemas/cv.py`)**

```python
class CVGenerateRequest(BaseModel):
    job_id: uuid.UUID
    template: CVTemplate = "classic_german"
    icon_set: CVIconSet | None = None
    avoid_page_breaks: bool = True  # default on
```

**Model (`models/cv.py`)**

New column: `avoid_page_breaks: bool`, server default `True`.

**Service (`services/cv.py`)**

- `generate_cv` stores `avoid_page_breaks` on the `GeneratedCV` record.
- `get_cv_html` passes `avoid_page_breaks=record.avoid_page_breaks` to the Jinja2 template context.

**Migration**

One Alembic migration adds both `icon_set` (VARCHAR 32, nullable, default `NULL`) and `avoid_page_breaks` (BOOLEAN, not null, server default `TRUE`) to `generated_cvs`.

---

## Feature 2: Icon Sets

### What it does

Adds optional inline SVG icons to CV templates for contact fields (phone, email, location, LinkedIn) and section headers (profile, experience, education, skills, languages). Users choose an icon set at generation time; the choice defaults per template and is stored on the CV record for consistent re-rendering.

### Icon set registry (`applire/icon_sets.py`)

Single Python module. Adding a new icon set = one new dict entry.

```python
ICON_KEYS = ("phone", "email", "location", "linkedin",
             "profile", "experience", "education", "skills", "languages")

ICON_SETS: dict[str, dict[str, str]] = {
    "none":    {key: "" for key in ICON_KEYS},
    "outline": { ... },   # Lucide-style, stroke="currentColor"
    "filled":  { ... },   # Material-style, fill="currentColor"
}

TEMPLATE_DEFAULT_ICON_SET: dict[str, str] = {
    "classic_german": "none",
    "modern_swiss":   "outline",
}

def resolve_icon_set(template: str, icon_set: str | None) -> dict[str, str]:
    """Return icon dict for chosen set, falling back to template default then 'none'."""
    chosen = icon_set or TEMPLATE_DEFAULT_ICON_SET.get(template, "none")
    return ICON_SETS.get(chosen, ICON_SETS["none"])
```

### `currentColor` for future colour scheme support

All SVGs use `stroke="currentColor"` (outline) or `fill="currentColor"` (filled). Icon colour is inherited from the parent element's CSS `color` property, which is driven by `--accent` / `--muted` CSS variables. Future colour scheme changes require only updating the CSS variables — icons recolour automatically.

### Schema (`schemas/cv.py`)

```python
CVIconSet = Literal["none", "outline", "filled"]

class CVGenerateRequest(BaseModel):
    job_id: uuid.UUID
    template: CVTemplate = "classic_german"
    icon_set: CVIconSet | None = None        # None = use template default
    avoid_page_breaks: bool = True
```

### Model (`models/cv.py`)

New column: `icon_set: str | None`, nullable, default `NULL` (resolved to template default at render time).

### Service (`services/cv.py`)

```python
# In get_cv_html:
from applire.icon_sets import resolve_icon_set
icons = resolve_icon_set(record.template, record.icon_set)
return template.render(cv=tailored, icons=icons, avoid_page_breaks=record.avoid_page_breaks)
```

`generate_cv` and `_render_cv_background` store the `icon_set` value (may be `None`) on the record.

### Template usage pattern (both templates)

Contact fields:
```html
{% if cv.contact.phone %}
<span>{{ icons.phone | safe }}{{ cv.contact.phone }}</span>
{% endif %}
```

Section headers:
```html
{{ icons.experience | safe }} Experience
```

When `icons.phone` is `""` (the `none` set), `| safe` renders nothing — no structural changes needed.

### Per-template defaults

| Template | Default icon set |
|---|---|
| `classic_german` | `none` |
| `modern_swiss` | `outline` |
| _(future templates)_ | Declared in `TEMPLATE_DEFAULT_ICON_SET` |

---

## Migration

Single Alembic migration (`add_icon_set_and_avoid_page_breaks_to_generated_cvs`):

```python
op.add_column("generated_cvs", sa.Column("icon_set", sa.String(32), nullable=True))
op.add_column("generated_cvs", sa.Column("avoid_page_breaks", sa.Boolean(), nullable=False, server_default="true"))
```

Existing CVs: `icon_set=NULL` (resolves to template default at render), `avoid_page_breaks=TRUE`.

---

## Testing Plan

### Unit tests (`tests/unit/test_icon_sets.py`)

| Test | Assertion |
|---|---|
| `test_resolve_icon_set_default` | `resolve_icon_set("modern_swiss", None)` returns `outline` set |
| `test_resolve_icon_set_override` | `resolve_icon_set("classic_german", "filled")` returns `filled` set |
| `test_resolve_icon_set_unknown_template` | Unknown template name falls back to `none` |
| `test_icon_set_currentcolor` | All SVGs in `outline` and `filled` sets contain `currentColor`, no hex colour values |

### Unit tests (`tests/unit/test_cv_service.py` additions)

| Test | Assertion |
|---|---|
| `test_cv_html_contains_icons` | `get_cv_html` with `icon_set="outline"` produces HTML containing `<svg` |
| `test_cv_html_no_icons` | `icon_set="none"` produces HTML with no `<svg` tags |
| `test_cv_html_page_break_on` | `avoid_page_breaks=True` renders `class="no-breaks"` on `<body>` |
| `test_cv_html_page_break_off` | `avoid_page_breaks=False` does not render `no-breaks` class |
| `test_generate_cv_stores_icon_set` | `GeneratedCV` record persists the chosen `icon_set` |
| `test_generate_cv_stores_avoid_page_breaks` | `GeneratedCV` record persists `avoid_page_breaks` |

### Migration test

Existing migration test suite gets one assertion confirming both new columns exist with correct defaults.

### Out of scope

Visual/pixel accuracy of PDF output is validated manually by reviewing a generated PDF. Playwright/Chromium rendering correctness is not tested in CI.

---

## What is not changing

- `TailoredCVData` schema — no new fields; icons are a rendering concern, not a data concern.
- Frontend — CV generation request parameters are passed through; no new UI components in this sprint.
- MCP tools — `icon_set` and `avoid_page_breaks` are added as optional parameters to the CV generation tool.
- Existing CVs — backward compatible; `NULL` icon_set resolves to template default.
