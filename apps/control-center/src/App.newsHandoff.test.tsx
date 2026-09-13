import { cleanup, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

const mocked = vi.hoisted(() => ({
  truthEnabled: false,
  readArguments: [] as unknown[],
}));

vi.mock("./hooks/useControlCenterData", () => ({
  useControlCenterData: (...args: unknown[]) => {
    mocked.readArguments = args;
    return {
      status: "loading", data: null, error: null, snapshotRef: null, retry: vi.fn(),
    };
  },
}));

vi.mock("./hooks/useCriticalBackendTruth", () => ({
  useCriticalBackendTruth: (enabled: boolean) => {
    mocked.truthEnabled = enabled;
    return {
      status: "ready",
      truth: {
        envelope_integrity_ref: `proof-ref:backend-truth-envelope:sha256:${"8".repeat(64)}`,
        backend_revision_ref: `commit-ref:git:${"1".repeat(40)}`,
        backend_instance_ref: `backend-instance-ref:control-center:${"2".repeat(32)}`,
      },
      errorRef: null, lastVerified: null, retry: vi.fn(),
    };
  },
}));

import { App } from "./App";

beforeEach(() => {
  mocked.truthEnabled = false;
  mocked.readArguments = [];
});

afterEach(() => {
  cleanup();
  window.history.pushState({}, "", "/");
});

it.each(["/workspace/today", "/today", "/briefing", "/morning-briefing"])(
  "keeps the real %s route on the strict News handoff read scope",
  async (path) => {
    window.history.pushState({}, "", path);
    render(<App />);
    await waitFor(() => {
      expect(mocked.truthEnabled).toBe(true);
      expect(mocked.readArguments[0]).toBe(true);
      expect(mocked.readArguments[1]).toEqual({
        snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"8".repeat(64)}`,
        backendRevisionRef: `commit-ref:git:${"1".repeat(40)}`,
        backendInstanceRef: `backend-instance-ref:control-center:${"2".repeat(32)}`,
      });
      expect(mocked.readArguments[2]).toBe("news-handoff");
    });
  },
);
