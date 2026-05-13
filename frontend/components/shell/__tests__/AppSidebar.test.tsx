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

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AppSidebar } from "../AppSidebar";

const mockPush = vi.fn();
let mockPathname = "/dashboard";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => mockPathname,
}));

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}));

describe("AppSidebar", () => {
  beforeEach(() => {
    mockPush.mockReset();
    mockPathname = "/dashboard";
  });

  it("renders Applire logo image", () => {
    render(<AppSidebar />);
    expect(screen.getByRole("img", { name: /applire/i })).toBeInTheDocument();
  });

  it("renders Applire brand name", () => {
    render(<AppSidebar />);
    expect(screen.getByText("Applire")).toBeInTheDocument();
  });

  it("renders all five nav items", () => {
    render(<AppSidebar />);
    expect(screen.getByRole("button", { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /profile/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /import/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /documents/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /settings/i })).toBeInTheDocument();
  });

  it("highlights Dashboard when pathname is /dashboard", () => {
    mockPathname = "/dashboard";
    render(<AppSidebar />);
    const btn = screen.getByRole("button", { name: /dashboard/i });
    expect(btn.className).toContain("bg-primary-container");
  });

  it("highlights import nav when pathname is /profile/upload", () => {
    mockPathname = "/profile/upload";
    render(<AppSidebar />);
    const btn = screen.getByRole("button", { name: /import/i });
    expect(btn.className).toContain("bg-primary-container");
  });

  it("does not highlight profile nav when pathname is /profile/upload", () => {
    mockPathname = "/profile/upload";
    render(<AppSidebar />);
    const btn = screen.getByRole("button", { name: /profile/i });
    expect(btn.className).not.toContain("bg-primary-container");
  });

  it("highlights Documents when pathname is /documents", () => {
    mockPathname = "/documents";
    render(<AppSidebar />);
    const btn = screen.getByRole("button", { name: /documents/i });
    expect(btn.className).toContain("bg-primary-container");
  });

  it("does not highlight Dashboard when on documents path", () => {
    mockPathname = "/documents";
    render(<AppSidebar />);
    const btn = screen.getByRole("button", { name: /dashboard/i });
    expect(btn.className).not.toContain("bg-primary-container");
  });

  it("clicking Documents navigates to /documents", () => {
    render(<AppSidebar />);
    fireEvent.click(screen.getByRole("button", { name: /documents/i }));
    expect(mockPush).toHaveBeenCalledWith("/documents");
  });

  it("clicking Profile navigates to /profile", () => {
    render(<AppSidebar />);
    fireEvent.click(screen.getByRole("button", { name: /profile/i }));
    expect(mockPush).toHaveBeenCalledWith("/profile");
  });

  it("clicking import nav navigates to /profile/upload", () => {
    render(<AppSidebar />);
    fireEvent.click(screen.getByRole("button", { name: /import/i }));
    expect(mockPush).toHaveBeenCalledWith("/profile/upload");
  });

  it("computes initials from userName 'Max Mustermann' → 'MM'", () => {
    render(<AppSidebar userName="Max Mustermann" />);
    expect(screen.getByText("MM")).toBeInTheDocument();
  });

  it("shows single initial for single-word name", () => {
    render(<AppSidebar userName="Felix" />);
    expect(screen.getByText("F")).toBeInTheDocument();
  });

  it("shows '?' when userName is not provided", () => {
    render(<AppSidebar />);
    expect(screen.getByText("?")).toBeInTheDocument();
  });

  it("displays userName in the user strip", () => {
    render(<AppSidebar userName="Tobias Rosenbaum" />);
    expect(screen.getByText("Tobias Rosenbaum")).toBeInTheDocument();
  });

  it("shows em-dash when userName is null", () => {
    render(<AppSidebar userName={null} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("does not render a help button", () => {
    render(<AppSidebar />);
    expect(screen.queryByRole("button", { name: /help/i })).not.toBeInTheDocument();
  });

  it("renders a version string in the footer", () => {
    render(<AppSidebar />);
    // NEXT_PUBLIC_APP_VERSION is undefined in test env — component falls back to empty string
    // We just check the footer element exists with the right test-id
    expect(screen.getByTestId("sidebar-version")).toBeInTheDocument();
  });
});
