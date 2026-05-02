# Marcus Complete Journey — E2E Test Design

**Date:** 2026-05-01
**Sprint:** 31
**Status:** Approved
**Tier:** PQ (requires Docker stack + real LLM via OpenRouter)

---

## Goal

Add a single Playwright test file that covers the full Marcus happy path from scratch:
CV upload + JD paste → gap analysis → interview (one answer) → CV generation → cover letter generation.

Neither existing PQ test covers this end-to-end:
- `marcus-new-user-journey.spec.ts` stops at the interview completion screen.
- `cover-letter.spec.ts` skips the interview entirely.

---

## File

`tests/e2e/pq/markus-complete-journey.spec.ts`

---

## Setup Helper: `setupCompleteJourney(page)`

Returns `flowId: string`. Drives the full linear path:

1. `DELETE /api/profile` — reset backend state for a clean new-user start
2. Navigate to `/`, wait for `networkidle`
3. Click "Paste Text" button; fill JD textarea with `sample_jd.txt` + unique timestamp comment
4. Set `file-input` to `fixtures/profiles/sample_cv.pdf`
5. Assert `submit-button` enabled; click it
6. Wait for URL `/flow/.*/gaps` (timeout: 90 s)
7. Wait for `loading-indicator` not visible (timeout: 30 s)
8. Click `interview-button`; wait for URL `/flow/.*/interview` (timeout: 30 s)
9. Wait for `interview-loading` not visible (timeout: 30 s)
10. Wait for `interview-question` visible
11. Fill `answer-textarea` with a Marcus-appropriate answer; click `send-button`
12. Wait up to 30 s for question text to change or `completion-screen` to appear
13. If `completion-screen` not yet visible: click `done-button` → wait for `done-confirm` → click "End interview"
14. Wait for `completion-screen` visible (timeout: 30 s)
15. Click `generate-cv-button`; wait for URL `/flow/.*/cv` (timeout: 60 s)
16. If "Skip for now" button visible (photo prompt): click it
17. Click "CV generieren"; wait for `refinement-panel` visible (timeout: 90 s)
18. Click `tab-actions`; click `generate-cover-letter-btn`
19. Wait for `cover-letter-modal` visible
20. Fill `cl-salary` with `"95.000 € p.a."`; click `cl-modal-generate`
21. Wait for URL `/flow/.*/cover-letter` (timeout: 30 s)
22. Wait for `cover-letter-iframe` visible (timeout: 60 s)
23. Extract and return `flowId` from URL

---

## Test Cases

All three tests call `setupCompleteJourney` independently (no shared state).

### US-MK01 — Complete journey ends on cover letter page

- Call `setupCompleteJourney`
- Assert URL matches `/flow/.*/cover-letter`
- Assert `cover-letter-iframe` is visible

### US-MK02 — Back-to-CV navigation from cover letter

- Call `setupCompleteJourney`, capture `flowId`
- Assert `cl-view-cv-btn` is visible; click it
- Assert URL resolves to `/flow/{flowId}/cv`

### US-MK03 — PDF download button present after full journey

- Call `setupCompleteJourney`
- Assert `cl-topbar-download-btn` is visible and enabled

---

## Marcus Answer Copy

Used in step 11 of `setupCompleteJourney`:

> "Ich habe über 10 Jahre Erfahrung in der Softwareentwicklung, davon 6 Jahre mit Python und FastAPI in produktiven Umgebungen. Ich habe mehrere Microservice-Architekturen entworfen und betrieben."

This is a plausible, substantive answer for the Senior Software Engineer JD in `sample_jd.txt` and avoids triggering a conflict.

---

## Fixtures

| Fixture | Path |
|---|---|
| CV | `tests/fixtures/profiles/sample_cv.pdf` |
| JD | `tests/fixtures/JDs/sample_jd.txt` |

No new fixtures required.

---

## Config

File must run under `playwright.config.pq.ts` only — not the default `playwright.config.ts`.
The file header comment must include the standard PQ warning:

```
DO NOT run this file with the standard `npx playwright test` command.
```

---

## Out of Scope

- Interview with more than one answer
- Cover letter editing or template switching (covered in `cover-letter.spec.ts`)
- Photo upload during the journey
- Error/unhappy paths
