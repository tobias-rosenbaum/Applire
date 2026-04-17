/**
 * ProcessingOverlay — JD URL error handling (Sprint 26)
 *
 * Verifies that a 422 response with error_code="jd_fetch_failed" causes the
 * JD step to be marked "skipped" (not error) and the pipeline to continue.
 */
import { render, screen, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { ProcessingOverlay } from "../processing-overlay";
import { withIntl } from "@/lib/test-utils/with-intl";

// next/navigation must be mocked — jsdom has no router
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const mockFile = new File(["cv content"], "cv.pdf", { type: "application/pdf" });

const DEFAULT_PROPS = {
  files: [mockFile],
  jdMode: "url" as const,
  jdUrl: "https://blocked.example.com/job",
  jdText: "",
  onCancel: vi.fn(),
};

describe("ProcessingOverlay — JD URL error handling", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("marks JD step as skipped and continues to upload when JD analyze returns jd_fetch_failed", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();

      // JD analyze → 422 jd_fetch_failed
      if (url.includes("/api/job/analyze")) {
        return {
          ok: false,
          status: 422,
          statusText: "Unprocessable Entity",
          json: async () => ({ detail: { error_code: "jd_fetch_failed", message: "blocked" } }),
        } as Response;
      }

      // Flow creation (bare flow, no job)
      if (url.includes("/api/flow") && !url.includes("advance") && !url.includes("state")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({ flow_id: "test-flow-xyz" }),
        } as Response;
      }

      // CV upload
      if (url.includes("/api/profile/upload")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({}),
        } as Response;
      }

      // Fallback
      return {
        ok: true,
        status: 200,
        json: async () => ({}),
      } as Response;
    });

    render(withIntl(<ProcessingOverlay {...DEFAULT_PROPS} />));

    // JD step skip message must appear
    await waitFor(
      () => {
        expect(
          screen.getByText("The site blocked us — you can paste the text later")
        ).toBeInTheDocument();
      },
      { timeout: 5000 }
    );

    // No hard error block should be rendered
    expect(screen.queryByTestId("processing-error")).toBeNull();

    // Upload step must become active (pipeline continued)
    await waitFor(
      () => {
        expect(screen.getByText("Uploading CV")).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
  });

  it("marks JD step as skipped with url_invalid copy when error_code is jd_url_invalid", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();

      if (url.includes("/api/job/analyze")) {
        return {
          ok: false,
          status: 422,
          statusText: "Unprocessable Entity",
          json: async () => ({ detail: { error_code: "jd_url_invalid", message: "not a valid url" } }),
        } as Response;
      }

      if (url.includes("/api/flow") && !url.includes("advance") && !url.includes("state")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({ flow_id: "test-flow-abc" }),
        } as Response;
      }

      if (url.includes("/api/profile/upload")) {
        return { ok: true, status: 200, json: async () => ({}) } as Response;
      }

      return { ok: true, status: 200, json: async () => ({}) } as Response;
    });

    render(withIntl(<ProcessingOverlay {...DEFAULT_PROPS} />));

    await waitFor(
      () => {
        expect(
          screen.getByText("That doesn't look like a valid URL — you can add it later")
        ).toBeInTheDocument();
      },
      { timeout: 5000 }
    );

    expect(screen.queryByTestId("processing-error")).toBeNull();
  });

  it("still hard-stops on unrecognised 422 (no error_code)", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input.toString();

      if (url.includes("/api/job/analyze")) {
        return {
          ok: false,
          status: 422,
          statusText: "Unprocessable Entity",
          // Old-style plain string detail — should hard-stop
          json: async () => ({ detail: "Some unknown validation error" }),
        } as Response;
      }

      return { ok: true, status: 200, json: async () => ({}) } as Response;
    });

    render(withIntl(<ProcessingOverlay {...DEFAULT_PROPS} />));

    await waitFor(
      () => {
        expect(screen.getByTestId("processing-error")).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
  });
});
