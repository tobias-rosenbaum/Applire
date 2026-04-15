# Sprint 26 — JD URL Error Handling Design

**Date:** 2026-04-15
**Sprint:** 26
**Author:** Claude Code (brainstorming session with Tobias Rosenbaum)
**Status:** Approved — ready for implementation

---

## Problem Statement

When Marcus pastes a job description URL that is invalid, blocked, taken down, or returns unextractable content, the current behaviour is:

1. The entire processing pipeline halts
2. A raw technical error string is dumped in a red box
3. Marcus cannot upload his CVs or build his profile until the URL issue is resolved
4. There is no actionable recovery path

This is the first "not-so-happy path" for the new customer (Marcus) persona.

---

## Failure Taxonomy

| Failure type | HTTP status from scraper | `error_code` |
|---|---|---|
| Malformed / non-http URL | 422 (ValueError) | `jd_url_invalid` |
| Blocked, 403/429, bot wall | 422 (ScraperError) | `jd_fetch_failed` |
| 404 — job posting taken down | 422 (ScraperError) | `jd_fetch_failed` |
| Thin content / JS wall / paywall | 422 (ScraperError) | `jd_fetch_failed` |

---

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Pipeline behaviour on URL failure | Auto-skip JD step, continue | CV upload should never be blocked by a URL |
| Recovery UX location | Dismissible banner on gaps page | Lowest friction; no special inline widget needed |
| Error message granularity | Two categories (invalid vs. fetch failed) | Helps Marcus self-diagnose a typo vs. a real block |
| Error classification mechanism | Structured `error_code` in backend response | Stable, testable; immune to copy changes |

---

## Section 1: Backend Changes

### `scraper.py`

`ScraperError` gains a `code: str` field defaulting to `"jd_fetch_failed"`. No behaviour change — purely informational.

```python
class ScraperError(Exception):
    def __init__(self, url: str, reason: str, code: str = "jd_fetch_failed") -> None:
        self.url = url
        self.reason = reason
        self.code = code
        super().__init__(reason)
```

### `routers/job.py`

The two `except` blocks for `ValueError` and `ScraperError` in `analyze_job_description` return a structured `detail` dict instead of a plain string:

```python
except ValueError as exc:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"error_code": "jd_url_invalid", "message": str(exc)},
    )
except ScraperError as exc:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"error_code": "jd_fetch_failed", "message": exc.reason},
    )
```

**No new endpoints. No DB changes. No migrations.**

---

## Section 2: Frontend — Processing Overlay

### `components/processing-overlay.tsx`

`StepState` gains a `"skipped"` variant (alongside existing `"pending"`, `"in_progress"`, `"completed"`, `"error"`). The `StepChecklist` component renders it with an amber colour and a skip icon (or dash), distinct from the green checkmark of `"completed"`.

The JD URL analysis call is wrapped in its own fault-tolerant block. On a 422 with a recognised `error_code`, the step is marked `"skipped"` with a human-readable detail:

| `error_code` | Step detail shown |
|---|---|
| `jd_url_invalid` | "That doesn't look like a valid URL — you can add it later" |
| `jd_fetch_failed` | "The site blocked us — you can paste the text later" |
| Any other non-OK status | Falls through to the existing hard-stop error path |

`jobId` stays `null`, so the pipeline continues exactly as today when no JD is provided (CV upload → profile build → gap detection skipped).

### Redirect with query param

On completion, the redirect includes a `jd_status` query param only when a URL was attempted and failed:

```ts
router.push(`/flow/${flowId}/gaps?jd_status=url_invalid`)
// or ?jd_status=fetch_failed
```

Not set when the user left the URL field empty.

---

## Section 3: Frontend — Recovery Banner

### `app/flow/[flowId]/gaps/page.tsx`

Reads `useSearchParams()` on mount. If `jd_status` is present, renders a dismissible amber banner above the main content.

**Copy:**

| `jd_status` | Banner text |
|---|---|
| `url_invalid` | "That URL didn't look valid. Paste the job description text to run gap analysis." |
| `fetch_failed` | "We couldn't load that job posting — it may be blocked or taken down. Paste the job description text to run gap analysis." |

**CTA:** "Add job description →" — navigates to the home page / JD entry point for returning users.

**Dismissal:** `×` button closes the banner via component state. No persistence needed — the query param is absent on refresh, so the banner does not re-appear.

---

## Section 4: Testing

### Backend unit tests

New tests (in `tests/unit/test_job_router_url_errors.py` or equivalent):
- `POST /api/job/analyze` with a non-http URL → 422, `detail.error_code == "jd_url_invalid"`
- `POST /api/job/analyze` with a URL where `scrape_job_url` raises `ScraperError` → 422, `detail.error_code == "jd_fetch_failed"`

Both tests mock `scrape_job_url` — no real HTTP calls.

### Frontend unit tests (Vitest)

One test for `ProcessingOverlay`: when the JD API returns `{"error_code": "jd_fetch_failed", "message": "..."}`, the JD step is marked skipped (not errored) and the pipeline continues to the upload step.

### E2E test (Playwright)

New scenario in the onboarding E2E suite:
1. User enters an invalid URL + uploads a CV → submits
2. Processing overlay shows JD step skipped with correct message
3. Pipeline completes, redirects to gaps page with `?jd_status=fetch_failed`
4. Amber banner is visible with correct copy
5. "Add job description →" link is present and navigates correctly

Backend mocked — no real scraping in CI.

**Coverage gate: ≥75% backend unit coverage maintained.**

---

## User Journey Impact

This sprint adds **Branch F: JD URL Fetch Failure** to the Marcus (New Customer) persona. See updated persona doc.

### Emotional journey (Branch F)

```
[Confident]   →  Pastes a URL, clicks "Analyze & Build Profile"
    ↓
[Surprised]   →  JD step shows amber "skipped" (not red error)
    ↓
[Reassured]   →  CVs still upload, profile still builds
    ↓
[Informed]    →  Amber banner on gaps page explains what happened
    ↓
[Empowered]   →  Clear CTA to add JD via paste — no dead end
```

---

## Out of Scope

- Retry URL with different User-Agent / proxy
- Per-domain scraping rules beyond the existing `_JS_HOSTS` list
- Storing the failed URL for later retry
- Email notification when a URL becomes available
- Any UI change to the URL input field itself (e.g., inline validation before submit)

---

## Epic / User Story References

- **E-NEW:** JD Input Resilience (Sprint 26)
  - US-NEW-01: Graceful URL failure with pipeline continuation
  - US-NEW-02: Contextual recovery banner with actionable CTA
