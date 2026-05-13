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

import { render, screen, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { CoverLetterRefinementPanel } from "../CoverLetterRefinementPanel";
import { withIntl } from "@/lib/test-utils/with-intl";

beforeEach(() => {
  vi.spyOn(global, "fetch").mockResolvedValue({
    ok: true,
    json: async () => ({ sections: [] }),
    text: async () => "",
  } as Response);
});

afterEach(() => {
  vi.restoreAllMocks();
});

const BASE_PROPS = {
  flowId: "test-flow",
  coverLetterId: "aaaa-1111",
  letterData: null,
  currentTemplate: "classic_german" as const,
  onSectionSaved: vi.fn(),
  onTemplateChange: vi.fn(),
  onRegenerateCoverLetter: vi.fn(),
  onDownloadPdf: vi.fn(),
  downloading: false,
};

describe("CoverLetterRefinementPanel collapse", () => {
  it("renders collapse button when expanded", () => {
    render(
      withIntl(
        <CoverLetterRefinementPanel
          {...BASE_PROPS}
          collapsed={false}
          onToggleCollapse={vi.fn()}
        />
      )
    );
    expect(screen.getByTestId("cl-panel-collapse-btn")).toBeTruthy();
  });

  it("calls onToggleCollapse when collapse button clicked", () => {
    const toggle = vi.fn();
    render(
      withIntl(
        <CoverLetterRefinementPanel
          {...BASE_PROPS}
          collapsed={false}
          onToggleCollapse={toggle}
        />
      )
    );
    fireEvent.click(screen.getByTestId("cl-panel-collapse-btn"));
    expect(toggle).toHaveBeenCalledOnce();
  });

  it("renders icon rail when collapsed", () => {
    render(
      withIntl(
        <CoverLetterRefinementPanel
          {...BASE_PROPS}
          collapsed={true}
          onToggleCollapse={vi.fn()}
        />
      )
    );
    expect(screen.getByTestId("cl-panel-expand-btn")).toBeTruthy();
    expect(screen.getByTestId("cl-tab-icon-content")).toBeTruthy();
    expect(screen.getByTestId("cl-tab-icon-design")).toBeTruthy();
    expect(screen.getByTestId("cl-tab-icon-actions")).toBeTruthy();
  });

  it("calls onToggleCollapse when expand button clicked", () => {
    const toggle = vi.fn();
    render(
      withIntl(
        <CoverLetterRefinementPanel
          {...BASE_PROPS}
          collapsed={true}
          onToggleCollapse={toggle}
        />
      )
    );
    fireEvent.click(screen.getByTestId("cl-panel-expand-btn"));
    expect(toggle).toHaveBeenCalledOnce();
  });

  it("clicking tab icon in collapsed state calls onToggleCollapse", () => {
    const toggle = vi.fn();
    render(
      withIntl(
        <CoverLetterRefinementPanel
          {...BASE_PROPS}
          collapsed={true}
          onToggleCollapse={toggle}
        />
      )
    );
    fireEvent.click(screen.getByTestId("cl-tab-icon-design"));
    expect(toggle).toHaveBeenCalledOnce();
  });
});
