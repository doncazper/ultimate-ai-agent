import { afterEach, describe, expect, it, vi } from "vitest";

import {
  buildLocalTaskCommitAuthorityRequest,
  buildLocalTaskCommitRequest,
  localTaskCommitIdempotencyRef,
  localTaskCommitReceiptIsSafe,
  loadNorthStarDecisionsData,
} from "./client";
import { API_ENDPOINTS } from "./endpoints";
import { mockControlCenterData } from "../mocks/controlCenterData";
import type { FounderLoopLocalTaskCommitReceipt } from "./types";

const binding = {
  snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"1".repeat(64)}`,
  backendRevisionRef: `commit-ref:git:${"2".repeat(40)}`,
  backendInstanceRef:
    "backend-instance-ref:control-center:33333333333333333333333333333333",
};

const localTaskItemRef = "founder-action:mock-local-task-review";
const localTaskApprovalRef = "approval-ref:northstar:local-task-approved";

function validLocalTaskReceipt(): FounderLoopLocalTaskCommitReceipt {
  const request = buildLocalTaskCommitRequest(
    localTaskItemRef,
    localTaskApprovalRef,
  );
  const authorityProofRefs = [
    "authority-policy-decision-ref:northstar-local-task",
    "authority-lease-ref:northstar-workspace-write",
    "audit-ref:authority-policy:northstar-local-task",
    "receipt-ref:authority-policy:northstar-local-task",
  ] as const;
  return {
    contract_ref: "contract-ref:founder-loop-local-task-commit:v1",
    item_ref: localTaskItemRef,
    action_kind: "local_task_create",
    local_task_ref:
      "local-task:founder-loop:founder-action-mock-local-task-review",
    status: "local_task_created",
    receipt_ref: "receipt:founder-loop-local-task:northstar-review",
    audit_ref: "audit:founder-loop-local-task:northstar-review",
    idempotency_key_ref: localTaskCommitIdempotencyRef(
      localTaskItemRef,
      request,
    ),
    payload_fingerprint_ref:
      "payload-fingerprint-ref:northstar-local-task:test",
    run_ref: "run-ref:founder-loop-v1:governed-local-loop",
    evidence_timeline_event_ref:
      "evidence-timeline-event:local-task:northstar-review",
    approval_ref: localTaskApprovalRef,
    approval_status: "approved",
    approval_reason_refs: ["approval-reason-ref:northstar:test"],
    authority_decision_ref: authorityProofRefs[0],
    authority_decision_outcome: "ask",
    authority_lease_ref: authorityProofRefs[1],
    authority_audit_ref: authorityProofRefs[2],
    authority_policy_receipt_ref: authorityProofRefs[3],
    authority_domain_ref: "authority-domain-ref:workspace",
    authority_capability_ref: "authority-capability-ref:write",
    authority_required_mode_ref: "authority-mode-ref:ask-before-changes",
    local_task_created: true,
    safe_disable_ref: "safe-disable-ref:test:local-task",
    rollback_ref: "rollback-ref:test:local-task",
    safe_disable_posture_ref:
      "safe-disable-posture:founder-loop:local-task-create:enabled",
    safe_disable_enabled: true,
    rollback_execution_enabled: false,
    rollback_blocker_refs: ["blocked-state:rollback-execution-not-scoped"],
    connector_write_performed: false,
    shell_subprocess_execution_performed: false,
    model_provider_authority_used: false,
    memory_write_performed: false,
    context_injection_performed: false,
    external_side_effect_performed: false,
    raw_content_stored: false,
    replayed: false,
    safe_summary: "Exact local task state was recorded with safe refs only.",
    evidence_refs: [
      "evidence-ref:northstar-local-task:test",
      "evidence-timeline-event:local-task:northstar-review",
      ...authorityProofRefs,
    ],
    blocked_state_refs: [
      "blocked-state:no-connector-write",
      "blocked-state:no-shell-subprocess-execution",
      "blocked-state:no-model-provider-authority",
      "blocked-state:no-memory-write",
      "blocked-state:no-context-injection",
      "blocked-state:no-external-side-effect",
      "blocked-state:no-production-authority",
    ],
    created_at: "2026-09-09T00:00:00Z",
  };
}

function boundedDecisionFixtures() {
  const inbox = structuredClone(mockControlCenterData.founderActionsInbox);
  const workQueue = inbox.action_inbox_work_queue_read_model;
  if (!workQueue) throw new Error("Missing Action Inbox work queue fixture");
  const laneOrder = [
    "needs_approval",
    "blocked",
    "draft_only",
    "cost_blocked",
    "no_authority",
    "approved_no_execution",
    "rejected",
    "deferred",
    "receipt_recorded",
  ];
  inbox.action_inbox_decision_lane_contract_ref =
    "contract-ref:product-loop-005-action-inbox-decision-lanes:v1";
  inbox.action_inbox_decision_lane_read_model = {
    contract_ref:
      "contract-ref:product-loop-005-action-inbox-decision-lanes:v1",
    status: "implemented_backend_owned_decision_lanes",
    source: "python_core_action_inbox_decision_lane_read_model",
    backend_owned: true,
    local_read_model_only: true,
    safe_refs_only: true,
    raw_content_included: false,
    lane_order: laneOrder,
    lanes: laneOrder.map((laneId) => ({
      lane_id: laneId,
      label: laneId,
      status: "empty",
      safe_summary: "No bounded fixture item is present.",
      count: 0,
      item_refs: [],
      blocked_state_refs: [],
      next_safe_action: "Wait for backend-owned work.",
      approval_alone_executes: false,
      action_execution_enabled: false,
    })),
    items: [],
    blocked_state_refs: ["blocked-state:no-action-execution"],
    missing_envelope_fields_fail_safe: true,
    cost_posture_visible_before_approval: true,
    provider_authority_visible_before_approval: true,
    approval_scope_visible_before_approval: true,
    expected_receipts_visible_before_approval: true,
    action_execution_enabled: false,
    connector_write_enabled: false,
    shell_subprocess_execution_enabled: false,
    browser_execution_enabled: false,
    provider_model_call_enabled: false,
    memory_write_enabled: false,
    context_injection_authorized: false,
    hidden_memory_write_authorized: false,
    production_authority_enabled: false,
    approval_alone_executes: false,
  } as NonNullable<typeof inbox.action_inbox_decision_lane_read_model>;
  workQueue.source = "python_core_action_inbox_work_queue_read_model";
  workQueue.backend_owned = true;
  return {
    [API_ENDPOINTS.founderActionsInbox]: inbox,
    [API_ENDPOINTS.controlCenterSettingsStatus]: {
      ...structuredClone(mockControlCenterData.settingsStatus),
      authority_lease_state: {
        ...structuredClone(
          mockControlCenterData.settingsStatus.authority_lease_state,
        ),
        backend_owned: true,
      },
    },
  };
}

function stubBoundedFetch(fixtures: Record<string, unknown>) {
  vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
    const path = new URL(
      input instanceof Request ? input.url : String(input),
      "http://127.0.0.1",
    ).pathname;
    if (!(path in fixtures)) throw new Error(`Missing bounded fixture ${path}`);
    return new Response(JSON.stringify({ ok: true, data: fixtures[path] }), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
        "X-UAA-Backend-Instance-Ref": binding.backendInstanceRef,
      },
    });
  }));
}

describe("loadNorthStarDecisionsData", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("binds the bounded Decisions read to backend-owned authority state", async () => {
    stubBoundedFetch(boundedDecisionFixtures());

    const data = await loadNorthStarDecisionsData(binding);

    expect(fetch).toHaveBeenCalledTimes(2);
    expect(data.routeStates["/actions"].state).toBe("backend_owned");
    expect(data.routeStates["/settings"].state).toBe("backend_owned");
    expect(data.settingsStatus.authority_lease_state.backend_owned).toBe(true);
    expect(data.connection.usingMockData).toBe(false);
  });

  it("fails closed when the authority status claims a settings toggle grants authority", async () => {
    const fixtures = boundedDecisionFixtures();
    const settings = fixtures[API_ENDPOINTS.controlCenterSettingsStatus] as {
      settings_toggle_grants_authority: boolean;
    };
    settings.settings_toggle_grants_authority = true;
    stubBoundedFetch(fixtures);

    await expect(loadNorthStarDecisionsData(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });
});

describe("local task commit boundary", () => {
  it("builds one canonical payload and binds authority evaluation to the exact item", () => {
    const request = buildLocalTaskCommitRequest(
      localTaskItemRef,
      localTaskApprovalRef,
    );

    expect(request).toEqual({
      approval_ref: localTaskApprovalRef,
      decision_reason_ref:
        "decision-reason-ref:control-center:local-task-commit",
      metadata_refs: [
        "metadata-ref:control-center-local-task-commit",
        localTaskItemRef,
      ],
    });
    expect(buildLocalTaskCommitAuthorityRequest(
      localTaskItemRef,
      request,
    )).toEqual(expect.objectContaining({
      action_ref: "authority-action-ref:founder-loop-local-task-commit",
      domain: "workspace",
      capability: "write",
      resource_refs: [
        localTaskItemRef,
        "local-task:founder-loop:founder-action-mock-local-task-review",
        "contract-ref:founder-loop-local-task-commit:v1",
        localTaskCommitIdempotencyRef(localTaskItemRef, request),
      ],
      route_ref:
        "POST /control-center/actions/{action_id}/local-task/commit",
      lane_ref: "lane-ref:action-inbox-local-task-commit",
      requested_mode: "ask_before_changes",
    }));
  });

  it("rejects receipts without the exact authority proof or with unsafe display data", () => {
    const receipt = validLocalTaskReceipt();
    const binding = {
      itemRef: localTaskItemRef,
      approvalRef: localTaskApprovalRef,
      idempotencyRef: receipt.idempotency_key_ref,
      safeDisableRef: receipt.safe_disable_ref ?? "",
      rollbackRef: receipt.rollback_ref ?? "",
    };

    expect(localTaskCommitReceiptIsSafe(receipt, binding)).toBe(true);
    expect(localTaskCommitReceiptIsSafe({
      ...receipt,
      authority_decision_ref: "authority-policy-decision-ref:substituted",
    }, binding)).toBe(false);
    for (const unsafeSummary of [
      `credential: ${"x".repeat(20)}`,
      `Bearer ${"a".repeat(20)}`,
      "Host MacBook-Pro.local",
      "username=operator",
      "Review /Users/operator/private.log",
      "raw_prompt: copy the private prompt here",
      "response: private model output",
      "Receipt created by alice@example.com",
      `ghp_${"a".repeat(36)}`,
    ]) {
      expect(localTaskCommitReceiptIsSafe({
        ...receipt,
        safe_summary: unsafeSummary,
      }, binding)).toBe(false);
    }
    expect(localTaskCommitReceiptIsSafe({
      ...receipt,
      receipt_ref: "receipt-ref:/Users/operator/private.log",
    }, binding)).toBe(false);
    expect(localTaskCommitReceiptIsSafe({
      ...receipt,
      evidence_refs: receipt.evidence_refs.filter(
        (ref) => ref !== receipt.authority_policy_receipt_ref,
      ),
    }, binding)).toBe(false);
  });
});
