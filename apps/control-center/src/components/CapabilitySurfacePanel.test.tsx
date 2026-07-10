import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { mockControlCenterData } from "../mocks/controlCenterData";
import { CapabilitySurfacePanel } from "./CapabilitySurfacePanel";

describe("CapabilitySurfacePanel web hybrid posture", () => {
  it("renders operator-readable backend truth without authority claims", () => {
    render(
      <CapabilitySurfacePanel surface={mockControlCenterData.capabilitySurface} />,
    );

    expect(screen.getByText("Web search and extraction")).toBeInTheDocument();
    expect(screen.getByText("SearXNG read-only search")).toBeInTheDocument();
    expect(
      screen.getByText("Self-hosted one-page markdown"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Firecrawl Cloud free-plan one-page markdown"),
    ).toBeInTheDocument();
    expect(screen.getByText("External content is untrusted")).toBeInTheDocument();
    expect(
      screen.getByText(/Exact approval, AuthorityLease, and request budget/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Paid usage, Keyless/)).toBeInTheDocument();
    expect(screen.queryByText(/\{.*\}/)).not.toBeInTheDocument();
  });
});
