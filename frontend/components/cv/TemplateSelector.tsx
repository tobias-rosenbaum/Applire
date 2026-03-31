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
] as const;

type CVTemplate = "classic_german" | "modern_swiss";

interface TemplateSelectorProps {
  onGenerate: (template: CVTemplate) => void;
  isLoading?: boolean;
}

export function TemplateSelector({ onGenerate, isLoading = false }: TemplateSelectorProps) {
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
          <button
            key={tpl.id}
            type="button"
            onClick={() => setSelected(tpl.id)}
            className={[
              "text-left rounded-xl overflow-hidden bg-white shadow-soft border-2 transition-all duration-200",
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
        ))}
      </div>

      <button
        type="button"
        onClick={() => onGenerate(selected)}
        disabled={isLoading}
        className="w-full bg-teal text-white font-semibold py-3 rounded-lg text-sm hover:bg-teal-dim transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? "Generiere …" : "CV generieren"}
      </button>
    </div>
  );
}
