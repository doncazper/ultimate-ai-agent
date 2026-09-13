import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

const mocked = vi.hoisted(() => ({
  truthStatus: "ready",
  readStatus: "error",
  readArguments: [] as unknown[],
  retry: vi.fn(),
}));

vi.mock("./hooks/useControlCenterData", () => ({
  useControlCenterData: (...args: unknown[]) => {
    mocked.readArguments = args;
    return {
      status: mocked.readStatus, data: null, error: "Local read failed safely.",
      snapshotRef: null, retry: mocked.retry,
    };
  },
}));
vi.mock("./hooks/useCriticalBackendTruth", () => ({
  useCriticalBackendTruth: () => ({
    status: mocked.truthStatus,
    truth: mocked.truthStatus === "ready" ? {
      envelope_integrity_ref: `proof-ref:backend-truth-envelope:sha256:${"8".repeat(64)}`,
      backend_revision_ref: `commit-ref:git:${"1".repeat(40)}`,
      backend_instance_ref: `backend-instance-ref:control-center:${"2".repeat(32)}`,
    } : null,
    errorRef: mocked.truthStatus === "degraded" ? "BACKEND_TRUTH_STALE" : null,
    lastVerified: null, retry: vi.fn(),
  }),
}));

import { App } from "./App";

beforeEach(() => {
  mocked.truthStatus = "ready";
  mocked.readStatus = "error";
  mocked.readArguments = [];
  mocked.retry.mockClear();
});
afterEach(() => { cleanup(); window.history.pushState({}, "", "/"); });

it.each(["/workspace/today", "/today", "/briefing", "/morning-briefing"])(
  "offers one operator-triggered bound read retry on %s",
  async (path) => {
    window.history.pushState({}, "", path);
    const view = render(<App />);
    const retry = await screen.findByRole("button", { name: "Retry local read" });
    expect(mocked.retry).not.toHaveBeenCalled();
    expect(mocked.readArguments[0]).toBe(true);
    expect(mocked.readArguments[1]).toEqual({
      snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"8".repeat(64)}`,
      backendRevisionRef: `commit-ref:git:${"1".repeat(40)}`,
      backendInstanceRef: `backend-instance-ref:control-center:${"2".repeat(32)}`,
    });
    expect(mocked.readArguments[2]).toBe("news-handoff");
    fireEvent.click(retry);
    expect(mocked.retry).toHaveBeenCalledTimes(1);
    mocked.readStatus = "loading";
    view.rerender(<App />);
    await waitFor(() => expect(screen.queryByRole("button", { name: "Retry local read" })).not.toBeInTheDocument());
    expect(mocked.retry).toHaveBeenCalledTimes(1);
  },
);

it.each(["/workspace/today", "/today", "/briefing"])(
  "does not retry %s against expired backend truth",
  async (path) => {
    window.history.pushState({}, "", path);
    mocked.truthStatus = "degraded";
    render(<App />);
    await screen.findByText("BACKEND_TRUTH_STALE");
    expect(screen.queryByRole("button", { name: "Retry local read" })).not.toBeInTheDocument();
    expect(mocked.retry).not.toHaveBeenCalled();
    expect(mocked.readArguments[0]).toBe(false);
  },
);

it("does not expand read recovery to unrelated routes", async () => {
  window.history.pushState({}, "", "/plans");
  render(<App />);
  await screen.findByText("Local read failed safely.");
  expect(screen.queryByRole("button", { name: "Retry local read" })).not.toBeInTheDocument();
  expect(mocked.retry).not.toHaveBeenCalled();
});
