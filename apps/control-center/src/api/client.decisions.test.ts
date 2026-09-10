import { afterEach, describe, expect, it, vi } from "vitest";

import { loadNorthStarDecisionsData } from "./client";
import { API_ENDPOINTS } from "./endpoints";
import { mockControlCenterData } from "../mocks/controlCenterData";

const binding = {
  snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"1".repeat(64)}`,
  backendRevisionRef: `commit-ref:git:${"2".repeat(40)}`,
  backendInstanceRef:
    "backend-instance-ref:control-center:33333333333333333333333333333333",
};

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
