// frontend/app/flow/[flowId]/cv/page.tsx
"use client";

import { use, useEffect, useState } from "react";
import { TemplateSelector } from "@/components/cv/TemplateSelector";
import { GenerationProgress } from "@/components/cv/GenerationProgress";
import { CVPreview } from "@/components/cv/CVPreview";
import { WhatNext } from "@/components/cv/WhatNext";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

type Phase = "template_select" | "generating" | "preview" | "complete";
type CVTemplate = "classic_german" | "modern_swiss";

interface FlowState {
  job_id: string;
  job_summary?: { role_title: string } | null;
  gap_summary?: { match_score: number } | null;
  cv_summary?: { cv_id: string; pdf_url: string; expires_at: string } | null;
}

export default function CVPage({
  params,
}: {
  params: Promise<{ flowId: string }>;
}) {
  const { flowId } = use(params);

  const [phase, setPhase] = useState<Phase>("template_select");
  const [cvId, setCvId] = useState<string | null>(null);
  const [template, setTemplate] = useState<CVTemplate>("classic_german");
  const [flowState, setFlowState] = useState<FlowState | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  // Restore state from server on mount — skip template picker if CV already exists
  useEffect(() => {
    async function init() {
      try {
        const res = await fetch(`${API_BASE}/api/flow/${flowId}/state`);
        if (!res.ok) return;
        const fs: FlowState = await res.json();
        setFlowState(fs);
        if (fs.cv_summary?.cv_id) {
          setCvId(fs.cv_summary.cv_id);
          setPhase("preview");
        }
      } catch {
        // Non-fatal — user sees template picker
      }
    }
    void init();
  }, [flowId]);

  async function handleGenerate(tpl: CVTemplate) {
    if (!flowState) return;
    setTemplate(tpl);
    setIsGenerating(true);
    try {
      const res = await fetch(`${API_BASE}/api/cv/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: flowState.job_id, template: tpl }),
      });
      if (!res.ok) return;
      // Only cv_id, status, expires_at are returned — NOT html_url/pdf_url
      const data: { cv_id: string; status: string; expires_at: string } = await res.json();
      setCvId(data.cv_id);
      setPhase("generating");
    } finally {
      setIsGenerating(false);
    }
  }

  function handleReady(readyCvId: string) {
    setCvId(readyCvId);
    // Refresh flow state so cv_summary is populated for CVPreview
    fetch(`${API_BASE}/api/flow/${flowId}/state`)
      .then((r) => r.json())
      .then((fs: FlowState) => setFlowState(fs))
      .catch(() => {});
    setPhase("preview");
  }

  return (
    <div className="p-6 min-h-screen bg-neutral-light" data-testid="cv-page">
      {phase === "template_select" && (
        <TemplateSelector onGenerate={handleGenerate} isLoading={isGenerating} />
      )}

      {phase === "generating" && cvId && (
        <GenerationProgress
          cvId={cvId}
          flowId={flowId}
          onReady={handleReady}
          onRetry={() => setPhase("template_select")}
        />
      )}

      {phase === "preview" && cvId && (
        <CVPreview
          cvId={cvId}
          template={template}
          jobSummary={flowState?.job_summary ?? null}
          gapSummary={flowState?.gap_summary ?? null}
          cvSummary={flowState?.cv_summary ?? null}
          onRegenerateDifferent={() => setPhase("template_select")}
          onRegenerateSame={() => {
            if (flowState) void handleGenerate(template);
          }}
          onNext={() => setPhase("complete")}
        />
      )}

      {phase === "complete" && (
        <WhatNext flowId={flowId} roleTitle={flowState?.job_summary?.role_title} />
      )}
    </div>
  );
}
