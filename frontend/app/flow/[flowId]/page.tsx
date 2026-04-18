"use client";

import { use, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

// Mirrors STEP_ROUTE in layout.tsx
const STEP_ROUTE: Record<string, string> = {
  cv_import: "import",
  gap_analysis: "gaps",
  interview: "interview",
  cv_generation: "cv",
  complete: "cv",
};

/**
 * Entry-point page for /flow/[flowId].
 *
 * The layout handles redirect for mid-flow steps (gap_analysis → /gaps, etc.).
 * This page handles the jd_analysis step: JD has already been analysed by the
 * time the user lands here, so we immediately advance to the next step and
 * redirect.  If the layout already redirected (non-jd_analysis step), this
 * page never mounts.
 */
export default function FlowIndexPage({
  params,
}: {
  params: Promise<{ flowId: string }>;
}) {
  const { flowId } = use(params);
  const router = useRouter();
  const t = useTranslations("flow");

  useEffect(() => {
    async function advanceAndRedirect() {
      try {
        const stateRes = await fetch(`${API_BASE}/api/flow/${flowId}/state`);
        if (!stateRes.ok) {
          router.replace("/");
          return;
        }
        const state = await stateRes.json();

        const nextStep: string | undefined = state.available_actions?.next;
        if (!nextStep) {
          router.replace("/");
          return;
        }

        // gap_analysis requires an artifact_id (the gap analysis result).
        // Run the analysis here — before advancing — so the flow stores the
        // gap_analysis_id.  This ensures the gaps page always reads a cached
        // result instead of re-running the LLM on every load.
        let artifactId: string | undefined;
        if (nextStep === "gap_analysis" && state.job_id) {
          const gapRes = await fetch(`${API_BASE}/api/job/${state.job_id}/gaps`, {
            method: "POST",
          });
          if (!gapRes.ok) {
            router.replace("/");
            return;
          }
          const gapData = await gapRes.json();
          artifactId = gapData.id;
        }

        const advRes = await fetch(`${API_BASE}/api/flow/${flowId}/advance`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            step: nextStep,
            ...(artifactId ? { artifact_id: artifactId } : {}),
          }),
        });

        if (advRes.ok) {
          const newState = await advRes.json();
          const segment = STEP_ROUTE[newState.current_step];
          if (segment) {
            router.replace(`/flow/${flowId}/${segment}`);
            return;
          }
        }
      } catch {
        // network error — fall through to dashboard
      }
      router.replace("/");
    }

    void advanceAndRedirect();
  }, [flowId, router]);

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "40vh",
        color: "#6b7280",
        fontSize: 14,
      }}
    >
      {t("starting")}
    </div>
  );
}
