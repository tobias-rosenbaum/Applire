"use client";

import { ErrorBoundary } from "@/components/error-boundary";
import { OfflineBanner } from "@/components/offline-banner";
import { ThemeProvider } from "@/components/theme-provider";

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ThemeProvider>
      <ErrorBoundary>
        <OfflineBanner />
        {children}
      </ErrorBoundary>
    </ThemeProvider>
  );
}