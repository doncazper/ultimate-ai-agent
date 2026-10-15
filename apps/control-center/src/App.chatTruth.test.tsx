import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ControlCenterData } from "./api/types";
import { mockControlCenterData } from "./mocks/controlCenterData";

const mocked = vi.hoisted(() => ({
  controlCenterState: {} as unknown,
  truthState: {} as unknown,
  truthEnabled: false,
  controlCenterScope: "",
}));

vi.mock("./hooks/useControlCenterData", () => ({
  useControlCenterData: (_enabled: boolean, _binding: unknown, scope: string) => {
    mocked.controlCenterScope = scope;
    return mocked.controlCenterState;
  },
}));

vi.mock("./hooks/useCriticalBackendTruth", () => ({
  useCriticalBackendTruth: (enabled: boolean) => {
    mocked.truthEnabled = enabled;
    return mocked.truthState;
  },
}));

import { App } from "./App";

function backendData(routeState: "backend_owned" | "mock_fallback") {
  const data = structuredClone(mockControlCenterData) as ControlCenterData;
  data.connection.state = "online";
  data.connection.usingMockData = false;
  data.connection.warnings = [];
  for (const route of [
    "/today", "/actions", "/approvals", "/chat",
    "/critical/dashboard-read-model", "/evidence",
    "/critical/manifest-read-model", "/critical/provider-catalog-read-model",
    "/runs", "/runtime", "/settings",
  ]) {
    data.routeStates[route] = {
      ...data.routeStates["/today"], route, surfaceLabel: route, state: "backend_owned",
    };
  }
  data.routeStates["/today"].state = routeState;
  return data;
}

beforeEach(() => {
  window.history.pushState({}, "", "/chat");
  mocked.controlCenterState = {
    status: "ready", data: backendData("backend_owned"), error: null,
  };
  mocked.truthState = {
    status: "onboarding",
    truth: {
      backend_revision_ref: `commit-ref:git:${"1".repeat(40)}`,
      envelope_integrity_ref: "proof-ref:truth:first-run",
    },
    errorRef: "BACKEND_TRUTH_EVIDENCE_INCOMPLETE",
    lastVerified: null,
    retry: vi.fn(),
  };
  mocked.truthEnabled = false;
  mocked.controlCenterScope = "";
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("first-run Chat backend truth boundary", () => {
  it.each(["backend_owned", "mock_fallback"] as const)(
    "admits first-run Chat only with %s route data",
    async (routeState) => {
      mocked.controlCenterState = {
        status: "ready", data: backendData(routeState), error: null,
      };
      const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
        new Response("{}", { status: 401 }),
      );

      render(<App />);

      expect(mocked.truthEnabled).toBe(true);
      expect(mocked.controlCenterScope).toBe("chat");
      if (routeState === "backend_owned") {
        expect(screen.getByRole("heading", { name: "Talk to your model" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
        expect(screen.getByRole("link", { name: /^Chat$/ })).toHaveAttribute("href", "/chat");
        await waitFor(() => expect(fetchMock).toHaveBeenCalled());
        expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith("/v1/chat/completions"))).toBe(false);
      } else {
        expect(screen.getByText("CRITICAL_ROUTE_READ_MODEL_UNVERIFIED")).toBeInTheDocument();
        expect(screen.queryByRole("heading", { name: "Talk to your model" })).not.toBeInTheDocument();
        expect(fetchMock).not.toHaveBeenCalled();
      }
    },
  );

  it.each([
    "BACKEND_TRUTH_STALE", "BACKEND_TRUTH_EVIDENCE_INVALID",
    "BACKEND_TRUTH_STORAGE_UNAVAILABLE", "BACKEND_TRUTH_REVISION_UNBOUND",
  ])("keeps first-run Chat closed for %s", (errorRef) => {
    mocked.truthState = {
      status: "degraded", truth: null, errorRef, lastVerified: null, retry: vi.fn(),
    };

    render(<App />);

    expect(screen.getByText(errorRef)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Talk to your model" })).not.toBeInTheDocument();
  });

  it("mounts secondary Chat requests only when their disclosure is opened", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      new Response("{}", { status: 401 }),
    );
    const requested = (path: string) => fetchMock.mock.calls.some(([url]) => String(url).endsWith(path));

    render(<App />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(requested("/control-center/chat/workspace")).toBe(false);
    expect(requested("/control-center/turn-router/preview")).toBe(false);

    fireEvent.click(screen.getByText("Details", { selector: "summary" }));
    await waitFor(() => expect(requested("/control-center/turn-router/preview")).toBe(true));
    expect(requested("/control-center/chat/workspace")).toBe(false);

    fireEvent.click(screen.getByText("Content-free draft checkpoints", { selector: "summary" }));
    await waitFor(() => expect(requested("/control-center/chat/workspace")).toBe(true));
    expect(requested("/v1/chat/completions")).toBe(false);
  });

  it("lets the operator retry a failed Chat read without sending a model turn", () => {
    const retry = vi.fn();
    mocked.controlCenterState = {
      status: "error", data: null, error: "Local read unavailable.", retry,
    };
    const fetchMock = vi.spyOn(globalThis, "fetch");

    render(<App />);

    expect(screen.queryByRole("heading", { name: "Talk to your model" })).not.toBeInTheDocument();
    expect(retry).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Retry local read" }));
    expect(retry).toHaveBeenCalledTimes(1);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
