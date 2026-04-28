import { render, screen, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { GenerationProgress } from "../GenerationProgress";
import { withIntl } from "@/lib/test-utils/with-intl";

const DEFAULT_PROPS = {
  cvId: "test-cv-id",
  flowId: "test-flow-id",
  onReady: vi.fn(),
  onRetry: vi.fn(),
};

describe("GenerationProgress", () => {
  afterEach(() => vi.restoreAllMocks());

  it("renders all three step labels immediately", () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({}),
    } as Response);

    render(withIntl(<GenerationProgress {...DEFAULT_PROPS} />));

    expect(screen.getByText("In queue…")).toBeInTheDocument();
    expect(screen.getByText("Rendering CV…")).toBeInTheDocument();
    expect(screen.getByText("Done!")).toBeInTheDocument();
  });

  it("marks queued step active and others pending on initial render", () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        cv_id: "test-cv-id",
        status: "pending",
        error_message: null,
        expires_at: "2026-05-01T00:00:00Z",
      }),
    } as Response);

    render(withIntl(<GenerationProgress {...DEFAULT_PROPS} />));

    const queued = screen.getByText("In queue…").closest("[data-step-status]");
    expect(queued).toHaveAttribute("data-step-status", "active");
    const rendering = screen.getByText("Rendering CV…").closest("[data-step-status]");
    expect(rendering).toHaveAttribute("data-step-status", "pending");
  });

  it("marks queued done and rendering active when status is generating", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        cv_id: "test-cv-id",
        status: "generating",
        error_message: null,
        expires_at: "2026-05-01T00:00:00Z",
      }),
    } as Response);

    render(withIntl(<GenerationProgress {...DEFAULT_PROPS} />));

    await waitFor(() => {
      const queued = screen.getByText("In queue…").closest("[data-step-status]");
      expect(queued).toHaveAttribute("data-step-status", "done");
      const rendering = screen.getByText("Rendering CV…").closest("[data-step-status]");
      expect(rendering).toHaveAttribute("data-step-status", "active");
    });
  });

  it("shows error message and retry button when status is failed", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        cv_id: "test-cv-id",
        status: "failed",
        error_message: "Something went wrong.",
        expires_at: "2026-05-01T00:00:00Z",
      }),
    } as Response);

    render(withIntl(<GenerationProgress {...DEFAULT_PROPS} />));

    await waitFor(() => {
      expect(screen.getByText("Something went wrong.")).toBeInTheDocument();
      expect(screen.getByText("Try again →")).toBeInTheDocument();
    });
  });

  it("calls onReady when status becomes ready", async () => {
    const onReady = vi.fn();
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        cv_id: "test-cv-id",
        status: "ready",
        error_message: null,
        expires_at: "2026-05-01T00:00:00Z",
      }),
    } as Response);

    render(withIntl(<GenerationProgress {...DEFAULT_PROPS} onReady={onReady} />));

    await waitFor(() => {
      expect(onReady).toHaveBeenCalledWith("test-cv-id");
    });
  });
});
