import { NextIntlClientProvider } from "next-intl";
import enMessages from "../../messages/en.json";
import deMessages from "../../messages/de.json";

const allMessages = { en: enMessages, de: deMessages };

/**
 * Wraps a React element in NextIntlClientProvider for Vitest tests.
 * Defaults to English so test assertions can use English strings.
 */
export function withIntl(
  element: React.ReactElement,
  locale: "en" | "de" = "en"
): React.ReactElement {
  return (
    <NextIntlClientProvider locale={locale} messages={allMessages[locale]}>
      {element}
    </NextIntlClientProvider>
  );
}
