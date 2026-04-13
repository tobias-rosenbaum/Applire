# Sprint 15 — Smart Gap Interview

**Date:** 2026-04-08  
**Status:** Approved  
**Features:** Multi-question per gap · Cross-gap resolution · Expanded profile enrichment

---

## Overview

Three improvements to the gap interview (MODE A — Targeted Gap-Fill):

1. **Multi-question per gap** — if a user's answer doesn't fully address a gap, the LLM asks a smarter follow-up that probes adjacent domains rather than re-asking the same question.
2. **Cross-gap resolution** — if a user's answer implicitly resolves other thematically related gaps, those gaps are marked as addressed and skipped.
3. **Expanded profile enrichment** — answers are mined for certifications, languages, and education (in addition to the existing skills + work history) and merged into the master profile.

All three features share a single LLM call per turn (the `ResponseParser`). No additional round-trips are introduced.

---

## 1. State & Configuration

### New constants (`backend/applire/constants.py`)

```python
import os

INTERVIEW_MAX_QUESTIONS_PER_GAP: int = int(
    os.environ.get("INTERVIEW_MAX_QUESTIONS_PER_GAP", "3")
)
```

- Configurable via environment variable for Docker self-hosters (set in `.env` / `docker-compose.yml`).
- Defaults to `3`. The existing hard session ceilings (`INTERVIEW_HARD_CEILING_TARGETED = 12`, `INTERVIEW_HARD_CEILING_GUIDED = 20`) remain architectural constants and are **not** env-var-backed.
- The total session ceiling always wins: if `questions_asked >= hard_ceiling`, the session ends regardless of per-gap state.

### New `InterviewState` fields (`backend/applire/schemas/session.py`)

```python
class InterviewState(TypedDict):
    # ... existing fields unchanged ...
    questions_per_gap: dict  # gap_str → int (questions asked for that gap so far)
    skipped_gaps: list[str]  # gaps resolved transitively by a cross-gap answer
```

Both fields are optional with defaults (`{}` / `[]`) — existing sessions missing these keys behave identically to today.

---

## 2. ResponseParser — Extended Schema

The `ResponseParser` is the only LLM node changed. All three features are served by a single updated schema.

### New JSON schema (`backend/applire/prompts/interview.py`)

```json
{
  "skills_to_add": ["list of concrete skills explicitly mentioned"],
  "work_history_to_add": [
    {
      "company": "Company name or null",
      "role": "Job title or null",
      "start_date": "YYYY-MM or YYYY or null",
      "end_date": "YYYY-MM or YYYY or null (null = current)",
      "bullets": ["achievement or responsibility mentioned"]
    }
  ],
  "certifications_to_add": [
    {"name": "Certification name", "issuing_body": "Issuing body or null", "year": "YYYY or null"}
  ],
  "languages_to_add": [
    {"language": "Language name", "level": "native|fluent|professional|basic"}
  ],
  "education_to_add": [
    {
      "institution": "Institution name",
      "degree": "Degree title",
      "field": "Field of study or null",
      "graduation_year": "YYYY or null"
    }
  ],
  "gap_resolution": "full | partial | none",
  "follow_up_hint": "Suggested adjacent domain or null — used only when gap_resolution != full",
  "gaps_also_addressed": ["list of other open gaps this answer also resolves"]
}
```

### Semantics

| Field | Meaning |
|---|---|
| `gap_resolution` | `full` = concrete answer that addresses the gap; `partial` = something relevant but incomplete; `none` = vague, off-topic, or empty |
| `follow_up_hint` | Short instruction for the follow-up QuestionGenerator, e.g. `"ask about GMP or other regulated manufacturing environments"`. `null` when `gap_resolution == "full"`. |
| `gaps_also_addressed` | Other open gaps (from `remaining_gaps` context) that this answer also resolves. Empty list when none. |

### Backward compatibility

The existing `gap_addressed: bool` return value from `response_parser()` is **derived** in code as `gap_resolution != "none"` and kept in the returned dict. No existing callers break.

### Signature change

```python
async def response_parser(
    gap: str,
    question: str,
    answer: str,
    provider: LLMProvider,
    remaining_gaps: list[str] | None = None,   # NEW — open gaps for cross-gap context
) -> dict:
```

`remaining_gaps` is included in the prompt so the LLM can identify `gaps_also_addressed`. For regular sessions, this is `critical_gaps[current_gap_index + 1:]` filtered against `skipped_gaps`. For micro-sessions, this is the full gap list from the gap analysis.

---

## 3. Feature 1 — Multi-Question Per Gap

### New prompt builder (`backend/applire/prompts/interview.py`)

```python
FOLLOW_UP_QUESTION_SYSTEM_PROMPT = """\
You are an expert career coach specialised in the DACH job market.
The candidate has not yet fully addressed a specific gap in their profile.
Do NOT re-ask the original question. Instead, probe an adjacent domain or analogous
context that is likely to surface the missing experience indirectly.

Requirements:
- Lead with the adjacent domain suggested in the follow-up hint
- Be concrete: name the technology, regulation, industry, or context to explore
- Remain encouraging — the candidate may simply not have recognised the connection
- Output ONLY the question text — no preamble, no numbering, no explanation"""

def build_follow_up_question_prompt(
    gap: str,
    follow_up_hint: str,
    profile: dict,
    recent_messages: list[dict],
    gap_category: str | None = None,
) -> str: ...
```

The system prompt instructs the LLM to **probe an adjacent domain** rather than re-ask the original question. The `follow_up_hint` (e.g. "ask about GMP or other regulated manufacturing environments") is the primary driver of the question direction.

### Updated `question_generator_with_profile` signature

```python
async def question_generator_with_profile(
    state: InterviewState,
    profile: dict,
    provider: LLMProvider,
    gap_category: str | None = None,
    job_context: dict | None = None,
    follow_up_hint: str | None = None,   # NEW
) -> str:
```

When `follow_up_hint` is present, routes to `build_follow_up_question_prompt` instead of the standard gap question prompt.

### Advance logic in `send_message` (`backend/applire/services/session.py`)

```
gap_resolution = patch["gap_resolution"]
questions_for_this_gap = state["questions_per_gap"].get(current_gap, 1)

if gap_resolution == "full" OR questions_for_this_gap >= MAX_QUESTIONS_PER_GAP:
    → advance current_gap_index (existing behaviour)
else:
    → state["questions_per_gap"][current_gap] = questions_for_this_gap + 1
    → call question_generator_with_profile(..., follow_up_hint=patch["follow_up_hint"])
    → stay on current_gap_index
    → return next question (complete=False)
```

`questions_per_gap` is initialised as `{}` in `_build_state()` when the session is created. The default `.get(current_gap, 1)` handles the first answer (the initial question counts as 1). With `MAX_QUESTIONS_PER_GAP=3`, this allows the initial question plus up to 2 follow-ups before the gap is force-advanced. The follow-up path still increments `questions_asked` and checks against the session hard ceiling.

---

## 4. Feature 2 — Cross-Gap Resolution

### In `send_message`

After `response_parser` returns, before advancing the index:

```python
for also_gap in patch.get("gaps_also_addressed", []):
    if (
        also_gap in state["critical_gaps"]
        and also_gap != current_gap
        and also_gap not in state["addressed_gaps"]
        and also_gap not in state["skipped_gaps"]
    ):
        state["skipped_gaps"].append(also_gap)
        state["addressed_gaps"].append(also_gap)
```

### Advancing past skipped gaps

A helper `_next_valid_index(critical_gaps, from_index, skipped_gaps)` returns the next index whose gap is not in `skipped_gaps`. `gaps_remaining` is recomputed using this helper.

### API response

`SessionMessageResponse` gains one new optional field:

```python
gaps_also_addressed: list[str] | None = None
```

This is populated whenever the cross-gap list is non-empty, for UI / MCP feedback ("your answer also addressed: GMP certification").

### Micro-session behaviour

For micro-sessions, `remaining_gaps` passed to `response_parser` is the full open gap list from the gap analysis (not just the one targeted gap). Cross-addressed gaps cannot be "skipped" within the same micro-session (there is no next question), but:

1. Profile enrichment (Feature 3) persists any extracted data for those gaps.
2. `gaps_also_addressed` is returned in the response so the UI can surface the information.
3. The next gap analysis (run at the start of the next full session) will reflect the updated profile and may reclassify those gaps as resolved.

---

## 5. Feature 3 — Expanded Profile Enrichment

### Updated `profile_updater` (`backend/applire/services/interview_graph.py`)

Three new merge rules, following the same accumulate-never-overwrite pattern as skills:

**Certifications** — append if `name` (case-insensitive) not already present:
```python
existing_cert_names = {c.get("name", "").lower() for c in profile.get("certifications", [])}
new_certs = [c for c in patch.get("certifications_to_add", [])
             if c.get("name", "").lower() not in existing_cert_names]
if new_certs:
    profile["certifications"] = list(profile.get("certifications", [])) + new_certs
```

**Languages** — append if language not present; keep existing level if already there:
```python
existing_langs = {l.get("language", "").lower() for l in profile.get("languages", [])}
new_langs = [l for l in patch.get("languages_to_add", [])
             if l.get("language", "").lower() not in existing_langs]
if new_langs:
    profile["languages"] = list(profile.get("languages", [])) + new_langs
```

**Education** — append if `(institution, degree)` pair (case-insensitive) not already present:
```python
existing_edu = {
    (_norm(e.get("institution")), _norm(e.get("degree")))
    for e in profile.get("education", [])
}
new_edu = [e for e in patch.get("education_to_add", [])
           if (_norm(e.get("institution")), _norm(e.get("degree"))) not in existing_edu]
if new_edu:
    profile["education"] = list(profile.get("education", [])) + new_edu
```

---

## 6. Data Flow Summary

```
POST /api/session/{id}/message
  │
  ├─ done-signal check (pre-LLM, unchanged)
  │
  ├─ ResponseParser(gap, question, answer, remaining_gaps)
  │     → gap_resolution, follow_up_hint
  │     → gaps_also_addressed
  │     → skills/work/certifications/languages/education to add
  │
  ├─ ProfileUpdater (extended — 5 merge rules)
  │     → persists to MasterProfile.profile_json
  │
  ├─ Cross-gap resolution
  │     → updates skipped_gaps + addressed_gaps in state
  │
  ├─ Advance decision
  │     gap_resolution==full OR questions_per_gap[gap] >= MAX?
  │       YES → advance index, skip skipped_gaps, next gap
  │       NO  → increment counter, generate follow-up question
  │
  └─ Response (SessionMessageResponse)
        complete | question | gaps_remaining | gaps_also_addressed
```

---

## 7. Files Changed

| File | Change |
|---|---|
| `backend/applire/constants.py` | Add `INTERVIEW_MAX_QUESTIONS_PER_GAP` (env-var backed) |
| `backend/applire/schemas/session.py` | Add `questions_per_gap`, `skipped_gaps` to `InterviewState`; add `gaps_also_addressed` to `SessionMessageResponse` |
| `backend/applire/prompts/interview.py` | Extend `RESPONSE_PARSER_SYSTEM_PROMPT` + `build_response_parser_prompt`; add `FOLLOW_UP_QUESTION_SYSTEM_PROMPT` + `build_follow_up_question_prompt` |
| `backend/applire/services/interview_graph.py` | Extend `response_parser` (new fields + `remaining_gaps`); extend `profile_updater` (3 new merge rules); extend `question_generator_with_profile` (`follow_up_hint`) |
| `backend/applire/services/session.py` | Update `send_message` (advance logic, cross-gap resolution, follow-up routing); update micro-session to pass full gap list as `remaining_gaps`; add `questions_per_gap: {}` and `skipped_gaps: []` to `_build_state()` |
| `tests/unit/` | New unit tests for all changed functions |

No database migrations required — `InterviewState` is stored as JSONB; new fields are optional with defaults.

---

## 8. Testing

### Unit tests (no Docker)

- `response_parser`: mocked LLM returns for each `gap_resolution` value; `gaps_also_addressed` populated correctly; new profile fields extracted.
- `profile_updater`: certifications/languages/education merge rules; deduplication; no overwrite of existing entries.
- `send_message` follow-up path: `gap_resolution=partial` stays on same gap; counter increments; `follow_up_hint` routed correctly.
- `send_message` follow-up ceiling: after `MAX_QUESTIONS_PER_GAP` follow-ups, gap is advanced regardless.
- `send_message` cross-gap: `gaps_also_addressed` gaps appear in `skipped_gaps`; index advances past them; `gaps_remaining` reflects skips.
- Micro-session cross-gap: `gaps_also_addressed` returned in response; profile enriched.

### Existing tests

All existing unit and E2E tests remain unaffected. The new behaviour only activates when the LLM returns `gap_resolution != "full"` or `gaps_also_addressed` is non-empty — mocked tests return the previous schema subset and remain valid.

---

## 9. Out of Scope

- MODE B (Guided Build) is unchanged — multi-question logic, cross-gap, and extended enrichment apply to MODE A only.
- No frontend changes required — the new `gaps_also_addressed` field in the response is optional and additive.
- No changes to the gap analysis pipeline or the flow orchestrator.
