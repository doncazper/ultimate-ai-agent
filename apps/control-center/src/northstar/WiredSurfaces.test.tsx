import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mockControlCenterData } from "../mocks/controlCenterData";
import { NorthStarControlCenter } from "./NorthStarControlCenter";

const apiMocks = vi.hoisted(() => ({
  createWorkBoardCard: vi.fn(),
  createWorkBoardTask: vi.fn(),
  fetchWorkBoard: vi.fn(),
  submitActionDecision: vi.fn(),
  fetchFounderActionsInbox: vi.fn(),
  recordMemoryReviewDecision: vi.fn(),
  fetchFounderMemoryReview: vi.fn(),
  recordManualMemoryCandidate: vi.fn(),
  revokeAuthorityLease: vi.fn(),
  fetchControlCenterSettingsStatus: vi.fn(),
}));

vi.mock("../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api/client")>()),
  ...apiMocks,
}));

function cloneData() {
  return structuredClone(mockControlCenterData);
}

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  cleanup();
  window.history.replaceState({}, "", "/");
});

describe("North Star backend wiring", () => {
  it("records Work Board card and task receipts only when the exact backend lanes are eligible", async () => {
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
    apiMocks.createWorkBoardCard.mockResolvedValue({
      receipt_ref: "receipt:work-board-card:test",
      card_ref: "work-board-card:test",
    });
    apiMocks.createWorkBoardTask.mockResolvedValue({
      receipt_ref: "receipt:work-board-task:test",
      local_task_ref: "local-task:test",
    });
    apiMocks.fetchWorkBoard.mockResolvedValue(data.workBoard);

    render(<NorthStarControlCenter activePath="/workspace/work-board" data={data} />);

    fireEvent.click(screen.getAllByRole("button", { name: "Create card" })[0]);
    fireEvent.change(screen.getByLabelText("Card title"), { target: { value: "Exact local card" } });
    fireEvent.change(screen.getByLabelText("Safe summary"), { target: { value: "Bounded safe summary for the exact local card." } });
    fireEvent.click(screen.getByRole("button", { name: "Record exact card" }));

    await waitFor(() => expect(apiMocks.createWorkBoardCard).toHaveBeenCalledTimes(1));
    expect(apiMocks.createWorkBoardCard.mock.calls[0][0]).toMatchObject({
      title: "Exact local card",
      safe_summary: "Bounded safe summary for the exact local card.",
    });
    expect(await screen.findByText(/Card recorded · receipt:work-board-card:test/)).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "Create local task record" }));
    await waitFor(() => expect(apiMocks.createWorkBoardTask).toHaveBeenCalledTimes(1));
    expect(apiMocks.createWorkBoardTask.mock.calls[0][0]).toMatchObject({
      card_ref: data.workBoard.cards[0].card_ref,
    });
    expect(await screen.findByText(/Local task record created · receipt:work-board-task:test/)).toBeVisible();
  });

  it("records an Action Inbox decision receipt and refreshes the backend read model", async () => {
    const data = cloneData();
    data.routeStates["/actions"].state = "backend_owned";
    const item = data.founderActionsInbox.items[0];
    Object.assign(item, {
      action_group_id: "ready_for_decision",
      action_group_label: "Ready for decision",
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
    apiMocks.submitActionDecision.mockResolvedValue({
      decision: "reject",
      receipt_ref: "receipt:action-decision:test",
      safe_summary: "Exact rejection receipt recorded.",
      replayed: false,
      action_executed: false,
    });
    apiMocks.fetchFounderActionsInbox.mockResolvedValue(data.founderActionsInbox);

    render(<NorthStarControlCenter activePath="/workspace/decisions" data={data} />);
    fireEvent.click(screen.getByRole("button", { name: "Record reject" }));

    await waitFor(() => expect(apiMocks.submitActionDecision).toHaveBeenCalledWith(
      item.item_ref,
      "reject",
      expect.objectContaining({ decision_reason_ref: "decision-reason-ref:northstar-action:reject" }),
    ));
    expect((await screen.findAllByText(/receipt:action-decision:test/)).length).toBeGreaterThan(0);
    expect(apiMocks.fetchFounderActionsInbox).toHaveBeenCalledTimes(1);
  });

  it("records a Memory Review correction receipt and reloads the queue", async () => {
    const data = cloneData();
    data.routeStates["/memory"].state = "backend_owned";
    const candidate = structuredClone(data.founderToday.memory_review_queue[0]);
    candidate.available_decision_states = ["accept", "correct", "reject", "defer"];
    data.founderMemoryReview.items = [candidate];
    apiMocks.recordMemoryReviewDecision.mockResolvedValue({
      receipt_ref: "receipt:memory-review:test",
      replayed: false,
      safe_summary_ref: "safe-summary-ref:memory:test",
    });
    apiMocks.fetchFounderMemoryReview.mockResolvedValue(data.founderMemoryReview);

    render(<NorthStarControlCenter activePath="/workspace/knowledge" data={data} />);
    fireEvent.change(screen.getByLabelText("Correction"), { target: { value: "Corrected bounded safe summary." } });
    fireEvent.click(screen.getByRole("button", { name: "Record correct receipt" }));

    await waitFor(() => expect(apiMocks.recordMemoryReviewDecision).toHaveBeenCalledTimes(1));
    expect(apiMocks.recordMemoryReviewDecision.mock.calls[0][2]).toMatchObject({
      corrected_safe_summary: "Corrected bounded safe summary.",
      reviewer_ref: "actor-ref:northstar-memory-review",
    });
    expect(await screen.findByText(/receipt:memory-review:test/)).toBeVisible();
    expect(apiMocks.fetchFounderMemoryReview).toHaveBeenCalledTimes(1);
  });

  it("records a manual note as a review candidate without claiming a memory write", async () => {
    const data = cloneData();
    data.routeStates["/memory"].state = "backend_owned";
    apiMocks.recordManualMemoryCandidate.mockResolvedValue({
      receipt_ref: "receipt:manual-memory:test",
      review_candidate_created: true,
      reviewed_recall_record_created: false,
      memory_write_performed: false,
    });
    apiMocks.fetchFounderMemoryReview.mockResolvedValue(data.founderMemoryReview);

    render(<NorthStarControlCenter activePath="/workspace/knowledge" data={data} />);
    fireEvent.click(screen.getByRole("button", { name: "Add local note" }));
    fireEvent.change(screen.getByLabelText("Note title"), { target: { value: "Founder preference" } });
    fireEvent.change(screen.getByLabelText("Bounded safe summary"), { target: { value: "Review this bounded operator note." } });
    fireEvent.click(screen.getByRole("button", { name: "Record review candidate" }));

    await waitFor(() => expect(apiMocks.recordManualMemoryCandidate).toHaveBeenCalledWith(expect.objectContaining({
      candidate_kind: "operator_note",
      title: "Founder preference",
      safe_summary: "Review this bounded operator note.",
    })));
    expect(await screen.findByText(/No recall record or memory write was created/)).toBeVisible();
  });

  it("keeps an Action Inbox receipt visible when queue refresh fails", async () => {
    const data = cloneData();
    data.routeStates["/actions"].state = "backend_owned";
    const item = data.founderActionsInbox.items[0];
    Object.assign(item, {
      action_group_id: "ready_for_decision",
      action_review_actions: ["reject"],
      approval_envelope: { ...item.approval_envelope, source: "python_core_action_inbox_read_model", backend_owned: true },
      receipt_visibility: { ...item.receipt_visibility, source: "python_core_action_inbox_read_model", backend_owned: true },
    });
    apiMocks.submitActionDecision.mockResolvedValue({ decision: "reject", receipt_ref: "receipt:refresh-failure:test", replayed: false, action_executed: false });
    apiMocks.fetchFounderActionsInbox.mockRejectedValue(new Error("temporary refresh failure"));

    render(<NorthStarControlCenter activePath="/workspace/decisions" data={data} />);
    fireEvent.click(screen.getByRole("button", { name: "Record reject" }));

    expect((await screen.findAllByText(/receipt:refresh-failure:test.*Refresh pending: temporary refresh failure/)).length).toBeGreaterThan(0);
  });

  it("renders overlooked backend read models while keeping writes disabled", () => {
    const data = cloneData();
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

  it("requires explicit confirmation before revoking an exact active authority lease", async () => {
    const data = cloneData();
    data.routeStates["/trust"].state = "backend_owned";
    data.routeStates["/settings"].state = "backend_owned";
    Object.assign(data.trustAuthorityMatrix, { backend_owned: true, status: "backend_owned" });
    data.settingsStatus.authority_lease_state.backend_owned = true;
    const elevatedLease = {
      ...data.settingsStatus.authority_lease_state.active_leases[0],
      lease_ref: "authority-lease-ref:test-elevated",
      mode: "approved_safe_local_work_session" as const,
      status: "active" as const,
    };
    data.settingsStatus.authority_lease_state.active_leases = [elevatedLease];
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

    render(<NorthStarControlCenter activePath="/workspace/activity-trust" data={data} />);
    fireEvent.click(screen.getByRole("button", { name: "Revoke lease" }));
    expect(apiMocks.revokeAuthorityLease).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Confirm revoke" }));

    await waitFor(() => expect(apiMocks.revokeAuthorityLease).toHaveBeenCalledWith({
      lease_ref: "authority-lease-ref:test-elevated",
      decision_reason_ref: "reason-ref:northstar-authority-revoke",
      safe_summary: "Control Center revoked the exact active authority lease after operator confirmation.",
    }));
    expect(await screen.findByText(/receipt:authority-revoke:test/)).toBeVisible();
  });
});
