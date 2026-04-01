"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

const USER_STATUS_OPTIONS = [
  { value: "tracking", label: "Tracking", className: "bg-gray-400 text-white" },
  { value: "applied", label: "Applied", className: "bg-blue-500 text-white" },
  { value: "rejected", label: "Rejected", className: "bg-critical text-white" },
  { value: "offer", label: "Offer", className: "bg-success text-white" },
];

const WORKFLOW_STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  analyzing: { label: "Analyzing", className: "bg-teal text-white" },
  interviewing: { label: "Interviewing", className: "bg-teal text-white" },
  cv_generating: { label: "Generating CV", className: "bg-teal text-white" },
  completed: { label: "CV Ready", className: "bg-success text-white" },
  none: { label: "Tracking", className: "bg-gray-400 text-white" },
};

interface ApplicationDetail {
  id: string;
  role_title: string | null;
  company_name: string | null;
  workflow_status: string;
  user_status: string;
  notes: string | null;
  applied_at: string | null;
  deadline: string | null;
  flow_session_id: string | null;
  flow_current_step: string | null;
  created_at: string;
  updated_at: string;
}

export default function ApplicationDetailPage() {
  const router = useRouter();
  const params = useParams();
  const appId = params.appId as string;

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [application, setApplication] = useState<ApplicationDetail | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Editable fields
  const [userStatus, setUserStatus] = useState("");
  const [notes, setNotes] = useState("");
  const [deadline, setDeadline] = useState("");

  useEffect(() => {
    async function loadApplication() {
      try {
        const res = await fetch(`${API_BASE}/api/applications/${appId}`);
        if (res.ok) {
          const data: ApplicationDetail = await res.json();
          setApplication(data);
          setUserStatus(data.user_status);
          setNotes(data.notes || "");
          setDeadline(data.deadline ? data.deadline.slice(0, 16) : "");
        } else {
          setError("Application not found.");
        }
      } catch (err) {
        console.error("Failed to load application:", err);
        setError("Failed to load application data.");
      } finally {
        setLoading(false);
      }
    }
    loadApplication();
  }, [appId]);

  const handleSave = async () => {
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const payload: Record<string, unknown> = {};
      if (userStatus) payload.user_status = userStatus;
      if (notes !== application?.notes) payload.notes = notes || null;
      if (deadline) {
        payload.deadline = new Date(deadline).toISOString();
      } else if (application?.deadline) {
        payload.deadline = null;
      }

      if (Object.keys(payload).length === 0) {
        setSuccess("No changes to save.");
        setSaving(false);
        return;
      }

      const res = await fetch(`${API_BASE}/api/applications/${appId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const updated: ApplicationDetail = await res.json();
        setApplication(updated);
        setSuccess("Changes saved successfully.");
      } else {
        const err = await res.json();
        setError(err.detail || "Failed to save changes.");
      }
    } catch (err) {
      console.error("Save failed:", err);
      setError("Failed to save changes.");
    } finally {
      setSaving(false);
    }
  };

  const handleResume = () => {
    if (application?.flow_session_id) {
      router.push(`/flow/${application.flow_session_id}`);
    }
  };

  const handleViewCV = () => {
    if (application?.flow_session_id) {
      router.push(`/flow/${application.flow_session_id}/cv`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-dim">
        <p className="text-gray-500">Loading application details...</p>
      </div>
    );
  }

  if (error && !application) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-surface-dim">
        <p className="text-critical mb-4">{error}</p>
        <Button onClick={() => router.push("/")}>Back to Dashboard</Button>
      </div>
    );
  }

  if (!application) return null;

  const workflowConfig = WORKFLOW_STATUS_CONFIG[application.workflow_status] || WORKFLOW_STATUS_CONFIG.none;
  const daysUntilDeadline = application.deadline
    ? Math.ceil((new Date(application.deadline).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
    : null;

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
              ← Back to Dashboard
            </button>
            <h1 className="font-heading text-2xl font-bold text-neutral-dark">
              {application.role_title || "Unbekannte Rolle"}
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Badge className={workflowConfig.className}>
              {workflowConfig.label}
            </Badge>
            <Badge className={USER_STATUS_OPTIONS.find(s => s.value === userStatus)?.className || "bg-gray-400 text-white"}>
              {USER_STATUS_OPTIONS.find(s => s.value === userStatus)?.label || userStatus}
            </Badge>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Success/Error Messages */}
          {success && (
            <div className="p-4 rounded-lg bg-success/10 border border-success/20">
              <p className="text-sm text-success">{success}</p>
            </div>
          )}
          {error && (
            <div className="p-4 rounded-lg bg-critical/10 border border-critical/20">
              <p className="text-sm text-critical">{error}</p>
            </div>
          )}

          {/* Company Info */}
          <Card className="p-6">
            <h2 className="font-heading text-xl font-bold text-neutral-dark mb-4">
              Company & Role
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">Company</label>
                <p className="text-base text-neutral-dark mt-1">
                  {application.company_name || "—"}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Role</label>
                <p className="text-base text-neutral-dark mt-1">
                  {application.role_title || "—"}
                </p>
              </div>
            </div>
          </Card>

          {/* Status Management */}
          <Card className="p-6">
            <h2 className="font-heading text-xl font-bold text-neutral-dark mb-4">
              Status Management
            </h2>
            <div className="space-y-4">
              {/* User Status Dropdown */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Application Status
                </label>
                <select
                  value={userStatus}
                  onChange={(e) => setUserStatus(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/20"
                >
                  {USER_STATUS_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Deadline */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Deadline
                </label>
                <Input
                  type="datetime-local"
                  value={deadline}
                  onChange={(e) => setDeadline(e.target.value)}
                  className="max-w-xs"
                />
                {daysUntilDeadline !== null && (
                  <p className={cn(
                    "text-xs mt-1",
                    daysUntilDeadline > 0 ? "text-gray-500" : "text-critical"
                  )}>
                    {daysUntilDeadline > 0
                      ? `${daysUntilDeadline} ${daysUntilDeadline === 1 ? "day" : "days"} remaining`
                      : "Deadline has passed"}
                  </p>
                )}
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes
                </label>
                <textarea
                  className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm min-h-[100px] focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/20"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add notes about this application..."
                />
              </div>

              {/* Save Button */}
              <div className="flex justify-end">
                <Button onClick={handleSave} disabled={saving}>
                  {saving ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </div>
          </Card>

          {/* Flow Progress */}
          {application.flow_session_id && (
            <Card className="p-6">
              <h2 className="font-heading text-xl font-bold text-neutral-dark mb-4">
                Flow Progress
              </h2>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Current Step</span>
                  <span className="text-sm font-medium text-neutral-dark">
                    {application.flow_current_step || "—"}
                  </span>
                </div>
                <div className="flex gap-2">
                  {application.flow_current_step && application.flow_current_step !== "complete" && (
                    <Button variant="secondary" onClick={handleResume}>
                      Resume Flow
                    </Button>
                  )}
                  {application.workflow_status === "completed" && (
                    <Button variant="outline" onClick={handleViewCV}>
                      View CV
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          )}

          {/* Metadata */}
          <Card className="p-6">
            <h2 className="font-heading text-xl font-bold text-neutral-dark mb-4">
              Details
            </h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <label className="text-gray-500">Created</label>
                <p className="text-neutral-dark mt-1">
                  {new Date(application.created_at).toLocaleDateString()}
                </p>
              </div>
              <div>
                <label className="text-gray-500">Last Updated</label>
                <p className="text-neutral-dark mt-1">
                  {new Date(application.updated_at).toLocaleDateString()}
                </p>
              </div>
              {application.applied_at && (
                <div>
                  <label className="text-gray-500">Applied At</label>
                  <p className="text-neutral-dark mt-1">
                    {new Date(application.applied_at).toLocaleDateString()}
                  </p>
                </div>
              )}
            </div>
          </Card>
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
          <a href="/settings" className="text-sm text-teal hover:underline">
            Settings
          </a>
        </div>
      </footer>
    </div>
  );
}
