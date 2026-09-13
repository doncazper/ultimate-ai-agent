import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { CriticalBackendTruthState } from "./hooks/useCriticalBackendTruth";
import { preview, workspace } from "./test/newsSignalsAdoptionFixture";

const mocked = vi.hoisted(() => ({
  truthState: {} as unknown,
  truthEnabled: false,
  loadNewsSignalsAdoptionWorkspace: vi.fn(),
  previewNewsSignalsAdoptionMutation: vi.fn(),
  captureNewsSignalsAdoptionApproval: vi.fn(),
  commitNewsSignalsAdoptionMutation: vi.fn(),
}));

vi.mock("./hooks/useCriticalBackendTruth", () => ({
  useCriticalBackendTruth: (enabled: boolean) => {
    mocked.truthEnabled = enabled;
    return mocked.truthState;
  },
}));
vi.mock("./api/client", async (importOriginal) => ({
  ...await importOriginal<typeof import("./api/client")>(),
  loadNewsSignalsAdoptionWorkspace: mocked.loadNewsSignalsAdoptionWorkspace,
  previewNewsSignalsAdoptionMutation: mocked.previewNewsSignalsAdoptionMutation,
  captureNewsSignalsAdoptionApproval: mocked.captureNewsSignalsAdoptionApproval,
  commitNewsSignalsAdoptionMutation: mocked.commitNewsSignalsAdoptionMutation,
}));

// Exercise the actual App route, panel and context provider together. Mocking
// the binding hook here would conceal the missing-provider regression.
import { App } from "./App";

const binding = {
  snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"8".repeat(64)}`,
  backendRevisionRef: `commit-ref:git:${"1".repeat(40)}`,
  backendInstanceRef: `backend-instance-ref:control-center:${"2".repeat(32)}`,
};

function truthState(status: CriticalBackendTruthState["status"], errorRef: string | null = null) {
  return {
    status,
    truth: status === "ready" || status === "onboarding" ? {
      envelope_integrity_ref: binding.snapshotRef,
      backend_revision_ref: binding.backendRevisionRef,
      backend_instance_ref: binding.backendInstanceRef,
    } : null,
    errorRef,
    lastVerified: null,
    retry: vi.fn(),
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  window.history.pushState({}, "", "/news");
  mocked.truthState = truthState("ready");
  mocked.truthEnabled = false;
  mocked.loadNewsSignalsAdoptionWorkspace.mockResolvedValue(workspace);
  mocked.previewNewsSignalsAdoptionMutation.mockResolvedValue(preview);
  mocked.captureNewsSignalsAdoptionApproval.mockResolvedValue({});
  mocked.commitNewsSignalsAdoptionMutation.mockResolvedValue({});
});

afterEach(() => {
  cleanup();
  window.history.pushState({}, "", "/");
});

async function reviewSource() {
  fireEvent.change(await screen.findByLabelText("Source name"), {
    target: { value: "Queue project release notes" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Review source" }));
  return screen.findByRole("button", { name: "Confirm and save" });
}

describe("normal News route backend binding", () => {
  it.each(["ready", "onboarding"] as const)(
    "binds explicit source confirmation to the current %s backend",
    async (status) => {
      mocked.truthState = truthState(status);
      render(<App />);
      const save = await reviewSource();

      expect(mocked.truthEnabled).toBe(true);
      expect(save).toBeEnabled();
      expect(mocked.captureNewsSignalsAdoptionApproval).not.toHaveBeenCalled();
      expect(mocked.commitNewsSignalsAdoptionMutation).not.toHaveBeenCalled();
      fireEvent.click(save);

      expect(await screen.findByText("The reviewed local News change was saved.")).toBeInTheDocument();
      const [request, idempotencyRef] = mocked.previewNewsSignalsAdoptionMutation.mock.calls[0];
      expect(mocked.captureNewsSignalsAdoptionApproval).toHaveBeenCalledExactlyOnceWith(
        request, preview, idempotencyRef, binding,
      );
      expect(mocked.commitNewsSignalsAdoptionMutation).toHaveBeenCalledExactlyOnceWith(
        request, preview, idempotencyRef, binding,
      );
    },
  );

  it.each(["BACKEND_TRUTH_STALE", "BACKEND_TRUTH_EVIDENCE_INVALID", "BACKEND_TRUTH_STORAGE_UNAVAILABLE"])(
    "does not admit News or save against %s",
    (errorRef) => {
      mocked.truthState = truthState("degraded", errorRef);
      render(<App />);
      expect(mocked.truthEnabled).toBe(true);
      expect(screen.getByText(errorRef)).toBeInTheDocument();
      expect(screen.queryByLabelText("Source name")).not.toBeInTheDocument();
      expect(mocked.loadNewsSignalsAdoptionWorkspace).not.toHaveBeenCalled();
      expect(mocked.captureNewsSignalsAdoptionApproval).not.toHaveBeenCalled();
      expect(mocked.commitNewsSignalsAdoptionMutation).not.toHaveBeenCalled();
    },
  );

  it("waits for backend truth before reading the News workspace", () => {
    mocked.truthState = truthState("loading");
    render(<App />);
    expect(screen.getByRole("button", { name: "Retry backend and route data" })).toBeDisabled();
    expect(mocked.loadNewsSignalsAdoptionWorkspace).not.toHaveBeenCalled();
  });

  it("drops a pending confirmation on expiry and requires a fresh review after recovery", async () => {
    const view = render(<App />);
    expect(await reviewSource()).toBeEnabled();

    mocked.truthState = truthState("degraded", "BACKEND_TRUTH_STALE");
    view.rerender(<App />);
    expect(screen.queryByRole("button", { name: "Confirm and save" })).not.toBeInTheDocument();
    mocked.truthState = truthState("ready");
    view.rerender(<App />);
    await screen.findByLabelText("Source name");
    expect(screen.queryByRole("button", { name: "Confirm and save" })).not.toBeInTheDocument();
    expect(mocked.captureNewsSignalsAdoptionApproval).not.toHaveBeenCalled();
    expect(mocked.commitNewsSignalsAdoptionMutation).not.toHaveBeenCalled();
    await waitFor(() => expect(mocked.loadNewsSignalsAdoptionWorkspace).toHaveBeenCalledTimes(2));
  });
});
