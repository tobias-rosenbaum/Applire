"use client";

import { useState } from "react";
import { CoverLetterContentTab } from "./CoverLetterContentTab";
import { CoverLetterDesignTab } from "./CoverLetterDesignTab";
import { CoverLetterActionsTab } from "./CoverLetterActionsTab";

type CLTemplate =
  | "classic_german"
  | "modern_swiss"
  | "executive"
  | "tech_developer"
  | "creative_sidebar"
  | "academic"
  | "compact_pro";

type TabId = "content" | "design" | "actions";

interface CoverLetterRefinementPanelProps {
  flowId: string;
  coverLetterId: string;
  letterData: Record<string, unknown> | null;
  currentTemplate: CLTemplate;
  onSectionSaved: () => void;
  onTemplateChange: (template: CLTemplate) => void;
  onRegenerateCoverLetter: () => void;
  onDownloadPdf: () => void;
  downloading: boolean;
}

const TABS: { id: TabId; label: string }[] = [
  { id: "content", label: "Inhalt" },
  { id: "design", label: "Design" },
  { id: "actions", label: "Aktionen" },
];

export function CoverLetterRefinementPanel({
  flowId,
  coverLetterId,
  letterData,
  currentTemplate,
  onSectionSaved,
  onTemplateChange,
  onRegenerateCoverLetter,
  onDownloadPdf,
  downloading,
}: CoverLetterRefinementPanelProps) {
  const [activeTab, setActiveTab] = useState<TabId>("content");

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Tab bar */}
      <div className="flex border-b border-neutral-200 flex-shrink-0">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-neutral-500 hover:text-neutral-700"
            }`}
            data-testid={`cl-tab-${tab.id}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === "content" && (
          <CoverLetterContentTab
            coverLetterId={coverLetterId}
            letterData={letterData as Parameters<typeof CoverLetterContentTab>[0]["letterData"]}
            onSectionSaved={onSectionSaved}
          />
        )}
        {activeTab === "design" && (
          <CoverLetterDesignTab
            flowId={flowId}
            currentTemplate={currentTemplate}
            onTemplateChange={onTemplateChange}
          />
        )}
        {activeTab === "actions" && (
          <CoverLetterActionsTab
            onRegenerateCoverLetter={onRegenerateCoverLetter}
            onDownloadPdf={onDownloadPdf}
            downloading={downloading}
          />
        )}
      </div>
    </div>
  );
}
