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
