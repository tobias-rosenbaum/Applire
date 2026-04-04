// frontend/components/cv/GapHint.tsx
"use client";

import { useState } from "react";
import { AssistMicroSession } from "./AssistMicroSession";

interface GapHintItem {
  id: string;
  label: string;
}

interface GapHintProps {
  gap: GapHintItem;
  cvId: string;
  sectionId: string;
  onDismiss: (gapId: string) => void;
  onAcceptSuggestion: (suggestion: string, focus: boolean) => void;
}

export function GapHint({ gap, cvId, sectionId, onDismiss, onAcceptSuggestion }: GapHintProps) {
  const [showAssist, setShowAssist] = useState(false);

  return (
    <div className="mb-2">
      <div className="flex items-center justify-between bg-warning-container border border-warning/30 rounded-lg px-3 py-2">
        <span className="text-xs text-neutral-dark font-medium">{gap.label}</span>
        <div className="flex gap-1 ml-2 shrink-0">
          <button
            type="button"
            onClick={() => onDismiss(gap.id)}
            className="text-xs text-teal border border-teal px-2 py-0.5 rounded hover:bg-teal hover:text-white transition-colors"
            data-testid="write-myself-btn"
          >
            Selbst schreiben
          </button>
          <button
            type="button"
            onClick={() => setShowAssist((v) => !v)}
            className="text-xs text-teal border border-teal px-2 py-0.5 rounded hover:bg-teal hover:text-white transition-colors"
            data-testid="kaile-help-btn"
          >
            Kaile hilft
          </button>
        </div>
      </div>

      {showAssist && (
        <AssistMicroSession
          cvId={cvId}
          sectionId={sectionId}
          gap={gap}
          onAccept={(suggestion) => {
            onAcceptSuggestion(suggestion, false);
            setShowAssist(false);
          }}
          onEdit={(suggestion) => {
            onAcceptSuggestion(suggestion, true);
            setShowAssist(false);
          }}
          onReject={() => setShowAssist(false)}
        />
      )}
    </div>
  );
}
