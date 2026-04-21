# Profile Enrichment — Design Spec
**Date:** 2026-04-21  
**Status:** Approved  
**Sprint:** TBD

---

## Overview

Add a conversational enrichment feature to the master profile view. The system detects completeness gaps in the user's profile (missing achievements, team sizes, budget context, professional summary) and conducts a targeted chat session to fill them. The user can mark any gap as N/A to permanently dismiss it from future scans.

---

## Entry Points

Two triggers on `/profile`, both open the same enrichment drawer:

1. **Completeness banner** — shown at the top of the profile page when gaps exist. Displays overall completeness score (%), a progress bar, gap count, and an "Enrich Profile" button. Triggers a full-profile enrichment session (no scope).

2. **Per-entry Enrich button** — shown on each work experience entry that has gaps, alongside a gap count badge (e.g. "⚠ 3 gaps"). Triggers a scoped session limited to that entry.

Complete entries show a green checkmark. Entries with no gaps get no button.

---

## Enrichment Drawer (UI)

A right-side ShadCN `Sheet` component. The profile page remains partially visible and dimmed behind it.

**Header:** Feature name, current scope label (entry name or "Full Profile"), close button.

**Left panel — gap list:**
- All gaps for the session, each showing field name and entry context
- Status indicators: `active` (current), pending, done, N/A
- Active gap highlighted in blue
- N/A gaps shown struck-through and dimmed

**Right panel — chat:**
- Applire's question displayed with a left blue border
- User replies shown right-aligned
- Input area at the bottom with: text field, Skip button, Mark N/A button, Send button
- On session completion: success state shown briefly, drawer closes, profile page re-fetches

**State (component-local):** `sessionId`, `gaps: GapItem[]`, `messages: Message[]`, `done: boolean`. No URL routing change — the drawer lives on the existing `/profile` page.

---

## Backend Architecture

### Approach

Extend the existing 4-node interview graph with a new Mode C. Add dedicated HTTP endpoints for the enrichment session lifecycle. The existing `/api/session` flow is untouched.

### New function: `gap_detector_mode_c(profile: dict) -> list[str]`

Added to `backend/applire/services/interview_graph.py` alongside the existing `gap_detector` (Mode A) and `gap_detector_mode_b` (Mode B).

Scans the profile JSONB for completeness gaps. Pure deterministic Python — no LLM call, no reviewer needed.

**Fields scanned (priority order):**
1. `WorkEntry.achievements` — empty list → gap
2. `WorkEntry.team_size` — None → gap  
3. `WorkEntry.budget_managed` — None → gap
4. `WorkEntry.industry_context` — None → gap
5. `professional_summary` — empty/None → gap

Fields listed in `profile_json._meta.na_fields` are excluded from the scan.

**Output format:** ordered `list[str]`, e.g.:
```
["achievements: Product Lead @ Beta GmbH",
 "team_size: Product Lead @ Beta GmbH",
 "achievements: Dev @ Gamma Corp",
 "professional_summary"]
```

These strings are consumed by the existing `QuestionGenerator` and `ResponseParser` nodes unchanged.

**Scoped sessions:** when `scope` is provided (e.g. `"work_experience:Beta GmbH:Product Lead"`), only gaps for that entry are included.

### Reviewer integration

The `ResponseParser` node is wrapped with `review_and_refine()` for all Mode C sessions.

Two new prompts added to `backend/applire/prompts/`:
- `review_interview_response.py` — `RESPONSE_PARSER_REVIEW_SYSTEM_PROMPT` and `build_response_parser_review_prompt(gap, question, answer, draft)`

The reviewer checks: are the extracted achievements concrete and accurate? Is structured data (team_size, budget_managed) correctly typed? Does the draft faithfully reflect what the user said?

Max retries read from the existing `LLM_REVIEW_MAX_RETRIES` env var (default: 2). On retry exhaustion, the last draft is accepted and a WARNING is logged — consistent with the existing reviewer behaviour (ADR-021).

### Session schema changes

`SessionCreateRequest.mode` gains `"profile_enrich"` as a valid literal:
```python
mode: Literal["targeted", "guided", "profile_enrich"] | None = None
```

`InterviewState` gains one new field:
```python
na_gaps: list[str]  # gaps explicitly dismissed by the user as N/A
```

The existing `skipped_gaps` field (cross-resolved gaps) is unchanged.

### New endpoints

Added to a new `backend/applire/routers/profile_enrich.py` router (registered in `main.py`). `profile.py` is already large; keeping enrich endpoints in their own file is cleaner.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/profile/enrich/start` | Create Mode C session. Body: `{ scope?: string }`. Returns `{ session_id, first_question, gaps: GapItem[], estimated_questions }` |
| `POST` | `/api/profile/enrich/{id}/respond` | Submit answer. Runs ResponseParser → reviewer → ProfileUpdater → QuestionGenerator (next gap). Returns `{ next_question?, gaps, done }` |
| `POST` | `/api/profile/enrich/{id}/skip` | Advance past current gap without answering. Returns next question or done |
| `POST` | `/api/profile/enrich/{id}/na` | Mark current gap as N/A. Persists to `profile_json._meta.na_fields`. Returns next question or done |

Sessions persist in the existing `interview_sessions` table with the existing 30-day GDPR TTL. No Alembic migration required.

### Profile metadata

N/A decisions are written to `profile_json._meta.na_fields: list[str]` — a top-level `_meta` key in the JSONB. Never rendered in CVs. Excluded from future `gap_detector_mode_c` scans. Covered by existing GDPR retention rules automatically.

---

## New / Changed Files

| File | Change |
|---|---|
| `backend/applire/services/interview_graph.py` | Add `gap_detector_mode_c()` |
| `backend/applire/schemas/session.py` | Add `"profile_enrich"` mode literal; add `na_gaps` to `InterviewState` |
| `backend/applire/prompts/review_interview_response.py` | New — reviewer prompts for ResponseParser |
| `backend/applire/routers/profile_enrich.py` | New — four enrich endpoints, registered in `main.py` |
| `frontend/app/profile/page.tsx` | Add completeness banner; add per-entry gap badge + Enrich button |
| `frontend/components/profile/EnrichmentDrawer.tsx` | New — Sheet with gap list + chat panels |
| `frontend/lib/enrich.ts` | New — API client for the four enrich endpoints |

---

## Testing

**Unit tests (`tests/unit/`):**
- `gap_detector_mode_c` with fixture profiles: assert correct gaps detected, correct priority order, N/A fields excluded, scoped sessions return only matching entry gaps
- Reviewer-wrapped `response_parser`: mock provider returning low-quality draft, assert retry loop triggers; mock approval, assert single pass

**E2E (`tests/e2e/`):**
- Start enrichment session, answer two questions, assert achievements written to profile
- Mark one gap N/A, start new session, assert that gap absent from gap list

---

## Architecture Notes

- The four-node graph topology is unchanged (ADR-004 stands). Mode C is a third entry into the GapDetector node only.
- The reviewer wraps the ResponseParser call in the enrich endpoint handler — not inside `interview_graph.py` itself — keeping the graph nodes pure and independently testable.
- `_meta` in `profile_json` is intentionally a private namespace. The profile extraction pipeline and CV tailoring pipeline must not read or write it.
- No new ADR required: Mode C is a natural extension of the GapDetector pattern established in ADR-004. The reviewer application follows the pattern from ADR-021.
