"use client";

import { useTranslations } from "next-intl";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const WORKFLOW_STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  analyzing: { label: "Analyzing", className: "bg-teal text-white" },
  interviewing: { label: "Interviewing", className: "bg-teal text-white" },
  cv_generating: { label: "Generating CV", className: "bg-teal text-white" },
  completed: { label: "CV Ready", className: "bg-success text-white" },
  none: { label: "Tracking", className: "bg-gray-400 text-white" },
};

const USER_STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  tracking: { label: "Tracking", className: "bg-gray-400 text-white" },
  applied: { label: "Applied", className: "bg-blue-500 text-white" },
  rejected: { label: "Rejected", className: "bg-critical text-white" },
  offer: { label: "Offer", className: "bg-success text-white" },
};

export interface ApplicationCardProps {
  id: string;
  roleTitle: string | null;
  companyName: string | null;
  workflowStatus: string;
  userStatus: string;
  flowCurrentStep: string | null;
  updatedAt: string;
  deadline?: string | null;
  onResume?: () => void;
  onViewCV?: () => void;
  onResubmit?: () => void;
  onDelete?: () => void;
  onClick?: () => void;
}

export function ApplicationCard({
  id,
  roleTitle,
  companyName,
  workflowStatus,
  userStatus,
  flowCurrentStep,
  updatedAt,
  deadline,
  onResume,
  onViewCV,
  onResubmit,
  onDelete,
  onClick,
}: ApplicationCardProps) {
  const t = useTranslations("dashboard");
  const workflowConfig = WORKFLOW_STATUS_CONFIG[workflowStatus] || WORKFLOW_STATUS_CONFIG.none;
  const userConfig = USER_STATUS_CONFIG[userStatus] || USER_STATUS_CONFIG.tracking;

  const showResume = flowCurrentStep && flowCurrentStep !== "complete";
  const showViewCV = workflowStatus === "completed";
  const showResubmit = workflowStatus === "completed";

  const daysUntilDeadline = deadline
    ? Math.ceil((new Date(deadline).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
    : null;

  return (
    <Card
      className={cn(
        "p-4 cursor-pointer transition-all duration-200 hover:shadow-card",
        "border border-gray-200 hover:border-teal/30"
      )}
      onClick={onClick}
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-heading text-base font-semibold text-neutral-dark truncate">
            {roleTitle || "Unbekannte Rolle"}
          </h3>
          {companyName && (
            <p className="text-sm text-gray-500 truncate">{companyName}</p>
          )}
        </div>

        <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
          <Badge className={workflowConfig.className}>
            {workflowConfig.label}
          </Badge>

          <Badge className={userConfig.className}>
            {userConfig.label}
          </Badge>

          {daysUntilDeadline !== null && daysUntilDeadline > 0 && (
            <span className="text-xs text-amber-600 whitespace-nowrap">
              {daysUntilDeadline} {daysUntilDeadline === 1 ? "day" : "days"} left
            </span>
          )}
          {daysUntilDeadline !== null && daysUntilDeadline <= 0 && (
            <span className="text-xs text-critical whitespace-nowrap">
              Deadline passed
            </span>
          )}

          <div className="flex items-center gap-1">
            {showResume && onResume && (
              <Button
                variant="secondary"
                size="sm"
                onClick={(e: React.MouseEvent) => {
                  e.stopPropagation();
                  onResume();
                }}
              >
                {t("resume")}
              </Button>
            )}
            {showViewCV && onViewCV && (
              <Button
                variant="outline"
                size="sm"
                onClick={(e: React.MouseEvent) => {
                  e.stopPropagation();
                  onViewCV();
                }}
              >
                View CV
              </Button>
            )}
            {showResubmit && onResubmit && (
              <Button
                variant="ghost"
                size="sm"
                onClick={(e: React.MouseEvent) => {
                  e.stopPropagation();
                  onResubmit();
                }}
              >
                Resubmit
              </Button>
            )}
            {onDelete && (
              <Button
                variant="ghost"
                size="sm"
                onClick={(e: React.MouseEvent) => {
                  e.stopPropagation();
                  onDelete();
                }}
                className="text-critical hover:text-critical/80"
              >
                🗑
              </Button>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
