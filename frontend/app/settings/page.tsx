"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

function DefaultColorPicker() {
  const [hex, setHex] = useState("#2b5fa8");
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/settings`)
      .then((r) => r.json())
      .then((d) => { if (d.default_accent_hex) setHex(d.default_accent_hex); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    const res = await fetch(`${API_BASE}/api/settings`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ default_accent_hex: hex }),
    });
    if (res.ok) setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  if (loading) return <div className="h-8 w-32 bg-surface-container rounded animate-pulse" />;

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2 bg-surface-container border border-neutral-medium rounded px-2 py-1.5">
        <div className="w-5 h-5 rounded border border-neutral-medium" style={{ background: hex }} />
        <input
          type="text"
          value={hex}
          onChange={(e) => { if (/^#[0-9a-fA-F]{0,6}$/.test(e.target.value)) setHex(e.target.value); }}
          className="text-sm font-mono bg-transparent outline-none w-20"
          maxLength={7}
        />
      </div>
      <button
        type="button"
        onClick={handleSave}
        className="px-3 py-1.5 text-sm font-medium bg-teal text-white rounded hover:opacity-90"
      >
        {saved ? "Gespeichert ✓" : "Speichern"}
      </button>
    </div>
  );
}

export default function SettingsPage() {
  const router = useRouter();
  const [deleting, setDeleting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState("");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState("");

  const handleExport = async () => {
    setExporting(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/profile/export`);
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "applire-export.json";
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        const err = await res.json();
        setError(err.detail || "Export failed.");
      }
    } catch (err) {
      console.error("Export failed:", err);
      setError("Export failed. Please try again.");
    } finally {
      setExporting(false);
    }
  };

  const handleDelete = async () => {
    if (deleteConfirmation !== "DELETE") {
      setError('Please type "DELETE" to confirm.');
      return;
    }
    setDeleting(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/profile`, {
        method: "DELETE",
      });
      if (res.status === 202 || res.ok) {
        // Redirect to home after deletion
        router.push("/");
      } else {
        const err = await res.json();
        setError(err.detail || "Deletion failed.");
      }
    } catch (err) {
      console.error("Delete failed:", err);
      setError("Deletion failed. Please try again.");
    } finally {
      setDeleting(false);
      setShowDeleteConfirm(false);
      setDeleteConfirmation("");
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-surface-dim">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push("/")}
              className="text-sm text-teal hover:underline"
            >
              ← Back
            </button>
            <h1 className="font-heading text-2xl font-bold text-neutral-dark">Settings</h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          {error && (
            <div className="p-4 rounded-lg bg-critical/10 border border-critical/20">
              <p className="text-sm text-critical">{error}</p>
            </div>
          )}

          {/* GDPR Section */}
          <Card className="p-6">
            <h2 className="font-heading text-xl font-bold text-neutral-dark mb-4">
              Data & Privacy
            </h2>
            <p className="text-sm text-gray-500 mb-6">
              Manage your personal data in accordance with GDPR (Art. 17 & 20).
            </p>

            <div className="space-y-4">
              {/* Export Data */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <h3 className="font-medium text-neutral-dark">Export My Data</h3>
                  <p className="text-sm text-gray-500">
                    Download a complete JSON export of all your data (GDPR Art. 20).
                  </p>
                </div>
                <Button
                  variant="outline"
                  onClick={handleExport}
                  disabled={exporting}
                >
                  {exporting ? "Exporting..." : "Export"}
                </Button>
              </div>

              {/* Delete Data */}
              <div className="flex items-center justify-between p-4 bg-critical/5 rounded-lg border border-critical/20">
                <div>
                  <h3 className="font-medium text-critical">Delete All My Data</h3>
                  <p className="text-sm text-gray-500">
                    Permanently erase all your data, including applications, CVs, and profile (GDPR Art. 17).
                  </p>
                </div>
                <Button
                  variant="destructive"
                  onClick={() => setShowDeleteConfirm(true)}
                  disabled={deleting}
                >
                  Delete
                </Button>
              </div>
            </div>
          </Card>

          {/* Standard-Farbe für Lebensläufe */}
          <section className="rounded-lg border border-neutral-medium p-4">
            <h2 className="text-base font-semibold text-neutral-dark mb-1">
              Standard-Farbe für Lebensläufe
            </h2>
            <p className="text-sm text-neutral-medium mb-4">
              Wird verwendet, wenn keine Firmenfarbe erkannt werden kann.
            </p>
            <DefaultColorPicker />
          </section>

          {/* Delete Confirmation Dialog */}
          {showDeleteConfirm && (
            <Card className="p-6 border-2 border-critical/30">
              <h3 className="font-heading text-lg font-bold text-critical mb-2">
                Confirm Data Deletion
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                This action is <strong>irreversible</strong>. All your data will be permanently erased:
              </p>
              <ul className="text-sm text-gray-600 list-disc list-inside mb-4 space-y-1">
                <li>Master Profile and enrichment history</li>
                <li>All applications and their flow sessions</li>
                <li>Interview sessions and transcripts</li>
                <li>Generated CVs and uploaded files</li>
              </ul>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Type <code className="bg-gray-100 px-1 rounded">DELETE</code> to confirm:
                </label>
                <input
                  type="text"
                  value={deleteConfirmation}
                  onChange={(e) => setDeleteConfirmation(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-critical focus:outline-none focus:ring-2 focus:ring-critical/20"
                  placeholder="DELETE"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  variant="destructive"
                  onClick={handleDelete}
                  disabled={deleting || deleteConfirmation !== "DELETE"}
                >
                  {deleting ? "Deleting..." : "Confirm Delete"}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setDeleteConfirmation("");
                    setError("");
                  }}
                >
                  Cancel
                </Button>
              </div>
            </Card>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto flex justify-center gap-6">
          <a href="/" className="text-sm text-teal hover:underline">
            Dashboard
          </a>
          <a href="/profile" className="text-sm text-teal hover:underline">
            My Profile
          </a>
          <a href="/admin/appearance" className="text-sm text-teal hover:underline">
            Admin
          </a>
          <a href="/help" className="text-sm text-gray-500 hover:underline">
            Help
          </a>
        </div>
      </footer>
    </div>
  );
}
