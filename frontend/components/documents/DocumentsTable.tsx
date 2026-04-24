"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";

export interface DocumentItem {
  cv_id: string;
  flow_id: string | null;
  role_title: string | null;
  company_name: string | null;
  template: string;
  status: "ready" | "generating" | "expired" | "pending" | "failed";
  created_at: string;
  expires_at: string;
}

type StatusFilter = "all" | "ready" | "generating" | "expiring";
type SortMode = "newest" | "oldest" | "company";

const TEMPLATE_LABELS: Record<string, string> = {
  classic_german:   "Classic German",
  modern_swiss:     "Modern Swiss",
  executive:        "Executive",
  tech_developer:   "Tech Developer",
  creative_sidebar: "Creative Sidebar",
  academic:         "Academic",
  compact_pro:      "Compact Pro",
};

function daysUntilExpiry(expiresAt: string): number {
  return Math.ceil((new Date(expiresAt).getTime() - Date.now()) / 864e5);
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("de-DE", { day: "numeric", month: "short", year: "numeric" });
}

interface DocumentsTableProps {
  items: DocumentItem[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (p: number) => void;
}

export function DocumentsTable({ items, total, page, pageSize, onPageChange }: DocumentsTableProps) {
  const t = useTranslations("documents");
  const router = useRouter();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [sort, setSort] = useState<SortMode>("newest");

  const filtered = useMemo(() => {
    let rows = [...items];

    if (statusFilter === "ready")      rows = rows.filter((r) => r.status === "ready");
    if (statusFilter === "generating") rows = rows.filter((r) => r.status === "generating" || r.status === "pending");
    if (statusFilter === "expiring")   rows = rows.filter((r) => r.status === "ready" && daysUntilExpiry(r.expires_at) <= 7);

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      rows = rows.filter(
        (r) =>
          (r.role_title ?? "").toLowerCase().includes(q) ||
          (r.company_name ?? "").toLowerCase().includes(q)
      );
    }

    if (sort === "oldest")  rows.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    if (sort === "company") rows.sort((a, b) => (a.company_name ?? "").localeCompare(b.company_name ?? ""));

    return rows;
  }, [items, statusFilter, searchQuery, sort]);

  const totalPages = Math.ceil(total / pageSize);
  const from = (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div>
      {/* Filter bar */}
      <div className="flex items-center gap-2.5 mb-3.5 flex-wrap">
        {(["all", "ready", "generating", "expiring"] as StatusFilter[]).map((f) => (
          <button
            key={f}
            onClick={() => setStatusFilter(f)}
            className={cn(
              "px-3.5 py-1 rounded-full text-[12px] font-bold border-[1.5px] transition-colors",
              statusFilter === f
                ? "bg-[#003399] text-white border-[#003399]"
                : "bg-white text-gray-500 border-gray-200 hover:border-[#b5c4ff] hover:text-[#003399]"
            )}
          >
            {t(f === "all" ? "filterAll" : f === "ready" ? "filterReady" : f === "generating" ? "filterGenerating" : "filterExpiring")}
          </button>
        ))}

        {/* Text search */}
        <div className="flex items-center gap-1.5 bg-white border-[1.5px] border-gray-200 rounded-full px-3.5 py-1 focus-within:border-[#003399] transition-all">
          <span className="material-symbols-outlined text-gray-400" style={{ fontSize: 15 }}>search</span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={t("searchPlaceholder")}
            className="border-none outline-none bg-transparent text-[12px] text-gray-800 placeholder:text-gray-400 w-36"
          />
        </div>

        <div className="flex-1" />

        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as SortMode)}
          className="text-[12px] text-gray-500 border-[1.5px] border-gray-200 rounded-lg px-2.5 py-1 bg-white outline-none cursor-pointer"
        >
          <option value="newest">{t("sortNewest")}</option>
          <option value="oldest">{t("sortOldest")}</option>
          <option value="company">{t("sortCompany")}</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-[14px] border-[1.5px] border-gray-200 overflow-hidden">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-[#f9f9ff] border-b-[1.5px] border-gray-100">
              <th className="text-left px-4 py-2.5 text-[11px] font-bold text-gray-500 uppercase tracking-wider">{t("colDocument")}</th>
              <th className="text-left px-4 py-2.5 text-[11px] font-bold text-gray-500 uppercase tracking-wider">{t("colTemplate")}</th>
              <th className="text-left px-4 py-2.5 text-[11px] font-bold text-gray-500 uppercase tracking-wider">{t("colStatus")}</th>
              <th className="text-left px-4 py-2.5 text-[11px] font-bold text-gray-500 uppercase tracking-wider">{t("colExpires")}</th>
              <th className="px-4 py-2.5" />
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center py-12 text-[13px] text-gray-400">
                  {t("noDocuments")}
                </td>
              </tr>
            ) : (
              filtered.map((item) => {
                const days = daysUntilExpiry(item.expires_at);
                const isReady = item.status === "ready";
                const isGenerating = item.status === "generating" || item.status === "pending";
                return (
                  <tr
                    key={item.cv_id}
                    className="border-b border-gray-50 last:border-none hover:bg-[#f5f7ff] transition-colors cursor-pointer"
                  >
                    <td className="px-4 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          "w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0",
                          isGenerating ? "bg-amber-50" : "bg-[#e9edff]"
                        )}>
                          <span
                            className="material-symbols-outlined"
                            style={{ fontSize: 20, color: isGenerating ? "#8b5000" : "#003399" }}
                          >
                            description
                          </span>
                        </div>
                        <div>
                          <p className="text-[13.5px] font-semibold text-gray-900 leading-tight">
                            {item.role_title ?? "Unknown role"}
                          </p>
                          <p className="text-[11.5px] text-gray-500 mt-0.5">
                            {item.company_name ?? ""} · {t("generatedOn", { date: formatDate(item.created_at) })}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="text-[11px] font-semibold px-2 py-1 rounded-md bg-[#f1f3ff] text-gray-600">
                        {TEMPLATE_LABELS[item.template] ?? item.template}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      {isReady && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-1 rounded-full bg-[#e6f4ea] text-[#1e6b3a]">
                          <span className="material-symbols-outlined" style={{ fontSize: 13 }}>check_circle</span>
                          {t("statusReady")}
                        </span>
                      )}
                      {isGenerating && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-1 rounded-full bg-amber-50 text-amber-700">
                          <span className="material-symbols-outlined" style={{ fontSize: 13 }}>hourglass_top</span>
                          {t("statusGenerating")}
                        </span>
                      )}
                      {item.status === "expired" && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-1 rounded-full bg-gray-100 text-gray-500">
                          {t("statusExpired")}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3.5">
                      {isReady && days <= 7 ? (
                        <span className="flex items-center gap-1 text-[12px] font-semibold text-amber-600">
                          <span className="material-symbols-outlined" style={{ fontSize: 14 }}>warning</span>
                          {days <= 0 ? t("expiresToday") : t("expiresIn", { days })}
                        </span>
                      ) : isReady ? (
                        <span className="text-[12px] text-gray-500">{formatDate(item.expires_at)}</span>
                      ) : (
                        <span className="text-[12px] text-gray-300">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      {isReady && item.flow_id ? (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/flow/${item.flow_id}/cv`);
                          }}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 border-[1.5px] border-gray-200 rounded-lg text-[12px] font-semibold text-gray-600 hover:border-[#003399] hover:text-[#003399] hover:bg-[#f1f3ff] transition-all"
                        >
                          <span className="material-symbols-outlined" style={{ fontSize: 15 }}>open_in_new</span>
                          {t("openButton")}
                        </button>
                      ) : isGenerating ? (
                        <button
                          disabled
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 border-[1.5px] border-gray-200 rounded-lg text-[12px] font-semibold text-gray-400 opacity-50 cursor-not-allowed"
                        >
                          <span className="material-symbols-outlined" style={{ fontSize: 15 }}>hourglass_top</span>
                          {t("generatingButton")}
                        </button>
                      ) : null}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {total > pageSize && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 text-[12px] text-gray-500">
            <span>{t("showing", { from, to, total })}</span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => onPageChange(page - 1)}
                disabled={page === 1}
                className="w-[30px] h-[30px] rounded-md border-[1.5px] border-gray-200 flex items-center justify-center disabled:opacity-40 hover:border-[#003399] hover:text-[#003399] transition-colors"
              >
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>chevron_left</span>
              </button>
              {[...Array(totalPages)].map((_, i) => (
                <button
                  key={i}
                  onClick={() => onPageChange(i + 1)}
                  className={cn(
                    "w-[30px] h-[30px] rounded-md border-[1.5px] text-[12px] font-semibold transition-colors",
                    page === i + 1
                      ? "bg-[#003399] text-white border-[#003399]"
                      : "border-gray-200 text-gray-500 hover:border-[#003399] hover:text-[#003399]"
                  )}
                >
                  {i + 1}
                </button>
              ))}
              <button
                onClick={() => onPageChange(page + 1)}
                disabled={page === totalPages}
                className="w-[30px] h-[30px] rounded-md border-[1.5px] border-gray-200 flex items-center justify-center disabled:opacity-40 hover:border-[#003399] hover:text-[#003399] transition-colors"
              >
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>chevron_right</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
