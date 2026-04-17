"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { Card } from "@/components/ui/card";
import { ProgressLinear } from "@/components/ui/progress";
import { StepChecklist, StepItem, StepState } from "@/components/ui/step-checklist";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

async function apiErrorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    const detail = body.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail))
      return detail.map((e: { msg?: string }) => e.msg ?? JSON.stringify(e)).join("; ");
    return res.statusText || `HTTP ${res.status}`;
  } catch {
    return res.statusText || `HTTP ${res.status}`;
  }
}

const INITIAL_STATES: Record<string, StepState> = {
  analyze_jd: "pending",
  upload: "pending",
  build_profile: "pending",
  detect_gaps: "pending",
};

interface Props {
  files: File[];
  jdMode: "url" | "text";
  jdUrl: string;
  jdText: string;
  onCancel: () => void;
}

export function ProcessingOverlay({ files, jdMode, jdUrl, jdText, onCancel }: Props) {
  const router = useRouter();
  const t = useTranslations("processing");

  const STEPS: StepItem[] = [
    { key: "analyze_jd", label: t("analyzingJD") },
    { key: "upload", label: "Uploading CV" },
    { key: "build_profile", label: t("buildingProfile") },
    { key: "detect_gaps", label: "Detecting Gaps" },
  ];

  const [stepStates, setStepStates] = useState<Record<string, StepState>>(INITIAL_STATES);
  const [stepDetails, setStepDetails] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const started = useRef(false);

  function markStep(key: string, state: StepState, detail?: string) {
    setStepStates((prev) => ({ ...prev, [key]: state }));
    if (detail !== undefined) setStepDetails((prev) => ({ ...prev, [key]: detail }));
  }

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    async function runPipeline() {
      try {
        let jobId: string | null = null;
        let jdFailReason: "url_invalid" | "fetch_failed" | null = null;

        // Step 1: Analyze Job Description
        markStep("analyze_jd", "in_progress");
        if (jdMode === "url" && jdUrl.trim()) {
          const res = await fetch(`${API_BASE}/api/job/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: jdUrl.trim() }),
          });
          if (!res.ok) {
            if (res.status === 422) {
              let body: { detail?: { error_code?: string; message?: string } | string | unknown[] } | null = null;
              try {
                body = await res.json();
              } catch {
                // body stays null
              }
              const detail =
                body?.detail && typeof body.detail === "object" && !Array.isArray(body.detail)
                  ? body.detail
                  : null;
              const errorCode = detail?.error_code;
              if (errorCode === "jd_url_invalid") {
                markStep("analyze_jd", "skipped", t("jdUrlInvalid"));
                jdFailReason = "url_invalid";
              } else if (errorCode === "jd_fetch_failed") {
                markStep("analyze_jd", "skipped", t("jdFetchFailed"));
                jdFailReason = "fetch_failed";
              } else {
                // Unrecognised 422 — hard stop
                const msg =
                  typeof body?.detail === "string" ? body.detail
                  : detail?.message ?? res.statusText ?? `HTTP ${res.status}`;
                throw new Error(msg);
              }
            } else {
              throw new Error(await apiErrorMessage(res));
            }
          } else {
            const data = await res.json();
            jobId = data.id;
            markStep("analyze_jd", "completed", data.role_title ? `Role: ${data.role_title}` : "Job description analyzed");
          }
        } else if (jdMode === "text" && jdText.trim()) {
          const res = await fetch(`${API_BASE}/api/job/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: jdText }),
          });
          if (!res.ok) throw new Error(await apiErrorMessage(res));
          const data = await res.json();
          jobId = data.id;
          markStep("analyze_jd", "completed", data.role_title ? `Role: ${data.role_title}` : "Job description analyzed");
        } else {
          markStep("analyze_jd", "completed", "No job description — skipped");
        }

        // Step 2: Create flow session + Upload CVs
        markStep("upload", "in_progress");

        // When a job was analyzed, create an Application record (+ FlowSession)
        // atomically so it appears on the dashboard. Without a job there is nothing
        // to track yet, so fall back to a bare FlowSession.
        let flowId: string;
        if (jobId !== null) {
          const appRes = await fetch(`${API_BASE}/api/applications`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ job_analysis_id: jobId, start_workflow: true }),
          });
          if (!appRes.ok) throw new Error(await apiErrorMessage(appRes));
          const appData = await appRes.json();
          flowId = appData.flow_session_id;
        } else {
          const flowRes = await fetch(`${API_BASE}/api/flow`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ job_id: null }),
          });
          if (!flowRes.ok) throw new Error(await apiErrorMessage(flowRes));
          const flow = await flowRes.json();
          flowId = flow.flow_id;
        }

        for (const file of files) {
          const formData = new FormData();
          formData.append("file", file);
          const uploadRes = await fetch(`${API_BASE}/api/profile/upload`, {
            method: "POST",
            body: formData,
          });
          if (!uploadRes.ok) throw new Error(await apiErrorMessage(uploadRes));
        }

        const cvLabel = files.length === 1 ? "1 CV uploaded" : `${files.length} CVs uploaded`;
        markStep("upload", "completed", cvLabel);

        // Step 3: Build profile (instant — upload already did the work)
        markStep("build_profile", "in_progress");
        await new Promise((r) => setTimeout(r, 400));
        const profileDetail =
          files.length === 1
            ? "Updated master profile with 1 new CV"
            : `Updated master profile with ${files.length} new CVs`;
        markStep("build_profile", "completed", profileDetail);

        // Step 4: Detect gaps (only if a job was linked)
        markStep("detect_gaps", "in_progress");

        if (!jobId) {
          markStep("detect_gaps", "completed", "No job linked — skipped");
          await new Promise((r) => setTimeout(r, 400));
          const gapsUrl = jdFailReason
            ? `/flow/${flowId}/gaps?jd_status=${jdFailReason}`
            : `/flow/${flowId}/gaps`;
          router.push(gapsUrl);
          return;
        }

        const stateRes = await fetch(`${API_BASE}/api/flow/${flowId}/state`);
        if (!stateRes.ok) throw new Error("Could not retrieve flow state");
        const flowState = await stateRes.json();
        const linkedJobId: string = flowState.job_id ?? jobId;

        const gapRes = await fetch(`${API_BASE}/api/job/${linkedJobId}/gaps`, {
          method: "POST",
        });
        if (!gapRes.ok) throw new Error(await apiErrorMessage(gapRes));
        const gapData = await gapRes.json();

        await fetch(`${API_BASE}/api/flow/${flowId}/advance`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ step: "gap_analysis", artifact_id: gapData.id ?? null }),
        });

        const score = gapData.match_score ?? gapData.overall_score;
        const gapDetail =
          score != null ? `Match score: ${Math.round(score * 100)}%` : "Gap analysis complete";
        markStep("detect_gaps", "completed", gapDetail);

        await new Promise((r) => setTimeout(r, 400));
        const gapsUrl = jdFailReason
          ? `/flow/${flowId}/gaps?jd_status=${jdFailReason}`
          : `/flow/${flowId}/gaps`;
        router.push(gapsUrl);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "An error occurred. Please try again.");
      }
    }

    runPipeline();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const completedCount = Object.values(stepStates).filter((s) => s === "completed" || s === "skipped").length;
  const progress = (completedCount / STEPS.length) * 100;

  const stepsWithDetails = STEPS.map((step) => ({
    ...step,
    detail: stepDetails[step.key],
  }));

  return (
    <div data-testid="processing-indicator" className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm px-4">
      <Card className="w-full max-w-[560px] p-8">
        <div className="text-center mb-8">
          <h2 className="font-heading text-2xl font-bold text-neutral-dark mb-2">
            Processing Your Profile
          </h2>
          <p className="text-sm text-gray-500">
            Analyzing your CV and building your master profile
          </p>
        </div>

        {error ? (
          <div className="space-y-4">
            <div data-testid="processing-error" className="p-4 rounded-lg bg-critical/10 border border-critical/20">
              <p className="text-sm text-critical">{error}</p>
            </div>
            <div className="flex justify-center">
              <button
                onClick={onCancel}
                data-testid="cancel-button"
                className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-neutral-dark transition-colors"
              >
                ← Go back and try again
              </button>
            </div>
          </div>
        ) : (
          <>
            <StepChecklist steps={stepsWithDetails} stepStates={stepStates} />
            <div className="mt-8">
              <ProgressLinear value={progress} data-testid="progress-bar" />
              <p data-testid="progress-text" className="text-xs text-gray-500 text-center mt-2">
                {Math.round(progress)}% complete
              </p>
            </div>
            <p className="text-xs text-gray-500 text-center mt-6">
              This usually takes about 30 seconds
            </p>
          </>
        )}
      </Card>
    </div>
  );
}