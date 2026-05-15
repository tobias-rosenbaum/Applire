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


import { createContext, useCallback, useContext, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? (process.env.NODE_ENV === "development" ? "http://localhost:8001" : "");

interface ThemeContextValue {
  /** Call after activating a scheme to propagate it immediately without a page reload. */
  refreshTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({ refreshTheme: () => {} });

export function useTheme(): ThemeContextValue {
  return useContext(ThemeContext);
}

async function applyActiveScheme(): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/api/admin/color-schemes/active`);
    if (!res.ok) return; // fall back to globals.css static values
    const data = await res.json();
    const derived: Record<string, string> = data.derived;
    for (const [key, value] of Object.entries(derived)) {
      document.documentElement.style.setProperty(key, value);
    }
  } catch {
    // Network error or server not ready — globals.css fallback remains active
  }
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const refreshTheme = useCallback(() => {
    applyActiveScheme();
  }, []);

  useEffect(() => {
    applyActiveScheme();
  }, []);

  return (
    <ThemeContext.Provider value={{ refreshTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
