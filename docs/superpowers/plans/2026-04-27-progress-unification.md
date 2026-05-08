# Progress Indicator Unification + Cover Letter Bug Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unify the three progress experiences (upload overlay, CV generation, cover letter) into one shared `ProgressWidget` component; fix the cover letter `letterData` bug; add all new strings in DE + EN.

**Architecture:** A new purely-presentational `ProgressWidget` accepts an array of `ProgressStep` objects and renders an SVG ring (step-derived %) + animated step list. The three existing components are refactored to drive this widget. The backend `CoverLetterStatusResponse` is extended to include `letter_data` when status is `ready`, which the frontend stores in state so the content-editing tab receives real data.

**Tech Stack:** Python 3.12 / Pydantic v2, Next.js 15 / React 19 / TypeScript strict, Tailwind CSS v4 (custom theme tokens from `globals.css`), `next-intl` v4, Vitest + Testing Library, pytest-asyncio.

---

## File Map

| Action | File |
|---|---|
| Modify | `backend/applire/schemas/cover_letter.py` |
| Modify | `backend/applire/services/cover_letter.py` |
| Modify | `tests/unit/test_cover_letter.py` |
| Modify | `frontend/app/globals.css` |
| **Create** | `frontend/components/ui/progress-widget.tsx` |
| **Create** | `frontend/components/ui/__tests__/ProgressWidget.test.tsx` |
| Modify | `frontend/components/processing-overlay.tsx` |
| Modify | `frontend/components/__tests__/ProcessingOverlay.test.tsx` |
| Modify | `frontend/components/cv/GenerationProgress.tsx` |
| Modify | `frontend/app/(shell)/flow/[flowId]/cover-letter/page.tsx` |
| Modify | `frontend/messages/de.json` |
| Modify | `frontend/messages/en.json` |

---

## Task 1 — Backend: expose `letter_data` in cover letter status response

**Files:**
- Modify: `backend/applire/schemas/cover_letter.py`
- Modify: `backend/applire/services/cover_letter.py`
- Modify: `tests/unit/test_cover_letter.py`

- [ ] **Step 1: Write two failing tests** — append to `tests/unit/test_cover_letter.py` after the existing `test_get_cover_letter_status_ready_has_urls` test:

```python
@pytest.mark.asyncio
async def test_get_cover_letter_status_ready_includes_letter_data(db):
    """When status is ready, letter_data must be returned in the response."""
    from applire.models.cover_letter import GeneratedCoverLetter, CoverLetterStatus
    from applire.services.cover_letter import get_cover_letter_status

    letter_data = {"header": {"name": "Test User"}, "body": {"paragraphs": ["Hello"]}}
    cl = GeneratedCoverLetter(
        job_analysis_id=uuid.uuid4(),
        profile_id=uuid.uuid4(),
        template="classic_german",
        letter_data=letter_data,
        pre_gen_inputs={},
        status=CoverLetterStatus.ready.value,
    )
    db.add(cl)
    await db.commit()
    await db.refresh(cl)

    result = await get_cover_letter_status(cl.id, db, "http://localhost:8001")
    assert result.letter_data == letter_data


@pytest.mark.asyncio
async def test_get_cover_letter_status_pending_letter_data_is_none(db):
    """When status is not ready, letter_data must be None."""
    from applire.models.cover_letter import GeneratedCoverLetter, CoverLetterStatus
    from applire.services.cover_letter import get_cover_letter_status

    cl = GeneratedCoverLetter(
        job_analysis_id=uuid.uuid4(),
        profile_id=uuid.uuid4(),
        template="classic_german",
        letter_data={"body": {"paragraphs": ["draft"]}},
        pre_gen_inputs={},
        status=CoverLetterStatus.generating.value,
    )
    db.add(cl)
    await db.commit()
    await db.refresh(cl)

    result = await get_cover_letter_status(cl.id, db, "http://localhost:8001")
    assert result.letter_data is None
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /home/apliqa/Documents/Applire/Applire-Core/.worktrees/sprint-31
python3 -m pytest tests/unit/test_cover_letter.py::test_get_cover_letter_status_ready_includes_letter_data tests/unit/test_cover_letter.py::test_get_cover_letter_status_pending_letter_data_is_none -v
```

Expected: `FAILED` — `CoverLetterStatusResponse` has no `letter_data` attribute.

- [ ] **Step 3: Add `letter_data` field to `CoverLetterStatusResponse`**

In `backend/applire/schemas/cover_letter.py`, update the `CoverLetterStatusResponse` class (currently ends at the `model_config` line) to add the new field:

```python
class CoverLetterStatusResponse(BaseModel):
    cover_letter_id: uuid.UUID
    status: CoverLetterStatus
    html_url: Optional[str] = None
    pdf_url: Optional[str] = None
    error_message: Optional[str] = None
    expires_at: datetime
    letter_data: Optional[dict] = None  # populated only when status == ready

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Populate `letter_data` in the service**

In `backend/applire/services/cover_letter.py`, update `get_cover_letter_status()`. Find the return statement (currently around line 175) and update it:

```python
    letter_data = None
    if cl.status == CoverLetterStatus.ready.value:
        html_url = f"{base_url}/api/cover-letter/{cl_id}/html"
        pdf_url = f"{base_url}/api/cover-letter/{cl_id}/pdf"
        letter_data = cl.letter_data

    return CoverLetterStatusResponse(
        cover_letter_id=cl.id,
        status=cl.status,
        html_url=html_url,
        pdf_url=pdf_url,
        error_message=cl.error_message,
        expires_at=cl.expires_at,
        letter_data=letter_data,
    )
```

(Also remove the two separate `html_url = None` / `pdf_url = None` lines that precede the existing `if cl.status == CoverLetterStatus.ready.value:` block — the new code above replaces them.)

- [ ] **Step 5: Run tests to confirm they pass**

```bash
python3 -m pytest tests/unit/test_cover_letter.py::test_get_cover_letter_status_ready_includes_letter_data tests/unit/test_cover_letter.py::test_get_cover_letter_status_pending_letter_data_is_none -v
```

Expected: both `PASSED`.

- [ ] **Step 6: Run the full cover letter unit test suite**

```bash
python3 -m pytest tests/unit/test_cover_letter.py -v
```

Expected: all tests pass. Coverage should stay ≥ 75%.

- [ ] **Step 7: Commit**

```bash
git add backend/applire/schemas/cover_letter.py backend/applire/services/cover_letter.py tests/unit/test_cover_letter.py
git commit -m "feat(cover-letter): expose letter_data in status response when ready"
```

---

## Task 2 — i18n: add new keys to de.json and en.json

**Files:**
- Modify: `frontend/messages/de.json`
- Modify: `frontend/messages/en.json`

- [ ] **Step 1: Add `uploadingCVN` key to the `processing` namespace in `de.json`**

Locate the `"processing"` object (around line 36). Add after the existing `"uploadingCV"` line:

```json
"uploadingCVN": "Lebenslauf {n} von {total} wird hochgeladen",
```

- [ ] **Step 2: Add progress keys to the `coverLetter` namespace in `de.json`**

Locate the `"coverLetter"` object (around line 234). Add before the closing `}`:

```json
"progressSubtitle": "KI formuliert Ihr Anschreiben",
"stepPreparing": "Daten werden aufbereitet",
"stepGenerating": "Anschreiben wird generiert",
"stepReady": "Fertig"
```

- [ ] **Step 3: Apply the same additions to `en.json`**

In the `"processing"` object, add after `"uploadingCV"`:

```json
"uploadingCVN": "Uploading CV {n} of {total}",
```

In the `"coverLetter"` object, add before the closing `}`:

```json
"progressSubtitle": "AI is writing your cover letter",
"stepPreparing": "Preparing data",
"stepGenerating": "Generating cover letter",
"stepReady": "Done"
```

- [ ] **Step 4: Verify JSON is valid**

```bash
python3 -c "import json; json.load(open('frontend/messages/de.json')); json.load(open('frontend/messages/en.json')); print('valid')"
```

Expected: `valid`

- [ ] **Step 5: Commit**

```bash
git add frontend/messages/de.json frontend/messages/en.json
git commit -m "feat(i18n): add progress widget keys for cover letter and multi-CV upload"
```

---

## Task 3 — Add shimmer animation to `globals.css`

**Files:**
- Modify: `frontend/app/globals.css`

- [ ] **Step 1: Append shimmer keyframe and utility class to `globals.css`**

Open `frontend/app/globals.css`. After the existing `@keyframes slide-up` block (around line 95), add:

```css
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.animate-shimmer {
  background: linear-gradient(
    90deg,
    var(--color-gold-container),
    rgba(254, 203, 0, 0.06),
    var(--color-gold-container)
  );
  background-size: 200% 100%;
  animation: shimmer 2s ease infinite;
}
```

- [ ] **Step 2: Verify the dev server starts without CSS errors**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

Expected: build succeeds (exit 0, no CSS parse errors).

- [ ] **Step 3: Commit**

```bash
git add frontend/app/globals.css
git commit -m "feat(ui): add shimmer keyframe animation for progress widget active step"
```

---

## Task 4 — Create `ProgressWidget` component

**Files:**
- Create: `frontend/components/ui/progress-widget.tsx`
- Create: `frontend/components/ui/__tests__/ProgressWidget.test.tsx`

- [ ] **Step 1: Write the failing test file** — create `frontend/components/ui/__tests__/ProgressWidget.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ProgressWidget } from "../progress-widget";

const makeSteps = (statuses: Array<"done" | "active" | "pending">) =>
  statuses.map((status, i) => ({ label: `Step ${i + 1}`, status }));

describe("ProgressWidget", () => {
  it("shows 0% when no steps are done", () => {
    render(
      <ProgressWidget
        steps={makeSteps(["active", "pending", "pending"])}
        title="Loading"
      />
    );
    expect(screen.getByText("0%")).toBeInTheDocument();
  });

  it("shows 33% when 1 of 3 steps is done", () => {
    render(
      <ProgressWidget
        steps={makeSteps(["done", "active", "pending"])}
        title="Loading"
      />
    );
    expect(screen.getByText("33%")).toBeInTheDocument();
  });

  it("shows 100% when all steps are done", () => {
    render(
      <ProgressWidget
        steps={makeSteps(["done", "done", "done"])}
        title="Loading"
      />
    );
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("renders title and optional subtitle", () => {
    render(
      <ProgressWidget
        steps={makeSteps(["active"])}
        title="Analysing"
        subtitle="This takes a moment"
      />
    );
    expect(screen.getByText("Analysing")).toBeInTheDocument();
    expect(screen.getByText("This takes a moment")).toBeInTheDocument();
  });

  it("applies animate-shimmer class to active step row", () => {
    const { container } = render(
      <ProgressWidget
        steps={makeSteps(["done", "active", "pending"])}
        title="Working"
      />
    );
    const rows = container.querySelectorAll("[data-step-status]");
    expect(rows[1].getAttribute("data-step-status")).toBe("active");
    expect(rows[1].className).toContain("animate-shimmer");
  });

  it("renders step labels", () => {
    render(
      <ProgressWidget
        steps={[
          { label: "First step", status: "done" },
          { label: "Second step", status: "active" },
        ]}
        title="Test"
      />
    );
    expect(screen.getByText("First step")).toBeInTheDocument();
    expect(screen.getByText("Second step")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
cd frontend && npx vitest run components/ui/__tests__/ProgressWidget.test.tsx 2>&1 | tail -10
```

Expected: `FAIL` — module not found.

- [ ] **Step 3: Create `frontend/components/ui/progress-widget.tsx`**

```tsx
"use client";

import { cn } from "@/lib/utils";

export type ProgressStepStatus = "done" | "active" | "pending";

export interface ProgressStep {
  label: string;
  status: ProgressStepStatus;
}

interface ProgressWidgetProps {
  steps: ProgressStep[];
  title: string;
  subtitle?: string;
  className?: string;
}

const RING_R = 30;
const CIRCUMFERENCE = 2 * Math.PI * RING_R; // ≈ 188.5

function StepIcon({ status }: { status: ProgressStepStatus }) {
  if (status === "done") {
    return (
      <div className="flex-shrink-0 w-4 h-4 rounded-full bg-primary flex items-center justify-center">
        <svg className="w-2.5 h-2.5" fill="none" stroke="white" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
        </svg>
      </div>
    );
  }
  if (status === "active") {
    return (
      <div className="flex-shrink-0 w-4 h-4 rounded-full border-2 border-gold-dim flex items-center justify-center">
        <div className="w-1.5 h-1.5 rounded-full bg-gold-dim animate-pulse" />
      </div>
    );
  }
  return (
    <div className="flex-shrink-0 w-4 h-4 rounded-full border-2 border-outline-variant" />
  );
}

export function ProgressWidget({ steps, title, subtitle, className }: ProgressWidgetProps) {
  const doneCount = steps.filter((s) => s.status === "done").length;
  const pct = steps.length === 0 ? 0 : Math.round((doneCount / steps.length) * 100);
  const offset = CIRCUMFERENCE - (pct / 100) * CIRCUMFERENCE;

  return (
    <div className={cn("flex flex-col items-center", className)}>
      {/* Ring */}
      <div className="relative w-20 h-20 mb-4">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 72 72" aria-hidden="true">
          <circle
            cx="36" cy="36" r={RING_R}
            fill="none"
            className="stroke-surface-container-high"
            strokeWidth="5"
          />
          <circle
            cx="36" cy="36" r={RING_R}
            fill="none"
            className="stroke-primary"
            strokeWidth="5.5"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: "stroke-dashoffset 0.6s ease" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-lg font-extrabold text-primary leading-none">{pct}%</span>
          <span className="text-[8px] font-semibold tracking-widest uppercase text-on-surface-variant mt-0.5">
            done
          </span>
        </div>
      </div>

      {/* Title + subtitle */}
      <div className="text-center mb-4">
        <p className="font-semibold text-sm text-primary">{title}</p>
        {subtitle && (
          <p className="text-xs text-on-surface-variant mt-0.5">{subtitle}</p>
        )}
      </div>

      {/* Steps */}
      <div className="w-full space-y-1.5">
        {steps.map((step, i) => (
          <div
            key={i}
            data-step-status={step.status}
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs transition-all duration-200",
              step.status === "done" && "bg-primary-container/20",
              step.status === "active" && "animate-shimmer border border-gold/40",
              step.status === "pending" && "opacity-40"
            )}
          >
            <StepIcon status={step.status} />
            <span
              className={cn(
                "font-medium",
                step.status === "active" && "font-bold text-gold-dim",
                step.status !== "active" && "text-on-surface"
              )}
            >
              {step.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd frontend && npx vitest run components/ui/__tests__/ProgressWidget.test.tsx 2>&1 | tail -10
```

Expected: all 6 tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add frontend/components/ui/progress-widget.tsx frontend/components/ui/__tests__/ProgressWidget.test.tsx
git commit -m "feat(ui): add ProgressWidget shared component with SVG ring and shimmer steps"
```

---

## Task 5 — Refactor `ProcessingOverlay`: dynamic CV steps + `ProgressWidget`

**Files:**
- Modify: `frontend/components/processing-overlay.tsx`
- Modify: `frontend/components/__tests__/ProcessingOverlay.test.tsx`

- [ ] **Step 1: Add a failing test for the multi-CV step count**

Append to `frontend/components/__tests__/ProcessingOverlay.test.tsx`:

```tsx
it("renders one step per uploaded CV file when multiple files are provided", async () => {
  const file1 = new File(["cv1"], "cv1.pdf", { type: "application/pdf" });
  const file2 = new File(["cv2"], "cv2.pdf", { type: "application/pdf" });
  const file3 = new File(["cv3"], "cv3.pdf", { type: "application/pdf" });

  vi.spyOn(globalThis, "fetch").mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ flow_id: "flow-multi" }),
  } as Response);

  render(
    withIntl(
      <ProcessingOverlay
        files={[file1, file2, file3]}
        jdMode="text"
        jdUrl=""
        jdText=""
        onCancel={vi.fn()}
      />
    )
  );

  // Each CV gets its own numbered step label
  await waitFor(
    () => {
      expect(screen.getByText("Uploading CV 1 of 3")).toBeInTheDocument();
    },
    { timeout: 5000 }
  );
});
```

- [ ] **Step 2: Run the test to confirm it fails**

```bash
cd frontend && npx vitest run components/__tests__/ProcessingOverlay.test.tsx --reporter=verbose 2>&1 | tail -20
```

Expected: the new test `FAILED` — "Uploading CV 1 of 3" not found.

- [ ] **Step 3: Rewrite `processing-overlay.tsx`**

Replace the entire file content:

```tsx
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { Card } from "@/components/ui/card";
import { ProgressWidget, ProgressStep } from "@/components/ui/progress-widget";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

async function apiErrorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    const detail = body.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail))
      return detail.map((e: { msg?: string }) => e.msg ?? JSON.stringify(e)).join("; ");
    return res.statusText || `HTTP ${res.status}`;
  } catch {
    return res.statusText || `HTTP ${res.status}`;
  }
}

type StepState = "pending" | "in_progress" | "completed" | "skipped";

interface Props {
  files: File[];
  jdMode: "url" | "text";
  jdUrl: string;
  jdText: string;
  onCancel: () => void;
}

export function ProcessingOverlay({ files, jdMode, jdUrl, jdText, onCancel }: Props) {
  const router = useRouter();
  const t = useTranslations("processing");

  // Build step keys + labels once — one upload step per file
  const STEPS = useMemo(() => [
    { key: "analyze_jd", label: t("analyzingJD") },
    ...files.map((_, i) => ({
      key: `upload_${i}`,
      label:
        files.length === 1
          ? t("uploadingCV")
          : t("uploadingCVN", { n: i + 1, total: files.length }),
    })),
    { key: "build_profile", label: t("buildingProfile") },
    { key: "detect_gaps", label: t("detectingGaps") },
  ], []); // eslint-disable-line react-hooks/exhaustive-deps

  const [stepStates, setStepStates] = useState<Record<string, StepState>>(
    () => Object.fromEntries(STEPS.map((s) => [s.key, "pending" as StepState]))
  );
  const [error, setError] = useState<string | null>(null);
  const started = useRef(false);

  function markStep(key: string, state: StepState) {
    setStepStates((prev) => ({ ...prev, [key]: state }));
  }

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    async function runPipeline() {
      try {
        let jobId: string | null = null;
        let jdFailReason: "url_invalid" | "fetch_failed" | null = null;

        // Step 1: Analyze Job Description
        markStep("analyze_jd", "in_progress");
        if (jdMode === "url" && jdUrl.trim()) {
          const res = await fetch(`${API_BASE}/api/job/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: jdUrl.trim() }),
          });
          if (!res.ok) {
            if (res.status === 422) {
              let body: { detail?: { error_code?: string; message?: string } | string | unknown[] } | null = null;
              try { body = await res.json(); } catch { /* body stays null */ }
              const detail =
                body?.detail && typeof body.detail === "object" && !Array.isArray(body.detail)
                  ? body.detail
                  : null;
              const errorCode = detail?.error_code;
              if (errorCode === "jd_url_invalid") {
                markStep("analyze_jd", "skipped");
                jdFailReason = "url_invalid";
              } else if (errorCode === "jd_fetch_failed") {
                markStep("analyze_jd", "skipped");
                jdFailReason = "fetch_failed";
              } else {
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
            markStep("analyze_jd", "completed");
          }
        } else if (jdMode === "text" && jdText.trim()) {
          const res = await fetch(`${API_BASE}/api/job/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: jdText }),
          });
          if (!res.ok) throw new Error(await apiErrorMessage(res));
          const data = await res.json();
          jobId = data.id;
          markStep("analyze_jd", "completed");
        } else {
          markStep("analyze_jd", "completed");
        }

        // Steps 2…N+1: Upload each CV individually
        let flowId: string;
        if (jobId !== null) {
          const appRes = await fetch(`${API_BASE}/api/applications`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ job_analysis_id: jobId, start_workflow: true }),
          });
          if (!appRes.ok) throw new Error(await apiErrorMessage(appRes));
          const appData = await appRes.json();
          flowId = appData.flow_session_id;
        } else {
          const flowRes = await fetch(`${API_BASE}/api/flow`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ job_id: null }),
          });
          if (!flowRes.ok) throw new Error(await apiErrorMessage(flowRes));
          const flow = await flowRes.json();
          flowId = flow.flow_id;
        }

        for (let i = 0; i < files.length; i++) {
          const stepKey = `upload_${i}`;
          markStep(stepKey, "in_progress");
          const formData = new FormData();
          formData.append("file", files[i]);
          const uploadRes = await fetch(`${API_BASE}/api/profile/upload`, {
            method: "POST",
            body: formData,
          });
          if (!uploadRes.ok) throw new Error(await apiErrorMessage(uploadRes));
          markStep(stepKey, "completed");
        }

        // Step N+2: Build profile
        markStep("build_profile", "in_progress");
        await new Promise((r) => setTimeout(r, 400));
        markStep("build_profile", "completed");

        // Step N+3: Detect gaps
        markStep("detect_gaps", "in_progress");

        if (!jobId) {
          markStep("detect_gaps", "completed");
          await new Promise((r) => setTimeout(r, 400));
          const gapsUrl = jdFailReason
            ? `/flow/${flowId}/gaps?jd_status=${jdFailReason}`
            : `/flow/${flowId}/gaps`;
          router.push(gapsUrl);
          return;
        }

        const stateRes = await fetch(`${API_BASE}/api/flow/${flowId}/state`);
        if (!stateRes.ok) throw new Error("Could not retrieve flow state");
        const flowState = await stateRes.json();
        const linkedJobId: string = flowState.job_id ?? jobId;

        const gapRes = await fetch(`${API_BASE}/api/job/${linkedJobId}/gaps`, { method: "POST" });
        if (!gapRes.ok) throw new Error(await apiErrorMessage(gapRes));
        const gapData = await gapRes.json();

        await fetch(`${API_BASE}/api/flow/${flowId}/advance`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ step: "gap_analysis", artifact_id: gapData.id ?? null }),
        });

        markStep("detect_gaps", "completed");
        await new Promise((r) => setTimeout(r, 400));

        const gapsUrl = jdFailReason
          ? `/flow/${flowId}/gaps?jd_status=${jdFailReason}`
          : `/flow/${flowId}/gaps`;
        router.push(gapsUrl);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "An error occurred. Please try again.");
      }
    }

    runPipeline();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Map internal step states → ProgressWidget format
  const widgetSteps: ProgressStep[] = STEPS.map((step) => {
    const state = stepStates[step.key] ?? "pending";
    return {
      label: step.label,
      status:
        state === "completed" || state === "skipped"
          ? "done"
          : state === "in_progress"
          ? "active"
          : "pending",
    };
  });

  return (
    <div data-testid="processing-indicator" className="fixed inset-0 z-50 flex items-center justify-center bg-primary/5 backdrop-blur-sm px-4">
      <Card className="w-full max-w-[480px] p-8">
        {error ? (
          <div className="space-y-4">
            <div data-testid="processing-error" className="p-4 rounded-lg bg-critical/10 border border-critical/20">
              <p className="text-sm text-critical">{error}</p>
            </div>
            <div className="flex justify-center">
              <button
                onClick={onCancel}
                data-testid="cancel-button"
                className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-neutral-dark transition-colors"
              >
                {t("goBack")}
              </button>
            </div>
          </div>
        ) : (
          <ProgressWidget
            steps={widgetSteps}
            title={t("title")}
            subtitle={t("subtitle")}
          />
        )}
      </Card>
    </div>
  );
}
```

- [ ] **Step 4: Run all `ProcessingOverlay` tests**

```bash
cd frontend && npx vitest run components/__tests__/ProcessingOverlay.test.tsx --reporter=verbose 2>&1 | tail -20
```

Expected: all tests pass (including the 3 existing JD error tests + the new multi-CV test).

- [ ] **Step 5: Commit**

```bash
git add frontend/components/processing-overlay.tsx frontend/components/__tests__/ProcessingOverlay.test.tsx
git commit -m "feat(upload): dynamic per-CV progress steps with unified ProgressWidget"
```

---

## Task 6 — Refactor `GenerationProgress`: use `ProgressWidget`

**Files:**
- Modify: `frontend/components/cv/GenerationProgress.tsx`

No new i18n keys needed — the existing `generationTitle`, `generationHint`, `stepQueued`, `stepRendering`, `stepDone` keys are reused.

- [ ] **Step 1: Replace `GenerationProgress.tsx`**

Replace the entire file:

```tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { ProgressWidget, ProgressStep } from "@/components/ui/progress-widget";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";
const POLL_INTERVAL_MS = 3000;
const STALENESS_MS = 60_000;

type CVStatus = "pending" | "generating" | "ready" | "failed" | "expired";

interface CVStatusResponse {
  cv_id: string;
  status: CVStatus;
  error_message: string | null;
  expires_at: string;
}

interface GenerationProgressProps {
  cvId: string;
  flowId: string;
  onReady: (cvId: string) => void;
  onRetry: () => void;
}

function activeStepIndex(status: CVStatus): number {
  if (status === "pending") return 0;
  if (status === "generating") return 1;
  if (status === "ready") return 2;
  return 0;
}

export function GenerationProgress({ cvId, flowId, onReady, onRetry }: GenerationProgressProps) {
  const t = useTranslations("cv");
  const [status, setStatus] = useState<CVStatus>("pending");
  const [error, setError] = useState<string | null>(null);
  const [stale, setStale] = useState(false);
  const startedAt = useRef(Date.now());
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    async function poll() {
      if (Date.now() - startedAt.current > STALENESS_MS) {
        setStale(true);
      }

      try {
        const res = await fetch(`${API_BASE}/api/cv/${cvId}/status`);
        if (!res.ok) return;
        const data: CVStatusResponse = await res.json();
        setStatus(data.status);

        if (data.status === "ready") {
          if (intervalRef.current) clearInterval(intervalRef.current);
          try {
            await fetch(`${API_BASE}/api/flow/${flowId}/advance`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ step: "cv_generation", artifact_id: cvId }),
            });
          } catch {
            // non-fatal
          }
          onReady(cvId);
        } else if (data.status === "failed") {
          if (intervalRef.current) clearInterval(intervalRef.current);
          setError(data.error_message ?? t("generationFailed"));
        }
      } catch {
        // Continue polling on network errors
      }
    }

    void poll();
    intervalRef.current = setInterval(() => void poll(), POLL_INTERVAL_MS);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [cvId, flowId, onReady, t]);

  const stepLabels = [t("stepQueued"), t("stepRendering"), t("stepDone")];
  const activeIndex = activeStepIndex(status);

  const widgetSteps: ProgressStep[] = stepLabels.map((label, i) => ({
    label,
    status: i < activeIndex ? "done" : i === activeIndex ? "active" : "pending",
  }));

  return (
    <div className="max-w-sm mx-auto animate-fade-in py-8">
      <ProgressWidget
        steps={widgetSteps}
        title={t("generationTitle")}
        subtitle={t("generationHint")}
      />

      {stale && !error && (
        <div className="mt-6 border-l-4 border-warning bg-warning-container rounded-r-lg p-3 text-sm text-neutral-dark">
          {t("generationStale")}
        </div>
      )}

      {error && (
        <div className="mt-6 border-l-4 border-critical bg-critical-container rounded-r-lg p-4">
          <p className="text-sm text-neutral-dark mb-2">{error}</p>
          <button
            type="button"
            onClick={onRetry}
            className="text-sm font-semibold text-critical hover:underline"
          >
            {t("retryGeneration")}
          </button>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Run the full frontend unit test suite**

```bash
cd frontend && npm test 2>&1 | tail -10
```

Expected: all tests pass (no `GenerationProgress` tests exist yet — this step is a sanity check that no other test broke).

- [ ] **Step 3: Commit**

```bash
git add frontend/components/cv/GenerationProgress.tsx
git commit -m "feat(cv): replace static step circles with unified ProgressWidget"
```

---

## Task 7 — Cover letter page: add progress widget and fix `letterData`

**Files:**
- Modify: `frontend/app/(shell)/flow/[flowId]/cover-letter/page.tsx`

- [ ] **Step 1: Update the type annotation for the status API response in `startPolling`**

The `startPolling` function currently casts the response as `{ status: string }`. Widen it to include `letter_data`:

```tsx
const data = await res.json() as {
  status: string;
  letter_data?: Record<string, unknown> | null;
};
```

Then update the `data.status === "ready"` branch inside `startPolling` to also store `letter_data`:

```tsx
if (data.status === "ready") {
  clearInterval(pollRef.current!);
  setPhase("ready");
  setClState((prev) =>
    prev ? { ...prev, status: "ready", letterData: data.letter_data ?? null } : prev
  );
}
```

- [ ] **Step 2: Update `init()` to store `letter_data` when cover letter is already ready**

In `init()`, the `statusData` fetch result is currently typed as `{ status: string }`. Widen it:

```tsx
const statusData = await statusRes.json() as {
  status: string;
  letter_data?: Record<string, unknown> | null;
};
```

Then update the state initialization to include `letter_data`:

```tsx
setClState({
  coverLetterId: clId,
  status: statusData.status,
  template: clSummary.template as CLTemplate,
  letterData: statusData.status === "ready" ? (statusData.letter_data ?? null) : null,
  preGenInputs: null,
  jobId: flowData.job_id ?? null,
  roleTitle: flowData.job_summary?.role_title ?? null,
});
```

- [ ] **Step 3: Add the `ProgressWidget` import and replace the generating phase UI**

At the top of the file, add the import:

```tsx
import { ProgressWidget, ProgressStep } from "@/components/ui/progress-widget";
```

Replace the `phase === "generating"` branch in the JSX (currently a single `<div>` with the text):

```tsx
{phase === "generating" ? (
  <div className="flex items-center justify-center flex-1">
    <ProgressWidget
      steps={clProgressSteps(clState?.status ?? "pending")}
      title={t("generating")}
      subtitle={t("progressSubtitle")}
      className="max-w-xs w-full"
    />
  </div>
) : (
  // ... existing ready phase JSX unchanged
)}
```

- [ ] **Step 4: Add the `clProgressSteps` helper inside the component**

Add this function just before the `return` statement:

```tsx
function clProgressSteps(status: string): ProgressStep[] {
  const stepDefs = [
    { label: t("stepPreparing"), matchStatuses: [] as string[] },
    { label: t("stepGenerating"), matchStatuses: ["generating"] },
    { label: t("stepReady"),      matchStatuses: ["ready"] },
  ];
  const activeIndex =
    status === "ready" ? 2 : status === "generating" ? 1 : 0;

  return stepDefs.map((step, i) => ({
    label: step.label,
    status: i < activeIndex ? "done" : i === activeIndex ? "active" : "pending",
  }));
}
```

- [ ] **Step 5: Build to catch TypeScript errors**

```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -E "error|warning" | head -20
```

Expected: zero TypeScript errors.

- [ ] **Step 6: Run the full frontend unit test suite**

```bash
cd frontend && npm test 2>&1 | tail -10
```

Expected: all tests pass.

- [ ] **Step 7: Run the full backend unit test suite**

```bash
python3 -m pytest tests/unit/ -q --tb=short 2>&1 | tail -10
```

Expected: all tests pass, coverage ≥ 75%.

- [ ] **Step 8: Commit**

```bash
git add frontend/app/\(shell\)/flow/\[flowId\]/cover-letter/page.tsx
git commit -m "feat(cover-letter): add progress widget and fix letterData always-null bug"
```

---

## Self-Review Checklist

After writing the plan, verified against spec:

| Spec requirement | Task |
|---|---|
| Shared `ProgressWidget` with SVG ring + step list | Task 4 |
| Step-derived % (`doneCount / total * 100`) | Task 4 (component code) |
| Upload overlay: dynamic per-CV steps | Task 5 |
| Upload: singular label when 1 CV, numbered when >1 | Task 5 (step-building logic) |
| CV generation uses `ProgressWidget` inline | Task 6 |
| Cover letter uses `ProgressWidget` inline | Task 7 |
| Cover letter `letterData` bug fix (backend) | Task 1 |
| Cover letter `letterData` fix (frontend polling) | Task 7 steps 1–2 |
| `letter_data` populated in `init()` when already ready | Task 7 step 2 |
| German + English strings: `uploadingCVN` | Task 2 |
| German + English strings: cover letter progress keys | Task 2 |
| Gold shimmer animation on active step | Task 3 + Task 4 (`.animate-shimmer`) |
| No hardcoded hex — uses theme tokens | Task 4 (`stroke-primary`, `bg-primary-container`, `border-gold/40`, `text-gold-dim`, `bg-gold-container` via CSS var in `globals.css`) |
