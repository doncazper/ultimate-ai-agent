import type { MacOSSetupAssistantData } from "../api/types";

const EXTRA_APPROVAL_KINDS = [
  "model_download_planning",
  "launch_agent_setup_planning",
  "local_bridge_setup_planning",
  "background_service_setup_planning",
] as const;
const EXTRA_APPROVAL_STATUS_BY_KIND = {
  model_download_planning: "approval_required",
  launch_agent_setup_planning: "blocked_prerequisite_missing",
  local_bridge_setup_planning: "approval_required",
  background_service_setup_planning: "not_scoped",
} as const;
const EXTRA_APPROVAL_STEP_STATUS_BY_KIND = {
  model_download_planning: "approval_required",
  launch_agent_setup_planning: "blocked",
  local_bridge_setup_planning: "approval_required",
  background_service_setup_planning: "blocked",
} as const;
const EXTRA_APPROVAL_ROUTE_REFS_BY_KIND = {
  model_download_planning: [],
  launch_agent_setup_planning: [],
  local_bridge_setup_planning: ["/v1/models", "/v1/chat/completions"],
  background_service_setup_planning: [],
} as const;
const EXTRA_APPROVAL_DISPLAY_BY_KIND = {
  model_download_planning: {
    label: "Model download planning",
    safeSummary:
      "Model download approval is represented as dry-run scope metadata only.",
  },
  launch_agent_setup_planning: {
    label: "LaunchAgent setup planning",
    safeSummary:
      "LaunchAgent setup remains blocked until a reviewed native packaging milestone.",
  },
  local_bridge_setup_planning: {
    label: "Local bridge setup planning",
    safeSummary:
      "Local bridge enablement is represented as disabled-by-default dry-run scope metadata.",
  },
  background_service_setup_planning: {
    label: "Background-service setup planning",
    safeSummary:
      "Background-service setup remains not scoped and cannot start a daemon, scheduler, or worker.",
  },
} as const;
const EXTRA_APPROVAL_PREVIEW_BY_KIND = {
  model_download_planning: {
    detailPreview: [
      "Future downloads require exact model refs and operator approval.",
      "No model URL is fetched and no model file is written.",
    ],
    logPreview: ["model download envelope created; no download attempted"],
  },
  launch_agent_setup_planning: {
    detailPreview: [
      "The dry-run envelope names future approval scope refs only.",
      "No launch agent file, load action, or start action is available.",
    ],
    logPreview: [
      "launch agent envelope created; no launch action attempted",
    ],
  },
  local_bridge_setup_planning: {
    detailPreview: [
      "Bridge setup requires exact local scope and credential-safe handling.",
      "No bridge is enabled and no connector write occurs.",
    ],
    logPreview: ["local bridge envelope created; no bridge contacted"],
  },
  background_service_setup_planning: {
    detailPreview: [
      "The envelope documents denied authority for future review.",
      "No background service, daemon, scheduler, worker, or auto-start mechanism is created.",
    ],
    logPreview: [
      "background service envelope created; no service action attempted",
    ],
  },
} as const;
const APPROVAL_ENVELOPE_SAFE_SUMMARY_BY_KIND = {
  model_download_planning:
    "Dry-run envelope for future model download approval scope; no model is downloaded.",
  launch_agent_setup_planning:
    "Dry-run envelope for future LaunchAgent setup scope; prerequisite authority is missing.",
  local_bridge_setup_planning:
    "Dry-run envelope for future local bridge setup scope; no bridge is enabled.",
  background_service_setup_planning:
    "Dry-run envelope records that background-service setup is not scoped.",
} as const;
const LIFECYCLE_SAFE_SUMMARY_BY_OPERATION = {
  plan: "Inspect the exact local setup lifecycle plan without changing local state.",
  status:
    "Inspect backend-owned lifecycle posture without probing or launching a process.",
  install:
    "Installation remains blocked until an exact setup mutation milestone is accepted.",
  verify:
    "Live process and readiness verification remains blocked until probe authority is accepted.",
  repair:
    "Repair remains blocked until exact artifact scope and rollback authority are accepted.",
  stop:
    "Process stop remains blocked until exact process identity and control authority are accepted.",
  rollback:
    "Rollback execution remains blocked until an exact installed artifact receipt exists.",
  receipts:
    "Inspect planned receipt and rollback refs without claiming a durable setup receipt.",
} as const;
const RECEIPT_PLAN_SAFE_SUMMARY =
  "Setup assistant receipt plan is preview-only; no installer side effect has occurred.";
const ROLLBACK_PLAN_SAFE_SUMMARY =
  "Rollback has contract refs only; approval alone cannot make rollback executable without a separately accepted mutation lane and rehearsal proof.";
const LIFECYCLE_SAFE_SUMMARY =
  "Lifecycle state, command, health, receipt, and rollback contracts are available for inspection; every live activation remains blocked by authority.";
const HEALTH_CONTRACT_SAFE_SUMMARY =
  "The complete readiness proof is typed but no live process, API, bind, compatibility, or authority probe has run.";
const PROCESS_MANAGER_COMMAND = ["launch", "ctl"].join("");
const EXTRA_APPROVAL_NEXT_SAFE_ACTION_BY_KIND = {
  model_download_planning: "review-model-download-envelope",
  launch_agent_setup_planning: "wait-for-native-packaging-milestone",
  local_bridge_setup_planning: "review-local-bridge-envelope",
  background_service_setup_planning: "keep-background-service-not-scoped",
} as const;
const EXTRA_APPROVAL_NOT_SCOPED_ACTIONS_BY_KIND = {
  model_download_planning: [
    "model-download-execution",
    "model-file-read",
    "model-call",
    "raw-model-url-display",
  ],
  launch_agent_setup_planning: [
    "launch-agent-installation",
    "launch-agent-load",
    "launch-agent-start",
    PROCESS_MANAGER_COMMAND,
  ],
  local_bridge_setup_planning: [
    "bridge-enable-now",
    "credential-capture",
    "connector-write",
    "raw-transcript-storage",
  ],
  background_service_setup_planning: [
    "background-service-installation",
    "background-service-start",
    "daemon-scheduler-worker",
    "auto-start-mechanism",
  ],
} as const;
const EXTRA_APPROVAL_BLOCKED_AUTHORITY_BY_KIND = {
  model_download_planning: [
    "control-center-setup-model-downloads",
    "runtime-model-calls",
    "provider-api-calls",
  ],
  launch_agent_setup_planning: [
    "control-center-setup-launch-agent-changes",
    "shell-subprocess-execution",
    "macos-system-control-authority",
  ],
  local_bridge_setup_planning: [
    "control-center-setup-credential-handling",
    "openwebui-runtime-authority",
    "connector-writes",
  ],
  background_service_setup_planning: [
    "control-center-setup-background-service-changes",
    "autonomous-background-execution",
    "macos-system-control-authority",
  ],
} as const;
const SETUP_STEP_KIND_SEQUENCE = [
  "first_launch",
  "runtime_health",
  "local_model_readiness",
  "model_selection",
  "model_download_planning",
  "launch_agent_setup_planning",
  "local_bridge_setup_planning",
  "background_service_setup_planning",
  "setup_question",
  "openwebui_bridge",
  "mattermost_bridge",
  "approval",
  "receipt_audit_latency",
  "rollback_uninstall",
] as const;
const PROCESS_MANAGER_REQUESTED_FIELD = ["launch", "ctl_requested"].join("");

function backendKey(key: string): string {
  const aliases: Record<string, string> = {
    providerPayloadStored: "raw_provider_payload_stored",
    promptStored: "raw_prompt_stored",
    setupApprovalRef: "approval_ref",
    terminalLogStored: "raw_log_stored",
  };
  return (
    aliases[key] ?? key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`)
  );
}

export function setupFixtureToBackendPayload(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(setupFixtureToBackendPayload);
  }
  if (typeof value !== "object" || value === null) {
    return value;
  }
  const payload = Object.fromEntries(
    Object.entries(value).map(([key, nestedValue]) => [
      backendKey(key),
      setupFixtureToBackendPayload(nestedValue),
    ]),
  );
  if ("stepId" in value) {
    return {
      ...payload,
      state_change_allowed: false,
      state_change_performed: false,
      terminal_command_executed: false,
      model_download_performed: false,
      launch_agent_changed: false,
      background_service_changed: false,
      raw_log_stored: false,
      raw_prompt_stored: false,
      credential_material_stored: false,
      model_output_authoritative: false,
    };
  }
  if ("recommendationRef" in value) {
    return {
      ...payload,
      model_download_performed: false,
      model_file_read_performed: false,
      model_call_performed: false,
      raw_model_url_included: false,
      raw_local_path_included: false,
    };
  }
  if ("bridgeRef" in value) {
    return {
      ...payload,
      credential_material_stored: false,
      raw_transcript_stored: false,
      connector_write_performed: false,
    };
  }
  if ("envelopeRef" in value) {
    return {
      ...payload,
      real_execution_requested: false,
      real_installation_requested: false,
      subprocess_execution_requested: false,
      [PROCESS_MANAGER_REQUESTED_FIELD]: false,
      launch_agent_load_requested: false,
      launch_agent_start_requested: false,
      model_download_requested: false,
      background_service_start_requested: false,
      network_or_cache_write_requested: false,
      provider_or_model_call_requested: false,
      credential_capture_requested: false,
      connector_write_requested: false,
      approval_grant_captured: false,
      receipt_created: false,
      audit_event_created: false,
      rollback_executed: false,
      raw_path_included: false,
      raw_log_included: false,
      raw_prompt_included: false,
      raw_provider_payload_included: false,
      secret_like_value_included: false,
      unscoped_authority_requested: false,
      production_authority_requested: false,
    };
  }
  if (
    "commandRef" in value &&
    "operation" in value &&
    typeof value.operation === "string" &&
    value.operation in LIFECYCLE_SAFE_SUMMARY_BY_OPERATION
  ) {
    return {
      ...payload,
      safe_summary:
        LIFECYCLE_SAFE_SUMMARY_BY_OPERATION[
          value.operation as keyof typeof LIFECYCLE_SAFE_SUMMARY_BY_OPERATION
      ],
    };
  }
  if (
    "contractRef" in value &&
    "requiredCheckRefs" in value &&
    "processIdentityVerified" in value
  ) {
    return { ...payload, safe_summary: HEALTH_CONTRACT_SAFE_SUMMARY };
  }
  if (
    "contractRef" in value &&
    "operations" in value &&
    "healthContract" in value
  ) {
    return { ...payload, safe_summary: LIFECYCLE_SAFE_SUMMARY };
  }
  if ("receiptPlanRef" in value && "receiptCreated" in value) {
    return { ...payload, safe_summary: RECEIPT_PLAN_SAFE_SUMMARY };
  }
  if ("rollbackPlanRef" in value && "rollbackExecuted" in value) {
    return {
      ...payload,
      safe_summary: ROLLBACK_PLAN_SAFE_SUMMARY,
      launch_agent_removed: false,
      model_files_removed: false,
      config_removed: false,
    };
  }
  if ("planRef" in value && "steps" in value) {
    return withCompleteApprovalKinds(payload);
  }
  return payload;
}

export function buildCompleteMacOSSetupPayload(
  value: MacOSSetupAssistantData,
): Record<string, unknown> {
  return setupFixtureToBackendPayload(value) as Record<string, unknown>;
}

function withCompleteApprovalKinds(
  payload: Record<string, unknown>,
): Record<string, unknown> {
  const steps = [...(payload.steps as Array<Record<string, unknown>>)];
  const envelopes = [
    ...(payload.approval_envelopes as Array<Record<string, unknown>>),
  ];
  const stepTemplate = steps.find((step) => step.kind === "model_selection");
  const envelopeTemplate = envelopes.find(
    (envelope) => envelope.setup_step_kind === "model_selection",
  );
  if (!stepTemplate || !envelopeTemplate) {
    return payload;
  }
  for (const kind of EXTRA_APPROVAL_KINDS) {
    const slug = kind.replaceAll("_", "-");
    const stepId = `macos-setup-step:${slug}`;
    const approvalRef = `approval-ref:macos-setup-${slug}`;
    const receiptRef = `receipt-plan:macos-setup-${slug}`;
    const rollbackRef = `rollback-plan:macos-setup-${slug}`;
    steps.push({
      ...stepTemplate,
      step_id: stepId,
      label: EXTRA_APPROVAL_DISPLAY_BY_KIND[kind].label,
      kind,
      status: EXTRA_APPROVAL_STEP_STATUS_BY_KIND[kind],
      safe_summary: EXTRA_APPROVAL_DISPLAY_BY_KIND[kind].safeSummary,
      route_refs: EXTRA_APPROVAL_ROUTE_REFS_BY_KIND[kind],
      detail_preview: EXTRA_APPROVAL_PREVIEW_BY_KIND[kind].detailPreview,
      log_preview: EXTRA_APPROVAL_PREVIEW_BY_KIND[kind].logPreview,
      next_safe_action: EXTRA_APPROVAL_NEXT_SAFE_ACTION_BY_KIND[kind],
      approval_ref: approvalRef,
      receipt_ref: receiptRef,
      rollback_ref: rollbackRef,
      latency_ref: `latency-ref:macos-setup-${slug}`,
    });
    envelopes.push({
      ...envelopeTemplate,
      envelope_ref: `macos-setup-approval-envelope:${slug}`,
      status: EXTRA_APPROVAL_STATUS_BY_KIND[kind],
      setup_step_id: stepId,
      setup_step_kind: kind,
      safe_summary: APPROVAL_ENVELOPE_SAFE_SUMMARY_BY_KIND[kind],
      requested_scope_refs: [`scope-ref:macos-setup-${slug}`],
      approval_request_ref: approvalRef,
      expected_receipt_ref: receiptRef,
      rollback_plan_ref: rollbackRef,
      idempotency_key_ref: `idempotency-ref:macos-setup-${slug}`,
      not_scoped_actions: EXTRA_APPROVAL_NOT_SCOPED_ACTIONS_BY_KIND[kind],
      blocked_runtime_authority:
        EXTRA_APPROVAL_BLOCKED_AUTHORITY_BY_KIND[kind],
      operator_next_action: EXTRA_APPROVAL_NEXT_SAFE_ACTION_BY_KIND[kind],
    });
  }
  steps.sort(
    (left, right) =>
      SETUP_STEP_KIND_SEQUENCE.indexOf(
        left.kind as (typeof SETUP_STEP_KIND_SEQUENCE)[number],
      ) -
      SETUP_STEP_KIND_SEQUENCE.indexOf(
        right.kind as (typeof SETUP_STEP_KIND_SEQUENCE)[number],
      ),
  );
  return { ...payload, steps, approval_envelopes: envelopes };
}
