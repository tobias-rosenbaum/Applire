"use client";

import { useState } from "react";

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
  detectedCompany: DetectedCompany | null;
  currentAccentHex: string;
  onColorApplied: () => void;
}

export function DesignTab({
  cvId,
  detectedCompany,
  currentAccentHex,
  onColorApplied,
}: DesignTabProps) {
  const [selectedHex, setSelectedHex] = useState(currentAccentHex);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isDirty = selectedHex.toLowerCase() !== currentAccentHex.toLowerCase();

  const handleApply = async () => {
    if (!isDirty || applying) return;
    setApplying(true);
    setError(null);
    try {
      const res = await fetch(`/api/cv/${cvId}/color`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accent_hex: selectedHex }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? "Farbe konnte nicht gespeichert werden");
      }
      onColorApplied();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unbekannter Fehler");
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 p-3" data-testid="design-tab">

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
                automatisch erkannt
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Preset swatches */}
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-neutral-medium mb-2">
          Akzentfarbe wählen
        </p>
        <div className="flex flex-wrap gap-2 mb-3">
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

        {/* Hex input */}
        <div className="flex items-center gap-2 bg-surface-container border border-neutral-medium rounded px-2 py-1.5">
          <div
            className="w-4 h-4 rounded flex-shrink-0 border border-neutral-medium"
            style={{ background: selectedHex }}
          />
          <input
            type="text"
            value={selectedHex}
            onChange={(e) => {
              const val = e.target.value;
              if (/^#[0-9a-fA-F]{0,6}$/.test(val)) setSelectedHex(val);
            }}
            className="flex-1 text-sm font-mono bg-transparent outline-none text-neutral-dark min-w-0"
            maxLength={7}
          />
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
        className="w-full py-2 rounded text-sm font-semibold bg-teal text-white disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 transition-opacity"
      >
        {applying ? "Wird angewendet…" : "Farbe übernehmen"}
      </button>
    </div>
  );
}
