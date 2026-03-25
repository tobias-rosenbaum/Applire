"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

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

const s = {
  app: {
    display: "flex",
    flexDirection: "column" as const,
    minHeight: "100vh",
    maxWidth: 720,
    margin: "0 auto",
    padding: "48px 20px",
    gap: 24,
  },
  header: { fontSize: 28, fontWeight: 700, color: "#1a1a2e", marginBottom: 4 },
  subheader: { fontSize: 14, color: "#6b7280" },
  card: {
    background: "#fff",
    borderRadius: 10,
    padding: 24,
    boxShadow: "0 1px 4px rgba(0,0,0,.08)",
  },
  label: { fontSize: 13, fontWeight: 600, marginBottom: 8, display: "block", color: "#374151" },
  tabRow: { display: "flex", gap: 4, marginBottom: 14 },
  tab: (active: boolean) => ({
    padding: "6px 16px",
    borderRadius: 6,
    border: "1px solid #d1d5db",
    cursor: "pointer",
    fontSize: 13,
    fontWeight: 600,
    background: active ? "#2563eb" : "#f9fafb",
    color: active ? "#fff" : "#374151",
  }),
  urlInput: {
    width: "100%",
    padding: "10px 12px",
    borderRadius: 6,
    border: "1px solid #d1d5db",
    fontSize: 13,
    fontFamily: "inherit",
    boxSizing: "border-box" as const,
  },
  textarea: {
    width: "100%",
    minHeight: 160,
    padding: 10,
    borderRadius: 6,
    border: "1px solid #d1d5db",
    fontFamily: "inherit",
    fontSize: 13,
    resize: "vertical" as const,
    boxSizing: "border-box" as const,
  },
  hint: { fontSize: 12, color: "#6b7280", marginTop: 8 },
  btn: {
    marginTop: 16,
    padding: "10px 24px",
    borderRadius: 6,
    border: "none",
    cursor: "pointer",
    fontWeight: 600,
    fontSize: 14,
    background: "#2563eb",
    color: "#fff",
  },
  error: { color: "#dc2626", fontSize: 12, marginTop: 8 },
};

export default function Home() {
  const router = useRouter();
  const [jdMode, setJdMode] = useState<"url" | "text">("url");
  const [jdUrl, setJdUrl] = useState("");
  const [jdText, setJdText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyseJD() {
    if (jdMode === "url" && !jdUrl.trim()) {
      setError("Bitte eine URL eingeben.");
      return;
    }
    if (jdMode === "text" && !jdText.trim()) {
      setError("Bitte Stellenbeschreibung einfügen.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      // Step 1: analyse the JD
      const body = jdMode === "url" ? { url: jdUrl.trim() } : { text: jdText };
      const jdRes = await fetch(`${API_BASE}/api/job/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!jdRes.ok) throw new Error(await apiErrorMessage(jdRes));
      const job = await jdRes.json();

      // Step 2: create a flow session — resolves user_type (new/returning)
      const flowRes = await fetch(`${API_BASE}/api/flow`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: job.id }),
      });
      if (!flowRes.ok) throw new Error(await apiErrorMessage(flowRes));
      const flow = await flowRes.json();

      // Step 3: route based on user_type
      const nextStep = flow.available_actions?.next;
      if (nextStep === "gap_analysis") {
        // Returning user — skip import
        router.push(`/flow/${flow.flow_id}/gaps`);
      } else {
        // New user — go to CV import
        router.push(`/flow/${flow.flow_id}/import`);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Fehler bei der Analyse");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={s.app}>
      <div>
        <div style={s.header}>Apliqa</div>
        <div style={s.subheader}>
          KI-gestütztes Lebenslauf-Tailoring für den DACH-Markt — Von der Stellenanzeige zum
          maßgeschneiderten Lebenslauf in unter 15 Minuten.
        </div>
      </div>

      <div style={s.card}>
        <label style={s.label}>Stellenanzeige einfügen</label>
        <div style={s.tabRow}>
          <button style={s.tab(jdMode === "url")} onClick={() => setJdMode("url")}>
            URL
          </button>
          <button style={s.tab(jdMode === "text")} onClick={() => setJdMode("text")}>
            Text einfügen
          </button>
        </div>

        {jdMode === "url" ? (
          <>
            <input
              type="url"
              style={s.urlInput}
              placeholder="https://www.stepstone.de/…"
              value={jdUrl}
              onChange={(e) => setJdUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && analyseJD()}
              disabled={loading}
            />
            <div style={s.hint}>
              Stepstone, Indeed, XING Jobs — direkte URL funktioniert für die meisten Portale.
              Bei LinkedIn bitte den Text manuell einfügen.
            </div>
          </>
        ) : (
          <textarea
            style={s.textarea}
            placeholder="Füge die vollständige Stellenbeschreibung hier ein …"
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            disabled={loading}
          />
        )}

        {error && <div style={s.error}>{error}</div>}

        <button style={s.btn} onClick={analyseJD} disabled={loading}>
          {loading ? "Analysiere …" : "Jetzt analysieren →"}
        </button>
      </div>
    </div>
  );
}
