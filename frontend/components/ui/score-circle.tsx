"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface ScoreCircleProps extends React.HTMLAttributes<HTMLDivElement> {
  score: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
}

function getScoreColor(score: number): { ring: string; bg: string; label: string } {
  if (score >= 70) {
    return {
      ring: "text-success",
      bg: "bg-success",
      label: "Strong Fit",
    };
  }
  if (score >= 40) {
    return {
      ring: "text-warning",
      bg: "bg-warning",
      label: "Moderate Fit",
    };
  }
  return {
    ring: "text-critical",
    bg: "bg-critical",
    label: "Needs Work",
  };
}

function ScoreCircle({
  score,
  size = 100,
  strokeWidth = 8,
  label,
  className,
  ...props
}: ScoreCircleProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const colorConfig = getScoreColor(score);

  const [displayScore, setDisplayScore] = React.useState(0);

  React.useEffect(() => {
    const duration = 1000;
    const steps = 30;
    const increment = score / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= score) {
        setDisplayScore(score);
        clearInterval(timer);
      } else {
        setDisplayScore(current);
      }
    }, duration / steps);
    return () => clearInterval(timer);
  }, [score]);

  return (
    <div
      className={cn("relative inline-flex flex-col items-center justify-center", className)}
      style={{ width: size }}
      {...props}
    >
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          className="transform -rotate-90"
        >
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className="text-gray-200"
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className={cn(colorConfig.ring, "transition-all duration-500 ease-out")}
          />
        </svg>
        <div className={cn(
          "absolute inset-0 flex items-center justify-center rounded-full",
          colorConfig.bg
        )}>
          <span className="text-2xl font-bold text-white">
            {Math.round(displayScore)}%
          </span>
        </div>
      </div>
      <span className="text-xs font-semibold text-gray-600 mt-2">
        {label ?? colorConfig.label}
      </span>
    </div>
  );
}

export { ScoreCircle };