"use client";

import { useEffect, useRef, useState } from "react";
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

interface Message {
  role: "assistant" | "user";
  content: string;
}

interface FlowState {
  job_id: string;
  job_summary?: { role_title: string; required_skills?: string[] } | null;
}

const s = {
  layout: { display: "flex", gap: 24, alignItems: "flex-start" },
  main: { flex: 1, minWidth: 0 },
  sidebar: {
    width: 240,
    flexShrink: 0,
    background: "#fff",
    borderRadius: 10,
    padding: 16,
    boxShadow: "0 1px 4px rgba(0,0,0,.08)",
    fontSize: 12,
    color: "#374151",
  },
  sidebarTitle: { fontSize: 12, fontWeight: 700, color: "#1a1a2e", marginBottom: 8 },
  sidebarTag: {
    display: "inline-block",
    padding: "2px 8px",
    background: "#e0e7ff",
    color: "#3730a3",
    borderRadius: 10,
    fontSize: 11,
    margin: "2px 3px 2px 0",
  },
  heading: { fontSize: 20, fontWeight: 700, color: "#1a1a2e", marginBottom: 6 },
  progress: { fontSize: 12, color: "#6b7280", marginBottom: 16 },
  chatBox: {
    background: "#fff",
    borderRadius: 10,
    padding: 20,
    boxShadow: "0 1px 4px rgba(0,0,0,.08)",
    marginBottom: 16,
    maxHeight: 420,
    overflowY: "auto" as const,
    display: "flex",
    flexDirection: "column" as const,
    gap: 12,
  },
  bubble: (role: "assistant" | "user") => ({
    alignSelf: role === "user" ? "flex-end" : "flex-start",
    maxWidth: "80%",
    background: role === "user" ? "#2563eb" : "#f3f4f6",
    color: role === "user" ? "#fff" : "#1a1a2e",
    borderRadius: role === "user" ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
    padding: "10px 14px",
    fontSize: 14,
    lineHeight: 1.5,
  }),
  inputRow: {
    display: "flex",
    gap: 8,
    background: "#fff",
    borderRadius: 10,
    padding: 12,
    boxShadow: "0 1px 4px rgba(0,0,0,.08)",
    alignItems: "flex-end",
  },
  textarea: {
    flex: 1,
    padding: "8px 12px",
    borderRadius: 6,
    border: "1px solid #d1d5db",
    fontFamily: "inherit",
    fontSize: 13,
    resize: "none" as const,
    minHeight: 44,
    maxHeight: 160,
    lineHeight: 1.5,
    overflowY: "auto" as const,
  },
  sendBtn: (disabled: boolean) => ({
    padding: "10px 20px",
    borderRadius: 6,
    border: "none",
    cursor: disabled ? "not-allowed" : "pointer",
    fontWeight: 600,
    fontSize: 13,
    background: disabled ? "#93c5fd" : "#2563eb",
    color: "#fff",
    flexShrink: 0,
  }),
  skipBtn: {
    padding: "10px 16px",
    borderRadius: 6,
    border: "none",
    cursor: "pointer",
    fontWeight: 500,
    fontSize: 13,
    background: "#e5e7eb",
    color: "#374151",
    flexShrink: 0,
  },
  error: { color: "#dc2626", fontSize: 12, marginTop: 8 },
  loading: { fontSize: 14, color: "#6b7280", padding: "40px 0" },
  jdToggle: {
    fontSize: 12,
    color: "#2563eb",
    cursor: "pointer",
    textDecoration: "underline",
    marginBottom: 8,
    display: "inline-block",
  },
};

export default function InterviewPage({
  params,
}: {
  params: Promise<{ flowId: string }>;
}) {
  const { flowId } = use(params);
  const router = useRouter();
  const chatEndRef = useRef<HTMLDivElement>(null);

  const [flowState, setFlowState] = useState<FlowState | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [gapsTotal, setGapsTotal] = useState(0);
  const [gapsRemaining, setGapsRemaining] = useState(0);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [showJdContext, setShowJdContext] = useState(false);

  useEffect(() => {
    async function init() {
      try {
        const fsRes = await fetch(`${API_BASE}/api/flow/${flowId}/state`);
        if (!fsRes.ok) throw new Error("Flow nicht gefunden");
        const fs: FlowState = await fsRes.json();
        setFlowState(fs);

        // Create or resume interview session
        const sessionRes = await fetch(`${API_BASE}/api/session`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ job_id: fs.job_id }),
        });
        if (!sessionRes.ok) throw new Error(await apiErrorMessage(sessionRes));
        const sessionData = await sessionRes.json();

        setSessionId(sessionData.session_id);
        setGapsTotal(sessionData.gaps_total ?? 0);
        setGapsRemaining(sessionData.gaps_remaining ?? 0);
        setMessages([{ role: "assistant", content: sessionData.question ?? sessionData.first_question }]);

        // Advance flow to "interview" step with session ID
        const advRes = await fetch(`${API_BASE}/api/flow/${flowId}/advance`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            step: "interview",
            artifact_id: sessionData.session_id,
          }),
        });
        // 409 = already at interview step, that's fine
        if (!advRes.ok && advRes.status !== 409) {
          console.warn("advance_flow warning:", await advRes.text());
        }
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Fehler beim Starten des Interviews");
      } finally {
        setLoading(false);
      }
    }
    void init();
  }, [flowId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendAnswer() {
    if (!sessionId || !answer.trim() || sending) return;
    const userMsg = answer.trim();
    setAnswer("");
    setError("");
    setSending(true);

    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);

    try {
      const res = await fetch(`${API_BASE}/api/session/${sessionId}/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg }),
      });
      if (!res.ok) throw new Error(await apiErrorMessage(res));
      const data = await res.json();

      if (data.complete) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "Interview abgeschlossen. Generiere deinen Lebenslauf." },
        ]);
        await advanceToCV();
      } else {
        setMessages((prev) => [...prev, { role: "assistant", content: data.question }]);
        setGapsRemaining(data.gaps_remaining ?? 0);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Fehler beim Senden");
    } finally {
      setSending(false);
    }
  }

  async function advanceToCV() {
    try {
      await fetch(`${API_BASE}/api/flow/${flowId}/advance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: "cv_generation" }),
      });
    } catch {
      // best-effort
    }
    router.push(`/flow/${flowId}/cv`);
  }

  async function skipInterview() {
    setError("");
    await advanceToCV();
  }

  if (loading) return <div style={s.loading}>Starte Interview …</div>;

  return (
    <div style={s.layout}>
      <div style={s.main}>
        <div style={s.heading}>Gap-Interview</div>
        {gapsTotal > 0 && (
          <div style={s.progress}>
            Frage {gapsTotal - gapsRemaining + 1} von ~{gapsTotal} · {gapsRemaining} Lücken
            verbleibend
          </div>
        )}

        <div style={s.chatBox}>
          {messages.map((msg, i) => (
            <div key={i} style={s.bubble(msg.role)}>
              {msg.content}
            </div>
          ))}
          {sending && (
            <div style={s.bubble("assistant")}>
              <em>…</em>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {error && <div style={s.error}>{error}</div>}

        <div style={s.inputRow}>
          <textarea
            style={s.textarea}
            placeholder="Deine Antwort … (Enter zum Senden, Shift+Enter für neue Zeile)"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void sendAnswer();
              }
            }}
            disabled={sending}
            rows={2}
          />
          <button
            style={s.sendBtn(!answer.trim() || sending)}
            onClick={sendAnswer}
            disabled={!answer.trim() || sending}
          >
            Senden
          </button>
          <button style={s.skipBtn} onClick={skipInterview} disabled={sending}>
            Überspringen
          </button>
        </div>
      </div>

      {/* JD context sidebar */}
      <div style={s.sidebar}>
        <div style={s.sidebarTitle}>Stellenprofil</div>
        <span style={s.jdToggle} onClick={() => setShowJdContext((v) => !v)}>
          {showJdContext ? "Ausblenden" : "Einblenden"}
        </span>
        {showJdContext && flowState?.job_summary && (
          <>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>
              {flowState.job_summary.role_title}
            </div>
            {flowState.job_summary.required_skills?.map((skill) => (
              <span key={skill} style={s.sidebarTag}>
                {skill}
              </span>
            ))}
          </>
        )}
        {!showJdContext && (
          <div style={{ color: "#9ca3af", fontSize: 11 }}>
            Zeige die Stellenanforderungen zur Orientierung an.
          </div>
        )}
      </div>
    </div>
  );
}
