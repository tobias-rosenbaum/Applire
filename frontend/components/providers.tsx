"use client";

import { ErrorBoundary } from "@/components/error-boundary";
import { OfflineBanner } from "@/components/offline-banner";
import { ThemeProvider } from "@/components/theme-provider";
import { LocaleProvider } from "@/lib/providers/locale-provider";

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ThemeProvider>
      <LocaleProvider>
        <ErrorBoundary>
          <OfflineBanner />
          {children}
        </ErrorBoundary>
      </LocaleProvider>
    </ThemeProvider>
  );
}