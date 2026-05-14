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

import type { ProgressStep } from "@/components/ui/progress-widget";

export function buildClProgressSteps(
  status: string,
  t: (key: string) => string
): ProgressStep[] {
  const activeIdx = status === "generating" ? 1 : status === "ready" ? 2 : 0;
  const labels = [t("stepPreparing"), t("stepGenerating"), t("stepReady")];
  return labels.map((label, i) => ({
    label,
    status: (i < activeIdx ? "done" : i === activeIdx ? "active" : "pending") as ProgressStep["status"],
  }));
}
