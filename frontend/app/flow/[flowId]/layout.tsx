"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { use } from "react";

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

const STEP_LABELS: { step: string; label: string }[] = [
  { step: "cv_import",     label: "1 Profil" },
  { step: "gap_analysis",  label: "2 Lücken" },
  { step: "interview",     label: "3 Interview" },
  { step: "cv_generation", label: "4 Lebenslauf" },
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
    overflow: "hidden",
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
        const expectedSegment = STEP_ROUTE[state.current_step];
        const currentSegment = pathname.split("/").pop() ?? "";

        if (
          expectedSegment &&
          currentSegment !== expectedSegment &&
          state.current_step !== "jd_analysis"
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
        <a href="/" style={s.logo}>
          Applire
        </a>

        <div style={s.stepper}>
          {STEP_LABELS.map(({ step, label }, idx) => {
            const isActive = STEP_ROUTE[step] === currentSegment;
            const isDone = currentStepIndex > idx;
            return (
              <span key={step} style={s.stepBadge(isActive, isDone)}>
                {label}
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
        {ready ? children : <div style={s.loading}>Lade …</div>}
      </div>
    </div>
  );
}
