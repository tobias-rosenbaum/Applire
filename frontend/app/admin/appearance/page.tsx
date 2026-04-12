"use client";

import { useRouter } from "next/navigation";
import { SchemeEditor } from "@/components/admin/scheme-editor";
import { ThemePreview } from "@/components/admin/theme-preview";

export default function AppearancePage() {
  const router = useRouter();
  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--color-surface-dim)" }}>
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center gap-4">
          <button
            onClick={() => router.push("/settings")}
            className="text-sm hover:underline"
            style={{ color: "var(--color-teal)" }}
          >
            ← Settings
          </button>
          <h1 className="text-2xl font-bold" style={{ color: "var(--color-neutral-dark, #2C3E50)" }}>
            Appearance
          </h1>
        </div>
      </header>

      <main className="flex-1 px-6 py-6">
        <div className="max-w-6xl mx-auto flex gap-5">
          <SchemeEditor />
          <ThemePreview />
        </div>
      </main>
    </div>
  );
}
