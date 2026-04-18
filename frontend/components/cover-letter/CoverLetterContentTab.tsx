"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

interface LetterData {
  header?: { name?: string; address?: string; phone?: string; email?: string };
  recipient?: { name?: string; company?: string };
  body?: { paragraphs?: string[] };
  signature?: { closing?: string; name?: string };
}

interface CoverLetterContentTabProps {
  coverLetterId: string;
  letterData: LetterData | null;
  onSectionSaved: () => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export function CoverLetterContentTab({
  coverLetterId,
  letterData,
  onSectionSaved,
}: CoverLetterContentTabProps) {
  const tc = useTranslations("common");
  const [bodyText, setBodyText] = useState(
    letterData?.body?.paragraphs?.join("\n\n") ?? ""
  );
  const [bodyEditing, setBodyEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  async function handleSaveBody() {
    setSaving(true);
    setSaveError(null);
    try {
      const res = await fetch(`${API_BASE}/api/cover-letter/${coverLetterId}/section`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ section: "body", content: bodyText }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setBodyEditing(false);
      onSectionSaved();
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : "Fehler beim Speichern");
    } finally {
      setSaving(false);
    }
  }

  const header = letterData?.header;
  const recipient = letterData?.recipient;
  const signature = letterData?.signature;

  return (
    <div className="flex flex-col gap-3 p-3">
      <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wide">
        Abschnitte
      </p>

      {/* Header — read-only */}
      <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-semibold">Kopfzeile</span>
          <span className="text-xs text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
            auto
          </span>
        </div>
        <p className="text-xs text-neutral-500">
          {header?.name ?? "Aus Profil"}{header?.email ? ` · ${header.email}` : ""}
        </p>
      </div>

      {/* Recipient — read-only */}
      <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-semibold">Empfänger</span>
          <span className="text-xs text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
            auto
          </span>
        </div>
        <p className="text-xs text-neutral-500">
          {recipient?.name ?? "–"}{recipient?.company ? ` · ${recipient.company}` : ""}
        </p>
      </div>

      {/* Body — editable */}
      <div
        className={`border rounded-lg p-3 transition-colors ${
          bodyEditing
            ? "border-blue-400 bg-blue-50"
            : "border-neutral-200 bg-neutral-50"
        }`}
      >
        <div className="flex items-center justify-between mb-2">
          <span className={`text-sm font-semibold ${bodyEditing ? "text-blue-700" : ""}`}>
            Anschreiben-Text
          </span>
          <span className="text-xs text-blue-600 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded-full">
            bearbeitbar
          </span>
        </div>
        <textarea
          className="w-full border border-blue-200 rounded p-2 text-xs text-neutral-700 resize-none bg-white focus:outline-none focus:ring-2 focus:ring-blue-400"
          rows={8}
          value={bodyText}
          onChange={(e) => {
            setBodyText(e.target.value);
            setBodyEditing(true);
          }}
          data-testid="cl-body-textarea"
        />
        {saveError && (
          <p className="text-xs text-red-500 mt-1">{saveError}</p>
        )}
        {bodyEditing && (
          <div className="flex gap-2 mt-2">
            <button
              type="button"
              onClick={handleSaveBody}
              disabled={saving}
              className="flex-1 bg-blue-600 text-white text-xs py-1.5 rounded hover:bg-blue-700 disabled:opacity-50"
              data-testid="cl-save-body-btn"
            >
              {saving ? tc("preparing") : tc("save")}
            </button>
            <button
              type="button"
              onClick={() => {
                setBodyText(letterData?.body?.paragraphs?.join("\n\n") ?? "");
                setBodyEditing(false);
              }}
              disabled={saving}
              className="flex-1 border border-neutral-300 text-xs py-1.5 rounded hover:border-neutral-500 disabled:opacity-50"
            >
              {tc("cancel")}
            </button>
          </div>
        )}
      </div>

      {/* Signature — read-only */}
      <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-semibold">Unterschrift & Datum</span>
          <span className="text-xs text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
            auto
          </span>
        </div>
        <p className="text-xs text-neutral-500">
          {signature?.closing ?? "Mit freundlichen Grüßen"} · {signature?.name ?? "–"}
        </p>
      </div>
    </div>
  );
}
