import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  within,
  waitFor,
} from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { App } from "./App";
import {
  API_ENDPOINTS,
  actionDecisionEndpoint,
  actionLocalTaskCommitEndpoint,
  chatTurnHandoffEndpoint,
  chatTurnReceiptEndpoint,
  isAllowedReadEndpoint,
  isPreviewEndpoint,
  memoryContextPackActionProposalEndpoint,
  memoryReviewDecisionEndpoint,
  memoryReviewReceiptEndpoint,
  READ_ENDPOINTS,
} from "./api/endpoints";
import {
  CONTROL_CENTER_READ_TIMEOUT_MS,
  fetchMemoryReviewDecisionReceipt,
  recordMemoryFeedback,
  recordMemoryReviewDecision,
  setLocalApiBearerForSession,
} from "./api/client";
import { EmptyState, ErrorState, LoadingState } from "./components/DataState";
import {
  MOCK_CONTROL_CENTER_ROUTE_COUNT,
  MOCK_OPENAPI_ROUTE_COUNT,
  mockControlCenterData,
} from "./mocks/controlCenterData";
import { primaryNavItems, supportingNavItems } from "./routes";

function mockFetchWithFallback() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      throw new Error("backend unavailable");
    }),
  );
}

function safeCostSuffix(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9_.@-]+/g, "-")
    .replace(/^-|-$/g, "");
}

function approvedActionCostFields(sourceRef: string) {
  const suffix = safeCostSuffix(sourceRef);
  const costReceiptRefs = [
    `budget-decision-ref:${suffix}`,
    `cost-estimate-ref:${suffix}`,
    "model-profile-ref:frontier-approved-test",
    "provider-ref:frontier-approved-test",
    `usage-capture-ref:${suffix}`,
  ];
  return {
    action_envelope_cost_contract_ref:
      "contract-ref:frontier-ai-cost-usage-telemetry:v1",
    action_envelope_estimated_cost_usd: 0,
    action_envelope_max_approved_cost_usd: 0,
    action_envelope_provider_ref: "provider-ref:frontier-approved-test",
    action_envelope_model_profile_ref:
      "model-profile-ref:frontier-approved-test",
    action_envelope_input_metered_units: 0,
    action_envelope_output_metered_units: 0,
    action_envelope_total_metered_units: 0,
    action_envelope_cost_estimate_ref: `cost-estimate-ref:${suffix}`,
    action_envelope_captured_usage_ref: `usage-capture-ref:${suffix}`,
    action_envelope_budget_decision_ref: `budget-decision-ref:${suffix}`,
    action_envelope_cost_receipt_refs: costReceiptRefs,
    action_envelope_cost_blocked_state_refs: [],
    action_envelope_cost_state_label: "Cost approved",
    action_envelope_provider_authority_state_label:
      "Provider/model refs present",
    action_envelope_unknown_paid_cost_requires_explicit_approval: true,
    action_envelope_frontier_usage_claimed: false,
  };
}

function founderLoopProductProofFixture(
  overrides: Record<string, unknown> = {},
) {
  const steps = [
    ["morning_briefing", "Morning Briefing", "/briefing"],
    ["today", "Today", "/today"],
    ["action_inbox", "Action Inbox", "/actions"],
    ["decision_receipt", "Receipt", "/actions"],
    ["evidence_timeline", "Evidence Timeline", "/evidence"],
    ["memory_review", "Memory Review", "/memory"],
    ["weekly_review", "Weekly Review", "/today"],
  ].map(([stepId, surface, route], index) => ({
    step_id: stepId,
    surface,
    backend_route_ref:
      stepId === "morning_briefing"
        ? "GET /control-center/morning-briefing/summary"
        : stepId === "action_inbox"
          ? "GET /control-center/actions/inbox"
          : stepId === "evidence_timeline"
            ? "GET /control-center/evidence/timeline"
            : "GET /control-center/today/summary",
    frontend_route_ref: route,
    status:
      stepId === "decision_receipt"
        ? "receipt_backed_decision_path_visible"
        : "backend_owned_read_model",
    safe_summary: `${surface} product proof step ${index + 1}.`,
    source_refs: [`source-ref:founder-loop-product-proof:${stepId}`],
    evidence_refs: [`evidence-ref:founder-loop-product-proof:${stepId}`],
    receipt_refs:
      stepId === "decision_receipt"
        ? ["receipt:founder-loop-product-proof:action-defer"]
        : [],
    blocked_state_refs: [
      "blocked-state:founder-loop-proof-no-production-authority",
    ],
    next_safe_action: "Inspect backend-owned safe refs before promotion.",
  }));
  const productizedSurfaceBindings = [
    ["start_here", "Start Here", "/start", "GET /control-center/start-here/summary"],
    ["today", "Today", "/today", "GET /control-center/today/summary"],
    ["action_inbox", "Action Inbox", "/actions", "GET /control-center/actions/inbox"],
    ["proof", "Proof", "/proof", "GET /control-center/proof/index"],
    ["evidence", "Evidence", "/evidence", "GET /control-center/evidence/timeline"],
    ["memory", "Memory", "/memory", "GET /control-center/memory/review"],
    ["trust", "Trust", "/trust", "GET /control-center/trust-authority/matrix"],
    ["settings", "Settings", "/settings", "GET /control-center/settings/status"],
  ].map(([surfaceId, surface, route, backendRoute]) => ({
    surface_id: surfaceId,
    surface,
    frontend_route_ref: route,
    backend_route_ref: backendRoute,
    status: "backend_owned_productized_surface",
    product_posture: "daily_loop_productized",
    safe_summary: `${surface} shares backend-owned daily loop refs.`,
    shared_ref: "founder-loop-state-ref:demo-safe-seeded-loop",
    primary_proof_ref: "proof-ref:founder-loop-v1:governed-local-loop",
    source_refs: [`source-ref:founder-loop-productized:${surfaceId}`],
    receipt_refs:
      surfaceId === "action_inbox"
        ? ["receipt:founder-loop-product-proof:action-defer"]
        : [],
    evidence_refs: [`evidence-ref:founder-loop-productized:${surfaceId}`],
    memory_candidate_refs:
      surfaceId === "memory"
        ? ["business-memory-candidate:founder-loop-preferences"]
        : [],
    blocked_state_refs: [
      "blocked-state:founder-loop-proof-no-production-authority",
    ],
    next_safe_action: "Use the shared backend refs before promotion.",
  }));
  return {
    schema_version: "founder-loop-v1-product-proof.v1",
    contract_ref: "contract-ref:founder-loop-v1-product-proof:v1",
    status: "implemented_backend_owned_product_proof_pass_safe_refs_only",
    source: "python_core_founder_loop_v1_product_proof_read_model",
    backend_owned: true,
    local_read_model_only: true,
    seeded_demo_safe: true,
    safe_refs_only: true,
    safe_summary_only: true,
    raw_content_included: false,
    scenario_ref: "scenario-ref:founder-loop-v1-demo-safe-seeded-loop",
    shared_state_ref: "founder-loop-state-ref:demo-safe-seeded-loop",
    full_strength_goal:
      "Start Here, Today, Action Inbox, Proof, Evidence, Memory, Trust, and Settings operate as one local-first governed daily loop.",
    repo_safe_scope:
      "Backend-owned safe refs, read-only route posture, visual cohesion, mock fallback labels, and CLI inspection only.",
    blocked_authority_summary:
      "Provider/model calls, connector writes/sends, browser work, shell subprocess work, background autonomy, public release claims, and production authority remain blocked.",
    exact_promotion_path_refs: [
      "promotion-path-ref:daily-loop-productization:shared-backend-refs",
      "promotion-path-ref:daily-loop-productization:route-proof-cohesion",
      "promotion-path-ref:daily-loop-productization:receipt-evidence-memory-binding",
      "promotion-path-ref:daily-loop-productization:approved-mutation-lanes-only",
    ],
    productized_surface_order: [
      "start_here",
      "today",
      "action_inbox",
      "proof",
      "evidence",
      "memory",
      "trust",
      "settings",
    ],
    productized_surface_count: productizedSurfaceBindings.length,
    productized_surface_bindings: productizedSurfaceBindings,
    productized_route_refs: productizedSurfaceBindings.map(
      (binding) => binding.frontend_route_ref,
    ),
    productized_backend_route_refs: productizedSurfaceBindings.map(
      (binding) => binding.backend_route_ref,
    ),
    loop_order: [
      "morning_briefing",
      "today",
      "action_inbox",
      "decision_receipt",
      "evidence_timeline",
      "memory_review",
      "weekly_review",
    ],
    steps,
    supported_decision_actions: ["approve", "edit", "reject", "defer"],
    morning_briefing_refs: ["briefing:storage-state-first-loop"],
    today_refs: ["daily-loop-summary:local"],
    action_inbox_refs: ["founder-action:setup-assistant-hardening"],
    action_decision_receipt_refs: [
      "receipt:founder-loop-product-proof:action-defer",
    ],
    evidence_timeline_refs: [
      "evidence-timeline:action/founder-action/setup-assistant-hardening",
    ],
    evidence_event_refs: ["evidence-event:action-decision-recorded-test"],
    memory_review_candidate_refs: [
      "business-memory-candidate:founder-loop-preferences",
    ],
    memory_review_receipt_refs: [
      "receipt:founder-loop-product-proof:memory-defer",
    ],
    weekly_review_refs: ["review-period-ref:local-weekly-window"],
    receipt_refs: [
      "receipt:founder-loop-product-proof:action-defer",
      "receipt:founder-loop-product-proof:memory-defer",
    ],
    evidence_refs: ["evidence-ref:founder-loop-v1-product-proof"],
    blocked_authority_refs: [
      "blocked-state:founder-loop-proof-no-provider-model-call",
      "blocked-state:founder-loop-proof-no-a2a-mcp-runtime-dispatch",
      "blocked-state:founder-loop-proof-no-browser-or-live-web",
      "blocked-state:founder-loop-proof-no-connector-write",
      "blocked-state:founder-loop-proof-no-email-calendar-send",
      "blocked-state:founder-loop-proof-no-crm-write-or-account-sync",
      "blocked-state:founder-loop-proof-no-shell-execution",
      "blocked-state:founder-loop-proof-no-background-autonomy",
      "blocked-state:founder-loop-proof-no-react-only-authority",
      "blocked-state:founder-loop-proof-no-public-release-claim",
      "blocked-state:founder-loop-proof-no-production-authority",
    ],
    memory_review_status: "candidate_available",
    weekly_review_status: "implemented_backend_owned_weekly_review_artifact_v1",
    decision_receipt_status: "receipt_backed_decision_path_visible",
    safe_summary:
      "Founder Loop V1 product proof binds Morning Briefing, Today, Action Inbox decisions, receipts, Evidence Timeline, Memory Review, and Weekly Review through backend-owned safe refs.",
    next_safe_action:
      "Inspect shared safe refs before claiming more authority.",
    authority_boundary:
      "Founder Loop V1 product proof is backend-owned local read model authority only.",
    provider_model_call_enabled: false,
    runtime_model_call_enabled: false,
    a2a_runtime_dispatch_enabled: false,
    mcp_runtime_dispatch_enabled: false,
    browser_execution_enabled: false,
    live_web_enabled: false,
    connector_write_enabled: false,
    email_calendar_send_enabled: false,
    crm_write_enabled: false,
    account_sync_enabled: false,
    shell_subprocess_execution_enabled: false,
    background_autonomy_enabled: false,
    memory_write_authorized: false,
    context_injection_authorized: false,
    public_beta_claim_enabled: false,
    public_release_claim_enabled: false,
    production_authority_enabled: false,
    ...overrides,
  };
}

function founderLoopRunsIntegrationFixture(
  overrides: Record<string, unknown> = {},
) {
  const surfaceOrder = [
    "morning_briefing",
    "today",
    "action_inbox",
    "decision_receipt",
    "evidence_timeline",
    "memory_review",
    "weekly_review",
  ];
  const surfaceLabels: Record<string, string> = {
    morning_briefing: "Morning Briefing",
    today: "Today",
    action_inbox: "Action Inbox",
    decision_receipt: "Decision Receipt",
    evidence_timeline: "Evidence Timeline",
    memory_review: "Memory Review",
    weekly_review: "Weekly Review",
  };
  const surfaceRoutes: Record<string, string> = {
    morning_briefing: "/briefing",
    today: "/today",
    action_inbox: "/actions",
    decision_receipt: "/actions",
    evidence_timeline: "/evidence",
    memory_review: "/memory",
    weekly_review: "/today",
  };
  const bindings = surfaceOrder.map((surfaceId) => ({
    surface_id: surfaceId,
    surface: surfaceLabels[surfaceId],
    status: "backend_owned_run_ref_projection",
    frontend_route_ref: surfaceRoutes[surfaceId],
    backend_route_ref:
      surfaceId === "morning_briefing"
        ? "GET /control-center/morning-briefing/summary"
        : surfaceId === "action_inbox"
          ? "GET /control-center/actions/inbox"
          : surfaceId === "evidence_timeline"
            ? "GET /control-center/evidence/timeline"
            : surfaceId === "memory_review"
              ? "GET /control-center/memory/review"
              : "GET /control-center/today/summary",
    run_ref: "run-ref:founder-loop-v1:governed-local-loop",
    proof_ref: `proof-ref:founder-loop-v1:${surfaceId}`,
    proof_detail_ref: `proof-detail-ref:founder-loop-v1:${surfaceId}`,
    proof_detail_route_ref: "proof-detail-route:planned-universal-proof",
    action_source_refs:
      surfaceId === "action_inbox" || surfaceId === "decision_receipt"
        ? ["founder-action:setup-assistant-hardening"]
        : [],
    approval_refs:
      surfaceId === "action_inbox"
        ? ["approval-envelope:founder-loop:setup-assistant-hardening"]
        : [],
    receipt_refs:
      surfaceId === "decision_receipt" || surfaceId === "memory_review"
        ? ["receipt:founder-loop-runs:decision"]
        : [],
    evidence_refs: [
      `proof-ref:founder-loop-v1:${surfaceId}`,
      "evidence-ref:founder-loop-runs-integration",
    ],
    evidence_event_refs:
      surfaceId === "evidence_timeline"
        ? ["evidence-event:action-decision-recorded-test"]
        : [],
    memory_candidate_refs:
      surfaceId === "memory_review"
        ? ["business-memory-candidate:founder-loop-preferences"]
        : [],
    operator_run_event_refs: [
      "operator-run-event:evidence-event-action-decision-recorded-test",
    ],
    blocked_state_refs: [
      "blocked-state:founder-loop-runs-no-production-authority",
    ],
    safe_summary: `${surfaceLabels[surfaceId]} is tied to backend-owned run and proof refs.`,
    next_safe_action:
      "Inspect run and proof refs before claiming this surface outcome.",
  }));
  return {
    schema_version: "founder-loop-runs-integration.v1",
    contract_ref: "contract-ref:founder-loop-runs-integration:v1",
    status: "implemented_backend_owned_run_proof_refs_safe_refs_only",
    source: "python_core_founder_loop_runs_integration_read_model",
    backend_owned: true,
    local_read_model_only: true,
    safe_refs_only: true,
    redacted_summaries_only: true,
    raw_payloads_persisted: false,
    ui_truth_source: "python_core_read_model",
    primary_run_ref: "run-ref:founder-loop-v1:governed-local-loop",
    primary_proof_ref: "proof-ref:founder-loop-v1:governed-local-loop",
    surface_order: surfaceOrder,
    surface_count: surfaceOrder.length,
    run_refs: ["run-ref:founder-loop-v1:governed-local-loop"],
    proof_refs: [
      "proof-ref:founder-loop-v1:governed-local-loop",
      ...surfaceOrder.map((surfaceId) => `proof-ref:founder-loop-v1:${surfaceId}`),
    ],
    proof_detail_refs: surfaceOrder.map(
      (surfaceId) => `proof-detail-ref:founder-loop-v1:${surfaceId}`,
    ),
    action_source_refs: ["founder-action:setup-assistant-hardening"],
    approval_refs: ["approval-envelope:founder-loop:setup-assistant-hardening"],
    receipt_refs: ["receipt:founder-loop-runs:decision"],
    evidence_refs: [
      "proof-ref:founder-loop-v1:governed-local-loop",
      "evidence-ref:founder-loop-runs-integration",
    ],
    evidence_event_refs: ["evidence-event:action-decision-recorded-test"],
    memory_candidate_refs: [
      "business-memory-candidate:founder-loop-preferences",
    ],
    operator_run_event_refs: [
      "operator-run-event:evidence-event-action-decision-recorded-test",
    ],
    blocked_authority_refs: [
      "blocked-state:founder-loop-runs-no-provider-model-call",
      "blocked-state:founder-loop-runs-no-connector-write",
      "blocked-state:founder-loop-runs-no-browser-or-live-web",
      "blocked-state:founder-loop-runs-no-shell-execution",
      "blocked-state:founder-loop-runs-no-background-autonomy",
      "blocked-state:founder-loop-runs-no-ui-only-truth",
      "blocked-state:founder-loop-runs-no-memory-write-authority",
      "blocked-state:founder-loop-runs-no-context-injection",
      "blocked-state:founder-loop-runs-no-production-authority",
    ],
    surface_bindings: bindings,
    action_origin_posture:
      "action_refs_are_bound_to_the_shared_founder_loop_run_ref",
    decision_receipt_posture:
      "decisions_are_explained_by_backend_receipt_refs_or_explicit_none",
    evidence_path_posture:
      "state_is_supported_by_safe_evidence_refs_and_operator_run_event_refs",
    proof_detail_posture:
      "proof_refs_available_dedicated_universal_proof_route_not_present",
    memory_candidate_posture: "memory_candidate_refs_visible",
    weekly_review_posture:
      "weekly_review_summarizes_same_loop_state_from_safe_refs",
    authority_boundary:
      "Founder Loop runs integration is backend-owned local safe-ref provenance only.",
    next_safe_action:
      "Inspect run, proof, receipt, evidence, and blocker refs before claiming a Founder Loop outcome.",
    provider_model_call_enabled: false,
    runtime_model_call_enabled: false,
    connector_write_enabled: false,
    connector_send_enabled: false,
    browser_execution_enabled: false,
    live_web_enabled: false,
    shell_subprocess_execution_enabled: false,
    scheduler_enabled: false,
    background_autonomy_enabled: false,
    action_execution_enabled: false,
    approval_authority_enabled: false,
    memory_write_authorized: false,
    context_injection_authorized: false,
    ui_mutation_authority_enabled: false,
    production_authority_enabled: false,
    ...overrides,
  };
}

function unifiedWorkThreadFixture(overrides: Record<string, unknown> = {}) {
  const steps = [
    ["chat_handoff", "Chat", "/chat"],
    ["plan", "Plans", "/plans"],
    ["action", "Action Inbox", "/actions"],
    ["decision_receipt", "Receipt", "/actions"],
    ["evidence", "Evidence", "/evidence"],
    ["memory_review", "Memory Review", "/memory"],
    ["weekly_review", "Weekly Review", "/today"],
  ].map(([stepId, surface, route], index) => ({
    step_id: stepId,
    surface,
    frontend_route_ref: route,
    backend_route_ref:
      stepId === "action"
        ? "GET /control-center/actions/inbox"
        : stepId === "evidence"
          ? "GET /control-center/evidence/timeline"
          : stepId === "memory_review"
            ? "GET /control-center/memory/review"
            : "GET /control-center/today/summary",
    status:
      stepId === "decision_receipt"
        ? "decision_receipts_visible"
        : "backend_owned_read_model",
    safe_summary: `${surface} unified work thread step ${index + 1}.`,
    source_refs: [`source-ref:unified-work-thread:${stepId}`],
    proposal_refs:
      stepId === "plan" ? ["plan-proposal-ref:unified-work-thread"] : [],
    receipt_refs:
      stepId === "decision_receipt"
        ? ["receipt:unified-work-thread:action-defer"]
        : [],
    evidence_refs: [`evidence-ref:unified-work-thread:${stepId}`],
    blocked_authority_refs: [
      "blocked-state:unified-work-thread-no-production-authority",
    ],
    next_safe_action: "Inspect backend-owned safe refs before promotion.",
  }));
  return {
    schema_version: "fcc-thread-001-unified-work-thread.v1",
    contract_ref: "contract-ref:fcc-thread-001-unified-work-thread:v1",
    status: "implemented_backend_owned_read_model_safe_refs_only",
    source: "python_core_unified_work_thread_read_model",
    backend_owned: true,
    local_read_model_only: true,
    seeded_demo_safe: true,
    safe_refs_only: true,
    safe_summary_only: true,
    raw_content_included: false,
    thread_ref: "work-thread-ref:founder-loop:demo-safe-seeded-loop",
    thread_title: "Unified Founder Loop work thread",
    step_order: [
      "chat_handoff",
      "plan",
      "action",
      "decision_receipt",
      "evidence",
      "memory_review",
      "weekly_review",
    ],
    steps,
    chat_turn_receipt_refs: ["receipt:unified-work-thread:chat-turn"],
    chat_handoff_receipt_refs: ["receipt:unified-work-thread:chat-handoff"],
    plan_refs: ["plan-ref:unified-work-thread"],
    plan_proposal_refs: ["plan-proposal-ref:unified-work-thread"],
    action_refs: ["founder-action:setup-assistant-hardening"],
    action_decision_receipt_refs: ["receipt:unified-work-thread:action-defer"],
    evidence_timeline_refs: [
      "evidence-timeline:action/founder-action/setup-assistant-hardening",
    ],
    evidence_event_refs: ["evidence-event:unified-work-thread:action-defer"],
    memory_review_candidate_refs: [
      "business-memory-candidate:founder-loop-preferences",
    ],
    memory_review_receipt_refs: ["receipt:unified-work-thread:memory-defer"],
    weekly_review_refs: ["review-period-ref:local-weekly-window"],
    receipt_refs: [
      "receipt:unified-work-thread:chat-turn",
      "receipt:unified-work-thread:chat-handoff",
      "receipt:unified-work-thread:action-defer",
      "receipt:unified-work-thread:memory-defer",
    ],
    evidence_refs: ["evidence-ref:fcc-thread-001-unified-work-thread"],
    blocked_authority_refs: [
      "blocked-state:unified-work-thread-no-action-execution",
      "blocked-state:unified-work-thread-no-provider-model-call",
      "blocked-state:unified-work-thread-no-a2a-mcp-runtime-dispatch",
      "blocked-state:unified-work-thread-no-browser-live-web",
      "blocked-state:unified-work-thread-no-connector-read-write",
      "blocked-state:unified-work-thread-no-email-calendar-send",
      "blocked-state:unified-work-thread-no-crm-write-or-account-sync",
      "blocked-state:unified-work-thread-no-shell-subprocess",
      "blocked-state:unified-work-thread-no-memory-write",
      "blocked-state:unified-work-thread-no-context-injection",
      "blocked-state:unified-work-thread-no-background-autonomy",
      "blocked-state:unified-work-thread-no-public-beta-claim",
      "blocked-state:unified-work-thread-no-public-release-claim",
      "blocked-state:unified-work-thread-no-production-authority",
    ],
    safe_summary:
      "Unified Work Thread links Chat handoff, Plan, Action, receipt, Evidence, Memory Review, and Weekly Review refs into one backend-owned read model.",
    next_safe_action:
      "Inspect the safe refs across the thread before promoting any new authority or product-readiness claim.",
    authority_boundary:
      "Unified Work Thread is read-only local Founder Loop state and grants no execution authority.",
    provider_model_call_enabled: false,
    runtime_model_call_enabled: false,
    a2a_runtime_dispatch_enabled: false,
    mcp_runtime_dispatch_enabled: false,
    browser_execution_enabled: false,
    live_web_enabled: false,
    connector_read_enabled: false,
    connector_write_enabled: false,
    email_calendar_send_enabled: false,
    crm_write_enabled: false,
    account_sync_enabled: false,
    shell_subprocess_execution_enabled: false,
    background_autonomy_enabled: false,
    memory_write_authorized: false,
    context_injection_authorized: false,
    action_execution_enabled: false,
    public_beta_claim_enabled: false,
    public_release_claim_enabled: false,
    production_authority_enabled: false,
    ...overrides,
  };
}

function stubFounderTodayReadEndpoint(today: unknown) {
  const fetchMock = vi.fn(async (url: string) => {
    const urlText = String(url);
    if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
      return new Response(JSON.stringify({ ok: true, result: today }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
      return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
    throw new Error(`unexpected request ${urlText}`);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function stubReadEndpointsWithHungEndpoint(hungEndpoint: string) {
  const fetchMock = vi.fn((url: string) => {
    const urlText = String(url);
    if (urlText.endsWith(hungEndpoint)) {
      return new Promise<Response>(() => {
        // Intentionally unresolved: exercises the bounded read timeout path.
      });
    }
    if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
      return Promise.resolve(
        new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }
    throw new Error(`unexpected request ${urlText}`);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function stubReadEndpointOverrides(overrides: Record<string, unknown>) {
  const fetchMock = vi.fn(async (url: string) => {
    const urlText = String(url);
    const endpoint = READ_ENDPOINTS.find((candidate) =>
      urlText.endsWith(candidate),
    );
    if (!endpoint) {
      throw new Error(`unexpected request ${urlText}`);
    }
    const override = overrides[endpoint];
    if (override !== undefined) {
      return new Response(JSON.stringify({ ok: true, result: override }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
    return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

async function advanceControlCenterReadTimeout() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(CONTROL_CENTER_READ_TIMEOUT_MS + 1);
  });
}

function applyApprovedActionCost(item: {
  item_ref: string;
  approval_envelope?: Record<string, unknown>;
  [key: string]: unknown;
}) {
  const fields = approvedActionCostFields(item.item_ref);
  Object.assign(item, fields);
  if (item.approval_envelope) {
    Object.assign(item.approval_envelope, {
      estimated_cost_usd: fields.action_envelope_estimated_cost_usd,
      max_approved_cost_usd: fields.action_envelope_max_approved_cost_usd,
      provider_ref: fields.action_envelope_provider_ref,
      model_profile_ref: fields.action_envelope_model_profile_ref,
      input_metered_units: fields.action_envelope_input_metered_units,
      output_metered_units: fields.action_envelope_output_metered_units,
      total_metered_units: fields.action_envelope_total_metered_units,
      cost_estimate_ref: fields.action_envelope_cost_estimate_ref,
      captured_usage_ref: fields.action_envelope_captured_usage_ref,
      budget_decision_ref: fields.action_envelope_budget_decision_ref,
      cost_receipt_refs: fields.action_envelope_cost_receipt_refs,
      cost_blocked_state_refs: fields.action_envelope_cost_blocked_state_refs,
      cost_state_label: fields.action_envelope_cost_state_label,
      provider_authority_state_label:
        fields.action_envelope_provider_authority_state_label,
      unknown_paid_cost_requires_explicit_approval:
        fields.action_envelope_unknown_paid_cost_requires_explicit_approval,
      frontier_usage_claimed: fields.action_envelope_frontier_usage_claimed,
    });
  }
}

function plansToActionsBridgeFixture(overrides: Record<string, unknown> = {}) {
  const item = {
    item_ref: "plans-to-actions-bridge:plan-summary-test",
    source_plan_ref: "plan-summary:test",
    linked_action_item_ref: "action:task-decomposition:test",
    plan_title: "Founder Loop test plan",
    plan_status: "proposal_only_review_required",
    safe_summary:
      "Plan proposal maps to a reviewable Action envelope with refs only.",
    why_proposed: "The plan needs review before scoped work exists.",
    risk_class: "medium",
    action_envelope_ref: "action-envelope:plans:plan-summary-test",
    action_scope_ref: "scope-ref:plans-action-envelope:plan-summary-test",
    approval_requirement_ref:
      "approval-requirement:plans-action-envelope:plan-summary-test",
    task_decomposition_proposal_ref: "task-decomposition-proposal:test",
    task_decomposition_review_envelope_ref:
      "review-envelope:task-decomposition:test",
    task_decomposition_action_inbox_bridge_ref:
      "action-inbox-proposal:task-decomposition:test",
    review_receipt_labels: ["approve", "edit", "reject", "defer"],
    expected_receipt_refs: [
      "receipt-plan:plans-action-envelope:plan-summary-test",
    ],
    receipt_refs: [],
    rollback_ref: "rollback-plan:plans-action-envelope:plan-summary-test",
    safe_disable_ref: "safe-disable:plans-action-envelope:plan-summary-test",
    evidence_refs: ["evidence-ref:founder-loop:test-plan"],
    step_refs: ["task-decomposition-step:test-1"],
    risk_refs: ["risk-ref:task-decomposition:test"],
    ambiguity_refs: [],
    missing_evidence_refs: ["missing-evidence-ref:task-decomposition:test"],
    blocked_authority_refs: [
      "blocked-state:plans-to-actions-proposal-only",
      "blocked-state:plans-to-actions-approval-refs-identifiers-only",
      "blocked-state:plans-to-actions-no-action-execution",
      "blocked-state:plans-to-actions-no-tool-execution",
      "blocked-state:plans-to-actions-no-workflow-execution",
      "blocked-state:plans-to-actions-no-model-provider-call",
      "blocked-state:plans-to-actions-no-shell-subprocess",
      "blocked-state:plans-to-actions-no-browser-execution",
      "blocked-state:plans-to-actions-no-connector-runtime",
      "blocked-state:plans-to-actions-no-connector-write",
      "blocked-state:plans-to-actions-no-memory-write",
      "blocked-state:plans-to-actions-no-context-injection",
      "blocked-state:plans-to-actions-no-production-authority",
    ],
    next_safe_action: "Review refs only.",
    backend_owned: true,
    review_only: true,
    proposal_only: true,
    exact_scope_required: true,
    expected_receipts_required: true,
    rollback_required: true,
    safe_disable_required: true,
    safe_refs_only: true,
    raw_content_included: false,
    approval_ref_authority: false,
    approval_grant_capture_enabled: false,
    approval_alone_executes: false,
    execution_authorized: false,
    execution_performed: false,
    action_execution_enabled: false,
    action_execution_performed: false,
    tool_execution_enabled: false,
    tool_execution_performed: false,
    workflow_execution_enabled: false,
    workflow_execution_performed: false,
    model_provider_call_enabled: false,
    model_provider_authority_allowed: false,
    provider_model_call_enabled: false,
    shell_subprocess_execution_enabled: false,
    shell_subprocess_execution_performed: false,
    browser_execution_enabled: false,
    browser_execution_performed: false,
    connector_runtime_enabled: false,
    connector_write_enabled: false,
    connector_write_performed: false,
    memory_write_authorized: false,
    memory_write_performed: false,
    context_injection_authorized: false,
    context_injection_performed: false,
    automatic_planning_authority_enabled: false,
    production_authority_enabled: false,
  };
  return {
    schema_version: "product-loop-006-plans-to-actions.v1",
    contract_ref:
      "contract-ref:product-loop-006-plans-to-reviewable-action-envelopes:v1",
    status: "implemented_backend_owned_review_envelope_bridge",
    source: "python_core_plans_to_actions_bridge_read_model",
    backend_owned: true,
    local_read_model_only: true,
    safe_refs_only: true,
    raw_content_included: false,
    item_count: 1,
    items: [item],
    plan_refs: ["plan-summary:test"],
    action_inbox_item_refs: ["action:task-decomposition:test"],
    task_decomposition_proposal_refs: ["task-decomposition-proposal:test"],
    expected_receipt_refs: [
      "receipt-plan:plans-action-envelope:plan-summary-test",
    ],
    rollback_refs: ["rollback-plan:plans-action-envelope:plan-summary-test"],
    safe_disable_refs: ["safe-disable:plans-action-envelope:plan-summary-test"],
    blocked_state_refs: item.blocked_authority_refs,
    next_safe_action: "Review refs only.",
    authority_boundary:
      "Plans-to-Actions bridge is review metadata only; approval refs remain identifiers.",
    approval_ref_authority: false,
    approval_grant_capture_enabled: false,
    approval_alone_executes: false,
    execution_authorized: false,
    execution_performed: false,
    action_execution_enabled: false,
    action_execution_performed: false,
    tool_execution_enabled: false,
    tool_execution_performed: false,
    workflow_execution_enabled: false,
    workflow_execution_performed: false,
    model_provider_call_enabled: false,
    model_provider_authority_allowed: false,
    provider_model_call_enabled: false,
    shell_subprocess_execution_enabled: false,
    shell_subprocess_execution_performed: false,
    browser_execution_enabled: false,
    browser_execution_performed: false,
    connector_runtime_enabled: false,
    connector_write_enabled: false,
    connector_write_performed: false,
    memory_write_authorized: false,
    memory_write_performed: false,
    context_injection_authorized: false,
    context_injection_performed: false,
    automatic_planning_authority_enabled: false,
    production_authority_enabled: false,
    ...overrides,
  };
}

function actionDecisionLaneReadModelFixture(
  overrides: Record<string, unknown> = {},
) {
  const item = {
    item_ref: "founder-action:test-cost-blocked",
    lane_id: "cost_blocked",
    lane_label: "Cost blocked",
    title: "Cost posture review",
    status: "review_ready",
    priority: "high",
    action_kind: "local_task_create",
    side_effect_class: "local_dev_workspace_only",
    safe_summary: "Cost and provider refs must be reviewed first.",
    why_shown: "Cost blocked before approval.",
    next_safe_action: "Resolve cost estimate, budget decision, and receipt refs.",
    authority_boundary: "Approval alone does not execute work.",
    approval_required: true,
    approval_envelope_ref: "approval-envelope:test-cost-blocked",
    approval_envelope_status: "review_ready_exact_scope_required",
    approval_scope_ref: "scope-ref:test-cost-blocked",
    approval_requirement_ref: "approval-requirement:test-cost-blocked",
    expected_receipt_refs: ["receipt-plan:test-cost-blocked"],
    expected_receipt_state: "visible",
    evidence_refs: ["evidence-ref:test-cost-blocked"],
    receipt_refs: [],
    expected_receipt_refs_visible: true,
    rollback_ref: "rollback-ref:test-cost-blocked",
    safe_disable_ref: "safe-disable:test-cost-blocked",
    blocked_authority_refs: [
      "blocked-state:action-inbox-no-action-execution",
      "blocked-state:frontier-provider-model-ref-missing",
    ],
    missing_envelope_field_states: ["none"],
    cost_state_label: "Cost blocked",
    provider_authority_state_label: "No provider authority",
    estimated_cost_usd: 0,
    max_approved_cost_usd: 0,
    provider_ref: "provider-ref:not-invoked",
    model_profile_ref: "model-profile-ref:not-invoked",
    input_metered_units: 0,
    output_metered_units: 0,
    total_metered_units: 0,
    cost_estimate_ref: "cost-estimate-ref:test-cost-blocked",
    captured_usage_ref: "usage-capture-ref:test-cost-blocked",
    budget_decision_ref: "budget-decision-ref:test-cost-blocked",
    cost_receipt_refs: [
      "cost-estimate-ref:test-cost-blocked",
      "usage-capture-ref:test-cost-blocked",
      "budget-decision-ref:test-cost-blocked",
    ],
    cost_blocked_state_refs: [
      "blocked-state:frontier-provider-model-ref-missing",
    ],
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
  return {
    contract_ref: "contract-ref:action-inbox-decision-lanes:v1",
    status: "implemented_backend_owned_decision_lanes",
    source: "python_core_action_inbox_decision_lane_read_model",
    backend_owned: true,
    local_read_model_only: true,
    safe_refs_only: true,
    raw_content_included: false,
    lane_order: ["cost_blocked"],
    lanes: [
      {
        lane_id: "cost_blocked",
        label: "Cost blocked",
        status: "review_ready",
        safe_summary: "Cost posture blocks receipt capture.",
        count: 1,
        item_refs: [item.item_ref],
        blocked_state_refs: ["blocked-state:frontier-provider-model-ref-missing"],
        next_safe_action: "Resolve exact cost posture.",
        approval_alone_executes: false,
        action_execution_enabled: false,
      },
    ],
    items: [item],
    blocked_state_refs: ["blocked-state:action-inbox-no-action-execution"],
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
    ...overrides,
  };
}

function fusionWorkClassificationFixture(
  classification:
    | "judgment_required"
    | "mechanical"
    | "validation"
    | "bookkeeping"
    | "ambiguous"
    | "blocked",
) {
  const humanReviewRequired = [
    "judgment_required",
    "ambiguous",
    "blocked",
  ].includes(classification);
  return {
    schema_version: "fcc_fusion_work_classification.v1",
    contract_ref: "contract-ref:fcc-fusion-routing-delegation:v1",
    classification,
    reason_refs: [`classification-reason-ref:fusion:${classification}`],
    confidence_posture: "medium",
    ambiguity_posture: humanReviewRequired ? "ambiguous" : "clear",
    human_review_required: humanReviewRequired,
    blocked_authority_refs:
      classification === "blocked"
        ? ["blocked-state:fusion-no-model-provider-call"]
        : [],
    source_refs: [`source-ref:fusion:${classification}`],
    evidence_refs: [`evidence-ref:fusion:${classification}`],
    reviewed_at_ref: "review-state:not-reviewed",
    expiry_posture_ref: `expiry-posture:fusion:${classification}`,
    review_aid_only: true,
    execution_authorized: false,
    action_execution_enabled: false,
  };
}

function fusionCacheContextFixture() {
  return {
    schema_version: "fcc_fusion_cache_context_economics.v1",
    contract_ref: "contract-ref:fcc-fusion-routing-delegation:v1",
    context_budget_ref: "context-budget-ref:fusion:test",
    compaction_boundary_ref: "compaction-boundary-ref:fusion:test:not-executed",
    cache_miss_expected: false,
    cache_reuse_posture: "possible",
    reroute_reason: "none",
    estimated_context_cost_posture: "context-cost-posture:estimated-metadata-only",
    cache_or_context_blocker_refs: [],
    evidence_refs: ["evidence-ref:fusion-cache-context:test"],
    explanatory_posture_only: true,
    measured_provider_event: false,
    runtime_model_switch_performed: false,
  };
}

function fusionDelegationFixture(
  workClassification = fusionWorkClassificationFixture("mechanical"),
) {
  return {
    schema_version: "fcc_fusion_delegation_proposal.v1",
    contract_ref: "contract-ref:fcc-fusion-routing-delegation:v1",
    proposal_state: "proposed",
    proposed_delegate_kind: "validation_worker",
    delegate_scope_ref: "delegate-scope-ref:fusion:test",
    main_owner_responsibility_refs: [
      "main-owner-responsibility-ref:fusion:test:plan",
      "main-owner-responsibility-ref:fusion:test:final-review",
    ],
    delegated_work_refs: ["delegated-work-ref:fusion:test"],
    review_required_posture_ref: "review-required:main-owner-final-review",
    blocked_execution_refs: [
      "blocked-state:fusion-sidekick-worker-execution-not-scoped",
      "blocked-state:fusion-background-dispatch-not-scoped",
    ],
    expected_receipt_refs: ["receipt-plan:fusion-delegation:test"],
    rollback_safe_disable_posture_refs: [
      "rollback-posture-ref:fusion-delegation:test",
      "safe-disable-posture-ref:fusion-delegation:test",
    ],
    work_classification: workClassification,
    future_only: true,
    creates_approval_ref: false,
    creates_execution_ref: false,
    worker_execution_enabled: false,
    background_dispatch_enabled: false,
  };
}

function fusionRoutingReadModelFixture() {
  const classifications = [
    fusionWorkClassificationFixture("judgment_required"),
    fusionWorkClassificationFixture("mechanical"),
    fusionWorkClassificationFixture("validation"),
    fusionWorkClassificationFixture("ambiguous"),
    fusionWorkClassificationFixture("blocked"),
  ];
  return {
    schema_version: "fcc_fusion_routing_delegation.v1",
    contract_ref: "contract-ref:fcc-fusion-routing-delegation:v1",
    source: "python_core_fusion_routing_delegation_read_model",
    status: "implemented_backend_owned_readability_metadata_no_execution",
    backend_owned: true,
    safe_refs_only: true,
    raw_content_included: false,
    surfaces: ["Today", "Plans", "Actions", "Chat", "Evidence", "Code"],
    work_classifications: classifications,
    route_decisions: [
      {
        schema_version: "fcc_fusion_route_decision_visibility.v1",
        contract_ref: "contract-ref:fcc-fusion-routing-delegation:v1",
        status: "selected",
        selected_profile_ref: "model-profile-ref:local-preview",
        rejected_profile_refs: [],
        reason_codes: ["SELECTED_PROFILE"],
        privacy_posture_ref: "privacy-posture:metadata-only",
        cost_posture_ref: "cost-posture:preview-only",
        latency_posture_ref: "latency-posture:estimated-only",
        context_posture_ref: "context-posture:preview-only",
        approval_posture_ref: "approval-posture:not-required-for-preview",
        operator_summary:
          "Local preview route selected for metadata visibility only.",
        no_execution_performed: true,
        model_invocation_performed: false,
        provider_call_performed: false,
      },
      {
        schema_version: "fcc_fusion_route_decision_visibility.v1",
        contract_ref: "contract-ref:fcc-fusion-routing-delegation:v1",
        status: "rejected",
        selected_profile_ref: "model-profile-ref:none-selected",
        rejected_profile_refs: ["model-profile-ref:disabled"],
        reason_codes: ["PROFILE_DISABLED"],
        privacy_posture_ref: "privacy-posture:metadata-only",
        cost_posture_ref: "cost-posture:preview-only",
        latency_posture_ref: "latency-posture:not-measured",
        context_posture_ref: "context-posture:preview-only",
        approval_posture_ref: "approval-posture:not-authority",
        operator_summary: "Disabled profile rejected for preview readability.",
        no_execution_performed: true,
        model_invocation_performed: false,
        provider_call_performed: false,
      },
      {
        schema_version: "fcc_fusion_route_decision_visibility.v1",
        contract_ref: "contract-ref:fcc-fusion-routing-delegation:v1",
        status: "blocked",
        selected_profile_ref: "model-profile-ref:none-selected",
        rejected_profile_refs: ["model-profile-ref:cloud-paid"],
        reason_codes: ["UNKNOWN_PAID_COST_REQUIRES_APPROVAL"],
        privacy_posture_ref: "privacy-posture:cloud-review-required",
        cost_posture_ref: "cost-posture:unknown-paid-cost-blocked",
        latency_posture_ref: "latency-posture:not-measured",
        context_posture_ref: "context-posture:not-expanded",
        approval_posture_ref: "approval-posture:required",
        operator_summary: "Paid route blocked until exact approval exists.",
        no_execution_performed: true,
        model_invocation_performed: false,
        provider_call_performed: false,
      },
    ],
    delegation_proposals: [
      fusionDelegationFixture(fusionWorkClassificationFixture("validation")),
    ],
    cache_context_economics: [fusionCacheContextFixture()],
    dogfood_records: [
      {
        schema_version: "fcc_fusion_dogfood_evidence.v1",
        contract_ref: "contract-ref:fcc-fusion-routing-delegation:v1",
        review_record_ref: "dogfood-review-ref:fusion:test",
        outcome: "partially_useful",
        friction_delta_ref: "dogfood-delta-ref:fusion:test:operator-friction",
        review_time_delta_ref: "dogfood-delta-ref:fusion:test:review-time",
        cost_confusion_delta_ref: "dogfood-delta-ref:fusion:test:cost-confusion",
        routing_cost_delta_ref: "dogfood-delta-ref:fusion:test:routing-cost",
        ambiguity_delta_ref: "dogfood-delta-ref:fusion:test:ambiguity",
        interruption_delta_ref: "dogfood-delta-ref:fusion:test:interruptions",
        redacted_summary_ref: "redacted-summary-ref:fusion-dogfood:test",
        evidence_refs: ["evidence-ref:fusion-dogfood:test"],
        local_private_only: true,
        external_analytics_enabled: false,
        live_learning_claimed: false,
      },
    ],
    blocked_state_refs: [
      "blocked-state:fusion-no-model-provider-call",
      "blocked-state:fusion-no-sidekick-execution",
      "blocked-state:fusion-no-action-execution",
      "blocked-state:fusion-no-tool-execution",
      "blocked-state:fusion-no-background-work",
    ],
    next_safe_action:
      "Use classification, route, delegation, and context/cost fields as review aids only.",
    authority_boundary:
      "Fusion routing and delegation metadata improves review readability; it does not authorize runtime work.",
    action_execution_enabled: false,
    sidekick_execution_enabled: false,
    provider_model_call_enabled: false,
    shell_subprocess_execution_enabled: false,
    browser_execution_enabled: false,
    connector_write_enabled: false,
    memory_write_authorized: false,
    context_injection_authorized: false,
    background_dispatch_enabled: false,
    production_authority_enabled: false,
  };
}

describe("Web Control Center shell", () => {
  it("renders mock dashboard summaries without production authority", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/dashboard");
    render(<App />);

    expect(await screen.findByText("Mock fallback active")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Backend unavailable; showing non-authoritative mock fallback data/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/API base: relative local API/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Overview" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Today" })).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Source Inbox" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Action Inbox" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Setup" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Runtime" })).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Foundation Gate" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "API Routes" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Action Preview" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Runtime readiness")).toBeInTheDocument();
    expect(screen.getByText("API boundary")).toBeInTheDocument();
    expect(screen.getByText(/No generic execution/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Local task authority requires backend approval/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Mock fallback; non-authoritative/i),
    ).toBeInTheDocument();
    expect(screen.getByText("API boundary unverified")).toBeInTheDocument();
    expect(screen.getByText("Evidence refs unverified")).toBeInTheDocument();
    expect(screen.getByText("Sources blocked/status-only")).toBeInTheDocument();
    expect(screen.getByText("Kill-switch posture")).toBeInTheDocument();
    expect(screen.getByText("Unverified in fallback")).toBeInTheDocument();
    expect(screen.getAllByText("exact route proof").length).toBeGreaterThan(0);
    expect(screen.queryByText("Local loop active")).not.toBeInTheDocument();
    expect(screen.queryByText("API boundary stable")).not.toBeInTheDocument();
    expect(screen.queryByText("Evidence healthy")).not.toBeInTheDocument();
    expect(screen.queryByText("Sources 2 blocked")).not.toBeInTheDocument();
    expect(screen.queryByText("Kill-switch")).not.toBeInTheDocument();
    expect(screen.queryByText("Armed")).not.toBeInTheDocument();
    expect(screen.queryByText("ship")).not.toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: /find route or action/i }),
    );
    const palette = screen.getByRole("dialog", { name: /command palette/i });
    expect(
      within(palette).getAllByText(/exact route proof/i).length,
    ).toBeGreaterThan(0);
    expect(within(palette).queryByText("ship")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /execute/i }),
    ).not.toBeInTheDocument();
  });

  it("prioritizes the Founder Loop while keeping supporting routes reachable", async () => {
    expect(primaryNavItems.map((item) => item.label)).toEqual([
      "Start Here",
      "Today",
      "Source Inbox",
      "Plans",
      "Action Inbox",
      "Proof",
      "Trust",
      "Memory",
      "Evidence",
      "Settings",
    ]);
    expect(supportingNavItems.map((item) => item.label)).toEqual(
      expect.arrayContaining([
        "Setup",
        "Dashboard",
        "Operator Loop",
        "Trial Packet",
        "Runtime",
        "API Routes",
        "Differentiators",
        "Action Preview",
      ]),
    );

    mockFetchWithFallback();
    window.history.pushState({}, "", "/today");
    render(<App />);

    await screen.findByRole("heading", { name: /^Today$/i });
    const navigation = screen.getByLabelText(/Control Center navigation/i);
    const labels = within(navigation)
      .getAllByRole("link")
      .map((link) => link.getAttribute("aria-label"));
    expect(labels.slice(0, 10)).toEqual([
      "Start Here",
      "Today",
      "Source Inbox",
      "Plans",
      "Action Inbox",
      "Proof",
      "Trust",
      "Memory",
      "Evidence",
      "Settings",
    ]);
    expect(
      within(navigation).getByText("Supporting Surfaces"),
    ).toBeInTheDocument();
    expect(
      within(navigation).getByRole("link", { name: "Setup" }),
    ).toBeInTheDocument();
    expect(
      within(navigation).getByRole("link", { name: "API Routes" }),
    ).toBeInTheDocument();
    expect(
      within(navigation).getByRole("link", { name: "Differentiators" }),
    ).toBeInTheDocument();
    expect(within(navigation).getAllByText("partial").length).toBeGreaterThan(
      0,
    );
    expect(
      within(navigation).queryByText("blocked/planned"),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Product spine contract/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Founder daily loop/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/non-authoritative fallback shape/i),
    ).toBeInTheDocument();
    expect(screen.queryByText(/backend-bound loop/i)).not.toBeInTheDocument();
    const loopSpine = screen.getByLabelText("Founder daily loop modules");
    const loopLinks = within(loopSpine).getAllByRole("link");
    expect(loopLinks).toHaveLength(8);
    expect(loopLinks[0]).toHaveAttribute("aria-current", "page");
    for (const surface of [
      "Today",
      "Briefing",
      "Source Inbox",
      "Plans",
      "Action Inbox",
      "Memory",
      "Evidence",
      "Settings",
    ]) {
      expect(
        loopLinks.some((link) => link.textContent?.includes(surface)),
      ).toBe(true);
    }
    expect(
      loopLinks.some((link) => link.textContent?.includes("blocked")),
    ).toBe(true);
    expect(
      loopLinks.some((link) => link.textContent?.includes("receipt-backed")),
    ).toBe(true);
    expect(
      screen.getAllByText(/Local task authority requires backend approval/i)
        .length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/Connector writes blocked/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Production authority blocked/i),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:today-product-spine:v1").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Today decisions first/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("backend digest missing").length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByText(
        "contract-ref:product-loop-003-today-loop-tightening:v1",
      ),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("python_core_today_loop_read_model"),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/Execute and track/i)).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: /Scan: Today, Review, Changed, Influence, Blocked/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Daily loop command deck"),
    ).toBeInTheDocument();
    for (const question of [
      "What matters today",
      "What needs review",
      "What changed",
      "What memory/evidence is influencing the loop",
      "What is blocked or unsafe",
    ]) {
      expect(
        screen.getByRole("heading", { name: question }),
      ).toBeInTheDocument();
    }
    expect(screen.getAllByText("Why shown").length).toBeGreaterThan(0);
    expect(screen.getAllByText("What this affects").length).toBeGreaterThan(0);
    expect(screen.queryByText(/backend review refs/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^\d+ changed refs$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/backend blocker refs/i)).not.toBeInTheDocument();
    expect(
      screen.getByText(/Proposal-only refs stay review-only/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/No apply\/use\/execute control for proposals/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Memory recall is influence, not truth authority/i),
    ).toBeInTheDocument();
    expect(document.querySelector("pre")).toBeNull();
    for (const unsafeControl of [/^apply$/i, /^use$/i, /^execute$/i]) {
      expect(
        screen.queryByRole("button", { name: unsafeControl }),
      ).not.toBeInTheDocument();
    }
    expect(screen.queryByText("Mutation controls")).not.toBeInTheDocument();
    expect(
      screen.getByText("Loop visibility sufficient").nextElementSibling,
    ).toHaveTextContent("no");
    expect(
      screen.getByText("Standalone completion").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      screen.getByRole("heading", { name: /Today required signals/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("priorities")).toBeInTheDocument();
    expect(screen.getByText("stale_source_posture")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Daily command loop/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("Home").nextElementSibling).toHaveTextContent(
      "Morning Briefing",
    );
    expect(
      screen.getByRole("heading", { name: /Source readiness states/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Non-authoritative source readiness fallback from mock_fallback_non_authoritative/i,
      ),
    ).toBeInTheDocument();
    const sourcePosture = screen.getByLabelText("Source readiness posture");
    expect(
      within(sourcePosture).getByText("Backend owned").nextElementSibling,
    ).toHaveTextContent("no");
    expect(screen.getByText(/inbox: blocked/i)).toBeInTheDocument();
    expect(
      screen.getByText("Blocked sources").nextElementSibling,
    ).toHaveTextContent("1");
    expect(
      screen.getByText("Metadata-only sources").nextElementSibling,
    ).toHaveTextContent("3");
    expect(
      screen.getByText("Not configured sources").nextElementSibling,
    ).toHaveTextContent("1");
    expect(screen.getAllByText("metadata_only").length).toBeGreaterThan(0);
    expect(screen.getAllByText("not_configured").length).toBeGreaterThan(0);
    expect(screen.getAllByText("unavailable").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Review queue groups/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/crm_followups: 1; review_only/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /CRM-lite follow-ups/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/memory-to-loop binding marked a follow-up commitment/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Memory why shown/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(
        /Today shows this memory because it is a reviewed recall candidate/i,
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Dogfood capture/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Public beta claim").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      screen.getByRole("heading", { name: /Weekly Review narrative/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Weekly Review reads the daily loop as history/i)
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Plan\/action state/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Receipt/local-task controls").nextElementSibling,
    ).toHaveTextContent("receipt and exact local-task controls only");
    expect(
      screen.getAllByText("partial_backend_not_product_ready").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Memory-to-loop binding/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:memory-to-loop-binding:v1").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("Loop items").nextElementSibling).toHaveTextContent(
      "4",
    );
    expect(
      screen.getByText("Memory-derived actions").nextElementSibling,
    ).toHaveTextContent("1");
    expect(
      screen.getByText("Accepted recall").nextElementSibling,
    ).toHaveTextContent("display-only");
    expect(
      screen.getByRole("heading", { name: /Private beta-readiness gate/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:private-beta-readiness-gate:v1").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("Evidence packet").nextElementSibling,
    ).toHaveTextContent(
      "evidence-packet:private-beta-readiness:local-founder-loop",
    );
    expect(
      screen.getAllByText("Full-strength version")[0].nextElementSibling,
    ).toHaveTextContent("Local-first command center");
    expect(
      screen.getAllByText("Repo-safe version")[0].nextElementSibling,
    ).toHaveTextContent("Backend-owned safe-ref readiness metadata");
    expect(
      screen.getAllByText("Blocked / needs authority")[0].nextElementSibling,
    ).toHaveTextContent("Public beta");
    expect(
      screen.getByText("Product-loop trial").nextElementSibling,
    ).toHaveTextContent(
      "contract-ref:product-loop-012-private-product-loop-trial-script:v1",
    );
    expect(
      screen.getAllByRole("heading", { name: /Exact promotion path/i }).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "promotion-path-ref:private-beta:scoped-authority-prs",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("Public beta").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      screen.getByRole("heading", { name: /Beta-test criteria/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/CRM-Lite Follow-Ups: blocked/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Start Here: partial/i)).toBeInTheDocument();
    expect(screen.getByText(/Dogfood Live Loop: partial/i)).toBeInTheDocument();
    expect(
      screen.getAllByText("blocked-state:no-public-beta").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /User intent understanding/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:user-intent-understanding:v1").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("Low confidence").nextElementSibling,
    ).toHaveTextContent("asks user");
    expect(
      screen.getByText("Hidden authority").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      screen.getByText(/clarify_chat_to_plan_handoff: low confidence/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /resolve_conflicting_crm_follow_up: conflicting confidence/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("blocked-state:no-hidden-intent-authority").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Weekly CEO Review/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("weekly-review-ref:memory-to-loop-binding").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Memory loop states/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Action Inbox: follow_up_commitment/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "accepted-recall-ref:not-authorized:memory-review-founder-loop-preferences",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Action envelope contract/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:plans-action-envelope:v1").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("blocked-state:no-action-execution").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("Cost blocked").length).toBeGreaterThan(0);
    expect(screen.getAllByText("No provider authority").length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText("Unknown paid cost").length).toBeGreaterThan(0);
    expect(
      screen.getAllByRole("button", { name: /Record Action-envelope receipt/i })
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Module feed contract/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Chat: implemented_local_operator_surface_contract/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Code: implemented_governed_code_workbench_contract_apply_blocked/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Stale-source posture/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /approve|run|send|write|sync|execute/i,
      }),
    ).not.toBeInTheDocument();
  });

  it("renders backend-owned Operator Workspace Spine on Today without mutation controls", async () => {
    const today = cloneForTest(mockControlCenterData.founderToday);
    const workspaceSpine = {
      ...today.operator_workspace_spine_read_model!,
      source: "python_core_operator_workspace_spine_read_model" as const,
      backend_owned: true,
      status: "implemented_read_only_operator_workspace_spine",
    };
    today.operator_workspace_spine_contract_ref =
      "contract-ref:operator-workspace-spine:v1";
    today.operator_workspace_spine_status = workspaceSpine.status;
    today.operator_workspace_spine_read_model = workspaceSpine;
    stubFounderTodayReadEndpoint(today);
    window.history.pushState({}, "", "/today");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Today$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Operator Workspace Spine/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Repo work as safe refs: scope, proposal, preview, run evidence/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("python_core_operator_workspace_spine_read_model"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("proof-ref:operator-workspace-spine:read-model")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("git-posture-ref:operator-workspace:mock-read-only")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "blocked-state:operator-workspace:no-git-mutation",
      ).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("blocked").length).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", {
        name: /git commit|commit changes|push branch|pull branch|checkout branch|merge branch|rebase branch|create pr|apply patch|rollback patch|run command|execute command|open terminal|dispatch coworker|schedule worker|stream logs|cancel run|resume run/i,
      }),
    ).not.toBeInTheDocument();
  });

  it("renders Start Here as a backend-owned loop guide without runtime controls", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/start");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Start Here$/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/mock fallback/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText("local_loop_unverified_mock_fallback"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("action-envelope:mock-fallback:start-here"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("blocked-state:start-here:no-runtime-execution"),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /approve|run|send|write|sync|execute/i,
      }),
    ).not.toBeInTheDocument();
  });

  it("renders Proof Detail as a read-only proof index without runtime controls", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/proof");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Proof Detail$/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/mock fallback/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("proof-ref:mock-fallback:daily-loop").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("blocked-state:proof-detail:no-runtime-execution")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "mock_control_center_proof_run_detail_non_authoritative",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", {
        name: /approve|run|send|write|sync|execute/i,
      }),
    ).not.toBeInTheDocument();
  });

  it("renders backend-owned Web Evidence proof slice on the Proof route", async () => {
    const baseProofIndex = backendOwnedProofIndexFixture();
    const webRecord = {
      ...baseProofIndex.records[0],
      proof_ref: "proof-ref:web-evidence:product-slice",
      proof_kind: "web_evidence",
      status: "implemented_route_ready_no_web_evidence_attached",
      title: "Web Evidence",
      safe_summary:
        "The web evidence product slice route is ready, but no local web evidence receipt has been attached yet.",
      backend_route_refs: ["POST /control-center/web-evidence/attach"],
      blocked_authority_refs: [
        "blocked-state:web-evidence:no-unrestricted-browsing",
        "blocked-state:web-evidence:no-browser-actions",
        "blocked-state:web-evidence:no-auth-session-state",
      ],
      run_detail: baseProofIndex.records[0].run_detail
        ? {
            ...baseProofIndex.records[0].run_detail,
            proof_ref: "proof-ref:web-evidence:product-slice",
            proof_kind: "web_evidence",
            title: "Web Evidence",
            backend_route_refs: ["POST /control-center/web-evidence/attach"],
            blocked_authority_refs: [
              "blocked-state:web-evidence:no-unrestricted-browsing",
              "blocked-state:web-evidence:no-browser-actions",
              "blocked-state:web-evidence:no-auth-session-state",
            ],
          }
        : baseProofIndex.records[0].run_detail,
    };
    stubReadEndpointOverrides({
      [API_ENDPOINTS.controlCenterProofIndex]: {
        ...baseProofIndex,
        proof_count: 1,
        proof_refs: [webRecord.proof_ref],
        records: [webRecord],
      },
    });
    window.history.pushState({}, "", "/proof");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Proof Detail$/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Web Evidence").length).toBeGreaterThan(0);
    expect(
      screen.getByText(/configured host allowlist HTTPS GET/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /attach preview/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^send$/i }),
    ).not.toBeInTheDocument();
  });

  it("renders provider draft preview proof as inspection-only", async () => {
    const baseProofIndex = backendOwnedProofIndexFixture();
    const providerRecord = {
      ...baseProofIndex.records[0],
      proof_ref: "proof-ref:provider-draft-summarize:exact",
      proof_kind: "provider_draft_preview",
      status: "exact_core_cli_fixture_proven_default_ui_blocked",
      title: "Provider Draft Preview",
      safe_summary:
        "Provider draft/summarize is an exact core and CLI inspection lane. Fixture proof can return a transient draft preview to the requester; durable records store safe refs only.",
      authority_posture:
        "Default Control Center invocation and default live provider network remain blocked. Model output is draft-only and is not truth, memory, context, connector, action, background, or production authority.",
      receipt_refs: [
        "receipt-ref:provider-draft-summarize:exact-required-before-live-use",
      ],
      evidence_refs: [
        "evidence-ref:provider-draft-summarize:fixture-proof",
        "provider-draft-summarize-lane:exact-approved:v1",
      ],
      approval_refs: ["approval-ref:provider-draft-summarize:exact-required"],
      rollback_refs: ["rollback-ref:provider-draft-summarize:discard-local-draft"],
      safe_disable_refs: [
        "safe-disable-ref:provider-draft-summarize:disable-exact-lane",
      ],
      blocked_authority_refs: [
        "blocked-state:provider-draft-summarize:no-autonomous-provider-call",
        "blocked-state:provider-draft-summarize:no-default-control-center-invocation",
        "blocked-state:provider-draft-summarize:no-default-live-provider-network",
      ],
      run_detail: baseProofIndex.records[0].run_detail
        ? {
            ...baseProofIndex.records[0].run_detail,
            proof_ref: "proof-ref:provider-draft-summarize:exact",
            proof_kind: "provider_draft_preview",
            title: "Provider Draft Preview",
            safe_summary:
              "Provider draft/summarize is an exact core and CLI inspection lane.",
            authority_posture:
              "Default Control Center invocation and default live provider network remain blocked.",
            receipt_refs: [
              "receipt-ref:provider-draft-summarize:exact-required-before-live-use",
            ],
            approval_refs: [
              "approval-ref:provider-draft-summarize:exact-required",
            ],
            rollback_refs: [
              "rollback-ref:provider-draft-summarize:discard-local-draft",
            ],
            safe_disable_refs: [
              "safe-disable-ref:provider-draft-summarize:disable-exact-lane",
            ],
            blocked_authority_refs: [
              "blocked-state:provider-draft-summarize:no-autonomous-provider-call",
              "blocked-state:provider-draft-summarize:no-default-control-center-invocation",
              "blocked-state:provider-draft-summarize:no-default-live-provider-network",
            ],
          }
        : baseProofIndex.records[0].run_detail,
    };
    stubReadEndpointOverrides({
      [API_ENDPOINTS.controlCenterProofIndex]: {
        ...baseProofIndex,
        proof_count: 1,
        proof_refs: [providerRecord.proof_ref],
        records: [providerRecord],
      },
    });
    window.history.pushState({}, "", "/proof");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Proof Detail$/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Provider Draft Preview").length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Default Control Center invocation and default live provider network remain blocked/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "blocked-state:provider-draft-summarize:no-default-control-center-invocation",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(
        "safe-disable-ref:provider-draft-summarize:disable-exact-lane",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", {
        name: /call provider|invoke provider|run provider|send|execute/i,
      }),
    ).not.toBeInTheDocument();
  });

  it("renders connector draft proposal proof as inspection-only", async () => {
    const baseProofIndex = backendOwnedProofIndexFixture();
    const connectorRecord = {
      ...baseProofIndex.records[0],
      proof_ref: "proof-ref:connector-draft-only-proposals:v1",
      proof_kind: "connector_draft_proposal",
      status: "draft_proposals_ready_no_send_write",
      title: "Connector Draft-Only Proposals",
      safe_summary:
        "Connector draft-only proposals are backend-owned email-response and calendar-hold review artifacts. They store safe refs and bounded redacted outlines only; no connector payload, account content, credential material, send, write, or sync is persisted.",
      authority_posture:
        "Connector runtime, sends, writes, account sync, OAuth, auth-material collection, background sync, provider/model calls, memory writes, context injection, and production authority remain blocked.",
      backend_route_refs: [
        "GET /control-center/sources/readiness",
        "GET /control-center/proof/index",
        "GET /control-center/proof/{proof_ref}",
      ],
      receipt_refs: [
        "receipt-ref:connector-draft-only:no-send-write-performed",
      ],
      evidence_refs: [
        "evidence-ref:connector-draft-only:source-readiness-safe-refs",
      ],
      approval_refs: [
        "approval-ref:connector-draft-only:email-send-future",
        "approval-ref:connector-draft-only:calendar-write-future",
      ],
      rollback_refs: [
        "rollback-posture-ref:connector-draft-only:email-response",
        "rollback-posture-ref:connector-draft-only:calendar-event",
      ],
      safe_disable_refs: [
        "safe-disable-ref:connector-draft-only:disable-local-draft-surface",
      ],
      blocked_authority_refs: [
        "blocked-state:connector-draft-only:no-connector-send",
        "blocked-state:connector-draft-only:no-connector-write",
        "blocked-state:connector-draft-only:no-oauth",
        "blocked-state:connector-draft-only:no-auth-material-collection",
      ],
      run_detail: baseProofIndex.records[0].run_detail
        ? {
            ...baseProofIndex.records[0].run_detail,
            proof_ref: "proof-ref:connector-draft-only-proposals:v1",
            proof_kind: "connector_draft_proposal",
            title: "Connector Draft-Only Proposals",
            safe_summary:
              "Connector draft-only proposals are backend-owned review artifacts.",
            authority_posture:
              "Connector runtime, sends, writes, account sync, OAuth, auth-material collection, background sync, provider/model calls, memory writes, context injection, and production authority remain blocked.",
            backend_route_refs: [
              "GET /control-center/sources/readiness",
              "GET /control-center/proof/index",
              "GET /control-center/proof/{proof_ref}",
            ],
            receipt_refs: [
              "receipt-ref:connector-draft-only:no-send-write-performed",
            ],
            approval_refs: [
              "approval-ref:connector-draft-only:email-send-future",
              "approval-ref:connector-draft-only:calendar-write-future",
            ],
            rollback_refs: [
              "rollback-posture-ref:connector-draft-only:email-response",
              "rollback-posture-ref:connector-draft-only:calendar-event",
            ],
            safe_disable_refs: [
              "safe-disable-ref:connector-draft-only:disable-local-draft-surface",
            ],
            blocked_authority_refs: [
              "blocked-state:connector-draft-only:no-connector-send",
              "blocked-state:connector-draft-only:no-connector-write",
              "blocked-state:connector-draft-only:no-oauth",
              "blocked-state:connector-draft-only:no-auth-material-collection",
            ],
          }
        : baseProofIndex.records[0].run_detail,
    };
    stubReadEndpointOverrides({
      [API_ENDPOINTS.controlCenterProofIndex]: {
        ...baseProofIndex,
        proof_count: 1,
        proof_refs: [connectorRecord.proof_ref],
        records: [connectorRecord],
      },
    });
    window.history.pushState({}, "", "/proof");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Proof Detail$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("Connector Draft-Only Proposals").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(
        /Connector runtime, sends, writes, account sync, OAuth, auth-material collection/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(
        "blocked-state:connector-draft-only:no-connector-send",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "blocked-state:connector-draft-only:no-connector-write",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "safe-disable-ref:connector-draft-only:disable-local-draft-surface",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", {
        name: /send|sync|write|oauth|connect account|execute/i,
      }),
    ).not.toBeInTheDocument();
  });

  it("renders operator workspace spine proof as inspection-only", async () => {
    const baseProofIndex = backendOwnedProofIndexFixture();
    const workspaceRecord = {
      ...baseProofIndex.records[0],
      proof_ref: "proof-ref:operator-workspace-spine:read-model",
      proof_kind: "operator_workspace_spine",
      status: "implemented_read_only_operator_workspace_spine",
      title: "Operator Workspace Spine",
      safe_summary:
        "Workspace status, Git posture, preview status, run-log posture, and coworker handoff are backend-owned safe refs only.",
      authority_posture:
        "The operator workspace spine is read-only posture. File writes, Git mutation, shell execution, browser automation, dev-server control, provider/model calls, connector writes, background autonomy, raw path/log persistence, and production authority remain blocked.",
      backend_route_refs: [
        "GET /control-center/today/summary#operator_workspace_spine",
        "GET /control-center/proof/index",
        "GET /control-center/proof/{proof_ref}",
      ],
      receipt_refs: ["receipt-ref:operator-workspace-spine:no-runtime-performed"],
      evidence_refs: ["evidence-ref:operator-workspace-spine:today"],
      approval_refs: [
        "approval-ref:operator-workspace-spine:not-required-for-read",
      ],
      rollback_refs: [
        "rollback-ref:operator-workspace-spine:remove-read-model-projection",
      ],
      safe_disable_refs: [
        "safe-disable-ref:operator-workspace-spine:disable-read-model",
      ],
      blocked_authority_refs: [
        "blocked-state:operator-workspace:no-git-mutation",
        "blocked-state:operator-workspace:no-shell-subprocess-execution",
        "blocked-state:operator-workspace:no-browser-automation",
        "blocked-state:operator-workspace:no-background-autonomy",
      ],
      run_detail: baseProofIndex.records[0].run_detail
        ? {
            ...baseProofIndex.records[0].run_detail,
            proof_ref: "proof-ref:operator-workspace-spine:read-model",
            proof_kind: "operator_workspace_spine",
            title: "Operator Workspace Spine",
            safe_summary:
              "Workspace status, Git posture, preview status, run-log posture, and coworker handoff are backend-owned safe refs only.",
            authority_posture:
              "The operator workspace spine is read-only posture.",
            backend_route_refs: [
              "GET /control-center/today/summary#operator_workspace_spine",
              "GET /control-center/proof/index",
              "GET /control-center/proof/{proof_ref}",
            ],
            receipt_refs: [
              "receipt-ref:operator-workspace-spine:no-runtime-performed",
            ],
            approval_refs: [
              "approval-ref:operator-workspace-spine:not-required-for-read",
            ],
            rollback_refs: [
              "rollback-ref:operator-workspace-spine:remove-read-model-projection",
            ],
            safe_disable_refs: [
              "safe-disable-ref:operator-workspace-spine:disable-read-model",
            ],
            blocked_authority_refs: [
              "blocked-state:operator-workspace:no-git-mutation",
              "blocked-state:operator-workspace:no-shell-subprocess-execution",
              "blocked-state:operator-workspace:no-browser-automation",
              "blocked-state:operator-workspace:no-background-autonomy",
            ],
          }
        : baseProofIndex.records[0].run_detail,
    };
    stubReadEndpointOverrides({
      [API_ENDPOINTS.controlCenterProofIndex]: {
        ...baseProofIndex,
        proof_count: 1,
        proof_refs: [workspaceRecord.proof_ref],
        records: [workspaceRecord],
      },
    });
    window.history.pushState({}, "", "/proof");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Proof Detail$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("Operator Workspace Spine").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Workspace status, Git posture, preview status/i)
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "blocked-state:operator-workspace:no-git-mutation",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "safe-disable-ref:operator-workspace-spine:disable-read-model",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", {
        name: /git commit|commit changes|push branch|pull branch|checkout branch|merge branch|rebase branch|create pr|apply patch|rollback patch|run command|execute command|open terminal|dispatch coworker|schedule worker|stream logs|cancel run|resume run/i,
      }),
    ).not.toBeInTheDocument();
  });

  it("fails closed for unsafe Proof Run Detail backend payloads", async () => {
    const unsafeCases = [
      {
        name: "raw content",
        mutate: (record: ReturnType<typeof backendOwnedProofIndexFixture>["records"][number]) => ({
          ...record,
          raw_content_included: true,
        }),
      },
      {
        name: "enabled authority",
        mutate: (record: ReturnType<typeof backendOwnedProofIndexFixture>["records"][number]) => ({
          ...record,
          run_detail: {
            ...record.run_detail,
            provider_model_call_enabled: true,
          },
        }),
      },
      {
        name: "mismatched proof ref",
        mutate: (record: ReturnType<typeof backendOwnedProofIndexFixture>["records"][number]) => ({
          ...record,
          run_detail: {
            ...record.run_detail,
            proof_ref: "proof-ref:unsafe:mismatch",
          },
        }),
      },
      {
        name: "missing run detail",
        mutate: (record: ReturnType<typeof backendOwnedProofIndexFixture>["records"][number]) => ({
          ...record,
          run_detail: null,
        }),
      },
      {
        name: "unsafe ref text",
        mutate: (record: ReturnType<typeof backendOwnedProofIndexFixture>["records"][number]) => ({
          ...record,
          run_detail: {
            ...record.run_detail,
            evidence_refs: ["/Users/private/raw-path"],
          },
        }),
      },
    ];

    const { loadControlCenterData } = await import("./api/client");
    for (const unsafeCase of unsafeCases) {
      const baseProofIndex = backendOwnedProofIndexFixture();
      const unsafeRecord = unsafeCase.mutate(baseProofIndex.records[0]);
      const unsafeProofIndex = {
        ...baseProofIndex,
        proof_count: 1,
        proof_refs: [unsafeRecord.proof_ref],
        records: [unsafeRecord],
      };
      const fetchMock = vi.fn(async (url: string) => {
        const urlText = String(url);
        if (urlText.endsWith(API_ENDPOINTS.controlCenterProofIndex)) {
          return new Response(
            JSON.stringify({ ok: true, result: unsafeProofIndex }),
            {
              status: 200,
              headers: { "Content-Type": "application/json" },
            },
          );
        }
        if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
          return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
        throw new Error(`unexpected request ${urlText}`);
      });
      vi.stubGlobal("fetch", fetchMock);

      const data = await loadControlCenterData();

      expect(data.connection.state, unsafeCase.name).toBe("degraded");
      expect(data.connection.warnings, unsafeCase.name).toContain(
        "PROOF_INDEX_MOCK_FALLBACK",
      );
      expect(data.proofIndex.source, unsafeCase.name).toBe(
        "mock_fallback_non_authoritative",
      );
      expect(data.proofIndex.records[0].run_detail?.source, unsafeCase.name).toBe(
        "mock_control_center_proof_run_detail_non_authoritative",
      );
    }
  });

  it("renders one coherent backend-owned dogfood loop across shared surfaces", async () => {
    const dogfoodData = dogfoodLiveLoopEndpointData();
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      if (options?.method === "POST") {
        throw new Error("unexpected mutation request");
      }
      const urlText = String(url);
      const matched = Object.entries(dogfoodData).find(([endpoint]) =>
        urlText.endsWith(endpoint),
      );
      if (matched) {
        return new Response(
          JSON.stringify({ ok: true, result: matched[1] }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (
        !options?.method &&
        READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const routes = [
      ["/start", /^Start Here$/i, dogfoodRefs.actionEnvelopeRef],
      ["/today", /Founder daily loop/i, dogfoodRefs.receiptRef],
      ["/actions", /^Action Inbox$/i, dogfoodRefs.receiptRef],
      ["/proof", /^Proof Detail$/i, dogfoodRefs.localTaskProofRef],
      ["/memory", /^Memory Review$/i, dogfoodRefs.memoryCandidateRef],
      ["/evidence", /Evidence Timeline/i, dogfoodRefs.timelineEventRef],
      ["/trust", /^Trust$/i, dogfoodRefs.localTaskProofRef],
      ["/settings", /^Settings$/i, "proof-ref:founder-loop-v1:governed-local-loop"],
    ] as const;

    for (const [path, heading, expectedRef] of routes) {
      window.history.pushState({}, "", path);
      const view = render(<App />);
      try {
        expect(await screen.findByText("Backend online")).toBeInTheDocument();
        expect(
          screen.getAllByRole("heading", { name: heading }).length,
        ).toBeGreaterThan(0);
        expect(screen.getAllByText(expectedRef).length).toBeGreaterThan(0);
        const spine = screen.getByLabelText("Founder daily loop modules");
        for (const surface of [
          "Start Here",
          "Today",
          "Action Inbox",
          "Proof",
          "Evidence",
          "Memory",
          "Trust",
          "Settings",
        ]) {
          expect(
            within(spine)
              .getAllByRole("link")
              .some((link) => link.textContent?.includes(surface)),
          ).toBe(true);
        }
        expect(
          within(spine).queryByText(/Source Inbox/),
        ).not.toBeInTheDocument();
        expect(
          screen.queryByText(/Backend unavailable; showing non-authoritative/i),
        ).not.toBeInTheDocument();
        if (path === "/actions") {
          expect(
            screen.getByText(
              "The exact local task lane produced a backend receipt and proof refs.",
            ),
          ).toBeInTheDocument();
          expect(screen.getByText("receipt_refs_recorded")).toBeInTheDocument();
          expect(
            screen.getByText("no_mutation_control_exposed"),
          ).toBeInTheDocument();
          expect(screen.getAllByText(dogfoodRefs.localTaskProofRef).length).toBeGreaterThan(0);
          expect(screen.getAllByText(dogfoodRefs.receiptRef).length).toBeGreaterThan(0);
          expect(
            screen.queryByRole("button", { name: /Execute|Send|Apply/i }),
          ).not.toBeInTheDocument();
        }
        if (path === "/memory" || path === "/evidence") {
          expect(
            screen.getAllByText("Shared loop").some((node) =>
              node.nextElementSibling?.textContent?.includes(
                "loop-binding-ref:evidence-memory:daily-loop-v1",
              ),
            ),
          ).toBe(true);
          expect(
            screen.getAllByText("Reviewed write").some((node) =>
              node.nextElementSibling?.textContent?.includes("not active"),
            ),
          ).toBe(true);
          expect(
            screen.getAllByText("Broad memory write").some((node) =>
              node.nextElementSibling?.textContent?.includes("blocked"),
            ),
          ).toBe(true);
          expect(screen.getAllByText(dogfoodRefs.actionRef).length).toBeGreaterThan(
            0,
          );
          expect(
            screen.getAllByText(dogfoodRefs.localTaskProofRef).length,
          ).toBeGreaterThan(0);
        }
      } finally {
        view.unmount();
        cleanup();
      }
    }

    window.history.pushState({}, "", "/");
    expect(
      fetchMock.mock.calls.some(
        ([, options]) => (options as RequestInit | undefined)?.method === "POST",
      ),
    ).toBe(false);
  });

  it("fails closed when Evidence/Memory shared refs drift", async () => {
    const dogfoodData = dogfoodLiveLoopEndpointData();
    const unsafeBinding = {
      ...dogfoodEvidenceMemoryBinding(),
      shared_proof_refs: [],
    };
    dogfoodData[API_ENDPOINTS.founderTodaySummary] = {
      ...dogfoodData[API_ENDPOINTS.founderTodaySummary],
      evidence_memory_loop_binding_read_model: unsafeBinding,
    };
    dogfoodData[API_ENDPOINTS.founderMemoryReview] = {
      ...dogfoodData[API_ENDPOINTS.founderMemoryReview],
      evidence_memory_loop_binding_read_model: unsafeBinding,
    };
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      if (options?.method === "POST") {
        throw new Error("unexpected mutation request");
      }
      const urlText = String(url);
      const matched = Object.entries(dogfoodData).find(([endpoint]) =>
        urlText.endsWith(endpoint),
      );
      if (matched) {
        return new Response(JSON.stringify({ ok: true, result: matched[1] }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (
        !options?.method &&
        READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const { loadControlCenterData } = await import("./api/client");
    const data = await loadControlCenterData();

    expect(
      data.founderToday.evidence_memory_loop_binding_read_model,
    ).toBeUndefined();
    expect(
      data.founderMemoryReview.evidence_memory_loop_binding_read_model,
    ).toBeUndefined();

    window.history.pushState({}, "", "/memory");
    const view = render(<App />);
    try {
      expect(await screen.findByText("Backend online")).toBeInTheDocument();
      expect(
        screen.getByLabelText("Evidence and Memory loop binding unavailable"),
      ).toBeInTheDocument();
      expect(screen.getByText("backend proof required")).toBeInTheDocument();
      expect(
        screen.getByText(
          "blocked-state:evidence-memory-loop:backend-read-model-required",
        ),
      ).toBeInTheDocument();
      expect(screen.queryByText("Shared loop")).not.toBeInTheDocument();
    } finally {
      view.unmount();
      cleanup();
      window.history.pushState({}, "", "/");
    }
  });

  it("renders Trust safe-disable, rollback, promotion, and CLI refs from backend", async () => {
    stubReadEndpointOverrides({
      [API_ENDPOINTS.trustAuthorityMatrix]: betaTrustAuthorityMatrix(),
    });

    window.history.pushState({}, "", "/trust");
    const view = render(<App />);

    try {
      expect(await screen.findByText("Backend online")).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: /^Trust$/i }),
      ).toBeInTheDocument();
      expect(screen.getByText("Provider draft/summarize")).toBeInTheDocument();
      expect(screen.getByText("Connector draft-only")).toBeInTheDocument();
      expect(screen.getAllByText("review only").length).toBeGreaterThan(0);
      expect(screen.getByText("Exact local task commit")).toBeInTheDocument();
      expect(screen.getAllByText("approval required").length).toBeGreaterThan(0);
      expect(screen.getAllByText("CLI and verifiers").length).toBeGreaterThan(0);
      expect(
        screen.getAllByText(
          "python scripts/dev/uaa_founder_loop.py inspect-trust-authority",
        ).length,
      ).toBeGreaterThan(0);
      expect(
        screen.getByText("python scripts/inspect_connector_draft_proposals.py"),
      ).toBeInTheDocument();
      expect(
        screen.getAllByText("Safe-disable and rollback").length,
      ).toBeGreaterThan(0);
      expect(
        screen.getByText(
          "safe-disable-ref:provider-draft-summarize:disable-exact-lane",
        ),
      ).toBeInTheDocument();
      expect(
        screen.getByText("rollback-ref:provider-draft-summarize:discard-local-draft"),
      ).toBeInTheDocument();
      expect(screen.getAllByText("Promotion path").length).toBeGreaterThan(0);
      expect(
        screen.getByText(
          "promotion-path-ref:trust:provider-draft-summarize:live-provider-separate-contract",
        ),
      ).toBeInTheDocument();
      expect(
        screen.queryByRole("button", {
          name: /Approve|Execute|Send|Apply|Write|Sync|OAuth|Authorize|Connect account|Sign in/i,
        }),
      ).not.toBeInTheDocument();
    } finally {
      view.unmount();
      cleanup();
      window.history.pushState({}, "", "/");
    }
  });

  it("keeps Trust backend-owned when an unrelated endpoint degrades", async () => {
    const trust = betaTrustAuthorityMatrix();
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.runObservability)) {
        throw new Error("run observability unavailable");
      }
      if (urlText.endsWith(API_ENDPOINTS.trustAuthorityMatrix)) {
        return new Response(JSON.stringify({ ok: true, result: trust }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    window.history.pushState({}, "", "/trust");
    const view = render(<App />);

    try {
      expect(await screen.findByText("Backend degraded")).toBeInTheDocument();
      expect(screen.getByText("Provider draft/summarize")).toBeInTheDocument();
      expect(
        screen.getAllByText("Safe-disable and rollback").length,
      ).toBeGreaterThan(0);
      expect(
        screen.queryByText("Mock Fallback Lane Refs"),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByText(/Backend unavailable; showing non-authoritative/i),
      ).not.toBeInTheDocument();
    } finally {
      view.unmount();
      cleanup();
      window.history.pushState({}, "", "/");
    }
  });

  it("fails closed for unsafe Trust authority matrix payloads", async () => {
    const unsafeCases = [
      {
        name: "unknown authority state",
        mutate: () => {
          const matrix = betaTrustAuthorityMatrix();
          matrix.lanes[0] = {
            ...matrix.lanes[0],
            authority_state: "enabled",
          };
          return matrix;
        },
      },
      {
        name: "tier 4 marked available",
        mutate: () => {
          const matrix = betaTrustAuthorityMatrix();
          matrix.lanes[4] = {
            ...matrix.lanes[4],
            authority_state: "available_now",
            authority_state_label: "available now",
            operator_posture: "enabled_read_only",
          };
          return matrix;
        },
      },
      {
        name: "rollback execution enabled",
        mutate: () => {
          const matrix = betaTrustAuthorityMatrix();
          matrix.lanes[0] = {
            ...matrix.lanes[0],
            rollback_execution_enabled: true,
          };
          return matrix;
        },
      },
      {
        name: "tier 3 missing safe disable refs",
        mutate: () => {
          const matrix = betaTrustAuthorityMatrix();
          matrix.lanes[3] = {
            ...matrix.lanes[3],
            safe_disable_refs: [],
          };
          matrix.safe_disable_refs = trustLaneUnion(matrix.lanes, "safe_disable_refs");
          return matrix;
        },
      },
      {
        name: "aggregate safe-disable drift",
        mutate: () => ({
          ...betaTrustAuthorityMatrix(),
          safe_disable_refs: [],
        }),
      },
      {
        name: "control center grants authority",
        mutate: () => ({
          ...betaTrustAuthorityMatrix(),
          control_center_grants_authority: true,
        }),
      },
      {
        name: "production authority enabled",
        mutate: () => ({
          ...betaTrustAuthorityMatrix(),
          production_authority_enabled: true,
        }),
      },
      {
        name: "unsafe raw text",
        mutate: () => ({
          ...betaTrustAuthorityMatrix(),
          operator_summary: "Raw prompt content must not render.",
        }),
      },
    ];

    const { loadControlCenterData } = await import("./api/client");
    for (const unsafeCase of unsafeCases) {
      stubReadEndpointOverrides({
        [API_ENDPOINTS.trustAuthorityMatrix]: unsafeCase.mutate(),
      });

      const data = await loadControlCenterData();

      expect(data.connection.state, unsafeCase.name).toBe("degraded");
      expect(data.connection.warnings, unsafeCase.name).toContain(
        "TRUST_AUTHORITY_MATRIX_MOCK_FALLBACK",
      );
      expect(data.trustAuthorityMatrix.backend_owned, unsafeCase.name).toBe(
        false,
      );
      vi.unstubAllGlobals();
    }
  });

  it("renders the daily loop spine across primary Founder Loop surfaces", async () => {
    const primarySurfaces = [
      ["/today", "Today"],
      ["/briefing", "Briefing"],
      ["/inbox", "Source Inbox"],
      ["/plans", "Plans"],
      ["/actions", "Action Inbox"],
      ["/memory", "Memory"],
      ["/evidence", "Evidence"],
      ["/settings", "Settings"],
    ] as const;

    for (const [path, label] of primarySurfaces) {
      mockFetchWithFallback();
      window.history.pushState({}, "", path);
      const view = render(<App />);

      expect(
        await screen.findByRole("heading", { name: /Founder daily loop/i }),
      ).toBeInTheDocument();
      const spine = screen.getByLabelText("Founder daily loop modules");
      const activeCard = within(spine)
        .getAllByRole("link")
        .find((link) => link.getAttribute("aria-current") === "page");
      expect(activeCard).toHaveTextContent(label);
      expect(
        screen.getAllByText(/No generic execution/i).length,
      ).toBeGreaterThan(0);
      expect(
        screen.getAllByText(/Local task authority requires backend approval/i)
          .length,
      ).toBeGreaterThan(0);
      expect(
        screen.queryByRole("button", { name: /^execute$/i }),
      ).not.toBeInTheDocument();

      view.unmount();
      cleanup();
      vi.unstubAllGlobals();
    }
  });

  it("does not backfill the Today loop digest from mocks for partial backend responses", async () => {
    const partialToday = { ...mockControlCenterData.founderToday };
    delete (partialToday as { today_loop_read_model?: unknown })
      .today_loop_read_model;
    delete (partialToday as { today_loop_tightening_contract_ref?: unknown })
      .today_loop_tightening_contract_ref;
    delete (partialToday as { follow_up_tracker?: unknown }).follow_up_tracker;
    delete (partialToday as { follow_up_tracker_contract_ref?: unknown })
      .follow_up_tracker_contract_ref;
    delete (partialToday as { weekly_ceo_review_v1_read_model?: unknown })
      .weekly_ceo_review_v1_read_model;
    delete (partialToday as { weekly_ceo_review_v1_contract_ref?: unknown })
      .weekly_ceo_review_v1_contract_ref;
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(
          JSON.stringify({ ok: true, result: partialToday }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/today");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Today$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("backend digest missing").length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByText(
        "contract-ref:product-loop-003-today-loop-tightening:v1",
      ),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("python_core_today_loop_read_model"),
    ).not.toBeInTheDocument();
    expect(
      screen.getAllByText("backend tracker missing").length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByText("contract-ref:product-loop-004-follow-up-tracker:v1"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("python_core_follow_up_tracker_read_model"),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/backend review refs/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^\d+ changed refs$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/backend blocker refs/i)).not.toBeInTheDocument();
  });

  it("renders backend-owned Founder Loop V1 product proof from backend data", async () => {
    const productProof = founderLoopProductProofFixture();
    const today = {
      ...mockControlCenterData.founderToday,
      founder_loop_v1_product_proof_contract_ref:
        "contract-ref:founder-loop-v1-product-proof:v1",
      founder_loop_v1_product_proof_read_model: productProof,
    };
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(JSON.stringify({ ok: true, result: today }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/today");
    render(<App />);

    const proofPath = await screen.findByLabelText("Founder Loop proof path");
    expect(
      within(proofPath).getByRole("heading", {
        name: /Morning Briefing to Weekly Review/i,
      }),
    ).toBeInTheDocument();
    expect(within(proofPath).getByText("backend-owned demo-safe")).toBeInTheDocument();
    expect(
      within(proofPath).getByText(
        "founder-loop-state-ref:demo-safe-seeded-loop",
      ),
    ).toBeInTheDocument();
    expect(
      within(proofPath).getAllByText("Morning Briefing").length,
    ).toBeGreaterThan(0);
    expect(within(proofPath).getAllByText("Action Inbox").length).toBeGreaterThan(
      0,
    );
    expect(within(proofPath).getAllByText("Weekly Review").length).toBeGreaterThan(
      0,
    );
    const currentProofLinks = within(proofPath)
      .getAllByRole("link")
      .filter((link) => link.getAttribute("aria-current") === "page");
    expect(currentProofLinks).toHaveLength(1);
    expect(currentProofLinks[0]).toHaveTextContent("Today");
    expect(within(proofPath).queryByRole("button")).not.toBeInTheDocument();

    const proofPanel = await screen.findByLabelText(
      "Founder Loop V1 product proof",
    );
    expect(
      within(proofPanel).getByRole("heading", {
        name: /Founder Loop V1 product proof/i,
      }),
    ).toBeInTheDocument();
    expect(
      within(proofPanel).getByText(
        "contract-ref:founder-loop-v1-product-proof:v1",
      ),
    ).toBeInTheDocument();
    expect(
      within(proofPanel).getByText(
        "python_core_founder_loop_v1_product_proof_read_model",
      ),
    ).toBeInTheDocument();
    expect(
      within(proofPanel).getByText("Decision receipts").nextElementSibling,
    ).toHaveTextContent("receipt_backed_decision_path_visible");
    expect(
      within(proofPanel).getByText("Memory review").nextElementSibling,
    ).toHaveTextContent("candidate visible");
    expect(
      within(proofPanel).getByText("Provider/model calls").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(proofPanel).getByText("Production authority").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(proofPanel).getAllByText(
        "receipt:founder-loop-product-proof:action-defer",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      within(proofPanel).getByText(
        "business-memory-candidate:founder-loop-preferences",
      ),
    ).toBeInTheDocument();
    expect(
      within(proofPanel).getAllByText(
        "blocked-state:founder-loop-proof-no-production-authority",
      ).length,
    ).toBeGreaterThan(0);
  });

  it("renders backend-owned Founder Loop run and proof refs without mutation controls", async () => {
    const runsIntegration = founderLoopRunsIntegrationFixture();
    const today = {
      ...mockControlCenterData.founderToday,
      founder_loop_runs_integration_contract_ref:
        "contract-ref:founder-loop-runs-integration:v1",
      founder_loop_runs_integration_read_model: runsIntegration,
      loop_trace_refs: {
        run_refs: runsIntegration.run_refs,
        operator_run_event_refs: runsIntegration.operator_run_event_refs,
        receipt_refs: runsIntegration.receipt_refs,
        evidence_refs: runsIntegration.evidence_refs,
        evidence_event_refs: runsIntegration.evidence_event_refs,
        proof_refs: runsIntegration.proof_refs,
        approval_refs: runsIntegration.approval_refs,
        blocked_authority_refs: runsIntegration.blocked_authority_refs,
      },
    };
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(JSON.stringify({ ok: true, result: today }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/today");
    render(<App />);

    const panel = await screen.findByLabelText("Founder Loop run and proof refs");
    expect(
      within(panel).getAllByText("run-ref:founder-loop-v1:governed-local-loop")
        .length,
    ).toBeGreaterThan(0);
    expect(
      within(panel).getAllByText("proof-ref:founder-loop-v1:governed-local-loop")
        .length,
    ).toBeGreaterThan(0);
    expect(
      within(panel).getAllByText("receipt:founder-loop-runs:decision").length,
    ).toBeGreaterThan(0);
    expect(
      within(panel).getAllByText(
        "operator-run-event:evidence-event-action-decision-recorded-test",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      within(panel).getAllByText(
        "blocked-state:founder-loop-runs-no-production-authority",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      within(panel).getByText("Execution").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(within(panel).queryByRole("button")).not.toBeInTheDocument();
  });

  it("renders backend-owned Unified Work Thread from backend data", async () => {
    const unifiedWorkThread = unifiedWorkThreadFixture();
    const today = {
      ...mockControlCenterData.founderToday,
      unified_work_thread_contract_ref:
        "contract-ref:fcc-thread-001-unified-work-thread:v1",
      unified_work_thread_read_model: unifiedWorkThread,
    };
    stubFounderTodayReadEndpoint(today);
    window.history.pushState({}, "", "/today");
    render(<App />);

    const threadPanel = await screen.findByLabelText("Unified Work Thread");
    expect(
      within(threadPanel).getByRole("heading", {
        name: /Unified Work Thread/i,
      }),
    ).toBeInTheDocument();
    expect(
      within(threadPanel).getByText(
        "contract-ref:fcc-thread-001-unified-work-thread:v1",
      ),
    ).toBeInTheDocument();
    expect(
      within(threadPanel).getByText(
        "python_core_unified_work_thread_read_model",
      ),
    ).toBeInTheDocument();
    expect(
      within(threadPanel).getByText(
        "work-thread-ref:founder-loop:demo-safe-seeded-loop",
      ),
    ).toBeInTheDocument();
    expect(
      within(threadPanel).getByText("Provider/model calls").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(threadPanel).getByText("Connector read/write").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(threadPanel).getByText("Execution").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(threadPanel).getByText("Production authority").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(threadPanel).getAllByText("receipt:unified-work-thread:action-defer")
        .length,
    ).toBeGreaterThan(0);
    expect(
      within(threadPanel).getByText(
        "business-memory-candidate:founder-loop-preferences",
      ),
    ).toBeInTheDocument();
    expect(
      within(threadPanel).getAllByText(
        "blocked-state:unified-work-thread-no-production-authority",
      ).length,
    ).toBeGreaterThan(0);
    expect(within(threadPanel).queryByRole("button")).not.toBeInTheDocument();
  });

  it("shows the shared Founder Loop proof path on Action Inbox without adding execution controls", async () => {
    const productProof = founderLoopProductProofFixture();
    const today = {
      ...mockControlCenterData.founderToday,
      founder_loop_v1_product_proof_contract_ref:
        "contract-ref:founder-loop-v1-product-proof:v1",
      founder_loop_v1_product_proof_read_model: productProof,
    };
    stubFounderTodayReadEndpoint(today);
    window.history.pushState({}, "", "/actions");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Action Inbox$/i }),
    ).toBeInTheDocument();
    const proofPath = screen.getByLabelText("Founder Loop proof path");
    expect(
      within(proofPath).getByRole("heading", {
        name: /Morning Briefing to Weekly Review/i,
      }),
    ).toBeInTheDocument();
    expect(within(proofPath).getAllByText("Action Inbox").length).toBeGreaterThan(
      0,
    );
    expect(within(proofPath).getByText("No provider/model calls")).toBeInTheDocument();
    expect(within(proofPath).getByText("No connector writes")).toBeInTheDocument();
    const currentProofLinks = within(proofPath)
      .getAllByRole("link")
      .filter((link) => link.getAttribute("aria-current") === "page");
    expect(currentProofLinks).toHaveLength(1);
    expect(currentProofLinks[0]).toHaveTextContent("Action Inbox");
    expect(within(proofPath).queryByRole("button")).not.toBeInTheDocument();
    const approvalReview = screen.getByLabelText("Action Inbox approval review");
    expect(within(approvalReview).getByText("Review items")).toBeInTheDocument();
    expect(within(approvalReview).getByText("Pending refs")).toBeInTheDocument();
    expect(within(approvalReview).queryByRole("button")).not.toBeInTheDocument();
    const connectorQueue = screen.getByLabelText("Connector delivery review queue");
    expect(
      within(connectorQueue).getByText("Connector Delivery Review Queue"),
    ).toBeInTheDocument();
    expect(
      within(connectorQueue).getByText(/delivery-ready metadata only \/ not sent/i),
    ).toBeInTheDocument();
    expect(
      within(connectorQueue).getByText("Delivery execution"),
    ).toBeInTheDocument();
    expect(within(connectorQueue).getByText("blocked/planned")).toBeInTheDocument();
    expect(
      within(connectorQueue).queryByRole("button", { name: /send|deliver|retry|sync|write|execute/i }),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/raw message body/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/founder@example\.com/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/bearer token/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\/Users\//i)).not.toBeInTheDocument();
  });

  it("labels adjacent Founder Loop surfaces without faking a current proof step", async () => {
    const productProof = founderLoopProductProofFixture();
    const today = {
      ...mockControlCenterData.founderToday,
      founder_loop_v1_product_proof_contract_ref:
        "contract-ref:founder-loop-v1-product-proof:v1",
      founder_loop_v1_product_proof_read_model: productProof,
    };
    stubFounderTodayReadEndpoint(today);
    window.history.pushState({}, "", "/plans");
    render(<App />);

    expect(await screen.findByRole("heading", { name: /^Plans$/i })).toBeInTheDocument();
    const proofPath = screen.getByLabelText("Founder Loop proof path");
    expect(
      within(proofPath).getByText(
        /This surface is adjacent to the seeded proof path/i,
      ),
    ).toBeInTheDocument();
    const currentProofLinks = within(proofPath)
      .getAllByRole("link")
      .filter((link) => link.getAttribute("aria-current") === "page");
    expect(currentProofLinks).toHaveLength(0);
  });

  it("renders Action Inbox when an optional shared read times out", async () => {
    vi.useFakeTimers();
    const fetchMock = stubReadEndpointsWithHungEndpoint(
      API_ENDPOINTS.providerSetupGuide,
    );
    window.history.pushState({}, "", "/actions");
    const view = render(<App />);

    try {
      expect(screen.getByText("Loading local Action Inbox")).toBeInTheDocument();
      await advanceControlCenterReadTimeout();
      vi.useRealTimers();

      expect(
        await screen.findByRole("heading", { name: /^Action Inbox$/i }),
      ).toBeInTheDocument();
      expect(screen.queryByText("Loading local Action Inbox")).not.toBeInTheDocument();
      expect(screen.getByText("Backend degraded")).toBeInTheDocument();
      expect(
        fetchMock.mock.calls.some(([url]) =>
          String(url).endsWith(API_ENDPOINTS.founderActionsInbox),
        ),
      ).toBe(true);
      expect(
        fetchMock.mock.calls.some(([url]) =>
          String(url).endsWith(API_ENDPOINTS.founderTodaySummary),
        ),
      ).toBe(true);
      const actionExecutionValues = screen
        .getAllByText("Action execution")
        .map((term) => term.nextElementSibling?.textContent);
      expect(actionExecutionValues).toContain("blocked");
      expect(
        screen.queryByRole("button", { name: /^execute$/i }),
      ).not.toBeInTheDocument();
      for (const blockedControl of [
        /Record approval receipt/i,
        /Record edit receipt/i,
        /Record rejection receipt/i,
        /Record defer receipt/i,
        /Create local task record/i,
      ]) {
        expect(
          screen.queryByRole("button", { name: blockedControl }),
        ).not.toBeInTheDocument();
      }
    } finally {
      view.unmount();
      cleanup();
      vi.unstubAllGlobals();
      vi.useRealTimers();
    }
  });

  it("renders Plans when an optional shared read times out", async () => {
    vi.useFakeTimers();
    const fetchMock = stubReadEndpointsWithHungEndpoint(
      API_ENDPOINTS.providerSetupGuide,
    );
    window.history.pushState({}, "", "/plans");
    const view = render(<App />);

    try {
      expect(screen.getByText("Loading local Plans")).toBeInTheDocument();
      await advanceControlCenterReadTimeout();
      vi.useRealTimers();

      expect(
        await screen.findByRole("heading", { name: /^Plans$/i }),
      ).toBeInTheDocument();
      expect(screen.queryByText("Loading local Plans")).not.toBeInTheDocument();
      expect(screen.getByText("Backend degraded")).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: /Task decomposition route posture/i }),
      ).toBeInTheDocument();
      expect(
        fetchMock.mock.calls.some(([url]) =>
          String(url).endsWith(API_ENDPOINTS.founderActionsInbox),
        ),
      ).toBe(true);
      expect(
        fetchMock.mock.calls.some(([url]) =>
          String(url).endsWith(API_ENDPOINTS.founderTodaySummary),
        ),
      ).toBe(true);
      expect(
        screen.queryByRole("button", { name: /^execute$/i }),
      ).not.toBeInTheDocument();
    } finally {
      view.unmount();
      cleanup();
      vi.unstubAllGlobals();
      vi.useRealTimers();
    }
  });

  it("drops incomplete Action Inbox decision lanes instead of crashing the route", async () => {
    const unsafeInbox = {
      ...mockControlCenterData.founderActionsInbox,
      action_inbox_decision_lane_contract_ref:
        "contract-ref:action-inbox-decision-lanes:v1",
      action_inbox_decision_lane_read_model: {
        ...actionDecisionLaneReadModelFixture(),
        items: actionDecisionLaneReadModelFixture().items.map(
          (item, index) => {
            if (index !== 0) {
              return item;
            }
            const unsafeItem = { ...item } as Record<string, unknown>;
            delete unsafeItem.estimated_cost_usd;
            delete unsafeItem.max_approved_cost_usd;
            return unsafeItem;
          },
        ),
      },
    };
    stubReadEndpointOverrides({
      [API_ENDPOINTS.founderActionsInbox]: unsafeInbox,
    });
    window.history.pushState({}, "", "/actions");
    const view = render(<App />);

    try {
      expect(
        await screen.findByRole("heading", { name: /^Action Inbox$/i }),
      ).toBeInTheDocument();
      expect(screen.queryByText("Loading local Action Inbox")).not.toBeInTheDocument();
      expect(
        screen.getByText("backend decision lanes missing"),
      ).toBeInTheDocument();
      expect(
        screen.getByText(/will not backfill cost, authority, approval, or receipt lanes/i),
      ).toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /^execute$/i }),
      ).not.toBeInTheDocument();
    } finally {
      view.unmount();
      cleanup();
      vi.unstubAllGlobals();
    }
  });

  it("renders Plans with degraded fallback when Today arrays are null", async () => {
    const unsafeToday = {
      ...mockControlCenterData.founderToday,
      actions: null,
      plans: null,
      briefing_items: null,
      memory_review_queue: null,
      evidence_timeline: null,
      sections: {
        ...mockControlCenterData.founderToday.sections,
        action_inbox_count: null,
        plan_count: null,
      },
    };
    stubReadEndpointOverrides({
      [API_ENDPOINTS.founderTodaySummary]: unsafeToday,
    });
    window.history.pushState({}, "", "/plans");
    const view = render(<App />);

    try {
      expect(
        await screen.findByRole("heading", { name: /^Plans$/i }),
      ).toBeInTheDocument();
      expect(screen.queryByText("Loading local Plans")).not.toBeInTheDocument();
      expect(screen.getByText("Backend degraded")).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: /Founder daily loop/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: /Task decomposition route posture/i }),
      ).toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /^execute$/i }),
      ).not.toBeInTheDocument();
    } finally {
      view.unmount();
      cleanup();
      vi.unstubAllGlobals();
    }
  });

  it.each([
    ["/briefing", /^Morning Briefing$/i],
    ["/memory", /^Memory Review$/i],
    ["/evidence", /^Evidence Timeline$/i],
  ])("shows the shared Founder Loop proof path on %s", async (path, heading) => {
    const productProof = founderLoopProductProofFixture();
    const today = {
      ...mockControlCenterData.founderToday,
      founder_loop_v1_product_proof_contract_ref:
        "contract-ref:founder-loop-v1-product-proof:v1",
      founder_loop_v1_product_proof_read_model: productProof,
    };
    stubFounderTodayReadEndpoint(today);
    window.history.pushState({}, "", path);
    render(<App />);

    expect(await screen.findByRole("heading", { name: heading })).toBeInTheDocument();
    const proofPath = screen.getByLabelText("Founder Loop proof path");
    expect(
      within(proofPath).getByRole("heading", {
        name: /Morning Briefing to Weekly Review/i,
      }),
    ).toBeInTheDocument();
    expect(within(proofPath).getByText("backend-owned demo-safe")).toBeInTheDocument();
    expect(within(proofPath).getAllByText("Weekly Review").length).toBeGreaterThan(
      0,
    );
    expect(within(proofPath).getByText("No memory writes/context injection"))
      .toBeInTheDocument();
    expect(within(proofPath).getByText("No shell/subprocess execution"))
      .toBeInTheDocument();
  });

  it("derives proof path navigation from step ids instead of backend-fed route strings", async () => {
    const productProof = founderLoopProductProofFixture();
    productProof.steps = productProof.steps.map((step) =>
      step.step_id === "memory_review"
        ? { ...step, frontend_route_ref: "https://example.invalid/unsafe" }
        : step,
    );
    const today = {
      ...mockControlCenterData.founderToday,
      founder_loop_v1_product_proof_contract_ref:
        "contract-ref:founder-loop-v1-product-proof:v1",
      founder_loop_v1_product_proof_read_model: productProof,
    };
    stubFounderTodayReadEndpoint(today);
    window.history.pushState({}, "", "/today");
    render(<App />);

    const proofPath = await screen.findByLabelText("Founder Loop proof path");
    const memoryLink = within(proofPath)
      .getAllByRole("link")
      .find((link) => link.textContent?.includes("Memory Review"));
    expect(memoryLink).toBeDefined();
    expect(memoryLink).toHaveAttribute("href", "/memory");
  });

  it("does not backfill Founder Loop product proof from mocks for partial backend responses", async () => {
    const partialToday = { ...mockControlCenterData.founderToday };
    delete (
      partialToday as {
        founder_loop_v1_product_proof_read_model?: unknown;
      }
    ).founder_loop_v1_product_proof_read_model;
    delete (
      partialToday as {
        founder_loop_v1_product_proof_contract_ref?: unknown;
      }
    ).founder_loop_v1_product_proof_contract_ref;
    delete (
      partialToday as {
        unified_work_thread_read_model?: unknown;
      }
    ).unified_work_thread_read_model;
    delete (
      partialToday as {
        unified_work_thread_contract_ref?: unknown;
      }
    ).unified_work_thread_contract_ref;
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(
          JSON.stringify({ ok: true, result: partialToday }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/today");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Today$/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Founder Loop V1 product proof"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("contract-ref:founder-loop-v1-product-proof:v1"),
    ).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Unified Work Thread")).not.toBeInTheDocument();
    expect(
      screen.queryByText("contract-ref:fcc-thread-001-unified-work-thread:v1"),
    ).not.toBeInTheDocument();
  });

  it("fails closed for unsafe Founder Loop product proof authority flags", async () => {
    const unsafeToday = {
      ...mockControlCenterData.founderToday,
      founder_loop_v1_product_proof_contract_ref:
        "contract-ref:founder-loop-v1-product-proof:v1",
      founder_loop_v1_product_proof_read_model: founderLoopProductProofFixture({
        provider_model_call_enabled: true,
      }),
    };
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(
          JSON.stringify({ ok: true, result: unsafeToday }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/today");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Today$/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Founder Loop V1 product proof"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(
        "python_core_founder_loop_v1_product_proof_read_model",
      ),
    ).not.toBeInTheDocument();
  });

  it("fails closed for unsafe Unified Work Thread authority flags and blockers", async () => {
    const unsafeToday = {
      ...mockControlCenterData.founderToday,
      unified_work_thread_contract_ref:
        "contract-ref:fcc-thread-001-unified-work-thread:v1",
      unified_work_thread_read_model: unifiedWorkThreadFixture({
        provider_model_call_enabled: true,
      }),
    };
    stubFounderTodayReadEndpoint(unsafeToday);
    window.history.pushState({}, "", "/today");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Today$/i }),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("Unified Work Thread")).not.toBeInTheDocument();
    expect(
      screen.queryByText("python_core_unified_work_thread_read_model"),
    ).not.toBeInTheDocument();

    cleanup();
    const missingBlockerToday = {
      ...mockControlCenterData.founderToday,
      unified_work_thread_contract_ref:
        "contract-ref:fcc-thread-001-unified-work-thread:v1",
      unified_work_thread_read_model: unifiedWorkThreadFixture({
        blocked_authority_refs: [
          "blocked-state:unified-work-thread-no-production-authority",
        ],
      }),
    };
    stubFounderTodayReadEndpoint(missingBlockerToday);
    window.history.pushState({}, "", "/today");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Today$/i }),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("Unified Work Thread")).not.toBeInTheDocument();
  });

  it("does not backfill the Today loop digest when the API base is blocked", async () => {
    vi.stubEnv("VITE_UAA_API_BASE_URL", "https://example.invalid");
    vi.resetModules();
    try {
      const { loadControlCenterData } = await import("./api/client");
      const data = await loadControlCenterData();

      expect(data.connection.state).toBe("mock_fallback");
      expect(data.connection.warnings).toContain(
        "EXTERNAL_API_BASE_URL_BLOCKED",
      );
      expect(data.founderToday.today_loop_read_model).toBeUndefined();
      expect(
        data.founderToday.today_loop_tightening_contract_ref,
      ).toBeUndefined();
      expect(data.founderToday.follow_up_tracker).toBeUndefined();
      expect(data.founderToday.follow_up_tracker_contract_ref).toBeUndefined();
      expect(data.founderToday.weekly_ceo_review_v1_read_model).toBeUndefined();
      expect(
        data.founderToday.weekly_ceo_review_v1_contract_ref,
      ).toBeUndefined();
      expect(
        data.founderToday.founder_loop_v1_product_proof_read_model,
      ).toBeUndefined();
      expect(
        data.founderToday.founder_loop_v1_product_proof_contract_ref,
      ).toBeUndefined();
      expect(
        data.founderToday.unified_work_thread_read_model,
      ).toBeUndefined();
      expect(
        data.founderToday.unified_work_thread_contract_ref,
      ).toBeUndefined();
      expect(
        data.founderToday.plans_to_actions_bridge_read_model,
      ).toBeUndefined();
      expect(
        data.founderToday.plans_to_actions_bridge_contract_ref,
      ).toBeUndefined();
      expect(
        data.founderToday.plans_action_envelope_contract_ref,
      ).toBeUndefined();
      expect(
        (data.founderToday.plans[0] as unknown as Record<string, unknown>)
          .action_envelope_contract_ref,
      ).toBeUndefined();
      expect(
        (data.founderToday.plans[0] as unknown as Record<string, unknown>)
          .action_envelope_ref,
      ).toBeUndefined();
      expect(data.founderActionsInbox.follow_up_tracker).toBeUndefined();
      expect(
        data.founderActionsInbox.follow_up_tracker_contract_ref,
      ).toBeUndefined();
      expect(
        data.founderActionsInbox.action_inbox_decision_lane_read_model,
      ).toBeUndefined();
      expect(
        data.founderActionsInbox.action_inbox_decision_lane_contract_ref,
      ).toBeUndefined();
      expect(
        data.founderActionsInbox.plans_to_actions_bridge_read_model,
      ).toBeUndefined();
      expect(
        data.founderActionsInbox.plans_to_actions_bridge_contract_ref,
      ).toBeUndefined();
      expect(data.founderMorningBriefing.follow_up_tracker).toBeUndefined();
      expect(
        data.founderMorningBriefing.follow_up_tracker_contract_ref,
      ).toBeUndefined();
      expect(
        data.founderMorningBriefing.morning_briefing_v1_read_model,
      ).toBeUndefined();
      expect(
        data.founderMorningBriefing.morning_briefing_v1_contract_ref,
      ).toBeUndefined();
      expect(
        data.founderMorningBriefing.weekly_ceo_review_v1_read_model,
      ).toBeUndefined();
      expect(
        data.founderMorningBriefing.weekly_ceo_review_v1_contract_ref,
      ).toBeUndefined();
      expect(
        data.founderMorningBriefing.founder_loop_v1_product_proof_read_model,
      ).toBeUndefined();
      expect(
        data.founderMorningBriefing.founder_loop_v1_product_proof_contract_ref,
      ).toBeUndefined();
    } finally {
      vi.unstubAllEnvs();
      vi.resetModules();
    }
  });

  it("does not backfill Morning Briefing V1 from mocks for partial backend responses", async () => {
    const partialBriefing = { ...mockControlCenterData.founderMorningBriefing };
    delete (
      partialBriefing as {
        morning_briefing_v1_read_model?: unknown;
      }
    ).morning_briefing_v1_read_model;
    delete (
      partialBriefing as {
        morning_briefing_v1_contract_ref?: unknown;
      }
    ).morning_briefing_v1_contract_ref;
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderMorningBriefing)) {
        return new Response(
          JSON.stringify({ ok: true, result: partialBriefing }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/briefing");
    render(<App />);

    expect(
      await screen.findByText("backend read model missing"),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(
        "contract-ref:product-loop-007-morning-briefing-v1:v1",
      ),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("python_core_morning_briefing_v1_read_model"),
    ).not.toBeInTheDocument();
  });

  it("fails closed for unsafe backend Morning Briefing V1 authority flags", async () => {
    const unsafeBriefing = {
      ...mockControlCenterData.founderMorningBriefing,
      morning_briefing_v1_read_model: {
        ...(mockControlCenterData.founderMorningBriefing
          .morning_briefing_v1_read_model ?? {}),
        connector_runtime_enabled: true,
      },
    };
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderMorningBriefing)) {
        return new Response(
          JSON.stringify({ ok: true, result: unsafeBriefing }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/briefing");
    render(<App />);

    expect(
      await screen.findByText("backend read model missing"),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(
        "contract-ref:product-loop-007-morning-briefing-v1:v1",
      ),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByLabelText("Backend-owned Morning Briefing V1 read model"),
    ).not.toBeInTheDocument();
  });

  it("renders backend-owned Weekly CEO Review V1 from backend data", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/evidence");
    render(<App />);

    const weeklyPanel = await screen.findByLabelText(
      "Backend-owned Weekly CEO Review V1 read model",
    );
    expect(
      within(weeklyPanel).getByRole("heading", {
        name: /Weekly CEO Review V1/i,
      }),
    ).toBeInTheDocument();
    expect(
      within(weeklyPanel).getByText(
        "contract-ref:product-loop-008-weekly-ceo-review-v1:v1",
      ),
    ).toBeInTheDocument();
    expect(
      within(weeklyPanel).getByText(
        "python_core_weekly_ceo_review_v1_read_model",
      ),
    ).toBeInTheDocument();
    expect(
      within(weeklyPanel).getByText("Model summaries").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(weeklyPanel).getByText("Production claim").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(weeklyPanel).getByText(
        "blocked-state:weekly-ceo-review-no-production-authority",
      ),
    ).toBeInTheDocument();
  });

  it("does not backfill Weekly CEO Review V1 from mocks for partial backend responses", async () => {
    const partialToday = { ...mockControlCenterData.founderToday };
    delete (
      partialToday as {
        weekly_ceo_review_v1_read_model?: unknown;
      }
    ).weekly_ceo_review_v1_read_model;
    delete (
      partialToday as {
        weekly_ceo_review_v1_contract_ref?: unknown;
      }
    ).weekly_ceo_review_v1_contract_ref;
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(
          JSON.stringify({ ok: true, result: partialToday }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/evidence");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Evidence Timeline/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Backend-owned Weekly CEO Review V1 read model"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(
        "contract-ref:product-loop-008-weekly-ceo-review-v1:v1",
      ),
    ).not.toBeInTheDocument();
  });

  it("fails closed for unsafe backend Weekly CEO Review V1 authority flags", async () => {
    const unsafeToday = {
      ...mockControlCenterData.founderToday,
      weekly_ceo_review_v1_read_model: {
        ...(mockControlCenterData.founderToday
          .weekly_ceo_review_v1_read_model ?? {}),
        model_summary_enabled: true,
      },
    };
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(JSON.stringify({ ok: true, result: unsafeToday }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/evidence");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Evidence Timeline/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Backend-owned Weekly CEO Review V1 read model"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(
        "contract-ref:product-loop-008-weekly-ceo-review-v1:v1",
      ),
    ).not.toBeInTheDocument();
  });

  it("fails closed for malformed Weekly CEO Review V1 status and event refs", async () => {
    const malformedToday = {
      ...mockControlCenterData.founderToday,
      weekly_ceo_review_v1_read_model: {
        ...(mockControlCenterData.founderToday
          .weekly_ceo_review_v1_read_model ?? {}),
        status: 42,
        evidence_event_refs: ["evidence-timeline-ref:wrong-namespace"],
        evidence_event_count: 1,
      },
    };
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(
          JSON.stringify({ ok: true, result: malformedToday }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/evidence");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Evidence Timeline/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Backend-owned Weekly CEO Review V1 read model"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("evidence-timeline-ref:wrong-namespace"),
    ).not.toBeInTheDocument();
  });

  it("renders backend-owned Chat to Loop handoff outcomes", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/chat");
    render(<App />);

    const handoffPanel = await screen.findByLabelText(
      "Backend-owned Chat to Loop handoff read model",
    );
    expect(
      within(handoffPanel).getByRole("heading", {
        name: /Chat to Loop Handoff/i,
      }),
    ).toBeInTheDocument();
    const handoffOutcomes = within(handoffPanel).getByLabelText(
      "Chat to Loop handoff outcomes",
    );
    for (const label of [
      "remember this",
      "create action",
      "add to plan",
      "defer",
      "ask human",
    ]) {
      expect(
        within(handoffOutcomes).getByText(new RegExp(label, "i")),
      ).toBeInTheDocument();
    }
    expect(
      within(handoffOutcomes).getByText(
        /^blocked: blocked_authority; Authority; blocked-state:chat-to-loop-no-action-execution$/i,
      ),
    ).toBeInTheDocument();
    expect(
      within(handoffPanel).getByText(
        "blocked-state:chat-to-loop-no-production-authority",
      ),
    ).toBeInTheDocument();
    expect(
      within(handoffPanel).getByText("Memory write").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(handoffPanel).getByText("Action execution").nextElementSibling,
    ).toHaveTextContent("blocked");
  });

  it("fails closed for unsafe Chat to Loop handoff payloads", async () => {
    const directMemoryWriteKey = "direct_memory_" + "write_authorized";
    const unsafeToday = {
      ...mockControlCenterData.founderToday,
      chat_to_loop_handoff_read_model: {
        ...(mockControlCenterData.founderToday
          .chat_to_loop_handoff_read_model ?? {}),
        [directMemoryWriteKey]: true,
      },
    };
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(JSON.stringify({ ok: true, result: unsafeToday }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/chat");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Chat Local Operator$/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Backend-owned Chat to Loop handoff read model"),
    ).not.toBeInTheDocument();
  });

  it("fails closed for unsafe Chat to Loop handoff refs", async () => {
    const unsafeToday = {
      ...mockControlCenterData.founderToday,
      chat_to_loop_handoff_read_model: {
        ...(mockControlCenterData.founderToday
          .chat_to_loop_handoff_read_model ?? {}),
        evidence_refs: ["evidence-ref:alice@example.com"],
      },
    };
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(JSON.stringify({ ok: true, result: unsafeToday }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/chat");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Chat Local Operator$/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Backend-owned Chat to Loop handoff read model"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("evidence-ref:alice@example.com"),
    ).not.toBeInTheDocument();
  });

  it("fails closed for unsafe Chat to Loop handoff rendered text", async () => {
    const unsafeToday = {
      ...mockControlCenterData.founderToday,
      chat_to_loop_handoff_read_model: {
        ...(mockControlCenterData.founderToday
          .chat_to_loop_handoff_read_model ?? {}),
        safe_summary: "Contains raw prompt material.",
      },
    };
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(JSON.stringify({ ok: true, result: unsafeToday }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/chat");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Chat Local Operator$/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Backend-owned Chat to Loop handoff read model"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("Contains raw prompt material."),
    ).not.toBeInTheDocument();
  });

  it("fails closed for malformed Chat to Loop handoff outcomes", async () => {
    const baseReadModel =
      mockControlCenterData.founderToday.chat_to_loop_handoff_read_model;
    const unsafeToday = {
      ...mockControlCenterData.founderToday,
      chat_to_loop_handoff_read_model: {
        ...(baseReadModel ?? {}),
        outcome_kinds: [
          ...((baseReadModel?.outcome_kinds ?? []) as string[]),
          "execute_action",
        ],
        outcomes: (baseReadModel?.outcomes ?? []).map((outcome, index) =>
          index === 0
            ? {
                ...outcome,
                target_surface: "Execution",
                proposal_ref: "proposal-ref:relative/path/project",
              }
            : outcome,
        ),
      },
    };
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(JSON.stringify({ ok: true, result: unsafeToday }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/chat");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Chat Local Operator$/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Backend-owned Chat to Loop handoff read model"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("proposal-ref:relative/path/project"),
    ).not.toBeInTheDocument();
  });

  it("does not backfill Chat to Loop handoff from mocks", async () => {
    const partialToday = { ...mockControlCenterData.founderToday };
    delete (
      partialToday as {
        chat_to_loop_handoff_read_model?: unknown;
      }
    ).chat_to_loop_handoff_read_model;
    delete (
      partialToday as {
        chat_to_loop_handoff_contract_ref?: unknown;
      }
    ).chat_to_loop_handoff_contract_ref;
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(
          JSON.stringify({ ok: true, result: partialToday }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/chat");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Chat Local Operator$/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Backend-owned Chat to Loop handoff read model"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(
        "contract-ref:product-loop-009-chat-to-loop-handoff:v1",
      ),
    ).not.toBeInTheDocument();
  });

  it("does not backfill Action Inbox decision lanes from mocks", async () => {
    const partialInbox = { ...mockControlCenterData.founderActionsInbox };
    delete (
      partialInbox as {
        action_inbox_decision_lane_read_model?: unknown;
      }
    ).action_inbox_decision_lane_read_model;
    delete (
      partialInbox as {
        action_inbox_decision_lane_contract_ref?: unknown;
      }
    ).action_inbox_decision_lane_contract_ref;
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderActionsInbox)) {
        return new Response(
          JSON.stringify({ ok: true, result: partialInbox }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/actions");
    render(<App />);

    expect(
      await screen.findByText("backend decision lanes missing"),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(
        "contract-ref:product-loop-005-action-inbox-decision-lanes:v1",
      ),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("python_core_action_inbox_decision_lane_read_model"),
    ).not.toBeInTheDocument();
  });

  it("renders the Plans to Actions bridge only from a safe backend read model", async () => {
    const bridge = plansToActionsBridgeFixture();
    const inbox = {
      ...mockControlCenterData.founderActionsInbox,
      plans_to_actions_bridge_contract_ref:
        "contract-ref:product-loop-006-plans-to-reviewable-action-envelopes:v1",
      plans_to_actions_bridge_read_model: bridge,
    };
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderActionsInbox)) {
        return new Response(JSON.stringify({ ok: true, result: inbox }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/actions");
    render(<App />);

    const bridgePanel = await screen.findByLabelText(
      "Plans to reviewable Action envelopes",
    );
    expect(
      within(bridgePanel).getByText(
        "contract-ref:product-loop-006-plans-to-reviewable-action-envelopes:v1",
      ),
    ).toBeInTheDocument();
    expect(
      within(bridgePanel).getByText(
        "python_core_plans_to_actions_bridge_read_model",
      ),
    ).toBeInTheDocument();
    expect(
      within(bridgePanel).getAllByText("decision receipt option: approve")
        .length,
    ).toBeGreaterThan(0);
    expect(
      within(bridgePanel).getByText(
        "receipt-plan:plans-action-envelope:plan-summary-test",
      ),
    ).toBeInTheDocument();
    expect(
      within(bridgePanel).getByText(
        "rollback-plan:plans-action-envelope:plan-summary-test",
      ),
    ).toBeInTheDocument();
    expect(
      within(bridgePanel).getByText(
        "safe-disable:plans-action-envelope:plan-summary-test",
      ),
    ).toBeInTheDocument();
    expect(
      within(bridgePanel).queryByRole("button", {
        name: /execute|run|apply|commit/i,
      }),
    ).not.toBeInTheDocument();
  });

  it("renders fusion routing and delegation readability from backend contracts", async () => {
    const fusionReadModel = fusionRoutingReadModelFixture();
    const bridge = plansToActionsBridgeFixture();
    const workClassification = fusionWorkClassificationFixture("validation");
    (bridge as Record<string, unknown>).items = [
      {
        ...(bridge.items[0] as Record<string, unknown>),
        work_classification: workClassification,
        delegation_proposal: fusionDelegationFixture(workClassification),
        cache_context_economics: fusionCacheContextFixture(),
      },
    ];
    const today = {
      ...mockControlCenterData.founderToday,
      fusion_routing_delegation_contract_ref:
        "contract-ref:fcc-fusion-routing-delegation:v1",
      fusion_routing_delegation_read_model: fusionReadModel,
      plans_to_actions_bridge_contract_ref:
        "contract-ref:product-loop-006-plans-to-reviewable-action-envelopes:v1",
      plans_to_actions_bridge_read_model: bridge,
    };
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(JSON.stringify({ ok: true, result: today }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/today");
    render(<App />);

    const fusionPanels = await screen.findAllByLabelText(
      "Fusion routing and delegation readability",
    );
    const fusionPanel = fusionPanels[0];
    expect(fusionPanel).toHaveTextContent(
      "contract-ref:fcc-fusion-routing-delegation:v1",
    );
    expect(fusionPanel).toHaveTextContent(
      "python_core_fusion_routing_delegation_read_model",
    );
    expect(fusionPanel).toHaveTextContent("Sidekick executionblocked");
    expect(fusionPanel).toHaveTextContent("Provider/model callsblocked");
    expect(fusionPanel).toHaveTextContent("Work type judgment required");
    expect(fusionPanel).toHaveTextContent("Work type mechanical");
    expect(fusionPanel).toHaveTextContent("Work type validation");
    expect(fusionPanel).toHaveTextContent("Work type ambiguous");
    expect(fusionPanel).toHaveTextContent("Work type blocked");
    expect(fusionPanel).toHaveTextContent(
      "selected: Local preview route selected",
    );
    expect(fusionPanel).toHaveTextContent(
      "rejected: Disabled profile rejected",
    );
    expect(fusionPanel).toHaveTextContent(
      "blocked: Paid route blocked until exact approval exists.",
    );
    expect(
      within(fusionPanel).queryByRole("button", {
        name: /execute|run|apply|commit|delegate|switch/i,
      }),
    ).not.toBeInTheDocument();

    const metadataCards = await screen.findAllByLabelText(
      "Fusion routing metadata",
    );
    expect(metadataCards[0]).toHaveTextContent("Work typevalidation");
    expect(metadataCards[0]).toHaveTextContent(
      "Proposed delegatevalidation_worker",
    );
    expect(metadataCards[0]).toHaveTextContent("Worker executionblocked");
    expect(metadataCards[0]).toHaveTextContent("Runtime model switchblocked");
  });

  it("fails closed for unsafe fusion routing readability payloads", async () => {
    const unsafeReadModel = {
      ...fusionRoutingReadModelFixture(),
      provider_model_call_enabled: true,
    };
    const today = {
      ...mockControlCenterData.founderToday,
      fusion_routing_delegation_contract_ref:
        "contract-ref:fcc-fusion-routing-delegation:v1",
      fusion_routing_delegation_read_model: unsafeReadModel,
    };
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(JSON.stringify({ ok: true, result: today }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/today");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Today$/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Fusion routing and delegation readability"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("python_core_fusion_routing_delegation_read_model"),
    ).not.toBeInTheDocument();
  });

  it("fails closed when the Plans-to-Actions bridge is missing or unsafe", async () => {
    const unsafeBridge = plansToActionsBridgeFixture({
      action_execution_enabled: true,
    });
    const inbox = {
      ...mockControlCenterData.founderActionsInbox,
      plans_to_actions_bridge_contract_ref:
        "contract-ref:product-loop-006-plans-to-reviewable-action-envelopes:v1",
      plans_to_actions_bridge_read_model: unsafeBridge,
    };
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderActionsInbox)) {
        return new Response(JSON.stringify({ ok: true, result: inbox }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/actions");
    render(<App />);

    expect(
      (await screen.findAllByText("backend bridge missing")).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByText(
        "contract-ref:product-loop-006-plans-to-reviewable-action-envelopes:v1",
      ),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("python_core_plans_to_actions_bridge_read_model"),
    ).not.toBeInTheDocument();
  });

  it("fails closed when the Action Inbox work queue exposes unsafe controls", async () => {
    const unsafeWorkQueue = {
      ...cloneForTest(
        mockControlCenterData.founderActionsInbox.action_inbox_work_queue_read_model,
      ),
      source: "python_core_action_inbox_work_queue_read_model",
      backend_owned: true,
      status: "implemented_backend_owned_action_inbox_work_queue",
      fake_mutation_controls_exposed: true,
      work_items: [
        {
          ...cloneForTest(
            mockControlCenterData.founderActionsInbox
              .action_inbox_work_queue_read_model!.work_items[0],
          ),
          proof_ref: "proof-ref:action-decision:unsafe-work-queue-test",
          fake_mutation_control_exposed: true,
        },
      ],
      work_item_count: 1,
      work_item_refs: ["founder-action:mock-local-task-review"],
    };
    const inbox = {
      ...mockControlCenterData.founderActionsInbox,
      action_inbox_work_queue_contract_ref:
        "contract-ref:usable-authority-action-inbox-work-queue:v1",
      action_inbox_work_queue_read_model: unsafeWorkQueue,
    };
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderActionsInbox)) {
        return new Response(JSON.stringify({ ok: true, result: inbox }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/actions");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Action Inbox$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Action Inbox queue posture is unavailable. The UI will not infer durable queue truth from filters, local state, or mock lane data."),
    ).toBeInTheDocument();
    expect(
      screen.queryByText("proof-ref:action-decision:unsafe-work-queue-test"),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("Fake controls")).not.toBeInTheDocument();
  });

  it("fails closed when a Plans-to-Actions bridge item carries unsafe fields", async () => {
    const unsafeBridge = plansToActionsBridgeFixture();
    unsafeBridge.items = [
      {
        ...unsafeBridge.items[0],
        raw_content_included: true,
        action_execution_enabled: true,
      },
    ];
    const inbox = {
      ...mockControlCenterData.founderActionsInbox,
      plans_to_actions_bridge_contract_ref:
        "contract-ref:product-loop-006-plans-to-reviewable-action-envelopes:v1",
      plans_to_actions_bridge_read_model: unsafeBridge,
    };
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderActionsInbox)) {
        return new Response(JSON.stringify({ ok: true, result: inbox }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/actions");
    render(<App />);

    expect(
      (await screen.findAllByText("backend bridge missing")).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByText("python_core_plans_to_actions_bridge_read_model"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("decision receipt option: approve"),
    ).not.toBeInTheDocument();
  });

  it("does not backfill mock plan Action envelope posture when the bridge is missing", async () => {
    const partialToday = { ...mockControlCenterData.founderToday };
    delete (partialToday as { plans_to_actions_bridge_read_model?: unknown })
      .plans_to_actions_bridge_read_model;
    delete (partialToday as { plans_to_actions_bridge_contract_ref?: unknown })
      .plans_to_actions_bridge_contract_ref;
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(
          JSON.stringify({ ok: true, result: partialToday }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/today");
    render(<App />);

    expect(
      (await screen.findAllByText("backend bridge missing")).length,
    ).toBeGreaterThan(0);
    const planHeadings = await screen.findAllByRole("heading", {
      name: "Plans",
    });
    const plansPanel = planHeadings[0].closest("article");
    expect(plansPanel).toBeTruthy();
    expect(
      within(plansPanel as HTMLElement).queryByText(
        "contract-ref:plans-action-envelope:v1",
      ),
    ).not.toBeInTheDocument();
    expect(
      within(plansPanel as HTMLElement).queryByText(
        "action-envelope:plans:plan-summary-founder-loop-v1",
      ),
    ).not.toBeInTheDocument();
  });

  it("renders backend follow-up tracker even when the Today loop digest is absent", async () => {
    const partialToday = { ...mockControlCenterData.founderToday };
    delete (partialToday as { today_loop_read_model?: unknown })
      .today_loop_read_model;
    delete (partialToday as { today_loop_tightening_contract_ref?: unknown })
      .today_loop_tightening_contract_ref;
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(
          JSON.stringify({ ok: true, result: partialToday }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/today");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Today$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("backend digest missing").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("contract-ref:product-loop-004-follow-up-tracker:v1"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("python_core_follow_up_tracker_read_model"),
    ).toBeInTheDocument();
  });

  it("renders the Today loop digest only from the backend Today endpoint", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderTodaySummary)) {
        return new Response(
          JSON.stringify({
            ok: true,
            result: mockControlCenterData.founderToday,
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/today");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Today$/i }),
    ).toBeInTheDocument();
    const todayDigest = await screen.findByLabelText(
      "Backend-owned Today loop digest",
    );
    expect(
      within(todayDigest).getByText(
        "contract-ref:product-loop-003-today-loop-tightening:v1",
      ),
    ).toBeInTheDocument();
    expect(
      within(todayDigest).getByText("python_core_today_loop_read_model"),
    ).toBeInTheDocument();
    expect(
      within(todayDigest).getByText("What matters now").nextElementSibling,
    ).toHaveTextContent("founder-action:mock-setup-hardening");
    expect(
      screen.getByText(/Needs review: 2; ready_for_review/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Blocked now: 2; ready_for_review/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Changed: 2; ready_for_review/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Follow-ups: 1; ready_for_review/i),
    ).toBeInTheDocument();
    expect(
      within(todayDigest).getByText("Action execution").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(todayDigest).getByText("Connector runtime").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(todayDigest).getByText("Runtime model calls").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      screen.getByText("contract-ref:product-loop-004-follow-up-tracker:v1"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("python_core_follow_up_tracker_read_model"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Message send/i)[0].nextElementSibling,
    ).toHaveTextContent("blocked");
    for (const label of [
      "Reminder scheduler",
      "Connector reads",
      "Connector writes",
      "Email/calendar fetch",
      "Task creation",
      "Runtime model calls",
      "Hidden memory write",
      "Context injection",
      "Production authority",
    ]) {
      expect(
        screen.getAllByText(label)[0].nextElementSibling,
      ).toHaveTextContent("blocked");
    }
    expect(screen.getByText("Relationship follow-ups: 1")).toBeInTheDocument();
    expect(screen.getByText("Promises: 1")).toBeInTheDocument();
    expect(screen.getByText("Pending replies: 1")).toBeInTheDocument();
    expect(
      screen.getAllByText("No-source state")[0].nextElementSibling,
    ).toHaveTextContent("no");
    expect(
      screen.getAllByText("Local review only")[0].nextElementSibling,
    ).toHaveTextContent("yes");
  });

  it("opens Morning Briefing as the daily local home without new authority", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/briefing");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Morning Briefing$/i }),
    ).toBeInTheDocument();
    const briefingV1Panel = screen.getByLabelText(
      "Backend-owned Morning Briefing V1 read model",
    );
    expect(
      within(briefingV1Panel).getByText(
        "contract-ref:product-loop-007-morning-briefing-v1:v1",
      ),
    ).toBeInTheDocument();
    expect(
      within(briefingV1Panel).getByText("Connector runtime").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(briefingV1Panel).getByText("Email/calendar fetch")
        .nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(briefingV1Panel).getByText("Automatic recommendations")
        .nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(briefingV1Panel).getByText("Repo write").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(briefingV1Panel).getByText("Workbench apply").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(briefingV1Panel).getByText("Authority boundary"),
    ).toBeInTheDocument();
    expect(
      within(briefingV1Panel).getByText("founder-action:mock-setup-hardening"),
    ).toBeInTheDocument();
    expect(
      within(briefingV1Panel).getByText(
        "memory-review:founder-loop-preferences",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Briefing daily loop/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Daily command loop/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("Home").nextElementSibling).toHaveTextContent(
      "Morning Briefing",
    );
    expect(
      screen.getByRole("heading", { name: /Source readiness states/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/calendar: not_configured/i)).toBeInTheDocument();
    expect(screen.getByText(/inbox: blocked/i)).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /CRM-lite follow-ups/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Memory why shown/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Dogfood capture/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Weekly Review narrative/i }),
    ).toBeInTheDocument();
    expect(
      screen
        .getAllByText("Action execution")
        .some((node) =>
          node.nextElementSibling?.textContent?.includes("blocked"),
        ),
    ).toBe(true);
    expect(
      screen.getByText("Public beta claim").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      screen.queryByRole("button", {
        name: /approve|run|send|write|sync|execute/i,
      }),
    ).not.toBeInTheDocument();
  });

  it("creates a Today Action envelope through the exact receipt route", async () => {
    const receipt = {
      contract_ref: "contract-ref:founder-loop-v1-vertical-slice:v1",
      today_item_ref: "briefing:storage-state-first-loop",
      item_ref: "founder-action:today-promotion:storage-state-first-loop",
      action_envelope_ref:
        "action-envelope:founder-loop-v1:storage-state-first-loop",
      status: "action_envelope_created",
      receipt_ref: "receipt:today-action-envelope:storage-state-first-loop",
      audit_ref: "audit:today-action-envelope:storage-state-first-loop",
      idempotency_key_ref: "idempotency-ref:control-center-today-action:test",
      payload_fingerprint_ref: "payload-fingerprint-ref:test",
      evidence_timeline_event_ref:
        "evidence-timeline-event:today-action-envelope:storage-state-first-loop",
      action_executed: false,
      approval_grants_execution: false,
      connector_write_performed: false,
      memory_write_performed: false,
      raw_content_stored: false,
      replayed: false,
      safe_summary:
        "Reviewable Action envelope created; execution remains blocked.",
      evidence_refs: ["evidence-ref:founder-loop:today-action-envelope"],
      blocked_state_refs: ["blocked-state:no-action-execution"],
      created_at: "2026-06-22T00:00:00Z",
    };
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      if (
        options?.method === "POST" &&
        String(url) === API_ENDPOINTS.founderTodayActionEnvelope
      ) {
        return new Response(JSON.stringify({ ok: true, result: receipt }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      const urlText = String(url);
      if (
        !options?.method &&
        READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error("backend unavailable");
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/today");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Today$/i }),
    ).toBeInTheDocument();
    const actionEnvelopeButtons = screen.getAllByRole("button", {
      name: /Record Action-envelope receipt/i,
    });
    fireEvent.click(actionEnvelopeButtons[1]);

    await screen.findByText(
      "receipt:today-action-envelope:storage-state-first-loop",
    );
    const [, options] =
      fetchMock.mock.calls.find((call) => call[1]?.method === "POST") ?? [];
    expect(fetchMock).toHaveBeenCalledWith(
      API_ENDPOINTS.founderTodayActionEnvelope,
      expect.any(Object),
    );
    expect(options?.method).toBe("POST");
    expect(options?.headers).toMatchObject({
      Accept: "application/json",
      "Content-Type": "application/json",
    });
    expect(
      String(
        (options?.headers as Record<string, string>)["X-UAA-Idempotency-Key"],
      ),
    ).toMatch(/^idempotency-ref:control-center-today-action:/);
    expect(JSON.parse(String(options?.body))).toMatchObject({
      today_item_ref: "briefing:storage-state-first-loop",
      actor_context: "control_center_today_surface",
      decision_reason_ref: "decision-reason-ref:today-action-envelope",
    });
    expect(
      screen.getByText("audit:today-action-envelope:storage-state-first-loop"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "evidence-timeline-event:today-action-envelope:storage-state-first-loop",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^execute$/i }),
    ).not.toBeInTheDocument();
  });

  it("records a Chat durable receipt and reviewable handoff with safe refs only", async () => {
    const chatReceipt = {
      contract_ref: "contract-ref:founder-loop-chat-durable-receipt:v1",
      turn_ref: "chat-turn:local-operator:uaa-llama-cpp-local",
      route_ref: API_ENDPOINTS.localChatCompletions,
      model_ref: "model-ref:uaa-llama-cpp-local",
      runtime_truth: "local-chat-route-answered",
      auth_truth: "local-bearer-accepted",
      tool_denial_truth: "tools-functions-streaming-denied",
      safe_summary_ref: "safe-summary-ref:control-center-chat-probe",
      handoff_refs: [
        "handoff-ref:chat-to-actions:uaa-llama-cpp-local",
        "handoff-ref:chat-to-plans:uaa-llama-cpp-local",
      ],
      receipt_ref: "receipt:chat-turn:control-center-test",
      evidence_ref: "evidence-ref:chat-turn:control-center-test",
      idempotency_key_ref: "idempotency-ref:control-center-chat-turn:test",
      payload_fingerprint_ref: "payload-fingerprint:chat-durable-receipt:test",
      evidence_refs: ["evidence-ref:control-center-chat-probe"],
      blocked_state_refs: [
        "blocked-state:no-model-output-authority",
        "blocked-state:no-tool-execution",
        "blocked-state:no-memory-write",
        "blocked-state:no-context-injection",
        "blocked-state:no-provider-sdk-call",
        "blocked-state:no-web-fetch",
        "blocked-state:no-connector-write",
        "blocked-state:no-shell-subprocess-execution",
        "blocked-state:no-action-execution",
        "blocked-state:no-approval-grant-capture",
        "blocked-state:no-production-authority",
      ],
      response_visible: false,
      prompt_body_visible: false,
      completion_body_visible: false,
      model_output_authority: false,
      tool_execution_enabled: false,
      memory_write_authorized: false,
      context_injection_authorized: false,
      provider_sdk_call_enabled: false,
      web_fetch_enabled: false,
      connector_write_enabled: false,
      shell_subprocess_execution_enabled: false,
      action_execution_enabled: false,
      approval_grant_capture_enabled: false,
      production_authority_enabled: false,
      replayed: false,
      created_at: "2026-06-22T00:00:00Z",
    };
    const handoffReceipt = {
      contract_ref: "contract-ref:founder-loop-chat-durable-receipt:v1",
      turn_ref: chatReceipt.turn_ref,
      handoff_target: "actions",
      handoff_ref: "handoff-ref:chat-to-actions:control-center-test",
      created_ref: "founder-action:chat-handoff:control-center-test",
      receipt_ref: "receipt:chat-handoff:control-center-test",
      audit_ref: "audit:chat-handoff:control-center-test",
      evidence_ref: "evidence-ref:chat-handoff:control-center-test",
      idempotency_key_ref:
        "idempotency-ref:control-center-chat-handoff:actions:test",
      payload_fingerprint_ref:
        "payload-fingerprint:chat-durable-receipt:handoff-test",
      safe_summary_ref: "safe-summary-ref:chat-handoff:control-center-test",
      evidence_refs: ["evidence-ref:chat-handoff:control-center-test"],
      blocked_state_refs: ["blocked-state:no-action-execution"],
      action_executed: false,
      plan_executed: false,
      connector_write_performed: false,
      memory_write_performed: false,
      model_output_authority: false,
      context_injection_authorized: false,
      production_authority_enabled: false,
      replayed: false,
      created_at: "2026-06-22T00:00:00Z",
    };
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      const urlText = String(url);
      if (
        !options?.method &&
        READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (!options?.method && urlText.endsWith(API_ENDPOINTS.localModels)) {
        return new Response(
          JSON.stringify({ data: [{ id: "uaa-llama-cpp-local" }] }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (
        options?.method === "POST" &&
        urlText.endsWith(API_ENDPOINTS.localChatCompletions)
      ) {
        return new Response(
          JSON.stringify({
            ok: true,
            result: {
              id: "chatcmpl-safe-probe",
              uaa_safety: {
                tool_executed: false,
                tools_enabled: false,
                functions_enabled: false,
                streaming_enabled: false,
              },
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (
        options?.method === "POST" &&
        urlText.endsWith(API_ENDPOINTS.controlCenterChatTurns)
      ) {
        return new Response(JSON.stringify({ ok: true, result: chatReceipt }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (
        !options?.method &&
        urlText.endsWith(chatTurnReceiptEndpoint(chatReceipt.turn_ref))
      ) {
        return new Response(JSON.stringify({ ok: true, result: chatReceipt }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (
        options?.method === "POST" &&
        urlText.endsWith(chatTurnHandoffEndpoint(chatReceipt.turn_ref))
      ) {
        return new Response(
          JSON.stringify({ ok: true, result: handoffReceipt }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/chat");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Chat Local Operator$/i }),
    ).toBeInTheDocument();
    fireEvent.click(
      await screen.findByRole("button", {
        name: /Probe redacted local turn/i,
      }),
    );

    await screen.findByText("receipt:chat-turn:control-center-test");
    const [, receiptOptions] =
      fetchMock.mock.calls.find(
        ([url, options]) =>
          options?.method === "POST" &&
          String(url).endsWith(API_ENDPOINTS.controlCenterChatTurns),
      ) ?? [];
    expect(receiptOptions?.headers).toMatchObject({
      "X-UAA-Idempotency-Key": expect.stringMatching(
        /^idempotency-ref:control-center-chat-turn:/,
      ),
    });
    const receiptBody = JSON.stringify(
      JSON.parse(String(receiptOptions?.body)),
    );
    expect(receiptBody).toContain("model-ref:uaa-llama-cpp-local");
    expect(receiptBody).not.toContain("messages");
    expect(receiptBody).not.toContain("content");
    expect(receiptBody).not.toContain("raw");

    fireEvent.click(
      await screen.findByRole("button", { name: /Record actions proposal/i }),
    );

    await screen.findByText("receipt:chat-handoff:control-center-test");
    expect(
      screen.getByText("founder-action:chat-handoff:control-center-test"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("blocked").length).toBeGreaterThan(0);
    const [, handoffOptions] =
      fetchMock.mock.calls.find(
        ([url, options]) =>
          options?.method === "POST" &&
          String(url).endsWith(chatTurnHandoffEndpoint(chatReceipt.turn_ref)),
      ) ?? [];
    expect(handoffOptions?.headers).toMatchObject({
      "X-UAA-Idempotency-Key": expect.stringMatching(
        /^idempotency-ref:control-center-chat-handoff:actions:/,
      ),
    });
    expect(JSON.parse(String(handoffOptions?.body))).toMatchObject({
      handoff_target: "actions",
      decision_reason_ref: "decision-reason-ref:control-center-chat-actions",
    });
  });

  it("renders runtime, remote, mobile, and plugin governance panels as safe summaries", async () => {
    mockFetchWithFallback();

    window.history.pushState({}, "", "/runtime");
    const { unmount } = render(<App />);
    expect(await screen.findByText("Capability Matrix")).toBeInTheDocument();
    expect(screen.getByText("cloud_provider_runtime")).toBeInTheDocument();
    unmount();

    window.history.pushState({}, "", "/remote-workers");
    const remote = render(<App />);
    expect(await screen.findByText("Remote workers")).toBeInTheDocument();
    expect(screen.getByText("Private mesh")).toBeInTheDocument();
    remote.unmount();

    window.history.pushState({}, "", "/mobile-planning");
    const mobile = render(<App />);
    expect(await screen.findByText("Mobile Planning")).toBeInTheDocument();
    expect(screen.getByText(/Sensor access enabled: no/i)).toBeInTheDocument();
    mobile.unmount();

    window.history.pushState({}, "", "/plugin-governance");
    render(<App />);
    expect(await screen.findByText("Plugin Governance")).toBeInTheDocument();
    expect(
      screen.getByText(/Plugin enablement allowed: no/i),
    ).toBeInTheDocument();
  });

  it("renders clear headings for every local shell page", async () => {
    const expectedHeadings = [
      ["/", /Dashboard overview/i],
      ["/today", /^Today$/i],
      ["/inbox", /^Source Inbox$/i],
      ["/actions", /^Action Inbox$/i],
      ["/briefing", /Morning Briefing/i],
      ["/crm", /CRM M1 fixture-only shell/i],
      ["/private-trial", /Private Operator Trial/i],
      ["/setup", /macOS Setup Assistant/i],
      ["/dashboard", /Dashboard overview/i],
      ["/operator-loop", /Operator Loop/i],
      ["/differentiators", /Control Center Differentiators/i],
      ["/chat", /^Chat Local Operator$/i],
      ["/plans", /^Plans$/i],
      ["/models", /^Models$/i],
      ["/runtime", /Runtime readiness/i],
      ["/foundation-gate", /Foundation Gate/i],
      ["/api-routes", /API Routes/i],
      ["/approvals", /Approval Queue/i],
      ["/receipts", /Receipt Viewer/i],
      ["/events", /Event Viewer/i],
      ["/events/timeline", /Event Timeline/i],
      ["/evidence", /Evidence Viewer/i],
      ["/files", /File Reference Viewer/i],
      ["/files/review", /File Review Surface/i],
      ["/context/proposals", /Context Proposal Surface/i],
      ["/memory", /^Memory Review$/i],
      ["/storage", /^Storage$/i],
      ["/runtime/local", /Local Runtime Status/i],
      ["/runtime/manual-smoke", /Manual Smoke Control Surface/i],
      ["/remote-workers", /Remote worker boundary/i],
      ["/mobile-planning", /Mobile planning/i],
      ["/plugin-governance", /Plugin governance/i],
      ["/settings", /^Settings$/i],
      ["/action-preview", /Action Preview/i],
    ] as const;

    for (const [path, heading] of expectedHeadings) {
      mockFetchWithFallback();
      window.history.pushState({}, "", path);
      const { unmount } = render(<App />);
      expect(
        await screen.findByRole("heading", { name: heading }),
      ).toBeInTheDocument();
      unmount();
      vi.unstubAllGlobals();
    }
  });

  it("renders API route classification posture", async () => {
    window.history.pushState({}, "", "/api-routes");
    render(<App />);

    expect(await screen.findByText("API Routes")).toBeInTheDocument();
    expect(screen.getByText("Classification")).toBeInTheDocument();
    expect(screen.getAllByText(/local_readonly/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Classification is posture evidence only/i),
    ).toBeInTheDocument();
  });

  it("renders Inbox as a blocked planned triage surface without connector authority", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, options?: RequestInit) => {
        const urlText = String(url);
        if (
          !options?.method &&
          READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))
        ) {
          return new Response(
            JSON.stringify(envelopeForReadEndpoint(urlText)),
            {
              status: 200,
              headers: { "Content-Type": "application/json" },
            },
          );
        }
        throw new Error("unexpected connector authority call");
      }),
    );
    window.history.pushState({}, "", "/inbox");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Source Inbox$/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("blocked/planned").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Route posture/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("/inbox")).toBeInTheDocument();
    expect(
      screen.getAllByText("/control-center/sources/readiness").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("local_dev_workspace_only")).toBeInTheDocument();
    expect(
      screen.getByText("not required for read-only source readiness"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Source readiness states/i }),
    ).toBeInTheDocument();
    const routePosture = screen.getByLabelText(
      "Dedicated source readiness route",
    );
    expect(routePosture).toHaveTextContent("backend-owned");
    expect(
      within(routePosture).getByText("Account auth").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(routePosture).getByText("Raw source ingestion").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      within(routePosture).getByText("Write authority").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      screen.getByText(/live email, calendar, account, polling/i),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:email-read-only-missing").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", {
        name: /Define email read-only metadata contract/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("proposal-kind:read-only-email-metadata-contract"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "source-readiness-proposal:email-read-only-metadata-contract",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("proposal_only_no_execution_path"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("blocked-state:no-account-auth").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(/docs\/control_center\/OPERATOR_SHELL_GAP_MAP.md/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/docs\/strategy\/FOUNDER_COMMAND_CENTER_MVP_SPEC.md/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/email\/calendar connector runtime is not scoped/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Connector draft proposals/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("draft_proposals_ready_no_send_write"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("contract-ref:connector-draft-only-proposals:v1"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("python_core_connector_draft_proposal_read_model"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("connector-draft-proposal-ref:email-response"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("connector-draft-proposal-ref:calendar-event"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("blocked; future exact lane required").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(
        /connector draft proposals are review-only safe refs; send and write remain blocked/i,
      ),
    ).toBeInTheDocument();
    for (const forbiddenControl of [
      /send/i,
      /archive/i,
      /delete/i,
      /calendar write/i,
      /sync/i,
      /oauth/i,
      /authorize/i,
      /connect account/i,
      /sign in/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: forbiddenControl }),
      ).not.toBeInTheDocument();
    }

    for (const label of [
      /^send$/i,
      /^archive$/i,
      /^delete$/i,
      /^connect$/i,
      /^write$/i,
      /^approve$/i,
      /^run$/i,
      /^install$/i,
      /^sync$/i,
      /^oauth$/i,
      /^authorize$/i,
      /^connect account$/i,
      /^sign in$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
  });

  it("renders Private Trial packet as local safe refs without full beta claims", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/private-trial");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Private Operator Trial/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("local/private only")).toBeInTheDocument();
    expect(screen.getByText("milestone:uaa-p1-087.2a")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Full UAA-P1-087.2 still needs accepted or revised local\/private findings later/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("contract-ref:private-operator-ui-functional-tuning:v1"),
    ).toBeInTheDocument();
    expect(screen.getByText("milestone:uaa-p1-087.2b")).toBeInTheDocument();
    expect(
      screen.getAllByText("ledger-ref:private-operator-trial-acceptance:v1")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Acceptance ledger/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("operator_review_ready")).toBeInTheDocument();
    expect(
      screen.getByText("manual-smoke-step:private-trial:boot-control-center"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("acceptance-question:private-trial:memory-confidence"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "tuning-decision:private-trial:pending-memory-review-emphasis",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("finding-ref:private-trial:pending:crm-lite-follow-ups"),
    ).toBeInTheDocument();
    expect(screen.getByText("milestone:uaa-p1-087.2c")).toBeInTheDocument();
    expect(
      screen.getByText("scaffold-ref:private-operator-trial-manual-review:v1"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("manual_review_deferred_pending_implementation"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("unanswered_pending_manual_review").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("pending-answer:private-trial:crm-lite-follow-ups"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "missing-implementation:founder-loop:action-decision-receipts",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("launcher-command:uaa-trial-boot"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Authority boundary/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("blocked-state:no-public-beta"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("blocked-state:no-production-authority"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("blocked-state:openwebui-secondary-only"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("private-trial-check:local-boot"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("private-trial-check:crm-lite-follow-ups"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("friction-ref:private-trial:blocked-state-language")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("gap-ref:private-trial:crm-lite-local-follow-up-store"),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /approve|run|send|write|sync|execute/i,
      }),
    ).not.toBeInTheDocument();
  });

  it("renders Action Inbox decision receipt posture without action execution", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/actions");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Action Inbox$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /State posture/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("/control-center/actions/inbox").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("Action execution remains blocked"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("GET /control-center/actions/{action_id}/receipt"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Local prerequisites/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("GET /control-center/storage/status"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("status-ref:control-center-route-manifest"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("capability-ref:local-approval-authority"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Provider cost authority posture/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Unknown paid cost/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/COST_ESTIMATE_REF_REQUIRED/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/BUDGET_DECISION_REF_REQUIRED/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /^Ready for decision$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /^Approved local-task create lane$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /^Blocked by authority$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /^Expired\/stale$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /^Receipt recorded$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: /^Proposal-only \/ no execution path$/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("ready_for_decision").length).toBeGreaterThan(0);
    expect(
      screen.queryByText("approved_local_task_lane"),
    ).not.toBeInTheDocument();
    expect(screen.getAllByText("blocked_by_authority").length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText("proposal_only_no_execution_path").length,
    ).toBeGreaterThan(0);

    expect(
      screen.getByText("approval-envelope:founder-loop:mock-setup-hardening"),
    ).toBeInTheDocument();
    expect(screen.getByText("dry_run_ref_available")).toBeInTheDocument();
    expect(
      screen.getAllByRole("heading", {
        name: /^Approval Envelope Unavailable$/i,
      }).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "contract-ref:founder-loop-action-approval-envelope:v1",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/mock_fallback_non_authoritative/).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByText(/python_core_action_inbox_read_model/),
    ).not.toBeInTheDocument();
    expect(screen.getAllByText("local_task_create").length).toBeGreaterThan(0);
    expect(screen.getAllByText("not_applicable").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("backend_read_model_unavailable").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("mock_only_backend_read_model_unavailable").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("blocked-state:no-connector-write").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("evidence-ref:founder-loop:local-task-commit").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByRole("heading", {
        name: /^Receipt Visibility Unavailable$/i,
      }).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "contract-ref:founder-loop-action-receipt-visibility:v1",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "local_task_commit_receipt_ref:backend_read_model_unavailable",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByText(
        "receipt:founder-loop-action:mock-local-task-create:approve",
      ),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(
        "evidence-event:action-decision-recorded-evidence-timeline-action-founder-action-mock-local-task-create",
      ),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("decision_idempotency_replay_available"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("decision_conflicting_idempotency_payload_rejected"),
    ).not.toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:founder-loop:mock-setup-hardening")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("blocked_pending_scoped_mutation_contract"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Cost blocked").length).toBeGreaterThan(0);
    expect(screen.getAllByText("No provider authority").length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText("Unknown paid cost").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("receipt-plan:founder-loop:mock-setup-hardening")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("audit-plan:founder-loop:mock-setup-hardening"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("idempotency-ref:founder-loop:mock-setup-hardening")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("rollback-plan:founder-loop:mock-setup-hardening")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("safe-disable:founder-loop:mock-setup-hardening")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("contract-ref:founder-loop-action-state-machine:v1")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: /Record approval/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Record edit/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Record rejection/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Record defer/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /Create local task record/i,
      }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(
        /Decision controls unavailable until the local backend supplies/i,
      ),
    ).toBeInTheDocument();
    const blockedLane = screen
      .getByRole("heading", { name: /^Blocked by authority$/i })
      .closest("section");
    expect(blockedLane).not.toBeNull();
    expect(
      within(blockedLane as HTMLElement).queryByRole("button", {
        name: /Record approval|Create local task record/i,
      }),
    ).not.toBeInTheDocument();
    const proposalLane = screen
      .getByRole("heading", { name: /^Proposal-only \/ no execution path$/i })
      .closest("section");
    expect(proposalLane).not.toBeNull();
    expect(
      within(proposalLane as HTMLElement).queryByRole("button", {
        name: /Record approval|Create local task record/i,
      }),
    ).not.toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:founder-loop-local-task-commit:v1")
        .length,
    ).toBeGreaterThan(0);
    expect(document.body.textContent).toContain(
      "POST /control-center/actions/{action_id}/local-task/commit",
    );
    expect(
      screen.getByRole("heading", { name: /Action envelope contract/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:plans-action-envelope:v1").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "action-envelope:plans:founder-action-mock-setup-hardening",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByText(
        "scope-ref:plans-action-envelope:founder-action-mock-setup-hardening",
      ),
    ).not.toBeInTheDocument();
    expect(
      screen.getAllByText("blocked-state:no-approval-grant-capture").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Memory-derived proposals/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(
        "memory-derived-action-proposal:memory-review-founder-loop-preferences",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "memory-loop-binding:today:business-memory-candidate-preference-memory-review-founder-loop-preferences",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("approval_required_before_any_memory_derived_action")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("blocked-state:no-memory-write").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(
        /Review refs only; request a scoped state-change milestone/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("approval_ref_must_validate_exact_scope"),
    ).toBeInTheDocument();
    expect(screen.getByText("no_memory_write")).toBeInTheDocument();
    expect(screen.getByText("no_context_injection")).toBeInTheDocument();

    for (const label of [
      /^approve$/i,
      /^send$/i,
      /^run$/i,
      /^install$/i,
      /^connect$/i,
      /^write$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
  });

  it("filters Action Inbox lanes as presentation-only drilldowns over backend groups", async () => {
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      if (options?.method === "POST") {
        throw new Error("unexpected mutation request");
      }
      return new Response(
        JSON.stringify(envelopeForReadEndpoint(String(url))),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/actions");
    const actionView = render(<App />);

    try {
      expect(await screen.findByText("Backend online")).toBeInTheDocument();
      const filterRegion = screen.getByLabelText("Action Inbox lane filters");
      expect(
        within(filterRegion).getByRole("button", {
          name: /Filter lane: All lanes/i,
        }),
      ).toHaveAttribute("aria-pressed", "true");
      expect(
        screen.getByLabelText("Selected Action Inbox lane drilldown"),
      ).toHaveTextContent("all_lanes");
      const laneStack = screen.getByLabelText("Action Inbox queue lanes");
      expect(
        within(laneStack).getByRole("heading", {
          name: /^Approved local-task create lane$/i,
        }),
      ).toBeInTheDocument();
      expect(
        within(laneStack).getByRole("heading", {
          name: /^Ready for decision$/i,
        }),
      ).toBeInTheDocument();

      fireEvent.click(
        within(filterRegion).getByRole("button", {
          name: /Filter lane: Approved local-task create lane/i,
        }),
      );

      const drilldown = screen.getByLabelText(
        "Selected Action Inbox lane drilldown",
      );
      expect(drilldown).toHaveTextContent("approved_local_task_lane");
      expect(drilldown).toHaveTextContent(
        "Inspect approval posture or commit the local-task create lane.",
      );
      expect(
        within(laneStack).getByRole("heading", {
          name: /^Approved local-task create lane$/i,
        }),
      ).toBeInTheDocument();
      expect(
        within(laneStack).queryByRole("heading", {
          name: /^Ready for decision$/i,
        }),
      ).not.toBeInTheDocument();
      expect(
        screen.getAllByRole("heading", { name: /^Approval Envelope Card$/i })
          .length,
      ).toBeGreaterThan(0);
      expect(
        screen.getAllByRole("heading", { name: /^Receipt Visibility$/i })
          .length,
      ).toBeGreaterThan(0);
      expect(
        screen.queryByRole("button", { name: /^execute$/i }),
      ).not.toBeInTheDocument();

      fireEvent.click(
        within(filterRegion).getByRole("button", {
          name: /Filter lane: All lanes/i,
        }),
      );
      expect(
        within(laneStack).getByRole("heading", {
          name: /^Ready for decision$/i,
        }),
      ).toBeInTheDocument();
    } finally {
      actionView.unmount();
      cleanup();
      window.history.pushState({}, "", "/");
    }
  });

  it("renders backend-owned local task safe-disable and rollback posture", async () => {
    const disabledInbox = JSON.parse(
      JSON.stringify({
        ...mockControlCenterData.founderActionsInbox,
        ...mockApiData.founderActionsInbox,
        items: mockApiData.founderActionsInbox.items,
      }),
    );
    const disabledItem = disabledInbox.items.find(
      (candidate: { item_ref: string }) =>
        candidate.item_ref === "founder-action:mock-local-task-create",
    );
    Object.assign(disabledItem, {
      status: "blocked",
      action_group_id: "blocked_by_authority",
      action_group_label: "Blocked by authority",
      action_group_reason:
        "Backend safe-disable posture blocks the exact local-task create lane.",
      action_group_available_action:
        "Inspect safe-disable and rollback refs; no commit control is exposed.",
      local_task_commit_approval_status: "backend_owned_safe_disable_active",
      local_task_commit_eligible: false,
      local_task_commit_blocked_reasons: [
        "blocked-state:local-task-create-safe-disabled",
      ],
      local_task_commit_next_safe_action:
        "Keep local task creation disabled until backend posture is re-enabled.",
      local_task_safe_disable_active: true,
      local_task_safe_disable_posture: {
        ...disabledItem.local_task_safe_disable_posture,
        local_task_commits_enabled: false,
        safe_disable_active: true,
        disabled_reason_refs: ["blocked-state:local-task-create-safe-disabled"],
        blocked_state_refs: [
          "blocked-state:local-task-create-safe-disabled",
          "blocked-state:no-connector-write",
          "blocked-state:no-shell-subprocess-execution",
          "blocked-state:no-model-provider-authority",
          "blocked-state:no-memory-write",
          "blocked-state:no-context-injection",
          "blocked-state:no-external-side-effect",
          "blocked-state:no-production-authority",
        ],
        next_safe_action:
          "Keep local task creation disabled until backend posture is re-enabled.",
      },
    });
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      const urlText = String(url);
      if (options?.method === "POST") {
        throw new Error("unexpected mutation request");
      }
      if (
        !options?.method &&
        urlText.endsWith(API_ENDPOINTS.founderActionsInbox)
      ) {
        return new Response(
          JSON.stringify({
            ok: true,
            result: disabledInbox,
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (
        !options?.method &&
        READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/actions");
    const actionView = render(<App />);

    try {
      expect(await screen.findByText("Backend online")).toBeInTheDocument();
      const postureCard = screen.getByLabelText("Local task commit posture");
      expect(postureCard).toHaveTextContent("local_task_commit_eligible");
      expect(postureCard).toHaveTextContent("false");
      expect(postureCard).toHaveTextContent(
        "local_task_commit_approval_status",
      );
      expect(postureCard).toHaveTextContent(
        "backend_owned_safe_disable_active",
      );
      expect(postureCard).toHaveTextContent(
        "local_task_commit_blocked_reasons",
      );
      expect(postureCard).toHaveTextContent(
        "blocked-state:local-task-create-safe-disabled",
      );
      expect(postureCard).toHaveTextContent(
        "local_task_commit_next_safe_action",
      );
      expect(postureCard).toHaveTextContent(
        "Keep local task creation disabled until backend posture is re-enabled.",
      );
      expect(postureCard).toHaveTextContent("local_task_safe_disable_active");
      expect(postureCard).toHaveTextContent(
        "local_task_safe_disable_posture_ref",
      );
      expect(postureCard).toHaveTextContent(
        "safe-disable-posture:founder-loop:local-task-create",
      );
      expect(postureCard).toHaveTextContent("local_task_rollback_ref");
      expect(postureCard).toHaveTextContent(
        "rollback-not-applicable:local-task-safe-disable",
      );
      expect(postureCard).toHaveTextContent(
        "local_task_rollback_execution_enabled",
      );
      expect(postureCard).toHaveTextContent(
        "blocked-state:local-task-rollback-execution-not-scoped",
      );
      expect(postureCard).toHaveTextContent("blocked-state:no-connector-write");
      expect(postureCard).toHaveTextContent(
        "blocked-state:no-production-authority",
      );
      expect(
        screen.queryByRole("button", {
          name: /Create local task record/i,
        }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /^execute$/i }),
      ).not.toBeInTheDocument();
    } finally {
      actionView.unmount();
      cleanup();
      window.history.pushState({}, "", "/");
    }
  });

  it("keeps missing Action Inbox envelope fields non-authoritative", async () => {
    const missingEnvelopeInbox = JSON.parse(
      JSON.stringify({
        ...mockControlCenterData.founderActionsInbox,
        ...mockApiData.founderActionsInbox,
        items: mockApiData.founderActionsInbox.items,
      }),
    );
    const partialItem = missingEnvelopeInbox.items.find(
      (candidate: { item_ref: string }) =>
        candidate.item_ref === "founder-action:mock-local-task-create",
    );
    delete partialItem.approval_envelope;
    delete partialItem.receipt_visibility;
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      const urlText = String(url);
      if (options?.method === "POST") {
        throw new Error("unexpected mutation request");
      }
      if (
        !options?.method &&
        urlText.endsWith(API_ENDPOINTS.founderActionsInbox)
      ) {
        return new Response(
          JSON.stringify({
            ok: true,
            result: missingEnvelopeInbox,
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (
        !options?.method &&
        READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/actions");
    const actionView = render(<App />);

    try {
      expect(await screen.findByText("Backend online")).toBeInTheDocument();
      expect(
        screen.getAllByRole("heading", {
          name: /^Approval Envelope Unavailable$/i,
        }).length,
      ).toBeGreaterThan(0);
      expect(
        screen.getAllByRole("heading", {
          name: /^Receipt Visibility Unavailable$/i,
        }).length,
      ).toBeGreaterThan(0);
      expect(
        screen.getAllByText("blocked-state:backend-owned-envelope-missing")
          .length,
      ).toBeGreaterThan(0);
      expect(
        screen.getAllByText("approval_envelope:missing").length,
      ).toBeGreaterThan(0);
      expect(
        screen.getAllByText("receipt_visibility:missing").length,
      ).toBeGreaterThan(0);
      expect(
        screen.queryByRole("button", {
          name: /Create local task record/i,
        }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /^execute$/i }),
      ).not.toBeInTheDocument();
    } finally {
      actionView.unmount();
      cleanup();
      window.history.pushState({}, "", "/");
    }
  });

  it("blocks Action Inbox approval when cost posture is not approved", async () => {
    const inbox = JSON.parse(
      JSON.stringify({
        ...mockControlCenterData.founderActionsInbox,
        ...mockApiData.founderActionsInbox,
        items: mockApiData.founderActionsInbox.items,
      }),
    );
    const readyItem = inbox.items.find(
      (candidate: { item_ref: string }) =>
        candidate.item_ref === "founder-action:mock-local-task-create",
    );
    Object.assign(readyItem, {
      status: "proposed",
      action_group_id: "ready_for_decision",
      action_group_label: "Ready for decision",
      action_group_reason:
        "Backend exact scope is ready, but cost posture is blocked.",
      action_group_available_action:
        "Resolve cost posture before recording approval.",
      approval_envelope_status: "ready_for_backend_decision",
      action_envelope_cost_state_label: "Cost blocked",
      action_envelope_provider_ref: "provider-ref:not-invoked",
      action_envelope_model_profile_ref: "model-profile-ref:not-invoked",
      action_envelope_provider_authority_state_label: "No provider authority",
      action_envelope_cost_receipt_refs: [],
      action_envelope_cost_blocked_state_refs: [
        "blocked-state:frontier-provider-model-ref-missing",
      ],
      local_task_commit_approval_ref: null,
      local_task_commit_approval_status: "missing",
      local_task_commit_eligible: false,
      local_task_commit_blocked_reasons: [
        "blocked-state:backend-owned-approval-missing",
      ],
    });
    Object.assign(readyItem.approval_envelope, {
      cost_state_label: "Cost blocked",
      provider_ref: "provider-ref:not-invoked",
      model_profile_ref: "model-profile-ref:not-invoked",
      provider_authority_state_label: "No provider authority",
      cost_receipt_refs: [],
      cost_blocked_state_refs: [
        "blocked-state:frontier-provider-model-ref-missing",
      ],
    });
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      const urlText = String(url);
      if (
        !options?.method &&
        urlText.endsWith(API_ENDPOINTS.founderActionsInbox)
      ) {
        return new Response(JSON.stringify({ ok: true, result: inbox }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (
        !options?.method &&
        READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify({ ok: false }), { status: 500 });
    });

    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/actions");
    render(<App />);

    const approvalButton = await screen.findByRole("button", {
      name: /Record approval/i,
    });
    expect(approvalButton).toBeDisabled();
    expect(screen.getAllByText("Cost blocked").length).toBeGreaterThan(0);
    expect(screen.getAllByText("No provider authority").length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getByText(
        /Approval blocked by cost posture: Cost blocked, No provider authority/i,
      ),
    ).toBeInTheDocument();
    fireEvent.click(approvalButton);
    expect(
      fetchMock.mock.calls.some(([, request]) => request?.method === "POST"),
    ).toBe(false);
  });

  it("renders backend Action Inbox decision lanes before operator approval", async () => {
    const laneIds = [
      "needs_approval",
      "blocked",
      "draft_only",
      "cost_blocked",
      "no_authority",
      "approved_no_execution",
      "rejected",
      "deferred",
      "receipt_recorded",
    ] as const;
    const laneLabels: Record<(typeof laneIds)[number], string> = {
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
    const costBlockedItem = {
      item_ref: "founder-action:test-cost-blocked",
      lane_id: "cost_blocked",
      lane_label: "Cost blocked",
      title: "Cost posture review",
      status: "review_ready",
      priority: "high",
      action_kind: "local_task_create",
      side_effect_class: "local_dev_workspace_only",
      safe_summary: "Cost and provider refs must be reviewed first.",
      why_shown: "Cost blocked before approval.",
      next_safe_action:
        "Resolve cost estimate, budget decision, and receipt refs.",
      authority_boundary: "Approval alone does not execute work.",
      approval_required: true,
      approval_envelope_ref: "approval-envelope:test-cost-blocked",
      approval_envelope_status: "review_ready_exact_scope_required",
      approval_scope_ref: "scope-ref:test-cost-blocked",
      approval_requirement_ref: "approval-requirement:test-cost-blocked",
      expected_receipt_refs: ["receipt-plan:test-cost-blocked"],
      expected_receipt_state: "visible",
      evidence_refs: ["evidence-ref:test-cost-blocked"],
      receipt_refs: [],
      expected_receipt_refs_visible: true,
      rollback_ref: "rollback-ref:test-cost-blocked",
      safe_disable_ref: "safe-disable:test-cost-blocked",
      blocked_authority_refs: [
        "blocked-state:action-inbox-no-action-execution",
        "blocked-state:frontier-provider-model-ref-missing",
      ],
      missing_envelope_field_states: ["none"],
      cost_state_label: "Cost blocked",
      provider_authority_state_label: "No provider authority",
      estimated_cost_usd: 0,
      max_approved_cost_usd: 0,
      provider_ref: "provider-ref:not-invoked",
      model_profile_ref: "model-profile-ref:not-invoked",
      input_metered_units: 0,
      output_metered_units: 0,
      total_metered_units: 0,
      cost_estimate_ref: "cost-estimate-ref:test-cost-blocked",
      captured_usage_ref: "usage-capture-ref:test-cost-blocked",
      budget_decision_ref: "budget-decision-ref:test-cost-blocked",
      cost_receipt_refs: [
        "cost-estimate-ref:test-cost-blocked",
        "usage-capture-ref:test-cost-blocked",
        "budget-decision-ref:test-cost-blocked",
      ],
      cost_blocked_state_refs: [
        "blocked-state:frontier-provider-model-ref-missing",
      ],
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
    const approvedNoExecutionItem = {
      ...costBlockedItem,
      item_ref: "founder-action:test-approved-no-execution",
      lane_id: "approved_no_execution",
      lane_label: "Approved / no execution",
      title: "Approved receipt review",
      status: "approved",
      cost_state_label: "Cost approved",
      provider_authority_state_label: "Provider/model refs present",
      provider_ref: "provider-ref:test",
      model_profile_ref: "model-profile-ref:test",
      cost_blocked_state_refs: [],
      unknown_paid_cost_requires_explicit_approval: false,
      provider_model_refs_present: true,
    };
    const partialMissingEnvelopeItem = {
      ...costBlockedItem,
      item_ref: "founder-action:test-partial-missing-envelope",
      lane_id: "blocked",
      lane_label: "Blocked",
      title: "Partial envelope review",
      cost_state_label: "Cost approved",
      provider_authority_state_label: "Provider/model refs present",
      provider_ref: "provider-ref:test",
      model_profile_ref: "model-profile-ref:test",
      cost_blocked_state_refs: [],
      unknown_paid_cost_requires_explicit_approval: false,
      provider_model_refs_present: true,
      missing_envelope_field_states: [
        "approval_scope_ref:missing",
        "expected_receipt_refs:missing",
        "rollback_ref:missing",
      ],
      expected_receipt_refs: ["missing"],
      expected_receipt_state: "missing_fail_closed",
    };
    const inbox = {
      ...mockApiData.founderActionsInbox,
      action_inbox_decision_lane_contract_ref:
        "contract-ref:product-loop-005-action-inbox-decision-lanes:v1",
      action_inbox_decision_lane_read_model: {
        contract_ref:
          "contract-ref:product-loop-005-action-inbox-decision-lanes:v1",
        status: "backend_owned_decision_lane_read_model",
        source: "python_core_action_inbox_decision_lane_read_model",
        backend_owned: true,
        local_read_model_only: true,
        safe_refs_only: true,
        raw_content_included: false,
        lane_order: laneIds,
        lanes: laneIds.map((laneId) => ({
          lane_id: laneId,
          label: laneLabels[laneId],
          status: `${laneId}_state`,
          safe_summary: `${laneLabels[laneId]} safe-ref lane.`,
          count:
            laneId === "cost_blocked" || laneId === "approved_no_execution"
              ? 1
              : laneId === "blocked"
                ? 1
                : 0,
          item_refs:
            laneId === "cost_blocked"
              ? ["founder-action:test-cost-blocked"]
              : laneId === "approved_no_execution"
                ? ["founder-action:test-approved-no-execution"]
                : laneId === "blocked"
                  ? ["founder-action:test-partial-missing-envelope"]
                  : [],
          blocked_state_refs: [
            "blocked-state:action-inbox-no-action-execution",
          ],
          next_safe_action: "Inspect safe refs only.",
          approval_alone_executes: false,
          action_execution_enabled: false,
        })),
        items: [
          costBlockedItem,
          approvedNoExecutionItem,
          partialMissingEnvelopeItem,
        ],
        blocked_state_refs: ["blocked-state:action-inbox-no-action-execution"],
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
      },
    };
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      const urlText = String(url);
      if (
        !options?.method &&
        urlText.endsWith(API_ENDPOINTS.founderActionsInbox)
      ) {
        return new Response(JSON.stringify({ ok: true, result: inbox }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (
        !options?.method &&
        READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify({ ok: false }), { status: 500 });
    });

    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/actions");
    render(<App />);

    expect(
      await screen.findByText(
        "contract-ref:product-loop-005-action-inbox-decision-lanes:v1",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("python_core_action_inbox_decision_lane_read_model"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Cost blocked").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Cost approved").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Unknown paid cost").length).toBeGreaterThan(0);
    expect(screen.getAllByText("No provider authority").length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText("Approved / no execution").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("Expected receipts").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("Missing envelope fields").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("approval_scope_ref:missing")).toBeInTheDocument();
    expect(
      screen.getByText("expected_receipt_refs:missing"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Blocked authority").length).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: /^execute$/i }),
    ).not.toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some(([, request]) => request?.method === "POST"),
    ).toBe(false);
  });

  it("records approval through backend refresh before committing the local task lane", async () => {
    const approvedInbox = JSON.parse(
      JSON.stringify({
        ...mockControlCenterData.founderActionsInbox,
        ...mockApiData.founderActionsInbox,
        items: mockApiData.founderActionsInbox.items,
      }),
    );
    const initialInbox = JSON.parse(JSON.stringify(approvedInbox));
    const readyItem = initialInbox.items.find(
      (candidate: { item_ref: string }) =>
        candidate.item_ref === "founder-action:mock-local-task-create",
    );
    Object.assign(readyItem, {
      status: "proposed",
      action_group_id: "ready_for_decision",
      action_group_label: "Ready for decision",
      action_group_reason:
        "Backend exact scope is ready for a decision receipt.",
      action_group_available_action: "Record a backend-owned decision receipt.",
      approval_envelope_status: "ready_for_backend_decision",
      local_task_commit_approval_ref: null,
      local_task_commit_approval_status: "missing",
      local_task_commit_eligible: false,
      local_task_commit_blocked_reasons: [
        "blocked-state:backend-owned-approval-missing",
      ],
      local_task_commit_next_safe_action:
        "Record approval before committing local task state.",
      receipt_refs: [],
      audit_refs: [],
      receipt_visibility: {
        ...readyItem.receipt_visibility,
        decision_receipt_ref: "pending",
        local_task_ref: "pending",
        local_task_commit_receipt_ref: "pending",
        evidence_timeline_event_ref: "pending",
        missing_field_states: [
          "decision_receipt_ref:pending",
          "local_task_commit_receipt_ref:pending",
        ],
      },
      updated_at: "2026-06-22T00:00:00Z",
    });
    applyApprovedActionCost(readyItem);
    const approvalReceipt = {
      contract_ref: "contract-ref:founder-loop-action-state-machine:v1",
      decision_ref: "decision-ref:mock-local-task-create:approve",
      item_ref: "founder-action:mock-local-task-create",
      decision: "approve",
      status: "approved",
      receipt_ref: "receipt:founder-loop-action:mock-local-task-create:approve",
      audit_ref: "audit:founder-loop-action:mock-local-task-create:approve",
      idempotency_key_ref: "idempotency-ref:control-center-action:approve",
      payload_fingerprint_ref: "payload-fingerprint-ref:action:approve",
      approval_ref: "approval-ref:mock-local-task-action-approve",
      approval_status: "approved",
      approval_reason_refs: ["approval-reason:approved"],
      action_executed: false,
      approval_grants_execution: false,
      connector_write_performed: false,
      memory_write_performed: false,
      raw_content_stored: false,
      replayed: false,
      safe_summary:
        "Action approval receipt recorded; action execution remains blocked.",
      evidence_refs: ["evidence-ref:founder-loop:action-decision"],
      blocked_state_refs: ["blocked-state:no-action-execution"],
      created_at: "2026-06-22T00:00:30Z",
    };
    const approvedItem = approvedInbox.items.find(
      (candidate: { item_ref: string }) =>
        candidate.item_ref === "founder-action:mock-local-task-create",
    );
    Object.assign(approvedItem, {
      status: "approved",
      action_group_id: "approved_local_task_lane",
      action_group_label: "Approved local-task create lane",
      action_group_reason:
        "Backend approval receipt made the exact local-task create lane eligible.",
      action_group_available_action:
        "Create local task record through the backend exact route.",
      approval_envelope_status: "approved",
      local_task_commit_approval_ref: approvalReceipt.approval_ref,
      local_task_commit_approval_status: "backend_owned_approval_ready",
      local_task_commit_eligible: true,
      local_task_commit_blocked_reasons: [],
      local_task_commit_next_safe_action:
        "Commit this approved local task through the exact local-task route.",
      receipt_refs: [...approvedItem.receipt_refs, approvalReceipt.receipt_ref],
      audit_refs: [...approvedItem.audit_refs, approvalReceipt.audit_ref],
      receipt_visibility: {
        ...approvedItem.receipt_visibility,
        decision_receipt_ref: approvalReceipt.receipt_ref,
        local_task_ref: "pending",
        local_task_commit_receipt_ref: "pending",
        evidence_timeline_event_ref:
          "evidence-timeline-event:action-decision:mock-local-task-create",
        replay_posture: "decision_idempotency_replay_available",
        conflict_posture: "decision_conflicting_idempotency_payload_rejected",
        missing_field_states: [
          "local_task_ref:pending",
          "local_task_commit_receipt_ref:pending",
        ],
      },
      updated_at: "2026-06-22T00:00:30Z",
    });
    applyApprovedActionCost(approvedItem);
    const commitReceipt = {
      contract_ref: "contract-ref:founder-loop-local-task-commit:v1",
      item_ref: "founder-action:mock-local-task-create",
      action_kind: "local_task_create",
      local_task_ref: "local-task:founder-action:mock-local-task-create",
      receipt_ref: "receipt:founder-loop-local-task:mock-local-task-create",
      audit_ref: "audit:founder-loop-local-task:mock-local-task-create",
      evidence_timeline_event_ref:
        "evidence-timeline-event:local-task:mock-local-task-create",
      idempotency_key_ref: "idempotency-ref:control-center-local-task:test",
      payload_fingerprint_ref: "payload-fingerprint-ref:local-task:test",
      approval_ref: "approval-ref:mock-local-task-action-approve",
      approval_status: "approved",
      status: "local_task_created",
      safe_summary: "Local task state was appended with safe refs only.",
      local_task_created: true,
      connector_write_performed: false,
      shell_subprocess_execution_performed: false,
      model_provider_authority_used: false,
      memory_write_performed: false,
      context_injection_performed: false,
      external_side_effect_performed: false,
      raw_content_stored: false,
      replayed: false,
      evidence_refs: ["evidence-ref:founder-loop:local-task-commit"],
      blocked_state_refs: ["blocked-state:no-production-authority"],
      created_at: "2026-06-22T00:01:00Z",
    };
    const committedInbox = JSON.parse(JSON.stringify(approvedInbox));
    const committedItem = committedInbox.items.find(
      (candidate: { item_ref: string }) =>
        candidate.item_ref === "founder-action:mock-local-task-create",
    );
    Object.assign(committedItem, {
      status: "receipt_recorded",
      action_group_id: "receipt_recorded",
      action_group_label: "Receipt recorded",
      local_task_commit_eligible: false,
      local_task_ref: commitReceipt.local_task_ref,
      local_task_commit_receipt_ref: commitReceipt.receipt_ref,
      receipt_refs: [...committedItem.receipt_refs, commitReceipt.receipt_ref],
      evidence_refs: [
        ...committedItem.evidence_refs,
        commitReceipt.evidence_timeline_event_ref,
      ],
      receipt_visibility: {
        ...committedItem.receipt_visibility,
        local_task_ref: commitReceipt.local_task_ref,
        local_task_commit_receipt_ref: commitReceipt.receipt_ref,
        evidence_timeline_event_ref: commitReceipt.evidence_timeline_event_ref,
        replay_posture: "idempotency_replay_available",
        conflict_posture: "conflicting_idempotency_payload_rejected",
        missing_field_states: ["none"],
      },
      updated_at: "2026-06-22T00:01:00Z",
    });
    const approvalEndpoint = actionDecisionEndpoint(
      "founder-action:mock-local-task-create",
      "approve",
    );
    const commitEndpoint = actionLocalTaskCommitEndpoint(
      "founder-action:mock-local-task-create",
    );
    let inboxReadCount = 0;
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      const urlText = String(url);
      if (
        !options?.method &&
        urlText.endsWith(API_ENDPOINTS.founderActionsInbox)
      ) {
        inboxReadCount += 1;
        const inbox =
          inboxReadCount === 1
            ? initialInbox
            : inboxReadCount === 2
              ? approvedInbox
              : committedInbox;
        return new Response(JSON.stringify({ ok: true, result: inbox }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (
        !options?.method &&
        READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (options?.method === "POST" && urlText.endsWith(approvalEndpoint)) {
        return new Response(
          JSON.stringify({ ok: true, result: approvalReceipt }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (options?.method === "POST" && urlText.endsWith(commitEndpoint)) {
        return new Response(
          JSON.stringify({ ok: true, result: commitReceipt }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      throw new Error(`unexpected request ${urlText}`);
    });

    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/actions");
    render(<App />);

    await screen.findByRole("heading", { name: /^Action Inbox$/i });
    const approvalButton = screen.getByRole("button", {
      name: /Record approval/i,
    });
    expect(approvalButton).toBeInTheDocument();
    expect(approvalButton).not.toBeDisabled();
    expect(screen.getAllByText("Cost approved").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("Provider/model refs present").length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", {
        name: /Create local task record/i,
      }),
    ).not.toBeInTheDocument();

    fireEvent.click(approvalButton);
    expect(
      (await screen.findAllByText(approvalReceipt.receipt_ref)).length,
    ).toBeGreaterThan(0);
    const commitButton = await screen.findByRole("button", {
      name: /Create local task record/i,
    });
    expect(commitButton).toBeInTheDocument();
    expect(commitButton).not.toBeDisabled();

    fireEvent.click(commitButton);
    expect(
      (await screen.findAllByText(commitReceipt.receipt_ref)).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", {
        name: /Create local task record/i,
      }),
    ).not.toBeInTheDocument();

    const [, approvalOptions] =
      fetchMock.mock.calls.find(
        ([url, request]) =>
          request?.method === "POST" && String(url).endsWith(approvalEndpoint),
      ) ?? [];
    const approvalRequestBody = JSON.parse(String(approvalOptions?.body));
    expect(approvalRequestBody).toMatchObject({
      decision_reason_ref: "decision-reason-ref:control-center:approve",
      metadata_refs: expect.arrayContaining([
        "metadata-ref:control-center-action-decision:approve",
        "founder-action:mock-local-task-create",
      ]),
    });
    expect(approvalRequestBody).not.toHaveProperty("approval_grants");
    expect(approvalRequestBody).not.toHaveProperty("grant_lists");
    expect(approvalRequestBody).not.toHaveProperty("authority_scopes");
    expect(approvalRequestBody).not.toHaveProperty("risk_class");
    expect(approvalRequestBody).not.toHaveProperty("side_effect_class");
    expect(approvalRequestBody).not.toHaveProperty("approval_requirement");
    expect(approvalRequestBody).not.toHaveProperty("exact_scope");
    expect(
      screen.queryByRole("button", { name: /^execute$/i }),
    ).not.toBeInTheDocument();
  });

  it("commits only the eligible Action Inbox local-task create lane through the typed route", async () => {
    const receipt = {
      contract_ref: "contract-ref:founder-loop-local-task-commit:v1",
      action_id: "mock-local-task-create",
      item_ref: "founder-action:mock-local-task-create",
      action_kind: "local_task_create",
      local_task_ref: "local-task:founder-action:mock-local-task-create",
      receipt_ref: "receipt:founder-loop-local-task:mock-local-task-create",
      audit_ref: "audit:founder-loop-local-task:mock-local-task-create",
      evidence_timeline_event_ref:
        "evidence-timeline-event:local-task:mock-local-task-create",
      idempotency_key_ref: "idempotency-ref:control-center-local-task:test",
      payload_fingerprint_ref: "payload-fingerprint-ref:local-task:test",
      approval_ref: "approval-ref:control-center-local-task:test",
      approval_status: "approved",
      status: "local_task_created",
      safe_summary: "Local task state was appended with safe refs only.",
      local_task_created: true,
      connector_write_performed: false,
      shell_subprocess_execution_performed: false,
      model_provider_authority_used: false,
      memory_write_performed: false,
      context_injection_performed: false,
      external_side_effect_performed: false,
      raw_content_stored: false,
      replayed: false,
      evidence_refs: ["evidence-ref:founder-loop:local-task-commit"],
      blocked_state_refs: [
        "blocked-state:no-connector-write",
        "blocked-state:no-shell-subprocess-execution",
        "blocked-state:no-model-provider-authority",
        "blocked-state:no-memory-write",
        "blocked-state:no-context-injection",
        "blocked-state:no-production-authority",
      ],
      created_at: "2026-06-22T00:00:00Z",
    };
    const committedInbox = JSON.parse(
      JSON.stringify({
        ...mockControlCenterData.founderActionsInbox,
        ...mockApiData.founderActionsInbox,
        items: mockApiData.founderActionsInbox.items,
      }),
    );
    const committedItem = committedInbox.items.find(
      (candidate: { item_ref: string }) =>
        candidate.item_ref === "founder-action:mock-local-task-create",
    );
    Object.assign(committedItem, {
      status: "receipt_recorded",
      action_group_id: "receipt_recorded",
      action_group_label: "Receipt recorded",
      action_group_reason:
        "Backend local task commit receipt is recorded and the item is no longer awaiting commit.",
      action_group_available_action: "Inspect receipt and evidence refs.",
      local_task_commit_eligible: false,
      local_task_ref: receipt.local_task_ref,
      local_task_commit_receipt_ref: receipt.receipt_ref,
      receipt_refs: [...committedItem.receipt_refs, receipt.receipt_ref],
      audit_refs: [...committedItem.audit_refs, receipt.audit_ref],
      evidence_refs: [
        ...committedItem.evidence_refs,
        receipt.evidence_timeline_event_ref,
      ],
      receipt_visibility: {
        ...committedItem.receipt_visibility,
        local_task_ref: receipt.local_task_ref,
        local_task_commit_receipt_ref: receipt.receipt_ref,
        evidence_timeline_event_ref: receipt.evidence_timeline_event_ref,
        replay_posture: "idempotency_replay_available",
        conflict_posture: "conflicting_idempotency_payload_rejected",
        missing_field_states: ["none"],
      },
      updated_at: "2026-06-22T00:01:00Z",
    });
    const endpoint = actionLocalTaskCommitEndpoint(
      "founder-action:mock-local-task-create",
    );
    let commitRecorded = false;
    const actionInboxReadUrls: string[] = [];
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      const urlText = String(url);
      if (
        !options?.method &&
        urlText.endsWith(API_ENDPOINTS.founderActionsInbox)
      ) {
        actionInboxReadUrls.push(urlText);
        return new Response(
          JSON.stringify({
            ok: true,
            result: commitRecorded
              ? committedInbox
              : {
                  ...mockControlCenterData.founderActionsInbox,
                  ...mockApiData.founderActionsInbox,
                  items: mockApiData.founderActionsInbox.items,
                },
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (
        !options?.method &&
        READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (options?.method === "POST" && urlText.endsWith(endpoint)) {
        commitRecorded = true;
        return new Response(JSON.stringify({ ok: true, result: receipt }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });

    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/actions");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Action Inbox$/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("Backend online")).toBeInTheDocument();
    expect(
      screen.getAllByRole("heading", { name: /^Approval Envelope Card$/i })
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByRole("heading", { name: /^Receipt Visibility$/i }).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/python_core_action_inbox_read_model/).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("Local task target ref").length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText("pending").length).toBeGreaterThan(0);
    fireEvent.click(
      screen.getByRole("button", { name: /Create local task record/i }),
    );

    expect(
      (await screen.findAllByText(receipt.receipt_ref)).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(receipt.local_task_ref).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText(receipt.evidence_timeline_event_ref).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("receipt_recorded").length).toBeGreaterThan(0);
    expect(
      screen.getByText("idempotency_replay_available"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("conflicting_idempotency_payload_rejected"),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /Create local task record/i,
      }),
    ).not.toBeInTheDocument();
    expect(actionInboxReadUrls.length).toBeGreaterThanOrEqual(2);
    const receiptLane = screen
      .getByRole("heading", { name: /^Receipt recorded$/i })
      .closest("section");
    expect(receiptLane).not.toBeNull();
    expect(
      within(receiptLane as HTMLElement).getByText(
        "Operational maturity scorecard task",
      ),
    ).toBeInTheDocument();
    const [, options] =
      fetchMock.mock.calls.find(
        ([url, request]) =>
          request?.method === "POST" && String(url).endsWith(endpoint),
      ) ?? [];
    expect(options?.headers).toMatchObject({
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-UAA-Idempotency-Key": expect.stringMatching(
        /^idempotency-ref:control-center-local-task:mock-local-task-create:/,
      ),
    });
    const requestBody = JSON.parse(String(options?.body));
    expect(requestBody).toMatchObject({
      approval_ref: "approval-ref:mock-local-task-action-approve",
      decision_reason_ref:
        "decision-reason-ref:control-center:local-task-commit",
      metadata_refs: expect.arrayContaining([
        "metadata-ref:control-center-local-task-commit",
        "founder-action:mock-local-task-create",
      ]),
    });
    expect(requestBody).not.toHaveProperty("approval_grants");
    expect(requestBody).not.toHaveProperty("grant_lists");
    expect(requestBody).not.toHaveProperty("authority_scopes");
    expect(requestBody).not.toHaveProperty("risk_class");
    expect(requestBody).not.toHaveProperty("side_effect_class");
    expect(requestBody).not.toHaveProperty("approval_requirement");
    expect(requestBody).not.toHaveProperty("exact_scope");
    expect(JSON.stringify(requestBody).toLowerCase()).not.toContain("raw");
    expect(
      screen.queryByRole("button", { name: /^execute$/i }),
    ).not.toBeInTheDocument();
  });

  it("keeps local task commit receipt local and explicit when backend read-model refresh fails", async () => {
    const receipt = {
      contract_ref: "contract-ref:founder-loop-local-task-commit:v1",
      action_id: "mock-local-task-create",
      item_ref: "founder-action:mock-local-task-create",
      action_kind: "local_task_create",
      local_task_ref: "local-task:founder-action:mock-local-task-create",
      receipt_ref: "receipt:founder-loop-local-task:refresh-failed",
      audit_ref: "audit:founder-loop-local-task:refresh-failed",
      evidence_timeline_event_ref:
        "evidence-timeline-event:local-task:refresh-failed",
      idempotency_key_ref: "idempotency-ref:control-center-local-task:test",
      payload_fingerprint_ref: "payload-fingerprint-ref:local-task:test",
      approval_ref: "approval-ref:control-center-local-task:test",
      approval_status: "approved",
      status: "local_task_created",
      safe_summary: "Local task state was appended with safe refs only.",
      local_task_created: true,
      connector_write_performed: false,
      shell_subprocess_execution_performed: false,
      model_provider_authority_used: false,
      memory_write_performed: false,
      context_injection_performed: false,
      external_side_effect_performed: false,
      raw_content_stored: false,
      replayed: false,
      evidence_refs: ["evidence-ref:founder-loop:local-task-commit"],
      blocked_state_refs: ["blocked-state:no-production-authority"],
      created_at: "2026-06-22T00:00:00Z",
    };
    const endpoint = actionLocalTaskCommitEndpoint(
      "founder-action:mock-local-task-create",
    );
    let commitRecorded = false;
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      const urlText = String(url);
      if (
        !options?.method &&
        urlText.endsWith(API_ENDPOINTS.founderActionsInbox)
      ) {
        if (commitRecorded) {
          return new Response(
            JSON.stringify({
              ok: false,
              error: { message: "Action Inbox read model unavailable" },
            }),
            {
              status: 503,
              headers: { "Content-Type": "application/json" },
            },
          );
        }
        return new Response(
          JSON.stringify({
            ok: true,
            result: {
              ...mockControlCenterData.founderActionsInbox,
              ...mockApiData.founderActionsInbox,
              items: mockApiData.founderActionsInbox.items,
            },
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (
        !options?.method &&
        READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (options?.method === "POST" && urlText.endsWith(endpoint)) {
        commitRecorded = true;
        return new Response(JSON.stringify({ ok: true, result: receipt }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });

    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/actions");
    render(<App />);

    await screen.findByRole("heading", { name: /^Action Inbox$/i });
    fireEvent.click(
      screen.getByRole("button", { name: /Create local task record/i }),
    );

    await screen.findByText(receipt.receipt_ref);
    expect(
      await screen.findByText(/Backend read-model refresh failed safely/i),
    ).toBeInTheDocument();
    expect(screen.getByText("refresh_failed")).toBeInTheDocument();
    expect(
      screen.queryByText(
        "Backend read model refreshed; receipt visibility now comes from the Action Inbox API.",
      ),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /Create local task record/i,
      }),
    ).not.toBeInTheDocument();
    expect(screen.getAllByText("Local task target ref").length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText("pending").length).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: /^execute$/i }),
    ).not.toBeInTheDocument();
  });

  it("shows replay posture from the refreshed Action Inbox read model", async () => {
    const replayReceipt = {
      contract_ref: "contract-ref:founder-loop-local-task-commit:v1",
      action_id: "mock-local-task-create",
      item_ref: "founder-action:mock-local-task-create",
      action_kind: "local_task_create",
      local_task_ref: "local-task:founder-action:mock-local-task-create",
      receipt_ref:
        "receipt:founder-loop-local-task:mock-local-task-create-replay",
      audit_ref: "audit:founder-loop-local-task:mock-local-task-create-replay",
      evidence_timeline_event_ref:
        "evidence-timeline-event:local-task:mock-local-task-create-replay",
      idempotency_key_ref: "idempotency-ref:control-center-local-task:replay",
      payload_fingerprint_ref: "payload-fingerprint-ref:local-task:replay",
      approval_ref: "approval-ref:mock-local-task-action-approve",
      approval_status: "approved",
      status: "local_task_created",
      safe_summary:
        "Prior local task commit receipt replayed with safe refs only.",
      local_task_created: true,
      connector_write_performed: false,
      shell_subprocess_execution_performed: false,
      model_provider_authority_used: false,
      memory_write_performed: false,
      context_injection_performed: false,
      external_side_effect_performed: false,
      raw_content_stored: false,
      replayed: true,
      evidence_refs: ["evidence-ref:founder-loop:local-task-commit"],
      blocked_state_refs: ["blocked-state:no-production-authority"],
      created_at: "2026-06-22T00:00:00Z",
    };
    const initialInbox = JSON.parse(
      JSON.stringify({
        ...mockControlCenterData.founderActionsInbox,
        ...mockApiData.founderActionsInbox,
        items: mockApiData.founderActionsInbox.items,
      }),
    );
    const replayedInbox = JSON.parse(JSON.stringify(initialInbox));
    const replayedItem = replayedInbox.items.find(
      (candidate: { item_ref: string }) =>
        candidate.item_ref === "founder-action:mock-local-task-create",
    );
    Object.assign(replayedItem, {
      status: "receipt_recorded",
      action_group_id: "receipt_recorded",
      action_group_label: "Receipt recorded",
      action_group_reason:
        "Backend local task commit receipt is recorded and replay posture is visible.",
      action_group_available_action: "Inspect receipt and evidence refs.",
      local_task_commit_eligible: false,
      local_task_ref: replayReceipt.local_task_ref,
      local_task_commit_receipt_ref: replayReceipt.receipt_ref,
      receipt_refs: [...replayedItem.receipt_refs, replayReceipt.receipt_ref],
      audit_refs: [...replayedItem.audit_refs, replayReceipt.audit_ref],
      evidence_refs: [
        ...replayedItem.evidence_refs,
        replayReceipt.evidence_timeline_event_ref,
      ],
      receipt_visibility: {
        ...replayedItem.receipt_visibility,
        local_task_ref: replayReceipt.local_task_ref,
        local_task_commit_receipt_ref: replayReceipt.receipt_ref,
        evidence_timeline_event_ref: replayReceipt.evidence_timeline_event_ref,
        replay_posture: "idempotency_replay_available",
        conflict_posture: "conflicting_idempotency_payload_rejected",
        missing_field_states: ["none"],
      },
      updated_at: "2026-06-22T00:01:00Z",
    });
    const endpoint = actionLocalTaskCommitEndpoint(
      "founder-action:mock-local-task-create",
    );
    let commitRecorded = false;
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      const urlText = String(url);
      if (
        !options?.method &&
        urlText.endsWith(API_ENDPOINTS.founderActionsInbox)
      ) {
        return new Response(
          JSON.stringify({
            ok: true,
            result: commitRecorded ? replayedInbox : initialInbox,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (
        !options?.method &&
        READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (options?.method === "POST" && urlText.endsWith(endpoint)) {
        commitRecorded = true;
        return new Response(
          JSON.stringify({ ok: true, result: replayReceipt }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      throw new Error(`unexpected request ${urlText}`);
    });

    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/actions");
    render(<App />);

    await screen.findByRole("heading", { name: /^Action Inbox$/i });
    fireEvent.click(
      screen.getByRole("button", { name: /Create local task record/i }),
    );

    expect(
      (await screen.findAllByText(replayReceipt.receipt_ref)).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(replayReceipt.local_task_ref).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(replayReceipt.evidence_timeline_event_ref).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("idempotency_replay_available"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("conflicting_idempotency_payload_rejected"),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /Create local task record/i,
      }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^execute$/i }),
    ).not.toBeInTheDocument();
  });

  it("keeps conflicting local task commits out of committed UI state", async () => {
    const endpoint = actionLocalTaskCommitEndpoint(
      "founder-action:mock-local-task-create",
    );
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      const urlText = String(url);
      if (
        !options?.method &&
        urlText.endsWith(API_ENDPOINTS.founderActionsInbox)
      ) {
        return new Response(
          JSON.stringify({
            ok: true,
            result: {
              ...mockControlCenterData.founderActionsInbox,
              ...mockApiData.founderActionsInbox,
              items: mockApiData.founderActionsInbox.items,
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (
        !options?.method &&
        READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (options?.method === "POST" && urlText.endsWith(endpoint)) {
        return new Response(
          JSON.stringify({
            detail: {
              code: "FOUNDER_LOOP_LOCAL_TASK_IDEMPOTENCY_CONFLICT",
              safe_message: "Conflicting idempotency payload rejected safely.",
            },
          }),
          { status: 409, headers: { "Content-Type": "application/json" } },
        );
      }
      throw new Error(`unexpected request ${urlText}`);
    });

    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/actions");
    render(<App />);

    await screen.findByRole("heading", { name: /^Action Inbox$/i });
    fireEvent.click(
      screen.getByRole("button", { name: /Create local task record/i }),
    );

    expect(
      await screen.findByText(
        "Conflicting idempotency payload rejected safely.",
      ),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Local task target ref").length).toBeGreaterThan(
      0,
    );
    expect(
      screen.queryByText("receipt:founder-loop-local-task:conflicting-commit"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(
        "evidence-timeline-event:local-task:conflicting-commit",
      ),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Create local task record/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^execute$/i }),
    ).not.toBeInTheDocument();
  });

  it("renders Memory context-pack proposals as proposal-only inspection", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/memory");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Memory Review$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Context-pack proposals/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("GET /control-center/memory/context-packs").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("context-pack:mock-founder-loop-preferences"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("proposal-only context pack over reviewed memory refs", {
        exact: false,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("blocked-state:no-context-injection").length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: /^inject context$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^call model$/i }),
    ).not.toBeInTheDocument();
  });

  it("does not backfill Memory context-pack previews from mocks", async () => {
    const partialContextPacks = {
      ...mockControlCenterData.founderMemoryContextPacks,
      status: "backend_partial_context_pack_proposals",
      context_pack_count: 0,
    };
    delete (partialContextPacks as { proposals?: unknown }).proposals;
    delete (partialContextPacks as { blocked_state_refs?: unknown })
      .blocked_state_refs;
    const partialContextManifest = {
      ...mockControlCenterData.founderMemoryContextManifest,
      status: "backend_partial_context_manifest",
      manifest_count: 0,
      context_pack_preview_count: 0,
    };
    delete (partialContextManifest as { manifests?: unknown }).manifests;
    delete (partialContextManifest as { blocked_state_refs?: unknown })
      .blocked_state_refs;
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderMemoryContextPacks)) {
        return new Response(
          JSON.stringify({ ok: true, result: partialContextPacks }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (urlText.endsWith(API_ENDPOINTS.founderMemoryContextManifest)) {
        return new Response(
          JSON.stringify({ ok: true, result: partialContextManifest }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/memory");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Memory Review$/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("backend_partial_context_manifest")).toBeInTheDocument();
    expect(screen.getAllByText("blocked/planned").length).toBeGreaterThan(0);
    expect(
      screen.queryByText("context-pack:mock-founder-loop-preferences"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("context-manifest-ref:fcc-mem-020:mock-preferences"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^inject context$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^call model$/i }),
    ).not.toBeInTheDocument();
  });

  it("creates Memory context-pack Action Inbox proposals through backend-owned handoff", async () => {
    const contextPackRef = "context-pack:mock-founder-loop-preferences";
    const receipt = {
      contract_ref:
        "contract-ref:governed-cognitive-memory-spine:phase6.1-internal-action-proposal:v1",
      route_ref:
        "POST /control-center/memory/context-packs/{context_pack_ref}/action-proposal",
      status: "implemented_internal_action_proposal_only",
      context_pack_ref: contextPackRef,
      context_pack_proposal_ref:
        "context-pack-proposal:mock-founder-loop-preferences",
      internal_action_proposal_ref:
        "proposal-ref:memory-context-pack-action:mock-founder-loop-preferences",
      item_ref:
        "founder-action:memory-context-pack:mock-founder-loop-preferences",
      action_envelope_ref:
        "action-envelope:memory-context-pack:mock-founder-loop-preferences",
      exact_approval_scope_ref:
        "scope-ref:memory-context-pack-action:mock-founder-loop-preferences",
      approval_ref:
        "approval-ref:memory-context-pack-action:mock-founder-loop-preferences",
      approval_status: "approved",
      approval_reason_refs: ["approval-reason:approval_validated"],
      receipt_ref:
        "receipt:memory-context-pack-action:mock-founder-loop-preferences",
      audit_ref:
        "audit:memory-context-pack-action:mock-founder-loop-preferences",
      idempotency_key_ref:
        "idempotency-ref:control-center-memory-context-action:mock",
      payload_fingerprint_ref:
        "payload-fingerprint:memory-context-pack-action:mock",
      evidence_timeline_event_ref:
        "evidence-timeline:memory-context-pack-action/mock",
      source_memory_record_refs: [
        "memory-record:reviewed:founder-loop-preferences",
      ],
      l1_preview_refs: ["l1-preview:founder-loop-preferences"],
      l2_projection_refs: ["l2-fact:founder-loop-preferences"],
      l3_representation_refs: ["l3-representation:founder-loop-preferences"],
      source_refs: ["source-ref:manual-note:founder-loop-preferences"],
      evidence_refs: ["evidence-ref:memory-context-pack:mock"],
      supporting_receipt_refs: [],
      rollback_ref:
        "rollback-ref:memory-context-pack-action:mock-founder-loop-preferences",
      safe_disable_ref:
        "safe-disable-ref:memory-context-pack-action:mock-founder-loop-preferences",
      blocked_state_refs: [
        "blocked-state:memory-execution-no-action-execution",
        "blocked-state:memory-execution-no-hidden-context-injection",
      ],
      action_proposal_created: true,
      action_executed: false,
      approval_grants_execution: false,
      connector_write_performed: false,
      crm_sync_performed: false,
      account_sync_performed: false,
      shell_subprocess_performed: false,
      browser_automation_performed: false,
      provider_model_call_performed: false,
      context_injection_performed: false,
      memory_write_performed: false,
      raw_content_stored: false,
      replayed: false,
      safe_summary:
        "Reviewed context-pack safe refs created an internal Action proposal for review only; execution and external side effects remain blocked.",
      created_at: "2026-06-23T00:00:00Z",
    };
    const initialContextPacks = JSON.parse(
      JSON.stringify(mockControlCenterData.founderMemoryContextPacks),
    );
    const refreshedContextPacks = JSON.parse(
      JSON.stringify(mockControlCenterData.founderMemoryContextPacks),
    );
    Object.assign(refreshedContextPacks.proposals[0], {
      internal_action_proposal_refs: [receipt.internal_action_proposal_ref],
      internal_action_receipt_refs: [receipt.receipt_ref],
      phase6_1_internal_action_proposal_status:
        "proposal_receipt_recorded_execution_blocked",
    });
    refreshedContextPacks.internal_action_proposal_receipts = [receipt];

    const endpoint = memoryContextPackActionProposalEndpoint(contextPackRef);
    let contextPackReadCount = 0;
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      const urlText = String(url);
      if (
        !options?.method &&
        urlText.endsWith(API_ENDPOINTS.founderMemoryContextPacks)
      ) {
        contextPackReadCount += 1;
        return new Response(
          JSON.stringify({
            ok: true,
            result:
              contextPackReadCount === 1
                ? initialContextPacks
                : refreshedContextPacks,
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (
        !options?.method &&
        READ_ENDPOINTS.some((candidate) => urlText.endsWith(candidate))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (options?.method === "POST" && urlText.endsWith(endpoint)) {
        return new Response(JSON.stringify({ ok: true, result: receipt }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });

    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/memory");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Memory Review$/i }),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", {
        name: /Record Action Inbox proposal receipt/i,
      }),
    );

    expect(
      (await screen.findAllByText(receipt.receipt_ref)).length,
    ).toBeGreaterThan(0);
    expect(
      (await screen.findAllByText(receipt.internal_action_proposal_ref)).length,
    ).toBeGreaterThan(0);
    expect(
      await screen.findByText(
        "Backend read model refreshed; Action Inbox handoff refs come from the Memory context-pack API.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Action executed")).toBeInTheDocument();
    expect(screen.getAllByText("no").length).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: /^execute$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^inject context$/i }),
    ).not.toBeInTheDocument();

    const [, postOptions] =
      fetchMock.mock.calls.find(
        ([url, request]) =>
          request?.method === "POST" && String(url).endsWith(endpoint),
      ) ?? [];
    const postBody = JSON.parse(String(postOptions?.body));
    expect(postBody).toMatchObject({
      decision_reason_ref:
        "decision-reason-ref:control-center-memory-context-pack-action-proposal",
      metadata_refs: expect.arrayContaining([
        "metadata-ref:control-center-memory-context-pack-action-proposal",
        contextPackRef,
      ]),
    });
    expect(postBody).not.toHaveProperty("approval_ref");
    expect(postBody).not.toHaveProperty("exact_approval_scope_ref");
    expect(postBody).not.toHaveProperty("approval_grants");
    expect(postBody).not.toHaveProperty("grant_lists");
    expect(postBody).not.toHaveProperty("authority_scopes");
    expect(postBody).not.toHaveProperty("context_payload");
  });

  it("renders Morning Briefing source-readiness posture without source controls", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/briefing");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Morning Briefing/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Source posture/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Missing contracts/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: /Read-only source readiness metadata/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("no connector runtime")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Email, calendar, connector runtime, background refresh/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("/control-center/morning-briefing/summary").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "blocked_missing_email_calendar_notification_contracts",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("status-ref:control-center-route-manifest"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:email-read-only-missing").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("contract-ref:calendar-read-only-missing").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("contract-ref:notification-delivery-missing").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("source-ref:control-center-route-status"),
    ).toBeInTheDocument();
    expect(screen.getByText("local_status_refs_only")).toBeInTheDocument();
    expect(
      screen.getByText("recheck_route_status_before_briefing_use"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /No email, calendar, or notification source evidence is bound/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(
        /Use route and storage refs only; define source contracts before refresh/i,
      ).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("no_background_refresh").length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText("no_notification_delivery").length,
    ).toBeGreaterThan(0);

    for (const label of [
      /^refresh$/i,
      /^send$/i,
      /^connect$/i,
      /^write$/i,
      /^approve$/i,
      /^run$/i,
      /^notify$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
  });

  it("searches route and disabled action entries through the command palette", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/dashboard");
    render(<App />);

    fireEvent.click(
      await screen.findByRole("button", { name: /find route or action/i }),
    );

    const palette = screen.getByRole("dialog", { name: /command palette/i });
    expect(palette).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/search routes and actions/i), {
      target: { value: "storage" },
    });

    expect(palette).toHaveTextContent("Storage");
    expect(palette).toHaveTextContent("Runtime - partial");

    fireEvent.change(screen.getByLabelText(/search routes and actions/i), {
      target: { value: "crm" },
    });
    expect(palette).toHaveTextContent("CRM");
    expect(palette).toHaveTextContent("Founder Loop - blocked");

    fireEvent.change(screen.getByLabelText(/search routes and actions/i), {
      target: { value: "local state" },
    });
    expect(palette).toHaveTextContent("Storage");
    expect(palette).toHaveTextContent("Runtime - partial");

    fireEvent.change(screen.getByLabelText(/search routes and actions/i), {
      target: { value: "state change" },
    });
    expect(palette).toHaveTextContent("Action state change");
    expect(palette).toHaveTextContent("Scoped backend contract required");
    expect(
      screen.queryByRole("button", { name: /^run$/i }),
    ).not.toBeInTheDocument();
  });

  it("renders accessible operator states for required Control Center surfaces", async () => {
    const requiredSurfaceChecks = [
      {
        path: "/chat",
        heading: /^Chat Local Operator$/,
        stateHeading: /Chat Local Operator states/i,
        blocked: /Blocked: local chat authority withheld/i,
        denied: /Denied: model output is not authority/i,
      },
      {
        path: "/plans",
        heading: /^Plans$/,
        stateHeading: /Plans states/i,
        blocked: /Blocked: product Plans loop incomplete/i,
        denied: /Denied: no unapproved plan execution/i,
      },
      {
        path: "/models",
        heading: /^Models$/,
        stateHeading: /Models states/i,
        blocked: /Blocked: model lifecycle authority not scoped/i,
        denied: /Denied: no provider or model authority/i,
      },
      {
        path: "/approvals",
        heading: /^Run-attached Approval Queue$/,
        stateHeading: /Approvals states/i,
        blocked: /Blocked: live approval binding incomplete/i,
        denied: /Denied: no UI approval grant/i,
      },
      {
        path: "/files",
        heading: /^File Reference Viewer$/,
        stateHeading: /Files states/i,
        blocked: /Blocked: broad file workbench incomplete/i,
        denied: /Denied: no unapproved file mutation/i,
      },
      {
        path: "/runtime",
        heading: /^Runtime readiness$/,
        stateHeading: /Runtime states/i,
        blocked: /Blocked: lifecycle controls not scoped/i,
        denied: /Denied: no hidden runtime authority/i,
      },
      {
        path: "/evidence",
        heading: /^Evidence Viewer$/,
        stateHeading: /Evidence states/i,
        blocked: /Blocked: release evidence index incomplete/i,
        denied: /Denied: no sensitive evidence display/i,
      },
      {
        path: "/settings",
        heading: /^Settings$/,
        stateHeading: /Settings states/i,
        blocked: /Blocked: settings mutation authority not scoped/i,
        denied: /Denied: no authority toggle/i,
      },
    ] as const;

    for (const check of requiredSurfaceChecks) {
      mockFetchWithFallback();
      window.history.pushState({}, "", check.path);
      const { unmount } = render(<App />);

      expect(
        await screen.findByRole("heading", { name: check.heading }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: check.stateHeading }),
      ).toBeInTheDocument();
      expect(screen.getByText(check.blocked)).toBeInTheDocument();
      expect(screen.getByText(check.denied)).toBeInTheDocument();
      expect(screen.getAllByRole("status").length).toBeGreaterThanOrEqual(4);
      expect(screen.getAllByRole("alert").length).toBeGreaterThanOrEqual(1);
      expect(
        screen.getAllByText(/Next safe action:/i).length,
      ).toBeGreaterThanOrEqual(5);
      expect(
        screen.queryByRole("button", { name: /^run$/i }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /^send$/i }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /^approve$/i }),
      ).not.toBeInTheDocument();

      unmount();
      vi.unstubAllGlobals();
    }
  });

  it("renders CRM M1 fixture-only shell without CRM authority", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/crm");
    render(<App />);

    expect(
      await screen.findByRole("heading", {
        name: /CRM M1 fixture-only shell/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("contract-ref:crm-m1-fixture-only-vertical-shell:v1"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("route-ref:control-center:crm-fixture-only-shell"),
    ).toBeInTheDocument();
    expect(screen.getByText("Real Estate Realtor")).toBeInTheDocument();
    expect(screen.getByText("Healthcare")).toBeInTheDocument();
    expect(screen.getByText("Finance Insurance")).toBeInTheDocument();
    expect(screen.getByText("Retail E-commerce")).toBeInTheDocument();
    expect(screen.getByText("Professional Services")).toBeInTheDocument();
    expect(
      screen.getByText("No CRM write controls are available"),
    ).toBeInTheDocument();
    expect(screen.getByText("Backend read model").nextElementSibling).toHaveTextContent(
      "blocked",
    );
    expect(screen.getByText("Backend route").nextElementSibling).toHaveTextContent(
      "blocked",
    );
    expect(screen.getByText("Connector runtime").nextElementSibling).toHaveTextContent(
      "blocked",
    );
    expect(screen.getByText("Sends/calendar").nextElementSibling).toHaveTextContent(
      "blocked",
    );
    expect(
      screen.queryByText(/GET \/control-center\/crm/i),
    ).not.toBeInTheDocument();
    for (const unsafeControl of [
      /send/i,
      /sync/i,
      /import/i,
      /write/i,
      /execute/i,
      /connect/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: unsafeControl }),
      ).not.toBeInTheDocument();
    }
  });

  it("renders priority operator flows instead of placeholder-first screens", async () => {
    const priorityFlowChecks = [
      {
        path: "/chat",
        heading: /^Chat Local Operator$/,
        marker: /UAA \/v1 model route/i,
        route: API_ENDPOINTS.localChatCompletions,
      },
      {
        path: "/plans",
        heading: /^Plans$/,
        marker: /Task decomposition route posture/i,
        route: "/task-decomposition/classify",
      },
      {
        path: "/models",
        heading: /^Models$/,
        marker: /Backend-owned Local Models status/i,
        route: /GET \/control-center\/local-models\/status/i,
      },
      {
        path: "/evidence",
        heading: /^Evidence Viewer$/,
        marker: /Evidence lanes/i,
        route: "/task-decomposition/audit",
      },
      {
        path: "/settings",
        heading: /^Settings$/,
        marker: /Backend-owned Settings status/i,
        route: /GET \/control-center\/settings\/status/i,
      },
    ] as const;

    for (const check of priorityFlowChecks) {
      mockFetchWithFallback();
      window.history.pushState({}, "", check.path);
      const { unmount } = render(<App />);

      expect(
        await screen.findByRole("heading", { name: check.heading }),
      ).toBeInTheDocument();
      expect(screen.getAllByText(check.marker).length).toBeGreaterThan(0);
      if (typeof check.route === "string") {
        expect(screen.getAllByText(check.route).length).toBeGreaterThan(0);
      } else {
        expect(screen.getAllByText(check.route).length).toBeGreaterThan(0);
      }
      if (check.path === "/chat") {
        expect(
          screen.getAllByText("contract-ref:chat-local-operator-surface:v1")
            .length,
        ).toBeGreaterThan(0);
      }
      expect(
        screen.queryByText(/v0\.43\.0 M39 context proposal surface/i),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /^send$/i }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /^run$/i }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /^approve$/i }),
      ).not.toBeInTheDocument();

      unmount();
      vi.unstubAllGlobals();
    }
  });

  it("renders Settings and Local Models backend-owned status routes", async () => {
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      const urlText = String(url);
      if (
        !options?.method &&
        READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (!options?.method && urlText.endsWith(API_ENDPOINTS.localModels)) {
        return new Response(JSON.stringify({ data: [] }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/settings");
    const settingsView = render(<App />);

    expect(
      await screen.findByRole("heading", {
        name: /Backend-owned Settings status/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/GET \/control-center\/settings\/status/i).length,
    ).toBeGreaterThan(0);
    const settingsSpine = screen.getByLabelText("Founder daily loop modules");
    const settingsSpineCard = within(settingsSpine)
      .getAllByRole("link")
      .find((link) => link.textContent?.includes("Settings"));
    expect(settingsSpineCard).toHaveTextContent("read_only_status");
    expect(settingsSpineCard).toHaveTextContent(
      "GET /control-center/settings/status",
    );
    expect(
      screen.queryByText(/Add backend-owned manifest/i),
    ).not.toBeInTheDocument();
    expect(screen.getByText("active_promotion_gate")).toBeInTheDocument();
    expect(screen.getByText("read_only_metadata_only")).toBeInTheDocument();
    expect(screen.getByText("not_configured_status_only")).toBeInTheDocument();
    expect(screen.getByText("feature_flag_mutation")).toBeInTheDocument();
    expect(screen.getByText("kill_switch_mutation")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Settings authority posture labels"),
    ).toBeInTheDocument();
    for (const label of [
      "Web",
      "Providers",
      "Connectors",
      "Memory context use",
      "Model runtime",
      "Local model lifecycle",
      "Platform capabilities",
    ]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    expect(screen.getAllByText("Blocked").length).toBeGreaterThan(0);
    expect(screen.getByText("Degraded")).toBeInTheDocument();
    expect(screen.getByText("Partial")).toBeInTheDocument();
    expect(screen.getAllByText("Metadata only").length).toBeGreaterThan(0);
    expect(
      screen.getByLabelText("Settings kill-switch and feature-flag posture"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("status", {
        name: /Kill switch: Global runtime authority/i,
      }),
    ).toHaveTextContent("Not configured");
    expect(
      screen.getByRole("status", {
        name: /Feature flag: Authority visibility/i,
      }),
    ).toHaveTextContent("Metadata only");
    expect(
      screen.getByText(
        "contract-ref:product-loop-011-settings-kill-switch-clarity:v1",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("scripts/inspect_platform_capabilities.py").length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: /enable|toggle|save|execute/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /enable web|configure provider|connect connector|inject context|install|start|stop|connect|provider call|model call|browser action|shell action/i,
      }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Provider Guidance/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("provider-catalog:cost-literacy:mock-fallback"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/UNKNOWN_PAID_COST_REQUIRES_EXPLICIT_APPROVAL/i)
        .length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/OpenAI API/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/OPENAI_ENV_STYLE_REF/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText(/Pricing docs/i).length).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Provider credential readiness/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: /Provider and Settings diagnostics/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/readable_diagnostics_only/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.getByText(/CostGovernor provider spend boundary/i)).toBeInTheDocument();
    expect(screen.getAllByText(/^Missing$/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/^Disabled$/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/^Future scoped$/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/scripts\/inspect_provider_router_dry_run\.py/i)
        .length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/Unknown paid cost/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Above-budget estimate/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/Future receipt refs/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText(/Provider usage claims/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/cost-estimate-ref:openai-compatible:required/i)
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/budget-decision-ref:openai-compatible:required/i)
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/max-approved-usd-ref:openai-compatible:required/i)
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/cost-receipt-ref:openai-compatible:future-required/i)
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/UNKNOWN_PAID_COST_REQUIRES_APPROVAL/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/PROVIDER_USAGE_CLAIM_REQUIRES_RECEIPT_REFS/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("textbox", { name: /api key|secret|token/i }),
    ).not.toBeInTheDocument();

    settingsView.unmount();
    cleanup();

    window.history.pushState({}, "", "/models");
    render(<App />);

    expect(
      await screen.findByRole("heading", {
        name: /Backend-owned Local Models status/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/GET \/control-center\/local-models\/status/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("uaa_local_model_inventory.v1"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("model_download").length).toBeGreaterThan(0);
    expect(screen.getAllByText("model_pull").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("provider_model_authority").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("runtime_adapter_execution").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("Ollama")).toBeInTheDocument();
    expect(screen.getByText("MLX-LM")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Provider Cost Literacy/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("Quick chat")).toBeInTheDocument();
    expect(screen.getByText("CRM briefing")).toBeInTheDocument();
    expect(screen.getByText("Long document review")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Provider credential readiness/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Unknown paid cost/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/CostGovernor binding/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.queryByRole("button", {
        name: /download|switch|start|stop|execute/i,
      }),
    ).not.toBeInTheDocument();

    vi.unstubAllGlobals();
  });

  it("fails closed for stale Settings authority posture payloads", async () => {
    const staleSettingsStatus = JSON.parse(
      JSON.stringify(mockControlCenterData.settingsStatus),
    ) as Record<string, unknown>;
    staleSettingsStatus.authority_postures = "stale";
    delete staleSettingsStatus.kill_switch_postures;
    staleSettingsStatus.feature_flag_postures = [
      {
        label: "Unsafe",
        state_label: "Enabled",
        toggle_enabled: true,
      },
    ];
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      const urlText = String(url);
      if (
        !options?.method &&
        urlText.endsWith(API_ENDPOINTS.controlCenterSettingsStatus)
      ) {
        return new Response(
          JSON.stringify({ ok: true, data: staleSettingsStatus }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (
        !options?.method &&
        READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/settings");
    render(<App />);

    expect(
      await screen.findByRole("status", {
        name: /Settings authority posture blocked/i,
      }),
    ).toHaveTextContent("Settings authority posture unavailable");
    expect(screen.queryByText("Unsafe")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /enable|toggle|save|execute|install|start|stop|connect/i,
      }),
    ).not.toBeInTheDocument();

    vi.unstubAllGlobals();
  });

  it("fails closed for unsafe provider credential readiness dashboard payloads", async () => {
    const unsafeDashboard = JSON.parse(
      JSON.stringify(mockApiData.dashboard),
    ) as Record<string, unknown>;
    const unsafeReadiness = JSON.parse(
      JSON.stringify(
        mockControlCenterData.dashboard.provider_credential_readiness,
      ),
    ) as Record<string, unknown>;
    const unsafePostureCounts = unsafeReadiness.posture_counts as Record<
      string,
      unknown
    >;
    const unsafeProviders = unsafeReadiness.providers as Array<
      Record<string, unknown>
    >;
    unsafeReadiness.provider_runtime_authority_denied = false;
    unsafeReadiness.unknown_paid_cost_requires_approval = false;
    unsafePostureCounts.configured = 99;
    unsafeProviders[0].provider_model_refs_bound = true;
    (
      unsafeProviders[0].cost_governor_binding as Record<string, unknown>
    ).provider_use_authority_granted = true;
    unsafeDashboard.provider_credential_readiness = unsafeReadiness;

    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      const urlText = String(url);
      if (
        !options?.method &&
        urlText.endsWith(API_ENDPOINTS.controlCenterDashboard)
      ) {
        return new Response(
          JSON.stringify({ ok: true, result: unsafeDashboard }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (
        !options?.method &&
        READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/settings");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Settings$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Provider credential readiness/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/OpenAI-compatible provider/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/approval required/i).length).toBeGreaterThan(0);
    expect(screen.queryByText("99")).not.toBeInTheDocument();
    expect(
      screen.queryByText(/blocked posture missing/i),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /test provider|call provider|invoke provider/i,
      }),
    ).not.toBeInTheDocument();

    vi.unstubAllGlobals();
  });

  it("fails closed for nested provider readiness authority flags", async () => {
    const unsafeDashboard = JSON.parse(
      JSON.stringify(mockApiData.dashboard),
    ) as Record<string, unknown>;
    const unsafeReadiness = JSON.parse(
      JSON.stringify(
        mockControlCenterData.dashboard.provider_credential_readiness,
      ),
    ) as Record<string, unknown>;
    (
      unsafeReadiness.vault_adapter_readiness as Record<string, unknown>
    ).adapter_runtime_enabled = true;
    (
      unsafeReadiness.vault_adapter_readiness as Record<string, unknown>
    ).readiness_status = "vault-ready-bypass";
    (
      unsafeReadiness.enrollment_readiness as Record<string, unknown>
    ).enrollment_enabled = true;
    (
      unsafeReadiness.enrollment_readiness as Record<string, unknown>
    ).readiness_status = "enrollment-ready-bypass";
    (
      unsafeReadiness.validation_readiness as Record<string, unknown>
    ).validation_enabled = true;
    (
      unsafeReadiness.validation_readiness as Record<string, unknown>
    ).provider_response_persistence_allowed = true;
    (
      unsafeReadiness.validation_readiness as Record<string, unknown>
    ).readiness_status = "validation-ready-bypass";
    (
      unsafeReadiness.invocation_readiness as Record<string, unknown>
    ).invocation_enabled = true;
    (
      unsafeReadiness.invocation_readiness as Record<string, unknown>
    ).model_output_authoritative = true;
    (
      unsafeReadiness.invocation_readiness as Record<string, unknown>
    ).readiness_status = "invocation-ready-bypass";
    (
      unsafeReadiness.tiny_invocation_readiness as Record<string, unknown>
    ).invocation_enabled = true;
    (
      unsafeReadiness.tiny_invocation_readiness as Record<string, unknown>
    ).provider_sdk_call_enabled = true;
    (
      unsafeReadiness.tiny_invocation_readiness as Record<string, unknown>
    ).network_call_enabled = true;
    (
      unsafeReadiness.tiny_invocation_readiness as Record<string, unknown>
    ).billing_authority_granted = true;
    (
      unsafeReadiness.tiny_invocation_readiness as Record<string, unknown>
    ).status = "tiny-ready-bypass";
    (
      unsafeReadiness.router_dry_run_readiness as Record<string, unknown>
    ).invocation_authorized = true;
    (
      unsafeReadiness.router_dry_run_readiness as Record<string, unknown>
    ).provider_sdk_call_performed = true;
    (
      unsafeReadiness.router_dry_run_readiness as Record<string, unknown>
    ).billing_authority_granted = true;
    (
      unsafeReadiness.router_dry_run_readiness as Record<string, unknown>
    ).status = "router-ready-bypass";
    (
      unsafeReadiness.provider_settings_diagnostics as Record<string, unknown>
    ).provider_sdk_call_enabled = true;
    (
      unsafeReadiness.provider_settings_diagnostics as Record<string, unknown>
    ).status = "unsafe_provider_settings_diagnostics";
    ((
      unsafeReadiness.provider_settings_diagnostics as Record<string, unknown>
    ).items as Array<Record<string, unknown>>)[0].state_label =
      "Unsafe enabled diagnostic";
    unsafeDashboard.provider_credential_readiness = unsafeReadiness;

    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      const urlText = String(url);
      if (
        !options?.method &&
        urlText.endsWith(API_ENDPOINTS.controlCenterDashboard)
      ) {
        return new Response(
          JSON.stringify({ ok: true, result: unsafeDashboard }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (
        !options?.method &&
        READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/settings");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Settings$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/blocked_no_approved_backend/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/blocked_not_scoped/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText(/validation_blocked/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.queryByText(/vault-ready-bypass/i)).not.toBeInTheDocument();
    expect(
      screen.queryByText(/enrollment-ready-bypass/i),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(/validation-ready-bypass/i),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(/invocation-ready-bypass/i),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/tiny-ready-bypass/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/router-ready-bypass/i)).not.toBeInTheDocument();
    expect(
      screen.queryByText(/unsafe_provider_settings_diagnostics/i),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(/Unsafe enabled diagnostic/i),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /validate provider|invoke provider/i,
      }),
    ).not.toBeInTheDocument();

    vi.unstubAllGlobals();
  });

  it("shows governed provider credential readiness without credential collection", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/settings");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Settings$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Provider credential readiness/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: /Provider and Settings diagnostics/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Cost blocked/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Credential vault adapter/i)).toBeInTheDocument();
    expect(
      screen.getAllByText(/Provider router dry-run/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/scripts\/inspect_settings_authority_posture\.py/i)
        .length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/reference_readiness_only/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Provider invocation/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText(/Tiny exact-approved provider lane/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Disabled no execution/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/Live adapter blocked/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText(/Live receipt required/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText(/Usage captured/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Cost captured/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Cost incomplete/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Review required/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Further use blocked/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText(/Receipt completeness/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText(/Receipt observation/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText(/Receipt observation labels/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/no receipt observed/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText(/No provider authority/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/TINY_PROVIDER_LANE_DISABLED_BY_DEFAULT/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/Raw key collection/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText(/Credential material stored/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/Vault adapter/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Credential adapter readiness/i),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Credential enrollment/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/Validation readiness/i)).toBeInTheDocument();
    expect(screen.getByText(/External validation/i)).toBeInTheDocument();
    expect(screen.getByText(/Validation authority/i)).toBeInTheDocument();
    expect(screen.getAllByText(/approval required/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Provider response persistence allowed/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Invocation readiness/i)).toBeInTheDocument();
    expect(screen.getByText(/Vault adapter contract/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Credential enrollment contract/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Provider validation contract/i),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Governed provider invocation/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/VAULT_ADAPTER_NOT_SCOPED/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/EXACT_APPROVAL_REQUIRED/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/VALIDATION_ADAPTER_DISABLED_BY_DEFAULT/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/CREDENTIAL_ENROLLMENT_NOT_SCOPED/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/TRANSIENT_SECRET_INTAKE_NOT_APPROVED/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/APPROVED_VAULT_BACKEND_REQUIRED/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/POLICY_APPROVAL_AUDIT_RECEIPT_REQUIRED/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/OpenAI-compatible provider/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/provider auth ref status/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/consent-ref:/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/policy-ref:/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/revocation-ref:/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/PROVIDER_INVOCATION_NOT_SCOPED/i).length,
    ).toBeGreaterThan(0);

    expect(
      screen.queryByRole("textbox", { name: /api key|secret|token/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /save key|connect provider/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /test provider|call provider/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /enroll credential|add credential|store credential|resolve credential/i,
      }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /validate provider|invoke provider/i,
      }),
    ).not.toBeInTheDocument();
  });

  it("renders macOS setup assistant preview without installer authority", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/setup");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /macOS Setup Assistant/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Visual setup preview/i)).toBeInTheDocument();
    expect(screen.getByText("First-run proof spine")).toBeInTheDocument();
    expect(screen.getByText("Local package proof")).toBeInTheDocument();
    expect(screen.getByText("Exact promotion path")).toBeInTheDocument();
    expect(
      screen.getByText("packaging-proof:local-macos-app-bundle"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("script:verify-local-macos-app-bundle-proof"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Provider setup is reference-only/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Provider Catalog/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Provider account guidance/i)).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: /Provider credential and cost posture/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Unknown paid cost/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/No provider authority/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Disabled no execution/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/Live adapter blocked/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText(/CostGovernor binding/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText(/Provider router dry-run/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/No fallback execution/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Router no-authority refs/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/Setup docs/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/API docs/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Pricing docs/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Secret entry controls/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("textbox", { name: /api key|secret|token/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /save key|connect provider|test provider|call provider|invoke provider/i,
      }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Local prerequisites/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/existing local status routes only/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText("/runtime/readiness").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("/runtime/capability-matrix").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Blocked setup authority/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("macos-setup-bridge-enablement"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("macos-setup-rollback-execution"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("macos-setup-signed-distribution"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("macos-setup-production-authority"),
    ).toBeInTheDocument();
    expect(screen.getByText(/First launch setup/i)).toBeInTheDocument();
    expect(screen.getByText(/Runtime health/i)).toBeInTheDocument();
    expect(
      screen.getAllByText(/Local model readiness/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/Model selection/i)).toBeInTheDocument();
    expect(screen.getByText(/Fast local chat/i)).toBeInTheDocument();
    expect(screen.getByText(/Balanced local assistant/i)).toBeInTheDocument();
    expect(screen.getByText(/Coding local assistant/i)).toBeInTheDocument();
    expect(
      screen.getAllByText(/approval-ref:macos-setup-model-selection/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Dry-run approval envelopes/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("macos-setup-approval-envelope:model-selection")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("idempotency-ref:macos-setup-model-selection").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("scope-ref:macos-setup-model-selection"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/approval refs are identifiers only/i),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Preview only\. Raw logs, raw paths/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(/macos-setup-receipt-plan:foundation/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/macos-setup-rollback-plan:foundation/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/OpenWebUI bridge/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Mattermost Agent Rooms/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/Verify the model choices/i)).toBeInTheDocument();
    expect(screen.getAllByText(/no command executed/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText(/Installer side effects/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: /^run$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^install$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^approve$/i }),
    ).not.toBeInTheDocument();
  });

  it("covers first product loop browser smoke readiness with truthful backend-bound states", async () => {
    const firstLoopStates = {
      openControlCenter: "mock_fallback",
      inspectRuntimeHealthAndModelReadiness: "route_ready",
      selectOrApproveLocalGgufModel: "backend_gated",
      chatShellThroughUaaV1: "gateway_gated",
      createTaskDecompositionPlan: "backend_gated",
      approveSafeRegisteredCapability: "backend_authority",
      inspectReceiptAuditLatencyRollback: "inspection_ready",
    };

    expect(firstLoopStates).toEqual({
      openControlCenter: "mock_fallback",
      inspectRuntimeHealthAndModelReadiness: "route_ready",
      selectOrApproveLocalGgufModel: "backend_gated",
      chatShellThroughUaaV1: "gateway_gated",
      createTaskDecompositionPlan: "backend_gated",
      approveSafeRegisteredCapability: "backend_authority",
      inspectReceiptAuditLatencyRollback: "inspection_ready",
    });

    mockFetchWithFallback();
    window.history.pushState({}, "", "/dashboard");
    const dashboard = render(<App />);
    expect(
      await screen.findByRole("heading", { name: /Dashboard overview/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByRole("heading", { name: /Operator Loop/i }).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/Runtime health/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Local model readiness/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Chat through UAA \/v1/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Task decomposition plan/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/One safe capability approval/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(/Receipt, audit, latency, rollback/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Frontend authority/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getByText(/Frontend\/generic mutation authority/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Production readiness claim/i)).toBeInTheDocument();
    expect(screen.getByText(/Model output authoritative/i)).toBeInTheDocument();
    expect(screen.getByText(/Prompt content recording/i)).toBeInTheDocument();
    expect(screen.getByText(/Provider payload recording/i)).toBeInTheDocument();
    expect(
      screen.getByText(/inspect_local_backend_loop_routes/i),
    ).toBeInTheDocument();
    expect(screen.getByText("Mock fallback active")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Backend unavailable; showing non-authoritative mock fallback data/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/API base: relative local API/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/No generic execution/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Local task authority requires backend approval/i),
    ).toBeInTheDocument();
    dashboard.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/runtime");
    const runtime = render(<App />);
    expect(
      await screen.findByRole("heading", { name: /Runtime readiness/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Production readiness claim/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Reviewed local model runtime evidence/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Local contract state only/i)).toBeInTheDocument();
    runtime.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/runtime/local");
    const localRuntime = render(<App />);
    expect(
      await screen.findByRole("heading", { name: /Local Runtime Status/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/NO_RUNTIME_EXECUTION/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getByText(/Model output remains non-authoritative/i),
    ).toBeInTheDocument();
    localRuntime.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/runtime/manual-smoke");
    const manualSmoke = render(<App />);
    expect(
      await screen.findByRole("heading", {
        name: /Manual Smoke Control Surface/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Manual smoke reports are safe summaries/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/no smoke attempt was performed/i),
    ).toBeInTheDocument();
    manualSmoke.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/action-preview");
    const actionPreview = render(<App />);
    expect(
      await screen.findByText(/Preview only action request/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /never runs, enables, grants, deploys, or dispatches anything/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/approval reference is never treated as authority/i),
    ).toBeInTheDocument();
    actionPreview.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/approvals");
    const approvals = render(<App />);
    expect(
      await screen.findByRole("heading", { name: /Approval Queue/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/No approval was granted from this UI/i),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(
        /Python Agent Core remains the only approval authority/i,
      ).length,
    ).toBeGreaterThan(0);
    approvals.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/events/timeline");
    const evidence = render(<App />);
    expect(
      await screen.findByRole("heading", { name: /Event Timeline/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Trace detail is redacted summary metadata only/i),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Foundation Gate evidence summary/i).length,
    ).toBeGreaterThan(0);
    evidence.unmount();
    vi.unstubAllGlobals();

    for (const forbidden of [
      /raw json/i,
      /completed successfully/i,
      /production ready for external users/i,
      /^execute$/i,
      /^run$/i,
      /^send$/i,
      /^approve$/i,
    ]) {
      expect(screen.queryByText(forbidden)).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: forbidden }),
      ).not.toBeInTheDocument();
    }
  });

  it("renders the UAA-P1-011 operator loop as one readable proof chain", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/operator-loop");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Operator Loop/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/First product loop proof/i)).toBeInTheDocument();
    expect(screen.getByText(/Steps surfaced/i)).toBeInTheDocument();
    expect(screen.getByText(/Routes surfaced/i)).toBeInTheDocument();
    expect(screen.getByText(/Blocked prerequisites/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Approval and evidence proof/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Approval refs are identifiers only/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Route side-effect classes/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Side-effect class/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/local_dev_workspace_only/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/validation_only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/receipt_refs/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/audit_refs/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/rollback_refs/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/capability_latency_metrics/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Model output authority/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: /^run$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^execute$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^approve$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^send$/i }),
    ).not.toBeInTheDocument();
  });

  it("renders UAA-P1-054 differentiator screens without adding authority controls", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/differentiators");
    render(<App />);

    expect(
      await screen.findByRole("heading", {
        name: /Control Center Differentiators/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/safe-ref \/ redacted-first/i)).toBeInTheDocument();
    expect(
      screen.getByText(/OpenAPI, \/api\/manifest, PolicyEngine/i),
    ).toBeInTheDocument();

    const routePanel = screen
      .getByRole("heading", { name: /Route Authority/i })
      .closest("article");
    expect(routePanel).not.toBeNull();
    expect(
      within(routePanel!).getByText(/OpenAPI path count/i),
    ).toBeInTheDocument();
    expect(
      within(routePanel!).getByText(String(MOCK_OPENAPI_ROUTE_COUNT)),
    ).toBeInTheDocument();
    expect(
      within(routePanel!).getByText(/Operation IDs unique/i),
    ).toBeInTheDocument();
    expect(
      within(routePanel!).getAllByText(/Contract truth/i).length,
    ).toBeGreaterThan(0);
    expect(
      within(routePanel!).getAllByText(/Side-effect class/i).length,
    ).toBeGreaterThan(0);
    expect(
      within(routePanel!).getAllByText(/Owner \/ service/i).length,
    ).toBeGreaterThan(0);
    expect(
      within(routePanel!).getByText(/docs\/api\/openapi_contract.md/i),
    ).toBeInTheDocument();

    const approvalPanel = screen
      .getByRole("heading", { name: /Approval State/i })
      .closest("article");
    expect(approvalPanel).not.toBeNull();
    expect(
      within(approvalPanel!).getByText(/Approval ref/i),
    ).toBeInTheDocument();
    expect(
      within(approvalPanel!).getByText(/Exact scope/i),
    ).toBeInTheDocument();
    expect(
      within(approvalPanel!).getByText(/Stale \/ expiry/i),
    ).toBeInTheDocument();
    expect(
      within(approvalPanel!).getByText(/refs are identifiers only/i),
    ).toBeInTheDocument();
    expect(
      within(approvalPanel!).getByText(/mock_receipt_ref_001/i),
    ).toBeInTheDocument();

    const receiptPanel = screen
      .getByRole("heading", { name: /Evidence Receipts/i })
      .closest("article");
    expect(receiptPanel).not.toBeNull();
    expect(
      within(receiptPanel!).getByText(/Foundation Gate refs/i),
    ).toBeInTheDocument();
    expect(
      within(receiptPanel!).getByText(/foundation-gate-ref:latest-report/i),
    ).toBeInTheDocument();
    expect(
      within(receiptPanel!).getByText(/Latency refs/i),
    ).toBeInTheDocument();
    expect(
      within(receiptPanel!).getByText(
        /latency-ref:foundation-gate:latest-report/i,
      ),
    ).toBeInTheDocument();
    expect(
      within(receiptPanel!).getByText(/Rollback refs/i),
    ).toBeInTheDocument();

    const workspacePanel = screen
      .getByRole("heading", { name: /Safe Workspace Preview/i })
      .closest("article");
    expect(workspacePanel).not.toBeNull();
    expect(
      within(workspacePanel!).getByText(/bounded preview/i),
    ).toBeInTheDocument();
    expect(
      within(workspacePanel!).getByText(/Path posture/i),
    ).toBeInTheDocument();
    expect(
      within(workspacePanel!).getByText(/redacted_safe_label_only/i),
    ).toBeInTheDocument();
    expect(
      within(workspacePanel!).getByText(/patch apply, rollback execution/i),
    ).toBeInTheDocument();

    const modelPanel = screen
      .getByRole("heading", { name: /Local Model \/ M167 Status/i })
      .closest("article");
    expect(modelPanel).not.toBeNull();
    expect(
      within(modelPanel!).getByText(/Runtime readiness/i),
    ).toBeInTheDocument();
    expect(
      within(modelPanel!).getByText(/OpenWebUI shell/i),
    ).toBeInTheDocument();
    expect(
      within(modelPanel!).getByText(/output is not production authority/i),
    ).toBeInTheDocument();
    expect(
      within(modelPanel!).getByText(/model download, GGUF approval/i),
    ).toBeInTheDocument();

    const observabilityPanel = screen
      .getByRole("heading", { name: /M167 Observability Timeline/i })
      .closest("article");
    expect(observabilityPanel).not.toBeNull();
    expect(
      within(observabilityPanel!).getByText(/Session \/ run ref/i),
    ).toBeInTheDocument();
    expect(
      within(observabilityPanel!).getByText(/Client-error posture/i),
    ).toBeInTheDocument();
    expect(
      within(observabilityPanel!).getByText(
        /unredacted forensic mode is blocked/i,
      ),
    ).toBeInTheDocument();
    expect(
      within(observabilityPanel!).getByText(/External telemetry/i),
    ).toBeInTheDocument();

    for (const label of [
      /^approve$/i,
      /^deny$/i,
      /^grant$/i,
      /^revoke$/i,
      /^execute$/i,
      /^run$/i,
      /^send$/i,
      /^write$/i,
      /^download$/i,
      /^upload$/i,
      /^export$/i,
      /^start$/i,
      /^stop$/i,
      /^install$/i,
      /^load$/i,
      /^browse$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(
      screen.queryByText(/provider payload content/i),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/environment dump/i)).not.toBeInTheDocument();
  });

  it("renders loading and empty states with safe operational copy", () => {
    const { rerender } = render(<LoadingState />);
    expect(screen.getByRole("status")).toHaveTextContent(
      /loading local control center/i,
    );
    expect(
      screen.getByText(/checking local backend connection state/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/read-only/i)).toBeInTheDocument();

    rerender(
      <EmptyState
        title="No routes listed"
        message="No API routes were returned by the local mock."
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent(/No routes listed/i);
    expect(
      screen.getByText(/No API routes were returned/i),
    ).toBeInTheDocument();

    rerender(
      <ErrorState message="Control Center data could not be loaded safely." />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      /Control Center data unavailable/i,
    );
    expect(
      screen.getByText(/Next safe action: verify the local backend/i),
    ).toBeInTheDocument();
  });

  it("keeps backend checking state informational while reads are pending", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise(() => undefined)),
    );
    window.history.pushState({}, "", "/dashboard");
    render(<App />);

    expect(screen.getByRole("status")).toHaveTextContent(
      /checking local backend connection state/i,
    );
    expect(
      screen.queryByRole("button", { name: /execute/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /approve/i }),
    ).not.toBeInTheDocument();
  });

  it("renders M15 approval queue as read-only preview-only summaries", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/approvals");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Approval Queue/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/read-only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/preview-only/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Approval Authority handles final decision/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText("mock_approval_ref_001").length).toBeGreaterThan(
      0,
    );
    expect(screen.getByText(/risk: medium/i)).toBeInTheDocument();
    expect(screen.getByText(/data: internal/i)).toBeInTheDocument();
    expect(
      screen.getByText(/CONTROL_CENTER_REVIEW_REQUIRED/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/No approval was granted from this UI/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^approve$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^deny$/i }),
    ).not.toBeInTheDocument();
  });

  it("makes approval detail authority boundaries explicit without dark-pattern action language", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/approvals");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Approval Queue/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(
        /This UI cannot grant, deny, execute, or bypass approvals/i,
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        /Approval refs are identifiers only and never authority/i,
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        /Python Agent Core remains the only approval authority/i,
      ).length,
    ).toBeGreaterThan(0);

    for (const label of [
      /^approve$/i,
      /^deny$/i,
      /^execute$/i,
      /^run$/i,
      /^send$/i,
      /^deploy$/i,
      /^enable$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
  });

  it("renders M15 receipt summaries and details without raw sensitive content", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/receipts");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Receipt Viewer/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/redacted summary-only receipt records/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText("mock_receipt_ref_001").length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText(/redacted_summary_only/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/No receipt mutation is available from this UI/i)
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(/Receipt detail is redacted summary metadata only/i),
    ).toBeInTheDocument();
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw file/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw memory/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/supersecretvalue123/i)).not.toBeInTheDocument();
  });

  it("renders M15 event summaries and details without raw prompt file memory or credentials", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/events");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Event Viewer/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/redacted event summaries/i)).toBeInTheDocument();
    expect(screen.getAllByText("mock_event_ref_001").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/source: CCC Web mock surface/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(/No event action is available from this UI/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Event detail is redacted summary metadata only/i),
    ).toBeInTheDocument();
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw file/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw memory/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/credential/i)).not.toBeInTheDocument();
  });

  it("renders M16 event timeline and run receipt trace summaries without raw payloads", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/events/timeline");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Event Timeline/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/M16 trace surface/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Timeline and trace views are read-only/i),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/redacted summary-only/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("mock_run_ref_001").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("mock_correlation_ref_001").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("mock_event_ref_001").length).toBeGreaterThan(0);
    expect(screen.getAllByText("mock_receipt_ref_001").length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText("mock_evidence_ref_gate_001").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Foundation Gate evidence summary/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(/No trace export or external telemetry is available/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Trace detail is redacted summary metadata only/i),
    ).toBeInTheDocument();

    for (const label of [
      /^execute$/i,
      /^run$/i,
      /^export$/i,
      /^send$/i,
      /^deploy$/i,
      /^enable$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw secret/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw file/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw memory/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw credential/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/provider payload/i)).not.toBeInTheDocument();
  });

  it("switches the selected M16 trace while keeping the timeline read-only", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/events/timeline");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Event Timeline/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByRole("heading", { name: "mock_event_ref_001" }).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("article", { name: /mock_event_ref_001/i }),
    ).toHaveAttribute("aria-current", "true");

    const traceButtons = screen.getAllByRole("button", { name: /view trace/i });
    fireEvent.click(traceButtons[1]);

    expect(
      screen.getAllByRole("heading", { name: "mock_event_ref_002" }).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("article", { name: /mock_event_ref_002/i }),
    ).toHaveAttribute("aria-current", "true");
    expect(
      screen.getByText(/Trace detail is redacted summary metadata only/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/NO_PRODUCTION_AUTHORITY/i).length,
    ).toBeGreaterThan(0);

    for (const label of [
      /^execute$/i,
      /^run$/i,
      /^export$/i,
      /^send$/i,
      /^write$/i,
      /^deploy$/i,
      /^enable$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw secret/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw file/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw memory/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw credential/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/provider payload/i)).not.toBeInTheDocument();
  });

  it("renders M17 evidence summaries and details as read-only redacted metadata", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/evidence");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Evidence Viewer/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/M17 knowledge surface/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Evidence views are read-only/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/REDACTED_SUMMARY_ONLY/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("mock_evidence_ref_001").length).toBeGreaterThan(
      0,
    );
    expect(screen.getByText(/Source type/i)).toBeInTheDocument();
    expect(screen.getByText(/Provenance summary/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Evidence detail is redacted summary metadata only/i),
    ).toBeInTheDocument();

    for (const label of [
      /^execute$/i,
      /^run$/i,
      /^write$/i,
      /^delete$/i,
      /^reveal raw$/i,
      /^show raw$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw secret/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw file/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw memory/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/provider payload/i)).not.toBeInTheDocument();
  });

  it("renders FCC-P1-006 Evidence Timeline as readable safe refs", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/evidence");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Evidence Timeline/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(
        "implemented_productized_evidence_timeline_safe_refs_only",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("GET /control-center/evidence/timeline").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Operator Run Timeline/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("contract-ref:operator-run-timeline:v1").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "implemented_read_only_operator_run_timeline_safe_refs_only",
      ).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/Five borrowed patterns/i)).toBeInTheDocument();
    for (const patternId of [
      "typed_event_ledger",
      "run_control_states",
      "evidence_based_completion",
      "approval_preview_and_rejection_feedback",
      "evidence_condensing_with_safe_refs",
    ]) {
      expect(screen.getAllByText(new RegExp(patternId)).length).toBeGreaterThan(
        0,
      );
    }
    expect(screen.getByText(/Frontier AI cost telemetry/i)).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:frontier-ai-cost-usage-telemetry:v1")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("accounting_slots_ready_no_provider_calls").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("budget-status:unknown-paid-cost-requires-approval")
        .length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("provider-ref:not-invoked")).toBeInTheDocument();
    expect(
      screen.getByText("model-profile-ref:not-invoked"),
    ).toBeInTheDocument();
    expect(screen.getByText("Estimated cost USD")).toBeInTheDocument();
    expect(screen.getAllByText(/Evidence narrative/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getByText(
        /Narrative entries are unavailable from the backend response/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Evidence history grammar")).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:evidence-history-grammar:v1").length,
    ).toBeGreaterThan(0);
    for (const question of [
      "What was proposed?",
      "What was approved?",
      "What happened?",
      "What changed?",
      "What can be undone?",
      "What is stale?",
      "What remains blocked?",
    ]) {
      expect(screen.getAllByText(question).length).toBeGreaterThan(0);
    }
    expect(
      screen.getAllByText(/Approval ref authority/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/Rollback execution/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText(/Memory truth authority/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Raw evidence included/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/Private source artifacts/i)).toBeInTheDocument();
    expect(
      screen.getAllByText(/Approval refs are identifiers only/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(/rollback refs do not perform rollback/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Foundation Gate refs do not confer release authority/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/latency refs are measurement evidence only/i),
    ).toBeInTheDocument();

    for (const marker of [
      "receipt_audit_rollback_ref",
      "action_envelope_created",
      "today_item",
      "evidence-event:action-envelope-created-mock-founder-loop",
      "action-envelope:plans:founder-loop-mock",
      "audit-plan:founder-loop:mock-setup-hardening",
      "idempotency-ref:founder-loop:mock-setup-hardening",
      "rollback_not_applicable_or_not_scoped",
      "rollback_execution_not_scoped",
      "no_raw_evidence_display",
      "no_approval_ref_authority",
      "no_context_injection",
      "no_action_execution",
      "no_connector_write",
    ]) {
      expect(screen.getAllByText(marker).length).toBeGreaterThan(0);
    }

    for (const label of [
      /^execute$/i,
      /^run$/i,
      /^write$/i,
      /^delete$/i,
      /^rollback$/i,
      /^approve$/i,
      /^send$/i,
      /^sync$/i,
      /^reveal raw$/i,
      /^show raw$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw response/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/provider payload/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw path/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw log/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/environment dump/i)).not.toBeInTheDocument();
  });

  it("renders Evidence Timeline narrative entries", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async (url: RequestInfo | URL) =>
          new Response(JSON.stringify(envelopeForReadEndpoint(String(url))), {
            headers: { "Content-Type": "application/json" },
          }),
      ),
    );
    window.history.pushState({}, "", "/evidence");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Evidence Timeline/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Evidence narrative/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText(
        "contract-ref:product-loop-010-evidence-timeline-narrative:v1",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "implemented_evidence_timeline_narrative_safe_refs_only",
      ).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("What happened")).toBeInTheDocument();
    expect(screen.getByText("Why recorded")).toBeInTheDocument();
    expect(screen.getByText("Approval posture")).toBeInTheDocument();
    expect(screen.getByText("Still blocked")).toBeInTheDocument();
    expect(screen.getByText("Inspect")).toBeInTheDocument();
    expect(
      screen.getByText(
        /A reviewable Today-to-Action evidence event was recorded as safe refs/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: /Narrative: Setup Assistant hardening review/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("evidence-narrative:mock-founder-loop").length,
    ).toBeGreaterThan(0);
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/provider payload/i)).not.toBeInTheDocument();
  });

  it("renders Run Observability on Evidence without runtime controls", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async (url: RequestInfo | URL) =>
          new Response(JSON.stringify(envelopeForReadEndpoint(String(url))), {
            headers: { "Content-Type": "application/json" },
          }),
      ),
    );
    window.history.pushState({}, "", "/evidence");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Evidence Timeline/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Run Observability/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("implemented_read_only").length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText("GET /control-center/runs/observability").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "python -m ultimate_ai_agent.core.task_decomposition.cli inspect-run-observability",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/blocked_no_live_stream_runtime/).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/blocked_no_connector_write_or_send/).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("presentation only").length).toBeGreaterThan(0);
    for (const label of [
      /^cancel$/i,
      /^resume$/i,
      /^stream$/i,
      /^execute$/i,
      /^send$/i,
      /^retry$/i,
      /^deliver$/i,
      /^approve$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(
      [...primaryNavItems, ...supportingNavItems].some(
        (item) => item.path === "/runs",
      ),
    ).toBe(false);
    expect(
      [...primaryNavItems, ...supportingNavItems].some(
        (item) => item.path === "/proof" && item.releaseStatus === "partial",
      ),
    ).toBe(true);
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw response/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/provider payload/i)).not.toBeInTheDocument();
  });

  it("fails closed for unsafe Evidence Timeline narrative payloads", async () => {
    const unsafeEvidence = JSON.parse(
      JSON.stringify(mockControlCenterData.founderEvidenceTimeline),
    );
    unsafeEvidence.narrative_read_model.entries[0].what_happened =
      "raw prompt should not render";
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: RequestInfo | URL) => {
        const urlText = String(url);
        if (urlText.endsWith(API_ENDPOINTS.founderEvidenceTimeline)) {
          return new Response(
            JSON.stringify({ ok: true, result: unsafeEvidence }),
            { headers: { "Content-Type": "application/json" } },
          );
        }
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          headers: { "Content-Type": "application/json" },
        });
      }),
    );
    window.history.pushState({}, "", "/evidence");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Evidence Timeline/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Narrative entries are unavailable from the backend response/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/raw prompt should not render/i),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(
        "contract-ref:product-loop-010-evidence-timeline-narrative:v1",
      ),
    ).not.toBeInTheDocument();
  });

  it("does not backfill Evidence Timeline narrative from mocks", async () => {
    const evidenceWithoutNarrative = {
      ...(mockControlCenterData.founderEvidenceTimeline as unknown as Record<
        string,
        unknown
      >),
    };
    delete evidenceWithoutNarrative.narrative_read_model;
    delete evidenceWithoutNarrative.narrative_contract_ref;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: RequestInfo | URL) => {
        const urlText = String(url);
        if (urlText.endsWith(API_ENDPOINTS.founderEvidenceTimeline)) {
          return new Response(
            JSON.stringify({ ok: true, result: evidenceWithoutNarrative }),
            { headers: { "Content-Type": "application/json" } },
          );
        }
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          headers: { "Content-Type": "application/json" },
        });
      }),
    );
    window.history.pushState({}, "", "/evidence");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Evidence Timeline/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Narrative entries are unavailable from the backend response/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByText("evidence-narrative:mock-founder-loop"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(
        "contract-ref:product-loop-010-evidence-timeline-narrative:v1",
      ),
    ).not.toBeInTheDocument();
  });

  it("renders M17 file ref summaries without raw file contents or filesystem controls", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/files");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /File Reference Viewer/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/File ref views are read-only/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText("mock_file_ref_001").length).toBeGreaterThan(0);
    expect(screen.getByText(/Safe filename/i)).toBeInTheDocument();
    expect(
      screen.getByText(/File writes are not available from this UI/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/No filesystem browsing is available/i),
    ).toBeInTheDocument();

    for (const label of [
      /open file/i,
      /delete file/i,
      /write file/i,
      /browse filesystem/i,
      /^execute$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw file content/i)).not.toBeInTheDocument();
    expect(
      screen.queryByText(new RegExp("/Users/", "i")),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/\/home\//i)).not.toBeInTheDocument();
  });

  it("renders M37 file review packets with review-only approval capture controls", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/files/review");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /File Review Surface/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/M37 review approval capture/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/mock and non-authoritative/i)).toBeInTheDocument();
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/NO_PRODUCTION_AUTHORITY/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/Review-only surface/i)).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /^Redacted preview$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Reviewed change summary mentions \[REDACTED:SECRET_ASSIGNMENT\]/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/Redaction summary/i)).toBeInTheDocument();
    expect(
      screen.getByText(
        /Secret-like assignment and private path fragments were removed before display/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/Exact binding refs/i)).toBeInTheDocument();
    expect(
      screen.getAllByText("file-review-packet:mock_001").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("redacted-file-preview-output:mock_001"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("file-review-redaction-summary:mock_001"),
    ).toBeInTheDocument();
    expect(screen.getByText("file-ref:mock_review_001")).toBeInTheDocument();
    expect(
      screen.getByText(
        "filesystem-preview-path:safe-root_m36/docs/review-summary.md",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Approval gate contract status/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/exact_binding_ready/i)).toBeInTheDocument();
    expect(screen.getByText(/Receipt plan metadata/i)).toBeInTheDocument();
    expect(screen.getByText(/raw content stored: no/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /approve review-only/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /deny review-only/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /captures a review-only approval record bound to this exact redacted packet/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(
        /does not grant raw file access, context proposal, context injection, memory writes, export, or execution/i,
      ).length,
    ).toBeGreaterThan(0);
  });

  it("keeps M37 approval capture review-only without raw or authority controls", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/files/review");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /File Review Surface/i }),
    ).toBeInTheDocument();
    const reviewButtons = screen.getAllByRole("button", {
      name: /view review packet/i,
    });
    expect(reviewButtons.length).toBeGreaterThan(1);
    fireEvent.click(reviewButtons[1]);

    expect(
      screen.getAllByRole("heading", { name: "file-review-packet:mock_002" })
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("article", { name: /file-review-packet:mock_002/i }),
    ).toHaveAttribute("aria-current", "true");
    expect(screen.getByText("file-ref:mock_review_002")).toBeInTheDocument();
    expect(
      screen.getByText(
        "filesystem-preview-path:safe-root_m36/docs/alternate-review.md",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Review approval capture is review-only persistence/i)
        .length,
    ).toBeGreaterThan(0);

    for (const label of [
      /^approve raw/i,
      /^deny raw/i,
      /^submit$/i,
      /^save$/i,
      /mark reviewed/i,
      /mark-reviewed/i,
      /^export$/i,
      /^download$/i,
      /copy raw/i,
      /file picker/i,
      /browse/i,
      /upload/i,
      /root selector/i,
      /open raw file/i,
      /context proposal/i,
      /inject/i,
      /write memory/i,
      /^execute$/i,
      /^run$/i,
      /run tool/i,
      /call model/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(
      screen.getByRole("button", { name: /approve review-only/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /deny review-only/i }),
    ).toBeInTheDocument();
    expect(screen.queryByText(/raw_content/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/full_file_content/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/unredacted_preview/i)).not.toBeInTheDocument();
    expect(
      screen.queryByText(new RegExp("/Users/", "i")),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/\/home\//i)).not.toBeInTheDocument();
    expect(screen.queryByText(/supersecretvalue123/i)).not.toBeInTheDocument();
  });

  it("captures a mock M37 review-only decision without authority", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/files/review");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /File Review Surface/i }),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: /approve review-only/i }),
    );

    expect(screen.getByText(/approved_for_review_only/i)).toBeInTheDocument();
    expect(screen.getByText(/capture persisted: yes/i)).toBeInTheDocument();
    expect(screen.getByText(/raw access authorized: no/i)).toBeInTheDocument();
    expect(
      screen.getByText(/context proposal authorized: no/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/memory write authorized: no/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/export authorized: no/i)).toBeInTheDocument();
    expect(screen.getByText(/execution authorized: no/i)).toBeInTheDocument();
  });

  it("does not carry review-only capture state across packet selection", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/files/review");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /File Review Surface/i }),
    ).toBeInTheDocument();

    // Approve review-only on the first (default-selected) packet.
    fireEvent.click(
      screen.getByRole("button", { name: /approve review-only/i }),
    );
    expect(screen.getByText(/approved_for_review_only/i)).toBeInTheDocument();

    // Switching to a different packet must reset the capture state to that
    // packet's own value rather than leaking the first packet's approval.
    const reviewButtons = screen.getAllByRole("button", {
      name: /view review packet/i,
    });
    fireEvent.click(reviewButtons[1]);

    expect(
      screen.getByRole("article", { name: /file-review-packet:mock_002/i }),
    ).toHaveAttribute("aria-current", "true");
    expect(
      screen.queryByText(/approved_for_review_only/i),
    ).not.toBeInTheDocument();
    expect(screen.getAllByText(/not_captured/i).length).toBeGreaterThan(0);

    fireEvent.click(reviewButtons[0]);

    expect(
      screen.getByRole("article", { name: /file-review-packet:mock_001/i }),
    ).toHaveAttribute("aria-current", "true");
    expect(screen.getByText(/approved_for_review_only/i)).toBeInTheDocument();
    expect(screen.getByText(/capture persisted: yes/i)).toBeInTheDocument();
  });

  it("keeps M37 binding refs safe and free of private path shapes", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/files/review");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /File Review Surface/i }),
    ).toBeInTheDocument();

    const documentText = document.body.textContent ?? "";
    for (const safeRef of [
      "file-review-packet:mock_001",
      "redacted-file-preview-output:mock_001",
      "file-review-redaction-summary:mock_001",
      "file-ref:mock_review_001",
      "filesystem-preview-path:safe-root_m36/docs/review-summary.md",
    ]) {
      expect(documentText).toContain(safeRef);
    }

    for (const unsafeFragment of [
      "/Users/",
      "/home/",
      "C:\\",
      "../",
      "absolute_path",
      "raw_absolute_path",
      "raw file path",
    ]) {
      expect(documentText.toLowerCase()).not.toContain(
        unsafeFragment.toLowerCase(),
      );
    }

    expect(screen.getAllByText(/safe refs only/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        /Only the review approval capture route may persist safe refs/i,
      ).length,
    ).toBeGreaterThan(0);
  });

  it("renders M39 context proposals as read-only safe proposal summaries", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/context/proposals");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Context Proposal Surface/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/M39 CCC context proposal surface/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/mock and non-authoritative/i)).toBeInTheDocument();
    expect(screen.getAllByText(/proposal-only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/NO_PRODUCTION_AUTHORITY/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/Safe proposal sections/i)).toBeInTheDocument();
    expect(screen.getByText(/Redacted review excerpt/i)).toBeInTheDocument();
    expect(
      screen.getByText(
        /M39 surface displays redacted proposal text with \[REDACTED:SECRET_ASSIGNMENT\]/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/Source chain refs/i)).toBeInTheDocument();
    expect(
      screen.getAllByText("safe-context-proposal:mock_001").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("file-review-approval-capture:mock_001").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("file-review-packet:mock_001").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("redacted-file-preview-output:mock_001").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("file-review-redaction-summary:mock_001").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("file-ref:mock_review_001").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "filesystem-preview-path:safe-root_m39/docs/review-summary.md",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("user:mock_reviewer_001").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/Decision status/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/proposal_ready_for_review/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Receipt plan metadata/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/context injected: no/i)).toBeInTheDocument();
    expect(
      screen.getByText(/OpenWebUI handoff authorized: no/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/memory write authorized: no/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/export authorized: no/i)).toBeInTheDocument();
    expect(screen.getByText(/execution authorized: no/i)).toBeInTheDocument();
  });

  it("keeps M39 proposal selection read-only without handoff injection or mutation controls", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/context/proposals");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Context Proposal Surface/i }),
    ).toBeInTheDocument();
    const proposalButtons = screen.getAllByRole("button", {
      name: /view context proposal/i,
    });
    expect(proposalButtons.length).toBeGreaterThan(1);
    fireEvent.click(proposalButtons[1]);

    expect(
      screen.getAllByRole("heading", { name: "safe-context-proposal:mock_002" })
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("article", { name: /safe-context-proposal:mock_002/i }),
    ).toHaveAttribute("aria-current", "true");
    expect(
      screen.getAllByText(
        "safe-context-proposal-section:mock_002:redacted-preview",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("file-ref:mock_review_002").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "filesystem-preview-path:safe-root_m39/docs/alternate-review.md",
      ).length,
    ).toBeGreaterThan(0);

    for (const label of [
      /^approve$/i,
      /^deny$/i,
      /^submit$/i,
      /^save$/i,
      /^export$/i,
      /^download$/i,
      /copy raw/i,
      /send to openwebui/i,
      /handoff/i,
      /inject/i,
      /write memory/i,
      /^execute$/i,
      /^run$/i,
      /run tool/i,
      /call model/i,
      /open raw file/i,
      /file picker/i,
      /browse/i,
      /upload/i,
      /root selector/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw_content/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/full_file_content/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/unredacted_preview/i)).not.toBeInTheDocument();
    expect(
      screen.queryByText(new RegExp("/Users/", "i")),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/\/home\//i)).not.toBeInTheDocument();
    expect(screen.queryByText(/supersecretvalue123/i)).not.toBeInTheDocument();
    expect(
      screen.getAllByText(/Control Center output is not authority/i).length,
    ).toBeGreaterThan(0);
  });

  it("renders Memory Review as a review-only inbox with explicit memory authority blockers", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/memory");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Memory Review$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Review posture/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Missing contracts/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("/memory")).toBeInTheDocument();
    expect(
      screen.getAllByText("GET /control-center/memory/review").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "storage_backed_review_queue_with_backend_decision_receipts",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("founder-loop-storage:mock-local-sqlite-jsonl"),
    ).toBeInTheDocument();
    expect(
      screen
        .getAllByText("Memory writes")
        .some((node) =>
          node.nextElementSibling?.textContent?.match(/blocked|receipt-bound/i),
        ),
    ).toBe(true);
    expect(
      screen.getByText("Memory deletes").nextElementSibling,
    ).toHaveTextContent("disabled");
    expect(
      screen
        .getAllByText("Context injection")
        .some((node) =>
          node.nextElementSibling?.textContent?.match(/disabled|blocked/i),
        ),
    ).toBe(true);
    expect(
      screen.getByText(/Review-only memory candidates; recall is not truth/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Memory review can record safe accept, correction, reject, defer, merge, supersede, and forget-request receipts/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("memory-review:founder-loop-preferences").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("preference").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Memory Workbench V1/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Memory lifecycle posture/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("GET /control-center/memory/workbench"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("contract-ref:fcc-mem-001-memory-workbench:v1"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("contract-ref:memory-merge-supersede-posture:v1"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Duplicate review: 1 entry; merge receipt present/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Stale review: 1 entry; defer receipt present/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Conflict review: 1 entry; supersede receipt present/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Corrected: 1 entry; correction receipt present/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Merged: 1 entry; merge receipt present/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Superseded: 1 entry; supersede receipt present/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Forget request: 1 entry; forget-request receipt present/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("receipt:memory-review:merge:mock-peer").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("blocked-state:memory-lifecycle-no-hard-delete")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Ranked recall diagnostics/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "contract-ref:fcc-mem-022-ranked-retrieval-recall-tuning:v1",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Recall rank").nextElementSibling,
    ).toHaveTextContent("124");
    expect(
      screen.getByText("Lexical/tag/ref only").nextElementSibling,
    ).toHaveTextContent("yes");
    expect(
      screen.getByText("Embeddings/vector/provider").nextElementSibling,
    ).toHaveTextContent("blocked");
    expect(
      screen
        .getAllByText("Memory writes")
        .some((node) =>
          node.nextElementSibling?.textContent?.match(/blocked|receipt-bound/i),
        ),
    ).toBe(true);
    expect(
      screen.getAllByText("rank-include-ref:lexical-safe-summary-title-match")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("rank-exclusion-ref:stale-pressure").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("blocked-state:memory-ranking-no-context-injection")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Search \/ Filter/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("GET /control-center/memory/search"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Manual Candidate Intake/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Creates review queue state only/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/high \/ review_needed/i)).toBeInTheDocument();
    expect(screen.getAllByText("memory_review_queue").length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText("recheck_source_refs_before_memory_use").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("provenance-ref:manual-note:mock-preferences"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("source-ref:manual-note:founder-loop-storage").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("contract-ref:memory-write-policy-binding-missing")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("contract-ref:memory-retention-delete-missing")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByText(
        "contract-ref:business-memory-quality-controls-missing",
      ),
    ).not.toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:context-injection-missing").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("quality-state:needs-review").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("quality-state:stale").length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText("quality-reason:review-state:review-needed").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("why-shown:loop-relevance:founder-loop").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("blocked-state:manual-memory-intake-no-recall-record"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("no_memory_write").length).toBeGreaterThan(0);
    expect(screen.getAllByText("no_context_injection").length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText("no_memory_delete").length).toBeGreaterThan(0);
    expect(screen.getAllByText("no_memory_export").length).toBeGreaterThan(0);
    expect(screen.getAllByText("no_raw_source_display").length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText("no_external_crm_write").length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText("no_account_sync").length).toBeGreaterThan(0);
    expect(screen.getAllByText("no_automatic_recall").length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText("no_connector_write").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("no_model_provider_authority").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("no_background_sync").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Review provenance and evidence refs/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Review decisions/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:memory-review-decision:v1").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("contract-ref:fcc-v1-005-memory-review-decisions:v1")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("button", { name: /Record accept receipt/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Record correction receipt/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Record reject receipt/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText(/Corrected bounded safe summary/i),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText(/Corrected safe-summary ref/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Business memory/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:business-memory-quality-controls:v1")
        .length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("blocked").length).toBeGreaterThan(0);
    expect(screen.getAllByText("low_confidence").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "business-memory-candidate:preference:memory-review-founder-loop-preferences",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("weekly-review-ref:business-memory-carry-forward")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Memory intake/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:cross-surface-memory-intake:v1").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("memory-intake-proposal:local-coding").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("memory-intake-proposal:external-assistant-review")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Memory-to-loop/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:memory-to-loop-binding:v1").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "memory-loop-binding:today:business-memory-candidate-preference-memory-review-founder-loop-preferences",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "follow-up-commitment-ref:memory-review-founder-loop-preferences",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "memory-derived-action-proposal:memory-review-founder-loop-preferences",
      ).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("Local Coding").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("External Assistant Review").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("missing_safe_evidence_until_reviewed").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("recheck_source_refs_before_memory_intake").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("blocked-state:no-shell-history-import").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("blocked-state:no-raw-file-import").length,
    ).toBeGreaterThan(0);

    for (const label of [
      /^accept$/i,
      /^correct$/i,
      /^reject$/i,
      /^retain$/i,
      /^delete$/i,
      /^write$/i,
      /^inject$/i,
      /^approve$/i,
      /^merge$/i,
      /^supersede$/i,
      /^defer$/i,
      /^run$/i,
      /^sync$/i,
      /^crm sync$/i,
      /^dedupe$/i,
      /^resolve conflict$/i,
      /^mark reviewed$/i,
      /^promote to recall$/i,
      /^accept recall$/i,
      /^bind memory$/i,
      /^create follow-up$/i,
      /^create action$/i,
      /^use in context$/i,
      /^inject context$/i,
      /^resolve blocker$/i,
      /^mark accepted$/i,
      /^import$/i,
      /^quality control$/i,
      /^export$/i,
      /^save$/i,
      /learn this/i,
      /forget this/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw memory content/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw transcript/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw source/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/authoritative truth/i)).not.toBeInTheDocument();
  });

  it("records Memory quality feedback without memory writes or context injection", async () => {
    setLocalApiBearerForSession("test-local-bearer");
    const feedbackReceipt = {
      schema_version: "fcc_mem_018_memory_feedback_receipt.v1",
      contract_ref: "contract-ref:fcc-mem-018-feedback-quality-queue:v1",
      route_ref: "POST /control-center/memory/feedback",
      feedback_ref: "memory-feedback:fcc-mem-021:control-center-test",
      receipt_ref: "receipt:memory-feedback:fcc-mem-021:control-center-test",
      quality_issue_ref: "memory-quality-issue:fcc-mem-018:mock-stale",
      target_ref:
        "business-memory-candidate:preference:memory-review-founder-loop-preferences",
      target_kind: "memory_candidate",
      feedback_kind: "stale",
      reviewer_ref: "actor-ref:control-center-memory-review",
      evidence_refs: ["evidence-ref:fcc-mem-021:feedback-test"],
      reason_refs: ["reason-ref:control-center-memory-feedback:stale"],
      metadata_refs: ["memory-quality-issue:fcc-mem-018:mock-stale"],
      blocked_state_refs: [
        "blocked-state:memory-feedback-no-automatic-memory-write",
        "blocked-state:memory-feedback-no-context-injection",
      ],
      idempotency_key_ref:
        "idempotency-ref:control-center-memory-feedback:stale:test",
      payload_fingerprint_ref:
        "payload-fingerprint-ref:control-center-memory-feedback:test",
      status: "feedback_recorded",
      quality_issue_created: true,
      memory_write_performed: false,
      automatic_memory_write_authorized: false,
      delete_execution_authorized: false,
      context_injection_authorized: false,
      action_execution_authorized: false,
      production_authority_enabled: false,
      replayed: false,
      created_at: "2026-06-23T00:00:00Z",
    };
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      expect(String(url)).toContain(API_ENDPOINTS.founderMemoryFeedback);
      expect(String(options?.method)).toBe("POST");
      expect(
        String((options?.headers as Record<string, string>)["X-UAA-Idempotency-Key"]),
      ).toContain("idempotency-ref:control-center-memory-feedback");
      return new Response(
        JSON.stringify({ ok: true, result: feedbackReceipt }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    const receipt = await recordMemoryFeedback({
      target_ref:
        "business-memory-candidate:preference:memory-review-founder-loop-preferences",
      target_kind: "memory_candidate",
      feedback_kind: "stale",
      reviewer_ref: "actor-ref:control-center-memory-review",
      evidence_refs: ["evidence-ref:fcc-mem-021:feedback-test"],
      reason_refs: ["reason-ref:control-center-memory-feedback:stale"],
      metadata_refs: ["memory-quality-issue:fcc-mem-018:mock-stale"],
      blocked_state_refs: [
        "blocked-state:memory-feedback-no-automatic-memory-write",
        "blocked-state:memory-feedback-no-context-injection",
      ],
    });

    expect(receipt.receipt_ref).toBe(feedbackReceipt.receipt_ref);
    expect(receipt.memory_write_performed).toBe(false);
    expect(receipt.context_injection_authorized).toBe(false);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    setLocalApiBearerForSession(null);
  });

  it("renders memory self-heal recommendations as proposal-only Action Inbox items", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/actions");
    render(<App />);

    expect(
      await screen.findByText("Review memory quality and maintenance refs"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("memory-proposal-bridge-ref:fcc-mem-021-action-inbox")
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(
        /Memory proposal receipt controls require the local backend Action Inbox/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("GET /control-center/memory/quality-issues").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("GET /control-center/memory/maintenance-runs").length,
    ).toBeGreaterThan(0);
    const maintenanceRunLabel = new RegExp(["Run", "maintenance"].join(" "), "i");
    expect(
      screen.queryByRole("button", { name: maintenanceRunLabel }),
    ).not.toBeInTheDocument();
  });

  it("records a Memory Review decision receipt with safe refs only", async () => {
    const candidateRef =
      "business-memory-candidate:preference:memory-review-founder-loop-preferences";
    const receipt = {
      contract_ref: "contract-ref:fcc-v1-005-memory-review-decisions:v1",
      candidate_ref: candidateRef,
      review_ref: "memory-review:founder-loop-preferences",
      decision: "accept",
      corrected_summary_ref: null,
      corrected_safe_summary: null,
      source_refs: ["source-ref:manual-note:founder-loop-storage"],
      evidence_refs: ["evidence-ref:founder-loop:mock-memory"],
      reviewer_ref: "actor-ref:control-center-memory-review",
      receipt_ref: "receipt:memory-review:accept:control-center-test",
      decision_ref: "memory-review-decision:accept:control-center-test",
      audit_ref: "audit-ref:memory-review:accept:control-center-test",
      idempotency_key_ref:
        "idempotency-ref:control-center-memory-review:accept:test",
      payload_fingerprint_ref:
        "payload-fingerprint:memory-review-decision:test",
      evidence_timeline_event_ref:
        "evidence-ref:memory-review:accept:control-center-test",
      approval_ref: "approval-ref:memory-review:accept:control-center-test",
      approval_status: "approved",
      approval_reason_refs: ["approval-reason:approval-validated"],
      reviewed_recall_ref:
        "reviewed-recall-ref:memory-review:control-center-test",
      reviewed_recall_record_ref: "memory-record-ref:mem_control_center_test",
      correction_ref: null,
      rejection_ref: null,
      defer_ref: null,
      merge_ref: null,
      supersede_ref: null,
      forget_request_ref: null,
      merge_refs: [],
      supersedes_refs: [],
      suppressed_recall_record_refs: [],
      safe_summary_ref: "safe-summary-ref:memory-review:accept",
      blocked_state_refs: ["blocked-state:no-context-injection"],
      authority_boundary:
        "Memory Review decisions create backend-owned safe receipts; accept/correct may create recall-only local records.",
      context_injection_authorized: false,
      connector_write_authorized: false,
      external_crm_sync_authorized: false,
      account_sync_authorized: false,
      automatic_action_execution_authorized: false,
      model_provider_authority_allowed: false,
      source_truth_authority: false,
      memory_truth_authority: false,
      production_authority_enabled: false,
      replayed: false,
      created_at: "2026-06-22T00:00:00Z",
    };
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      const urlText = String(url);
      if (
        !options?.method &&
        READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))
      ) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (
        options?.method === "POST" &&
        urlText.endsWith(memoryReviewDecisionEndpoint(candidateRef, "accept"))
      ) {
        return new Response(JSON.stringify({ ok: true, result: receipt }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/memory");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Memory Review$/i }),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: /Record accept receipt/i }),
    );

    await screen.findByText("receipt:memory-review:accept:control-center-test");
    expect(
      screen.getByText("memory-record-ref:mem_control_center_test"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("audit-ref:memory-review:accept:control-center-test"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("evidence-ref:memory-review:accept:control-center-test"),
    ).toBeInTheDocument();
    expect(
      screen
        .getAllByText("Context injection")
        .some((node) =>
          node.nextElementSibling?.textContent?.includes("blocked"),
        ),
    ).toBe(true);
    const [, options] =
      fetchMock.mock.calls.find(
        ([url, requestOptions]) =>
          requestOptions?.method === "POST" &&
          String(url).endsWith(
            memoryReviewDecisionEndpoint(candidateRef, "accept"),
          ),
      ) ?? [];
    expect(options?.headers).toMatchObject({
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-UAA-Idempotency-Key": expect.stringMatching(
        /^idempotency-ref:control-center-memory-review:accept:/,
      ),
    });
    const bodyText = String(options?.body);
    const body = JSON.parse(bodyText);
    expect(body).toMatchObject({
      reviewer_ref: "actor-ref:control-center-memory-review",
      source_refs: ["source-ref:manual-note:founder-loop-storage"],
      evidence_refs: ["evidence-ref:founder-loop:mock-memory"],
    });
    expect(body.corrected_summary_ref).toBeUndefined();
    expect(bodyText).not.toContain("raw");
    expect(bodyText).not.toContain("prompt");
    expect(bodyText).not.toContain("response");
    expect(bodyText).not.toContain("provider_payload");
  });

  it("does not backfill lifecycle posture or decisions from mocks for partial backend workbench responses", async () => {
    const partialWorkbench = {
      ...mockControlCenterData.founderMemoryWorkbench,
      items: mockControlCenterData.founderMemoryWorkbench.items.map((item) => {
        const { available_lifecycle_decisions: _available, ...rest } = item;
        return rest;
      }),
    };
    delete (partialWorkbench as { lifecycle_posture?: unknown })
      .lifecycle_posture;
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderMemoryWorkbench)) {
        return new Response(
          JSON.stringify({ ok: true, result: partialWorkbench }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/memory");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Memory Review$/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("backend posture missing")).toBeInTheDocument();
    expect(
      screen.queryByText("contract-ref:memory-merge-supersede-posture:v1"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("receipt:memory-review:merge:mock-peer"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Record accept receipt/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Record merge receipt/i }),
    ).not.toBeInTheDocument();
  });

  it("does not backfill nested lifecycle posture fields from mocks", async () => {
    cleanup();
    const partialWorkbench = {
      ...mockControlCenterData.founderMemoryWorkbench,
      lifecycle_posture: {
        schema_version: "product-loop-002-memory-merge-supersede-posture.v1",
        contract_ref: "contract-ref:memory-merge-supersede-posture:v1",
        status: "partial_backend_contract_missing_lanes",
      },
    };
    const fetchMock = vi.fn(async (url: string) => {
      const urlText = String(url);
      if (urlText.endsWith(API_ENDPOINTS.founderMemoryWorkbench)) {
        return new Response(
          JSON.stringify({ ok: true, result: partialWorkbench }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }
      if (READ_ENDPOINTS.some((endpoint) => urlText.endsWith(endpoint))) {
        return new Response(JSON.stringify(envelopeForReadEndpoint(urlText)), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/memory");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Memory Review$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("partial_backend_contract_missing_lanes"),
    ).toBeInTheDocument();
    expect(screen.getByText("Lifecycle lanes: none")).toBeInTheDocument();
    expect(
      screen.queryByText(/Duplicate review: 1 entry; merge receipt present/i),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("receipt:memory-review:merge:mock-peer"),
    ).not.toBeInTheDocument();
  });

  it("attaches a non-persistent local bearer to memory read and write helpers", async () => {
    const candidateRef = "memory-candidate:auth-header-test";
    const localBearer = "control-center-local-bearer-test";
    const receipt = {
      contract_ref: "contract-ref:memory-review-decision:v1",
      candidate_ref: candidateRef,
      review_ref: "memory-review:auth-header-test",
      decision: "accept",
      corrected_summary_ref: null,
      corrected_safe_summary: null,
      reviewed_recall_record_ref: "memory-record-ref:auth-header-test",
      source_refs: ["source-ref:auth-header-test"],
      evidence_refs: ["evidence-ref:auth-header-test"],
      reviewer_ref: "actor-ref:control-center-memory-review",
      receipt_ref: "receipt:memory-review:auth-header-test",
      decision_ref: "memory-review-decision:auth-header-test",
      audit_ref: "audit-ref:memory-review:auth-header-test",
      idempotency_key_ref: "idempotency-ref:memory-review:auth-header-test",
      payload_fingerprint_ref:
        "payload-fingerprint:memory-review:auth-header-test",
      evidence_timeline_event_ref:
        "evidence-timeline-event:memory-review:auth-header-test",
      approval_ref: "approval-ref:memory-review:auth-header-test",
      approval_status: "approved",
      approval_reason_refs: ["approval-reason:approval-validated"],
      safe_summary_ref: "safe-summary-ref:memory-review:accept",
      reviewed_recall_ref: "reviewed-recall-ref:memory-review:auth-header-test",
      correction_ref: null,
      rejection_ref: null,
      defer_ref: null,
      merge_ref: null,
      supersede_ref: null,
      forget_request_ref: null,
      merge_refs: [],
      supersedes_refs: [],
      suppressed_recall_record_refs: [],
      authority_boundary:
        "Memory Review decisions create backend-owned safe receipts; accept/correct may create recall-only local records.",
      context_injection_authorized: false,
      source_truth_authority: false,
      memory_truth_authority: false,
      connector_write_performed: false,
      crm_sync_performed: false,
      account_sync_performed: false,
      action_execution_performed: false,
      production_authority_enabled: false,
      blocked_state_refs: ["blocked-state:no-context-injection"],
      replayed: false,
      created_at: "2026-06-22T00:00:00Z",
    };
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      const urlText = String(url);
      if (urlText.endsWith(memoryReviewReceiptEndpoint(candidateRef))) {
        return new Response(JSON.stringify({ ok: true, result: receipt }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (
        options?.method === "POST" &&
        urlText.endsWith(memoryReviewDecisionEndpoint(candidateRef, "accept"))
      ) {
        return new Response(JSON.stringify({ ok: true, result: receipt }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected request ${urlText}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    setLocalApiBearerForSession(localBearer);

    await fetchMemoryReviewDecisionReceipt(candidateRef);
    await recordMemoryReviewDecision(candidateRef, "accept", {
      reviewer_ref: "actor-ref:control-center-memory-review",
      source_refs: ["source-ref:auth-header-test"],
      evidence_refs: ["evidence-ref:auth-header-test"],
    });

    const getCall = fetchMock.mock.calls.find(
      ([url, options]) =>
        String(url).endsWith(memoryReviewReceiptEndpoint(candidateRef)) &&
        !options?.method,
    );
    const postCall = fetchMock.mock.calls.find(
      ([url, options]) =>
        String(url).endsWith(
          memoryReviewDecisionEndpoint(candidateRef, "accept"),
        ) && options?.method === "POST",
    );
    expect(getCall?.[1]?.headers).toMatchObject({
      Authorization: `Bearer ${localBearer}`,
    });
    expect(postCall?.[1]?.headers).toMatchObject({
      Authorization: `Bearer ${localBearer}`,
      "X-UAA-Idempotency-Key": expect.stringMatching(
        /^idempotency-ref:control-center-memory-review:accept:/,
      ),
    });
    expect(String(postCall?.[1]?.body)).not.toContain(localBearer);
    setLocalApiBearerForSession(null);
  });

  it("keeps alternate M17 metadata selection read-only and redacted", async () => {
    for (const route of ["/evidence", "/files"]) {
      cleanup();
      mockFetchWithFallback();
      window.history.pushState({}, "", route);
      render(<App />);

      await waitFor(() => {
        expect(
          screen.getAllByRole("button", { name: /view metadata/i }).length,
        ).toBeGreaterThan(1);
      });
      const metadataButtons = screen.getAllByRole("button", {
        name: /view metadata/i,
      });
      fireEvent.click(metadataButtons[1]);

      const expectedRef =
        route === "/evidence" ? "mock_evidence_ref_002" : "mock_file_ref_002";
      expect(
        screen.getAllByRole("heading", { name: expectedRef }).length,
      ).toBeGreaterThan(0);
      expect(
        screen.getByRole("article", { name: new RegExp(expectedRef, "i") }),
      ).toHaveAttribute("aria-current", "true");
      expect(
        screen.getAllByText(/redacted_summary_only/i).length,
      ).toBeGreaterThan(0);
      expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);

      for (const label of [
        /^execute$/i,
        /^run$/i,
        /write file/i,
        /delete file/i,
        /browse filesystem/i,
        /edit memory/i,
        /delete memory/i,
        /reveal raw/i,
        /show raw/i,
      ]) {
        expect(
          screen.queryByRole("button", { name: label }),
        ).not.toBeInTheDocument();
      }
      expect(
        screen.queryByText(/raw evidence payload/i),
      ).not.toBeInTheDocument();
      expect(screen.queryByText(/raw file content/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/raw memory content/i)).not.toBeInTheDocument();
      expect(
        screen.queryByText(new RegExp("/Users/", "i")),
      ).not.toBeInTheDocument();
      expect(screen.queryByText(/\/home\//i)).not.toBeInTheDocument();
    }
    expect(mockControlCenterData.m17Knowledge.memories[1].memoryRef).toBe(
      "mock_memory_ref_002",
    );
  });

  it("renders M18 local runtime status as read-only validation-only metadata", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/runtime/local");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Local Runtime Status/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/M18 local runtime surface/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Local runtime status is read-only/i),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Runtime readiness report/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/manual_loopback_smoke/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/NO_RUNTIME_EXECUTION/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getByText(
        /No local runtime is started, stopped, connected, or executed from this UI/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Model output remains non-authoritative/i),
    ).toBeInTheDocument();

    for (const label of [
      /^execute$/i,
      /^run$/i,
      /^start$/i,
      /^stop$/i,
      /^connect$/i,
      /^launch$/i,
      /^call model$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw response/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/provider payload/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/supersecretvalue123/i)).not.toBeInTheDocument();
  });

  it("renders M18 manual smoke report handling without execution or raw report display", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/runtime/manual-smoke");
    render(<App />);

    expect(
      await screen.findByRole("heading", {
        name: /Manual Smoke Control Surface/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/validation-only report surface/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Manual smoke reports are safe summaries/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/mock_manual_smoke_report_ref_001/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/fixed prompt hash/i)).toBeInTheDocument();
    expect(screen.getByText(/response preview shown: no/i)).toBeInTheDocument();
    expect(
      screen.getByText(
        /Manual smoke execution remains CLI-only, fixed-prompt-only, approval-gated/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/REDACTED_SUMMARY_ONLY/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/VALIDATION_ONLY/i).length).toBeGreaterThan(0);

    for (const label of [
      /^execute$/i,
      /^run$/i,
      /^start$/i,
      /^stop$/i,
      /^connect$/i,
      /^launch$/i,
      /^send$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw response body/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw transcript/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/api_key/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/token=/i)).not.toBeInTheDocument();
  });

  it("submits action preview only to the preview endpoint", async () => {
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      if (options?.method === "POST") {
        return new Response(
          JSON.stringify({
            ok: true,
            result: {
              decision_id: "decision_mock",
              request_id: "frontend_preview_request",
              allowed: true,
              status: "allowed_preview",
              reason_codes: ["CONTROL_CENTER_PREVIEW_ALLOWED"],
              safe_message:
                "Control Center preview is allowed. No action was executed.",
              preview_summary: "Preview only; no action was executed.",
              metadata: { executed: false },
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      throw new Error("backend unavailable");
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/action-preview");
    render(<App />);

    expect(
      await screen.findByText(/Preview only action request/i),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/Risk level/i)).toBeInTheDocument();
    expect(
      screen.getByText(
        /High and critical previews remain non-execution decisions/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /Blocked execution action/i }),
    ).toBeDisabled();
    fireEvent.click(
      await screen.findByRole("button", { name: /preview action/i }),
    );

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        API_ENDPOINTS.actionPreview,
        expect.any(Object),
      ),
    );
    const [, options] =
      fetchMock.mock.calls.find((call) => call[1]?.method === "POST") ?? [];
    expect(options?.method).toBe("POST");
    expect(
      screen.queryByRole("button", { name: /execute/i }),
    ).not.toBeInTheDocument();
  });

  it("shows live local backend connection state only when every read request succeeds", async () => {
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      if (options?.method === "POST") {
        throw new Error("unexpected preview request");
      }
      return new Response(
        JSON.stringify(envelopeForReadEndpoint(String(url))),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/dashboard");
    render(<App />);

    expect(await screen.findByText("Backend online")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Live data came from local read, preview, and exact receipt backend routes/i,
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Mock fallback active/i)).not.toBeInTheDocument();
  });

  it("renders setup assistant summary from the local backend when available", async () => {
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      if (options?.method === "POST") {
        throw new Error("unexpected preview request");
      }
      return new Response(
        JSON.stringify(envelopeForReadEndpoint(String(url))),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/setup");
    render(<App />);

    expect(await screen.findByText("Backend online")).toBeInTheDocument();
    expect(screen.getByText("Backend API setup timeline")).toBeInTheDocument();
    expect(
      screen.getByText("control-center:setup-assistant-api-test"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("macos-setup-approval-envelope:api-summary").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("idempotency-ref:macos-setup-api-summary").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("First-run proof spine")).toBeInTheDocument();
    expect(screen.getByText("Local package proof")).toBeInTheDocument();
    expect(screen.getByText("Exact promotion path")).toBeInTheDocument();
    expect(
      screen.getByText("packaging-proof:local-macos-app-bundle"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("loop-ref:setup-to-daily-loop:v1"),
    ).toBeInTheDocument();
  });

  it("shows degraded local backend state when only part of the read set succeeds", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (String(url).includes(API_ENDPOINTS.runtimeCapabilityMatrix)) {
        throw new Error("capability matrix unavailable");
      }
      return new Response(
        JSON.stringify(envelopeForReadEndpoint(String(url))),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/dashboard");
    render(<App />);

    expect(await screen.findByText("Backend degraded")).toBeInTheDocument();
    expect(
      screen.getByText(/Some local backend summaries were unavailable/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /non-authoritative mock fallback filled missing panels/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Backend degraded; verify refs/i),
    ).toBeInTheDocument();
    expect(screen.getByText("API boundary unverified")).toBeInTheDocument();
    expect(screen.getByText("Evidence refs unverified")).toBeInTheDocument();
    expect(screen.queryByText("API boundary stable")).not.toBeInTheDocument();
    expect(screen.queryByText("Evidence healthy")).not.toBeInTheDocument();
  });

  it("does not expose dangerous action control labels", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/action-preview");
    render(<App />);

    await screen.findByText(/Preview only action request/i);

    for (const label of [
      /execute/i,
      /^run$/i,
      /send/i,
      /deploy/i,
      /enable/i,
      /approve/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
  });

  it("renders unsafe preview decisions as blocked without claiming execution", async () => {
    const fetchMock = vi.fn(async (_url: string, options?: RequestInit) => {
      const body = JSON.parse(String(options?.body ?? "{}")) as {
        target_ref?: string;
      };
      const reason = body.target_ref?.includes("remote-workers")
        ? "REMOTE_EXECUTION_BLOCKED"
        : body.target_ref?.includes("plugins")
          ? "PLUGIN_ENABLEMENT_BLOCKED"
          : body.target_ref?.includes("mobile")
            ? "MOBILE_SENSOR_BLOCKED"
            : "CONTROL_CENTER_PREVIEW_ALLOWED";
      return new Response(
        JSON.stringify({
          ok: reason === "CONTROL_CENTER_PREVIEW_ALLOWED",
          result: {
            decision_id: "decision_mock",
            request_id: "frontend_preview_request",
            allowed: false,
            status: "blocked",
            reason_codes: [reason],
            safe_message:
              "Control Center preview was blocked by read-only policy.",
            preview_summary: "Preview only; no action was executed.",
            metadata: { executed: false },
          },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/action-preview");
    render(<App />);

    fireEvent.change(await screen.findByLabelText(/Target reference/i), {
      target: { value: "remote-workers/dispatch/job" },
    });
    fireEvent.click(screen.getByRole("button", { name: /preview action/i }));

    expect((await screen.findAllByText("blocked")).length).toBeGreaterThan(0);
    expect(screen.getByText(/REMOTE_EXECUTION_BLOCKED/i)).toBeInTheDocument();
    expect(screen.getByText(/no action was executed/i)).toBeInTheDocument();
  });

  it("redacts secret-like input before user-visible output", async () => {
    vi.stubGlobal("fetch", vi.fn());
    window.history.pushState({}, "", "/action-preview");
    render(<App />);

    fireEvent.change(await screen.findByLabelText(/Purpose/i), {
      target: { value: "token=supersecretvalue123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /preview action/i }));

    expect(
      await screen.findByText(/Secret-like input was redacted/i),
    ).toBeInTheDocument();
    expect(screen.queryByText(/supersecretvalue123/i)).not.toBeInTheDocument();
  });

  it("redacts secret-like backend preview errors before display", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              ok: false,
              error: {
                code: "SAFE_REJECTION",
                message:
                  "Preview rejected because token=supersecretvalue123 was invalid.",
              },
            }),
            { status: 400, headers: { "Content-Type": "application/json" } },
          ),
      ),
    );
    window.history.pushState({}, "", "/action-preview");
    render(<App />);

    fireEvent.click(
      await screen.findByRole("button", { name: /preview action/i }),
    );

    expect(
      await screen.findByText(
        /Preview rejected because \[redacted\] was invalid/i,
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/supersecretvalue123/i)).not.toBeInTheDocument();
  });

  it("keeps read endpoints separate from the single preview POST endpoint", () => {
    expect(READ_ENDPOINTS).not.toContain(API_ENDPOINTS.actionPreview);
    expect(READ_ENDPOINTS).not.toContain(
      API_ENDPOINTS.founderTodayActionEnvelope,
    );
    expect(READ_ENDPOINTS).not.toContain(
      API_ENDPOINTS.runtimeSmokeReportValidate,
    );
    expect(READ_ENDPOINTS).not.toContain(API_ENDPOINTS.controlCenterChatTurns);
    expect(API_ENDPOINTS.actionPreview).toBe("/control-center/actions/preview");
    expect(API_ENDPOINTS.controlCenterChatTurns).toBe(
      "/control-center/chat/turns",
    );
    expect(API_ENDPOINTS.founderMemoryContextPacks).toBe(
      "/control-center/memory/context-packs",
    );
    expect(API_ENDPOINTS.founderMemoryRetrievalDiagnostics).toBe(
      "/control-center/memory/retrieval-diagnostics",
    );
    expect(API_ENDPOINTS.founderMemoryContextManifest).toBe(
      "/control-center/memory/context-manifest",
    );
    expect(`GET ${API_ENDPOINTS.founderMemoryRetrievalDiagnostics}`).toBe(
      "GET /control-center/memory/retrieval-diagnostics",
    );
    expect(`GET ${API_ENDPOINTS.founderMemoryContextManifest}`).toBe(
      "GET /control-center/memory/context-manifest",
    );
    expect(isAllowedReadEndpoint(API_ENDPOINTS.founderMemoryContextPacks)).toBe(
      true,
    );
    expect(
      isAllowedReadEndpoint(API_ENDPOINTS.founderMemoryRetrievalDiagnostics),
    ).toBe(true);
    expect(
      isAllowedReadEndpoint(API_ENDPOINTS.founderMemoryContextManifest),
    ).toBe(true);
    expect(isAllowedReadEndpoint(API_ENDPOINTS.founderStartHereSummary)).toBe(
      true,
    );
    expect(isAllowedReadEndpoint(API_ENDPOINTS.controlCenterProofIndex)).toBe(
      true,
    );
    expect(isAllowedReadEndpoint(API_ENDPOINTS.trustAuthorityMatrix)).toBe(
      true,
    );
    expect(chatTurnReceiptEndpoint("chat-turn:test")).toBe(
      "/control-center/chat/turns/chat-turn%3Atest/receipt",
    );
    expect(chatTurnHandoffEndpoint("chat-turn:test")).toBe(
      "/control-center/chat/turns/chat-turn%3Atest/handoff",
    );
    expect(API_ENDPOINTS.runtimeSmokeReportValidate).toBe(
      "/runtime/smoke-reports/validate",
    );
    expect(isPreviewEndpoint(API_ENDPOINTS.actionPreview)).toBe(true);
    expect(isAllowedReadEndpoint(API_ENDPOINTS.controlCenterDashboard)).toBe(
      true,
    );
    expect(isAllowedReadEndpoint(API_ENDPOINTS.founderTodaySummary)).toBe(true);
    expect(isAllowedReadEndpoint(API_ENDPOINTS.founderActionsInbox)).toBe(true);
    expect(isAllowedReadEndpoint(API_ENDPOINTS.founderMorningBriefing)).toBe(
      true,
    );
    expect(isAllowedReadEndpoint(API_ENDPOINTS.founderSourceReadiness)).toBe(
      true,
    );
    expect(isAllowedReadEndpoint(API_ENDPOINTS.founderStorageStatus)).toBe(
      true,
    );
    expect(
      isAllowedReadEndpoint(API_ENDPOINTS.controlCenterSettingsStatus),
    ).toBe(true);
    expect(
      isAllowedReadEndpoint(API_ENDPOINTS.controlCenterLocalModelsStatus),
    ).toBe(true);
    expect(isAllowedReadEndpoint(API_ENDPOINTS.runObservability)).toBe(true);
    expect(isAllowedReadEndpoint(API_ENDPOINTS.providerSetupGuide)).toBe(true);
    expect(isAllowedReadEndpoint("/control-center/actions/execute")).toBe(
      false,
    );
    expect(isPreviewEndpoint("/control-center/plugins/enable")).toBe(false);
  });
});

function backendOwnedTrustAuthorityMatrix() {
  return {
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
}

type TrustFixtureLane = {
  lane_ref: string;
  label: string;
  tier: number;
  tier_id: string;
  tier_label: string;
  lane_kind: string;
  authority_state: string;
  authority_state_label: string;
  operator_posture: string;
  current_posture: string;
  approval_posture: string;
  operator_can_do_now: string;
  next_safe_action: string;
  route_refs: string[];
  proof_refs: string[];
  verifier_refs: string[];
  docs_refs: string[];
  cli_inspection_refs: string[];
  safe_disable_refs: string[];
  rollback_refs: string[];
  promotion_path_refs: string[];
  blocked_authority_refs: string[];
  requires_exact_approval: boolean;
  requires_safe_disable: boolean;
  requires_rollback_posture: boolean;
  rollback_execution_enabled: boolean;
  safe_refs_only: boolean;
  control_center_grants_authority: boolean;
};

function betaTrustAuthorityMatrix(overrides: Record<string, unknown> = {}) {
  const lanes: TrustFixtureLane[] = [
    trustFixtureLane({
      lane_ref: "trust-lane:today-loop-read",
      label: "Today daily loop",
      tier: 1,
      tier_id: "tier_1_local_read_preview",
      tier_label: "Local read/preview",
      lane_kind: "read_preview",
      authority_state: "available_now",
      authority_state_label: "available now",
      operator_posture: "enabled_read_only",
      route_refs: ["GET /control-center/today/summary"],
      proof_refs: ["proof-ref:founder-loop-v1:governed-local-loop"],
      cli_inspection_refs: [
        "python scripts/dev/uaa_founder_loop.py inspect-trust-authority",
        "python scripts/dev/uaa_founder_loop.py inspect",
      ],
    }),
    trustFixtureLane({
      lane_ref: "trust-lane:provider-draft-summarize",
      label: "Provider draft/summarize",
      tier: 2,
      tier_id: "tier_2_local_draft_proposal",
      tier_label: "Local draft/proposal",
      lane_kind: "draft_proposal",
      authority_state: "available_now",
      authority_state_label: "available now",
      operator_posture: "review_only",
      route_refs: ["provider-draft-summarize-lane:exact-approved:v1"],
      proof_refs: ["proof-ref:provider-draft-summarize:exact"],
      cli_inspection_refs: [
        "python scripts/dev/uaa_founder_loop.py inspect-trust-authority",
        "python scripts/inspect_provider_draft_summarize_lane.py",
      ],
      safe_disable_refs: [
        "safe-disable-ref:provider-draft-summarize:disable-exact-lane",
      ],
      rollback_refs: [
        "rollback-ref:provider-draft-summarize:discard-local-draft",
      ],
      promotion_path_refs: [
        "promotion-path-ref:trust:provider-draft-summarize:live-provider-separate-contract",
      ],
      blocked_authority_refs: [
        "blocked-state:trust:no-provider-model-call",
      ],
    }),
    trustFixtureLane({
      lane_ref: "trust-lane:connector-draft-only",
      label: "Connector draft-only",
      tier: 2,
      tier_id: "tier_2_local_draft_proposal",
      tier_label: "Local draft/proposal",
      lane_kind: "draft_proposal",
      authority_state: "available_now",
      authority_state_label: "available now",
      operator_posture: "review_only",
      route_refs: ["GET /control-center/sources/readiness#connector_draft_proposals"],
      proof_refs: ["proof-ref:connector-draft-only-proposals:v1"],
      cli_inspection_refs: [
        "python scripts/dev/uaa_founder_loop.py inspect-trust-authority",
        "python scripts/inspect_connector_draft_proposals.py",
      ],
      safe_disable_refs: [
        "safe-disable-ref:connector-draft-only:disable-local-draft-surface",
      ],
      rollback_refs: ["rollback-ref:connector-draft-only:discard-local-draft"],
      promotion_path_refs: [
        "promotion-path-ref:trust:connector-draft-only:test-send-separate-contract",
      ],
      blocked_authority_refs: ["blocked-state:trust:no-connector-send"],
    }),
    trustFixtureLane({
      lane_ref: "trust-lane:local-task-commit",
      label: "Exact local task commit",
      tier: 3,
      tier_id: "tier_3_reversible_local_mutation",
      tier_label: "Reversible local mutation",
      lane_kind: "reversible_local_mutation",
      authority_state: "approval_required",
      authority_state_label: "approval required",
      operator_posture: "approval_required",
      route_refs: [
        "POST /control-center/actions/{action_id}/local-task/commit",
      ],
      proof_refs: [dogfoodRefs.localTaskProofRef],
      cli_inspection_refs: [
        "python scripts/dev/uaa_founder_loop.py inspect-trust-authority",
        "python scripts/dev/uaa_founder_loop.py inspect-action-work-queue",
      ],
      safe_disable_refs: ["safe-disable:founder-loop:local-task-create-scorecard"],
      rollback_refs: ["rollback-not-applicable:local-task-safe-disable"],
      promotion_path_refs: [
        "promotion-path-ref:trust:local-task-commit:additional-local-lanes",
      ],
      blocked_authority_refs: [
        "blocked-state:local-task-commit:no-external-side-effects",
      ],
      requires_exact_approval: true,
      requires_safe_disable: true,
      requires_rollback_posture: true,
    }),
    trustFixtureLane({
      lane_ref: "trust-lane:external-mutations",
      label: "External sends/writes and broad runtime actions",
      tier: 4,
      tier_id: "tier_4_external_mutation",
      tier_label: "External mutation",
      lane_kind: "external_mutation",
      authority_state: "blocked",
      authority_state_label: "blocked",
      operator_posture: "blocked",
      proof_refs: ["proof-ref:external-mutation:blocked"],
      safe_disable_refs: [
        "safe-disable-ref:trust:external-mutations:default-deny",
      ],
      rollback_refs: [
        "rollback-ref:trust:external-mutations:future-lane-required",
      ],
      promotion_path_refs: [
        "promotion-path-ref:trust:external-mutations:connector-write-send",
      ],
      blocked_authority_refs: [
        "blocked-state:trust:no-connector-write-send",
        "blocked-state:trust:no-shell-subprocess-execution",
      ],
      requires_exact_approval: true,
      requires_safe_disable: true,
      requires_rollback_posture: true,
    }),
  ];
  return {
    ...mockControlCenterData.trustAuthorityMatrix,
    status: "implemented_backend_owned_trust_authority_matrix",
    backend_owned: true,
    operator_summary:
      "Backend-owned Trust fixture shows enabled, review-only, approval-required, and blocked lanes.",
    lanes,
    tier_summaries: trustTierSummaries(lanes),
    available_now_lane_refs: lanes
      .filter((lane) => lane.authority_state === "available_now")
      .map((lane) => lane.lane_ref),
    approval_required_lane_refs: lanes
      .filter((lane) => lane.authority_state === "approval_required")
      .map((lane) => lane.lane_ref),
    planned_lane_refs: lanes
      .filter((lane) => lane.authority_state === "planned")
      .map((lane) => lane.lane_ref),
    blocked_lane_refs: lanes
      .filter((lane) => lane.authority_state === "blocked")
      .map((lane) => lane.lane_ref),
    route_refs: trustLaneUnion(lanes, "route_refs"),
    proof_refs: trustLaneUnion(lanes, "proof_refs"),
    verifier_refs: trustLaneUnion(lanes, "verifier_refs"),
    docs_refs: trustLaneUnion(lanes, "docs_refs"),
    cli_inspection_refs: trustLaneUnion(lanes, "cli_inspection_refs"),
    safe_disable_refs: trustLaneUnion(lanes, "safe_disable_refs"),
    rollback_refs: trustLaneUnion(lanes, "rollback_refs"),
    promotion_path_refs: trustLaneUnion(lanes, "promotion_path_refs"),
    blocked_authority_refs: trustLaneUnion(lanes, "blocked_authority_refs"),
    ...overrides,
  };
}

function trustFixtureLane(
  overrides: Partial<TrustFixtureLane>,
): TrustFixtureLane {
  return {
    lane_ref: "trust-lane:test",
    label: "Trust test lane",
    tier: 1,
    tier_id: "tier_1_local_read_preview",
    tier_label: "Local read/preview",
    lane_kind: "read_preview",
    authority_state: "available_now",
    authority_state_label: "available now",
    operator_posture: "enabled_read_only",
    current_posture: "Backend-owned Trust lane posture.",
    approval_posture: "No approval required for read-only inspection.",
    operator_can_do_now: "Inspect backend-owned Trust refs.",
    next_safe_action: "Inspect proof and verifier refs.",
    route_refs: [],
    proof_refs: [],
    verifier_refs: ["tests/test_trust_authority_matrix.py"],
    docs_refs: ["docs/control_center/USABLE_AUTHORITY_GRADUATION_PLAN.md"],
    cli_inspection_refs: [
      "python scripts/dev/uaa_founder_loop.py inspect-trust-authority",
    ],
    safe_disable_refs: ["safe-disable-ref:trust:test:read-model-only"],
    rollback_refs: ["rollback-ref:trust:test:no-mutation"],
    promotion_path_refs: ["promotion-path-ref:trust:test:exact-scope-required"],
    blocked_authority_refs: [],
    requires_exact_approval: false,
    requires_safe_disable: false,
    requires_rollback_posture: false,
    rollback_execution_enabled: false,
    safe_refs_only: true,
    control_center_grants_authority: false,
    ...overrides,
  };
}

function trustLaneUnion(lanes: TrustFixtureLane[], field: keyof TrustFixtureLane) {
  return Array.from(
    new Set(lanes.flatMap((lane) => lane[field] as string[])),
  );
}

function trustTierSummaries(lanes: TrustFixtureLane[]) {
  return [0, 1, 2, 3, 4, 5].map((tier) => {
    const tierLanes = lanes.filter((lane) => lane.tier === tier);
    const tierMeta = {
      0: ["tier_0_ui_ephemeral_state", "UI/ephemeral state"],
      1: ["tier_1_local_read_preview", "Local read/preview"],
      2: ["tier_2_local_draft_proposal", "Local draft/proposal"],
      3: ["tier_3_reversible_local_mutation", "Reversible local mutation"],
      4: ["tier_4_external_mutation", "External mutation"],
      5: ["tier_5_background_standing_authority", "Background/standing authority"],
    }[tier] as [string, string];
    return {
      tier,
      tier_id: tierMeta[0],
      label: tierMeta[1],
      available_now_count: tierLanes.filter(
        (lane) => lane.authority_state === "available_now",
      ).length,
      approval_required_count: tierLanes.filter(
        (lane) => lane.authority_state === "approval_required",
      ).length,
      planned_count: tierLanes.filter((lane) => lane.authority_state === "planned")
        .length,
      blocked_count: tierLanes.filter((lane) => lane.authority_state === "blocked")
        .length,
      operator_summary: `${tierMeta[1]} Trust fixture summary.`,
    };
  });
}

const dogfoodRefs = {
  actionRef: "founder-action:local-task-create-scorecard",
  actionEnvelopeRef: "action-envelope:plans:founder-action-local-task-create-scorecard",
  approvalRef:
    "approval-ref:founder-loop-action:founder-action-local-task-create-scorecard:idempotency-ref-dogfood-live-loop-local-task-approval",
  decisionReceiptRef:
    "receipt:founder-loop-action:founder-action-local-task-create-scorecard:approve:idempotency-ref-dogfood-live-loop-local-task-approval",
  evidenceRef: "evidence-ref:founder-loop:local-task-commit",
  localTaskProofRef:
    "proof-ref:local-task-commit:founder-action-local-task-create-scorecard",
  localTaskRef:
    "local-task:founder-loop:founder-action-local-task-create-scorecard",
  memoryCandidateRef:
    "business-memory-candidate:preference:memory-review-founder-loop-preferences",
  receiptRef:
    "receipt:founder-loop-local-task:founder-action-local-task-create-scorecard:idempotency-ref-dogfood-live-loop-local-task-commit",
  runRef: "run-ref:founder-loop-v1:governed-local-loop",
  timelineEventRef:
    "evidence-timeline:local-task/founder-action-local-task-create-scorecard",
};

function cloneForTest<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function dogfoodEvidenceMemoryBinding() {
  return {
    schema_version: "evidence-memory-loop-binding.v1",
    contract_ref: "contract-ref:usable-authority-evidence-memory-loop-binding:v1",
    source: "python_core_evidence_memory_loop_binding_read_model",
    status: "implemented_backend_owned_evidence_memory_loop_binding",
    backend_owned: true,
    local_read_model_only: true,
    safe_refs_only: true,
    raw_content_included: false,
    route_refs: [
      "GET /control-center/today/summary",
      "GET /control-center/memory/review",
      "GET /control-center/evidence/timeline",
    ],
    cli_ref: "python scripts/dev/uaa_founder_loop.py inspect-evidence-memory-binding",
    evidence_binding_count: 1,
    memory_binding_count: 1,
    evidence_bindings: [
      {
        binding_ref: "evidence-memory-binding:dogfood-live-loop:evidence",
        timeline_item_ref: dogfoodRefs.timelineEventRef,
        event_ref:
          "evidence-event:local_task_created-evidence-timeline-action-founder-action-local-task-create-scorecard",
        event_type: "local_task_created",
        group_ref: "evidence-group:dogfood-live-loop:local-task",
        title: "Local task commit evidence",
        why_recorded:
          "The dogfood loop recorded one exact local task receipt through Python Core.",
        source_refs: [dogfoodRefs.actionRef],
        action_refs: [dogfoodRefs.actionRef],
        run_refs: [dogfoodRefs.runRef],
        proof_refs: [dogfoodRefs.localTaskProofRef],
        shared_loop_refs: ["loop-binding-ref:evidence-memory:daily-loop-v1"],
        shared_run_refs: [dogfoodRefs.runRef],
        shared_action_refs: [dogfoodRefs.actionRef],
        shared_proof_refs: [dogfoodRefs.localTaskProofRef],
        approval_refs: [dogfoodRefs.approvalRef],
        receipt_refs: [dogfoodRefs.receiptRef],
        evidence_refs: [dogfoodRefs.evidenceRef, dogfoodRefs.timelineEventRef],
        memory_candidate_refs: [dogfoodRefs.memoryCandidateRef],
        blocked_authority_refs: [
          "blocked-state:evidence-memory-loop:no-action-execution",
        ],
        next_safe_action:
          "Inspect the receipt, proof, and memory binding before claiming the loop.",
      },
    ],
    memory_bindings: [
      {
        binding_ref: "evidence-memory-binding:dogfood-live-loop:memory",
        memory_candidate_ref: dogfoodRefs.memoryCandidateRef,
        review_ref: "memory-review:founder-loop-preferences",
        title: "Founder loop preference memory",
        why_shown:
          "Reviewed recall appears because the local task scorecard loop cites it.",
        source_refs: ["memory-source-ref:memory-review-queue"],
        why_shown_refs: ["why-shown-ref:dogfood-live-loop:memory"],
        related_action_refs: [dogfoodRefs.actionRef],
        related_run_refs: [dogfoodRefs.runRef],
        related_proof_refs: [dogfoodRefs.localTaskProofRef],
        shared_loop_refs: ["loop-binding-ref:evidence-memory:daily-loop-v1"],
        shared_run_refs: [dogfoodRefs.runRef],
        shared_action_refs: [dogfoodRefs.actionRef],
        shared_proof_refs: [dogfoodRefs.localTaskProofRef],
        related_evidence_refs: [
          dogfoodRefs.evidenceRef,
          dogfoodRefs.timelineEventRef,
        ],
        decision_receipt_refs: ["receipt-plan:memory-review:founder-loop-preferences"],
        blocked_authority_refs: [
          "blocked-state:evidence-memory-loop:no-memory-truth-authority",
          "blocked-state:evidence-memory-loop:no-runtime-context-injection",
        ],
        reviewed_recall_only: true,
        write_posture: "general_memory_write_blocked",
        reviewed_memory_write_scope_ref:
          "exact-scope-ref:memory-review:accept-correct-reviewed-recall-write",
        reviewed_memory_write_authorized: false,
        broad_memory_write_blocked: true,
        memory_write_safe_disable_ref:
          "safe-disable-ref:memory-review:accept-correct-reviewed-recall-write",
        memory_write_rollback_ref:
          "rollback-ref:memory-review:accept-correct-reviewed-recall-write",
        context_posture: "runtime_context_injection_blocked",
        next_safe_action:
          "Use this memory only as reviewed recall, not truth or hidden context.",
        memory_truth_authority: false,
        context_injection_authorized: false,
        automatic_memory_write_authorized: false,
      },
    ],
    evidence_refs: [dogfoodRefs.evidenceRef, dogfoodRefs.timelineEventRef],
    memory_candidate_refs: [dogfoodRefs.memoryCandidateRef],
    action_refs: [dogfoodRefs.actionRef],
    run_refs: [dogfoodRefs.runRef],
    proof_refs: [dogfoodRefs.localTaskProofRef],
    receipt_refs: [dogfoodRefs.receiptRef, dogfoodRefs.decisionReceiptRef],
    shared_loop_ref: "loop-binding-ref:evidence-memory:daily-loop-v1",
    shared_run_refs: [dogfoodRefs.runRef],
    shared_action_refs: [dogfoodRefs.actionRef],
    shared_proof_refs: [dogfoodRefs.localTaskProofRef],
    reviewed_memory_write_scope_ref:
      "exact-scope-ref:memory-review:accept-correct-reviewed-recall-write",
    reviewed_memory_write_authorized_decisions: ["accept", "correct"],
    reviewed_memory_write_authorized: false,
    broad_memory_write_blocked: true,
    memory_write_safe_disable_ref:
      "safe-disable-ref:memory-review:accept-correct-reviewed-recall-write",
    memory_write_rollback_ref:
      "rollback-ref:memory-review:accept-correct-reviewed-recall-write",
    promotion_path_refs: [
      "promotion-path:evidence-memory:reviewed-recall-write-exact-scope",
      "promotion-path:evidence-memory:context-injection-separate-contract",
      "promotion-path:evidence-memory:delete-export-separate-contract",
      "promotion-path:evidence-memory:connector-sync-separate-contract",
    ],
    blocked_authority_refs: [
      "blocked-state:evidence-memory-loop:no-memory-truth-authority",
      "blocked-state:evidence-memory-loop:no-runtime-context-injection",
      "blocked-state:evidence-memory-loop:no-action-execution",
      "blocked-state:evidence-memory-loop:no-connector-write-or-send",
      "blocked-state:evidence-memory-loop:no-provider-model-call",
      "blocked-state:evidence-memory-loop:no-production-authority",
    ],
    operator_summary:
      "One local task receipt links Action Inbox, Evidence, Memory, Proof, and Trust through safe refs.",
    next_safe_action:
      "Inspect the shared refs before promoting broader authority.",
    authority_boundary:
      "Evidence and Memory explain the loop only; they do not execute actions or grant memory truth.",
    memory_truth_authority: false,
    context_injection_authorized: false,
    automatic_memory_write_authorized: false,
    memory_delete_enabled: false,
    memory_export_enabled: false,
    action_execution_enabled: false,
    connector_write_enabled: false,
    connector_send_enabled: false,
    provider_model_call_enabled: false,
    shell_subprocess_execution_enabled: false,
    browser_execution_enabled: false,
    background_autonomy_enabled: false,
    production_authority_enabled: false,
  };
}

function dogfoodActionItem() {
  const seed = cloneForTest(
    mockApiData.founderActionsInbox.items.find(
      (candidate) => candidate.item_ref === "founder-action:mock-local-task-create",
    ) ?? mockApiData.founderActionsInbox.items[0],
  );
  return {
    ...seed,
    item_ref: dogfoodRefs.actionRef,
    title: "Maintain operational maturity scorecard",
    safe_summary:
      "Create a local Founder Loop task for the dogfood acceptance scorecard.",
    status: "receipt_recorded",
    action_kind: "local_task_create",
    action_group_id: "receipt_recorded",
    action_group_label: "Receipt recorded",
    action_group_reason:
      "The exact local task lane has a backend receipt and proof refs.",
    action_group_available_action: "Inspect receipt, evidence, and proof refs.",
    action_envelope_ref: dogfoodRefs.actionEnvelopeRef,
    approval_envelope_ref: "approval-envelope:founder-loop:local-task-create-scorecard",
    approval_envelope_status: "approved_receipt_recorded",
    local_task_ref: dogfoodRefs.localTaskRef,
    local_task_commit_approval_ref: dogfoodRefs.approvalRef,
    local_task_commit_approval_status: "approved",
    local_task_commit_eligible: false,
    local_task_commit_receipt_ref: dogfoodRefs.receiptRef,
    local_task_commit_blocked_reasons: [],
    local_task_commit_next_safe_action:
      "Inspect the local task receipt and Proof Detail before promoting authority.",
    receipt_refs: [
      "receipt-plan:founder-loop:local-task-create-scorecard",
      dogfoodRefs.decisionReceiptRef,
      dogfoodRefs.receiptRef,
    ],
    evidence_refs: [dogfoodRefs.evidenceRef, dogfoodRefs.timelineEventRef],
    audit_refs: [
      "audit:founder-loop-local-task:founder-action-local-task-create-scorecard:idempotency-ref-dogfood-live-loop-local-task-commit",
    ],
    proof_refs: [dogfoodRefs.localTaskProofRef],
    approval_envelope: {
      ...seed.approval_envelope,
      source: "python_core_action_inbox_read_model",
      backend_owned: true,
      exact_scope:
        "scope-ref:plans-action-envelope:founder-action-local-task-create-scorecard",
      approval_requirement:
        "approval-requirement:plans-action-envelope:founder-action-local-task-create-scorecard",
      expected_receipt_refs: [dogfoodRefs.receiptRef],
      evidence_refs: [dogfoodRefs.evidenceRef],
      missing_field_states: ["none"],
    },
    receipt_visibility: {
      ...seed.receipt_visibility,
      source: "python_core_action_inbox_read_model",
      backend_owned: true,
      decision_receipt_ref: dogfoodRefs.decisionReceiptRef,
      local_task_ref: dogfoodRefs.localTaskRef,
      local_task_commit_receipt_ref: dogfoodRefs.receiptRef,
      evidence_timeline_event_ref: dogfoodRefs.timelineEventRef,
      missing_field_states: ["none"],
    },
  };
}

function withDogfoodProofRunDetail(record: typeof mockControlCenterData.proofIndex.records[number]) {
  const kind = String(record.proof_kind).replaceAll("_", "-");
  const runRef = record.run_refs[0] ?? dogfoodRefs.runRef;
  return {
    ...record,
    run_detail: {
      ...record.run_detail,
      source: "python_core_control_center_proof_run_detail",
      run_detail_ref: `run-detail-ref:dogfood:${kind}`,
      proof_ref: record.proof_ref,
      proof_kind: record.proof_kind,
      run_ref: runRef,
      status: record.status,
      title: record.title,
      safe_summary:
        "Dogfood Run Detail ties proof, run, receipt, evidence, approval, rollback, memory, and blocked authority refs.",
      authority_posture: record.authority_posture,
      route_refs: record.route_refs,
      backend_route_refs: [
        ...record.backend_route_refs,
        "GET /control-center/proof/{proof_ref}",
      ],
      related_run_refs: [runRef],
      operator_run_event_refs: [`operator-run-event-ref:proof:${kind}:dogfood`],
      receipt_refs: record.receipt_refs,
      evidence_refs: record.evidence_refs,
      audit_refs: record.audit_refs,
      approval_refs: record.approval_refs,
      rollback_refs: record.rollback_refs,
      safe_disable_refs: record.safe_disable_refs,
      memory_candidate_refs: record.memory_candidate_refs,
      blocked_authority_refs: record.blocked_authority_refs,
      exact_promotion_path_refs: [
        "promotion-path-ref:proof-run-spine:detail-route-parity",
        "promotion-path-ref:proof-run-spine:receipt-evidence-binding",
        "promotion-path-ref:proof-run-spine:rollback-safe-disable-binding",
        "promotion-path-ref:proof-run-spine:cli-inspection-parity",
        `promotion-path-ref:proof-run-spine:${kind}`,
      ],
      next_safe_action: record.next_safe_action,
    },
  };
}

function dogfoodProofIndex() {
  const localTaskRecord = withDogfoodProofRunDetail({
    ...mockControlCenterData.proofIndex.records[0],
    proof_ref: dogfoodRefs.localTaskProofRef,
    proof_kind: "local_task_commit",
    status: "receipt_recorded",
    title: "Local Task Commit",
    safe_summary:
      "Dogfood Live Loop Acceptance proves one exact local task receipt through backend-owned safe refs.",
    authority_posture:
      "Local task proof is local-only and does not grant generic action execution.",
    route_refs: ["route-ref:control-center:actions"],
    backend_route_refs: [
      "POST /control-center/actions/{action_id}/local-task/commit",
    ],
    run_refs: [dogfoodRefs.runRef],
    receipt_refs: [dogfoodRefs.receiptRef],
    evidence_refs: [dogfoodRefs.evidenceRef, dogfoodRefs.timelineEventRef],
    audit_refs: [
      "audit:founder-loop-local-task:founder-action-local-task-create-scorecard:idempotency-ref-dogfood-live-loop-local-task-commit",
    ],
    approval_refs: [dogfoodRefs.approvalRef],
    rollback_refs: ["rollback-not-applicable:local-task-safe-disable"],
    safe_disable_refs: ["safe-disable:founder-loop:local-task-create-scorecard"],
    memory_candidate_refs: [dogfoodRefs.memoryCandidateRef],
    next_safe_action:
      "Inspect receipt and evidence refs before claiming the local task outcome.",
    blocked_authority_refs: [
      "blocked-state:proof-detail:no-runtime-execution",
      "blocked-state:proof-detail:no-provider-model-call",
      "blocked-state:proof-detail:no-connector-write-or-send",
      "blocked-state:proof-detail:no-production-authority",
    ],
  });
  const dailyRecord = withDogfoodProofRunDetail({
    ...mockControlCenterData.proofIndex.records[0],
    proof_ref: "proof-ref:founder-loop-v1:governed-local-loop",
    proof_kind: "daily_loop",
    status: "complete_local_dogfood_loop_proven",
    title: "Governed Daily Loop",
    safe_summary:
      "Start Here, Today, Action Inbox, Evidence, Memory, Proof, and Trust share the same backend-owned loop refs.",
    run_refs: [dogfoodRefs.runRef],
    receipt_refs: [dogfoodRefs.receiptRef],
    evidence_refs: [dogfoodRefs.evidenceRef],
    approval_refs: [dogfoodRefs.approvalRef],
    memory_candidate_refs: [dogfoodRefs.memoryCandidateRef],
  });
  return {
    ...mockControlCenterData.proofIndex,
    source: "python_core_control_center_proof_index",
    status: "implemented_backend_owned_universal_proof_index",
    backend_owned: true,
    proof_count: 2,
    proof_refs: [dogfoodRefs.localTaskProofRef, dailyRecord.proof_ref],
    records: [localTaskRecord, dailyRecord],
  };
}

function backendOwnedProofIndexFixture() {
  const proofIndex = cloneForTest(mockControlCenterData.proofIndex);
  return {
    ...proofIndex,
    source: "python_core_control_center_proof_index",
    status: "implemented_backend_owned_universal_proof_index",
    backend_owned: true,
    records: proofIndex.records.map((record) => ({
      ...record,
      run_detail: record.run_detail
        ? {
            ...record.run_detail,
            source: "python_core_control_center_proof_run_detail" as const,
          }
        : record.run_detail,
    })),
  };
}

function dogfoodLiveLoopEndpointData() {
  const binding = dogfoodEvidenceMemoryBinding();
  const actionItem = dogfoodActionItem();
  const today = {
    ...cloneForTest(mockControlCenterData.founderToday),
    status: "storage_backed_daily_loop",
    actions: [actionItem],
    evidence_refs: [dogfoodRefs.evidenceRef, dogfoodRefs.timelineEventRef],
    daily_loop_summary: {
      ...cloneForTest(mockControlCenterData.founderToday.daily_loop_summary),
      status: "complete_local_dogfood_loop_proven",
      loop_ref: "daily-loop:dogfood-live-loop-acceptance",
      today_plan_summary:
        "One complete local dogfood loop is receipt-backed and inspectable.",
      next_safe_action:
        "Open Proof Detail, Evidence, Memory, and Trust to inspect the same refs.",
    },
    evidence_memory_loop_binding_contract_ref: binding.contract_ref,
    evidence_memory_loop_binding_read_model: binding,
    founder_loop_v1_product_proof_read_model: founderLoopProductProofFixture({
      status: "complete_local_dogfood_loop_proven",
      scenario_ref: "scenario-ref:dogfood-live-loop-acceptance",
      shared_state_ref: "founder-loop-state-ref:dogfood-live-loop-acceptance",
      action_inbox_refs: [dogfoodRefs.actionRef],
      action_decision_receipt_refs: [dogfoodRefs.decisionReceiptRef],
      evidence_timeline_refs: [dogfoodRefs.timelineEventRef],
      evidence_event_refs: [dogfoodRefs.timelineEventRef],
      memory_review_candidate_refs: [dogfoodRefs.memoryCandidateRef],
      receipt_refs: [dogfoodRefs.decisionReceiptRef, dogfoodRefs.receiptRef],
      evidence_refs: [dogfoodRefs.evidenceRef],
      decision_receipt_status: "local_task_receipt_recorded",
      safe_summary:
        "Dogfood Live Loop Acceptance binds one local task commit receipt to shared backend-owned refs.",
    }),
    founder_loop_runs_integration_read_model: founderLoopRunsIntegrationFixture({
      status: "backend_owned_run_refs_visible",
      run_refs: [dogfoodRefs.runRef],
      receipt_refs: [dogfoodRefs.receiptRef],
      evidence_refs: [dogfoodRefs.evidenceRef],
      action_source_refs: [dogfoodRefs.actionRef],
      proof_refs: [dogfoodRefs.localTaskProofRef],
      memory_candidate_refs: [dogfoodRefs.memoryCandidateRef],
    }),
    memory_candidate_refs: [dogfoodRefs.memoryCandidateRef],
    memory_review_decision_receipt_refs: [
      "receipt-plan:memory-review:founder-loop-preferences",
    ],
  };
  const startHere = {
    ...cloneForTest(mockControlCenterData.founderStartHere),
    source: "python_core_control_center_start_here_read_model",
    backend_owned: true,
    status: "implemented_backend_owned_start_here_loop_contract",
    readiness_state: "ready_for_one_local_governed_loop",
    local_loop_status: "one_governed_local_loop_available",
    complete_daily_loop_available: true,
    action_proposal_ref: dogfoodRefs.actionEnvelopeRef,
    primary_run_ref: dogfoodRefs.runRef,
    primary_proof_ref: "proof-ref:founder-loop-v1:governed-local-loop",
    missing_prerequisite_refs: [],
    evidence_refs: [dogfoodRefs.evidenceRef, dogfoodRefs.timelineEventRef],
    steps: mockControlCenterData.founderStartHere.steps.map((step) => ({
      ...step,
      proof_ref:
        step.step_id === "decision_receipt"
          ? dogfoodRefs.localTaskProofRef
          : "proof-ref:founder-loop-v1:governed-local-loop",
      receipt_refs:
        step.step_id === "decision_receipt" ? [dogfoodRefs.receiptRef] : [],
      evidence_refs: [dogfoodRefs.evidenceRef],
      approval_refs:
        step.step_id === "action_inbox" ? [dogfoodRefs.approvalRef] : [],
      memory_candidate_refs:
        step.step_id === "memory_review" ? [dogfoodRefs.memoryCandidateRef] : [],
    })),
  };
  const actionsInbox = {
    ...cloneForTest(mockControlCenterData.founderActionsInbox),
    ...cloneForTest(mockApiData.founderActionsInbox),
    status: "storage_backed_review_queue",
    items: [actionItem],
    action_groups: [
      {
        group_id: "receipt_recorded",
        label: "Receipt recorded",
        safe_summary:
          "The dogfood local task lane has backend receipt and proof refs.",
        available_action: "Inspect receipt and evidence refs.",
        count: 1,
      },
    ],
    action_inbox_work_queue_read_model: {
      ...cloneForTest(
        mockControlCenterData.founderActionsInbox.action_inbox_work_queue_read_model,
      ),
      source: "python_core_action_inbox_work_queue_read_model",
      backend_owned: true,
      status: "implemented_backend_owned_action_inbox_work_queue",
      item_count: 1,
      operator_actionable_count: 0,
      ready_for_decision_count: 0,
      approved_local_task_count: 0,
      proposal_only_count: 0,
      blocked_count: 0,
      receipt_recorded_count: 1,
      lane_count: 1,
      lanes: [
        {
          lane_id: "receipt_recorded",
          lane_ref: "action-work-queue-lane:receipt-recorded",
          label: "Receipt recorded",
          status: "receipt_recorded",
          safe_summary:
            "The local task commit receipt is available for inspection.",
          available_action: "Inspect receipt and proof refs.",
          count: 1,
          item_refs: [dogfoodRefs.actionRef],
          tier: "tier_1_local_read_preview",
          blocked_authority_refs: [],
        },
      ],
      work_item_count: 1,
      work_item_refs: [dogfoodRefs.actionRef],
      work_items: [
        {
          item_ref: dogfoodRefs.actionRef,
          title: "Maintain operational maturity scorecard",
          lane_id: "receipt_recorded",
          lane_label: "Receipt recorded",
          status: "receipt_recorded",
          priority: "high",
          risk_class: "medium",
          action_kind: "local_task_create",
          side_effect_class: "local_dev_workspace_only",
          safe_summary:
            "The exact local task lane produced a backend receipt and proof refs.",
          approval_posture: "approved_receipt_recorded",
          receipt_posture: "receipt_refs_recorded",
          mutation_control_posture: "no_mutation_control_exposed",
          next_safe_action:
            "Inspect the local task receipt and Proof Detail before promoting authority.",
          approval_required: true,
          operator_actionable: false,
          local_task_commit_eligible: false,
          fake_mutation_control_exposed: false,
          approval_envelope_ref:
            "approval-envelope:founder-loop:local-task-create-scorecard",
          local_task_commit_route_ref:
            "POST /control-center/actions/{action_id}/local-task/commit",
          proof_ref: dogfoodRefs.localTaskProofRef,
          expected_receipt_refs: [dogfoodRefs.receiptRef],
          receipt_refs: [dogfoodRefs.decisionReceiptRef, dogfoodRefs.receiptRef],
          evidence_refs: [dogfoodRefs.evidenceRef, dogfoodRefs.timelineEventRef],
          rollback_ref: "rollback-not-applicable:local-task-safe-disable",
          safe_disable_ref: "safe-disable:founder-loop:local-task-create-scorecard",
          blocked_authority_refs: [
            "blocked-state:action-inbox-work-queue:no-broad-action-execution",
            "blocked-state:action-inbox-work-queue:no-connector-write-or-send",
          ],
        },
      ],
      next_item: null,
      next_item_ref: null,
      next_safe_action:
        "Inspect the recorded local task receipt and Proof Detail before promoting authority.",
      tier_3_exact_local_task_commit_available: false,
      fake_mutation_controls_exposed: false,
      unsafe_ref_omitted_count: 0,
      unsafe_ref_blocked_state_refs: [],
    },
  };
  const evidence = {
    ...cloneForTest(mockControlCenterData.founderEvidenceTimeline),
    status: "storage_backed_redacted_history_grammar_refs",
    event_count: 1,
    group_count: 1,
    receipt_refs: [dogfoodRefs.receiptRef],
    evidence_refs: [dogfoodRefs.evidenceRef, dogfoodRefs.timelineEventRef],
    idempotency_refs: [
      "idempotency-ref:dogfood-live-loop:local-task-commit",
    ],
    events: [
      {
        event_ref: dogfoodRefs.timelineEventRef,
        event_type: "local_task_created",
        group_kind: "action",
        group_ref: "evidence-group:dogfood-live-loop:local-task",
        title: "Local task commit receipt recorded",
        safe_summary:
          "The exact local task lane produced a backend receipt and evidence refs.",
        proposed_ref: dogfoodRefs.actionRef,
        approved_ref: dogfoodRefs.approvalRef,
        happened_ref: dogfoodRefs.receiptRef,
        changed_ref: dogfoodRefs.localTaskRef,
        undoable_ref: "rollback-not-applicable:local-task-safe-disable",
        stale_ref: "freshness-ref:dogfood-live-loop:current",
        blocked_ref: "blocked-state:dogfood-live-loop:no-external-side-effect",
        history_answers: cloneForTest(
          mockControlCenterData.founderEvidenceTimeline.events[0]?.history_answers ??
            mockControlCenterData.founderToday.evidence_timeline[0]?.history_answers,
        ),
        evidence_refs: [dogfoodRefs.evidenceRef],
        receipt_refs: [dogfoodRefs.receiptRef],
        audit_refs: [
          "audit:founder-loop-local-task:founder-action-local-task-create-scorecard:idempotency-ref-dogfood-live-loop-local-task-commit",
        ],
        idempotency_refs: [
          "idempotency-ref:dogfood-live-loop:local-task-commit",
        ],
      },
    ],
    groups: [
      {
        group_ref: "evidence-group:dogfood-live-loop:local-task",
        group_kind: "action",
        title: "Local task commit",
        event_count: 1,
        event_types: ["local_task_created"],
        evidence_refs: [dogfoodRefs.evidenceRef],
      },
    ],
    evidence_memory_loop_binding_contract_ref: binding.contract_ref,
    evidence_memory_loop_binding_read_model: binding,
    founder_loop_runs_integration_read_model:
      today.founder_loop_runs_integration_read_model,
  };
  const memoryReview = {
    ...cloneForTest(mockControlCenterData.founderMemoryReview),
    evidence_memory_loop_binding_contract_ref: binding.contract_ref,
    evidence_memory_loop_binding_read_model: binding,
    items: mockControlCenterData.founderMemoryReview.items.map((item, index) =>
      index === 0
        ? {
            ...item,
            business_memory_candidate_ref: dogfoodRefs.memoryCandidateRef,
            evidence_refs: [dogfoodRefs.evidenceRef, dogfoodRefs.timelineEventRef],
          }
        : item,
    ),
  };
  const trust = backendOwnedTrustAuthorityMatrix();
  trust.operator_summary =
    "Dogfood Live Loop Acceptance proves local reviewed authority for one local task receipt; broad autonomy remains blocked.";
  trust.proof_refs = [
    dogfoodRefs.localTaskProofRef,
    ...trust.proof_refs.filter((ref) => ref !== dogfoodRefs.localTaskProofRef),
  ];
  trust.lanes = trust.lanes.map((lane) =>
    lane.lane_ref === "trust-lane:local-task-commit"
      ? {
          ...lane,
          proof_refs: [dogfoodRefs.localTaskProofRef],
          operator_can_do_now:
            "Inspect the dogfood local task receipt and proof refs.",
        }
      : lane,
  );
  return {
    [API_ENDPOINTS.founderTodaySummary]: today,
    [API_ENDPOINTS.founderStartHereSummary]: startHere,
    [API_ENDPOINTS.founderActionsInbox]: actionsInbox,
    [API_ENDPOINTS.controlCenterProofIndex]: dogfoodProofIndex(),
    [API_ENDPOINTS.trustAuthorityMatrix]: trust,
    [API_ENDPOINTS.founderEvidenceTimeline]: evidence,
    [API_ENDPOINTS.founderMemoryReview]: memoryReview,
  };
}

function envelopeForReadEndpoint(url: string) {
  const data = {
    [API_ENDPOINTS.controlCenterManifest]: {
      ...mockApiData.manifest,
      version: "0.20.1",
    },
    [API_ENDPOINTS.controlCenterDashboard]: {
      ...mockApiData.dashboard,
      baseline_version: "0.20.1",
      provider_credential_readiness:
        mockControlCenterData.dashboard.provider_credential_readiness,
    },
    [API_ENDPOINTS.approvalSummary]: mockApiData.dashboard.approval_summary,
    [API_ENDPOINTS.approvalQueue]: mockControlCenterData.runAttachedApprovalQueue,
    [API_ENDPOINTS.runObservability]: {
      ...mockControlCenterData.runObservability,
      source: "python_core_run_observability_read_model",
      backend_owned: true,
      status: "implemented_read_only",
      run_ref: "task-decomposition-run:app-test-observability",
      selected_run_ref: "task-decomposition-run:app-test-observability",
      lifecycle: {
        schema_version: "durable_run_lifecycle_read_model.v1",
      },
      progress: {
        schema_version: "run_progress_read_model.v1",
      },
      run_refs: ["task-decomposition-run:app-test-observability"],
      lifecycle_event_refs: ["durable-run-storage-entry:test:app"],
      progress_event_refs: ["durable-run-event-ref:test:app"],
      approval_refs: ["approval-ref:test:app"],
      coworker_handoff_refs: ["handoff-ref:test:app"],
      connector_delivery_refs: ["connector-delivery-ref:test:app"],
      receipt_refs: ["receipt-ref:test:app"],
      evidence_refs: ["evidence-ref:test:app"],
      proof_refs: ["proof-ref:test:app"],
      event_count: 1,
      progress_event_count: 1,
      approval_item_count: 1,
      coworker_event_count: 1,
      connector_delivery_count: 1,
      connector_delivery_review_count: 1,
    },
    [API_ENDPOINTS.runtimeReadinessSummary]:
      mockApiData.dashboard.runtime_readiness_summary,
    [API_ENDPOINTS.foundationGateSummary]:
      mockApiData.dashboard.foundation_gate_summary,
    [API_ENDPOINTS.controlCenterStatus]: mockApiData.status,
    [API_ENDPOINTS.controlCenterRoutes]: mockApiData.routes,
    [API_ENDPOINTS.runtimeReadiness]: {
      ...mockApiData.runtimeReadiness,
      baseline_version: "0.20.1",
    },
    [API_ENDPOINTS.runtimeCapabilityMatrix]: {
      ...mockApiData.capabilityMatrix,
      baseline_version: "0.20.1",
    },
    [API_ENDPOINTS.setupAssistantSummary]: mockApiData.setupAssistantSummary,
    [API_ENDPOINTS.providerSetupGuide]: mockControlCenterData.providerCatalog,
    [API_ENDPOINTS.controlCenterSettingsStatus]:
      mockControlCenterData.settingsStatus,
    [API_ENDPOINTS.controlCenterLocalModelsStatus]:
      mockControlCenterData.localModelsStatus,
    [API_ENDPOINTS.founderTodaySummary]: mockControlCenterData.founderToday,
    [API_ENDPOINTS.founderStartHereSummary]: {
      ...mockControlCenterData.founderStartHere,
      source: "python_core_control_center_start_here_read_model",
      backend_owned: true,
      status: "implemented_backend_owned_start_here_loop_contract",
      readiness_state: "ready_for_one_local_governed_loop",
      local_loop_status: "one_governed_local_loop_available",
      complete_daily_loop_available: true,
      missing_prerequisite_refs: [],
    },
    [API_ENDPOINTS.controlCenterProofIndex]: {
      ...backendOwnedProofIndexFixture(),
    },
    [API_ENDPOINTS.trustAuthorityMatrix]: backendOwnedTrustAuthorityMatrix(),
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
    [API_ENDPOINTS.founderActionsInbox]: {
      ...mockControlCenterData.founderActionsInbox,
      ...mockApiData.founderActionsInbox,
      items: mockApiData.founderActionsInbox.items,
    },
    [API_ENDPOINTS.founderMorningBriefing]:
      mockControlCenterData.founderMorningBriefing,
    [API_ENDPOINTS.founderSourceReadiness]: {
      ...mockControlCenterData.founderSourceReadiness,
      source: "python_core_source_readiness_read_model",
      backend_owned: true,
      generated_at: "2026-01-01T00:00:00Z",
      connector_draft_proposals: {
        ...mockControlCenterData.founderSourceReadiness.connector_draft_proposals,
        source: "python_core_connector_draft_proposal_read_model",
        backend_owned: true,
        contract_ref: "contract-ref:connector-draft-only-proposals:v1",
        proof_refs: ["proof-ref:connector-draft-only-proposals:v1"],
        proposals:
          mockControlCenterData.founderSourceReadiness.connector_draft_proposals?.proposals.map(
            (proposal) => ({
              ...proposal,
              proposal_ref: proposal.proposal_ref.replace("mock-", ""),
              draft_ref: proposal.draft_ref.replace("mock-", ""),
            }),
          ) ?? [],
      },
      source_readiness_proposal_candidates:
        mockControlCenterData.founderSourceReadiness.source_readiness_proposal_candidates.map(
          (proposal) => ({
            ...proposal,
            source: "python_core_source_readiness_read_model",
            backend_owned: true,
            proposal_ref: proposal.proposal_ref.replace("mock-", ""),
            action_item_ref: proposal.action_item_ref.replace("mock-", ""),
            status: "proposal_only",
          }),
        ),
      source_readiness_posture: {
        ...mockControlCenterData.founderSourceReadiness
          .source_readiness_posture,
        source: "python_core_source_readiness_read_model",
        backend_owned: true,
      },
    },
    [API_ENDPOINTS.founderStorageStatus]: mockApiData.founderStorageStatus,
  };
  const endpoint = Object.keys(data).find((candidate) =>
    url.endsWith(candidate),
  );
  return { ok: true, result: data[endpoint as keyof typeof data] };
}

const mockApiData = {
  manifest: {
    manifest_id: "test_manifest",
    version: "0.20.1",
    generated_at: "2026-01-01T00:00:00Z",
    declared_capabilities: ["control_center_read_only_dashboard"],
    blocked_capabilities: [
      "runtime_execution",
      "remote_dispatch",
      "mobile_sensor_access",
      "plugin_enablement",
    ],
    api_route_refs: [
      "/control-center/dashboard",
      "/control-center/actions/preview",
    ],
    metadata: {
      read_only: true,
      preview_only: true,
      production_control_center: false,
    },
    surfaces: [],
  },
  dashboard: {
    snapshot_id: "test_dashboard",
    baseline_version: "0.20.1",
    generated_at: "2026-01-01T00:00:00Z",
    system_status: {
      label: "Control Center",
      status: "read_only",
      summary: "Read-only local backend summary.",
    },
    foundation_gate_summary: {
      status: "passed",
      passed_count: 1,
      failed_count: 0,
      summary: "Gate summary only.",
    },
    runtime_readiness_summary: {
      status: "report_only",
      production_ready: false,
      real_model_runtime_ready: false,
      remote_execution_ready: false,
      mobile_sensor_ready: false,
      plugin_or_native_build_ready: false,
    },
    approval_summary: {
      pending_count: 0,
      approval_grants_created: false,
      arbitrary_approval_ref_authority: false,
      summary: "Read-only approval summary.",
    },
    api_summary: {
      route_count: MOCK_OPENAPI_ROUTE_COUNT,
      control_center_route_count: MOCK_CONTROL_CENTER_ROUTE_COUNT,
      operation_ids_unique: true,
      execution_routes_present: false,
    },
    remote_worker_summary: {
      status: "dry_run_only",
      execution_enabled: false,
      dispatch_enabled: false,
    },
    private_mesh_summary: {
      status: "planned_disabled",
      headscale_integrated: false,
      tailscale_integrated: false,
      wireguard_integrated: false,
    },
    mobile_planning_summary: {
      status: "planned_disabled",
      sensor_access_enabled: false,
      mobile_app_implemented: false,
    },
    plugin_governance_summary: {
      status: "planned_disabled",
      plugin_enablement_allowed: false,
      native_build_tools_enabled: false,
    },
    warnings: [],
    blockers: [],
    next_recommended_action: "review_local_backend_status",
    metadata: { read_only: true, preview_only: true },
  },
  status: {
    status: "available",
    read_only: true,
    preview_only: true,
    frontend_shell: true,
    production_authority: false,
    message: "Local backend status only.",
  },
  routes: {
    route_count: 15,
    routes: [
      {
        path: "/control-center/dashboard",
        methods: ["GET"],
        operation_id: "get_control_center_dashboard",
        tags: ["control-center"],
        validation_only: true,
        route_group: "control-center",
        owner: "Python Agent Core",
        service_module: "control_center_service",
        side_effect_class: "read_only",
        route_classification: "local_readonly",
        protected_route: true,
        classification_reason:
          "local read-only route inventory or status surface; protected in production posture",
        risk_class: "low",
        release_status: "implemented",
        auth_posture: "local-dev unauthenticated; production auth future",
        blocked_from_production: true,
        evidence_refs: [
          "docs/control_center/route_status_manifest.json",
          "tests/test_control_center_api_routes.py",
        ],
      },
    ],
  },
  runtimeReadiness: {
    report_id: "test_readiness",
    baseline_version: "0.20.1",
    status: "report_only",
    production_ready: false,
    real_model_runtime_ready: false,
    remote_execution_ready: false,
    mobile_sensor_ready: false,
    plugin_or_native_build_ready: false,
    capability_matrix_ref: "test_matrix",
    warnings: [],
    blockers: [],
    metadata: { model_output_authoritative: false },
  },
  capabilityMatrix: {
    matrix_id: "test_matrix",
    baseline_version: "0.20.1",
    metadata: { no_model_was_called: true },
    entries: [],
  },
  setupAssistantSummary: {
    plan_ref: "macos-setup-plan:api-test",
    status: "dry_run_only",
    macos_first: true,
    local_first: true,
    disabled_by_default: true,
    native_macos_app_ready: false,
    control_center_preview_ready: true,
    setup_question_assistant_enabled: false,
    model_output_authoritative: false,
    installer_side_effects_enabled: false,
    visual_shell_ref: "control-center:setup-assistant-api-test",
    full_strength_goal:
      "First run leads from local setup posture to a daily loop with Today, Action Inbox, receipt, evidence, proof, memory, and Trust refs.",
    repo_safe_scope:
      "Read-only setup plan, local package proof refs, dry-run approval envelopes, and bounded Control Center presentation only.",
    blocked_authority_summary:
      "Installer execution, model downloads, LaunchAgent changes, bridge enablement, shell subprocess, browser automation, public distribution, signing, notarization, and production authority remain blocked.",
    first_run_loop_refs: [
      "loop-ref:setup-to-daily-loop:v1",
      "contract-ref:start-here-local-loop:v1",
      "contract-ref:private-beta-readiness-gate:v1",
    ],
    local_package_proof_status:
      "local_unsigned_loopback_package_proof_available_runtime_launch_blocked",
    local_package_proof_refs: [
      "packaging-proof:local-runtime-loopback",
      "packaging-proof:local-macos-app-bundle",
      "script:verify-local-macos-app-bundle-proof",
    ],
    promotion_path_refs: [
      "promotion-path-ref:setup:local-rehearsal-receipt",
      "promotion-path-ref:setup:exact-approved-mutation-pr",
    ],
    steps: [
      {
        step_id: "macos-setup-step:api-summary",
        label: "Backend API setup timeline",
        kind: "first_launch",
        status: "dry_run_only",
        safe_summary: "Read-only setup summary from backend test fixture.",
        route_refs: ["/control-center/setup-assistant/summary"],
        detail_preview: ["bounded setup preview only"],
        log_preview: ["no command executed"],
        approval_required: true,
        approval_ref: "approval-ref:macos-setup-api-summary",
        receipt_ref: "receipt-plan:macos-setup-api-summary",
        rollback_ref: "rollback-plan:macos-setup-api-summary",
        latency_ref: "latency-ref:macos-setup-api-summary",
        reason_codes: ["MACOS_SETUP_SUMMARY_API_TEST"],
        next_safe_action: "inspect_setup_plan",
      },
    ],
    model_recommendations: [
      {
        recommendation_ref: "macos-setup-model-rec:api-test",
        model_ref: "local-model-option:api-test",
        display_name: "API test model class",
        fit_summary: "Recommendation class only.",
        recommended_for: "Frontend mapper test.",
        memory_bucket: "ram:test",
        disk_bucket: "disk:test",
        privacy_summary: "No model call is made.",
        approval_required_before_download: true,
        selected_by_default: true,
        reason_codes: ["MACOS_SETUP_MODEL_RECOMMENDATION_ONLY"],
      },
    ],
    bridge_previews: [
      {
        bridge_ref: "macos-setup-bridge:api-test",
        label: "API test bridge",
        status: "approval_required",
        safe_summary: "Bridge preview only.",
        enablement_default: "disabled",
        approval_required: true,
        reason_codes: ["MACOS_SETUP_BRIDGE_DISABLED_BY_DEFAULT"],
      },
    ],
    approval_envelopes: [
      {
        envelope_ref: "macos-setup-approval-envelope:api-summary",
        status: "approval_required",
        setup_step_id: "macos-setup-step:api-summary",
        setup_step_kind: "first_launch",
        safe_summary:
          "Dry-run approval envelope from backend test fixture; no setup mutation is enabled.",
        requested_scope_refs: ["scope-ref:macos-setup-api-summary"],
        approval_request_ref: "approval-ref:macos-setup-api-summary",
        expected_receipt_ref: "receipt-plan:macos-setup-api-summary",
        rollback_plan_ref: "rollback-plan:macos-setup-api-summary",
        idempotency_key_ref: "idempotency-ref:macos-setup-api-summary",
        risk_class: "medium",
        side_effect_class: "validation_only",
        not_scoped_actions: ["setup-mutation"],
        blocked_runtime_authority: ["installer-authority"],
        evidence_refs: ["docs-ref:uaa-setup-assistant-plan"],
        verifier_refs: ["vitest:control-center-app"],
        operator_next_action: "inspect_setup_plan",
        stale_state_handling: "Stale if backend setup summary fixture changes.",
        redaction_summary:
          "Safe refs only; raw logs, paths, prompts, and credentials are omitted.",
        dry_run_only: true,
        approval_required: true,
        approval_ref_is_identifier_only: true,
        exact_scope_required: true,
        idempotency_required: true,
        rollback_required: true,
        redaction_required: true,
        disabled_by_default: true,
        reason_codes: ["MACOS_SETUP_APPROVAL_ENVELOPE_DRY_RUN_ONLY"],
      },
    ],
    receipt_plan: {
      receipt_plan_ref: "macos-setup-receipt-plan:api-test",
      audit_ref: "macos-setup-audit:api-test",
      latency_ref: "macos-setup-latency:api-test",
      safe_summary: "Receipt preview only.",
      receipt_created: false,
      audit_event_created: false,
      raw_log_stored: false,
      raw_prompt_stored: false,
      raw_provider_payload_stored: false,
      credential_material_stored: false,
    },
    rollback_plan: {
      rollback_plan_ref: "macos-setup-rollback-plan:api-test",
      uninstall_ref: "macos-setup-uninstall:api-test",
      safe_summary: "Rollback preview only.",
      rollback_available_after_approval: true,
      rollback_executed: false,
    },
    blocked_capabilities: ["macos-setup-model-download"],
    next_steps: ["Review setup summary."],
    morning_review_checklist: ["Confirm setup summary is dry-run only."],
  },
  m15Review: {
    status: "mock_preview_only",
    readOnly: true,
    previewOnly: true,
    mock: true,
    nonAuthoritative: true,
    authorityBoundary:
      "Approval Authority handles final decision; Control Center displays summaries only.",
    warningCodes: ["MOCK_DATA_ONLY", "REDACTED_SUMMARY_ONLY"],
    approvalQueue: [
      {
        approvalRef: "mock_approval_ref_001",
        status: "pending_review",
        riskLevel: "medium",
        dataClassification: "internal",
        actorSummary: "Local developer session summary",
        requestedActionSummary:
          "Preview-only policy review for a proposed local workspace change.",
        subjectSummary:
          "Mock local review subject; no file body or prompt body is shown.",
        reasonCodes: ["CONTROL_CENTER_REVIEW_REQUIRED"],
        createdAt: "2026-01-01T00:00:00Z",
        expiresAt: "2026-01-01T01:00:00Z",
        requiredNextAction: "Review in Python Agent Core approval authority.",
        safeMessage: "No approval was granted from this UI.",
        previewOutcomeSummary:
          "Grant or denial outcome is preview-only and non-authoritative.",
        relatedRefs: ["mock_receipt_ref_001", "mock_event_ref_001"],
        previewOnly: true,
        readOnly: true,
        mock: true,
      },
    ],
    receipts: [
      {
        receiptRef: "mock_receipt_ref_001",
        eventRefs: ["mock_event_ref_001"],
        actionTypeSummary: "approval_review_preview",
        actorSummary: "Local developer session summary",
        status: "recorded_summary",
        riskLevel: "medium",
        dataClassification: "internal",
        redactionStatus: "redacted_summary_only",
        safeMessage:
          "Receipt is a redacted summary; no receipt mutation is available from this UI.",
        timestamp: "2026-01-01T00:02:00Z",
        relatedRefs: ["mock_approval_ref_001"],
        previewOnly: true,
        readOnly: true,
        mock: true,
      },
    ],
    events: [
      {
        eventRef: "mock_event_ref_001",
        eventType: "approval_review_preview",
        actorSummary: "Local developer session summary",
        sourceSurface: "CCC Web mock surface",
        resultStatus: "summary_recorded",
        reasonCodes: ["CONTROL_CENTER_REVIEW_REQUIRED"],
        timestamp: "2026-01-01T00:02:00Z",
        relatedRefs: ["mock_approval_ref_001", "mock_receipt_ref_001"],
        redactionStatus: "redacted_summary_only",
        safeMessage: "No event action is available from this UI.",
        previewOnly: true,
        readOnly: true,
        mock: true,
      },
    ],
  },
  founderToday: {
    schema_version: "founder_loop_storage.v1",
    status: "storage_backed_partial_loop",
    surface: "Today",
    storage_ref: "founder-loop-storage:test",
    side_effect_class: "local_dev_workspace_only",
    approval_required_before_mutation: true,
    product_spine_contract_ref: "contract-ref:today-product-spine:v1",
    required_loop_surfaces: ["Today", "Actions", "Evidence", "Memory"],
    required_today_signals: [
      {
        signal: "priorities",
        source: "action_and_briefing_priority_fields",
        required: true,
      },
      {
        signal: "blockers",
        source: "blocked_states_and_missing_contract_refs",
        required: true,
      },
      {
        signal: "follow_ups",
        source: "next_safe_action_fields",
        required: true,
      },
      {
        signal: "plan_action_state",
        source: "plans_actions_and_approval_posture",
        required: true,
      },
      {
        signal: "memory_review_count",
        source: "sections.memory_review_count",
        required: true,
      },
      {
        signal: "stale_source_posture",
        source: "stale_state_fields",
        required: true,
      },
      {
        signal: "next_safe_actions",
        source: "next_safe_actions",
        required: true,
      },
    ],
    module_feed_contract: [
      {
        module: "Today",
        status: "implemented_storage_backed_partial_loop",
        required_loop_outputs: [
          "today_state",
          "action_state",
          "evidence_state",
          "memory_state",
        ],
        current_feed_refs: [
          "GET /control-center/today/summary",
          "evidence-ref:founder-loop:today-summary",
        ],
        standalone_complete_allowed: false,
      },
      {
        module: "Actions",
        status: "implemented_review_queue_execution_blocked",
        required_loop_outputs: [
          "today_priority_or_blocker",
          "action_envelope_or_blocked_state",
          "evidence_ref",
          "memory_review_or_blocked_state",
        ],
        current_feed_refs: [
          "GET /control-center/actions/inbox",
          "evidence-ref:founder-loop:action-inbox",
        ],
        standalone_complete_allowed: false,
      },
      {
        module: "Plans",
        status: "implemented_reviewable_action_envelope_contract",
        required_loop_outputs: [
          "today_plan_state",
          "action_envelope_or_blocked_state",
          "plan_evidence_ref",
          "memory_candidate_or_blocked_state",
        ],
        current_feed_refs: [
          "status-ref:founder-loop-plan-summary",
          "contract-ref:plans-action-envelope:v1",
        ],
        standalone_complete_allowed: false,
      },
      {
        module: "Memory",
        status:
          "implemented_review_queue_quality_intake_and_loop_binding_contract",
        required_loop_outputs: [
          "today_memory_review_count",
          "action_or_follow_up_candidate",
          "memory_evidence_ref",
          "reviewed_recall_or_blocked_state",
        ],
        current_feed_refs: [
          "status-ref:founder-loop-memory-review",
          "contract-ref:memory-review-decision:v1",
          "contract-ref:business-memory-quality-controls:v1",
          "contract-ref:cross-surface-memory-intake:v1",
          "contract-ref:memory-to-loop-binding:v1",
        ],
        standalone_complete_allowed: false,
      },
      {
        module: "Evidence",
        status: "implemented_redacted_history_grammar_contract_partial",
        required_loop_outputs: [
          "today_evidence_state",
          "action_receipt_or_blocked_state",
          "evidence_timeline_ref",
          "memory_evidence_or_blocked_state",
        ],
        current_feed_refs: [
          "GET /control-center/today/summary",
          "contract-ref:evidence-history-grammar:v1",
        ],
        standalone_complete_allowed: false,
      },
      {
        module: "Morning Briefing",
        status: "implemented_skeleton_source_contracts_missing",
        required_loop_outputs: [
          "today_priority_or_blocker",
          "follow_up_or_action_candidate",
          "source_readiness_evidence_ref",
          "memory_candidate_or_blocked_state",
        ],
        current_feed_refs: [
          "GET /control-center/morning-briefing/summary",
          "contract-ref:calendar-read-only-missing",
        ],
        standalone_complete_allowed: false,
      },
      {
        module: "Chat",
        status: "implemented_local_operator_surface_contract",
        required_loop_outputs: [
          "today_chat_state",
          "plan_or_action_handoff_state",
          "chat_evidence_ref",
          "memory_candidate_or_blocked_state",
        ],
        current_feed_refs: [
          "contract-ref:chat-local-operator-surface:v1",
          "/v1/chat/completions",
        ],
        standalone_complete_allowed: false,
      },
      {
        module: "Code",
        status: "implemented_governed_code_workbench_contract_apply_blocked",
        required_loop_outputs: [
          "today_code_state",
          "action_or_apply_blocked_state",
          "diff_validation_evidence_ref",
          "memory_candidate_or_blocked_state",
        ],
        current_feed_refs: ["contract-ref:governed-code-workbench:v1"],
        standalone_complete_allowed: false,
      },
    ],
    module_completion_contract: {
      visibility_requirement:
        "Module state must be visible in Today, Actions, Evidence, and Memory before completion can be claimed.",
      visibility_is_sufficient_for_completion: false,
      standalone_module_complete_allowed: false,
      required_done_gates: [
        "definition_of_done",
        "schema_or_typed_contract",
        "focused_tests",
        "redaction_checks",
        "policy_approval_boundary",
        "openapi_api_manifest_when_routes_change",
        "cli_or_repo_local_inspection_path",
      ],
    },
    business_memory_quality_contract_ref:
      "contract-ref:business-memory-quality-controls:v1",
    business_memory_candidate_kinds: [
      "profile",
      "project",
      "relationship",
      "organization",
      "deal",
      "opportunity",
      "promise",
      "follow_up",
      "preference",
      "decision",
      "commitment",
    ].map((candidateKind) => ({
      candidate_kind: candidateKind,
      candidate_kind_ref: `business-memory-kind:${candidateKind.replaceAll("_", "-")}`,
      review_required: true,
      safe_summary_only: true,
      source_refs_required: true,
      provenance_refs_required: true,
      evidence_refs_required: true,
      quality_posture_required: true,
      correction_path_required: true,
      retention_delete_export_posture_required: true,
      crm_write_authorized: false,
      account_sync_authorized: false,
      context_injection_authorized: false,
      accepted_as_recall: false,
    })),
    business_memory_quality_states: [
      "duplicate",
      "conflict",
      "stale_expired",
      "low_confidence",
      "source_missing",
      "evidence_missing",
      "blocked",
      "reviewed",
    ].map((qualityState) => ({
      quality_state: qualityState,
      quality_state_ref: `business-memory-quality:${qualityState.replaceAll("_", "-")}`,
      blocks_unreviewed_recall: true,
      requires_operator_review: true,
      requires_safe_refs: true,
      requires_correction_path: [
        "duplicate",
        "conflict",
        "stale_expired",
        "low_confidence",
      ].includes(qualityState),
      is_blocking_posture: qualityState !== "reviewed",
      authorizes_memory_write: false,
      authorizes_crm_write: false,
      authorizes_context_injection: false,
    })),
    business_memory_required_ref_fields: [
      "review_ref",
      "candidate_ref",
      "source_refs",
      "provenance_refs",
      "evidence_refs",
      "quality_state_refs",
      "related_entity_refs",
      "blocker_refs",
    ],
    business_memory_surface_bindings: [
      {
        surface: "Today",
        feed_status: "implemented_safe_ref_quality_summary",
        feed_ref: "today-ref:memory-review-business-quality",
        authority_boundary:
          "Quality posture can create blockers and follow-up refs only.",
      },
      {
        surface: "Action Inbox",
        feed_status: "implemented_follow_up_candidate_refs_only",
        feed_ref: "action-inbox-ref:memory-follow-up-candidates",
        authority_boundary:
          "Promises and follow-ups are review candidates, not execution tasks.",
      },
      {
        surface: "Evidence Timeline",
        feed_status: "implemented_history_refs_only",
        feed_ref: "evidence-ref:memory-business-quality-history",
        authority_boundary:
          "Quality changes must read as history with safe refs only.",
      },
      {
        surface: "Weekly CEO Review",
        feed_status: "implemented_carry_forward_refs_only",
        feed_ref: "weekly-review-ref:business-memory-carry-forward",
        authority_boundary:
          "Weekly review can carry decisions and blockers, not sync accounts.",
      },
    ],
    business_memory_authority_posture: {
      safe_refs_only: true,
      review_required_before_recall: true,
      memory_write_authorized: false,
      memory_delete_authorized: false,
      memory_export_authorized: false,
      automatic_memory_write_authorized: false,
      context_injection_authorized: false,
      external_crm_write_authorized: false,
      account_sync_authorized: false,
      connector_runtime_enabled: false,
      account_auth_enabled: false,
      provider_or_model_authority_allowed: false,
      source_truth_authority: false,
      accepted_as_recall: false,
      public_beta_claim_enabled: false,
      public_distribution_claim_enabled: false,
      production_authority_enabled: false,
    },
    business_memory_status:
      "implemented_review_queue_safe_ref_quality_metadata_contract",
    chat_local_operator_contract_ref:
      "contract-ref:chat-local-operator-surface:v1",
    chat_local_operator_status: "implemented_local_turn_truth_surface",
    chat_local_operator_turn_ref: "chat-turn:local-operator:local-chat-gateway",
    chat_local_operator_route_ref: "/v1/chat/completions",
    chat_local_operator_model_ref: "model-ref:local-chat-gateway",
    chat_local_operator_runtime_truth: "runtime-readiness-gated",
    chat_local_operator_auth_truth: "local-bearer-required",
    chat_local_operator_tool_denial_truth: "tools-functions-streaming-denied",
    chat_local_operator_tool_denial_ref:
      "tool-denial-ref:chat-local-operator:local-chat-gateway",
    chat_local_operator_safe_evidence_refs: [
      "evidence-ref:chat-local-operator:today",
    ],
    chat_local_operator_plans_handoff_ref:
      "handoff-ref:chat-to-plans:local-chat-gateway",
    chat_local_operator_actions_handoff_ref:
      "handoff-ref:chat-to-actions:local-chat-gateway",
    chat_local_operator_required_truth_fields: [
      "turn_ref",
      "route_ref",
      "model_ref",
      "runtime_truth",
      "auth_truth",
      "tool_denial_truth",
      "safe_evidence_refs",
      "plans_handoff_ref",
      "actions_handoff_ref",
      "blocked_state_refs",
    ],
    chat_local_operator_required_blocked_refs: [
      "blocked-state:no-model-output-authority",
      "blocked-state:no-tool-execution",
      "blocked-state:no-memory-write",
      "blocked-state:no-context-injection",
      "blocked-state:no-provider-sdk-call",
      "blocked-state:no-web-fetch",
      "blocked-state:no-connector-write",
      "blocked-state:no-shell-subprocess-execution",
      "blocked-state:no-action-execution",
      "blocked-state:no-approval-grant-capture",
      "blocked-state:no-production-authority",
    ],
    chat_local_operator_surface_bindings: [
      {
        surface: "Today",
        feed_status: "implemented_local_operator_turn_truth_refs",
        feed_ref: "contract-ref:chat-local-operator-surface:v1",
        authority_boundary: "Chat state is safe operator-turn metadata only.",
      },
    ],
    chat_local_operator_authority_posture: {
      safe_refs_only: true,
      response_visible: false,
      prompt_body_visible: false,
      completion_body_visible: false,
      model_output_authority: false,
      tool_execution_enabled: false,
      memory_write_authorized: false,
      context_injection_authorized: false,
      provider_sdk_call_enabled: false,
      web_fetch_enabled: false,
      connector_write_enabled: false,
      shell_subprocess_execution_enabled: false,
      action_execution_enabled: false,
      approval_grant_capture_enabled: false,
      production_authority_enabled: false,
    },
    chat_local_operator_blocked_state_refs: [
      "blocked-state:no-model-output-authority",
      "blocked-state:no-tool-execution",
      "blocked-state:no-memory-write",
      "blocked-state:no-context-injection",
      "blocked-state:no-provider-sdk-call",
      "blocked-state:no-web-fetch",
      "blocked-state:no-connector-write",
      "blocked-state:no-shell-subprocess-execution",
      "blocked-state:no-action-execution",
      "blocked-state:no-approval-grant-capture",
      "blocked-state:no-production-authority",
    ],
    chat_durable_receipt_contract_ref:
      "contract-ref:founder-loop-chat-durable-receipt:v1",
    chat_durable_receipt_route_refs: [
      "POST /control-center/chat/turns",
      "GET /control-center/chat/turns/{turn_ref}/receipt",
      "POST /control-center/chat/turns/{turn_ref}/handoff",
    ],
    chat_durable_receipt_status:
      "implemented_receipt_routes_ready_no_turn_recorded",
    chat_turn_receipt_refs: [],
    chat_handoff_receipt_refs: [],
    chat_handoff_created_refs: [],
    governed_code_workbench_contract_ref:
      "contract-ref:governed-code-workbench:v1",
    governed_code_workbench_status:
      "implemented_reviewable_repo_local_diff_contract_apply_blocked",
    governed_code_workbench_proposal_ref:
      "code-proposal:founder-loop-safe-diff",
    governed_code_workbench_repo_scope_ref:
      "repo-scope:governed-code:code-proposal-founder-loop-safe-diff",
    governed_code_workbench_safe_diff_summary_ref:
      "diff-summary-ref:governed-code:code-proposal-founder-loop-safe-diff",
    governed_code_workbench_validation_plan_ref:
      "validation-plan-ref:governed-code:code-proposal-founder-loop-safe-diff",
    governed_code_workbench_validation_result_refs: [
      "validation-result-ref:governed-code:not-run",
    ],
    governed_code_workbench_approval_requirement_ref:
      "approval-requirement:governed-code:code-proposal-founder-loop-safe-diff",
    governed_code_workbench_expected_apply_receipt_ref:
      "receipt-plan:governed-code-apply:code-proposal-founder-loop-safe-diff",
    governed_code_workbench_expected_rollback_receipt_ref:
      "rollback-receipt-plan:governed-code:code-proposal-founder-loop-safe-diff",
    governed_code_workbench_evidence_refs: ["evidence-ref:governed-code:today"],
    governed_code_workbench_idempotency_key_ref:
      "idempotency-ref:governed-code:code-proposal-founder-loop-safe-diff",
    governed_code_workbench_safe_summary:
      "Governed Code proposal records repo-local scope, safe diff summary, validation plan, approval requirement, expected apply receipt, and rollback receipt refs; apply remains blocked.",
    governed_code_workbench_validation_plan_summary:
      "Run focused tests and verifiers before any exact approval-bound apply.",
    governed_code_workbench_required_ref_fields: [
      "proposal_ref",
      "repo_scope_ref",
      "safe_diff_summary_ref",
      "validation_plan_ref",
      "validation_result_refs",
      "approval_requirement_ref",
      "expected_apply_receipt_ref",
      "expected_rollback_receipt_ref",
      "evidence_refs",
      "idempotency_key_ref",
      "blocked_state_refs",
    ],
    governed_code_workbench_required_blocked_refs: [
      "blocked-state:no-unapproved-mutation",
      "blocked-state:no-apply-execution",
      "blocked-state:no-approval-grant-capture",
      "blocked-state:no-unrestricted-shell",
      "blocked-state:no-shell-subprocess-execution",
      "blocked-state:no-remote-execution",
      "blocked-state:no-broad-coding-agent-autonomy",
      "blocked-state:no-provider-sdk-call",
      "blocked-state:no-web-fetch",
      "blocked-state:no-connector-write",
      "blocked-state:no-diff-body-storage",
      "blocked-state:no-production-authority",
    ],
    governed_code_workbench_surface_bindings: [
      {
        surface: "Today",
        feed_status: "implemented_governed_code_proposal_refs",
        feed_ref: "contract-ref:governed-code-workbench:v1",
        authority_boundary: "Code state is safe proposal metadata only.",
      },
    ],
    governed_code_workbench_authority_posture: {
      safe_refs_only: true,
      repo_local_scope_required: true,
      safe_diff_summary_only: true,
      validation_required_before_apply: true,
      approval_required_before_apply: true,
      atomic_apply_required: true,
      rollback_receipt_required: true,
      audit_required: true,
      redaction_required: true,
      apply_execution_enabled: false,
      approval_grant_capture_enabled: false,
      direct_file_write_enabled: false,
      unrestricted_shell_enabled: false,
      shell_subprocess_execution_enabled: false,
      remote_execution_enabled: false,
      broad_coding_agent_autonomy_enabled: false,
      provider_sdk_call_enabled: false,
      web_fetch_enabled: false,
      connector_write_enabled: false,
      diff_body_storage_enabled: false,
      production_authority_enabled: false,
    },
    governed_code_workbench_blocked_state_refs: [
      "blocked-state:no-unapproved-mutation",
      "blocked-state:no-apply-execution",
      "blocked-state:no-approval-grant-capture",
      "blocked-state:no-unrestricted-shell",
      "blocked-state:no-shell-subprocess-execution",
      "blocked-state:no-remote-execution",
      "blocked-state:no-broad-coding-agent-autonomy",
      "blocked-state:no-provider-sdk-call",
      "blocked-state:no-web-fetch",
      "blocked-state:no-connector-write",
      "blocked-state:no-diff-body-storage",
      "blocked-state:no-production-authority",
    ],
    plans_action_envelope_contract_ref: "contract-ref:plans-action-envelope:v1",
    plans_action_envelope_review_postures: [
      "approve",
      "edit",
      "reject",
      "defer",
    ].map((reviewAction) => ({
      review_action: reviewAction,
      review_posture_ref: `review-posture:plans-action-envelope:${reviewAction}`,
      exact_scope_required: true,
      safe_refs_required: true,
      receipt_refs_required: true,
      grants_execution_authority: false,
      captures_approval_grant: false,
    })),
    plans_action_envelope_required_ref_fields: [
      "action_envelope_ref",
      "source_plan_ref",
      "scope_ref",
      "side_effect_class",
      "risk_class",
      "approval_requirement_ref",
      "review_posture_refs",
      "evidence_refs",
      "expected_receipt_refs",
      "idempotency_key_ref",
      "expires_at",
      "rollback_ref",
      "safe_disable_ref",
      "blocked_state_refs",
    ],
    plans_action_envelope_required_blocked_refs: [
      "blocked-state:no-action-execution",
      "blocked-state:no-tool-execution",
      "blocked-state:no-workflow-execution",
      "blocked-state:no-approval-grant-capture",
      "blocked-state:approval-refs-identifiers-only",
      "blocked-state:no-connector-runtime",
      "blocked-state:no-connector-write",
      "blocked-state:no-browser-automation",
      "blocked-state:no-shell-subprocess-execution",
      "blocked-state:no-model-provider-authority",
      "blocked-state:no-public-beta-or-distribution",
      "blocked-state:no-production-authority",
    ],
    plans_action_envelope_surface_bindings: [
      {
        surface: "Today",
        feed_status: "implemented_plan_action_state_contract",
        feed_ref: "today-ref:plans-action-envelope-state",
        authority_boundary:
          "Today can show envelope posture but cannot execute actions.",
      },
    ],
    plans_action_envelope_authority_posture: {
      safe_refs_only: true,
      exact_scope_required: true,
      approval_required_before_mutation: true,
      approval_ref_authority: false,
      approval_grant_capture_enabled: false,
      action_execution_enabled: false,
      state_change_enabled: false,
      tool_execution_enabled: false,
      workflow_execution_enabled: false,
      browser_execution_enabled: false,
      connector_runtime_enabled: false,
      connector_write_enabled: false,
      shell_subprocess_execution_enabled: false,
      model_provider_authority_allowed: false,
      memory_write_authorized: false,
      context_injection_authorized: false,
      public_beta_claim_enabled: false,
      public_distribution_claim_enabled: false,
      production_authority_enabled: false,
    },
    plans_action_envelope_status:
      "implemented_today_to_action_envelope_vertical_slice_execution_blocked",
    priority_refs: [
      "priority-ref:action:high:founder-action-test",
      "priority-ref:briefing:medium:briefing-test",
    ],
    blocker_refs: [
      "blocked-state:no_action_execution_route",
      "blocked-state:no_connector_write_route",
      "blocked-state:no_runtime_model_call_route",
    ],
    follow_up_refs: [
      "follow-up-ref:actions:founder-action-test",
      "follow-up-ref:plans:plan-summary-test",
    ],
    plan_action_state: {
      action_count: 1,
      plan_count: 1,
      approval_required_before_mutation: true,
      mutating_controls_enabled: true,
      execution_authorized: false,
      action_envelope_contract_status:
        "implemented_today_promotion_and_action_decision_receipts_execution_blocked",
      action_envelope_contract_ref: "contract-ref:plans-action-envelope:v1",
      review_actions: ["approve", "edit", "reject", "defer"],
      approval_grant_capture_enabled: false,
      state_change_enabled: true,
    },
    stale_source_posture: {
      status: "recheck_required_before_action_or_source_use",
      source_refresh_enabled: false,
      connector_runtime_enabled: false,
      stale_state_refs: [
        "stale-ref:action:founder-action-test",
        "stale-ref:memory:memory-review-test",
      ],
    },
    next_safe_actions: [
      {
        surface: "Actions",
        source_ref: "founder-action:test",
        safe_summary:
          "Review refs only; request a scoped state-change milestone before mutation.",
      },
      {
        surface: "Plans",
        source_ref: "plan-summary:test",
        safe_summary: "Review route-backed summaries.",
      },
    ],
    sections: {
      action_inbox_count: 1,
      plan_count: 1,
      memory_review_count: 1,
      briefing_count: 1,
      evidence_timeline_count: 8,
    },
    actions: [
      {
        item_ref: "founder-action:test",
        title: "Storage-backed action",
        safe_summary: "Bounded action summary.",
        surface: "Actions",
        priority: "high",
        risk_class: "high",
        status: "review_ready",
        side_effect_class: "validation_only",
        authority_boundary:
          "Review-only display; Python Agent Core and LocalApprovalAuthority must validate exact scope before mutation.",
        approval_required: true,
        approval_envelope_ref: "approval-envelope:founder-loop:test",
        approval_envelope_status: "dry_run_ref_available",
        state_change_contract_ref: "contract-ref:founder-loop:test",
        state_change_readiness: "blocked_pending_scoped_mutation_contract",
        blocked_state: "Scoped backend contract required",
        evidence_refs: ["evidence-ref:founder-loop:test-action"],
        receipt_refs: ["receipt-plan:founder-loop:test"],
        audit_refs: ["audit-plan:founder-loop:test"],
        idempotency_key_ref: "idempotency-ref:founder-loop:test",
        expires_at: "review_required_before_mutation",
        stale_state: "recheck_action_summary_before_mutation",
        rollback_ref: "rollback-plan:founder-loop:test",
        safe_disable_ref: "safe-disable:founder-loop:test",
        action_envelope_contract_ref: "contract-ref:plans-action-envelope:v1",
        action_envelope_ref: "action-envelope:plans:founder-action-test",
        action_envelope_status: "review_ready_execution_blocked",
        action_envelope_safe_summary:
          "Action item is available as safe review metadata with exact-scope, receipt, idempotency, rollback, and safe-disable refs.",
        action_scope_ref: "scope-ref:plans-action-envelope:founder-action-test",
        action_approval_requirement_ref:
          "approval-requirement:plans-action-envelope:founder-action-test",
        action_review_actions: ["approve", "edit", "reject", "defer"],
        action_review_posture_refs: [
          "review-posture:plans-action-envelope:approve",
          "review-posture:plans-action-envelope:edit",
          "review-posture:plans-action-envelope:reject",
          "review-posture:plans-action-envelope:defer",
        ],
        action_expected_receipt_refs: ["receipt-plan:founder-loop:test"],
        action_idempotency_key_ref:
          "idempotency-ref:plans-action-envelope:founder-action-test",
        action_expires_at: "review_required_before_mutation",
        action_stale_state: "recheck_plan_and_action_refs_before_mutation",
        action_rollback_ref:
          "rollback-plan:plans-action-envelope:founder-action-test",
        action_safe_disable_ref:
          "safe-disable:plans-action-envelope:founder-action-test",
        action_blocked_state_refs: [
          "blocked-state:no-action-execution",
          "blocked-state:no-approval-grant-capture",
          "blocked-state:approval-refs-identifiers-only",
          "blocked-state:no-connector-write",
          "blocked-state:no-shell-subprocess-execution",
          "blocked-state:no-model-provider-authority",
          "blocked-state:no-public-beta-or-distribution",
          "blocked-state:no-production-authority",
        ],
        action_authority_boundary:
          "Reviewable Action envelope only; execution and approval grant capture remain blocked until exact scoped LocalApprovalAuthority validation exists.",
        action_exact_scope_required: true,
        action_envelope_approval_ref_authority: false,
        action_envelope_grant_capture_enabled: false,
        action_envelope_execution_enabled: false,
        action_envelope_connector_write_enabled: false,
        action_envelope_shell_execution_enabled: false,
        action_envelope_model_provider_authority_allowed: false,
        action_envelope_safe_refs_only: true,
        action_envelope_raw_content_included: false,
        next_safe_action:
          "Review refs only; request a scoped state-change milestone before mutation.",
      },
    ],
    plans: [
      {
        plan_ref: "plan-summary:test",
        title: "Founder Loop test plan",
        status: "partial_backend_not_product_ready",
        safe_summary: "Bounded plan summary.",
        next_step_summary: "Review route-backed summaries.",
        evidence_refs: ["evidence-ref:founder-loop:test-plan"],
        action_envelope_contract_ref: "contract-ref:plans-action-envelope:v1",
        action_envelope_ref: "action-envelope:plans:plan-summary-test",
        action_envelope_status: "review_ready_execution_blocked",
        action_envelope_safe_summary:
          "Plan summary has a reviewable Action envelope with exact-scope, receipt, idempotency, rollback, and safe-disable refs; execution remains blocked.",
        scope_ref: "scope-ref:plans-action-envelope:plan-summary-test",
        side_effect_class: "validation_only",
        risk_class: "medium",
        approval_required: true,
        approval_requirement_ref:
          "approval-requirement:plans-action-envelope:plan-summary-test",
        review_actions: ["approve", "edit", "reject", "defer"],
        review_posture_refs: [
          "review-posture:plans-action-envelope:approve",
          "review-posture:plans-action-envelope:edit",
          "review-posture:plans-action-envelope:reject",
          "review-posture:plans-action-envelope:defer",
        ],
        expected_receipt_refs: [
          "receipt-plan:plans-action-envelope:plan-summary-test",
        ],
        idempotency_key_ref:
          "idempotency-ref:plans-action-envelope:plan-summary-test",
        expires_at: "review_required_before_mutation",
        stale_state: "recheck_plan_and_action_refs_before_mutation",
        rollback_ref: "rollback-plan:plans-action-envelope:plan-summary-test",
        safe_disable_ref:
          "safe-disable:plans-action-envelope:plan-summary-test",
        blocked_state_refs: [
          "blocked-state:no-action-execution",
          "blocked-state:no-approval-grant-capture",
          "blocked-state:approval-refs-identifiers-only",
          "blocked-state:no-connector-write",
          "blocked-state:no-shell-subprocess-execution",
          "blocked-state:no-model-provider-authority",
          "blocked-state:no-public-beta-or-distribution",
          "blocked-state:no-production-authority",
        ],
        authority_boundary:
          "Reviewable Action envelope only; execution and approval grant capture remain blocked until exact scoped LocalApprovalAuthority validation exists.",
        exact_scope_required: true,
        approval_ref_authority: false,
        approval_grant_capture_enabled: false,
        action_execution_enabled: false,
        tool_execution_enabled: false,
        workflow_execution_enabled: false,
        browser_execution_enabled: false,
        connector_runtime_enabled: false,
        connector_write_enabled: false,
        shell_subprocess_execution_enabled: false,
        model_provider_authority_allowed: false,
        safe_refs_only: true,
        raw_content_included: false,
        plan_action_envelope_ref: "action-envelope:plans:plan-summary-test",
        plan_action_scope_ref:
          "scope-ref:plans-action-envelope:plan-summary-test",
        plan_action_approval_requirement_ref:
          "approval-requirement:plans-action-envelope:plan-summary-test",
        plan_action_review_posture_refs: [
          "review-posture:plans-action-envelope:approve",
          "review-posture:plans-action-envelope:edit",
          "review-posture:plans-action-envelope:reject",
          "review-posture:plans-action-envelope:defer",
        ],
        plan_action_expected_receipt_refs: [
          "receipt-plan:plans-action-envelope:plan-summary-test",
        ],
        plan_action_blocked_state_refs: [
          "blocked-state:no-action-execution",
          "blocked-state:no-approval-grant-capture",
        ],
        plan_action_authority_boundary:
          "Reviewable Action envelope only; execution and approval grant capture remain blocked until exact scoped LocalApprovalAuthority validation exists.",
      },
    ],
    memory_review_queue: [
      {
        review_ref: "memory-review:test",
        title: "Memory review",
        safe_summary: "Bounded memory summary.",
        candidate_kind: "preference",
        priority: "high",
        status: "review_needed",
        review_state: "review_needed",
        side_effect_class: "local_dev_workspace_only",
        authority_boundary:
          "Review-only memory candidate; recall is not truth, and writes, deletes, and context injection remain unscoped.",
        provenance_refs: ["provenance-ref:manual-note:test"],
        source_refs: ["source-ref:manual-note:test"],
        missing_contract_refs: [
          "contract-ref:memory-write-policy-binding-missing",
          "contract-ref:memory-retention-delete-missing",
          "contract-ref:context-injection-missing",
        ],
        correction_posture: "correction_requires_scoped_memory_write_contract",
        rejection_posture:
          "rejection_is_review_state_only_until_capture_contract",
        retention_posture: "retention_policy_not_bound",
        delete_posture: "delete_execution_not_scoped",
        confidence_posture: "safe_summary_unverified",
        stale_state: "recheck_source_refs_before_memory_use",
        blocked_states: [
          "no_memory_write",
          "no_context_injection",
          "no_memory_delete",
          "no_memory_export",
          "no_raw_source_display",
          "no_external_crm_write",
          "no_account_sync",
          "no_automatic_recall",
          "no_connector_write",
          "no_model_provider_authority",
          "no_background_sync",
        ],
        next_safe_action:
          "Review provenance and evidence refs; keep writes blocked until a scoped memory policy milestone.",
        evidence_refs: ["evidence-ref:founder-loop:test-memory"],
        source_policy_ref: "contract-ref:memory-source-provenance:v1",
        source_kind: "manual_note",
        source_kind_ref: "memory-source-kind:manual-note",
        source_refs_status: "safe_source_refs_present",
        provenance_refs_status: "safe_provenance_refs_present",
        source_review_required: true,
        source_trust_posture: "untrusted_until_reviewed",
        safe_summary_only: true,
        source_truth_authority: false,
        memory_write_authorized: false,
        automatic_memory_write_authorized: false,
        context_injection_authorized: false,
        account_auth_enabled: false,
        public_beta_claim_enabled: false,
        public_distribution_claim_enabled: false,
        production_authority_enabled: false,
        source_payload_storage_allowed: false,
        prompt_body_storage_allowed: false,
        response_body_storage_allowed: false,
        provider_body_storage_allowed: false,
        path_body_storage_allowed: false,
        log_body_storage_allowed: false,
        account_ref_storage_allowed: false,
        private_content_storage_allowed: false,
        connector_runtime_allowed: false,
        provider_or_model_authority_allowed: false,
        accepted_as_truth: false,
        decision_contract_ref: "contract-ref:memory-review-decision:v1",
        available_decision_states: [
          "accept",
          "correct",
          "reject",
          "defer",
          "merge",
          "supersede",
          "forget_request",
        ],
        decision_capture_status: "review_needed_no_decision_captured",
        decision_required_ref_fields: [
          "actor_ref",
          "source_refs",
          "provenance_refs",
          "evidence_refs",
          "stale_state",
          "retention_posture",
          "audit_refs",
          "receipt_refs",
          "blocked_state_refs",
        ],
        decision_actor_ref: "actor-ref:local-operator-review-required",
        decision_source_provenance_contract_ref:
          "contract-ref:memory-source-provenance:v1",
        decision_source_kind: "manual_note",
        decision_source_trust_posture: "untrusted_until_reviewed",
        decision_redaction_status: "redacted_summary_only",
        decision_audit_refs: ["audit-plan:memory-review:test"],
        decision_receipt_refs: ["receipt-plan:memory-review:test"],
        decision_blocked_state_refs: [
          "blocked-state:no-memory-write",
          "blocked-state:no-memory-delete",
          "blocked-state:no-memory-export",
          "blocked-state:no-context-injection",
          "blocked-state:no-connector-runtime",
          "blocked-state:no-account-auth",
          "blocked-state:no-model-provider-authority",
          "blocked-state:no-public-beta-or-production-authority",
        ],
        decision_stale_state: "recheck_source_refs_before_memory_use",
        decision_retention_posture: "retention_policy_not_bound",
        decision_correction_posture:
          "correction_requires_scoped_memory_write_contract",
        decision_authority_boundary:
          "Memory review decisions are review metadata only; writes, deletes, exports, context injection, connector runtime, account auth, and production authority remain unscoped.",
        decision_review_only: true,
        memory_delete_authorized: false,
        memory_export_authorized: false,
        retention_execution_authorized: false,
        business_memory_quality_contract_ref:
          "contract-ref:business-memory-quality-controls:v1",
        business_memory_candidate_ref:
          "business-memory-candidate:preference:memory-review-test",
        business_memory_candidate_kind: "preference",
        business_memory_candidate_kind_ref: "business-memory-kind:preference",
        business_memory_source_provenance_contract_ref:
          "contract-ref:memory-source-provenance:v1",
        business_memory_source_kind: "manual_note",
        business_memory_source_trust_posture: "untrusted_until_reviewed",
        business_memory_redaction_status: "redacted_summary_only",
        business_memory_quality_state_refs: [
          "business-memory-quality:blocked",
          "business-memory-quality:low-confidence",
        ],
        business_memory_quality_posture: "review_required_quality_blocked",
        business_memory_review_state: "review_needed",
        business_memory_correction_path:
          "correction_requires_scoped_memory_write_contract",
        business_memory_stale_state: "recheck_source_refs_before_memory_use",
        business_memory_retention_posture: "retention_policy_not_bound",
        business_memory_delete_posture: "delete_execution_not_scoped",
        business_memory_export_posture: "export_execution_not_scoped",
        business_memory_related_entity_refs: [
          "business-memory-entity:preference:memory-review-test",
        ],
        business_memory_duplicate_of_refs: [],
        business_memory_conflict_with_refs: [],
        business_memory_blocker_refs: [
          "blocked-state:no-memory-write",
          "blocked-state:no-memory-delete",
          "blocked-state:no-memory-export",
          "blocked-state:no-context-injection",
          "blocked-state:no-external-crm-write",
          "blocked-state:no-account-sync",
          "blocked-state:no-automatic-recall",
          "blocked-state:no-connector-runtime",
          "blocked-state:no-account-auth",
          "blocked-state:no-model-provider-authority",
          "blocked-state:no-source-truth-authority",
          "blocked-state:no-raw-source-display",
          "blocked-state:no-public-beta-or-distribution",
          "blocked-state:no-production-authority",
        ],
        business_memory_surface_refs: [
          "today-ref:memory-review-business-quality",
          "action-inbox-ref:memory-follow-up-candidates",
          "evidence-ref:memory-business-quality-history",
          "weekly-review-ref:business-memory-carry-forward",
        ],
        business_memory_next_safe_action:
          "Review quality posture and safe refs; keep memory writes, CRM sync, and context injection blocked until scoped policy milestones exist.",
        business_memory_safe_refs_only: true,
        business_memory_review_required_before_recall: true,
        business_memory_accepted_as_recall: false,
        business_memory_write_authorized: false,
        business_memory_delete_authorized: false,
        business_memory_export_authorized: false,
        business_memory_crm_write_authorized: false,
        business_memory_account_sync_authorized: false,
        business_memory_context_injection_authorized: false,
        business_memory_authority_boundary:
          "Business memory quality is review metadata only; external CRM writes, account sync, automatic recall, memory mutation, and context injection remain unscoped.",
      },
    ],
    memory_review_route_ref: "/memory",
    memory_review_backend_route_ref: "GET /control-center/today/summary",
    memory_review_status:
      "storage_backed_review_queue_with_business_quality_and_loop_binding_metadata",
    memory_review_authority_boundary:
      "Review-only memory candidates; recall is not truth, and writes, deletes, context injection, connector writes, model/provider calls, and background sync are unscoped.",
    memory_write_enabled: false,
    memory_delete_enabled: false,
    context_injection_enabled: false,
    memory_review_missing_contract_refs: [
      "contract-ref:memory-write-policy-binding-missing",
      "contract-ref:memory-retention-delete-missing",
      "contract-ref:context-injection-missing",
    ],
    memory_review_blocked_states: [
      "no_memory_write",
      "no_context_injection",
      "no_memory_delete",
      "no_memory_export",
      "no_raw_source_display",
      "no_external_crm_write",
      "no_account_sync",
      "no_automatic_recall",
      "no_connector_write",
      "no_model_provider_authority",
      "no_background_sync",
    ],
    briefing_items: [
      {
        briefing_ref: "briefing:test",
        title: "Briefing item",
        safe_summary: "Bounded briefing summary.",
        priority: "high",
        status: "active",
        side_effect_class: "local_dev_workspace_only",
        authority_boundary:
          "Review-only briefing summary; source reads and delivery remain unscoped.",
        source_readiness: "local_status_refs_only",
        source_refs: ["source-ref:control-center-route-status"],
        missing_contract_refs: [
          "contract-ref:email-read-only-missing",
          "contract-ref:calendar-read-only-missing",
          "contract-ref:notification-delivery-missing",
        ],
        blocked_states: [
          "no_email_calendar_source_contract",
          "no_background_refresh",
        ],
        stale_state: "recheck_route_status_before_briefing_use",
        evidence_gap:
          "No email, calendar, or notification source evidence is bound.",
        next_safe_action:
          "Use route and storage refs only; define source contracts before refresh.",
        evidence_refs: ["evidence-ref:founder-loop:test-briefing"],
      },
    ],
    evidence_timeline: [
      {
        timeline_item_ref: "evidence-timeline:action/founder-action/test",
        item_kind: "receipt_audit_rollback_ref",
        title: "Storage-backed action",
        safe_summary:
          "Action evidence is shown as receipt, audit, idempotency, rollback, and safe-disable refs only; mutation stays blocked.",
        source_refs: ["founder-action:test"],
        status_refs: ["status-ref:founder-loop-action-inbox"],
        related_route_refs: ["GET /control-center/actions/inbox", "/actions"],
        side_effect_class: "validation_only",
        authority_posture:
          "Review-only display; Python Agent Core and LocalApprovalAuthority must validate exact scope before mutation.",
        approval_posture: "dry_run_ref_available",
        receipt_refs: ["receipt-plan:founder-loop:test"],
        audit_refs: ["audit-plan:founder-loop:test"],
        replay_refs: ["replay-ref:founder-loop:action-inbox"],
        rollback_refs: ["rollback-plan:founder-loop:test"],
        rollback_blockers: [],
        latency_refs: [],
        foundation_gate_refs: [],
        redaction_status: "redacted_summary_only",
        stale_state: "recheck_action_summary_before_mutation",
        missing_evidence_posture: "receipt_refs_available",
        blocked_states: [
          "blocked_pending_scoped_mutation_contract",
          "approval_refs_are_identifiers_only",
        ],
        next_safe_action:
          "Review refs only; request a scoped state-change milestone before mutation.",
      },
      {
        timeline_item_ref: "evidence-timeline:plan/plan-summary/test",
        item_kind: "plan_action_envelope_ref",
        title: "Founder Loop test plan",
        safe_summary:
          "Plan evidence includes a reviewable Action envelope ref with exact scope, expected receipts, idempotency, rollback, and safe-disable posture; execution remains blocked.",
        source_refs: ["plan-summary:test"],
        status_refs: [
          "status-ref:founder-loop-plan-summary",
          "contract-ref:plans-action-envelope:v1",
          "action-envelope:plans:plan-summary-test",
        ],
        related_route_refs: ["/plans", "/task-decomposition/status"],
        side_effect_class: "validation_only",
        authority_posture:
          "Reviewable Action envelope only; execution and approval grant capture remain blocked until exact scoped LocalApprovalAuthority validation exists.",
        approval_posture:
          "approval-requirement:plans-action-envelope:plan-summary-test",
        receipt_refs: ["receipt-plan:plans-action-envelope:plan-summary-test"],
        audit_refs: [],
        replay_refs: ["replay-ref:founder-loop:plan-summary"],
        rollback_refs: [
          "rollback-plan:plans-action-envelope:plan-summary-test",
        ],
        rollback_blockers: ["rollback_execution_not_scoped"],
        latency_refs: [],
        foundation_gate_refs: [],
        redaction_status: "redacted_summary_only",
        stale_state: "recheck_plan_and_action_refs_before_mutation",
        missing_evidence_posture:
          "execution_receipt_missing_until_scoped_action_contract",
        blocked_states: [
          "blocked-state:no-action-execution",
          "blocked-state:no-approval-grant-capture",
          "blocked-state:approval-refs-identifiers-only",
          "blocked-state:no-connector-write",
          "blocked-state:no-shell-subprocess-execution",
          "blocked-state:no-model-provider-authority",
          "blocked-state:no-public-beta-or-distribution",
          "blocked-state:no-production-authority",
        ],
        next_safe_action: "Review route-backed summaries.",
      },
      {
        timeline_item_ref: "evidence-timeline:memory/memory-review/test",
        item_kind: "memory_review_evidence_ref",
        title: "Memory review",
        safe_summary:
          "Memory evidence is recall metadata only. Memory is not truth, not approval, and not context-injection authority.",
        source_refs: ["memory-review:test", "source-ref:manual-note:test"],
        status_refs: [
          "status-ref:founder-loop-memory-review",
          "contract-ref:memory-write-policy-binding-missing",
          "contract-ref:memory-retention-delete-missing",
          "contract-ref:business-memory-quality-controls:v1",
          "contract-ref:context-injection-missing",
        ],
        related_route_refs: ["GET /control-center/today/summary", "/memory"],
        side_effect_class: "local_dev_workspace_only",
        authority_posture:
          "Review-only memory candidate; recall is not truth, and writes, deletes, and context injection remain unscoped.",
        approval_posture: "memory_review_refs_do_not_authorize_writes",
        receipt_refs: [],
        audit_refs: [],
        replay_refs: ["replay-ref:founder-loop:memory-review"],
        rollback_refs: [],
        rollback_blockers: ["memory_write_or_delete_rollback_not_scoped"],
        latency_refs: [],
        foundation_gate_refs: [],
        redaction_status: "redacted_summary_only",
        stale_state: "recheck_source_refs_before_memory_use",
        missing_evidence_posture:
          "memory_contract_refs_missing_until_scoped_review_contracts",
        blocked_states: [
          "no_memory_write",
          "no_context_injection",
          "no_memory_delete",
        ],
        next_safe_action:
          "Review provenance and evidence refs; keep writes blocked until a scoped memory policy milestone.",
      },
      {
        timeline_item_ref: "evidence-timeline:briefing/briefing/test",
        item_kind: "source_readiness_evidence_ref",
        title: "Briefing item",
        safe_summary:
          "Briefing evidence is source-readiness posture only. Email, calendar, connector, refresh, and notification runtime stay blocked.",
        source_refs: [
          "briefing:test",
          "source-ref:control-center-route-status",
        ],
        status_refs: [
          "evidence-timeline:briefing-status/local_status_refs_only",
        ],
        related_route_refs: [
          "GET /control-center/morning-briefing/summary",
          "/briefing",
        ],
        side_effect_class: "local_dev_workspace_only",
        authority_posture:
          "Review-only briefing summary; source reads and delivery remain unscoped.",
        approval_posture: "source_refs_do_not_authorize_connector_runtime",
        receipt_refs: [],
        audit_refs: [],
        replay_refs: ["replay-ref:founder-loop:morning-briefing"],
        rollback_refs: [],
        rollback_blockers: ["source_refresh_rollback_not_scoped"],
        latency_refs: [],
        foundation_gate_refs: [],
        redaction_status: "redacted_summary_only",
        stale_state: "recheck_route_status_before_briefing_use",
        missing_evidence_posture:
          "missing_source_contract_refs_until_read_only_runtime_milestone",
        blocked_states: [
          "no_email_calendar_source_contract",
          "no_background_refresh",
        ],
        next_safe_action:
          "Use route and storage refs only; define source contracts before refresh.",
      },
      {
        timeline_item_ref: "evidence-timeline:foundation-gate/latency",
        item_kind: "foundation_gate_latency_ref",
        title: "Foundation Gate and latency posture",
        safe_summary:
          "Foundation Gate and latency refs are status evidence only; they do not grant production authority or runtime authority.",
        source_refs: ["status-ref:foundation-gate-summary"],
        status_refs: ["status-ref:foundation-gate-report"],
        related_route_refs: [
          "GET /control-center/foundation-gate/summary",
          "/foundation-gate",
        ],
        side_effect_class: "validation_only",
        authority_posture:
          "Foundation Gate status and latency measurements are evidence, not production authority.",
        approval_posture: "approval_refs_are_identifiers_only_not_authority",
        receipt_refs: [],
        audit_refs: ["audit-ref:foundation-gate:latest"],
        replay_refs: ["replay-ref:foundation-gate:latest"],
        rollback_refs: [],
        rollback_blockers: ["rollback_execution_not_scoped"],
        latency_refs: [
          "latency-ref:foundation-gate:latest-report",
          "performance-ref:release-latency-baseline",
        ],
        foundation_gate_refs: ["foundation-gate-ref:latest-report"],
        redaction_status: "safe_refs_only",
        stale_state: "recheck_foundation_gate_report_before_release_claim",
        missing_evidence_posture:
          "release_evidence_packet_missing_until_scoped_release",
        blocked_states: [
          "foundation_gate_refs_not_production_authority",
          "latency_refs_not_authority",
          "no_release_authority",
        ],
        next_safe_action:
          "Inspect Foundation Gate and latency refs; keep production claims blocked until release evidence is scoped.",
      },
    ],
    evidence_timeline_route_ref: "/evidence",
    evidence_timeline_backend_route_ref:
      "GET /control-center/evidence/timeline",
    evidence_timeline_status:
      "implemented_productized_evidence_timeline_safe_refs_only",
    evidence_timeline_authority_boundary:
      "Evidence Timeline is safe-ref and redacted-summary only. It does not expose private content, grant approval, perform rollback, or confer production authority.",
    evidence_timeline_blocked_states: [
      "no_raw_evidence_display",
      "no_rollback_execution",
      "approval_refs_are_identifiers_only",
      "foundation_gate_refs_not_production_authority",
      "latency_refs_not_authority",
      "connector_source_runtime_blocked",
    ],
    evidence_refs: ["evidence-ref:founder-loop:test-today"],
    blocked_states: ["no_action_execution_route"],
  },
  founderActionsInbox: {
    schema_version: "founder_loop_storage.v1",
    status: "storage_backed_review_queue",
    surface: "Actions",
    storage_ref: "founder-loop-storage:test",
    side_effect_class: "local_dev_workspace_only",
    route_ref: "/control-center/actions/inbox",
    read_only_route_refs: [
      "GET /control-center/actions/inbox",
      "GET /control-center/storage/status",
      "GET /control-center/routes",
      "GET /control-center/runtime-readiness/summary",
      "GET /control-center/foundation-gate/summary",
    ],
    local_prerequisite_refs: [
      "status-ref:founder-loop-storage",
      "status-ref:control-center-route-manifest",
      "capability-ref:local-approval-authority",
    ],
    items: [
      {
        item_ref: "founder-action:mock-local-task-create",
        title: "Operational maturity scorecard task",
        safe_summary:
          "Create local task state for keeping the operational maturity scorecard current.",
        surface: "Actions",
        priority: "high",
        risk_class: "medium",
        action_kind: "local_task_create",
        status: "approved",
        side_effect_class: "local_dev_workspace_only",
        authority_boundary:
          "Exact local-task create lane only; external authority remains blocked.",
        approval_required: true,
        approval_envelope_ref:
          "approval-envelope:founder-loop:mock-local-task-create",
        approval_envelope_status: "approved_receipt_recorded",
        state_change_contract_ref:
          "contract-ref:founder-loop-local-task-commit:v1",
        state_change_readiness: "local_task_commit_contract_requires_commit",
        blocked_state:
          "Only local task creation is available; all external authority remains blocked.",
        evidence_refs: ["evidence-ref:founder-loop:local-task-commit"],
        receipt_refs: [
          "receipt:founder-loop-action:mock-local-task-create:approve",
        ],
        audit_refs: [
          "audit:founder-loop-action:mock-local-task-create:approve",
        ],
        idempotency_key_ref:
          "idempotency-ref:founder-loop:mock-local-task-create",
        expires_at: "review_required_before_local_task_commit",
        stale_state: "recheck_action_approval_before_local_task_commit",
        rollback_ref: "rollback-not-applicable:local-task-safe-disable",
        safe_disable_ref: "safe-disable:founder-loop:mock-local-task-create",
        action_envelope_contract_ref: "contract-ref:plans-action-envelope:v1",
        action_envelope_ref:
          "action-envelope:plans:founder-action-mock-local-task-create",
        action_envelope_status: "approved_receipt_recorded",
        action_scope_ref:
          "scope-ref:plans-action-envelope:founder-action-mock-local-task-create",
        action_approval_requirement_ref:
          "approval-requirement:plans-action-envelope:founder-action-mock-local-task-create",
        action_review_actions: ["approve", "edit", "reject", "defer"],
        action_expected_receipt_refs: [
          "receipt-plan:founder-loop:mock-local-task-create",
        ],
        action_blocked_state_refs: [
          "blocked-state:no-connector-write",
          "blocked-state:no-shell-subprocess-execution",
          "blocked-state:no-model-provider-authority",
          "blocked-state:no-memory-write",
          "blocked-state:no-context-injection",
          "blocked-state:no-production-authority",
        ],
        action_envelope_execution_enabled: false,
        action_envelope_grant_capture_enabled: false,
        action_envelope_raw_content_included: false,
        local_task_commit_contract_ref:
          "contract-ref:founder-loop-local-task-commit:v1",
        local_task_commit_route_ref:
          "POST /control-center/actions/{action_id}/local-task/commit",
        local_task_ref: "local-task:founder-action:mock-local-task-create",
        local_task_commit_approval_ref:
          "approval-ref:mock-local-task-action-approve",
        local_task_commit_approval_status: "backend_owned_approval_ready",
        local_task_commit_eligible: true,
        local_task_commit_receipt_ref: null,
        local_task_commit_blocked_reasons: [],
        local_task_commit_next_safe_action:
          "Commit this approved local task through the exact local-task route.",
        local_task_commit_external_authority_blocked_refs: [
          "blocked-state:no-connector-write",
          "blocked-state:no-shell-subprocess-execution",
          "blocked-state:no-model-provider-authority",
          "blocked-state:no-memory-write",
          "blocked-state:no-context-injection",
          "blocked-state:no-external-side-effect",
          "blocked-state:no-production-authority",
        ],
        local_task_safe_disable_posture: {
          schema_version: "founder_loop_local_task_safe_disable_posture.v1",
          source: "python_core_founder_loop_storage",
          backend_owned: true,
          lane_id: "local_task_create",
          action_kind: "local_task_create",
          local_task_commits_enabled: true,
          safe_disable_active: false,
          safe_disable_ref: "safe-disable:founder-loop:mock-local-task-create",
          rollback_ref: "rollback-not-applicable:local-task-safe-disable",
          safe_disable_posture_ref:
            "safe-disable-posture:founder-loop:local-task-create",
          disabled_reason_refs: [],
          blocked_state_refs: [
            "blocked-state:no-connector-write",
            "blocked-state:no-shell-subprocess-execution",
            "blocked-state:no-model-provider-authority",
            "blocked-state:no-memory-write",
            "blocked-state:no-context-injection",
            "blocked-state:no-external-side-effect",
            "blocked-state:no-production-authority",
          ],
          rollback_execution_enabled: false,
          rollback_blocker_refs: [
            "blocked-state:local-task-rollback-execution-not-scoped",
          ],
          next_safe_action:
            "Commit exact-scoped approved local tasks through the local-task route.",
          updated_at: "2026-06-22T00:00:00Z",
        },
        local_task_safe_disable_ref:
          "safe-disable:founder-loop:mock-local-task-create",
        local_task_safe_disable_active: false,
        local_task_safe_disable_posture_ref:
          "safe-disable-posture:founder-loop:local-task-create",
        local_task_rollback_ref:
          "rollback-not-applicable:local-task-safe-disable",
        local_task_rollback_execution_enabled: false,
        local_task_rollback_blocker_refs: [
          "blocked-state:local-task-rollback-execution-not-scoped",
        ],
        approval_envelope: {
          schema_version: "founder_loop_action_approval_envelope.v1",
          contract_ref: "contract-ref:founder-loop-action-approval-envelope:v1",
          source: "python_core_action_inbox_read_model",
          backend_owned: true,
          action_kind: "local_task_create",
          exact_scope:
            "scope-ref:plans-action-envelope:founder-action-mock-local-task-create",
          risk_class: "medium",
          side_effect_class: "local_dev_workspace_only",
          approval_requirement:
            "approval-requirement:plans-action-envelope:founder-action-mock-local-task-create",
          expiry_or_staleness:
            "review_required_before_local_task_commit; recheck_action_approval_before_local_task_commit",
          idempotency_ref:
            "idempotency-ref:founder-loop:mock-local-task-create",
          expected_receipt_refs: [
            "receipt-plan:founder-loop:mock-local-task-create",
          ],
          rollback_safe_disable_posture:
            "rollback-not-applicable:local-task-safe-disable; safe-disable:founder-loop:mock-local-task-create",
          blocked_authority_refs: [
            "blocked-state:no-connector-write",
            "blocked-state:no-shell-subprocess-execution",
            "blocked-state:no-model-provider-authority",
            "blocked-state:no-memory-write",
            "blocked-state:no-context-injection",
            "blocked-state:no-external-side-effect",
            "blocked-state:no-production-authority",
          ],
          evidence_refs: ["evidence-ref:founder-loop:local-task-commit"],
          missing_field_states: ["none"],
        },
        receipt_visibility: {
          schema_version: "founder_loop_action_receipt_visibility.v1",
          contract_ref:
            "contract-ref:founder-loop-action-receipt-visibility:v1",
          source: "python_core_action_inbox_read_model",
          backend_owned: true,
          decision_receipt_ref:
            "receipt:founder-loop-action:mock-local-task-create:approve",
          local_task_ref: "pending",
          local_task_commit_receipt_ref: "pending",
          evidence_timeline_event_ref:
            "evidence-event:action-decision-recorded-evidence-timeline-action-founder-action-mock-local-task-create",
          replay_posture: "decision_idempotency_replay_available",
          conflict_posture: "decision_conflicting_idempotency_payload_rejected",
          missing_field_states: [
            "local_task_ref:pending",
            "local_task_commit_receipt_ref:pending",
          ],
        },
        action_group_id: "approved_local_task_lane",
        action_group_label: "Approved local-task create lane",
        action_group_reason:
          "Exact backend approval is recorded and the typed local-task commit lane is eligible.",
        action_group_available_action:
          "Inspect approval posture or commit the local-task create lane.",
        next_safe_action:
          "Commit this approved local task or inspect its blocked external authority refs.",
      },
      {
        item_ref: "founder-action:test",
        title: "Storage-backed action",
        safe_summary: "Bounded action summary.",
        surface: "Actions",
        priority: "high",
        risk_class: "high",
        status: "review_ready",
        side_effect_class: "validation_only",
        authority_boundary:
          "Review-only display; Python Agent Core and LocalApprovalAuthority must validate exact scope before mutation.",
        approval_required: true,
        approval_envelope_ref: "approval-envelope:founder-loop:test",
        approval_envelope_status: "dry_run_ref_available",
        state_change_contract_ref: "contract-ref:founder-loop:test",
        state_change_readiness: "blocked_pending_scoped_mutation_contract",
        blocked_state: "Scoped backend contract required",
        evidence_refs: ["evidence-ref:founder-loop:test-action"],
        receipt_refs: ["receipt-plan:founder-loop:test"],
        audit_refs: ["audit-plan:founder-loop:test"],
        idempotency_key_ref: "idempotency-ref:founder-loop:test",
        expires_at: "review_required_before_mutation",
        stale_state: "recheck_action_summary_before_mutation",
        rollback_ref: "rollback-plan:founder-loop:test",
        safe_disable_ref: "safe-disable:founder-loop:test",
        approval_envelope: {
          schema_version: "founder_loop_action_approval_envelope.v1",
          contract_ref: "contract-ref:founder-loop-action-approval-envelope:v1",
          source: "python_core_action_inbox_read_model",
          backend_owned: true,
          action_kind: "review_only",
          exact_scope: "missing",
          risk_class: "high",
          side_effect_class: "validation_only",
          approval_requirement: "missing",
          expiry_or_staleness:
            "review_required_before_mutation; recheck_action_summary_before_mutation",
          idempotency_ref: "idempotency-ref:founder-loop:test",
          expected_receipt_refs: ["receipt-plan:founder-loop:test"],
          rollback_safe_disable_posture:
            "rollback-plan:founder-loop:test; safe-disable:founder-loop:test",
          blocked_authority_refs: ["blocked-state:state-change-blocked"],
          evidence_refs: ["evidence-ref:founder-loop:test-action"],
          missing_field_states: [
            "exact_scope:missing",
            "approval_requirement:missing",
          ],
        },
        receipt_visibility: {
          schema_version: "founder_loop_action_receipt_visibility.v1",
          contract_ref:
            "contract-ref:founder-loop-action-receipt-visibility:v1",
          source: "python_core_action_inbox_read_model",
          backend_owned: true,
          decision_receipt_ref: "pending",
          local_task_ref: "not_applicable",
          local_task_commit_receipt_ref: "not_applicable",
          evidence_timeline_event_ref: "pending",
          replay_posture: "pending",
          conflict_posture: "pending",
          missing_field_states: [
            "decision_receipt_ref:pending",
            "evidence_timeline_event_ref:pending",
            "replay_posture:pending",
            "conflict_posture:pending",
          ],
        },
        next_safe_action:
          "Review refs only; request a scoped state-change milestone before mutation.",
      },
    ],
    approval_required_before_mutation: true,
    mutating_controls_enabled: true,
    action_execution_enabled: false,
    decision_route_refs: [
      "POST /control-center/actions/{action_id}/approve",
      "POST /control-center/actions/{action_id}/edit",
      "POST /control-center/actions/{action_id}/reject",
      "POST /control-center/actions/{action_id}/defer",
      "GET /control-center/actions/{action_id}/receipt",
    ],
    decision_state_contract_ref:
      "contract-ref:founder-loop-action-state-machine:v1",
    decision_statuses: [
      "proposed",
      "approved",
      "edited",
      "rejected",
      "deferred",
      "expired",
      "receipt_recorded",
      "blocked",
    ],
    decision_actions: ["approve", "edit", "reject", "defer"],
    decision_receipts_required: true,
    idempotency_replay_enabled: true,
    idempotency_conflict_rejected: true,
    disabled_state_label: "Action execution remains blocked",
    evidence_refs: ["evidence-ref:founder-loop:test-inbox"],
    blocked_states: [
      "no_action_execution_route",
      "approval_ref_must_validate_exact_scope",
      "no_memory_write",
      "no_context_injection",
    ],
  },
  founderMorningBriefing: {
    schema_version: "founder_loop_storage.v1",
    status: "storage_backed_briefing_skeleton",
    surface: "Morning Briefing",
    storage_ref: "founder-loop-storage:test",
    side_effect_class: "local_dev_workspace_only",
    route_ref: "/control-center/morning-briefing/summary",
    read_only_route_refs: [
      "GET /control-center/morning-briefing/summary",
      "GET /control-center/storage/status",
      "GET /control-center/routes",
      "GET /control-center/runtime-readiness/summary",
      "GET /control-center/foundation-gate/summary",
    ],
    local_prerequisite_refs: [
      "status-ref:founder-loop-storage",
      "status-ref:control-center-route-manifest",
      "contract-ref:email-read-only-missing",
      "contract-ref:calendar-read-only-missing",
      "contract-ref:notification-delivery-missing",
    ],
    source_readiness: "blocked_missing_email_calendar_notification_contracts",
    authority_boundary:
      "Read-only briefing summary; no email, calendar, connector, refresh, notification, model, memory, or delivery authority.",
    bounded_preview_only: true,
    refresh_enabled: false,
    notification_delivery_enabled: false,
    missing_contract_refs: [
      "contract-ref:email-read-only-missing",
      "contract-ref:calendar-read-only-missing",
      "contract-ref:notification-delivery-missing",
    ],
    items: [
      {
        briefing_ref: "briefing:test",
        title: "Briefing item",
        safe_summary: "Bounded briefing summary.",
        priority: "high",
        status: "active",
        side_effect_class: "local_dev_workspace_only",
        authority_boundary:
          "Review-only briefing summary; source reads and delivery remain unscoped.",
        source_readiness: "local_status_refs_only",
        source_refs: ["source-ref:control-center-route-status"],
        missing_contract_refs: [
          "contract-ref:email-read-only-missing",
          "contract-ref:calendar-read-only-missing",
          "contract-ref:notification-delivery-missing",
        ],
        blocked_states: [
          "no_email_calendar_source_contract",
          "no_background_refresh",
        ],
        stale_state: "recheck_route_status_before_briefing_use",
        evidence_gap:
          "No email, calendar, or notification source evidence is bound.",
        next_safe_action:
          "Use route and storage refs only; define source contracts before refresh.",
        evidence_refs: ["evidence-ref:founder-loop:test-briefing"],
      },
    ],
    evidence_refs: ["evidence-ref:founder-loop:test-briefing"],
    blocked_states: [
      "no_email_read_authority",
      "no_calendar_read_authority",
      "no_connector_runtime",
      "no_background_refresh",
      "no_notification_delivery",
    ],
  },
  founderStorageStatus: {
    schema_version: "founder_loop_storage.v1",
    migration_version: "founder_loop_storage.v1",
    storage_ref: "founder-loop-storage:test",
    sqlite_state_ref: "founder-loop-sqlite:test",
    jsonl_log_refs: {
      audit: "founder-loop-log:audit",
      transcript: "founder-loop-log:transcript",
      realtime: "founder-loop-log:realtime",
      receipt: "founder-loop-log:receipt",
    },
    counts: {
      action_inbox: 1,
      briefing_items: 1,
      plan_summaries: 1,
      memory_review_queue: 1,
      idempotency_keys: 0,
      route_state_snapshots: 0,
      evidence_refs: 1,
    },
    safe_refs_only: true,
    raw_content_stored: false,
    postgres_sync_required: false,
    postgres_sync_status: "adapter_boundary_only",
    backup_manifest_ref: "backup-manifest:founder-loop-minimum-set",
    backup_manifest: {
      schema_version: "founder_loop_storage.v1",
      manifest_ref: "backup-manifest:founder-loop-minimum-set",
      required_artifact_refs: ["founder-loop-sqlite:test"],
      raw_paths_included: false,
      raw_logs_included: false,
      safe_refs_only: true,
    },
    updated_at: "2026-01-01T00:00:00Z",
  },
};

const mockApiLocalTaskCreateItem = mockApiData.founderActionsInbox.items.find(
  (candidate) => candidate.item_ref === "founder-action:mock-local-task-create",
);
if (mockApiLocalTaskCreateItem) {
  applyApprovedActionCost(mockApiLocalTaskCreateItem);
}
