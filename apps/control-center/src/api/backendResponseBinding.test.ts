import { afterEach, describe, expect, it, vi } from "vitest";
import {
  fetchFounderActionsInbox,
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
});
