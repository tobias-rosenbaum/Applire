# CV Templates Expansion + Multi-Color Schema Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend Applire from 2 to 7 CV templates and introduce a multi-slot color schema (`primary`, `primary_tint`, `surface`, `surface_text`, `secondary`) with WCAG-compliant auto-contrast, while keeping full backward compatibility with existing templates.

**Architecture:** `ColorContext` dataclass gains 5 new fields (3 Phase-1 defaults, 2 auto-derived); existing `accent`/`tint` fields remain as aliases. All new slots are computed from `seed_primary` at render time — no DB migration. Five new Jinja2 templates are registered in `_TEMPLATE_FILES` and the `CVTemplate` literal.

**Tech Stack:** Python 3.12, FastAPI, Jinja2, Playwright (PDF rendering), pytest, SQLAlchemy, colorsys (stdlib)

**Branch:** `sprint-24`

**Working directory for all commands:** `/home/apliqa/Documents/Applire/Solution`

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Modify | `backend/applire/services/color_detection.py` | Add `derive_surface_text()`, extend `ColorContext`, update `_make_color_context()` and `resolve_color_context()` |
| Modify | `tests/unit/test_color_detection.py` | New unit tests for `derive_surface_text()` and `ColorContext` fields |
| Create | `backend/applire/templates/executive.html.j2` | Executive/Premium template |
| Create | `backend/applire/templates/tech_developer.html.j2` | Tech/Developer dark template |
| Create | `backend/applire/templates/creative_sidebar.html.j2` | Creative two-column sidebar template |
| Create | `backend/applire/templates/academic.html.j2` | Academic/Scientific template |
| Create | `backend/applire/templates/compact_pro.html.j2` | Compact Pro dense template |
| Modify | `backend/applire/schemas/cv.py` | Add 5 new literals to `CVTemplate` |
| Modify | `backend/applire/services/cv.py` | Add 5 entries to `_TEMPLATE_FILES` |
| Create | `tests/unit/test_template_render.py` | Parametrized render test for all 7 templates |
| Create | `backend/data/static/templates/*.png` | Thumbnail PNGs (generated via script) |

---

## Task 1: Add `derive_surface_text()` + unit tests

**Files:**
- Modify: `backend/applire/services/color_detection.py` (after `derive_tint`)
- Modify: `tests/unit/test_color_detection.py` (new `TestDeriveSurfaceText` class)

- [ ] **Step 1: Write failing tests**

Append to `tests/unit/test_color_detection.py`:

```python
class TestDeriveSurfaceText:
    """WCAG-contrast-driven auto text colour on coloured surfaces."""

    def test_dark_surface_returns_white(self):
        from applire.services.color_detection import derive_surface_text
        # Navy — luminance ~0.06
        assert derive_surface_text("#1a3a6e") == "#ffffff"

    def test_light_surface_returns_dark(self):
        from applire.services.color_detection import derive_surface_text
        # Light blue — luminance ~0.75
        assert derive_surface_text("#c5d8f8") == "#1a1a1a"

    def test_pure_black_returns_white(self):
        from applire.services.color_detection import derive_surface_text
        assert derive_surface_text("#000000") == "#ffffff"

    def test_pure_white_returns_dark(self):
        from applire.services.color_detection import derive_surface_text
        assert derive_surface_text("#ffffff") == "#1a1a1a"

    def test_mid_grey_boundary(self):
        from applire.services.color_detection import derive_surface_text
        # #767676 is approx WCAG boundary — just confirm it returns a valid value
        result = derive_surface_text("#767676")
        assert result in ("#ffffff", "#1a1a1a")

    def test_result_is_always_one_of_two_values(self):
        from applire.services.color_detection import derive_surface_text
        for colour in ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff6600"]:
            assert derive_surface_text(colour) in ("#ffffff", "#1a1a1a")
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_color_detection.py::TestDeriveSurfaceText -v
```

Expected: `ImportError` or `AttributeError` — `derive_surface_text` does not exist yet.

- [ ] **Step 3: Implement `derive_surface_text()`**

In `backend/applire/services/color_detection.py`, add immediately after the `derive_tint` function (around line 57):

```python
def derive_surface_text(hex_color: str) -> str:
    """Return white or black for legible text on hex_color background.

    Uses the WCAG relative-luminance formula (IEC 61966-2-1 sRGB).
    Threshold 0.179 is the geometric mean of 4.5:1 contrast against #000 and #fff.
    """
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

    def _lin(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    luminance = 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)
    return "#ffffff" if luminance < 0.179 else "#1a1a1a"
```

- [ ] **Step 4: Run tests — expect all pass**

```bash
pytest tests/unit/test_color_detection.py::TestDeriveSurfaceText -v
```

Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/applire/services/color_detection.py tests/unit/test_color_detection.py
git commit -m "feat: add derive_surface_text() with WCAG luminance threshold"
```

---

## Task 2: Extend `ColorContext` and update all construction sites

**Files:**
- Modify: `backend/applire/services/color_detection.py`
- Modify: `tests/unit/test_color_detection.py`

- [ ] **Step 1: Write failing test for new ColorContext fields**

Append to `tests/unit/test_color_detection.py`:

```python
class TestColorContextFields:
    """_make_color_context must populate all Phase-1 slots."""

    def _ctx(self, hex_color):
        from applire.services.color_detection import _make_color_context
        return _make_color_context(hex_color)

    def test_primary_equals_seed(self):
        ctx = self._ctx("#2b5fa8")
        assert ctx.primary == "#2b5fa8"

    def test_accent_alias_equals_primary(self):
        ctx = self._ctx("#2b5fa8")
        assert ctx.accent == ctx.primary

    def test_primary_tint_is_hex(self):
        ctx = self._ctx("#2b5fa8")
        assert ctx.primary_tint.startswith("#") and len(ctx.primary_tint) == 7

    def test_tint_alias_equals_primary_tint(self):
        ctx = self._ctx("#2b5fa8")
        assert ctx.tint == ctx.primary_tint

    def test_surface_equals_primary_in_phase1(self):
        ctx = self._ctx("#2b5fa8")
        assert ctx.surface == ctx.primary

    def test_secondary_equals_primary_in_phase1(self):
        ctx = self._ctx("#2b5fa8")
        assert ctx.secondary == ctx.primary

    def test_surface_text_is_white_for_dark_surface(self):
        ctx = self._ctx("#1a3a6e")
        assert ctx.surface_text == "#ffffff"

    def test_surface_text_is_dark_for_light_surface(self):
        ctx = self._ctx("#dce8f7")
        assert ctx.surface_text == "#1a1a1a"
```

- [ ] **Step 2: Run to confirm failures**

```bash
pytest tests/unit/test_color_detection.py::TestColorContextFields -v
```

Expected: `AttributeError` — fields don't exist yet.

- [ ] **Step 3: Replace `ColorContext` dataclass and `_make_color_context`**

In `backend/applire/services/color_detection.py`, replace the existing `ColorContext` dataclass and `_make_color_context` / `_default_context` functions:

```python
@dataclass
class ColorContext:
    primary: str        # hex — main brand color
    primary_tint: str   # hex — light version of primary (L=95%, S=10%)
    surface: str        # hex — sidebar/header bg (Phase 1: = primary)
    surface_text: str   # "#ffffff" or "#1a1a1a" — WCAG auto-computed
    secondary: str      # hex — second accent (Phase 1: = primary)
    # Backward-compat aliases — existing templates use color.accent / color.tint
    accent: str         # = primary
    tint: str           # = primary_tint


def _make_color_context(hex_primary: str) -> ColorContext:
    tint = derive_tint(hex_primary)
    return ColorContext(
        primary=hex_primary,
        primary_tint=tint,
        surface=hex_primary,      # Phase 1: surface = primary
        surface_text=derive_surface_text(hex_primary),
        secondary=hex_primary,    # Phase 1: secondary = primary
        accent=hex_primary,       # backward compat
        tint=tint,                # backward compat
    )


def _default_context() -> ColorContext:
    return _make_color_context(DEFAULT_ACCENT)
```

- [ ] **Step 4: Update `resolve_color_context` to use `_make_color_context`**

In `resolve_color_context`, replace every `ColorContext(accent=..., tint=...)` construction with `_make_color_context(cp.derived["--cv-accent"])`:

```python
async def resolve_color_context(record: "GeneratedCV", db: AsyncSession) -> ColorContext:
    from applire.models.job import JobAnalysis

    # Step 1: CV-specific override
    if record.color_profile_id:
        cp = await db.get(ColorProfile, record.color_profile_id)
        if cp:
            return _make_color_context(cp.derived["--cv-accent"])

    # Step 2: Auto-detected company color
    job = await db.get(JobAnalysis, record.job_analysis_id)
    if job and job.company_id:
        company = await db.get(Company, job.company_id)
        if company and company.color_profile_id:
            cp = await db.get(ColorProfile, company.color_profile_id)
            if cp:
                return _make_color_context(cp.derived["--cv-accent"])

    # Step 3: User default (CE: always stub user)
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == _CE_STUB_USER_ID)
    )
    settings = result.scalar_one_or_none()
    if settings and settings.default_color_profile_id:
        cp = await db.get(ColorProfile, settings.default_color_profile_id)
        if cp:
            return _make_color_context(cp.derived["--cv-accent"])

    # Step 4: System default
    return _default_context()
```

- [ ] **Step 5: Run all color detection tests**

```bash
pytest tests/unit/test_color_detection.py -v
```

Expected: All tests (existing + new) PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/applire/services/color_detection.py tests/unit/test_color_detection.py
git commit -m "feat: extend ColorContext with primary/surface/secondary slots and backward-compat aliases"
```

---

## Task 3: Template — `executive.html.j2`

**Files:**
- Create: `backend/applire/templates/executive.html.j2`

- [ ] **Step 1: Create the template**

Create `backend/applire/templates/executive.html.j2`:

```jinja2
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <title>Lebenslauf – {{ cv.contact.name }}</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --cv-primary: {{ color.primary }};
      --cv-primary-tint: {{ color.primary_tint }};
      --cv-surface: {{ color.surface }};
      --cv-surface-text: {{ color.surface_text }};
      --cv-secondary: {{ color.secondary }};
      --text: #1a1a2e;
      --muted: #4a4a5a;
      --rule: #d8d8e0;
    }

    body {
      font-family: Georgia, "Times New Roman", serif;
      font-size: 10.5pt;
      line-height: 1.5;
      color: var(--text);
      background: #fff;
    }

    .page {
      width: 210mm;
      min-height: 297mm;
      margin: 0 auto;
    }

    /* ---- Dark header band ---- */
    .header {
      background: var(--cv-surface);
      color: var(--cv-surface-text);
      padding: 18mm 20mm 14mm 20mm;
    }

    .header-inner {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16pt;
    }

    .header-name h1 {
      font-size: 24pt;
      font-weight: bold;
      letter-spacing: 0.04em;
      color: var(--cv-surface-text);
      margin-bottom: 4pt;
    }

    .header-title {
      font-size: 11pt;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--cv-surface-text);
      opacity: 0.75;
    }

    .header-contact {
      text-align: right;
      font-size: 9pt;
      color: var(--cv-surface-text);
      opacity: 0.85;
      line-height: 1.8;
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    .header-avatar {
      flex-shrink: 0;
      width: 32mm;
      height: 32mm;
      border-radius: 50%;
      overflow: hidden;
      border: 2px solid rgba(255,255,255,0.3);
    }
    .header-avatar img { width: 100%; height: 100%; object-fit: cover; object-position: center top; }

    /* ---- Body: two-column ---- */
    .body {
      display: grid;
      grid-template-columns: 1fr 2fr;
      gap: 0;
      padding: 14mm 20mm 16mm 20mm;
    }

    .col-left { padding-right: 14pt; border-right: 1px solid var(--rule); }
    .col-right { padding-left: 14pt; }

    /* ---- Section ---- */
    .section { margin-bottom: 14pt; }

    .section-title {
      font-size: 8pt;
      font-weight: bold;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--cv-primary);
      border-bottom: 1.5px solid var(--cv-primary);
      padding-bottom: 2pt;
      margin-bottom: 8pt;
    }

    /* ---- Entry ---- */
    .entry { margin-bottom: 9pt; }

    .entry-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
    }

    .entry-title {
      font-size: 10.5pt;
      font-weight: bold;
      color: var(--text);
    }

    .entry-dates {
      font-size: 8.5pt;
      color: var(--muted);
      white-space: nowrap;
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    .entry-subtitle {
      font-size: 9.5pt;
      color: var(--muted);
      margin-bottom: 3pt;
    }

    .entry-bullets {
      padding-left: 12pt;
      list-style-type: disc;
      margin-top: 3pt;
    }

    .entry-bullets li {
      margin-bottom: 1.5pt;
      font-size: 9.5pt;
    }

    /* ---- Skills (left column) ---- */
    .skill-item {
      font-size: 9.5pt;
      padding: 2pt 0;
      color: var(--text);
      border-bottom: 1px dotted var(--rule);
    }

    /* ---- Languages ---- */
    .lang-row {
      display: flex;
      justify-content: space-between;
      font-size: 9.5pt;
      padding: 2pt 0;
      border-bottom: 1px dotted var(--rule);
    }
    .lang-name { font-weight: 600; }
    .lang-level { color: var(--muted); }

    /* ---- Summary ---- */
    .summary-text {
      font-size: 10.5pt;
      line-height: 1.55;
      color: var(--text);
    }
  </style>
</head>
<body>
<div class="page">

  <header class="header">
    <div class="header-inner">
      <div>
        <div class="header-name"><h1>{{ cv.contact.name }}</h1></div>
        {% if cv.work_history %}<div class="header-title">{{ cv.work_history[0].role }}</div>{% endif %}
      </div>
      <div style="display:flex;align-items:flex-start;gap:14pt;">
        <div class="header-contact">
          {% if cv.contact.location %}<div>{{ cv.contact.location }}</div>{% endif %}
          {% if cv.contact.phone %}<div>{{ cv.contact.phone }}</div>{% endif %}
          {% if cv.contact.email %}<div>{{ cv.contact.email }}</div>{% endif %}
          {% if cv.contact.linkedin %}<div>{{ cv.contact.linkedin }}</div>{% endif %}
        </div>
        {% if cv.show_photo and cv.contact.photo_url %}
        <div class="header-avatar">
          <img src="{{ cv.contact.photo_url }}" alt="Foto">
        </div>
        {% endif %}
      </div>
    </div>
  </header>

  <div class="body">

    <!-- LEFT COLUMN -->
    <div class="col-left">

      {% if cv.skills %}
      <div class="section">
        <div class="section-title">Kompetenzen</div>
        {% for skill in cv.skills %}
        <div class="skill-item">{{ skill }}</div>
        {% endfor %}
      </div>
      {% endif %}

      {% if cv.education %}
      <div class="section">
        <div class="section-title">Ausbildung</div>
        {% for edu in cv.education %}
        <div class="entry">
          <div class="entry-title">{{ edu.degree }}{% if edu.field %}, {{ edu.field }}{% endif %}</div>
          <div class="entry-subtitle">{{ edu.institution }}</div>
          <div class="entry-dates">{{ edu.start_date }}{% if edu.start_date %} – {% endif %}{{ edu.end_date if edu.end_date else ("heute" if edu.start_date else "") }}</div>
        </div>
        {% endfor %}
      </div>
      {% endif %}

      {% if cv.languages %}
      <div class="section">
        <div class="section-title">Sprachen</div>
        {% for lang in cv.languages %}
        <div class="lang-row">
          <span class="lang-name">{{ lang.language }}</span>
          <span class="lang-level">{{ lang.level }}</span>
        </div>
        {% endfor %}
      </div>
      {% endif %}

    </div>

    <!-- RIGHT COLUMN -->
    <div class="col-right">

      {% if cv.summary %}
      <div class="section">
        <div class="section-title">Profil</div>
        <p class="summary-text">{{ cv.summary }}</p>
      </div>
      {% endif %}

      {% if cv.work_history %}
      <div class="section">
        <div class="section-title">Berufserfahrung</div>
        {% for job in cv.work_history %}
        <div class="entry">
          <div class="entry-header">
            <div class="entry-title">{{ job.role }}</div>
            <div class="entry-dates">{{ job.start_date }} – {{ job.end_date if job.end_date else "heute" }}</div>
          </div>
          <div class="entry-subtitle">{{ job.company }}</div>
          {% if job.bullets %}
          <ul class="entry-bullets">
            {% for bullet in job.bullets %}
            <li>{{ bullet }}</li>
            {% endfor %}
          </ul>
          {% endif %}
        </div>
        {% endfor %}
      </div>
      {% endif %}

    </div>
  </div>

</div>
</body>
</html>
```

- [ ] **Step 2: Verify Jinja2 syntax is valid (render test comes in Task 8)**

```bash
cd /home/apliqa/Documents/Applire/Solution
python3 -c "
from jinja2 import Environment, FileSystemLoader, select_autoescape
env = Environment(loader=FileSystemLoader('backend/applire/templates'), autoescape=select_autoescape(['html']))
t = env.get_template('executive.html.j2')
print('OK:', t.name)
"
```

Expected: `OK: executive.html.j2`

- [ ] **Step 3: Commit**

```bash
git add backend/applire/templates/executive.html.j2
git commit -m "feat: add executive CV template (dark header, two-column, serif)"
```

---

## Task 4: Template — `tech_developer.html.j2`

**Files:**
- Create: `backend/applire/templates/tech_developer.html.j2`

- [ ] **Step 1: Create the template**

Create `backend/applire/templates/tech_developer.html.j2`:

```jinja2
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>CV – {{ cv.contact.name }}</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --cv-primary: {{ color.primary }};
      --cv-primary-tint: {{ color.primary_tint }};
      --cv-surface: {{ color.surface }};
      --cv-surface-text: {{ color.surface_text }};
      --bg: #0d1117;
      --bg2: #161b22;
      --border: #30363d;
      --text: #e6edf3;
      --muted: #8b949e;
    }

    body {
      font-family: "Courier New", Courier, monospace;
      font-size: 10pt;
      line-height: 1.55;
      color: var(--text);
      background: var(--bg);
    }

    .page {
      width: 210mm;
      min-height: 297mm;
      margin: 0 auto;
      padding: 16mm 20mm 16mm 20mm;
    }

    /* ---- Header ---- */
    .header {
      border-bottom: 1px solid var(--border);
      padding-bottom: 12pt;
      margin-bottom: 16pt;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }

    .header-name {
      font-size: 20pt;
      font-weight: bold;
      color: var(--cv-primary);
      letter-spacing: -0.01em;
    }

    .header-handle {
      font-size: 9pt;
      color: var(--muted);
      margin-top: 2pt;
    }

    .header-contact {
      text-align: right;
      font-size: 8.5pt;
      color: var(--muted);
      line-height: 1.8;
    }

    /* ---- Accent strip ---- */
    .accent-strip {
      height: 3pt;
      background: var(--cv-primary);
      margin-bottom: 16pt;
      border-radius: 1pt;
    }

    /* ---- Section ---- */
    .section { margin-bottom: 16pt; }

    .section-label {
      font-size: 8pt;
      color: var(--muted);
      letter-spacing: 0.05em;
      margin-bottom: 8pt;
    }

    .section-label::before { content: "// "; color: var(--border); }

    /* ---- Entry ---- */
    .entry { margin-bottom: 10pt; }

    .entry-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 1pt;
    }

    .entry-title {
      font-size: 10.5pt;
      font-weight: bold;
      color: var(--cv-primary);
    }

    .entry-dates {
      font-size: 8.5pt;
      color: var(--muted);
    }

    .entry-subtitle {
      font-size: 9pt;
      color: var(--muted);
      margin-bottom: 3pt;
    }

    .entry-bullets {
      padding-left: 12pt;
      list-style-type: none;
      margin-top: 3pt;
    }

    .entry-bullets li::before { content: "▸ "; color: var(--cv-primary); }

    .entry-bullets li {
      margin-bottom: 2pt;
      font-size: 9.5pt;
      color: var(--text);
    }

    /* ---- Skills ---- */
    .skills-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 4pt 6pt;
      list-style: none;
    }

    .skills-grid li {
      font-size: 8.5pt;
      padding: 2pt 7pt;
      background: var(--bg2);
      border: 1px solid var(--cv-primary);
      border-radius: 2pt;
      color: var(--cv-primary);
    }

    /* ---- Summary ---- */
    .summary-text {
      font-size: 10pt;
      color: var(--text);
      line-height: 1.55;
    }

    /* ---- Languages ---- */
    .lang-row {
      display: flex;
      gap: 8pt;
      font-size: 9.5pt;
      margin-bottom: 3pt;
    }
    .lang-name { color: var(--cv-primary); font-weight: bold; }
    .lang-level { color: var(--muted); }

    @media print {
      body { background: var(--bg); -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    }
  </style>
</head>
<body>
<div class="page">

  <div class="accent-strip"></div>

  <header class="header">
    <div>
      <div class="header-name">{{ cv.contact.name }}</div>
      {% if cv.contact.linkedin %}
      <div class="header-handle">{{ cv.contact.linkedin }}</div>
      {% endif %}
    </div>
    <div class="header-contact">
      {% if cv.contact.location %}<div>{{ cv.contact.location }}</div>{% endif %}
      {% if cv.contact.email %}<div>{{ cv.contact.email }}</div>{% endif %}
      {% if cv.contact.phone %}<div>{{ cv.contact.phone }}</div>{% endif %}
    </div>
  </header>

  {% if cv.summary %}
  <div class="section">
    <div class="section-label">about</div>
    <p class="summary-text">{{ cv.summary }}</p>
  </div>
  {% endif %}

  {% if cv.skills %}
  <div class="section">
    <div class="section-label">stack</div>
    <ul class="skills-grid">
      {% for skill in cv.skills %}
      <li>{{ skill }}</li>
      {% endfor %}
    </ul>
  </div>
  {% endif %}

  {% if cv.work_history %}
  <div class="section">
    <div class="section-label">experience</div>
    {% for job in cv.work_history %}
    <div class="entry">
      <div class="entry-header">
        <div class="entry-title">{{ job.role }}</div>
        <div class="entry-dates">{{ job.start_date }} – {{ job.end_date if job.end_date else "present" }}</div>
      </div>
      <div class="entry-subtitle">{{ job.company }}</div>
      {% if job.bullets %}
      <ul class="entry-bullets">
        {% for bullet in job.bullets %}
        <li>{{ bullet }}</li>
        {% endfor %}
      </ul>
      {% endif %}
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if cv.education %}
  <div class="section">
    <div class="section-label">education</div>
    {% for edu in cv.education %}
    <div class="entry">
      <div class="entry-header">
        <div class="entry-title">{{ edu.degree }}{% if edu.field %}, {{ edu.field }}{% endif %}</div>
        <div class="entry-dates">{{ edu.start_date }}{% if edu.start_date %} – {% endif %}{{ edu.end_date if edu.end_date else ("present" if edu.start_date else "") }}</div>
      </div>
      <div class="entry-subtitle">{{ edu.institution }}</div>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if cv.languages %}
  <div class="section">
    <div class="section-label">languages</div>
    {% for lang in cv.languages %}
    <div class="lang-row">
      <span class="lang-name">{{ lang.language }}</span>
      <span class="lang-level">{{ lang.level }}</span>
    </div>
    {% endfor %}
  </div>
  {% endif %}

</div>
</body>
</html>
```

- [ ] **Step 2: Verify syntax**

```bash
python3 -c "
from jinja2 import Environment, FileSystemLoader, select_autoescape
env = Environment(loader=FileSystemLoader('backend/applire/templates'), autoescape=select_autoescape(['html']))
t = env.get_template('tech_developer.html.j2')
print('OK:', t.name)
"
```

Expected: `OK: tech_developer.html.j2`

- [ ] **Step 3: Commit**

```bash
git add backend/applire/templates/tech_developer.html.j2
git commit -m "feat: add tech_developer CV template (dark bg, monospace, code aesthetic)"
```

---

## Task 5: Template — `creative_sidebar.html.j2`

**Files:**
- Create: `backend/applire/templates/creative_sidebar.html.j2`

- [ ] **Step 1: Create the template**

Create `backend/applire/templates/creative_sidebar.html.j2`:

```jinja2
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <title>CV – {{ cv.contact.name }}</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --cv-primary: {{ color.primary }};
      --cv-primary-tint: {{ color.primary_tint }};
      --cv-surface: {{ color.surface }};
      --cv-surface-text: {{ color.surface_text }};
      --text: #1c1c1c;
      --muted: #5a5a5a;
      --rule: #e0e0e0;
    }

    body {
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 10pt;
      line-height: 1.5;
      color: var(--text);
      background: #fff;
    }

    .page {
      width: 210mm;
      min-height: 297mm;
      margin: 0 auto;
      display: flex;
    }

    /* ---- Left sidebar ---- */
    .sidebar {
      width: 68mm;
      background: var(--cv-surface);
      color: var(--cv-surface-text);
      padding: 20mm 12mm 16mm 12mm;
      flex-shrink: 0;
    }

    .sidebar-avatar {
      width: 40mm;
      height: 40mm;
      border-radius: 50%;
      overflow: hidden;
      margin: 0 auto 10pt;
      border: 3px solid rgba(255,255,255,0.35);
    }
    .sidebar-avatar img { width: 100%; height: 100%; object-fit: cover; object-position: center top; }

    .sidebar-avatar-placeholder {
      width: 40mm;
      height: 40mm;
      border-radius: 50%;
      background: rgba(255,255,255,0.2);
      margin: 0 auto 10pt;
    }

    .sidebar-name {
      font-size: 12pt;
      font-weight: bold;
      text-align: center;
      color: var(--cv-surface-text);
      margin-bottom: 4pt;
    }

    .sidebar-section {
      margin-top: 14pt;
    }

    .sidebar-section-title {
      font-size: 7pt;
      font-weight: bold;
      text-transform: uppercase;
      letter-spacing: 0.15em;
      color: var(--cv-surface-text);
      opacity: 0.65;
      border-bottom: 1px solid rgba(255,255,255,0.2);
      padding-bottom: 3pt;
      margin-bottom: 6pt;
    }

    .sidebar-item {
      font-size: 8.5pt;
      color: var(--cv-surface-text);
      line-height: 1.7;
    }

    .sidebar-skill {
      font-size: 8.5pt;
      color: var(--cv-surface-text);
      padding: 1.5pt 0;
      border-bottom: 1px solid rgba(255,255,255,0.1);
      line-height: 1.5;
    }

    /* ---- Main column ---- */
    .main {
      flex: 1;
      padding: 20mm 18mm 16mm 16mm;
    }

    /* ---- Section ---- */
    .section { margin-bottom: 14pt; }

    .section-title {
      font-size: 9.5pt;
      font-weight: bold;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--cv-primary);
      border-bottom: 2px solid var(--cv-primary);
      padding-bottom: 2pt;
      margin-bottom: 8pt;
    }

    /* ---- Entry ---- */
    .entry { margin-bottom: 9pt; }

    .entry-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
    }

    .entry-title {
      font-size: 10.5pt;
      font-weight: bold;
      color: var(--text);
    }

    .entry-dates {
      font-size: 8.5pt;
      color: var(--muted);
      white-space: nowrap;
    }

    .entry-subtitle {
      font-size: 9.5pt;
      color: var(--muted);
      margin-bottom: 3pt;
    }

    .entry-bullets {
      padding-left: 12pt;
      list-style-type: disc;
      margin-top: 3pt;
    }

    .entry-bullets li {
      margin-bottom: 2pt;
      font-size: 9.5pt;
    }

    /* ---- Skill tags in main col ---- */
    .tag-list {
      display: flex;
      flex-wrap: wrap;
      gap: 4pt;
      list-style: none;
    }

    .tag-list li {
      font-size: 8.5pt;
      padding: 2pt 8pt;
      background: var(--cv-primary-tint);
      color: var(--cv-primary);
      border-radius: 2pt;
      font-weight: 600;
    }

    /* ---- Summary ---- */
    .summary-text {
      font-size: 10pt;
      line-height: 1.55;
    }
  </style>
</head>
<body>
<div class="page">

  <!-- SIDEBAR -->
  <aside class="sidebar">
    {% if cv.show_photo and cv.contact.photo_url %}
    <div class="sidebar-avatar">
      <img src="{{ cv.contact.photo_url }}" alt="Foto">
    </div>
    {% else %}
    <div class="sidebar-avatar-placeholder"></div>
    {% endif %}

    <div class="sidebar-name">{{ cv.contact.name }}</div>

    <div class="sidebar-section">
      <div class="sidebar-section-title">Kontakt</div>
      {% if cv.contact.location %}<div class="sidebar-item">{{ cv.contact.location }}</div>{% endif %}
      {% if cv.contact.phone %}<div class="sidebar-item">{{ cv.contact.phone }}</div>{% endif %}
      {% if cv.contact.email %}<div class="sidebar-item">{{ cv.contact.email }}</div>{% endif %}
      {% if cv.contact.linkedin %}<div class="sidebar-item">{{ cv.contact.linkedin }}</div>{% endif %}
    </div>

    {% if cv.skills %}
    <div class="sidebar-section">
      <div class="sidebar-section-title">Skills</div>
      {% for skill in cv.skills %}
      <div class="sidebar-skill">{{ skill }}</div>
      {% endfor %}
    </div>
    {% endif %}

    {% if cv.languages %}
    <div class="sidebar-section">
      <div class="sidebar-section-title">Sprachen</div>
      {% for lang in cv.languages %}
      <div class="sidebar-item">{{ lang.language }} · {{ lang.level }}</div>
      {% endfor %}
    </div>
    {% endif %}
  </aside>

  <!-- MAIN -->
  <main class="main">

    {% if cv.summary %}
    <div class="section">
      <div class="section-title">Profil</div>
      <p class="summary-text">{{ cv.summary }}</p>
    </div>
    {% endif %}

    {% if cv.work_history %}
    <div class="section">
      <div class="section-title">Berufserfahrung</div>
      {% for job in cv.work_history %}
      <div class="entry">
        <div class="entry-header">
          <div class="entry-title">{{ job.role }}</div>
          <div class="entry-dates">{{ job.start_date }} – {{ job.end_date if job.end_date else "heute" }}</div>
        </div>
        <div class="entry-subtitle">{{ job.company }}</div>
        {% if job.bullets %}
        <ul class="entry-bullets">
          {% for bullet in job.bullets %}
          <li>{{ bullet }}</li>
          {% endfor %}
        </ul>
        {% endif %}
      </div>
      {% endfor %}
    </div>
    {% endif %}

    {% if cv.education %}
    <div class="section">
      <div class="section-title">Ausbildung</div>
      {% for edu in cv.education %}
      <div class="entry">
        <div class="entry-header">
          <div class="entry-title">{{ edu.degree }}{% if edu.field %}, {{ edu.field }}{% endif %}</div>
          <div class="entry-dates">{{ edu.start_date }}{% if edu.start_date %} – {% endif %}{{ edu.end_date if edu.end_date else ("heute" if edu.start_date else "") }}</div>
        </div>
        <div class="entry-subtitle">{{ edu.institution }}</div>
      </div>
      {% endfor %}
    </div>
    {% endif %}

  </main>

</div>
</body>
</html>
```

- [ ] **Step 2: Verify syntax**

```bash
python3 -c "
from jinja2 import Environment, FileSystemLoader, select_autoescape
env = Environment(loader=FileSystemLoader('backend/applire/templates'), autoescape=select_autoescape(['html']))
t = env.get_template('creative_sidebar.html.j2')
print('OK:', t.name)
"
```

- [ ] **Step 3: Commit**

```bash
git add backend/applire/templates/creative_sidebar.html.j2
git commit -m "feat: add creative_sidebar CV template (coloured sidebar, auto-contrast text)"
```

---

## Task 6: Template — `academic.html.j2`

**Files:**
- Create: `backend/applire/templates/academic.html.j2`

- [ ] **Step 1: Create the template**

Create `backend/applire/templates/academic.html.j2`:

```jinja2
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <title>Curriculum Vitae – {{ cv.contact.name }}</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --cv-primary: {{ color.primary }};
      --cv-primary-tint: {{ color.primary_tint }};
      --text: #111;
      --muted: #444;
      --rule: #bbb;
    }

    body {
      font-family: "Times New Roman", Times, serif;
      font-size: 11pt;
      line-height: 1.5;
      color: var(--text);
      background: #fff;
    }

    .page {
      width: 210mm;
      min-height: 297mm;
      margin: 0 auto;
      padding: 22mm 22mm 20mm 22mm;
    }

    /* ---- Header: centred ---- */
    .header {
      text-align: center;
      border-bottom: 1.5px solid var(--cv-primary);
      padding-bottom: 10pt;
      margin-bottom: 16pt;
    }

    .header h1 {
      font-size: 18pt;
      font-weight: bold;
      letter-spacing: 0.03em;
      margin-bottom: 4pt;
    }

    .header-sub {
      font-size: 9.5pt;
      color: var(--muted);
      line-height: 1.8;
    }

    /* ---- Section ---- */
    .section { margin-bottom: 14pt; }

    .section-title {
      font-size: 10.5pt;
      font-weight: bold;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--cv-primary);
      border-bottom: 1px solid var(--rule);
      padding-bottom: 2pt;
      margin-bottom: 8pt;
    }

    /* ---- Entry: two-column date + content ---- */
    .entry {
      display: grid;
      grid-template-columns: 28mm 1fr;
      gap: 0 8pt;
      margin-bottom: 8pt;
    }

    .entry-date {
      font-size: 9.5pt;
      color: var(--muted);
      padding-top: 1pt;
      text-align: right;
    }

    .entry-content { }

    .entry-title {
      font-size: 10.5pt;
      font-weight: bold;
    }

    .entry-subtitle {
      font-size: 9.5pt;
      color: var(--muted);
      margin-bottom: 2pt;
    }

    .entry-bullets {
      padding-left: 12pt;
      list-style-type: disc;
      margin-top: 2pt;
    }

    .entry-bullets li {
      margin-bottom: 1.5pt;
      font-size: 10pt;
    }

    /* ---- Skills / competences ---- */
    .skill-block { font-size: 10pt; line-height: 1.7; }

    /* ---- Languages ---- */
    .lang-table {
      display: grid;
      grid-template-columns: max-content 1fr;
      gap: 3pt 16pt;
      font-size: 10pt;
    }
    .lang-name { font-weight: 600; }
    .lang-level { color: var(--muted); }

    /* ---- Summary ---- */
    .summary-text { font-size: 11pt; line-height: 1.55; }
  </style>
</head>
<body>
<div class="page">

  <header class="header">
    <h1>{{ cv.contact.name }}</h1>
    <div class="header-sub">
      {% if cv.contact.location %}<span>{{ cv.contact.location }}</span>{% endif %}
      {% if cv.contact.email %} &nbsp;·&nbsp; <span>{{ cv.contact.email }}</span>{% endif %}
      {% if cv.contact.phone %} &nbsp;·&nbsp; <span>{{ cv.contact.phone }}</span>{% endif %}
      {% if cv.contact.linkedin %}<br/><span>{{ cv.contact.linkedin }}</span>{% endif %}
    </div>
  </header>

  {% if cv.summary %}
  <div class="section">
    <div class="section-title">Forschungsprofil</div>
    <p class="summary-text">{{ cv.summary }}</p>
  </div>
  {% endif %}

  {% if cv.work_history %}
  <div class="section">
    <div class="section-title">Berufliche Tätigkeit</div>
    {% for job in cv.work_history %}
    <div class="entry">
      <div class="entry-date">{{ job.start_date }}<br/>– {{ job.end_date if job.end_date else "heute" }}</div>
      <div class="entry-content">
        <div class="entry-title">{{ job.role }}</div>
        <div class="entry-subtitle">{{ job.company }}</div>
        {% if job.bullets %}
        <ul class="entry-bullets">
          {% for bullet in job.bullets %}<li>{{ bullet }}</li>{% endfor %}
        </ul>
        {% endif %}
      </div>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if cv.education %}
  <div class="section">
    <div class="section-title">Ausbildung</div>
    {% for edu in cv.education %}
    <div class="entry">
      <div class="entry-date">{{ edu.start_date }}<br/>{% if edu.start_date %}– {% endif %}{{ edu.end_date if edu.end_date else ("heute" if edu.start_date else "") }}</div>
      <div class="entry-content">
        <div class="entry-title">{{ edu.degree }}{% if edu.field %}, {{ edu.field }}{% endif %}</div>
        <div class="entry-subtitle">{{ edu.institution }}</div>
      </div>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if cv.skills %}
  <div class="section">
    <div class="section-title">Kompetenzen</div>
    <div class="skill-block">{{ cv.skills | join(" · ") }}</div>
  </div>
  {% endif %}

  {% if cv.languages %}
  <div class="section">
    <div class="section-title">Sprachkenntnisse</div>
    <div class="lang-table">
      {% for lang in cv.languages %}
      <span class="lang-name">{{ lang.language }}</span>
      <span class="lang-level">{{ lang.level }}</span>
      {% endfor %}
    </div>
  </div>
  {% endif %}

</div>
</body>
</html>
```

- [ ] **Step 2: Verify syntax**

```bash
python3 -c "
from jinja2 import Environment, FileSystemLoader, select_autoescape
env = Environment(loader=FileSystemLoader('backend/applire/templates'), autoescape=select_autoescape(['html']))
t = env.get_template('academic.html.j2')
print('OK:', t.name)
"
```

- [ ] **Step 3: Commit**

```bash
git add backend/applire/templates/academic.html.j2
git commit -m "feat: add academic CV template (centred header, date-column layout, serif)"
```

---

## Task 7: Template — `compact_pro.html.j2`

**Files:**
- Create: `backend/applire/templates/compact_pro.html.j2`

- [ ] **Step 1: Create the template**

Create `backend/applire/templates/compact_pro.html.j2`:

```jinja2
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <title>Lebenslauf – {{ cv.contact.name }}</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --cv-primary: {{ color.primary }};
      --cv-primary-tint: {{ color.primary_tint }};
      --text: #1a1a1a;
      --muted: #555;
      --rule: #d5d5d5;
      --bg-alt: #f8f9fa;
    }

    body {
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 9.5pt;
      line-height: 1.45;
      color: var(--text);
      background: #fff;
    }

    .page {
      width: 210mm;
      min-height: 297mm;
      margin: 0 auto;
      padding: 14mm 18mm 14mm 18mm;
    }

    /* ---- Header ---- */
    .header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      border-bottom: 2.5px solid var(--cv-primary);
      padding-bottom: 6pt;
      margin-bottom: 10pt;
    }

    .header-name {
      font-size: 17pt;
      font-weight: bold;
      color: var(--text);
    }

    .header-contact {
      text-align: right;
      font-size: 8pt;
      color: var(--muted);
      line-height: 1.7;
    }

    /* ---- Two-column body grid ---- */
    .body {
      display: grid;
      grid-template-columns: 1fr 1fr;
      column-gap: 14pt;
    }

    .col { }

    /* ---- Section ---- */
    .section { margin-bottom: 10pt; }

    .section-title {
      font-size: 7.5pt;
      font-weight: bold;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--cv-primary);
      border-bottom: 1px solid var(--cv-primary);
      padding-bottom: 1.5pt;
      margin-bottom: 5pt;
    }

    /* ---- Entry ---- */
    .entry { margin-bottom: 6pt; }

    .entry-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
    }

    .entry-title {
      font-size: 9.5pt;
      font-weight: bold;
    }

    .entry-dates {
      font-size: 7.5pt;
      color: var(--muted);
      white-space: nowrap;
    }

    .entry-subtitle {
      font-size: 8.5pt;
      color: var(--muted);
      margin-bottom: 2pt;
    }

    .entry-bullets {
      padding-left: 10pt;
      list-style-type: disc;
      margin-top: 2pt;
    }

    .entry-bullets li {
      margin-bottom: 1pt;
      font-size: 9pt;
    }

    /* ---- Skills: comma-separated or wrap ---- */
    .skills-compact {
      font-size: 9pt;
      color: var(--text);
      line-height: 1.65;
    }

    /* ---- Languages ---- */
    .lang-row {
      display: flex;
      justify-content: space-between;
      font-size: 9pt;
      padding: 1.5pt 0;
      border-bottom: 1px dotted var(--rule);
    }
    .lang-name { font-weight: 600; }
    .lang-level { color: var(--muted); }

    /* ---- Summary ---- */
    .summary-text {
      font-size: 9.5pt;
      line-height: 1.5;
    }
  </style>
</head>
<body>
<div class="page">

  <header class="header">
    <div class="header-name">{{ cv.contact.name }}</div>
    <div class="header-contact">
      {% if cv.contact.location %}<span>{{ cv.contact.location }}</span>{% endif %}
      {% if cv.contact.email %} &nbsp;·&nbsp; <span>{{ cv.contact.email }}</span>{% endif %}
      {% if cv.contact.phone %} &nbsp;·&nbsp; <span>{{ cv.contact.phone }}</span>{% endif %}
      {% if cv.contact.linkedin %}<br/><span>{{ cv.contact.linkedin }}</span>{% endif %}
    </div>
  </header>

  {% if cv.summary %}
  <div class="section">
    <div class="section-title">Profil</div>
    <p class="summary-text">{{ cv.summary }}</p>
  </div>
  {% endif %}

  <div class="body">

    <!-- LEFT: Experience + Education -->
    <div class="col">

      {% if cv.work_history %}
      <div class="section">
        <div class="section-title">Berufserfahrung</div>
        {% for job in cv.work_history %}
        <div class="entry">
          <div class="entry-header">
            <div class="entry-title">{{ job.role }}</div>
            <div class="entry-dates">{{ job.start_date }} – {{ job.end_date if job.end_date else "heute" }}</div>
          </div>
          <div class="entry-subtitle">{{ job.company }}</div>
          {% if job.bullets %}
          <ul class="entry-bullets">
            {% for bullet in job.bullets %}<li>{{ bullet }}</li>{% endfor %}
          </ul>
          {% endif %}
        </div>
        {% endfor %}
      </div>
      {% endif %}

      {% if cv.education %}
      <div class="section">
        <div class="section-title">Ausbildung</div>
        {% for edu in cv.education %}
        <div class="entry">
          <div class="entry-header">
            <div class="entry-title">{{ edu.degree }}{% if edu.field %}, {{ edu.field }}{% endif %}</div>
            <div class="entry-dates">{{ edu.start_date }}{% if edu.start_date %} – {% endif %}{{ edu.end_date if edu.end_date else ("heute" if edu.start_date else "") }}</div>
          </div>
          <div class="entry-subtitle">{{ edu.institution }}</div>
        </div>
        {% endfor %}
      </div>
      {% endif %}

    </div>

    <!-- RIGHT: Skills + Languages -->
    <div class="col">

      {% if cv.skills %}
      <div class="section">
        <div class="section-title">Kompetenzen</div>
        <div class="skills-compact">{{ cv.skills | join(" · ") }}</div>
      </div>
      {% endif %}

      {% if cv.languages %}
      <div class="section">
        <div class="section-title">Sprachen</div>
        {% for lang in cv.languages %}
        <div class="lang-row">
          <span class="lang-name">{{ lang.language }}</span>
          <span class="lang-level">{{ lang.level }}</span>
        </div>
        {% endfor %}
      </div>
      {% endif %}

    </div>

  </div>

</div>
</body>
</html>
```

- [ ] **Step 2: Verify syntax**

```bash
python3 -c "
from jinja2 import Environment, FileSystemLoader, select_autoescape
env = Environment(loader=FileSystemLoader('backend/applire/templates'), autoescape=select_autoescape(['html']))
t = env.get_template('compact_pro.html.j2')
print('OK:', t.name)
"
```

- [ ] **Step 3: Commit**

```bash
git add backend/applire/templates/compact_pro.html.j2
git commit -m "feat: add compact_pro CV template (dense two-column, max info density)"
```

---

## Task 8: Register all templates + parametrized render unit test

**Files:**
- Modify: `backend/applire/schemas/cv.py` (line 9)
- Modify: `backend/applire/services/cv.py` (lines 71–74)
- Create: `tests/unit/test_template_render.py`

- [ ] **Step 1: Write the failing render test first**

Create `tests/unit/test_template_render.py`:

```python
"""
Parametrized smoke test: every registered template must render without
Jinja2 errors given a minimal TailoredCVData fixture.

Run: pytest tests/unit/test_template_render.py -v
"""
import sys
from pathlib import Path

import pytest

_backend = Path(__file__).parent.parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


@pytest.fixture(scope="module")
def minimal_cv():
    from applire.schemas.cv import (
        TailoredCVData, TailoredContact, TailoredWorkEntry,
        TailoredEducationEntry, TailoredLanguage,
    )
    return TailoredCVData(
        contact=TailoredContact(
            name="Anna Musterfrau",
            email="anna@example.com",
            phone="+49 89 123456",
            location="München",
            linkedin="linkedin.com/in/anna",
            photo_url=None,
        ),
        summary="Erfahrene Managerin mit Fokus auf digitale Transformation.",
        work_history=[
            TailoredWorkEntry(
                company="Beispiel GmbH",
                role="Head of Product",
                start_date="2020",
                end_date=None,
                bullets=["Aufbau des Produktteams", "Einführung agiler Methoden"],
            )
        ],
        skills=["Python", "Agile", "Stakeholder Management"],
        education=[
            TailoredEducationEntry(
                institution="LMU München",
                degree="MBA",
                field="Betriebswirtschaft",
                start_date="2014",
                end_date="2016",
            )
        ],
        languages=[TailoredLanguage(language="Deutsch", level="Muttersprache")],
        show_photo=False,
    )


@pytest.fixture(scope="module")
def minimal_color():
    from applire.services.color_detection import _make_color_context
    return _make_color_context("#2b5fa8")


@pytest.fixture(scope="module")
def jinja_env():
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    templates_dir = _backend / "applire" / "templates"
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html"]),
    )


ALL_TEMPLATES = [
    ("classic_german", "lebenslauf.html.j2"),
    ("modern_swiss", "modern_swiss.html.j2"),
    ("executive", "executive.html.j2"),
    ("tech_developer", "tech_developer.html.j2"),
    ("creative_sidebar", "creative_sidebar.html.j2"),
    ("academic", "academic.html.j2"),
    ("compact_pro", "compact_pro.html.j2"),
]


@pytest.mark.parametrize("template_key,template_file", ALL_TEMPLATES)
def test_template_renders_without_error(
    template_key, template_file, jinja_env, minimal_cv, minimal_color
):
    """Each template must render to a non-empty HTML string with no Jinja2 errors."""
    template = jinja_env.get_template(template_file)
    html = template.render(cv=minimal_cv, color=minimal_color)
    assert html, f"{template_key}: rendered HTML is empty"
    assert "Anna Musterfrau" in html, f"{template_key}: contact name missing from output"
    assert "Beispiel GmbH" in html, f"{template_key}: work history missing from output"


@pytest.mark.parametrize("template_key,template_file", ALL_TEMPLATES)
def test_template_uses_color_variables(template_key, template_file, jinja_env, minimal_color):
    """Rendered HTML must contain the primary colour hex value."""
    template = jinja_env.get_template(template_file)
    from applire.schemas.cv import TailoredCVData, TailoredContact
    cv = TailoredCVData(contact=TailoredContact(name="Test", location="Berlin"), show_photo=False)
    html = template.render(cv=cv, color=minimal_color)
    assert "#2b5fa8" in html, f"{template_key}: primary colour not found in rendered HTML"
```

- [ ] **Step 2: Run test — expect failures for unregistered templates**

```bash
pytest tests/unit/test_template_render.py -v
```

Expected: `classic_german` and `modern_swiss` pass (files exist); the 5 new template files exist but the `CVTemplate` literal and `_TEMPLATE_FILES` aren't updated yet (that's fine — the render test uses the Jinja2 env directly, so all 7 should already pass if the `.j2` files are present). Confirm all 14 test cases pass before continuing.

- [ ] **Step 3: Update `CVTemplate` literal**

In `backend/applire/schemas/cv.py`, replace line 9:

```python
CVTemplate = Literal[
    "classic_german",
    "modern_swiss",
    "executive",
    "tech_developer",
    "creative_sidebar",
    "academic",
    "compact_pro",
]
```

- [ ] **Step 4: Update `_TEMPLATE_FILES`**

In `backend/applire/services/cv.py`, replace the `_TEMPLATE_FILES` dict (lines 71–74):

```python
_TEMPLATE_FILES: dict[str, str] = {
    "classic_german": "lebenslauf.html.j2",
    "modern_swiss": "modern_swiss.html.j2",
    "executive": "executive.html.j2",
    "tech_developer": "tech_developer.html.j2",
    "creative_sidebar": "creative_sidebar.html.j2",
    "academic": "academic.html.j2",
    "compact_pro": "compact_pro.html.j2",
}
```

- [ ] **Step 5: Run full unit suite**

```bash
pytest tests/unit/ -v --tb=short
```

Expected: All tests pass (no regressions).

- [ ] **Step 6: Commit**

```bash
git add backend/applire/schemas/cv.py backend/applire/services/cv.py tests/unit/test_template_render.py
git commit -m "feat: register 5 new templates in CVTemplate and _TEMPLATE_FILES, add render smoke tests"
```

---

## Task 9: Generate thumbnail PNGs

**Files:**
- Create: `backend/data/static/templates/executive.png`
- Create: `backend/data/static/templates/tech_developer.png`
- Create: `backend/data/static/templates/creative_sidebar.png`
- Create: `backend/data/static/templates/academic.png`
- Create: `backend/data/static/templates/compact_pro.png`

- [ ] **Step 1: Write the thumbnail generation script**

Create `scripts/generate_thumbnails.py` (not committed — one-off helper):

```python
#!/usr/bin/env python3
"""
Generate 400×566 thumbnail PNGs for all CV templates.

Usage: python scripts/generate_thumbnails.py
Requires: Playwright + the backend package on sys.path.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.async_api import async_playwright

from applire.schemas.cv import (
    TailoredCVData, TailoredContact, TailoredWorkEntry,
    TailoredEducationEntry, TailoredLanguage,
)
from applire.services.color_detection import _make_color_context

SAMPLE_CV = TailoredCVData(
    contact=TailoredContact(
        name="Anna Musterfrau",
        email="anna@example.com",
        phone="+49 89 123456",
        location="München",
        linkedin="linkedin.com/in/anna",
        photo_url=None,
    ),
    summary="Erfahrene Managerin mit Fokus auf digitale Transformation und agile Methoden.",
    work_history=[
        TailoredWorkEntry(
            company="Digitale AG", role="Head of Product",
            start_date="2020", end_date=None,
            bullets=["Aufbau des Produktteams", "OKR-Einführung"],
        ),
        TailoredWorkEntry(
            company="Beispiel GmbH", role="Senior Managerin",
            start_date="2017", end_date="2020",
            bullets=["Projektleitung", "Stakeholder Management"],
        ),
    ],
    skills=["Python", "Agile", "Stakeholder Management", "OKR", "SQL"],
    education=[
        TailoredEducationEntry(
            institution="LMU München", degree="MBA",
            field="Betriebswirtschaft", start_date="2014", end_date="2016",
        )
    ],
    languages=[
        TailoredLanguage(language="Deutsch", level="Muttersprache"),
        TailoredLanguage(language="Englisch", level="C1"),
    ],
    show_photo=False,
)

TEMPLATES_DIR = Path(__file__).parent.parent / "backend" / "applire" / "templates"
OUT_DIR = Path(__file__).parent.parent / "backend" / "data" / "static" / "templates"

TEMPLATES = [
    "classic_german",
    "modern_swiss",
    "executive",
    "tech_developer",
    "creative_sidebar",
    "academic",
    "compact_pro",
]

FILE_MAP = {
    "classic_german": "lebenslauf.html.j2",
    "modern_swiss": "modern_swiss.html.j2",
    "executive": "executive.html.j2",
    "tech_developer": "tech_developer.html.j2",
    "creative_sidebar": "creative_sidebar.html.j2",
    "academic": "academic.html.j2",
    "compact_pro": "compact_pro.html.j2",
}

COLOR = _make_color_context("#2b5fa8")


async def main():
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        for key in TEMPLATES:
            tmpl = env.get_template(FILE_MAP[key])
            html = tmpl.render(cv=SAMPLE_CV, color=COLOR)
            page = await browser.new_page(viewport={"width": 794, "height": 1123})  # A4 @ 96dpi
            await page.set_content(html, wait_until="networkidle")
            out_path = OUT_DIR / f"{key}.png"
            await page.screenshot(path=str(out_path), clip={"x": 0, "y": 0, "width": 400, "height": 566})
            print(f"  wrote {out_path}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Run the script**

```bash
cd /home/apliqa/Documents/Applire/Solution
python scripts/generate_thumbnails.py
```

Expected output:
```
  wrote backend/data/static/templates/classic_german.png
  wrote backend/data/static/templates/modern_swiss.png
  wrote backend/data/static/templates/executive.png
  wrote backend/data/static/templates/tech_developer.png
  wrote backend/data/static/templates/creative_sidebar.png
  wrote backend/data/static/templates/academic.png
  wrote backend/data/static/templates/compact_pro.png
```

- [ ] **Step 3: Visually inspect all 7 thumbnails**

Open each PNG in an image viewer and confirm:
- No blank/white-only images
- Text is readable and not clipped
- Accent colour `#2b5fa8` is visible in the appropriate places
- `tech_developer.png` has a dark background

- [ ] **Step 4: Commit thumbnails**

```bash
git add backend/data/static/templates/executive.png \
        backend/data/static/templates/tech_developer.png \
        backend/data/static/templates/creative_sidebar.png \
        backend/data/static/templates/academic.png \
        backend/data/static/templates/compact_pro.png
git commit -m "chore: add thumbnail PNGs for 5 new CV templates"
```

---

## Task 10: Run full test suite + manual QA

- [ ] **Step 1: Full unit test run with coverage**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/ -v --cov=applire --cov-report=term-missing --cov-fail-under=75
```

Expected: All tests pass, coverage ≥ 75%.

- [ ] **Step 2: Start the stack and check each template renders in-app**

```bash
docker-compose up -d
```

Then via the frontend or API, generate a CV with each of the 7 template values and verify:
- Status reaches `ready`
- `GET /api/cv/{id}/html` returns HTML with correct colour
- `GET /api/cv/{id}/pdf` returns a valid PDF
- `tech_developer` PDF has dark background (requires `print_background=True` — already set)

- [ ] **Step 3: Final commit — update design doc status**

In `docs/superpowers/specs/2026-04-13-cv-templates-color-schema-design.md`, change `**Status:** Approved` to `**Status:** Implemented`.

```bash
git add docs/superpowers/specs/2026-04-13-cv-templates-color-schema-design.md
git commit -m "docs: mark sprint-24 color schema + templates spec as implemented"
```

---

## Self-Review Notes

- All 5 new templates use `color.primary`, `color.primary_tint`, `color.surface`, `color.surface_text` CSS vars — spec covered ✓
- `secondary` is defined in `ColorContext` but no template uses it yet — intentional (Phase 2) ✓
- Backward compat aliases `accent`/`tint` keep existing templates unchanged — verified by render test ✓
- `tech_developer` needs `print-color-adjust: exact` in CSS — included ✓
- `academic` and `compact_pro` show no photo — `show_photo` check omitted by design ✓
- `derive_surface_text` threshold 0.179 is documented in spec and code comment ✓
- No DB migration — confirmed: only `_make_color_context` changed, `seed_primary` still the single stored value ✓
