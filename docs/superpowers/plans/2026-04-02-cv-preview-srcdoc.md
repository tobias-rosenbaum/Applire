# CV Preview srcDoc Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the Firefox cross-origin iframe block by replacing `<iframe src>` with a fetch-and-inject `<iframe srcDoc>` pattern, clean up now-unnecessary backend headers, and add unit + E2E tests.

**Architecture:** Three parallel tracks executed sequentially: (1) backend removes frame-restriction headers from `GET /api/cv/{id}/html`, (2) frontend `CVPreview.tsx` gains fetch state + srcDoc rendering with loading/error/retry states, (3) Vitest+RTL unit tests and Playwright cross-browser E2E tests are added. API contract, Jinja2 pipeline, and PDF path are unchanged.

**Tech Stack:** Next.js 15 / React 19, FastAPI, pytest + FastAPI TestClient, Vitest 3, @testing-library/react 16, Playwright

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `backend/tests/unit/__init__.py` | Empty — enables pytest discovery in unit/ |
| Create | `backend/tests/unit/test_cv_html_headers.py` | Asserts frame-restriction headers are absent |
| Modify | `backend/applire/routers/cv.py:71-77` | Remove `X-Frame-Options` and `Content-Security-Policy` headers |
| Modify | `frontend/package.json` | Add Vitest + RTL devDependencies |
| Create | `frontend/vitest.config.ts` | Vitest config: jsdom env, `@/` alias |
| Create | `frontend/components/cv/__tests__/CVPreview.test.tsx` | RTL unit tests: loading, loaded, error, retry |
| Modify | `frontend/components/cv/CVPreview.tsx` | Add fetch state + effect + srcDoc render |
| Modify | `playwright.config.ts` | Uncomment Firefox project |
| Create | `tests/e2e/cv-preview.spec.ts` | E2E: srcdoc assert + download smoke test |

---

## Task 1: Backend — Write failing test then remove frame-restriction headers (22.3)

**Files:**
- Create: `backend/tests/unit/test_cv_html_headers.py`
- Modify: `backend/applire/routers/cv.py:71-77`

- [ ] **Step 1.1: Create `backend/tests/unit/__init__.py`** (empty, needed for pytest discovery)

```bash
touch backend/tests/unit/__init__.py
```

- [ ] **Step 1.2: Create the unit test file**

```python
# backend/tests/unit/test_cv_html_headers.py
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from applire.auth import get_auth_provider
from applire.db.session import get_db
from applire.routers.cv import router

_TEST_CV_ID = str(uuid.UUID("12345678-1234-1234-1234-123456789012"))
_TEST_HTML = "<html><body><p>Max Mustermann</p></body></html>"


async def _stub_db():
    """Async generator stub — provides a None session, satisfying the Depends(get_db) contract."""
    yield None


@pytest.fixture()
def client():
    """Fresh minimal app per test, with auth and db overridden."""
    app = FastAPI()
    app.dependency_overrides[get_auth_provider] = lambda: None
    app.dependency_overrides[get_db] = _stub_db
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=True)


def test_html_endpoint_has_no_x_frame_options_header(client):
    with patch("applire.routers.cv.get_cv_html", new_callable=AsyncMock, return_value=_TEST_HTML):
        response = client.get(f"/api/cv/{_TEST_CV_ID}/html")

    assert response.status_code == 200
    assert "x-frame-options" not in response.headers


def test_html_endpoint_has_no_csp_frame_ancestors_header(client):
    with patch("applire.routers.cv.get_cv_html", new_callable=AsyncMock, return_value=_TEST_HTML):
        response = client.get(f"/api/cv/{_TEST_CV_ID}/html")

    assert response.status_code == 200
    assert "content-security-policy" not in response.headers


def test_html_endpoint_returns_html_content_type(client):
    with patch("applire.routers.cv.get_cv_html", new_callable=AsyncMock, return_value=_TEST_HTML):
        response = client.get(f"/api/cv/{_TEST_CV_ID}/html")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
```

- [ ] **Step 1.3: Run the tests — expect them to FAIL**

```bash
cd /home/applire/Documents/applire/Applire/Solution
python -m pytest backend/tests/unit/test_cv_html_headers.py -v
```

Expected: `FAILED` — `assert "x-frame-options" not in response.headers` fails because the header is currently present.

- [ ] **Step 1.4: Remove the frame-restriction headers from `cv.py`**

In `backend/applire/routers/cv.py`, replace lines 71–77:

```python
# FROM:
        return HTMLResponse(
            content=html,
            headers={
                "X-Frame-Options": "SAMEORIGIN",
                "Content-Security-Policy": "frame-ancestors 'self'",
            },
        )

# TO:
        return HTMLResponse(content=html)
```

- [ ] **Step 1.5: Run the tests — expect them to PASS**

```bash
python -m pytest backend/tests/unit/test_cv_html_headers.py -v
```

Expected:
```
PASSED backend/tests/unit/test_cv_html_headers.py::test_html_endpoint_has_no_x_frame_options_header
PASSED backend/tests/unit/test_cv_html_headers.py::test_html_endpoint_has_no_csp_frame_ancestors_header
PASSED backend/tests/unit/test_cv_html_headers.py::test_html_endpoint_returns_html_content_type
```

- [ ] **Step 1.6: Commit**

```bash
git add backend/tests/unit/__init__.py backend/tests/unit/test_cv_html_headers.py backend/applire/routers/cv.py
git commit -m "fix(backend): remove frame-restriction headers from CV HTML endpoint (22.3)"
```

---

## Task 2: Frontend — Set up Vitest + RTL (22.5 prerequisite)

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/vitest.config.ts`

- [ ] **Step 2.1: Install Vitest and RTL dependencies**

```bash
cd /home/applire/Documents/applire/Applire/Solution/frontend
npm install --save-dev \
  vitest \
  jsdom \
  @vitejs/plugin-react \
  @testing-library/react \
  @testing-library/user-event \
  @testing-library/jest-dom
```

Verify the installs appear in `package.json` devDependencies.

- [ ] **Step 2.2: Create `frontend/vitest.config.ts`**

```typescript
// frontend/vitest.config.ts
import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: [],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
});
```

- [ ] **Step 2.3: Add test script to `package.json`**

In `frontend/package.json`, add to `"scripts"`:

```json
"test": "vitest run",
"test:watch": "vitest"
```

- [ ] **Step 2.4: Verify Vitest is configured correctly (no tests yet)**

```bash
cd /home/applire/Documents/applire/Applire/Solution/frontend
npm test
```

Expected: `No test files found` or exit 0. Any import/config error here means the alias or plugin setup needs fixing.

- [ ] **Step 2.5: Commit**

```bash
git add frontend/package.json frontend/vitest.config.ts frontend/package-lock.json
git commit -m "chore(frontend): add Vitest + RTL testing setup (22.5)"
```

---

## Task 3: Frontend — Write failing RTL tests for CVPreview (22.5)

**Files:**
- Create: `frontend/components/cv/__tests__/CVPreview.test.tsx`

- [ ] **Step 3.1: Create the test file**

```tsx
// frontend/components/cv/__tests__/CVPreview.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { CVPreview } from "../CVPreview";

const BASE_PROPS = {
  cvId: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  template: "classic_german" as const,
  jobSummary: null,
  gapSummary: null,
  cvSummary: null,
  onRegenerateDifferent: vi.fn(),
  onRegenerateSame: vi.fn(),
  onNext: vi.fn(),
};

const TEST_HTML = "<html><body><p>Max Mustermann</p></body></html>";

describe("CVPreview", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders a loading skeleton while fetch is in flight", () => {
    vi.spyOn(globalThis, "fetch").mockReturnValue(new Promise(() => {})); // never resolves

    render(<CVPreview {...BASE_PROPS} />);

    expect(screen.queryByTestId("cv-iframe")).toBeNull();
    // The skeleton has the animate-pulse class
    const skeleton = document.querySelector(".animate-pulse");
    expect(skeleton).not.toBeNull();
  });

  it("renders iframe with srcDoc after successful fetch", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      text: async () => TEST_HTML,
    } as Response);

    render(<CVPreview {...BASE_PROPS} />);

    const iframe = await screen.findByTestId("cv-iframe");
    expect(iframe.getAttribute("srcdoc")).toBe(TEST_HTML);
    expect(iframe.getAttribute("sandbox")).toBe("allow-same-origin");
    expect(iframe.tagName.toLowerCase()).toBe("iframe");
  });

  it("renders error message with retry button when fetch fails", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network error"));

    render(<CVPreview {...BASE_PROPS} />);

    await screen.findByText("Vorschau konnte nicht geladen werden.");
    expect(
      screen.getByRole("button", { name: "Erneut versuchen" })
    ).toBeTruthy();
    expect(screen.queryByTestId("cv-iframe")).toBeNull();
  });

  it("re-fetches and shows iframe when retry button is clicked", async () => {
    const mockFetch = vi
      .spyOn(globalThis, "fetch")
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce({
        ok: true,
        text: async () => TEST_HTML,
      } as unknown as Response);

    render(<CVPreview {...BASE_PROPS} />);

    // Wait for error state
    await screen.findByText("Vorschau konnte nicht geladen werden.");

    // Click retry
    fireEvent.click(screen.getByRole("button", { name: "Erneut versuchen" }));

    // iframe should appear after re-fetch
    const iframe = await screen.findByTestId("cv-iframe");
    expect(iframe.getAttribute("srcdoc")).toBe(TEST_HTML);
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });
});
```

- [ ] **Step 3.2: Run tests — expect all 4 to FAIL**

```bash
cd /home/applire/Documents/applire/Applire/Solution/frontend
npm test
```

Expected: all 4 tests fail — `cv-iframe` not found, no skeleton, etc. — because `CVPreview.tsx` still uses the old `<iframe src>` pattern.

- [ ] **Step 3.3: Commit the failing tests**

```bash
git add frontend/components/cv/__tests__/CVPreview.test.tsx
git commit -m "test(frontend): add failing RTL tests for CVPreview srcDoc states (22.5)"
```

---

## Task 4: Frontend — Implement CVPreview srcDoc migration (22.1)

**Files:**
- Modify: `frontend/components/cv/CVPreview.tsx`

- [ ] **Step 4.1: Replace CVPreview.tsx with the srcDoc implementation**

Replace the entire file content:

```tsx
"use client";

import { useState, useEffect } from "react";
import { ScoreCircle } from "@/components/ui/score-circle";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

const TEMPLATE_LABELS: Record<string, string> = {
  classic_german: "Klassischer Lebenslauf",
  modern_swiss: "Modern Swiss CV",
};

interface CVSummary {
  cv_id: string;
  expires_at: string;
}

interface GapSummary {
  match_score: number;
}

interface JobSummary {
  role_title: string;
}

interface CVPreviewProps {
  cvId: string;
  template: "classic_german" | "modern_swiss";
  jobSummary: JobSummary | null;
  gapSummary: GapSummary | null;
  cvSummary: CVSummary | null;
  onRegenerateDifferent: () => void;
  onRegenerateSame: () => void;
  onNext: () => void;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("de-DE", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

export function CVPreview({
  cvId,
  template,
  jobSummary,
  gapSummary,
  cvSummary,
  onRegenerateDifferent,
  onRegenerateSame,
  onNext,
}: CVPreviewProps) {
  const [htmlContent, setHtmlContent] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setHtmlContent(null);
    setPreviewError(false);

    fetch(`${API_BASE}/api/cv/${cvId}/html`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load preview");
        return res.text();
      })
      .then((html) => {
        if (!cancelled) setHtmlContent(html);
      })
      .catch(() => {
        if (!cancelled) setPreviewError(true);
      });

    return () => {
      cancelled = true;
    };
  }, [cvId, retryCount]);

  const isExpired = cvSummary
    ? new Date(cvSummary.expires_at) < new Date()
    : false;

  async function handleDownload() {
    try {
      const res = await fetch(`${API_BASE}/api/cv/${cvId}/pdf`);
      if (!res.ok) return;
      const blob = await res.blob();
      const disposition = res.headers.get("Content-Disposition") ?? "";
      const match = disposition.match(/filename="([^"]+)"/);
      const filename = match?.[1] ?? `lebenslauf-${cvId.slice(0, 8)}.pdf`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // silently fail
    }
  }

  return (
    <div className="flex gap-6 h-[75vh] animate-fade-in">
      {/* Left metadata panel (40%) */}
      <div className="w-2/5 flex flex-col gap-4 bg-neutral-light rounded-xl p-5 overflow-y-auto shrink-0">
        {jobSummary && (
          <h2 className="text-lg font-heading font-bold text-neutral-dark leading-snug">
            {jobSummary.role_title}
          </h2>
        )}

        <span className="inline-block bg-teal text-white text-xs font-semibold px-3 py-1 rounded-full w-fit">
          {TEMPLATE_LABELS[template] ?? template}
        </span>

        {gapSummary && (
          <div className="flex justify-center py-2">
            <ScoreCircle score={Math.round(gapSummary.match_score * 100)} size={90} />
          </div>
        )}

        {cvSummary && !isExpired && (
          <div className="border-l-4 border-warning bg-warning-container rounded-r-lg p-3 text-xs text-neutral-dark">
            Verfügbar bis {formatDate(cvSummary.expires_at)}
          </div>
        )}
        {isExpired && (
          <div className="border-l-4 border-critical bg-critical-container rounded-r-lg p-3 text-xs text-neutral-dark">
            Abgelaufen. Bitte neu generieren.
          </div>
        )}

        <div className="flex flex-col gap-2 mt-auto">
          <button
            type="button"
            onClick={() => void handleDownload()}
            data-testid="download-button"
            className="w-full bg-success text-white font-semibold py-3 rounded-lg text-sm hover:opacity-90 transition-opacity"
          >
            PDF herunterladen
          </button>
          <button
            type="button"
            onClick={onRegenerateSame}
            className="w-full border border-teal text-teal font-semibold py-2.5 rounded-lg text-sm hover:opacity-90 transition-opacity"
          >
            Neu generieren
          </button>
          <button
            type="button"
            onClick={onRegenerateDifferent}
            className="w-full border border-teal text-teal font-semibold py-2.5 rounded-lg text-sm hover:opacity-90 transition-opacity"
          >
            Andere Vorlage
          </button>
          <button
            type="button"
            onClick={onNext}
            className="w-full bg-teal text-white font-semibold py-3 rounded-lg text-sm hover:opacity-90 transition-colors"
          >
            Was nun? →
          </button>
        </div>
      </div>

      {/* Right preview panel (60%) */}
      <div className="flex-1 bg-white rounded-xl shadow-soft overflow-hidden">
        {previewError ? (
          <div className="flex flex-col items-center justify-center h-full gap-3">
            <p className="text-sm text-gray-500">
              Vorschau konnte nicht geladen werden.
            </p>
            <button
              type="button"
              onClick={() => {
                setPreviewError(false);
                setRetryCount((c) => c + 1);
              }}
              className="text-sm text-teal underline hover:opacity-80"
            >
              Erneut versuchen
            </button>
          </div>
        ) : htmlContent ? (
          <iframe
            srcDoc={htmlContent}
            sandbox="allow-same-origin"
            title="Lebenslauf Vorschau"
            className="w-full h-full border-0"
            data-testid="cv-iframe"
          />
        ) : (
          <div className="w-full h-full animate-pulse bg-gray-100 rounded" />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4.2: Run RTL tests — expect all 4 to PASS**

```bash
cd /home/applire/Documents/applire/Applire/Solution/frontend
npm test
```

Expected:
```
✓ CVPreview > renders a loading skeleton while fetch is in flight
✓ CVPreview > renders iframe with srcDoc after successful fetch
✓ CVPreview > renders error message with retry button when fetch fails
✓ CVPreview > re-fetches and shows iframe when retry button is clicked
Test Files  1 passed (1)
Tests  4 passed (4)
```

If any test fails, re-read the test and component carefully before changing the implementation. The tests define the correct behavior.

- [ ] **Step 4.3: Commit**

```bash
git add frontend/components/cv/CVPreview.tsx
git commit -m "fix(frontend): replace cross-origin iframe src with srcDoc fetch pattern (22.1)"
```

---

## Task 5: E2E — Enable Firefox + write CV preview Playwright tests (22.2 + 22.4)

**Files:**
- Modify: `playwright.config.ts`
- Create: `tests/e2e/cv-preview.spec.ts`

- [ ] **Step 5.1: Enable Firefox project in `playwright.config.ts`**

Replace the `projects` array in `playwright.config.ts`:

```typescript
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
```

- [ ] **Step 5.2: Create the CV preview E2E spec**

```typescript
// tests/e2e/cv-preview.spec.ts
import { test, expect } from '@playwright/test';

const TEST_FLOW_ID = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee';
const TEST_CV_ID = 'cccccccc-cccc-cccc-cccc-cccccccccccc';
const TEST_JOB_ID = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb';
const CV_PAGE_URL = `/flow/${TEST_FLOW_ID}/cv`;

const MOCK_FLOW_STATE = {
  job_id: TEST_JOB_ID,
  job_summary: { role_title: 'Senior Software Engineer' },
  gap_summary: { match_score: 0.87 },
  cv_summary: {
    cv_id: TEST_CV_ID,
    pdf_url: `http://localhost:8001/api/cv/${TEST_CV_ID}/pdf`,
    expires_at: new Date(Date.now() + 86400000).toISOString(),
  },
};

const MOCK_CV_HTML = `<html><body>
  <h1>Max Mustermann</h1>
  <p>Senior Software Engineer</p>
</body></html>`;

test.describe('CV Preview — srcDoc rendering', () => {
  test.beforeEach(async ({ page }) => {
    // Mock flow state so the page skips to preview phase immediately
    await page.route(`**/api/flow/${TEST_FLOW_ID}/state`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_FLOW_STATE),
      });
    });

    // Mock the CV HTML endpoint
    await page.route(`**/api/cv/${TEST_CV_ID}/html`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: MOCK_CV_HTML,
      });
    });
  });

  test('iframe is present with non-empty srcdoc attribute', async ({ page }) => {
    const cspErrors: string[] = [];
    page.on('console', (msg) => {
      if (
        msg.type() === 'error' &&
        (msg.text().includes('Content-Security-Policy') ||
          msg.text().includes('frame-ancestors') ||
          msg.text().includes('X-Frame-Options'))
      ) {
        cspErrors.push(msg.text());
      }
    });

    await page.goto(CV_PAGE_URL);

    // Wait for iframe to appear
    const iframe = page.locator('[data-testid="cv-iframe"]');
    await expect(iframe).toBeVisible({ timeout: 10000 });

    // srcdoc attribute must be non-empty
    const srcdoc = await iframe.getAttribute('srcdoc');
    expect(srcdoc).toBeTruthy();
    expect(srcdoc!.length).toBeGreaterThan(0);

    // sandbox attribute must be present
    const sandbox = await iframe.getAttribute('sandbox');
    expect(sandbox).toBe('allow-same-origin');

    // No CSP or frame-blocking console errors
    expect(cspErrors).toHaveLength(0);
  });

  test('iframe renders visible text content from CV HTML', async ({ page }) => {
    await page.goto(CV_PAGE_URL);

    const iframe = page.locator('[data-testid="cv-iframe"]');
    await expect(iframe).toBeVisible({ timeout: 10000 });

    // Access the iframe's content frame
    const frame = page.frameLocator('[data-testid="cv-iframe"]');
    await expect(frame.locator('h1')).toHaveText('Max Mustermann', { timeout: 5000 });
  });

  test('download button triggers PDF fetch', async ({ page }) => {
    // Mock the PDF endpoint
    let pdfFetched = false;
    await page.route(`**/api/cv/${TEST_CV_ID}/pdf`, async (route) => {
      pdfFetched = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/pdf',
        headers: {
          'Content-Disposition': `attachment; filename="lebenslauf-test.pdf"`,
        },
        body: Buffer.from('%PDF-1.4 mock content'),
      });
    });

    await page.goto(CV_PAGE_URL);

    // Wait for preview to be ready
    await expect(page.locator('[data-testid="cv-iframe"]')).toBeVisible({
      timeout: 10000,
    });

    // Click download — use waitForEvent to capture the download
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('[data-testid="download-button"]'),
    ]);

    expect(download).toBeTruthy();
    expect(pdfFetched).toBe(true);
  });
});
```

- [ ] **Step 5.3: Install Firefox browser for Playwright (if not already installed)**

```bash
cd /home/applire/Documents/applire/Applire/Solution
npx playwright install firefox
```

Expected: Firefox browser binaries downloaded. If already installed: `Skipping browser install`.

- [ ] **Step 5.4: Verify test syntax is correct (dry run, no server needed)**

```bash
npx playwright test tests/e2e/cv-preview.spec.ts --list
```

Expected: lists 3 tests × 2 projects (chromium, firefox) = 6 tests listed. Any syntax error will surface here without needing the app running.

- [ ] **Step 5.5: Commit**

```bash
git add playwright.config.ts tests/e2e/cv-preview.spec.ts
git commit -m "test(e2e): add CV preview srcDoc tests on Chromium + Firefox (22.2, 22.4)"
```

---

## Running the Full E2E Suite

The E2E tests require the full stack running. With Docker:

```bash
cd /home/applire/Documents/applire/Applire/Solution
docker-compose up -d
# Wait for services to be healthy
npx playwright test tests/e2e/cv-preview.spec.ts --headed
```

To run all projects:
```bash
npx playwright test tests/e2e/cv-preview.spec.ts --project=chromium --project=firefox
```

---

## Done When

- [ ] `GET /api/cv/{id}/html` returns no `X-Frame-Options` or `Content-Security-Policy` headers
- [ ] All 3 backend unit tests pass (`pytest backend/tests/unit/test_cv_html_headers.py`)
- [ ] All 4 RTL unit tests pass (`npm test` in `frontend/`)
- [ ] Firefox renders CV preview without console errors or blank iframe
- [ ] Chrome continues to render correctly
- [ ] PDF download works in both browsers
- [ ] Playwright E2E tests pass on Chromium and Firefox
