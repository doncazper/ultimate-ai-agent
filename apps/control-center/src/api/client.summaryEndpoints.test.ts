import { afterEach, describe, expect, it, vi } from "vitest";
import {
  computeRuntimeSkillMarketplaceSnapshotHashRef,
  loadControlCenterData,
  loadRuntimeSkillMarketplacePosture,
} from "./client";
import { API_ENDPOINTS } from "./endpoints";
import type { RuntimeSkillMarketplacePostureReadModel } from "./types";
import { mockControlCenterData } from "../mocks/controlCenterData";
import studioSkillMarketplaceVisualFixture from "../../tests/visual/fixtures/studio-skill-marketplace-posture.json";

const EMPTY_SKILL_MARKETPLACE_SOURCES = [
  {
    source_ref: "source-ref:skill-marketplace:clawhub",
    source_kind: "clawhub" as const,
    display_label: "ClawHub",
    captured_at: "2026-07-13T00:00:00Z",
    source_version_ref: "source-version-ref:clawhub:test",
    record_count: 0,
    rank_signal: "weekly_trending" as const,
    score_signal: "stars" as const,
    live_fetch_performed: false as const,
    raw_payload_persisted: false as const,
  },
  {
    source_ref: "source-ref:skill-marketplace:hermes",
    source_kind: "hermes" as const,
    display_label: "Hermes",
    captured_at: "2026-07-13T00:00:00Z",
    source_version_ref: "source-version-ref:hermes:test",
    record_count: 0,
    rank_signal: "not_provided" as const,
    score_signal: "not_provided" as const,
    live_fetch_performed: false as const,
    raw_payload_persisted: false as const,
  },
];

const CURRENT_SKILL_MARKETPLACE_FRESHNESS = {
  catalog_snapshot_ref: "skill-marketplace-catalog-snapshot-ref:test",
  status: "current" as const,
  display_status: "available" as const,
  checked_at: "2026-07-14T00:00:00Z",
  expires_at: "2026-07-20T00:00:00Z",
  freshness_policy_ref:
    "freshness-policy-ref:skill-marketplace-catalog:seven-days",
  reason_refs: ["reason-ref:skill-marketplace-catalog:freshness-current"],
  stale: false,
  catalog_displayable: true,
  unknown_degrades_to_unavailable: true as const,
};

async function validSkillMarketplacePosture(): Promise<RuntimeSkillMarketplacePostureReadModel> {
  const posture: RuntimeSkillMarketplacePostureReadModel = {
    ...mockControlCenterData.runtimeSkillMarketplacePosture,
    snapshot_hash_ref: `snapshot-hash-ref:skill-marketplace-posture:${"0".repeat(64)}`,
    authority_state_decision_ref:
      "authority-policy-decision-ref:test-runtime-skill-marketplace-posture",
    authority_state_decision_outcome: "allow",
    authority_state_status: "implemented_authority_bound_read_model",
    authority_state_operator_message:
      "Allowed by exact read-only authority for test metadata inspection.",
    authority_state_reason_refs: [
      "reason-ref:authority:active-lease-grants-domain-capability",
    ],
    catalog_freshness: { ...CURRENT_SKILL_MARKETPLACE_FRESHNESS },
    catalog: {
      schema_version: "runtime_skill_marketplace_catalog_snapshot.v1" as const,
      snapshot_ref: "skill-marketplace-catalog-snapshot-ref:test",
      captured_at: "2026-07-13T00:00:00Z",
      sources: EMPTY_SKILL_MARKETPLACE_SOURCES.map((source) => ({ ...source })),
      entries: [],
      entry_count: 0,
      default_page_size: 25 as const,
      pagination_supported: true as const,
      metadata_only: true as const,
      live_marketplace_fetch_performed: false as const,
      raw_marketplace_payload_persisted: false as const,
    },
  };
  posture.snapshot_hash_ref =
    await computeRuntimeSkillMarketplaceSnapshotHashRef(posture);
  return posture;
}

describe("loadControlCenterData summary endpoint wiring", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads Studio skill metadata through one focused backend read", async () => {
    const posture = await validSkillMarketplacePosture();
    stubControlCenterFetch({
      [API_ENDPOINTS.runtimeSkillMarketplacePosture]: posture,
    });

    const result = await loadRuntimeSkillMarketplacePosture();

    expect(result).toEqual({
      posture,
      backendValidated: true,
      catalogDisplayable: true,
    });
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining(API_ENDPOINTS.runtimeSkillMarketplacePosture),
      expect.any(Object),
    );
  });

  it("loads the backend-owned social publishing proposal as a read-only Studio surface", async () => {
    stubControlCenterFetch(baseRouteData());

    const data = await loadControlCenterData();

    expect(data.socialPublishingProposal).toEqual(
      mockControlCenterData.socialPublishingProposal,
    );
    expect(data.socialPublishingProposal.dry_run_only).toBe(true);
    expect(data.socialPublishingProposal.publishing_enabled).toBe(false);
    expect(data.socialPublishingProposal.external_write_enabled).toBe(false);
    expect(data.routeStates["/studio"].state).toBe("backend_owned");
  });

  it("fails closed when the social publishing proposal claims write authority", async () => {
    const routeData = baseRouteData();
    const unsafeProposal = structuredClone(
      mockControlCenterData.socialPublishingProposal,
    ) as unknown as Record<string, unknown>;
    unsafeProposal.publishing_enabled = true;
    routeData[API_ENDPOINTS.socialPublishingProposal] = unsafeProposal;
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.socialPublishingProposal).toEqual(
      mockControlCenterData.socialPublishingProposal,
    );
    expect(data.routeStates["/studio"].state).toBe("degraded");
    expect(data.routeStates["/studio"].warningRefs).toContain(
      "SOCIAL_PUBLISHING_PROPOSAL_MOCK_FALLBACK",
    );
  });

  it("fails closed when the social publishing platform inventory is duplicated", async () => {
    const routeData = baseRouteData();
    const unsafeProposal = structuredClone(
      mockControlCenterData.socialPublishingProposal,
    );
    unsafeProposal.fixture.variants[2].platform = "instagram";
    routeData[API_ENDPOINTS.socialPublishingProposal] = unsafeProposal;
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.routeStates["/studio"].state).toBe("degraded");
    expect(data.socialPublishingProposal).toEqual(
      mockControlCenterData.socialPublishingProposal,
    );
  });

  it("accepts the backend-generated Studio visual fixture", async () => {
    stubControlCenterFetch({
      [API_ENDPOINTS.runtimeSkillMarketplacePosture]:
        studioSkillMarketplaceVisualFixture.data,
    });

    const result = await loadRuntimeSkillMarketplacePosture();

    expect(result.backendValidated).toBe(true);
    expect(result.catalogDisplayable).toBe(true);
  });

  it("fails closed when the focused Studio read contains duplicate source refs", async () => {
    const posture = await validSkillMarketplacePosture();
    posture.catalog!.sources[1].source_ref =
      posture.catalog!.sources[0].source_ref;
    stubControlCenterFetch({
      [API_ENDPOINTS.runtimeSkillMarketplacePosture]: posture,
    });

    const result = await loadRuntimeSkillMarketplacePosture();

    expect(result.backendValidated).toBe(false);
    expect(result.catalogDisplayable).toBe(false);
    expect(result.posture).toEqual(
      mockControlCenterData.runtimeSkillMarketplacePosture,
    );
  });

  it.each([
    ["unsafe summary", (posture: RuntimeSkillMarketplacePostureReadModel) => {
      posture.safe_summary = "Secret: token-like material must not render.";
    }],
    ["unsafe source label", (posture: RuntimeSkillMarketplacePostureReadModel) => {
      posture.catalog!.sources[0].display_label = "/Users/private/source";
    }],
    ["forged count", (posture: RuntimeSkillMarketplacePostureReadModel) => {
      posture.catalog!.sources[0].record_count = Number.NaN;
    }],
    ["forged freshness", (posture: RuntimeSkillMarketplacePostureReadModel) => {
      posture.catalog_freshness.display_status = "available_stale";
    }],
  ])("fails closed for %s in a Studio payload", async (_label, mutate) => {
    const posture = await validSkillMarketplacePosture();
    mutate(posture);
    stubControlCenterFetch({
      [API_ENDPOINTS.runtimeSkillMarketplacePosture]: posture,
    });

    const result = await loadRuntimeSkillMarketplacePosture();

    expect(result.backendValidated).toBe(false);
    expect(result.catalogDisplayable).toBe(false);
    expect(result.posture).toEqual(
      mockControlCenterData.runtimeSkillMarketplacePosture,
    );
  });

  it("rejects a correct-length snapshot digest that does not bind the payload", async () => {
    const posture = await validSkillMarketplacePosture();
    posture.snapshot_hash_ref =
      `snapshot-hash-ref:skill-marketplace-posture:${"f".repeat(64)}`;
    stubControlCenterFetch({
      [API_ENDPOINTS.runtimeSkillMarketplacePosture]: posture,
    });

    const result = await loadRuntimeSkillMarketplacePosture();

    expect(result.backendValidated).toBe(false);
    expect(result.catalogDisplayable).toBe(false);
  });

  it.each(["ask", "deny", "degrade_to_draft"] as const)(
    "preserves a validated %s authority posture while withholding catalog rows",
    async (outcome) => {
      const posture = await validSkillMarketplacePosture();
      posture.authority_state_decision_outcome = outcome;
      posture.authority_state_status = `authority_${outcome}`;
      posture.authority_state_operator_message =
        "Exact read-only authority is not currently available.";
      posture.catalog_freshness.display_status = "unavailable_authority";
      posture.catalog_freshness.catalog_displayable = false;
      posture.snapshot_hash_ref =
        await computeRuntimeSkillMarketplaceSnapshotHashRef(posture);
      stubControlCenterFetch({
        [API_ENDPOINTS.runtimeSkillMarketplacePosture]: posture,
      });

      const result = await loadRuntimeSkillMarketplacePosture();

      expect(result.backendValidated).toBe(true);
      expect(result.catalogDisplayable).toBe(false);
      expect(result.posture).toEqual(posture);
      expect(result.posture.catalog?.entry_count).toBe(0);
      expect(result.posture.catalog?.entries).toEqual([]);
    },
  );

  it("rejects non-displayable catalog rows even when the digest matches", async () => {
    const posture = structuredClone(
      studioSkillMarketplaceVisualFixture.data,
    ) as RuntimeSkillMarketplacePostureReadModel;
    posture.authority_state_decision_outcome = "deny";
    posture.authority_state_status = "authority_deny";
    posture.authority_state_operator_message =
      "Exact read-only authority is not currently available.";
    posture.catalog_freshness.display_status = "unavailable_authority";
    posture.catalog_freshness.catalog_displayable = false;
    posture.snapshot_hash_ref =
      await computeRuntimeSkillMarketplaceSnapshotHashRef(posture);
    stubControlCenterFetch({
      [API_ENDPOINTS.runtimeSkillMarketplacePosture]: posture,
    });

    const result = await loadRuntimeSkillMarketplacePosture();

    expect(result.backendValidated).toBe(false);
    expect(result.catalogDisplayable).toBe(false);
  });

  it("rejects a hash-mismatched Studio payload in the aggregate loader", async () => {
    const posture = await validSkillMarketplacePosture();
    posture.safe_summary = "Tampered but structurally safe summary.";
    stubControlCenterFetch({
      ...baseRouteData(),
      [API_ENDPOINTS.runtimeSkillMarketplacePosture]: posture,
    });

    const data = await loadControlCenterData();

    expect(data.runtimeSkillMarketplacePosture).toEqual(
      mockControlCenterData.runtimeSkillMarketplacePosture,
    );
  });

  it("prefers dedicated Control Center summaries over embedded dashboard summaries", async () => {
    const directApprovalSummary = {
      ...mockControlCenterData.dashboard.approval_summary,
      pending_count: 7,
      summary: "Dedicated approval summary route.",
    };
    const directRuntimeSummary = {
      ...mockControlCenterData.dashboard.runtime_readiness_summary,
      status: "dedicated_runtime_summary",
    };
    const directFoundationSummary = {
      ...mockControlCenterData.dashboard.foundation_gate_summary,
      status: "dedicated_foundation_summary",
    };
    const directApprovalQueue = {
      ...mockControlCenterData.runAttachedApprovalQueue,
      source: "python_core_run_attached_approval_queue_read_model" as const,
      backend_owned: true,
      summary: {
        ...mockControlCenterData.runAttachedApprovalQueue.summary,
        queue_item_count: 4,
      },
    };

    stubControlCenterFetch({
      ...baseRouteData(),
      [API_ENDPOINTS.controlCenterDashboard]: {
        ...mockControlCenterData.dashboard,
        approval_summary: {
          ...mockControlCenterData.dashboard.approval_summary,
          pending_count: 1,
        },
        runtime_readiness_summary: {
          ...mockControlCenterData.dashboard.runtime_readiness_summary,
          status: "dashboard_runtime_summary",
        },
        foundation_gate_summary: {
          ...mockControlCenterData.dashboard.foundation_gate_summary,
          status: "dashboard_foundation_summary",
        },
      },
      [API_ENDPOINTS.approvalSummary]: directApprovalSummary,
      [API_ENDPOINTS.approvalQueue]: directApprovalQueue,
      [API_ENDPOINTS.runtimeReadinessSummary]: directRuntimeSummary,
      [API_ENDPOINTS.foundationGateSummary]: directFoundationSummary,
    });

    const data = await loadControlCenterData();

    expect(data.dashboard.approval_summary).toEqual(directApprovalSummary);
    expect(data.dashboard.runtime_readiness_summary).toEqual(
      directRuntimeSummary,
    );
    expect(data.dashboard.foundation_gate_summary).toEqual(
      directFoundationSummary,
    );
    expect(data.runAttachedApprovalQueue).toEqual(directApprovalQueue);
    expect(data.connection.state).toBe("online");
    expect(data.connection.usingMockData).toBe(false);
  });

  it("degrades without mock data when only dedicated summary routes fail", async () => {
    const routeData = baseRouteData();
    delete routeData[API_ENDPOINTS.approvalSummary];
    delete routeData[API_ENDPOINTS.runtimeReadinessSummary];
    delete routeData[API_ENDPOINTS.foundationGateSummary];
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.dashboard.approval_summary).toEqual(
      mockControlCenterData.dashboard.approval_summary,
    );
    expect(data.dashboard.runtime_readiness_summary).toEqual(
      mockControlCenterData.dashboard.runtime_readiness_summary,
    );
    expect(data.dashboard.foundation_gate_summary).toEqual(
      mockControlCenterData.dashboard.foundation_gate_summary,
    );
    expect(data.connection.state).toBe("degraded");
    expect(data.connection.usingMockData).toBe(false);
    expect(data.connection.warnings).toContain(
      "CONTROL_CENTER_SUMMARY_ENDPOINT_FALLBACK",
    );
    expect(data.connection.warnings).not.toContain("PARTIAL_MOCK_FALLBACK");
  });

  it("marks missing approval queue route as non-authoritative mock fallback", async () => {
    const routeData = baseRouteData();
    delete routeData[API_ENDPOINTS.approvalQueue];
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.runAttachedApprovalQueue.source).toBe(
      "mock_fallback_non_authoritative",
    );
    expect(data.runAttachedApprovalQueue.backend_owned).toBe(false);
    expect(data.connection.state).toBe("degraded");
    expect(data.connection.usingMockData).toBe(true);
    expect(data.connection.warnings).toContain("PARTIAL_MOCK_FALLBACK");
    expect(data.connection.warnings).toContain(
      "RUN_ATTACHED_APPROVAL_QUEUE_MOCK_FALLBACK",
    );
    expect(data.connection.safeMessage).toContain(
      "non-authoritative mock fallback",
    );
  });

  it("marks missing run observability route as non-authoritative mock fallback", async () => {
    const routeData = baseRouteData();
    delete routeData[API_ENDPOINTS.runObservability];
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.runObservability.source).toBe("mock_fallback_non_authoritative");
    expect(data.runObservability.backend_owned).toBe(false);
    expect(data.runObservability.ui_mutation_controls_enabled).toBe(false);
    expect(data.runObservability.connector_sends_enabled).toBe(false);
    expect(data.connection.state).toBe("degraded");
    expect(data.connection.usingMockData).toBe(true);
    expect(data.connection.warnings).toContain("PARTIAL_MOCK_FALLBACK");
    expect(data.connection.warnings).toContain(
      "RUN_OBSERVABILITY_MOCK_FALLBACK",
    );
  });

  it("marks missing Start Here route as non-authoritative mock fallback", async () => {
    const routeData = baseRouteData();
    delete routeData[API_ENDPOINTS.founderStartHereSummary];
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.founderStartHere.source).toBe(
      "mock_fallback_non_authoritative",
    );
    expect(data.founderStartHere.backend_owned).toBe(false);
    expect(data.founderStartHere.local_loop_status).toBe(
      "local_loop_unverified_mock_fallback",
    );
    expect(data.connection.state).toBe("degraded");
    expect(data.connection.usingMockData).toBe(true);
    expect(data.connection.warnings).toContain("PARTIAL_MOCK_FALLBACK");
    expect(data.connection.warnings).toContain("START_HERE_MOCK_FALLBACK");
    expect(data.connection.safeMessage).toContain(
      "non-authoritative mock fallback",
    );
  });

  it("marks missing Proof index route as non-authoritative mock fallback", async () => {
    const routeData = baseRouteData();
    delete routeData[API_ENDPOINTS.controlCenterProofIndex];
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.proofIndex.source).toBe("mock_fallback_non_authoritative");
    expect(data.proofIndex.backend_owned).toBe(false);
    expect(data.connection.state).toBe("degraded");
    expect(data.connection.usingMockData).toBe(true);
    expect(data.connection.warnings).toContain("PARTIAL_MOCK_FALLBACK");
    expect(data.connection.warnings).toContain("PROOF_INDEX_MOCK_FALLBACK");
  });

  it("marks missing Coding multi-agent review route as non-authoritative fallback", async () => {
    const routeData = baseRouteData();
    delete routeData[API_ENDPOINTS.controlCenterCodingMultiAgentReview];
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.codingMultiAgentReview.backend_owned).toBe(false);
    expect(data.routeStates["/coding"].state).toBe("mock_fallback");
    expect(data.routeStates["/coding"].backendRouteRefs).toContain(
      "GET /control-center/coding/multi-agent-review",
    );
    expect(data.routeStates["/coding"].warningRefs).toContain(
      "CODING_MULTI_AGENT_REVIEW_MOCK_FALLBACK",
    );
    expect(data.connection.state).toBe("degraded");
    expect(data.connection.usingMockData).toBe(true);
    expect(data.connection.warnings).toContain("PARTIAL_MOCK_FALLBACK");
    expect(data.connection.warnings).toContain(
      "CODING_MULTI_AGENT_REVIEW_MOCK_FALLBACK",
    );
  });

  it("marks unsafe Coding multi-agent review flags as non-authoritative fallback", async () => {
    const routeData = baseRouteData();
    const unsafeReview = JSON.parse(
      JSON.stringify(routeData[API_ENDPOINTS.controlCenterCodingMultiAgentReview]),
    );
    unsafeReview.provider_sdk_call_enabled = true;
    unsafeReview.agent_slots[0].raw_prompt_included = true;
    routeData[API_ENDPOINTS.controlCenterCodingMultiAgentReview] = unsafeReview;
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.codingMultiAgentReview.backend_owned).toBe(false);
    expect(data.codingMultiAgentReview.provider_sdk_call_enabled).toBe(false);
    expect(data.routeStates["/coding"].state).toBe("degraded");
    expect(data.routeStates["/coding"].warningRefs).toContain(
      "CODING_MULTI_AGENT_REVIEW_MOCK_FALLBACK",
    );
    expect(data.connection.warnings).toContain(
      "CODING_MULTI_AGENT_REVIEW_MOCK_FALLBACK",
    );
  });

  it("marks incomplete Coding multi-agent review shape as non-authoritative fallback", async () => {
    const routeData = baseRouteData();
    const incompleteReview = JSON.parse(
      JSON.stringify(routeData[API_ENDPOINTS.controlCenterCodingMultiAgentReview]),
    );
    incompleteReview.agent_slots = [incompleteReview.agent_slots[0]];
    incompleteReview.unblock_prompt_refs = [];
    routeData[API_ENDPOINTS.controlCenterCodingMultiAgentReview] =
      incompleteReview;
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.codingMultiAgentReview.backend_owned).toBe(false);
    expect(data.routeStates["/coding"].state).toBe("degraded");
    expect(data.routeStates["/coding"].warningRefs).toContain(
      "CODING_MULTI_AGENT_REVIEW_MOCK_FALLBACK",
    );
    expect(data.connection.safeMessage).toContain(
      "Coding backend read models were unavailable or unsafe",
    );
  });

  it("marks missing Work Board route as non-authoritative fallback", async () => {
    const routeData = baseRouteData();
    delete routeData[API_ENDPOINTS.controlCenterWorkBoard];
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.workBoard.backend_owned).toBe(false);
    expect(data.workBoard.non_authoritative_mock_fallback).toBe(true);
    expect(data.workBoard.board_mutation_enabled).toBe(false);
    expect(data.workBoard.durable_drag_drop_enabled).toBe(false);
    expect(data.routeStates["/work-board"].state).toBe("mock_fallback");
    expect(data.routeStates["/work-board"].backendRouteRefs).toContain(
      "GET /control-center/work-board",
    );
    expect(data.routeStates["/work-board"].warningRefs).toContain(
      "WORK_BOARD_MOCK_FALLBACK",
    );
    expect(data.connection.state).toBe("degraded");
    expect(data.connection.usingMockData).toBe(true);
    expect(data.connection.warnings).toContain("WORK_BOARD_MOCK_FALLBACK");
  });

  it("marks missing runtime capability discovery as non-authoritative fallback", async () => {
    const routeData = baseRouteData();
    delete routeData[API_ENDPOINTS.runtimeCapabilityDiscovery];
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.runtimeCapabilityDiscovery.live_discovery_performed).toBe(false);
    expect(data.runtimeCapabilityDiscovery.uaa_authorized_capability_count).toBe(0);
    expect(
      data.runtimeCapabilityDiscovery.toolset_posture.uaa_allowed_execution_count,
    ).toBe(0);
    expect(
      data.runtimeCapabilityDiscovery.toolset_posture.live_tool_invocation_enabled,
    ).toBe(false);
    expect(data.routeStates["/runtime"].state).toBe("mock_fallback");
    expect(data.routeStates["/runtime"].backendRouteRefs).toContain(
      "GET /api/runtime/capability-discovery",
    );
    expect(data.connection.state).toBe("degraded");
    expect(data.connection.usingMockData).toBe(true);
    expect(data.connection.warnings).toContain(
      "RUNTIME_CAPABILITY_DISCOVERY_MOCK_FALLBACK",
    );
  });

  it("marks missing runtime run events as non-authoritative fallback", async () => {
    const routeData = baseRouteData();
    delete routeData[API_ENDPOINTS.runtimeRunEvents];
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.runtimeRunEvents.create_run_route_enabled).toBe(false);
    expect(data.runtimeRunEvents.stop_run_route_enabled).toBe(false);
    expect(data.runtimeRunEvents.approval_resolution_route_enabled).toBe(false);
    expect(data.runtimeRunEvents.completed_run_count).toBe(0);
    expect(data.runtimeRunEvents.status).toBe("durable_local_replay");
    expect(data.runtimeRunEvents.durable_event_source).toBe(true);
    expect(data.runtimeRunEvents.cursor_replay_supported).toBe(true);
    expect(data.runtimeRunEvents.goal_lifecycle.goals).toEqual([]);
    expect(data.runtimeRunEvents.event_previews).toEqual([]);
    expect(data.runtimeRunEvents.authority_state_mapping_ref).toBe(
      "lane-ref:runtime-run-events-read-model",
    );
    expect(data.runtimeRunEvents.authority_state_decision_outcome).toBe("allow");
    expect(data.runtimeRunEvents.unsupported_adapter_refs).toContain(
      "adapter-ref:runtime-run-create:not-implemented",
    );
    expect(data.routeStates["/runtime"].state).toBe("mock_fallback");
    expect(data.routeStates["/runtime"].backendRouteRefs).toContain(
      "GET /api/runtime/run-events",
    );
    expect(data.routeStates[API_ENDPOINTS.runtimeRunEvents].state).toBe(
      "mock_fallback",
    );
    expect(
      data.routeStates[API_ENDPOINTS.runtimeRunEvents].backendRouteRefs,
    ).toContain("GET /api/runtime/run-events");
    expect(data.connection.state).toBe("degraded");
    expect(data.connection.usingMockData).toBe(true);
    expect(data.connection.warnings).toContain("RUNTIME_RUN_EVENTS_MOCK_FALLBACK");
  });

  it("marks invalid runtime run events as degraded durable state", async () => {
    const routeData = baseRouteData();
    routeData[API_ENDPOINTS.runtimeRunEvents] = {};
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.routeStates[API_ENDPOINTS.runtimeRunEvents].state).toBe(
      "degraded",
    );
    expect(data.routeStates[API_ENDPOINTS.runtimeRunEvents].warningRefs).toContain(
      "RUNTIME_RUN_EVENTS_MOCK_FALLBACK",
    );
  });

  it("marks validated runtime run events as backend-owned durable state", async () => {
    stubControlCenterFetch(baseRouteData());

    const data = await loadControlCenterData();

    expect(data.routeStates[API_ENDPOINTS.runtimeRunEvents].state).toBe(
      "backend_owned",
    );
    expect(data.routeStates[API_ENDPOINTS.runtimeRunEvents].warningRefs).toEqual(
      [],
    );
  });

  it("marks missing runtime approval bridge as non-authoritative fallback", async () => {
    const routeData = baseRouteData();
    delete routeData[API_ENDPOINTS.runtimeApprovalBridge];
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.runtimeApprovalBridge.approval_resolution_route_enabled).toBe(
      false,
    );
    expect(data.runtimeApprovalBridge.deny_resolution_route_enabled).toBe(false);
    expect(data.runtimeApprovalBridge.timeout_resolution_route_enabled).toBe(
      false,
    );
    expect(data.runtimeApprovalBridge.runtime_resolution_sent_count).toBe(0);
    expect(data.runtimeApprovalBridge.authority_state_mapping_ref).toBe(
      "lane-ref:runtime-approval-bridge-read-model",
    );
    expect(data.runtimeApprovalBridge.authority_state_decision_outcome).toBe(
      "allow",
    );
    expect(data.runtimeApprovalBridge.unsupported_adapter_refs).toContain(
      "adapter-ref:runtime-approval-resolution-send:not-implemented",
    );
    expect(
      data.runtimeApprovalBridge.action_inbox_projection
        .approval_controls_visible,
    ).toBe(false);
    expect(data.routeStates["/runtime"].state).toBe("mock_fallback");
    expect(data.routeStates["/runtime"].backendRouteRefs).toContain(
      "GET /api/runtime/approval-bridge",
    );
    expect(data.connection.state).toBe("degraded");
    expect(data.connection.usingMockData).toBe(true);
    expect(data.connection.warnings).toContain(
      "RUNTIME_APPROVAL_BRIDGE_MOCK_FALLBACK",
    );
  });

  it("marks missing runtime streaming progress as non-authoritative fallback", async () => {
    const routeData = baseRouteData();
    delete routeData[API_ENDPOINTS.runtimeStreamingProgress];
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.runtimeStreamingProgress.live_subscription_enabled).toBe(false);
    expect(data.runtimeStreamingProgress.sse_transport_enabled).toBe(false);
    expect(data.runtimeStreamingProgress.websocket_transport_enabled).toBe(false);
    expect(data.runtimeStreamingProgress.event_ingest_enabled).toBe(false);
    expect(data.runtimeStreamingProgress.authority_state_mapping_ref).toBe(
      "lane-ref:runtime-streaming-progress-read-model",
    );
    expect(data.runtimeStreamingProgress.authority_state_decision_outcome).toBe(
      "allow",
    );
    expect(data.runtimeStreamingProgress.unsupported_adapter_refs).toContain(
      "adapter-ref:runtime-streaming-progress-live-sse:not-implemented",
    );
    expect(data.runtimeStreamingProgress.stale_stream).toBe(true);
    expect(data.routeStates["/runtime"].state).toBe("mock_fallback");
    expect(data.routeStates["/runtime"].backendRouteRefs).toContain(
      "GET /api/runtime/streaming-progress",
    );
    expect(data.connection.state).toBe("degraded");
    expect(data.connection.usingMockData).toBe(true);
    expect(data.connection.warnings).toContain(
      "RUNTIME_STREAMING_PROGRESS_MOCK_FALLBACK",
    );
  });

  it("marks missing runtime profiles as non-authoritative fallback", async () => {
    const routeData = baseRouteData();
    delete routeData[API_ENDPOINTS.runtimeProfiles];
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.runtimeProfiles.profile_creation_enabled).toBe(false);
    expect(data.runtimeProfiles.profile_deletion_enabled).toBe(false);
    expect(data.runtimeProfiles.runtime_config_write_enabled).toBe(false);
    expect(data.runtimeProfiles.sensitive_material_copy_enabled).toBe(false);
    expect(data.runtimeProfiles.cross_profile_authority_bleed_allowed).toBe(false);
    expect(data.runtimeProfiles.authority_state_mapping_ref).toBe(
      "lane-ref:runtime-profile-isolation-read-model",
    );
    expect(data.runtimeProfiles.authority_state_decision_outcome).toBe("allow");
    expect(data.runtimeProfiles.unsupported_adapter_refs).toContain(
      "adapter-ref:runtime-profile-provider-call:not-implemented",
    );
    expect(data.routeStates["/runtime"].state).toBe("mock_fallback");
    expect(data.routeStates["/runtime"].backendRouteRefs).toContain(
      "GET /api/runtime/profiles",
    );
    expect(data.connection.state).toBe("degraded");
    expect(data.connection.usingMockData).toBe(true);
    expect(data.connection.warnings).toContain("RUNTIME_PROFILES_MOCK_FALLBACK");
  });

  it("marks missing runtime tool registry as non-authoritative fallback", async () => {
    const routeData = baseRouteData();
    delete routeData[API_ENDPOINTS.runtimeToolRegistry];
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.runtimeToolRegistry.tool_invocation_enabled).toBe(false);
    expect(data.runtimeToolRegistry.remote_discovery_enabled).toBe(false);
    expect(data.runtimeToolRegistry.plugin_import_enabled).toBe(false);
    expect(data.runtimeToolRegistry.connector_write_activation_enabled).toBe(false);
    expect(data.runtimeToolRegistry.invocation_enabled_count).toBe(0);
    expect(data.runtimeToolRegistry.preview_available_count).toBeGreaterThan(0);
    expect(data.routeStates["/runtime"].state).toBe("mock_fallback");
    expect(data.routeStates["/runtime"].backendRouteRefs).toContain(
      "GET /api/runtime/tool-registry",
    );
    expect(data.connection.state).toBe("degraded");
    expect(data.connection.usingMockData).toBe(true);
    expect(data.connection.warnings).toContain(
      "RUNTIME_TOOL_REGISTRY_MOCK_FALLBACK",
    );
  });

  it("marks missing CRM route as non-authoritative fallback", async () => {
    const routeData = baseRouteData();
    delete routeData[API_ENDPOINTS.crmSummary];
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.crmLocalCommandCenter.backend_owned).toBe(false);
    expect(data.crmLocalCommandCenter.authority_posture.send_enabled).toBe(false);
    expect(data.crmLocalCommandCenter.authority_posture.connector_write_enabled).toBe(
      false,
    );
    expect(data.routeStates["/crm"].state).toBe("mock_fallback");
    expect(data.routeStates["/crm"].backendRouteRefs).toContain(
      "GET /control-center/crm/summary",
    );
    expect(data.connection.state).toBe("degraded");
    expect(data.connection.usingMockData).toBe(true);
    expect(data.connection.warnings).toContain(
      "CRM_LOCAL_COMMAND_CENTER_MOCK_FALLBACK",
    );
  });

  it("marks a CRM response without the Social projection as non-authoritative fallback", async () => {
    const routeData = baseRouteData();
    const crm = JSON.parse(JSON.stringify(routeData[API_ENDPOINTS.crmSummary]));
    delete crm.social_relationship_projection;
    routeData[API_ENDPOINTS.crmSummary] = crm;
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.crmLocalCommandCenter.backend_owned).toBe(false);
    expect(data.crmLocalCommandCenter.social_relationship_projection.backend_owned).toBe(
      false,
    );
    expect(data.routeStates["/crm"].state).toBe("degraded");
    expect(data.connection.warnings).toContain(
      "CRM_LOCAL_COMMAND_CENTER_MOCK_FALLBACK",
    );
  });

  it.each([
    ["null projection", (crm: Record<string, unknown>) => {
      crm.social_relationship_projection = null;
    }],
    ["null projection item", (crm: Record<string, unknown>) => {
      const projection = crm.social_relationship_projection as Record<
        string,
        unknown
      >;
      projection.items = [null];
      projection.total_item_count = 1;
      projection.returned_item_count = 1;
    }],
    ["missing relationships array", (crm: Record<string, unknown>) => {
      delete crm.relationships;
    }],
    ["null people array", (crm: Record<string, unknown>) => {
      crm.people = null;
    }],
    ["non-array organizations", (crm: Record<string, unknown>) => {
      crm.organizations = {};
    }],
    ["null relationship entry", (crm: Record<string, unknown>) => {
      crm.relationships = [null];
    }],
    ["primitive person entry", (crm: Record<string, unknown>) => {
      crm.people = ["person-ref:crm-local:invalid"];
    }],
    ["array organization entry", (crm: Record<string, unknown>) => {
      crm.organizations = [[]];
    }],
  ])("fails closed for a CRM response with a %s", async (_label, mutate) => {
    const routeData = baseRouteData();
    const crm = JSON.parse(JSON.stringify(routeData[API_ENDPOINTS.crmSummary]));
    mutate(crm);
    routeData[API_ENDPOINTS.crmSummary] = crm;
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.crmLocalCommandCenter.backend_owned).toBe(false);
    expect(data.routeStates["/crm"].state).toBe("degraded");
    expect(data.connection.warnings).toContain(
      "CRM_LOCAL_COMMAND_CENTER_MOCK_FALLBACK",
    );
  });

  it("fails closed for CRM Social ownership metadata drift", async () => {
    const routeData = baseRouteData();
    const crm = JSON.parse(JSON.stringify(routeData[API_ENDPOINTS.crmSummary]));
    crm.social_relationship_projection.source_posture_ref =
      "source-posture-ref:crm-social:mock-fallback";
    routeData[API_ENDPOINTS.crmSummary] = crm;
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.crmLocalCommandCenter.backend_owned).toBe(false);
    expect(data.routeStates["/crm"].state).toBe("degraded");
  });

  it.each([
    ["safe summary", "safe_summary", "Altered safe-looking summary."],
    [
      "deep link",
      "crm_deep_link_ref",
      "control-center-deep-link-ref:crm:unbound-safe-looking-item",
    ],
    ["person owner", "person_ref", "person-ref:crm-local:other"],
    [
      "organization owner",
      "organization_ref",
      "organization-ref:crm-local:other",
    ],
    ["health", "health_state", "steady"],
    ["freshness", "freshness_state", "stale"],
  ])("fails closed for CRM Social item %s drift", async (_label, field, value) => {
    const routeData = baseRouteData();
    const crm = JSON.parse(JSON.stringify(routeData[API_ENDPOINTS.crmSummary]));
    crm.social_relationship_projection.items[0][field] = value;
    routeData[API_ENDPOINTS.crmSummary] = crm;
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.crmLocalCommandCenter.backend_owned).toBe(false);
    expect(data.routeStates["/crm"].state).toBe("degraded");
    expect(data.connection.warnings).toContain(
      "CRM_LOCAL_COMMAND_CENTER_MOCK_FALLBACK",
    );
  });

  it("rejects Settings authority state that is not backend-owned", async () => {
    const routeData = baseRouteData();
    const settings = routeData[
      API_ENDPOINTS.controlCenterSettingsStatus
    ] as Record<string, unknown>;
    routeData[API_ENDPOINTS.controlCenterSettingsStatus] = {
      ...settings,
      authority_lease_state: {
        ...(settings.authority_lease_state as Record<string, unknown>),
        backend_owned: false,
      },
    };
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.routeStates["/settings"].state).toBe("mock_fallback");
    expect(data.settingsStatus.authority_lease_state.backend_owned).toBe(false);
  });

  it("rejects agent-loop payloads missing backend-owned reasoning truth", async () => {
    const routeData = baseRouteData();
    const thread = routeData[API_ENDPOINTS.founderAgentLoopThread] as Record<
      string,
      unknown
    >;
    routeData[API_ENDPOINTS.founderAgentLoopThread] = {
      ...thread,
      reasoning_truth: {
        ...(thread.reasoning_truth as Record<string, unknown>),
        backend_owned: false,
        authority_posture: "authorized",
      },
    };
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.founderAgentLoopThread.backend_owned).toBe(false);
    expect(data.founderAgentLoopThread.reasoning_truth.authority_posture).toBe(
      "non_authoritative_review_truth",
    );
    expect(data.connection.state).toBe("degraded");
    expect(data.connection.warnings).toContain(
      "AGENT_LOOP_THREAD_MOCK_FALLBACK",
    );
  });

  it.each([
    ["lane count", (posture: Record<string, unknown>) => {
      posture.existing_exact_network_lane_count = 5;
    }],
    ["content authority", (posture: Record<string, unknown>) => {
      const rows = posture.rows as Array<Record<string, unknown>>;
      rows[0].external_content_can_grant_authority = true;
    }],
    ["missing evidence", (posture: Record<string, unknown>) => {
      const rows = posture.rows as Array<Record<string, unknown>>;
      rows[0].evidence_refs = [];
    }],
  ])("rejects unsafe external-information %s truth", async (_label, mutate) => {
    const routeData = baseRouteData();
    const thread = JSON.parse(
      JSON.stringify(routeData[API_ENDPOINTS.founderAgentLoopThread]),
    ) as Record<string, unknown>;
    const highMaturity = thread.high_maturity_spine_readiness as Record<
      string,
      unknown
    >;
    const externalInformation = highMaturity.external_information_handling as Record<
      string,
      unknown
    >;
    mutate(externalInformation);
    routeData[API_ENDPOINTS.founderAgentLoopThread] = thread;
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.founderAgentLoopThread.backend_owned).toBe(false);
    expect(data.connection.warnings).toContain(
      "AGENT_LOOP_THREAD_MOCK_FALLBACK",
    );
  });

  it("rejects malformed governed memory context selections", async () => {
    const routeData = baseRouteData();
    const contextManifest = routeData[
      API_ENDPOINTS.founderMemoryContextManifest
    ] as Record<string, unknown>;
    routeData[API_ENDPOINTS.founderMemoryContextManifest] = {
      ...contextManifest,
      governed_context: {
        schema_version: "governed_memory_context_manifest.v1",
        contract_ref: "contract-ref:governed-memory-context-manifest:v1",
        route_ref: "GET /control-center/memory/context-manifest",
        status: "ready_for_operator_preview",
        context_manifest_ref: "context-manifest-ref:malformed",
        manifest_fingerprint_ref: "fingerprint-ref:malformed",
        context_receipt_ref: "receipt-ref:malformed",
        context_receipt_status: "derived_preview_not_persisted",
        query_ref: "query-ref:malformed",
        checked_at: "2026-07-11T00:00:00Z",
        source_index_generated_at: "2026-07-11T00:00:00Z",
        expires_at: "2026-07-11T01:00:00Z",
        source_scan_truncated: false,
        candidate_count_complete: true,
        budget: {
          max_items: 1,
          max_tokens: 10,
          selected_items: 1,
          used_tokens: 1,
          capacity_excluded_items: 0,
          status: "available",
        },
        candidate_count: 1,
        selection_count: 1,
        exclusion_count: 0,
        selections: [{}],
        exclusions: [],
        blocked_state_refs: ["blocked-state:memory-context:no-authority"],
        redaction_status: "safe_refs_only",
        preview_only: true,
        context_injection_authorized: false,
        automatic_memory_inclusion_authorized: false,
        memory_truth_authority: false,
        action_execution_authorized: false,
        approval_authority_granted: false,
        connector_write_authorized: false,
        model_provider_authority_allowed: false,
        raw_content_persisted: false,
        production_authority_enabled: false,
      },
    };
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.founderMemoryContextManifest.governed_context).toBeUndefined();
    expect(data.connection.warnings).toContain("PARTIAL_MOCK_FALLBACK");
  });

  it("rejects unsafe web research aggregation posture", async () => {
    const routeData = baseRouteData();
    const capabilitySurface = routeData[
      API_ENDPOINTS.controlCenterCapabilitySurface
    ] as typeof mockControlCenterData.capabilitySurface;
    routeData[API_ENDPOINTS.controlCenterCapabilitySurface] = {
      ...capabilitySurface,
      web_hybrid: {
        ...capabilitySurface.web_hybrid,
        research_aggregation: {
          ...capabilitySurface.web_hybrid.research_aggregation,
          raw_page_content_persisted: true,
        },
      },
    };
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(
      data.capabilitySurface.web_hybrid.research_aggregation
        .raw_page_content_persisted,
    ).toBe(false);
    expect(data.connection.warnings).toContain("PARTIAL_MOCK_FALLBACK");
  });

  it("rejects maturity score inflation without evidence-gated acceptance", async () => {
    const routeData = baseRouteData();
    const capabilitySurface = JSON.parse(
      JSON.stringify(routeData[API_ENDPOINTS.controlCenterCapabilitySurface]),
    ) as typeof mockControlCenterData.capabilitySurface;
    capabilitySurface.maturity.components[0].verified_score = 10;
    capabilitySurface.maturity.components[0].evidence_status = "baseline_only";
    routeData[API_ENDPOINTS.controlCenterCapabilitySurface] = capabilitySurface;
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.connection.warnings).toContain("PARTIAL_MOCK_FALLBACK");
    expect(data.capabilitySurface.maturity.components[0].verified_score).toBe(
      data.capabilitySurface.maturity.components[0].baseline_score,
    );
    expect(data.capabilitySurface.maturity.authority_granted).toBe(false);
  });

  it("rejects maturity aggregate and taxonomy drift", async () => {
    for (const mutate of [
      (maturity: typeof mockControlCenterData.capabilitySurface.maturity) => {
        maturity.baseline_weighted_score = 99;
      },
      (maturity: typeof mockControlCenterData.capabilitySurface.maturity) => {
        maturity.components[1].component_id = maturity.components[0].component_id;
      },
      (maturity: typeof mockControlCenterData.capabilitySurface.maturity) => {
        const extensibility = maturity.components.find(
          (component) => component.component_id === "extensibility_ecosystem",
        );
        if (extensibility) {
          extensibility.baseline_score = 9;
        }
      },
      (maturity: typeof mockControlCenterData.capabilitySurface.maturity) => {
        maturity.components[0].gates[0].evidence_refs = [];
      },
      (maturity: typeof mockControlCenterData.capabilitySurface.maturity) => {
        maturity.components[0].gates[1].blocker_codes = [];
      },
      (maturity: typeof mockControlCenterData.capabilitySurface.maturity) => {
        maturity.safe_summary = { unsafe: true } as unknown as string;
      },
    ]) {
      const routeData = baseRouteData();
      const capabilitySurface = JSON.parse(
        JSON.stringify(routeData[API_ENDPOINTS.controlCenterCapabilitySurface]),
      ) as typeof mockControlCenterData.capabilitySurface;
      mutate(capabilitySurface.maturity);
      routeData[API_ENDPOINTS.controlCenterCapabilitySurface] = capabilitySurface;
      stubControlCenterFetch(routeData);

      const data = await loadControlCenterData();

      expect(data.connection.warnings).toContain("PARTIAL_MOCK_FALLBACK");
      expect(data.capabilitySurface.maturity.baseline_weighted_score).toBe(87.5);
    }
  });

  it("rejects unsafe WEB-HYBRID lane and rendered-ref content", async () => {
    const routeData = baseRouteData();
    const capabilitySurface = JSON.parse(
      JSON.stringify(
        routeData[API_ENDPOINTS.controlCenterCapabilitySurface],
      ),
    ) as typeof mockControlCenterData.capabilitySurface;
    const unsafePath = ["", "Users", "private", "raw page content"].join("/");
    const unsafeProviderMarker = ["provider", "payload"].join("_");
    const unsafePageRef = ["https:", "", "private.example", "raw-page"].join("/");
    capabilitySurface.web_hybrid.lanes[0].display_label = unsafePath;
    capabilitySurface.web_hybrid.lanes[1].provider_ref =
      `provider-ref:firecrawl:${unsafeProviderMarker}`;
    capabilitySurface.web_hybrid.research_aggregation.proof_refs = [
      unsafePageRef,
    ];
    routeData[API_ENDPOINTS.controlCenterCapabilitySurface] = capabilitySurface;
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();
    const serialized = JSON.stringify(data.capabilitySurface);

    expect(data.connection.warnings).toContain("PARTIAL_MOCK_FALLBACK");
    expect(data.capabilitySurface.web_hybrid.lanes[0].display_label).toBe(
      "SearXNG read-only search",
    );
    expect(serialized).not.toContain(unsafePath);
    expect(serialized).not.toContain(
      `provider-ref:firecrawl:${unsafeProviderMarker}`,
    );
    expect(serialized).not.toContain("private.example");
  });

  it("rejects secret and local-path shapes in WEB-HYBRID rendered text", async () => {
    const unsafeRenderedValues = [
      ["password", "supersecret"].join("="),
      ["authorization", "Bearer private-value"].join("="),
      ["cookie", "private-value"].join("="),
      ["", "private", "tmp", "private-value"].join("/"),
      ["", "var", "tmp", "private-value"].join("/"),
      ["C:", "Users", "private", "private-value"].join("\\"),
    ];

    for (const unsafeValue of unsafeRenderedValues) {
      const routeData = baseRouteData();
      const capabilitySurface = JSON.parse(
        JSON.stringify(
          routeData[API_ENDPOINTS.controlCenterCapabilitySurface],
        ),
      ) as typeof mockControlCenterData.capabilitySurface;
      capabilitySurface.web_hybrid.safe_summary = unsafeValue;
      routeData[API_ENDPOINTS.controlCenterCapabilitySurface] = capabilitySurface;
      stubControlCenterFetch(routeData);

      const data = await loadControlCenterData();

      expect(data.connection.warnings).toContain("PARTIAL_MOCK_FALLBACK");
      expect(JSON.stringify(data.capabilitySurface)).not.toContain(unsafeValue);
    }
  });

  it("fails closed for malformed unselected CRM relationships", async () => {
    async function expectFallback(
      mutate: (relationship: Record<string, unknown>) => void,
    ): Promise<void> {
      const routeData = baseRouteData();
      const crm = JSON.parse(JSON.stringify(routeData[API_ENDPOINTS.crmSummary]));
      crm.relationships.push({
        ...crm.relationships[0],
        relationship_ref: "relationship-ref:crm-local:unselected",
      });
      mutate(crm.relationships[1]);
      routeData[API_ENDPOINTS.crmSummary] = crm;
      stubControlCenterFetch(routeData);

      const data = await loadControlCenterData();

      expect(data.crmLocalCommandCenter.backend_owned).toBe(false);
      expect(data.routeStates["/crm"].state).toBe("degraded");
      expect(data.connection.warnings).toContain(
        "CRM_LOCAL_COMMAND_CENTER_MOCK_FALLBACK",
      );
    }

    await expectFallback((relationship) => {
      delete relationship.health_state;
    });
    await expectFallback((relationship) => {
      relationship.timeline_event_refs = null;
    });
    await expectFallback((relationship) => {
      relationship.raw_contact_details_included = true;
    });
  });
});

function baseRouteData(): Record<string, unknown> {
  const backendOwnedApprovalQueue = {
    ...mockControlCenterData.runAttachedApprovalQueue,
    source: "python_core_run_attached_approval_queue_read_model" as const,
    backend_owned: true,
  };
  const backendOwnedStartHere = {
    ...mockControlCenterData.founderStartHere,
    source: "python_core_control_center_start_here_read_model" as const,
    backend_owned: true,
    status: "implemented_backend_owned_start_here_loop_contract",
    readiness_state: "ready_for_one_local_governed_loop",
    local_loop_status: "one_governed_local_loop_available",
    complete_daily_loop_available: true,
    missing_prerequisite_refs: [],
  };
  const backendOwnedProofIndex = {
    ...mockControlCenterData.proofIndex,
    source: "python_core_control_center_proof_index" as const,
    backend_owned: true,
    status: "implemented_backend_owned_universal_proof_index",
    records: mockControlCenterData.proofIndex.records.map((record) => ({
      ...record,
      run_detail: record.run_detail
        ? {
            ...record.run_detail,
            source: "python_core_control_center_proof_run_detail" as const,
          }
        : record.run_detail,
    })),
  };
  const backendOwnedTrustAuthorityMatrix = {
    ...mockControlCenterData.trustAuthorityMatrix,
    status: "implemented_backend_owned_trust_authority_matrix",
    backend_owned: true,
    operator_summary:
      "Backend-owned Trust matrix fixture for local read authority posture.",
    next_safe_action: "Inspect backend-owned Trust route and CLI refs.",
    lanes: mockControlCenterData.trustAuthorityMatrix.lanes.map((lane) => ({
      ...lane,
      current_posture:
        lane.authority_state === "available_now"
          ? "Backend-owned local read and preview posture is available for review."
          : "External mutation requires an implemented AuthorityLease domain/capability scope plus exact approval and receipts.",
      operator_can_do_now:
        lane.authority_state === "available_now"
          ? "Inspect backend-owned local read and preview surfaces."
          : "Keep external mutation blocked.",
      next_safe_action: "Inspect backend-owned Trust route and CLI refs.",
    })),
    tier_summaries: mockControlCenterData.trustAuthorityMatrix.tier_summaries.map(
      (tier) => ({
        ...tier,
        operator_summary: "Backend-owned Trust tier summary fixture.",
      }),
    ),
  };
  const backendOwnedCodingSession = {
    ...mockControlCenterData.codingSession,
    session_ref: "coding-session:summary-endpoint-test",
    status: "implemented_read_only_cockpit_seed",
    backend_owned: true,
    mock_fallback: false,
    local_read_model_only: true,
    safe_refs_only: true,
    raw_content_included: false,
    control_center_grants_authority: false,
    file_write_enabled: false,
    shell_subprocess_execution_enabled: false,
    git_mutation_enabled: false,
    provider_model_call_enabled: false,
    browser_automation_enabled: false,
    connector_write_enabled: false,
    background_autonomy_enabled: false,
    production_authority_enabled: false,
  };
  const backendOwnedCodingContext = {
    ...mockControlCenterData.codingContext,
    context_pack_ref: "context-pack:coding-summary-endpoint-test",
    session_ref: "coding-session:summary-endpoint-test",
    backend_owned: true,
    read_only: true,
    preview_only: true,
    safe_refs_only: true,
    raw_paths_included: false,
    raw_content_included: false,
    repo_file_read_performed: false,
    file_write_enabled: false,
    shell_subprocess_execution_enabled: false,
    git_mutation_enabled: false,
    provider_model_call_enabled: false,
    browser_automation_enabled: false,
    connector_write_enabled: false,
    production_authority_enabled: false,
  };
  const backendOwnedCodingPatchProposal = {
    ...mockControlCenterData.codingPatchProposal,
    patch_proposal_ref: "patch-proposal:coding-summary-endpoint-test",
    session_ref: "coding-session:summary-endpoint-test",
    context_pack_ref: "context-pack:coding-summary-endpoint-test",
    backend_owned: true,
    read_only: true,
    proposal_only: true,
    safe_refs_only: true,
    raw_paths_included: false,
    raw_content_included: false,
    repo_file_read_performed: false,
    patch_apply_enabled: false,
    file_write_enabled: false,
    shell_subprocess_execution_enabled: false,
    git_mutation_enabled: false,
    provider_model_call_enabled: false,
    browser_automation_enabled: false,
    connector_write_enabled: false,
    production_authority_enabled: false,
  };
  const backendOwnedCodingPatchApplyReadiness = {
    ...mockControlCenterData.codingPatchApplyReadiness,
    readiness_ref: "patch-apply-readiness:coding-summary-endpoint-test",
    session_ref: "coding-session:summary-endpoint-test",
    context_pack_ref: "context-pack:coding-summary-endpoint-test",
    patch_proposal_ref: "patch-proposal:coding-summary-endpoint-test",
    backend_owned: true,
    read_only: true,
    readiness_only: true,
    safe_refs_only: true,
    raw_paths_included: false,
    raw_content_included: false,
    repo_file_read_performed: false,
    exact_patch_body_available: false,
    hunk_selection_contract_available: false,
    checkpoint_contract_available: false,
    approval_binding_available: false,
    rollback_contract_available: false,
    patch_apply_enabled: false,
    file_write_enabled: false,
    approval_grant_capture_enabled: false,
    rollback_execution_enabled: false,
    shell_subprocess_execution_enabled: false,
    git_mutation_enabled: false,
    provider_model_call_enabled: false,
    browser_automation_enabled: false,
    connector_write_enabled: false,
    background_autonomy_enabled: false,
    production_authority_enabled: false,
  };
  const backendOwnedCodingTestCommandReadiness = {
    ...mockControlCenterData.codingTestCommandReadiness,
    readiness_ref: "test-command-readiness:coding-summary-endpoint-test",
    session_ref: "coding-session:summary-endpoint-test",
    context_pack_ref: "context-pack:coding-summary-endpoint-test",
    patch_proposal_ref: "patch-proposal:coding-summary-endpoint-test",
    patch_apply_readiness_ref:
      "patch-apply-readiness:coding-summary-endpoint-test",
    backend_owned: true,
    read_only: true,
    readiness_only: true,
    safe_refs_only: true,
    raw_command_included: false,
    raw_output_included: false,
    command_output_summary_included: false,
    exit_code_available: false,
    test_receipt_created: false,
    command_execution_enabled: false,
    shell_subprocess_execution_enabled: false,
    arbitrary_shell_enabled: false,
    install_command_enabled: false,
    network_command_enabled: false,
    destructive_command_enabled: false,
    background_process_enabled: false,
    file_write_enabled: false,
    git_mutation_enabled: false,
    provider_model_call_enabled: false,
    browser_automation_enabled: false,
    connector_write_enabled: false,
    production_authority_enabled: false,
  };
  const backendOwnedCodingGitReview = {
    ...mockControlCenterData.codingGitReview,
    git_review_ref: "git-review:coding-summary-endpoint-test",
    session_ref: "coding-session:summary-endpoint-test",
    context_pack_ref: "context-pack:coding-summary-endpoint-test",
    patch_proposal_ref: "patch-proposal:coding-summary-endpoint-test",
    patch_apply_readiness_ref:
      "patch-apply-readiness:coding-summary-endpoint-test",
    test_command_readiness_ref:
      "test-command-readiness:coding-summary-endpoint-test",
    backend_owned: true,
    read_only: true,
    proposal_only: true,
    safe_refs_only: true,
    git_status_execution_enabled: false,
    git_diff_execution_enabled: false,
    stage_enabled: false,
    commit_enabled: false,
    push_enabled: false,
    pr_open_enabled: false,
    merge_enabled: false,
    raw_git_output_included: false,
    raw_diff_included: false,
    raw_path_included: false,
    commit_message_text_included: false,
    pr_description_text_included: false,
    git_receipt_created: false,
    shell_subprocess_execution_enabled: false,
    file_write_enabled: false,
    git_mutation_enabled: false,
    provider_model_call_enabled: false,
    browser_automation_enabled: false,
    connector_write_enabled: false,
    production_authority_enabled: false,
  };
  const backendOwnedCodingLivePreview = {
    ...mockControlCenterData.codingLivePreview,
    live_preview_ref: "live-preview:coding-summary-endpoint-test",
    session_ref: "coding-session:summary-endpoint-test",
    context_pack_ref: "context-pack:coding-summary-endpoint-test",
    patch_proposal_ref: "patch-proposal:coding-summary-endpoint-test",
    test_command_readiness_ref:
      "test-command-readiness:coding-summary-endpoint-test",
    git_review_ref: "git-review:coding-summary-endpoint-test",
    backend_owned: true,
    read_only: true,
    status_only: true,
    safe_refs_only: true,
    raw_url_included: false,
    raw_console_output_included: false,
    screenshot_artifact_included: false,
    screenshot_capture_enabled: false,
    visual_regression_enabled: false,
    console_capture_enabled: false,
    dev_server_status_detection_enabled: false,
    dev_server_start_enabled: false,
    dev_server_stop_enabled: false,
    browser_preview_enabled: false,
    browser_automation_enabled: false,
    browser_interaction_enabled: false,
    network_fetch_enabled: false,
    shell_subprocess_execution_enabled: false,
    file_write_enabled: false,
    git_mutation_enabled: false,
    provider_model_call_enabled: false,
    connector_write_enabled: false,
    production_authority_enabled: false,
  };
  const backendOwnedCodingMultiAgentReview = {
    ...mockControlCenterData.codingMultiAgentReview,
    review_ref: "multi-agent-review:coding-summary-endpoint-test",
    session_ref: "coding-session:summary-endpoint-test",
    context_pack_ref: "context-pack:coding-summary-endpoint-test",
    patch_proposal_ref: "patch-proposal:coding-summary-endpoint-test",
    test_command_readiness_ref:
      "test-command-readiness:coding-summary-endpoint-test",
    git_review_ref: "git-review:coding-summary-endpoint-test",
    live_preview_ref: "live-preview:coding-summary-endpoint-test",
    pair_agent_relay: {
      ...mockControlCenterData.codingMultiAgentReview.pair_agent_relay,
      readiness_ref: "coding-pair-agent-relay-readiness:summary-endpoint-test",
      run_contract: {
        ...mockControlCenterData.codingMultiAgentReview.pair_agent_relay
          .run_contract,
        run_ref: "coding-pair-run:summary-endpoint-test",
        task_ref: "coding-task:pair-agent-summary-endpoint-test",
        idempotency_ref: "idempotency-ref:coding-pair:summary-endpoint-test",
      },
      repo_safe_current_state:
        "Backend-owned Pair Agents readiness cannot start foreground adapters.",
      safe_summary:
        "Pair Agents is backend-owned preview/readiness only; foreground adapter execution is blocked.",
      next_safe_action:
        "Review the exact unblock prompt before any future foreground adapter execution lane.",
      backend_owned: true,
    },
    backend_owned: true,
    read_only: true,
    proposal_only: true,
    safe_refs_only: true,
    provider_model_call_enabled: false,
    provider_sdk_call_enabled: false,
    local_agent_execution_enabled: false,
    multi_agent_execution_enabled: false,
    background_dispatch_enabled: false,
    background_autonomy_enabled: false,
    autonomous_execution_enabled: false,
    context_injection_enabled: false,
    raw_prompt_included: false,
    raw_response_included: false,
    provider_payload_included: false,
    file_write_enabled: false,
    shell_subprocess_execution_enabled: false,
    git_mutation_enabled: false,
    browser_automation_enabled: false,
    connector_write_enabled: false,
    production_authority_enabled: false,
  };
  const backendOwnedWorkBoard = {
    ...mockControlCenterData.workBoard,
    board_ref: "work-board:summary-endpoint-test",
    source_label: "python_core_work_board_read_model",
    backend_owned: true,
    read_only: true,
    safe_refs_only: true,
    non_authoritative_mock_fallback: false,
    raw_paths_included: false,
    raw_content_included: false,
    board_mutation_enabled: false,
    durable_drag_drop_enabled: false,
    durable_reorder_persistence_enabled: true,
    approval_required_for_reorder: true,
    reorder_route_ref: "POST /control-center/work-board/reorder",
    latest_reorder_receipt_ref: null,
    local_card_create_enabled: true,
    local_card_create_contract_available: true,
    approval_required_for_card_create: true,
    card_create_route_available: true,
    card_create_route_ref: "POST /control-center/work-board/cards",
    latest_card_create_receipt_ref: null,
    local_task_records: [],
    local_task_create_enabled: true,
    local_task_create_contract_available: true,
    approval_required_for_task_create: true,
    task_create_route_available: true,
    task_create_route_ref: "POST /control-center/work-board/tasks",
    latest_task_create_receipt_ref: null,
    issue_tracker_write_enabled: false,
    connector_write_enabled: false,
    shell_subprocess_execution_enabled: false,
    browser_automation_enabled: false,
    background_autonomy_enabled: false,
    production_authority_enabled: false,
    drag_drop_posture: {
      ...mockControlCenterData.workBoard.drag_drop_posture,
      local_preview_enabled: true,
      keyboard_reorder_preview_enabled: true,
      durable_reorder_enabled: true,
      backend_mutation_route_available: true,
      receipt_created: false,
      rollback_available: true,
      mutation_route_ref: "POST /control-center/work-board/reorder",
      approval_required: true,
      exact_scope_required: true,
      idempotency_required: true,
      safe_disable_refs: ["safe-disable-ref:work-board:durable-reorder"],
      rollback_refs: ["rollback-ref:work-board:restore-previous-order"],
    },
  };
  const backendOwnedCrm = {
    ...mockControlCenterData.crmLocalCommandCenter,
    source: "python_core_crm_local_command_center_read_model" as const,
    state: "read_only" as const,
    backend_owned: true,
    read_only: true,
    safe_refs_only: true,
    social_relationship_projection: {
      ...mockControlCenterData.crmLocalCommandCenter.social_relationship_projection,
      source_posture_ref: "source-posture-ref:crm-social:reviewed-local",
      freshness_ref: "freshness-ref:crm-social:derived-from-crm-snapshot",
      backend_owned: true,
      items:
        mockControlCenterData.crmLocalCommandCenter.social_relationship_projection.items.map(
          (item) => ({
            ...item,
            projection_item_ref:
              "projection-item-ref:crm-social:relationship-ref:crm-local:mock-alpha-ccc98c92f1691866",
            crm_deep_link_ref:
              "control-center-deep-link-ref:crm:relationship-ref:crm-local:mock-alpha-ccc98c92f1691866",
            safe_summary:
              "Non-authoritative fallback relationship with safe refs only.",
            why_shown:
              "Shown because CRM owns a reviewed relationship tagged for the Social relationship context projection.",
            backend_owned: true,
          }),
        ),
    },
    authority_posture: {
      ...mockControlCenterData.crmLocalCommandCenter.authority_posture,
      backend_owned: true,
      control_center_grants_authority: false,
      read_only_routes_enabled: true,
      exact_local_mutation_lane_enabled: true,
      connector_runtime_enabled: false,
      connector_write_enabled: false,
      account_sync_enabled: false,
      send_enabled: false,
      calendar_write_enabled: false,
      provider_model_call_enabled: false,
      live_web_enabled: false,
      browser_runtime_enabled: false,
      background_autonomy_enabled: false,
      external_crm_write_enabled: false,
      production_authority_enabled: false,
    },
  };
  return {
    [API_ENDPOINTS.controlCenterManifest]: mockControlCenterData.manifest,
    [API_ENDPOINTS.controlCenterDashboard]: mockControlCenterData.dashboard,
    [API_ENDPOINTS.controlCenterStatus]: mockControlCenterData.status,
    [API_ENDPOINTS.controlCenterRoutes]: mockControlCenterData.routes,
    [API_ENDPOINTS.controlCenterCapabilitySurface]:
      mockControlCenterData.capabilitySurface,
    [API_ENDPOINTS.runtimeReadiness]: mockControlCenterData.runtimeReadiness,
    [API_ENDPOINTS.runtimeCapabilityMatrix]:
      mockControlCenterData.capabilityMatrix,
    [API_ENDPOINTS.runtimeDelegationAdapter]:
      mockControlCenterData.runtimeDelegationAdapter,
    [API_ENDPOINTS.runtimeInterfaceMode]:
      mockControlCenterData.runtimeInterfaceMode,
    [API_ENDPOINTS.runtimeHermesContextPack]:
      mockControlCenterData.runtimeHermesContextPack,
    [API_ENDPOINTS.runtimeCapabilityDiscovery]:
      mockControlCenterData.runtimeCapabilityDiscovery,
    [API_ENDPOINTS.runtimeRunEvents]: mockControlCenterData.runtimeRunEvents,
    [API_ENDPOINTS.runtimeApprovalBridge]:
      mockControlCenterData.runtimeApprovalBridge,
    [API_ENDPOINTS.runtimeStreamingProgress]:
      mockControlCenterData.runtimeStreamingProgress,
    [API_ENDPOINTS.runtimeProfiles]: mockControlCenterData.runtimeProfiles,
    [API_ENDPOINTS.runtimeToolRegistry]: mockControlCenterData.runtimeToolRegistry,
    [API_ENDPOINTS.runtimeVirtualProviderMoa]:
      mockControlCenterData.runtimeVirtualProviderMoa,
    [API_ENDPOINTS.runtimeUsageCostAnalytics]:
      mockControlCenterData.runtimeUsageCostAnalytics,
    [API_ENDPOINTS.runtimePromptStabilityTiers]:
      mockControlCenterData.runtimePromptStabilityTiers,
    [API_ENDPOINTS.runtimeContextBudgetPressure]:
      mockControlCenterData.runtimeContextBudgetPressure,
    [API_ENDPOINTS.runtimeHardlineCommandBlocklist]:
      mockControlCenterData.runtimeHardlineCommandBlocklist,
    [API_ENDPOINTS.runtimeManagedScopePolicy]:
      mockControlCenterData.runtimeManagedScopePolicy,
    [API_ENDPOINTS.runtimeDoctorDiagnostics]:
      mockControlCenterData.runtimeDoctorDiagnostics,
    [API_ENDPOINTS.runtimeSessionContinuity]:
      mockControlCenterData.runtimeSessionContinuity,
    [API_ENDPOINTS.runtimeMcpCatalogFiltering]:
      mockControlCenterData.runtimeMcpCatalogFiltering,
    [API_ENDPOINTS.runtimeBackgroundJobs]:
      mockControlCenterData.runtimeBackgroundJobs,
    [API_ENDPOINTS.runtimeSubagentIsolation]:
      mockControlCenterData.runtimeSubagentIsolation,
    [API_ENDPOINTS.runtimeWorktreePerAgent]:
      mockControlCenterData.runtimeWorktreePerAgent,
    [API_ENDPOINTS.runtimeStagedOrchestration]:
      mockControlCenterData.runtimeStagedOrchestration,
    [API_ENDPOINTS.runtimeLspDiagnostics]:
      mockControlCenterData.runtimeLspDiagnostics,
    [API_ENDPOINTS.runtimePreviewRail]:
      mockControlCenterData.runtimePreviewRail,
    [API_ENDPOINTS.runtimeSlashCommandRegistry]:
      mockControlCenterData.runtimeSlashCommandRegistry,
    [API_ENDPOINTS.runtimeInterruptRedirect]:
      mockControlCenterData.runtimeInterruptRedirect,
    [API_ENDPOINTS.runtimeLoggingProfile]:
      mockControlCenterData.runtimeLoggingProfile,
    [API_ENDPOINTS.runtimeResultClassification]:
      mockControlCenterData.runtimeResultClassification,
    [API_ENDPOINTS.runtimeVoiceMediaPosture]:
      mockControlCenterData.runtimeVoiceMediaPosture,
    [API_ENDPOINTS.runtimeMessagingGatewayPosture]:
      mockControlCenterData.runtimeMessagingGatewayPosture,
    [API_ENDPOINTS.runtimeRemoteExecutionPosture]:
      mockControlCenterData.runtimeRemoteExecutionPosture,
    [API_ENDPOINTS.runtimePluginMetadataPosture]:
      mockControlCenterData.runtimePluginMetadataPosture,
    [API_ENDPOINTS.runtimeSkillMarketplacePosture]:
      mockControlCenterData.runtimeSkillMarketplacePosture,
    [API_ENDPOINTS.setupAssistantSummary]:
      mockControlCenterData.macosSetupAssistant,
    [API_ENDPOINTS.providerSetupGuide]: mockControlCenterData.providerCatalog,
    [API_ENDPOINTS.modelProviderControlPlane]:
      mockControlCenterData.modelProviderControlPlane,
    [API_ENDPOINTS.controlCenterSettingsStatus]: {
      ...mockControlCenterData.settingsStatus,
      authority_lease_state: {
        ...mockControlCenterData.settingsStatus.authority_lease_state,
        backend_owned: true,
      },
    },
    [API_ENDPOINTS.controlCenterLocalModelsStatus]:
      mockControlCenterData.localModelsStatus,
    [API_ENDPOINTS.founderTodaySummary]: mockControlCenterData.founderToday,
    [API_ENDPOINTS.founderAgentLoopThread]: {
      ...mockControlCenterData.founderAgentLoopThread,
      thread_ref: "agent-loop-thread:summary-test:current",
      status: "implemented_backend_owned_read_model_no_new_authority",
      capability_status: "partial",
      source: "python_core_agent_loop_thread_read_model",
      backend_owned: true,
      reasoning_truth: {
        ...mockControlCenterData.founderAgentLoopThread.reasoning_truth,
        backend_owned: true,
      },
      high_maturity_spine_readiness: {
        ...mockControlCenterData.founderAgentLoopThread.high_maturity_spine_readiness,
        status: "implemented_backend_owned_read_model_no_new_authority",
        source: "python_core_agent_loop_thread_read_model",
        backend_owned: true,
        implemented_count: 5,
        usable_or_better_count: 13,
        average_score_0_10: 7.3,
        overall_projection_0_100: 73,
        coverage_status:
          "all_w1_w13_have_code_docs_tests_or_governed_blocked_posture",
        rows:
          mockControlCenterData.founderAgentLoopThread.high_maturity_spine_readiness.rows.map(
            (row, index) => ({
              ...row,
              status: index % 3 === 0 ? "implemented" : "partial",
              maturity: "usable",
              score_0_10: index % 3 === 0 ? 8 : 7,
            }),
          ),
        external_information_handling: {
          ...mockControlCenterData.founderAgentLoopThread
            .high_maturity_spine_readiness.external_information_handling,
          status: "implemented_read_only_posture_map_existing_lanes_only",
          source: "python_core_agent_loop_thread_read_model",
          backend_owned: true,
          implemented_or_blocked_count: 8,
          existing_exact_network_lane_count: 4,
          exact_bounded_provider_lanes_implemented: true,
          rows:
            mockControlCenterData.founderAgentLoopThread.high_maturity_spine_readiness.external_information_handling.rows.map(
              (row) => {
                const exactLaneCount =
                  row.category_id === "allowlisted_gateway_preview"
                    ? 1
                    : row.category_id === "provider_search_scrape"
                      ? 3
                      : 0;
                return {
                  ...row,
                  status: "implemented_or_governed_blocked",
                  existing_exact_network_lane: exactLaneCount > 0,
                  exact_network_lane_count: exactLaneCount,
                };
              },
            ),
        },
      },
      operator_decision_matrix: {
        ...mockControlCenterData.founderAgentLoopThread.operator_decision_matrix,
        status: "implemented_backend_owned_read_model_no_new_authority",
        capability_status: "implemented",
        source: "python_core_agent_loop_thread_read_model",
        backend_owned: true,
        operator_can_decide_from_cockpit: true,
      },
    },
    [API_ENDPOINTS.founderStartHereSummary]: backendOwnedStartHere,
    [API_ENDPOINTS.controlCenterProofIndex]: backendOwnedProofIndex,
    [API_ENDPOINTS.trustAuthorityMatrix]: backendOwnedTrustAuthorityMatrix,
    [API_ENDPOINTS.controlCenterCodingSession]: backendOwnedCodingSession,
    [API_ENDPOINTS.controlCenterCodingContext]: backendOwnedCodingContext,
    [API_ENDPOINTS.controlCenterCodingPatchProposal]:
      backendOwnedCodingPatchProposal,
    [API_ENDPOINTS.controlCenterCodingPatchApplyReadiness]:
      backendOwnedCodingPatchApplyReadiness,
    [API_ENDPOINTS.controlCenterCodingTestCommandReadiness]:
      backendOwnedCodingTestCommandReadiness,
    [API_ENDPOINTS.controlCenterCodingGitReview]: backendOwnedCodingGitReview,
    [API_ENDPOINTS.controlCenterCodingLivePreview]:
      backendOwnedCodingLivePreview,
    [API_ENDPOINTS.controlCenterCodingMultiAgentReview]:
      backendOwnedCodingMultiAgentReview,
    [API_ENDPOINTS.controlCenterWorkBoard]: backendOwnedWorkBoard,
    [API_ENDPOINTS.socialPublishingProposal]:
      mockControlCenterData.socialPublishingProposal,
    [API_ENDPOINTS.founderEvidenceTimeline]:
      mockControlCenterData.founderEvidenceTimeline,
    [API_ENDPOINTS.founderMemoryReview]:
      mockControlCenterData.founderMemoryReview,
    [API_ENDPOINTS.founderMemoryWorkbench]:
      mockControlCenterData.founderMemoryWorkbench,
    [API_ENDPOINTS.founderMemoryContextPacks]:
      mockControlCenterData.founderMemoryContextPacks,
    [API_ENDPOINTS.founderMemoryRetrievalDiagnostics]:
      mockControlCenterData.founderMemoryRetrievalDiagnostics,
    [API_ENDPOINTS.founderMemoryCitationIntegrity]:
      mockControlCenterData.founderMemoryCitationIntegrity,
    [API_ENDPOINTS.founderMemoryQualityIssues]:
      mockControlCenterData.founderMemoryQualityIssues,
    [API_ENDPOINTS.founderMemoryMaintenanceRuns]:
      mockControlCenterData.founderMemoryMaintenanceRuns,
    [API_ENDPOINTS.founderMemoryContextManifest]:
      mockControlCenterData.founderMemoryContextManifest,
    [API_ENDPOINTS.founderActionsInbox]:
      mockControlCenterData.founderActionsInbox,
    [API_ENDPOINTS.founderMorningBriefing]:
      mockControlCenterData.founderMorningBriefing,
    [API_ENDPOINTS.founderSourceReadiness]:
      mockControlCenterData.founderSourceReadiness,
    [API_ENDPOINTS.founderStorageStatus]:
      mockControlCenterData.founderStorageStatus,
    [API_ENDPOINTS.crmSummary]: backendOwnedCrm,
    [API_ENDPOINTS.approvalSummary]:
      mockControlCenterData.dashboard.approval_summary,
    [API_ENDPOINTS.approvalQueue]: backendOwnedApprovalQueue,
    [API_ENDPOINTS.runObservability]: {
      ...mockControlCenterData.runObservability,
      source: "python_core_run_observability_read_model" as const,
      backend_owned: true,
    },
    [API_ENDPOINTS.runtimeReadinessSummary]:
      mockControlCenterData.dashboard.runtime_readiness_summary,
    [API_ENDPOINTS.foundationGateSummary]:
      mockControlCenterData.dashboard.foundation_gate_summary,
  };
}

function stubControlCenterFetch(routeData: Record<string, unknown>): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown) => {
      const path = endpointPath(input);
      if (!Object.prototype.hasOwnProperty.call(routeData, path)) {
        throw new Error(`missing test route fixture for ${path}`);
      }
      return new Response(
        JSON.stringify({
          ok: true,
          data: routeData[path],
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      );
    }),
  );
}

function endpointPath(input: unknown): string {
  if (typeof input === "string") {
    return new URL(input, "http://127.0.0.1").pathname;
  }
  if (input instanceof URL) {
    return input.pathname;
  }
  if (typeof input === "object" && input !== null && "url" in input) {
    return new URL(
      String((input as { url: unknown }).url),
      "http://127.0.0.1",
    ).pathname;
  }
  return new URL(String(input), "http://127.0.0.1").pathname;
}
