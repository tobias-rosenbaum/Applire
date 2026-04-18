"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { NextIntlClientProvider } from "next-intl";
import enMessages from "../../messages/en.json";
import deMessages from "../../messages/de.json";

type Locale = "de" | "en";

const messages: Record<Locale, typeof enMessages> = {
  en: enMessages,
  de: deMessages,
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

interface LocaleContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => Promise<void>;
}

const LocaleContext = createContext<LocaleContextValue>({
  locale: "en",
  setLocale: async () => {},
});

export function useLocale() {
  return useContext(LocaleContext);
}

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");

  useEffect(() => {
    fetch(`${API_BASE}/api/settings`)
      .then((r) => r.json())
      .then((data) => {
        const lang = data.ui_language as Locale | null;
        if (lang === "de" || lang === "en") {
          setLocaleState(lang);
          document.documentElement.lang = lang;
        }
      })
      .catch(() => {
        // Network error — stay with "en" default
      });
  }, []);

  const setLocale = useCallback(async (newLocale: Locale) => {
    await fetch(`${API_BASE}/api/settings`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ui_language: newLocale }),
    });
    setLocaleState(newLocale);
    document.documentElement.lang = newLocale;
  }, []);

  return (
    <LocaleContext.Provider value={{ locale, setLocale }}>
      <NextIntlClientProvider locale={locale} messages={messages[locale]}>
        {children}
      </NextIntlClientProvider>
    </LocaleContext.Provider>
  );
}
