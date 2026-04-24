"use client";

import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";

export type CardStatus = "in_progress" | "cv_ready" | "interrupted" | "tracking";

export interface DashboardApplicationCardProps {
  applicationId: string;
  roleTitle: string | null;
  companyName: string | null;
  workflowStatus: string;
  flowSessionId: string | null;
  updatedAt: string;
  onStartFlow?: () => void;
}

function deriveCardStatus(workflowStatus: string, updatedAt: string): CardStatus {
  if (workflowStatus === "completed") return "cv_ready";
  if (workflowStatus === "none") return "tracking";
  const hoursAgo = (Date.now() - new Date(updatedAt).getTime()) / 36e5;
  if (workflowStatus === "analyzing" || workflowStatus === "interviewing" || workflowStatus === "cv_generating") {
    return hoursAgo > 48 ? "interrupted" : "in_progress";
  }
  return "in_progress";
}

const PROGRESS: Record<CardStatus, number> = {
  in_progress: 50,
  cv_ready: 100,
  interrupted: 65,
  tracking: 0,
};

const CHIP: Record<CardStatus, { label: string; className: string }> = {
  in_progress:  { label: "In Progress",  className: "bg-[#e9edff] text-[#003399]" },
  cv_ready:     { label: "CV Ready",     className: "bg-[#dcfce7] text-[#166534]" },
  interrupted:  { label: "Interrupted",  className: "bg-[#fef9c3] text-[#854d0e]" },
  tracking:     { label: "Tracking",     className: "bg-[#f1f5f9] text-[#64748b]" },
};

const PROGRESS_COLOR: Record<CardStatus, string> = {
  in_progress: "bg-[#003399]",
  cv_ready:    "bg-[#22c55e]",
  interrupted: "bg-[#eab308]",
  tracking:    "bg-[#e2e5f0]",
};

export function DashboardApplicationCard({
  applicationId,
  roleTitle,
  companyName,
  workflowStatus,
  flowSessionId,
  updatedAt,
  onStartFlow,
}: DashboardApplicationCardProps) {
  const router = useRouter();
  const status = deriveCardStatus(workflowStatus, updatedAt);
  const chip = CHIP[status];
  const initial = (companyName ?? roleTitle ?? "?")[0].toUpperCase();

  const relativeTime = (() => {
    const h = Math.floor((Date.now() - new Date(updatedAt).getTime()) / 36e5);
    if (h < 1) return "just now";
    if (h < 24) return `${h}h ago`;
    return `${Math.floor(h / 24)}d ago`;
  })();

  function handleAction(e: React.MouseEvent) {
    e.stopPropagation();
    if (status === "tracking") {
      onStartFlow?.();
    } else if (flowSessionId) {
      const dest = status === "cv_ready" ? `/flow/${flowSessionId}/cv` : `/flow/${flowSessionId}/interview`;
      router.push(dest);
    }
  }

  const ACTION_LABEL: Record<CardStatus, string> = {
    in_progress: "Resume",
    cv_ready:    "Open",
    interrupted: "Continue",
    tracking:    "Start Flow",
  };

  return (
    <div
      className={cn(
        "bg-white rounded-xl border-[1.5px] p-4 cursor-pointer transition-all",
        status === "interrupted" ? "border-dashed border-gray-300" : "border-gray-200",
        status === "cv_ready" ? "border-green-200 bg-green-50/30" : "",
        "hover:shadow-md hover:border-[#b5c4ff]"
      )}
      onClick={() => router.push(`/applications/${applicationId}`)}
    >
      <div className="flex items-start justify-between mb-2.5">
        <div
          className={cn(
            "w-[34px] h-[34px] rounded-lg flex items-center justify-center text-[14px] font-extrabold font-manrope",
            status === "cv_ready"    ? "bg-[#e6f4ea] text-[#1e6b3a]" :
            status === "interrupted" ? "bg-[#fff3cc] text-[#584400]" :
            status === "tracking"    ? "bg-gray-100 text-gray-500" :
                                       "bg-[#eef1ff] text-[#003399]"
          )}
        >
          {initial}
        </div>
        <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide", chip.className)}>
          {chip.label}
        </span>
      </div>

      <p className="text-[14px] font-bold text-gray-900 font-manrope leading-snug truncate">
        {roleTitle ?? "Unknown role"}
      </p>
      <p className="text-[12px] text-gray-500 mt-0.5 truncate">{companyName ?? ""}</p>

      {/* Progress bar */}
      <div className="h-1 bg-gray-100 rounded-full mt-3 mb-3 overflow-hidden">
        <div
          className={cn("h-1 rounded-full", PROGRESS_COLOR[status])}
          style={{ width: `${PROGRESS[status]}%` }}
        />
      </div>

      <div className="flex items-center justify-between">
        <span className="text-[11.5px] text-gray-400">{relativeTime}</span>
        <button
          onClick={handleAction}
          className={cn(
            "text-[12px] font-bold px-3 py-1.5 rounded-lg flex items-center gap-1 transition-colors",
            status === "cv_ready"
              ? "bg-[#dcfce7] text-[#166534] hover:bg-[#bbf7d0]"
              : "bg-[#002068] text-white hover:bg-[#003399]"
          )}
        >
          <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
            {status === "cv_ready" ? "open_in_new" : status === "tracking" ? "bolt" : "play_arrow"}
          </span>
          {ACTION_LABEL[status]}
        </button>
      </div>
    </div>
  );
}
