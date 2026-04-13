// frontend/components/cv/RefinementPanel.tsx
"use client";

import { useState } from "react";
import { ContentTab } from "./ContentTab";
import { ActionsTab } from "./ActionsTab";
import { DesignTab } from "./DesignTab";

type Tab = "content" | "actions" | "appearance";

interface RefinementPanelProps {
  cvId: string;
  jobSummary: string | null;
  gapSummary: { gaps: Array<{ id: string; label: string }>; sections: Array<any> } | null;
  cvSummary: { sections: Array<any> } | null;
  template: { label: string | null } | null;
  matchScore: number | null;
  expiryWarning: { level: "none" | "warning" | "critical"; expiresIn: string } | null;
  detectedCompany: { name: string; hex: string } | null;
  currentAccentHex: string;
  onHtmlRefresh: () => void;
  onRegenerateSame: () => void;
  onRegenerateDifferent: () => void;
  onRegenerateWithTemplate: (template: string) => void;
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
  detectedCompany,
  currentAccentHex,
  onHtmlRefresh,
  onRegenerateSame,
  onRegenerateDifferent,
  onRegenerateWithTemplate,
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
      className="w-1/2 h-[calc(100vh-56px)] overflow-y-auto border-l border-neutral-medium bg-white flex flex-col"
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
        <button
          type="button"
          onClick={() => setActiveTab("appearance")}
          className={`flex-1 text-sm py-2.5 px-3 font-medium transition-colors ${
            activeTab === "appearance"
              ? "text-teal border-b-2 border-teal"
              : "text-neutral-medium hover:text-neutral-dark"
          }`}
          role="tab"
          aria-selected={activeTab === "appearance"}
          data-testid="tab-appearance"
        >
          🎨 Design
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
        ) : activeTab === "actions" ? (
          <ActionsTab
            matchScore={matchScore}
            expiryWarning={expiryWarning}
            onDownloadPdf={onDownloadPdf}
            onRegenerateSame={onRegenerateSame}
            onRegenerateWithTemplate={onRegenerateWithTemplate}
            onNext={onNext}
          />
        ) : (
          <DesignTab
            cvId={cvId}
            templateLabel={template?.label ?? null}
            detectedCompany={detectedCompany}
            currentAccentHex={currentAccentHex}
            onColorApplied={onHtmlRefresh}
            onChangeTemplate={onRegenerateDifferent}
          />
        )}
      </div>
    </div>
  );
}
