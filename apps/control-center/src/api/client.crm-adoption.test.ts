import { afterEach, describe, expect, it, vi } from "vitest";
import {
  commitCrmAdoptionMutation,
  commitCrmPortableRestore,
  type BackendTruthReadBinding,
} from "./client";
import { API_ENDPOINTS } from "./endpoints";
import type {
  CrmAdoptionMutationPreview,
  CrmAdoptionMutationRequest,
  CrmPortableBackup,
  CrmPortableRestorePreview,
} from "./types";

const binding: BackendTruthReadBinding = {
  snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"8".repeat(64)}`,
  backendRevisionRef: `commit-ref:git:${"1".repeat(40)}`,
  backendInstanceRef:
    "backend-instance-ref:control-center:22222222222222222222222222222222",
};

const mutation = {
  action: "undo",
  expected_revision: 4,
} as CrmAdoptionMutationRequest;

const mutationPreview = {
  preview_ref: "crm-mutation-preview-ref:test",
  approval_ref: "approval-ref:crm:test",
} as CrmAdoptionMutationPreview;

const backup = {
  ciphertext_fingerprint_ref: "ciphertext-ref:crm-backup:test",
} as CrmPortableBackup;

const restorePreview = {
  preview_ref: "crm-restore-preview-ref:test",
  approval_ref: "approval-ref:crm-restore:test",
} as CrmPortableRestorePreview;

describe("CRM adoption mutation provenance", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("binds local mutation and restore commits to exact backend truth", async () => {
    const fetchMock = vi.fn(
      async (_url: string | URL | Request, _init?: RequestInit) =>
        new Response(
          JSON.stringify({
            success: true,
            data: { receipt_ref: "receipt-ref:crm-adoption:test" },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await commitCrmAdoptionMutation(
      mutation,
      mutationPreview,
      "idempotency-ref:crm-adoption:test-mutation",
      binding,
    );
    await commitCrmPortableRestore(
      backup,
      "correct horse battery staple",
      restorePreview,
      "idempotency-ref:crm-adoption:test-restore",
      binding,
    );

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      API_ENDPOINTS.crmAdoptionCommit,
      API_ENDPOINTS.crmAdoptionRestore,
    ]);
    for (const [, init] of fetchMock.mock.calls) {
      const headers = init?.headers as Record<string, string>;
      expect(headers["X-UAA-Operator-Confirmed"]).toBe("true");
      expect(headers["X-UAA-Control-Center-Mutation-Binding"]).toBe(
        "backend-truth.v1",
      );
      expect(headers["X-UAA-Expected-Backend-Truth-Ref"]).toBe(
        binding.snapshotRef,
      );
      expect(headers["X-UAA-Expected-Backend-Revision-Ref"]).toBe(
        binding.backendRevisionRef,
      );
      expect(headers["X-UAA-Expected-Backend-Instance-Ref"]).toBe(
        binding.backendInstanceRef,
      );
    }
  });

  it("fails closed before a commit when backend truth is unavailable", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      commitCrmAdoptionMutation(
        mutation,
        mutationPreview,
        "idempotency-ref:crm-adoption:missing-binding",
        null,
      ),
    ).rejects.toThrow("BACKEND_TRUTH_MUTATION_BINDING_REQUIRED");
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
