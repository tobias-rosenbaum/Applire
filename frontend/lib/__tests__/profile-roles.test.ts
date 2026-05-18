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
import { addRole, markApplicationHired } from "../profile-roles";

const okJson = (body: unknown) =>
  ({ ok: true, status: 200, json: () => Promise.resolve(body) } as Response);

describe("addRole", () => {
  it("POSTs the payload to /api/profile/roles and returns the parsed body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      okJson({ profile_id: "p", new_role_id: "r", closed_role_ids: [], completeness_score: 0.8 })
    );
    global.fetch = fetchMock as unknown as typeof fetch;

    const res = await addRole({
      title: "Director", company: "B", start_date: "2026-06-01",
      close_roles: [], source: "manual",
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/profile/roles",
      expect.objectContaining({ method: "POST" })
    );
    expect(res.new_role_id).toBe("r");
  });

  it("throws on non-2xx", async () => {
    global.fetch = vi.fn().mockResolvedValue(
      { ok: false, status: 422, statusText: "Unprocessable", json: () => Promise.resolve({ detail: "bad" }) } as Response
    );
    await expect(addRole({
      title: "x", company: "y", start_date: "2026-06-01",
      close_roles: [], source: "manual",
    })).rejects.toThrow(/bad/);
  });
});

describe("markApplicationHired", () => {
  it("POSTs to the mark-hired endpoint and returns the redirect url", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      okJson({ application_id: "a", user_status: "hired", redirect_url: "/profile/upload?action=add-role&source=application&application_id=a" })
    );
    global.fetch = fetchMock as unknown as typeof fetch;
    const res = await markApplicationHired("a");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/applications/a/mark-hired",
      expect.objectContaining({ method: "POST" })
    );
    expect(res.redirect_url).toContain("action=add-role");
  });
});
