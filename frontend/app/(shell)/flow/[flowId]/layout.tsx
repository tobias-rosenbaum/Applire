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
import { usePathname, useRouter } from "next/navigation";
import { use } from "react";
import { useTranslations } from "next-intl";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

// Maps backend current_step to the sub-route segment
const STEP_ROUTE: Record<string, string> = {
  jd_analysis:   "",          // back to landing — should not normally appear
  cv_import:     "import",
  gap_analysis:  "gaps",
  interview:     "interview",
  cv_generation: "cv",
  complete:      "cv",
};

const STEP_KEYS: { step: string; labelKey: "stepProfile" | "stepGaps" | "stepInterview" | "stepCV" }[] = [
  { step: "cv_import",     labelKey: "stepProfile" },
  { step: "gap_analysis",  labelKey: "stepGaps" },
  { step: "interview",     labelKey: "stepInterview" },
  { step: "cv_generation", labelKey: "stepCV" },
];

interface FlowState {
  flow_id: string;
  user_type: "new" | "returning";
  current_step: string;
  available_actions: Record<string, string>;
  job_summary?: { role_title: string } | null;
  profile_completeness?: number | null;
}

const s = {
  shell: {
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column" as const,
    background: "#f5f5f5",
  },
  topBar: {
    background: "#fff",
    borderBottom: "1px solid #e5e7eb",
    padding: "12px 24px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 16,
  },
  logo: { fontSize: 18, fontWeight: 700, color: "#1a1a2e", textDecoration: "none" },
  jobBadge: {
    fontSize: 12,
    color: "#6b7280",
    background: "#f3f4f6",
    padding: "3px 10px",
    borderRadius: 20,
    maxWidth: 300,
    overflow: "hidden" as const,
    textOverflow: "ellipsis" as const,
    whiteSpace: "nowrap" as const,
  },
  stepper: {
    display: "flex",
    gap: 4,
    alignItems: "center",
  },
  stepBadge: (active: boolean, done: boolean) => ({
    padding: "4px 12px",
    borderRadius: 12,
    fontSize: 12,
    fontWeight: 600,
    background: done ? "#22c55e" : active ? "#2563eb" : "#e2e8f0",
    color: done || active ? "#fff" : "#64748b",
  }),
  main: {
    flex: 1,
    width: "100%",
    overflow: "auto",
  },
  mainConstrained: {
    flex: 1,
    maxWidth: 960,
    width: "100%",
    margin: "0 auto",
    padding: "32px 20px",
  },
  loading: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "60vh",
    fontSize: 14,
    color: "#6b7280",
  },
};

export default function FlowLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ flowId: string }>;
}) {
  const { flowId } = use(params);
  const router = useRouter();
  const pathname = usePathname();
  const t = useTranslations("flow");
  const [flowState, setFlowState] = useState<FlowState | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    async function loadAndGuard() {
      try {
        const res = await fetch(`${API_BASE}/api/flow/${flowId}/state`);
        if (!res.ok) {
          router.replace("/");
          return;
        }
        const state: FlowState = await res.json();
        setFlowState(state);

        // Redirect guard: ensure URL matches backend step
        // Side-routes (e.g. cover-letter) are valid at any step and bypass the guard.
        const SIDE_ROUTES = new Set(["cover-letter"]);
        const expectedSegment = STEP_ROUTE[state.current_step];
        const currentSegment = pathname.split("/").pop() ?? "";

        if (
          expectedSegment &&
          currentSegment !== expectedSegment &&
          state.current_step !== "jd_analysis" &&
          !SIDE_ROUTES.has(currentSegment)
        ) {
          router.replace(`/flow/${flowId}/${expectedSegment}`);
          return;
        }
      } catch {
        router.replace("/");
        return;
      }
      setReady(true);
    }
    void loadAndGuard();
  }, [flowId, pathname, router]);

  const currentSegment = pathname.split("/").pop() ?? "";

  const stepOrder = ["cv_import", "gap_analysis", "interview", "cv_generation"];
  const currentStepIndex = flowState
    ? stepOrder.indexOf(flowState.current_step)
    : -1;

  return (
    <div style={s.shell}>
      <div style={s.topBar}>
        <Link href="/" style={s.logo}>
          Applire
        </Link>

        <div style={s.stepper}>
          {STEP_KEYS.map(({ step, labelKey }, idx) => {
            const isActive = STEP_ROUTE[step] === currentSegment;
            const isDone = currentStepIndex > idx;
            return (
              <span key={step} style={s.stepBadge(isActive, isDone)}>
                {t(labelKey)}
              </span>
            );
          })}
        </div>

        {flowState?.job_summary && (
          <div style={s.jobBadge} title={flowState.job_summary.role_title}>
            {flowState.job_summary.role_title}
          </div>
        )}
      </div>

      <div style={currentSegment === "cv" ? s.main : s.mainConstrained}>
        {ready ? children : <div style={s.loading}>{t("loading")}</div>}
      </div>
    </div>
  );
}
