import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { mockControlCenterData } from "../mocks/controlCenterData";
import { CapabilitySurfacePanel } from "./CapabilitySurfacePanel";

describe("CapabilitySurfacePanel web hybrid posture", () => {
  it("renders operator-readable backend truth without authority claims", () => {
    render(
      <CapabilitySurfacePanel surface={mockControlCenterData.capabilitySurface} />,
    );
    const webPanel = screen.getByRole("region", {
      name: "Web search and extraction",
    });

    expect(screen.getByText("Web search and extraction")).toBeInTheDocument();
    expect(screen.getByText("SearXNG read-only search")).toBeInTheDocument();
    expect(
      screen.getByText("Self-hosted one-page markdown"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Firecrawl Cloud free-plan one-page markdown"),
    ).toBeInTheDocument();
    expect(screen.getByText("External content is untrusted")).toBeInTheDocument();
    expect(screen.getByText("Bounded cited research")).toBeInTheDocument();
    expect(
      screen.getByText(/current citations are 0; zero means no current observation/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText("scripts/inspect_web_hybrid_status.py"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("web-hybrid-read-model-ref:operator:v1"),
    ).toBeInTheDocument();
    for (const lane of mockControlCenterData.capabilitySurface.web_hybrid.lanes) {
      expect(screen.getByText(lane.capability_ref)).toBeInTheDocument();
      expect(screen.getByText(lane.adapter_ref)).toBeInTheDocument();
    }
    expect(
      within(webPanel).getByText(
        new RegExp(
          mockControlCenterData.capabilitySurface.web_hybrid.research_aggregation
            .proof_refs[0],
        ),
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/CURRENT_RESEARCH_OBSERVATIONS_NOT_INJECTED/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Exact approval, mission-scoped AuthorityLease/),
    ).toBeInTheDocument();
    expect(
      within(webPanel).getByText("not injected by this read-only surface"),
    ).toBeInTheDocument();
    expect(
      within(webPanel).getByText("3", { selector: ".stat-card strong" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Paid usage, Keyless/)).toBeInTheDocument();
    expect(screen.queryByText(/\{.*\}/)).not.toBeInTheDocument();
  });

  it("renders the evidence-gated maturity plan without inflating scores", () => {
    render(
      <CapabilitySurfacePanel surface={mockControlCenterData.capabilitySurface} />,
    );

    const maturityPanel = screen.getByRole("region", {
      name: "Capability score evidence",
    });
    expect(
      within(screen.getByRole("region", { name: "Capabilities" })).getByText(
        "fallback shape only",
      ),
    ).toBeInTheDocument();
    expect(within(maturityPanel).getByText("Extensibility and ecosystem")).toBeInTheDocument();
    expect(within(maturityPanel).getByText("Scores never mint authority")).toBeInTheDocument();
    expect(within(maturityPanel).getAllByText("baseline only").length).toBeGreaterThan(0);
    expect(
      within(maturityPanel).getByText(/passing automated checks advances evidence readiness/i),
    ).toBeInTheDocument();
    expect(within(maturityPanel).getAllByText(/next proof:/i).length).toBe(16);
    expect(within(maturityPanel).queryByText(/globally authorized/i)).not.toBeInTheDocument();
  });
});
