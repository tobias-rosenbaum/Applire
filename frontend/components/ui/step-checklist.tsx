"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface StepItem {
  key: string;
  label: string;
  detail?: string;
}

export type StepState = "completed" | "in_progress" | "pending" | "skipped";

interface StepChecklistProps {
  steps: StepItem[];
  stepStates: Record<string, StepState>;
  className?: string;
}

function StepIcon({ state }: { state: StepState }) {
  if (state === "completed") {
    return (
      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-success text-white animate-[pop-in_0.2s_ease-out]">
        <svg
          className="h-4 w-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2.5}
            d="M5 13l4 4L19 7"
          />
        </svg>
      </div>
    );
  }

  if (state === "in_progress") {
    return (
      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 border-teal bg-transparent">
        <svg
          className="h-3 w-3 text-teal animate-spin"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
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
      </div>
    );
  }

  if (state === "skipped") {
    return (
      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-amber-100 border-2 border-amber-400">
        <svg
          className="h-3 w-3 text-amber-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2.5}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </div>
    );
  }

  return (
    <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 border-gray-300 bg-transparent" />
  );
}

export function StepChecklist({ steps, stepStates, className }: StepChecklistProps) {
  return (
    <div className={cn("space-y-4", className)}>
      {steps.map((step) => {
        const state = stepStates[step.key] || "pending";
        return (
          <div key={step.key} className="flex items-start gap-3">
            <StepIcon state={state} />
            <div className="flex-1 min-w-0">
              <p
                className={cn(
                  "text-sm transition-colors duration-200",
                  state === "completed" && "text-gray-500 line-through",
                  state === "in_progress" && "font-semibold text-neutral-dark",
                  state === "skipped" && "text-amber-600",
                  state === "pending" && "text-gray-400"
                )}
              >
                {step.label}
              </p>
              {step.detail && (state === "completed" || state === "skipped") && (
                <p className={cn(
                  "text-xs mt-0.5 animate-[fade-in_0.3s_ease-out]",
                  state === "skipped" ? "text-amber-600" : "text-gray-500"
                )}>
                  {step.detail}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}