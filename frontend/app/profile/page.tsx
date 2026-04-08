"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { PhotoManager } from "@/components/profile/PhotoManager";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

interface ProfileSection {
  name?: string;
  email?: string;
  phone?: string;
  location?: string;
  summary?: string;
  work_experience?: Array<{
    title?: string;
    company?: string;
    start_date?: string;
    end_date?: string;
    description?: string;
  }>;
  education?: Array<{
    degree?: string;
    institution?: string;
    year?: string;
  }>;
  skills?: string[];
  languages?: Array<{ name?: string; level?: string }>;
  certifications?: Array<{ name?: string; issuer?: string; year?: string }>;
  photo_url?: string | null;
}

interface EnrichmentRecord {
  timestamp: string;
  source: string;
  changes: Array<{ section: string; field: string; action: string }>;
}

interface ProfileResponse {
  id: string;
  profile: {
    personal_info?: ProfileSection;
    professional_summary?: string;
    work_experience?: ProfileSection["work_experience"];
    education?: ProfileSection["education"];
    skills?: ProfileSection["skills"];
    languages?: ProfileSection["languages"];
    certifications?: ProfileSection["certifications"];
  };
  completeness: number;
  merge_conflicts: Array<{
    conflict_id: string;
    section: string;
    field: string;
    source: string;
  }>;
  created_at: string;
  updated_at: string;
}

type SectionKey =
  | "personal_info"
  | "professional_summary"
  | "work_experience"
  | "education"
  | "skills"
  | "languages"
  | "certifications";

const SECTION_LABELS: Record<SectionKey, string> = {
  personal_info: "Personal Info",
  professional_summary: "Professional Summary",
  work_experience: "Work Experience",
  education: "Education",
  skills: "Skills",
  languages: "Languages",
  certifications: "Certifications",
};

export default function ProfilePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [enrichmentHistory, setEnrichmentHistory] = useState<EnrichmentRecord[]>([]);
  const [editingSection, setEditingSection] = useState<SectionKey | null>(null);
  const [editValue, setEditValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [profilePhotoUrl, setProfilePhotoUrl] = useState<string | null>(null);

  useEffect(() => {
    async function loadProfile() {
      try {
        const [profileRes, enrichmentRes] = await Promise.all([
          fetch(`${API_BASE}/api/profile`),
          fetch(`${API_BASE}/api/profile/enrichment-history`),
        ]);

        if (profileRes.ok) {
          const data: ProfileResponse = await profileRes.json();
          setProfile(data);
          setProfilePhotoUrl(
            data.profile.personal_info?.photo_url ?? null
          );
        } else {
          setError("No profile found. Please import a CV first.");
        }

        if (enrichmentRes.ok) {
          const data: EnrichmentRecord[] = await enrichmentRes.json();
          setEnrichmentHistory(data.slice(-10).reverse());
        }
      } catch (err) {
        console.error("Failed to load profile:", err);
        setError("Failed to load profile data.");
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, []);

  const handleEdit = (section: SectionKey) => {
    if (!profile) return;
    const value = profile.profile[section];
    setEditValue(typeof value === "string" ? value : JSON.stringify(value, null, 2));
    setEditingSection(section);
  };

  const handleSave = async () => {
    if (!profile || !editingSection) return;
    setSaving(true);
    try {
      let parsed: unknown;
      try {
        parsed = JSON.parse(editValue);
      } catch {
        parsed = editValue;
      }

      const res = await fetch(`${API_BASE}/api/profile/${editingSection}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed),
      });

      if (res.ok) {
        const updated: ProfileResponse = await res.json();
        setProfile(updated);
        setEditingSection(null);
        setEditValue("");
      } else {
        const err = await res.json();
        setError(err.detail || "Failed to save section.");
      }
    } catch (err) {
      console.error("Save failed:", err);
      setError("Failed to save section.");
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditingSection(null);
    setEditValue("");
  };

  const completenessScore = profile?.completeness ?? 0;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-dim">
        <p className="text-gray-500">Loading profile...</p>
      </div>
    );
  }

  if (error && !profile) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-surface-dim">
        <p className="text-critical mb-4">{error}</p>
        <Button onClick={() => router.push("/")}>Back to Home</Button>
      </div>
    );
  }

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
            <h1 className="font-heading text-2xl font-bold text-neutral-dark">My Profile</h1>
          </div>
          {profile && (
            <span
              className={cn(
                "text-xs font-medium px-3 py-1 rounded-full",
                completenessScore >= 0.8
                  ? "bg-success text-white"
                  : completenessScore >= 0.5
                  ? "bg-warning text-white"
                  : "bg-gray-400 text-white"
              )}
            >
              {Math.round(completenessScore * 100)}% Complete
            </span>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-4">
          {error && (
            <div className="p-4 rounded-lg bg-critical/10 border border-critical/20">
              <p className="text-sm text-critical">{error}</p>
            </div>
          )}

          {/* Photo Section */}
          <Card className="p-4">
            <PhotoManager
              currentPhotoUrl={profilePhotoUrl}
              onPhotoChange={(url) => setProfilePhotoUrl(url)}
            />
          </Card>

          {/* Profile Sections */}
          {(Object.keys(SECTION_LABELS) as SectionKey[]).map((section) => {
            const isEditing = editingSection === section;
            const value = profile?.profile[section];
            const hasValue = value !== undefined && value !== null && value !== "";

            return (
              <Card key={section} className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-heading text-base font-semibold text-neutral-dark">
                    {SECTION_LABELS[section]}
                  </h3>
                  {!isEditing && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEdit(section)}
                    >
                      Edit
                    </Button>
                  )}
                </div>

                {isEditing ? (
                  <div className="space-y-3">
                    <textarea
                      className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm text-neutral-dark min-h-[120px] focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/20"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                    />
                    <div className="flex gap-2">
                      <Button onClick={handleSave} disabled={saving}>
                        {saving ? "Saving..." : "Save"}
                      </Button>
                      <Button variant="outline" onClick={handleCancel}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-gray-700">
                    {hasValue ? (
                      typeof value === "string" ? (
                        <p>{value}</p>
                      ) : (
                        <pre className="whitespace-pre-wrap text-xs bg-gray-50 p-3 rounded">
                          {JSON.stringify(value, null, 2)}
                        </pre>
                      )
                    ) : (
                      <p className="text-gray-400 italic">Not provided</p>
                    )}
                  </div>
                )}
              </Card>
            );
          })}

          {/* Enrichment History */}
          {enrichmentHistory.length > 0 && (
            <Card className="p-4 mt-6">
              <h3 className="font-heading text-base font-semibold text-neutral-dark mb-4">
                Enrichment History
              </h3>
              <div className="space-y-2">
                {enrichmentHistory.map((record, idx) => (
                  <div
                    key={idx}
                    className="text-sm p-3 bg-gray-50 rounded border border-gray-200"
                  >
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span className="font-medium text-teal">{record.source}</span>
                      <span>{new Date(record.timestamp).toLocaleDateString()}</span>
                    </div>
                    {record.changes.map((change, cIdx) => (
                      <p key={cIdx} className="text-gray-600">
                        {change.action}: {change.section}/{change.field}
                      </p>
                    ))}
                  </div>
                ))}
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
          <a href="/settings" className="text-sm text-teal hover:underline">
            Settings
          </a>
          <a href="/help" className="text-sm text-gray-500 hover:underline">
            Help
          </a>
        </div>
      </footer>
    </div>
  );
}
