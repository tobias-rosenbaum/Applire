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

import { getApiErrorMessage } from "./errors";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export interface GapItem {
  id: string;
  label: string;
  status: "pending" | "active" | "done" | "na" | "skipped";
}

export interface EnrichSession {
  session_id: string;
  first_question: string;
  gaps: GapItem[];
  estimated_questions: number;
}

export interface EnrichRespondResult {
  next_question: string | null;
  gaps: GapItem[];
  done: boolean;
  profile_updated: boolean;
}

export interface EnrichActionResult {
  next_question: string | null;
  gaps: GapItem[];
  done: boolean;
}

export async function startEnrichSession(scope?: string): Promise<EnrichSession> {
  const res = await fetch(`${API_BASE}/api/profile/enrich/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scope: scope ?? null }),
  });
  if (!res.ok) {
    const errorMsg = await getApiErrorMessage(res);
    throw new Error(errorMsg);
  }
  return res.json();
}

export async function respondToEnrich(
  sessionId: string,
  answer: string
): Promise<EnrichRespondResult> {
  const res = await fetch(`${API_BASE}/api/profile/enrich/${sessionId}/respond`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answer }),
  });
  if (!res.ok) {
    const errorMsg = await getApiErrorMessage(res);
    throw new Error(errorMsg);
  }
  return res.json();
}

export async function skipGap(sessionId: string): Promise<EnrichActionResult> {
  const res = await fetch(`${API_BASE}/api/profile/enrich/${sessionId}/skip`, {
    method: "POST",
  });
  if (!res.ok) {
    const errorMsg = await getApiErrorMessage(res);
    throw new Error(errorMsg);
  }
  return res.json();
}

export async function markGapNA(sessionId: string): Promise<EnrichActionResult> {
  const res = await fetch(`${API_BASE}/api/profile/enrich/${sessionId}/na`, {
    method: "POST",
  });
  if (!res.ok) {
    const errorMsg = await getApiErrorMessage(res);
    throw new Error(errorMsg);
  }
  return res.json();
}
