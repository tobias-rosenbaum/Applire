"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { use } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScoreCircle } from "@/components/ui/score-circle";
import { StatCard } from "@/components/ui/stat-card";
import { cn } from "@/lib/utils";

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
  job_summary?: { role_title: string } | null;
}

interface ProfileStats {
  positions: number;
  projects: number;
  certifications: number;
  data_points: number;
}

export default function GapsPage({
  params,
}: {
  params: Promise<{ flowId: string }>;
}) {
  const { flowId } = use(params);
  const router = useRouter();

  const [gaps, setGaps] = useState<GapAnalysis | null>(null);
  const [flowState, setFlowState] = useState<FlowState | null>(null);
  const [profileStats, setProfileStats] = useState<ProfileStats>({
    positions: 5,
    projects: 12,
    certifications: 3,
    data_points: 47,
  });
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        // Load flow state
        const fsRes = await fetch(`${API_BASE}/api/flow/${flowId}/state`);
        if (!fsRes.ok) throw new Error("Flow not found");
        const fs: FlowState = await fsRes.json();
        setFlowState(fs);

        // Load gap analysis
        let gapData: GapAnalysis;
        if (fs.gap_summary?.gap_analysis_id) {
          const gRes = await fetch(`${API_BASE}/api/job/${fs.job_id}/gaps`);
          if (gRes.ok) {
            gapData = await gRes.json();
          } else {
            const postRes = await fetch(`${API_BASE}/api/job/${fs.job_id}/gaps`, {
              method: "POST",
            });
            if (!postRes.ok) throw new Error(await apiErrorMessage(postRes));
            gapData = await postRes.json();
          }
        } else {
          const postRes = await fetch(`${API_BASE}/api/job/${fs.job_id}/gaps`, {
            method: "POST",
          });
          if (!postRes.ok) throw new Error(await apiErrorMessage(postRes));
          gapData = await postRes.json();
        }
        setGaps(gapData);

        // Fetch profile stats if available
        try {
          const profileRes = await fetch(`${API_BASE}/api/profile`);
          if (profileRes.ok) {
            const profileData = await profileRes.json();
            setProfileStats({
              positions: profileData.positions_count ?? 5,
              projects: profileData.projects_count ?? 12,
              certifications: profileData.certifications_count ?? 3,
              data_points: profileData.data_points_count ?? 47,
            });
          }
        } catch {
          // Keep default stats
        }
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load analysis");
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
      // For interview, we need to create an interview session first
      if (target === "interview") {
        const sessionRes = await fetch(`${API_BASE}/api/session`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            job_id: flowState?.job_id,
            mode: "quick",
          }),
        });
        if (!sessionRes.ok) {
          const errData = await sessionRes.json();
          throw new Error(
            typeof errData.detail === "string"
              ? errData.detail
              : "Failed to create interview session"
          );
        }
        const sessionData = await sessionRes.json();
        const sessionId = sessionData.id || sessionData.session_id;
        
        // Now advance with the session ID
        const advRes = await fetch(`${API_BASE}/api/flow/${flowId}/advance`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ step: target, artifact_id: sessionId }),
        });
        if (!advRes.ok) {
          const errData = await advRes.json();
          throw new Error(
            errData.detail?.allowed_transitions
              ? `Invalid step. Allowed: ${errData.detail.allowed_transitions.join(", ")}`
              : typeof errData.detail === "string"
              ? errData.detail
              : "Error"
          );
        }
        router.push(`/flow/${flowId}/interview`);
      } else {
        // cv_generation: the CV page generates the artifact and advances the flow itself
        router.push(`/flow/${flowId}/cv`);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
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
      setError(e instanceof Error ? e.message : "Failed to load analysis");
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div data-testid="loading-indicator" className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-teal border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-sm text-gray-500">Analyzing your profile...</p>
        </div>
      </div>
    );
  }

  const matchScore = gaps?.match_score ? Math.round(gaps.match_score * 100) : 0;
  const roleTitle = flowState?.job_summary?.role_title ?? "the target role";
  const gapCount = gaps?.category_c?.length ?? 0;

  return (
    <div data-testid="gap-analysis-page" className="max-w-4xl mx-auto">
      {/* Section 1: Master Profile Summary */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4">
          <div className="flex h-6 w-6 items-center justify-center rounded-full bg-success text-white">
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="font-heading text-xl font-bold text-neutral-dark">
            Master Profile Created
          </h2>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard value={profileStats.positions} label="Positions" />
          <StatCard value={profileStats.projects} label="Projects" />
          <StatCard value={profileStats.certifications} label="Certifications" />
          <StatCard value={profileStats.data_points} label="Data Points" />
        </div>
      </div>

      {/* Section 2: Match Score */}
      <Card className="p-6 mb-8">
        <div className="flex flex-col lg:flex-row items-center gap-6">
          <ScoreCircle score={matchScore} size={100} />
          
          <div className="flex-1 text-center lg:text-left">
            <h3 className="font-heading text-lg font-bold text-neutral-dark mb-2">
              {roleTitle}
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              Your profile matches {matchScore}% of this role&apos;s requirements.
            </p>

            {/* Category badges */}
            <div className="flex flex-wrap gap-2 justify-center lg:justify-start">
              {gaps?.category_a && gaps.category_a.length > 0 && (
                <Badge variant="success">
                  {gaps.category_a.length} direct matches
                </Badge>
              )}
              {gaps?.category_b && gaps.category_b.length > 0 && (
                <Badge variant="warning">
                  {gaps.category_b.length} likely matches
                </Badge>
              )}
              {gapCount > 0 && (
                <Badge variant="critical">
                  {gapCount} gaps to address
                </Badge>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Section 3: Gaps */}
      {gapCount > 0 && (
        <div data-testid="gaps-section" className="mb-8">
          <h3 className="font-heading text-lg font-bold text-neutral-dark mb-4">
            {gapCount} gap{gapCount !== 1 ? "s" : ""} identified:
          </h3>

          <div className="space-y-3">
            {gaps?.category_c?.map((gap, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="w-2 h-2 rounded-full bg-warning mt-2 shrink-0" />
                <div>
                  <p className="font-semibold text-neutral-dark">{gap}</p>
                  <p className="text-sm text-gray-500 italic mt-0.5">
                    We&apos;ll help you address this in the interview.
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Category details (expandable) */}
      <details className="mb-8">
        <summary className="cursor-pointer text-sm text-teal hover:underline mb-2">
          View detailed breakdown
        </summary>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          <Card className="p-4 border-t-4 border-t-success">
            <h4 className="font-semibold text-sm mb-2 text-success">A — Direct Match</h4>
            <div className="flex flex-wrap gap-1">
              {gaps?.category_a?.length ? (
                gaps.category_a.map((item, i) => (
                  <Badge key={i} variant="success" className="text-xs">{item}</Badge>
                ))
              ) : (
                <span className="text-xs text-gray-400 italic">None</span>
              )}
            </div>
          </Card>

          <Card className="p-4 border-t-4 border-t-warning">
            <h4 className="font-semibold text-sm mb-2 text-warning">B — Likely Match</h4>
            <div className="flex flex-wrap gap-1">
              {gaps?.category_b?.length ? (
                gaps.category_b.map((item, i) => (
                  <Badge key={i} variant="warning" className="text-xs">{item}</Badge>
                ))
              ) : (
                <span className="text-xs text-gray-400 italic">None</span>
              )}
            </div>
          </Card>

          <Card className="p-4 border-t-4 border-t-critical">
            <h4 className="font-semibold text-sm mb-2 text-critical">C — Gaps</h4>
            <div className="flex flex-wrap gap-1">
              {gaps?.category_c?.length ? (
                gaps.category_c.map((item, i) => (
                  <Badge key={i} variant="critical" className="text-xs">{item}</Badge>
                ))
              ) : (
                <span className="text-xs text-gray-400 italic">None</span>
              )}
            </div>
          </Card>
        </div>
      </details>

      {/* Error state */}
      {error && (
        <div data-testid="error-message" className="mb-6 p-4 rounded-lg bg-critical/10 border border-critical/20">
          <p className="text-sm text-critical">{error}</p>
          {!gaps && (
            <Button variant="outline" size="sm" onClick={retryGapAnalysis} className="mt-2">
              Retry Analysis
            </Button>
          )}
        </div>
      )}

      {/* CTAs */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-center">
        {flowState?.user_type === "new" && gapCount > 0 && (
          <div className="flex flex-col items-center">
            <Button
              size="lg"
              onClick={() => advance("interview")}
              disabled={actionLoading}
              className="min-w-[240px]"
              data-testid="interview-button"
            >
              Quick Interview (3 min)
            </Button>
            <p className="text-xs italic text-gray-500 mt-2">
              Answer a few questions to close the gaps
            </p>
          </div>
        )}

        <Button
          variant={flowState?.user_type === "returning" || gapCount === 0 ? "primary" : "secondary"}
          size="lg"
          onClick={() => advance("cv_generation")}
          disabled={actionLoading}
          className="min-w-[200px]"
          data-testid="generate-cv-button"
        >
          Generate CV Now
        </Button>

        <a
          href="#"
          className="text-sm text-teal underline hover:no-underline"
          onClick={(e) => e.preventDefault()}
        >
          Explore Profile
        </a>
      </div>
    </div>
  );
}