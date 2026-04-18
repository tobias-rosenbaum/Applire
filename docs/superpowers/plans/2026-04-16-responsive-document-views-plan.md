# Sprint 27 — Responsive Document Views Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix A4 scaling in the Cover Letter preview and add a collapsible right panel (icon rail) to both Cover Letter and CV views so the document preview always uses available horizontal space.

**Architecture:** `CoverLetterDocument` gains a `ResizeObserver` + CSS transform scale, mirroring the existing `CVDocument` pattern exactly. Both refinement panels (`CoverLetterRefinementPanel`, `RefinementPanel`) accept new `collapsed`/`onToggleCollapse` props and manage their own width; their parent pages carry the `panelOpen` boolean state.

**Tech Stack:** Next.js 15 App Router, React 19, TypeScript strict mode, Tailwind CSS v4, Vitest + Testing Library (jsdom), `ResizeObserver` Web API.

---

## Branch

Work on branch `sprint-27`. Create it from `main` before Task 1.

```bash
git checkout main && git pull
git checkout -b sprint-27
```

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `frontend/components/cover-letter/CoverLetterDocument.tsx` | Modify | Add ResizeObserver + CSS scale |
| `frontend/components/cover-letter/__tests__/CoverLetterDocument.test.tsx` | Create | Vitest tests for scaling + fetch behaviour |
| `frontend/components/cover-letter/CoverLetterRefinementPanel.tsx` | Modify | Add `collapsed`/`onToggleCollapse` props; icon rail |
| `frontend/app/flow/[flowId]/cover-letter/page.tsx` | Modify | `panelOpen` state; flex-1 preview div; pass collapse props |
| `frontend/components/cv/RefinementPanel.tsx` | Modify | Add `collapsed`/`onToggleCollapse` props; icon rail; self-managed width |
| `frontend/app/flow/[flowId]/cv/page.tsx` | Modify | `panelOpen` state; flex-1 preview div; pass collapse props |

---

## Task 1 — CoverLetterDocument: ResizeObserver + CSS Scale

**Files:**
- Modify: `frontend/components/cover-letter/CoverLetterDocument.tsx`
- Create: `frontend/components/cover-letter/__tests__/CoverLetterDocument.test.tsx`

### Context

`CVDocument` (reference implementation at `frontend/components/cv/CVDocument.tsx`) uses a `ResizeObserver` on a wrapper div to track `containerWidth`, then computes `scale = Math.min(1, containerWidth / 794)` and applies `transform: scale(scale)` on the iframe. `CoverLetterDocument` currently renders a bare iframe at `w-full h-full` — A4 content (794px wide) is clipped on containers narrower than 794px.

The fix: add the same observer pattern, fix the iframe to A4 dimensions, and apply the CSS transform.

`CV_WIDTH = 794` (A4 at 96 dpi). A4 height = `CV_WIDTH * Math.sqrt(2)` ≈ 1123px.

---

- [ ] **Step 1: Create the test file with failing tests**

Create `frontend/components/cover-letter/__tests__/CoverLetterDocument.test.tsx`:

```tsx
import { render, screen, act, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { CoverLetterDocument } from "../CoverLetterDocument";

const CL_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb";
const TEST_HTML = "<html><body><p>Sehr geehrte Damen</p></body></html>";

describe("CoverLetterDocument", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("shows loading state while fetch is in flight", () => {
    vi.spyOn(globalThis, "fetch").mockReturnValue(new Promise(() => {}));
    render(<CoverLetterDocument coverLetterId={CL_ID} />);
    expect(screen.getByText("Lade Vorschau…")).toBeTruthy();
    expect(screen.queryByTestId("cover-letter-iframe")).toBeNull();
  });

  it("renders iframe with srcDoc after successful fetch", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      text: async () => TEST_HTML,
    } as Response);
    render(<CoverLetterDocument coverLetterId={CL_ID} />);
    const iframe = await screen.findByTestId("cover-letter-iframe") as HTMLIFrameElement;
    expect(iframe.getAttribute("srcdoc")).toBe(TEST_HTML);
  });

  it("shows error message when fetch fails", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network error"));
    render(<CoverLetterDocument coverLetterId={CL_ID} />);
    await screen.findByText("Network error");
  });

  it("fetches from correct API URL", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      text: async () => TEST_HTML,
    } as Response);
    render(<CoverLetterDocument coverLetterId={CL_ID} />);
    await screen.findByTestId("cover-letter-iframe");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(`/api/cover-letter/${CL_ID}/html`)
    );
  });

  it("applies CSS scale transform proportional to container width", async () => {
    let roCallback: ResizeObserverCallback | undefined;
    vi.stubGlobal(
      "ResizeObserver",
      vi.fn((cb: ResizeObserverCallback) => {
        roCallback = cb;
        return { observe: vi.fn(), unobserve: vi.fn(), disconnect: vi.fn() };
      })
    );
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      text: async () => TEST_HTML,
    } as Response);

    render(<CoverLetterDocument coverLetterId={CL_ID} />);
    const iframe = await screen.findByTestId("cover-letter-iframe") as HTMLIFrameElement;

    // 600px container → scale = Math.min(1, 600/794) ≈ 0.755...
    act(() => {
      roCallback?.(
        [{ contentRect: { width: 600 } } as ResizeObserverEntry],
        {} as ResizeObserver
      );
    });

    await waitFor(() => {
      expect(iframe.style.transform).toMatch(/scale\(0\.7/);
    });
  });

  it("caps scale at 1 for containers wider than 794px", async () => {
    let roCallback: ResizeObserverCallback | undefined;
    vi.stubGlobal(
      "ResizeObserver",
      vi.fn((cb: ResizeObserverCallback) => {
        roCallback = cb;
        return { observe: vi.fn(), unobserve: vi.fn(), disconnect: vi.fn() };
      })
    );
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      text: async () => TEST_HTML,
    } as Response);

    render(<CoverLetterDocument coverLetterId={CL_ID} />);
    const iframe = await screen.findByTestId("cover-letter-iframe") as HTMLIFrameElement;

    act(() => {
      roCallback?.(
        [{ contentRect: { width: 1000 } } as ResizeObserverEntry],
        {} as ResizeObserver
      );
    });

    await waitFor(() => {
      expect(iframe.style.transform).toBe("scale(1)");
    });
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && npx vitest run components/cover-letter/__tests__/CoverLetterDocument.test.tsx
```

Expected: all tests fail (loading/error/iframe tests) or PASS only the loading test (which coincidentally matches current behaviour). The scale tests must FAIL because the current component has no ResizeObserver and the iframe has no transform style.

- [ ] **Step 3: Implement CoverLetterDocument with scaling**

Replace the full content of `frontend/components/cover-letter/CoverLetterDocument.tsx`:

```tsx
"use client";

import { useEffect, useRef, useState } from "react";

interface CoverLetterDocumentProps {
  coverLetterId: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";
const CV_WIDTH = 794; // A4 at 96 dpi

export function CoverLetterDocument({ coverLetterId }: CoverLetterDocumentProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [srcDoc, setSrcDoc] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [containerWidth, setContainerWidth] = useState(0);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      setContainerWidth(entry.contentRect.width);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    if (!coverLetterId) return;
    let cancelled = false;

    async function load() {
      try {
        const res = await fetch(`${API_BASE}/api/cover-letter/${coverLetterId}/html`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const html = await res.text();
        if (!cancelled) setSrcDoc(html);
      } catch (err: unknown) {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Preview nicht verfügbar");
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [coverLetterId]);

  const scale = containerWidth > 0 ? Math.min(1, containerWidth / CV_WIDTH) : 1;
  const iframeHeight = CV_WIDTH * Math.sqrt(2); // A4 aspect ratio ≈ 1123px

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full overflow-hidden"
    >
      {error ? (
        <div className="flex items-center justify-center h-full text-sm text-red-500">
          {error}
        </div>
      ) : !srcDoc ? (
        <div className="flex items-center justify-center h-full text-sm text-neutral-400">
          Lade Vorschau…
        </div>
      ) : (
        <iframe
          srcDoc={srcDoc}
          title="Anschreiben Vorschau"
          data-testid="cover-letter-iframe"
          sandbox="allow-same-origin"
          style={{
            width: CV_WIDTH,
            height: iframeHeight,
            transform: `scale(${scale})`,
            transformOrigin: "top left",
            border: "none",
            display: "block",
          }}
        />
      )}
    </div>
  );
}
```

- [ ] **Step 4: Run tests and verify all pass**

```bash
cd frontend && npx vitest run components/cover-letter/__tests__/CoverLetterDocument.test.tsx
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd frontend && git add components/cover-letter/CoverLetterDocument.tsx components/cover-letter/__tests__/CoverLetterDocument.test.tsx
git commit -m "feat: add ResizeObserver scaling to CoverLetterDocument (mirrors CVDocument)"
```

---

## Task 2 — Collapsible Panel: Cover Letter View

**Files:**
- Modify: `frontend/components/cover-letter/CoverLetterRefinementPanel.tsx`
- Modify: `frontend/app/flow/[flowId]/cover-letter/page.tsx`

### Context

`CoverLetterRefinementPanel` has 3 tabs: Inhalt (content), Design (design), Aktionen (actions). The panel is rendered inside `cover-letter/page.tsx` in a `w-1/2 min-w-[340px]` div. After this task, the panel manages its own width (`w-[380px]` expanded, `w-12` collapsed), the preview div becomes `flex-1 min-w-0`, and the page carries `panelOpen` state.

---

- [ ] **Step 1: Write failing test for collapse toggle in CoverLetterRefinementPanel**

Create `frontend/components/cover-letter/__tests__/CoverLetterRefinementPanel.test.tsx`:

```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { CoverLetterRefinementPanel } from "../CoverLetterRefinementPanel";

// Sub-components make fetch calls — stub them globally
beforeEach(() => {
  vi.spyOn(global, "fetch").mockResolvedValue({
    ok: true,
    json: async () => ({ sections: [] }),
  } as Response);
});

afterEach(() => {
  vi.restoreAllMocks();
});

const BASE_PROPS = {
  flowId: "test-flow",
  coverLetterId: "aaaa-1111",
  letterData: null,
  currentTemplate: "classic_german" as const,
  onSectionSaved: vi.fn(),
  onTemplateChange: vi.fn(),
  onRegenerateCoverLetter: vi.fn(),
  onDownloadPdf: vi.fn(),
  downloading: false,
};

describe("CoverLetterRefinementPanel collapse", () => {
  it("renders collapse button when expanded", () => {
    render(
      <CoverLetterRefinementPanel
        {...BASE_PROPS}
        collapsed={false}
        onToggleCollapse={vi.fn()}
      />
    );
    expect(screen.getByTestId("cl-panel-collapse-btn")).toBeTruthy();
  });

  it("calls onToggleCollapse when collapse button clicked", () => {
    const toggle = vi.fn();
    render(
      <CoverLetterRefinementPanel
        {...BASE_PROPS}
        collapsed={false}
        onToggleCollapse={toggle}
      />
    );
    fireEvent.click(screen.getByTestId("cl-panel-collapse-btn"));
    expect(toggle).toHaveBeenCalledOnce();
  });

  it("renders icon rail when collapsed", () => {
    render(
      <CoverLetterRefinementPanel
        {...BASE_PROPS}
        collapsed={true}
        onToggleCollapse={vi.fn()}
      />
    );
    expect(screen.getByTestId("cl-panel-expand-btn")).toBeTruthy();
    expect(screen.getByTestId("cl-tab-icon-content")).toBeTruthy();
    expect(screen.getByTestId("cl-tab-icon-design")).toBeTruthy();
    expect(screen.getByTestId("cl-tab-icon-actions")).toBeTruthy();
  });

  it("calls onToggleCollapse when expand button clicked", () => {
    const toggle = vi.fn();
    render(
      <CoverLetterRefinementPanel
        {...BASE_PROPS}
        collapsed={true}
        onToggleCollapse={toggle}
      />
    );
    fireEvent.click(screen.getByTestId("cl-panel-expand-btn"));
    expect(toggle).toHaveBeenCalledOnce();
  });

  it("clicking tab icon in collapsed state calls onToggleCollapse", () => {
    const toggle = vi.fn();
    render(
      <CoverLetterRefinementPanel
        {...BASE_PROPS}
        collapsed={true}
        onToggleCollapse={toggle}
      />
    );
    fireEvent.click(screen.getByTestId("cl-tab-icon-design"));
    expect(toggle).toHaveBeenCalledOnce();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npx vitest run components/cover-letter/__tests__/CoverLetterRefinementPanel.test.tsx
```

Expected: all tests fail with "collapsed is not a prop" or render errors.

- [ ] **Step 3: Implement collapsible CoverLetterRefinementPanel**

Replace the full content of `frontend/components/cover-letter/CoverLetterRefinementPanel.tsx`:

```tsx
"use client";

import { useState } from "react";
import { CoverLetterContentTab } from "./CoverLetterContentTab";
import { CoverLetterDesignTab } from "./CoverLetterDesignTab";
import { CoverLetterActionsTab } from "./CoverLetterActionsTab";

type CLTemplate =
  | "classic_german"
  | "modern_swiss"
  | "executive"
  | "tech_developer"
  | "creative_sidebar"
  | "academic"
  | "compact_pro";

type TabId = "content" | "design" | "actions";

interface CoverLetterRefinementPanelProps {
  flowId: string;
  coverLetterId: string;
  letterData: Record<string, unknown> | null;
  currentTemplate: CLTemplate;
  onSectionSaved: () => void;
  onTemplateChange: (template: CLTemplate) => void;
  onRegenerateCoverLetter: () => void;
  onDownloadPdf: () => void;
  downloading: boolean;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

const TABS: { id: TabId; label: string; icon: string }[] = [
  { id: "content", label: "Inhalt", icon: "✏️" },
  { id: "design", label: "Design", icon: "🎨" },
  { id: "actions", label: "Aktionen", icon: "⚡" },
];

export function CoverLetterRefinementPanel({
  flowId,
  coverLetterId,
  letterData,
  currentTemplate,
  onSectionSaved,
  onTemplateChange,
  onRegenerateCoverLetter,
  onDownloadPdf,
  downloading,
  collapsed,
  onToggleCollapse,
}: CoverLetterRefinementPanelProps) {
  const [activeTab, setActiveTab] = useState<TabId>("content");

  if (collapsed) {
    return (
      <div className="w-12 flex flex-col items-center bg-white border-l border-neutral-200 py-2 gap-2 flex-shrink-0 transition-[width] duration-200 ease-in-out overflow-hidden">
        <button
          type="button"
          onClick={onToggleCollapse}
          className="w-8 h-8 flex items-center justify-center rounded hover:bg-neutral-100 text-neutral-500 text-sm"
          title="Panel öffnen"
          data-testid="cl-panel-expand-btn"
        >
          ❮
        </button>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => {
              setActiveTab(tab.id);
              onToggleCollapse();
            }}
            className={`w-8 h-8 flex items-center justify-center rounded text-base ${
              activeTab === tab.id
                ? "bg-blue-50 text-blue-600"
                : "hover:bg-neutral-100"
            }`}
            title={tab.label}
            data-testid={`cl-tab-icon-${tab.id}`}
          >
            {tab.icon}
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="w-[380px] flex flex-col h-full bg-white border-l border-neutral-200 flex-shrink-0 transition-[width] duration-200 ease-in-out">
      {/* Tab bar */}
      <div className="flex items-center border-b border-neutral-200 flex-shrink-0">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-neutral-500 hover:text-neutral-700"
            }`}
            data-testid={`cl-tab-${tab.id}`}
          >
            {tab.label}
          </button>
        ))}
        <button
          type="button"
          onClick={onToggleCollapse}
          className="ml-auto px-2 py-3 text-neutral-400 hover:text-neutral-600 text-sm"
          title="Panel einklappen"
          data-testid="cl-panel-collapse-btn"
        >
          ❯
        </button>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === "content" && (
          <CoverLetterContentTab
            coverLetterId={coverLetterId}
            letterData={letterData as Parameters<typeof CoverLetterContentTab>[0]["letterData"]}
            onSectionSaved={onSectionSaved}
          />
        )}
        {activeTab === "design" && (
          <CoverLetterDesignTab
            flowId={flowId}
            currentTemplate={currentTemplate}
            onTemplateChange={onTemplateChange}
          />
        )}
        {activeTab === "actions" && (
          <CoverLetterActionsTab
            onRegenerateCoverLetter={onRegenerateCoverLetter}
            onDownloadPdf={onDownloadPdf}
            downloading={downloading}
          />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
cd frontend && npx vitest run components/cover-letter/__tests__/CoverLetterRefinementPanel.test.tsx
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Update cover-letter/page.tsx**

In `frontend/app/flow/[flowId]/cover-letter/page.tsx`, make these changes:

**5a.** Add `panelOpen` state after the existing `downloading` state declaration (around line 45):

```tsx
// Before (line ~45):
const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

// After:
const [panelOpen, setPanelOpen] = useState(true);
const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
```

**5b.** Change the preview div from `w-1/2 min-w-0` to `flex-1 min-w-0` (around line 212):

```tsx
// Before:
<div className="w-1/2 min-w-0 flex flex-col border-r border-neutral-200 bg-neutral-50 p-3">

// After:
<div className="flex-1 min-w-0 flex flex-col border-r border-neutral-200 bg-neutral-50 p-3">
```

**5c.** Change the right panel wrapper from `w-1/2 min-w-[340px]` to `flex-shrink-0` (around line 220) and pass collapse props:

```tsx
// Before:
<div className="w-1/2 min-w-[340px] flex flex-col overflow-hidden">
  <CoverLetterRefinementPanel
    flowId={flowId}
    coverLetterId={clState!.coverLetterId}
    letterData={clState!.letterData}
    currentTemplate={clState!.template}
    onSectionSaved={handleSectionSaved}
    onTemplateChange={handleTemplateChange}
    onRegenerateCoverLetter={() => setShowModal(true)}
    onDownloadPdf={() => void handleDownloadPdf()}
    downloading={downloading}
  />
</div>

// After:
<div className="flex-shrink-0 flex flex-col overflow-hidden">
  <CoverLetterRefinementPanel
    flowId={flowId}
    coverLetterId={clState!.coverLetterId}
    letterData={clState!.letterData}
    currentTemplate={clState!.template}
    onSectionSaved={handleSectionSaved}
    onTemplateChange={handleTemplateChange}
    onRegenerateCoverLetter={() => setShowModal(true)}
    onDownloadPdf={() => void handleDownloadPdf()}
    downloading={downloading}
    collapsed={!panelOpen}
    onToggleCollapse={() => setPanelOpen((o) => !o)}
  />
</div>
```

- [ ] **Step 6: Run full Vitest suite to verify no regressions**

```bash
cd frontend && npx vitest run
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/components/cover-letter/CoverLetterRefinementPanel.tsx \
        frontend/components/cover-letter/__tests__/CoverLetterRefinementPanel.test.tsx \
        frontend/app/flow/[flowId]/cover-letter/page.tsx
git commit -m "feat: collapsible icon-rail panel for Cover Letter view"
```

---

## Task 3 — Collapsible Panel: CV View

**Files:**
- Modify: `frontend/components/cv/RefinementPanel.tsx`
- Modify: `frontend/app/flow/[flowId]/cv/page.tsx`

### Context

`RefinementPanel` currently has `w-1/2` baked into its root `<div>` (line 62). With the collapsible approach, the component manages its own width (`w-[380px]` expanded, `w-12` collapsed) just like `CoverLetterRefinementPanel`. The CV view has 3 tabs: Inhalt (content, `tab-content`), Aktionen (actions, `tab-actions`), Design (appearance, `tab-appearance`).

---

- [ ] **Step 1: Write failing tests for RefinementPanel collapse**

The existing test file is at `frontend/components/cv/__tests__/RefinementPanel.test.tsx`. Add a new `describe` block for collapse behaviour at the end of the file:

```tsx
describe("RefinementPanel collapse", () => {
  it("renders collapse button when expanded", () => {
    render(
      <RefinementPanel
        {...BASE_PROPS}
        collapsed={false}
        onToggleCollapse={vi.fn()}
      />
    );
    expect(screen.getByTestId("cv-panel-collapse-btn")).toBeTruthy();
  });

  it("calls onToggleCollapse when collapse button clicked", () => {
    const toggle = vi.fn();
    render(
      <RefinementPanel
        {...BASE_PROPS}
        collapsed={false}
        onToggleCollapse={toggle}
      />
    );
    fireEvent.click(screen.getByTestId("cv-panel-collapse-btn"));
    expect(toggle).toHaveBeenCalledOnce();
  });

  it("renders icon rail when collapsed", () => {
    render(
      <RefinementPanel
        {...BASE_PROPS}
        collapsed={true}
        onToggleCollapse={vi.fn()}
      />
    );
    expect(screen.getByTestId("cv-panel-expand-btn")).toBeTruthy();
    expect(screen.getByTestId("cv-tab-icon-content")).toBeTruthy();
    expect(screen.getByTestId("cv-tab-icon-actions")).toBeTruthy();
    expect(screen.getByTestId("cv-tab-icon-appearance")).toBeTruthy();
  });

  it("clicking tab icon in collapsed state calls onToggleCollapse", () => {
    const toggle = vi.fn();
    render(
      <RefinementPanel
        {...BASE_PROPS}
        collapsed={true}
        onToggleCollapse={toggle}
      />
    );
    fireEvent.click(screen.getByTestId("cv-tab-icon-content"));
    expect(toggle).toHaveBeenCalledOnce();
  });
});
```

Also add `fireEvent` to the import at the top of the file if it is not already imported:
```tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npx vitest run components/cv/__tests__/RefinementPanel.test.tsx
```

Expected: the new collapse tests FAIL (props don't exist yet); existing tests PASS.

- [ ] **Step 3: Implement collapsible RefinementPanel**

Replace the full content of `frontend/components/cv/RefinementPanel.tsx`:

```tsx
// frontend/components/cv/RefinementPanel.tsx
"use client";

import { useState } from "react";
import { ContentTab } from "./ContentTab";
import { ActionsTab } from "./ActionsTab";
import { DesignTab } from "./DesignTab";

type Tab = "content" | "actions" | "appearance";

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: "content", label: "Inhalt", icon: "📝" },
  { id: "actions", label: "Aktionen", icon: "⚙️" },
  { id: "appearance", label: "Design", icon: "🎨" },
];

interface RefinementPanelProps {
  cvId: string;
  flowId: string;
  jobSummary: string | null;
  gapSummary: { gaps: Array<{ id: string; label: string }>; sections: Array<any> } | null;
  cvSummary: { sections: Array<any> } | null;
  template: { label: string | null } | null;
  matchScore: number | null;
  expiryWarning: { level: "none" | "warning" | "critical"; expiresIn: string } | null;
  coverLetterId: string | null;
  detectedCompany: { name: string; hex: string } | null;
  currentAccentHex: string;
  onHtmlRefresh: () => void;
  onRegenerateSame: () => void;
  onRegenerateDifferent: () => void;
  onRegenerateWithTemplate: (template: string) => void;
  onNext: () => void;
  onDownloadPdf: () => void;
  onGenerateCoverLetter: () => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export function RefinementPanel({
  cvId,
  flowId,
  jobSummary,
  gapSummary,
  cvSummary,
  template,
  matchScore,
  expiryWarning,
  coverLetterId,
  detectedCompany,
  currentAccentHex,
  onHtmlRefresh,
  onRegenerateSame,
  onRegenerateDifferent,
  onRegenerateWithTemplate,
  onNext,
  onDownloadPdf,
  onGenerateCoverLetter,
  collapsed,
  onToggleCollapse,
}: RefinementPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>("content");

  const flowSummary = {
    job_summary: jobSummary,
    gap_summary: gapSummary,
    cv_summary: cvSummary,
  };

  if (collapsed) {
    return (
      <div
        className="w-12 flex flex-col items-center h-[calc(100vh-56px)] bg-white border-l border-neutral-medium py-2 gap-2 flex-shrink-0 transition-[width] duration-200 ease-in-out overflow-hidden"
        data-testid="refinement-panel"
      >
        <button
          type="button"
          onClick={onToggleCollapse}
          className="w-8 h-8 flex items-center justify-center rounded hover:bg-neutral-100 text-neutral-500 text-sm"
          title="Panel öffnen"
          data-testid="cv-panel-expand-btn"
        >
          ❮
        </button>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => {
              setActiveTab(tab.id);
              onToggleCollapse();
            }}
            className={`w-8 h-8 flex items-center justify-center rounded text-base ${
              activeTab === tab.id
                ? "bg-blue-50 text-blue-600"
                : "hover:bg-neutral-100"
            }`}
            title={tab.label}
            data-testid={`cv-tab-icon-${tab.id}`}
          >
            {tab.icon}
          </button>
        ))}
      </div>
    );
  }

  return (
    <div
      className="w-[380px] h-[calc(100vh-56px)] overflow-y-auto border-l border-neutral-medium bg-white flex flex-col flex-shrink-0 transition-[width] duration-200 ease-in-out"
      data-testid="refinement-panel"
    >
      {/* Tab strip */}
      <div className="flex items-center border-b border-neutral-medium shrink-0">
        <button
          type="button"
          onClick={() => setActiveTab("content")}
          className={`flex-1 text-sm py-2.5 px-3 font-medium transition-colors ${
            activeTab === "content"
              ? "text-teal border-b-2 border-teal"
              : "text-neutral-medium hover:text-neutral-dark"
          }`}
          role="tab"
          aria-selected={activeTab === "content"}
          data-testid="tab-content"
        >
          &#x1f4dd; Inhalt
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("actions")}
          className={`flex-1 text-sm py-2.5 px-3 font-medium transition-colors ${
            activeTab === "actions"
              ? "text-teal border-b-2 border-teal"
              : "text-neutral-medium hover:text-neutral-dark"
          }`}
          role="tab"
          aria-selected={activeTab === "actions"}
          data-testid="tab-actions"
        >
          &#x2699;&#xfe0f; Aktionen
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("appearance")}
          className={`flex-1 text-sm py-2.5 px-3 font-medium transition-colors ${
            activeTab === "appearance"
              ? "text-teal border-b-2 border-teal"
              : "text-neutral-medium hover:text-neutral-dark"
          }`}
          role="tab"
          aria-selected={activeTab === "appearance"}
          data-testid="tab-appearance"
        >
          🎨 Design
        </button>
        <button
          type="button"
          onClick={onToggleCollapse}
          className="px-2 py-2.5 text-neutral-400 hover:text-neutral-600 text-sm shrink-0"
          title="Panel einklappen"
          data-testid="cv-panel-collapse-btn"
        >
          ❯
        </button>
      </div>

      {/* Active tab content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === "content" ? (
          <ContentTab
            cvId={cvId}
            flowSummary={flowSummary}
            onSectionSave={() => onHtmlRefresh()}
            onUnsavedChange={() => {}}
          />
        ) : activeTab === "actions" ? (
          <ActionsTab
            flowId={flowId}
            matchScore={matchScore}
            expiryWarning={expiryWarning}
            coverLetterId={coverLetterId}
            onDownloadPdf={onDownloadPdf}
            onRegenerateSame={onRegenerateSame}
            onRegenerateWithTemplate={onRegenerateWithTemplate}
            onNext={onNext}
            onGenerateCoverLetter={onGenerateCoverLetter}
          />
        ) : (
          <DesignTab
            cvId={cvId}
            templateLabel={template?.label ?? null}
            detectedCompany={detectedCompany}
            currentAccentHex={currentAccentHex}
            onColorApplied={onHtmlRefresh}
            onChangeTemplate={onRegenerateDifferent}
          />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
cd frontend && npx vitest run components/cv/__tests__/RefinementPanel.test.tsx
```

Expected: all tests PASS (existing + new collapse tests).

- [ ] **Step 5: Update cv/page.tsx**

In `frontend/app/flow/[flowId]/cv/page.tsx`, make these changes inside the `phase === "preview"` branch:

**5a.** Add `panelOpen` state next to other state declarations (around line 42):

```tsx
// After the existing state declarations (showCoverLetterModal line):
const [panelOpen, setPanelOpen] = useState(true);
```

**5b.** Change the preview div from `w-1/2` to `flex-1 min-w-0` (around line 152):

```tsx
// Before:
<div className="w-1/2 flex flex-col min-w-0 px-4 py-3 gap-3 bg-neutral-light overflow-hidden">

// After:
<div className="flex-1 min-w-0 flex flex-col px-4 py-3 gap-3 bg-neutral-light overflow-hidden">
```

**5c.** Pass collapse props to `RefinementPanel` (around line 164):

```tsx
// Before:
<RefinementPanel
  cvId={cvId}
  flowId={flowId}
  jobSummary={flowState?.job_summary?.role_title ?? null}
  gapSummary={{...}}
  cvSummary={{...}}
  template={{...}}
  matchScore={...}
  expiryWarning={expiryWarning}
  coverLetterId={...}
  detectedCompany={...}
  currentAccentHex={...}
  onHtmlRefresh={() => cvDocRef.current?.refresh()}
  onRegenerateSame={() => void handleGenerate(template)}
  onRegenerateDifferent={() => setPhase("template_select")}
  onRegenerateWithTemplate={(tpl) => void handleGenerate(tpl as CVTemplate)}
  onNext={() => setPhase("complete")}
  onDownloadPdf={() => void handleDownloadPdf()}
  onGenerateCoverLetter={() => setShowCoverLetterModal(true)}
/>

// After (add the two new props at the end):
<RefinementPanel
  cvId={cvId}
  flowId={flowId}
  jobSummary={flowState?.job_summary?.role_title ?? null}
  gapSummary={{
    gaps: (flowState?.gap_summary as any)?.gaps ?? [],
    sections: (flowState?.gap_summary as any)?.sections ?? [],
  }}
  cvSummary={{
    sections: (flowState?.cv_summary as any)?.sections ?? [],
  }}
  template={{ label: template === "classic_german" ? "Klassischer Lebenslauf" : "Modern Swiss CV" }}
  matchScore={flowState?.gap_summary?.match_score ?? null}
  expiryWarning={expiryWarning}
  coverLetterId={flowState?.cover_letter_summary?.cover_letter_id ?? null}
  detectedCompany={(flowState?.gap_summary as any)?.detected_company ?? null}
  currentAccentHex={(flowState?.gap_summary as any)?.current_accent_hex ?? "#2b5fa8"}
  onHtmlRefresh={() => cvDocRef.current?.refresh()}
  onRegenerateSame={() => void handleGenerate(template)}
  onRegenerateDifferent={() => setPhase("template_select")}
  onRegenerateWithTemplate={(tpl) => void handleGenerate(tpl as CVTemplate)}
  onNext={() => setPhase("complete")}
  onDownloadPdf={() => void handleDownloadPdf()}
  onGenerateCoverLetter={() => setShowCoverLetterModal(true)}
  collapsed={!panelOpen}
  onToggleCollapse={() => setPanelOpen((o) => !o)}
/>
```

- [ ] **Step 6: Run full Vitest suite**

```bash
cd frontend && npx vitest run
```

Expected: all tests PASS.

- [ ] **Step 7: Run TypeScript compiler check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no type errors.

- [ ] **Step 8: Commit**

```bash
git add frontend/components/cv/RefinementPanel.tsx \
        frontend/components/cv/__tests__/RefinementPanel.test.tsx \
        frontend/app/flow/[flowId]/cv/page.tsx
git commit -m "feat: collapsible icon-rail panel for CV view"
```

---

## Task 4 — Manual Verification

Before pushing to remote and creating a PR, verify the features work visually.

- [ ] **Step 1: Start the dev server**

```bash
cd frontend && npm run dev
```

Open `http://localhost:3000` in Chromium.

- [ ] **Step 2: Verify CoverLetterDocument scaling**

Navigate to a flow that has a cover letter. Open DevTools → set viewport to 1280×800 (14" laptop simulation). The cover letter preview must be fully visible — no horizontal clipping. The A4 document must scale proportionally within the available left half of the screen.

- [ ] **Step 3: Verify CL view panel collapse**

On the cover letter page:
1. Panel opens expanded (380px). Click `❯` — panel collapses to icon rail (48px). Preview takes the freed space.
2. Click `❮` — panel expands back to 380px.
3. In collapsed state, click the ✏️ icon — panel expands on "Inhalt" tab.
4. Click ❯ to collapse again, then click 🎨 — panel expands on "Design" tab.
5. Reload the page — panel is expanded (default state, no persistence).

- [ ] **Step 4: Verify CV view panel collapse**

Navigate to a flow's CV preview:
1. Same collapse/expand behaviour as cover letter.
2. Reload — panel opens expanded.

- [ ] **Step 5: Commit if any minor CSS tweaks were made**

```bash
git add -p   # stage only intentional changes
git commit -m "fix: minor visual tweaks after manual verification"
```

---

## Task 5 — Push and PR

- [ ] **Step 1: Push branch to remote**

```bash
git push -u origin sprint-27
```

- [ ] **Step 2: Create pull request**

```bash
gh pr create \
  --title "feat: Sprint 27 — Responsive Document Views (CL scaling + collapsible panel)" \
  --body "$(cat <<'EOF'
## Summary
- Fixes CoverLetterDocument A4 clipping on 14" laptops by mirroring CVDocument's ResizeObserver + CSS scale pattern
- Adds collapsible icon-rail panel to Cover Letter and CV views (default: expanded, no localStorage)
- Preview pane becomes flex-1 and fills freed horizontal space when panel is collapsed

## Files Changed
- `frontend/components/cover-letter/CoverLetterDocument.tsx` — ResizeObserver + transform scale
- `frontend/components/cover-letter/CoverLetterRefinementPanel.tsx` — collapsed prop + icon rail
- `frontend/app/flow/[flowId]/cover-letter/page.tsx` — panelOpen state, flex-1 preview
- `frontend/components/cv/RefinementPanel.tsx` — collapsed prop + icon rail, self-managed width
- `frontend/app/flow/[flowId]/cv/page.tsx` — panelOpen state, flex-1 preview

## Test plan
- [ ] All Vitest unit tests pass (`cd frontend && npx vitest run`)
- [ ] TypeScript strict check clean (`npx tsc --noEmit`)
- [ ] Cover letter preview fills screen on 1280px viewport with no horizontal clipping
- [ ] Panel collapse/expand works in both CL and CV views
- [ ] Tab icon in collapsed state expands the panel and activates the correct tab
- [ ] Page reload always shows panel expanded (no localStorage persistence)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```
