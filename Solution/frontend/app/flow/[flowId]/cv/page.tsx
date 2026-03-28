"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { use } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

async function apiErrorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    const detail = body.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail))
      return detail.map((e: { msg?: string }) => e.msg ?? JSON.stringify(e)).join("; ");
    return res.statusText || `HTTP ${res.status}`;
  } catch {
    return res.statusText || `HTTP ${res.status}`;
  }
}

interface GeneratedCV {
  cv_id: string;
  html_url: string;
  pdf_url: string;
}

interface FlowState {
  job_id: string;
  cv_summary?: { cv_id: string; pdf_url: string } | null;
}

const s = {
  heading: { fontSize: 20, fontWeight: 700, color: "#1a1a2e", marginBottom: 6 },
  sub: { fontSize: 13, color: "#6b7280", marginBottom: 20 },
  toolbar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    marginBottom: 12,
    background: "#fff",
    borderRadius: 10,
    padding: "12px 16px",
    boxShadow: "0 1px 4px rgba(0,0,0,.08)",
    flexWrap: "wrap" as const,
  },
  templateRow: { display: "flex", gap: 8, alignItems: "center" },
  templateLabel: { fontSize: 12, color: "#6b7280", marginRight: 4 },
  select: {
    padding: "6px 10px",
    borderRadius: 6,
    border: "1px solid #d1d5db",
    fontSize: 13,
    fontFamily: "inherit",
    background: "#fff",
    cursor: "pointer",
  },
  actionsRow: { display: "flex", gap: 8 },
  btn: (variant: "primary" | "secondary" | "success") => ({
    padding: "8px 18px",
    borderRadius: 6,
    border: "none",
    cursor: "pointer",
    fontWeight: 600,
    fontSize: 13,
    background:
      variant === "primary"
        ? "#2563eb"
        : variant === "success"
        ? "#16a34a"
        : "#e5e7eb",
    color: variant === "primary" || variant === "success" ? "#fff" : "#374151",
    textDecoration: "none",
    display: "inline-block",
  }),
  previewPane: {
    border: "1px solid #d1d5db",
    borderRadius: 10,
    overflow: "hidden" as const,
    height: "70vh",
    background: "#fff",
    boxShadow: "0 1px 4px rgba(0,0,0,.08)",
  },
  error: { color: "#dc2626", fontSize: 12, marginTop: 8 },
  loading: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: "60vh",
    fontSize: 14,
    color: "#6b7280",
    flexDirection: "column" as const,
    gap: 8,
  },
  doneRow: { display: "flex", justifyContent: "flex-end", marginTop: 12 },
};

export default function CVPage({
  params,
}: {
  params: Promise<{ flowId: string }>;
}) {
  const { flowId } = use(params);
  const router = useRouter();

  const [cv, setCV] = useState<GeneratedCV | null>(null);
  const [flowState, setFlowState] = useState<FlowState | null>(null);
  const [template, setTemplate] = useState<"classic_german" | "modern_swiss">("classic_german");
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function init() {
      try {
        const fsRes = await fetch(`${API_BASE}/api/flow/${flowId}/state`);
        if (!fsRes.ok) throw new Error("Flow nicht gefunden");
        const fs: FlowState = await fsRes.json();
        setFlowState(fs);

        // Auto-generate CV on first visit
        await generateCV(fs.job_id, "classic_german", fs, flowId);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Fehler beim Laden");
      }
    }
    void init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flowId]);

  async function generateCV(
    jobId: string,
    tpl: "classic_german" | "modern_swiss",
    fs: FlowState,
    fId: string
  ) {
    setError("");
    setGenerating(true);
    try {
      const res = await fetch(`${API_BASE}/api/cv/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId, template: tpl }),
      });
      if (!res.ok) throw new Error(await apiErrorMessage(res));
      const data: GeneratedCV = await res.json();
      setCV(data);

      // Advance flow to cv_generation with the new CV id (idempotent — may already be there)
      const advRes = await fetch(`${API_BASE}/api/flow/${fId}/advance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: "cv_generation", artifact_id: data.cv_id }),
      });
      // 409 = already at cv_generation — fine
      if (!advRes.ok && advRes.status !== 409) {
        console.warn("advance warning:", await advRes.text());
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Generierung fehlgeschlagen");
    } finally {
      setGenerating(false);
    }
  }

  async function regenerate() {
    if (!flowState) return;
    await generateCV(flowState.job_id, template, flowState, flowId);
  }

  async function markDone() {
    try {
      await fetch(`${API_BASE}/api/flow/${flowId}/advance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: "complete" }),
      });
    } catch {
      // best-effort
    }
    router.push("/");
  }

  if (generating && !cv) {
    return (
      <div data-testid="cv-loading" style={s.loading}>
        <div>Erstelle Lebenslauf …</div>
        <div style={{ fontSize: 12, color: "#9ca3af" }}>
          Das kann 20–40 Sekunden dauern.
        </div>
      </div>
    );
  }

  return (
    <div data-testid="cv-page">
      <div style={s.heading}>Dein maßgeschneiderter Lebenslauf</div>
      <div style={s.sub}>Vorschau, herunterladen oder mit anderer Vorlage neu generieren.</div>

      <div style={s.toolbar}>
        <div style={s.templateRow}>
          <span style={s.templateLabel}>Vorlage:</span>
          <select
            style={s.select}
            value={template}
            onChange={(e) => setTemplate(e.target.value as "classic_german" | "modern_swiss")}
          >
            <option value="classic_german">Klassischer Lebenslauf (DE)</option>
            <option value="modern_swiss">Modern Swiss CV (EN/DE)</option>
          </select>
          <button style={s.btn("secondary")} onClick={regenerate} disabled={generating}>
            {generating ? "Generiere …" : "Neu generieren"}
          </button>
        </div>

        <div style={s.actionsRow}>
          {cv && (
            <a 
              href={`${API_BASE}${cv.pdf_url}`} 
              download 
              style={s.btn("success")}
              data-testid="download-button"
            >
              PDF herunterladen
            </a>
          )}
        </div>
      </div>

      {error && <div style={s.error}>{error}</div>}

      {cv ? (
        <iframe
          src={`${API_BASE}${cv.html_url}`}
          style={s.previewPane}
          title="Lebenslauf Vorschau"
        />
      ) : (
        !generating && (
          <div style={s.loading}>
            <div>Kein Lebenslauf geladen.</div>
          </div>
        )
      )}

      <div style={s.doneRow}>
        <button 
          style={s.btn("primary")} 
          onClick={markDone}
          data-testid="done-button"
        >
          Fertig — zurück zur Startseite
        </button>
      </div>
    </div>
  );
}