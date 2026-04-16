import { render, screen, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { CoverLetterRefinementPanel } from "../CoverLetterRefinementPanel";

beforeEach(() => {
  vi.spyOn(global, "fetch").mockResolvedValue({
    ok: true,
    json: async () => ({ sections: [] }),
    text: async () => "",
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
