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

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { withIntl } from "@/lib/test-utils/with-intl";
import { ActionsTab } from "../ActionsTab";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock("@/lib/profile-roles", () => ({
  markApplicationHired: (...args: Parameters<typeof mockMarkApplicationHired>) =>
    mockMarkApplicationHired(...args),
  addRole: vi.fn(),
  fetchOpenRoles: vi.fn(),
}));

const mockPush = vi.fn();
const mockMarkApplicationHired = vi.fn();

const BASE_PROPS = {
  flowId: "test-flow-id",
  matchScore: 0.82,
  expiryWarning: null as { level: "none" | "warning" | "critical"; expiresIn: string } | null,
  coverLetterId: null as string | null,
  onDownloadPdf: vi.fn(),
  onRegenerateSame: vi.fn(),
  onRegenerateWithTemplate: vi.fn(),
  onNext: vi.fn(),
  onGenerateCoverLetter: vi.fn(),
};

describe("ActionsTab", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders match score as percentage", () => {
    render(withIntl(<ActionsTab {...BASE_PROPS} />));
    expect(screen.getByText("82%")).toBeTruthy();
    expect(screen.getByText("Matching-Score")).toBeTruthy();
  });

  it("does not show expiry warning when level is none", () => {
    render(withIntl(<ActionsTab {...BASE_PROPS} expiryWarning={null} />));
    expect(screen.queryByText(/läuft ab/)).toBeNull();
  });

  it("shows warning expiry when level is warning", () => {
    render(withIntl(<ActionsTab {...BASE_PROPS} expiryWarning={{ level: "warning", expiresIn: "2 Tage" }} />));
    expect(screen.getByText(/bald ab/)).toBeTruthy();
    expect(screen.getByText("2 Tage")).toBeTruthy();
  });

  it("shows critical expiry when level is critical", () => {
    render(withIntl(<ActionsTab {...BASE_PROPS} expiryWarning={{ level: "critical", expiresIn: "in 3 Stunden" }} />));
    expect(screen.getByText(/läuft ab/)).toBeTruthy();
    expect(screen.getByText("in 3 Stunden")).toBeTruthy();
  });

  it("Download PDF button has correct testid", () => {
    render(withIntl(<ActionsTab {...BASE_PROPS} />));
    expect(screen.getByTestId("download-pdf-btn")).toBeTruthy();
  });

  it("Regenerate same button has correct testid", () => {
    render(withIntl(<ActionsTab {...BASE_PROPS} />));
    expect(screen.getByTestId("regenerate-same-btn")).toBeTruthy();
  });

  it("Next step button has correct testid", () => {
    render(withIntl(<ActionsTab {...BASE_PROPS} />));
    expect(screen.getByTestId("next-step-btn")).toBeTruthy();
  });

  it("Clicking Download PDF calls onDownloadPdf", () => {
    const onDownloadPdf = vi.fn();
    render(withIntl(<ActionsTab {...BASE_PROPS} onDownloadPdf={onDownloadPdf} />));
    screen.getByTestId("download-pdf-btn").click();
    expect(onDownloadPdf).toHaveBeenCalled();
  });

  it("Clicking Next Step calls onNext", () => {
    const onNext = vi.fn();
    render(withIntl(<ActionsTab {...BASE_PROPS} onNext={onNext} />));
    screen.getByTestId("next-step-btn").click();
    expect(onNext).toHaveBeenCalled();
  });

  it("renders without matchScore (null)", () => {
    render(withIntl(<ActionsTab {...BASE_PROPS} matchScore={null} />));
    expect(screen.queryByText(/%/)).toBeNull();
  });
});

describe("ActionsTab — Mark as Hired", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("does not render the button when applicationId is null", () => {
    render(withIntl(<ActionsTab {...BASE_PROPS} applicationId={null} />));
    expect(
      screen.queryByRole("button", { name: /Mark as Hired/i })
    ).not.toBeInTheDocument();
  });

  it("renders the button when applicationId is provided", () => {
    render(withIntl(<ActionsTab {...BASE_PROPS} applicationId="abc" />));
    expect(
      screen.getByRole("button", { name: /Mark as Hired/i })
    ).toBeInTheDocument();
  });

  it("calls markApplicationHired and navigates on click", async () => {
    mockMarkApplicationHired.mockResolvedValue({
      application_id: "abc",
      user_status: "hired",
      redirect_url:
        "/profile/upload?action=add-role&source=application&application_id=abc",
    });

    render(withIntl(<ActionsTab {...BASE_PROPS} applicationId="abc" />));
    fireEvent.click(screen.getByRole("button", { name: /Mark as Hired/i }));

    await waitFor(() => {
      expect(mockMarkApplicationHired).toHaveBeenCalledWith("abc");
      expect(mockPush).toHaveBeenCalledWith(
        "/profile/upload?action=add-role&source=application&application_id=abc"
      );
    });
  });
});
