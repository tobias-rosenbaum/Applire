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

interface GapAnalysis {
  id: string;
  match_score: number;
  category_a: string[];
  category_b: string[];
  category_c: string[];
  strengths: string[];
}

interface FlowState {
  job_id: string;
  user_type: "new" | "returning";
  available_actions: Record<string, string>;
  gap_summary?: { gap_analysis_id: string } | null;
}

const s = {
  heading: { fontSize: 20, fontWeight: 700, color: "#1a1a2e", marginBottom: 6 },
  sub: { fontSize: 13, color: "#6b7280", marginBottom: 24 },
  scoreRow: {
    display: "flex",
    alignItems: "center",
    gap: 16,
    marginBottom: 28,
    background: "#fff",
    borderRadius: 10,
    padding: 20,
    boxShadow: "0 1px 4px rgba(0,0,0,.08)",
  },
  scoreLabel: { fontSize: 13, color: "#6b7280", marginBottom: 4 },
  scoreValue: (score: number) => ({
    fontSize: 32,
    fontWeight: 700,
    color: score >= 0.7 ? "#16a34a" : score >= 0.4 ? "#ca8a04" : "#dc2626",
  }),
  scoreBar: {
    flex: 1,
    height: 10,
    background: "#e5e7eb",
    borderRadius: 5,
    overflow: "hidden" as const,
  },
  scoreBarFill: (score: number) => ({
    height: "100%",
    width: `${Math.round(score * 100)}%`,
    background: score >= 0.7 ? "#16a34a" : score >= 0.4 ? "#ca8a04" : "#dc2626",
    borderRadius: 5,
    transition: "width 0.4s ease",
  }),
  categoryGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr",
    gap: 16,
    marginBottom: 24,
  },
  card: (color: string) => ({
    background: "#fff",
    borderRadius: 10,
    padding: 20,
    boxShadow: "0 1px 4px rgba(0,0,0,.08)",
    borderTop: `3px solid ${color}`,
  }),
  cardTitle: { fontSize: 13, fontWeight: 700, marginBottom: 4 },
  cardSub: { fontSize: 11, color: "#6b7280", marginBottom: 12 },
  tagList: { display: "flex", flexWrap: "wrap" as const, gap: 6 },
  tag: (color: string, bg: string) => ({
    padding: "3px 10px",
    borderRadius: 12,
    fontSize: 12,
    background: bg,
    color,
    fontWeight: 500,
  }),
  empty: { fontSize: 12, color: "#9ca3af", fontStyle: "italic" as const },
  actions: { display: "flex", gap: 10, marginTop: 8 },
  btn: (variant: "primary" | "secondary") => ({
    padding: "10px 24px",
    borderRadius: 6,
    border: "none",
    cursor: "pointer",
    fontWeight: 600,
    fontSize: 13,
    background: variant === "primary" ? "#2563eb" : "#e5e7eb",
    color: variant === "primary" ? "#fff" : "#374151",
  }),
  loading: { fontSize: 14, color: "#6b7280", padding: "40px 0" },
  error: { color: "#dc2626", fontSize: 12, marginTop: 8 },
};

export default function GapsPage({
  params,
}: {
  params: Promise<{ flowId: string }>;
}) {
  const { flowId } = use(params);
  const router = useRouter();

  const [gaps, setGaps] = useState<GapAnalysis | null>(null);
  const [flowState, setFlowState] = useState<FlowState | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        // Load flow state to get job_id and check if gap analysis already done
        const fsRes = await fetch(`${API_BASE}/api/flow/${flowId}/state`);
        if (!fsRes.ok) throw new Error("Flow nicht gefunden");
        const fs: FlowState = await fsRes.json();
        setFlowState(fs);

        // Load gap analysis — either from flow's gap_summary or trigger fresh
        let gapData: GapAnalysis;
        if (fs.gap_summary?.gap_analysis_id) {
          // Already exists from import step — fetch it
          const gRes = await fetch(
            `${API_BASE}/api/job/${fs.job_id}/gaps`
          );
          if (gRes.ok) {
            gapData = await gRes.json();
          } else {
            // Fallback: re-run
            const postRes = await fetch(`${API_BASE}/api/job/${fs.job_id}/gaps`, {
              method: "POST",
            });
            if (!postRes.ok) throw new Error(await apiErrorMessage(postRes));
            gapData = await postRes.json();
          }
        } else {
          // Trigger gap analysis (returning user path — first time on gaps page)
          const postRes = await fetch(`${API_BASE}/api/job/${fs.job_id}/gaps`, {
            method: "POST",
          });
          if (!postRes.ok) throw new Error(await apiErrorMessage(postRes));
          gapData = await postRes.json();
        }
        setGaps(gapData);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Fehler beim Laden der Analyse");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [flowId]);

  async function advance(target: "interview" | "cv_generation") {
    if (!gaps) return;
    setError("");
    setActionLoading(true);
    try {
      const advRes = await fetch(`${API_BASE}/api/flow/${flowId}/advance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: target }),
      });
      if (!advRes.ok) {
        const errData = await advRes.json();
        throw new Error(
          errData.detail?.allowed_transitions
            ? `Ungültiger Schritt. Erlaubt: ${errData.detail.allowed_transitions.join(", ")}`
            : typeof errData.detail === "string"
            ? errData.detail
            : "Fehler"
        );
      }
      router.push(target === "interview" ? `/flow/${flowId}/interview` : `/flow/${flowId}/cv`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Fehler");
    } finally {
      setActionLoading(false);
    }
  }

  async function retryGapAnalysis() {
    if (!flowState) return;
    setError("");
    setLoading(true);
    try {
      const postRes = await fetch(`${API_BASE}/api/job/${flowState.job_id}/gaps`, {
        method: "POST",
      });
      if (!postRes.ok) throw new Error(await apiErrorMessage(postRes));
      setGaps(await postRes.json());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Fehler beim Laden der Analyse");
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div style={s.loading}>Analysiere Lücken …</div>;

  return (
    <div>
      <div style={s.heading}>Deine Übereinstimmung mit der Stelle</div>
      <div style={s.sub}>
        Kategorie A: direkte Übereinstimmung · B: wahrscheinlich vorhanden · C: unbekannt /
        Lücke
      </div>

      {gaps && (
        <>
          {/* Match score gauge */}
          <div style={s.scoreRow}>
            <div>
              <div style={s.scoreLabel}>Match-Score</div>
              <div style={s.scoreValue(gaps.match_score)}>
                {Math.round(gaps.match_score * 100)}%
              </div>
            </div>
            <div style={s.scoreBar}>
              <div style={s.scoreBarFill(gaps.match_score)} />
            </div>
          </div>

          {/* A / B / C category cards */}
          <div style={s.categoryGrid}>
            <div style={s.card("#16a34a")}>
              <div style={s.cardTitle}>A — Direkte Übereinstimmung</div>
              <div style={s.cardSub}>Klar nachgewiesen in deinem Profil</div>
              <div style={s.tagList}>
                {gaps.category_a.length > 0 ? (
                  gaps.category_a.map((item) => (
                    <span key={item} style={s.tag("#166534", "#dcfce7")}>
                      {item}
                    </span>
                  ))
                ) : (
                  <span style={s.empty}>Keine direkten Treffer</span>
                )}
              </div>
            </div>

            <div style={s.card("#ca8a04")}>
              <div style={s.cardTitle}>B — Wahrscheinlich vorhanden</div>
              <div style={s.cardSub}>Im Interview bestätigen</div>
              <div style={s.tagList}>
                {gaps.category_b.length > 0 ? (
                  gaps.category_b.map((item) => (
                    <span key={item} style={s.tag("#854d0e", "#fef9c3")}>
                      {item}
                    </span>
                  ))
                ) : (
                  <span style={s.empty}>Keine Einträge</span>
                )}
              </div>
            </div>

            <div style={s.card("#dc2626")}>
              <div style={s.cardTitle}>C — Lücken</div>
              <div style={s.cardSub}>Im Interview adressieren</div>
              <div style={s.tagList}>
                {gaps.category_c.length > 0 ? (
                  gaps.category_c.map((item) => (
                    <span key={item} style={s.tag("#991b1b", "#fee2e2")}>
                      {item}
                    </span>
                  ))
                ) : (
                  <span style={s.empty}>Keine offenen Lücken</span>
                )}
              </div>
            </div>
          </div>
        </>
      )}

      {error && (
        <div style={{ marginBottom: 16 }}>
          <div style={s.error}>{error}</div>
          {!gaps && (
            <button style={{ ...s.btn("secondary"), marginTop: 8 }} onClick={retryGapAnalysis}>
              Analyse wiederholen
            </button>
          )}
        </div>
      )}

      <div style={s.actions}>
        {/* Show "Start Interview" for new users with gaps, "Skip to CV" always available */}
        {flowState?.user_type === "new" && gaps && gaps.category_c.length > 0 && (
          <button
            style={s.btn("primary")}
            onClick={() => advance("interview")}
            disabled={actionLoading}
          >
            {actionLoading ? "…" : "Interview starten →"}
          </button>
        )}
        <button
          style={s.btn(
            flowState?.user_type === "returning" || !gaps?.category_c.length
              ? "primary"
              : "secondary"
          )}
          onClick={() => advance("cv_generation")}
          disabled={actionLoading}
        >
          {actionLoading ? "…" : "Direkt zum Lebenslauf →"}
        </button>
      </div>
    </div>
  );
}
