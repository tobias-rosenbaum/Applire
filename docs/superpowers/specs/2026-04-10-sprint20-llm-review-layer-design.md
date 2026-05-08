# Design Spec: LLM Review Layer (Sprint 20)
**Date:** 2026-04-10  
**Status:** Approved  
**ADR:** ADR-021

---

## Problem

User acceptance testing in Sprint 19 revealed two hallucination classes:

1. **Profile extraction** — a single work entry was extracted three times: once correctly, twice as ghost variants with fabricated dates and no source basis. These propagated into downstream artifacts including the tailored CV.
2. **CV tailoring** — the tailoring agent produced bullet points that matched the job description but had no basis in the candidate's CV or interview answers.

Both failures stem from single-shot LLM calls with no grounding verification. Outputs are trusted and persisted immediately.

---

## Scope

Sprint 20 applies the review layer to:
- `services/profile.py` — profile extraction from uploaded CV
- `services/cv.py` — CV tailoring

JD analysis, gap analysis, and interview response parsing remain single-shot (lower hallucination risk, addressed in a future sprint if evidence warrants).

---

## Architecture

### Core: `services/reviewer.py`

Single public function:

```python
async def review_and_refine(
    source: str,
    draft: dict,
    generator_prompt_fn: Callable[[str, dict, str], str],
    generator_system: str,
    reviewer_prompt_fn: Callable[[str, dict], str],
    reviewer_system: str,
    provider: LLMProvider,
    max_retries: int,
) -> dict:
```

**Loop logic:**
1. Call reviewer with `(source, draft)` → `{ "approved": bool, "issues": [str], "feedback": str }`
2. If `approved=true` or `max_retries` exhausted → return current draft (log warning if exhausted)
3. Otherwise call generator with `(source, draft, feedback)` → new draft → go to 1

On retry exhaustion the last draft is returned — never raises. A `WARNING` log records the outstanding issues for observability.

When `max_retries=0` the function returns the draft immediately without any LLM calls.

### Reviewer output schema

```json
{
  "approved": true,
  "issues": [],
  "feedback": ""
}
```

```json
{
  "approved": false,
  "issues": ["work_history[1] (Acme GmbH, 2021-03) has no basis in source text"],
  "feedback": "Remove work_history entries at index 1 and 2 — duplicates of index 0 with fabricated dates."
}
```

The schema is intentionally minimal. Per-issue severity and reviewer-proposed corrections are explicitly deferred (see ADR-021).

---

## New Files

### `backend/applire/services/reviewer.py`
Generic retry loop. No domain knowledge — domain is entirely in the prompts.

### `backend/applire/prompts/review_profile_extraction.py`
Exports:
- `REVIEW_SYSTEM_PROMPT` — instructs the reviewer to check for fabricated/duplicated work entries
- `build_review_prompt(raw_cv_text, extracted_json) -> str`

Reviewer checks:
- All work entries appear exactly once in the source text
- Company names, roles, and dates match verbatim
- No entry without a corresponding source passage

### `backend/applire/prompts/review_cv_tailoring.py`
Exports:
- `REVIEW_SYSTEM_PROMPT` — instructs the reviewer to check all claims against the master profile and interview answers
- `build_review_prompt(source_material, tailored_json) -> str`

Source material = master profile JSON + interview answers serialised to string.

Reviewer checks:
- All companies, roles, dates exist verbatim in the master profile
- No bullet claims a technology, achievement, or project absent from profile or interview answers
- Keyword gaps incorporated only where the profile provides plausible supporting evidence

### Retry prompts (added to existing prompt files)

Each existing generator prompt file gains a `build_retry_prompt(source, previous_draft, feedback) -> str` function. The retry variant prepends the reviewer's `feedback` explicitly: *"A review identified the following issues with your previous output. Correct them."*

- `prompts/profile_extraction.py` → `build_retry_prompt`
- `prompts/cv_tailoring.py` → `build_retry_prompt`

---

## Configuration

`backend/applire/constants.py`:
```python
LLM_REVIEW_MAX_RETRIES: int = int(os.getenv("LLM_REVIEW_MAX_RETRIES", "2"))
```

`docker-compose.yml` — commented env var with default documented:
```yaml
# LLM_REVIEW_MAX_RETRIES=2  # max reviewer retry passes per LLM step (0 = disabled)
```

---

## Integration Points

### `services/profile.py` — `_import_from_text()`

```python
# Current:
data: dict = await provider.aparse_json(build_user_prompt(raw_text), system=SYSTEM_PROMPT)

# Sprint 20:
data: dict = await provider.aparse_json(build_user_prompt(raw_text), system=SYSTEM_PROMPT)
data = await review_and_refine(
    source=raw_text,
    draft=data,
    generator_prompt_fn=build_retry_prompt,
    generator_system=SYSTEM_PROMPT,
    reviewer_prompt_fn=build_review_prompt,
    reviewer_system=REVIEW_SYSTEM_PROMPT,
    provider=provider,
    max_retries=LLM_REVIEW_MAX_RETRIES,
)
```

### `services/cv.py` — `_render_cv_background()`

`tailored_raw` passes through `review_and_refine()` before `TailoredCVData.model_validate(tailored_raw)`. Source material = master profile JSON + interview session answers serialised to a single string.

No schema changes. No new DB columns. No API surface changes.

---

## Testing

### Unit tests (`tests/unit/test_reviewer.py`)
- Approves first pass → draft returned unchanged, 1 reviewer call
- Rejects once then approves → 2 generator calls, 2 reviewer calls
- Always rejects → exhausts retries, returns last draft, warning logged
- `max_retries=0` → draft returned immediately, 0 LLM calls

### Unit tests (`tests/unit/test_review_prompts.py`)
- Smoke: `build_review_prompt()` and `build_retry_prompt()` render without error for fixture inputs
- Both profile extraction and CV tailoring variants covered

### Existing tests
No changes required. Existing unit tests mock `provider.aparse_json` and do not call `review_and_refine()`. Integration tests exercise the full loop via the mock LLM provider.

No new E2E tests — the existing happy-path E2E covers profile import and CV generation end-to-end.

---

## Prompt Hardening

Before the review layer runs, the generator prompts are hardened to reduce the probability of hallucinations reaching the reviewer at all. This reduces retries and token cost.

### `prompts/profile_extraction.py`

**Issues in current prompt:**
- No deduplication instruction — nothing prevents the same position from being output multiple times
- No explicit rule that missing data must be `null`, not inferred
- User prompt carries no grounding reminder

**Changes:**
- Add a `STRICT EXTRACTION RULES` preamble (4 rules) to `SYSTEM_PROMPT`:
  1. Each employer position must appear exactly once — merge if seen under multiple headings
  2. Extract only information explicitly present in the source; missing fields → `null`
  3. Bullets must be copied or closely paraphrased from what is stated — no inferred responsibilities
  4. Count distinct positions before writing `work_history`; output must contain exactly that many entries
- Strengthen `build_user_prompt()` to echo the key constraints as a one-line reminder

### `prompts/cv_tailoring.py`

**Issues in current prompt:**
- Rule 3: "only add skills the candidate *plausibly has* based on their history" — explicitly permits inference, which is what caused the invented passages
- Rule 1: "Rewrite work experience bullets" — "rewrite" is ambiguous; the model interpreted it as licence to write from scratch
- Rule 1: "Quantify where the candidate's data *allows* it" — "allows" is ambiguous; model inferred metrics not in the source
- Rule 5 protects only company names, dates, and degrees — not bullets, technologies, achievements, or metrics
- No entry-count constraint on `work_history`

**Changes:**
- Rule 1: Change to "Rephrase and re-emphasise bullets already in CANDIDATE PROFILE … Do NOT add new achievements, technologies, projects, or metrics that are not explicitly present in CANDIDATE PROFILE. Quantify only where CANDIDATE PROFILE explicitly provides numbers or metrics."
- Rule 3: Change "plausibly has" to "explicitly demonstrated in the candidate's work history or skills list. If a keyword gap has no explicit basis in the profile, omit it."
- Rule 5: Expand to cover all factual claims: "company names, roles, dates, degrees, technologies, project names, and metrics. Do NOT invent, infer, or embellish ANY fact not present in CANDIDATE PROFILE. When in doubt, leave it out."
- Add new rule: "The number of `work_history` entries in your output must equal exactly the number in CANDIDATE PROFILE. Do not add, remove, or split entries."

Both prompt files increment their `# Prompt version` comment to `v2`.

---

## Non-Goals (Sprint 20)

- Per-issue severity in reviewer output (deferred, see ADR-021)
- Reviewer-proposed corrections as fallback (deferred, see ADR-021)
- Review layer on JD analysis, gap analysis, or interview response parsing
- UI surfacing of review warnings or issue lists
