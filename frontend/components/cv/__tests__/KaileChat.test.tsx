import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { KaileChat } from "../KaileChat";

const GAPS = [
  { id: "EU GMP Audit", label: "EU GMP Audit" },
  { id: "Post-Brexit", label: "Post-Brexit" },
];

const BASE_PROPS = {
  cvId: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  sectionId: "introduction",
  gaps: GAPS,
  preSelectedGapIds: [] as string[],
  onApply: vi.fn(),
  onEditFirst: vi.fn(),
  onCancel: vi.fn(),
};

describe("KaileChat", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders textarea and Rewrite button", () => {
    render(<KaileChat {...BASE_PROPS} />);
    expect(screen.getByTestId("kaile-directions-input")).toBeTruthy();
    expect(screen.getByTestId("kaile-rewrite-btn")).toBeTruthy();
  });

  it("renders gap chips when gaps are provided", () => {
    render(<KaileChat {...BASE_PROPS} />);
    expect(screen.getByTestId("gap-chip-EU GMP Audit")).toBeTruthy();
    expect(screen.getByTestId("gap-chip-Post-Brexit")).toBeTruthy();
  });

  it("does not render gap chip section when gaps is empty", () => {
    render(<KaileChat {...BASE_PROPS} gaps={[]} />);
    expect(screen.queryByTestId("gap-chip-EU GMP Audit")).toBeNull();
  });

  it("pre-selects chips passed in preSelectedGapIds", () => {
    render(<KaileChat {...BASE_PROPS} preSelectedGapIds={["EU GMP Audit"]} />);
    const chip = screen.getByTestId("gap-chip-EU GMP Audit");
    expect(chip.getAttribute("data-selected")).toBe("true");
  });

  it("toggling a chip changes its selected state", () => {
    render(<KaileChat {...BASE_PROPS} />);
    const chip = screen.getByTestId("gap-chip-EU GMP Audit");
    expect(chip.getAttribute("data-selected")).toBe("false");
    fireEvent.click(chip);
    expect(chip.getAttribute("data-selected")).toBe("true");
    fireEvent.click(chip);
    expect(chip.getAttribute("data-selected")).toBe("false");
  });

  it("calls rewrite endpoint on submit and shows suggestion", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ suggestion: "Updated section text" }),
    } as Response);

    render(<KaileChat {...BASE_PROPS} />);
    fireEvent.change(screen.getByTestId("kaile-directions-input"), {
      target: { value: "I also did chromatography" },
    });
    fireEvent.click(screen.getByTestId("kaile-rewrite-btn"));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining(`/api/cv/${BASE_PROPS.cvId}/sections/${BASE_PROPS.sectionId}/rewrite`),
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ directions: "I also did chromatography", gap_ids: [] }),
        }),
      );
    });

    await screen.findByTestId("kaile-suggestion");
  });

  it("shows Apply, Edit first, and Discard buttons after suggestion", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ suggestion: "Updated section text" }),
    } as Response);

    render(<KaileChat {...BASE_PROPS} />);
    fireEvent.click(screen.getByTestId("kaile-rewrite-btn"));
    await screen.findByTestId("kaile-suggestion");

    expect(screen.getByTestId("apply-suggestion-btn")).toBeTruthy();
    expect(screen.getByTestId("edit-first-btn")).toBeTruthy();
    expect(screen.getByTestId("discard-suggestion-btn")).toBeTruthy();
  });

  it("Apply calls onApply with suggestion text", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ suggestion: "New suggestion text" }),
    } as Response);

    render(<KaileChat {...BASE_PROPS} />);
    fireEvent.click(screen.getByTestId("kaile-rewrite-btn"));
    await screen.findByTestId("apply-suggestion-btn");

    fireEvent.click(screen.getByTestId("apply-suggestion-btn"));
    expect(BASE_PROPS.onApply).toHaveBeenCalledWith("New suggestion text");
  });

  it("Edit first calls onEditFirst with suggestion text", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ suggestion: "New suggestion text" }),
    } as Response);

    render(<KaileChat {...BASE_PROPS} />);
    fireEvent.click(screen.getByTestId("kaile-rewrite-btn"));
    await screen.findByTestId("apply-suggestion-btn");

    fireEvent.click(screen.getByTestId("edit-first-btn"));
    expect(BASE_PROPS.onEditFirst).toHaveBeenCalledWith("New suggestion text");
  });

  it("Discard calls onCancel", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ suggestion: "New suggestion text" }),
    } as Response);

    render(<KaileChat {...BASE_PROPS} />);
    fireEvent.click(screen.getByTestId("kaile-rewrite-btn"));
    await screen.findByTestId("apply-suggestion-btn");

    fireEvent.click(screen.getByTestId("discard-suggestion-btn"));
    expect(BASE_PROPS.onCancel).toHaveBeenCalled();
  });

  it("shows loading state while rewrite is in progress", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(
      () => new Promise((resolve) => {
        setTimeout(() => resolve({
          ok: true,
          json: async () => ({ suggestion: "Slow suggestion" }),
        } as Response), 100);
      }),
    );

    render(<KaileChat {...BASE_PROPS} />);
    fireEvent.click(screen.getByTestId("kaile-rewrite-btn"));
    expect(screen.getByTestId("kaile-loading")).toBeTruthy();
    await screen.findByTestId("kaile-suggestion");
  });

  it("submits gap chips with selected gap IDs", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ suggestion: "Updated section text" }),
    } as Response);

    render(<KaileChat {...BASE_PROPS} />);
    // Toggle first gap chip
    fireEvent.click(screen.getByTestId("gap-chip-EU GMP Audit"));
    // Toggle second gap chip
    fireEvent.click(screen.getByTestId("gap-chip-Post-Brexit"));
    // Submit
    fireEvent.click(screen.getByTestId("kaile-rewrite-btn"));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining(`/api/cv/${BASE_PROPS.cvId}/sections/${BASE_PROPS.sectionId}/rewrite`),
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            directions: "",
            gap_ids: ["EU GMP Audit", "Post-Brexit"],
          }),
        }),
      );
    });
  });
});
