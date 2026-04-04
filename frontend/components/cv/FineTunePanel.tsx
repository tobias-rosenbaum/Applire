// frontend/components/cv/FineTunePanel.tsx
"use client";

import { useState, useEffect } from "react";
import { SectionEditor } from "./SectionEditor";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

interface GapHintItem {
  id: string;
  label: string;
}

interface SectionItem {
  section_id: string;
  label: string;
  content: string;
  has_override: boolean;
  gaps: GapHintItem[];
}

interface CVSectionsResponse {
  sections: SectionItem[];
  general_gaps: GapHintItem[];
}

interface FineTunePanelProps {
  cvId: string;
  initialHtml: string | null;
  onClose: () => void;
}

export function FineTunePanel({ cvId, initialHtml, onClose }: FineTunePanelProps) {
  const [sections, setSections] = useState<SectionItem[]>([]);
  const [generalGaps, setGeneralGaps] = useState<GapHintItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [activeSection, setActiveSection] = useState<SectionItem | null>(null);
  const [htmlContent, setHtmlContent] = useState<string | null>(initialHtml);
  const [pendingSection, setPendingSection] = useState<SectionItem | null>(null);
  const [showDiscardDialog, setShowDiscardDialog] = useState(false);
  const [hasUnsaved, setHasUnsaved] = useState(false);

  useEffect(() => {
    void loadSections();
  }, [cvId]);

  async function loadSections() {
    setLoading(true);
    setError(false);
    try {
      const res = await fetch(`${API_BASE}/api/cv/${cvId}/sections`);
      if (!res.ok) throw new Error("Failed");
      const data: CVSectionsResponse = await res.json();
      setSections(data.sections);
      setGeneralGaps(data.general_gaps);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  function requestSectionSwitch(section: SectionItem) {
    if (hasUnsaved) {
      setPendingSection(section);
      setShowDiscardDialog(true);
    } else {
      setActiveSection(section);
    }
  }

  function handleDiscard() {
    setShowDiscardDialog(false);
    setHasUnsaved(false);
    if (pendingSection === null) {
      // User was trying to close the panel
      onClose();
    } else {
      setActiveSection(pendingSection);
      setPendingSection(null);
    }
  }

  function handleKeepEditing() {
    setShowDiscardDialog(false);
    setPendingSection(null);
  }

  function handleSaved(updatedHtml: string, savedContent: string) {
    setHtmlContent(updatedHtml);
    setHasUnsaved(false);
    setSections((prev) =>
      prev.map((s) =>
        s.section_id === activeSection?.section_id
          ? { ...s, content: savedContent, has_override: true }
          : s
      )
    );
  }

  function handleCloseRequest() {
    if (hasUnsaved) {
      setPendingSection(null);
      setShowDiscardDialog(true);
    } else {
      onClose();
    }
  }

  const allGapsClosed =
    sections.length > 0 && sections.every((s) => s.gaps.length === 0);

  return (
    <div className="flex-1 flex flex-row gap-4 h-[75vh]">
      {/* Unsaved changes dialog */}
      {showDiscardDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl p-6 shadow-xl max-w-sm w-full mx-4">
            <p className="text-sm font-semibold text-neutral-dark mb-4">
              Ungespeicherte Änderungen verwerfen?
            </p>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleDiscard}
                className="flex-1 bg-critical text-white font-semibold py-2 rounded-lg text-sm hover:opacity-90"
                data-testid="discard-confirm"
              >
                Verwerfen
              </button>
              <button
                type="button"
                onClick={handleKeepEditing}
                className="flex-1 border border-teal text-teal font-semibold py-2 rounded-lg text-sm hover:opacity-90"
                data-testid="keep-editing"
              >
                Weiter bearbeiten
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Left: editor panel (42%) */}
      <div className="w-[42%] flex flex-col bg-neutral-light rounded-xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
          <span className="text-sm font-bold text-neutral-dark">
            {allGapsClosed ? (
              <span className="text-success" data-testid="all-gaps-closed">
                ✓ Alle Lücken geschlossen
              </span>
            ) : (
              "Abschnitte bearbeiten"
            )}
          </span>
          <button
            type="button"
            onClick={handleCloseRequest}
            className="text-xs text-gray-500 hover:text-gray-700"
          >
            Schließen ✕
          </button>
        </div>

        {/* Section list */}
        <div className="overflow-y-auto flex-1 p-2">
          {loading && (
            <div className="space-y-2 p-2">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-12 rounded-lg bg-gray-200 animate-pulse"
                  data-testid="section-skeleton"
                />
              ))}
            </div>
          )}

          {error && !loading && (
            <div className="p-4 text-center">
              <p className="text-sm text-gray-500 mb-2">
                Abschnitte konnten nicht geladen werden.
              </p>
              <button
                type="button"
                onClick={() => void loadSections()}
                className="text-sm text-teal underline hover:opacity-80"
              >
                Erneut versuchen
              </button>
            </div>
          )}

          {!loading &&
            !error &&
            sections.map((section) => (
              <button
                key={section.section_id}
                type="button"
                onClick={() => requestSectionSwitch(section)}
                data-testid="section-list-item"
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg mb-1 text-left transition-colors ${
                  activeSection?.section_id === section.section_id
                    ? "bg-teal text-white"
                    : "hover:bg-gray-100 text-neutral-dark"
                }`}
              >
                <span className="text-sm font-medium truncate">{section.label}</span>
                <span className="ml-2 shrink-0">
                  {section.gaps.length > 0 ? (
                    <span
                      data-testid="gap-badge"
                      className="bg-warning text-white text-xs font-bold px-1.5 py-0.5 rounded-full"
                    >
                      {section.gaps.length}
                    </span>
                  ) : (
                    <span className="text-success text-xs">✓</span>
                  )}
                </span>
              </button>
            ))}
        </div>

        {/* Section editor */}
        {activeSection && !loading && (
          <div className="border-t border-gray-200">
            <SectionEditor
              cvId={cvId}
              section={activeSection}
              onSaved={handleSaved}
              onUnsavedChange={setHasUnsaved}
            />
          </div>
        )}
      </div>

      {/* Right: CV preview iframe (58%) */}
      <div className="flex-1 bg-white rounded-xl shadow-soft overflow-hidden relative">
        {htmlContent ? (
          <iframe
            srcDoc={htmlContent}
            sandbox="allow-same-origin"
            title="Lebenslauf Vorschau"
            className="w-full h-full border-0"
            data-testid="finetune-preview-iframe"
          />
        ) : (
          <div className="w-full h-full animate-pulse bg-gray-100 rounded" />
        )}
      </div>
    </div>
  );
}
