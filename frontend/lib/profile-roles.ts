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

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export type AddRoleSource = "application" | "jd_paste" | "manual";

export interface CloseRoleEntry {
  role_id: string;
  end_date: string;
}

export interface AddRoleRequest {
  title: string;
  company: string;
  start_date: string;
  location?: string | null;
  industry?: string | null;
  close_roles: CloseRoleEntry[];
  source: AddRoleSource;
  source_ref?: string | null;
}

export interface AddRoleResponse {
  profile_id: string;
  new_role_id: string;
  closed_role_ids: string[];
  completeness_score: number;
}

export interface MarkHiredResponse {
  application_id: string;
  user_status: string;
  redirect_url: string;
}

async function unwrap<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // ignore parse error
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

export async function addRole(body: AddRoleRequest): Promise<AddRoleResponse> {
  const res = await fetch(`${API_BASE}/api/profile/roles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return unwrap<AddRoleResponse>(res);
}

export async function markApplicationHired(applicationId: string): Promise<MarkHiredResponse> {
  const res = await fetch(`${API_BASE}/api/applications/${applicationId}/mark-hired`, {
    method: "POST",
  });
  return unwrap<MarkHiredResponse>(res);
}

export interface OpenRoleDTO {
  id: string;
  company: string;
  role: string;
  start_date: string | null;
}

export async function fetchOpenRoles(): Promise<OpenRoleDTO[]> {
  const res = await fetch(`${API_BASE}/api/profile`);
  if (!res.ok) return [];
  const body = await res.json();
  const items = body?.profile?.work_experience ?? body?.work_experience ?? [];
  return items
    .filter((w: { end_date?: string | null }) => !w.end_date)
    .map((w: { id: string; company: string; role: string; start_date: string | null }) => ({
      id: w.id,
      company: w.company,
      role: w.role,
      start_date: w.start_date,
    }));
}
