"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

// Curated professional preset colors (hue-diverse, all print-safe)
const PRESET_COLORS = [
  { hex: "#2b5fa8", label: "Klassisches Blau" },
  { hex: "#c0392b", label: "Rot" },
  { hex: "#27ae60", label: "Grün" },
  { hex: "#8e44ad", label: "Violett" },
  { hex: "#1a7a6e", label: "Teal" },
  { hex: "#e67e22", label: "Orange" },
];

interface DetectedCompany {
  name: string;
  hex: string;
}

interface DesignTabProps {
  cvId: string;
  templateLabel: string | null;
  detectedCompany: DetectedCompany | null;
  currentAccentHex: string;
  onColorApplied: () => void;
  onChangeTemplate: () => void;
}

export function DesignTab({
  cvId,
  templateLabel,
  detectedCompany,
  currentAccentHex,
  onColorApplied,
  onChangeTemplate,
}: DesignTabProps) {
  const t = useTranslations("cv");
  const [selectedHex, setSelectedHex] = useState(currentAccentHex);
  const [appliedHex, setAppliedHex] = useState(currentAccentHex);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isDirty = selectedHex.toLowerCase() !== appliedHex.toLowerCase();

  const handleApply = async () => {
    if (!isDirty || applying) return;
    setApplying(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/cv/${cvId}/color`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accent_hex: selectedHex }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? "Farbe konnte nicht gespeichert werden");
      }
      setAppliedHex(selectedHex);
      onColorApplied();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unbekannter Fehler");
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 p-3" data-testid="design-tab">

      {/* Template selection */}
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-neutral-medium mb-2">
          Vorlage
        </p>
        <div className="flex items-center justify-between gap-2">
          {templateLabel && (
            <span className="text-sm font-medium text-neutral-dark">{templateLabel}</span>
          )}
          <button
            type="button"
            onClick={onChangeTemplate}
            className="text-sm text-teal underline hover:opacity-80 whitespace-nowrap"
            data-testid="change-template-btn"
          >
            Vorlage ändern
          </button>
        </div>
      </div>

      {/* Detected company color card */}
      {detectedCompany && (
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-neutral-medium mb-2">
            Erkannte Firmenfarbe
          </p>
          <div className="flex items-center gap-3 bg-teal-container-light border border-teal-container rounded-lg p-2.5">
            <button
              type="button"
              aria-label={`Farbe wählen: ${detectedCompany.hex}`}
              onClick={() => setSelectedHex(detectedCompany.hex)}
              className="w-8 h-8 rounded-full border-2 border-white shadow-sm flex-shrink-0 cursor-pointer"
              style={{ background: detectedCompany.hex }}
            />
            <div className="min-w-0">
              <p className="text-sm font-semibold text-neutral-dark truncate">
                {detectedCompany.name}
              </p>
              <p className="text-xs text-neutral-medium font-mono">{detectedCompany.hex}</p>
              <span className="text-xs font-semibold text-teal bg-teal-container rounded-full px-2 py-0.5 inline-block mt-0.5">
                {t("colorAutoDetected")}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Color picker */}
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-neutral-medium mb-3">
          Akzentfarbe wählen
        </p>

        {/* Native color picker — styled swatch wraps hidden input */}
        <div className="flex items-center gap-3 mb-3">
          <label className="cursor-pointer flex-shrink-0" title="Farbe auswählen">
            <div
              className="w-9 h-9 rounded-lg border border-neutral-medium shadow-sm"
              style={{ background: selectedHex }}
            />
            <input
              type="color"
              value={selectedHex}
              onChange={(e) => setSelectedHex(e.target.value)}
              className="sr-only"
            />
          </label>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-semibold text-neutral-dark">Akzentfarbe</div>
            <div className="text-[11px] text-neutral-medium">Überschriften, Linien, Hervorhebungen</div>
          </div>
          <code className="text-[11px] text-neutral-medium bg-surface-container px-1.5 py-0.5 rounded flex-shrink-0">
            {selectedHex}
          </code>
        </div>

        {/* Preset swatches */}
        <div className="flex flex-wrap gap-2">
          {PRESET_COLORS.map(({ hex, label }) => (
            <button
              key={hex}
              type="button"
              aria-label={`Farbe wählen: ${label}`}
              onClick={() => setSelectedHex(hex)}
              title={label}
              className={`w-7 h-7 rounded-full transition-transform ${
                selectedHex.toLowerCase() === hex.toLowerCase()
                  ? "ring-2 ring-offset-1 ring-neutral-dark scale-110"
                  : "hover:scale-105"
              }`}
              style={{ background: hex }}
            />
          ))}
        </div>
      </div>

      {/* Error */}
      {error && (
        <p className="text-xs text-red-600 bg-red-50 rounded p-2">{error}</p>
      )}

      {/* Apply button */}
      <button
        type="button"
        onClick={handleApply}
        disabled={!isDirty || applying}
        data-testid="color-apply-btn"
        className="w-full py-2 rounded text-sm font-semibold bg-teal text-white disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 transition-opacity"
      >
        {applying ? t("applyColor") : t("applyColor")}
      </button>
    </div>
  );
}
