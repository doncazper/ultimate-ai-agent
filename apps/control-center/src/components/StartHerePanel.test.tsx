import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ControlCenterStartHereSummary } from "../api/types";
import { mockControlCenterData } from "../mocks/controlCenterData";
import { StartHerePanel } from "./StartHerePanel";

describe("StartHerePanel", () => {
  it("maps backend route refs through an explicit local allowlist", () => {
    const startHere: ControlCenterStartHereSummary = {
      ...mockControlCenterData.founderStartHere,
      steps: [
        step("Today", "route-ref:control-center:today", "ready"),
        step(
          "Action Inbox",
          "route-ref:control-center:action-inbox",
          "ready",
        ),
        step(
          "Decision Receipt",
          "route-ref:control-center:decision-receipt",
          "partial_review",
        ),
        step(
          "Evidence Timeline",
          "route-ref:control-center:evidence-timeline",
          "ready",
        ),
        step(
          "Memory Review",
          "route-ref:control-center:memory-review",
          "ready",
        ),
        step(
          "Weekly Review",
          "route-ref:control-center:weekly-review",
          "ready",
        ),
        step("Unknown", "route-ref:control-center:not-allowlisted", "unknown"),
        step("External", "//outside.invalid", "unknown"),
      ],
    };

    render(
      <StartHerePanel
        authoritative
        authorityMode="read_only"
        authorityModeAuthoritative
        startHere={startHere}
      />,
    );

    for (const [label, href] of [
      ["Today", "/today"],
      ["Action Inbox", "/actions"],
      ["Decision Receipt", "/actions"],
      ["Evidence Timeline", "/evidence"],
      ["Memory Review", "/memory"],
      ["Weekly Review", "/today"],
      ["Unknown", "/start"],
      ["External", "/start"],
    ] as const) {
      expect(readinessLink(label)).toHaveAttribute(
        "href",
        href,
      );
    }
    expect(screen.getByText("read only")).toBeInTheDocument();
  });

  it("renders blocked and unknown readiness as non-positive posture", () => {
    const startHere: ControlCenterStartHereSummary = {
      ...mockControlCenterData.founderStartHere,
      steps: [
        step("Ready", "route-ref:control-center:today", "ready"),
        step("Not ready", "route-ref:control-center:actions", "not_ready"),
        step(
          "Missing",
          "route-ref:control-center:memory",
          "missing_backend_binding",
        ),
      ],
    };

    render(
      <StartHerePanel
        authoritative={false}
        authorityMode="ask_before_changes"
        authorityModeAuthoritative={false}
        startHere={startHere}
      />,
    );

    expect(dotFor("Ready")).toHaveClass("green");
    expect(dotFor("Not ready")).toHaveClass("red");
    expect(dotFor("Missing")).toHaveClass("red");
    expect(screen.getByText("unverified fallback")).toBeInTheDocument();
  });
});

function step(label: string, routeRef: string, status: string) {
  return {
    ...mockControlCenterData.founderStartHere.steps[0],
    step_id: label.toLowerCase().replaceAll(" ", "-"),
    label,
    route_ref: routeRef,
    status,
  };
}

function dotFor(label: string): Element {
  const link = readinessLink(label);
  return link.querySelector(".start-check-dot") ?? link;
}

function readinessLink(label: string): HTMLElement {
  const link = screen
    .getAllByRole("link", { name: new RegExp(label) })
    .find((candidate) => candidate.closest(".start-check-list") !== null);
  if (!link) {
    throw new Error("Expected a readiness checklist link");
  }
  return link;
}
