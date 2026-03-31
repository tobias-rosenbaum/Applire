"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

interface WhatNextProps {
  flowId: string;
  roleTitle?: string | null;
}

export function WhatNext({ flowId, roleTitle }: WhatNextProps) {
  const router = useRouter();
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    // Advance flow to complete on mount (Task 20.5) — best-effort
    fetch(`${API_BASE}/api/flow/${flowId}/advance`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ step: "complete" }),
    }).catch(() => {});
  }, [flowId]);

  async function handleCopy() {
    const text = roleTitle
      ? `Mein Lebenslauf für die Stelle „${roleTitle}" wurde mit Apliqa optimiert. Präzise. Überzeugend. Zukunftsfähig.`
      : "Mein Lebenslauf wurde mit Apliqa optimiert. Präzise. Überzeugend. Zukunftsfähig.";
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard API may be unavailable
    }
  }

  return (
    <div className="max-w-md mx-auto text-center animate-slide-up">
      <div className="w-16 h-16 rounded-full bg-success flex items-center justify-center text-white text-2xl mx-auto mb-4">
        ✓
      </div>

      <h1 className="text-2xl font-heading font-bold text-neutral-dark mb-2">
        Dein Lebenslauf ist bereit!
      </h1>
      <p className="text-sm text-gray-500 mb-8">
        Präzise. Überzeugend. Zukunftsfähig.
      </p>

      <div className="flex flex-col gap-3">
        <button
          type="button"
          onClick={() => void handleCopy()}
          className="w-full bg-gold text-white font-semibold py-3 rounded-lg text-sm hover:opacity-90 transition-opacity"
          data-testid="apply-button"
        >
          {copied ? "Zusammenfassung kopiert ✓" : "Jetzt bewerben — Zusammenfassung kopieren"}
        </button>

        <button
          type="button"
          onClick={() => router.push("/")}
          className="w-full bg-teal text-white font-semibold py-3 rounded-lg text-sm hover:opacity-90 transition-colors"
        >
          Neue Bewerbung starten
        </button>

        <button
          type="button"
          onClick={() => router.push("/")}
          className="text-sm text-teal hover:underline"
        >
          Zurück zur Startseite
        </button>
      </div>
    </div>
  );
}
