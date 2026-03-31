"use client";

import { ScoreCircle } from "@/components/ui/score-circle";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

const TEMPLATE_LABELS: Record<string, string> = {
  classic_german: "Klassischer Lebenslauf",
  modern_swiss: "Modern Swiss CV",
};

interface CVSummary {
  cv_id: string;
  expires_at: string;
}

interface GapSummary {
  match_score: number;
}

interface JobSummary {
  role_title: string;
}

interface CVPreviewProps {
  cvId: string;
  template: "classic_german" | "modern_swiss";
  jobSummary: JobSummary | null;
  gapSummary: GapSummary | null;
  cvSummary: CVSummary | null;
  onRegenerateDifferent: () => void;
  onRegenerateSame: () => void;
  onNext: () => void;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("de-DE", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

export function CVPreview({
  cvId,
  template,
  jobSummary,
  gapSummary,
  cvSummary,
  onRegenerateDifferent,
  onRegenerateSame,
  onNext,
}: CVPreviewProps) {
  const isExpired = cvSummary
    ? new Date(cvSummary.expires_at) < new Date()
    : false;

  async function handleDownload() {
    try {
      const res = await fetch(`${API_BASE}/api/cv/${cvId}/pdf`);
      if (!res.ok) return;
      const blob = await res.blob();
      const disposition = res.headers.get("Content-Disposition") ?? "";
      const match = disposition.match(/filename="([^"]+)"/);
      const filename = match?.[1] ?? `lebenslauf-${cvId.slice(0, 8)}.pdf`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // silently fail
    }
  }

  return (
    <div className="flex gap-6 h-[75vh] animate-fade-in">
      {/* Left metadata panel (40%) */}
      <div className="w-2/5 flex flex-col gap-4 bg-neutral-light rounded-xl p-5 overflow-y-auto shrink-0">
        {jobSummary && (
          <h2 className="text-lg font-heading font-bold text-neutral-dark leading-snug">
            {jobSummary.role_title}
          </h2>
        )}

        <span className="inline-block bg-teal text-white text-xs font-semibold px-3 py-1 rounded-full w-fit">
          {TEMPLATE_LABELS[template] ?? template}
        </span>

        {gapSummary && (
          <div className="flex justify-center py-2">
            <ScoreCircle score={Math.round(gapSummary.match_score * 100)} size={90} />
          </div>
        )}

        {cvSummary && !isExpired && (
          <div className="border-l-4 border-warning bg-warning-container rounded-r-lg p-3 text-xs text-neutral-dark">
            Verfügbar bis {formatDate(cvSummary.expires_at)}
          </div>
        )}
        {isExpired && (
          <div className="border-l-4 border-critical bg-critical-container rounded-r-lg p-3 text-xs text-neutral-dark">
            Abgelaufen. Bitte neu generieren.
          </div>
        )}

        <div className="flex flex-col gap-2 mt-auto">
          <button
            type="button"
            onClick={() => void handleDownload()}
            data-testid="download-button"
            className="w-full bg-success text-white font-semibold py-3 rounded-lg text-sm hover:opacity-90 transition-opacity"
          >
            PDF herunterladen
          </button>
          <button
            type="button"
            onClick={onRegenerateSame}
            className="w-full border border-teal text-teal font-semibold py-2.5 rounded-lg text-sm hover:opacity-90 transition-opacity"
          >
            Neu generieren
          </button>
          <button
            type="button"
            onClick={onRegenerateDifferent}
            className="w-full border border-teal text-teal font-semibold py-2.5 rounded-lg text-sm hover:opacity-90 transition-opacity"
          >
            Andere Vorlage
          </button>
          <button
            type="button"
            onClick={onNext}
            className="w-full bg-teal text-white font-semibold py-3 rounded-lg text-sm hover:opacity-90 transition-colors"
          >
            Was nun? →
          </button>
        </div>
      </div>

      {/* Right iframe panel (60%) */}
      <div className="flex-1 bg-white rounded-xl shadow-soft overflow-hidden">
        <iframe
          src={`${API_BASE}/api/cv/${cvId}/html`}
          title="Lebenslauf Vorschau"
          className="w-full h-full border-0"
          data-testid="cv-iframe"
        />
      </div>
    </div>
  );
}
