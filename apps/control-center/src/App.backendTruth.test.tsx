import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ControlCenterData } from "./api/types";
import { mockControlCenterData } from "./mocks/controlCenterData";

const mocked = vi.hoisted(() => ({
  controlCenterState: {} as unknown,
  truthState: {} as unknown,
}));

vi.mock("./hooks/useControlCenterData", () => ({
  useControlCenterData: () => mocked.controlCenterState,
}));

vi.mock("./hooks/useCriticalBackendTruth", () => ({
  useCriticalBackendTruth: () => mocked.truthState,
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
  for (const route of ["/today", "/actions", "/evidence", "/settings"]) {
    data.routeStates[route].state = "backend_owned";
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
});

afterEach(() => cleanup());

describe("critical backend truth boundary", () => {
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

  it("fails closed when any auxiliary read model used by a critical page falls back", () => {
    const data = backendData("backend_owned");
    data.connection.state = "degraded";
    data.connection.usingMockData = true;
    data.connection.warnings = ["PARTIAL_MOCK_FALLBACK"];
    mocked.controlCenterState = { status: "ready", data, error: null };

    render(<App />);

    expect(
      screen.getByText("CRITICAL_ROUTE_READ_MODEL_UNVERIFIED"),
    ).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Today" })).not.toBeInTheDocument();
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
