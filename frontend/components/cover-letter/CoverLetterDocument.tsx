"use client";

import { useEffect, useState } from "react";

interface CoverLetterDocumentProps {
  coverLetterId: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export function CoverLetterDocument({ coverLetterId }: CoverLetterDocumentProps) {
  const [srcDoc, setSrcDoc] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!coverLetterId) return;
    let cancelled = false;

    async function load() {
      try {
        const res = await fetch(`${API_BASE}/api/cover-letter/${coverLetterId}/html`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const html = await res.text();
        if (!cancelled) setSrcDoc(html);
      } catch (err: unknown) {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Preview nicht verfügbar");
      }
    }

    load();
    return () => { cancelled = true; };
  }, [coverLetterId]);

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-red-500">
        {error}
      </div>
    );
  }

  if (!srcDoc) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-neutral-400">
        Lade Vorschau…
      </div>
    );
  }

  return (
    <iframe
      srcDoc={srcDoc}
      className="w-full h-full border-0"
      title="Anschreiben Vorschau"
      data-testid="cover-letter-iframe"
      sandbox="allow-same-origin"
    />
  );
}
