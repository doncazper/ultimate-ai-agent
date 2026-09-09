import type {
  MacOSSetupAssistantData,
  MacOSSetupAssistantStep,
  MacOSSetupApprovalEnvelope,
  MacOSSetupBridgePreview,
  MacOSSetupHealthContract,
  MacOSSetupDiagnostic,
  MacOSSetupLifecycleContract,
  MacOSSetupLifecycleOperation,
  MacOSSetupLifecycleOperationName,
  MacOSSetupLifecycleState,
  MacOSSetupModelRecommendation,
  MacOSSetupReceiptPlan,
  MacOSSetupRollbackPlan,
  MacOSSetupStepStatus,
} from "./types";
import { containsSecretLike } from "./redaction";

const MACOS_SETUP_STATUSES = new Set<MacOSSetupStepStatus>([
  "planned",
  "ready",
  "dry_run_only",
  "approval_required",
  "blocked",
  "manual_only",
]);
const MACOS_SETUP_LIFECYCLE_STATE_SEQUENCE: MacOSSetupLifecycleState[] = [
  "prerequisites",
  "ready_to_install",
  "approval_required",
  "installing",
  "installed",
  "starting",
  "healthy",
  "degraded",
  "repairable",
  "stopping",
  "rollback_required",
  "rolled_back",
  "failed",
];
const MACOS_SETUP_LIFECYCLE_STATES = new Set<MacOSSetupLifecycleState>(
  MACOS_SETUP_LIFECYCLE_STATE_SEQUENCE,
);
const MACOS_SETUP_LIFECYCLE_OPERATION_SEQUENCE: MacOSSetupLifecycleOperationName[] =
  [
    "plan",
    "status",
    "install",
    "verify",
    "repair",
    "stop",
    "rollback",
    "receipts",
  ];
const MACOS_SETUP_LIFECYCLE_OPERATIONS =
  new Set<MacOSSetupLifecycleOperationName>(
    MACOS_SETUP_LIFECYCLE_OPERATION_SEQUENCE,
  );
const MACOS_SETUP_LIFECYCLE_TARGET_STATES: Record<
  MacOSSetupLifecycleOperationName,
  MacOSSetupLifecycleState
> = {
  plan: "prerequisites",
  status: "prerequisites",
  install: "installed",
  verify: "healthy",
  repair: "healthy",
  stop: "stopping",
  rollback: "rolled_back",
  receipts: "prerequisites",
};
const MACOS_SETUP_STEP_KINDS = new Set([
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
]);
const MACOS_SETUP_APPROVAL_STATUSES = new Set([
  "dry_run_plan_created",
  "approval_required",
  "blocked_prerequisite_missing",
  "denied_unsafe_authority",
  "not_scoped",
]);
const MACOS_SETUP_REQUIRED_APPROVAL_KINDS = new Set([
  "model_selection",
  "model_download_planning",
  "launch_agent_setup_planning",
  "local_bridge_setup_planning",
  "background_service_setup_planning",
  "openwebui_bridge",
  "mattermost_bridge",
]);
const MACOS_SETUP_APPROVAL_SCOPE_BY_KIND = {
  model_selection: ["scope-ref:macos-setup-model-selection"],
  model_download_planning: [
    "scope-ref:macos-setup-model-download-planning",
  ],
  launch_agent_setup_planning: [
    "scope-ref:macos-setup-launch-agent-setup-planning",
  ],
  local_bridge_setup_planning: [
    "scope-ref:macos-setup-local-bridge-setup-planning",
  ],
  background_service_setup_planning: [
    "scope-ref:macos-setup-background-service-setup-planning",
  ],
  openwebui_bridge: ["scope-ref:macos-setup-openwebui-bridge"],
  mattermost_bridge: ["scope-ref:macos-setup-mattermost-bridge"],
} as const;
const MACOS_SETUP_BLOCKED_CAPABILITY_SEQUENCE = [
  "macos-setup-runtime-installation",
  "macos-setup-model-download",
  "macos-setup-launch-agent-change",
  "macos-setup-background-service-change",
  "macos-setup-bridge-enablement",
  "macos-setup-provider-call",
  "macos-setup-credential-storage",
  "macos-setup-rollback-execution",
  "macos-setup-signed-distribution",
  "macos-setup-production-authority",
] as const;
const MACOS_SETUP_REQUIRED_HEALTH_CHECK_SEQUENCE = [
  "health-check-ref:setup-process-identity",
  "health-check-ref:setup-api-manifest-version",
  "health-check-ref:setup-loopback-bind",
  "health-check-ref:setup-control-center-compatibility",
  "health-check-ref:setup-forbidden-authority-absent",
] as const;
const MACOS_SETUP_SAFE_REF_RE = /^[A-Za-z][A-Za-z0-9_.:-]{2,190}$/;
const MACOS_SETUP_SAFE_TEXT_RE =
  /^[A-Za-z0-9][A-Za-z0-9 _.,:/()+#;-]{0,799}$/;
const MACOS_SETUP_SAFE_ROUTE_RE = /^\/[A-Za-z0-9_./{}:-]{0,179}$/;
const MACOS_SETUP_ABSOLUTE_PATH_RE =
  /(^|[^A-Za-z0-9._/\\-])(?:~\/?|\/(?:Applications|Library|Network|System|Users|Volumes|bin|dev|etc|home|opt|private|sbin|tmp|usr|var)(?:\/|\b)|[A-Za-z]:[\\/]|\\\\)/;
const MACOS_SETUP_MAX_COLLECTION_ITEMS = 100;
const MACOS_SETUP_MAX_DETAIL_CHARS = 800;
const MACOS_SETUP_MAX_LOG_CHARS = 400;
const MACOS_SETUP_PROCESS_MANAGER_REQUESTED_FIELD = [
  "launch",
  "ctl_requested",
].join("");
const MACOS_SETUP_RUNTIME_TEXT_FRAGMENTS = [
  ["launch", "ctl"].join(""),
  "load launchagent",
  "start launchagent",
  "install launchagent",
  "start background service",
  "install background service",
  "download model now",
  "execute installer",
  "run installer",
];
export function normalizeMacOSSetupAssistant(
  source: unknown,
  fallback: MacOSSetupAssistantData,
): { value: MacOSSetupAssistantData; usedFallback: boolean } {
  const value = normalizeMacOSSetupAssistantValue(source, fallback);
  const probeFallback = alternateFallback(fallback);
  const probeValue = normalizeMacOSSetupAssistantValue(source, probeFallback);
  const usedFallback =
    setupSafetySourceRequiresFallback(source) ||
    JSON.stringify(value) !== JSON.stringify(probeValue);
  return {
    value: usedFallback ? fallback : value,
    usedFallback,
  };
}

function normalizeMacOSSetupAssistantValue(
  value: unknown,
  fallback: MacOSSetupAssistantData,
): MacOSSetupAssistantData {
  if (!isRecord(value)) {
    return fallback;
  }
  const steps = recordsValue(value, "steps");
  const recommendations = recordsValue(value, "model_recommendations");
  const bridges = recordsValue(value, "bridge_previews");
  const envelopes = recordsValue(value, "approval_envelopes");
  const diagnostics = recordsValue(value, "diagnostics");
  return {
    planRef: stringValue(value, "plan_ref", fallback.planRef),
    status: setupStatusValue(value, "status", fallback.status),
    macosFirst: booleanValue(value, "macos_first", fallback.macosFirst),
    localFirst: booleanValue(value, "local_first", fallback.localFirst),
    disabledByDefault: booleanValue(
      value,
      "disabled_by_default",
      fallback.disabledByDefault,
    ),
    nativeMacosAppReady: booleanValue(
      value,
      "native_macos_app_ready",
      fallback.nativeMacosAppReady,
    ),
    controlCenterPreviewReady: booleanValue(
      value,
      "control_center_preview_ready",
      fallback.controlCenterPreviewReady,
    ),
    setupQuestionAssistantEnabled: booleanValue(
      value,
      "setup_question_assistant_enabled",
      fallback.setupQuestionAssistantEnabled,
    ),
    modelOutputAuthoritative: booleanValue(
      value,
      "model_output_authoritative",
      fallback.modelOutputAuthoritative,
    ),
    installerSideEffectsEnabled: booleanValue(
      value,
      "installer_side_effects_enabled",
      fallback.installerSideEffectsEnabled,
    ),
    visualShellRef: stringValue(
      value,
      "visual_shell_ref",
      fallback.visualShellRef,
    ),
    fullStrengthGoal: stringValue(
      value,
      "full_strength_goal",
      fallback.fullStrengthGoal,
    ),
    repoSafeScope: stringValue(value, "repo_safe_scope", fallback.repoSafeScope),
    blockedAuthoritySummary: stringValue(
      value,
      "blocked_authority_summary",
      fallback.blockedAuthoritySummary,
    ),
    firstRunLoopRefs: stringArrayValue(
      value,
      "first_run_loop_refs",
      fallback.firstRunLoopRefs,
    ),
    localPackageProofStatus: stringValue(
      value,
      "local_package_proof_status",
      fallback.localPackageProofStatus,
    ),
    localPackageProofRefs: stringArrayValue(
      value,
      "local_package_proof_refs",
      fallback.localPackageProofRefs,
    ),
    promotionPathRefs: stringArrayValue(
      value,
      "promotion_path_refs",
      fallback.promotionPathRefs,
    ),
    lifecycle: normalizeMacOSSetupLifecycle(
      recordValue(value, "lifecycle"),
      fallback.lifecycle,
    ),
    diagnostics:
      diagnostics.length > 0
        ? diagnostics.map((diagnostic, index) =>
            normalizeMacOSSetupDiagnostic(
              diagnostic,
              fallbackItem(fallback.diagnostics, index),
            ),
          )
        : fallback.diagnostics,
    steps:
      steps.length > 0
        ? steps.map((step, index) =>
            normalizeMacOSSetupStep(step, fallbackItem(fallback.steps, index)),
          )
        : fallback.steps,
    modelRecommendations:
      recommendations.length > 0
        ? recommendations.map((recommendation, index) =>
            normalizeMacOSSetupRecommendation(
              recommendation,
              fallbackItem(fallback.modelRecommendations, index),
            ),
          )
        : fallback.modelRecommendations,
    bridgePreviews:
      bridges.length > 0
        ? bridges.map((bridge, index) =>
            normalizeMacOSSetupBridge(
              bridge,
              fallbackItem(fallback.bridgePreviews, index),
            ),
          )
        : fallback.bridgePreviews,
    approvalEnvelopes:
      envelopes.length > 0
        ? envelopes.map((envelope, index) =>
            normalizeMacOSSetupApprovalEnvelope(
              envelope,
              fallbackItem(fallback.approvalEnvelopes, index),
            ),
          )
        : fallback.approvalEnvelopes,
    receiptPlan: normalizeMacOSSetupReceiptPlan(
      recordValue(value, "receipt_plan"),
      fallback.receiptPlan,
    ),
    rollbackPlan: normalizeMacOSSetupRollbackPlan(
      recordValue(value, "rollback_plan"),
      fallback.rollbackPlan,
    ),
    blockedCapabilities: stringArrayValue(
      value,
      "blocked_capabilities",
      fallback.blockedCapabilities,
    ),
    nextSteps: stringArrayValue(value, "next_steps", fallback.nextSteps),
    morningReviewChecklist: stringArrayValue(
      value,
      "morning_review_checklist",
      fallback.morningReviewChecklist,
    ),
  };
}

function normalizeMacOSSetupDiagnostic(
  value: Record<string, unknown>,
  fallback: MacOSSetupDiagnostic,
): MacOSSetupDiagnostic {
  const status = stringValue(value, "status", fallback.status);
  return {
    diagnosticRef: stringValue(
      value,
      "diagnostic_ref",
      fallback.diagnosticRef,
    ),
    label: stringValue(value, "label", fallback.label),
    status:
      status === "ready" || status === "missing" || status === "blocked"
        ? status
        : fallback.status,
    safeSummary: stringValue(value, "safe_summary", fallback.safeSummary),
    sourceRefs: stringArrayValue(value, "source_refs", fallback.sourceRefs),
    reasonCodes: stringArrayValue(value, "reason_codes", fallback.reasonCodes),
    nextSafeAction: stringValue(
      value,
      "next_safe_action",
      fallback.nextSafeAction,
    ),
    readOnly: true,
    liveProbePerformed: false,
    stateChangePerformed: false,
  };
}

function normalizeMacOSSetupLifecycle(
  value: Record<string, unknown> | undefined,
  fallback: MacOSSetupLifecycleContract,
): MacOSSetupLifecycleContract {
  if (!value) {
    return fallback;
  }
  const operations = recordsValue(value, "operations");
  const operationSequenceIsExact = hasExactLifecycleOperationSequence(
    value.operations,
  );
  return {
    schemaVersion: stringValue(
      value,
      "schema_version",
      fallback.schemaVersion,
    ),
    contractRef: stringValue(value, "contract_ref", fallback.contractRef),
    status: "blocked_by_authority",
    currentState: "prerequisites",
    stateSequence: lifecycleStateArrayValue(
      value,
      "state_sequence",
      fallback.stateSequence,
    ),
    operations:
      operationSequenceIsExact
        ? operations.map((operation, index) =>
            normalizeMacOSSetupLifecycleOperation(
              operation,
              fallbackItem(fallback.operations, index),
            ),
          )
        : fallback.operations,
    healthContract: normalizeMacOSSetupHealthContract(
      recordValue(value, "health_contract"),
      fallback.healthContract,
    ),
    authorityPrerequisiteRef: stringValue(
      value,
      "authority_prerequisite_ref",
      fallback.authorityPrerequisiteRef,
    ),
    authorityStateRef: stringValue(
      value,
      "authority_state_ref",
      fallback.authorityStateRef,
    ),
    pythonCoreServiceRef: stringValue(
      value,
      "python_core_service_ref",
      fallback.pythonCoreServiceRef,
    ),
    apiSurfaceRef: stringValue(
      value,
      "api_surface_ref",
      fallback.apiSurfaceRef,
    ),
    cliSurfaceRef: stringValue(
      value,
      "cli_surface_ref",
      fallback.cliSurfaceRef,
    ),
    controlCenterSurfaceRef: stringValue(
      value,
      "control_center_surface_ref",
      fallback.controlCenterSurfaceRef,
    ),
    safeDisableRef: stringValue(
      value,
      "safe_disable_ref",
      fallback.safeDisableRef,
    ),
    rollbackContractRef: stringValue(
      value,
      "rollback_contract_ref",
      fallback.rollbackContractRef,
    ),
    receiptContractRef: stringValue(
      value,
      "receipt_contract_ref",
      fallback.receiptContractRef,
    ),
    blockedReasonRefs: stringArrayValue(
      value,
      "blocked_reason_refs",
      fallback.blockedReasonRefs,
    ),
    safeSummary: stringValue(value, "safe_summary", fallback.safeSummary),
    activationAuthorized: false,
    installationPerformed: false,
    processLaunched: false,
    healthProbePerformed: false,
    repairPerformed: false,
    stopPerformed: false,
    rollbackPerformed: false,
    fileMutationPerformed: false,
    credentialWritePerformed: false,
    subprocessExecuted: false,
    liveNetworkRequestPerformed: false,
    productionAuthorityEnabled: false,
  };
}

function normalizeMacOSSetupLifecycleOperation(
  value: Record<string, unknown>,
  fallback: MacOSSetupLifecycleOperation,
): MacOSSetupLifecycleOperation {
  const operation = lifecycleOperationValue(
    value,
    "operation",
    fallback.operation,
  );
  const readOnly =
    operation === "plan" ||
    operation === "status" ||
    operation === "receipts";
  return {
    operation,
    commandRef: stringValue(value, "command_ref", fallback.commandRef),
    status: readOnly ? "available_read_only" : "blocked_by_authority",
    currentState: "prerequisites",
    targetState: lifecycleStateValue(
      value,
      "target_state",
      fallback.targetState,
    ),
    safeSummary: stringValue(value, "safe_summary", fallback.safeSummary),
    exactScopeRef: stringValue(
      value,
      "exact_scope_ref",
      fallback.exactScopeRef,
    ),
    approvalRef: stringValue(value, "approval_ref", fallback.approvalRef),
    idempotencyKeyRef: stringValue(
      value,
      "idempotency_key_ref",
      fallback.idempotencyKeyRef,
    ),
    receiptRef: stringValue(value, "receipt_ref", fallback.receiptRef),
    rollbackRef: stringValue(value, "rollback_ref", fallback.rollbackRef),
    safeDisableRef: stringValue(
      value,
      "safe_disable_ref",
      fallback.safeDisableRef,
    ),
    evidenceRefs: stringArrayValue(
      value,
      "evidence_refs",
      fallback.evidenceRefs,
    ),
    verifierRefs: stringArrayValue(
      value,
      "verifier_refs",
      fallback.verifierRefs,
    ),
    reasonCodes: stringArrayValue(value, "reason_codes", fallback.reasonCodes),
    mutationRequired:
      !readOnly &&
      booleanValue(value, "mutation_required", fallback.mutationRequired),
    liveProbeRequired:
      !readOnly &&
      booleanValue(value, "live_probe_required", fallback.liveProbeRequired),
    approvalRequired: !readOnly,
    authorityGranted: false,
    stateChangePerformed: false,
    subprocessExecuted: false,
    fileMutationPerformed: false,
    processMutationPerformed: false,
    credentialWritePerformed: false,
    networkRequestPerformed: false,
    receiptPersisted: false,
  };
}

function setupSafetySourceRequiresFallback(source: unknown): boolean {
  if (!isRecord(source)) {
    return true;
  }
  const steps = recordArray(source.steps);
  const diagnostics = recordArray(source.diagnostics);
  const recommendations = recordArray(source.model_recommendations);
  const bridges = recordArray(source.bridge_previews, true);
  const envelopes = recordArray(source.approval_envelopes);
  const lifecycle = recordValue(source, "lifecycle");
  const receiptPlan = recordValue(source, "receipt_plan");
  const rollbackPlan = recordValue(source, "rollback_plan");

  return (
    !isSafeRef(source.plan_ref) ||
    !isSetupStatus(source.status) ||
    source.macos_first !== true ||
    source.local_first !== true ||
    source.disabled_by_default !== true ||
    source.control_center_preview_ready !== true ||
    source.native_macos_app_ready !== false ||
    source.setup_question_assistant_enabled !== false ||
    source.model_output_authoritative !== false ||
    source.installer_side_effects_enabled !== false ||
    !isSafeRef(source.visual_shell_ref) ||
    !isSafeText(source.full_strength_goal, MACOS_SETUP_MAX_DETAIL_CHARS) ||
    !isSafeText(source.repo_safe_scope, MACOS_SETUP_MAX_DETAIL_CHARS) ||
    !isSafeText(
      source.blocked_authority_summary,
      MACOS_SETUP_MAX_DETAIL_CHARS,
    ) ||
    !isSafeText(
      source.local_package_proof_status,
      MACOS_SETUP_MAX_DETAIL_CHARS,
    ) ||
    !isSafeRefArray(source.first_run_loop_refs, true) ||
    !isSafeRefArray(source.local_package_proof_refs, true) ||
    !isSafeRefArray(source.promotion_path_refs, true) ||
    !hasExactStringSequence(
      source.blocked_capabilities,
      MACOS_SETUP_BLOCKED_CAPABILITY_SEQUENCE,
    ) ||
    !isSafeTextArray(source.next_steps, MACOS_SETUP_MAX_DETAIL_CHARS) ||
    !isSafeTextArray(
      source.morning_review_checklist,
      MACOS_SETUP_MAX_DETAIL_CHARS,
    ) ||
    !steps ||
    !diagnostics ||
    !recommendations ||
    !bridges ||
    !envelopes ||
    !lifecycle ||
    !receiptPlan ||
    !rollbackPlan ||
    steps.some((step) => !isSafeSetupStep(step)) ||
    diagnostics.some((diagnostic) => !isSafeSetupDiagnostic(diagnostic)) ||
    recommendations.some(
      (recommendation) => !isSafeSetupRecommendation(recommendation),
    ) ||
    bridges.some((bridge) => !isSafeSetupBridge(bridge)) ||
    envelopes.some((envelope) => !isSafeSetupApprovalEnvelope(envelope)) ||
    !approvalEnvelopesBindToSteps(steps, envelopes) ||
    !isSafeSetupReceiptPlan(receiptPlan) ||
    !isSafeSetupRollbackPlan(rollbackPlan) ||
    !isSafeSetupLifecycle(lifecycle)
  );
}

function isSafeSetupDiagnostic(value: Record<string, unknown>): boolean {
  return (
    isSafeRef(value.diagnostic_ref) &&
    isSafeText(value.label, 120) &&
    (value.status === "ready" ||
      value.status === "missing" ||
      value.status === "blocked") &&
    isSafeText(value.safe_summary, MACOS_SETUP_MAX_DETAIL_CHARS) &&
    isSafeRefArray(value.source_refs, true) &&
    isSafeRefArray(value.reason_codes, true) &&
    isSafeRef(value.next_safe_action) &&
    value.read_only === true &&
    value.live_probe_performed === false &&
    value.state_change_performed === false
  );
}

function isSafeSetupStep(value: Record<string, unknown>): boolean {
  return (
    isSafeRef(value.step_id) &&
    typeof value.kind === "string" &&
    MACOS_SETUP_STEP_KINDS.has(value.kind) &&
    isSafeText(value.label, 120) &&
    isSetupStatus(value.status) &&
    isSafeText(value.safe_summary, MACOS_SETUP_MAX_DETAIL_CHARS) &&
    isSafeRouteArray(value.route_refs) &&
    isSafeTextArray(value.detail_preview, MACOS_SETUP_MAX_DETAIL_CHARS) &&
    isSafeTextArray(value.log_preview, MACOS_SETUP_MAX_LOG_CHARS) &&
    typeof value.approval_required === "boolean" &&
    (value.status !== "approval_required" ||
      value.approval_required === true) &&
    isSafeOptionalRef(value.approval_ref) &&
    isSafeRef(value.receipt_ref) &&
    isSafeRef(value.rollback_ref) &&
    isSafeOptionalRef(value.latency_ref) &&
    isSafeRefArray(value.reason_codes) &&
    isSafeRef(value.next_safe_action) &&
    allBooleanFieldsEqual(
      value,
      [
        "state_change_allowed",
        "state_change_performed",
        "terminal_command_executed",
        "model_download_performed",
        "launch_agent_changed",
        "background_service_changed",
        "raw_log_stored",
        "raw_prompt_stored",
        "credential_material_stored",
        "model_output_authoritative",
      ],
      false,
    )
  );
}

function isSafeSetupRecommendation(value: Record<string, unknown>): boolean {
  return (
    isSafeRef(value.recommendation_ref) &&
    isSafeRef(value.model_ref) &&
    isSafeText(value.display_name, MACOS_SETUP_MAX_DETAIL_CHARS) &&
    isSafeText(value.fit_summary, MACOS_SETUP_MAX_DETAIL_CHARS) &&
    isSafeText(value.recommended_for, MACOS_SETUP_MAX_DETAIL_CHARS) &&
    isSafeText(value.memory_bucket, MACOS_SETUP_MAX_DETAIL_CHARS) &&
    isSafeText(value.disk_bucket, MACOS_SETUP_MAX_DETAIL_CHARS) &&
    isSafeText(value.privacy_summary, MACOS_SETUP_MAX_DETAIL_CHARS) &&
    value.approval_required_before_download === true &&
    typeof value.selected_by_default === "boolean" &&
    isSafeRefArray(value.reason_codes) &&
    allBooleanFieldsEqual(
      value,
      [
        "model_download_performed",
        "model_file_read_performed",
        "model_call_performed",
        "raw_model_url_included",
        "raw_local_path_included",
      ],
      false,
    )
  );
}

function isSafeSetupBridge(value: Record<string, unknown>): boolean {
  return (
    isSafeRef(value.bridge_ref) &&
    isSafeText(value.label, 120) &&
    isSetupStatus(value.status) &&
    isSafeText(value.safe_summary, MACOS_SETUP_MAX_DETAIL_CHARS) &&
    value.enablement_default === "disabled" &&
    value.approval_required === true &&
    isSafeRefArray(value.reason_codes) &&
    allBooleanFieldsEqual(
      value,
      [
        "credential_material_stored",
        "raw_transcript_stored",
        "connector_write_performed",
      ],
      false,
    )
  );
}

function isSafeSetupApprovalEnvelope(
  value: Record<string, unknown>,
): boolean {
  return (
    isSafeRef(value.envelope_ref) &&
    typeof value.status === "string" &&
    MACOS_SETUP_APPROVAL_STATUSES.has(value.status) &&
    isSafeRef(value.setup_step_id) &&
    typeof value.setup_step_kind === "string" &&
    MACOS_SETUP_STEP_KINDS.has(value.setup_step_kind) &&
    isSafeEnvelopeText(value.safe_summary) &&
    hasExactApprovalScope(
      value.setup_step_kind,
      value.requested_scope_refs,
    ) &&
    isSafeApprovalRequestRef(value.approval_request_ref) &&
    isSafePrefixedRef(value.expected_receipt_ref, "receipt-plan:") &&
    isSafePrefixedRef(value.rollback_plan_ref, "rollback-plan:") &&
    isSafePrefixedRef(value.idempotency_key_ref, "idempotency-ref:") &&
    isSafeText(value.risk_class, 40) &&
    value.side_effect_class === "validation_only" &&
    isSafeRefArray(value.not_scoped_actions, true) &&
    isSafeRefArray(value.blocked_runtime_authority, true) &&
    isSafeRefArray(value.evidence_refs, true) &&
    isSafeRefArray(value.verifier_refs, true) &&
    isSafeRef(value.operator_next_action) &&
    isSafeEnvelopeText(value.stale_state_handling) &&
    isSafeEnvelopeText(value.redaction_summary) &&
    allBooleanFieldsEqual(
      value,
      [
        "dry_run_only",
        "approval_required",
        "approval_ref_is_identifier_only",
        "exact_scope_required",
        "idempotency_required",
        "rollback_required",
        "redaction_required",
        "disabled_by_default",
      ],
      true,
    ) &&
    allBooleanFieldsEqual(
      value,
      [
        "real_execution_requested",
        "real_installation_requested",
        "subprocess_execution_requested",
        MACOS_SETUP_PROCESS_MANAGER_REQUESTED_FIELD,
        "launch_agent_load_requested",
        "launch_agent_start_requested",
        "model_download_requested",
        "background_service_start_requested",
        "network_or_cache_write_requested",
        "provider_or_model_call_requested",
        "credential_capture_requested",
        "connector_write_requested",
        "approval_grant_captured",
        "receipt_created",
        "audit_event_created",
        "rollback_executed",
        "raw_path_included",
        "raw_log_included",
        "raw_prompt_included",
        "raw_provider_payload_included",
        "secret_like_value_included",
        "unscoped_authority_requested",
        "production_authority_requested",
      ],
      false,
    ) &&
    isSafeRefArray(value.reason_codes)
  );
}

function approvalEnvelopesBindToSteps(
  steps: Record<string, unknown>[],
  envelopes: Record<string, unknown>[],
): boolean {
  const stepsById = new Map(
    steps.map((step) => [String(step.step_id), step] as const),
  );
  const envelopeKinds = new Set(
    envelopes.map((envelope) => String(envelope.setup_step_kind)),
  );
  const requiredApprovalSteps = steps.filter(
    (step) =>
      typeof step.kind === "string" &&
      MACOS_SETUP_REQUIRED_APPROVAL_KINDS.has(step.kind),
  );
  const envelopesByStepId = new Map(
    envelopes.map(
      (envelope) => [String(envelope.setup_step_id), envelope] as const,
    ),
  );
  if (
    stepsById.size !== steps.length ||
    envelopesByStepId.size !== envelopes.length ||
    requiredApprovalSteps.length !== envelopes.length ||
    envelopeKinds.size !== MACOS_SETUP_REQUIRED_APPROVAL_KINDS.size ||
    ![...MACOS_SETUP_REQUIRED_APPROVAL_KINDS].every((kind) =>
      envelopeKinds.has(kind),
    )
  ) {
    return false;
  }
  return requiredApprovalSteps.every((step) => {
    const envelope = envelopesByStepId.get(String(step.step_id));
    return (
      envelope !== undefined &&
      envelope.setup_step_kind === step.kind &&
      step.approval_required === true &&
      step.approval_ref === envelope.approval_request_ref &&
      step.receipt_ref === envelope.expected_receipt_ref &&
      step.rollback_ref === envelope.rollback_plan_ref
    );
  });
}

function isSafeSetupReceiptPlan(value: Record<string, unknown>): boolean {
  return (
    isSafeRef(value.receipt_plan_ref) &&
    isSafeRef(value.audit_ref) &&
    isSafeRef(value.latency_ref) &&
    isSafeText(value.safe_summary, MACOS_SETUP_MAX_DETAIL_CHARS) &&
    allBooleanFieldsEqual(
      value,
      [
        "receipt_created",
        "audit_event_created",
        "raw_log_stored",
        "raw_prompt_stored",
        "raw_provider_payload_stored",
        "credential_material_stored",
      ],
      false,
    )
  );
}

function isSafeSetupRollbackPlan(value: Record<string, unknown>): boolean {
  return (
    isSafeRef(value.rollback_plan_ref) &&
    isSafeRef(value.uninstall_ref) &&
    isSafeText(value.safe_summary, MACOS_SETUP_MAX_DETAIL_CHARS) &&
    value.rollback_contract_defined === true &&
    isSafeRefArray(value.blocked_reason_refs, true) &&
    isSafeRef(value.next_safe_action) &&
    allBooleanFieldsEqual(
      value,
      [
        "rollback_available_after_approval",
        "rollback_execution_available",
        "rollback_rehearsal_completed",
        "restore_proof_available",
        "rollback_executed",
        "launch_agent_removed",
        "model_files_removed",
        "config_removed",
      ],
      false,
    )
  );
}

function isSafeSetupLifecycle(value: Record<string, unknown>): boolean {
  const operations = recordArray(value.operations);
  const healthContract = recordValue(value, "health_contract");
  return (
    !!operations &&
    !!healthContract &&
    isSafeRef(value.schema_version) &&
    isSafeRef(value.contract_ref) &&
    value.status === "blocked_by_authority" &&
    value.current_state === "prerequisites" &&
    hasExactStringSequence(
      value.state_sequence,
      MACOS_SETUP_LIFECYCLE_STATE_SEQUENCE,
    ) &&
    hasExactLifecycleOperationSequence(value.operations) &&
    isSafeRef(value.authority_prerequisite_ref) &&
    isSafeRef(value.authority_state_ref) &&
    isSafeRef(value.python_core_service_ref) &&
    isSafeRef(value.api_surface_ref) &&
    isSafeRef(value.cli_surface_ref) &&
    isSafeRef(value.control_center_surface_ref) &&
    isSafeRef(value.safe_disable_ref) &&
    isSafeRef(value.rollback_contract_ref) &&
    isSafeRef(value.receipt_contract_ref) &&
    isSafeRefArray(value.blocked_reason_refs, true) &&
    isSafeText(value.safe_summary, MACOS_SETUP_MAX_DETAIL_CHARS) &&
    allBooleanFieldsEqual(
      value,
      [
        "activation_authorized",
        "installation_performed",
        "process_launched",
        "health_probe_performed",
        "repair_performed",
        "stop_performed",
        "rollback_performed",
        "file_mutation_performed",
        "credential_write_performed",
        "subprocess_executed",
        "live_network_request_performed",
        "production_authority_enabled",
      ],
      false,
    ) &&
    operations.every((operation, index) =>
      isSafeSetupLifecycleOperation(
        operation,
        MACOS_SETUP_LIFECYCLE_OPERATION_SEQUENCE[index],
      ),
    ) &&
    isSafeSetupHealthContract(healthContract)
  );
}

function isSafeSetupLifecycleOperation(
  value: Record<string, unknown>,
  expectedOperation: MacOSSetupLifecycleOperationName,
): boolean {
  const readOnly =
    expectedOperation === "plan" ||
    expectedOperation === "status" ||
    expectedOperation === "receipts";
  return (
    value.operation === expectedOperation &&
    value.command_ref ===
      `repo-local-command:macos-setup-lifecycle:${expectedOperation}` &&
    value.status ===
      (readOnly ? "available_read_only" : "blocked_by_authority") &&
    value.current_state === "prerequisites" &&
    value.target_state ===
      MACOS_SETUP_LIFECYCLE_TARGET_STATES[expectedOperation] &&
    isSafeText(value.safe_summary, MACOS_SETUP_MAX_DETAIL_CHARS) &&
    isSafeRef(value.exact_scope_ref) &&
    isSafeRef(value.approval_ref) &&
    isSafeRef(value.idempotency_key_ref) &&
    isSafeRef(value.receipt_ref) &&
    isSafeRef(value.rollback_ref) &&
    isSafeRef(value.safe_disable_ref) &&
    isSafeRefArray(value.evidence_refs, true) &&
    isSafeRefArray(value.verifier_refs, true) &&
    isSafeRefArray(value.reason_codes) &&
    typeof value.mutation_required === "boolean" &&
    typeof value.live_probe_required === "boolean" &&
    value.approval_required === !readOnly &&
    (!readOnly ||
      (value.mutation_required === false &&
        value.live_probe_required === false)) &&
    (readOnly ||
      (value.reason_codes as string[]).includes(
        "MACOS_SETUP_LIFECYCLE_AUTHORITY_NOT_GRANTED",
      )) &&
    allBooleanFieldsEqual(
      value,
      [
        "authority_granted",
        "state_change_performed",
        "subprocess_executed",
        "file_mutation_performed",
        "process_mutation_performed",
        "credential_write_performed",
        "network_request_performed",
        "receipt_persisted",
      ],
      false,
    )
  );
}

function isSafeSetupHealthContract(value: Record<string, unknown>): boolean {
  return (
    isSafeRef(value.contract_ref) &&
    value.status === "blocked_by_authority" &&
    hasExactStringSequence(
      value.required_check_refs,
      MACOS_SETUP_REQUIRED_HEALTH_CHECK_SEQUENCE,
    ) &&
    isSafeText(value.safe_summary, MACOS_SETUP_MAX_DETAIL_CHARS) &&
    allBooleanFieldsEqual(
      value,
      [
        "process_identity_verified",
        "api_manifest_version_verified",
        "loopback_bind_verified",
        "control_center_compatibility_verified",
        "forbidden_authority_absence_verified",
        "live_probe_performed",
      ],
      false,
    )
  );
}

function hasExactLifecycleOperationSequence(value: unknown): boolean {
  return (
    Array.isArray(value) &&
    value.length === MACOS_SETUP_LIFECYCLE_OPERATION_SEQUENCE.length &&
    value.every(
      (operation, index) =>
        isRecord(operation) &&
        operation.operation ===
          MACOS_SETUP_LIFECYCLE_OPERATION_SEQUENCE[index],
    )
  );
}

function hasExactStringSequence(
  value: unknown,
  expected: readonly string[],
): boolean {
  return (
    Array.isArray(value) &&
    value.length === expected.length &&
    value.every((item, index) => item === expected[index])
  );
}

function hasExactApprovalScope(
  kind: unknown,
  value: unknown,
): boolean {
  if (
    typeof kind !== "string" ||
    !(kind in MACOS_SETUP_APPROVAL_SCOPE_BY_KIND)
  ) {
    return false;
  }
  return hasExactStringSequence(
    value,
    MACOS_SETUP_APPROVAL_SCOPE_BY_KIND[
      kind as keyof typeof MACOS_SETUP_APPROVAL_SCOPE_BY_KIND
    ],
  );
}

function allBooleanFieldsEqual(
  value: Record<string, unknown>,
  fields: readonly string[],
  expected: boolean,
): boolean {
  return fields.every((field) => value[field] === expected);
}

function normalizeMacOSSetupHealthContract(
  value: Record<string, unknown> | undefined,
  fallback: MacOSSetupHealthContract,
): MacOSSetupHealthContract {
  if (!value) {
    return fallback;
  }
  return {
    contractRef: stringValue(value, "contract_ref", fallback.contractRef),
    status: "blocked_by_authority",
    requiredCheckRefs: stringArrayValue(
      value,
      "required_check_refs",
      fallback.requiredCheckRefs,
    ),
    safeSummary: stringValue(value, "safe_summary", fallback.safeSummary),
    processIdentityVerified: false,
    apiManifestVersionVerified: false,
    loopbackBindVerified: false,
    controlCenterCompatibilityVerified: false,
    forbiddenAuthorityAbsenceVerified: false,
    liveProbePerformed: false,
  };
}

function alternateFallback(
  fallback: MacOSSetupAssistantData,
): MacOSSetupAssistantData {
  const transform = (value: unknown): unknown => {
    if (typeof value === "string") return `${value}:fallback-probe`;
    if (typeof value === "boolean") return !value;
    if (typeof value === "number") return value + 1;
    if (Array.isArray(value)) return value.map(transform);
    if (isRecord(value)) {
      return Object.fromEntries(
        Object.entries(value).map(([key, item]) => [key, transform(item)]),
      );
    }
    return value;
  };
  return transform(fallback) as MacOSSetupAssistantData;
}

function normalizeMacOSSetupApprovalEnvelope(
  value: Record<string, unknown>,
  fallback: MacOSSetupApprovalEnvelope,
): MacOSSetupApprovalEnvelope {
  return {
    envelopeRef: stringValue(value, "envelope_ref", fallback.envelopeRef),
    status: stringValue(value, "status", fallback.status),
    setupStepId: stringValue(value, "setup_step_id", fallback.setupStepId),
    setupStepKind: stringValue(
      value,
      "setup_step_kind",
      fallback.setupStepKind,
    ),
    safeSummary: stringValue(value, "safe_summary", fallback.safeSummary),
    requestedScopeRefs: stringArrayValue(
      value,
      "requested_scope_refs",
      fallback.requestedScopeRefs,
    ),
    approvalRequestRef: stringValue(
      value,
      "approval_request_ref",
      fallback.approvalRequestRef,
    ),
    expectedReceiptRef: stringValue(
      value,
      "expected_receipt_ref",
      fallback.expectedReceiptRef,
    ),
    rollbackPlanRef: stringValue(
      value,
      "rollback_plan_ref",
      fallback.rollbackPlanRef,
    ),
    idempotencyKeyRef: stringValue(
      value,
      "idempotency_key_ref",
      fallback.idempotencyKeyRef,
    ),
    riskClass: stringValue(value, "risk_class", fallback.riskClass),
    sideEffectClass: stringValue(
      value,
      "side_effect_class",
      fallback.sideEffectClass,
    ),
    notScopedActions: stringArrayValue(
      value,
      "not_scoped_actions",
      fallback.notScopedActions,
    ),
    blockedRuntimeAuthority: stringArrayValue(
      value,
      "blocked_runtime_authority",
      fallback.blockedRuntimeAuthority,
    ),
    evidenceRefs: stringArrayValue(
      value,
      "evidence_refs",
      fallback.evidenceRefs,
    ),
    verifierRefs: stringArrayValue(
      value,
      "verifier_refs",
      fallback.verifierRefs,
    ),
    operatorNextAction: stringValue(
      value,
      "operator_next_action",
      fallback.operatorNextAction,
    ),
    staleStateHandling: stringValue(
      value,
      "stale_state_handling",
      fallback.staleStateHandling,
    ),
    redactionSummary: stringValue(
      value,
      "redaction_summary",
      fallback.redactionSummary,
    ),
    dryRunOnly: booleanValue(value, "dry_run_only", fallback.dryRunOnly),
    approvalRequired: booleanValue(
      value,
      "approval_required",
      fallback.approvalRequired,
    ),
    approvalRefIsIdentifierOnly: booleanValue(
      value,
      "approval_ref_is_identifier_only",
      fallback.approvalRefIsIdentifierOnly,
    ),
    exactScopeRequired: booleanValue(
      value,
      "exact_scope_required",
      fallback.exactScopeRequired,
    ),
    idempotencyRequired: booleanValue(
      value,
      "idempotency_required",
      fallback.idempotencyRequired,
    ),
    rollbackRequired: booleanValue(
      value,
      "rollback_required",
      fallback.rollbackRequired,
    ),
    redactionRequired: booleanValue(
      value,
      "redaction_required",
      fallback.redactionRequired,
    ),
    disabledByDefault: booleanValue(
      value,
      "disabled_by_default",
      fallback.disabledByDefault,
    ),
    reasonCodes: stringArrayValue(value, "reason_codes", fallback.reasonCodes),
  };
}

function normalizeMacOSSetupStep(
  value: Record<string, unknown>,
  fallback: MacOSSetupAssistantStep,
): MacOSSetupAssistantStep {
  return {
    stepId: stringValue(value, "step_id", fallback.stepId),
    label: stringValue(value, "label", fallback.label),
    kind: stringValue(value, "kind", fallback.kind),
    status: setupStatusValue(value, "status", fallback.status),
    safeSummary: stringValue(value, "safe_summary", fallback.safeSummary),
    routeRefs: stringArrayValue(value, "route_refs", fallback.routeRefs),
    detailPreview: stringArrayValue(
      value,
      "detail_preview",
      fallback.detailPreview,
    ),
    logPreview: stringArrayValue(value, "log_preview", fallback.logPreview),
    approvalRequired: booleanValue(
      value,
      "approval_required",
      fallback.approvalRequired,
    ),
    setupApprovalRef:
      optionalStringValue(value, "approval_ref") ?? fallback.setupApprovalRef,
    receiptRef: stringValue(value, "receipt_ref", fallback.receiptRef),
    rollbackRef: stringValue(value, "rollback_ref", fallback.rollbackRef),
    latencyRef: optionalStringValue(value, "latency_ref") ?? fallback.latencyRef,
    reasonCodes: stringArrayValue(value, "reason_codes", fallback.reasonCodes),
    nextSafeAction: stringValue(
      value,
      "next_safe_action",
      fallback.nextSafeAction,
    ),
  };
}

function normalizeMacOSSetupRecommendation(
  value: Record<string, unknown>,
  fallback: MacOSSetupModelRecommendation,
): MacOSSetupModelRecommendation {
  return {
    recommendationRef: stringValue(
      value,
      "recommendation_ref",
      fallback.recommendationRef,
    ),
    modelRef: stringValue(value, "model_ref", fallback.modelRef),
    displayName: stringValue(value, "display_name", fallback.displayName),
    fitSummary: stringValue(value, "fit_summary", fallback.fitSummary),
    recommendedFor: stringValue(
      value,
      "recommended_for",
      fallback.recommendedFor,
    ),
    memoryBucket: stringValue(value, "memory_bucket", fallback.memoryBucket),
    diskBucket: stringValue(value, "disk_bucket", fallback.diskBucket),
    privacySummary: stringValue(
      value,
      "privacy_summary",
      fallback.privacySummary,
    ),
    approvalRequiredBeforeDownload: booleanValue(
      value,
      "approval_required_before_download",
      fallback.approvalRequiredBeforeDownload,
    ),
    selectedByDefault: booleanValue(
      value,
      "selected_by_default",
      fallback.selectedByDefault,
    ),
    reasonCodes: stringArrayValue(value, "reason_codes", fallback.reasonCodes),
  };
}

function normalizeMacOSSetupBridge(
  value: Record<string, unknown>,
  fallback: MacOSSetupBridgePreview,
): MacOSSetupBridgePreview {
  return {
    bridgeRef: stringValue(value, "bridge_ref", fallback.bridgeRef),
    label: stringValue(value, "label", fallback.label),
    status: setupStatusValue(value, "status", fallback.status),
    safeSummary: stringValue(value, "safe_summary", fallback.safeSummary),
    enablementDefault: stringValue(
      value,
      "enablement_default",
      fallback.enablementDefault,
    ),
    approvalRequired: booleanValue(
      value,
      "approval_required",
      fallback.approvalRequired,
    ),
    reasonCodes: stringArrayValue(value, "reason_codes", fallback.reasonCodes),
  };
}

function normalizeMacOSSetupReceiptPlan(
  value: Record<string, unknown> | undefined,
  fallback: MacOSSetupReceiptPlan,
): MacOSSetupReceiptPlan {
  if (!value) {
    return fallback;
  }
  return {
    receiptPlanRef: stringValue(
      value,
      "receipt_plan_ref",
      fallback.receiptPlanRef,
    ),
    auditRef: stringValue(value, "audit_ref", fallback.auditRef),
    latencyRef: stringValue(value, "latency_ref", fallback.latencyRef),
    safeSummary: stringValue(value, "safe_summary", fallback.safeSummary),
    receiptCreated: booleanValue(
      value,
      "receipt_created",
      fallback.receiptCreated,
    ),
    auditEventCreated: booleanValue(
      value,
      "audit_event_created",
      fallback.auditEventCreated,
    ),
    terminalLogStored: booleanValue(
      value,
      "raw_log_stored",
      fallback.terminalLogStored,
    ),
    promptStored: booleanValue(value, "raw_prompt_stored", fallback.promptStored),
    providerPayloadStored: booleanValue(
      value,
      "raw_provider_payload_stored",
      fallback.providerPayloadStored,
    ),
    credentialMaterialStored: booleanValue(
      value,
      "credential_material_stored",
      fallback.credentialMaterialStored,
    ),
  };
}

function normalizeMacOSSetupRollbackPlan(
  value: Record<string, unknown> | undefined,
  fallback: MacOSSetupRollbackPlan,
): MacOSSetupRollbackPlan {
  if (!value) {
    return fallback;
  }
  return {
    rollbackPlanRef: stringValue(
      value,
      "rollback_plan_ref",
      fallback.rollbackPlanRef,
    ),
    uninstallRef: stringValue(value, "uninstall_ref", fallback.uninstallRef),
    safeSummary: stringValue(value, "safe_summary", fallback.safeSummary),
    rollbackAvailableAfterApproval: false,
    rollbackContractDefined: booleanValue(
      value,
      "rollback_contract_defined",
      fallback.rollbackContractDefined,
    ),
    rollbackExecutionAvailable: false,
    rollbackRehearsalCompleted: false,
    restoreProofAvailable: false,
    blockedReasonRefs: stringArrayValue(
      value,
      "blocked_reason_refs",
      fallback.blockedReasonRefs,
    ),
    nextSafeAction: stringValue(
      value,
      "next_safe_action",
      fallback.nextSafeAction,
    ),
    rollbackExecuted: false,
  };
}

function setupStatusValue(
  value: Record<string, unknown>,
  key: string,
  fallback: MacOSSetupStepStatus,
): MacOSSetupStepStatus {
  const candidate = value[key];
  if (
    typeof candidate === "string" &&
    MACOS_SETUP_STATUSES.has(candidate as MacOSSetupStepStatus)
  ) {
    return candidate as MacOSSetupStepStatus;
  }
  return fallback;
}

function lifecycleStateValue(
  value: Record<string, unknown>,
  key: string,
  fallback: MacOSSetupLifecycleState,
): MacOSSetupLifecycleState {
  const candidate = value[key];
  if (
    typeof candidate === "string" &&
    MACOS_SETUP_LIFECYCLE_STATES.has(candidate as MacOSSetupLifecycleState)
  ) {
    return candidate as MacOSSetupLifecycleState;
  }
  return fallback;
}

function lifecycleStateArrayValue(
  value: Record<string, unknown>,
  key: string,
  fallback: MacOSSetupLifecycleState[],
): MacOSSetupLifecycleState[] {
  const candidate = value[key];
  if (!Array.isArray(candidate)) {
    return fallback;
  }
  const states = candidate.filter(
    (item): item is MacOSSetupLifecycleState =>
      typeof item === "string" &&
      MACOS_SETUP_LIFECYCLE_STATES.has(item as MacOSSetupLifecycleState),
  );
  return states.length > 0 ? states : fallback;
}

function lifecycleOperationValue(
  value: Record<string, unknown>,
  key: string,
  fallback: MacOSSetupLifecycleOperationName,
): MacOSSetupLifecycleOperationName {
  const candidate = value[key];
  if (
    typeof candidate === "string" &&
    MACOS_SETUP_LIFECYCLE_OPERATIONS.has(
      candidate as MacOSSetupLifecycleOperationName,
    )
  ) {
    return candidate as MacOSSetupLifecycleOperationName;
  }
  return fallback;
}

function fallbackItem<T>(items: T[], index: number): T {
  return items[index] ?? (items[0] as T);
}

function recordValue(
  value: Record<string, unknown>,
  key: string,
): Record<string, unknown> | undefined {
  const candidate = value[key];
  return isRecord(candidate) ? candidate : undefined;
}

function recordsValue(
  value: Record<string, unknown>,
  key: string,
): Record<string, unknown>[] {
  const candidate = value[key];
  return Array.isArray(candidate) ? candidate.filter(isRecord) : [];
}

function recordArray(
  value: unknown,
  allowEmpty = false,
): Record<string, unknown>[] | undefined {
  if (
    !Array.isArray(value) ||
    (!allowEmpty && value.length === 0) ||
    value.length > MACOS_SETUP_MAX_COLLECTION_ITEMS ||
    !value.every(isRecord)
  ) {
    return undefined;
  }
  return value;
}

function isSetupStatus(value: unknown): value is MacOSSetupStepStatus {
  return (
    typeof value === "string" &&
    MACOS_SETUP_STATUSES.has(value as MacOSSetupStepStatus)
  );
}

function isSafeRef(value: unknown): value is string {
  return (
    typeof value === "string" &&
    MACOS_SETUP_SAFE_REF_RE.test(value) &&
    !containsSecretLike(value)
  );
}

function isSafeOptionalRef(value: unknown): boolean {
  return value === undefined || value === null || isSafeRef(value);
}

function isSafePrefixedRef(value: unknown, prefix: string): value is string {
  return isSafeRef(value) && value.startsWith(prefix);
}

function isSafeApprovalRequestRef(value: unknown): value is string {
  return (
    isSafeRef(value) &&
    !value.startsWith("approval_test") &&
    (value.startsWith("approval-ref:") ||
      value.startsWith("approval-request-ref:"))
  );
}

function isSafeRefArray(
  value: unknown,
  requireNonEmpty = false,
): value is string[] {
  return (
    Array.isArray(value) &&
    (!requireNonEmpty || value.length > 0) &&
    value.length <= MACOS_SETUP_MAX_COLLECTION_ITEMS &&
    value.every(isSafeRef)
  );
}

function isSafeRouteArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.length <= MACOS_SETUP_MAX_COLLECTION_ITEMS &&
    value.every(
      (item) =>
        typeof item === "string" &&
        MACOS_SETUP_SAFE_ROUTE_RE.test(item) &&
        !containsSecretLike(item),
    )
  );
}

function isSafeText(value: unknown, maxLength: number): value is string {
  if (typeof value !== "string") {
    return false;
  }
  const text = value.trim();
  return (
    text.length > 0 &&
    Array.from(text).length <= maxLength &&
    MACOS_SETUP_SAFE_TEXT_RE.test(text) &&
    !MACOS_SETUP_ABSOLUTE_PATH_RE.test(text) &&
    !containsSecretLike(text)
  );
}

function isSafeTextArray(value: unknown, maxLength: number): value is string[] {
  return (
    Array.isArray(value) &&
    value.length <= MACOS_SETUP_MAX_COLLECTION_ITEMS &&
    value.every((item) => isSafeText(item, maxLength))
  );
}

function isSafeEnvelopeText(value: unknown): value is string {
  return (
    isSafeText(value, MACOS_SETUP_MAX_DETAIL_CHARS) &&
    !MACOS_SETUP_RUNTIME_TEXT_FRAGMENTS.some((fragment) =>
      value.toLowerCase().includes(fragment),
    )
  );
}

function stringValue(
  value: Record<string, unknown>,
  key: string,
  fallback: string,
): string {
  const candidate = value[key];
  return typeof candidate === "string" ? candidate : fallback;
}

function optionalStringValue(
  value: Record<string, unknown>,
  key: string,
): string | undefined {
  const candidate = value[key];
  return typeof candidate === "string" ? candidate : undefined;
}

function booleanValue(
  value: Record<string, unknown>,
  key: string,
  fallback: boolean,
): boolean {
  const candidate = value[key];
  return typeof candidate === "boolean" ? candidate : fallback;
}

function stringArrayValue(
  value: Record<string, unknown>,
  key: string,
  fallback: string[],
): string[] {
  const candidate = value[key];
  if (!Array.isArray(candidate)) {
    return fallback;
  }
  return candidate.filter((item): item is string => typeof item === "string");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
