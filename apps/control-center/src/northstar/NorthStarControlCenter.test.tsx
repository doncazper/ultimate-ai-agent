import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { mockControlCenterData } from "../mocks/controlCenterData";
import { NorthStarControlCenter } from "./NorthStarControlCenter";
import {
  isNorthStarPath,
  workspaceSurfaceFromPath,
} from "./model";
import {
  isLegacyReferencePath,
  legacySurfaceDefinitions,
  legacySurfaceFromPath,
} from "./legacyModel";

afterEach(() => {
  cleanup();
  window.history.replaceState({}, "", "/");
});

describe("North Star workspace surface routing", () => {
  it.each([
    ["/workspace", "today"],
    ["/workspace/today", "today"],
    ["/workspace/communications", "communications"],
    ["/workspace/messenger", "messenger"],
    ["/workspace/work-board", "work-board"],
    ["/workspace/crm", "crm"],
    ["/workspace/calendar", "calendar"],
    ["/workspace/news", "news"],
    ["/workspace/studio", "studio"],
    ["/workspace/knowledge", "knowledge"],
    ["/workspace/activity-trust", "activity-trust"],
    ["/workspace/customize", "customize"],
    ["/workspace/settings", "settings"],
    ["/workspace/developer-tools", "developer-tools"],
    ["/workspace/decisions", "decisions"],
    ["/workspace/onboarding", "onboarding"],
  ] as const)("maps %s to %s", (path, surface) => {
    expect(isNorthStarPath(path)).toBe(true);
    expect(workspaceSurfaceFromPath(path)).toBe(surface);
  });

  it("keeps the canonical application routes outside the review lane", () => {
    expect(isNorthStarPath("/today")).toBe(false);
    expect(isNorthStarPath("/settings")).toBe(false);
  });
});

describe("North Star workspace surface behavior", () => {
  it("renders the dense, readable Settings representation", () => {
    render(
      <NorthStarControlCenter
        activePath="/workspace/settings"
        data={mockControlCenterData}
      />,
    );

    expect(screen.getByRole("heading", { name: "Settings" })).toBeVisible();
    expect(screen.getByText("Launch surface")).toBeVisible();
    expect(screen.getByText("Settings mutation")).toBeVisible();
    expect(screen.getByText("Preview only")).toBeVisible();
  });

  it("renders Skill Workbench as guarded discovery, not activation", () => {
    render(
      <NorthStarControlCenter
        activePath="/workspace/studio"
        data={mockControlCenterData}
      />,
    );

    expect(screen.getByRole("heading", { name: "Skill Workbench" })).toBeVisible();
    expect(screen.getByText(/Sanitized preview/)).toBeVisible();
    expect(screen.getAllByText("External code blocked").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Start from a brief" })).toBeDisabled();
  });

  it("exposes Messenger reference states without sending a message", () => {
    render(
      <NorthStarControlCenter
        activePath="/workspace/messenger"
        data={mockControlCenterData}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Messenger reference states" }));
    fireEvent.click(screen.getByRole("button", { name: "Failure recovery" }));

    expect(screen.getByText(/Offline preview · No connector runtime/)).toBeVisible();
    expect(screen.getByText("No message sent")).toBeVisible();
    expect(screen.getByRole("button", { name: "Send message unavailable" })).toBeDisabled();
  });
});

describe("Legacy render pack routing", () => {
  it("maps every accepted 01–19 render to an isolated reference route", () => {
    expect(legacySurfaceDefinitions).toHaveLength(19);
    for (const definition of legacySurfaceDefinitions) {
      expect(isLegacyReferencePath(definition.path)).toBe(true);
      expect(legacySurfaceFromPath(definition.path).id).toBe(definition.id);
      expect(definition.render).toMatch(/\.png$/);
    }
  });

  it("renders a dense reference surface with explicit backend posture", () => {
    render(
      <NorthStarControlCenter
        activePath="/workspace/reference/19-operator-loop"
        data={mockControlCenterData}
      />,
    );

    expect(screen.getByRole("heading", { name: "Operator Loop" })).toBeVisible();
    expect(screen.getByText("Reference build 19/19", { exact: false })).toBeVisible();
    expect(screen.getByText("Not backend-wired", { exact: true })).toBeVisible();
    expect(screen.getByText("No hidden authority", { exact: true })).toBeVisible();
  });
});
