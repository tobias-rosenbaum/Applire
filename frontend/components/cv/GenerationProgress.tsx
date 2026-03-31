"use client";

import { useEffect, useRef, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";
const POLL_INTERVAL_MS = 3000;
const STALENESS_MS = 60_000;

type CVStatus = "pending" | "generating" | "ready" | "failed" | "expired";

interface CVStatusResponse {
  cv_id: string;
  status: CVStatus;
  error_message: string | null;
  expires_at: string;
}

interface GenerationProgressProps {
  cvId: string;
  flowId: string;
  onReady: (cvId: string) => void;
  onRetry: () => void;
}

const STEPS = [
  { key: "queued", label: "In der Warteschlange…" },
  { key: "generating", label: "Lebenslauf wird gerendert…" },
  { key: "ready", label: "Fertig!" },
];

function activeStepIndex(status: CVStatus): number {
  if (status === "pending") return 0;
  if (status === "generating") return 1;
  if (status === "ready") return 2;
  return 0;
}

export function GenerationProgress({ cvId, flowId, onReady, onRetry }: GenerationProgressProps) {
  const [status, setStatus] = useState<CVStatus>("pending");
  const [error, setError] = useState<string | null>(null);
  const [stale, setStale] = useState(false);
  const startedAt = useRef(Date.now());
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    async function poll() {
      if (Date.now() - startedAt.current > STALENESS_MS) {
        setStale(true);
        if (intervalRef.current) clearInterval(intervalRef.current);
        return;
      }

      try {
        const res = await fetch(`${API_BASE}/api/cv/${cvId}/status`);
        if (!res.ok) return;
        const data: CVStatusResponse = await res.json();
        setStatus(data.status);

        if (data.status === "ready") {
          if (intervalRef.current) clearInterval(intervalRef.current);
          try {
            await fetch(`${API_BASE}/api/flow/${flowId}/advance`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ step: "cv_generation", artifact_id: cvId }),
            });
          } catch {
            // non-fatal
          }
          onReady(cvId);
        } else if (data.status === "failed") {
          if (intervalRef.current) clearInterval(intervalRef.current);
          setError(data.error_message ?? "Generierung fehlgeschlagen.");
        }
      } catch {
        // Continue polling on network errors
      }
    }

    void poll();
    intervalRef.current = setInterval(() => void poll(), POLL_INTERVAL_MS);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [cvId, flowId, onReady]);

  const activeIndex = activeStepIndex(status);

  return (
    <div className="max-w-md mx-auto animate-fade-in">
      <h1 className="text-2xl font-heading font-bold text-neutral-dark mb-1">
        Lebenslauf wird erstellt
      </h1>
      <p className="text-sm text-gray-500 mb-8">Das dauert normalerweise 20–40 Sekunden.</p>

      <div className="bg-white rounded-xl shadow-soft p-6 space-y-5 mb-6">
        {STEPS.map((step, i) => {
          const isDone = i < activeIndex;
          const isActive = i === activeIndex && status !== "failed";
          return (
            <div key={step.key} className="flex items-center gap-3">
              {isDone ? (
                <span className="w-6 h-6 rounded-full bg-success flex items-center justify-center text-white text-xs font-bold shrink-0">
                  ✓
                </span>
              ) : isActive ? (
                <span className="w-6 h-6 rounded-full border-2 border-teal flex items-center justify-center shrink-0">
                  <span
                    className="w-2.5 h-2.5 rounded-full bg-teal animate-spin"
                  />
                </span>
              ) : (
                <span className="w-6 h-6 rounded-full border-2 border-gray-200 shrink-0" />
              )}
              <span
                className={[
                  "text-sm",
                  isDone
                    ? "text-gray-400 line-through"
                    : isActive
                    ? "text-neutral-dark font-semibold"
                    : "text-gray-300",
                ].join(" ")}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {stale && !error && (
        <div className="border-l-4 border-warning bg-warning-container rounded-r-lg p-3 text-sm text-neutral-dark">
          Dauert länger als erwartet — du kannst später zurückkommen.
        </div>
      )}

      {error && (
        <div className="border-l-4 border-critical bg-critical-container rounded-r-lg p-4">
          <p className="text-sm text-neutral-dark mb-2">{error}</p>
          <button
            type="button"
            onClick={onRetry}
            className="text-sm font-semibold text-critical hover:underline"
          >
            Erneut versuchen →
          </button>
        </div>
      )}
    </div>
  );
}
