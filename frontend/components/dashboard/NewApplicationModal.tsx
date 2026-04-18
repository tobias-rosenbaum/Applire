"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

type JdMode = "url" | "text";

interface NewApplicationModalProps {
  onClose: () => void;
  onSuccess: (applicationId: string, flowId: string) => void;
}

export function NewApplicationModal({ onClose, onSuccess }: NewApplicationModalProps) {
  const t = useTranslations("dashboard");
  const tCommon = useTranslations("common");
  const [jdMode, setJdMode] = useState<JdMode>("url");
  const [jdUrl, setJdUrl] = useState("");
  const [jdText, setJdText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const canSubmit = (jdMode === "url" && jdUrl.trim()) || (jdMode === "text" && jdText.trim());

  const handleSubmit = async () => {
    setLoading(true);
    setError("");

    try {
      // Step 1: Analyze JD
      const jdPayload =
        jdMode === "url"
          ? { url: jdUrl }
          : { text: jdText };

      const analyzeRes = await fetch(`${API_BASE}/api/job/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(jdPayload),
      });

      if (!analyzeRes.ok) {
        const err = await analyzeRes.json();
        setError(err.detail || t("analyzeError"));
        setLoading(false);
        return;
      }

      const jobData = await analyzeRes.json();
      const jobAnalysisId = jobData.id;

      // Step 2: Create application with workflow start
      const createRes = await fetch(`${API_BASE}/api/applications`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_analysis_id: jobAnalysisId,
          start_workflow: true,
        }),
      });

      if (!createRes.ok) {
        const err = await createRes.json();
        if (createRes.status === 409) {
          setError(t("duplicateApplication"));
        } else {
          setError(err.detail || t("createError"));
        }
        setLoading(false);
        return;
      }

      const applicationData = await createRes.json();
      const applicationId = applicationData.id;
      const flowId = applicationData.flow_session_id;

      onSuccess(applicationId, flowId);
    } catch (err) {
      console.error("New application failed:", err);
      setError("An unexpected error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-heading text-xl font-bold text-neutral-dark">
            {t("newApplication")}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            disabled={loading}
          >
            ✕
          </button>
        </div>

        <p className="text-sm text-gray-500 mb-6">
          {t("modalDescription")}
        </p>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-critical/10 border border-critical/20">
            <p className="text-sm text-critical">{error}</p>
          </div>
        )}

        {/* JD Input */}
        <div className="mb-6">
          {/* Tab toggle */}
          <div className="flex gap-1 mb-4 border-b border-gray-200">
            <button
              type="button"
              onClick={() => setJdMode("url")}
              className={cn(
                "px-4 py-2 text-sm font-medium transition-colors relative",
                jdMode === "url"
                  ? "text-teal"
                  : "text-gray-500 hover:text-neutral-dark"
              )}
            >
              {t("jdTabUrl")}
              {jdMode === "url" && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-teal" />
              )}
            </button>
            <button
              type="button"
              onClick={() => setJdMode("text")}
              className={cn(
                "px-4 py-2 text-sm font-medium transition-colors relative",
                jdMode === "text"
                  ? "text-teal"
                  : "text-gray-500 hover:text-neutral-dark"
              )}
            >
              {t("jdTabText")}
              {jdMode === "text" && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-teal" />
              )}
            </button>
          </div>

          {/* Tab content */}
          {jdMode === "url" ? (
            <Input
              type="url"
              placeholder="https://www.stepstone.de/..."
              value={jdUrl}
              onChange={(e) => setJdUrl(e.target.value)}
              disabled={loading}
            />
          ) : (
            <textarea
              className="flex min-h-[180px] w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm text-neutral-dark placeholder:text-gray-400 transition-colors focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/20 disabled:cursor-not-allowed disabled:opacity-50 resize-y"
              placeholder={t("jdPlaceholder")}
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              disabled={loading}
            />
          )}
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <Button variant="outline" onClick={onClose} disabled={loading}>
            {tCommon("cancel")}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!canSubmit || loading}
          >
            {loading ? t("analyzing") : t("startApplication")}
          </Button>
        </div>
      </Card>
    </div>
  );
}
