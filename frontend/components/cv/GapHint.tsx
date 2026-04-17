// frontend/components/cv/GapHint.tsx
"use client";

import { useTranslations } from "next-intl";

interface GapHintItem {
  id: string;
  label: string;
}

interface GapHintProps {
  gap: GapHintItem;
  onDismiss: (gapId: string) => void;
  onAddressGap: (gapId: string) => void;
}

export function GapHint({ gap, onDismiss, onAddressGap }: GapHintProps) {
  const t = useTranslations("cv");

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
            {t("writeMyself")}
          </button>
          <button
            type="button"
            onClick={() => onAddressGap(gap.id)}
            className="text-xs text-teal border border-teal px-2 py-0.5 rounded hover:bg-teal hover:text-white transition-colors"
            data-testid="kaile-help-btn"
          >
            {t("letKaileHelp")}
          </button>
        </div>
      </div>
    </div>
  );
}
