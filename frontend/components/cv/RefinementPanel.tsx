// frontend/components/cv/RefinementPanel.tsx
"use client";

import { useState } from "react";
import { ContentTab } from "./ContentTab";
import { ActionsTab } from "./ActionsTab";

type Tab = "content" | "actions";

interface RefinementPanelProps {
  cvId: string;
  jobSummary: string | null;
  gapSummary: { gaps: Array<{ id: string; label: string }>; sections: Array<any> } | null;
  cvSummary: { sections: Array<any> } | null;
  template: { label: string | null } | null;
  matchScore: number | null;
  expiryWarning: { level: "none" | "warning" | "critical"; expiresIn: string } | null;
  onHtmlRefresh: () => void;
  onRegenerateSame: () => void;
  onRegenerateDifferent: () => void;
  onNext: () => void;
  onDownloadPdf: () => void;
}

export function RefinementPanel({
  cvId,
  jobSummary,
  gapSummary,
  cvSummary,
  template,
  matchScore,
  expiryWarning,
  onHtmlRefresh,
  onRegenerateSame,
  onRegenerateDifferent,
  onNext,
  onDownloadPdf,
}: RefinementPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>("content");

  const flowSummary = {
    job_summary: jobSummary,
    gap_summary: gapSummary,
    cv_summary: cvSummary,
  };

  return (
    <div
      className="w-[28%] min-w-[220px] max-w-[360px] h-[calc(100vh-56px)] overflow-y-auto border-l border-neutral-medium bg-white flex flex-col"
      data-testid="refinement-panel"
    >
      {/* Tab strip */}
      <div className="flex border-b border-neutral-medium shrink-0">
        <button
          type="button"
          onClick={() => setActiveTab("content")}
          className={`flex-1 text-sm py-2.5 px-3 font-medium transition-colors ${
            activeTab === "content"
              ? "text-teal border-b-2 border-teal"
              : "text-neutral-medium hover:text-neutral-dark"
          }`}
          role="tab"
          aria-selected={activeTab === "content"}
          data-testid="tab-content"
        >
          &#x1f4dd; Inhalt
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("actions")}
          className={`flex-1 text-sm py-2.5 px-3 font-medium transition-colors ${
            activeTab === "actions"
              ? "text-teal border-b-2 border-teal"
              : "text-neutral-medium hover:text-neutral-dark"
          }`}
          role="tab"
          aria-selected={activeTab === "actions"}
          data-testid="tab-actions"
        >
          &#x2699;&#xfe0f; Aktionen
        </button>
      </div>

      {/* Active tab content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === "content" ? (
          <ContentTab
            cvId={cvId}
            flowSummary={flowSummary}
            onSectionSave={() => onHtmlRefresh()}
            onUnsavedChange={() => {}}
          />
        ) : (
          <ActionsTab
            matchScore={matchScore}
            templateLabel={template?.label ?? null}
            expiryWarning={expiryWarning}
            onDownloadPdf={onDownloadPdf}
            onRegenerateSame={onRegenerateSame}
            onRegenerateDifferent={onRegenerateDifferent}
            onNext={onNext}
          />
        )}
      </div>
    </div>
  );
}
