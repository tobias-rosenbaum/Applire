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

  it("renders Applire brand name", () => {
    render(<AppSidebar />);
    expect(screen.getByText("Applire")).toBeInTheDocument();
  });

  it("renders all four nav items", () => {
    render(<AppSidebar />);
    expect(screen.getByRole("button", { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /profile/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /documents/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /settings/i })).toBeInTheDocument();
  });

  it("highlights Dashboard when pathname is /dashboard", () => {
    mockPathname = "/dashboard";
    render(<AppSidebar />);
    const btn = screen.getByRole("button", { name: /dashboard/i });
    expect(btn.className).toContain("bg-[#eef1ff]");
  });

  it("highlights Documents when pathname is /documents", () => {
    mockPathname = "/documents";
    render(<AppSidebar />);
    const btn = screen.getByRole("button", { name: /documents/i });
    expect(btn.className).toContain("bg-[#eef1ff]");
  });

  it("does not highlight Dashboard when on documents path", () => {
    mockPathname = "/documents";
    render(<AppSidebar />);
    const btn = screen.getByRole("button", { name: /dashboard/i });
    expect(btn.className).not.toContain("bg-[#eef1ff]");
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
});
