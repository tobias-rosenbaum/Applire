import { render, screen, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { RefinementPanel } from "../RefinementPanel";

const BASE_PROPS = {
  cvId: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  jobSummary: "Senior Software Engineer",
  gapSummary: {
    gaps: [{ id: "Python", label: "Python" }],
    sections: [
      { section_id: "introduction", label: "Introduction", content: "Experienced dev", has_override: false, gaps: [{ id: "Python", label: "Python" }] },
      { section_id: "skills", label: "Skills", content: "Python, React", has_override: false, gaps: [] },
    ],
  },
  cvSummary: {
    sections: [
      { section_id: "introduction", label: "Introduction", content: "Experienced dev", has_override: false, gaps: [{ id: "Python", label: "Python" }] },
      { section_id: "skills", label: "Skills", content: "Python, React", has_override: false, gaps: [] },
    ],
  },
  template: { label: "Klassischer Lebenslauf" },
  matchScore: 0.82,
  expiryWarning: null as { level: "none" | "warning" | "critical"; expiresIn: string } | null,
  onHtmlRefresh: vi.fn(),
  onRegenerateSame: vi.fn(),
  onRegenerateDifferent: vi.fn(),
  onNext: vi.fn(),
  onDownloadPdf: vi.fn(),
};

describe("RefinementPanel", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders with Content tab active by default", () => {
    render(<RefinementPanel {...BASE_PROPS} />);
    expect(screen.getByTestId("tab-content")).toBeTruthy();
    expect(screen.getByTestId("tab-actions")).toBeTruthy();
    // Content tab should show gap count
    expect(screen.getByText("1 Lücke gefunden für \"Senior Software Engineer\"")).toBeTruthy();
  });

  it("switching to Actions tab shows Actions component", () => {
    render(<RefinementPanel {...BASE_PROPS} />);
    fireEvent.click(screen.getByTestId("tab-actions"));
    // ActionsTab shows match score
    expect(screen.getByText("82%")).toBeTruthy();
    expect(screen.getByText("Klassischer Lebenslauf")).toBeTruthy();
  });

  it("switching back to Content tab restores Content", () => {
    render(<RefinementPanel {...BASE_PROPS} />);
    fireEvent.click(screen.getByTestId("tab-actions"));
    fireEvent.click(screen.getByTestId("tab-content"));
    expect(screen.getByText("1 Lücke gefunden für \"Senior Software Engineer\"")).toBeTruthy();
  });

  it("tab-content has correct aria-selected when active", () => {
    render(<RefinementPanel {...BASE_PROPS} />);
    const contentTab = screen.getByTestId("tab-content");
    expect(contentTab.getAttribute("aria-selected")).toBe("true");
    const actionsTab = screen.getByTestId("tab-actions");
    expect(actionsTab.getAttribute("aria-selected")).toBe("false");
  });

  it("tab-actions has correct aria-selected when active", () => {
    render(<RefinementPanel {...BASE_PROPS} />);
    fireEvent.click(screen.getByTestId("tab-actions"));
    const actionsTab = screen.getByTestId("tab-actions");
    expect(actionsTab.getAttribute("aria-selected")).toBe("true");
    const contentTab = screen.getByTestId("tab-content");
    expect(contentTab.getAttribute("aria-selected")).toBe("false");
  });
});
