import { afterEach, describe, expect, it, vi } from "vitest";
import {
  buildLocalTaskCommitRequest,
  commitLocalTask,
  fetchFounderActionsInbox,
  previewAuthorityDecision,
  submitActionDecision,
  validateBackendResponseBinding,
  withBackendTruthMutationHeaders,
  type BackendTruthReadBinding,
} from "./client";

const binding: BackendTruthReadBinding = {
  snapshotRef: "proof-ref:backend-truth-envelope:sha256:current",
  backendRevisionRef: `commit-ref:git:${"1".repeat(40)}`,
  backendInstanceRef:
    "backend-instance-ref:control-center:22222222222222222222222222222222",
};

function headers(overrides: Record<string, string> = {}): Headers {
  return new Headers({
    "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
    "X-UAA-Backend-Instance-Ref": binding.backendInstanceRef,
    ...overrides,
  });
}

describe("backend response provenance binding", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });
  it("accepts route data from the exact admitted backend process", () => {
    expect(() =>
      validateBackendResponseBinding(headers(), binding),
    ).not.toThrow();
  });

  it.each([
    [
      "missing revision",
      { "X-UAA-Backend-Revision-Ref": "" },
    ],
    [
      "substituted revision",
      { "X-UAA-Backend-Revision-Ref": `commit-ref:git:${"3".repeat(40)}` },
    ],
    [
      "missing instance",
      { "X-UAA-Backend-Instance-Ref": "" },
    ],
    [
      "cross-process substitution",
      {
        "X-UAA-Backend-Instance-Ref":
          "backend-instance-ref:control-center:44444444444444444444444444444444",
      },
    ],
  ])("rejects %s", (_label, overrides) => {
    expect(() =>
      validateBackendResponseBinding(headers(overrides), binding),
    ).toThrow("BACKEND_RESPONSE_PROVENANCE_MISMATCH");
  });

  it("does not require provenance for non-critical aggregate reads", () => {
    expect(() =>
      validateBackendResponseBinding(new Headers(), null),
    ).not.toThrow();
  });

  it("binds a critical mutation to the exact admitted truth envelope", () => {
    expect(
      withBackendTruthMutationHeaders(
        { Accept: "application/json" },
        binding,
      ),
    ).toEqual({
      Accept: "application/json",
      "X-UAA-Control-Center-Mutation-Binding": "backend-truth.v1",
      "X-UAA-Expected-Backend-Revision-Ref": binding.backendRevisionRef,
      "X-UAA-Expected-Backend-Instance-Ref": binding.backendInstanceRef,
      "X-UAA-Expected-Backend-Truth-Ref": binding.snapshotRef,
    });
  });

  it("fails closed before a critical mutation when no truth binding exists", () => {
    expect(() =>
      withBackendTruthMutationHeaders({ Accept: "application/json" }, null),
    ).toThrow("BACKEND_TRUTH_MUTATION_BINDING_REQUIRED");
  });

  it("rejects a post-mutation refresh from a replacement backend", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({ ok: true, result: { items: [] } }),
          {
            status: 200,
            headers: {
              "Content-Type": "application/json",
              "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
              "X-UAA-Backend-Instance-Ref":
                "backend-instance-ref:control-center:44444444444444444444444444444444",
            },
          },
        ),
      ),
    );

    await expect(fetchFounderActionsInbox(binding)).rejects.toThrow(
      "BACKEND_RESPONSE_PROVENANCE_MISMATCH",
    );
  });

  it("binds an authority preview to the admitted backend process", async () => {
    const fetchMock = vi.fn(async () =>
      new Response(
        JSON.stringify({
          ok: true,
          result: { preview_ref: "preview-ref:test" },
        }),
        {
          status: 200,
          headers: {
            "Content-Type": "application/json",
            "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
            "X-UAA-Backend-Instance-Ref": binding.backendInstanceRef,
          },
        },
      ));
    vi.stubGlobal("fetch", fetchMock);

    await previewAuthorityDecision({
      action_ref: "authority-action-ref:test",
      domain: "workspace",
      capability: "write",
      safe_summary: "Evaluate exact test authority.",
      resource_refs: ["resource-ref:test"],
      route_ref: "POST /test",
      lane_ref: "lane-ref:test",
      requested_mode: "ask_before_changes",
      draft_fallback_available: true,
      rollback_ref: "rollback-ref:test",
      safe_disable_ref: "safe-disable-ref:test",
    }, binding);

    expect(fetchMock).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          "X-UAA-Expected-Backend-Revision-Ref": binding.backendRevisionRef,
          "X-UAA-Expected-Backend-Instance-Ref": binding.backendInstanceRef,
          "X-UAA-Expected-Backend-Truth-Ref": binding.snapshotRef,
        }),
      }),
    );
  });

  it("rejects an authority preview from a replacement backend", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            ok: true,
            result: { preview_ref: "preview-ref:test" },
          }),
          {
            status: 200,
            headers: {
              "Content-Type": "application/json",
              "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
              "X-UAA-Backend-Instance-Ref":
                "backend-instance-ref:control-center:44444444444444444444444444444444",
            },
          },
        ),
      ),
    );

    await expect(previewAuthorityDecision({
      action_ref: "authority-action-ref:test",
      domain: "workspace",
      capability: "write",
      safe_summary: "Evaluate exact test authority.",
      resource_refs: ["resource-ref:test"],
      route_ref: "POST /test",
      lane_ref: "lane-ref:test",
      requested_mode: "ask_before_changes",
      draft_fallback_available: true,
      rollback_ref: "rollback-ref:test",
      safe_disable_ref: "safe-disable-ref:test",
    }, binding)).rejects.toThrow("BACKEND_RESPONSE_PROVENANCE_MISMATCH");
  });

  it("admits local-task and decision receipts from the exact backend process", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        ok: true,
        result: { receipt_ref: "receipt:local-task:bound" },
      }), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
          "X-UAA-Backend-Instance-Ref": binding.backendInstanceRef,
        },
      }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        ok: true,
        result: { receipt_ref: "receipt:decision:bound" },
      }), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
          "X-UAA-Backend-Instance-Ref": binding.backendInstanceRef,
        },
      }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(commitLocalTask(
      "founder-action:bound",
      buildLocalTaskCommitRequest(
        "founder-action:bound",
        "approval-ref:bound",
      ),
      binding,
    )).resolves.toMatchObject({ receipt_ref: "receipt:local-task:bound" });
    await expect(submitActionDecision(
      "founder-action:bound",
      "defer",
      {
        expected_revision_ref: "action-revision:bound",
        decision_reason_ref: "decision-reason-ref:bound",
        metadata_refs: ["metadata-ref:bound"],
      },
      binding,
    )).resolves.toMatchObject({ receipt_ref: "receipt:decision:bound" });
  });

  it.each([
    [
      "local-task commit",
      () => commitLocalTask(
        "founder-action:replacement",
        buildLocalTaskCommitRequest(
          "founder-action:replacement",
          "approval-ref:replacement",
        ),
        binding,
      ),
    ],
    [
      "action decision",
      () => submitActionDecision(
        "founder-action:replacement",
        "defer",
        {
          expected_revision_ref: "action-revision:replacement",
          decision_reason_ref: "decision-reason-ref:replacement",
          metadata_refs: ["metadata-ref:replacement"],
        },
        binding,
      ),
    ],
  ])("rejects a %s response from a replacement backend before body admission", async (
    _label,
    submitMutation,
  ) => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("not-json", {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
          "X-UAA-Backend-Instance-Ref":
            "backend-instance-ref:control-center:44444444444444444444444444444444",
        },
      })),
    );

    await expect(submitMutation()).rejects.toThrow(
      "BACKEND_RESPONSE_PROVENANCE_MISMATCH",
    );
  });
});
