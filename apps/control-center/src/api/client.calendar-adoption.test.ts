import { afterEach, describe, expect, it, vi } from "vitest";
import {
  captureCalendarAdoptionApproval,
  captureCalendarAdoptionRestoreApproval,
  commitCalendarAdoptionMutation,
  commitCalendarAdoptionRestore,
  type BackendTruthReadBinding,
} from "./client";
import { API_ENDPOINTS } from "./endpoints";
import type {
  CalendarAdoptionMutationPreview,
  CalendarAdoptionMutationRequest,
  CalendarAdoptionPortableBackup,
  CalendarAdoptionRestorePreview,
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
} as CalendarAdoptionMutationRequest;

const mutationPreview = {
  preview_ref: "preview-ref:calendar-adoption:test",
  approval_ref: "approval-ref:calendar-adoption:test",
} as CalendarAdoptionMutationPreview;

const backup = {
  ciphertext_fingerprint_ref:
    `ciphertext-fingerprint-ref:sha256:${"7".repeat(64)}`,
} as CalendarAdoptionPortableBackup;

const restorePreview = {
  preview_ref: "preview-ref:calendar-adoption-restore:test",
  approval_ref: "approval-ref:calendar-adoption-restore:test",
} as CalendarAdoptionRestorePreview;

describe("Calendar adoption mutation provenance", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("binds approval capture and commits to exact backend truth", async () => {
    const fetchMock = vi.fn(
      async (_url: string | URL | Request, _init?: RequestInit) =>
        new Response(
          JSON.stringify({
            success: true,
            data: { receipt_ref: "receipt-ref:calendar-adoption:test" },
          }),
          {
            status: 200,
            headers: {
              "Content-Type": "application/json",
              "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
              "X-UAA-Backend-Instance-Ref": binding.backendInstanceRef,
            },
          },
        ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await captureCalendarAdoptionApproval(
      mutation,
      mutationPreview,
      "idempotency-ref:calendar-adoption:test-mutation",
      binding,
    );
    await commitCalendarAdoptionMutation(
      mutation,
      mutationPreview,
      "idempotency-ref:calendar-adoption:test-mutation",
      binding,
    );
    await captureCalendarAdoptionRestoreApproval(
      backup,
      "correct horse battery staple",
      restorePreview,
      "idempotency-ref:calendar-adoption:test-restore",
      binding,
    );
    await commitCalendarAdoptionRestore(
      backup,
      "correct horse battery staple",
      restorePreview,
      "idempotency-ref:calendar-adoption:test-restore",
      binding,
    );

    expect(fetchMock).toHaveBeenCalledTimes(4);
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      API_ENDPOINTS.calendarAdoptionApproval,
      API_ENDPOINTS.calendarAdoptionCommit,
      API_ENDPOINTS.calendarAdoptionRestoreApproval,
      API_ENDPOINTS.calendarAdoptionRestoreCommit,
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

  it("fails closed before mutation when backend truth is unavailable", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      commitCalendarAdoptionMutation(
        mutation,
        mutationPreview,
        "idempotency-ref:calendar-adoption:missing-binding",
        null,
      ),
    ).rejects.toThrow("BACKEND_TRUTH_MUTATION_BINDING_REQUIRED");
    await expect(
      captureCalendarAdoptionRestoreApproval(
        backup,
        "correct horse battery staple",
        restorePreview,
        "idempotency-ref:calendar-adoption:missing-restore-binding",
        null,
      ),
    ).rejects.toThrow("BACKEND_TRUTH_MUTATION_BINDING_REQUIRED");
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
