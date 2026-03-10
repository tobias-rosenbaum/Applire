"use client";

import { useRef, useState } from "react";

// The browser calls the backend directly — no server-side proxy needed.
// NEXT_PUBLIC_ vars are baked at build time; the default covers both local
// dev (npm run dev) and the Docker scenario (backend port 8001 is mapped
// to the host in docker-compose).
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

async function apiErrorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    const detail = body.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((e: { msg?: string }) => e.msg ?? JSON.stringify(e)).join("; ");
    return res.statusText || `HTTP ${res.status}`;
  } catch {
    return res.statusText || `HTTP ${res.status}`;
  }
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface JobAnalysis {
  id: string;
  role_title: string;
  match_score?: number;
}

interface ProfileStatus {
  id: string;
  completeness: number;
}

interface GeneratedCV {
  cv_id: string;
  html_url: string;
  pdf_url: string;
}

type Step = "jd" | "profile" | "interview" | "generate" | "preview";

// ---------------------------------------------------------------------------
// Styles (plain objects — no build-time CSS needed)
// ---------------------------------------------------------------------------

const s = {
  app: {
    display: "flex",
    flexDirection: "column" as const,
    height: "100vh",
    maxWidth: 1200,
    margin: "0 auto",
    padding: "24px 20px",
    gap: 20,
  },
  header: { fontSize: 22, fontWeight: 700, color: "#1a1a2e", marginBottom: 4 },
  subheader: { fontSize: 13, color: "#666" },
  stepper: { display: "flex", gap: 6, marginBottom: 4 },
  stepBadge: (active: boolean, done: boolean) => ({
    padding: "3px 10px",
    borderRadius: 12,
    fontSize: 12,
    fontWeight: 600,
    background: done ? "#22c55e" : active ? "#2563eb" : "#e2e8f0",
    color: done || active ? "#fff" : "#64748b",
  }),
  card: {
    background: "#fff",
    borderRadius: 10,
    padding: 20,
    boxShadow: "0 1px 4px rgba(0,0,0,.08)",
  },
  label: { fontSize: 13, fontWeight: 600, marginBottom: 6, display: "block", color: "#374151" },
  textarea: {
    width: "100%",
    minHeight: 140,
    padding: 10,
    borderRadius: 6,
    border: "1px solid #d1d5db",
    fontFamily: "inherit",
    fontSize: 13,
    resize: "vertical" as const,
    boxSizing: "border-box" as const,
  },
  btn: (variant: "primary" | "secondary" | "success") => ({
    padding: "8px 18px",
    borderRadius: 6,
    border: "none",
    cursor: "pointer",
    fontWeight: 600,
    fontSize: 13,
    background: variant === "primary" ? "#2563eb" : variant === "success" ? "#16a34a" : "#e5e7eb",
    color: variant === "primary" || variant === "success" ? "#fff" : "#374151",
  }),
  error: { color: "#dc2626", fontSize: 12, marginTop: 6 },
  info: { fontSize: 12, color: "#6b7280", marginTop: 6 },
  previewPane: {
    flex: 1,
    border: "1px solid #d1d5db",
    borderRadius: 8,
    overflow: "hidden",
    minHeight: 500,
    background: "#fff",
  },
  row: { display: "flex", gap: 10, alignItems: "center", marginTop: 10, flexWrap: "wrap" as const },
  fileInput: { fontSize: 13 },
  tabRow: { display: "flex", gap: 4, marginBottom: 12 },
  tab: (active: boolean) => ({
    padding: "5px 14px",
    borderRadius: 6,
    border: "1px solid #d1d5db",
    cursor: "pointer",
    fontSize: 12,
    fontWeight: 600,
    background: active ? "#2563eb" : "#f9fafb",
    color: active ? "#fff" : "#374151",
  }),
  urlInput: {
    width: "100%",
    padding: "9px 12px",
    borderRadius: 6,
    border: "1px solid #d1d5db",
    fontSize: 13,
    fontFamily: "inherit",
    boxSizing: "border-box" as const,
  },
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function Home() {
  const [step, setStep] = useState<Step>("jd");

  // JD
  const [jdMode, setJdMode] = useState<"url" | "text">("url");
  const [jdUrl, setJdUrl] = useState("");
  const [jdText, setJdText] = useState("");
  const [jdLoading, setJdLoading] = useState(false);
  const [jdError, setJdError] = useState("");
  const [jobAnalysis, setJobAnalysis] = useState<JobAnalysis | null>(null);

  // Profile
  const [profileStatus, setProfileStatus] = useState<ProfileStatus | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  // Interview
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [interviewQuestion, setInterviewQuestion] = useState("");
  const [interviewAnswer, setInterviewAnswer] = useState("");
  const [gapsTotal, setGapsTotal] = useState(0);
  const [gapsRemaining, setGapsRemaining] = useState(0);
  const [interviewLoading, setInterviewLoading] = useState(false);
  const [interviewError, setInterviewError] = useState("");

  // Generate
  const [genLoading, setGenLoading] = useState(false);
  const [genError, setGenError] = useState("");
  const [generatedCV, setGeneratedCV] = useState<GeneratedCV | null>(null);

  // ---------------------------------------------------------------------------
  // Step 1 — Analyse JD
  // ---------------------------------------------------------------------------
  async function analyseJD() {
    if (jdMode === "url" && !jdUrl.trim()) { setJdError("Bitte eine URL eingeben."); return; }
    if (jdMode === "text" && !jdText.trim()) { setJdError("Bitte Stellenbeschreibung einfügen."); return; }
    setJdError("");
    setJdLoading(true);
    try {
      const body = jdMode === "url" ? { url: jdUrl.trim() } : { text: jdText };
      const res = await fetch(`${API_BASE}/api/job/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(await apiErrorMessage(res));
      const data = await res.json();
      setJobAnalysis(data);
      setStep("profile");
      // Also try to load profile
      void loadProfile();
    } catch (e: unknown) {
      setJdError(e instanceof Error ? e.message : "Failed to analyse JD");
    } finally {
      setJdLoading(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Step 2 — Load / import profile
  // ---------------------------------------------------------------------------
  async function loadProfile() {
    try {
      const res = await fetch(`${API_BASE}/api/profile`);
      if (res.ok) {
        const data = await res.json();
        setProfileStatus({ id: data.id, completeness: data.completeness });
      }
    } catch {
      // no profile yet — that's fine
    }
  }

  async function uploadCV() {
    const file = fileRef.current?.files?.[0];
    if (!file) { setProfileError("Select a PDF first."); return; }
    setProfileError("");
    setProfileLoading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API_BASE}/api/profile/import`, { method: "POST", body: form });
      if (!res.ok) throw new Error(await apiErrorMessage(res));
      const data = await res.json();
      setProfileStatus({ id: data.id, completeness: data.completeness });
      setStep("interview");
      void startInterview();
    } catch (e: unknown) {
      setProfileError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setProfileLoading(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Step 3 — Gap-fill interview
  // ---------------------------------------------------------------------------
  async function startInterview() {
    if (!jobAnalysis) return;
    setInterviewError("");
    setInterviewLoading(true);
    try {
      // Gap analysis must exist before a session can be created
      const gapRes = await fetch(`${API_BASE}/api/job/${jobAnalysis.id}/gaps`, {
        method: "POST",
      });
      if (!gapRes.ok) throw new Error(await apiErrorMessage(gapRes));

      const res = await fetch(`${API_BASE}/api/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobAnalysis.id }),
      });
      if (!res.ok) throw new Error(await apiErrorMessage(res));
      const data = await res.json();
      setSessionId(data.session_id);
      setInterviewQuestion(data.question);
      setGapsTotal(data.gaps_total);
      setGapsRemaining(data.gaps_remaining);
    } catch (e: unknown) {
      setInterviewError(e instanceof Error ? e.message : "Failed to start interview");
    } finally {
      setInterviewLoading(false);
    }
  }

  async function sendAnswer() {
    if (!sessionId || !interviewAnswer.trim()) return;
    setInterviewError("");
    setInterviewLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/session/${sessionId}/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: interviewAnswer.trim() }),
      });
      if (!res.ok) throw new Error(await apiErrorMessage(res));
      const data = await res.json();
      setInterviewAnswer("");
      if (data.complete) {
        setStep("generate");
      } else {
        setInterviewQuestion(data.question);
        setGapsRemaining(data.gaps_remaining);
      }
    } catch (e: unknown) {
      setInterviewError(e instanceof Error ? e.message : "Failed to send answer");
    } finally {
      setInterviewLoading(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Step 4 — Generate tailored CV
  // ---------------------------------------------------------------------------
  async function generateCV() {
    if (!jobAnalysis) return;
    setGenError("");
    setGenLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/cv/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobAnalysis.id }),
      });
      if (!res.ok) throw new Error(await apiErrorMessage(res));
      const data = await res.json();
      setGeneratedCV(data);
      setStep("preview");
    } catch (e: unknown) {
      setGenError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setGenLoading(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  const steps: { key: Step; label: string }[] = [
    { key: "jd", label: "1 JD Analyse" },
    { key: "profile", label: "2 Profil" },
    { key: "interview", label: "3 Interview" },
    { key: "generate", label: "4 Generieren" },
    { key: "preview", label: "5 Vorschau" },
  ];
  const stepOrder: Step[] = ["jd", "profile", "interview", "generate", "preview"];

  return (
    <div style={s.app}>
      {/* Header */}
      <div>
        <div style={s.header}>Apliqa</div>
        <div style={s.subheader}>KI-gestütztes Lebenslauf-Tailoring für den DACH-Markt</div>
      </div>

      {/* Stepper */}
      <div style={s.stepper}>
        {steps.map(({ key, label }) => {
          const idx = stepOrder.indexOf(key);
          const currentIdx = stepOrder.indexOf(step);
          return (
            <span
              key={key}
              style={s.stepBadge(key === step, idx < currentIdx)}
            >
              {label}
            </span>
          );
        })}
      </div>

      {/* ---- Step 1: JD ---- */}
      <div style={s.card}>
        <label style={s.label}>Stellenanzeige einfügen</label>
        {!jobAnalysis && (
          <div style={s.tabRow}>
            <button style={s.tab(jdMode === "url")} onClick={() => setJdMode("url")}>
              URL eingeben
            </button>
            <button style={s.tab(jdMode === "text")} onClick={() => setJdMode("text")}>
              Text einfügen
            </button>
          </div>
        )}
        {jdMode === "url" ? (
          <input
            type="url"
            style={s.urlInput}
            placeholder="https://www.stepstone.de/…"
            value={jdUrl}
            onChange={(e) => setJdUrl(e.target.value)}
            disabled={!!jobAnalysis}
          />
        ) : (
          <textarea
            style={s.textarea}
            placeholder="Füge die vollständige Stellenbeschreibung hier ein …"
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            disabled={!!jobAnalysis}
          />
        )}
        {jdError && <div style={s.error}>{jdError}</div>}
        {jobAnalysis ? (
          <div style={{ ...s.info, color: "#16a34a", marginTop: 8 }}>
            ✓ Analysiert: <strong>{jobAnalysis.role_title}</strong>
          </div>
        ) : (
          <div style={s.row}>
            <button style={s.btn("primary")} onClick={analyseJD} disabled={jdLoading}>
              {jdLoading ? "Analysiere …" : "JD analysieren"}
            </button>
          </div>
        )}
      </div>

      {/* ---- Step 2: Profile ---- */}
      {step !== "jd" && (
        <div style={s.card}>
          <label style={s.label}>Lebenslauf / Profil</label>
          {profileStatus && (
            <div style={{ ...s.info, color: "#16a34a", marginBottom: 10 }}>
              ✓ Profil geladen — Vollständigkeit: <strong>{profileStatus.completeness}%</strong>
            </div>
          )}
          <input ref={fileRef} type="file" accept=".pdf" style={s.fileInput} />
          {profileError && <div style={s.error}>{profileError}</div>}
          <div style={s.row}>
            <button style={s.btn("primary")} onClick={uploadCV} disabled={profileLoading}>
              {profileLoading ? "Lade hoch …" : profileStatus ? "PDF ersetzen & weiter" : "PDF hochladen"}
            </button>
            {profileStatus && (
              <button style={s.btn("secondary")} onClick={() => { setStep("interview"); void startInterview(); }}>
                Weiter (bestehendes Profil verwenden)
              </button>
            )}
          </div>
        </div>
      )}

      {/* ---- Step 3: Interview ---- */}
      {(step === "interview" || step === "generate" || step === "preview") && (
        <div style={s.card}>
          <label style={s.label}>Gap-Interview</label>
          {step === "interview" ? (
            interviewLoading && !interviewQuestion ? (
              <div style={s.info}>Starte Interview …</div>
            ) : (
              <>
                {gapsTotal > 0 && (
                  <div style={{ ...s.info, marginBottom: 8 }}>
                    Frage {gapsTotal - gapsRemaining + 1} von {gapsTotal}
                  </div>
                )}
                <div style={{ fontWeight: 500, fontSize: 14, marginBottom: 10 }}>{interviewQuestion}</div>
                <textarea
                  style={s.textarea}
                  placeholder="Deine Antwort …"
                  value={interviewAnswer}
                  onChange={(e) => setInterviewAnswer(e.target.value)}
                  disabled={interviewLoading}
                />
                {interviewError && <div style={s.error}>{interviewError}</div>}
                <div style={s.row}>
                  <button style={s.btn("primary")} onClick={sendAnswer} disabled={interviewLoading || !interviewAnswer.trim()}>
                    {interviewLoading ? "Sende …" : "Antworten"}
                  </button>
                  <button style={s.btn("secondary")} onClick={() => setStep("generate")} disabled={interviewLoading}>
                    Überspringen
                  </button>
                </div>
              </>
            )
          ) : (
            <div style={{ ...s.info, color: "#16a34a" }}>✓ Interview abgeschlossen</div>
          )}
        </div>
      )}

      {/* ---- Step 4: Generate ---- */}
      {(step === "generate" || step === "preview") && (
        <div style={s.card}>
          <label style={s.label}>Lebenslauf generieren</label>
          {generatedCV ? (
            <div style={{ ...s.info, color: "#16a34a" }}>✓ Lebenslauf erstellt</div>
          ) : (
            <>
              {genError && <div style={s.error}>{genError}</div>}
              <div style={s.row}>
                <button style={s.btn("primary")} onClick={generateCV} disabled={genLoading}>
                  {genLoading ? "Generiere …" : "Lebenslauf erstellen"}
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {/* ---- Step 4: Preview ---- */}
      {step === "preview" && generatedCV && (
        <div style={{ display: "flex", flexDirection: "column", flex: 1, gap: 10 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontWeight: 600, fontSize: 14 }}>Vorschau</span>
            <a
              href={generatedCV.pdf_url}
              download
              style={{
                ...s.btn("success"),
                textDecoration: "none",
                display: "inline-block",
              }}
            >
              PDF herunterladen
            </a>
          </div>
          <iframe
            src={generatedCV.html_url}
            style={s.previewPane}
            title="CV Vorschau"
          />
        </div>
      )}
    </div>
  );
}
