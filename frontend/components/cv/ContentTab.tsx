// frontend/components/cv/ContentTab.tsx
"use client";

import { useCallback, useEffect, useState } from "react";
import { SectionEditor } from "./SectionEditor";
import { KaileChat } from "./KaileChat";

export interface GapHintItem {
  id: string;
  label: string;
}

export interface SectionItem {
  section_id: string;
  label: string;
  content: string;
  has_override: boolean;
  gaps: GapHintItem[];
}

interface FlowStateSummary {
  job_summary: string | null;
  gap_summary: {
    gaps: GapHintItem[];
    sections: SectionItem[];
  } | null;
  cv_summary: { sections: SectionItem[] } | null;
}

interface ContentTabProps {
  cvId: string;
  flowSummary: FlowStateSummary | null;
  onSectionSave: (updatedHtml: string) => void;
  onUnsavedChange: (hasUnsaved: boolean) => void;
}

export function ContentTab({ cvId, flowSummary, onSectionSave, onUnsavedChange }: ContentTabProps) {
  const [mode, setMode] = useState<"browse" | "edit">("browse");
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null);
  const [preSelectedGapIds, setPreSelectedGapIds] = useState<string[]>([]);
  const [hasUnsaved, setHasUnsaved] = useState(false);

  // Warn before page unload when in edit mode with unsaved changes
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (hasUnsaved && mode === "edit") {
        e.preventDefault();
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [hasUnsaved, mode]);

  const sections: SectionItem[] =
    flowSummary?.gap_summary?.sections ??
    flowSummary?.cv_summary?.sections ??
    [];

  const allGaps: GapHintItem[] = flowSummary?.gap_summary?.gaps ?? [];

  const handleBrowseToEdit = useCallback(
    (sectionId: string, preselectedGaps: string[] = []) => {
      if (hasUnsaved) {
        if (!confirm("You have unsaved changes. Are you sure you want to leave this section?")) {
          return;
        }
      }
      setActiveSectionId(sectionId);
      setPreSelectedGapIds(preselectedGaps);
      setMode("edit");
      setHasUnsaved(false);
    },
    [hasUnsaved],
  );

  const handleBackToBrowse = useCallback(() => {
    if (hasUnsaved) {
      if (!confirm("You have unsaved changes. Are you sure you want to leave this section?")) {
        return;
      }
    }
    setMode("browse");
    setActiveSectionId(null);
    setPreSelectedGapIds([]);
    setHasUnsaved(false);
  }, [hasUnsaved]);

  const handleAddressGap = useCallback(
    (gapId: string) => {
      const owner = sections.find((s) => s.gaps.some((g) => g.id === gapId));
      if (owner) {
        handleBrowseToEdit(owner.section_id, [gapId]);
      }
    },
    [sections, handleBrowseToEdit],
  );

  const handleSectionEdit = useCallback(
    (sectionId: string) => {
      handleBrowseToEdit(sectionId, []);
    },
    [handleBrowseToEdit],
  );

  const activeSection = sections.find((s) => s.section_id === activeSectionId) ?? null;

  if (mode === "edit" && activeSection) {
    return (
      <div className="flex flex-col gap-4 p-3">
        <button
          type="button"
          onClick={handleBackToBrowse}
          className="text-xs text-teal underline hover:opacity-80 self-start"
        >
          &larr; Zur&uuml;ck zur &Uuml;bersicht
        </button>

        <h3 className="text-sm font-medium text-neutral-dark">
          {activeSection.label}
        </h3>

        <SectionEditor
          cvId={cvId}
          section={activeSection}
          onSaved={(html) => {
            onSectionSave(html);
            setHasUnsaved(false);
          }}
          onUnsavedChange={(unsaved) => {
            setHasUnsaved(unsaved);
            onUnsavedChange(unsaved);
          }}
          onAddressGap={handleAddressGap}
        />

        <KaileChat
          cvId={cvId}
          sectionId={activeSection.section_id}
          gaps={activeSection.gaps}
          preSelectedGapIds={preSelectedGapIds}
          onApply={() => {
            // TODO (Task 11): wire suggestion into SectionEditor textarea via shared state
          }}
          onEditFirst={() => {
            // TODO (Task 11): wire suggestion into SectionEditor textarea and focus
          }}
          onCancel={() => {}}
        />
      </div>
    );
  }

  // Browse mode
  const pluralGaps = allGaps.length !== 1;

  return (
    <div className="flex flex-col gap-3 p-3">
      {allGaps.length > 0 && (
        <>
          <div className="flex items-center gap-2">
            <span className="text-lg">🤖</span>
            <p className="text-sm text-neutral-dark">
              {allGaps.length} {pluralGaps ? "Lücken" : "Lücke"} gefunden für &quot;{flowSummary?.job_summary ?? "Rolle"}&quot;
            </p>
          </div>
          <div className="flex flex-col gap-2">
            {allGaps.map((gap) => (
              <button
                key={gap.id}
                type="button"
                onClick={() => handleAddressGap(gap.id)}
                className="text-left text-sm border border-neutral-medium rounded-lg p-2.5 hover:border-teal transition-colors"
              >
                <span className="text-xs text-neutral-medium font-medium">{gap.label}</span>
              </button>
            ))}
          </div>
          <hr className="border-neutral-medium" />
        </>
      )}

      <h4 className="text-xs font-semibold text-neutral-dark uppercase tracking-wide">
        Abschnitte bearbeiten
      </h4>
      <div className="flex flex-col gap-1.5">
        {sections.map((section) => (
          <button
            key={section.section_id}
            type="button"
            onClick={() => handleSectionEdit(section.section_id)}
            className="text-left text-sm flex items-center justify-between border border-transparent rounded-lg px-3 py-2 hover:border-neutral-medium transition-colors"
          >
            <span className="text-neutral-darker">{section.label}</span>
            {section.gaps.length > 0 ? (
              <span className="text-xs bg-warning-container text-warning px-1.5 py-0.5 rounded-full">
                {section.gaps.length}
              </span>
            ) : (
              <span className="text-xs text-success">✓</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
