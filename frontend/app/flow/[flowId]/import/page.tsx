"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { use } from "react";
import { useTranslations } from "next-intl";

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

async function advanceFlow(flowId: string, step: string, artifactId?: string) {
  const res = await fetch(`${API_BASE}/api/flow/${flowId}/advance`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ step, artifact_id: artifactId ?? null }),
  });
  if (!res.ok) throw new Error(await apiErrorMessage(res));
  return res.json();
}

const s = {
  heading: { fontSize: 20, fontWeight: 700, color: "#1a1a2e", marginBottom: 6 },
  sub: { fontSize: 13, color: "#6b7280", marginBottom: 24 },
  optionGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr",
    gap: 16,
    marginBottom: 24,
  },
  option: (active: boolean) => ({
    background: "#fff",
    borderRadius: 10,
    padding: 20,
    boxShadow: active ? "0 0 0 2px #2563eb" : "0 1px 4px rgba(0,0,0,.08)",
    cursor: "pointer",
    textAlign: "center" as const,
    border: active ? "1px solid #2563eb" : "1px solid transparent",
  }),
  optionTitle: { fontSize: 14, fontWeight: 600, color: "#1a1a2e", marginBottom: 4 },
  optionDesc: { fontSize: 12, color: "#6b7280" },
  card: {
    background: "#fff",
    borderRadius: 10,
    padding: 24,
    boxShadow: "0 1px 4px rgba(0,0,0,.08)",
  },
  label: { fontSize: 13, fontWeight: 600, marginBottom: 8, display: "block", color: "#374151" },
  hint: { fontSize: 11, color: "#9ca3af", marginBottom: 12, lineHeight: 1.5 },
  fileInput: { fontSize: 13, marginBottom: 12 },
  row: { display: "flex", gap: 10, alignItems: "center", marginTop: 12, flexWrap: "wrap" as const },
  btn: (variant: "primary" | "secondary" | "ghost") => ({
    padding: "9px 20px",
    borderRadius: 6,
    border: "none",
    cursor: "pointer",
    fontWeight: 600,
    fontSize: 13,
    background:
      variant === "primary"
        ? "#2563eb"
        : variant === "secondary"
        ? "#e5e7eb"
        : "transparent",
    color: variant === "primary" ? "#fff" : "#374151",
    textDecoration: "none",
  }),
  error: { color: "#dc2626", fontSize: 12, marginTop: 8 },
  completeness: (score: number) => ({
    display: "inline-block",
    padding: "2px 10px",
    borderRadius: 12,
    fontSize: 12,
    fontWeight: 600,
    background: score >= 0.7 ? "#dcfce7" : score >= 0.4 ? "#fef9c3" : "#fee2e2",
    color: score >= 0.7 ? "#166534" : score >= 0.4 ? "#854d0e" : "#991b1b",
  }),
};

type ImportMode = "pdf" | "linkedin" | "fresh";

export default function ImportPage({
  params,
}: {
  params: Promise<{ flowId: string }>;
}) {
  const { flowId } = use(params);
  const router = useRouter();
  const t = useTranslations("import");

  const [mode, setMode] = useState<ImportMode>("pdf");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [uploadedCompleteness, setUploadedCompleteness] = useState<number | null>(null);
  const [profileSaved, setProfileSaved] = useState(false);

  const pdfRef = useRef<HTMLInputElement>(null);
  const zipRef = useRef<HTMLInputElement>(null);

  async function handleUpload() {
    setError("");
    setLoading(true);
    try {
      let uploadRes: Response;

      if (mode === "pdf") {
        const file = pdfRef.current?.files?.[0];
        if (!file) { setError("Bitte eine PDF-Datei auswählen."); return; }
        const form = new FormData();
        form.append("file", file);
        uploadRes = await fetch(`${API_BASE}/api/profile/upload`, {
          method: "POST",
          body: form,
        });
      } else {
        // LinkedIn ZIP or PDF
        const file = zipRef.current?.files?.[0];
        if (!file) { setError("Bitte eine LinkedIn-ZIP-Datei auswählen."); return; }
        const form = new FormData();
        form.append("file", file);
        uploadRes = await fetch(`${API_BASE}/api/profile/import`, {
          method: "POST",
          body: form,
        });
      }

      if (!uploadRes.ok) throw new Error(await apiErrorMessage(uploadRes));
      const uploadData = await uploadRes.json();
      setUploadedCompleteness(uploadData.completeness_score ?? null);
      setProfileSaved(true);

      // Trigger gap analysis then advance flow
      await proceedToGaps();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload fehlgeschlagen");
    } finally {
      setLoading(false);
    }
  }

  async function proceedToGaps() {
    setError("");
    setLoading(true);
    try {
      // Run gap analysis for the flow's job
      const flowStateRes = await fetch(`${API_BASE}/api/flow/${flowId}/state`);
      if (!flowStateRes.ok) throw new Error("Flow nicht gefunden");
      const flowState = await flowStateRes.json();

      const gapRes = await fetch(`${API_BASE}/api/job/${flowState.job_id}/gaps`, {
        method: "POST",
      });
      if (!gapRes.ok) {
        const msg = await apiErrorMessage(gapRes);
        throw new Error(
          gapRes.status === 504
            ? `KI-Zeitüberschreitung: ${msg}`
            : msg
        );
      }
      const gapData = await gapRes.json();

      await advanceFlow(flowId, "gap_analysis", gapData.id);
      router.push(`/flow/${flowId}/gaps`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Fehler beim Fortfahren");
    } finally {
      setLoading(false);
    }
  }

  async function startFresh() {
    setError("");
    setLoading(true);
    try {
      // No CV upload — advance directly to gap_analysis (triggers MODE B interview)
      const flowStateRes = await fetch(`${API_BASE}/api/flow/${flowId}/state`);
      if (!flowStateRes.ok) throw new Error("Flow nicht gefunden");
      const flowState = await flowStateRes.json();

      const gapRes = await fetch(`${API_BASE}/api/job/${flowState.job_id}/gaps`, {
        method: "POST",
      });
      if (!gapRes.ok) throw new Error(await apiErrorMessage(gapRes));
      const gapData = await gapRes.json();

      await advanceFlow(flowId, "gap_analysis", gapData.id);
      router.push(`/flow/${flowId}/gaps`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Fehler beim Fortfahren");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div style={s.heading}>{t("title")}</div>
      <div style={s.sub}>
        Lade deinen CV hoch oder starte frisch — das System passt sich an.
      </div>

      <div style={s.optionGrid}>
        <div style={s.option(mode === "pdf")} onClick={() => setMode("pdf")}>
          <div style={s.optionTitle}>PDF hochladen</div>
          <div style={s.optionDesc}>Beliebiger Lebenslauf als PDF oder DOCX</div>
        </div>
        <div style={s.option(mode === "linkedin")} onClick={() => setMode("linkedin")}>
          <div style={s.optionTitle}>LinkedIn PDF</div>
          <div style={s.optionDesc}>LinkedIn-Profil als PDF oder ZIP-Archiv</div>
        </div>
        <div style={s.option(mode === "fresh")} onClick={() => setMode("fresh")}>
          <div style={s.optionTitle}>Neu starten</div>
          <div style={s.optionDesc}>Das System befragt dich Schritt für Schritt</div>
        </div>
      </div>

      {mode === "pdf" && (
        <div style={s.card}>
          <label style={s.label}>PDF oder DOCX hochladen</label>
          <input ref={pdfRef} type="file" accept=".pdf,.docx,.doc" style={s.fileInput} />
          {uploadedCompleteness !== null && (
            <div style={{ marginBottom: 12 }}>
              Profil-Vollständigkeit:{" "}
              <span style={s.completeness(uploadedCompleteness)}>
                {Math.round(uploadedCompleteness * 100)}%
              </span>
            </div>
          )}
          {error && <div style={s.error}>{error}</div>}
          <div style={s.row}>
            {profileSaved && error ? (
              <button style={s.btn("primary")} onClick={proceedToGaps} disabled={loading}>
                {loading ? "Analysiere …" : "Analyse wiederholen →"}
              </button>
            ) : (
              <button style={s.btn("primary")} onClick={handleUpload} disabled={loading}>
                {loading ? "Hochladen …" : "Hochladen & weiter"}
              </button>
            )}
          </div>
        </div>
      )}

      {mode === "linkedin" && (
        <div style={s.card}>
          <label style={s.label}>LinkedIn-Export hochladen</label>
          <div style={s.hint}>
            LinkedIn → Einstellungen → Datenschutz → Daten abrufen → Vollständiges Archiv
            herunterladen. Alternativ: Profil als PDF speichern.
          </div>
          <input ref={zipRef} type="file" accept=".zip,.pdf" style={s.fileInput} />
          {error && <div style={s.error}>{error}</div>}
          <div style={s.row}>
            {profileSaved && error ? (
              <button style={s.btn("primary")} onClick={proceedToGaps} disabled={loading}>
                {loading ? "Analysiere …" : "Analyse wiederholen →"}
              </button>
            ) : (
              <button style={s.btn("primary")} onClick={handleUpload} disabled={loading}>
                {loading ? "Importiere …" : "Importieren & weiter"}
              </button>
            )}
          </div>
        </div>
      )}

      {mode === "fresh" && (
        <div style={s.card}>
          <div style={{ fontSize: 14, color: "#374151", marginBottom: 16 }}>
            Das System wird dich in einem geführten Interview Schritt für Schritt durch dein
            Profil führen. Keine Vorkenntnisse erforderlich — beantworte einfach die Fragen.
          </div>
          {error && <div style={s.error}>{error}</div>}
          <button style={s.btn("primary")} onClick={startFresh} disabled={loading}>
            {loading ? "Starte …" : "Ohne Lebenslauf starten →"}
          </button>
        </div>
      )}
    </div>
  );
}
