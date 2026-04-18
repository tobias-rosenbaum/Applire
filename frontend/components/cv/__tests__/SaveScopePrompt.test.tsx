import { render, screen, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { withIntl } from "@/lib/test-utils/with-intl";
import { SaveScopePrompt } from "../SaveScopePrompt";

describe("SaveScopePrompt", () => {
  afterEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("renders both save options", () => {
    render(withIntl(<SaveScopePrompt onConfirm={vi.fn()} onCancel={vi.fn()} />));
    expect(screen.getByTestId("save-to-profile-btn")).toBeTruthy();
    expect(screen.getByTestId("save-cv-only-btn")).toBeTruthy();
  });

  it("'Save to Profile' calls onConfirm with true", () => {
    const onConfirm = vi.fn();
    render(withIntl(<SaveScopePrompt onConfirm={onConfirm} onCancel={vi.fn()} />));
    fireEvent.click(screen.getByTestId("save-to-profile-btn"));
    expect(onConfirm).toHaveBeenCalledWith(true);
  });

  it("'Just this CV' calls onConfirm with false", () => {
    const onConfirm = vi.fn();
    render(withIntl(<SaveScopePrompt onConfirm={onConfirm} onCancel={vi.fn()} />));
    fireEvent.click(screen.getByTestId("save-cv-only-btn"));
    expect(onConfirm).toHaveBeenCalledWith(false);
  });

  it("when remember-choice is checked and CV selected, stores 'cv' in sessionStorage", () => {
    render(withIntl(<SaveScopePrompt onConfirm={vi.fn()} onCancel={vi.fn()} />));
    fireEvent.click(screen.getByTestId("remember-choice-checkbox"));
    fireEvent.click(screen.getByTestId("save-cv-only-btn"));
    expect(sessionStorage.getItem("finetune_save_scope")).toBe("cv");
  });

  it("when remember-choice is checked and profile selected, stores 'profile' in sessionStorage", () => {
    render(withIntl(<SaveScopePrompt onConfirm={vi.fn()} onCancel={vi.fn()} />));
    fireEvent.click(screen.getByTestId("remember-choice-checkbox"));
    fireEvent.click(screen.getByTestId("save-to-profile-btn"));
    expect(sessionStorage.getItem("finetune_save_scope")).toBe("profile");
  });

  it("Cancel calls onCancel", () => {
    const onCancel = vi.fn();
    render(withIntl(<SaveScopePrompt onConfirm={vi.fn()} onCancel={onCancel} />));
    fireEvent.click(screen.getByRole("button", { name: "Abbrechen" }));
    expect(onCancel).toHaveBeenCalledOnce();
  });
});
