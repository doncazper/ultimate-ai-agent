import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ControlCenterData } from "./api/types";
import { mockControlCenterData } from "./mocks/controlCenterData";

const mocked = vi.hoisted(() => ({
  controlCenterState: {} as unknown,
  truthState: {} as unknown,
  truthEnabled: false,
}));

vi.mock("./hooks/useControlCenterData", () => ({
  useControlCenterData: () => mocked.controlCenterState,
}));

vi.mock("./hooks/useCriticalBackendTruth", () => ({
  useCriticalBackendTruth: (enabled: boolean) => {
    mocked.truthEnabled = enabled;
    return mocked.truthState;
  },
}));

import { App } from "./App";

const lastVerified = {
  verifiedAt: "2026-07-22T18:00:10.000Z",
  sourceRef: "source-ref:python-core:control-center-backend-truth",
  backendRevisionRef: `commit-ref:git:${"1".repeat(40)}`,
};

function backendData(routeState: "backend_owned" | "mock_fallback") {
  const data = structuredClone(mockControlCenterData) as ControlCenterData;
  data.connection.state = "online";
  data.connection.usingMockData = false;
  data.connection.warnings = [];
  for (const route of [
    "/today",
    "/actions",
    "/approvals",
    "/chat",
    "/critical/dashboard-read-model",
    "/evidence",
    "/critical/manifest-read-model",
    "/critical/provider-catalog-read-model",
    "/runs",
    "/runtime",
    "/settings",
  ]) {
    data.routeStates[route] = {
      ...data.routeStates["/today"],
      route,
      surfaceLabel: route,
      state: "backend_owned",
    };
  }
  data.routeStates["/today"].state = routeState;
  return data;
}

beforeEach(() => {
  window.history.pushState({}, "", "/today");
  mocked.controlCenterState = {
    status: "ready",
    data: backendData("backend_owned"),
    error: null,
    snapshotRef: "proof-ref:truth:current",
    retry: vi.fn(),
  };
  mocked.truthState = {
    status: "ready",
    truth: { envelope_integrity_ref: "proof-ref:truth:current" },
    errorRef: null,
    lastVerified,
    retry: vi.fn(),
  };
  mocked.truthEnabled = false;
});

afterEach(() => cleanup());

describe("critical backend truth boundary", () => {
  it("loads backend truth before rendering the runtime mutation surface", () => {
    window.history.pushState({}, "", "/runtime");

    render(<App />);

    expect(mocked.truthEnabled).toBe(true);
    expect(
      screen.getByRole("heading", { name: "Runtime readiness" }),
    ).toBeInTheDocument();
  });

  it("hides critical product content when the truth envelope is stale", () => {
    mocked.truthState = {
      status: "degraded",
      truth: null,
      errorRef: "BACKEND_TRUTH_STALE",
      lastVerified,
      retry: vi.fn(),
    };

    render(<App />);

    expect(
      screen.getByRole("heading", {
        name: "Today is not showing unverified product state",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("BACKEND_TRUTH_STALE")).toBeInTheDocument();
    expect(screen.getByText(lastVerified.backendRevisionRef)).toBeInTheDocument();
    expect(screen.queryByText("Backend-owned first loop")).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Retry backend and route data" }),
    ).toBeEnabled();
  });

  it("hides critical product content while truth is still loading", () => {
    mocked.truthState = {
      status: "loading",
      truth: null,
      errorRef: null,
      lastVerified: null,
      retry: vi.fn(),
    };

    render(<App />);

    expect(screen.getByText(/checking the current Python-owned revision/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Retry backend and route data" }),
    ).toBeDisabled();
  });

  it("rejects mock-filled critical route data even with a current envelope", () => {
    mocked.controlCenterState = {
      status: "ready",
      data: backendData("mock_fallback"),
      error: null,
    };

    render(<App />);

    expect(
      screen.getByText("CRITICAL_ROUTE_READ_MODEL_UNVERIFIED"),
    ).toBeInTheDocument();
    expect(screen.queryByText("Mock fallback active")).not.toBeInTheDocument();
  });

  it("renders the critical route only when envelope and route data are current", () => {
    render(<App />);

    expect(screen.queryByText(/not showing unverified product state/i)).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Today" })).toBeInTheDocument();
  });

  it("routes the critical Morning Briefing alias to the briefing surface", () => {
    window.history.pushState({}, "", "/morning-briefing");
    const data = backendData("backend_owned");
    data.routeStates["/briefing"].state = "backend_owned";
    mocked.controlCenterState = { status: "ready", data, error: null };

    render(<App />);

    expect(screen.getByRole("heading", { name: "Morning Briefing" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Dashboard" })).not.toBeInTheDocument();
  });

  it("canonicalizes trailing slashes before critical route admission", () => {
    window.history.pushState({}, "", "/today/");

    render(<App />);

    expect(screen.getByRole("heading", { name: "Today" })).toBeInTheDocument();
    expect(
      screen.queryByText(/not showing unverified product state/i),
    ).not.toBeInTheDocument();
  });

  it("admits a valid first-run envelope only to onboarding surfaces", () => {
    window.history.pushState({}, "", "/setup");
    const data = backendData("backend_owned");
    data.routeStates["/setup"].state = "backend_owned";
    data.routeStates["/settings"].state = "backend_owned";
    mocked.controlCenterState = {
      status: "ready",
      data,
      error: null,
      snapshotRef: "proof-ref:truth:first-run",
      retry: vi.fn(),
    };
    mocked.truthState = {
      status: "onboarding",
      truth: {
        backend_revision_ref: lastVerified.backendRevisionRef,
        envelope_integrity_ref: "proof-ref:truth:first-run",
      },
      errorRef: "BACKEND_TRUTH_EVIDENCE_INCOMPLETE",
      lastVerified: null,
      retry: vi.fn(),
    };

    render(<App />);

    expect(
      screen.getByRole("heading", { name: /macOS Setup Assistant/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/not showing unverified product state/i),
    ).not.toBeInTheDocument();
  });

  it("admits the exact Action Inbox bootstrap lane during first run", () => {
    window.history.pushState({}, "", "/actions");
    const data = backendData("backend_owned");
    mocked.controlCenterState = {
      status: "ready",
      data,
      error: null,
      snapshotRef: "proof-ref:truth:first-run",
      retry: vi.fn(),
    };
    mocked.truthState = {
      status: "onboarding",
      truth: {
        backend_revision_ref: lastVerified.backendRevisionRef,
        envelope_integrity_ref: "proof-ref:truth:first-run",
      },
      errorRef: "BACKEND_TRUTH_EVIDENCE_INCOMPLETE",
      lastVerified: null,
      retry: vi.fn(),
    };

    render(<App />);

    expect(
      screen.queryByText(/not showing unverified product state/i),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Action Inbox" }),
    ).toBeInTheDocument();
  });

  it("admits only the canonical Settings authority bootstrap during first run", () => {
    window.history.pushState({}, "", "/settings");
    const data = backendData("backend_owned");
    data.settingsStatus.authority_lease_state.backend_owned = true;
    const askBeforeChanges =
      data.settingsStatus.authority_lease_state.mode_catalog.find(
        (entry) => entry.mode === "ask_before_changes",
      );
    if (!askBeforeChanges) {
      throw new Error("missing ask-before-changes authority mode fixture");
    }
    askBeforeChanges.issue_ready = true;
    askBeforeChanges.requires_mission_ref = false;
    mocked.controlCenterState = {
      status: "ready",
      data,
      error: null,
      snapshotRef: "proof-ref:truth:first-run",
      retry: vi.fn(),
    };
    mocked.truthState = {
      status: "onboarding",
      truth: {
        backend_revision_ref: lastVerified.backendRevisionRef,
        envelope_integrity_ref: "proof-ref:truth:first-run",
      },
      errorRef: "BACKEND_TRUTH_EVIDENCE_INCOMPLETE",
      lastVerified: null,
      retry: vi.fn(),
    };

    render(<App />);

    expect(
      screen.queryByText(/not showing unverified product state/i),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Settings" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Ask before changes" }),
    ).toBeEnabled();
  });

  it("keeps the read-only workspace Settings shell closed during first run", async () => {
    window.history.pushState({}, "", "/workspace/settings");
    mocked.truthState = {
      status: "onboarding",
      truth: {
        backend_revision_ref: lastVerified.backendRevisionRef,
        envelope_integrity_ref: "proof-ref:truth:first-run",
      },
      errorRef: "BACKEND_TRUTH_EVIDENCE_INCOMPLETE",
      lastVerified: null,
      retry: vi.fn(),
    };

    render(<App />);

    expect(
      await screen.findByRole("heading", {
        name: "Control Center is not showing unverified product state",
      }),
    ).toBeInTheDocument();
  });

  it("keeps non-onboarding critical surfaces closed on first run", () => {
    mocked.truthState = {
      status: "onboarding",
      truth: {
        backend_revision_ref: lastVerified.backendRevisionRef,
        envelope_integrity_ref: "proof-ref:truth:first-run",
      },
      errorRef: "BACKEND_TRUTH_EVIDENCE_INCOMPLETE",
      lastVerified: null,
      retry: vi.fn(),
    };

    render(<App />);

    expect(screen.getByText(/fresh local state/i)).toBeInTheDocument();
    expect(
      screen
        .getAllByRole("link", { name: "Setup" })
        .some((link) => link.getAttribute("href") === "/setup"),
    ).toBe(true);
    expect(screen.queryByRole("heading", { name: "Today" })).not.toBeInTheDocument();
  });

  it("retries truth and route data together", async () => {
    const truthRetry = vi.fn().mockResolvedValue(undefined);
    const dataRetry = vi.fn();
    mocked.truthState = {
      status: "degraded",
      truth: null,
      errorRef: "BACKEND_TRUTH_STALE",
      lastVerified,
      retry: truthRetry,
    };
    mocked.controlCenterState = {
      status: "loading",
      data: null,
      error: null,
      snapshotRef: null,
      retry: dataRetry,
    };

    render(<App />);
    screen
      .getByRole("button", { name: "Retry backend and route data" })
      .click();

    expect(truthRetry).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(dataRetry).toHaveBeenCalledTimes(1));
  });

  it("fails closed when a shared Founder Loop read model falls back", () => {
    window.history.pushState({}, "", "/proof");
    const data = backendData("backend_owned");
    data.routeStates["/proof"].state = "backend_owned";
    data.routeStates["/evidence"].state = "mock_fallback";
    mocked.controlCenterState = { status: "ready", data, error: null };

    render(<App />);

    expect(
      screen.getByText("CRITICAL_ROUTE_READ_MODEL_UNVERIFIED"),
    ).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Proof" })).not.toBeInTheDocument();
  });

  it("keeps a critical route available when only unrelated auxiliary reads fall back", () => {
    const data = backendData("backend_owned");
    data.connection.state = "degraded";
    data.connection.usingMockData = true;
    data.connection.warnings = ["PARTIAL_MOCK_FALLBACK"];
    mocked.controlCenterState = { status: "ready", data, error: null };

    render(<App />);

    expect(
      screen.queryByText("CRITICAL_ROUTE_READ_MODEL_UNVERIFIED"),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Today" })).toBeInTheDocument();
  });

  it("fails closed when a directly rendered auxiliary read model falls back", () => {
    const data = backendData("backend_owned");
    data.routeStates["/chat"].state = "mock_fallback";
    mocked.controlCenterState = { status: "ready", data, error: null };

    render(<App />);

    expect(
      screen.getByText("CRITICAL_ROUTE_READ_MODEL_UNVERIFIED"),
    ).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Today" })).not.toBeInTheDocument();
  });

  it.each([
    ["/critical/dashboard-read-model", "dashboard"],
    ["/runtime", "runtime readiness"],
  ])(
    "fails the Evidence route closed when %s falls back",
    (route, _label) => {
      window.history.pushState({}, "", "/evidence");
      const data = backendData("backend_owned");
      data.routeStates[route].state = "mock_fallback";
      mocked.controlCenterState = { status: "ready", data, error: null };

      render(<App />);

      expect(
        screen.getByText("CRITICAL_ROUTE_READ_MODEL_UNVERIFIED"),
      ).toBeInTheDocument();
      expect(
        screen.queryByRole("heading", { name: "Evidence" }),
      ).not.toBeInTheDocument();
    },
  );

  it.each(["/today", "/actions", "/evidence"])(
    "fails the Settings route closed when %s falls back",
    (route) => {
      window.history.pushState({}, "", "/settings");
      const data = backendData("backend_owned");
      data.routeStates[route].state = "mock_fallback";
      mocked.controlCenterState = { status: "ready", data, error: null };

      render(<App />);

      expect(
        screen.getByText("CRITICAL_ROUTE_READ_MODEL_UNVERIFIED"),
      ).toBeInTheDocument();
      expect(
        screen.queryByRole("heading", { name: "Settings" }),
      ).not.toBeInTheDocument();
    },
  );

  it("gates Settings and authority controls on the backend truth envelope", () => {
    window.history.pushState({}, "", "/settings");
    mocked.truthState = {
      status: "degraded",
      truth: null,
      errorRef: "BACKEND_TRUTH_STALE",
      lastVerified,
      retry: vi.fn(),
    };

    render(<App />);

    expect(
      screen.getByRole("heading", {
        name: "Settings is not showing unverified product state",
      }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Full workspace" }),
    ).not.toBeInTheDocument();
  });

  it("does not render mock workspace product content while critical data loads", async () => {
    window.history.pushState({}, "", "/workspace/today");
    mocked.controlCenterState = { status: "loading", data: null, error: null };

    render(<App />);

    expect(
      await screen.findByText(/is loading local route state$/),
    ).toBeInTheDocument();
    expect(screen.queryByText("Preview data")).not.toBeInTheDocument();
  });

  it("excludes legacy mock approval cards from the critical approvals route", () => {
    window.history.pushState({}, "", "/approvals");
    const data = backendData("backend_owned");
    data.routeStates["/approvals"] = {
      ...data.routeStates["/actions"],
      route: "/approvals",
      surfaceLabel: "Approvals",
      state: "backend_owned",
    };
    data.routeStates["/settings"].state = "backend_owned";
    mocked.controlCenterState = {
      status: "ready",
      data,
      error: null,
      snapshotRef: "proof-ref:truth:current",
      retry: vi.fn(),
    };

    render(<App />);

    expect(screen.queryByText("Preview-only approval cards")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Legacy approval preview rows")).not.toBeInTheDocument();
  });

  it("excludes legacy mock evidence records from the critical evidence route", () => {
    window.history.pushState({}, "", "/evidence");
    const data = backendData("backend_owned");
    data.routeStates["/runs"] = {
      ...data.routeStates["/evidence"],
      route: "/runs",
      surfaceLabel: "Runs",
      state: "backend_owned",
    };
    mocked.controlCenterState = {
      status: "ready",
      data,
      error: null,
      snapshotRef: "proof-ref:truth:current",
      retry: vi.fn(),
    };

    render(<App />);

    expect(screen.queryByRole("heading", { name: "Evidence Viewer" })).not.toBeInTheDocument();
    expect(screen.queryByText("mock_evidence_ref_001")).not.toBeInTheDocument();
  });
});
