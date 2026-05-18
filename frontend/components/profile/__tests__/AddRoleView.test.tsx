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

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { AddRoleView } from "../AddRoleView";
import { withIntl } from "@/lib/test-utils/with-intl";

vi.mock("@/lib/profile-roles", () => ({
  addRole: vi.fn().mockResolvedValue({
    profile_id: "p",
    new_role_id: "r",
    closed_role_ids: [],
    completeness_score: 0.85,
  }),
  markApplicationHired: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams("source=manual"),
}));

describe("AddRoleView — manual mode", () => {
  it("renders title, company, start date inputs", () => {
    render(withIntl(<AddRoleView openRoles={[]} />, "en"));
    expect(screen.getByLabelText(/Job title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Company/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Start date/i)).toBeInTheDocument();
  });

  it("disables save until required fields are present", () => {
    render(withIntl(<AddRoleView openRoles={[]} />, "en"));
    const saveBtn = screen.getByRole("button", { name: /Save changes/i });
    expect(saveBtn).toBeDisabled();

    fireEvent.change(screen.getByLabelText(/Job title/i), { target: { value: "Director" } });
    fireEvent.change(screen.getByLabelText(/Company/i), { target: { value: "Roche" } });
    fireEvent.change(screen.getByLabelText(/Start date/i), { target: { value: "2026-06-01" } });

    expect(saveBtn).not.toBeDisabled();
  });
});

describe("AddRoleView — jd_paste mode", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it("renders JD textarea when source=jd_paste", async () => {
    vi.doMock("@/lib/profile-roles", () => ({
      addRole: vi.fn().mockResolvedValue({
        profile_id: "p",
        new_role_id: "r",
        closed_role_ids: [],
        completeness_score: 0.85,
      }),
      markApplicationHired: vi.fn(),
    }));
    vi.doMock("next/navigation", () => ({
      useRouter: () => ({ push: vi.fn() }),
      useSearchParams: () => new URLSearchParams("source=jd_paste"),
    }));
    const { AddRoleView: View } = await import("../AddRoleView");
    render(withIntl(<View openRoles={[]} />, "en"));
    expect(screen.getByLabelText(/Paste the job description/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Analyse/i })).toBeInTheDocument();
  });
});

describe("AddRoleView — application pre-fill", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it("pre-fills title/company from /api/applications/{id}", async () => {
    vi.doMock("@/lib/profile-roles", () => ({
      addRole: vi.fn(),
      markApplicationHired: vi.fn(),
    }));
    vi.doMock("next/navigation", () => ({
      useRouter: () => ({ push: vi.fn() }),
      useSearchParams: () => new URLSearchParams("source=application&application_id=abc"),
    }));
    global.fetch = vi.fn(async (url) => {
      if (String(url).includes("/api/applications/abc")) {
        return new Response(JSON.stringify({
          id: "abc",
          role_title: "Director of QA",
          company_name: "Roche",
          flow_session_id: "f1",
        }));
      }
      throw new Error(`unexpected fetch: ${url}`);
    }) as unknown as typeof fetch;

    const { AddRoleView: View } = await import("../AddRoleView");
    render(withIntl(<View openRoles={[]} />, "en"));
    expect(await screen.findByDisplayValue("Director of QA")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Roche")).toBeInTheDocument();
  });
});
