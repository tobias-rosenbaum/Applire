"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ApplicationCard } from "./ApplicationCard";
import { NewApplicationModal } from "./NewApplicationModal";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

interface ProfileExistsResponse {
  exists: boolean;
  completeness_score: number;
}

interface Application {
  id: string;
  role_title: string | null;
  company_name: string | null;
  workflow_status: string;
  user_status: string;
  flow_session_id: string | null;
  flow_current_step: string | null;
  updated_at: string;
  deadline: string | null;
  notes: string | null;
}

interface ProfileData {
  personal_info?: { name?: string; email?: string };
}

interface ProfileResponse {
  profile: ProfileData;
  completeness: number;
}

interface ApplicationsResponse {
  items: Application[];
  total: number;
}

export function Dashboard() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<ProfileExistsResponse | null>(null);
  const [profileFull, setProfileFull] = useState<ProfileResponse | null>(null);
  const [applications, setApplications] = useState<Application[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [showNewApplicationModal, setShowNewApplicationModal] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        const [existsRes, appsRes] = await Promise.all([
          fetch(`${API_BASE}/api/profile/exists`),
          fetch(`${API_BASE}/api/applications`),
        ]);

        let existsData: ProfileExistsResponse | null = null;
        if (existsRes.ok) {
          existsData = await existsRes.json();
          setProfile(existsData);
        }

        if (appsRes.ok) {
          const appsData: ApplicationsResponse = await appsRes.json();
          setApplications(appsData.items);
        }

        if (existsData?.exists) {
          const profileRes = await fetch(`${API_BASE}/api/profile`);
          if (profileRes.ok) {
            const profileData: ProfileResponse = await profileRes.json();
            setProfileFull(profileData);
          }
        }
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Server-side search via API q parameter
  useEffect(() => {
    async function searchApplications() {
      try {
        const url = searchQuery.trim()
          ? `${API_BASE}/api/applications?q=${encodeURIComponent(searchQuery)}`
          : `${API_BASE}/api/applications`;
        const res = await fetch(url);
        if (res.ok) {
          const data: ApplicationsResponse = await res.json();
          setApplications(data.items);
        }
      } catch (err) {
        console.error("Search failed:", err);
      }
    }
    const debounce = setTimeout(searchApplications, 300);
    return () => clearTimeout(debounce);
  }, [searchQuery]);

  const userName = profileFull?.profile?.personal_info?.name;
  const completenessScore = profile?.completeness_score ?? profileFull?.completeness ?? 0;

  const handleNewApplication = () => {
    setShowNewApplicationModal(true);
  };

  const handleNewApplicationSuccess = (_applicationId: string, flowId: string) => {
    setShowNewApplicationModal(false);
    // Navigate to the flow
    router.push(`/flow/${flowId}`);
  };

  const handleResume = (flowId: string) => {
    router.push(`/flow/${flowId}`);
  };

  const handleViewCV = (flowId: string) => {
    router.push(`/flow/${flowId}/cv`);
  };

  const handleResubmit = (flowId: string) => {
    router.push(`/flow/${flowId}/cv`);
  };

  const handleCardClick = (appId: string) => {
    router.push(`/applications/${appId}`);
  };

  const handleDeleteApplication = async (appId: string) => {
    if (!confirm("Remove this application from your pipeline? This cannot be undone.")) {
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/applications/${appId}`, {
        method: "DELETE",
      });
      if (res.ok || res.status === 204) {
        setApplications((prev) => prev.filter((app) => app.id !== appId));
      }
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-dim">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-surface-dim">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="font-heading text-2xl font-bold text-neutral-dark">Applire</h1>
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
              Profile: {Math.round(completenessScore * 100)}%
            </span>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Welcome Section */}
          <div className="mb-8">
            <h2 className="font-heading text-3xl font-bold text-neutral-dark mb-2">
              Welcome back{userName ? `, ${userName.split(" ")[0]}` : ""}
            </h2>
            <p className="text-gray-500">
              Manage your applications and tailor your CV for each role.
            </p>
          </div>

          {/* New Application CTA */}
          <div className="mb-8 flex justify-center">
            <Button size="lg" onClick={handleNewApplication} className="min-w-[200px]">
              + New Application
            </Button>
          </div>

          {/* Applications List */}
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-heading text-xl font-semibold text-neutral-dark">
              Active Applications ({applications.length})
            </h3>
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="text-sm px-3 py-1.5 rounded-lg border border-gray-300 focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/20"
            />
          </div>

          <div className="space-y-3">
            {applications.length === 0 ? (
              <Card className="p-8 text-center">
                <p className="text-gray-500 mb-4">
                  {searchQuery ? "No applications match your search." : "No applications yet."}
                </p>
                {!searchQuery && (
                  <Button onClick={handleNewApplication}>Create your first application</Button>
                )}
              </Card>
            ) : (
              applications.map((app) => (
                <ApplicationCard
                  key={app.id}
                  id={app.id}
                  roleTitle={app.role_title}
                  companyName={app.company_name}
                  workflowStatus={app.workflow_status}
                  userStatus={app.user_status}
                  flowCurrentStep={app.flow_current_step}
                  updatedAt={app.updated_at}
                  deadline={app.deadline}
                  onResume={() => app.flow_session_id && handleResume(app.flow_session_id!)}
                  onViewCV={() => app.flow_session_id && handleViewCV(app.flow_session_id!)}
                  onResubmit={() => app.flow_session_id && handleResubmit(app.flow_session_id!)}
                  onDelete={() => handleDeleteApplication(app.id)}
                  onClick={() => handleCardClick(app.id)}
                />
              ))
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto flex justify-center gap-6">
          <a href="/profile" className="text-sm text-teal hover:underline">
            My Profile
          </a>
          <a href="/settings" className="text-sm text-teal hover:underline">
            Settings
          </a>
          <a href="/help" className="text-sm text-gray-500 hover:underline">
            Help
          </a>
        </div>
      </footer>

      {/* New Application Modal */}
      {showNewApplicationModal && (
        <NewApplicationModal
          onClose={() => setShowNewApplicationModal(false)}
          onSuccess={handleNewApplicationSuccess}
        />
      )}
    </div>
  );
}
