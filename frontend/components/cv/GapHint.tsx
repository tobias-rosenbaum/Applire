// frontend/components/cv/GapHint.tsx
"use client";

interface GapHintItem {
  id: string;
  label: string;
}

interface GapHintProps {
  gap: GapHintItem;
  onDismiss: (gapId: string) => void;
}

export function GapHint({ gap, onDismiss }: GapHintProps) {
  return (
    <div className="flex items-center justify-between bg-warning-container border border-warning/30 rounded-lg px-3 py-2 mb-1">
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
        <div className="relative group">
          <button
            type="button"
            disabled
            className="text-xs text-gray-400 border border-gray-300 px-2 py-0.5 rounded cursor-not-allowed"
            data-testid="kaile-help-btn"
          >
            Kaile hilft
          </button>
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-gray-800 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity">
            Kommt in Sprint 10
          </div>
        </div>
      </div>
    </div>
  );
}
