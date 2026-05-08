# JD URL Error Handling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gracefully handle invalid or blocked JD URLs — skip the JD step, continue the CV pipeline, and show an amber recovery banner on the gaps page.

**Architecture:** The backend returns a structured `{"error_code": "...", "message": "..."}` dict in the 422 `detail` field. The frontend `ProcessingOverlay` detects recognised error codes, marks the JD step `"skipped"` (amber), continues the pipeline, and appends `?jd_status=...` to the redirect. The gaps page reads this query param and renders a dismissible amber banner.

**Tech Stack:** Python 3.12 / FastAPI (backend), Next.js 15 / React 19 / TypeScript (frontend), pytest / Vitest / Playwright (testing).

---

## File Map

| Action | Path | What changes |
|---|---|---|
| Modify | `backend/applire/services/scraper.py` | Add `code` field to `ScraperError` |
| Modify | `backend/applire/routers/job.py` | Return structured `error_code` dict in 422 responses |
| Create | `tests/unit/test_job_router_url_errors.py` | Backend unit tests for both error codes |
| Modify | `frontend/components/ui/step-checklist.tsx` | Add `"skipped"` to `StepState`; render amber skip icon + detail |
| Modify | `frontend/components/processing-overlay.tsx` | Fault-tolerant JD URL block; `?jd_status=` redirect param |
| Modify | `frontend/app/flow/[flowId]/gaps/page.tsx` | Dismissible amber recovery banner from `jd_status` query param |
| Create | `frontend/components/__tests__/ProcessingOverlay.test.tsx` | Vitest: `jd_fetch_failed` → step skipped, pipeline continues |
| Create | `tests/e2e/oq/jd-url-error.spec.ts` | Playwright OQ: full Branch F scenario with mocked backend |

---

### Task 1: Add `code` field to `ScraperError`

**Files:**
- Modify: `backend/applire/services/scraper.py:33-39`

- [ ] **Step 1: Update `ScraperError.__init__`**

Open `backend/applire/services/scraper.py` and replace the `ScraperError` class:

```python
class ScraperError(Exception):
    """Raised when all tiers fail to extract job text."""

    def __init__(self, url: str, reason: str, code: str = "jd_fetch_failed") -> None:
        self.url = url
        self.reason = reason
        self.code = code
        super().__init__(reason)
```

- [ ] **Step 2: Verify existing call sites are unaffected**

Run:
```bash
cd /home/apliqa/Documents/Applire/Solution
grep -n "ScraperError(" backend/applire/services/scraper.py
```

Expected: three call sites (two in `scraper.py`). All use positional `url, reason` — the new `code` kwarg defaults and requires no change.

- [ ] **Step 3: Run existing scraper-related tests to confirm no regression**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/ -v -k "scraper or job" 2>&1 | tail -20
```

Expected: all passing (or skip if none exist yet — Task 3 adds them).

- [ ] **Step 4: Commit**

```bash
git add backend/applire/services/scraper.py
git commit -m "feat: add code field to ScraperError (Sprint 26)"
```

---

### Task 2: Return structured `error_code` in `routers/job.py`

**Files:**
- Modify: `backend/applire/routers/job.py:36-45`

- [ ] **Step 1: Replace the two `except` blocks in `analyze_job_description`**

Open `backend/applire/routers/job.py`. Replace the blocks that currently raise HTTP 422 with plain strings:

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

The surrounding `if body.url:` block stays the same. Only the two `except` handlers change.

- [ ] **Step 2: Manually verify the full `analyze_job_description` URL branch looks like this**

```python
    if body.url:
        try:
            text = await scrape_job_url(body.url)
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
        source_url = body.url
```

- [ ] **Step 3: Commit**

```bash
git add backend/applire/routers/job.py
git commit -m "feat: structured error_code in JD analyze 422 responses (Sprint 26)"
```

---

### Task 3: Backend unit tests for structured error codes

**Files:**
- Create: `tests/unit/test_job_router_url_errors.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_job_router_url_errors.py`:

```python
"""Unit tests for structured error_code in POST /api/job/analyze (Sprint 26).

Both tests mock scrape_job_url so no real HTTP calls are made.
Run with: pytest tests/unit/test_job_router_url_errors.py -v
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from applire.main import app
from applire.services.scraper import ScraperError


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# jd_url_invalid — ValueError from _validate_url
# ---------------------------------------------------------------------------


def test_analyze_invalid_url_returns_structured_error_code(client: TestClient) -> None:
    """A non-http URL must return 422 with error_code='jd_url_invalid'."""
    with patch(
        "applire.routers.job.scrape_job_url",
        new_callable=AsyncMock,
        side_effect=ValueError("Only http and https URLs are supported, got scheme: 'ftp'"),
    ):
        res = client.post("/api/job/analyze", json={"url": "ftp://example.com/job"})

    assert res.status_code == 422
    detail = res.json()["detail"]
    assert isinstance(detail, dict), f"Expected dict, got: {detail!r}"
    assert detail["error_code"] == "jd_url_invalid"
    assert "message" in detail
    assert len(detail["message"]) > 0


# ---------------------------------------------------------------------------
# jd_fetch_failed — ScraperError from scrape_job_url
# ---------------------------------------------------------------------------


def test_analyze_blocked_url_returns_structured_error_code(client: TestClient) -> None:
    """A blocked / thin-content URL must return 422 with error_code='jd_fetch_failed'."""
    with patch(
        "applire.routers.job.scrape_job_url",
        new_callable=AsyncMock,
        side_effect=ScraperError(
            url="https://blocked.example.com/job",
            reason="Could not extract job text from this page. Please paste the job description manually.",
        ),
    ):
        res = client.post("/api/job/analyze", json={"url": "https://blocked.example.com/job"})

    assert res.status_code == 422
    detail = res.json()["detail"]
    assert isinstance(detail, dict), f"Expected dict, got: {detail!r}"
    assert detail["error_code"] == "jd_fetch_failed"
    assert "message" in detail
    assert len(detail["message"]) > 0
```

- [ ] **Step 2: Run the tests to confirm they fail (before Task 2 is committed)**

> If Task 2 is already committed, skip directly to Step 3.

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_job_router_url_errors.py -v
```

Expected before Task 2: FAIL — `detail` is a string, not a dict.
Expected after Task 2: PASS.

- [ ] **Step 3: Run the tests to confirm they pass**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/test_job_router_url_errors.py -v
```

Expected output:
```
tests/unit/test_job_router_url_errors.py::test_analyze_invalid_url_returns_structured_error_code PASSED
tests/unit/test_job_router_url_errors.py::test_analyze_blocked_url_returns_structured_error_code PASSED
```

- [ ] **Step 4: Verify coverage gate still passes**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/ -v --cov=applire --cov-fail-under=75 2>&1 | tail -10
```

Expected: `Required test coverage of 75% reached.`

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_job_router_url_errors.py
git commit -m "test: backend unit tests for jd_url_invalid and jd_fetch_failed (Sprint 26)"
```

---

### Task 4: Add `"skipped"` state to `StepChecklist`

**Files:**
- Modify: `frontend/components/ui/step-checklist.tsx`

- [ ] **Step 1: Add `"skipped"` to the `StepState` union type**

Open `frontend/components/ui/step-checklist.tsx` line 12. Replace:

```typescript
export type StepState = "completed" | "in_progress" | "pending";
```

With:

```typescript
export type StepState = "completed" | "in_progress" | "pending" | "skipped";
```

- [ ] **Step 2: Add the amber skip icon to `StepIcon`**

Inside `StepIcon`, add a new branch before the final `return` (the pending empty circle). Place it after the `in_progress` block:

```tsx
  if (state === "skipped") {
    return (
      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-amber-100 border-2 border-amber-400">
        <svg
          className="h-3 w-3 text-amber-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2.5}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </div>
    );
  }
```

- [ ] **Step 3: Show detail text for both `"completed"` and `"skipped"` states**

Find the detail paragraph inside `StepChecklist` (line ~93). Replace:

```tsx
              {step.detail && state === "completed" && (
                <p className="text-xs text-gray-500 mt-0.5 animate-[fade-in_0.3s_ease-out]">
                  {step.detail}
                </p>
              )}
```

With:

```tsx
              {step.detail && (state === "completed" || state === "skipped") && (
                <p className={cn(
                  "text-xs mt-0.5 animate-[fade-in_0.3s_ease-out]",
                  state === "skipped" ? "text-amber-600" : "text-gray-500"
                )}>
                  {step.detail}
                </p>
              )}
```

- [ ] **Step 4: Add amber label styling for the skipped step label**

Inside the `<p>` tag that renders `step.label`, find the className `cn(...)` block. Add a case for `"skipped"`:

```tsx
                <p
                  className={cn(
                    "text-sm transition-colors duration-200",
                    state === "completed" && "text-gray-500 line-through",
                    state === "in_progress" && "font-semibold text-neutral-dark",
                    state === "skipped" && "text-amber-600",
                    state === "pending" && "text-gray-400"
                  )}
                >
```

- [ ] **Step 5: Run frontend type check**

```bash
cd /home/apliqa/Documents/Applire/Solution/frontend
npx tsc --noEmit 2>&1 | head -30
```

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/components/ui/step-checklist.tsx
git commit -m "feat: add skipped state to StepChecklist (Sprint 26)"
```

---

### Task 5: Fault-tolerant JD URL analysis in `ProcessingOverlay`

**Files:**
- Modify: `frontend/components/processing-overlay.tsx`

- [ ] **Step 1: Declare `jdFailReason` variable at the top of `runPipeline`**

Inside `runPipeline`, add this declaration immediately after `let jobId: string | null = null;`:

```typescript
        let jdFailReason: "url_invalid" | "fetch_failed" | null = null;
```

- [ ] **Step 2: Replace the URL fetch block with a fault-tolerant version**

Find the current URL branch (lines ~69-77). Replace:

```typescript
          const res = await fetch(`${API_BASE}/api/job/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: jdUrl.trim() }),
          });
          if (!res.ok) throw new Error(await apiErrorMessage(res));
          const data = await res.json();
          jobId = data.id;
          markStep("analyze_jd", "completed", data.role_title ? `Role: ${data.role_title}` : "Job description analyzed");
```

With:

```typescript
          const res = await fetch(`${API_BASE}/api/job/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: jdUrl.trim() }),
          });
          if (!res.ok) {
            if (res.status === 422) {
              let body: { detail?: { error_code?: string; message?: string } | string } | null = null;
              try {
                body = await res.json();
              } catch {
                // body stays null
              }
              const detail = body?.detail && typeof body.detail === "object" ? body.detail : null;
              const errorCode = detail?.error_code;
              if (errorCode === "jd_url_invalid") {
                markStep("analyze_jd", "skipped", "That doesn't look like a valid URL — you can add it later");
                jdFailReason = "url_invalid";
              } else if (errorCode === "jd_fetch_failed") {
                markStep("analyze_jd", "skipped", "The site blocked us — you can paste the text later");
                jdFailReason = "fetch_failed";
              } else {
                // Unrecognised 422 — hard stop
                const msg =
                  typeof body?.detail === "string" ? body.detail
                  : detail?.message ?? res.statusText ?? `HTTP ${res.status}`;
                throw new Error(msg);
              }
            } else {
              throw new Error(await apiErrorMessage(res));
            }
          } else {
            const data = await res.json();
            jobId = data.id;
            markStep("analyze_jd", "completed", data.role_title ? `Role: ${data.role_title}` : "Job description analyzed");
          }
```

- [ ] **Step 3: Update the progress calculation to count `"skipped"` steps**

Find the line:

```typescript
  const completedCount = Object.values(stepStates).filter((s) => s === "completed").length;
```

Replace with:

```typescript
  const completedCount = Object.values(stepStates).filter((s) => s === "completed" || s === "skipped").length;
```

- [ ] **Step 4: Pass `jdFailReason` in all redirect calls**

There are two `router.push` calls that redirect to the gaps page. Replace both:

First (inside `if (!jobId)` block, ~line 147):
```typescript
          router.push(`/flow/${flowId}/gaps`);
```
Replace with:
```typescript
          router.push(jdFailReason ? `/flow/${flowId}/gaps?jd_status=${jdFailReason}` : `/flow/${flowId}/gaps`);
```

Second (at the end of the pipeline, ~line 174):
```typescript
        router.push(`/flow/${flowId}/gaps`);
```
Replace with:
```typescript
        router.push(jdFailReason ? `/flow/${flowId}/gaps?jd_status=${jdFailReason}` : `/flow/${flowId}/gaps`);
```

- [ ] **Step 5: Run frontend type check**

```bash
cd /home/apliqa/Documents/Applire/Solution/frontend
npx tsc --noEmit 2>&1 | head -30
```

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/components/processing-overlay.tsx
git commit -m "feat: fault-tolerant JD URL analysis in ProcessingOverlay (Sprint 26)"
```

---

### Task 6: Recovery banner on gaps page

**Files:**
- Modify: `frontend/app/flow/[flowId]/gaps/page.tsx`

- [ ] **Step 1: Add `useSearchParams` import**

Open `frontend/app/flow/[flowId]/gaps/page.tsx`. Find the existing imports from React:

```typescript
import { useEffect, useState } from "react";
```

Replace with:

```typescript
import { useEffect, useState, Suspense } from "react";
```

Also add `useSearchParams` to the `next/navigation` import:

```typescript
import { useRouter, useSearchParams } from "next/navigation";
```

- [ ] **Step 2: Add the `JdRecoveryBanner` component**

Add this component above the `GapClickPanel` function (before line 85):

```tsx
// ---------------------------------------------------------------------------
// JD Recovery Banner — shown when jd_status query param is present (Sprint 26)
// ---------------------------------------------------------------------------

function JdRecoveryBannerInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [dismissed, setDismissed] = useState(false);

  const jdStatus = searchParams.get("jd_status");

  if (!jdStatus || dismissed) return null;

  const copy =
    jdStatus === "url_invalid"
      ? "That URL didn't look valid. Paste the job description text to run gap analysis."
      : "We couldn't load that job posting — it may be blocked or taken down. Paste the job description text to run gap analysis.";

  return (
    <div
      data-testid="jd-recovery-banner"
      className="mb-6 flex items-start gap-3 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3"
    >
      <svg
        className="mt-0.5 h-4 w-4 shrink-0 text-amber-600"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
        />
      </svg>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-amber-800">{copy}</p>
        <button
          data-testid="jd-recovery-cta"
          type="button"
          className="mt-1 text-sm font-medium text-amber-700 underline hover:no-underline"
          onClick={() => router.push("/")}
        >
          Add job description →
        </button>
      </div>
      <button
        data-testid="jd-recovery-dismiss"
        type="button"
        aria-label="Dismiss"
        className="shrink-0 text-amber-500 hover:text-amber-700 transition-colors"
        onClick={() => setDismissed(true)}
      >
        ×
      </button>
    </div>
  );
}

function JdRecoveryBanner() {
  return (
    <Suspense fallback={null}>
      <JdRecoveryBannerInner />
    </Suspense>
  );
}
```

> **Why `Suspense`?** Next.js 15 requires `useSearchParams()` to be wrapped in `<Suspense>` to avoid a build-time error. The inner component does the work; the outer wrapper provides the boundary.

- [ ] **Step 3: Render the banner at the top of the gaps page `<div>`**

Find the outermost `<div>` in the return statement (line ~401):

```tsx
  return (
    <div data-testid="gap-analysis-page" className="max-w-4xl mx-auto">
      {/* Section 1: Master Profile Summary */}
```

Insert the banner immediately after the opening `<div>`:

```tsx
  return (
    <div data-testid="gap-analysis-page" className="max-w-4xl mx-auto">
      <JdRecoveryBanner />
      {/* Section 1: Master Profile Summary */}
```

- [ ] **Step 4: Run frontend type check**

```bash
cd /home/apliqa/Documents/Applire/Solution/frontend
npx tsc --noEmit 2>&1 | head -30
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/app/flow/[flowId]/gaps/page.tsx
git commit -m "feat: JD recovery banner on gaps page (Sprint 26)"
```

---

### Task 7: Vitest test for `ProcessingOverlay` skipped state

**Files:**
- Create: `frontend/components/__tests__/ProcessingOverlay.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `frontend/components/__tests__/ProcessingOverlay.test.tsx`:

```tsx
/**
 * ProcessingOverlay — JD URL error handling (Sprint 26)
 *
 * Verifies that a 422 response with error_code="jd_fetch_failed" causes the
 * JD step to be marked "skipped" (not error) and the pipeline to continue.
 */
import { render, screen, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { ProcessingOverlay } from "../processing-overlay";

// next/navigation must be mocked — jsdom has no router
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const mockFile = new File(["cv content"], "cv.pdf", { type: "application/pdf" });

const DEFAULT_PROPS = {
  files: [mockFile],
  jdMode: "url" as const,
  jdUrl: "https://blocked.example.com/job",
  jdText: "",
  onCancel: vi.fn(),
};

describe("ProcessingOverlay — JD URL error handling", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("marks JD step as skipped and continues to upload when JD analyze returns jd_fetch_failed", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();

      // JD analyze → 422 jd_fetch_failed
      if (url.includes("/api/job/analyze")) {
        return {
          ok: false,
          status: 422,
          statusText: "Unprocessable Entity",
          json: async () => ({ detail: { error_code: "jd_fetch_failed", message: "blocked" } }),
        } as Response;
      }

      // Flow creation (bare flow, no job)
      if (url.includes("/api/flow") && !url.includes("advance") && !url.includes("state")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({ flow_id: "test-flow-xyz" }),
        } as Response;
      }

      // CV upload
      if (url.includes("/api/profile/upload")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({}),
        } as Response;
      }

      // Fallback — should not be reached in this scenario
      return {
        ok: true,
        status: 200,
        json: async () => ({}),
      } as Response;
    });

    render(<ProcessingOverlay {...DEFAULT_PROPS} />);

    // JD step skip message must appear
    await waitFor(
      () => {
        expect(
          screen.getByText("The site blocked us — you can paste the text later")
        ).toBeInTheDocument();
      },
      { timeout: 5000 }
    );

    // No hard error block should be rendered
    expect(screen.queryByTestId("processing-error")).toBeNull();

    // Upload step must become active (pipeline continued)
    await waitFor(
      () => {
        // "Uploading CV" label should be present (in_progress or completed)
        expect(screen.getByText("Uploading CV")).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
  });

  it("marks JD step as skipped with url_invalid copy when error_code is jd_url_invalid", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();

      if (url.includes("/api/job/analyze")) {
        return {
          ok: false,
          status: 422,
          statusText: "Unprocessable Entity",
          json: async () => ({ detail: { error_code: "jd_url_invalid", message: "not a valid url" } }),
        } as Response;
      }

      if (url.includes("/api/flow") && !url.includes("advance") && !url.includes("state")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({ flow_id: "test-flow-abc" }),
        } as Response;
      }

      if (url.includes("/api/profile/upload")) {
        return { ok: true, status: 200, json: async () => ({}) } as Response;
      }

      return { ok: true, status: 200, json: async () => ({}) } as Response;
    });

    render(<ProcessingOverlay {...DEFAULT_PROPS} />);

    await waitFor(
      () => {
        expect(
          screen.getByText("That doesn't look like a valid URL — you can add it later")
        ).toBeInTheDocument();
      },
      { timeout: 5000 }
    );

    expect(screen.queryByTestId("processing-error")).toBeNull();
  });

  it("still hard-stops on unrecognised 422 (no error_code)", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();

      if (url.includes("/api/job/analyze")) {
        return {
          ok: false,
          status: 422,
          statusText: "Unprocessable Entity",
          // Old-style plain string detail — should hard-stop
          json: async () => ({ detail: "Some unknown validation error" }),
        } as Response;
      }

      return { ok: true, status: 200, json: async () => ({}) } as Response;
    });

    render(<ProcessingOverlay {...DEFAULT_PROPS} />);

    await waitFor(
      () => {
        expect(screen.getByTestId("processing-error")).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
  });
});
```

- [ ] **Step 2: Run the tests to verify they pass**

```bash
cd /home/apliqa/Documents/Applire/Solution/frontend
npm test -- components/__tests__/ProcessingOverlay.test.tsx 2>&1 | tail -30
```

Expected:
```
 ✓ marks JD step as skipped and continues to upload when JD analyze returns jd_fetch_failed
 ✓ marks JD step as skipped with url_invalid copy when error_code is jd_url_invalid
 ✓ still hard-stops on unrecognised 422 (no error_code)
```

- [ ] **Step 3: Commit**

```bash
git add frontend/components/__tests__/ProcessingOverlay.test.tsx
git commit -m "test: Vitest tests for ProcessingOverlay JD URL error handling (Sprint 26)"
```

---

### Task 8: E2E test — Branch F JD URL error flow (OQ tier)

**Files:**
- Create: `tests/e2e/oq/jd-url-error.spec.ts`

- [ ] **Step 1: Write the E2E test**

Create `tests/e2e/oq/jd-url-error.spec.ts`:

```typescript
// tests/e2e/oq/jd-url-error.spec.ts
/**
 * Branch F — JD URL Fetch Failure (Sprint 26, OQ tier)
 *
 * Verifies the full error recovery flow when a job description URL fails.
 * All backend calls are mocked — no real LLM or scraper required.
 *
 * Run: npx playwright test tests/e2e/oq/jd-url-error.spec.ts
 */

import { test, expect } from "@playwright/test";

const FLOW_ID = "mock-flow-sprint26";

test.describe("Branch F — JD URL fetch failure", () => {
  test.beforeEach(async ({ page }) => {
    // Check user state → new user (show onboarding form)
    await page.route("**/api/profile/exists", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ exists: false }),
      });
    });

    // JD analyze → 422 jd_fetch_failed
    await page.route("**/api/job/analyze", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 422,
          contentType: "application/json",
          body: JSON.stringify({
            detail: {
              error_code: "jd_fetch_failed",
              message: "Could not extract job text from this page. Please paste the job description manually.",
            },
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Flow creation (bare, no job)
    await page.route("**/api/flow", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ flow_id: FLOW_ID }),
        });
      } else {
        await route.continue();
      }
    });

    // CV upload
    await page.route("**/api/profile/upload", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ok: true }),
      });
    });

    // Flow state (needed when gaps page loads)
    await page.route(`**/api/flow/${FLOW_ID}/state`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          job_id: null,
          user_type: "new",
          available_actions: {},
          gap_summary: null,
          job_summary: null,
        }),
      });
    });
  });

  test("overlay shows JD step as skipped and redirects with ?jd_status=fetch_failed", async ({
    page,
  }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // The URL input is in "URL" mode by default
    const urlInput = page.locator('input[type="url"]');
    await expect(urlInput).toBeVisible();
    await urlInput.fill("https://blocked-job-site.example.com/posting/123");

    // Upload a fake CV file
    const fileChooserPromise = page.waitForEvent("filechooser");
    await page.getByTestId("file-input").setInputFiles({
      name: "test-cv.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("fake pdf content"),
    });

    // Submit
    await page.getByTestId("submit-button").click();

    // Processing overlay should appear
    await expect(page.getByTestId("processing-indicator")).toBeVisible({ timeout: 5000 });

    // JD step should show the amber skipped message (not hard error)
    await expect(
      page.getByText("The site blocked us — you can paste the text later")
    ).toBeVisible({ timeout: 10000 });

    // Hard error block must NOT appear
    await expect(page.getByTestId("processing-error")).not.toBeVisible();

    // Pipeline should complete and redirect to gaps page with query param
    await expect(page).toHaveURL(
      new RegExp(`/flow/${FLOW_ID}/gaps\\?jd_status=fetch_failed`),
      { timeout: 15000 }
    );
  });

  test("amber recovery banner is visible on gaps page with correct copy", async ({
    page,
  }) => {
    // Navigate directly to the gaps page with the query param (simulates the redirect)
    await page.goto(`/flow/${FLOW_ID}/gaps?jd_status=fetch_failed`);
    await page.waitForLoadState("networkidle");

    // Banner must appear
    const banner = page.getByTestId("jd-recovery-banner");
    await expect(banner).toBeVisible({ timeout: 5000 });
    await expect(banner).toContainText(
      "We couldn't load that job posting — it may be blocked or taken down."
    );
  });

  test("amber recovery banner shows url_invalid copy for jd_status=url_invalid", async ({
    page,
  }) => {
    await page.goto(`/flow/${FLOW_ID}/gaps?jd_status=url_invalid`);
    await page.waitForLoadState("networkidle");

    const banner = page.getByTestId("jd-recovery-banner");
    await expect(banner).toBeVisible({ timeout: 5000 });
    await expect(banner).toContainText("That URL didn't look valid.");
  });

  test("CTA navigates to home page", async ({ page }) => {
    await page.goto(`/flow/${FLOW_ID}/gaps?jd_status=fetch_failed`);
    await page.waitForLoadState("networkidle");

    await expect(page.getByTestId("jd-recovery-cta")).toBeVisible({ timeout: 5000 });
    await page.getByTestId("jd-recovery-cta").click();

    await expect(page).toHaveURL("/", { timeout: 5000 });
  });

  test("dismiss button hides the banner", async ({ page }) => {
    await page.goto(`/flow/${FLOW_ID}/gaps?jd_status=fetch_failed`);
    await page.waitForLoadState("networkidle");

    const banner = page.getByTestId("jd-recovery-banner");
    await expect(banner).toBeVisible({ timeout: 5000 });

    await page.getByTestId("jd-recovery-dismiss").click();

    await expect(banner).not.toBeVisible({ timeout: 3000 });
  });
});
```

- [ ] **Step 2: Run the E2E tests (requires running app)**

Make sure the app is running (`docker-compose up -d` or `npm run dev` + `uvicorn`), then:

```bash
cd /home/apliqa/Documents/Applire/Solution
npx playwright test tests/e2e/oq/jd-url-error.spec.ts --reporter=list 2>&1 | tail -30
```

Expected: all 5 tests pass.

- [ ] **Step 3: If a test fails, check the Playwright trace**

```bash
npx playwright test tests/e2e/oq/jd-url-error.spec.ts --trace=on
npx playwright show-report
```

- [ ] **Step 4: Commit**

```bash
git add tests/e2e/oq/jd-url-error.spec.ts
git commit -m "test: E2E tests for JD URL error Branch F (Sprint 26)"
```

---

### Task 9: Create sprint branch and final verification

- [ ] **Step 1: Ensure all work is on the `sprint-26` branch**

```bash
cd /home/apliqa/Documents/Applire/Solution
git log --oneline -8
```

Confirm all Sprint 26 commits appear. If work was done on `main`, create the branch now (before opening the PR):

```bash
git checkout -b sprint-26
```

- [ ] **Step 2: Run full backend unit test suite**

```bash
cd /home/apliqa/Documents/Applire/Solution
pytest tests/unit/ -v --cov=applire --cov-fail-under=75 2>&1 | tail -15
```

Expected: ≥75% coverage, all tests pass.

- [ ] **Step 3: Run full Vitest suite**

```bash
cd /home/apliqa/Documents/Applire/Solution/frontend
npm test 2>&1 | tail -20
```

Expected: all tests pass, no type errors.

- [ ] **Step 4: Run full E2E suite**

```bash
cd /home/apliqa/Documents/Applire/Solution
npx playwright test --reporter=list 2>&1 | tail -20
```

Expected: all existing tests still pass plus the 5 new OQ tests.

- [ ] **Step 5: Manual smoke test (UAT)**

1. Start the full stack: `docker-compose up -d`
2. Open `http://localhost:3000`
3. Enter the URL `ftp://not-a-real-url` in the URL field, upload a real CV, click submit
4. Verify: JD step shows amber "skipped" icon and message "That doesn't look like a valid URL — you can add it later"
5. Verify: pipeline continues (upload and profile steps complete)
6. Verify: redirect lands on `/flow/.../gaps?jd_status=url_invalid`
7. Verify: amber banner appears with "That URL didn't look valid." copy
8. Verify: clicking "Add job description →" returns to home page
9. Verify: clicking `×` dismisses the banner

- [ ] **Step 6: Push branch and open PR**

```bash
git push -u origin sprint-26
gh pr create \
  --title "feat: Sprint 26 — JD URL Error Handling" \
  --body "$(cat <<'EOF'
## Summary

- Backend: `ScraperError` gains a `code` field; `POST /api/job/analyze` now returns structured `{"error_code": ..., "message": ...}` on 422 instead of a plain string
- Frontend overlay: JD URL analysis is now fault-tolerant — recognised 422s mark the step `"skipped"` (amber) and continue the pipeline; unrecognised errors still hard-stop
- Frontend gaps page: dismissible amber recovery banner is rendered when `?jd_status=` query param is present, with copy tailored to the error type and a CTA back to JD entry
- `StepState` gains `"skipped"` variant with amber icon, label colour, and detail text

## Epics / Stories
- E024 US097 — Graceful JD URL failure with pipeline continuation
- E024 US098 — Contextual recovery banner with actionable CTA

## Test plan
- [ ] Backend unit tests: `pytest tests/unit/test_job_router_url_errors.py -v` — 2 tests pass
- [ ] Coverage gate: `pytest tests/unit/ --cov=applire --cov-fail-under=75` — ≥75% maintained
- [ ] Vitest: `npm test -- components/__tests__/ProcessingOverlay.test.tsx` — 3 tests pass
- [ ] E2E OQ: `npx playwright test tests/e2e/oq/jd-url-error.spec.ts` — 5 tests pass
- [ ] Full regression: `npx playwright test` — all existing tests pass
- [ ] Manual UAT smoke test completed

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Self-Review Checklist

**Spec coverage:**
- ✅ `ScraperError.code` field — Task 1
- ✅ Structured `error_code` in 422 responses — Task 2
- ✅ Backend unit tests (`jd_url_invalid`, `jd_fetch_failed`) — Task 3
- ✅ `"skipped"` `StepState` variant with amber icon — Task 4
- ✅ Fault-tolerant JD URL block in overlay — Task 5
- ✅ `?jd_status=` redirect param — Task 5
- ✅ Dismissible amber banner on gaps page — Task 6
- ✅ Two copy variants (`url_invalid`, `fetch_failed`) — Task 6
- ✅ "Add job description →" CTA — Task 6
- ✅ Vitest overlay test — Task 7
- ✅ E2E Branch F tests — Task 8
- ✅ Coverage gate ≥75% — Task 9

**Type consistency:**
- `StepState` union extended in `step-checklist.tsx` Task 4 Step 1 — used in `processing-overlay.tsx` Task 5 immediately; no mismatch
- `jdFailReason` typed as `"url_invalid" | "fetch_failed" | null` in Task 5 Step 1 — used in query param construction in Task 5 Step 4; consistent
- `data-testid="jd-recovery-banner"`, `"jd-recovery-cta"`, `"jd-recovery-dismiss"` defined in Task 6 — referenced in Task 8; consistent

**No placeholders:** All code blocks are complete and runnable.
