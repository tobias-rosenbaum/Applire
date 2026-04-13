"use client";

interface ActionsTabProps {
  matchScore: number | null;
  expiryWarning: { level: "none" | "warning" | "critical"; expiresIn: string } | null;
  onDownloadPdf: () => void;
  onRegenerateSame: () => void;
  onNext: () => void;
}

export function ActionsTab({
  matchScore,
  expiryWarning,
  onDownloadPdf,
  onRegenerateSame,
  onNext,
}: ActionsTabProps) {
  return (
    <div className="flex flex-col gap-4 p-3">
      {matchScore !== null && (
        <div className="flex flex-col items-center gap-2">
          <div className="relative w-20 h-20">
            <svg className="w-full h-full" viewBox="0 0 36 36">
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="3"
              />
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#0d9488"
                strokeWidth="3"
                strokeDasharray={`${matchScore * 100}, 100`}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-lg font-bold text-neutral-dark">
                {Math.round(matchScore * 100)}%
              </span>
            </div>
          </div>
          <span className="text-xs text-neutral-medium">Matching-Score</span>
        </div>
      )}

      {expiryWarning && expiryWarning.level !== "none" && (
        <div
          className={`text-xs px-3 py-2 rounded border ${
            expiryWarning.level === "critical"
              ? "bg-error-light border-error text-error"
              : "bg-warning-container border-warning/30 text-warning"
          }`}
        >
          {expiryWarning.level === "critical" ? (
            <>CV läuft ab: <span>{expiryWarning.expiresIn}</span></>
          ) : (
            <>CV läuft bald ab: <span>{expiryWarning.expiresIn}</span></>
          )}
        </div>
      )}

      <div className="flex flex-col gap-2">
        <button
          type="button"
          onClick={onDownloadPdf}
          className="w-full bg-teal text-white text-sm font-medium py-2.5 rounded hover:opacity-90 transition-opacity"
          data-testid="download-pdf-btn"
        >
          PDF herunterladen
        </button>
        <button
          type="button"
          onClick={onRegenerateSame}
          className="w-full border border-neutral-medium text-sm py-2.5 rounded hover:border-teal transition-colors"
          data-testid="regenerate-same-btn"
        >
          Erneut generieren
        </button>
      </div>

      <button
        type="button"
        onClick={onNext}
        className="w-full bg-primary text-white text-sm font-medium py-2.5 rounded hover:bg-primary/90 transition-colors"
        data-testid="next-step-btn"
      >
        Was nun?
      </button>
    </div>
  );
}
