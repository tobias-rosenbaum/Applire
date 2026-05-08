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

import { render, screen, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { CVPreview } from "../CVPreview";

const BASE_PROPS = {
  cvId: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  template: "classic_german" as const,
  jobSummary: null,
  gapSummary: null,
  cvSummary: null,
  onRegenerateDifferent: vi.fn(),
  onRegenerateSame: vi.fn(),
  onNext: vi.fn(),
};

const TEST_HTML = "<html><body><p>Max Mustermann</p></body></html>";

describe("CVPreview", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders a loading skeleton while fetch is in flight", () => {
    vi.spyOn(globalThis, "fetch").mockReturnValue(new Promise(() => {})); // never resolves

    render(<CVPreview {...BASE_PROPS} />);

    expect(screen.queryByTestId("cv-iframe")).toBeNull();
    // The skeleton has the animate-pulse class
    const skeleton = document.querySelector(".animate-pulse");
    expect(skeleton).not.toBeNull();
  });

  it("renders iframe with srcDoc after successful fetch", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      text: async () => TEST_HTML,
    } as Response);

    render(<CVPreview {...BASE_PROPS} />);

    const iframe = await screen.findByTestId("cv-iframe");
    expect(iframe.getAttribute("srcdoc")).toBe(TEST_HTML);
    expect(iframe.getAttribute("sandbox")).toBe("allow-same-origin");
    expect(iframe.tagName.toLowerCase()).toBe("iframe");
  });

  it("renders error message with retry button when fetch fails", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network error"));

    render(<CVPreview {...BASE_PROPS} />);

    await screen.findByText("Vorschau konnte nicht geladen werden.");
    expect(
      screen.getByRole("button", { name: "Erneut versuchen" })
    ).toBeTruthy();
    expect(screen.queryByTestId("cv-iframe")).toBeNull();
  });

  it("re-fetches and shows iframe when retry button is clicked", async () => {
    const mockFetch = vi
      .spyOn(globalThis, "fetch")
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce({
        ok: true,
        text: async () => TEST_HTML,
      } as unknown as Response);

    render(<CVPreview {...BASE_PROPS} />);

    // Wait for error state
    await screen.findByText("Vorschau konnte nicht geladen werden.");

    // Click retry
    fireEvent.click(screen.getByRole("button", { name: "Erneut versuchen" }));

    // iframe should appear after re-fetch
    const iframe = await screen.findByTestId("cv-iframe");
    expect(iframe.getAttribute("srcdoc")).toBe(TEST_HTML);
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });
});
