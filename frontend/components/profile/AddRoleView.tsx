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

"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";

import { addRole, type AddRoleRequest, type AddRoleSource, type CloseRoleEntry } from "@/lib/profile-roles";

export interface OpenRole {
  id: string;
  company: string;
  role: string;
  start_date: string | null;
}

interface AddRoleViewProps {
  openRoles: OpenRole[];
  prefill?: { title?: string; company?: string; location?: string | null; industry?: string | null };
  sourceRef?: string | null;
}

export function AddRoleView({ openRoles, prefill, sourceRef }: AddRoleViewProps) {
  const t = useTranslations("profileUpdate.addRole");
  const router = useRouter();
  const searchParams = useSearchParams();
  const source = (searchParams.get("source") ?? "manual") as AddRoleSource;

  const [title, setTitle] = useState(prefill?.title ?? "");
  const [company, setCompany] = useState(prefill?.company ?? "");
  const [startDate, setStartDate] = useState("");
  const [location, setLocation] = useState(prefill?.location ?? "");
  const [industry, setIndustry] = useState(prefill?.industry ?? "");
  const [closeRoles, setCloseRoles] = useState<CloseRoleEntry[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [jdText, setJdText] = useState("");
  const [analysing, setAnalysing] = useState(false);

  useEffect(() => {
    const applicationId = searchParams.get("application_id");
    if (source !== "application" || !applicationId) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`/api/applications/${applicationId}`);
        if (!res.ok) {
          if (cancelled) return;
          setError(t("noJdHint"));
          return;
        }
        const app = await res.json();
        if (cancelled) return;
        setTitle(app.role_title ?? "");
        setCompany(app.company_name ?? "");
        // Note: ApplicationResponse does not include location or industry;
        // those stay empty for Emma to fill manually.
      } catch {
        if (cancelled) return;
        setError(t("noJdHint"));
      }
    })();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source, searchParams, t]);

  const canSave = !!(title.trim() && company.trim() && startDate && !submitting);

  async function analyseJd() {
    if (!jdText.trim()) return;
    setAnalysing(true);
    setError("");
    try {
      const res = await fetch("/api/job/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: jdText }),
      });
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(detail || `HTTP ${res.status}`);
      }
      const job = await res.json();
      setTitle(job.role_title ?? "");
      setCompany(job.company_name ?? "");
      // Note: /api/job/analyze does not return location or industry fields,
      // so Emma fills those manually.
    } catch (e) {
      setError(e instanceof Error ? e.message : "JD analysis failed");
    } finally {
      setAnalysing(false);
    }
  }

  async function handleSave() {
    setSubmitting(true);
    setError("");
    try {
      await addRole({
        title: title.trim(),
        company: company.trim(),
        start_date: startDate,
        location: location || null,
        industry: industry || null,
        close_roles: closeRoles,
        source,
        source_ref: sourceRef ?? null,
      });
      router.push("/profile");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
      setSubmitting(false);
    }
  }

  return (
    <section className="mx-auto max-w-2xl px-6 py-10">
      <h1 className="text-2xl font-bold font-manrope text-gray-900">{t("heading")}</h1>

      <div className="mt-8">
        {source === "jd_paste" && (
          <div className="mb-6">
            <label className="block">
              <span className="text-sm text-gray-700">{t("pasteJdLabel")}</span>
              <textarea
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                rows={6}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
            </label>
            <button
              type="button"
              onClick={analyseJd}
              disabled={analysing || !jdText.trim()}
              className="mt-2 px-3 py-1.5 rounded-lg bg-primary-container text-primary text-sm font-bold disabled:opacity-50"
            >
              {t("analyseJd")}
            </button>
          </div>
        )}
        <h2 className="text-base font-bold text-gray-900">{t("step1Heading")}</h2>
        <div className="mt-4 space-y-4">
          <Field label={t("titleLabel")} value={title} onChange={setTitle} required />
          <Field label={t("companyLabel")} value={company} onChange={setCompany} required />
          <Field label={t("startDateLabel")} type="date" value={startDate} onChange={setStartDate} required />
          <Field label={t("locationLabel")} value={location} onChange={setLocation} />
          <Field label={t("industryLabel")} value={industry} onChange={setIndustry} />
        </div>
      </div>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <div className="mt-8 flex justify-between">
        <button
          type="button"
          onClick={() => router.push("/profile/upload")}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          {t("cancel")}
        </button>
        <button
          type="button"
          disabled={!canSave}
          onClick={handleSave}
          className="px-4 py-2 rounded-lg bg-primary text-white text-sm font-bold disabled:opacity-50"
        >
          {submitting ? t("savedSuccess") : t("save")}
        </button>
      </div>
    </section>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  required,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  required?: boolean;
}) {
  return (
    <label className="block">
      <span className="text-sm text-gray-700">
        {label}
        {required && " *"}
      </span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
      />
    </label>
  );
}
