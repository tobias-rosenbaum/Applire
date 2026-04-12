"use client";

import { createContext, useCallback, useContext, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

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
