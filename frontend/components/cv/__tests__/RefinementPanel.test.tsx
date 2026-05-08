// Copyright (C) 2024-2026 Tobias Rosenbaum
//
// This file is part of Applire.
//
// Applire is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published
// by the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Applire is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with Applire. If not, see <https://www.gnu.org/licenses/>.

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, afterEach, beforeEach } from "vitest";
import { withIntl } from "@/lib/test-utils/with-intl";
import { RefinementPanel } from "../RefinementPanel";

const BASE_PROPS = {
  cvId: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  flowId: "test-flow-id",
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
  coverLetterId: null as string | null,
  detectedCompany: { name: "Siemens AG", hex: "#009fe3" },
  currentAccentHex: "#009fe3",
  onHtmlRefresh: vi.fn(),
  onRegenerateSame: vi.fn(),
  onRegenerateDifferent: vi.fn(),
  onRegenerateWithTemplate: vi.fn(),
  onNext: vi.fn(),
  onDownloadPdf: vi.fn(),
  onGenerateCoverLetter: vi.fn(),
  collapsed: false,
  onToggleCollapse: vi.fn(),
};

const MOCK_SECTIONS_RESPONSE = {
  sections: [
    { section_id: "introduction", label: "Introduction", content: "Experienced dev", has_override: false, gaps: [{ id: "Python", label: "Python" }] },
    { section_id: "skills", label: "Skills", content: "Python, React", has_override: false, gaps: [] },
  ],
  general_gaps: [],
};

describe("RefinementPanel", () => {
  beforeEach(() => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(MOCK_SECTIONS_RESPONSE),
    } as Response);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders with Content tab active by default", async () => {
    render(withIntl(<RefinementPanel {...BASE_PROPS} />));
    expect(screen.getByTestId("tab-content")).toBeTruthy();
    expect(screen.getByTestId("tab-actions")).toBeTruthy();
    // Content tab should show gap count after sections load
    await waitFor(() =>
      expect(screen.getByText("1 Lücke gefunden für \"Senior Software Engineer\"")).toBeTruthy()
    );
  });

  it("switching to Actions tab shows Actions component", () => {
    render(withIntl(<RefinementPanel {...BASE_PROPS} />));
    fireEvent.click(screen.getByTestId("tab-actions"));
    // ActionsTab shows match score
    expect(screen.getByText("82%")).toBeTruthy();
  });

  it("switching to Design tab shows template label and change button", () => {
    render(withIntl(<RefinementPanel {...BASE_PROPS} />));
    fireEvent.click(screen.getByTestId("tab-appearance"));
    expect(screen.getByText("Klassischer Lebenslauf")).toBeTruthy();
    expect(screen.getByTestId("change-template-btn")).toBeTruthy();
  });

  it("switching back to Content tab restores Content", async () => {
    render(withIntl(<RefinementPanel {...BASE_PROPS} />));
    fireEvent.click(screen.getByTestId("tab-actions"));
    fireEvent.click(screen.getByTestId("tab-content"));
    await waitFor(() =>
      expect(screen.getByText("1 Lücke gefunden für \"Senior Software Engineer\"")).toBeTruthy()
    );
  });

  it("tab-content has correct aria-selected when active", () => {
    render(withIntl(<RefinementPanel {...BASE_PROPS} />));
    const contentTab = screen.getByTestId("tab-content");
    expect(contentTab.getAttribute("aria-selected")).toBe("true");
    const actionsTab = screen.getByTestId("tab-actions");
    expect(actionsTab.getAttribute("aria-selected")).toBe("false");
  });

  it("tab-actions has correct aria-selected when active", () => {
    render(withIntl(<RefinementPanel {...BASE_PROPS} />));
    fireEvent.click(screen.getByTestId("tab-actions"));
    const actionsTab = screen.getByTestId("tab-actions");
    expect(actionsTab.getAttribute("aria-selected")).toBe("true");
    const contentTab = screen.getByTestId("tab-content");
    expect(contentTab.getAttribute("aria-selected")).toBe("false");
  });

  it("renders Design tab and shows company color card when clicked", () => {
    render(withIntl(<RefinementPanel {...BASE_PROPS} />));
    fireEvent.click(screen.getByTestId("tab-appearance"));
    expect(screen.getByText("Siemens AG")).toBeTruthy();
    expect(screen.getByText("auto-detected")).toBeTruthy();
  });
});

describe("RefinementPanel collapse", () => {
  it("renders collapse button when expanded", () => {
    render(
      withIntl(<RefinementPanel
        {...BASE_PROPS}
        collapsed={false}
        onToggleCollapse={vi.fn()}
      />)
    );
    expect(screen.getByTestId("cv-panel-collapse-btn")).toBeTruthy();
  });

  it("calls onToggleCollapse when collapse button clicked", () => {
    const toggle = vi.fn();
    render(
      withIntl(<RefinementPanel
        {...BASE_PROPS}
        collapsed={false}
        onToggleCollapse={toggle}
      />)
    );
    fireEvent.click(screen.getByTestId("cv-panel-collapse-btn"));
    expect(toggle).toHaveBeenCalledOnce();
  });

  it("renders icon rail when collapsed", () => {
    render(
      withIntl(<RefinementPanel
        {...BASE_PROPS}
        collapsed={true}
        onToggleCollapse={vi.fn()}
      />)
    );
    expect(screen.getByTestId("cv-panel-expand-btn")).toBeTruthy();
    expect(screen.getByTestId("cv-tab-icon-content")).toBeTruthy();
    expect(screen.getByTestId("cv-tab-icon-actions")).toBeTruthy();
    expect(screen.getByTestId("cv-tab-icon-appearance")).toBeTruthy();
  });

  it("clicking tab icon in collapsed state calls onToggleCollapse", () => {
    const toggle = vi.fn();
    render(
      withIntl(<RefinementPanel
        {...BASE_PROPS}
        collapsed={true}
        onToggleCollapse={toggle}
      />)
    );
    fireEvent.click(screen.getByTestId("cv-tab-icon-content"));
    expect(toggle).toHaveBeenCalledOnce();
    });
});
