"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface StatCardProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number | string;
  label: string;
  icon?: React.ReactNode;
}

function StatCard({ value, label, icon, className, ...props }: StatCardProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg bg-white shadow-soft p-4 relative overflow-hidden",
        className
      )}
      {...props}
    >
      {/* Teal accent bar at top */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-teal rounded-t-lg" />
      
      {icon && (
        <div className="mb-2 text-teal">
          {icon}
        </div>
      )}
      
      <span className="text-2xl font-bold text-teal">
        {value}
      </span>
      
      <span className="text-xs text-gray-500 text-center mt-1">
        {label}
      </span>
    </div>
  );
}

export { StatCard };