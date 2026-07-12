import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type {
  AuthorityMissionCompletionReadModel,
  AuthorityMissionWorkerJob,
  AuthorityMissionWorkerReadModel,
} from "../api/types";
import { AuthorityMissionInspectionPanel } from "./AuthorityMissionInspectionPanel";

function job(
  suffix: string,
  overrides: Partial<AuthorityMissionWorkerJob>,
): AuthorityMissionWorkerJob {
  return {
    job_safe_ref: `mission-worker-job-safe-ref:sha256:${suffix}`,
    plan_safe_ref: `mission-worker-plan-safe-ref:sha256:${suffix}`,
    mission_safe_ref: `mission-worker-mission-safe-ref:sha256:${suffix}`,
    run_safe_ref: `mission-worker-run-safe-ref:sha256:${suffix}`,
    durable_status: "pending",
    recovery_status: "pending",
    generation: 0,
    latest_event: "enqueued",
    latest_event_at: "2026-07-11T12:00:00Z",
    last_heartbeat_at: null,
    heartbeat_freshness: "not_observed",
    worker_safe_ref: null,
    claim_safe_ref: null,
    claim_expires_at: null,
    retry_not_before: null,
    deadline: "2026-07-11T13:00:00Z",
    steps: [
      {
        step_safe_ref: `mission-worker-step-safe-ref:sha256:${suffix}`,
        status: "pending",
        claim_freshness: "not_claimed",
        generation: 0,
        reason_refs: [],
        evidence_refs: [],
        adapter_reinvocation_allowed: false,
      },
    ],
    reason_refs: [],
    evidence_refs: [],
    request_payload_persisted: false,
    request_scoped_authority_required_before_resume: true,
    ...overrides,
  };
}

const readModel: AuthorityMissionWorkerReadModel = {
  schema_version: "uaa-local-mission-worker.v1",
  inspection_ref: "mission-worker-inspection-ref:sha256:panel",
  configuration_enabled: true,
  canonical_platform: "macos",
  observed_platform: "macos",
  platform_execution_supported: true,
  linux_surface_posture: "render_placeholder",
  windows_surface_posture: "render_placeholder",
  queue_capacity: 16,
  queued_job_count: 2,
  total_job_count: 4,
  omitted_terminal_job_count: 0,
  active_claim_count: 0,
  stale_claim_count: 0,
  kill_switch_engaged: false,
  jobs: [
    job("approval", {
      durable_status: "approval_wait",
      recovery_status: "approval_wait",
      steps: [
        {
          step_safe_ref: "mission-worker-step-safe-ref:sha256:approval",
          status: "approval_wait",
          claim_freshness: "not_claimed",
          generation: 1,
          reason_refs: ["reason-ref:mission-step:approval-required"],
          evidence_refs: ["approval-request-safe-ref:sha256:approval"],
          adapter_reinvocation_allowed: false,
        },
      ],
    }),
    job("retry", {
      durable_status: "retry_pending",
      recovery_status: "retry_pending",
      retry_not_before: "2026-07-11T12:01:00Z",
      steps: [
        {
          step_safe_ref: "mission-worker-step-safe-ref:sha256:retry",
          status: "retry_pending",
          claim_freshness: "not_claimed",
          generation: 1,
          reason_refs: ["reason-ref:mission-step:retry-scheduled"],
          evidence_refs: ["receipt-ref:authority-dispatch:retry"],
          adapter_reinvocation_allowed: false,
        },
      ],
    }),
    job("dead-letter", {
      durable_status: "failed",
      recovery_status: "failed",
      latest_event: "completed",
      steps: [
        {
          step_safe_ref: "mission-worker-step-safe-ref:sha256:dead-letter",
          status: "failed",
          claim_freshness: "not_claimed",
          generation: 2,
          reason_refs: ["reason-ref:mission-step:retry-attempts-exhausted"],
          evidence_refs: ["receipt-ref:authority-dispatch:dead-letter"],
          adapter_reinvocation_allowed: false,
        },
      ],
    }),
    job("cancelled", {
      durable_status: "cancelled",
      recovery_status: "cancelled",
      latest_event: "completed",
      steps: [
        {
          step_safe_ref: "mission-worker-step-safe-ref:sha256:cancelled",
          status: "cancelled",
          claim_freshness: "not_claimed",
          generation: 1,
          reason_refs: ["reason-ref:mission-step:mission-cancelled"],
          evidence_refs: ["mission-control-receipt-ref:cancelled"],
          adapter_reinvocation_allowed: false,
        },
      ],
    }),
  ],
  checked_at: "2026-07-11T12:00:00Z",
  operator_summary:
    "Local macOS mission worker inspection reports durable safe references only.",
  local_only: true,
  execution_authority_granted: false,
  approval_or_lease_minted: false,
  remote_queue_enabled: false,
  daemon_enabled: false,
  raw_task_input_persisted: false,
  raw_paths_included: false,
  raw_logs_included: false,
  raw_provider_payloads_included: false,
  redactions_applied: ["raw_task_inputs", "raw_paths", "raw_logs"],
};

const completionReadModel: AuthorityMissionCompletionReadModel = {
  schema_version: "uaa-mission-completion-read-model.v1",
  ledger_ref: "ledger-ref:mission-completion-receipts",
  completion_count: 1,
  latest_manifests: [
    {
      schema_version: "uaa-mission-completion.v1",
      completion_ref: "mission-completion-ref:sha256:panel",
      plan_ref: "mission-plan-ref:panel",
      plan_fingerprint_ref: "mission-plan-fingerprint-ref:sha256:panel",
      plan_receipt_ref: "mission-plan-receipt-ref:panel",
      plan_entry_hash_ref: "mission-plan-entry-hash-ref:panel",
      mission_ref: "mission-ref:panel",
      run_ref: "run-ref:panel",
      lease_ref: "authority-lease-ref:panel",
      lease_scope_fingerprint_ref: "authority-lease-scope-fingerprint-ref:panel",
      lease_scope: "mission",
      lease_mission_ref: "mission-ref:panel",
      lease_issued_at: "2026-07-11T12:00:00Z",
      lease_expires_at: "2026-07-11T13:00:00Z",
      mission_deadline: "2026-07-11T12:30:00Z",
      status: "succeeded",
      concurrency_limit: 1,
      parallel_execution_performed: false,
      step_bindings: [
        {
          step_ref: "mission-step-ref:panel",
          definition_fingerprint_ref: "mission-step-fingerprint-ref:panel",
          dispatch_ref: "dispatch-ref:panel",
          dispatch_request_fingerprint_ref: "dispatch-fingerprint-ref:panel",
          step_receipt_ref: "mission-step-receipt-ref:panel",
          step_entry_hash_ref: "mission-step-entry-hash-ref:panel",
          dispatch_receipt_ref: "dispatch-receipt-ref:panel",
          dispatch_entry_hash_ref: "dispatch-entry-hash-ref:panel",
          evidence_refs: ["evidence-ref:panel"],
        },
      ],
      dispatch_bindings: [
        {
          dispatch_ref: "dispatch-ref:panel",
          receipt_ref: "dispatch-receipt-ref:panel",
          entry_hash_ref: "dispatch-entry-hash-ref:panel",
          request_fingerprint_ref: "dispatch-fingerprint-ref:panel",
          lease_ref: "authority-lease-ref:panel",
          action_ref: "action-ref:panel",
          adapter_ref: "adapter-ref:panel",
          capability_ref: "capability-ref:panel",
          authority_decision_ref: "authority-decision-ref:panel",
          authority_policy_receipt_ref: "policy-receipt-ref:panel",
          approval_required: true,
          approval_ref: "approval-ref:panel",
          approval_validation_ref: "approval-validation-ref:panel",
          budget_reservation_ref: "budget-reservation-ref:panel",
          budget_reservation_receipt_ref: "budget-reserve-receipt-ref:panel",
          budget_start_receipt_ref: "budget-start-receipt-ref:panel",
          budget_settlement_receipt_ref: "budget-settlement-receipt-ref:panel",
          execution_ref: "execution-ref:panel",
          actual_operation_count: 1,
          actual_cost_microusd: 0,
          actual_cost_ref: "actual-cost-ref:panel",
          evidence_refs: ["evidence-ref:panel"],
        },
      ],
      budget_bindings: [
        {
          reservation_ref: "budget-reservation-ref:panel",
          reserve_receipt_ref: "budget-reserve-receipt-ref:panel",
          reserve_entry_hash_ref: "budget-reserve-entry-hash-ref:panel",
          start_receipt_ref: "budget-start-receipt-ref:panel",
          start_entry_hash_ref: "budget-start-entry-hash-ref:panel",
          settlement_receipt_ref: "budget-settlement-receipt-ref:panel",
          settlement_entry_hash_ref: "budget-settlement-entry-hash-ref:panel",
          lease_ref: "authority-lease-ref:panel",
          action_ref: "action-ref:panel",
          execution_ref: "execution-ref:panel",
          reserved_operation_count: 1,
          reserved_cost_microusd: 0,
          settlement_status: "settled",
          actual_operation_count: 1,
          actual_cost_microusd: 0,
          actual_cost_ref: "actual-cost-ref:panel",
          unresolved_cost: false,
        },
      ],
      approval_refs: ["approval-ref:panel"],
      approval_validation_refs: ["approval-validation-ref:panel"],
      control_snapshot_ref: "mission-control-snapshot-ref:panel",
      control_receipt_refs: [],
      cancellation_receipt_refs: [],
      dead_letter_receipt_refs: [],
      evidence_refs: ["evidence-ref:panel"],
      memory_candidate_ref: "memory-candidate-ref:panel",
      memory_candidate_posture: "review_required_recall_only",
      memory_truth_authority: false,
      context_injection_authorized: false,
      execution_evidence_grants_authority: false,
      signature_present: false,
      integrity_posture: "content_free_hash_chain",
      previous_entry_hash_ref: null,
      entry_hash_ref: "mission-completion-entry-hash-ref:sha256:panel",
      created_at: "2026-07-11T12:31:00Z",
      redactions_applied: ["raw_prompt"],
      raw_paths_included: false,
      raw_prompt_included: false,
      raw_response_included: false,
      raw_provider_payload_included: false,
    },
  ],
  integrity_summary: {
    schema_version: "uaa-mission-completion-integrity-summary.v1",
    verifier_version_ref: "verifier-ref:mission-completion:sha256-chain:v1",
    manifest_count: 1,
    chain_ref: "mission-completion-chain-ref:panel",
    genesis_entry_hash_ref: "mission-completion-entry-hash-ref:sha256:panel",
    terminal_entry_hash_ref: "mission-completion-entry-hash-ref:sha256:panel",
    hash_chain_verified: true,
    source_ledgers_verified: false,
    signature_present: false,
    signing_status: "blocked_signing_lifecycle_not_implemented",
    cryptographic_authenticity_verified: false,
    external_anchor_verified: false,
    execution_evidence_grants_authority: false,
  },
  portable_evidence_summary: {
    schema_version: "uaa-portable-mission-evidence-inspection.v1",
    status: "verified_local_hash_chain",
    bundle_ref: "portable-mission-evidence-bundle-ref:panel",
    completion_count: 1,
    envelope_count: 1,
    terminal_entry_hash_ref: "portable-evidence-entry-hash-ref:panel",
    local_hash_chain_verified: true,
    source_receipts_bound: true,
    source_ledgers_verified: false,
    caller_expected_binding_matched: false,
    signature_verified: false,
    signing_status: "blocked_signing_lifecycle_not_implemented",
    cryptographic_authenticity_verified: false,
    external_anchor_verified: false,
    execution_evidence_grants_authority: false,
    reason_refs: [
      "reason-ref:portable-mission-evidence:hash-chain-verified",
    ],
  },
  operator_summary: "One content-free mission completion is available.",
  request_scoped_authority_still_required: true,
  execution_available_from_read_model: false,
  approval_or_lease_minted: false,
  raw_content_included: false,
  raw_paths_included: false,
  source_ledgers_verified: false,
};

describe("AuthorityMissionInspectionPanel", () => {
  it("renders backend mission lifecycle truth without mutation controls", async () => {
    const loadWorkerState = vi.fn().mockResolvedValue(readModel);
    const loadCompletions = vi.fn().mockResolvedValue(completionReadModel);
    render(
      <AuthorityMissionInspectionPanel
        loadWorkerState={loadWorkerState}
        loadCompletions={loadCompletions}
      />,
    );

    const panel = await screen.findByRole("region", {
      name: "Authority mission worker",
    });
    expect(within(panel).getAllByText("approval wait").length).toBeGreaterThan(0);
    expect(within(panel).getAllByText("retry pending").length).toBeGreaterThan(0);
    expect(within(panel).getByText("Dead letter")).toBeInTheDocument();
    expect(within(panel).getAllByText("cancelled").length).toBeGreaterThan(0);
    expect(within(panel).getByText("macOS")).toBeInTheDocument();
    expect(within(panel).getAllByText("render placeholder")).toHaveLength(2);
    expect(
      within(panel).getByText("Authority granted").nextSibling,
    ).toHaveTextContent("no");
    expect(within(panel).queryByRole("button")).not.toBeInTheDocument();
    expect(within(panel).getByText("Mission completion evidence")).toBeInTheDocument();
    expect(within(panel).getByText("review required, recall only")).toBeInTheDocument();
    expect(within(panel).getAllByText(/content-free hash chain/)).toHaveLength(1);
    expect(within(panel).getByText("Mission budget settlement")).toBeInTheDocument();
    expect(within(panel).getByText("budget-reservation-ref:panel")).toBeInTheDocument();
    expect(within(panel).getByText("1 actual / 1 reserved")).toBeInTheDocument();
    expect(within(panel).getByText("0 actual / 0 reserved microusd")).toBeInTheDocument();
    expect(
      within(panel).getByText("Completion unresolved cost").closest("div"),
    ).toHaveTextContent("no");
    expect(
      within(panel).getByText(/active unresolved-cost posture is not exposed/i),
    ).toBeInTheDocument();
    expect(within(panel).getByLabelText("Budget receipts")).toBeInTheDocument();
    expect(within(panel).getByText("budget-settlement-receipt-ref:panel")).toBeInTheDocument();
    expect(within(panel).getByText(/Completion chain: local SHA-256 verified/)).toBeInTheDocument();
    expect(within(panel).getByText(/Portable evidence: verified local hash chain/)).toBeInTheDocument();
    expect(within(panel).getByText(/Source records bound: yes/)).toBeInTheDocument();
    expect(within(panel).getByText(/Signing: blocked/)).toBeInTheDocument();
    expect(within(panel).getByText(/Authenticity verified: false/)).toBeInTheDocument();
    expect(loadWorkerState).toHaveBeenCalledTimes(1);
    expect(loadCompletions).toHaveBeenCalledTimes(1);
  });

  it("fails closed without rendering mock mission truth", async () => {
    render(
      <AuthorityMissionInspectionPanel
        loadWorkerState={vi.fn().mockRejectedValue(new Error("offline"))}
        loadCompletions={vi.fn().mockRejectedValue(new Error("offline"))}
      />,
    );

    expect(
      await screen.findByRole("alert", {
        name: "Authority mission inspection data unavailable",
      }),
    ).toHaveTextContent("No mission capability is treated as active");
    expect(screen.queryByText("approval wait")).not.toBeInTheDocument();
  });

  it("renders invalid completion evidence as unverified", async () => {
    const invalidCompletion = {
      ...completionReadModel,
      integrity_summary: {
        ...completionReadModel.integrity_summary,
        hash_chain_verified: false,
      },
      portable_evidence_summary: {
        ...completionReadModel.portable_evidence_summary,
        status: "invalid",
        local_hash_chain_verified: false,
        source_receipts_bound: false,
        reason_refs: ["reason-ref:portable-mission-evidence:verification-failed"],
      },
    };
    render(
      <AuthorityMissionInspectionPanel
        loadWorkerState={vi.fn().mockResolvedValue(readModel)}
        loadCompletions={vi.fn().mockResolvedValue(invalidCompletion)}
      />,
    );

    const panel = await screen.findByRole("region", {
      name: "Authority mission worker",
    });
    expect(within(panel).getByText("Completion chain: invalid")).toBeInTheDocument();
    expect(within(panel).getByText("Portable evidence: invalid")).toBeInTheDocument();
    expect(within(panel).getByText("Source records bound: no")).toBeInTheDocument();
    expect(
      within(panel).queryByText("Completion chain: local SHA-256 verified"),
    ).not.toBeInTheDocument();
  });

  it("does not present completion loading or failure as zero recorded", async () => {
    let resolveCompletions: (
      value: AuthorityMissionCompletionReadModel,
    ) => void = () => undefined;
    const pending = new Promise<AuthorityMissionCompletionReadModel>((resolve) => {
      resolveCompletions = resolve;
    });
    const { rerender } = render(
      <AuthorityMissionInspectionPanel
        loadWorkerState={vi.fn().mockResolvedValue(readModel)}
        loadCompletions={vi.fn().mockReturnValue(pending)}
      />,
    );
    const panel = await screen.findByRole("region", {
      name: "Authority mission worker",
    });
    expect(within(panel).getByText("loading")).toBeInTheDocument();
    expect(within(panel).queryByText("0 recorded")).not.toBeInTheDocument();
    resolveCompletions(completionReadModel);
    expect(await within(panel).findByText("1 recorded")).toBeInTheDocument();

    rerender(
      <AuthorityMissionInspectionPanel
        loadWorkerState={vi.fn().mockResolvedValue(readModel)}
        loadCompletions={vi.fn().mockRejectedValue(new Error("unavailable"))}
      />,
    );
    expect(await within(panel).findByText("unavailable")).toBeInTheDocument();
    expect(within(panel).queryByText("0 recorded")).not.toBeInTheDocument();
  });
});
