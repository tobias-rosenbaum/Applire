"use client";

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


import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? (process.env.NODE_ENV === "development" ? "http://localhost:8001" : "");

interface ChecklistItem {
  label: string;
  done: boolean;
}

function buildChecklist(profile: Record<string, unknown> | null): ChecklistItem[] {
  if (!profile) return [];
  const pi = (profile.personal_info as Record<string, unknown>) ?? {};
  const work = (profile.work_experience as unknown[]) ?? [];
  const skills = (profile.skills as unknown[]) ?? [];
  const edu = (profile.education as unknown[]) ?? [];
  return [
    { label: "Berufserfahrung", done: work.length > 0 },
    { label: "Fähigkeiten", done: skills.length > 0 },
    { label: "Ausbildung", done: edu.length > 0 },
    { label: "Zusammenfassung", done: !!(pi.summary as string) },
  ];
}

export function ProfileStrengthCard() {
  const router = useRouter();
  const [score, setScore] = useState<number | null>(null);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const [existsRes, profileRes] = await Promise.all([
          fetch(`${API_BASE}/api/profile/exists`),
          fetch(`${API_BASE}/api/profile`),
        ]);
        if (existsRes.ok) {
          const d = await existsRes.json();
          setScore(Math.round((d.completeness_score ?? 0) * 100));
        }
        if (profileRes.ok) {
          const d = await profileRes.json();
          setChecklist(buildChecklist(d.profile ?? null));
        }
      } catch {
        // non-fatal — card stays in skeleton state
      }
    }
    void load();
  }, []);

  const barWidth = score !== null ? `${score}%` : "0%";

  return (
    <div className="rounded-[14px] p-5 text-white flex flex-col bg-gradient-to-br from-teal-dim to-primary shadow-lg shadow-teal-dim/20">
      <p className="text-[11px] font-bold uppercase tracking-widest text-white/60 mb-1.5">
        Profile Strength
      </p>

      {score === null ? (
        <div className="h-12 w-20 rounded bg-white/10 animate-pulse mb-3" />
      ) : (
        <p className="text-[46px] font-extrabold leading-none font-manrope mb-2.5">{score}</p>
      )}

      {/* Progress bar */}
      <div className="h-[5px] bg-white/20 rounded-full mb-2">
        <div
          className="h-[5px] bg-gold rounded-full transition-all duration-700"
          style={{ width: barWidth }}
        />
      </div>
      <p className="text-[11.5px] text-white/60 mb-3">
        Add missing sections to improve gap matching.
      </p>

      {/* Checklist */}
      <div className="flex flex-col gap-1.5 mb-4">
        {checklist.map((item) => (
          <div key={item.label} className="flex items-center gap-2 text-[11.5px]">
            <span
              className="material-symbols-outlined"
              style={{
                fontSize: 14,
                color: item.done ? "#4ade80" : "rgba(255,255,255,0.25)",
              }}
            >
              {item.done ? "check_circle" : "radio_button_unchecked"}
            </span>
            <span className={item.done ? "text-white/75" : "text-white/40"}>{item.label}</span>
          </div>
        ))}
      </div>

      <button
        onClick={() => router.push("/profile")}
        className="mt-auto text-[12px] font-bold text-gold flex items-center gap-1 hover:opacity-80 transition-opacity"
      >
        <span className="material-symbols-outlined" style={{ fontSize: 15 }}>arrow_forward</span>
        Complete Profile
      </button>
    </div>
  );
}
