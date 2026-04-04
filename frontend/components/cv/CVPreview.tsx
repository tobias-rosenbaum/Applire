"use client";

import { useState, useEffect, useRef } from "react";
import { ScoreCircle } from "@/components/ui/score-circle";
import { FineTunePanel } from "./FineTunePanel";

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
  const [htmlContent, setHtmlContent] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState(false);
  const [fineTuneOpen, setFineTuneOpen] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [isZoomed, setIsZoomed] = useState(false);
  const previewRef = useRef<HTMLDivElement>(null);
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const el = previewRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      setContainerSize({
        width: entry.contentRect.width,
        height: entry.contentRect.height,
      });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // CV templates use width: 210mm ≈ 794px at 96 dpi
  const CV_WIDTH = 794;
  const scale =
    containerSize.width > 0 ? Math.min(1, containerSize.width / CV_WIDTH) : 1;
  const needsScaling = scale < 1;

  useEffect(() => {
    let cancelled = false;
    setHtmlContent(null);
    setPreviewError(false);

    fetch(`${API_BASE}/api/cv/${cvId}/html`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load preview");
        return res.text();
      })
      .then((html) => {
        if (!cancelled) setHtmlContent(html);
      })
      .catch(() => {
        if (!cancelled) setPreviewError(true);
      });

    return () => {
      cancelled = true;
    };
  }, [cvId, retryCount]);

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
    <div className="flex flex-col md:flex-row gap-4 md:gap-6 animate-fade-in">
      {/* Left metadata panel — 256px fixed on desktop, full-width on mobile */}
      <div className="w-full md:w-64 md:h-[75vh] flex flex-col gap-4 bg-neutral-light rounded-xl p-5 overflow-y-auto shrink-0">
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
            onClick={() => setFineTuneOpen((o) => !o)}
            data-testid="finetune-toggle"
            className={`w-full font-semibold py-2.5 rounded-lg text-sm transition-opacity hover:opacity-90 ${
              fineTuneOpen
                ? "bg-teal text-white"
                : "border border-teal text-teal"
            }`}
          >
            {fineTuneOpen ? "Fine-tune schließen" : "Fine-tune"}
          </button>
          {!fineTuneOpen && (
            <>
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
            </>
          )}
        </div>
      </div>

      {fineTuneOpen ? (
        <FineTunePanel
          cvId={cvId}
          initialHtml={htmlContent}
          onClose={() => setFineTuneOpen(false)}
        />
      ) : (
        /*
         * Right preview panel.
         * The iframe uses sandbox="allow-same-origin" so injected CV HTML can resolve
         * relative resources. Scripts are intentionally blocked (no allow-scripts).
         * Do NOT add allow-scripts without a security review — allow-same-origin +
         * allow-scripts would expose the parent DOM to the injected content.
         *
         * On narrow screens the CV (794px wide) is scaled down to fit via CSS transform.
         * The zoom toggle lets users switch to full-size 1:1 view with scroll.
         */
        <div
          ref={previewRef}
          className="flex-1 h-[60vh] md:h-[75vh] bg-white rounded-xl shadow-soft overflow-hidden relative"
        >
          {/* Zoom toggle — only shown on narrow screens where scaling is active */}
          {needsScaling && htmlContent && !previewError && (
            <button
              type="button"
              onClick={() => setIsZoomed((z) => !z)}
              className="absolute top-2 right-2 z-10 bg-white/80 backdrop-blur-sm border border-gray-200 text-xs text-gray-600 px-2 py-1 rounded shadow-sm hover:bg-white transition-colors"
            >
              {isZoomed ? "Einpassen" : "Vergrößern"}
            </button>
          )}

          {previewError ? (
            <div className="flex flex-col items-center justify-center h-full gap-3">
              <p className="text-sm text-gray-500">
                Vorschau konnte nicht geladen werden.
              </p>
              <button
                type="button"
                onClick={() => {
                  setPreviewError(false);
                  setRetryCount((c) => c + 1);
                }}
                className="text-sm text-teal underline hover:opacity-80"
              >
                Erneut versuchen
              </button>
            </div>
          ) : htmlContent ? (
            needsScaling && !isZoomed ? (
              // Fit-to-width: scale the 794px CV down to the container width
              <iframe
                srcDoc={htmlContent}
                sandbox="allow-same-origin"
                title="Lebenslauf Vorschau"
                style={{
                  width: CV_WIDTH,
                  height: containerSize.height / scale,
                  transform: `scale(${scale})`,
                  transformOrigin: "top left",
                  border: "none",
                  display: "block",
                }}
                data-testid="cv-iframe"
              />
            ) : (
              // Full-size: 1:1 view, scroll to navigate (zoomed on mobile, normal on desktop)
              <div className={`h-full ${needsScaling ? "overflow-auto" : ""}`}>
                <iframe
                  srcDoc={htmlContent}
                  sandbox="allow-same-origin"
                  title="Lebenslauf Vorschau"
                  style={
                    needsScaling
                      ? { width: CV_WIDTH, minHeight: "100%", border: "none", display: "block" }
                      : {}
                  }
                  className={needsScaling ? "" : "w-full h-full border-0"}
                  data-testid="cv-iframe"
                />
              </div>
            )
          ) : (
            <div className="w-full h-full animate-pulse bg-gray-100 rounded" />
          )}
        </div>
      )}
    </div>
  );
}
