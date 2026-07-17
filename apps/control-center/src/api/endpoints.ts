export const API_ENDPOINTS = {
  health: "/health",
  version: "/version",
  apiManifest: "/api/manifest",
  controlCenterManifest: "/control-center/manifest",
  controlCenterDashboard: "/control-center/dashboard",
  controlCenterStatus: "/control-center/status",
  controlCenterRoutes: "/control-center/routes",
  controlCenterCapabilitySurface: "/control-center/capabilities/surface",
  approvalSummary: "/control-center/approvals/summary",
  approvalQueue: "/control-center/approvals/queue",
  runObservability: "/control-center/runs/observability",
  runtimeReadinessSummary: "/control-center/runtime-readiness/summary",
  foundationGateSummary: "/control-center/foundation-gate/summary",
  setupAssistantSummary: "/control-center/setup-assistant/summary",
  providerSetupGuide: "/control-center/providers/setup-guide",
  modelProviderControlPlane: "/control-center/providers/runtime-control-plane",
  controlCenterSettingsStatus: "/control-center/settings/status",
  controlCenterLocalModelsStatus: "/control-center/local-models/status",
  communicationsProviders: "/control-center/communications/providers",
  communicationsSessionPosture:
    "/control-center/communications/session-posture",
  communicationsMatrixSyncPosture:
    "/control-center/communications/matrix-sync/posture",
  communicationsMatrixCryptoPosture:
    "/control-center/communications/matrix-crypto/posture",
  communicationsMatrixMessagingPosture:
    "/control-center/communications/matrix-messaging/posture",
  communicationsRooms: "/control-center/communications/rooms",
  communicationsFailedSends: "/control-center/communications/failed-sends",
  communicationsSecurityPosture:
    "/control-center/communications/security-posture",
  founderTodaySummary: "/control-center/today/summary",
  founderAgentLoopThread: "/control-center/agent-loop/thread",
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
  controlCenterWorkBoardCards: "/control-center/work-board/cards",
  controlCenterWorkBoardReorder: "/control-center/work-board/reorder",
  controlCenterWorkBoardTasks: "/control-center/work-board/tasks",
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
  crmSummary: "/control-center/crm/summary",
  crmRelationships: "/control-center/crm/relationships",
  crmTimeline: "/control-center/crm/timeline",
  crmFollowUps: "/control-center/crm/follow-ups",
  crmPipelines: "/control-center/crm/pipelines",
  crmSmartLists: "/control-center/crm/smart-lists",
  runtimeReadiness: "/runtime/readiness",
  runtimeCapabilityMatrix: "/runtime/capability-matrix",
  runtimeDelegationAdapter: "/api/runtime/delegation-adapter",
  runtimeInterfaceMode: "/api/runtime/interface-mode",
  runtimeHermesContextPack: "/api/runtime/hermes/context-pack",
  runtimeCapabilityDiscovery: "/api/runtime/capability-discovery",
  runtimeRunEvents: "/api/runtime/run-events",
  runtimeApprovalBridge: "/api/runtime/approval-bridge",
  runtimeStreamingProgress: "/api/runtime/streaming-progress",
  runtimeProfiles: "/api/runtime/profiles",
  runtimeToolRegistry: "/api/runtime/tool-registry",
  runtimeVirtualProviderMoa: "/api/runtime/virtual-provider-moa",
  runtimeUsageCostAnalytics: "/api/runtime/usage-cost-analytics",
  runtimePromptStabilityTiers: "/api/runtime/prompt-stability-tiers",
  runtimeContextBudgetPressure: "/api/runtime/context-budget-pressure",
  runtimeHardlineCommandBlocklist: "/api/runtime/hardline-command-blocklist",
  runtimeManagedScopePolicy: "/api/runtime/managed-scope-policy",
  runtimeDoctorDiagnostics: "/api/runtime/doctor-diagnostics",
  runtimeSessionContinuity: "/api/runtime/session-continuity",
  runtimeMcpCatalogFiltering: "/api/runtime/mcp-catalog-filtering",
  runtimeBackgroundJobs: "/api/runtime/background-jobs",
  runtimeSubagentIsolation: "/api/runtime/subagent-isolation",
  runtimeWorktreePerAgent: "/api/runtime/worktree-per-agent",
  runtimeStagedOrchestration: "/api/runtime/staged-orchestration",
  runtimeLspDiagnostics: "/api/runtime/lsp-diagnostics",
  runtimePreviewRail: "/api/runtime/preview-rail",
  runtimeSlashCommandRegistry: "/api/runtime/slash-command-registry",
  runtimeInterruptRedirect: "/api/runtime/interrupt-redirect",
  runtimeLoggingProfile: "/api/runtime/logging-profile",
  runtimeResultClassification: "/api/runtime/result-classification",
  runtimeVoiceMediaPosture: "/api/runtime/voice-media-posture",
  runtimeMessagingGatewayPosture: "/api/runtime/messaging-gateway-posture",
  runtimeRemoteExecutionPosture: "/api/runtime/remote-execution-posture",
  runtimePluginMetadataPosture: "/api/runtime/plugin-metadata-posture",
  runtimeSkillMarketplacePosture: "/api/runtime/skill-marketplace-posture",
  runtimeAuthorityDecisionPreview: "/api/runtime/authority-decisions/preview",
  runtimeAuthorityMissionPlan: "/api/runtime/authority-missions/plan",
  runtimeAuthorityMissionWorkerState:
    "/api/runtime/authority-missions/worker-state",
  runtimeAuthorityMissionCompletions:
    "/api/runtime/authority-missions/completions",
  runtimeAuthorityLeases: "/api/runtime/authority-leases",
  runtimeAuthorityLeasesApproveAndIssue:
    "/api/runtime/authority-leases/approve-and-issue",
  runtimeAuthorityLeaseRevoke: "/api/runtime/authority-leases/revoke",
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
  "expire",
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

export function communicationsReceiptEndpoint(receiptRef: string): string {
  return `/control-center/communications/receipts/${encodeURIComponent(receiptRef)}`;
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
  API_ENDPOINTS.controlCenterCapabilitySurface,
  API_ENDPOINTS.approvalSummary,
  API_ENDPOINTS.approvalQueue,
  API_ENDPOINTS.runObservability,
  API_ENDPOINTS.runtimeReadinessSummary,
  API_ENDPOINTS.foundationGateSummary,
  API_ENDPOINTS.setupAssistantSummary,
  API_ENDPOINTS.providerSetupGuide,
  API_ENDPOINTS.modelProviderControlPlane,
  API_ENDPOINTS.controlCenterSettingsStatus,
  API_ENDPOINTS.runtimeAuthorityMissionWorkerState,
  API_ENDPOINTS.controlCenterLocalModelsStatus,
  API_ENDPOINTS.communicationsProviders,
  API_ENDPOINTS.communicationsSessionPosture,
  API_ENDPOINTS.communicationsRooms,
  API_ENDPOINTS.communicationsFailedSends,
  API_ENDPOINTS.communicationsSecurityPosture,
  API_ENDPOINTS.founderTodaySummary,
  API_ENDPOINTS.founderAgentLoopThread,
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
  API_ENDPOINTS.crmSummary,
  API_ENDPOINTS.crmRelationships,
  API_ENDPOINTS.crmTimeline,
  API_ENDPOINTS.crmFollowUps,
  API_ENDPOINTS.crmPipelines,
  API_ENDPOINTS.crmSmartLists,
  API_ENDPOINTS.runtimeReadiness,
  API_ENDPOINTS.runtimeCapabilityMatrix,
  API_ENDPOINTS.runtimeDelegationAdapter,
  API_ENDPOINTS.runtimeInterfaceMode,
  API_ENDPOINTS.runtimeHermesContextPack,
  API_ENDPOINTS.runtimeCapabilityDiscovery,
  API_ENDPOINTS.runtimeRunEvents,
  API_ENDPOINTS.runtimeApprovalBridge,
  API_ENDPOINTS.runtimeStreamingProgress,
  API_ENDPOINTS.runtimeProfiles,
  API_ENDPOINTS.runtimeToolRegistry,
  API_ENDPOINTS.runtimeVirtualProviderMoa,
  API_ENDPOINTS.runtimeUsageCostAnalytics,
  API_ENDPOINTS.runtimePromptStabilityTiers,
  API_ENDPOINTS.runtimeContextBudgetPressure,
  API_ENDPOINTS.runtimeHardlineCommandBlocklist,
  API_ENDPOINTS.runtimeManagedScopePolicy,
  API_ENDPOINTS.runtimeDoctorDiagnostics,
  API_ENDPOINTS.runtimeSessionContinuity,
  API_ENDPOINTS.runtimeMcpCatalogFiltering,
  API_ENDPOINTS.runtimeBackgroundJobs,
  API_ENDPOINTS.runtimeSubagentIsolation,
  API_ENDPOINTS.runtimeWorktreePerAgent,
  API_ENDPOINTS.runtimeStagedOrchestration,
  API_ENDPOINTS.runtimeLspDiagnostics,
  API_ENDPOINTS.runtimePreviewRail,
  API_ENDPOINTS.runtimeSlashCommandRegistry,
  API_ENDPOINTS.runtimeInterruptRedirect,
  API_ENDPOINTS.runtimeLoggingProfile,
  API_ENDPOINTS.runtimeResultClassification,
  API_ENDPOINTS.runtimeVoiceMediaPosture,
  API_ENDPOINTS.runtimeMessagingGatewayPosture,
  API_ENDPOINTS.runtimeRemoteExecutionPosture,
  API_ENDPOINTS.runtimePluginMetadataPosture,
  API_ENDPOINTS.runtimeSkillMarketplacePosture,
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
