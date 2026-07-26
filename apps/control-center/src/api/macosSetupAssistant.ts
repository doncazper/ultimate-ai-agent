import type {
  MacOSSetupAssistantData,
  MacOSSetupAssistantStep,
  MacOSSetupApprovalEnvelope,
  MacOSSetupBridgePreview,
  MacOSSetupHealthContract,
  MacOSSetupLifecycleContract,
  MacOSSetupLifecycleOperation,
  MacOSSetupLifecycleOperationName,
  MacOSSetupLifecycleState,
  MacOSSetupModelRecommendation,
  MacOSSetupReceiptPlan,
  MacOSSetupRollbackPlan,
  MacOSSetupStepStatus,
} from "./types";

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
export function normalizeMacOSSetupAssistant(
  source: unknown,
  fallback: MacOSSetupAssistantData,
): { value: MacOSSetupAssistantData; usedFallback: boolean } {
  const value = normalizeMacOSSetupAssistantValue(source, fallback);
  const probeFallback = alternateFallback(fallback);
  const probeValue = normalizeMacOSSetupAssistantValue(source, probeFallback);
  return {
    value,
    usedFallback:
      lifecycleSourceRequiresFallback(source) ||
      JSON.stringify(value) !== JSON.stringify(probeValue),
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

function lifecycleSourceRequiresFallback(source: unknown): boolean {
  if (!isRecord(source)) {
    return true;
  }
  const lifecycle = recordValue(source, "lifecycle");
  if (
    !lifecycle ||
    lifecycle.status !== "blocked_by_authority" ||
    lifecycle.current_state !== "prerequisites" ||
    !hasExactStringSequence(
      lifecycle.state_sequence,
      MACOS_SETUP_LIFECYCLE_STATE_SEQUENCE,
    ) ||
    !hasExactLifecycleOperationSequence(lifecycle.operations) ||
    !allBooleanFieldsEqual(
      lifecycle,
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
    )
  ) {
    return true;
  }

  const operations = lifecycle.operations as Record<string, unknown>[];
  const operationProofFields = [
    "authority_granted",
    "state_change_performed",
    "subprocess_executed",
    "file_mutation_performed",
    "process_mutation_performed",
    "credential_write_performed",
    "network_request_performed",
    "receipt_persisted",
  ];
  if (
    operations.some((operation, index) => {
      const operationName = MACOS_SETUP_LIFECYCLE_OPERATION_SEQUENCE[index];
      const readOnly =
        operationName === "plan" ||
        operationName === "status" ||
        operationName === "receipts";
      return (
        operation.status !==
          (readOnly ? "available_read_only" : "blocked_by_authority") ||
        operation.current_state !== "prerequisites" ||
        operation.approval_required !== !readOnly ||
        !allBooleanFieldsEqual(operation, operationProofFields, false) ||
        (readOnly &&
          (operation.mutation_required !== false ||
            operation.live_probe_required !== false))
      );
    })
  ) {
    return true;
  }

  const healthContract = recordValue(lifecycle, "health_contract");
  return (
    !healthContract ||
    healthContract.status !== "blocked_by_authority" ||
    !allBooleanFieldsEqual(
      healthContract,
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
    rollbackAvailableAfterApproval: booleanValue(
      value,
      "rollback_available_after_approval",
      fallback.rollbackAvailableAfterApproval,
    ),
    rollbackExecuted: booleanValue(
      value,
      "rollback_executed",
      fallback.rollbackExecuted,
    ),
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
