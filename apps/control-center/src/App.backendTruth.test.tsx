import { cleanup, render, screen } from "@testing-library/react";
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
  data.routeStates["/today"].state = routeState;
  return data;
}

beforeEach(() => {
  window.history.pushState({}, "", "/today");
  mocked.controlCenterState = {
    status: "ready",
    data: backendData("backend_owned"),
    error: null,
  };
  mocked.truthState = {
    status: "ready",
    truth: {},
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
    expect(screen.getByRole("button", { name: "Retry backend truth" })).toBeEnabled();
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
    expect(screen.getByRole("button", { name: "Retry backend truth" })).toBeDisabled();
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

  it("does not render mock workspace product content while critical data loads", async () => {
    window.history.pushState({}, "", "/workspace/today");
    mocked.controlCenterState = { status: "loading", data: null, error: null };

    render(<App />);

    expect(
      await screen.findByText(/is loading local route state$/),
    ).toBeInTheDocument();
    expect(screen.queryByText("Preview data")).not.toBeInTheDocument();
  });
});
