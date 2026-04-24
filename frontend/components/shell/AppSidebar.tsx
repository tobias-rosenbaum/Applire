"use client";

import { usePathname, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";

interface NavItem {
  key: "dashboard" | "profile" | "documents" | "settings";
  href: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { key: "dashboard", href: "/dashboard", icon: "dashboard" },
  { key: "profile",   href: "/profile",   icon: "person_book" },
  { key: "documents", href: "/documents", icon: "description" },
  { key: "settings",  href: "/settings",  icon: "settings" },
];

interface AppSidebarProps {
  userName?: string | null;
}

export function AppSidebar({ userName }: AppSidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const t = useTranslations("shell");

  const initials = userName
    ? userName.split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase()
    : "?";

  return (
    <aside className="w-60 min-w-[240px] bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-[18px] border-b border-gray-100">
        <div className="w-[34px] h-[34px] rounded-[9px] bg-gradient-to-br from-[#003399] to-[#002068] flex items-center justify-center flex-shrink-0">
          <span className="material-symbols-outlined text-white" style={{ fontSize: 18 }}>view_cozy</span>
        </div>
        <span className="text-[16px] font-extrabold text-[#003399] tracking-tight font-manrope">
          Applire
        </span>
      </div>

      {/* User strip */}
      <div className="flex items-center gap-2.5 px-5 py-3 border-b border-gray-100">
        <div className="w-[34px] h-[34px] rounded-full bg-gradient-to-br from-[#b5c4ff] to-[#dce1ff] flex items-center justify-center text-[13px] font-bold text-[#003399] flex-shrink-0">
          {initials}
        </div>
        <div className="min-w-0">
          <p className="text-[13px] font-bold text-gray-900 truncate">
            {userName ?? "—"}
          </p>
          <p className="text-[11px] text-gray-400 mt-0.5">{t("userFreePlan")}</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-2.5 flex flex-col gap-0.5">
        {NAV_ITEMS.map(({ key, href, icon }) => {
          const active = pathname.startsWith(href);
          return (
            <button
              key={key}
              onClick={() => router.push(href)}
              className={cn(
                "flex items-center gap-2.5 w-full px-3 py-2.5 rounded-lg text-[13px] font-medium transition-colors text-left",
                active
                  ? "bg-[#eef1ff] text-[#003399] font-bold border-r-[3px] border-[#003399] rounded-r-none"
                  : "text-gray-600 hover:bg-[#f1f3ff] hover:text-[#003399]"
              )}
            >
              <span
                className="material-symbols-outlined flex-shrink-0"
                style={{ fontSize: 20, fontVariationSettings: active ? "'FILL' 1" : "'FILL' 0" }}
              >
                {icon}
              </span>
              {t(key)}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-gray-100">
        <button
          onClick={() => router.push("/help")}
          className="flex items-center gap-2 text-[12.5px] text-gray-400 hover:text-[#003399] transition-colors w-full"
        >
          <span className="material-symbols-outlined" style={{ fontSize: 18 }}>help</span>
          {t("help")}
        </button>
      </div>
    </aside>
  );
}
