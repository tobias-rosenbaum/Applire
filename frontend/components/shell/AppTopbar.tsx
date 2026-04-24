"use client";

import { usePathname, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";

interface AppTopbarProps {
  onSearchChange?: (q: string) => void;
  searchValue?: string;
  searchPlaceholder?: string;
  showSearch?: boolean;
}

const SECTION_KEYS: Record<string, string> = {
  "/dashboard": "dashboard",
  "/profile":   "profile",
  "/documents": "documents",
  "/settings":  "settings",
};

export function AppTopbar({
  onSearchChange,
  searchValue = "",
  searchPlaceholder,
  showSearch = false,
}: AppTopbarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const t = useTranslations("shell");

  const sectionKey = Object.keys(SECTION_KEYS).find((k) => pathname.startsWith(k));
  const sectionLabel = sectionKey
    ? t(SECTION_KEYS[sectionKey] as Parameters<typeof t>[0])
    : "";

  return (
    <header className="h-[52px] bg-white/90 backdrop-blur border-b border-gray-200 flex items-center px-6 gap-4 flex-shrink-0">
      {/* Breadcrumb */}
      <div className="flex items-center gap-1.5 flex-1 text-[13px] text-gray-400 font-manrope">
        <span>Applire</span>
        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>chevron_right</span>
        <span className="text-gray-900 font-bold">{sectionLabel}</span>
      </div>

      {/* Search — only shown when parent opts in */}
      {showSearch && (
        <div className="flex items-center gap-2 bg-[#f1f3ff] border border-gray-200 rounded-full px-3.5 py-1.5 w-52">
          <span className="material-symbols-outlined text-gray-400" style={{ fontSize: 16 }}>search</span>
          <input
            type="text"
            value={searchValue}
            onChange={(e) => onSearchChange?.(e.target.value)}
            placeholder={searchPlaceholder ?? ""}
            className="bg-transparent border-none outline-none text-[12.5px] text-gray-800 placeholder:text-gray-400 w-full"
          />
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button className="w-8 h-8 rounded-full flex items-center justify-center text-gray-600 hover:bg-[#f1f3ff] hover:text-[#003399] transition-colors">
          <span className="material-symbols-outlined" style={{ fontSize: 20 }}>notifications</span>
        </button>
        <button
          onClick={() => router.push("/settings")}
          className="w-[30px] h-[30px] rounded-full bg-gradient-to-br from-[#b5c4ff] to-[#dce1ff] flex items-center justify-center text-[12px] font-bold text-[#003399] cursor-pointer"
        >
          A
        </button>
      </div>
    </header>
  );
}
