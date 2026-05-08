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

// frontend/components/cv/RefinementPanel.tsx
"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { ContentTab } from "./ContentTab";
import { ActionsTab } from "./ActionsTab";
import { DesignTab } from "./DesignTab";

type Tab = "content" | "actions" | "appearance";

interface RefinementPanelProps {
  cvId: string;
  flowId: string;
  jobSummary: string | null;
  gapSummary: { gaps: Array<{ id: string; label: string }>; sections: Array<{ section_id: string; label: string; content: string; has_override: boolean; gaps: Array<{ id: string; label: string }> }> } | null;
  cvSummary: { sections: Array<{ section_id: string; label: string; content: string; has_override: boolean; gaps: Array<{ id: string; label: string }> }> } | null;
  template: { label: string | null } | null;
  matchScore: number | null;
  expiryWarning: { level: "none" | "warning" | "critical"; expiresIn: string } | null;
  coverLetterId: string | null;
  detectedCompany: { name: string; hex: string } | null;
  currentAccentHex: string;
  onHtmlRefresh: () => void;
  onRegenerateSame: () => void;
  onRegenerateDifferent: () => void;
  onRegenerateWithTemplate: (template: string) => void;
  onNext: () => void;
  onDownloadPdf: () => void;
  onGenerateCoverLetter: () => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export function RefinementPanel({
  cvId,
  flowId,
  jobSummary,
  gapSummary,
  cvSummary,
  template,
  matchScore,
  expiryWarning,
  coverLetterId,
  detectedCompany,
  currentAccentHex,
  onHtmlRefresh,
  onRegenerateSame,
  onRegenerateDifferent,
  onRegenerateWithTemplate,
  onNext,
  onDownloadPdf,
  onGenerateCoverLetter,
  collapsed,
  onToggleCollapse,
}: RefinementPanelProps) {
  const t = useTranslations("cv");
  const [activeTab, setActiveTab] = useState<Tab>("content");

  const TABS: { id: Tab; label: string; icon: string }[] = [
    { id: "content", label: t("contentTab"), icon: "📝" },
    { id: "actions", label: t("actionsTab"), icon: "⚙️" },
    { id: "appearance", label: t("designTab"), icon: "🎨" },
  ];

  const flowSummary = {
    job_summary: jobSummary,
    gap_summary: gapSummary,
    cv_summary: cvSummary,
  };

  if (collapsed) {
    return (
      <div
        className="w-12 flex flex-col items-center h-[calc(100vh-56px)] bg-white border-l border-neutral-medium py-2 gap-2 flex-shrink-0 transition-[width] duration-200 ease-in-out overflow-hidden"
        data-testid="refinement-panel"
      >
        <button
          type="button"
          onClick={onToggleCollapse}
          className="w-8 h-8 flex items-center justify-center rounded hover:bg-neutral-100 text-neutral-500 text-sm"
          title="Panel öffnen"
          data-testid="cv-panel-expand-btn"
        >
          ❮
        </button>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => {
              setActiveTab(tab.id);
              onToggleCollapse();
            }}
            className={`w-8 h-8 flex items-center justify-center rounded text-base ${
              activeTab === tab.id
                ? "bg-blue-50 text-blue-600"
                : "hover:bg-neutral-100"
            }`}
            title={tab.label}
            data-testid={`cv-tab-icon-${tab.id}`}
          >
            {tab.icon}
          </button>
        ))}
      </div>
    );
  }

  return (
    <div
      className="w-[380px] h-[calc(100vh-56px)] overflow-y-auto border-l border-neutral-medium bg-white flex flex-col flex-shrink-0 transition-[width] duration-200 ease-in-out"
      data-testid="refinement-panel"
    >
      {/* Tab strip */}
      <div className="flex items-center border-b border-neutral-medium shrink-0">
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
          &#x1f4dd; {t("contentTab")}
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
          &#x2699;&#xfe0f; {t("actionsTab")}
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
          🎨 {t("designTab")}
        </button>
        <button
          type="button"
          onClick={onToggleCollapse}
          className="px-2 py-2.5 text-neutral-400 hover:text-neutral-600 text-sm shrink-0"
          title="Panel einklappen"
          data-testid="cv-panel-collapse-btn"
        >
          ❯
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
            flowId={flowId}
            matchScore={matchScore}
            expiryWarning={expiryWarning}
            coverLetterId={coverLetterId}
            onDownloadPdf={onDownloadPdf}
            onRegenerateSame={onRegenerateSame}
            onRegenerateWithTemplate={onRegenerateWithTemplate}
            onNext={onNext}
            onGenerateCoverLetter={onGenerateCoverLetter}
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
