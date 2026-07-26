import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mockControlCenterData } from "../mocks/controlCenterData";
import type { FounderLoopActionInboxDecisionLaneReadModel } from "../api/types";
import { BackendTruthMutationBindingProvider } from "../backendTruthMutationBinding";
import { NorthStarControlCenter } from "./NorthStarControlCenter";

const apiMocks = vi.hoisted(() => ({
  submitActionDecision: vi.fn(),
  fetchFounderActionsInbox: vi.fn(),
  recordMemoryReviewDecision: vi.fn(),
  fetchFounderMemoryReview: vi.fn(),
  recordManualMemoryCandidate: vi.fn(),
  revokeAuthorityLease: vi.fn(),
  fetchControlCenterSettingsStatus: vi.fn(),
}));

const mutationBinding = {
  snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"1".repeat(64)}`,
  backendRevisionRef: `commit-ref:git:${"2".repeat(40)}`,
  backendInstanceRef:
    "backend-instance-ref:control-center:33333333333333333333333333333333",
};

vi.mock("../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api/client")>()),
  ...apiMocks,
}));

function cloneData() {
  return structuredClone(mockControlCenterData);
}

function markLiveBackend(data: ReturnType<typeof cloneData>, ...routes: string[]) {
  data.connection.state = "online";
  data.connection.usingMockData = false;
  for (const route of routes) data.routeStates[route].state = "backend_owned";
}

function attachExactDecisionLane(
  data: ReturnType<typeof cloneData>,
  itemRef: string,
  laneId: "needs_approval" | "blocked" = "needs_approval",
) {
  const actionItem = data.founderActionsInbox.items.find((candidate) => candidate.item_ref === itemRef);
  if (!actionItem) throw new Error(`Missing test Action Inbox item ${itemRef}`);
  const actionEnvelopeRef = `action-envelope-ref:test:${itemRef}`;
  const approvalEnvelopeRef = `approval-envelope-ref:test:${itemRef}`;
  const scopeRef = `scope-ref:test:${itemRef}`;
  const expectedReceiptRefs = [`expected-receipt-ref:test:${itemRef}`];
  const rollbackRef = `rollback-ref:test:${itemRef}`;
  const safeDisableRef = `safe-disable-ref:test:${itemRef}`;
  const costEstimateRef = `cost-estimate-ref:test:${itemRef}`;
  const capturedUsageRef = `usage-capture-ref:test:${itemRef}`;
  const budgetDecisionRef = `budget-decision-ref:test:${itemRef}`;
  const costReceiptRefs = [costEstimateRef, capturedUsageRef, budgetDecisionRef];
  Object.assign(actionItem, {
    action_envelope_ref: actionEnvelopeRef,
    approval_envelope_ref: approvalEnvelopeRef,
    action_scope_ref: scopeRef,
    action_expected_receipt_refs: expectedReceiptRefs,
    action_rollback_ref: rollbackRef,
    rollback_ref: rollbackRef,
    action_safe_disable_ref: safeDisableRef,
    safe_disable_ref: safeDisableRef,
    action_envelope_cost_state_label: "Cost approved",
    action_envelope_provider_authority_state_label: "No provider authority",
    action_envelope_estimated_cost_usd: 0,
    action_envelope_max_approved_cost_usd: 0,
    action_envelope_provider_ref: "provider-ref:not-invoked",
    action_envelope_model_profile_ref: "model-profile-ref:not-invoked",
    action_envelope_input_metered_units: 0,
    action_envelope_output_metered_units: 0,
    action_envelope_total_metered_units: 0,
    action_envelope_cost_estimate_ref: costEstimateRef,
    action_envelope_captured_usage_ref: capturedUsageRef,
    action_envelope_budget_decision_ref: budgetDecisionRef,
    action_envelope_cost_receipt_refs: costReceiptRefs,
    action_envelope_cost_blocked_state_refs: [],
    action_envelope_unknown_paid_cost_requires_explicit_approval: true,
    action_envelope_frontier_usage_claimed: false,
    approval_envelope: {
      ...actionItem.approval_envelope,
      source: "python_core_action_inbox_read_model",
      backend_owned: true,
      exact_scope: scopeRef,
      expected_receipt_refs: expectedReceiptRefs,
      cost_state_label: "Cost approved",
      estimated_cost_usd: 0,
      max_approved_cost_usd: 0,
      provider_ref: "provider-ref:not-invoked",
      model_profile_ref: "model-profile-ref:not-invoked",
      input_metered_units: 0,
      output_metered_units: 0,
      total_metered_units: 0,
      cost_estimate_ref: costEstimateRef,
      captured_usage_ref: capturedUsageRef,
      budget_decision_ref: budgetDecisionRef,
      cost_receipt_refs: costReceiptRefs,
      cost_blocked_state_refs: [],
      unknown_paid_cost_requires_explicit_approval: true,
      frontier_usage_claimed: false,
      missing_field_states: ["none"],
    },
    receipt_visibility: {
      ...actionItem.receipt_visibility,
      source: "python_core_action_inbox_read_model",
      backend_owned: true,
      missing_field_states: ["decision_receipt_ref:pending"],
    },
  });
  const laneItem: FounderLoopActionInboxDecisionLaneReadModel["items"][number] = {
    item_ref: itemRef,
    lane_id: laneId,
    lane_label: laneId === "needs_approval" ? "Needs approval" : "Blocked",
    title: actionItem.title,
    status: laneId === "needs_approval" ? "review_ready" : "blocked",
    priority: actionItem.priority,
    action_kind: actionItem.action_kind ?? "review_only",
    side_effect_class: actionItem.side_effect_class,
    safe_summary: actionItem.safe_summary,
    why_shown: "Exact test decision lane binding.",
    next_safe_action: actionItem.next_safe_action,
    authority_boundary: actionItem.authority_boundary,
    approval_required: true,
    approval_envelope_ref: approvalEnvelopeRef,
    approval_envelope_status: "review_ready_exact_scope_required",
    approval_scope_ref: scopeRef,
    approval_requirement_ref: "approval-requirement-ref:test:exact-scope",
    expected_receipt_refs: expectedReceiptRefs,
    expected_receipt_state: "visible",
    evidence_refs: ["evidence-ref:test:decision-lane"],
    receipt_refs: [],
    expected_receipt_refs_visible: true,
    rollback_ref: rollbackRef,
    safe_disable_ref: safeDisableRef,
    blocked_authority_refs: ["blocked-state:test:no-action-execution"],
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
    cost_estimate_ref: costEstimateRef,
    captured_usage_ref: capturedUsageRef,
    budget_decision_ref: budgetDecisionRef,
    cost_receipt_refs: costReceiptRefs,
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
  const readModel: FounderLoopActionInboxDecisionLaneReadModel = {
    contract_ref: "contract-ref:product-loop-005-action-inbox-decision-lanes:v1",
    status: "implemented_backend_owned_decision_lanes",
    source: "python_core_action_inbox_decision_lane_read_model",
    backend_owned: true,
    local_read_model_only: true,
    safe_refs_only: true,
    raw_content_included: false,
    lane_order: ["needs_approval", "blocked", "draft_only", "cost_blocked", "no_authority", "approved_no_execution", "rejected", "deferred", "receipt_recorded"],
    lanes: [{
      lane_id: laneId,
      label: laneId === "needs_approval" ? "Needs approval" : "Blocked",
      status: laneId === "needs_approval" ? "review_ready" : "blocked",
      safe_summary: "Exact test decision lane.",
      count: 1,
      item_refs: [itemRef],
      blocked_state_refs: laneId === "blocked" ? ["blocked-state:test:decision-lane"] : [],
      next_safe_action: actionItem.next_safe_action,
      approval_alone_executes: false,
      action_execution_enabled: false,
    }],
    items: [laneItem],
    blocked_state_refs: ["blocked-state:test:no-action-execution"],
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
  };
  data.founderActionsInbox.action_inbox_decision_lane_contract_ref = readModel.contract_ref;
  data.founderActionsInbox.action_inbox_decision_lane_read_model = readModel;
}

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  cleanup();
  window.history.replaceState({}, "", "/");
});

describe("North Star backend wiring", () => {
  it("keeps Work Board mutations unavailable without an exact prepared envelope", () => {
    const data = cloneData();
    data.routeStates["/work-board"].state = "backend_owned";
    Object.assign(data.workBoard, {
      backend_owned: true,
      non_authoritative_mock_fallback: false,
      local_card_create_enabled: true,
      local_card_create_contract_available: true,
      approval_required_for_card_create: true,
      card_create_route_available: true,
      local_task_create_enabled: true,
      local_task_create_contract_available: true,
      approval_required_for_task_create: true,
      task_create_route_available: true,
    });
    render(<NorthStarControlCenter activePath="/workspace/work-board" data={data} />);

    for (const button of screen.getAllByRole("button", { name: /Create card unavailable/ })) {
      expect(button).toBeDisabled();
    }
    expect(screen.getByRole("button", { name: "Create local task unavailable" })).toBeDisabled();
    expect(screen.getByText(/Mutations unavailable without an exact approval envelope/)).toBeVisible();
  });

  it("records an Action Inbox decision receipt and refreshes the backend read model", async () => {
    const data = cloneData();
    markLiveBackend(data, "/actions");
    const item = data.founderActionsInbox.items[0];
    Object.assign(item, {
      action_review_actions: ["approve", "edit", "reject", "defer"],
      action_envelope_cost_state_label: "Cost approved",
      action_envelope_estimated_cost_usd: 0,
      action_envelope_max_approved_cost_usd: 0,
      action_envelope_cost_receipt_refs: ["cost-receipt-ref:test"],
      approval_envelope: {
        ...item.approval_envelope,
        source: "python_core_action_inbox_read_model",
        backend_owned: true,
      },
      receipt_visibility: {
        ...item.receipt_visibility,
        source: "python_core_action_inbox_read_model",
        backend_owned: true,
      },
    });
    attachExactDecisionLane(data, item.item_ref);
    apiMocks.submitActionDecision.mockResolvedValue({
      decision: "reject",
      receipt_ref: "receipt:action-decision:test",
      safe_summary: "Exact rejection receipt recorded.",
      replayed: false,
      action_executed: false,
    });
    apiMocks.fetchFounderActionsInbox.mockResolvedValue(data.founderActionsInbox);

    render(
      <BackendTruthMutationBindingProvider binding={mutationBinding}>
        <NorthStarControlCenter
          activePath="/workspace/decisions"
          data={data}
        />
      </BackendTruthMutationBindingProvider>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Record reject" }));

    await waitFor(() => expect(apiMocks.submitActionDecision).toHaveBeenCalledWith(
      item.item_ref,
      "reject",
      expect.objectContaining({ decision_reason_ref: "decision-reason-ref:northstar-action:reject" }),
      mutationBinding,
    ));
    expect((await screen.findAllByText(/receipt:action-decision:test/)).length).toBeGreaterThan(0);
    expect(apiMocks.fetchFounderActionsInbox).toHaveBeenCalledTimes(1);
  });

  it("does not infer Action Inbox mutation eligibility from group or action kind", () => {
    const data = cloneData();
    data.routeStates["/actions"].state = "backend_owned";
    const item = data.founderActionsInbox.items[0];
    Object.assign(item, {
      action_group_id: "ready_for_decision",
      action_kind: "self_heal_recommendation",
      action_review_actions: ["reject"],
      approval_envelope: { ...item.approval_envelope, source: "python_core_action_inbox_read_model", backend_owned: true },
      receipt_visibility: { ...item.receipt_visibility, source: "python_core_action_inbox_read_model", backend_owned: true },
    });

    render(<NorthStarControlCenter activePath="/workspace/decisions" data={data} />);

    expect(screen.getByRole("button", { name: "Record reject" })).toBeDisabled();
    expect(apiMocks.submitActionDecision).not.toHaveBeenCalled();
  });

  it("keeps a blocked backend decision-lane item read-only", () => {
    const data = cloneData();
    data.routeStates["/actions"].state = "backend_owned";
    const item = data.founderActionsInbox.items[0];
    Object.assign(item, {
      action_review_actions: ["reject"],
      approval_envelope: { ...item.approval_envelope, source: "python_core_action_inbox_read_model", backend_owned: true },
      receipt_visibility: { ...item.receipt_visibility, source: "python_core_action_inbox_read_model", backend_owned: true },
    });
    attachExactDecisionLane(data, item.item_ref, "blocked");

    render(<NorthStarControlCenter activePath="/workspace/decisions" data={data} />);

    expect(screen.getByRole("button", { name: "Record reject" })).toBeDisabled();
    expect(apiMocks.submitActionDecision).not.toHaveBeenCalled();
  });

  it("fails closed when a decision-lane envelope is incomplete or cross-bound", () => {
    const data = cloneData();
    data.routeStates["/actions"].state = "backend_owned";
    const item = data.founderActionsInbox.items[0];
    Object.assign(item, { action_review_actions: ["reject"] });
    attachExactDecisionLane(data, item.item_ref);
    const laneItem = data.founderActionsInbox.action_inbox_decision_lane_read_model?.items[0];
    if (!laneItem) throw new Error("Expected exact decision-lane fixture");
    laneItem.missing_envelope_field_states = ["approval_scope_ref:missing"];

    const view = render(<NorthStarControlCenter activePath="/workspace/decisions" data={data} />);
    expect(screen.getByRole("button", { name: "Record reject" })).toBeDisabled();

    const crossBound = cloneData();
    crossBound.routeStates["/actions"].state = "backend_owned";
    const crossBoundItem = crossBound.founderActionsInbox.items[0];
    Object.assign(crossBoundItem, { action_review_actions: ["reject"] });
    attachExactDecisionLane(crossBound, crossBoundItem.item_ref);
    const crossBoundLane = crossBound.founderActionsInbox.action_inbox_decision_lane_read_model?.items[0];
    if (!crossBoundLane) throw new Error("Expected exact decision-lane fixture");
    crossBoundLane.approval_scope_ref = "scope-ref:test:another-action";
    view.rerender(<NorthStarControlCenter activePath="/workspace/decisions" data={crossBound} />);

    expect(screen.getByRole("button", { name: "Record reject" })).toBeDisabled();
    expect(apiMocks.submitActionDecision).not.toHaveBeenCalled();
  });

  it("fails closed when approval cost or expected-receipt projections conflict", () => {
    const data = cloneData();
    markLiveBackend(data, "/actions");
    const item = data.founderActionsInbox.items[0];
    Object.assign(item, { action_review_actions: ["approve"] });
    attachExactDecisionLane(data, item.item_ref);
    const laneItem = data.founderActionsInbox.action_inbox_decision_lane_read_model?.items[0];
    if (!laneItem) throw new Error("Expected exact decision-lane fixture");
    laneItem.estimated_cost_usd = 1;
    laneItem.provider_authority_state_label = "Provider/model refs present";

    const view = render(<NorthStarControlCenter activePath="/workspace/decisions" data={data} />);
    expect(screen.getByRole("button", { name: "Record approve" })).toBeDisabled();

    const missingReceipts = cloneData();
    markLiveBackend(missingReceipts, "/actions");
    const missingReceiptItem = missingReceipts.founderActionsInbox.items[0];
    Object.assign(missingReceiptItem, { action_review_actions: ["approve"] });
    attachExactDecisionLane(missingReceipts, missingReceiptItem.item_ref);
    missingReceiptItem.action_expected_receipt_refs = [];
    if (missingReceiptItem.approval_envelope) missingReceiptItem.approval_envelope.expected_receipt_refs = [];
    const missingReceiptLane = missingReceipts.founderActionsInbox.action_inbox_decision_lane_read_model?.items[0];
    if (!missingReceiptLane) throw new Error("Expected exact decision-lane fixture");
    missingReceiptLane.expected_receipt_refs = [];
    view.rerender(<NorthStarControlCenter activePath="/workspace/decisions" data={missingReceipts} />);

    expect(screen.getByRole("button", { name: "Record approve" })).toBeDisabled();
    expect(apiMocks.submitActionDecision).not.toHaveBeenCalled();
  });

  it("keeps Action, Memory, and lease mutations disabled on contradictory mock connection state", () => {
    const data = cloneData();
    data.routeStates["/actions"].state = "backend_owned";
    const action = data.founderActionsInbox.items[0];
    Object.assign(action, { action_review_actions: ["reject"] });
    attachExactDecisionLane(data, action.item_ref);
    const view = render(<NorthStarControlCenter activePath="/workspace/decisions" data={data} />);
    expect(screen.getByRole("button", { name: "Record reject" })).toBeDisabled();

    data.routeStates["/memory"].state = "backend_owned";
    const memoryCandidate = structuredClone(data.founderToday.memory_review_queue[0]);
    memoryCandidate.available_decision_states = ["accept", "correct", "reject", "defer"];
    data.founderMemoryReview.items = [memoryCandidate];
    view.rerender(<NorthStarControlCenter activePath="/workspace/knowledge" data={data} />);
    expect(screen.getByRole("button", { name: "Add local note" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Record correct receipt" })).toBeDisabled();

    data.routeStates["/trust"].state = "backend_owned";
    data.routeStates["/settings"].state = "backend_owned";
    Object.assign(data.trustAuthorityMatrix, { backend_owned: true, status: "backend_owned" });
    data.settingsStatus.authority_lease_state.backend_owned = true;
    view.rerender(<NorthStarControlCenter activePath="/workspace/activity-trust" data={data} />);
    expect(screen.getByRole("button", { name: "Revoke lease" })).toBeDisabled();
    expect(apiMocks.submitActionDecision).not.toHaveBeenCalled();
    expect(apiMocks.recordMemoryReviewDecision).not.toHaveBeenCalled();
    expect(apiMocks.recordManualMemoryCandidate).not.toHaveBeenCalled();
    expect(apiMocks.revokeAuthorityLease).not.toHaveBeenCalled();
  });

  it("records a Memory Review correction receipt and reloads the queue", async () => {
    const data = cloneData();
    markLiveBackend(data, "/memory");
    const candidate = structuredClone(data.founderToday.memory_review_queue[0]);
    candidate.available_decision_states = ["accept", "correct", "reject", "defer"];
    data.founderMemoryReview.items = [candidate];
    apiMocks.recordMemoryReviewDecision.mockResolvedValue({
      receipt_ref: "receipt:memory-review:test",
      replayed: false,
      safe_summary_ref: "safe-summary-ref:memory:test",
    });
    apiMocks.fetchFounderMemoryReview.mockResolvedValue(data.founderMemoryReview);

    render(
      <BackendTruthMutationBindingProvider binding={mutationBinding}>
        <NorthStarControlCenter
          activePath="/workspace/knowledge"
          data={data}
        />
      </BackendTruthMutationBindingProvider>,
    );
    fireEvent.change(screen.getByLabelText("Correction"), { target: { value: "Corrected bounded safe summary." } });
    fireEvent.click(screen.getByRole("button", { name: "Record correct receipt" }));

    await waitFor(() => expect(apiMocks.recordMemoryReviewDecision).toHaveBeenCalledTimes(1));
    expect(apiMocks.recordMemoryReviewDecision.mock.calls[0][2]).toMatchObject({
      corrected_safe_summary: "Corrected bounded safe summary.",
      reviewer_ref: "actor-ref:northstar-memory-review",
    });
    expect(apiMocks.recordMemoryReviewDecision.mock.calls[0][3]).toEqual(
      mutationBinding,
    );
    expect(await screen.findByText(/receipt:memory-review:test/)).toBeVisible();
    expect(apiMocks.fetchFounderMemoryReview).toHaveBeenCalledTimes(1);
    expect(apiMocks.fetchFounderMemoryReview).toHaveBeenCalledWith(
      mutationBinding,
    );
  });

  it("keeps Memory Review decisions read-only when a candidate claims authority", () => {
    const data = cloneData();
    markLiveBackend(data, "/memory");
    const candidate = structuredClone(data.founderToday.memory_review_queue[0]);
    candidate.available_decision_states = ["accept", "correct", "reject", "defer"];
    candidate.context_injection_authorized = true;
    data.founderMemoryReview.items = [candidate];

    render(
      <BackendTruthMutationBindingProvider binding={mutationBinding}>
        <NorthStarControlCenter
          activePath="/workspace/knowledge"
          data={data}
        />
      </BackendTruthMutationBindingProvider>,
    );

    expect(screen.getByRole("button", { name: "Record correct receipt" })).toBeDisabled();
    expect(apiMocks.recordMemoryReviewDecision).not.toHaveBeenCalled();
  });

  it("fails closed when a Memory Review candidate has malformed decision bindings", () => {
    const data = cloneData();
    markLiveBackend(data, "/memory");
    const candidate = structuredClone(data.founderToday.memory_review_queue[0]);
    candidate.available_decision_states = ["accept", "correct", "reject", "defer"];
    candidate.decision_contract_ref = "contract-ref:memory-review-decision:unexpected";
    candidate.decision_receipt_refs = [];
    data.founderMemoryReview.items = [candidate];

    render(<NorthStarControlCenter activePath="/workspace/knowledge" data={data} />);

    expect(screen.getByRole("button", { name: "Record correct receipt" })).toBeDisabled();
    expect(apiMocks.recordMemoryReviewDecision).not.toHaveBeenCalled();
  });

  it("records a manual note as a review candidate without claiming a memory write", async () => {
    const data = cloneData();
    markLiveBackend(data, "/memory");
    apiMocks.recordManualMemoryCandidate.mockResolvedValue({
      receipt_ref: "receipt:manual-memory:test",
      review_candidate_created: true,
      reviewed_recall_record_created: false,
      memory_write_performed: false,
    });
    apiMocks.fetchFounderMemoryReview.mockResolvedValue(data.founderMemoryReview);

    render(
      <BackendTruthMutationBindingProvider binding={mutationBinding}>
        <NorthStarControlCenter
          activePath="/workspace/knowledge"
          data={data}
        />
      </BackendTruthMutationBindingProvider>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Add local note" }));
    fireEvent.change(screen.getByLabelText("Note title"), { target: { value: "Founder preference" } });
    fireEvent.change(screen.getByLabelText("Bounded safe summary"), { target: { value: "Review this bounded operator note." } });
    fireEvent.click(screen.getByRole("button", { name: "Record review candidate" }));

    await waitFor(() =>
      expect(apiMocks.recordManualMemoryCandidate).toHaveBeenCalledWith(
        expect.objectContaining({
          candidate_kind: "operator_note",
          title: "Founder preference",
          safe_summary: "Review this bounded operator note.",
        }),
        mutationBinding,
      ),
    );
    expect(await screen.findByText(/No recall record or memory write was created/)).toBeVisible();
    expect(apiMocks.fetchFounderMemoryReview).toHaveBeenCalledWith(
      mutationBinding,
    );
  });

  it("keeps an Action Inbox receipt visible when queue refresh fails", async () => {
    const data = cloneData();
    markLiveBackend(data, "/actions");
    const item = data.founderActionsInbox.items[0];
    Object.assign(item, {
      action_review_actions: ["reject"],
      approval_envelope: { ...item.approval_envelope, source: "python_core_action_inbox_read_model", backend_owned: true },
      receipt_visibility: { ...item.receipt_visibility, source: "python_core_action_inbox_read_model", backend_owned: true },
    });
    attachExactDecisionLane(data, item.item_ref);
    apiMocks.submitActionDecision.mockResolvedValue({ decision: "reject", receipt_ref: "receipt:refresh-failure:test", replayed: false, action_executed: false });
    apiMocks.fetchFounderActionsInbox.mockRejectedValue(new Error("temporary refresh failure"));

    render(<NorthStarControlCenter activePath="/workspace/decisions" data={data} />);
    fireEvent.click(screen.getByRole("button", { name: "Record reject" }));

    expect((await screen.findAllByText(/receipt:refresh-failure:test.*Refresh pending: temporary refresh failure/)).length).toBeGreaterThan(0);
  });

  it("renders overlooked backend read models while keeping writes disabled", () => {
    const data = cloneData();
    data.connection.state = "online";
    data.connection.usingMockData = false;
    data.routeStates["/crm"].state = "backend_owned";
    data.routeStates["/coding"].state = "backend_owned";
    Object.assign(data.crmLocalCommandCenter, { backend_owned: true, read_only: true, safe_refs_only: true });
    const { rerender } = render(<NorthStarControlCenter activePath="/workspace/crm" data={data} />);
    expect(screen.getByText(/Backend-owned CRM read model/)).toBeVisible();
    expect(screen.getByRole("button", { name: "Call" })).toBeDisabled();

    rerender(<NorthStarControlCenter activePath="/workspace/onboarding" data={data} />);
    fireEvent.click(screen.getByRole("button", { name: "Continue to review" }));
    expect(screen.getByRole("heading", { name: "Review your local setup" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Finish setup unavailable" })).toBeDisabled();

    rerender(<NorthStarControlCenter activePath="/workspace/studio" data={data} />);
    fireEvent.click(screen.getByRole("button", { name: /CodePropose, review, validate/ }));
    expect(screen.getByText(data.codingSession.project_model.project_label)).toBeVisible();
    expect(screen.getByText(/File writes blocked/)).toBeVisible();
  });

  it("does not label nested CRM or Studio data backend-owned when route truth is fallback", () => {
    const data = cloneData();
    Object.assign(data.crmLocalCommandCenter, { backend_owned: true, read_only: true, safe_refs_only: true });
    Object.assign(data.codingSession, { backend_owned: true, safe_refs_only: true });
    const view = render(<NorthStarControlCenter activePath="/workspace/crm" data={data} />);
    expect(screen.getByText(/Non-authoritative CRM fallback/)).toBeVisible();

    view.rerender(<NorthStarControlCenter activePath="/workspace/studio" data={data} />);
    fireEvent.click(screen.getByRole("button", { name: /CodePropose, review, validate/ }));
    expect(screen.getByText("Preview fallback")).toBeVisible();
  });

  it("does not show stale fixture detail after communication or news searches have no matches", () => {
    const data = cloneData();
    const view = render(<NorthStarControlCenter activePath="/workspace/communications" data={data} />);
    fireEvent.change(screen.getByPlaceholderText("Search preview communications"), { target: { value: "no-such-fixture" } });
    expect(screen.getByRole("heading", { name: "No fixture matches" })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "Customer kickoff timing" })).not.toBeInTheDocument();

    view.rerender(<NorthStarControlCenter activePath="/workspace/news" data={data} />);
    fireEvent.change(screen.getByPlaceholderText("Search preview news and briefings"), { target: { value: "no-such-fixture" } });
    expect(screen.getByText("No preview article matches this search.")).toBeVisible();
    expect(screen.getByText("No fixture is selected.")).toBeVisible();
    expect(screen.queryByText("Preview freshness")).not.toBeInTheDocument();
  });

  it("requires explicit confirmation before revoking an exact active authority lease", async () => {
    const data = cloneData();
    markLiveBackend(data, "/trust", "/settings");
    Object.assign(data.trustAuthorityMatrix, { backend_owned: true, status: "backend_owned" });
    data.settingsStatus.authority_lease_state.backend_owned = true;
    const elevatedLease = {
      ...data.settingsStatus.authority_lease_state.active_leases[0],
      lease_ref: "authority-lease-ref:test-elevated-first",
      mode: "approved_safe_local_work_session" as const,
      status: "active" as const,
    };
    const selectedLease = {
      ...elevatedLease,
      lease_ref: "authority-lease-ref:test-elevated-selected",
    };
    data.settingsStatus.authority_lease_state.active_leases = [elevatedLease, selectedLease];
    apiMocks.revokeAuthorityLease.mockResolvedValue({
      receipt: { receipt_ref: "receipt:authority-revoke:test" },
    });
    apiMocks.fetchControlCenterSettingsStatus.mockResolvedValue({
      ...data.settingsStatus,
      authority_lease_state: {
        ...data.settingsStatus.authority_lease_state,
        active_leases: [],
      },
    });

    render(
      <BackendTruthMutationBindingProvider binding={mutationBinding}>
        <NorthStarControlCenter
          activePath="/workspace/activity-trust"
          data={data}
        />
      </BackendTruthMutationBindingProvider>,
    );
    fireEvent.change(screen.getByLabelText("Select exact active lease"), { target: { value: selectedLease.lease_ref } });
    fireEvent.click(screen.getByRole("button", { name: "Revoke lease" }));
    expect(apiMocks.revokeAuthorityLease).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Confirm revoke" }));

    await waitFor(() => expect(apiMocks.revokeAuthorityLease).toHaveBeenCalledWith({
      lease_ref: "authority-lease-ref:test-elevated-selected",
      decision_reason_ref: "reason-ref:northstar-authority-revoke",
      safe_summary: "Control Center revoked the exact active authority lease after operator confirmation.",
    }, mutationBinding));
    expect(await screen.findByText(/receipt:authority-revoke:test/)).toBeVisible();
  });

  it("does not revoke when the confirmed lease disappears before the second click", () => {
    const data = cloneData();
    markLiveBackend(data, "/trust", "/settings");
    Object.assign(data.trustAuthorityMatrix, { backend_owned: true, status: "backend_owned" });
    data.settingsStatus.authority_lease_state.backend_owned = true;
    const lease = {
      ...data.settingsStatus.authority_lease_state.active_leases[0],
      lease_ref: "authority-lease-ref:test-disappears",
      mode: "approved_safe_local_work_session" as const,
      status: "active" as const,
    };
    data.settingsStatus.authority_lease_state.active_leases = [lease];
    const view = render(<NorthStarControlCenter activePath="/workspace/activity-trust" data={data} />);
    fireEvent.click(screen.getByRole("button", { name: "Revoke lease" }));

    const refreshed = structuredClone(data);
    refreshed.settingsStatus.authority_lease_state.active_leases = [];
    view.rerender(<NorthStarControlCenter activePath="/workspace/activity-trust" data={refreshed} />);

    expect(screen.queryByRole("button", { name: "Confirm revoke" })).not.toBeInTheDocument();
    expect(apiMocks.revokeAuthorityLease).not.toHaveBeenCalled();
  });
});
