"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Dashboard } from "@/components/dashboard/Dashboard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Dropzone } from "@/components/ui/dropzone";
import { FileChip } from "@/components/ui/file-chip";
import { useFileUpload } from "@/lib/hooks/use-file-upload";
import { cn } from "@/lib/utils";
import { ProcessingOverlay } from "@/components/processing-overlay";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

type JdMode = "url" | "text";

export default function Home() {
  const router = useRouter();
  const { files, addFiles, removeFile } = useFileUpload();
  const [jdMode, setJdMode] = useState<JdMode>("url");
  const [jdUrl, setJdUrl] = useState("");
  const [jdText, setJdText] = useState("");
  const [error, setError] = useState("");
  const [showOverlay, setShowOverlay] = useState(false);
  const [isReturningUser, setIsReturningUser] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);

  const hasFiles = files.length > 0;
  const canSubmit = hasFiles && !showOverlay;

  useEffect(() => {
    async function checkProfile() {
      try {
        const res = await fetch(`${API_BASE}/api/profile/exists`);
        if (res.ok) {
          const data = await res.json();
          setIsReturningUser(data.exists);
        } else {
          setIsReturningUser(false);
        }
      } catch {
        setIsReturningUser(false);
      } finally {
        setLoading(false);
      }
    }
    checkProfile();
  }, []);

  function handleSubmit() {
    if (!hasFiles) {
      setError("Please upload at least one CV to continue.");
      return;
    }
    setError("");
    setShowOverlay(true);
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-dim">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  // Returning user → Dashboard
  if (isReturningUser) {
    return <Dashboard />;
  }

  // New user → Screen 1 (CV upload + JD input)
  return (
    <div className="min-h-screen flex flex-col bg-surface-dim">
      {showOverlay && (
        <ProcessingOverlay
          files={files.map(({ file }) => file)}
          jdMode={jdMode}
          jdUrl={jdUrl}
          jdText={jdText}
          onCancel={() => setShowOverlay(false)}
        />
      )}
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
                Upload 2-4 CVs for the richest profile. We'll merge them automatically.
              </p>

              {/* Dropzone */}
              <Dropzone
                data-testid="upload-area"
                onDrop={(fileList) => addFiles(fileList)}
                accept=".pdf,.docx,.doc"
                multiple
                disabled={showOverlay}
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
                    disabled={showOverlay}
                  />
                ) : (
                  <textarea
                    className="flex min-h-[180px] w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm text-neutral-dark placeholder:text-gray-400 transition-colors focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/20 disabled:cursor-not-allowed disabled:opacity-50 resize-y"
                    placeholder="Paste the full job description here..."
                    value={jdText}
                    onChange={(e) => setJdText(e.target.value)}
                    disabled={showOverlay}
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
            <div data-testid="error-message" className="mt-6 p-4 rounded-lg bg-critical/10 border border-critical/20">
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
              data-testid="submit-button"
            >
              Analyze & Build Profile
            </Button>
            {!canSubmit && !showOverlay && (
              <p className="text-xs text-amber-600 mt-2">
                Upload at least one CV to continue
              </p>
            )}
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
