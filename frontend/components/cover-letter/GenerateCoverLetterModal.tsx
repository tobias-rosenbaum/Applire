"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

type CLTone = "formal" | "professional" | "conversational";

interface GenerateCoverLetterModalProps {
  jobId: string;
  prefillRecipientName?: string | null;
  prefillRecipientCompany?: string | null;
  /** If provided, modal shows "Regenerate" header and pre-fills fields */
  existingInputs?: {
    recipient_name?: string | null;
    recipient_company?: string | null;
    salary?: string | null;
    availability?: string | null;
    motivation?: string | null;
    tone?: CLTone;
  } | null;
  onClose: () => void;
  onGenerated: (coverLetterId: string) => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

const TONE_OPTIONS: { value: CLTone; label: string; sub: string }[] = [
  { value: "formal", label: "Formal", sub: "Traditionelles Bewerbungsschreiben" },
  { value: "professional", label: "Professional", sub: "Warm but polished" },
  { value: "conversational", label: "Conversational", sub: "Modern, direkt" },
];

export function GenerateCoverLetterModal({
  jobId,
  prefillRecipientName,
  prefillRecipientCompany,
  existingInputs,
  onClose,
  onGenerated,
}: GenerateCoverLetterModalProps) {
  const t = useTranslations("coverLetter");
  const tc = useTranslations("common");
  const isRegenerate = existingInputs != null;
  const [recipientName, setRecipientName] = useState(
    existingInputs?.recipient_name ?? prefillRecipientName ?? ""
  );
  const [recipientCompany, setRecipientCompany] = useState(
    existingInputs?.recipient_company ?? prefillRecipientCompany ?? ""
  );
  const [salary, setSalary] = useState(existingInputs?.salary ?? "");
  const [availability, setAvailability] = useState(existingInputs?.availability ?? "");
  const [motivation, setMotivation] = useState(existingInputs?.motivation ?? "");
  const [tone, setTone] = useState<CLTone>(existingInputs?.tone ?? "formal");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/cover-letter/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: jobId,
          recipient_name: recipientName || null,
          recipient_company: recipientCompany || null,
          salary: salary || null,
          availability: availability || null,
          motivation: motivation || null,
          tone,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error((data as { detail?: string }).detail ?? "Generation failed");
      }
      const data = await res.json();
      onGenerated((data as { cover_letter_id: string }).cover_letter_id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      data-testid="cover-letter-modal"
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6 flex flex-col gap-4">
        <div>
          <h2 className="text-lg font-bold">
            {isRegenerate ? t("regenerate") : t("generate")}
          </h2>
          <p className="text-xs text-neutral-500 mt-1">
            Wir erstellen ein Bewerbungsschreiben passend zu Ihrem Lebenslauf.
          </p>
        </div>

        {/* Recipient */}
        <div>
          <label className="block text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-1">
            Empfänger{" "}
            <span className="font-normal text-neutral-400">(aus Stellenanzeige)</span>
          </label>
          <div className="flex gap-2">
            <input
              className="flex-1 border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Name"
              value={recipientName}
              onChange={(e) => setRecipientName(e.target.value)}
              data-testid="cl-recipient-name"
            />
            <input
              className="flex-1 border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Unternehmen"
              value={recipientCompany}
              onChange={(e) => setRecipientCompany(e.target.value)}
              data-testid="cl-recipient-company"
            />
          </div>
        </div>

        {/* Salary */}
        <div>
          <label className="block text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-1">
            Gehaltswunsch{" "}
            <span className="font-normal text-neutral-400">(optional)</span>
          </label>
          <input
            className="w-full border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="z.B. 95.000 – 110.000 € p.a."
            value={salary}
            onChange={(e) => setSalary(e.target.value)}
            data-testid="cl-salary"
          />
        </div>

        {/* Availability */}
        <div>
          <label className="block text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-1">
            Verfügbarkeit{" "}
            <span className="font-normal text-neutral-400">(optional)</span>
          </label>
          <input
            className="w-full border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="z.B. 3 Monate zum Monatsende"
            value={availability}
            onChange={(e) => setAvailability(e.target.value)}
            data-testid="cl-availability"
          />
        </div>

        {/* Motivation */}
        <div>
          <label className="block text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-1">
            Persönliche Motivation{" "}
            <span className="font-normal text-neutral-400">(optional)</span>
          </label>
          <textarea
            className="w-full border border-neutral-300 rounded px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
            placeholder="Warum interessiert Sie diese Stelle? Leer lassen = KI generiert aus Stellenanzeige."
            value={motivation}
            onChange={(e) => setMotivation(e.target.value)}
            data-testid="cl-motivation"
          />
        </div>

        {/* Tone */}
        <div>
          <label className="block text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-2">
            Tonalität
          </label>
          <div className="flex gap-2">
            {TONE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setTone(opt.value)}
                className={`flex-1 rounded border p-2 text-left transition-colors ${
                  tone === opt.value
                    ? "border-blue-500 bg-blue-50"
                    : "border-neutral-200 hover:border-neutral-400"
                }`}
                data-testid={`cl-tone-${opt.value}`}
              >
                <div className="text-xs font-semibold">{opt.label}</div>
                <div className="text-xs text-neutral-500">{opt.sub}</div>
              </button>
            ))}
          </div>
        </div>

        {error && (
          <p className="text-xs text-red-600 bg-red-50 rounded p-2">{error}</p>
        )}

        <div className="flex gap-2 pt-1">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="flex-1 border border-neutral-300 rounded py-2.5 text-sm hover:border-neutral-500 transition-colors disabled:opacity-50"
            data-testid="cl-modal-cancel"
          >
            {tc("cancel")}
          </button>
          <button
            type="button"
            onClick={handleGenerate}
            disabled={loading}
            className="flex-[2] bg-blue-600 text-white rounded py-2.5 text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
            data-testid="cl-modal-generate"
          >
            {loading ? t("generating") : `${t("generate")} →`}
          </button>
        </div>
      </div>
    </div>
  );
}
