import { afterEach, describe, expect, it, vi } from "vitest";

import {
  buildLocalTaskCommitAuthorityRequest,
  buildLocalTaskCommitRequest,
  fetchNorthStarDecisionsInbox,
  localTaskAuthorityProofRefs,
  localTaskCommitDerivedRefs,
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

async function validLocalTaskReceipt(): Promise<FounderLoopLocalTaskCommitReceipt> {
  const request = buildLocalTaskCommitRequest(
    localTaskItemRef,
    localTaskApprovalRef,
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
    localTaskItemRef,
    request,
  );
  return {
    contract_ref: "contract-ref:founder-loop-local-task-commit:v1",
    item_ref: localTaskItemRef,
    action_kind: "local_task_create",
    local_task_ref:
      "local-task:founder-loop:founder-action-mock-local-task-review",
    status: "local_task_created",
    receipt_ref: derivedRefs.receiptRef,
    audit_ref: derivedRefs.auditRef,
    idempotency_key_ref: localTaskCommitIdempotencyRef(
      localTaskItemRef,
      request,
    ),
    payload_fingerprint_ref: derivedRefs.payloadFingerprintRef,
    run_ref: "run-ref:founder-loop-v1:governed-local-loop",
    evidence_timeline_event_ref: derivedRefs.evidenceTimelineEventRef,
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
    ["approval_required_before_mutation", "true"],
    ["mutating_controls_enabled", "false"],
    ["action_execution_enabled", "false"],
    ["decision_receipts_required", "false"],
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
    stubBoundedFetch(fixtures);

    await expect(fetchNorthStarDecisionsInbox(binding)).resolves.toEqual(
      expect.objectContaining({ items: expect.any(Array) }),
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
});

describe("local task commit boundary", () => {
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
