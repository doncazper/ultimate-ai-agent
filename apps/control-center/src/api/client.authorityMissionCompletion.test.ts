import { afterEach, describe, expect, it, vi } from "vitest";

import {
  fetchAuthorityMissionCompletions,
  resetControlCenterReadLimiterForTests,
} from "./client";
import { API_ENDPOINTS } from "./endpoints";
import type { AuthorityMissionCompletionReadModel } from "./types";

const safeReadModel: AuthorityMissionCompletionReadModel = {
  schema_version: "uaa-mission-completion-read-model.v1",
  ledger_ref: "ledger-ref:mission-completion-receipts",
  completion_count: 0,
  latest_manifests: [],
  operator_summary: "No content-free mission completions are recorded.",
  request_scoped_authority_still_required: true,
  execution_available_from_read_model: false,
  approval_or_lease_minted: false,
  raw_content_included: false,
  raw_paths_included: false,
  source_ledgers_verified: false,
};

const boundCompletionReadModel: AuthorityMissionCompletionReadModel = {
  ...safeReadModel,
  completion_count: 1,
  latest_manifests: [
    {
      schema_version: "uaa-mission-completion.v1",
      completion_ref: "mission-completion-ref:bound",
      plan_ref: "mission-plan-ref:bound",
      plan_fingerprint_ref: "mission-plan-fingerprint-ref:bound",
      plan_receipt_ref: "mission-plan-receipt-ref:bound",
      plan_entry_hash_ref: "mission-plan-entry-hash-ref:bound",
      mission_ref: "mission-ref:bound",
      run_ref: "run-ref:bound",
      lease_ref: "authority-lease-ref:bound",
      lease_scope: "mission",
      lease_mission_ref: "mission-ref:bound",
      lease_issued_at: "2026-07-11T12:00:00Z",
      lease_expires_at: "2026-07-11T13:00:00Z",
      mission_deadline: "2026-07-11T12:30:00Z",
      concurrency_limit: 1,
      parallel_execution_performed: false,
      status: "succeeded",
      step_bindings: [
        {
          step_ref: "mission-step-ref:bound",
          definition_fingerprint_ref: "step-fingerprint-ref:bound",
          dispatch_ref: "dispatch-ref:bound",
          dispatch_request_fingerprint_ref: "dispatch-fingerprint-ref:bound",
          step_receipt_ref: "step-receipt-ref:bound",
          step_entry_hash_ref: "step-entry-hash-ref:bound",
          dispatch_receipt_ref: "dispatch-receipt-ref:bound",
          dispatch_entry_hash_ref: "dispatch-entry-hash-ref:bound",
          evidence_refs: ["evidence-ref:bound"],
        },
      ],
      dispatch_bindings: [
        {
          dispatch_ref: "dispatch-ref:bound",
          receipt_ref: "dispatch-receipt-ref:bound",
          entry_hash_ref: "dispatch-entry-hash-ref:bound",
          request_fingerprint_ref: "dispatch-fingerprint-ref:bound",
          lease_ref: "authority-lease-ref:bound",
          action_ref: "action-ref:bound",
          adapter_ref: "adapter-ref:bound",
          capability_ref: "capability-ref:bound",
          authority_decision_ref: "authority-decision-ref:bound",
          authority_policy_receipt_ref: "policy-receipt-ref:bound",
          approval_required: true,
          approval_ref: "approval-ref:bound",
          approval_validation_ref: "approval-validation-ref:bound",
          budget_reservation_ref: "budget-reservation-ref:bound",
          budget_reservation_receipt_ref: "budget-reserve-receipt-ref:bound",
          budget_start_receipt_ref: "budget-start-receipt-ref:bound",
          budget_settlement_receipt_ref: "budget-settle-receipt-ref:bound",
          execution_ref: "execution-ref:bound",
          actual_operation_count: 1,
          actual_cost_microusd: 0,
          actual_cost_ref: "actual-cost-ref:bound",
          evidence_refs: ["evidence-ref:bound"],
        },
      ],
      budget_bindings: [
        {
          reservation_ref: "budget-reservation-ref:bound",
          reserve_receipt_ref: "budget-reserve-receipt-ref:bound",
          reserve_entry_hash_ref: "budget-reserve-entry-hash-ref:bound",
          start_receipt_ref: "budget-start-receipt-ref:bound",
          start_entry_hash_ref: "budget-start-entry-hash-ref:bound",
          settlement_receipt_ref: "budget-settle-receipt-ref:bound",
          settlement_entry_hash_ref: "budget-settle-entry-hash-ref:bound",
          lease_ref: "authority-lease-ref:bound",
          action_ref: "action-ref:bound",
          execution_ref: "execution-ref:bound",
          reserved_operation_count: 1,
          reserved_cost_microusd: 0,
          actual_operation_count: 1,
          actual_cost_microusd: 0,
          actual_cost_ref: "actual-cost-ref:bound",
          settlement_status: "settled",
          unresolved_cost: false,
        },
      ],
      approval_refs: ["approval-ref:bound"],
      approval_validation_refs: ["approval-validation-ref:bound"],
      control_snapshot_ref: "control-snapshot-ref:bound",
      control_receipt_refs: [],
      cancellation_receipt_refs: [],
      dead_letter_receipt_refs: [],
      evidence_refs: ["evidence-ref:bound"],
      memory_candidate_ref: "memory-candidate-ref:bound",
      memory_candidate_posture: "review_required_recall_only",
      memory_truth_authority: false,
      context_injection_authorized: false,
      execution_evidence_grants_authority: false,
      signature_present: false,
      integrity_posture: "content_free_hash_chain",
      previous_entry_hash_ref: null,
      entry_hash_ref: "completion-entry-hash-ref:bound",
      created_at: "2026-07-11T12:31:00Z",
      redactions_applied: ["raw_prompt"],
      raw_paths_included: false,
      raw_prompt_included: false,
      raw_response_included: false,
      raw_provider_payload_included: false,
    },
  ],
};

describe("authority mission completion client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    resetControlCenterReadLimiterForTests();
  });

  it("reads the protected backend-owned completion endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ success: true, data: safeReadModel }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchAuthorityMissionCompletions()).resolves.toEqual(
      safeReadModel,
    );
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(API_ENDPOINTS.runtimeAuthorityMissionCompletions),
      expect.objectContaining({
        headers: expect.objectContaining({ Accept: "application/json" }),
      }),
    );
  });

  it("rejects payloads that claim authority from completion evidence", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            success: true,
            data: {
              ...safeReadModel,
              execution_available_from_read_model: true,
              approval_or_lease_minted: true,
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    await expect(fetchAuthorityMissionCompletions()).rejects.toThrow(
      "unsafe or incompatible",
    );
  });

  it("rejects a manifest with missing dispatch and approval validation bindings", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            success: true,
            data: {
              ...safeReadModel,
              completion_count: 1,
              latest_manifests: [
                {
                  schema_version: "uaa-mission-completion.v1",
                  completion_ref: "mission-completion-ref:unsafe",
                  step_bindings: [{}],
                  budget_bindings: [{}],
                  approval_refs: [],
                  evidence_refs: [],
                },
              ],
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    await expect(fetchAuthorityMissionCompletions()).rejects.toThrow(
      "unsafe or incompatible",
    );
  });

  it("rejects a near-valid approval-required manifest with mismatched approval truth", async () => {
    const manifest = boundCompletionReadModel.latest_manifests[0];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            success: true,
            data: {
              ...boundCompletionReadModel,
              latest_manifests: [
                {
                  ...manifest,
                  approval_validation_refs: [],
                  dispatch_bindings: [
                    {
                      ...manifest.dispatch_bindings[0],
                      approval_validation_ref: null,
                    },
                  ],
                },
              ],
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    await expect(fetchAuthorityMissionCompletions()).rejects.toThrow(
      "unsafe or incompatible",
    );
  });

  it("rejects a near-valid manifest with cross-mission lease bindings", async () => {
    const manifest = boundCompletionReadModel.latest_manifests[0];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            success: true,
            data: {
              ...boundCompletionReadModel,
              latest_manifests: [
                {
                  ...manifest,
                  lease_mission_ref: "mission-ref:other",
                },
              ],
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    await expect(fetchAuthorityMissionCompletions()).rejects.toThrow(
      "unsafe or incompatible",
    );
  });
});
