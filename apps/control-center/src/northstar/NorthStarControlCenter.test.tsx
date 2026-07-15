import { cleanup, render, screen } from "@testing-library/react";
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

  it("fails closed for an unknown workspace route", () => {
    expect(workspaceSurfaceFromPath("/workspace/not-a-surface")).toBeUndefined();
    render(
      <NorthStarControlCenter
        activePath="/workspace/not-a-surface"
        data={mockControlCenterData}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Workspace route unavailable");
    expect(screen.queryByRole("heading", { name: "Morning Briefing" })).not.toBeInTheDocument();
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
    expect(screen.getByText(/Sanitized render fixture/)).toBeVisible();
    expect(screen.getAllByText("External code blocked").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Start from a brief" })).toBeDisabled();
  });

  it("links workspace navigation to the canonical Messenger shell", () => {
    render(
      <NorthStarControlCenter
        activePath="/workspace/today"
        data={mockControlCenterData}
      />,
    );

    expect(screen.getByRole("link", { name: "Messenger" })).toHaveAttribute("href", "/messenger");
  });

  it("uses the canonical Messenger shell when invoked through the workspace alias", () => {
    render(
      <NorthStarControlCenter
        activePath="/workspace/messenger"
        data={mockControlCenterData}
      />,
    );

    expect(screen.getByRole("heading", { name: "UAA Development" })).toBeVisible();
    expect(screen.getByText("Fixture-only preview")).toBeVisible();
  });
});

describe("Legacy render pack routing", () => {
  it("maps every accepted 01–19 render to an isolated reference route", () => {
    expect(legacySurfaceDefinitions).toHaveLength(19);
    for (const definition of legacySurfaceDefinitions) {
      expect(isLegacyReferencePath(definition.path)).toBe(true);
      expect(legacySurfaceFromPath(definition.path)?.id).toBe(definition.id);
      expect(definition.render).toMatch(/\.png$/);
    }
  });

  it("fails closed for an unknown legacy reference route", () => {
    expect(legacySurfaceFromPath("/workspace/reference/not-a-render")).toBeUndefined();
    render(
      <NorthStarControlCenter
        activePath="/workspace/reference/not-a-render"
        data={mockControlCenterData}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Reference route unavailable");
    expect(screen.queryByText("Reference build 1/19", { exact: false })).not.toBeInTheDocument();
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
