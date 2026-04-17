// frontend/components/cv/__tests__/DesignTab.test.tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { withIntl } from "@/lib/test-utils/with-intl";
import { DesignTab } from "../DesignTab";

const BASE_PROPS = {
  cvId: "dddddddd-dddd-dddd-dddd-dddddddddddd",
  templateLabel: null,
  detectedCompany: { name: "Siemens AG", hex: "#009fe3" },
  currentAccentHex: "#009fe3",
  onColorApplied: vi.fn(),
  onChangeTemplate: vi.fn(),
};

describe("DesignTab", () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        color_profile_id: "cpid-1234",
        derived: { "--cv-accent": "#ff5500", "--cv-accent-tint": "#fff0e8" },
      }),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the detected company color card when company is provided", () => {
    render(withIntl(<DesignTab {...BASE_PROPS} />));
    expect(screen.getByText("Siemens AG")).toBeTruthy();
    expect(screen.getAllByText("#009fe3").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("auto-detected")).toBeTruthy();
  });

  it("renders no company card when detectedCompany is null", () => {
    render(withIntl(<DesignTab {...BASE_PROPS} detectedCompany={null} />));
    expect(screen.queryByText("auto-detected")).toBeNull();
  });

  it("renders preset swatch row with color swatches", () => {
    render(withIntl(<DesignTab {...BASE_PROPS} />));
    const swatches = screen.getAllByRole("button", { name: /Farbe wählen/ });
    expect(swatches.length).toBeGreaterThanOrEqual(5);
  });

  it("renders hex input with current accent value", () => {
    render(withIntl(<DesignTab {...BASE_PROPS} />));
    const input = screen.getByDisplayValue("#009fe3");
    expect(input).toBeTruthy();
  });

  it("apply button is disabled when selection matches current accent", () => {
    render(withIntl(<DesignTab {...BASE_PROPS} />));
    const applyBtn = screen.getByText("Apply color");
    expect(applyBtn.closest("button")?.disabled).toBe(true);
  });

  it("typing a new hex enables the apply button", () => {
    render(withIntl(<DesignTab {...BASE_PROPS} />));
    const input = screen.getByDisplayValue("#009fe3");
    fireEvent.change(input, { target: { value: "#ff5500" } });
    const applyBtn = screen.getByText("Apply color");
    expect(applyBtn.closest("button")?.disabled).toBe(false);
  });

  it("clicking apply calls PATCH /api/cv/{id}/color", async () => {
    render(withIntl(<DesignTab {...BASE_PROPS} />));
    const input = screen.getByDisplayValue("#009fe3");
    fireEvent.change(input, { target: { value: "#ff5500" } });
    fireEvent.click(screen.getByText("Apply color"));
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/cv/dddddddd-dddd-dddd-dddd-dddddddddddd/color"),
        expect.objectContaining({ method: "PATCH" })
      );
    });
  });

  it("calls onColorApplied after successful PATCH", async () => {
    const onColorApplied = vi.fn();
    render(withIntl(<DesignTab {...BASE_PROPS} onColorApplied={onColorApplied} />));
    fireEvent.change(screen.getByDisplayValue("#009fe3"), { target: { value: "#ff5500" } });
    fireEvent.click(screen.getByText("Apply color"));
    await waitFor(() => expect(onColorApplied).toHaveBeenCalled());
  });
});
