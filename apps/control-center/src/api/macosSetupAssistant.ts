import type {
  MacOSSetupAssistantData,
  MacOSSetupAssistantStep,
  MacOSSetupBridgePreview,
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

export function normalizeMacOSSetupAssistant(
  value: unknown,
  fallback: MacOSSetupAssistantData,
): MacOSSetupAssistantData {
  if (!isRecord(value)) {
    return fallback;
  }
  const steps = recordsValue(value, "steps");
  const recommendations = recordsValue(value, "model_recommendations");
  const bridges = recordsValue(value, "bridge_previews");
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
