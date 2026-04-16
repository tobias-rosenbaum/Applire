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
  collapsed: boolean;
  onToggleCollapse: () => void;
}

const TABS: { id: TabId; label: string; icon: string }[] = [
  { id: "content", label: "Inhalt", icon: "✏️" },
  { id: "design", label: "Design", icon: "🎨" },
  { id: "actions", label: "Aktionen", icon: "⚡" },
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
  collapsed,
  onToggleCollapse,
}: CoverLetterRefinementPanelProps) {
  const [activeTab, setActiveTab] = useState<TabId>("content");

  if (collapsed) {
    return (
      <div className="w-12 flex flex-col items-center bg-white border-l border-neutral-200 py-2 gap-2 flex-shrink-0 transition-[width] duration-200 ease-in-out overflow-hidden">
        <button
          type="button"
          onClick={onToggleCollapse}
          className="w-8 h-8 flex items-center justify-center rounded hover:bg-neutral-100 text-neutral-500 text-sm"
          title="Panel öffnen"
          data-testid="cl-panel-expand-btn"
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
            data-testid={`cl-tab-icon-${tab.id}`}
          >
            {tab.icon}
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="w-[380px] flex flex-col h-full bg-white border-l border-neutral-200 flex-shrink-0 transition-[width] duration-200 ease-in-out">
      {/* Tab bar */}
      <div className="flex items-center border-b border-neutral-200 flex-shrink-0">
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
        <button
          type="button"
          onClick={onToggleCollapse}
          className="ml-auto px-2 py-3 text-neutral-400 hover:text-neutral-600 text-sm"
          title="Panel einklappen"
          data-testid="cl-panel-collapse-btn"
        >
          ❯
        </button>
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
