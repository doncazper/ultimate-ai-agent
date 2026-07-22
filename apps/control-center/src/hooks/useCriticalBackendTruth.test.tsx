import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ControlCenterBackendTruth } from "../api/types";
import { useCriticalBackendTruth } from "./useCriticalBackendTruth";

function truth(
  revision: string,
  evidenceStatus: ControlCenterBackendTruth["evidence_binding"]["status"] = "unverified_incomplete",
): ControlCenterBackendTruth {
  return {
    schema_version: "uaa-control-center-backend-truth.v1",
    source_ref: "source-ref:python-core:control-center-backend-truth",
    generated_at: "2026-07-22T18:00:00Z",
    valid_until: "2026-07-22T18:00:45Z",
    backend_revision_ref: revision,
    source_revision_bound: true,
    critical_surfaces: [],
    evidence_binding: {
      status: evidenceStatus,
      acceptance_schema_version: "dogfood-live-loop-acceptance.v1",
      acceptance_integrity_ref: "proof-ref:test",
      action_refs: [],
      run_refs: [],
      proof_refs: [],
      receipt_refs:
        evidenceStatus === "invalid_evidence" ? ["receipt-ref:corrupt-proof"] : [],
      evidence_refs: [],
      memory_candidate_refs: [],
      issue_refs: ["issue-ref:test"],
    },
    authority_posture: {
      mode_ref: "authority-mode-ref:read-only-local",
      approval_refs_are_identifiers_only: true,
      control_center_grants_authority: false,
      runtime_model_call_enabled: false,
      browser_or_web_execution_enabled: false,
      connector_write_enabled: false,
      shell_subprocess_execution_enabled: false,
      background_autonomy_enabled: false,
      production_authority_enabled: false,
    },
    cli_ref: "cli-ref:test",
    safe_refs_only: true,
    redacted_summaries_only: true,
    raw_content_included: false,
    raw_paths_included: false,
    envelope_integrity_ref: "proof-ref:test",
  };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

afterEach(() => vi.useRealTimers());

describe("useCriticalBackendTruth", () => {
  it("ignores an older refresh that resolves after the newest generation", async () => {
    const first = deferred<ControlCenterBackendTruth>();
    const second = deferred<ControlCenterBackendTruth>();
    const loader = vi
      .fn<() => Promise<ControlCenterBackendTruth>>()
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise);
    const { result } = renderHook(() => useCriticalBackendTruth(true, loader));

    act(() => result.current.retry());
    await act(async () => second.resolve(truth("commit-ref:git:new")));
    await waitFor(() => expect(result.current.status).toBe("ready"));
    await act(async () => first.resolve(truth("commit-ref:git:old")));

    expect(result.current.status).toBe("ready");
    expect(result.current.lastVerified?.backendRevisionRef).toBe("commit-ref:git:new");
  });

  it("preserves last verified provenance when a later backend read fails", async () => {
    const loader = vi
      .fn<() => Promise<ControlCenterBackendTruth>>()
      .mockResolvedValueOnce(truth("commit-ref:git:verified"))
      .mockRejectedValueOnce(new Error("BACKEND_TRUTH_STALE"));
    const { result } = renderHook(() => useCriticalBackendTruth(true, loader));
    await waitFor(() => expect(result.current.status).toBe("ready"));

    await act(async () => result.current.retry());
    await waitFor(() => expect(result.current.status).toBe("degraded"));

    expect(result.current.errorRef).toBe("BACKEND_TRUTH_STALE");
    expect(result.current.lastVerified?.backendRevisionRef).toBe(
      "commit-ref:git:verified",
    );
  });

  it("fails closed when a current envelope reports corrupt durable evidence", async () => {
    const loader = vi
      .fn<() => Promise<ControlCenterBackendTruth>>()
      .mockResolvedValueOnce(truth("commit-ref:git:verified"))
      .mockResolvedValueOnce(
        truth("commit-ref:git:verified", "invalid_evidence"),
      );
    const { result } = renderHook(() => useCriticalBackendTruth(true, loader));
    await waitFor(() => expect(result.current.status).toBe("ready"));

    await act(async () => result.current.retry());
    await waitFor(() => expect(result.current.status).toBe("degraded"));

    expect(result.current.errorRef).toBe("BACKEND_TRUTH_EVIDENCE_INVALID");
    expect(result.current.lastVerified?.backendRevisionRef).toBe(
      "commit-ref:git:verified",
    );
  });
});
