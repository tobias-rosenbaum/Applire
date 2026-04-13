"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

const TEMPLATES = [
  {
    id: "classic_german" as const,
    name: "Klassischer Lebenslauf",
    description: "Traditionelles deutsches Format — strukturiert, fotofähig, mit Tabellenstruktur.",
  },
  {
    id: "modern_swiss" as const,
    name: "Modern Swiss CV",
    description: "Klares, einspaltiges Design für den europäischen Markt. Kein Foto.",
  },
  {
    id: "executive" as const,
    name: "Executive / Premium",
    description: "Dunkler Header, zweispaltig, Serifen-Schrift — für Führungskräfte und Senior-Profile.",
  },
  {
    id: "tech_developer" as const,
    name: "Tech / Developer",
    description: "Code-Ästhetik, dunkler Hintergrund, Monospace — für Software Engineers und DevOps.",
  },
  {
    id: "creative_sidebar" as const,
    name: "Creative / Sidebar",
    description: "Farbige Sidebar, zweispaltig, rundes Avatar-Foto — für Design- und Kreativberufe.",
  },
  {
    id: "academic" as const,
    name: "Academic / Scientific",
    description: "Konservatives Layout, Serifen-Schrift, Publikationsliste — für Wissenschaft und Forschung.",
  },
  {
    id: "compact_pro" as const,
    name: "Compact Pro",
    description: "Maximale Informationsdichte, zweispaltiges Raster — für erfahrene Fachkräfte.",
  },
] as const;

type CVTemplate = (typeof TEMPLATES)[number]["id"];

interface TemplateSelectorProps {
  onGenerate: (template: CVTemplate) => void;
  isLoading?: boolean;
  /** Label for the action button — defaults to "CV generieren" */
  actionLabel?: string;
}

export function TemplateSelector({
  onGenerate,
  isLoading = false,
  actionLabel = "CV generieren",
}: TemplateSelectorProps) {
  const [selected, setSelected] = useState<CVTemplate>("classic_german");

  return (
    <div className="max-w-2xl mx-auto animate-fade-in">
      <h1 className="text-2xl font-heading font-bold text-neutral-dark mb-1">
        Vorlage auswählen
      </h1>
      <p className="text-sm text-gray-500 mb-8">
        Wähle eine Vorlage für deinen maßgeschneiderten Lebenslauf.
      </p>

      <div className="grid grid-cols-2 gap-6 mb-8">
        {TEMPLATES.map((tpl) => (
          <div key={tpl.id} data-testid="template-option">
            <button
              type="button"
              data-testid={`template-option-${tpl.id}`}
              onClick={() => setSelected(tpl.id)}
              className={[
                "w-full text-left rounded-xl overflow-hidden bg-white shadow-soft border-2 transition-all duration-200",
                selected === tpl.id
                  ? "border-teal ring-2 ring-teal ring-opacity-20"
                  : "border-transparent hover:border-gray-200",
              ].join(" ")}
            >
              <div className="h-1 bg-teal w-full" />
              <div className="bg-neutral-light h-48 overflow-hidden">
                <img
                  src={`${API_BASE}/static/templates/${tpl.id}.png`}
                  alt={`Vorschau: ${tpl.name}`}
                  className="w-full h-full object-cover object-top"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = "none";
                  }}
                />
              </div>
              <div className="p-4">
                <div className="flex items-center gap-2 mb-1">
                  {selected === tpl.id && (
                    <span className="w-4 h-4 rounded-full bg-teal flex items-center justify-center text-white text-[10px] font-bold">
                      ✓
                    </span>
                  )}
                  <p className="font-semibold text-neutral-dark text-sm">{tpl.name}</p>
                </div>
                <p className="text-xs text-gray-500">{tpl.description}</p>
              </div>
            </button>
          </div>
        ))}
      </div>

      <button
        type="button"
        data-testid="regenerate-cv-button"
        onClick={() => onGenerate(selected)}
        disabled={isLoading}
        className="w-full bg-teal text-white font-semibold py-3 rounded-lg text-sm hover:bg-teal-dim transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? "Generiere …" : actionLabel}
      </button>
    </div>
  );
}
