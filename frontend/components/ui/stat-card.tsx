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