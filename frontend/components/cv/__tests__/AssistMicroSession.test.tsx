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

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { AssistMicroSession } from "../AssistMicroSession";
import { withIntl } from "@/lib/test-utils/with-intl";

const GAP = { id: "Python", label: "Python" };
const BASE_PROPS = {
  cvId: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  sectionId: "introduction",
  gap: GAP,
  onAccept: vi.fn(),
  onEdit: vi.fn(),
  onReject: vi.fn(),
};

describe("AssistMicroSession", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows loading state then renders the question", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ session_id: "s1", question: "Wie lange Python?" }),
    } as Response);

    render(withIntl(<AssistMicroSession {...BASE_PROPS} />));
    // Initially shows loading
    expect(screen.getByTestId("assist-loading")).toBeTruthy();

    await screen.findByTestId("assist-question");
    expect(screen.getByTestId("assist-question").textContent).toContain("Wie lange Python?");
  });

  it("submitting answer shows suggestion with Accept/Edit/Reject", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session_id: "s1", question: "Wie lange Python?" }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ suggestion: "Erfahrener Python-Entwickler." }),
      } as Response);

    render(withIntl(<AssistMicroSession {...BASE_PROPS} />));
    await screen.findByTestId("assist-answer");
    fireEvent.change(screen.getByTestId("assist-answer"), {
      target: { value: "5 Jahre" },
    });
    fireEvent.click(screen.getByTestId("assist-submit"));

    await screen.findByTestId("assist-accept");
    expect(screen.getByTestId("assist-accept")).toBeTruthy();
    expect(screen.getByTestId("assist-edit")).toBeTruthy();
    expect(screen.getByTestId("assist-reject")).toBeTruthy();
  });

  it("Accept calls onAccept with suggestion", async () => {
    const onAccept = vi.fn();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session_id: "s1", question: "Frage?" }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ suggestion: "Verbessert." }),
      } as Response);

    render(withIntl(<AssistMicroSession {...BASE_PROPS} onAccept={onAccept} />));
    await screen.findByTestId("assist-answer");
    fireEvent.change(screen.getByTestId("assist-answer"), { target: { value: "Antwort" } });
    fireEvent.click(screen.getByTestId("assist-submit"));
    await screen.findByTestId("assist-accept");
    fireEvent.click(screen.getByTestId("assist-accept"));
    expect(onAccept).toHaveBeenCalledWith("Verbessert.");
  });

  it("Edit calls onEdit with suggestion", async () => {
    const onEdit = vi.fn();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session_id: "s1", question: "Frage?" }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ suggestion: "Verbessert." }),
      } as Response);

    render(withIntl(<AssistMicroSession {...BASE_PROPS} onEdit={onEdit} />));
    await screen.findByTestId("assist-answer");
    fireEvent.change(screen.getByTestId("assist-answer"), { target: { value: "Antwort" } });
    fireEvent.click(screen.getByTestId("assist-submit"));
    await screen.findByTestId("assist-edit");
    fireEvent.click(screen.getByTestId("assist-edit"));
    expect(onEdit).toHaveBeenCalledWith("Verbessert.");
  });

  it("Reject calls onReject", async () => {
    const onReject = vi.fn();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session_id: "s1", question: "Frage?" }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ suggestion: "Verbessert." }),
      } as Response);

    render(withIntl(<AssistMicroSession {...BASE_PROPS} onReject={onReject} />));
    await screen.findByTestId("assist-answer");
    fireEvent.change(screen.getByTestId("assist-answer"), { target: { value: "Antwort" } });
    fireEvent.click(screen.getByTestId("assist-submit"));
    await screen.findByTestId("assist-reject");
    fireEvent.click(screen.getByTestId("assist-reject"));
    expect(onReject).toHaveBeenCalledOnce();
  });
});
