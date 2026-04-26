import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DocumentsTable, type DocumentItem } from "../DocumentsTable";

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, params?: Record<string, unknown>) => {
    if (params) return `${key}:${JSON.stringify(params)}`;
    return key;
  },
}));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const FAR_FUTURE = new Date(Date.now() + 60 * 24 * 36e5).toISOString();
const NEAR_FUTURE = new Date(Date.now() + 3 * 24 * 36e5).toISOString();

const ITEMS: DocumentItem[] = [
  {
    cv_id: "cv-1",
    flow_id: "flow-1",
    role_title: "Head of Validation",
    company_name: "Roche",
    template: "classic_german",
    status: "ready",
    created_at: new Date().toISOString(),
    expires_at: FAR_FUTURE,
  },
  {
    cv_id: "cv-2",
    flow_id: "flow-2",
    role_title: "QA Lead",
    company_name: "Bayer",
    template: "modern_swiss",
    status: "ready",
    created_at: new Date().toISOString(),
    expires_at: NEAR_FUTURE,
  },
  {
    cv_id: "cv-3",
    flow_id: null,
    role_title: "Director of QA",
    company_name: "Novartis",
    template: "classic_german",
    status: "generating",
    created_at: new Date().toISOString(),
    expires_at: FAR_FUTURE,
  },
];

function renderTable(overrides?: Partial<React.ComponentProps<typeof DocumentsTable>>) {
  return render(
    <DocumentsTable
      items={ITEMS}
      total={3}
      page={1}
      pageSize={10}
      onPageChange={vi.fn()}
      {...overrides}
    />
  );
}

describe("DocumentsTable", () => {
  it("renders all rows by default", () => {
    renderTable();
    expect(screen.getByText("Head of Validation")).toBeInTheDocument();
    expect(screen.getByText("QA Lead")).toBeInTheDocument();
    expect(screen.getByText("Director of QA")).toBeInTheDocument();
  });

  it("text search filters rows by company", () => {
    renderTable();
    fireEvent.change(screen.getByPlaceholderText("searchPlaceholder"), {
      target: { value: "Roche" },
    });
    expect(screen.getByText("Head of Validation")).toBeInTheDocument();
    expect(screen.queryByText("QA Lead")).not.toBeInTheDocument();
  });

  it("text search is case-insensitive", () => {
    renderTable();
    fireEvent.change(screen.getByPlaceholderText("searchPlaceholder"), {
      target: { value: "bayer" },
    });
    expect(screen.getByText("QA Lead")).toBeInTheDocument();
    expect(screen.queryByText("Head of Validation")).not.toBeInTheDocument();
  });

  it("Generating filter hides ready rows", () => {
    renderTable();
    fireEvent.click(screen.getByText("filterGenerating"));
    expect(screen.getByText("Director of QA")).toBeInTheDocument();
    expect(screen.queryByText("Head of Validation")).not.toBeInTheDocument();
  });

  it("Expiring filter shows only rows expiring within 7 days", () => {
    renderTable();
    fireEvent.click(screen.getByText("filterExpiring"));
    expect(screen.getByText("QA Lead")).toBeInTheDocument();
    expect(screen.queryByText("Head of Validation")).not.toBeInTheDocument();
  });

  it("Open button is disabled for generating rows", () => {
    renderTable();
    const buttons = screen.getAllByRole("button");
    const generatingBtn = buttons.find((b) => b.textContent?.includes("generatingButton"));
    expect(generatingBtn).toBeDisabled();
  });
});
