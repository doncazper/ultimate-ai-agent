import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { mockControlCenterData } from "../mocks/controlCenterData";
import { MacOSSetupAssistantPanel } from "./MacOSSetupAssistantPanel";

describe("MacOSSetupAssistantPanel", () => {
  it("starts with readable backend-owned readiness and one next safe action", () => {
    render(
      <MacOSSetupAssistantPanel
        setup={mockControlCenterData.macosSetupAssistant}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Your local setup at a glance" }),
    ).toBeVisible();
    const counts = screen.getByLabelText("Setup diagnostic counts");
    expect(within(counts).getByText("Ready")).toBeVisible();
    expect(within(counts).getByText("Missing")).toBeVisible();
    expect(within(counts).getByText("Blocked")).toBeVisible();
    expect(within(counts).getAllByText("1")).toHaveLength(2);
    expect(within(counts).getByText("2")).toBeVisible();

    const attention = screen
      .getAllByRole("heading", { name: "Native macOS application" })[0]
      .closest(".setup-attention-card");
    expect(attention).not.toBeNull();
    expect(within(attention as HTMLElement).getByText("missing")).toBeVisible();
    expect(
      within(attention as HTMLElement).getByText("review-native-shell-scope"),
    ).toBeVisible();
  });

  it("keeps technical proof available but collapsed on the regular-user path", () => {
    render(
      <MacOSSetupAssistantPanel
        setup={mockControlCenterData.macosSetupAssistant}
      />,
    );

    const summary = screen.getByText(
      "Review technical setup proof and boundaries",
    );
    const disclosure = summary.closest("details");
    expect(disclosure).not.toBeNull();
    expect(disclosure).not.toHaveAttribute("open");
    expect(screen.getByRole("link", { name: "Settings" })).toHaveAttribute(
      "href",
      "/settings",
    );
    expect(
      screen.queryByRole("heading", { name: "Provider Catalog" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /run|install|repair|rollback/i }),
    ).not.toBeInTheDocument();
  });
});
