import { describe, expect, it } from "vitest";
import type {
  BackendConnectionSummary,
  ControlCenterRouteReadState,
} from "./api/types";
import { getRouteStateDescriptor } from "./routes";

const onlineConnection: BackendConnectionSummary = {
  state: "online",
  apiBaseLabel: "relative local API",
  checkedAt: "2026-01-01T00:00:00Z",
  safeMessage: "Local backend route state returned.",
  usingMockData: false,
  warnings: [],
};

function readState(
  route: string,
  surfaceLabel: string,
  state: ControlCenterRouteReadState["state"],
): ControlCenterRouteReadState {
  return {
    route,
    surfaceLabel,
    state,
    statusLabel: state === "backend_owned" ? "backend-owned" : state,
    sourceLabel: "Python Core/API read model",
    safeSummary: `${surfaceLabel} read model returned safe refs only.`,
    backendRouteRefs: [`GET /control-center${route}/summary`],
    warningRefs: [],
    blockedAuthorityRefs: ["blocked-state:no-production-authority"],
    nextSafeAction: "Inspect proof refs before relying on this route.",
  };
}

describe("getRouteStateDescriptor", () => {
  it("maps an exact-proof route with backend-owned data to success", () => {
    const descriptor = getRouteStateDescriptor(
      "/actions",
      onlineConnection,
      readState("/actions", "Action Inbox", "backend_owned"),
    );

    expect(descriptor.kind).toBe("success");
    expect(descriptor.title).toBe("Action Inbox has exact route proof");
    expect(descriptor.message).toContain("Backend route refs");
  });

  it("maps partial, blocked, empty, and fallback route postures truthfully", () => {
    expect(
      getRouteStateDescriptor(
        "/today",
        onlineConnection,
        readState("/today", "Today", "backend_owned"),
      ).kind,
    ).toBe("partial");
    expect(
      getRouteStateDescriptor(
        "/crm",
        onlineConnection,
        readState("/crm", "CRM", "backend_owned"),
      ).kind,
    ).toBe("partial");
    expect(
      getRouteStateDescriptor("/private-trial", onlineConnection).kind,
    ).toBe("empty");
    const fallback = getRouteStateDescriptor(
      "/actions",
      { ...onlineConnection, state: "mock_fallback", usingMockData: true },
      readState("/actions", "Action Inbox", "mock_fallback"),
    );
    expect(fallback.kind).toBe("partial");
    expect(fallback.statusLabel).toBe("mock_fallback");
    expect(fallback.title).toContain("fallback route state");
  });
});
