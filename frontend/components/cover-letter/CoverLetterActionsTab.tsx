"use client";

import { useTranslations } from "next-intl";

interface CoverLetterActionsTabProps {
  onRegenerateCoverLetter: () => void;
  onDownloadPdf: () => void;
  downloading: boolean;
}

export function CoverLetterActionsTab({
  onRegenerateCoverLetter,
  onDownloadPdf,
  downloading,
}: CoverLetterActionsTabProps) {
  const t = useTranslations("coverLetter");
  return (
    <div className="flex flex-col gap-3 p-3">
      <div className="flex flex-col gap-2">
        <button
          type="button"
          onClick={onDownloadPdf}
          disabled={downloading}
          className="w-full bg-blue-600 text-white text-sm font-medium py-2.5 rounded hover:bg-blue-700 transition-colors disabled:opacity-50"
          data-testid="cl-download-pdf-btn"
        >
          {downloading ? t("generating") : t("download")}
        </button>
      </div>

      <div className="border-t border-neutral-200 pt-3">
        <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wide mb-2">
          Neu generieren
        </p>
        <p className="text-xs text-neutral-400 mb-3">
          Öffnet das Eingabeformular mit den bisherigen Angaben. Das neue Anschreiben ersetzt das aktuelle.
        </p>
        <button
          type="button"
          onClick={onRegenerateCoverLetter}
          className="w-full border border-neutral-300 text-sm py-2.5 rounded hover:border-neutral-500 transition-colors"
          data-testid="cl-regenerate-btn"
        >
          ↻ {t("regenerate")}
        </button>
      </div>
    </div>
  );
}
