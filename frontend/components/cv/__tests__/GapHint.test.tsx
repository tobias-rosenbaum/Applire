import { render, screen, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { GapHint } from "../GapHint";

const GAP = { id: "Python", label: "Python" };

const BASE_PROPS = {
  gap: GAP,
  onDismiss: vi.fn(),
  onAddressGap: vi.fn(),
};

describe("GapHint", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders gap label", () => {
    render(<GapHint {...BASE_PROPS} />);
    expect(screen.getByText("Python")).toBeTruthy();
  });

  it("'Selbst schreiben' button calls onDismiss with gap id", () => {
    const onDismiss = vi.fn();
    render(<GapHint {...BASE_PROPS} onDismiss={onDismiss} />);
    fireEvent.click(screen.getByTestId("write-myself-btn"));
    expect(onDismiss).toHaveBeenCalledWith("Python");
  });

  it("'Kaile hilft' button calls onAddressGap with gap id", () => {
    const onAddressGap = vi.fn();
    render(<GapHint {...BASE_PROPS} onAddressGap={onAddressGap} />);
    fireEvent.click(screen.getByTestId("kaile-help-btn"));
    expect(onAddressGap).toHaveBeenCalledWith("Python");
  });

  it("'Kaile hilft' button does not open inline session", () => {
    render(<GapHint {...BASE_PROPS} />);
    fireEvent.click(screen.getByTestId("kaile-help-btn"));
    // No AssistMicroSession — no question text should appear
    expect(screen.queryByTestId("assist-question")).toBeNull();
  });
});
