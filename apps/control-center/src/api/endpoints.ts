export const API_ENDPOINTS = {
  health: "/health",
  version: "/version",
  apiManifest: "/api/manifest",
  controlCenterManifest: "/control-center/manifest",
  controlCenterDashboard: "/control-center/dashboard",
  controlCenterStatus: "/control-center/status",
  controlCenterRoutes: "/control-center/routes",
  approvalSummary: "/control-center/approvals/summary",
  approvalQueue: "/control-center/approvals/queue",
  runObservability: "/control-center/runs/observability",
  runtimeReadinessSummary: "/control-center/runtime-readiness/summary",
  foundationGateSummary: "/control-center/foundation-gate/summary",
  setupAssistantSummary: "/control-center/setup-assistant/summary",
  providerSetupGuide: "/control-center/providers/setup-guide",
  controlCenterSettingsStatus: "/control-center/settings/status",
  controlCenterLocalModelsStatus: "/control-center/local-models/status",
  founderTodaySummary: "/control-center/today/summary",
  founderStartHereSummary: "/control-center/start-here/summary",
  controlCenterCodingSession: "/control-center/coding/session",
  controlCenterCodingContext: "/control-center/coding/context",
  controlCenterCodingPatchProposal: "/control-center/coding/patch-proposal",
  controlCenterCodingPatchApplyReadiness:
    "/control-center/coding/patch-apply-readiness",
  controlCenterCodingTestCommandReadiness:
    "/control-center/coding/test-command-readiness",
  controlCenterCodingGitReview: "/control-center/coding/git-review",
  controlCenterCodingLivePreview: "/control-center/coding/live-preview",
  controlCenterCodingMultiAgentReview:
    "/control-center/coding/multi-agent-review",
  controlCenterWorkBoard: "/control-center/work-board",
  controlCenterWorkBoardReorder: "/control-center/work-board/reorder",
  controlCenterProofIndex: "/control-center/proof/index",
  trustAuthorityMatrix: "/control-center/trust-authority/matrix",
  founderTodayActionEnvelope: "/control-center/today/action-envelope",
  controlCenterWebEvidenceAttach: "/control-center/web-evidence/attach",
  founderEvidenceTimeline: "/control-center/evidence/timeline",
  controlCenterChatTurns: "/control-center/chat/turns",
  founderMemoryReview: "/control-center/memory/review",
  founderMemoryWorkbench: "/control-center/memory/workbench",
  founderMemorySearch: "/control-center/memory/search",
  founderMemoryManualCandidate: "/control-center/memory/review/manual-candidate",
  founderMemoryContextPacks: "/control-center/memory/context-packs",
  founderMemoryRetrievalDiagnostics:
    "/control-center/memory/retrieval-diagnostics",
  founderMemoryCitationIntegrity: "/control-center/memory/citation-integrity",
  founderMemoryQualityIssues: "/control-center/memory/quality-issues",
  founderMemoryFeedback: "/control-center/memory/feedback",
  founderMemoryMaintenanceRuns: "/control-center/memory/maintenance-runs",
  founderMemoryContextManifest: "/control-center/memory/context-manifest",
  founderMemoryObservationCandidates: "/control-center/memory/observation-candidates",
  founderMemoryProbe: "/control-center/memory/probe",
  founderMemoryContradictions: "/control-center/memory/contradictions",
  founderActionsInbox: "/control-center/actions/inbox",
  founderMorningBriefing: "/control-center/morning-briefing/summary",
  founderSourceReadiness: "/control-center/sources/readiness",
  founderStorageStatus: "/control-center/storage/status",
  runtimeReadiness: "/runtime/readiness",
  runtimeCapabilityMatrix: "/runtime/capability-matrix",
  runtimeSmokeReportValidate: "/runtime/smoke-reports/validate",
  localModels: "/v1/models",
  localChatCompletions: "/v1/chat/completions",
  actionPreview: "/control-center/actions/preview",
  turnRouterPreview: "/control-center/turn-router/preview",
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
  "defer",
  "merge",
  "supersede",
  "forget_request",
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

export function actionLocalTaskCommitEndpoint(actionId: string): string {
  return `/control-center/actions/${encodeURIComponent(actionRouteId(actionId))}/local-task/commit`;
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
  const routeDecision = decision === "forget_request" ? "forget-request" : decision;
  return `/control-center/memory/review/${encodeURIComponent(candidateRef)}/${routeDecision}`;
}

export function memoryReviewReceiptEndpoint(candidateRef: string): string {
  return `/control-center/memory/review/${encodeURIComponent(candidateRef)}/receipt`;
}

export function memoryContextPackActionProposalEndpoint(
  contextPackRef: string,
): string {
  return `/control-center/memory/context-packs/${encodeURIComponent(contextPackRef)}/action-proposal`;
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
  API_ENDPOINTS.approvalQueue,
  API_ENDPOINTS.runObservability,
  API_ENDPOINTS.runtimeReadinessSummary,
  API_ENDPOINTS.foundationGateSummary,
  API_ENDPOINTS.setupAssistantSummary,
  API_ENDPOINTS.providerSetupGuide,
  API_ENDPOINTS.controlCenterSettingsStatus,
  API_ENDPOINTS.controlCenterLocalModelsStatus,
  API_ENDPOINTS.founderTodaySummary,
  API_ENDPOINTS.founderStartHereSummary,
  API_ENDPOINTS.controlCenterCodingSession,
  API_ENDPOINTS.controlCenterCodingContext,
  API_ENDPOINTS.controlCenterCodingPatchProposal,
  API_ENDPOINTS.controlCenterCodingPatchApplyReadiness,
  API_ENDPOINTS.controlCenterCodingTestCommandReadiness,
  API_ENDPOINTS.controlCenterCodingGitReview,
  API_ENDPOINTS.controlCenterCodingLivePreview,
  API_ENDPOINTS.controlCenterCodingMultiAgentReview,
  API_ENDPOINTS.controlCenterWorkBoard,
  API_ENDPOINTS.controlCenterProofIndex,
  API_ENDPOINTS.trustAuthorityMatrix,
  API_ENDPOINTS.founderEvidenceTimeline,
  API_ENDPOINTS.founderMemoryReview,
  API_ENDPOINTS.founderMemoryWorkbench,
  API_ENDPOINTS.founderMemorySearch,
  API_ENDPOINTS.founderMemoryContextPacks,
  API_ENDPOINTS.founderMemoryRetrievalDiagnostics,
  API_ENDPOINTS.founderMemoryCitationIntegrity,
  API_ENDPOINTS.founderMemoryQualityIssues,
  API_ENDPOINTS.founderMemoryMaintenanceRuns,
  API_ENDPOINTS.founderMemoryContextManifest,
  API_ENDPOINTS.founderMemoryObservationCandidates,
  API_ENDPOINTS.founderMemoryProbe,
  API_ENDPOINTS.founderMemoryContradictions,
  API_ENDPOINTS.founderActionsInbox,
  API_ENDPOINTS.founderMorningBriefing,
  API_ENDPOINTS.founderSourceReadiness,
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
): endpoint is
  | typeof API_ENDPOINTS.actionPreview
  | typeof API_ENDPOINTS.turnRouterPreview {
  return (
    endpoint === API_ENDPOINTS.actionPreview ||
    endpoint === API_ENDPOINTS.turnRouterPreview
  );
}

export function isRuntimeValidationEndpoint(
  endpoint: string,
): endpoint is typeof API_ENDPOINTS.runtimeSmokeReportValidate {
  return endpoint === API_ENDPOINTS.runtimeSmokeReportValidate;
}
