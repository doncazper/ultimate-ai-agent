import { afterEach, describe, expect, it, vi } from "vitest";
import { loadControlCenterData } from "./client";
import { API_ENDPOINTS } from "./endpoints";
import { mockControlCenterData } from "../mocks/controlCenterData";

describe("loadControlCenterData summary endpoint wiring", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
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
    expect(data.routeStates["/runtime"].state).toBe("mock_fallback");
    expect(data.routeStates["/runtime"].backendRouteRefs).toContain(
      "GET /api/runtime/run-events",
    );
    expect(data.connection.state).toBe("degraded");
    expect(data.connection.usingMockData).toBe(true);
    expect(data.connection.warnings).toContain("RUNTIME_RUN_EVENTS_MOCK_FALLBACK");
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
          : "External mutation remains blocked until exact lanes graduate.",
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
    [API_ENDPOINTS.runtimeReadiness]: mockControlCenterData.runtimeReadiness,
    [API_ENDPOINTS.runtimeCapabilityMatrix]:
      mockControlCenterData.capabilityMatrix,
    [API_ENDPOINTS.runtimeDelegationAdapter]:
      mockControlCenterData.runtimeDelegationAdapter,
    [API_ENDPOINTS.runtimeCapabilityDiscovery]:
      mockControlCenterData.runtimeCapabilityDiscovery,
    [API_ENDPOINTS.runtimeRunEvents]: mockControlCenterData.runtimeRunEvents,
    [API_ENDPOINTS.setupAssistantSummary]:
      mockControlCenterData.macosSetupAssistant,
    [API_ENDPOINTS.providerSetupGuide]: mockControlCenterData.providerCatalog,
    [API_ENDPOINTS.modelProviderControlPlane]:
      mockControlCenterData.modelProviderControlPlane,
    [API_ENDPOINTS.controlCenterSettingsStatus]:
      mockControlCenterData.settingsStatus,
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
