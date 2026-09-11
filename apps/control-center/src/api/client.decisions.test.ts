import { afterEach, describe, expect, it, vi } from "vitest";

import {
  actionDecisionIdempotencyRef,
  buildLocalTaskCommitAuthorityRequest,
  buildLocalTaskCommitRequest,
  fetchNorthStarDecisionsInbox,
  founderLoopLocalTaskRef,
  localTaskAuthorityProofRefs,
  localTaskCommitDerivedRefs,
  localTaskCommitIdempotencyRef,
  localTaskCommitReceiptIsSafe,
  loadNorthStarDecisionsData,
  submitActionCancellation,
  submitActionDecision,
} from "./client";
import { API_ENDPOINTS } from "./endpoints";
import { mockControlCenterData } from "../mocks/controlCenterData";
import type {
  FounderLoopActionInboxDecisionLaneId,
  FounderLoopActionDecisionReceipt,
  FounderLoopActionLifecycleDecisionKind,
  FounderLoopActionsInbox,
  FounderLoopLocalTaskCommitReceipt,
} from "./types";

const binding = {
  snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"1".repeat(64)}`,
  backendRevisionRef: `commit-ref:git:${"2".repeat(40)}`,
  backendInstanceRef:
    "backend-instance-ref:control-center:33333333333333333333333333333333",
};

const localTaskItemRef = "founder-action:mock-local-task-review";
const localTaskApprovalRef = "approval-ref:northstar:local-task-approved";

function validActionDecisionReceipt(
  itemRef: string,
  decision: FounderLoopActionLifecycleDecisionKind,
  expectedRevisionRef: string,
  resultRevisionRef = expectedRevisionRef,
): FounderLoopActionDecisionReceipt {
  const request = {
    expected_revision_ref: expectedRevisionRef,
    decision_reason_ref: `decision-reason-ref:test:${decision}`,
  };
  const advanced = resultRevisionRef !== expectedRevisionRef;
  const resultGeneration = advanced ? 2 : 1;
  return {
    contract_ref: "contract-ref:founder-loop-action-state-machine:v1",
    decision_ref: `decision-ref:test:${decision}`,
    item_ref: itemRef,
    decision,
    status: decision === "cancel" ? "cancelled" : "deferred",
    receipt_ref: `receipt:founder-loop-action:test:${decision}`,
    audit_ref: `audit:founder-loop-action:test:${decision}`,
    idempotency_key_ref: actionDecisionIdempotencyRef(
      itemRef,
      decision,
      request,
    ),
    payload_fingerprint_ref: `payload-fingerprint-ref:test:${decision}`,
    expected_revision_ref: expectedRevisionRef,
    generation: 1,
    generation_ref: "action-generation:test:00000001",
    revision_ref: expectedRevisionRef,
    revision_fingerprint_ref:
      "revision-fingerprint:action-inbox:11111111111111111111",
    result_generation: resultGeneration,
    result_generation_ref: `action-generation:test:${String(resultGeneration).padStart(8, "0")}`,
    result_revision_ref: resultRevisionRef,
    result_revision_fingerprint_ref:
      `revision-fingerprint:action-inbox:${(advanced ? "2" : "1").repeat(20)}`,
    revision_advanced: advanced,
    approval_scope_ref:
      "approval-scope:action-inbox-revision:11111111111111111111",
    decision_route_ref:
      `POST /control-center/actions/{action_id}/${decision}`,
    decision_route_binding_ref:
      `route-ref:control-center:action-decision:${decision}`,
    decision_adapter_ref:
      "adapter-ref:python-core:founder-loop-action-decisions",
    decision_deadline_ref: "deadline-ref:action-inbox-decision:test:00000001",
    authority_input_refs: ["authority-action-ref:action-inbox-decision-receipt"],
    invalidated_approval_refs: [],
    invalidated_approval_count: 0,
    approval_ref: null,
    approval_status: "not_required_for_decision",
    approval_reason_refs: [],
    action_executed: false,
    approval_grants_execution: false,
    connector_write_performed: false,
    memory_write_performed: false,
    raw_content_stored: false,
    replayed: false,
    safe_summary: "Exact Action decision receipt recorded without execution.",
    evidence_refs: ["evidence-ref:test:action-decision"],
    blocked_state_refs: ["blocked-state:no-action-execution"],
    authority_domain_ref: "authority-domain-ref:workspace",
    authority_capability_ref: "authority-capability-ref:write",
    authority_required_mode_ref: "authority-mode-ref:ask-before-changes",
    created_at: "2026-09-10T00:00:00Z",
  };
}

async function validLocalTaskReceipt(
  itemRef = localTaskItemRef,
  approvalRef = localTaskApprovalRef,
): Promise<FounderLoopLocalTaskCommitReceipt> {
  const request = buildLocalTaskCommitRequest(
    itemRef,
    approvalRef,
  );
  const authorityLeaseRef = "authority-lease-ref:northstar-workspace-write";
  const authorityProof = await localTaskAuthorityProofRefs(
    authorityLeaseRef,
    "ask",
  );
  const authorityProofRefs = [
    authorityProof.authorityDecisionRef,
    authorityLeaseRef,
    authorityProof.authorityAuditRef,
    authorityProof.authorityPolicyReceiptRef,
  ] as const;
  const derivedRefs = await localTaskCommitDerivedRefs(
    itemRef,
    request,
  );
  return {
    contract_ref: "contract-ref:founder-loop-local-task-commit:v1",
    item_ref: itemRef,
    action_kind: "local_task_create",
    local_task_ref: founderLoopLocalTaskRef(itemRef),
    status: "local_task_created",
    receipt_ref: derivedRefs.receiptRef,
    audit_ref: derivedRefs.auditRef,
    idempotency_key_ref: localTaskCommitIdempotencyRef(
      itemRef,
      request,
    ),
    payload_fingerprint_ref: derivedRefs.payloadFingerprintRef,
    run_ref: "run-ref:founder-loop-v1:governed-local-loop",
    evidence_timeline_event_ref: derivedRefs.evidenceTimelineEventRef,
    approval_ref: approvalRef,
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
      derivedRefs.evidenceTimelineEventRef,
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
  for (const [index, item] of inbox.items.entries()) {
    const generation = index + 1;
    const revisionRef =
      `action-revision:bounded-decision-${generation}:00000001:${String(generation).repeat(20).slice(0, 20)}`;
    Object.assign(item, {
      action_revision_ref: revisionRef,
      expected_revision_ref: revisionRef,
      action_revision_decision_eligible: true,
    });
    if (item.approval_envelope) {
      Object.assign(item.approval_envelope, {
        schema_version: "founder_loop_action_approval_envelope.v1",
        contract_ref: "contract-ref:founder-loop-action-approval-envelope:v1",
        source: "python_core_action_inbox_read_model",
        backend_owned: true,
      });
    }
    if (item.receipt_visibility) {
      Object.assign(item.receipt_visibility, {
        schema_version: "founder_loop_action_receipt_visibility.v1",
        contract_ref:
          "contract-ref:founder-loop-action-receipt-visibility:v1",
        source: "python_core_action_inbox_read_model",
        backend_owned: true,
      });
    }
  }
  inbox.expected_revision_required = true;
  inbox.cancel_decision_enabled = true;
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
  const laneLabels: Record<string, string> = {
    needs_approval: "Needs approval",
    blocked: "Blocked",
    draft_only: "Draft-only",
    cost_blocked: "Cost blocked",
    no_authority: "No authority",
    approved_no_execution: "Approved / no execution",
    rejected: "Rejected",
    deferred: "Deferred",
    receipt_recorded: "Receipt recorded",
  };
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
      label: laneLabels[laneId],
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
  for (const lane of workQueue.lanes) {
    lane.item_refs = inbox.items
      .filter((item) => item.action_group_id === lane.lane_id)
      .map((item) => item.item_ref);
    lane.count = lane.item_refs.length;
  }
  const laneCount = (laneId: string) => workQueue.lanes
    .find((lane) => lane.lane_id === laneId)?.count ?? 0;
  workQueue.item_count = inbox.items.length;
  workQueue.ready_for_decision_count = laneCount("ready_for_decision");
  workQueue.approved_local_task_count = laneCount("approved_local_task_lane");
  workQueue.proposal_only_count = laneCount("proposal_only_no_execution_path");
  workQueue.blocked_count = laneCount("blocked_by_authority");
  workQueue.receipt_recorded_count = laneCount("receipt_recorded");
  workQueue.operator_actionable_count = workQueue.ready_for_decision_count
    + workQueue.approved_local_task_count;
  const inboxItemRefs = new Set(inbox.items.map((item) => item.item_ref));
  workQueue.work_items = workQueue.work_items.filter((item) =>
    inboxItemRefs.has(item.item_ref));
  workQueue.work_item_refs = workQueue.work_items.map((item) => item.item_ref);
  workQueue.work_item_count = workQueue.work_items.length;
  const decisionReadModel = inbox.action_inbox_decision_lane_read_model;
  const decisionLaneId = (
    action: (typeof inbox.items)[number],
  ): (typeof decisionReadModel.items)[number]["lane_id"] => {
    switch (action.action_group_id) {
      case "blocked_by_authority": return "blocked";
      case "expired_stale": return "deferred";
      case "approved_local_task_lane": return "approved_no_execution";
      case "receipt_recorded": return action.status === "rejected"
        ? "rejected"
        : action.status === "deferred"
          ? "deferred"
          : action.status === "approved"
            ? "approved_no_execution"
            : "receipt_recorded";
      case "proposal_only_no_execution_path": return "draft_only";
      default: return "needs_approval";
    }
  };
  decisionReadModel.items = inbox.items.map((action) => {
    const laneId = decisionLaneId(action);
    const laneLabel = laneLabels[laneId];
    const expectedReceiptRefs = action.action_expected_receipt_refs
      ?? action.approval_envelope?.expected_receipt_refs
      ?? [];
    return {
      item_ref: action.item_ref,
      lane_id: laneId,
      lane_label: laneLabel,
      title: action.title,
      status: action.status,
      priority: action.priority,
      action_kind: action.action_kind ?? "review_only",
      side_effect_class: action.side_effect_class,
      safe_summary: action.safe_summary,
      why_shown: action.action_group_reason ?? "Backend-derived decision lane.",
      next_safe_action: action.next_safe_action,
      authority_boundary: action.authority_boundary,
      approval_required: action.approval_required,
      approval_envelope_ref: action.approval_envelope_ref,
      approval_envelope_status: action.approval_envelope_status,
      approval_scope_ref:
        action.action_scope_ref ?? action.approval_envelope?.exact_scope,
      approval_requirement_ref:
        action.action_approval_requirement_ref
        ?? action.approval_envelope?.approval_requirement,
      expected_receipt_refs: expectedReceiptRefs,
      expected_receipt_state: "visible",
      evidence_refs: action.evidence_refs,
      receipt_refs: action.receipt_refs,
      expected_receipt_refs_visible: true,
      rollback_ref: action.action_rollback_ref ?? action.rollback_ref,
      safe_disable_ref: action.action_safe_disable_ref ?? action.safe_disable_ref,
      blocked_authority_refs: action.action_blocked_state_refs ?? [],
      missing_envelope_field_states: [],
      cost_state_label: "Cost approved",
      provider_authority_state_label: "No provider authority",
      estimated_cost_usd: 0,
      max_approved_cost_usd: 0,
      provider_ref: "provider-ref:not-invoked",
      model_profile_ref: "model-profile-ref:not-invoked",
      input_metered_units: 0,
      output_metered_units: 0,
      total_metered_units: 0,
      cost_estimate_ref: `cost-estimate-ref:test:${action.item_ref}`,
      captured_usage_ref: `usage-capture-ref:test:${action.item_ref}`,
      budget_decision_ref: `budget-decision-ref:test:${action.item_ref}`,
      cost_receipt_refs: [],
      cost_blocked_state_refs: [],
      unknown_paid_cost_requires_explicit_approval: true,
      frontier_usage_claimed: false,
      cost_telemetry_complete: true,
      provider_model_refs_present: false,
      backend_owned: true,
      safe_refs_only: true,
      raw_content_included: false,
      approval_alone_executes: false,
      approval_ref_authority: false,
      approval_grants_runtime_authority: false,
      action_execution_enabled: false,
      connector_write_enabled: false,
      shell_subprocess_execution_enabled: false,
      browser_execution_enabled: false,
      provider_model_call_enabled: false,
      memory_write_enabled: false,
      context_injection_authorized: false,
      hidden_memory_write_authorized: false,
      production_authority_enabled: false,
    };
  });
  for (const lane of decisionReadModel.lanes) {
    lane.item_refs = decisionReadModel.items
      .filter((item) => item.lane_id === lane.lane_id)
      .map((item) => item.item_ref);
    lane.count = lane.item_refs.length;
  }
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

function setDecisionLaneForItem(
  inbox: FounderLoopActionsInbox,
  itemRef: string,
  laneId: FounderLoopActionInboxDecisionLaneId,
) {
  const readModel = inbox.action_inbox_decision_lane_read_model;
  const laneItem = readModel?.items.find((item) => item.item_ref === itemRef);
  if (!readModel || !laneItem) {
    throw new Error(`Missing decision-lane fixture for ${itemRef}`);
  }
  const laneLabels: Record<FounderLoopActionInboxDecisionLaneId, string> = {
    needs_approval: "Needs approval",
    blocked: "Blocked",
    draft_only: "Draft-only",
    cost_blocked: "Cost blocked",
    no_authority: "No authority",
    approved_no_execution: "Approved / no execution",
    rejected: "Rejected",
    deferred: "Deferred",
    receipt_recorded: "Receipt recorded",
  };
  laneItem.lane_id = laneId;
  laneItem.lane_label = laneLabels[laneId];
  for (const lane of readModel.lanes) {
    lane.item_refs = readModel.items
      .filter((item) => item.lane_id === lane.lane_id)
      .map((item) => item.item_ref);
    lane.count = lane.item_refs.length;
  }
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

  it.each([
    ["missing", undefined],
    ["malformed", { lease_ref: "authority-lease-ref:unsafe" }],
  ])("fails closed when active AuthorityLease data is %s", async (_label, activeLeases) => {
    const fixtures = boundedDecisionFixtures();
    const settings = fixtures[API_ENDPOINTS.controlCenterSettingsStatus] as {
      authority_lease_state: { active_leases?: unknown };
    };
    settings.authority_lease_state.active_leases = activeLeases;
    stubBoundedFetch(fixtures);

    await expect(loadNorthStarDecisionsData(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it.each([
    ["missing", undefined],
    ["incompatible", { item_ref: "founder-action:invalid-items-shape" }],
  ])("fails closed when a refreshed inbox has %s items", async (_label, items) => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as
      Record<string, unknown>;
    if (items === undefined) delete inbox.items;
    else inbox.items = items;
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it("rejects a non-string local task commit approval ref", async () => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      items: Array<Record<string, unknown>>;
    };
    inbox.items[0].local_task_commit_approval_ref = 42;
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it.each([
    "action_revision_ref",
    "expected_revision_ref",
  ] as const)("rejects an unsafe %s before enabling Decisions", async (field) => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      items: Array<Record<string, unknown>>;
    };
    inbox.items[0][field] = { unsafe: "revision" };
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it("rejects an unbound projected local-task receipt", async () => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      items: Array<Record<string, unknown>>;
    };
    inbox.items[0].local_task_commit_receipt_ref =
      "receipt:founder-loop-local-task:substituted";
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it("rejects a terminal receipt visible only in the nested projection", async () => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      items: Array<Record<string, unknown>>;
    };
    const receiptVisibility = inbox.items[0].receipt_visibility as
      Record<string, unknown>;
    receiptVisibility.local_task_commit_receipt_ref =
      "receipt:founder-loop-local-task:substituted";
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it("rejects a non-string projected local-task receipt", async () => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      items: Array<Record<string, unknown>>;
    };
    inbox.items[0].local_task_commit_receipt_ref = { unsafe: "receipt" };
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it.each([
    ["approval_required_before_mutation", "true"],
    ["mutating_controls_enabled", "false"],
    ["action_execution_enabled", "false"],
    ["decision_receipts_required", "false"],
    ["expected_revision_required", "false"],
    ["cancel_decision_enabled", "false"],
  ])("rejects a non-boolean top-level %s posture", async (field, value) => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as
      Record<string, unknown>;
    inbox[field] = value;
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it("rejects unsafe nested decision-lane display text", async () => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      action_inbox_decision_lane_read_model: {
        lanes: Array<Record<string, unknown>>;
      };
    };
    inbox.action_inbox_decision_lane_read_model.lanes[0].label =
      "raw_prompt: private backend content";
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it.each([
    ["title", `credential: ${"x".repeat(20)}`],
    ["safe_summary", "raw_prompt: private backend content"],
    ["next_safe_action", "Review /Users/operator/private.log"],
    ["action_group_label", "Assigned to operator@example.com"],
    ["action_group_id", "group:/Users/operator/private"],
    ["action_scope_ref", "scope-ref:/Users/operator/private"],
    ["action_envelope_ref", "envelope-ref:hostname=private.local"],
  ])("rejects unsafe refreshed inbox %s text", async (field, unsafeText) => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      items: Array<Record<string, unknown>>;
    };
    inbox.items[0][field] = unsafeText;
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it("accepts the backend-defined expired Action Inbox group", async () => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      items: Array<Record<string, unknown>>;
      action_inbox_work_queue_read_model: unknown;
    };
    inbox.items[0].action_group_id = "expired_stale";
    inbox.items[0].action_group_label = "Expired/stale";
    const workQueue = inbox.action_inbox_work_queue_read_model as {
      ready_for_decision_count: number;
      operator_actionable_count: number;
      lanes: Array<{
        lane_id: string;
        label: string;
        count: number;
        item_refs: string[];
      }>;
      work_items: Array<Record<string, unknown>>;
    };
    const itemRef = String(inbox.items[0].item_ref);
    const priorLane = workQueue.lanes.find((lane) =>
      lane.item_refs.includes(itemRef));
    const expiredLane = workQueue.lanes.find((lane) =>
      lane.lane_id === "expired_stale");
    const workItem = workQueue.work_items.find((candidate) =>
      candidate.item_ref === itemRef);
    if (!priorLane || !expiredLane || !workItem) {
      throw new Error("Expected bounded work-queue group fixtures");
    }
    priorLane.item_refs = priorLane.item_refs.filter((ref) => ref !== itemRef);
    priorLane.count = priorLane.item_refs.length;
    workQueue.ready_for_decision_count -= 1;
    workQueue.operator_actionable_count -= 1;
    expiredLane.item_refs.push(itemRef);
    expiredLane.count = expiredLane.item_refs.length;
    workItem.lane_id = "expired_stale";
    workItem.lane_label = "Expired/stale";
    setDecisionLaneForItem(
      inbox as unknown as FounderLoopActionsInbox,
      itemRef,
      "deferred",
    );
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).resolves.toEqual(
      expect.objectContaining({ items: expect.any(Array) }),
    );
  });

  it("rejects a mismatched Action Inbox group label", async () => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      items: Array<Record<string, unknown>>;
    };
    inbox.items[0].action_group_id = "receipt_recorded";
    inbox.items[0].action_group_label = "Ready for decision";
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it("rejects a valid Action Inbox group pair rebound from its work-queue lane", async () => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      items: Array<Record<string, unknown>>;
    };
    inbox.items[0].action_group_id = "receipt_recorded";
    inbox.items[0].action_group_label = "Receipt recorded";
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it("rejects an empty Action Inbox while the work queue retains items", async () => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      items: unknown[];
    };
    inbox.items = [];
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it("rejects work-queue aggregate counts that do not match the inbox", async () => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      action_inbox_work_queue_read_model: { item_count: number };
    };
    inbox.action_inbox_work_queue_read_model.item_count += 1;
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it("rejects a work-queue lane ref with no matching Action Inbox item", async () => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      action_inbox_work_queue_read_model: {
        item_count: number;
        lanes: Array<{ count: number; item_refs: string[] }>;
      };
    };
    const workQueue = inbox.action_inbox_work_queue_read_model;
    workQueue.lanes[0].item_refs.push("founder-action:orphaned-work-queue-item");
    workQueue.lanes[0].count += 1;
    workQueue.item_count += 1;
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it("accepts the backend lane's bounded first eight refs while validating its full count", async () => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      items: Array<Record<string, unknown>>;
      action_inbox_work_queue_read_model: {
        item_count: number;
        ready_for_decision_count: number;
        approved_local_task_count: number;
        proposal_only_count: number;
        blocked_count: number;
        receipt_recorded_count: number;
        operator_actionable_count: number;
        work_item_count: number;
        work_item_refs: string[];
        work_items: Array<Record<string, unknown>>;
        lanes: Array<{
          lane_id: string;
          label: string;
          count: number;
          item_refs: string[];
        }>;
      };
    };
    const sourceItem = inbox.items[0];
    const workQueue = inbox.action_inbox_work_queue_read_model;
    const sourceWorkItem = workQueue.work_items[0];
    if (!sourceItem || !sourceWorkItem) {
      throw new Error("Expected bounded Action Inbox fixtures");
    }
    inbox.items = Array.from({ length: 9 }, (_, index) => ({
      ...structuredClone(sourceItem),
      item_ref: `founder-action:bounded-lane-${index + 1}`,
      action_group_id: "ready_for_decision",
      action_group_label: "Ready for decision",
    }));
    for (const lane of workQueue.lanes) {
      const matchingRefs = inbox.items
        .filter((item) => item.action_group_id === lane.lane_id)
        .map((item) => String(item.item_ref));
      lane.count = matchingRefs.length;
      lane.item_refs = matchingRefs.slice(0, 8);
    }
    workQueue.item_count = inbox.items.length;
    workQueue.ready_for_decision_count = inbox.items.length;
    workQueue.approved_local_task_count = 0;
    workQueue.proposal_only_count = 0;
    workQueue.blocked_count = 0;
    workQueue.receipt_recorded_count = 0;
    workQueue.operator_actionable_count = inbox.items.length;
    workQueue.work_items = inbox.items.slice(0, 6).map((item) => ({
      ...structuredClone(sourceWorkItem),
      item_ref: item.item_ref,
      lane_id: "ready_for_decision",
      lane_label: "Ready for decision",
    }));
    workQueue.work_item_refs = workQueue.work_items.map((item) =>
      String(item.item_ref));
    workQueue.work_item_count = workQueue.work_items.length;
    const decisionReadModel = (
      inbox as unknown as FounderLoopActionsInbox
    ).action_inbox_decision_lane_read_model;
    const sourceDecisionItem = decisionReadModel?.items[0];
    if (!decisionReadModel || !sourceDecisionItem) {
      throw new Error("Expected bounded decision-lane fixtures");
    }
    decisionReadModel.items = inbox.items.map((item) => ({
      ...structuredClone(sourceDecisionItem),
      item_ref: String(item.item_ref),
    }));
    for (const lane of decisionReadModel.lanes) {
      lane.item_refs = decisionReadModel.items
        .filter((item) => item.lane_id === lane.lane_id)
        .map((item) => item.item_ref);
      lane.count = lane.item_refs.length;
    }
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).resolves.toEqual(
      expect.objectContaining({ items: expect.any(Array) }),
    );
  });

  it("accepts dotted structured refs without treating them as hostnames", async () => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      items: Array<{
        action_scope_ref: string;
        approval_envelope?: { exact_scope: string };
      }>;
    };
    if (!inbox.items[0].approval_envelope) {
      throw new Error("Expected bounded approval envelope fixture");
    }
    inbox.items[0].action_scope_ref = "scope-ref:release.v1";
    inbox.items[0].approval_envelope.exact_scope = "scope-ref:release.v1";
    const laneItem = (
      inbox as unknown as FounderLoopActionsInbox
    ).action_inbox_decision_lane_read_model?.items[0];
    if (!laneItem) throw new Error("Expected bounded decision-lane item");
    laneItem.approval_scope_ref = "scope-ref:release.v1";
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).resolves.toEqual(
      expect.objectContaining({ items: expect.any(Array) }),
    );
  });

  it("rejects a decision lane rebound across the authoritative work queue", async () => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox];
    const blockedItem = inbox.items.find(
      (item) => item.action_group_id === "blocked_by_authority",
    );
    if (!blockedItem) throw new Error("Expected blocked Action Inbox item");
    setDecisionLaneForItem(inbox, blockedItem.item_ref, "needs_approval");
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it("rejects unsafe refreshed nested approval-envelope text", async () => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      items: Array<{ approval_envelope?: { exact_scope: string } }>;
    };
    if (!inbox.items[0].approval_envelope) {
      throw new Error("Expected bounded approval envelope fixture");
    }
    inbox.items[0].approval_envelope.exact_scope =
      "scope-ref:/Users/operator/private";
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it.each([
    ["backend_owned", "false"],
    ["source", "mock_fallback_non_authoritative"],
    ["contract_ref", "contract-ref:founder-loop-action-approval-envelope:other"],
  ])("rejects an approval envelope with non-canonical %s", async (field, value) => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      items: Array<{ approval_envelope?: Record<string, unknown> }>;
    };
    if (!inbox.items[0].approval_envelope) {
      throw new Error("Expected bounded approval envelope fixture");
    }
    inbox.items[0].approval_envelope[field] = value;
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });

  it.each([
    ["backend_owned", "false"],
    ["source", "mock_fallback_non_authoritative"],
    ["contract_ref", "contract-ref:founder-loop-action-receipt-visibility:other"],
    ["schema_version", "founder_loop_action_receipt_visibility.v2"],
  ])("rejects receipt visibility with non-canonical %s", async (field, value) => {
    const fixtures = boundedDecisionFixtures();
    const inbox = fixtures[API_ENDPOINTS.founderActionsInbox] as unknown as {
      items: Array<{ receipt_visibility?: Record<string, unknown> }>;
    };
    if (!inbox.items[0].receipt_visibility) {
      throw new Error("Expected bounded receipt visibility fixture");
    }
    inbox.items[0].receipt_visibility[field] = value;
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).rejects.toThrow(
      "NORTH_STAR_DECISIONS_RESPONSE_INVALID",
    );
  });
});

describe("action decision receipt boundary", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("admits only receipts bound to the exact decision and cancellation requests", async () => {
    const itemRef = "founder-action:receipt-binding";
    const revisionRef =
      "action-revision:receipt-binding:00000001:11111111111111111111";
    const resultRevisionRef =
      "action-revision:receipt-binding:00000002:22222222222222222222";
    const deferReceipt = validActionDecisionReceipt(
      itemRef,
      "defer",
      revisionRef,
    );
    const cancelReceipt = validActionDecisionReceipt(
      itemRef,
      "cancel",
      revisionRef,
      resultRevisionRef,
    );
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        ok: true,
        result: deferReceipt,
      }), { status: 200, headers: headersForBinding() }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        ok: true,
        result: cancelReceipt,
      }), { status: 200, headers: headersForBinding() })));

    await expect(submitActionDecision(itemRef, "defer", {
      expected_revision_ref: revisionRef,
      decision_reason_ref: "decision-reason-ref:test:defer",
    }, binding)).resolves.toEqual(deferReceipt);
    await expect(submitActionCancellation(itemRef, {
      expected_revision_ref: revisionRef,
      decision_reason_ref: "decision-reason-ref:test:cancel",
    }, binding)).resolves.toEqual(cancelReceipt);
  });

  it("rejects substituted or unsafe decision receipt evidence", async () => {
    const itemRef = "founder-action:receipt-rejection";
    const revisionRef =
      "action-revision:receipt-rejection:00000001:11111111111111111111";
    const request = {
      expected_revision_ref: revisionRef,
      decision_reason_ref: "decision-reason-ref:test:defer",
    };
    const receipt = validActionDecisionReceipt(itemRef, "defer", revisionRef);
    for (const unsafeReceipt of [
      { ...receipt, item_ref: "founder-action:substituted" },
      { ...receipt, decision: "approve" },
      { ...receipt, expected_revision_ref: "action-revision:substituted" },
      { ...receipt, idempotency_key_ref: "idempotency-ref:substituted" },
      { ...receipt, safe_summary: "raw_prompt: private backend content" },
      { ...receipt, replayed: "false" },
      { ...receipt, action_executed: true },
    ]) {
      vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({
        ok: true,
        result: unsafeReceipt,
      }), { status: 200, headers: headersForBinding() })));
      await expect(submitActionDecision(
        itemRef,
        "defer",
        request,
        binding,
      )).rejects.toThrow("Action decision receipt was not recorded safely.");
    }
  });
});

function headersForBinding(): Headers {
  return new Headers({
    "Content-Type": "application/json",
    "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
    "X-UAA-Backend-Instance-Ref": binding.backendInstanceRef,
  });
}

describe("local task commit boundary", () => {
  it("accepts exact Core-derived receipt refs longer than the display-text cap", async () => {
    const itemRef = `founder-action:${"i".repeat(80)}`;
    const approvalRef = `approval-ref:${"a".repeat(85)}`;
    const request = buildLocalTaskCommitRequest(itemRef, approvalRef);
    const receipt = await validLocalTaskReceipt(itemRef, approvalRef);
    const exactBinding = {
      itemRef,
      approvalRef,
      idempotencyRef: receipt.idempotency_key_ref,
      request,
      safeDisableRef: receipt.safe_disable_ref ?? "",
      rollbackRef: receipt.rollback_ref ?? "",
    };

    expect(receipt.receipt_ref.length).toBeGreaterThan(240);
    expect(await localTaskCommitReceiptIsSafe(receipt, exactBinding)).toBe(true);
  });

  it("builds one canonical payload and binds authority evaluation to the exact item", async () => {
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
    await expect(localTaskAuthorityProofRefs(
      "authority-lease-ref:northstar-workspace-write",
      "ask",
    )).resolves.toEqual({
      authorityDecisionRef:
        "authority-policy-decision-ref:sha256:06aa4ea47021558fd62b7da8",
      authorityAuditRef:
        "audit-ref:authority-policy:sha256:06aa4ea47021558fd62b7da8",
      authorityPolicyReceiptRef:
        "receipt-ref:authority-policy:sha256:c67344a7b22a5b5c27497c81",
    });
    await expect(localTaskCommitDerivedRefs(
      localTaskItemRef,
      request,
    )).resolves.toEqual({
      receiptRef:
        "receipt:founder-loop-local-task:founder-action-mock-local-task-review:idempotency-ref-control-center-local-task-mock-local-task-review-approval-ref-northstar-local-task-approved",
      auditRef:
        "audit:founder-loop-local-task:founder-action-mock-local-task-review:idempotency-ref-control-center-local-task-mock-local-task-review-approval-ref-northstar-local-task-approved",
      evidenceTimelineEventRef:
        "evidence-timeline:local-task/founder-action-mock-local-task-review",
      payloadFingerprintRef:
        "payload-fingerprint:founder-loop-local-task:d1213b519d8182dbbd2d198ec7a3d1f457713d28e83c3b4bfe850515d0e8775b",
    });
  });

  it("rejects receipts without the exact authority proof or with unsafe display data", async () => {
    const receipt = await validLocalTaskReceipt();
    const request = buildLocalTaskCommitRequest(
      localTaskItemRef,
      localTaskApprovalRef,
    );
    const binding = {
      itemRef: localTaskItemRef,
      approvalRef: localTaskApprovalRef,
      idempotencyRef: receipt.idempotency_key_ref,
      request,
      safeDisableRef: receipt.safe_disable_ref ?? "",
      rollbackRef: receipt.rollback_ref ?? "",
    };

    expect(await localTaskCommitReceiptIsSafe(receipt, binding)).toBe(true);
    expect(await localTaskCommitReceiptIsSafe({
      ...receipt,
      evidence_refs: [...receipt.evidence_refs, "evidence-ref:release.v1"],
    }, binding)).toBe(true);
    expect(await localTaskCommitReceiptIsSafe({
      ...receipt,
      replayed: undefined,
    } as unknown as FounderLoopLocalTaskCommitReceipt, binding)).toBe(false);
    expect(await localTaskCommitReceiptIsSafe({
      ...receipt,
      replayed: "false",
    } as unknown as FounderLoopLocalTaskCommitReceipt, binding)).toBe(false);
    expect(await localTaskCommitReceiptIsSafe({
      ...receipt,
      authority_decision_ref: "authority-policy-decision-ref:substituted",
    }, binding)).toBe(false);
    const substitutedProofRefs = [
      "authority-policy-decision-ref:sha256:111111111111111111111111",
      receipt.authority_lease_ref,
      "audit-ref:authority-policy:sha256:111111111111111111111111",
      "receipt-ref:authority-policy:sha256:222222222222222222222222",
    ] as const;
    expect(await localTaskCommitReceiptIsSafe({
      ...receipt,
      authority_decision_ref: substitutedProofRefs[0],
      authority_audit_ref: substitutedProofRefs[2],
      authority_policy_receipt_ref: substitutedProofRefs[3],
      evidence_refs: receipt.evidence_refs.map((ref) => {
        if (ref === receipt.authority_decision_ref) return substitutedProofRefs[0];
        if (ref === receipt.authority_audit_ref) return substitutedProofRefs[2];
        if (ref === receipt.authority_policy_receipt_ref) return substitutedProofRefs[3];
        return ref;
      }),
    }, binding)).toBe(false);
    const substitutedDerivedRefs = {
      receiptRef: "receipt:founder-loop-local-task:substituted",
      auditRef: "audit:founder-loop-local-task:substituted",
      eventRef: "evidence-timeline:local-task/substituted",
      payloadRef:
        `payload-fingerprint:founder-loop-local-task:${"1".repeat(64)}`,
    };
    expect(await localTaskCommitReceiptIsSafe({
      ...receipt,
      receipt_ref: substitutedDerivedRefs.receiptRef,
    }, binding)).toBe(false);
    expect(await localTaskCommitReceiptIsSafe({
      ...receipt,
      audit_ref: substitutedDerivedRefs.auditRef,
    }, binding)).toBe(false);
    expect(await localTaskCommitReceiptIsSafe({
      ...receipt,
      evidence_timeline_event_ref: substitutedDerivedRefs.eventRef,
      evidence_refs: receipt.evidence_refs.map((ref) =>
        ref === receipt.evidence_timeline_event_ref
          ? substitutedDerivedRefs.eventRef
          : ref),
    }, binding)).toBe(false);
    expect(await localTaskCommitReceiptIsSafe({
      ...receipt,
      payload_fingerprint_ref: substitutedDerivedRefs.payloadRef,
    }, binding)).toBe(false);
    expect(await localTaskCommitReceiptIsSafe({
      ...receipt,
      safe_disable_posture_ref:
        "safe-disable-posture:founder-loop:local-task-create:substituted",
    }, binding)).toBe(false);
    expect(await localTaskCommitReceiptIsSafe({
      ...receipt,
      approval_reason_refs: [],
    }, binding)).toBe(false);
    expect(await localTaskCommitReceiptIsSafe({
      ...receipt,
      receipt_ref: substitutedDerivedRefs.receiptRef,
      audit_ref: substitutedDerivedRefs.auditRef,
      evidence_timeline_event_ref: substitutedDerivedRefs.eventRef,
      payload_fingerprint_ref: substitutedDerivedRefs.payloadRef,
      evidence_refs: receipt.evidence_refs.map((ref) =>
        ref === receipt.evidence_timeline_event_ref
          ? substitutedDerivedRefs.eventRef
          : ref),
    }, binding)).toBe(false);
    for (const unsafeSummary of [
      `credential: ${"x".repeat(20)}`,
      `Bearer ${"a".repeat(20)}`,
      "Host MacBook-Pro.local",
      "Receipt created on build-17.corp.example.com",
      "username=operator",
      "Review /Users/operator/private.log",
      "raw_prompt: copy the private prompt here",
      "response: private model output",
      "Receipt created by alice@example.com",
      `ghp_${"a".repeat(36)}`,
    ]) {
      expect(await localTaskCommitReceiptIsSafe({
        ...receipt,
        safe_summary: unsafeSummary,
      }, binding)).toBe(false);
    }
    expect(await localTaskCommitReceiptIsSafe({
      ...receipt,
      receipt_ref: "receipt-ref:/Users/operator/private.log",
    }, binding)).toBe(false);
    expect(await localTaskCommitReceiptIsSafe({
      ...receipt,
      evidence_refs: receipt.evidence_refs.filter(
        (ref) => ref !== receipt.authority_policy_receipt_ref,
      ),
    }, binding)).toBe(false);
  });
});
