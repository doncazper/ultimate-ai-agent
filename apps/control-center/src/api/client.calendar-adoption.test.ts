import { afterEach, describe, expect, it, vi } from "vitest";
import {
  captureCalendarAdoptionApproval,
  captureCalendarAdoptionRestoreApproval,
  commitCalendarAdoptionMutation,
  commitCalendarAdoptionRestore,
  createCalendarAdoptionBackup,
  loadCalendarAdoptionWorkspace,
  previewCalendarAdoptionMutation,
  previewCalendarAdoptionRestore,
  type BackendTruthReadBinding,
} from "./client";
import { API_ENDPOINTS } from "./endpoints";
import type {
  CalendarAdoptionApprovalReceipt,
  CalendarAdoptionMutationPreview,
  CalendarAdoptionMutationReceipt,
  CalendarAdoptionMutationRequest,
  CalendarAdoptionPortableBackup,
  CalendarAdoptionRestorePreview,
  CalendarAdoptionWorkspaceView,
} from "./types";

const contractRef = "contract-ref:queue-v2-q33-calendar-adoption:v1";
const mutationIdempotencyRef =
  "idempotency-ref:calendar-adoption:test-mutation";
const restoreIdempotencyRef = "idempotency-ref:calendar-adoption:test-restore";

const binding: BackendTruthReadBinding = {
  snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"8".repeat(64)}`,
  backendRevisionRef: `commit-ref:git:${"1".repeat(40)}`,
  backendInstanceRef:
    "backend-instance-ref:control-center:22222222222222222222222222222222",
};

const mutation: CalendarAdoptionMutationRequest = {
  action: "undo",
  expected_revision: 4,
};

const mutationPreview: CalendarAdoptionMutationPreview = {
  schema_version: "uaa-calendar-adoption-mutation-preview.v1",
  contract_ref: contractRef,
  action: "undo",
  expected_revision: 4,
  resulting_revision: 5,
  target_ref: null,
  payload_fingerprint_ref:
    "payload-fingerprint-ref:calendar-adoption:sha256:preview",
  preview_ref: "preview-ref:calendar-adoption:sha256:preview",
  approval_ref: "approval-ref:calendar-adoption:sha256:preview",
  operation_ref: "operation-ref:calendar-adoption:sha256:preview",
  safe_summary: "Apply one exact private local Calendar lifecycle change.",
  mutation_performed: false,
  external_write_performed: false,
};

const backup: CalendarAdoptionPortableBackup = {
  schema_version: "uaa-calendar-adoption-portable-backup.v1",
  contract_ref: contractRef,
  salt: "AAAAAAAAAAAAAAAAAAAAAA==",
  nonce: "AAAAAAAAAAAAAAAA",
  ciphertext: "AAAAAAAAAAAAAAAAAAAAAA==",
  ciphertext_fingerprint_ref: `ciphertext-fingerprint-ref:sha256:${"7".repeat(64)}`,
  source_revision: 3,
  created_at: "2026-09-11T20:00:00Z",
  private_values_encrypted: true,
  key_material_included: false,
  raw_paths_included: false,
};

const restorePreview: CalendarAdoptionRestorePreview = {
  schema_version: "uaa-calendar-adoption-restore-preview.v1",
  contract_ref: contractRef,
  action: "restore_backup",
  expected_revision: 4,
  resulting_revision: 5,
  backup_revision: 3,
  calendar_count: 1,
  event_count: 2,
  current_state_ref: "state-ref:calendar-adoption:sha256:current",
  payload_fingerprint_ref:
    "payload-fingerprint-ref:calendar-adoption-restore:sha256:preview",
  preview_ref: "preview-ref:calendar-adoption-restore:sha256:preview",
  approval_ref: "approval-ref:calendar-adoption-restore:sha256:preview",
  operation_ref: "operation-ref:calendar-adoption-restore:sha256:preview",
  rollback_available: true,
  impact_status: "exact",
  restore_performed: false,
  private_values_included: false,
};

const workspaceView: CalendarAdoptionWorkspaceView = {
  schema_version: "uaa-calendar-adoption-read-model.v1",
  contract_ref: contractRef,
  status: "ready",
  workspace_ref: "workspace-ref:founder-private-calendar",
  calendar_set_ref: "calendar-set-ref:founder-private",
  revision: 4,
  current_state_ref: "state-ref:calendar-adoption:sha256:current",
  calendar_set_name: "My Calendar",
  calendars: [],
  occurrence_items: [],
  archived_events: [],
  conflict_items: [],
  view: "week",
  timezone: "UTC",
  range_starts_at: "2026-09-14T00:00:00Z",
  range_ends_at: "2026-09-21T00:00:00Z",
  result_ref: "calendar-view-result-ref:adoption:test",
  can_undo: false,
  next_safe_action: "Create an event.",
  backend_owned: true,
  local_only: true,
  exact_approval_required: true,
  backup_restore_available: true,
  external_calendar_write_enabled: false,
  connector_read_enabled: false,
  connector_write_enabled: false,
  provider_model_call_enabled: false,
  browser_automation_enabled: false,
  shell_subprocess_execution_enabled: false,
  background_scheduling_enabled: false,
  notification_delivery_enabled: false,
  production_authority_enabled: false,
};

function approvalReceipt(
  preview: CalendarAdoptionMutationPreview | CalendarAdoptionRestorePreview,
  idempotencyRef: string,
): CalendarAdoptionApprovalReceipt {
  return {
    schema_version: "uaa-calendar-adoption-approval-receipt.v1",
    contract_ref: contractRef,
    approval_ref: preview.approval_ref,
    approval_validation_ref: "appr_dec_123456789abc",
    preview_ref: preview.preview_ref,
    idempotency_ref: idempotencyRef,
    expires_at: "2026-09-11T20:05:00Z",
    backend_owned: true,
    mutation_performed: false,
  };
}

function mutationReceipt(
  action: CalendarAdoptionMutationReceipt["action"],
  preview: CalendarAdoptionMutationPreview | CalendarAdoptionRestorePreview,
  idempotencyRef: string,
  backupFingerprintRef: string | null,
): CalendarAdoptionMutationReceipt {
  return {
    schema_version: "uaa-calendar-adoption-mutation-receipt.v1",
    contract_ref: contractRef,
    action,
    target_ref:
      action === "restore_backup" ? "calendar-set-ref:founder-private" : null,
    before_revision: preview.expected_revision,
    after_revision: preview.resulting_revision,
    idempotency_ref: idempotencyRef,
    payload_fingerprint_ref: preview.payload_fingerprint_ref,
    preview_ref: preview.preview_ref,
    approval_ref: preview.approval_ref,
    approval_validation_ref: "appr_dec_123456789abc",
    approval_expires_at: "2026-09-11T20:05:00Z",
    authority_decision_ref: "authority-policy-decision-ref:calendar:test",
    authority_lease_ref: "authority-lease-ref:calendar:test",
    operation_ref: preview.operation_ref,
    receipt_ref: "receipt-ref:calendar-adoption:test",
    operation_receipt_refs: ["operation-receipt-ref:calendar:test"],
    backup_fingerprint_ref: backupFingerprintRef,
    state_ref: "state-ref:calendar-adoption-receipt:test",
    rollback_ref: "rollback-ref:calendar-adoption:test",
    safe_disable_ref: "safe-disable-ref:calendar-adoption-local-write:deny",
    replayed: false,
    local_calendar_write_performed: true,
    external_calendar_write_performed: false,
    connector_write_performed: false,
    provider_model_call_performed: false,
    shell_subprocess_execution_performed: false,
    browser_automation_performed: false,
    background_scheduling_performed: false,
    notification_delivery_performed: false,
    production_authority_enabled: false,
  };
}

function response(value: unknown, includeBinding = false): Response {
  return new Response(JSON.stringify({ success: true, data: value }), {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      ...(includeBinding
        ? {
            "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
            "X-UAA-Backend-Instance-Ref": binding.backendInstanceRef,
          }
        : {}),
    },
  });
}

describe("Calendar adoption response and mutation provenance", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("binds approval capture and commits to exact backend truth and receipts", async () => {
    const fetchMock = vi.fn(
      async (url: string | URL | Request, _init?: RequestInit) => {
        const path = String(url);
        if (path.endsWith(API_ENDPOINTS.calendarAdoptionApproval)) {
          return response(
            approvalReceipt(mutationPreview, mutationIdempotencyRef),
            true,
          );
        }
        if (path.endsWith(API_ENDPOINTS.calendarAdoptionCommit)) {
          return response(
            mutationReceipt(
              "undo",
              mutationPreview,
              mutationIdempotencyRef,
              null,
            ),
            true,
          );
        }
        if (path.endsWith(API_ENDPOINTS.calendarAdoptionRestoreApproval)) {
          return response(
            approvalReceipt(restorePreview, restoreIdempotencyRef),
            true,
          );
        }
        return response(
          mutationReceipt(
            "restore_backup",
            restorePreview,
            restoreIdempotencyRef,
            backup.ciphertext_fingerprint_ref,
          ),
          true,
        );
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    await captureCalendarAdoptionApproval(
      mutation,
      mutationPreview,
      mutationIdempotencyRef,
      binding,
    );
    await commitCalendarAdoptionMutation(
      mutation,
      mutationPreview,
      mutationIdempotencyRef,
      binding,
    );
    await captureCalendarAdoptionRestoreApproval(
      backup,
      "correct horse battery staple",
      restorePreview,
      restoreIdempotencyRef,
      binding,
    );
    await commitCalendarAdoptionRestore(
      backup,
      "correct horse battery staple",
      restorePreview,
      restoreIdempotencyRef,
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

  it("rejects successful but forged previews and backups", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        response({ ...mutationPreview, resulting_revision: 99 }),
      ),
    );
    await expect(
      previewCalendarAdoptionMutation(mutation, mutationIdempotencyRef),
    ).rejects.toThrow("CALENDAR_ADOPTION_RESPONSE_INVALID");

    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        response({ ...backup, private_values_encrypted: false }),
      ),
    );
    await expect(
      createCalendarAdoptionBackup(
        "correct horse battery staple",
        "idempotency-ref:calendar-adoption:test-backup",
      ),
    ).rejects.toThrow("CALENDAR_ADOPTION_RESPONSE_INVALID");

    vi.stubGlobal(
      "fetch",
      vi.fn(async () => response({ ...restorePreview, backup_revision: 99 })),
    );
    await expect(
      previewCalendarAdoptionRestore(
        backup,
        "correct horse battery staple",
        restoreIdempotencyRef,
      ),
    ).rejects.toThrow("CALENDAR_ADOPTION_RESPONSE_INVALID");
  });

  it("accepts an exact corrupt-target recovery preview without claiming an empty target", async () => {
    const recoveryPreview: CalendarAdoptionRestorePreview = {
      ...restorePreview,
      expected_revision: 0,
      resulting_revision: 1,
      current_state_ref:
        "state-ref:calendar-adoption-unreadable:sha256:current",
      rollback_available: false,
      impact_status: "unknown_current_state",
    };
    vi.stubGlobal("fetch", vi.fn(async () => response(recoveryPreview)));

    await expect(
      previewCalendarAdoptionRestore(
        backup,
        "correct horse battery staple",
        restoreIdempotencyRef,
      ),
    ).resolves.toEqual(recoveryPreview);
  });

  it("rejects Calendar reads with broadened authority boundaries", async () => {
    const blockedFlags = [
      "external_calendar_write_enabled",
      "connector_read_enabled",
      "connector_write_enabled",
      "provider_model_call_enabled",
      "browser_automation_enabled",
      "shell_subprocess_execution_enabled",
      "background_scheduling_enabled",
      "notification_delivery_enabled",
      "production_authority_enabled",
    ] as const;

    for (const flag of blockedFlags) {
      vi.stubGlobal(
        "fetch",
        vi.fn(async () => response({ ...workspaceView, [flag]: true })),
      );
      await expect(
        loadCalendarAdoptionWorkspace(
          "week",
          "2026-09-14T00:00:00Z",
          "UTC",
        ),
      ).rejects.toThrow("CALENDAR_ADOPTION_RESPONSE_INVALID");
    }

    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        response({ ...workspaceView, backup_restore_available: false }),
      ),
    );
    await expect(
      loadCalendarAdoptionWorkspace(
        "week",
        "2026-09-14T00:00:00Z",
        "UTC",
      ),
    ).rejects.toThrow("CALENDAR_ADOPTION_RESPONSE_INVALID");
  });

  it("rejects successful receipts that are rebound or broaden authority", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        response(
          {
            ...approvalReceipt(mutationPreview, mutationIdempotencyRef),
            idempotency_ref: "idempotency-ref:calendar-adoption:other",
          },
          true,
        ),
      ),
    );
    await expect(
      captureCalendarAdoptionApproval(
        mutation,
        mutationPreview,
        mutationIdempotencyRef,
        binding,
      ),
    ).rejects.toThrow("CALENDAR_ADOPTION_RESPONSE_INVALID");

    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        response(
          {
            ...mutationReceipt(
              "undo",
              mutationPreview,
              mutationIdempotencyRef,
              null,
            ),
            provider_model_call_performed: true,
          },
          true,
        ),
      ),
    );
    await expect(
      commitCalendarAdoptionMutation(
        mutation,
        mutationPreview,
        mutationIdempotencyRef,
        binding,
      ),
    ).rejects.toThrow("CALENDAR_ADOPTION_RESPONSE_INVALID");

    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        response(
          {
            ...mutationReceipt(
              "restore_backup",
              restorePreview,
              restoreIdempotencyRef,
              backup.ciphertext_fingerprint_ref,
            ),
            backup_fingerprint_ref: `ciphertext-fingerprint-ref:sha256:${"9".repeat(64)}`,
          },
          true,
        ),
      ),
    );
    await expect(
      commitCalendarAdoptionRestore(
        backup,
        "correct horse battery staple",
        restorePreview,
        restoreIdempotencyRef,
        binding,
      ),
    ).rejects.toThrow("CALENDAR_ADOPTION_RESPONSE_INVALID");
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
