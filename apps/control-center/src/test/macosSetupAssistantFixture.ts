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
  if ("rollbackPlanRef" in value && "rollbackExecuted" in value) {
    return {
      ...payload,
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
      label: `Bounded ${slug} review`,
      kind,
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
      requested_scope_refs: [`scope-ref:macos-setup-${slug}`],
      approval_request_ref: approvalRef,
      expected_receipt_ref: receiptRef,
      rollback_plan_ref: rollbackRef,
      idempotency_key_ref: `idempotency-ref:macos-setup-${slug}`,
    });
  }
  return { ...payload, steps, approval_envelopes: envelopes };
}
