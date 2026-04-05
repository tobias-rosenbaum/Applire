import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { FineTunePanel } from "../FineTunePanel";

const MOCK_SECTIONS_RESPONSE = {
  sections: [
    {
      section_id: "introduction",
      label: "Introduction",
      content: "Original intro",
      has_override: false,
      gaps: [{ id: "Python", label: "Python" }],
    },
    {
      section_id: "skills",
      label: "Skills",
      content: "Java\nSQL",
      has_override: false,
      gaps: [],
    },
  ],
  general_gaps: [],
};

const BASE_PROPS = {
  cvId: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  initialHtml: "<html><body>CV</body></html>",
  onClose: vi.fn(),
};

describe("FineTunePanel", () => {
  beforeEach(() => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => MOCK_SECTIONS_RESPONSE,
    } as Response);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows loading skeleton while fetching sections", () => {
    vi.spyOn(globalThis, "fetch").mockReturnValue(new Promise(() => {}));
    render(<FineTunePanel {...BASE_PROPS} />);
    expect(document.querySelectorAll("[data-testid='section-skeleton']").length).toBeGreaterThan(0);
  });

  it("renders section list items after loading", async () => {
    render(<FineTunePanel {...BASE_PROPS} />);
    const items = await screen.findAllByTestId("section-list-item");
    expect(items).toHaveLength(2);
    expect(screen.getByText("Introduction")).toBeTruthy();
    expect(screen.getByText("Skills")).toBeTruthy();
  });

  it("shows gap badge with count for sections with gaps", async () => {
    render(<FineTunePanel {...BASE_PROPS} />);
    await screen.findAllByTestId("section-list-item");
    const badge = screen.getByTestId("gap-badge");
    expect(badge.textContent).toBe("1");
  });

  it("shows retry button on fetch error", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network error"));
    render(<FineTunePanel {...BASE_PROPS} />);
    await screen.findByText("Erneut versuchen");
  });

  it("shows 'all gaps closed' when all section gaps are empty", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        sections: [
          {
            section_id: "introduction",
            label: "Introduction",
            content: "text",
            has_override: false,
            gaps: [],
          },
        ],
        general_gaps: [],
      }),
    } as Response);
    render(<FineTunePanel {...BASE_PROPS} />);
    await screen.findByTestId("all-gaps-closed");
  });

  it("gap badge is shown for sections with gaps", async () => {
    render(<FineTunePanel {...BASE_PROPS} />);
    await screen.findAllByTestId("section-list-item");
    expect(screen.getByTestId("gap-badge")).toBeTruthy();
  });

  it("renders mobile-accordion when matchMedia returns mobile", async () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: query.includes("768"),
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })),
    });

    render(<FineTunePanel {...BASE_PROPS} />);
    await screen.findAllByTestId("section-list-item");
    expect(document.querySelector("[data-testid='mobile-accordion']")).toBeTruthy();
  });
});
