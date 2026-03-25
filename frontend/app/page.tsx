"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Dropzone } from "@/components/ui/dropzone";
import { FileChip } from "@/components/ui/file-chip";
import { useFileUpload } from "@/lib/hooks/use-file-upload";
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

function translateError(status: number, detail?: string): string {
  switch (status) {
    case 504:
      return "This is taking longer than usual. Please try again.";
    case 503:
      return "Service temporarily busy. Please wait a moment and retry.";
    case 502:
      return "Could not parse this format. Please try a different file.";
    case 401:
      return "Session expired. Please refresh the page.";
    case 422:
      return detail ?? "Invalid input. Please check your entries.";
    default:
      return detail ?? `An error occurred (${status}). Please try again.`;
  }
}

type JdMode = "url" | "text";

export default function Home() {
  const router = useRouter();
  const { files, addFiles, removeFile, clear } = useFileUpload();
  const [jdMode, setJdMode] = useState<JdMode>("url");
  const [jdUrl, setJdUrl] = useState("");
  const [jdText, setJdText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const hasFiles = files.length > 0;
  const canSubmit = hasFiles && !loading;

  async function handleSubmit() {
    if (!hasFiles) {
      setError("Please upload at least one CV to continue.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      let jobId: string | null = null;

      // Step 1: Analyze JD if provided
      if (jdMode === "url" && jdUrl.trim()) {
        const jdRes = await fetch(`${API_BASE}/api/job/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: jdUrl.trim() }),
        });
        if (!jdRes.ok) {
          const msg = await apiErrorMessage(jdRes);
          throw new Error(jdRes.status === 504 ? translateError(504, msg) : msg);
        }
        const jdData = await jdRes.json();
        jobId = jdData.id;
      } else if (jdMode === "text" && jdText.trim()) {
        const jdRes = await fetch(`${API_BASE}/api/job/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: jdText }),
        });
        if (!jdRes.ok) {
          const msg = await apiErrorMessage(jdRes);
          throw new Error(jdRes.status === 504 ? translateError(504, msg) : msg);
        }
        const jdData = await jdRes.json();
        jobId = jdData.id;
      }

      // Step 2: Create flow session
      const flowRes = await fetch(`${API_BASE}/api/flow`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId }),
      });
      if (!flowRes.ok) {
        throw new Error(translateError(flowRes.status, await apiErrorMessage(flowRes)));
      }
      const flow = await flowRes.json();
      const flowId = flow.flow_id;

      // Step 3: Upload CVs
      for (const { file } of files) {
        const formData = new FormData();
        formData.append("file", file);
        
        const uploadRes = await fetch(`${API_BASE}/api/profile/upload`, {
          method: "POST",
          body: formData,
        });
        if (!uploadRes.ok) {
          throw new Error(translateError(uploadRes.status, await apiErrorMessage(uploadRes)));
        }
      }

      // Step 4: Navigate to processing screen
      router.push(`/flow/${flowId}/processing`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "An error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="font-heading text-2xl font-bold text-neutral-dark">Apliqa</h1>
          <p className="text-sm text-gray-500 hidden sm:block">
            AI-Powered CV Transformation
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 px-4 py-8 md:py-12">
        <div className="max-w-[900px] mx-auto">
          {/* Two-column grid */}
          <div className="grid grid-cols-1 md:grid-cols-[60%_40%] gap-6 md:gap-8">
            {/* Left Column - CV Upload */}
            <div>
              <h2 className="font-heading text-xl font-bold text-neutral-dark mb-1">
                Your CVs
              </h2>
              <p className="text-sm text-gray-500 mb-4">
                Upload 2-4 CVs for the richest profile. We&apos;ll merge them automatically.
              </p>

              {/* Dropzone */}
              <Dropzone
                onDrop={(fileList) => addFiles(fileList)}
                accept=".pdf,.docx,.doc"
                multiple
                disabled={loading}
              />

              {/* File chips */}
              {files.length > 0 && (
                <div className="mt-4 space-y-2">
                  {files.map(({ id, file }) => (
                    <FileChip
                      key={id}
                      filename={file.name}
                      size={file.size}
                      onRemove={() => removeFile(id)}
                    />
                  ))}
                  {files.length < 4 && (
                    <p className="text-xs text-gray-500 mt-2">
                      Add more files for a richer profile
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Right Column - JD Input */}
            <div>
              <h2 className="font-heading text-xl font-bold text-neutral-dark mb-1">
                Job Description
              </h2>
              <p className="text-sm text-gray-500 mb-4">
                Paste a JD so we can tailor your profile immediately.
              </p>

              <Card className="p-4">
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
                    URL
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
                    Paste Text
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
                    placeholder="Paste the full job description here..."
                    value={jdText}
                    onChange={(e) => setJdText(e.target.value)}
                    disabled={loading}
                  />
                )}

                <p className="text-xs italic text-gray-400 mt-3">
                  (Optional — you can add this later)
                </p>
              </Card>
            </div>
          </div>

          {/* Error message */}
          {error && (
            <div className="mt-6 p-4 rounded-lg bg-critical/10 border border-critical/20">
              <p className="text-sm text-critical">{error}</p>
            </div>
          )}

          {/* CTA Section */}
          <div className="mt-8 flex flex-col items-center">
            <Button
              size="lg"
              disabled={!canSubmit}
              onClick={handleSubmit}
              className="min-w-[240px]"
            >
              {loading ? (
                <>
                  <svg
                    className="animate-spin h-5 w-5 mr-2"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Processing...
                </>
              ) : (
                "Analyze & Build Profile"
              )}
            </Button>
            <p className="text-xs text-gray-500 mt-3">
              This usually takes about 30 seconds
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-sm text-gray-500">
            Precise. Confident. Future-Ready.
          </p>
        </div>
      </footer>
    </div>
  );
}