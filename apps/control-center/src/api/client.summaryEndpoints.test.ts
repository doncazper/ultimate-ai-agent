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
  return {
    [API_ENDPOINTS.controlCenterManifest]: mockControlCenterData.manifest,
    [API_ENDPOINTS.controlCenterDashboard]: mockControlCenterData.dashboard,
    [API_ENDPOINTS.controlCenterStatus]: mockControlCenterData.status,
    [API_ENDPOINTS.controlCenterRoutes]: mockControlCenterData.routes,
    [API_ENDPOINTS.runtimeReadiness]: mockControlCenterData.runtimeReadiness,
    [API_ENDPOINTS.runtimeCapabilityMatrix]:
      mockControlCenterData.capabilityMatrix,
    [API_ENDPOINTS.setupAssistantSummary]:
      mockControlCenterData.macosSetupAssistant,
    [API_ENDPOINTS.providerSetupGuide]: mockControlCenterData.providerCatalog,
    [API_ENDPOINTS.controlCenterSettingsStatus]:
      mockControlCenterData.settingsStatus,
    [API_ENDPOINTS.controlCenterLocalModelsStatus]:
      mockControlCenterData.localModelsStatus,
    [API_ENDPOINTS.founderTodaySummary]: mockControlCenterData.founderToday,
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
