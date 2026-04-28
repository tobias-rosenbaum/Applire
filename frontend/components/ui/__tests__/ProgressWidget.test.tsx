import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ProgressWidget } from "../progress-widget";

const makeSteps = (statuses: Array<"done" | "active" | "pending">) =>
  statuses.map((status, i) => ({ label: `Step ${i + 1}`, status }));

describe("ProgressWidget", () => {
  it("shows 0% when no steps are done", () => {
    render(
      <ProgressWidget
        steps={makeSteps(["active", "pending", "pending"])}
        title="Loading"
      />
    );
    expect(screen.getByText("0%")).toBeInTheDocument();
  });

  it("shows 33% when 1 of 3 steps is done", () => {
    render(
      <ProgressWidget
        steps={makeSteps(["done", "active", "pending"])}
        title="Loading"
      />
    );
    expect(screen.getByText("33%")).toBeInTheDocument();
  });

  it("shows 100% when all steps are done", () => {
    render(
      <ProgressWidget
        steps={makeSteps(["done", "done", "done"])}
        title="Loading"
      />
    );
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("renders title and optional subtitle", () => {
    render(
      <ProgressWidget
        steps={makeSteps(["active"])}
        title="Analysing"
        subtitle="This takes a moment"
      />
    );
    expect(screen.getByText("Analysing")).toBeInTheDocument();
    expect(screen.getByText("This takes a moment")).toBeInTheDocument();
  });

  it("applies animate-shimmer class to active step row", () => {
    const { container } = render(
      <ProgressWidget
        steps={makeSteps(["done", "active", "pending"])}
        title="Working"
      />
    );
    const rows = container.querySelectorAll("[data-step-status]");
    expect(rows[1].getAttribute("data-step-status")).toBe("active");
    expect(rows[1].className).toContain("animate-shimmer");
  });

  it("renders step labels", () => {
    render(
      <ProgressWidget
        steps={[
          { label: "First step", status: "done" },
          { label: "Second step", status: "active" },
        ]}
        title="Test"
      />
    );
    expect(screen.getByText("First step")).toBeInTheDocument();
    expect(screen.getByText("Second step")).toBeInTheDocument();
  });
});
