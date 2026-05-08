# Skill Enrichment — Design Spec

**Date:** 2026-04-16
**Sprint:** TBD (next sprint after Sprint 27)
**Status:** Approved

---

## Problem

The Master Profile stores skills as a flat list with `proficiency` and `years_experience` fields that are either LLM-guessed or `null`. The `WorkEntry` schema already captures `technologies: list[str]` per role, but there is no bidirectional link between skills and the work entries that used them. This means:

- `years_experience` is unreliable — LLMs frequently leave it `null` or hallucinate a round number.
- `proficiency` is purely LLM-assigned with no grounding in actual career history.
- Downstream features (gap analysis, CV tailoring, interview question targeting) cannot distinguish a skill used briefly in one role from a skill used across a full career.

Additionally, the `upload_cv()` code path does not invoke the existing `review_and_refine()` layer that is already wired into the LinkedIn import path, leaving extracted CV data unreviewed.

---

## Goals

1. Calculate `years_experience` deterministically from `WorkEntry.technologies` date ranges where possible.
2. Estimate `years_experience` via a single batch LLM call for skills not found in any `technologies` list.
3. Derive `proficiency` from calculated years, using the LLM-extracted proficiency as a floor (never downgrade).
4. Record provenance on each `Skill` — which work entries contributed to the calculation.
5. Wire up the missing `review_and_refine()` call in `upload_cv()`.
6. Keep the enrichment data fresh: re-run after every import and after any patch to `work_experience` or `skills`.

---

## Non-Goals

- No new API endpoints — this is internal enrichment only.
- No database schema changes — all data is stored in the existing `profile_json` JSONB column.
- No UI changes in this sprint.
- No enrichment for `language` or `domain` category skills (time-based experience is not meaningful for these).

---

## Architecture

### New service: `backend/applire/services/skill_enrichment.py`

Single public async function:

```python
async def enrich_skills(
    profile: MasterProfileData,
    provider: LLMProvider,
) -> MasterProfileData:
```

Returns a new `MasterProfileData` with enriched `skills`. Does not mutate the input.

**Pipeline:**

```
MasterProfileData
      │
      ▼
1. Match phase (deterministic)
   For each Skill (category ∈ {technical, soft}):
     - Find all WorkEntry where skill.name in entry.technologies (case-insensitive)
     - Sum non-overlapping date ranges → years_experience (float → rounded int)
     - Derive calculated_proficiency from years thresholds
     - Apply floor: proficiency = max(calculated, existing)
     - Set work_entry_refs = [entry.company, ...]
     - Set source = "deterministic"
      │
      ▼
2. Estimation phase (LLM — one batch call)
   Unmatched skills (work_entry_refs still empty):
     - Single LLM call: full work history + unmatched skill names
     - LLM returns {skill_name: years_experience} dict
     - Apply floor rule same as deterministic path
     - Set source = "llm_estimated"
      │
      ▼
3. Return enriched MasterProfileData
```

### New prompt file: `backend/applire/prompts/skill_estimation.py`

System prompt instructs the LLM to:
- Return a JSON object mapping skill name → estimated integer years of experience.
- Base estimates only on the provided work history — no fabrication.
- Use `null` if there is genuinely no basis for estimation.

### New prompt file: `backend/applire/prompts/review_cv_extraction.py`

The existing `review_profile_extraction.py` reviewer uses `work_history` field terminology (the legacy LinkedIn import schema). The `upload_cv()` path extracts to `work_experience`. A separate reviewer prompt is required for the CV upload path — structurally identical in intent but referencing `work_experience`, `responsibilities`, `achievements`, and `technologies` as the field names to audit.

### Schema change: `backend/applire/schemas/profile.py`

Add one field to `Skill`:

```python
work_entry_refs: list[str] = Field(default_factory=list)
```

Stores the `company` names of `WorkEntry` records that contributed to the deterministic calculation. Empty for `llm_estimated` and unprocessed skills. Backwards-compatible — existing JSONB records load cleanly (missing field defaults to `[]`).

No Alembic migration required.

---

## Proficiency Thresholds (deterministic path)

| Calculated years | Level |
|---|---|
| < 1 | basic |
| 1 – 3 | intermediate |
| 3 – 6 | advanced |
| ≥ 6 | expert |

**Floor rule:** `proficiency = max(calculated_proficiency, existing_proficiency)` using rank order `basic < intermediate < advanced < expert`. The LLM-extracted proficiency is never lowered by the calculation.

---

## Date Range Calculation

Input: a list of `WorkEntry` records matched to a skill.

Rules:
- Partial dates (`"2020"`, `"2020-01"`) are expanded to first-of-month: `"2020"` → `2020-01-01`, `"2020-06"` → `2020-06-01`.
- `end_date: null` means the role is current → use today's date.
- Overlapping ranges are merged before summing (a skill used at two concurrent jobs is not double-counted).
- Result is a float in years, rounded to nearest integer (minimum 1 if any match exists, to avoid `years_experience: 0`).

---

## Integration Points

### `upload_cv()` — `services/profile/__init__.py` step 3

**Before (current):**
```python
data = await provider.aparse_json(prompt, system=system, ...)
incoming = MasterProfileData.model_validate(data)
```

**After:**
```python
data = await provider.aparse_json(prompt, system=system, ...)
# Wire up missing review layer using the CV-extraction-specific reviewer prompt
# (not the LinkedIn/profile_extraction reviewer — field names differ)
data = await review_and_refine(
    source=raw_text,
    draft=data,
    generator_prompt_fn=_build_cv_extraction_retry_prompt,
    generator_system=system,
    reviewer_prompt_fn=_build_cv_extraction_review_prompt,
    reviewer_system=CV_EXTRACTION_REVIEW_SYSTEM_PROMPT,
    provider=provider,
    max_retries=LLM_REVIEW_MAX_RETRIES,
    generator_max_tokens=8192,
)
incoming = MasterProfileData.model_validate(data)
incoming = await enrich_skills(incoming, provider)
```

The generator retry prompt (`_build_cv_extraction_retry_prompt`) mirrors the existing `build_retry_prompt` in `profile_extraction.py` but references `work_experience` terminology.

### `_import_from_text()` — `services/profile/__init__.py`

After existing `review_and_refine()` call, before merge:
```python
incoming = MasterProfileData.model_validate(data)
incoming = await enrich_skills(incoming, provider)
```

### `patch_profile_section()` — `services/profile/__init__.py`

Add optional `provider: LLMProvider | None = None` parameter.

When `section in {"work_experience", "skills"}` and `provider` is not `None`, re-run enrichment on the full profile after the patch is applied:
```python
if section in {"work_experience", "skills"} and provider is not None:
    validated = await enrich_skills(validated, provider)
```

When `provider is None`, the patch applies without enrichment (backwards-compatible for callers that don't pass a provider — enrichment will run on the next import).

### Patch router endpoint — `routers/profile.py`

Add `provider: LLMProvider = Depends(_get_provider)` to the `patch_section` handler and thread it through to `patch_profile_section()`.

---

## File Map

| File | Action |
|---|---|
| `backend/applire/schemas/profile.py` | Add `work_entry_refs` to `Skill` |
| `backend/applire/services/skill_enrichment.py` | Create — match, calculate, estimate, tag |
| `backend/applire/prompts/skill_estimation.py` | Create — batch LLM estimation prompt |
| `backend/applire/prompts/review_cv_extraction.py` | Create — reviewer + retry prompts for `work_experience` schema |
| `backend/applire/services/profile/__init__.py` | Wire enrichment + review into `upload_cv()`, `_import_from_text()`, `patch_profile_section()` |
| `backend/applire/routers/profile.py` | Add provider dep to patch endpoint |
| `tests/unit/test_skill_enrichment.py` | Create — unit tests |

---

## Testing

### Unit tests (`tests/unit/test_skill_enrichment.py`)

- Date range calculation: overlapping ranges, null end dates, partial dates (`"2020"` vs `"2020-06"`), single entry, empty list.
- Proficiency floor: calculated > existing, calculated < existing, equal.
- Skill matching: case-insensitive match, no match, multiple entries matched.
- Batch estimation call: mock LLM response, verify `source = "llm_estimated"` and floor applied.
- Enrichment skips language/domain category skills.

### Integration

Existing `upload_cv` integration tests cover the happy path — no new integration tests required. The review layer fix in `upload_cv()` is covered by the existing test that mocks `review_and_refine`.

---

## Architecture Documentation

- **ADR**: New ADR entry — "Skill experience calculation: deterministic + LLM hybrid"
- **arc42**: Update section 8 (Concepts) to document the skill enrichment pipeline and the `work_entry_refs` provenance field.

---

## Open Questions

None — all design decisions resolved during brainstorming.
