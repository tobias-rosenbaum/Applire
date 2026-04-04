import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { GapHint } from "../GapHint";

const GAP = { id: "Python", label: "Python" };

describe("GapHint", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders gap label", () => {
    render(
      <GapHint
        gap={GAP}
        cvId="cv-1"
        sectionId="introduction"
        onDismiss={vi.fn()}
        onAcceptSuggestion={vi.fn()}
      />
    );
    expect(screen.getByText("Python")).toBeTruthy();
  });

  it("'Selbst schreiben' button calls onDismiss", () => {
    const onDismiss = vi.fn();
    render(
      <GapHint
        gap={GAP}
        cvId="cv-1"
        sectionId="introduction"
        onDismiss={onDismiss}
        onAcceptSuggestion={vi.fn()}
      />
    );
    fireEvent.click(screen.getByTestId("write-myself-btn"));
    expect(onDismiss).toHaveBeenCalledWith("Python");
  });

  it("'Kaile hilft' button is enabled", () => {
    render(
      <GapHint
        gap={GAP}
        cvId="cv-1"
        sectionId="introduction"
        onDismiss={vi.fn()}
        onAcceptSuggestion={vi.fn()}
      />
    );
    const btn = screen.getByTestId("kaile-help-btn") as HTMLButtonElement;
    expect(btn.disabled).toBe(false);
  });

  it("clicking 'Kaile hilft' triggers API call and shows question", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ session_id: "s1", question: "Wie lange Python?" }),
    } as Response);

    render(
      <GapHint
        gap={GAP}
        cvId="cv-1"
        sectionId="introduction"
        onDismiss={vi.fn()}
        onAcceptSuggestion={vi.fn()}
      />
    );

    fireEvent.click(screen.getByTestId("kaile-help-btn"));
    await screen.findByTestId("assist-question");
    expect(screen.getByTestId("assist-question").textContent).toContain("Wie lange Python?");
  });
});
