"use client";

// Copyright (C) 2024-2026 Tobias Rosenbaum
//
// This file is part of Applire.
//
// Applire is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published
// by the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Applire is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with Applire. If not, see <https://www.gnu.org/licenses/>.


import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? (process.env.NODE_ENV === "development" ? "http://localhost:8001" : "");

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
    case 409:
      return detail ?? "This action conflicts with the current state.";
    case 422:
      return detail ?? "Invalid input. Please check your entries.";
    default:
      return detail ?? `An error occurred (${status}). Please try again.`;
  }
}

export interface FlowState {
  flow_id: string;
  user_type: "new" | "returning";
  current_step: string;
  available_actions: Record<string, string>;
  job_summary?: { role_title: string } | null;
  profile_completeness?: number | null;
  job_id?: string;
}

interface UseFlowReturn {
  flowId: string | null;
  currentStep: string | null;
  availableActions: Record<string, string>;
  userType: "new" | "returning" | null;
  jobSummary: { role_title: string } | null;
  profileCompleteness: number | null;
  jobId: string | null;
  isLoading: boolean;
  error: string | null;
  advance: (step: string, artifactId?: string) => Promise<FlowState | null>;
  refresh: () => Promise<void>;
}

export function useFlow(flowId: string | null): UseFlowReturn {
  const router = useRouter();
  const [state, setState] = useState<FlowState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!flowId) {
      setIsLoading(false);
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const res = await fetch(`${API_BASE}/api/flow/${flowId}/state`);
      if (!res.ok) {
        if (res.status === 404) {
          setError("Flow not found. Please start over.");
        } else {
          setError(translateError(res.status, await apiErrorMessage(res)));
        }
        return;
      }
      const data: FlowState = await res.json();
      setState(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error loading flow");
    } finally {
      setIsLoading(false);
    }
  }, [flowId]);

  const advance = useCallback(
    async (step: string, artifactId?: string): Promise<FlowState | null> => {
      if (!flowId) return null;

      setError(null);

      try {
        const res = await fetch(`${API_BASE}/api/flow/${flowId}/advance`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ step, artifact_id: artifactId ?? null }),
        });

        if (!res.ok) {
          const msg = await apiErrorMessage(res);
          throw new Error(translateError(res.status, msg));
        }

        const newState: FlowState = await res.json();
        setState(newState);
        return newState;
      } catch (e) {
        const errorMsg = e instanceof Error ? e.message : "Error advancing flow";
        setError(errorMsg);
        return null;
      }
    },
    [flowId]
  );

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    flowId,
    currentStep: state?.current_step ?? null,
    availableActions: state?.available_actions ?? {},
    userType: state?.user_type ?? null,
    jobSummary: state?.job_summary ?? null,
    profileCompleteness: state?.profile_completeness ?? null,
    jobId: state?.job_id ?? null,
    isLoading,
    error,
    advance,
    refresh,
  };
}

// Polling version for processing screen
interface UseFlowPollingReturn extends UseFlowReturn {
  isPolling: boolean;
  startPolling: () => void;
  stopPolling: () => void;
}

export function useFlowPolling(
  flowId: string | null,
  options?: {
    interval?: number;
    onComplete?: () => void;
    targetStep?: string;
  }
): UseFlowPollingReturn {
  const baseFlow = useFlow(flowId);
  const [isPolling, setIsPolling] = useState(false);

  const interval = options?.interval ?? 2000;
  const targetStep = options?.targetStep ?? "gap_analysis";

  useEffect(() => {
    if (!isPolling || !flowId) return;

    const pollTimer = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/flow/${flowId}/state`);
        if (!res.ok) return;

        const data: FlowState = await res.json();

        // Check if we've reached the target step
        if (data.current_step === targetStep || data.current_step === "gap_analysis") {
          clearInterval(pollTimer);
          setIsPolling(false);
          options?.onComplete?.();
        }
      } catch {
        // Silently continue polling on error
      }
    }, interval);

    return () => clearInterval(pollTimer);
  }, [flowId, isPolling, interval, targetStep, options]);

  const startPolling = useCallback(() => setIsPolling(true), []);
  const stopPolling = useCallback(() => setIsPolling(false), []);

  return {
    ...baseFlow,
    isPolling,
    startPolling,
    stopPolling,
  };
}