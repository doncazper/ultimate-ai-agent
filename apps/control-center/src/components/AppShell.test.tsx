import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ControlCenterRouteReadState } from "../api/types";
import { AppShell } from "./AppShell";

const backendOwnedSetupRoute: ControlCenterRouteReadState = {
  route: "/setup",
  surfaceLabel: "Setup Assistant",
  state: "backend_owned",
  statusLabel: "implemented_backend_owned_read_model",
  sourceLabel: "Python Agent Core",
  safeSummary: "Backend-owned Setup readiness is available.",
  backendRouteRefs: ["GET /control-center/setup"],
  warningRefs: [],
  blockedAuthorityRefs: ["blocked-state:setup:no-runtime-execution"],
  nextSafeAction: "Review readiness evidence.",
};

describe("AppShell authority posture copy", () => {
  it("does not label a backend-owned route as fallback when authority posture is absent", () => {
    render(
      <AppShell activePath="/setup" routeState={backendOwnedSetupRoute}>
        <div>Setup content</div>
      </AppShell>,
    );

    expect(screen.getByText("Backend-owned route read model")).toBeInTheDocument();
    expect(
      screen.getByText("Authority posture not reported by this route read"),
    ).toBeInTheDocument();
    expect(
      screen.getByText((_, element) =>
        element?.textContent ===
        "Kill-switch posture: not reported by this route read",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText("Unverified in fallback")).not.toBeInTheDocument();
  });

  it("retains fallback wording when no backend-owned route read is present", () => {
    render(
      <AppShell activePath="/setup">
        <div>Fallback content</div>
      </AppShell>,
    );

    expect(screen.getByText("Unverified in fallback")).toBeInTheDocument();
    expect(
      screen.getByText((_, element) =>
        element?.textContent === "Kill-switch posture: unverified in fallback",
      ),
    ).toBeInTheDocument();
  });
});
