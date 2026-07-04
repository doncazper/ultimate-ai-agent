import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  RouteStatePanel,
  type RouteStateDescriptor,
  type RouteStateKind,
} from "./DataState";

const stateKinds: RouteStateKind[] = [
  "loading",
  "empty",
  "error",
  "blocked",
  "partial",
  "success",
];

function descriptor(kind: RouteStateKind): RouteStateDescriptor {
  return {
    kind,
    statusLabel: kind,
    surfaceLabel: "Today",
    title: `Today ${kind} route state`,
    message:
      "Backend-owned route refs are visible when available; blocked and fallback states stay visible.",
    nextSafeAction:
      "Inspect proof, receipts, and blocked authority refs before promotion.",
    sourceLabel: "Route truth: frontend test fixture.",
  };
}

describe("RouteStatePanel", () => {
  it.each(stateKinds)("renders the %s route state without authority controls", (kind) => {
    render(<RouteStatePanel state={descriptor(kind)} />);

    const role = kind === "error" ? "alert" : "status";
    expect(screen.getByRole(role)).toBeInTheDocument();
    expect(screen.getByLabelText("Today route state")).toBeInTheDocument();
    expect(screen.getByText(kind)).toBeInTheDocument();
    expect(screen.getByText(`Today ${kind} route state`)).toBeInTheDocument();
    expect(
      screen.getByText(/Inspect proof, receipts, and blocked authority refs/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Route truth: frontend test fixture/i),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(screen.queryByText(/Production ready/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\/Users\//i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw prompt|raw response|credential/i)).not.toBeInTheDocument();
  });
});
