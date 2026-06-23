export const API_ENDPOINTS = {
  health: "/health",
  version: "/version",
  apiManifest: "/api/manifest",
  controlCenterManifest: "/control-center/manifest",
  controlCenterDashboard: "/control-center/dashboard",
  controlCenterStatus: "/control-center/status",
  controlCenterRoutes: "/control-center/routes",
  approvalSummary: "/control-center/approvals/summary",
  runtimeReadinessSummary: "/control-center/runtime-readiness/summary",
  foundationGateSummary: "/control-center/foundation-gate/summary",
  setupAssistantSummary: "/control-center/setup-assistant/summary",
  founderTodaySummary: "/control-center/today/summary",
  founderTodayActionEnvelope: "/control-center/today/action-envelope",
  founderEvidenceTimeline: "/control-center/evidence/timeline",
  controlCenterChatTurns: "/control-center/chat/turns",
  founderMemoryReview: "/control-center/memory/review",
  founderActionsInbox: "/control-center/actions/inbox",
  founderMorningBriefing: "/control-center/morning-briefing/summary",
  founderStorageStatus: "/control-center/storage/status",
  runtimeReadiness: "/runtime/readiness",
  runtimeCapabilityMatrix: "/runtime/capability-matrix",
  runtimeSmokeReportValidate: "/runtime/smoke-reports/validate",
  localModels: "/v1/models",
  localChatCompletions: "/v1/chat/completions",
  actionPreview: "/control-center/actions/preview",
} as const;

export const ACTION_DECISION_KINDS = [
  "approve",
  "edit",
  "reject",
  "defer",
] as const;

export type ActionDecisionKind = (typeof ACTION_DECISION_KINDS)[number];
export const MEMORY_REVIEW_DECISION_KINDS = [
  "accept",
  "correct",
  "reject",
] as const;

export type MemoryReviewDecisionKind =
  (typeof MEMORY_REVIEW_DECISION_KINDS)[number];

export function actionDecisionEndpoint(
  actionId: string,
  decision: ActionDecisionKind,
): string {
  return `/control-center/actions/${encodeURIComponent(actionRouteId(actionId))}/${decision}`;
}

export function actionReceiptEndpoint(actionId: string): string {
  return `/control-center/actions/${encodeURIComponent(actionRouteId(actionId))}/receipt`;
}

export function chatTurnReceiptEndpoint(turnRef: string): string {
  return `/control-center/chat/turns/${encodeURIComponent(turnRef)}/receipt`;
}

export function chatTurnHandoffEndpoint(turnRef: string): string {
  return `/control-center/chat/turns/${encodeURIComponent(turnRef)}/handoff`;
}

export function memoryReviewDecisionEndpoint(
  candidateRef: string,
  decision: MemoryReviewDecisionKind,
): string {
  return `/control-center/memory/review/${encodeURIComponent(candidateRef)}/${decision}`;
}

export function memoryReviewReceiptEndpoint(candidateRef: string): string {
  return `/control-center/memory/review/${encodeURIComponent(candidateRef)}/receipt`;
}

export function isActionDecisionEndpoint(endpoint: string): boolean {
  return /^\/control-center\/actions\/[^/]+\/(approve|edit|reject|defer)$/.test(
    endpoint,
  );
}

function actionRouteId(actionId: string): string {
  return actionId.startsWith("founder-action:")
    ? actionId.slice("founder-action:".length)
    : actionId;
}

export const READ_ENDPOINTS = [
  API_ENDPOINTS.health,
  API_ENDPOINTS.version,
  API_ENDPOINTS.apiManifest,
  API_ENDPOINTS.controlCenterManifest,
  API_ENDPOINTS.controlCenterDashboard,
  API_ENDPOINTS.controlCenterStatus,
  API_ENDPOINTS.controlCenterRoutes,
  API_ENDPOINTS.approvalSummary,
  API_ENDPOINTS.runtimeReadinessSummary,
  API_ENDPOINTS.foundationGateSummary,
  API_ENDPOINTS.setupAssistantSummary,
  API_ENDPOINTS.founderTodaySummary,
  API_ENDPOINTS.founderEvidenceTimeline,
  API_ENDPOINTS.founderMemoryReview,
  API_ENDPOINTS.founderActionsInbox,
  API_ENDPOINTS.founderMorningBriefing,
  API_ENDPOINTS.founderStorageStatus,
  API_ENDPOINTS.runtimeReadiness,
  API_ENDPOINTS.runtimeCapabilityMatrix,
] as const;

export function isAllowedReadEndpoint(
  endpoint: string,
): endpoint is (typeof READ_ENDPOINTS)[number] {
  return READ_ENDPOINTS.includes(endpoint as (typeof READ_ENDPOINTS)[number]);
}

export function isPreviewEndpoint(
  endpoint: string,
): endpoint is typeof API_ENDPOINTS.actionPreview {
  return endpoint === API_ENDPOINTS.actionPreview;
}

export function isRuntimeValidationEndpoint(
  endpoint: string,
): endpoint is typeof API_ENDPOINTS.runtimeSmokeReportValidate {
  return endpoint === API_ENDPOINTS.runtimeSmokeReportValidate;
}
