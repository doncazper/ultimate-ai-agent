import { mockControlCenterData } from "../mocks/controlCenterData";
import type {
  ActionPreviewDecision,
  ActionPreviewRequest,
  BackendConnectionSummary,
  CodingCockpitSessionReadModel,
  CodingWorkspaceContextReadModel,
  ControlCenterDashboardSnapshot,
  ControlCenterData,
  ControlCenterLocalModelsStatus,
  ControlCenterManifest,
  ControlCenterProofIndex,
  ControlCenterRouteReadState,
  ControlCenterRouteReadStateKind,
  ControlCenterStartHereSummary,
  ControlCenterSettingsStatus,
  ControlCenterStatus,
  CrmLocalCommandCenterReadModel,
  TrustAuthorityMatrix,
  TurnHarnessBindingReadModel,
  TurnRouterPreviewReadModel,
  TurnRouterPreviewRequest,
  FounderLoopAgentLoopThread,
  FounderLoopActionsInbox,
  FounderLoopMorningBriefing,
  FounderLoopSourceReadiness,
  FounderLoopStorageStatus,
  FounderLoopTodaySummary,
  LocalModelsInspectionStatus,
  ModelProviderControlPlaneReadModel,
  ProviderCatalog,
  RedactedLocalChatProbeStatus,
  ResultEnvelope,
  RunAttachedApprovalQueue,
  RunObservabilityReadModel,
  RuntimeApprovalBridgeReadModel,
  RuntimeCapabilityMatrix,
  RuntimeCapabilityDiscoveryReadModel,
  RuntimeDelegationAdapterReadModel,
  RuntimeRunEventsReadModel,
  RuntimeStreamingProgressReadModel,
  RuntimeProfileIsolationReadModel,
  RuntimeReadinessReport,
  ApiRouteInventory,
  FounderLoopActionDecisionKind,
  FounderLoopActionDecisionReceipt,
  FounderLoopActionDecisionRequest,
  FounderLoopActionEnvelopePromotionReceipt,
  FounderLoopActionEnvelopePromotionRequest,
  FounderLoopEvidenceTimelineIndex,
  FounderLoopMemoryContextPackActionProposalReceipt,
  FounderLoopMemoryContextPackActionProposalRequest,
  FounderLoopMemoryContextPacks,
  FounderLoopMemoryCitationIntegrity,
  FounderLoopMemoryContextManifest,
  FounderLoopMemoryMaintenanceRuns,
  FounderLoopMemoryQualityIssues,
  FounderLoopMemoryReview,
  FounderLoopMemoryRetrievalDiagnostics,
  FounderLoopMemoryWorkbench,
  FounderLoopRunsIntegrationReadModel,
  FounderLoopTraceRefs,
  FounderLoopLocalTaskCommitReceipt,
  FounderLoopLocalTaskCommitRequest,
  ManualMemoryCandidateReceipt,
  ManualMemoryCandidateRequest,
  MemoryFeedbackReceipt,
  MemoryFeedbackRequest,
  MemoryReviewDecisionKind,
  MemoryReviewDecisionReceipt,
  MemoryReviewDecisionRequest,
  ProviderCredentialReadinessSummary,
  ProviderCredentialReadinessPosture,
  ChatHandoffReceipt,
  ChatHandoffRequest,
  ChatHandoffTarget,
  ChatTurnReceipt,
  ChatTurnReceiptRequest,
  CodingGitReviewReadModel,
  CodingLivePreviewReadModel,
  CodingMultiAgentReviewReadModel,
  CodingPatchApplyReadinessReadModel,
  CodingPatchProposalReadModel,
  CodingTestCommandReadinessReadModel,
  WebEvidenceProductSliceReceipt,
  WebEvidenceProductSliceRequest,
  WorkBoardReadModel,
  WorkBoardReorderReceipt,
  WorkBoardReorderRequest,
} from "./types";
import { resolveApiBaseUrl } from "./baseUrl";
import {
  API_ENDPOINTS,
  actionDecisionEndpoint,
  actionLocalTaskCommitEndpoint,
  chatTurnHandoffEndpoint,
  chatTurnReceiptEndpoint,
  memoryContextPackActionProposalEndpoint,
  memoryReviewDecisionEndpoint,
  memoryReviewReceiptEndpoint,
} from "./endpoints";
import { normalizeMacOSSetupAssistant } from "./macosSetupAssistant";
import { sanitizeForDisplay } from "./redaction";

const API_BASE_POLICY = resolveApiBaseUrl(
  import.meta.env.VITE_UAA_API_BASE_URL,
);
export const CONTROL_CENTER_READ_TIMEOUT_MS = 8000;
export const CONTROL_CENTER_MAX_CONCURRENT_READS = 8;
const DEFAULT_LOCAL_MODEL_ID = "uaa-llama-cpp-local";
const CHAT_OPERATOR_CONTRACT_REF =
  "contract-ref:chat-local-operator-surface:v1";
const CHAT_OPERATOR_BLOCKED_REFS = [
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
];
const PROVIDER_READINESS_POSTURES = [
  "configured",
  "not_configured",
  "revoked",
  "blocked",
  "validation_blocked",
  "invocation_blocked",
  "vault_blocked",
  "cost_blocked",
  "unknown_paid_cost_requires_approval",
] as const;
const PROVIDER_SETTINGS_DIAGNOSTIC_STATES = [
  "configured",
  "missing",
  "blocked",
  "degraded",
  "revoked",
  "expired",
  "cost_blocked",
  "disabled",
  "future_scoped",
] as const;
const REQUIRED_PROVIDER_COST_BLOCKERS = [
  "UNKNOWN_PAID_COST_REQUIRES_APPROVAL",
  "PROVIDER_MODEL_REFS_REQUIRED",
  "COST_ESTIMATE_REF_REQUIRED",
  "BUDGET_DECISION_REF_REQUIRED",
  "MAX_APPROVED_USD_REF_REQUIRED",
  "FUTURE_RECEIPT_REFS_REQUIRED",
  "PROVIDER_USAGE_CLAIM_REQUIRES_RECEIPT_REFS",
] as const;

let sessionLocalApiBearer: string | null = null;

interface ControlCenterReadLimiter {
  acquire: () => Promise<void>;
  release: () => void;
  reset: () => void;
}

function createControlCenterReadLimiter(): ControlCenterReadLimiter {
  let activeReadCount = 0;
  const pendingReadStarts: Array<() => void> = [];
  return {
    async acquire() {
      if (activeReadCount < CONTROL_CENTER_MAX_CONCURRENT_READS) {
        activeReadCount += 1;
        return;
      }
      await new Promise<void>((resolve) => {
        pendingReadStarts.push(resolve);
      });
      activeReadCount += 1;
    },
    release() {
      activeReadCount = Math.max(activeReadCount - 1, 0);
      const next = pendingReadStarts.shift();
      if (next) {
        next();
      }
    },
    reset() {
      activeReadCount = 0;
      pendingReadStarts.splice(0);
    },
  };
}

const defaultControlCenterReadLimiter = createControlCenterReadLimiter();

export function setLocalApiBearerForSession(value: string | null): void {
  const trimmed = value?.trim() ?? "";
  sessionLocalApiBearer = trimmed.length > 0 ? trimmed : null;
}

export function resetControlCenterReadLimiterForTests(): void {
  defaultControlCenterReadLimiter.reset();
}

function localApiBearerForRequest(): string | null {
  const configured = String(
    import.meta.env.VITE_UAA_LOCAL_API_BEARER ?? "",
  ).trim();
  return sessionLocalApiBearer ?? (configured.length > 0 ? configured : null);
}

function withLocalApiAuthHeaders(
  headers: Record<string, string>,
): Record<string, string> {
  const bearer = localApiBearerForRequest();
  if (!bearer) {
    return headers;
  }
  return {
    ...headers,
    Authorization: `Bearer ${bearer}`,
  };
}

async function readEnvelope<T>(
  endpoint: string,
  readLimiter = defaultControlCenterReadLimiter,
): Promise<T> {
  await readLimiter.acquire();
  try {
    const response = await withReadTimeout(
      fetch(`${API_BASE_POLICY.baseUrl}${endpoint}`, {
        headers: withLocalApiAuthHeaders({ Accept: "application/json" }),
      }),
      endpoint,
    );
    const data = (await response.json()) as ResultEnvelope<T> | T;
    if (!response.ok) {
      throw new Error(sanitizeForDisplay(data));
    }
    if (
      typeof data === "object" &&
      data !== null &&
      ("ok" in data || "success" in data)
    ) {
      const envelope = data as ResultEnvelope<T>;
      const result = envelope.result ?? envelope.data;
      const ok = envelope.ok ?? envelope.success;
      if (!ok || result === undefined) {
        throw new Error(
          sanitizeForDisplay(envelope.error?.message ?? "Request failed"),
        );
      }
      return result;
    }
    return data as T;
  } finally {
    readLimiter.release();
  }
}

function withReadTimeout<T>(promise: Promise<T>, endpoint: string): Promise<T> {
  let timeoutId: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<T>((_, reject) => {
    timeoutId = setTimeout(() => {
      reject(new Error(`Timed out reading ${endpoint}`));
    }, CONTROL_CENTER_READ_TIMEOUT_MS);
  });
  return Promise.race([
    promise.finally(() => {
      if (timeoutId !== undefined) {
        clearTimeout(timeoutId);
      }
    }),
    timeout,
  ]);
}

export async function loadControlCenterData(): Promise<ControlCenterData> {
  if (!API_BASE_POLICY.allowed) {
    return withConnection(
      {
        ...mockControlCenterData,
        founderToday: normalizeFounderToday(undefined).value,
        founderEvidenceTimeline:
          normalizeFounderEvidenceTimeline(undefined).value,
        founderActionsInbox: normalizeFounderActionsInbox(undefined).value,
        founderMorningBriefing:
          normalizeFounderMorningBriefing(undefined).value,
      },
      {
        state: "mock_fallback",
        safeMessage: API_BASE_POLICY.safeMessage,
        usingMockData: true,
        warnings: API_BASE_POLICY.warnings,
      },
    );
  }

  const loadReadLimiter = createControlCenterReadLimiter();
  const read = <T>(endpoint: string): Promise<T> =>
    readEnvelope<T>(endpoint, loadReadLimiter);

  const workBoardSettledPromise = Promise.allSettled([
    read<WorkBoardReadModel>(API_ENDPOINTS.controlCenterWorkBoard),
  ] as const);
  const agentLoopSettledPromise = Promise.allSettled([
    read<FounderLoopAgentLoopThread>(API_ENDPOINTS.founderAgentLoopThread),
  ] as const);
  const runtimeCapabilityDiscoverySettledPromise = Promise.allSettled([
    read<RuntimeCapabilityDiscoveryReadModel>(
      API_ENDPOINTS.runtimeCapabilityDiscovery,
    ),
  ] as const);
  const runtimeRunEventsSettledPromise = Promise.allSettled([
    read<RuntimeRunEventsReadModel>(API_ENDPOINTS.runtimeRunEvents),
  ] as const);
  const runtimeApprovalBridgeSettledPromise = Promise.allSettled([
    read<RuntimeApprovalBridgeReadModel>(API_ENDPOINTS.runtimeApprovalBridge),
  ] as const);
  const runtimeStreamingProgressSettledPromise = Promise.allSettled([
    read<RuntimeStreamingProgressReadModel>(
      API_ENDPOINTS.runtimeStreamingProgress,
    ),
  ] as const);
  const runtimeProfilesSettledPromise = Promise.allSettled([
    read<RuntimeProfileIsolationReadModel>(API_ENDPOINTS.runtimeProfiles),
  ] as const);
  const results = await Promise.allSettled([
    read<ControlCenterManifest>(API_ENDPOINTS.controlCenterManifest),
    read<ControlCenterDashboardSnapshot>(
      API_ENDPOINTS.controlCenterDashboard,
    ),
    read<ControlCenterStatus>(API_ENDPOINTS.controlCenterStatus),
    read<ApiRouteInventory>(API_ENDPOINTS.controlCenterRoutes),
    read<RuntimeReadinessReport>(API_ENDPOINTS.runtimeReadiness),
    read<RuntimeCapabilityMatrix>(
      API_ENDPOINTS.runtimeCapabilityMatrix,
    ),
    read<RuntimeDelegationAdapterReadModel>(
      API_ENDPOINTS.runtimeDelegationAdapter,
    ),
    read<unknown>(API_ENDPOINTS.setupAssistantSummary),
    read<ProviderCatalog>(API_ENDPOINTS.providerSetupGuide),
    read<ModelProviderControlPlaneReadModel>(
      API_ENDPOINTS.modelProviderControlPlane,
    ),
    read<ControlCenterSettingsStatus>(
      API_ENDPOINTS.controlCenterSettingsStatus,
    ),
    read<ControlCenterLocalModelsStatus>(
      API_ENDPOINTS.controlCenterLocalModelsStatus,
    ),
    read<FounderLoopTodaySummary>(API_ENDPOINTS.founderTodaySummary),
    read<FounderLoopEvidenceTimelineIndex>(
      API_ENDPOINTS.founderEvidenceTimeline,
    ),
    read<FounderLoopMemoryReview>(API_ENDPOINTS.founderMemoryReview),
    read<FounderLoopMemoryWorkbench>(
      API_ENDPOINTS.founderMemoryWorkbench,
    ),
    read<FounderLoopMemoryContextPacks>(
      API_ENDPOINTS.founderMemoryContextPacks,
    ),
    read<FounderLoopMemoryRetrievalDiagnostics>(
      API_ENDPOINTS.founderMemoryRetrievalDiagnostics,
    ),
    read<FounderLoopMemoryCitationIntegrity>(
      API_ENDPOINTS.founderMemoryCitationIntegrity,
    ),
    read<FounderLoopMemoryQualityIssues>(
      API_ENDPOINTS.founderMemoryQualityIssues,
    ),
    read<FounderLoopMemoryMaintenanceRuns>(
      API_ENDPOINTS.founderMemoryMaintenanceRuns,
    ),
    read<FounderLoopMemoryContextManifest>(
      API_ENDPOINTS.founderMemoryContextManifest,
    ),
    read<FounderLoopActionsInbox>(API_ENDPOINTS.founderActionsInbox),
    read<FounderLoopMorningBriefing>(
      API_ENDPOINTS.founderMorningBriefing,
    ),
    read<FounderLoopSourceReadiness>(
      API_ENDPOINTS.founderSourceReadiness,
    ),
    read<FounderLoopStorageStatus>(API_ENDPOINTS.founderStorageStatus),
    read<CrmLocalCommandCenterReadModel>(API_ENDPOINTS.crmSummary),
    read<ControlCenterDashboardSnapshot["approval_summary"]>(
      API_ENDPOINTS.approvalSummary,
    ),
    read<RunAttachedApprovalQueue>(API_ENDPOINTS.approvalQueue),
    read<RunObservabilityReadModel>(API_ENDPOINTS.runObservability),
    read<ControlCenterDashboardSnapshot["runtime_readiness_summary"]>(
      API_ENDPOINTS.runtimeReadinessSummary,
    ),
    read<ControlCenterDashboardSnapshot["foundation_gate_summary"]>(
      API_ENDPOINTS.foundationGateSummary,
    ),
    read<ControlCenterStartHereSummary>(
      API_ENDPOINTS.founderStartHereSummary,
    ),
    read<ControlCenterProofIndex>(API_ENDPOINTS.controlCenterProofIndex),
    read<TrustAuthorityMatrix>(API_ENDPOINTS.trustAuthorityMatrix),
    read<CodingCockpitSessionReadModel>(
      API_ENDPOINTS.controlCenterCodingSession,
    ),
    read<CodingWorkspaceContextReadModel>(
      API_ENDPOINTS.controlCenterCodingContext,
    ),
    read<CodingPatchProposalReadModel>(
      API_ENDPOINTS.controlCenterCodingPatchProposal,
    ),
    read<CodingPatchApplyReadinessReadModel>(
      API_ENDPOINTS.controlCenterCodingPatchApplyReadiness,
    ),
    read<CodingTestCommandReadinessReadModel>(
      API_ENDPOINTS.controlCenterCodingTestCommandReadiness,
    ),
    read<CodingGitReviewReadModel>(
      API_ENDPOINTS.controlCenterCodingGitReview,
    ),
    read<CodingLivePreviewReadModel>(
      API_ENDPOINTS.controlCenterCodingLivePreview,
    ),
    read<CodingMultiAgentReviewReadModel>(
      API_ENDPOINTS.controlCenterCodingMultiAgentReview,
    ),
  ] as const);
  const workBoardResult = await workBoardSettledPromise;
  const agentLoopResult = await agentLoopSettledPromise;
  const runtimeCapabilityDiscoveryResult =
    await runtimeCapabilityDiscoverySettledPromise;
  const runtimeRunEventsResult = await runtimeRunEventsSettledPromise;
  const runtimeApprovalBridgeResult =
    await runtimeApprovalBridgeSettledPromise;
  const runtimeStreamingProgressResult =
    await runtimeStreamingProgressSettledPromise;
  const runtimeProfilesResult = await runtimeProfilesSettledPromise;

  const manifest = fulfilledValue(results[0]);
  const dashboard = fulfilledValue(results[1]);
  const normalizedDashboard = normalizeControlCenterDashboard(dashboard);
  const status = fulfilledValue(results[2]);
  const routes = fulfilledValue(results[3]);
  const runtimeReadiness = fulfilledValue(results[4]);
  const capabilityMatrix = fulfilledValue(results[5]);
  const runtimeDelegationAdapter = fulfilledValue(results[6]);
  const runtimeCapabilityDiscovery = fulfilledValue(
    runtimeCapabilityDiscoveryResult[0],
  );
  const runtimeRunEvents = fulfilledValue(runtimeRunEventsResult[0]);
  const runtimeApprovalBridge = fulfilledValue(runtimeApprovalBridgeResult[0]);
  const runtimeStreamingProgress = fulfilledValue(
    runtimeStreamingProgressResult[0],
  );
  const runtimeProfiles = fulfilledValue(runtimeProfilesResult[0]);
  const setupAssistantSource = fulfilledValue(results[7]);
  const setupAssistant = normalizeMacOSSetupAssistant(
    setupAssistantSource,
    mockControlCenterData.macosSetupAssistant,
  );
  const providerCatalog = fulfilledValue(results[8]);
  const modelProviderControlPlane = fulfilledValue(results[9]);
  const controlCenterSettingsStatus = fulfilledValue(results[10]);
  const controlCenterLocalModelsStatus = fulfilledValue(results[11]);
  const founderToday = fulfilledValue(results[12]);
  const founderEvidenceTimeline = fulfilledValue(results[13]);
  const founderMemoryReview = fulfilledValue(results[14]);
  const founderMemoryWorkbench = fulfilledValue(results[15]);
  const founderMemoryContextPacks = fulfilledValue(results[16]);
  const founderMemoryRetrievalDiagnostics = fulfilledValue(results[17]);
  const founderMemoryCitationIntegrity = fulfilledValue(results[18]);
  const founderMemoryQualityIssues = fulfilledValue(results[19]);
  const founderMemoryMaintenanceRuns = fulfilledValue(results[20]);
  const founderMemoryContextManifest = fulfilledValue(results[21]);
  const founderActionsInbox = fulfilledValue(results[22]);
  const founderMorningBriefing = fulfilledValue(results[23]);
  const founderSourceReadiness = fulfilledValue(results[24]);
  const founderStorageStatus = fulfilledValue(results[25]);
  const crmLocalCommandCenter = fulfilledValue(results[26]);
  const approvalSummary = fulfilledValue(results[27]);
  const approvalQueue = fulfilledValue(results[28]);
  const runObservability = fulfilledValue(results[29]);
  const safeObservedRunObservability = safeRunObservability(runObservability);
  const runtimeReadinessSummary = fulfilledValue(results[30]);
  const foundationGateSummary = fulfilledValue(results[31]);
  const founderStartHere = fulfilledValue(results[32]);
  const proofIndex = fulfilledValue(results[33]);
  const trustAuthorityMatrix = fulfilledValue(results[34]);
  const codingSession = fulfilledValue(results[35]);
  const codingContext = fulfilledValue(results[36]);
  const codingPatchProposal = fulfilledValue(results[37]);
  const codingPatchApplyReadiness = fulfilledValue(results[38]);
  const codingTestCommandReadiness = fulfilledValue(results[39]);
  const codingGitReview = fulfilledValue(results[40]);
  const codingLivePreview = fulfilledValue(results[41]);
  const codingMultiAgentReview = fulfilledValue(results[42]);
  const workBoard = fulfilledValue(workBoardResult[0]);
  const founderAgentLoopThread = fulfilledValue(agentLoopResult[0]);
  const safeCodingMultiAgentReview = isSafeCodingMultiAgentReview(
    codingMultiAgentReview,
  )
    ? codingMultiAgentReview
    : undefined;
  const safeModelProviderControlPlane = isSafeModelProviderControlPlane(
    modelProviderControlPlane,
  )
    ? modelProviderControlPlane
    : undefined;
  const safeRuntimeDelegationAdapter = isSafeRuntimeDelegationAdapter(
    runtimeDelegationAdapter,
  )
    ? runtimeDelegationAdapter
    : undefined;
  const safeRuntimeCapabilityDiscovery = isSafeRuntimeCapabilityDiscovery(
    runtimeCapabilityDiscovery,
  )
    ? runtimeCapabilityDiscovery
    : undefined;
  const safeRuntimeRunEvents = isSafeRuntimeRunEvents(runtimeRunEvents)
    ? runtimeRunEvents
    : undefined;
  const safeRuntimeApprovalBridge = isSafeRuntimeApprovalBridge(
    runtimeApprovalBridge,
  )
    ? runtimeApprovalBridge
    : undefined;
  const safeRuntimeStreamingProgress = isSafeRuntimeStreamingProgress(
    runtimeStreamingProgress,
  )
    ? runtimeStreamingProgress
    : undefined;
  const safeRuntimeProfiles = isSafeRuntimeProfileIsolation(runtimeProfiles)
    ? runtimeProfiles
    : undefined;
  const normalizedFounderToday = normalizeFounderToday(founderToday);
  const normalizedFounderStartHere = normalizeFounderStartHere(founderStartHere);
  const normalizedProofIndex = normalizeProofIndex(proofIndex);
  const normalizedTrustAuthorityMatrix =
    normalizeTrustAuthorityMatrix(trustAuthorityMatrix);
  const normalizedFounderEvidenceTimeline = normalizeFounderEvidenceTimeline(
    founderEvidenceTimeline,
  );
  const normalizedFounderActionsInbox =
    normalizeFounderActionsInbox(founderActionsInbox);
  const normalizedFounderMemoryReview =
    normalizeFounderMemoryReview(founderMemoryReview);
  const normalizedFounderMemoryWorkbench = normalizeFounderMemoryWorkbench(
    founderMemoryWorkbench,
  );
  const normalizedFounderMemoryContextPacks =
    normalizeFounderMemoryContextPacks(founderMemoryContextPacks);
  const normalizedFounderMemoryRetrievalDiagnostics = mergeMissingFields(
    mockControlCenterData.founderMemoryRetrievalDiagnostics,
    founderMemoryRetrievalDiagnostics,
  );
  const normalizedFounderMemoryCitationIntegrity = mergeMissingFields(
    mockControlCenterData.founderMemoryCitationIntegrity,
    founderMemoryCitationIntegrity,
  );
  const normalizedFounderMemoryQualityIssues = mergeMissingFields(
    mockControlCenterData.founderMemoryQualityIssues,
    founderMemoryQualityIssues,
  );
  const normalizedFounderMemoryMaintenanceRuns = mergeMissingFields(
    mockControlCenterData.founderMemoryMaintenanceRuns,
    founderMemoryMaintenanceRuns,
  );
  const normalizedFounderMemoryContextManifest =
    normalizeFounderMemoryContextManifest(founderMemoryContextManifest);
  const normalizedFounderMorningBriefing = normalizeFounderMorningBriefing(
    founderMorningBriefing,
  );
  const normalizedFounderSourceReadiness = mergeMissingFields(
    mockControlCenterData.founderSourceReadiness,
    founderSourceReadiness,
  );
  const codingBackendRouteRefs = [
    "GET /control-center/coding/session",
    "GET /control-center/coding/context",
    "GET /control-center/coding/patch-proposal",
    "GET /control-center/coding/patch-apply-readiness",
    "GET /control-center/coding/test-command-readiness",
    "GET /control-center/coding/git-review",
    "GET /control-center/coding/live-preview",
    "GET /control-center/coding/multi-agent-review",
  ];
  const codingEndpointFallbackWarningRefs = [
    ...(codingSession === undefined ||
    codingSession.mock_fallback === true ||
    codingSession.backend_owned !== true
      ? ["CODING_SESSION_MOCK_FALLBACK"]
      : []),
    ...(codingContext === undefined || codingContext.backend_owned !== true
      ? ["CODING_CONTEXT_MOCK_FALLBACK"]
      : []),
    ...(codingPatchProposal === undefined ||
    codingPatchProposal.backend_owned !== true ||
    codingPatchProposal.proposal_only !== true
      ? ["CODING_PATCH_PROPOSAL_MOCK_FALLBACK"]
      : []),
    ...(codingPatchApplyReadiness === undefined ||
    codingPatchApplyReadiness.backend_owned !== true ||
    codingPatchApplyReadiness.readiness_only !== true
      ? ["CODING_PATCH_APPLY_READINESS_MOCK_FALLBACK"]
      : []),
    ...(codingTestCommandReadiness === undefined ||
    codingTestCommandReadiness.backend_owned !== true ||
    codingTestCommandReadiness.readiness_only !== true
      ? ["CODING_TEST_COMMAND_READINESS_MOCK_FALLBACK"]
      : []),
    ...(codingGitReview === undefined ||
    codingGitReview.backend_owned !== true ||
    codingGitReview.read_only !== true ||
    codingGitReview.proposal_only !== true ||
    codingGitReview.safe_refs_only !== true
      ? ["CODING_GIT_REVIEW_MOCK_FALLBACK"]
      : []),
    ...(codingLivePreview === undefined ||
    codingLivePreview.backend_owned !== true ||
    codingLivePreview.read_only !== true ||
    codingLivePreview.status_only !== true ||
    codingLivePreview.safe_refs_only !== true
      ? ["CODING_LIVE_PREVIEW_MOCK_FALLBACK"]
      : []),
    ...(safeCodingMultiAgentReview === undefined
      ? ["CODING_MULTI_AGENT_REVIEW_MOCK_FALLBACK"]
      : []),
  ];
  const workBoardFallbackUsed =
    workBoard === undefined ||
    workBoard.backend_owned !== true ||
    workBoard.read_only !== true ||
    workBoard.safe_refs_only !== true ||
    workBoard.board_mutation_enabled !== false ||
    workBoard.durable_drag_drop_enabled !== false ||
    workBoard.durable_reorder_persistence_enabled !== true ||
    workBoard.approval_required_for_reorder !== true ||
    workBoard.drag_drop_posture?.durable_reorder_enabled !== true ||
    workBoard.drag_drop_posture?.backend_mutation_route_available !== true ||
    workBoard.drag_drop_posture?.approval_required !== true;
  const workBoardEndpointFallbackWarningRefs = [
    ...(workBoardFallbackUsed ? ["WORK_BOARD_MOCK_FALLBACK"] : []),
  ];
  const safeFounderAgentLoopThread = isSafeFounderAgentLoopThread(
    founderAgentLoopThread,
  )
    ? founderAgentLoopThread
    : undefined;
  const agentLoopThreadFallbackUsed =
    safeFounderAgentLoopThread === undefined;
  const crmEndpointFallbackUsed =
    crmLocalCommandCenter === undefined ||
    crmLocalCommandCenter.backend_owned !== true ||
    crmLocalCommandCenter.safe_refs_only !== true ||
    crmLocalCommandCenter.authority_posture?.control_center_grants_authority !==
      false ||
    crmLocalCommandCenter.authority_posture?.send_enabled !== false ||
    crmLocalCommandCenter.authority_posture?.connector_write_enabled !== false ||
    crmLocalCommandCenter.authority_posture?.provider_model_call_enabled !== false;
  const modelProviderControlPlaneFallbackUsed =
    safeModelProviderControlPlane === undefined;
  const runtimeDelegationAdapterFallbackUsed =
    safeRuntimeDelegationAdapter === undefined;
  const runtimeCapabilityDiscoveryFallbackUsed =
    safeRuntimeCapabilityDiscovery === undefined;
  const runtimeRunEventsFallbackUsed = safeRuntimeRunEvents === undefined;
  const runtimeApprovalBridgeFallbackUsed =
    safeRuntimeApprovalBridge === undefined;
  const runtimeStreamingProgressFallbackUsed =
    safeRuntimeStreamingProgress === undefined;
  const runtimeProfilesFallbackUsed = safeRuntimeProfiles === undefined;

  const routeStates = buildRouteReadStates([
    routeReadStateInput({
      route: "/start",
      surfaceLabel: "Start Here",
      backendRouteRef: "GET /control-center/start-here/summary",
      endpointReturned: founderStartHere !== undefined,
      usedFallback: normalizedFounderStartHere.usedFallback,
    }),
    routeReadStateInput({
      route: "/today",
      surfaceLabel: "Today",
      backendRouteRef: "GET /control-center/today/summary",
      endpointReturned: founderToday !== undefined,
      usedFallback: normalizedFounderToday.usedFallback,
    }),
    routeReadStateInput({
      route: "/inbox",
      surfaceLabel: "Source Inbox",
      backendRouteRef: "GET /control-center/sources/readiness",
      endpointReturned: founderSourceReadiness !== undefined,
      usedFallback: founderSourceReadiness === undefined,
    }),
    routeReadStateInput({
      route: "/actions",
      surfaceLabel: "Action Inbox",
      backendRouteRef: "GET /control-center/actions/inbox",
      endpointReturned: founderActionsInbox !== undefined,
      usedFallback: normalizedFounderActionsInbox.usedFallback,
    }),
    routeReadStateInput({
      route: "/proof",
      surfaceLabel: "Proof",
      backendRouteRef: "GET /control-center/proof/index",
      endpointReturned: proofIndex !== undefined,
      usedFallback: normalizedProofIndex.usedFallback,
    }),
    routeReadStateInput({
      route: "/trust",
      surfaceLabel: "Trust",
      backendRouteRef: "GET /control-center/trust-authority/matrix",
      endpointReturned: trustAuthorityMatrix !== undefined,
      usedFallback: normalizedTrustAuthorityMatrix.usedFallback,
    }),
    routeReadStateInput({
      route: "/coding",
      surfaceLabel: "Coding",
      backendRouteRefs: codingBackendRouteRefs,
      endpointReturned:
        codingSession !== undefined &&
        codingContext !== undefined &&
        codingPatchProposal !== undefined &&
        codingPatchApplyReadiness !== undefined &&
        codingTestCommandReadiness !== undefined &&
        codingGitReview !== undefined &&
        codingLivePreview !== undefined &&
        codingMultiAgentReview !== undefined,
      warningRefs: codingEndpointFallbackWarningRefs,
      usedFallback:
        codingSession === undefined ||
        codingSession.mock_fallback === true ||
        codingSession.backend_owned !== true ||
        codingContext === undefined ||
        codingContext.backend_owned !== true ||
        codingPatchProposal === undefined ||
        codingPatchProposal.backend_owned !== true ||
        codingPatchProposal.proposal_only !== true ||
        codingPatchApplyReadiness === undefined ||
        codingPatchApplyReadiness.backend_owned !== true ||
        codingPatchApplyReadiness.readiness_only !== true ||
        codingTestCommandReadiness === undefined ||
        codingTestCommandReadiness.backend_owned !== true ||
        codingTestCommandReadiness.readiness_only !== true ||
        codingGitReview === undefined ||
        codingGitReview.backend_owned !== true ||
        codingGitReview.read_only !== true ||
        codingGitReview.proposal_only !== true ||
        codingGitReview.safe_refs_only !== true ||
        codingLivePreview === undefined ||
        codingLivePreview.backend_owned !== true ||
        codingLivePreview.read_only !== true ||
        codingLivePreview.status_only !== true ||
        codingLivePreview.safe_refs_only !== true ||
        safeCodingMultiAgentReview === undefined,
    }),
    routeReadStateInput({
      route: "/work-board",
      surfaceLabel: "Work Board",
      backendRouteRef: "GET /control-center/work-board",
      endpointReturned: workBoard !== undefined,
      warningRefs: workBoardEndpointFallbackWarningRefs,
      usedFallback: workBoardFallbackUsed,
    }),
    routeReadStateInput({
      route: "/memory",
      surfaceLabel: "Memory",
      backendRouteRef: "GET /control-center/memory/review",
      endpointReturned: founderMemoryReview !== undefined,
      usedFallback: normalizedFounderMemoryReview.usedFallback,
    }),
    routeReadStateInput({
      route: "/evidence",
      surfaceLabel: "Evidence",
      backendRouteRef: "GET /control-center/evidence/timeline",
      endpointReturned: founderEvidenceTimeline !== undefined,
      usedFallback: normalizedFounderEvidenceTimeline.usedFallback,
    }),
    routeReadStateInput({
      route: "/settings",
      surfaceLabel: "Settings",
      backendRouteRef: "GET /control-center/settings/status",
      endpointReturned: controlCenterSettingsStatus !== undefined,
      usedFallback: controlCenterSettingsStatus === undefined,
    }),
    routeReadStateInput({
      route: "/models",
      surfaceLabel: "Models",
      backendRouteRefs: [
        "GET /control-center/providers/runtime-control-plane",
        "GET /control-center/local-models/status",
      ],
      endpointReturned:
        modelProviderControlPlane !== undefined &&
        controlCenterLocalModelsStatus !== undefined,
      warningRefs: modelProviderControlPlaneFallbackUsed
        ? ["MODEL_PROVIDER_CONTROL_PLANE_MOCK_FALLBACK"]
        : [],
      usedFallback:
        modelProviderControlPlaneFallbackUsed ||
        controlCenterLocalModelsStatus === undefined,
    }),
    routeReadStateInput({
      route: "/runtime",
      surfaceLabel: "Runtime",
      backendRouteRefs: [
        "GET /runtime/readiness",
        "GET /runtime/capability-matrix",
        "GET /api/runtime/delegation-adapter",
        "GET /api/runtime/capability-discovery",
        "GET /api/runtime/run-events",
        "GET /api/runtime/approval-bridge",
        "GET /api/runtime/streaming-progress",
        "GET /api/runtime/profiles",
      ],
      endpointReturned:
        runtimeReadiness !== undefined &&
        capabilityMatrix !== undefined &&
        runtimeDelegationAdapter !== undefined &&
        runtimeCapabilityDiscovery !== undefined &&
        runtimeRunEvents !== undefined &&
        runtimeApprovalBridge !== undefined &&
        runtimeStreamingProgress !== undefined &&
        runtimeProfiles !== undefined,
      warningRefs: [
        ...(runtimeDelegationAdapterFallbackUsed
          ? ["RUNTIME_DELEGATION_ADAPTER_MOCK_FALLBACK"]
          : []),
        ...(runtimeCapabilityDiscoveryFallbackUsed
          ? ["RUNTIME_CAPABILITY_DISCOVERY_MOCK_FALLBACK"]
          : []),
        ...(runtimeRunEventsFallbackUsed
          ? ["RUNTIME_RUN_EVENTS_MOCK_FALLBACK"]
          : []),
        ...(runtimeApprovalBridgeFallbackUsed
          ? ["RUNTIME_APPROVAL_BRIDGE_MOCK_FALLBACK"]
          : []),
        ...(runtimeStreamingProgressFallbackUsed
          ? ["RUNTIME_STREAMING_PROGRESS_MOCK_FALLBACK"]
          : []),
        ...(runtimeProfilesFallbackUsed
          ? ["RUNTIME_PROFILES_MOCK_FALLBACK"]
          : []),
      ],
      usedFallback:
        runtimeReadiness === undefined ||
        capabilityMatrix === undefined ||
        runtimeDelegationAdapterFallbackUsed ||
        runtimeCapabilityDiscoveryFallbackUsed ||
        runtimeRunEventsFallbackUsed ||
        runtimeApprovalBridgeFallbackUsed ||
        runtimeStreamingProgressFallbackUsed ||
        runtimeProfilesFallbackUsed,
    }),
    routeReadStateInput({
      route: "/briefing",
      surfaceLabel: "Briefing",
      backendRouteRef: "GET /control-center/morning-briefing/summary",
      endpointReturned: founderMorningBriefing !== undefined,
      usedFallback: normalizedFounderMorningBriefing.usedFallback,
    }),
    routeReadStateInput({
      route: "/setup",
      surfaceLabel: "Setup",
      backendRouteRef: "GET /control-center/setup-assistant/summary",
      endpointReturned: setupAssistantSource !== undefined,
      usedFallback: setupAssistantSource === undefined,
    }),
    routeReadStateInput({
      route: "/storage",
      surfaceLabel: "Storage",
      backendRouteRef: "GET /control-center/storage/status",
      endpointReturned: founderStorageStatus !== undefined,
      usedFallback: founderStorageStatus === undefined,
    }),
    routeReadStateInput({
      route: "/crm",
      surfaceLabel: "CRM",
      backendRouteRef: "GET /control-center/crm/summary",
      endpointReturned: crmLocalCommandCenter !== undefined,
      usedFallback: crmEndpointFallbackUsed,
    }),
  ]);
  const founderLoopFieldFallbackUsed =
    normalizedFounderToday.usedFallback ||
    normalizedFounderEvidenceTimeline.usedFallback ||
    normalizedFounderActionsInbox.usedFallback ||
    normalizedFounderMemoryReview.usedFallback ||
    normalizedFounderMemoryWorkbench.usedFallback ||
    normalizedFounderMemoryContextPacks.usedFallback ||
    normalizedFounderMemoryRetrievalDiagnostics.usedFallback ||
    normalizedFounderMemoryCitationIntegrity.usedFallback ||
    normalizedFounderMemoryQualityIssues.usedFallback ||
    normalizedFounderMemoryMaintenanceRuns.usedFallback ||
    normalizedFounderMemoryContextManifest.usedFallback ||
    normalizedFounderMorningBriefing.usedFallback ||
    normalizedFounderSourceReadiness.usedFallback ||
    agentLoopThreadFallbackUsed;
  const providerCredentialReadinessFallbackUsed =
    normalizedDashboard.usedFallback;
  const codingSessionFallbackUsed =
    codingSession === undefined ||
    codingSession.mock_fallback === true ||
    codingSession.backend_owned !== true ||
    codingContext === undefined ||
    codingContext.backend_owned !== true ||
    codingPatchProposal === undefined ||
    codingPatchProposal.backend_owned !== true ||
    codingPatchProposal.proposal_only !== true ||
    codingPatchApplyReadiness === undefined ||
    codingPatchApplyReadiness.backend_owned !== true ||
    codingPatchApplyReadiness.readiness_only !== true ||
    codingTestCommandReadiness === undefined ||
    codingTestCommandReadiness.backend_owned !== true ||
    codingTestCommandReadiness.readiness_only !== true ||
    codingGitReview === undefined ||
    codingGitReview.backend_owned !== true ||
    codingGitReview.read_only !== true ||
    codingGitReview.proposal_only !== true ||
    codingGitReview.safe_refs_only !== true ||
    codingLivePreview === undefined ||
    codingLivePreview.backend_owned !== true ||
    codingLivePreview.read_only !== true ||
    codingLivePreview.status_only !== true ||
    codingLivePreview.safe_refs_only !== true ||
    safeCodingMultiAgentReview === undefined;
  const approvalQueueEndpointFallbackUsed = approvalQueue === undefined;
  const runObservabilityEndpointFallbackUsed =
    safeObservedRunObservability === undefined;
  const dashboardSummaryEndpointFallbackUsed =
    approvalSummary === undefined ||
    runtimeReadinessSummary === undefined ||
    foundationGateSummary === undefined;
  const generalMockFallbackUsed =
    manifest === undefined ||
    dashboard === undefined ||
    status === undefined ||
    routes === undefined ||
    runtimeReadiness === undefined ||
    capabilityMatrix === undefined ||
    runtimeDelegationAdapter === undefined ||
    runtimeCapabilityDiscovery === undefined ||
    runtimeRunEvents === undefined ||
    runtimeApprovalBridge === undefined ||
    runtimeStreamingProgress === undefined ||
    runtimeProfiles === undefined ||
    codingSession === undefined ||
    codingContext === undefined ||
    codingPatchProposal === undefined ||
    codingPatchApplyReadiness === undefined ||
    codingTestCommandReadiness === undefined ||
    codingGitReview === undefined ||
    codingLivePreview === undefined ||
    codingMultiAgentReview === undefined ||
    workBoard === undefined ||
    safeFounderAgentLoopThread === undefined ||
    setupAssistantSource === undefined ||
    providerCatalog === undefined ||
    safeModelProviderControlPlane === undefined ||
    controlCenterSettingsStatus === undefined ||
    controlCenterLocalModelsStatus === undefined ||
    founderStorageStatus === undefined;
  const coreFulfilledCount = results.filter(
    (result) => result.status === "fulfilled",
  ).length;
  const fulfilledCount =
    coreFulfilledCount +
    (workBoardResult[0].status === "fulfilled" ? 1 : 0) +
    (agentLoopResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeCapabilityDiscoveryResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeRunEventsResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeApprovalBridgeResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeStreamingProgressResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeProfilesResult[0].status === "fulfilled" ? 1 : 0);
  const expectedReadCount = results.length + 7;
  const dashboardWithEndpointSummaries: ControlCenterDashboardSnapshot = {
    ...normalizedDashboard.value,
    approval_summary:
      approvalSummary ?? normalizedDashboard.value.approval_summary,
    runtime_readiness_summary:
      runtimeReadinessSummary ??
      normalizedDashboard.value.runtime_readiness_summary,
    foundation_gate_summary:
      foundationGateSummary ??
      normalizedDashboard.value.foundation_gate_summary,
  };

  if (fulfilledCount === 0) {
    return withConnection(
      {
        ...mockControlCenterData,
        founderToday: normalizeFounderToday(undefined).value,
        founderStartHere: normalizeFounderStartHere(undefined).value,
        proofIndex: normalizeProofIndex(undefined).value,
        founderEvidenceTimeline:
          normalizeFounderEvidenceTimeline(undefined).value,
        founderActionsInbox: normalizeFounderActionsInbox(undefined).value,
        founderMorningBriefing:
          normalizeFounderMorningBriefing(undefined).value,
        codingSession: mockControlCenterData.codingSession,
        codingContext: mockControlCenterData.codingContext,
        codingPatchProposal: mockControlCenterData.codingPatchProposal,
        codingPatchApplyReadiness:
          mockControlCenterData.codingPatchApplyReadiness,
        codingTestCommandReadiness:
          mockControlCenterData.codingTestCommandReadiness,
        codingGitReview: mockControlCenterData.codingGitReview,
        codingLivePreview: mockControlCenterData.codingLivePreview,
        codingMultiAgentReview:
          mockControlCenterData.codingMultiAgentReview,
        workBoard: mockControlCenterData.workBoard,
      },
      {
        state: "mock_fallback",
        safeMessage:
          "Backend unavailable; showing non-authoritative mock fallback data.",
        usingMockData: true,
        warnings: ["LOCAL_BACKEND_UNAVAILABLE", "MOCK_DATA_ONLY"],
      },
    );
  }

  const data: ControlCenterData = {
    manifest: manifest ?? mockControlCenterData.manifest,
    dashboard: dashboardWithEndpointSummaries,
    status: status ?? mockControlCenterData.status,
    routes: routes ?? mockControlCenterData.routes,
    runtimeReadiness:
      runtimeReadiness ?? mockControlCenterData.runtimeReadiness,
    capabilityMatrix:
      capabilityMatrix ?? mockControlCenterData.capabilityMatrix,
    runtimeDelegationAdapter:
      safeRuntimeDelegationAdapter ??
      mockControlCenterData.runtimeDelegationAdapter,
    runtimeCapabilityDiscovery:
      safeRuntimeCapabilityDiscovery ??
      mockControlCenterData.runtimeCapabilityDiscovery,
    runtimeRunEvents:
      safeRuntimeRunEvents ?? mockControlCenterData.runtimeRunEvents,
    runtimeApprovalBridge:
      safeRuntimeApprovalBridge ?? mockControlCenterData.runtimeApprovalBridge,
    runtimeStreamingProgress:
      safeRuntimeStreamingProgress ??
      mockControlCenterData.runtimeStreamingProgress,
    runtimeProfiles:
      safeRuntimeProfiles ?? mockControlCenterData.runtimeProfiles,
    m15Review: mockControlCenterData.m15Review,
    runAttachedApprovalQueue:
      approvalQueue ?? mockControlCenterData.runAttachedApprovalQueue,
    runObservability:
      safeObservedRunObservability ?? mockControlCenterData.runObservability,
    m16Trace: mockControlCenterData.m16Trace,
    m17Knowledge: mockControlCenterData.m17Knowledge,
    m18Runtime: mockControlCenterData.m18Runtime,
    m36FileReview: mockControlCenterData.m36FileReview,
    m39ContextProposals: mockControlCenterData.m39ContextProposals,
    macosSetupAssistant: setupAssistant,
    providerCatalog: providerCatalog ?? mockControlCenterData.providerCatalog,
    modelProviderControlPlane:
      safeModelProviderControlPlane ??
      mockControlCenterData.modelProviderControlPlane,
    settingsStatus:
      controlCenterSettingsStatus ?? mockControlCenterData.settingsStatus,
    localModelsStatus:
      controlCenterLocalModelsStatus ?? mockControlCenterData.localModelsStatus,
    founderAgentLoopThread:
      safeFounderAgentLoopThread ??
      mockControlCenterData.founderAgentLoopThread,
    founderToday: normalizedFounderToday.value,
    founderStartHere: normalizedFounderStartHere.value,
    proofIndex: normalizedProofIndex.value,
    trustAuthorityMatrix: normalizedTrustAuthorityMatrix.value,
    codingSession: codingSession ?? mockControlCenterData.codingSession,
    codingContext: codingContext ?? mockControlCenterData.codingContext,
    codingPatchProposal:
      codingPatchProposal ?? mockControlCenterData.codingPatchProposal,
    codingPatchApplyReadiness:
      codingPatchApplyReadiness ??
      mockControlCenterData.codingPatchApplyReadiness,
    codingTestCommandReadiness:
      codingTestCommandReadiness ??
      mockControlCenterData.codingTestCommandReadiness,
    codingGitReview: codingGitReview ?? mockControlCenterData.codingGitReview,
    codingLivePreview:
      codingLivePreview ?? mockControlCenterData.codingLivePreview,
    codingMultiAgentReview:
      safeCodingMultiAgentReview ?? mockControlCenterData.codingMultiAgentReview,
    workBoard: workBoardFallbackUsed ? mockControlCenterData.workBoard : workBoard,
    founderEvidenceTimeline: normalizedFounderEvidenceTimeline.value,
    founderMemoryReview: normalizedFounderMemoryReview.value,
    founderMemoryWorkbench: normalizedFounderMemoryWorkbench.value,
    founderMemoryContextPacks: normalizedFounderMemoryContextPacks.value,
    founderMemoryRetrievalDiagnostics:
      normalizedFounderMemoryRetrievalDiagnostics.value,
    founderMemoryCitationIntegrity: normalizedFounderMemoryCitationIntegrity.value,
    founderMemoryQualityIssues: normalizedFounderMemoryQualityIssues.value,
    founderMemoryMaintenanceRuns: normalizedFounderMemoryMaintenanceRuns.value,
    founderMemoryContextManifest: normalizedFounderMemoryContextManifest.value,
    founderActionsInbox: normalizedFounderActionsInbox.value,
    founderMorningBriefing: normalizedFounderMorningBriefing.value,
    founderSourceReadiness: normalizedFounderSourceReadiness.value,
    founderStorageStatus:
      founderStorageStatus ?? mockControlCenterData.founderStorageStatus,
    crmLocalCommandCenter:
      crmEndpointFallbackUsed || crmLocalCommandCenter === undefined
        ? mockControlCenterData.crmLocalCommandCenter
        : crmLocalCommandCenter,
    crmM1FixtureShell: mockControlCenterData.crmM1FixtureShell,
    source: "api",
    connection: mockControlCenterData.connection,
    routeStates,
  };

  if (
    fulfilledCount === expectedReadCount &&
    !founderLoopFieldFallbackUsed &&
    !normalizedFounderStartHere.usedFallback &&
    !normalizedProofIndex.usedFallback &&
    !normalizedTrustAuthorityMatrix.usedFallback &&
    !codingSessionFallbackUsed &&
    !workBoardFallbackUsed &&
    !agentLoopThreadFallbackUsed &&
    !runtimeDelegationAdapterFallbackUsed &&
    !runtimeCapabilityDiscoveryFallbackUsed &&
    !runtimeRunEventsFallbackUsed &&
    !runtimeApprovalBridgeFallbackUsed &&
    !runtimeStreamingProgressFallbackUsed &&
    !runtimeProfilesFallbackUsed &&
    !modelProviderControlPlaneFallbackUsed &&
    !providerCredentialReadinessFallbackUsed &&
    !runObservabilityEndpointFallbackUsed &&
    !dashboardSummaryEndpointFallbackUsed &&
    !crmEndpointFallbackUsed
  ) {
    return withConnection(data, {
      state: "online",
      safeMessage:
        "Live data came from local read, preview, and exact receipt backend routes; mutating receipt routes remain backend-authority, approval/idempotency gated, and no generic execution.",
      usingMockData: false,
      warnings: [],
    });
  }

  const mockFallbackUsed =
    generalMockFallbackUsed ||
    founderLoopFieldFallbackUsed ||
    normalizedFounderStartHere.usedFallback ||
    normalizedProofIndex.usedFallback ||
    normalizedTrustAuthorityMatrix.usedFallback ||
    codingSessionFallbackUsed ||
    workBoardFallbackUsed ||
    agentLoopThreadFallbackUsed ||
    runtimeDelegationAdapterFallbackUsed ||
    runtimeCapabilityDiscoveryFallbackUsed ||
    runtimeRunEventsFallbackUsed ||
    runtimeApprovalBridgeFallbackUsed ||
    runtimeStreamingProgressFallbackUsed ||
    runtimeProfilesFallbackUsed ||
    modelProviderControlPlaneFallbackUsed ||
    providerCredentialReadinessFallbackUsed ||
    approvalQueueEndpointFallbackUsed ||
    runObservabilityEndpointFallbackUsed ||
    crmEndpointFallbackUsed;
  let degradedSafeMessage =
    "Some local backend summaries were unavailable; non-authoritative mock fallback filled missing panels.";
  if (providerCredentialReadinessFallbackUsed) {
    degradedSafeMessage =
      "Provider credential and cost posture was unavailable or unsafe; non-authoritative mock fallback kept provider readiness blocked.";
  } else if (codingSessionFallbackUsed) {
    degradedSafeMessage =
      "Some Coding backend read models were unavailable or unsafe; non-authoritative mock fallback kept coding authority blocked.";
  } else if (workBoardFallbackUsed) {
    degradedSafeMessage =
      "The Work Board backend read model was unavailable or unsafe; non-authoritative mock fallback kept board mutation blocked.";
  } else if (modelProviderControlPlaneFallbackUsed) {
    degradedSafeMessage =
      "Model/provider control-plane posture was unavailable or unsafe; non-authoritative mock fallback kept broad provider authority blocked.";
  } else if (runtimeDelegationAdapterFallbackUsed) {
    degradedSafeMessage =
      "Runtime delegation adapter posture was unavailable or unsafe; non-authoritative mock fallback kept delegated runtime authority blocked.";
  } else if (runtimeCapabilityDiscoveryFallbackUsed) {
    degradedSafeMessage =
      "Runtime capability discovery posture was unavailable or unsafe; non-authoritative mock fallback kept runtime controls blocked.";
  } else if (runtimeRunEventsFallbackUsed) {
    degradedSafeMessage =
      "Runtime run/event posture was unavailable or unsafe; non-authoritative mock fallback kept delegated run controls blocked.";
  } else if (runtimeApprovalBridgeFallbackUsed) {
    degradedSafeMessage =
      "Runtime approval bridge posture was unavailable or unsafe; non-authoritative mock fallback kept runtime approval resolution blocked.";
  } else if (runtimeStreamingProgressFallbackUsed) {
    degradedSafeMessage =
      "Runtime streaming progress posture was unavailable or unsafe; non-authoritative mock fallback kept live runtime transport blocked.";
  } else if (runtimeProfilesFallbackUsed) {
    degradedSafeMessage =
      "Runtime profile isolation posture was unavailable or unsafe; non-authoritative mock fallback kept profile mutation blocked.";
  } else if (
    founderLoopFieldFallbackUsed ||
    normalizedFounderStartHere.usedFallback ||
    normalizedProofIndex.usedFallback ||
    normalizedTrustAuthorityMatrix.usedFallback
  ) {
    degradedSafeMessage =
      "Some local backend summaries or fields were unavailable; non-authoritative mock fallback filled missing Founder Loop panels.";
  } else if (approvalQueueEndpointFallbackUsed) {
    degradedSafeMessage =
      "Run-attached approval queue endpoint was unavailable; non-authoritative mock fallback is shown without approval authority.";
  } else if (runObservabilityEndpointFallbackUsed) {
    degradedSafeMessage =
      "Run observability endpoint was unavailable; Evidence remains read-only and uses non-authoritative mock fallback refs.";
  } else if (crmEndpointFallbackUsed) {
    degradedSafeMessage =
      "CRM local command center endpoint was unavailable or unsafe; non-authoritative mock fallback keeps CRM authority blocked.";
  } else if (dashboardSummaryEndpointFallbackUsed) {
    degradedSafeMessage =
      "Some dedicated Control Center summary routes were unavailable; backend dashboard summaries kept the visible state bounded.";
  }

  return withConnection(data, {
    state: "degraded",
    safeMessage: degradedSafeMessage,
    usingMockData: mockFallbackUsed,
    warnings: [
      "LOCAL_BACKEND_DEGRADED",
      ...(mockFallbackUsed ? ["PARTIAL_MOCK_FALLBACK"] : []),
      ...(dashboardSummaryEndpointFallbackUsed
        ? ["CONTROL_CENTER_SUMMARY_ENDPOINT_FALLBACK"]
        : []),
      ...(approvalQueueEndpointFallbackUsed
        ? ["RUN_ATTACHED_APPROVAL_QUEUE_MOCK_FALLBACK"]
        : []),
      ...(runObservabilityEndpointFallbackUsed
        ? ["RUN_OBSERVABILITY_MOCK_FALLBACK"]
        : []),
      ...(crmEndpointFallbackUsed ? ["CRM_LOCAL_COMMAND_CENTER_MOCK_FALLBACK"] : []),
      ...(founderLoopFieldFallbackUsed
        ? ["PARTIAL_FOUNDER_LOOP_FIELD_FALLBACK"]
        : []),
      ...(normalizedFounderStartHere.usedFallback
        ? ["START_HERE_MOCK_FALLBACK"]
        : []),
      ...(normalizedProofIndex.usedFallback ? ["PROOF_INDEX_MOCK_FALLBACK"] : []),
      ...(normalizedTrustAuthorityMatrix.usedFallback
        ? ["TRUST_AUTHORITY_MATRIX_MOCK_FALLBACK"]
        : []),
      ...(codingSessionFallbackUsed
        ? codingEndpointFallbackWarningRefs.length > 0
          ? codingEndpointFallbackWarningRefs
          : ["CODING_SESSION_MOCK_FALLBACK"]
        : []),
      ...(workBoardFallbackUsed ? workBoardEndpointFallbackWarningRefs : []),
      ...(agentLoopThreadFallbackUsed
        ? ["AGENT_LOOP_THREAD_MOCK_FALLBACK"]
        : []),
      ...(runtimeDelegationAdapterFallbackUsed
        ? ["RUNTIME_DELEGATION_ADAPTER_MOCK_FALLBACK"]
        : []),
      ...(runtimeCapabilityDiscoveryFallbackUsed
        ? ["RUNTIME_CAPABILITY_DISCOVERY_MOCK_FALLBACK"]
        : []),
      ...(runtimeRunEventsFallbackUsed
        ? ["RUNTIME_RUN_EVENTS_MOCK_FALLBACK"]
        : []),
      ...(runtimeApprovalBridgeFallbackUsed
        ? ["RUNTIME_APPROVAL_BRIDGE_MOCK_FALLBACK"]
        : []),
      ...(runtimeStreamingProgressFallbackUsed
        ? ["RUNTIME_STREAMING_PROGRESS_MOCK_FALLBACK"]
        : []),
      ...(runtimeProfilesFallbackUsed ? ["RUNTIME_PROFILES_MOCK_FALLBACK"] : []),
      ...(modelProviderControlPlaneFallbackUsed
        ? ["MODEL_PROVIDER_CONTROL_PLANE_MOCK_FALLBACK"]
        : []),
      ...(providerCredentialReadinessFallbackUsed
        ? ["PARTIAL_PROVIDER_CREDENTIAL_READINESS_FALLBACK"]
        : []),
    ],
  });
}

export async function submitActionPreview(
  request: ActionPreviewRequest,
): Promise<ActionPreviewDecision> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.actionPreview}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
        "Content-Type": "application/json",
      }),
      body: JSON.stringify(request),
    },
  );
  const data = (await response.json()) as ResultEnvelope<ActionPreviewDecision>;
  const decision = data.result ?? data.data;
  if (!response.ok || !decision) {
    throw new Error(
      sanitizeForDisplay(
        data.error?.message ?? "Preview request was rejected safely.",
      ),
    );
  }
  return decision;
}

export async function submitTurnRouterPreview(
  request: TurnRouterPreviewRequest,
): Promise<TurnRouterPreviewReadModel> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.turnRouterPreview}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
        "Content-Type": "application/json",
      }),
      body: JSON.stringify(request),
    },
  );
  const data = (await response.json()) as ResultEnvelope<TurnRouterPreviewReadModel>;
  const preview = data.result ?? data.data;
  if (!response.ok || !preview) {
    throw new Error(
      sanitizeForDisplay(
        data.error?.message ?? "Turn router preview failed safely.",
      ),
    );
  }
  if (!isSafeTurnRouterPreview(preview)) {
    throw new Error(
      sanitizeForDisplay("Turn router preview was rejected safely."),
    );
  }
  return preview;
}

const TURN_ROUTER_PREVIEW_CONTRACTS = [
  "answer_directly",
  "base_answer",
  "answer_with_reviewed_memory",
  "draft_or_plan",
  "prepare_tool_or_action",
  "approval_required",
  "ask_clarifying_question",
  "blocked_unsafe",
] as const;
const TURN_ROUTER_MEMORY_SCOPES = [
  "none",
  "reviewed_relevant_only",
  "proposal_review_only",
] as const;
const TURN_ROUTER_TOOL_POLICIES = [
  "none",
  "read_only_or_proposal_only",
  "envelope_only_no_execution",
] as const;
const TURN_ROUTER_TOOL_CHOICES = ["none", "auto_read_only"] as const;
const TURN_ROUTER_APPROVAL_POLICIES = [
  "not_required",
  "required_before_execution",
  "blocked",
] as const;
const TURN_ROUTER_STATE_POLICIES = [
  "ephemeral_only",
  "draft_state_only",
  "proposal_state_only",
  "action_envelope",
] as const;
const TURN_ROUTER_PROMPT_PROFILES = [
  "minimal_answer",
  "base_answer",
  "memory_answer",
  "draft_or_plan",
  "tool_or_action_prep",
  "approval_boundary",
  "clarify",
  "safe_refusal",
] as const;
const TURN_ROUTER_OUTPUT_CONTRACTS = [
  "plain_answer",
  "base_answer",
  "memory_answer_with_refs",
  "draft_or_plan",
  "action_or_tool_proposal",
  "approval_envelope_required",
  "clarifying_question",
  "safe_refusal",
] as const;
const TURN_ROUTER_RISK_FLAGS = [
  "low_risk",
  "external_side_effect",
  "credential_or_payment",
  "destructive",
  "privacy_boundary",
  "freshness_required",
  "memory_requested",
  "unsafe",
] as const;
const TURN_ROUTER_REDACTIONS = [
  "ephemeral_request_text_omitted",
  "secret_like_input_safely_summarized",
] as const;
const TURN_ROUTER_SAFE_CREDENTIAL_REFS = new Set([
  "reason-ref:turn-contract:credential-account-privacy-boundary",
]);

function isSafeTurnRouterPreview(
  value: unknown,
): value is TurnRouterPreviewReadModel {
  if (!isPlainRecord(value) || !isPlainRecord(value.policy_summary)) {
    return false;
  }
  if (!isPlainRecord(value.no_effect_proof)) {
    return false;
  }
  const noEffect = value.no_effect_proof;
  const policy = value.policy_summary;
  const selectedContract = String(value.selected_turn_contract ?? "");
  const expectedPolicy = expectedTurnRouterPolicy(selectedContract);
  const blockedRefs = stringArray(value.blocked_authority_refs);
  const requiredBlockedRefs = [
    "blocked-state:turn-router-preview:no-runtime-model-call",
    "blocked-state:turn-router-preview:no-provider-call",
    "blocked-state:turn-router-preview:no-tool-execution",
    "blocked-state:turn-router-preview:no-action-execution",
    "blocked-state:turn-router-preview:no-memory-write",
    "blocked-state:turn-router-preview:no-shell-subprocess",
    "blocked-state:turn-router-preview:no-browser-network",
    "blocked-state:turn-router-preview:no-connector-write",
  ];
  return (
    value.contract_ref === "contract-ref:turn-router-preview:v1" &&
    isSafeTurnRouterPreviewRef(value.contract_ref) &&
    isSafeTurnRouterPreviewRef(value.preview_ref) &&
    isSafeTurnRouterPreviewRef(value.request_ref) &&
    (value.request_kind === "sample" ||
      value.request_kind === "ephemeral_text") &&
    (value.sample_id === null ||
      hasExactStringValue(value.sample_id, [
        "diy-desk",
        "office-memory",
        "shopping-list",
        "current-lumber-prices",
        "order-materials",
        "card-pickup",
        "base-answer-bypass",
      ])) &&
    value.route_refs instanceof Array &&
    hasExactStringList(stringArray(value.route_refs), [
      API_ENDPOINTS.turnRouterPreview,
    ]) &&
    typeof value.confidence === "number" &&
    value.confidence >= 0 &&
    value.confidence <= 1 &&
    hasSafeTurnRouterStringArray(
      value,
      "reason_refs",
      isSafeTurnRouterPreviewRef,
    ) &&
    hasSafeTurnRouterStringArray(value, "risk_flags", (item) =>
      hasExactStringValue(item, TURN_ROUTER_RISK_FLAGS),
    ) &&
    hasSafeTurnRouterStringArray(
      value,
      "lane_result_refs",
      isSafeTurnRouterPreviewRef,
    ) &&
    hasSafeTurnRouterStringArray(
      value,
      "source_refs",
      isSafeTurnRouterPreviewRef,
    ) &&
    hasSafeTurnRouterStringArray(
      value,
      "evidence_refs",
      isSafeTurnRouterPreviewRef,
    ) &&
    hasSafeTurnRouterStringArray(value, "redactions_applied", (item) =>
      hasExactStringValue(item, TURN_ROUTER_REDACTIONS),
    ) &&
    stringArray(value.redactions_applied).includes("ephemeral_request_text_omitted") &&
    isSafeTurnHarnessText(value.safe_summary) &&
    hasExactStringValue(selectedContract, TURN_ROUTER_PREVIEW_CONTRACTS) &&
    expectedPolicy !== null &&
    requiredBlockedRefs.every((ref) => blockedRefs.includes(ref)) &&
    hasSafeTurnRouterStringArray(
      value,
      "blocked_authority_refs",
      isSafeTurnRouterPreviewRef,
    ) &&
    value.raw_content_included === false &&
    value.ephemeral_request_text_omitted === true &&
    policy.turn_contract === selectedContract &&
    hasExactStringValue(policy.memory_scope, TURN_ROUTER_MEMORY_SCOPES) &&
    policy.memory_scope === expectedPolicy.memoryScope &&
    policy.memory_write_allowed === false &&
    policy.memory_read_allowed === expectedPolicy.memoryReadAllowed &&
    hasExactStringValue(policy.tool_policy, TURN_ROUTER_TOOL_POLICIES) &&
    policy.tool_policy === expectedPolicy.toolPolicy &&
    hasExactStringValue(policy.tool_choice, TURN_ROUTER_TOOL_CHOICES) &&
    policy.tool_choice === expectedPolicy.toolChoice &&
    hasExactStringValue(policy.approval_policy, TURN_ROUTER_APPROVAL_POLICIES) &&
    policy.approval_policy === expectedPolicy.approvalPolicy &&
    policy.approval_required === expectedPolicy.approvalRequired &&
    policy.planner === expectedPolicy.planner &&
    policy.durable_state === expectedPolicy.durableState &&
    hasExactStringValue(policy.state_policy, TURN_ROUTER_STATE_POLICIES) &&
    policy.state_policy === expectedPolicy.statePolicy &&
    hasExactStringValue(policy.prompt_profile, TURN_ROUTER_PROMPT_PROFILES) &&
    policy.prompt_profile === expectedPolicy.promptProfile &&
    hasExactStringValue(policy.output_contract, TURN_ROUTER_OUTPUT_CONTRACTS) &&
    policy.output_contract === expectedPolicy.outputContract &&
    noEffect.authority_granted === false &&
    noEffect.execution_permitted === false &&
    noEffect.no_runtime_model_call_performed === true &&
    noEffect.no_provider_call_performed === true &&
    noEffect.no_tool_execution_performed === true &&
    noEffect.no_action_execution_performed === true &&
    noEffect.no_workflow_execution_performed === true &&
    noEffect.no_context_injection_performed === true &&
    noEffect.no_memory_content_retrieved === true &&
    noEffect.no_memory_write_performed === true &&
    noEffect.no_durable_state_write_performed === true &&
    noEffect.no_shell_subprocess_performed === true &&
    noEffect.no_browser_network_performed === true &&
    noEffect.no_connector_write_performed === true &&
    noEffect.invocation_policy_compiled_only === true &&
    noEffect.raw_request_text_persisted === false &&
    policy.tool_execution_allowed === false &&
    policy.action_execution_allowed === false &&
    policy.workflow_execution_allowed === false &&
    policy.context_injection_allowed === false &&
    policy.runtime_model_call_allowed === false &&
    policy.provider_call_allowed === false &&
    policy.shell_subprocess_allowed === false &&
    policy.browser_network_allowed === false &&
    policy.connector_write_allowed === false &&
    policy.side_effects_allowed === false &&
    policy.execution_ready === false
  );
}

function hasSafeTurnRouterStringArray(
  record: Record<string, unknown>,
  field: string,
  predicate: (value: string) => boolean,
): boolean {
  const value = record[field];
  return (
    Array.isArray(value) &&
    value.every((item) => typeof item === "string" && predicate(item))
  );
}

function isSafeTurnRouterPreviewRef(value: unknown): value is string {
  if (typeof value !== "string" || !isSafeWebEvidenceRef(value)) {
    return false;
  }
  const lowered = value.toLowerCase();
  if (TURN_ROUTER_SAFE_CREDENTIAL_REFS.has(lowered)) {
    return true;
  }
  return !EVIDENCE_NARRATIVE_UNSAFE_REF_FRAGMENTS.some((fragment) =>
    lowered.includes(fragment),
  );
}

function expectedTurnRouterPolicy(
  selectedContract: string,
): {
  memoryScope: string;
  memoryReadAllowed: boolean;
  toolPolicy: string;
  toolChoice: string;
  approvalPolicy: string;
  approvalRequired: boolean;
  planner: boolean;
  durableState: boolean;
  statePolicy: string;
  promptProfile: string;
  outputContract: string;
} | null {
  switch (selectedContract) {
    case "answer_directly":
      return {
        memoryScope: "none",
        memoryReadAllowed: false,
        toolPolicy: "none",
        toolChoice: "none",
        approvalPolicy: "not_required",
        approvalRequired: false,
        planner: false,
        durableState: false,
        statePolicy: "ephemeral_only",
        promptProfile: "minimal_answer",
        outputContract: "plain_answer",
      };
    case "base_answer":
      return {
        memoryScope: "none",
        memoryReadAllowed: false,
        toolPolicy: "none",
        toolChoice: "none",
        approvalPolicy: "not_required",
        approvalRequired: false,
        planner: false,
        durableState: false,
        statePolicy: "ephemeral_only",
        promptProfile: "base_answer",
        outputContract: "base_answer",
      };
    case "answer_with_reviewed_memory":
      return {
        memoryScope: "reviewed_relevant_only",
        memoryReadAllowed: true,
        toolPolicy: "none",
        toolChoice: "none",
        approvalPolicy: "not_required",
        approvalRequired: false,
        planner: false,
        durableState: false,
        statePolicy: "ephemeral_only",
        promptProfile: "memory_answer",
        outputContract: "memory_answer_with_refs",
      };
    case "draft_or_plan":
      return {
        memoryScope: "none",
        memoryReadAllowed: false,
        toolPolicy: "none",
        toolChoice: "none",
        approvalPolicy: "not_required",
        approvalRequired: false,
        planner: true,
        durableState: false,
        statePolicy: "draft_state_only",
        promptProfile: "draft_or_plan",
        outputContract: "draft_or_plan",
      };
    case "prepare_tool_or_action":
      return {
        memoryScope: "proposal_review_only",
        memoryReadAllowed: false,
        toolPolicy: "read_only_or_proposal_only",
        toolChoice: "auto_read_only",
        approvalPolicy: "not_required",
        approvalRequired: false,
        planner: true,
        durableState: false,
        statePolicy: "proposal_state_only",
        promptProfile: "tool_or_action_prep",
        outputContract: "action_or_tool_proposal",
      };
    case "approval_required":
      return {
        memoryScope: "proposal_review_only",
        memoryReadAllowed: false,
        toolPolicy: "envelope_only_no_execution",
        toolChoice: "auto_read_only",
        approvalPolicy: "required_before_execution",
        approvalRequired: true,
        planner: true,
        durableState: true,
        statePolicy: "action_envelope",
        promptProfile: "approval_boundary",
        outputContract: "approval_envelope_required",
      };
    case "ask_clarifying_question":
      return {
        memoryScope: "none",
        memoryReadAllowed: false,
        toolPolicy: "none",
        toolChoice: "none",
        approvalPolicy: "not_required",
        approvalRequired: false,
        planner: false,
        durableState: false,
        statePolicy: "ephemeral_only",
        promptProfile: "clarify",
        outputContract: "clarifying_question",
      };
    case "blocked_unsafe":
      return {
        memoryScope: "none",
        memoryReadAllowed: false,
        toolPolicy: "none",
        toolChoice: "none",
        approvalPolicy: "blocked",
        approvalRequired: false,
        planner: false,
        durableState: false,
        statePolicy: "ephemeral_only",
        promptProfile: "safe_refusal",
        outputContract: "safe_refusal",
      };
    default:
      return null;
  }
}

const TURN_HARNESS_CONTRACTS = [
  "answer_directly",
  "base_answer",
  "answer_with_reviewed_memory",
  "draft_or_plan",
  "prepare_tool_or_action",
  "approval_required",
  "ask_clarifying_question",
  "blocked_unsafe",
] as const;
const TURN_HARNESS_MEMORY_SCOPES = [
  "none",
  "reviewed_relevant_only",
  "scoped_to_approval",
  "proposal_review_only",
] as const;
const TURN_HARNESS_TOOL_POLICIES = [
  "none",
  "read_only_or_proposal_only",
  "envelope_only_no_execution",
] as const;
const TURN_HARNESS_APPROVAL_POLICIES = [
  "not_required",
  "required_before_execution",
  "blocked",
] as const;
const TURN_HARNESS_RISK_FLAGS = [
  "low_risk",
  "external_side_effect",
  "credential_or_payment",
  "destructive",
  "privacy_boundary",
  "freshness_required",
  "memory_requested",
  "unsafe",
] as const;
const TURN_HARNESS_SAFE_CREDENTIAL_REFS = new Set([
  "reason-ref:turn-contract:credential-account-privacy-boundary",
]);

function isSafeTurnHarnessBinding(
  value: unknown,
): value is TurnHarnessBindingReadModel {
  if (!isPlainRecord(value)) {
    return false;
  }
  const toolRefs = stringArray(value.tool_refs);
  const answerLike =
    value.turn_contract === "answer_directly" ||
    value.turn_contract === "base_answer";
  const directAnswerStaysEmpty =
    !answerLike ||
    (value.memory_touched === false &&
      value.reviewed_memory_refs_allowed === false &&
      value.memory_write_allowed === false &&
      value.tools_exposed_count === 0 &&
      toolRefs.length === 0 &&
      value.planner === false &&
      value.durable_state === false &&
      value.approval_required === false);
  return (
    value.contract_ref ===
      "contract-ref:turn-contract-router:harness-binding:v1" &&
    isSafeTurnHarnessRef(value.contract_ref) &&
    isSafeTurnHarnessRef(value.binding_ref) &&
    isSafeTurnHarnessRef(value.decision_ref) &&
    isSafeTurnHarnessRef(value.policy_ref) &&
    hasExactStringValue(value.turn_contract, TURN_HARNESS_CONTRACTS) &&
    isSafeTurnHarnessText(value.safe_summary) &&
    hasSafeTurnHarnessStringArray(value, "reason_refs", isSafeTurnHarnessRef) &&
    hasSafeTurnHarnessStringArray(value, "evidence_refs", isSafeTurnHarnessRef) &&
    hasSafeTurnHarnessStringArray(value, "risk_flags", (item) =>
      hasExactStringValue(item, TURN_HARNESS_RISK_FLAGS),
    ) &&
    hasExactStringValue(value.memory_scope, TURN_HARNESS_MEMORY_SCOPES) &&
    typeof value.memory_touched === "boolean" &&
    typeof value.reviewed_memory_refs_allowed === "boolean" &&
    value.memory_content_retrieved === false &&
    typeof value.memory_write_allowed === "boolean" &&
    value.memory_write_performed === false &&
    hasExactStringValue(value.tool_policy, TURN_HARNESS_TOOL_POLICIES) &&
    isSafeNonNegativeInteger(value.tools_exposed_count) &&
    hasSafeTurnHarnessStringArray(value, "tool_refs", isSafeTurnHarnessRef) &&
    value.tools_exposed_count === toolRefs.length &&
    value.execution_tools_exposed_count === 0 &&
    typeof value.planner === "boolean" &&
    typeof value.durable_state === "boolean" &&
    hasExactStringValue(value.approval_policy, TURN_HARNESS_APPROVAL_POLICIES) &&
    typeof value.approval_required === "boolean" &&
    typeof value.approval_envelope_required === "boolean" &&
    value.side_effects_allowed === false &&
    value.execution_ready === false &&
    typeof value.receipt_required === "boolean" &&
    value.raw_prompt_persisted === false &&
    value.raw_response_persisted === false &&
    value.raw_memory_body_persisted === false &&
    value.raw_local_path_persisted === false &&
    value.credential_persisted === false &&
    value.safe_refs_only === true &&
    hasSafeTurnHarnessStringArray(
      value,
      "blocked_authority_refs",
      isSafeTurnHarnessRef,
    ) &&
    value.no_effect_scope === "turn_harness_binding_compilation_only" &&
    value.no_runtime_model_call_performed === true &&
    value.no_provider_call_performed === true &&
    value.no_tool_execution_performed === true &&
    value.no_action_execution_performed === true &&
    value.no_shell_subprocess_performed === true &&
    value.no_browser_network_performed === true &&
    value.no_connector_write_performed === true &&
    directAnswerStaysEmpty
  );
}

function hasSafeTurnHarnessStringArray(
  record: Record<string, unknown>,
  field: string,
  predicate: (value: string) => boolean,
): boolean {
  const value = record[field];
  return (
    Array.isArray(value) &&
    value.every((item) => typeof item === "string" && predicate(item))
  );
}

function isSafeTurnHarnessRef(value: unknown): value is string {
  if (typeof value !== "string" || !isSafeWebEvidenceRef(value)) {
    return false;
  }
  const lowered = value.toLowerCase();
  if (lowered.includes("credential")) {
    return TURN_HARNESS_SAFE_CREDENTIAL_REFS.has(lowered);
  }
  return true;
}

function isSafeTurnHarnessText(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length > 0 &&
    value.length <= 500 &&
    isSafeEvidenceNarrativeText(value)
  );
}

function isSafeNonNegativeInteger(value: unknown): value is number {
  return Number.isInteger(value) && Number(value) >= 0;
}

export async function submitActionDecision(
  actionId: string,
  decision: FounderLoopActionDecisionKind,
  request: FounderLoopActionDecisionRequest,
): Promise<FounderLoopActionDecisionReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${actionDecisionEndpoint(actionId, decision)}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-UAA-Idempotency-Key": actionDecisionIdempotencyRef(
          actionId,
          decision,
          request,
        ),
      }),
      body: JSON.stringify(request),
    },
  );
  const data =
    (await response.json()) as ResultEnvelope<FounderLoopActionDecisionReceipt>;
  const receipt = data.result ?? data.data;
  if (!response.ok || !receipt) {
    throw new Error(
      sanitizeForDisplay(
        data.error?.message ??
          "Action decision receipt was not recorded safely.",
      ),
    );
  }
  return receipt;
}

export async function commitLocalTask(
  actionId: string,
  request: FounderLoopLocalTaskCommitRequest,
): Promise<FounderLoopLocalTaskCommitReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${actionLocalTaskCommitEndpoint(actionId)}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-UAA-Idempotency-Key": localTaskCommitIdempotencyRef(
          actionId,
          request,
        ),
      }),
      body: JSON.stringify(request),
    },
  );
  const data = (await readJsonSafely(
    response,
  )) as ResultEnvelope<FounderLoopLocalTaskCommitReceipt>;
  const receipt = data.result ?? data.data;
  if (!response.ok || !receipt) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          data,
          "Local task commit receipt was not recorded safely.",
        ),
      ),
    );
  }
  return receipt;
}

export async function persistWorkBoardOrder(
  request: WorkBoardReorderRequest,
  idempotencyRef: string,
): Promise<WorkBoardReorderReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.controlCenterWorkBoardReorder}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-UAA-Idempotency-Key": idempotencyRef,
      }),
      body: JSON.stringify(request),
    },
  );
  const data = (await readJsonSafely(
    response,
  )) as ResultEnvelope<WorkBoardReorderReceipt>;
  const receipt = data.result ?? data.data;
  if (!response.ok || !receipt) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          data,
          "Work Board reorder was not persisted; inspect blocked refs.",
        ),
      ),
    );
  }
  return receipt;
}

export async function fetchFounderActionsInbox(): Promise<FounderLoopActionsInbox> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  return readEnvelope<FounderLoopActionsInbox>(
    API_ENDPOINTS.founderActionsInbox,
  );
}

export async function submitTodayActionEnvelope(
  request: FounderLoopActionEnvelopePromotionRequest,
): Promise<FounderLoopActionEnvelopePromotionReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.founderTodayActionEnvelope}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-UAA-Idempotency-Key": todayActionEnvelopeIdempotencyRef(
          request.today_item_ref,
          request,
        ),
      }),
      body: JSON.stringify(request),
    },
  );
  const data =
    (await response.json()) as ResultEnvelope<FounderLoopActionEnvelopePromotionReceipt>;
  const receipt = data.result ?? data.data;
  if (!response.ok || !receipt) {
    throw new Error(
      sanitizeForDisplay(
        data.error?.message ??
          "Today action envelope receipt was not recorded safely.",
      ),
    );
  }
  return receipt;
}

export async function submitWebEvidenceAttachment(
  request: WebEvidenceProductSliceRequest,
): Promise<WebEvidenceProductSliceReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.controlCenterWebEvidenceAttach}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-UAA-Idempotency-Ref": request.request_ref,
      }),
      body: JSON.stringify(request),
    },
  );
  const data = (await readJsonSafely(
    response,
  )) as ResultEnvelope<WebEvidenceProductSliceReceipt>;
  const receipt = data.result ?? data.data;
  const ok = data.ok ?? data.success;
  if (!response.ok || ok === false || !receipt) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          data,
          "Web evidence preview was not attached safely.",
        ),
      ),
    );
  }
  if (!isSafeWebEvidenceProductSliceReceipt(receipt)) {
    throw new Error(
      sanitizeForDisplay("Web evidence receipt was rejected safely."),
    );
  }
  return receipt;
}

const WEB_EVIDENCE_RECEIPT_DENIED_FLAGS = [
  "raw_response_body_stored",
  "raw_headers_stored",
  "absolute_url_returned",
  "query_string_returned",
  "auth_session_state_used",
  "request_body_sent",
  "non_get_method_used",
  "redirect_followed",
  "download_performed",
  "browser_automation_performed",
  "context_injection_performed",
  "memory_write_performed",
  "model_call_performed",
  "connector_write_performed",
  "action_execution_performed",
  "production_authority_granted",
] as const;

const WEB_EVIDENCE_RECEIPT_REQUIRED_ARRAYS = [
  "receipt_refs",
  "evidence_refs",
  "audit_refs",
  "rollback_refs",
  "safe_disable_refs",
  "blocked_authority_refs",
] as const;

const WEB_EVIDENCE_REQUIRED_BLOCKED_REFS = [
  "blocked-state:web-evidence:no-browser-actions",
  "blocked-state:web-evidence:no-auth-session-state",
  "blocked-state:web-evidence:no-downloads-or-uploads",
  "blocked-state:web-evidence:no-post-put-patch-delete",
  "blocked-state:web-evidence:no-raw-body-persistence",
  "blocked-state:web-evidence:no-context-injection",
  "blocked-state:web-evidence:no-memory-write",
  "blocked-state:web-evidence:no-provider-model-call",
  "blocked-state:web-evidence:no-connector-write",
  "blocked-state:web-evidence:no-production-authority",
] as const;

function isSafeWebEvidenceProductSliceReceipt(
  value: unknown,
): value is WebEvidenceProductSliceReceipt {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    value.schema_version ===
      "control-center-web-evidence-product-slice-receipt.v1" &&
    value.contract_ref === "contract-ref:web-evidence-product-slice:v1" &&
    value.source === "python_core_web_evidence_product_slice" &&
    value.route_ref === "POST /control-center/web-evidence/attach" &&
    value.cli_ref === "python scripts/dev/uaa_founder_loop.py attach-web-evidence" &&
    value.safe_refs_only_for_durable_surfaces === true &&
    value.redacted_preview_returned_to_requester === true &&
    value.web_access_gateway_required === true &&
    value.configured_host_allowlist_required === true &&
    value.operator_supplied_host_scope_required === true &&
    value.request_ref_payload_idempotency === true &&
    hasDeniedFlagsFalse(value, WEB_EVIDENCE_RECEIPT_DENIED_FLAGS) &&
    WEB_EVIDENCE_RECEIPT_REQUIRED_ARRAYS.every((field) =>
      Array.isArray(value[field]),
    ) &&
    isSafeWebEvidenceRef(value.request_ref) &&
    isSafeWebEvidenceRef(value.attach_to_ref) &&
    isSafeWebEvidenceRef(value.receipt_ref) &&
    isSafeWebEvidenceRef(value.evidence_ref) &&
    isSafeWebEvidenceRef(value.preview_ref) &&
    isSafeWebEvidenceSafeUrlRef(value.safe_url_ref) &&
    isSafeWebEvidenceRef(value.host_ref) &&
    isSafeWebEvidenceRef(value.transport_ref) &&
    isSafeWebEvidenceRef(value.web_access_request_ref) &&
    isSafeWebEvidenceRef(value.web_access_audit_ref) &&
    isSafeWebEvidenceRef(value.payload_fingerprint_ref) &&
    isSafeWebEvidenceRef(value.redaction_posture_ref) &&
    isSafeWebEvidenceRef(value.request_ref_idempotency_ref) &&
    stringArray(value.receipt_refs).includes(String(value.receipt_ref)) &&
    stringArray(value.evidence_refs).includes(String(value.evidence_ref)) &&
    stringArray(value.audit_refs).includes(String(value.web_access_audit_ref)) &&
    WEB_EVIDENCE_REQUIRED_BLOCKED_REFS.every((ref) =>
      stringArray(value.blocked_authority_refs).includes(ref),
    ) &&
    isSafeWebEvidenceAuditSummary(
      value.web_access_audit_summary,
      String(value.web_access_request_ref),
      String(value.safe_url_ref),
      String(value.host_ref),
    ) &&
    typeof value.redacted_preview === "string" &&
    !containsUnsafeWebEvidencePreview(value.redacted_preview)
  );
}

function isSafeWebEvidenceAuditSummary(
  value: unknown,
  webAccessRequestRef: string,
  safeUrlRef: string,
  hostRef: string,
): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    value.schema_version === "web-access-audit-summary.v1" &&
    value.request_ref === webAccessRequestRef &&
    value.safe_url_ref === safeUrlRef &&
    value.host_ref === hostRef &&
    value.adapter_kind === "local_fetch" &&
    value.network_lane === "tool_runtime_read_only_fetch" &&
    value.authority_mode === "read_only" &&
    value.risk_class === "low" &&
    value.policy_status === "allowed" &&
    value.content_untrusted === true &&
    value.raw_url_omitted === true &&
    value.raw_headers_omitted === true &&
    value.raw_body_omitted === true &&
    typeof value.timestamp === "string" &&
    value.timestamp.length > 0 &&
    Array.isArray(value.policy_reason_refs) &&
    value.policy_reason_refs.every(isSafeWebEvidenceRef) &&
    Array.isArray(value.source_metadata_refs) &&
    value.source_metadata_refs.every(isSafeWebEvidenceRef) &&
    !("url" in value) &&
    !("final_url" in value) &&
    !("absolute_url" in value) &&
    !("raw_url" in value)
  );
}

function isSafeWebEvidenceSafeUrlRef(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^http-fetch-url:[a-z0-9-]+\/(root|path-[a-f0-9]{16})$/.test(value)
  );
}

function isSafeWebEvidenceRef(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^[A-Za-z][A-Za-z0-9_.-]*:[A-Za-z0-9][A-Za-z0-9_.:/@-]*$/.test(value) &&
    !value.toLowerCase().includes("/users/") &&
    !value.toLowerCase().includes("raw_prompt") &&
    !value.toLowerCase().includes("raw_response") &&
    !value.toLowerCase().includes("provider_payload")
  );
}

function containsUnsafeWebEvidencePreview(value: string): boolean {
  const lowered = value.toLowerCase();
  return [
    "https://",
    "http://",
    "/users/",
    "raw prompt",
    "raw response",
    "provider payload",
    "authorization",
    "bearer ",
    "api" + "_key",
    "password",
    "private key",
  ].some((fragment) => lowered.includes(fragment));
}

export async function recordChatTurnReceipt(
  request: ChatTurnReceiptRequest,
): Promise<ChatTurnReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.controlCenterChatTurns}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-UAA-Idempotency-Key": chatTurnReceiptIdempotencyRef(
          request.turn_ref ?? request.model_ref,
          request,
        ),
      }),
      body: JSON.stringify(request),
    },
  );
  const data = (await readJsonSafely(
    response,
  )) as ResultEnvelope<ChatTurnReceipt>;
  const receipt = data.result ?? data.data;
  if (!response.ok || !receipt) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(data, "Chat turn receipt was not recorded safely."),
      ),
    );
  }
  return receipt;
}

export async function fetchChatTurnReceipt(
  turnRef: string,
): Promise<ChatTurnReceipt> {
  return readEnvelope<ChatTurnReceipt>(chatTurnReceiptEndpoint(turnRef));
}

export async function recordChatHandoff(
  turnRef: string,
  target: ChatHandoffTarget,
): Promise<ChatHandoffReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const request: ChatHandoffRequest = {
    handoff_target: target,
    decision_reason_ref: `decision-reason-ref:control-center-chat-${target}`,
    metadata_refs: [`metadata-ref:control-center-chat-handoff:${target}`],
  };
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${chatTurnHandoffEndpoint(turnRef)}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-UAA-Idempotency-Key": chatHandoffIdempotencyRef(
          turnRef,
          target,
          request,
        ),
      }),
      body: JSON.stringify(request),
    },
  );
  const data = (await readJsonSafely(
    response,
  )) as ResultEnvelope<ChatHandoffReceipt>;
  const receipt = data.result ?? data.data;
  if (!response.ok || !receipt) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          data,
          "Chat handoff receipt was not recorded safely.",
        ),
      ),
    );
  }
  return receipt;
}

export async function recordMemoryReviewDecision(
  candidateRef: string,
  decision: MemoryReviewDecisionKind,
  request: MemoryReviewDecisionRequest,
): Promise<MemoryReviewDecisionReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${memoryReviewDecisionEndpoint(candidateRef, decision)}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-UAA-Idempotency-Key": memoryReviewDecisionIdempotencyRef(
          candidateRef,
          decision,
          request,
        ),
      }),
      body: JSON.stringify(request),
    },
  );
  const data = (await readJsonSafely(
    response,
  )) as ResultEnvelope<MemoryReviewDecisionReceipt>;
  const receipt = data.result ?? data.data;
  if (!response.ok || !receipt) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          data,
          "Memory Review decision receipt was not recorded safely.",
        ),
      ),
    );
  }
  return receipt;
}

export async function fetchFounderMemoryContextPacks(): Promise<FounderLoopMemoryContextPacks> {
  return readEnvelope<FounderLoopMemoryContextPacks>(
    API_ENDPOINTS.founderMemoryContextPacks,
  );
}

export async function fetchFounderMemoryRetrievalDiagnostics(): Promise<FounderLoopMemoryRetrievalDiagnostics> {
  return readEnvelope<FounderLoopMemoryRetrievalDiagnostics>(
    API_ENDPOINTS.founderMemoryRetrievalDiagnostics,
  );
}

export async function fetchFounderMemoryCitationIntegrity(): Promise<FounderLoopMemoryCitationIntegrity> {
  return readEnvelope<FounderLoopMemoryCitationIntegrity>(
    API_ENDPOINTS.founderMemoryCitationIntegrity,
  );
}

export async function fetchFounderMemoryQualityIssues(): Promise<FounderLoopMemoryQualityIssues> {
  return readEnvelope<FounderLoopMemoryQualityIssues>(
    API_ENDPOINTS.founderMemoryQualityIssues,
  );
}

export async function fetchFounderMemoryMaintenanceRuns(): Promise<FounderLoopMemoryMaintenanceRuns> {
  return readEnvelope<FounderLoopMemoryMaintenanceRuns>(
    API_ENDPOINTS.founderMemoryMaintenanceRuns,
  );
}

export async function fetchFounderMemoryContextManifest(): Promise<FounderLoopMemoryContextManifest> {
  return readEnvelope<FounderLoopMemoryContextManifest>(
    API_ENDPOINTS.founderMemoryContextManifest,
  );
}

export async function fetchFounderMemoryReview(): Promise<FounderLoopMemoryReview> {
  return readEnvelope<FounderLoopMemoryReview>(
    API_ENDPOINTS.founderMemoryReview,
  );
}

export async function fetchFounderMemoryWorkbench(): Promise<FounderLoopMemoryWorkbench> {
  return readEnvelope<FounderLoopMemoryWorkbench>(
    API_ENDPOINTS.founderMemoryWorkbench,
  );
}

export async function recordManualMemoryCandidate(
  request: ManualMemoryCandidateRequest,
): Promise<ManualMemoryCandidateReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.founderMemoryManualCandidate}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-UAA-Idempotency-Key": manualMemoryCandidateIdempotencyRef(request),
      }),
      body: JSON.stringify(request),
    },
  );
  const data = (await readJsonSafely(
    response,
  )) as ResultEnvelope<ManualMemoryCandidateReceipt>;
  const receipt = data.result ?? data.data;
  if (!response.ok || !receipt) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          data,
          "Manual Memory candidate receipt was not recorded safely.",
        ),
      ),
    );
  }
  return receipt;
}

export async function recordMemoryFeedback(
  request: MemoryFeedbackRequest,
): Promise<MemoryFeedbackReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.founderMemoryFeedback}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-UAA-Idempotency-Key": memoryFeedbackIdempotencyRef(request),
      }),
      body: JSON.stringify(request),
    },
  );
  const data =
    (await readJsonSafely(response)) as ResultEnvelope<MemoryFeedbackReceipt>;
  const receipt = data.result ?? data.data;
  if (!response.ok || !receipt) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          data,
          "Memory feedback receipt was not recorded safely.",
        ),
      ),
    );
  }
  return receipt;
}

export async function recordMemoryContextPackActionProposal(
  contextPackRef: string,
  request: FounderLoopMemoryContextPackActionProposalRequest,
): Promise<FounderLoopMemoryContextPackActionProposalReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${memoryContextPackActionProposalEndpoint(contextPackRef)}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-UAA-Idempotency-Key": memoryContextPackActionIdempotencyRef(
          contextPackRef,
          request,
        ),
      }),
      body: JSON.stringify(request),
    },
  );
  const data = (await readJsonSafely(
    response,
  )) as ResultEnvelope<FounderLoopMemoryContextPackActionProposalReceipt>;
  const receipt = data.result ?? data.data;
  if (!response.ok || !receipt) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          data,
          "Memory context-pack Action proposal receipt was not recorded safely.",
        ),
      ),
    );
  }
  return receipt;
}

export async function fetchMemoryReviewDecisionReceipt(
  candidateRef: string,
): Promise<MemoryReviewDecisionReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  return readEnvelope<MemoryReviewDecisionReceipt>(
    memoryReviewReceiptEndpoint(candidateRef),
  );
}

function actionDecisionIdempotencyRef(
  actionId: string,
  decision: FounderLoopActionDecisionKind,
  request?: FounderLoopActionDecisionRequest,
): string {
  const safeActionId = actionId
    .replace(/^founder-action:/, "")
    .toLowerCase()
    .replace(/[^a-z0-9_.:-]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `idempotency-ref:control-center-action:${decision}:${safeActionId || "missing"}:${safeChatSuffix(request?.decision_reason_ref ?? "decision")}`;
}

function localTaskCommitIdempotencyRef(
  actionId: string,
  request?: FounderLoopLocalTaskCommitRequest,
): string {
  const safeActionId = actionId
    .replace(/^founder-action:/, "")
    .toLowerCase()
    .replace(/[^a-z0-9_.:-]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `idempotency-ref:control-center-local-task:${safeActionId || "missing"}:${safeChatSuffix(request?.approval_ref ?? "approval")}`;
}

function todayActionEnvelopeIdempotencyRef(
  todayItemRef: string,
  request?: FounderLoopActionEnvelopePromotionRequest,
): string {
  const safeTodayItemRef = todayItemRef
    .toLowerCase()
    .replace(/[^a-z0-9_.:-]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `idempotency-ref:control-center-today-action:${safeTodayItemRef || "missing"}:${safeChatSuffix(request?.decision_reason_ref ?? "decision")}`;
}

function chatTurnReceiptIdempotencyRef(
  turnRef: string,
  request?: ChatTurnReceiptRequest,
): string {
  const postureMaterial = stableStringifyForIdempotency(request ?? {});
  return `idempotency-ref:control-center-chat-turn:${safeChatSuffix(turnRef)}:${safeChatSuffix(request?.safe_summary_ref ?? "summary")}:${safeHashSuffix(postureMaterial)}`;
}

function chatHandoffIdempotencyRef(
  turnRef: string,
  target: ChatHandoffTarget,
  request?: ChatHandoffRequest,
): string {
  return `idempotency-ref:control-center-chat-handoff:${target}:${safeChatSuffix(turnRef)}:${safeChatSuffix(request?.decision_reason_ref ?? "decision")}`;
}

function localChatProbeIdempotencyRef(modelId: string): string {
  return `idempotency-ref:control-center-local-chat-probe:${safeChatSuffix(modelId || DEFAULT_LOCAL_MODEL_ID)}`;
}

function memoryReviewDecisionIdempotencyRef(
  candidateRef: string,
  decision: MemoryReviewDecisionKind,
  request?: MemoryReviewDecisionRequest,
): string {
  return `idempotency-ref:control-center-memory-review:${decision}:${safeChatSuffix(candidateRef)}:${safeChatSuffix(request?.reviewer_ref ?? "reviewer")}:${safeChatSuffix(request?.corrected_summary_ref ?? "none")}:${safeHashSuffix(request?.corrected_safe_summary ?? "none")}:${safeChatSuffix((request?.merge_refs ?? []).join("-") || "no-merge")}:${safeChatSuffix((request?.supersedes_refs ?? []).join("-") || "no-supersede")}:${safeChatSuffix(request?.forget_request_ref ?? "no-forget")}`;
}

function manualMemoryCandidateIdempotencyRef(
  request: ManualMemoryCandidateRequest,
): string {
  const refMaterial = [
    request.candidate_kind,
    request.priority ?? "medium",
    request.reviewer_ref ?? "actor-ref:local-operator",
    ...(request.source_refs ?? []),
    ...(request.provenance_refs ?? []),
    ...(request.evidence_refs ?? []),
    ...(request.missing_evidence_refs ?? []),
    ...(request.related_entity_refs ?? []),
    ...(request.tag_refs ?? []),
    ...(request.metadata_refs ?? []),
    ...(request.blocked_state_refs ?? []),
    safeHashSuffix(`${request.title}|${request.safe_summary}`),
  ].join("|");
  return `idempotency-ref:control-center-manual-memory:${safeChatSuffix(request.candidate_kind)}:${safeHashSuffix(refMaterial)}`;
}

function memoryContextPackActionIdempotencyRef(
  contextPackRef: string,
  request?: FounderLoopMemoryContextPackActionProposalRequest,
): string {
  return `idempotency-ref:control-center-memory-context-action:${safeChatSuffix(contextPackRef)}:${safeChatSuffix(request?.decision_reason_ref ?? "proposal")}`;
}

function memoryFeedbackIdempotencyRef(request: MemoryFeedbackRequest): string {
  const refMaterial = [
    request.target_ref,
    request.target_kind,
    request.feedback_kind,
    request.reviewer_ref ?? "actor-ref:local-operator",
    ...(request.evidence_refs ?? []),
    ...(request.reason_refs ?? []),
    ...(request.metadata_refs ?? []),
    ...request.blocked_state_refs,
  ].join("|");
  return `idempotency-ref:control-center-memory-feedback:${safeChatSuffix(request.feedback_kind)}:${safeHashSuffix(refMaterial)}`;
}

export async function inspectLocalModelsRoute(): Promise<LocalModelsInspectionStatus> {
  const checkedAt = new Date().toISOString();
  if (!API_BASE_POLICY.allowed) {
    return {
      state: "blocked",
      routeRef: API_ENDPOINTS.localModels,
      checkedAt,
      safeMessage: API_BASE_POLICY.safeMessage,
      modelIds: [],
      reasonCodes: ["LOCAL_API_BASE_BLOCKED"],
    };
  }

  try {
    const response = await fetch(
      `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.localModels}`,
      {
        headers: withLocalApiAuthHeaders({ Accept: "application/json" }),
      },
    );
    const data = await readJsonSafely(response);
    if (!response.ok) {
      return localModelsFailureStatus(response.status, data, checkedAt);
    }
    const modelIds = extractModelIds(data);
    return {
      state: modelIds.length > 0 ? "ready" : "degraded",
      routeRef: API_ENDPOINTS.localModels,
      checkedAt,
      safeMessage:
        modelIds.length > 0
          ? "Local model list is reachable through the UAA /v1 gateway."
          : "Local model route answered, but no model identifiers were listed.",
      modelIds,
      selectedModelId: modelIds[0],
      statusCode: response.status,
      reasonCodes:
        modelIds.length > 0
          ? ["LOCAL_MODELS_ROUTE_READY"]
          : ["LOCAL_MODELS_EMPTY"],
    };
  } catch {
    return {
      state: "unavailable",
      routeRef: API_ENDPOINTS.localModels,
      checkedAt,
      safeMessage:
        "Local model route could not be reached safely from Control Center.",
      modelIds: [],
      reasonCodes: ["LOCAL_MODELS_ROUTE_UNAVAILABLE"],
    };
  }
}

export async function requestRedactedLocalChatProbe(
  modelId = DEFAULT_LOCAL_MODEL_ID,
): Promise<RedactedLocalChatProbeStatus> {
  const startedAt =
    typeof performance !== "undefined" ? performance.now() : Date.now();
  const checkedAt = new Date().toISOString();
  const base = chatProbeBase(modelId, checkedAt);
  if (!API_BASE_POLICY.allowed) {
    return {
      ...base,
      state: "blocked",
      routeRef: API_ENDPOINTS.localChatCompletions,
      safeMessage: API_BASE_POLICY.safeMessage,
      reasonCodes: ["LOCAL_API_BASE_BLOCKED"],
    };
  }

  try {
    const response = await fetch(
      `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.localChatCompletions}`,
      {
        method: "POST",
        headers: withLocalApiAuthHeaders({
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-UAA-Idempotency-Key": localChatProbeIdempotencyRef(modelId),
        }),
        body: JSON.stringify({
          model: modelId,
          messages: [{ role: "user", content: "status" }],
          max_tokens: 8,
          stream: false,
        }),
      },
    );
    const data = await readJsonSafely(response);
    const durationMs = Math.round(
      (typeof performance !== "undefined" ? performance.now() : Date.now()) -
        startedAt,
    );
    if (!response.ok) {
      const failureState = response.status === 401 ? "denied" : "blocked";
      return {
        ...base,
        state: failureState,
        routeRef: API_ENDPOINTS.localChatCompletions,
        safeMessage: sanitizeForDisplay(
          extractErrorMessage(
            data,
            "Local chat route denied the readiness exchange.",
          ),
        ),
        runtimeTruth: "local-chat-route-denied",
        authTruth:
          response.status === 401
            ? "local-bearer-required"
            : "local-auth-or-runtime-blocked",
        statusCode: response.status,
        durationMs,
        reasonCodes: [
          response.status === 401
            ? "LOCAL_CHAT_BEARER_REQUIRED"
            : "LOCAL_CHAT_ROUTE_BLOCKED",
        ],
      };
    }
    const safety = extractSafetyRecord(data);
    const turnHarnessBinding = isSafeTurnHarnessBinding(
      safety.turn_harness_binding,
    )
      ? safety.turn_harness_binding
      : undefined;
    return {
      ...base,
      state: "ready",
      routeRef: API_ENDPOINTS.localChatCompletions,
      safeMessage:
        "Local chat completion route answered. The response body is not displayed by Control Center.",
      runtimeTruth: "local-chat-route-answered",
      authTruth: "local-bearer-accepted",
      toolDenialTruth:
        safetyFlagIsFalse(safety, ["tool_executed", "tools_enabled"]) &&
        safetyFlagIsFalse(safety, ["functions_enabled"]) &&
        safetyFlagIsFalse(safety, ["streaming_enabled"])
          ? "tools-functions-streaming-denied"
          : "tool-denial-truth-unavailable",
      statusCode: response.status,
      durationMs,
      reasonCodes: [
        "LOCAL_CHAT_REDACTED_PROBE_READY",
        turnHarnessBinding
          ? "TURN_HARNESS_BINDING_READY"
          : "TURN_HARNESS_BINDING_UNAVAILABLE_OR_REJECTED",
      ],
      turnHarnessBinding,
    };
  } catch {
    return {
      ...base,
      state: "unavailable",
      routeRef: API_ENDPOINTS.localChatCompletions,
      safeMessage:
        "Local chat route could not be reached safely from Control Center.",
      runtimeTruth: "local-chat-route-unavailable",
      authTruth: "auth-not-evaluated",
      reasonCodes: ["LOCAL_CHAT_ROUTE_UNAVAILABLE"],
    };
  }
}

function chatProbeBase(
  modelId: string,
  checkedAt: string,
): Omit<
  RedactedLocalChatProbeStatus,
  "state" | "safeMessage" | "reasonCodes" | "statusCode" | "durationMs"
> {
  const safeModelRef = safeChatSuffix(modelId);
  return {
    routeRef: API_ENDPOINTS.localChatCompletions,
    checkedAt,
    contractRef: CHAT_OPERATOR_CONTRACT_REF,
    turnRef: `chat-turn:local-operator:${safeModelRef}`,
    modelId,
    runtimeTruth: "runtime-not-contacted",
    authTruth: "auth-not-evaluated",
    toolDenialTruth: "tools-functions-streaming-denied",
    toolDenialRef: `tool-denial-ref:chat-local-operator:${safeModelRef}`,
    evidenceRefs: ["evidence-ref:chat-local-operator:browser-probe"],
    plansHandoffRef: `handoff-ref:chat-to-plans:${safeModelRef}`,
    actionsHandoffRef: `handoff-ref:chat-to-actions:${safeModelRef}`,
    blockedStateRefs: CHAT_OPERATOR_BLOCKED_REFS,
    modelOutputAuthority: false,
    toolExecutionEnabled: false,
    memoryWriteAuthorized: false,
    contextInjectionAuthorized: false,
    providerSdkCallEnabled: false,
    webFetchEnabled: false,
    connectorWriteEnabled: false,
    shellSubprocessExecutionEnabled: false,
    actionExecutionEnabled: false,
    approvalGrantCaptureEnabled: false,
    productionAuthorityEnabled: false,
    responseVisible: false,
  };
}

function safeChatSuffix(value: string): string {
  return (
    value
      .trim()
      .toLowerCase()
      .replaceAll(":", "-")
      .replace(/[^a-z0-9_.@-]+/g, "-")
      .replace(/^-+|-+$/g, "") || "missing"
  );
}

function safeHashSuffix(value: string): string {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16);
}

function stableStringifyForIdempotency(value: unknown): string {
  if (value === null) {
    return "null";
  }
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableStringifyForIdempotency(item)).join(",")}]`;
  }
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    return `{${Object.keys(record)
      .filter((key) => record[key] !== undefined)
      .sort()
      .map(
        (key) =>
          `${JSON.stringify(key)}:${stableStringifyForIdempotency(record[key])}`,
      )
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

function extractSafetyRecord(data: unknown): Record<string, unknown> {
  const candidate = unwrapEnvelope(data);
  if (typeof candidate !== "object" || candidate === null) {
    return {};
  }
  const record = candidate as Record<string, unknown>;
  const safety = record.uaa_safety;
  return typeof safety === "object" && safety !== null
    ? (safety as Record<string, unknown>)
    : {};
}

function safetyFlagIsFalse(
  safety: Record<string, unknown>,
  names: string[],
): boolean {
  return names.some((name) => safety[name] === false);
}

function isSafeRuntimeDelegationAdapter(
  value: RuntimeDelegationAdapterReadModel | undefined,
): value is RuntimeDelegationAdapterReadModel {
  if (value === undefined || !isPlainRecord(value.endpoint_posture)) {
    return false;
  }
  const deniedTopLevelFlags: Array<keyof RuntimeDelegationAdapterReadModel> = [
    "control_center_talks_directly_to_runtime",
    "live_run_submission_enabled",
    "runtime_model_calls_enabled",
    "provider_sdk_calls_enabled",
    "tool_execution_enabled",
    "shell_execution_enabled",
    "browser_automation_enabled",
    "connector_write_enabled",
    "background_autonomy_enabled",
    "production_authority_enabled",
    "raw_prompt_persisted",
    "raw_response_persisted",
    "raw_provider_payload_persisted",
    "raw_log_persisted",
    "raw_local_path_persisted",
    "credential_material_persisted",
  ];
  const endpoint = value.endpoint_posture;
  return (
    value.schema_version === "runtime_delegation_adapter.v1" &&
    value.status === "readiness_only" &&
    value.runtime_kind === "hermes_agent" &&
    value.uaa_controls_authority === true &&
    value.runtime_provides_capability_only === true &&
    value.safe_refs_only === true &&
    endpoint.live_transport_enabled === false &&
    endpoint.credential_material_exposed === false &&
    isNonEmptyStringArray(value.capability_refs) &&
    isNonEmptyStringArray(value.health_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.blocked_reason_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.blocked_reason_refs.includes(
      "blocked-authority:runtime-delegation-live-run-submission",
    ) &&
    value.blocked_reason_refs.includes(
      "blocked-authority:runtime-delegation-direct-control-center-runtime-access",
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeCapabilityDiscovery(
  value: RuntimeCapabilityDiscoveryReadModel | undefined,
): value is RuntimeCapabilityDiscoveryReadModel {
  if (value === undefined || !Array.isArray(value.capability_groups)) {
    return false;
  }
  const requiredGroupKinds = [
    "models",
    "runs",
    "events",
    "approvals",
    "sessions",
    "skills",
    "toolsets",
    "jobs",
    "blocked_actions",
  ] as const;
  const groupKinds = new Set(
    value.capability_groups.map((group) => group.group_kind),
  );
  const deniedTopLevelFlags: Array<keyof RuntimeCapabilityDiscoveryReadModel> = [
    "runtime_reachable",
    "live_discovery_performed",
    "control_center_talks_directly_to_runtime",
    "raw_prompt_persisted",
    "raw_response_persisted",
    "raw_provider_payload_persisted",
    "raw_runtime_payload_persisted",
    "raw_log_persisted",
    "raw_local_path_persisted",
    "credential_material_persisted",
  ];
  return (
    value.schema_version === "runtime_capability_discovery.v1" &&
    value.status === "static_readiness_only" &&
    value.uaa_controls_authority === true &&
    value.safe_refs_only === true &&
    value.stale === true &&
    value.stale_or_unreachable_degrades_to_blocked === true &&
    value.runtime_supported_cannot_grant_uaa_permission === true &&
    value.uaa_authorized_capability_count === 0 &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    requiredGroupKinds.every((kind) => groupKinds.has(kind)) &&
    value.capability_groups.every(
      (group) =>
        group.uaa_authorized_for_execution === false &&
        group.stale_or_unreachable_degrades_to_blocked === true &&
        isNonEmptyStringArray(group.capability_refs) &&
        isNonEmptyStringArray(group.blocked_authority_refs) &&
        isNonEmptyStringArray(group.next_safe_action_refs),
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeRunEvents(
  value: RuntimeRunEventsReadModel | undefined,
): value is RuntimeRunEventsReadModel {
  if (
    value === undefined ||
    !Array.isArray(value.lifecycle_mappings) ||
    !Array.isArray(value.run_proposals) ||
    !Array.isArray(value.event_previews)
  ) {
    return false;
  }
  const deniedTopLevelFlags: Array<keyof RuntimeRunEventsReadModel> = [
    "create_run_route_enabled",
    "stop_run_route_enabled",
    "approval_resolution_route_enabled",
    "live_event_stream_enabled",
    "control_center_talks_directly_to_runtime",
    "raw_prompt_persisted",
    "raw_response_persisted",
    "raw_provider_payload_persisted",
    "raw_runtime_payload_persisted",
    "raw_log_persisted",
    "raw_local_path_persisted",
    "credential_material_persisted",
  ];
  return (
    value.schema_version === "runtime_run_events.v1" &&
    value.status === "proposal_read_model_only" &&
    value.uaa_controls_authority === true &&
    value.no_mutation_routes_registered === true &&
    value.safe_refs_only === true &&
    value.proposal_count === value.run_proposals.length &&
    value.approval_wait_count ===
      value.run_proposals.filter(
        (proposal) => proposal.uaa_durable_run_state === "approval_wait",
      ).length &&
    value.completed_run_count === 0 &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.lifecycle_mappings.length > 0 &&
    value.lifecycle_mappings.every(
      (mapping) => mapping.receipt_required_before_claim === true,
    ) &&
    value.run_proposals.every(
      (proposal) =>
        proposal.uaa_durable_run_state !== "completed" &&
        proposal.create_run_enabled === false &&
        proposal.stop_run_enabled === false &&
        proposal.approval_resolution_enabled === false &&
        proposal.live_event_stream_enabled === false &&
        proposal.retry_recovery_enabled === false &&
        proposal.cancellation_proof_required === true &&
        isNonEmptyStringArray(proposal.event_refs) &&
        isNonEmptyStringArray(proposal.proof_refs) &&
        isNonEmptyStringArray(proposal.blocked_authority_refs),
    ) &&
    value.event_previews.every(
      (event) =>
        event.runtime_payload_persisted === false &&
        event.raw_log_persisted === false &&
        event.raw_prompt_persisted === false &&
        event.raw_response_persisted === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeStreamingProgress(
  value: RuntimeStreamingProgressReadModel | undefined,
): value is RuntimeStreamingProgressReadModel {
  if (value === undefined || !Array.isArray(value.event_previews)) {
    return false;
  }
  const deniedTopLevelFlags: Array<keyof RuntimeStreamingProgressReadModel> = [
    "live_subscription_enabled",
    "sse_transport_enabled",
    "websocket_transport_enabled",
    "reconnect_enabled",
    "event_ingest_enabled",
    "control_center_talks_directly_to_runtime",
    "raw_runtime_payload_persisted",
    "raw_tool_payload_persisted",
    "raw_token_persisted",
    "raw_log_persisted",
    "raw_prompt_persisted",
    "raw_response_persisted",
  ];
  const eventSequences = value.event_previews.map((event) => event.sequence);
  const sortedSequences = [...eventSequences].sort((left, right) => left - right);
  const uniqueSequences = new Set(eventSequences);
  const eventKinds = new Set(
    value.event_previews.map((event) => event.event_kind),
  );
  return (
    value.schema_version === "runtime_streaming_progress.v1" &&
    value.status === "read_model_event_preview_only" &&
    value.stream_state === "stale_disconnected" &&
    value.stale_stream === true &&
    value.uaa_controls_authority === true &&
    value.safe_refs_only === true &&
    value.bounded_retention_required === true &&
    value.event_hashes_required === true &&
    value.event_count === value.event_previews.length &&
    eventSequences.length === uniqueSequences.size &&
    eventSequences.every((sequence, index) => sequence === sortedSequences[index]) &&
    eventKinds.has("token") &&
    eventKinds.has("tool_started") &&
    eventKinds.has("tool_completed") &&
    eventKinds.has("approval_wait") &&
    eventKinds.has("warning") &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.event_previews.every(
      (event) =>
        typeof event.event_ref === "string" &&
        typeof event.proof_ref === "string" &&
        typeof event.event_hash_ref === "string" &&
        value.proof_refs.includes(event.proof_ref) &&
        event.event_hash_ref.startsWith("event-hash-ref:") &&
        event.preview_limit_bytes > 0 &&
        event.preview_limit_bytes <= 2048 &&
        event.runtime_payload_persisted === false &&
        event.raw_tool_payload_persisted === false &&
        event.raw_token_persisted === false &&
        event.raw_log_persisted === false &&
        event.raw_prompt_persisted === false &&
        event.raw_response_persisted === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeProfileIsolation(
  value: RuntimeProfileIsolationReadModel | undefined,
): value is RuntimeProfileIsolationReadModel {
  if (value === undefined || !Array.isArray(value.profiles)) {
    return false;
  }
  const deniedTopLevelFlags: Array<keyof RuntimeProfileIsolationReadModel> = [
    "profile_creation_enabled",
    "profile_deletion_enabled",
    "runtime_config_write_enabled",
    "sensitive_material_copy_enabled",
    "runtime_default_change_enabled",
    "cross_profile_authority_bleed_allowed",
    "control_center_mints_profiles",
    "raw_profile_names_persisted",
    "raw_workspace_paths_persisted",
    "raw_sensitive_material_persisted",
  ];
  const profileRefs = new Set(value.profiles.map((profile) => profile.profile_ref));
  const delegatedRefs = new Set(
    value.profiles.map((profile) => profile.delegated_runtime_profile_ref),
  );
  const roleSet = new Set(value.profiles.map((profile) => profile.role));
  const hasRefOverlap = [...profileRefs].some((ref) => delegatedRefs.has(ref));
  const configuredCount = value.profiles.filter(
    (profile) => profile.configured_status === "metadata_configured",
  ).length;
  const blockedCount = value.profiles.length - configuredCount;
  return (
    value.schema_version === "runtime_profile_isolation.v1" &&
    value.status === "profile_metadata_read_model_only" &&
    value.uaa_profile_refs_separate_from_delegated_runtime_refs === true &&
    value.safe_refs_only === true &&
    value.profile_count === value.profiles.length &&
    value.configured_profile_count === configuredCount &&
    value.blocked_profile_count === blockedCount &&
    hasRefOverlap === false &&
    roleSet.has("coding") &&
    roleSet.has("research") &&
    roleSet.has("operations") &&
    roleSet.has("crm") &&
    roleSet.has("review") &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.profiles.every(
      (profile) =>
        typeof profile.profile_ref === "string" &&
        typeof profile.delegated_runtime_profile_ref === "string" &&
        profile.profile_ref !== profile.delegated_runtime_profile_ref &&
        profile.configured_for_live_runtime === false &&
        profile.can_create_runtime_profile === false &&
        profile.can_delete_runtime_profile === false &&
        profile.can_write_runtime_config === false &&
        profile.can_copy_sensitive_material === false &&
        profile.can_change_runtime_defaults === false &&
        profile.can_execute_tools === false &&
        profile.can_call_models === false &&
        profile.can_write_memory === false &&
        profile.can_access_workspace_paths === false &&
        profile.cross_profile_authority_bleed_allowed === false &&
        isNonEmptyStringArray(profile.blocked_reason_refs) &&
        isNonEmptyStringArray(profile.proof_refs) &&
        isNonEmptyStringArray(profile.next_safe_action_refs),
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeApprovalBridge(
  value: RuntimeApprovalBridgeReadModel | undefined,
): value is RuntimeApprovalBridgeReadModel {
  if (
    value === undefined ||
    !isPlainRecord(value.action_inbox_projection) ||
    !isPlainRecord(value.scope_validation) ||
    !Array.isArray(value.envelopes) ||
    !Array.isArray(value.decision_previews)
  ) {
    return false;
  }
  const deniedTopLevelFlags: Array<keyof RuntimeApprovalBridgeReadModel> = [
    "approval_resolution_route_enabled",
    "deny_resolution_route_enabled",
    "timeout_resolution_route_enabled",
    "control_center_talks_directly_to_runtime",
    "raw_runtime_payload_persisted",
    "raw_prompt_persisted",
    "raw_response_persisted",
  ];
  const projection = value.action_inbox_projection;
  const denyCount = value.decision_previews.filter(
    (preview) => preview.decision_kind === "deny",
  ).length;
  const timeoutCount = value.decision_previews.filter(
    (preview) => preview.decision_kind === "timeout",
  ).length;
  const scopeMismatchCount = value.decision_previews.filter(
    (preview) => preview.decision_kind === "scope_mismatch",
  ).length;
  return (
    value.schema_version === "runtime_approval_bridge.v1" &&
    value.status === "read_model_resolution_blocked" &&
    value.uaa_controls_authority === true &&
    value.safe_refs_only === true &&
    value.runtime_resolution_sent_count === 0 &&
    value.pending_runtime_approval_count ===
      value.envelopes.filter((envelope) => envelope.state === "runtime_requested")
        .length &&
    value.denied_preview_count === denyCount &&
    value.timeout_preview_count === timeoutCount &&
    value.scope_mismatch_count === scopeMismatchCount &&
    value.scope_validation.scope_matches === false &&
    projection.approval_controls_visible === false &&
    projection.runtime_resolution_controls_visible === false &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.envelopes.length > 0 &&
    value.envelopes.every(
      (envelope) =>
        envelope.runtime_requested === true &&
        envelope.uaa_approval_recorded === false &&
        envelope.runtime_resolution_sent === false &&
        envelope.approval_resolution_enabled === false &&
        envelope.denial_resolution_enabled === false &&
        envelope.timeout_defaults_to_deny === true &&
        envelope.approval_refs_are_identifiers_only === true &&
        envelope.raw_runtime_payload_persisted === false &&
        envelope.raw_prompt_persisted === false &&
        envelope.raw_response_persisted === false &&
        value.proof_refs.includes(envelope.proof_ref) &&
        projection.action_inbox_item_ref === envelope.action_inbox_item_ref &&
        isNonEmptyStringArray(envelope.blocked_authority_refs) &&
        isNonEmptyStringArray(envelope.next_safe_action_refs),
    ) &&
    value.decision_previews.every(
      (preview) =>
        preview.runtime_resolution_sent === false &&
        projection.action_inbox_item_ref === preview.action_inbox_item_ref &&
        isNonEmptyStringArray(preview.blocked_authority_refs),
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeCodingMultiAgentReview(
  value: CodingMultiAgentReviewReadModel | undefined,
): value is CodingMultiAgentReviewReadModel {
  if (value === undefined || !Array.isArray(value.agent_slots)) {
    return false;
  }
  const requiredSlotKinds = [
    "implementer",
    "reviewer",
    "local_verifier",
    "security_reviewer",
    "ux_reviewer",
    "test_fixer",
    "merge_captain",
  ] as const;
  const slotKinds = new Set(value.agent_slots.map((slot) => slot.slot_kind));
  const hasRequiredSlots =
    value.agent_slots.length === requiredSlotKinds.length &&
    requiredSlotKinds.every((slotKind) => slotKinds.has(slotKind));
  const hasRequiredRefGroups = [
    value.backend_route_refs,
    value.frontend_route_refs,
    value.cli_inspection_refs,
    value.docs_refs,
    value.unblock_prompt_refs,
    value.plan_artifact_refs,
    value.review_artifact_refs,
    value.diff_comparison_refs,
    value.disagreement_summary_refs,
    value.handoff_refs,
    value.proof_refs,
    value.evidence_refs,
    value.blocked_authority_refs,
    value.promotion_path_refs,
    value.redactions_applied,
  ].every(isNonEmptyStringArray);
  const deniedTopLevelFlags: Array<keyof CodingMultiAgentReviewReadModel> = [
    "provider_model_call_enabled",
    "provider_sdk_call_enabled",
    "local_agent_execution_enabled",
    "multi_agent_execution_enabled",
    "background_dispatch_enabled",
    "background_autonomy_enabled",
    "autonomous_execution_enabled",
    "context_injection_enabled",
    "raw_prompt_included",
    "raw_response_included",
    "provider_payload_included",
    "file_write_enabled",
    "shell_subprocess_execution_enabled",
    "git_mutation_enabled",
    "browser_automation_enabled",
    "connector_write_enabled",
    "production_authority_enabled",
  ];
  const safeTopLevel =
    value.status === "blocked_missing_multi_agent_authority" &&
    value.backend_owned === true &&
    value.read_only === true &&
    value.proposal_only === true &&
    value.safe_refs_only === true &&
    hasRequiredSlots &&
    hasRequiredRefGroups &&
    deniedTopLevelFlags.every((flag) => value[flag] === false);
  const safeSlots = value.agent_slots.every(
    (slot) =>
      isNonEmptyStringArray(slot.output_artifact_refs) &&
      isNonEmptyStringArray(slot.proof_refs) &&
      isNonEmptyStringArray(slot.evidence_refs) &&
      isNonEmptyStringArray(slot.blocked_authority_refs) &&
      slot.provider_model_call_enabled === false &&
      slot.local_agent_execution_enabled === false &&
      slot.background_dispatch_enabled === false &&
      slot.autonomous_execution_enabled === false &&
      slot.raw_prompt_included === false &&
      slot.raw_response_included === false,
  );
  return safeTopLevel && safeSlots;
}

function isSafeFounderAgentLoopThread(
  value: FounderLoopAgentLoopThread | undefined,
): value is FounderLoopAgentLoopThread {
  if (value === undefined) {
    return false;
  }
  return (
    value.backend_owned === true &&
    value.local_read_model_only === true &&
    value.safe_refs_only === true &&
    value.raw_content_included === false &&
    typeof value.contract_ref === "string" &&
    typeof value.route_ref === "string" &&
    typeof value.cli_ref === "string" &&
    Array.isArray(value.plan?.steps) &&
    Array.isArray(value.proposed_actions) &&
    Array.isArray(value.evidence?.evidence_refs) &&
    Array.isArray(value.memory_review?.candidate_refs) &&
    value.operator_decision_matrix?.backend_owned === true &&
    value.operator_decision_matrix?.control_center_presentation_only === true &&
    value.operator_decision_matrix?.safe_refs_only === true &&
    value.operator_decision_matrix?.raw_content_included === false &&
    value.operator_decision_matrix?.ui_mints_authority === false &&
    value.operator_decision_matrix?.mutation_controls_enabled === false &&
    Array.isArray(value.operator_decision_matrix?.rows) &&
    value.operator_decision_matrix.rows.length > 0 &&
    value.operator_decision_matrix.rows.every(
      (row) =>
        typeof row.surface === "string" &&
        typeof row.backend_route_ref === "string" &&
        typeof row.cli_ref === "string" &&
        row.backend_truth_required === true &&
        row.mutation_enabled === false,
    ) &&
    Array.isArray(value.blocked_authority_refs) &&
    value.approval_posture?.control_center_mints_authority === false &&
    value.approval_posture?.action_execution_enabled === false &&
    value.authority_posture?.python_core_owns_truth === true &&
    value.authority_posture?.control_center_mints_authority === false &&
    value.authority_posture?.runtime_model_calls_enabled === false &&
    value.authority_posture?.provider_sdk_calls_enabled === false &&
    value.authority_posture?.live_web_fetching_enabled === false &&
    value.authority_posture?.browser_automation_enabled === false &&
    value.authority_posture?.connector_writes_enabled === false &&
    value.authority_posture?.unrestricted_shell_enabled === false &&
    value.authority_posture?.plugin_runtime_import_enabled === false &&
    value.authority_posture?.memory_write_authority_enabled === false &&
    value.authority_posture?.background_autonomy_enabled === false &&
    value.authority_posture?.production_authority_enabled === false
  );
}

function isNonEmptyStringArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.length > 0 &&
    value.every((item) => typeof item === "string" && item.length > 0)
  );
}

interface RouteReadStateInput {
  route: string;
  surfaceLabel: string;
  backendRouteRef?: string;
  backendRouteRefs?: string[];
  endpointReturned: boolean;
  usedFallback: boolean;
  warningRefs?: string[];
}

function routeReadStateInput(input: RouteReadStateInput): RouteReadStateInput {
  return input;
}

function buildRouteReadStates(
  inputs: RouteReadStateInput[],
): Record<string, ControlCenterRouteReadState> {
  return Object.fromEntries(
    inputs.map((input) => [input.route, buildRouteReadState(input)]),
  );
}

function buildRouteReadState(
  input: RouteReadStateInput,
): ControlCenterRouteReadState {
  const state: ControlCenterRouteReadStateKind = !input.endpointReturned
    ? "mock_fallback"
    : input.usedFallback
      ? "degraded"
      : "backend_owned";
  const labels: Record<ControlCenterRouteReadStateKind, string> = {
    backend_owned: "backend-owned",
    degraded: "partial backend",
    mock_fallback: "mock fallback",
    blocked: "blocked",
    planned: "planned",
  };
  const summaries: Record<ControlCenterRouteReadStateKind, string> = {
    backend_owned: `${input.surfaceLabel} read model returned from the local backend contract.`,
    degraded: `${input.surfaceLabel} returned with missing fields or fallback sections; treat it as partial route evidence.`,
    mock_fallback: `${input.surfaceLabel} backend read model did not return; non-authoritative fallback data is visible.`,
    blocked: `${input.surfaceLabel} runtime authority is blocked until an exact scoped lane graduates.`,
    planned: `${input.surfaceLabel} is planned and does not claim release-ready workflow state.`,
  };
  const fallbackWarningRefs =
    input.warningRefs && input.warningRefs.length > 0
      ? input.warningRefs
      : [`route-read-state:${input.route}:fallback`];
  const backendRouteRefs =
    input.backendRouteRefs ??
    (input.backendRouteRef === undefined ? [] : [input.backendRouteRef]);
  const warningRefs = state === "backend_owned" ? [] : fallbackWarningRefs;
  return {
    route: input.route,
    surfaceLabel: input.surfaceLabel,
    state,
    statusLabel: labels[state],
    sourceLabel:
      state === "backend_owned"
        ? "Python Core/API read model"
        : "frontend fallback provenance from local read attempt",
    safeSummary: summaries[state],
    backendRouteRefs,
    warningRefs,
    blockedAuthorityRefs: [
      "blocked-state:no-provider-model-call",
      "blocked-state:no-connector-write",
      "blocked-state:no-browser-automation",
      "blocked-state:no-shell-subprocess-execution",
      "blocked-state:no-production-authority",
    ],
    nextSafeAction:
      state === "backend_owned"
        ? "Inspect proof, receipts, and blocked authority refs before relying on the route."
        : "Keep the route partial and use CLI/verifier evidence before promotion.",
  };
}

function withConnection(
  data: ControlCenterData,
  connection: Pick<
    BackendConnectionSummary,
    "state" | "safeMessage" | "usingMockData" | "warnings"
  >,
): ControlCenterData {
  return {
    ...data,
    connection: {
      ...connection,
      apiBaseLabel: API_BASE_POLICY.label,
      checkedAt: new Date().toISOString(),
    },
  };
}

function fulfilledValue<T>(result: PromiseSettledResult<T>): T | undefined {
  return result.status === "fulfilled" ? result.value : undefined;
}

function safeRunObservability(
  value: RunObservabilityReadModel | undefined,
): RunObservabilityReadModel | undefined {
  if (value === undefined || !isPlainRecord(value)) {
    return undefined;
  }
  const record = value as unknown as Record<string, unknown>;
  if (
    record.schema_version !== "run_observability_read_model.v1" ||
    record.source !== "python_core_run_observability_read_model" ||
    record.backend_owned !== true ||
    record.safe_refs_only !== true ||
    record.redacted_summaries_only !== true ||
    record.approval_refs_are_identifiers_only !== true ||
    record.control_center_presentation_only !== true ||
    !Array.isArray(record.run_refs) ||
    !Array.isArray(record.blocked_authority_refs) ||
    !Array.isArray(record.proof_refs) ||
    !Array.isArray(record.checkpoint_summaries) ||
    !Array.isArray(record.redacted_error_summaries) ||
    !isPlainRecord(record.retry_recovery_posture) ||
    !isPlainRecord(record.approval_wait_state) ||
    !isPlainRecord(record.cancellation_dead_letter_state) ||
    !isPlainRecord(record.approval_queue) ||
    !isPlainRecord(record.connector_delivery_review_queue)
  ) {
    return undefined;
  }
  const retryRecovery = record.retry_recovery_posture as Record<string, unknown>;
  const approvalWait = record.approval_wait_state as Record<string, unknown>;
  const cancellationDeadLetter = record.cancellation_dead_letter_state as Record<
    string,
    unknown
  >;
  if (
    retryRecovery.retry_execution_enabled !== false ||
    retryRecovery.recovery_execution_enabled !== false ||
    approvalWait.approval_refs_are_identifiers_only !== true ||
    approvalWait.approval_ref_grants_authority !== false ||
    approvalWait.exact_scope_required_before_mutation !== true ||
    approvalWait.resume_execution_enabled !== false ||
    cancellationDeadLetter.cancel_execution_enabled !== false ||
    cancellationDeadLetter.dead_letter_execution_enabled !== false
  ) {
    return undefined;
  }
  const checkpointSummaries = record.checkpoint_summaries as unknown[];
  if (
    !checkpointSummaries.every(
      (item) =>
        isPlainRecord(item) &&
        item.safe_refs_only === true &&
        item.raw_payloads_persisted === false &&
        item.execution_performed === false,
    )
  ) {
    return undefined;
  }
  const redactedErrors = record.redacted_error_summaries as unknown[];
  if (
    !redactedErrors.every(
      (item) => isPlainRecord(item) && item.raw_error_omitted === true,
    )
  ) {
    return undefined;
  }
  for (const deniedFlag of [
    "raw_payloads_persisted",
    "prompt_content_stored",
    "response_content_stored",
    "provider_payload_content_stored",
    "approval_ref_grants_authority",
    "ui_mutation_controls_enabled",
    "cancel_resume_controls_enabled",
    "live_streaming_runtime_enabled",
    "provider_model_calls_enabled",
    "tool_execution_enabled",
    "connector_writes_enabled",
    "connector_sends_enabled",
    "background_worker_enabled",
    "scheduler_enabled",
    "autonomous_execution_enabled",
    "production_authority_enabled",
  ] as const) {
    if (record[deniedFlag] !== false) {
      return undefined;
    }
  }
  return value;
}

function mergeMissingFields<T>(
  fallback: T,
  value: T | undefined,
): { value: T; usedFallback: boolean } {
  if (value === undefined) {
    return { value: fallback, usedFallback: true };
  }
  if (!isPlainRecord(fallback) || !isPlainRecord(value)) {
    return { value, usedFallback: false };
  }

  let usedFallback = false;
  const merged: Record<string, unknown> = { ...fallback };
  const valueRecord = value as Record<string, unknown>;
  const fallbackRecord = fallback as Record<string, unknown>;

  for (const key of Object.keys(valueRecord)) {
    const childValue = valueRecord[key];
    const childFallback = fallbackRecord[key];
    if (
      childValue !== undefined &&
      isPlainRecord(childFallback) &&
      isPlainRecord(childValue)
    ) {
      const childMerge = mergeMissingFields(childFallback, childValue);
      merged[key] = childMerge.value;
      usedFallback = usedFallback || childMerge.usedFallback;
    } else {
      merged[key] = childValue;
    }
  }

  for (const key of Object.keys(fallbackRecord)) {
    if (!Object.prototype.hasOwnProperty.call(valueRecord, key)) {
      usedFallback = true;
    }
  }

  return { value: merged as T, usedFallback };
}

function normalizeFounderMemoryContextPacks(
  value: FounderLoopMemoryContextPacks | undefined,
): { value: FounderLoopMemoryContextPacks; usedFallback: boolean } {
  if (value === undefined) {
    return {
      value: mockControlCenterData.founderMemoryContextPacks,
      usedFallback: true,
    };
  }
  const merged = mergeMissingFields(
    mockControlCenterData.founderMemoryContextPacks,
    value,
  );
  const proposals = Array.isArray(value.proposals) ? value.proposals : [];
  const internalActionProposalReceipts = Array.isArray(
    value.internal_action_proposal_receipts,
  )
    ? value.internal_action_proposal_receipts
    : [];
  const blockedStateRefs = Array.isArray(value.blocked_state_refs)
    ? value.blocked_state_refs
    : [];
  return {
    value: {
      ...merged.value,
      context_pack_count:
        typeof value.context_pack_count === "number"
          ? value.context_pack_count
          : proposals.length,
      proposals,
      internal_action_proposal_receipts: internalActionProposalReceipts,
      blocked_state_refs: blockedStateRefs,
    },
    usedFallback: merged.usedFallback,
  };
}

function normalizeFounderMemoryContextManifest(
  value: FounderLoopMemoryContextManifest | undefined,
): { value: FounderLoopMemoryContextManifest; usedFallback: boolean } {
  if (value === undefined) {
    return {
      value: mockControlCenterData.founderMemoryContextManifest,
      usedFallback: true,
    };
  }
  const merged = mergeMissingFields(
    mockControlCenterData.founderMemoryContextManifest,
    value,
  );
  const manifests = Array.isArray(value.manifests) ? value.manifests : [];
  const blockedStateRefs = Array.isArray(value.blocked_state_refs)
    ? value.blocked_state_refs
    : [];
  return {
    value: {
      ...merged.value,
      manifest_count:
        typeof value.manifest_count === "number"
          ? value.manifest_count
          : manifests.length,
      manifests,
      context_pack_preview_count:
        typeof value.context_pack_preview_count === "number"
          ? value.context_pack_preview_count
          : manifests.length,
      blocked_state_refs: blockedStateRefs,
    },
    usedFallback: merged.usedFallback,
  };
}

function normalizeControlCenterDashboard(
  value: ControlCenterDashboardSnapshot | undefined,
): { value: ControlCenterDashboardSnapshot; usedFallback: boolean } {
  if (!isPlainRecord(value)) {
    return { value: mockControlCenterData.dashboard, usedFallback: true };
  }
  const normalized = { ...value } as Record<string, unknown>;
  if (
    isSafeProviderCredentialReadiness(normalized.provider_credential_readiness)
  ) {
    return {
      value: normalized as unknown as ControlCenterDashboardSnapshot,
      usedFallback: false,
    };
  }
  normalized.provider_credential_readiness =
    mockControlCenterData.dashboard.provider_credential_readiness;
  return {
    value: normalized as unknown as ControlCenterDashboardSnapshot,
    usedFallback: true,
  };
}

function isSafeModelProviderControlPlane(
  value: unknown,
): value is ModelProviderControlPlaneReadModel {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    value.schema_version !== "model_provider_control_plane.v1" ||
    value.status !== "governed_control_plane_wired" ||
    value.backend_owned !== true ||
    value.read_only !== true ||
    value.safe_refs_only !== true
  ) {
    return false;
  }
  const authority = value.authority;
  if (!isPlainRecord(authority)) {
    return false;
  }
  const authorityFalseFlags = [
    "broad_provider_runtime_enabled",
    "provider_sdk_call_enabled",
    "live_provider_network_call_enabled_by_default",
    "provider_router_execution_enabled",
    "model_router_execution_enabled",
    "local_llama_cpp_process_started_by_control_plane",
    "shell_execution_enabled",
    "background_autonomy_enabled",
    "production_authority_enabled",
    "raw_prompt_response_provider_payload_persisted",
  ];
  const authorityTrueFlags = [
    "exact_tiny_provider_lane_available",
    "exact_tiny_provider_lane_requires_approval",
    "exact_credential_validation_lane_available",
    "exact_credential_validation_requires_approval",
    "provider_router_dry_run_available",
    "model_router_trace_available",
    "local_llama_cpp_gateway_available",
    "local_llama_cpp_lifecycle_contract_available",
  ];
  if (
    authorityFalseFlags.some((field) => authority[field] !== false) ||
    authorityTrueFlags.some((field) => authority[field] !== true)
  ) {
    return false;
  }
  if (
    !Array.isArray(value.provider_adapters) ||
    value.provider_adapters.length < 2 ||
    !value.provider_adapters.every(isSafeProviderAdapterRuntimePosture)
  ) {
    return false;
  }
  if (!isSafeProviderSecretStatusPosture(value.secret_status)) {
    return false;
  }
  if (!isSafeProviderNetworkAllowlistPosture(value.network_allowlists)) {
    return false;
  }
  if (!isSafeModelMetadataDiscoveryPosture(value.model_metadata_discovery)) {
    return false;
  }
  if (!isSafeProviderCostHookPosture(value.cost_hooks)) {
    return false;
  }
  if (!isSafeLocalLlamaCppLifecyclePosture(value.local_llama_cpp_lifecycle)) {
    return false;
  }
  if (
    !Array.isArray(value.router_traces) ||
    value.router_traces.length === 0 ||
    !value.router_traces.every(isSafeModelRouterTracePosture)
  ) {
    return false;
  }
  if (!isSafeModelProviderResearchPosture(value.model_provider_research_posture)) {
    return false;
  }
  return (
    Array.isArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-state:model-provider:broad-provider-runtime",
    ) &&
    Array.isArray(value.exact_lane_route_refs) &&
    value.exact_lane_route_refs.includes(
      "POST /control-center/providers/exact-approved-lanes/tiny",
    )
  );
}

function isSafeModelProviderResearchPosture(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const falseFlags = [
    "provider_sdk_call_enabled",
    "remote_model_call_enabled",
    "live_web_fetch_enabled",
    "browser_automation_enabled",
    "credential_entry_enabled",
    "memory_write_authorized",
    "action_execution_authorized",
    "context_injection_authorized",
    "production_authority_enabled",
    "broad_autonomy_enabled",
  ];
  return (
    value.schema_version === "model_provider_research_posture.v1" &&
    value.status === "metadata_read_model_wired" &&
    value.route_ref === "GET /control-center/providers/runtime-control-plane" &&
    falseFlags.every((field) => value[field] === false) &&
    typeof value.provider_count === "number" &&
    Array.isArray(value.provider_postures) &&
    value.provider_postures.length === value.provider_count &&
    value.provider_postures.every(isSafeModelProviderResearchProviderPosture) &&
    isSafeModelOutputTruthPosture(value.model_output_truth) &&
    isSafeExternalInformationResearchPosture(value.external_information) &&
    Array.isArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-state:model-provider:model-output-as-authority",
    ) &&
    value.blocked_authority_refs.includes(
      "blocked-state:web-access:browser-automation",
    )
  );
}

function isSafeModelProviderResearchProviderPosture(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const falseFlags = [
    "provider_sdk_call_enabled",
    "model_invocation_enabled",
    "credential_material_visible",
    "provider_output_authority_enabled",
    "live_metadata_discovery_enabled",
  ];
  return (
    typeof value.provider_id === "string" &&
    typeof value.provider_label === "string" &&
    typeof value.provider_kind === "string" &&
    [
      "remote_provider_reference",
      "local_runtime_reference",
    ].includes(String(value.local_remote_posture)) &&
    [
      "reference_only",
      "blocked_missing_refs",
      "approval_required_exact_lane",
    ].includes(String(value.status)) &&
    falseFlags.every((field) => value[field] === false) &&
    typeof value.blocked_reason_ref === "string" &&
    typeof value.last_safe_diagnostic_receipt_ref === "string" &&
    typeof value.operator_next_step === "string"
  );
}

function isSafeModelOutputTruthPosture(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const trueFlags = [
    "model_output_is_proposal",
    "model_output_is_evidence_candidate",
    "verified_fact_refs_required",
    "uncertainty_unknowns_required",
  ];
  const falseFlags = [
    "generated_text_is_verified_fact",
    "memory_write_from_model_output_enabled",
    "action_authority_from_model_output_enabled",
    "context_injection_from_model_output_enabled",
    "connector_write_from_model_output_enabled",
    "production_authority_from_model_output_enabled",
  ];
  return (
    value.status === "proposal_and_evidence_not_authority" &&
    trueFlags.every((field) => value[field] === true) &&
    falseFlags.every((field) => value[field] === false) &&
    typeof value.truth_boundary_ref === "string"
  );
}

function isSafeExternalInformationResearchPosture(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const trueFlags = [
    "web_access_gateway_required",
    "default_policy_denied",
    "fetched_content_untrusted",
    "source_metadata_required",
    "audit_record_required",
  ];
  const falseFlags = [
    "fetched_content_instruction_authority_enabled",
    "live_web_fetch_enabled_by_control_plane",
    "browser_observe_enabled_by_control_plane",
    "browser_action_enabled_by_control_plane",
    "provider_search_enabled_by_control_plane",
    "context_injection_from_external_content_enabled",
    "memory_write_from_external_content_enabled",
  ];
  return (
    value.status === "web_access_gateway_deny_by_default" &&
    trueFlags.every((field) => value[field] === true) &&
    falseFlags.every((field) => value[field] === false) &&
    Array.isArray(value.allowed_current_lane_refs) &&
    value.allowed_current_lane_refs.length > 0 &&
    Array.isArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-state:web-access:no-browser-actions",
    )
  );
}

function isSafeProviderAdapterRuntimePosture(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const falseFlags = [
    "provider_sdk_call_enabled",
    "network_call_enabled_by_default",
    "prompt_persistence_allowed",
    "response_persistence_allowed",
    "provider_payload_persistence_allowed",
  ];
  const trueFlags = [
    "network_call_allowed_inside_exact_adapter",
    "credential_ref_required",
    "exact_approval_required",
    "cost_governor_required",
    "receipt_store_required_before_network",
    "redirects_blocked",
  ];
  return (
    value.status === "exact_lane_wired_disabled_by_default" &&
    falseFlags.every((field) => value[field] === false) &&
    trueFlags.every((field) => value[field] === true)
  );
}

function isSafeProviderSecretStatusPosture(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    value.status === "safe_refs_only" &&
    value.secret_material_visible === false &&
    value.secret_material_persisted_by_repo === false &&
    value.transient_secret_resolution_required_for_exact_lanes === true &&
    value.raw_key_collection_enabled === false &&
    isPlainRecord(value.credential_ref_statuses)
  );
}

function isSafeProviderNetworkAllowlistPosture(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    value.status === "exact_endpoint_refs_only" &&
    value.default_network_denied === true &&
    value.broad_web_fetch_enabled === false &&
    value.provider_sdk_network_enabled === false &&
    value.redirects_blocked === true &&
    value.post_mutation_scope_enabled === false &&
    Array.isArray(value.allowlist_refs) &&
    value.allowlist_refs.length > 0 &&
    Array.isArray(value.endpoint_refs) &&
    value.endpoint_refs.length > 0
  );
}

function isSafeModelMetadataDiscoveryPosture(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    value.status === "static_metadata_and_local_inventory" &&
    typeof value.provider_count === "number" &&
    value.provider_count > 0 &&
    Array.isArray(value.provider_model_refs) &&
    value.provider_model_refs.length > 0 &&
    value.live_provider_model_discovery_enabled === false &&
    value.automatic_pricing_fetch_enabled === false &&
    value.runtime_provider_metadata_fetch_enabled === false
  );
}

function isSafeProviderCostHookPosture(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const trueFlags = [
    "cost_estimate_refs_required",
    "budget_decision_refs_required",
    "max_approved_usd_refs_required",
    "expected_receipt_refs_required",
    "actual_usage_cost_refs_required",
    "unknown_paid_cost_blocks",
    "incomplete_actual_cost_blocks_further_use",
  ];
  return (
    value.status === "cost_governor_receipt_bound" &&
    trueFlags.every((field) => value[field] === true) &&
    value.provider_spend_authority_granted === false
  );
}

function isSafeLocalLlamaCppLifecyclePosture(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    value.status === "local_loopback_lifecycle_governed" &&
    value.loopback_only === true &&
    value.structured_argv_only === true &&
    value.shell_string_allowed === false &&
    value.process_start_performed_by_read_model === false &&
    value.model_call_performed_by_read_model === false &&
    value.raw_local_path_returned === false &&
    value.raw_log_stored === false
  );
}

function isSafeModelRouterTracePosture(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    value.status === "trace_only_no_execution" &&
    value.model_execution_performed === false &&
    value.provider_execution_performed === false &&
    value.provider_sdk_call_performed === false &&
    value.prompt_content_persisted === false &&
    value.response_content_persisted === false &&
    Array.isArray(value.reason_codes) &&
    value.reason_codes.length > 0
  );
}

function isSafeProviderCredentialReadiness(
  value: unknown,
): value is ProviderCredentialReadinessSummary {
  if (!isPlainRecord(value)) {
    return false;
  }
  const requiredFalseFlags = [
    "invocation_enabled",
    "raw_key_collection_enabled",
    "credential_material_stored",
    "vault_adapter_configured",
  ];
  if (requiredFalseFlags.some((field) => value[field] !== false)) {
    return false;
  }
  const requiredTrueFlags = [
    "cost_governor_binding_required",
    "provider_model_refs_required",
    "cost_estimate_ref_required",
    "budget_decision_ref_required",
    "max_approved_usd_ref_required",
    "future_receipt_refs_required",
    "unknown_paid_cost_requires_approval",
    "estimated_cost_above_budget_blocks_use",
    "provider_usage_claim_requires_receipt_refs",
    "provider_runtime_authority_denied",
    "provider_spend_authority_denied",
  ];
  if (requiredTrueFlags.some((field) => value[field] !== true)) {
    return false;
  }
  if (
    !isSupportedProviderReadinessPostureList(value.supported_readiness_postures)
  ) {
    return false;
  }
  if (
    !isSafeProviderVaultAdapterReadiness(value.vault_adapter_readiness) ||
    !isSafeProviderCredentialEnrollmentReadiness(value.enrollment_readiness) ||
    !isSafeProviderCredentialValidationReadiness(value.validation_readiness) ||
    !isSafeGovernedProviderInvocationReadiness(value.invocation_readiness) ||
    !isSafeTinyProviderInvocationReadiness(value.tiny_invocation_readiness) ||
    !isSafeProviderRouterDryRunReadiness(value.router_dry_run_readiness) ||
    !isSafeProviderSettingsDiagnostics(value.provider_settings_diagnostics)
  ) {
    return false;
  }
  if (!Array.isArray(value.providers)) {
    return false;
  }
  if (!value.providers.every(isSafeProviderCredentialReadinessItem)) {
    return false;
  }
  if (!providerPostureCountsMatch(value.posture_counts, value.providers)) {
    return false;
  }
  return REQUIRED_PROVIDER_COST_BLOCKERS.every(
    (code) =>
      Array.isArray(value.blocker_codes) && value.blocker_codes.includes(code),
  );
}

function isSafeProviderCredentialReadinessItem(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    value.invocation_enabled !== false ||
    value.credential_material_stored !== false ||
    value.raw_key_visible !== false
  ) {
    return false;
  }
  if (!isProviderReadinessPosture(value.readiness_posture)) {
    return false;
  }
  if (
    (value.readiness_posture === "configured") !==
    (value.credential_configured === true)
  ) {
    return false;
  }
  if (
    (value.readiness_posture === "revoked") !==
    (value.credential_revoked === true)
  ) {
    return false;
  }
  const binding = value.cost_governor_binding;
  if (!isPlainRecord(binding)) {
    return false;
  }
  const requiredBindingRefs = [
    "binding_ref",
    "provider_ref",
    "model_ref",
    "credential_ref",
    "cost_estimate_ref",
    "budget_decision_ref",
    "max_approved_usd_ref",
    "future_receipt_ref",
    "usage_receipt_ref",
    "cost_receipt_ref",
    "cost_governor_posture_ref",
    "cost_governor_decision_ref",
    "cost_governor_ref",
  ];
  if (
    requiredBindingRefs.some(
      (field) =>
        typeof binding[field] !== "string" ||
        String(binding[field]).trim().length === 0,
    )
  ) {
    return false;
  }
  const refsBound =
    binding.provider_ref_status === "present" &&
    binding.model_ref_status === "present";
  if (value.provider_model_refs_bound !== refsBound) {
    return false;
  }
  if (
    binding.provider_ref_status === "present" &&
    providerBindingRefLooksUnbound(binding.provider_ref)
  ) {
    return false;
  }
  if (
    binding.provider_ref_status === "present" &&
    binding.provider_ref !== value.provider_id
  ) {
    return false;
  }
  if (
    binding.model_ref_status === "present" &&
    providerBindingRefLooksUnbound(binding.model_ref)
  ) {
    return false;
  }
  if (
    !providerBindingRefLooksUnbound(binding.credential_ref) &&
    binding.credential_ref !== value.credential_ref
  ) {
    return false;
  }
  const bindingFalseFlags = [
    "provider_use_authority_granted",
    "credential_validation_authority_granted",
    "provider_sdk_call_enabled",
    "model_invocation_enabled",
    "billing_authority_granted",
  ];
  if (bindingFalseFlags.some((field) => binding[field] !== false)) {
    return false;
  }
  const bindingTrueFlags = [
    "unknown_paid_cost_requires_approval",
    "estimated_cost_above_budget_blocks_use",
    "provider_model_refs_required",
    "cost_estimate_ref_required",
    "budget_decision_ref_required",
    "max_approved_usd_ref_required",
    "future_receipt_refs_required",
    "provider_usage_claim_requires_receipt_refs",
  ];
  if (bindingTrueFlags.some((field) => binding[field] !== true)) {
    return false;
  }
  return REQUIRED_PROVIDER_COST_BLOCKERS.every(
    (code) =>
      Array.isArray(binding.blocker_codes) &&
      binding.blocker_codes.includes(code),
  );
}

function isSafeProviderVaultAdapterReadiness(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const falseFlags = [
    "adapter_available",
    "supports_write",
    "supports_read_handle",
    "supports_revoke",
    "credential_material_stored_by_repo",
    "raw_key_visible",
    "adapter_runtime_enabled",
  ];
  return (
    falseFlags.every((field) => value[field] === false) &&
    value.readiness_status === "blocked_no_approved_backend" &&
    Array.isArray(value.blocker_codes) &&
    value.blocker_codes.includes("VAULT_ADAPTER_NOT_SCOPED")
  );
}

function isSafeProviderCredentialEnrollmentReadiness(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const falseFlags = [
    "enrollment_enabled",
    "raw_key_collection_enabled",
    "credential_material_stored_by_repo",
    "evidence_contains_credential_material",
  ];
  return (
    falseFlags.every((field) => value[field] === false) &&
    value.readiness_status === "blocked_disabled_by_default" &&
    Array.isArray(value.blocker_codes) &&
    value.blocker_codes.includes("CREDENTIAL_ENROLLMENT_NOT_SCOPED")
  );
}

function isSafeProviderCredentialValidationReadiness(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const falseFlags = [
    "validation_enabled",
    "external_validation_allowed",
    "provider_response_persistence_allowed",
    "provider_sdk_call_enabled",
    "model_invocation_enabled",
    "billing_authority_granted",
  ];
  const trueFlags = ["exact_approval_required", "redacted_receipts_only"];
  const uiStates = value.ui_states;
  const expectedUiStates = [
    "validation blocked",
    "credential valid",
    "credential invalid",
    "approval required",
    "no provider authority",
  ];
  return (
    falseFlags.every((field) => value[field] === false) &&
    trueFlags.every((field) => value[field] === true) &&
    value.readiness_status === "validation_blocked" &&
    Array.isArray(uiStates) &&
    uiStates.length === expectedUiStates.length &&
    expectedUiStates.every((label) => uiStates.includes(label)) &&
    uiStates.every((label) => expectedUiStates.includes(String(label))) &&
    Array.isArray(value.blocker_codes) &&
    value.blocker_codes.includes("EXACT_APPROVAL_REQUIRED") &&
    value.blocker_codes.includes("VALIDATION_ADAPTER_DISABLED_BY_DEFAULT")
  );
}

function isSafeGovernedProviderInvocationReadiness(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const falseFlags = [
    "invocation_enabled",
    "model_output_authoritative",
    "streaming_enabled",
    "tools_functions_enabled",
    "memory_write_enabled",
    "context_injection_enabled",
    "browser_network_automation_enabled",
    "connector_writes_enabled",
  ];
  const trueFlags = [
    "policy_engine_required",
    "local_approval_required",
    "credential_ref_required",
    "provider_manifest_allowlist_required",
    "redacted_request_summary_only",
    "redacted_response_summary_only",
    "receipt_refs_required",
    "audit_refs_required",
    "rollback_or_safe_disable_required",
    "rate_budget_boundary_required",
  ];
  return (
    falseFlags.every((field) => value[field] === false) &&
    trueFlags.every((field) => value[field] === true) &&
    value.readiness_status === "blocked_not_scoped" &&
    Array.isArray(value.blocker_codes) &&
    value.blocker_codes.includes("PROVIDER_INVOCATION_NOT_SCOPED")
  );
}

function isSafeTinyProviderInvocationReadiness(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const falseFlags = [
    "invocation_enabled",
    "provider_sdk_call_enabled",
    "network_call_enabled",
    "autonomous_model_call_enabled",
    "background_execution_enabled",
    "billing_authority_granted",
    "usage_captured",
    "cost_captured",
    "cost_incomplete",
    "review_required",
    "further_use_blocked",
    "prompt_persistence_allowed",
    "response_persistence_allowed",
    "provider_exchange_persistence_allowed",
  ];
  const trueFlags = [
    "exact_approval_required",
    "credential_ref_required",
    "provider_ref_required",
    "model_ref_required",
    "cost_estimate_ref_required",
    "budget_decision_ref_required",
    "max_approved_usd_required",
    "expected_receipt_ref_required",
    "idempotency_ref_required",
    "unknown_paid_cost_blocks",
    "redacted_receipts_only",
    "actual_usage_ref_required",
    "actual_cost_ref_required",
    "receipt_completeness_required",
    "incomplete_cost_requires_review",
    "incomplete_cost_blocks_further_use",
  ];
  const supportedStates = [
    "disabled",
    "blocked_missing_provider_ref",
    "blocked_missing_model_ref",
    "blocked_missing_credential_ref",
    "blocked_missing_cost_estimate_ref",
    "blocked_missing_budget_decision_ref",
    "blocked_missing_max_approved_usd",
    "blocked_missing_expected_receipt_ref",
    "blocked_missing_policy_validation",
    "blocked_provider_not_allowed",
    "blocked_model_not_allowed",
    "unknown_paid_cost_blocked",
    "cost_blocked",
    "approval_required",
    "approval_invalid",
    "approved_no_execution",
    "live_adapter_blocked",
    "receipt_recorded",
  ];
  const supportedUiStateLabels = [
    "Cost blocked",
    "Unknown paid cost",
    "No provider authority",
    "Disabled no execution",
    "Live adapter blocked",
    "Live receipt required",
  ];
  const supportedReceiptObservationLabels = [
    "Usage captured",
    "Cost captured",
    "Cost incomplete",
    "Review required",
    "Further use blocked",
  ];
  const uiStates = value.ui_states;
  const receiptObservationSupportedStates =
    value.receipt_observation_supported_states;
  const providerScopeRefs = value.provider_scope_refs;
  const modelScopeRefs = value.model_scope_refs;
  const policyScopeRefs = value.policy_scope_refs;
  const adapterScopeRefs = value.adapter_scope_refs;
  return (
    falseFlags.every((field) => value[field] === false) &&
    trueFlags.every((field) => value[field] === true) &&
    typeof value.lane_ref === "string" &&
    typeof value.route_ref === "string" &&
    typeof value.provider_ref === "string" &&
    typeof value.model_ref === "string" &&
    Array.isArray(providerScopeRefs) &&
    providerScopeRefs.length === 2 &&
    providerScopeRefs.includes(
      "provider-ref:openai-compatible:tiny-exact-approved",
    ) &&
    providerScopeRefs.includes(
      "provider-ref:anthropic-compatible:tiny-exact-approved",
    ) &&
    Array.isArray(modelScopeRefs) &&
    modelScopeRefs.length === 2 &&
    modelScopeRefs.includes("model-ref:openai-compatible:tiny-contract-model") &&
    modelScopeRefs.includes(
      "model-ref:anthropic-compatible:tiny-contract-model",
    ) &&
    Array.isArray(policyScopeRefs) &&
    policyScopeRefs.length === 2 &&
    policyScopeRefs.includes(
      "policy-ref:provider-runtime:tiny-exact-approved:v1",
    ) &&
    policyScopeRefs.includes(
      "policy-ref:provider-runtime:tiny-second-exact-approved:v1",
    ) &&
    Array.isArray(adapterScopeRefs) &&
    adapterScopeRefs.length === 2 &&
    adapterScopeRefs.includes(
      "provider-adapter-ref:tiny-exact-approved:openai-compatible-live",
    ) &&
    adapterScopeRefs.includes(
      "provider-adapter-ref:tiny-exact-approved:anthropic-compatible-live",
    ) &&
    typeof value.receipt_observation_ref === "string" &&
    value.receipt_state_source === "no_receipt_observed" &&
    supportedStates.includes(String(value.status)) &&
    Array.isArray(uiStates) &&
    uiStates.length === supportedUiStateLabels.length &&
    supportedUiStateLabels.every((label) => uiStates.includes(label)) &&
    uiStates.every((label) => supportedUiStateLabels.includes(String(label))) &&
    Array.isArray(receiptObservationSupportedStates) &&
    receiptObservationSupportedStates.length ===
      supportedReceiptObservationLabels.length &&
    supportedReceiptObservationLabels.every((label) =>
      receiptObservationSupportedStates.includes(label),
    ) &&
    receiptObservationSupportedStates.every((label) =>
      supportedReceiptObservationLabels.includes(String(label)),
    ) &&
    Array.isArray(value.blocker_codes) &&
    value.blocker_codes.includes("TINY_PROVIDER_LANE_DISABLED_BY_DEFAULT") &&
    value.blocker_codes.includes("UNKNOWN_PAID_COST_BLOCKS") &&
    value.blocker_codes.includes("ACTUAL_USAGE_REF_REQUIRED") &&
    value.blocker_codes.includes("ACTUAL_COST_REF_REQUIRED") &&
    value.blocker_codes.includes("RECEIPT_COMPLETENESS_REQUIRED") &&
    value.blocker_codes.includes("INCOMPLETE_COST_REQUIRES_REVIEW") &&
    value.blocker_codes.includes("INCOMPLETE_COST_BLOCKS_FURTHER_USE") &&
    value.blocker_codes.includes("LIVE_PROVIDER_NETWORK_ONLY_INSIDE_SCOPED_ADAPTER")
  );
}

function isSafeProviderRouterDryRunReadiness(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const falseFlags = [
    "invocation_authorized",
    "fallback_execution_authorized",
    "network_call_performed",
    "provider_sdk_call_performed",
    "credential_validation_performed",
    "model_invocation_performed",
    "billing_authority_granted",
    "autonomous_background_execution_enabled",
    "prompt_content_persisted",
    "response_content_persisted",
    "provider_payload_content_persisted",
  ];
  const trueFlags = ["safe_refs_only", "proposal_only", "local_state_only"];
  const requiredUiStates = [
    "Provider router dry-run",
    "Proposal only",
    "Exact-approval candidate refs",
    "Blocked provider refs",
    "Degraded provider refs",
    "Cost risky",
    "Validation required",
    "No provider authority",
    "No fallback execution",
  ];
  const requiredBlockers = [
    "PROVIDER_ROUTER_DRY_RUN_PROPOSAL_ONLY",
    "NO_PROVIDER_INVOCATION",
    "NO_FALLBACK_EXECUTION",
    "NO_NETWORK_CALLS",
    "NO_PROVIDER_SDK_CALL",
    "NO_CREDENTIAL_VALIDATION",
    "NO_MODEL_CALL",
    "NO_BILLING_AUTHORITY",
    "NO_AUTONOMOUS_BACKGROUND_CALLS",
    "COSTGOVERNOR_REQUIRED_BEFORE_INVOCATION",
    "UNKNOWN_PAID_COST_BLOCKS",
    "EXACT_APPROVAL_SCOPE_REQUIRED_FOR_ANY_FUTURE_USE",
  ];
  if (
    falseFlags.some((field) => value[field] !== false) ||
    trueFlags.some((field) => value[field] !== true) ||
    value.status !== "proposal_only" ||
    typeof value.contract_ref !== "string" ||
    typeof value.route_ref !== "string" ||
    typeof value.proposal_ref !== "string" ||
    typeof value.router_run_ref !== "string" ||
    typeof value.idempotency_ref !== "string" ||
    typeof value.safe_summary !== "string" ||
    typeof value.recommended_exact_approval_scope_ref !== "string"
  ) {
    return false;
  }
  const uiStates = value.ui_states;
  const blockerCodes = value.blocker_codes;
  if (
    !Array.isArray(uiStates) ||
    uiStates.length !== requiredUiStates.length ||
    !requiredUiStates.every((label) => uiStates.includes(label)) ||
    !Array.isArray(blockerCodes) ||
    !requiredBlockers.every((code) => blockerCodes.includes(code))
  ) {
    return false;
  }
  const refLists = [
    "eligible_provider_refs",
    "blocked_provider_refs",
    "degraded_provider_refs",
    "missing_credential_refs",
    "cost_risky_refs",
    "validation_required_refs",
    "no_authority_refs",
  ];
  if (
    refLists.some(
      (field) =>
        !Array.isArray(value[field]) ||
        !(value[field] as unknown[]).every((item) => typeof item === "string"),
    )
  ) {
    return false;
  }
  if (!Array.isArray(value.provider_proposals)) {
    return false;
  }
  if (!value.provider_proposals.every(isSafeProviderRouterDryRunProviderProposal)) {
    return false;
  }
  return isSafeProviderRouterDryRunRecommendedScope(
    value.recommended_exact_approval_scope,
  );
}

function isSafeProviderRouterDryRunProviderProposal(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    value.proposal_only === true &&
    value.execution_authorized === false &&
    value.fallback_execution_authorized === false &&
    value.network_call_performed === false &&
    value.provider_sdk_call_performed === false &&
    value.credential_validation_performed === false &&
    value.model_invocation_performed === false &&
    value.billing_authority_granted === false &&
    value.provider_output_authoritative === false &&
    typeof value.provider_ref === "string" &&
    typeof value.provider_label === "string" &&
    typeof value.provider_manifest_ref === "string" &&
    typeof value.model_ref === "string" &&
    typeof value.credential_ref === "string" &&
    typeof value.missing_credential_ref === "string" &&
    typeof value.cost_risk_ref === "string" &&
    typeof value.validation_required_ref === "string" &&
    typeof value.no_authority_ref === "string" &&
    typeof value.recommended_approval_scope_ref === "string" &&
    Array.isArray(value.reason_codes) &&
    value.reason_codes.includes("PROVIDER_ROUTER_DRY_RUN_PROPOSAL_ONLY") &&
    value.reason_codes.includes("NO_PROVIDER_AUTHORITY")
  );
}

function isSafeProviderRouterDryRunRecommendedScope(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const trueFlags = [
    "exact_scope_required",
    "provider_ref_required",
    "model_ref_required",
    "credential_ref_required",
    "cost_governor_decision_required",
    "max_approved_usd_required",
    "idempotency_ref_required",
    "receipt_ref_required",
  ];
  return (
    trueFlags.every((field) => value[field] === true) &&
    value.execution_authorized_by_scope === false &&
    typeof value.approval_scope_ref === "string" &&
    typeof value.policy_ref === "string" &&
    typeof value.cost_estimate_ref === "string" &&
    typeof value.budget_decision_ref === "string" &&
    typeof value.expected_receipt_ref === "string"
  );
}

function isSafeProviderSettingsDiagnostics(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const falseFlags = [
    "provider_sdk_call_enabled",
    "model_invocation_enabled",
    "provider_validation_performed",
    "router_execution_authorized",
    "billing_authority_granted",
    "settings_mutation_enabled",
    "raw_payload_persistence_enabled",
    "production_authority_enabled",
  ];
  if (falseFlags.some((field) => value[field] !== false)) {
    return false;
  }
  const supportedStates = value.supported_states;
  if (
    value.schema_version !== "provider_settings_diagnostics.v1" ||
    value.status !== "readable_diagnostics_only" ||
    !hasStringArrays(value, [
      "route_refs",
      "cli_inspection_refs",
      "evidence_refs",
    ]) ||
    !Array.isArray(supportedStates) ||
    !supportedStates.every((state) => typeof state === "string") ||
    !PROVIDER_SETTINGS_DIAGNOSTIC_STATES.every((state) =>
      supportedStates.includes(state),
    )
  ) {
    return false;
  }
  if (!Array.isArray(value.items) || value.items.length === 0) {
    return false;
  }
  if (!value.items.every(isSafeProviderSettingsDiagnosticItem)) {
    return false;
  }
  return providerSettingsDiagnosticCountsMatch(
    value.state_counts,
    value.items,
  );
}

function isSafeProviderSettingsDiagnosticItem(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const falseFlags = [
    "provider_sdk_call_enabled",
    "model_invocation_enabled",
    "provider_validation_performed",
    "router_execution_authorized",
    "connector_write_enabled",
    "billing_authority_granted",
    "raw_credential_visible",
    "raw_provider_payload_persisted",
    "settings_mutation_enabled",
    "production_authority_enabled",
  ];
  return (
    falseFlags.every((field) => value[field] === false) &&
    isProviderSettingsDiagnosticState(value.state) &&
    typeof value.diagnostic_ref === "string" &&
    typeof value.label === "string" &&
    typeof value.state_label === "string" &&
    typeof value.safe_summary === "string" &&
    typeof value.next_safe_action === "string" &&
    hasStringArrays(value, [
      "reason_codes",
      "blocked_authority_refs",
      "evidence_refs",
      "cli_inspection_refs",
      "redactions_applied",
    ]) &&
    (value.reason_codes as string[]).length > 0 &&
    (value.blocked_authority_refs as string[]).length > 0 &&
    (value.evidence_refs as string[]).length > 0 &&
    (value.cli_inspection_refs as string[]).length > 0
  );
}

function providerSettingsDiagnosticCountsMatch(
  counts: unknown,
  items: unknown[],
): boolean {
  if (!isPlainRecord(counts)) {
    return false;
  }
  const expected = Object.fromEntries(
    PROVIDER_SETTINGS_DIAGNOSTIC_STATES.map((state) => [state, 0]),
  ) as Record<string, number>;
  for (const item of items) {
    if (
      !isPlainRecord(item) ||
      !isProviderSettingsDiagnosticState(item.state)
    ) {
      return false;
    }
    expected[item.state] += 1;
  }
  return PROVIDER_SETTINGS_DIAGNOSTIC_STATES.every(
    (state) => counts[state] === expected[state],
  );
}

function providerPostureCountsMatch(
  counts: unknown,
  providers: unknown[],
): boolean {
  if (!isPlainRecord(counts)) {
    return false;
  }
  const expected = Object.fromEntries(
    PROVIDER_READINESS_POSTURES.map((posture) => [posture, 0]),
  ) as Record<string, number>;
  for (const provider of providers) {
    if (
      !isPlainRecord(provider) ||
      !isProviderReadinessPosture(provider.readiness_posture)
    ) {
      return false;
    }
    expected[provider.readiness_posture] += 1;
  }
  return PROVIDER_READINESS_POSTURES.every(
    (posture) => counts[posture] === expected[posture],
  );
}

function isSupportedProviderReadinessPostureList(value: unknown): boolean {
  return (
    Array.isArray(value) &&
    value.length === PROVIDER_READINESS_POSTURES.length &&
    PROVIDER_READINESS_POSTURES.every((posture) => value.includes(posture))
  );
}

function isProviderReadinessPosture(
  value: unknown,
): value is (typeof PROVIDER_READINESS_POSTURES)[number] {
  return (
    typeof value === "string" &&
    PROVIDER_READINESS_POSTURES.includes(
      value as ProviderCredentialReadinessPosture,
    )
  );
}

function isProviderSettingsDiagnosticState(
  value: unknown,
): value is (typeof PROVIDER_SETTINGS_DIAGNOSTIC_STATES)[number] {
  return (
    typeof value === "string" &&
    PROVIDER_SETTINGS_DIAGNOSTIC_STATES.includes(
      value as (typeof PROVIDER_SETTINGS_DIAGNOSTIC_STATES)[number],
    )
  );
}

function providerBindingRefLooksUnbound(value: unknown): boolean {
  if (typeof value !== "string") {
    return true;
  }
  if (value.trim().length === 0) {
    return true;
  }
  const lowered = value.toLowerCase();
  return [":missing", "not-bound", "not-selected", "not-configured"].some(
    (marker) => lowered.includes(marker),
  );
}

const PLANS_TO_ACTIONS_BRIDGE_TRUE_FLAGS = [
  "backend_owned",
  "local_read_model_only",
  "safe_refs_only",
] as const;

const PLANS_TO_ACTIONS_BRIDGE_ITEM_TRUE_FLAGS = [
  "backend_owned",
  "review_only",
  "proposal_only",
  "exact_scope_required",
  "expected_receipts_required",
  "rollback_required",
  "safe_disable_required",
  "safe_refs_only",
] as const;

const PLANS_TO_ACTIONS_BRIDGE_DENIED_FLAGS = [
  "approval_ref_authority",
  "approval_grant_capture_enabled",
  "approval_alone_executes",
  "execution_authorized",
  "execution_performed",
  "action_execution_enabled",
  "action_execution_performed",
  "tool_execution_enabled",
  "tool_execution_performed",
  "workflow_execution_enabled",
  "workflow_execution_performed",
  "model_provider_call_enabled",
  "model_provider_authority_allowed",
  "provider_model_call_enabled",
  "shell_subprocess_execution_enabled",
  "shell_subprocess_execution_performed",
  "browser_execution_enabled",
  "browser_execution_performed",
  "connector_runtime_enabled",
  "connector_write_enabled",
  "connector_write_performed",
  "memory_write_authorized",
  "memory_write_performed",
  "context_injection_authorized",
  "context_injection_performed",
  "automatic_planning_authority_enabled",
  "production_authority_enabled",
] as const;

const PLANS_TO_ACTIONS_BRIDGE_REQUIRED_ARRAYS = [
  "plan_refs",
  "action_inbox_item_refs",
  "task_decomposition_proposal_refs",
  "expected_receipt_refs",
  "rollback_refs",
  "safe_disable_refs",
  "blocked_state_refs",
] as const;

const PLANS_TO_ACTIONS_BRIDGE_ITEM_REQUIRED_ARRAYS = [
  "review_receipt_labels",
  "expected_receipt_refs",
  "receipt_refs",
  "evidence_refs",
  "step_refs",
  "risk_refs",
  "ambiguity_refs",
  "missing_evidence_refs",
  "blocked_authority_refs",
] as const;

function hasTrueFlags(
  record: Record<string, unknown>,
  flags: readonly string[],
): boolean {
  return flags.every((flag) => record[flag] === true);
}

function hasDeniedFlagsFalse(
  record: Record<string, unknown>,
  flags: readonly string[],
): boolean {
  return flags.every((flag) => record[flag] === false);
}

function hasStringArrays(
  record: Record<string, unknown>,
  fields: readonly string[],
): boolean {
  return fields.every((field) => {
    const value = record[field];
    return (
      Array.isArray(value) && value.every((item) => typeof item === "string")
    );
  });
}

function hasStringFields(
  record: Record<string, unknown>,
  fields: readonly string[],
): boolean {
  return fields.every((field) => typeof record[field] === "string");
}

function hasNumberFields(
  record: Record<string, unknown>,
  fields: readonly string[],
): boolean {
  return fields.every((field) => typeof record[field] === "number");
}

const CHAT_TO_LOOP_SAFE_REF_RE = /^[A-Za-z0-9][A-Za-z0-9:_#=-]{0,239}$/;
const CHAT_TO_LOOP_UNSAFE_TEXT_FRAGMENTS = [
  "raw prompt",
  "raw_prompt",
  "raw response",
  "raw_response",
  "provider payload",
  "provider_payload",
  "provider exchange",
  "full transcript",
  "unredacted transcript",
  "credential",
  "authorization",
  "api key",
  "secret",
  "password",
] as const;

function isSafeChatToLoopRef(value: unknown): value is string {
  return typeof value === "string" && CHAT_TO_LOOP_SAFE_REF_RE.test(value);
}

function isSafeChatToLoopText(value: unknown): value is string {
  if (typeof value !== "string") {
    return false;
  }
  const lowered = value.toLowerCase();
  return !CHAT_TO_LOOP_UNSAFE_TEXT_FRAGMENTS.some((fragment) =>
    lowered.includes(fragment),
  );
}

function hasSafeChatToLoopRefArrays(
  record: Record<string, unknown>,
  fields: readonly string[],
): boolean {
  return fields.every((field) => {
    const value = record[field];
    return Array.isArray(value) && value.every(isSafeChatToLoopRef);
  });
}

function hasStringArrayPrefix(
  record: Record<string, unknown>,
  field: string,
  prefix: string,
): boolean {
  const value = record[field];
  return (
    Array.isArray(value) &&
    value.every((item) => typeof item === "string" && item.startsWith(prefix))
  );
}

function hasRequiredReviewReceiptLabels(value: unknown): boolean {
  if (!Array.isArray(value)) {
    return false;
  }
  const labels = new Set(
    value.filter((item): item is string => typeof item === "string"),
  );
  return ["approve", "edit", "reject", "defer"].every((label) =>
    labels.has(label),
  );
}

const PLAN_ACTION_ENVELOPE_TOP_LEVEL_KEYS = [
  "plans_action_envelope_contract_ref",
  "plans_action_envelope_review_postures",
  "plans_action_envelope_required_ref_fields",
  "plans_action_envelope_required_blocked_refs",
  "plans_action_envelope_surface_bindings",
  "plans_action_envelope_authority_posture",
  "plans_action_envelope_status",
] as const;

const PLAN_ACTION_ENVELOPE_PLAN_KEYS = [
  "action_envelope_contract_ref",
  "action_envelope_ref",
  "action_envelope_status",
  "scope_ref",
  "approval_required",
  "approval_requirement_ref",
  "idempotency_key_ref",
  "expires_at",
  "rollback_ref",
  "safe_disable_ref",
  "action_execution_enabled",
  "approval_grant_capture_enabled",
  "action_envelope_cost_estimate_ref",
  "action_envelope_budget_decision_ref",
  "action_envelope_usage_receipt_ref",
  "action_envelope_estimated_cost_usd",
  "action_envelope_max_approved_cost_usd",
  "action_envelope_metered_unit_estimate",
  "action_envelope_cost_receipt_refs",
  "action_envelope_cost_blocked_state_refs",
  "action_envelope_cost_state_label",
  "action_envelope_provider_ref",
  "action_envelope_model_profile_ref",
  "action_envelope_provider_authority_state_label",
  "action_envelope_unknown_paid_cost_requires_explicit_approval",
  "action_envelope_frontier_usage_claimed",
  "review_actions",
  "expected_receipt_refs",
  "blocked_state_refs",
] as const;

function stripPlansActionEnvelopePosture(
  value: Record<string, unknown>,
): Record<string, unknown> {
  const stripped = { ...value };
  for (const key of PLAN_ACTION_ENVELOPE_TOP_LEVEL_KEYS) {
    delete stripped[key];
  }
  if (Array.isArray(stripped.plans)) {
    stripped.plans = stripped.plans.map((plan) => {
      if (!isPlainRecord(plan)) {
        return plan;
      }
      const planCopy = { ...plan };
      for (const key of PLAN_ACTION_ENVELOPE_PLAN_KEYS) {
        delete planCopy[key];
      }
      return planCopy;
    });
  }
  return stripped;
}

function normalizeFounderStartHere(
  value: ControlCenterStartHereSummary | undefined,
): {
  value: ControlCenterStartHereSummary;
  usedFallback: boolean;
} {
  if (!isSafeStartHereSummary(value)) {
    return {
      value: mockControlCenterData.founderStartHere,
      usedFallback: true,
    };
  }
  const merged = mergeMissingFields(mockControlCenterData.founderStartHere, value);
  return {
    value: merged.value,
    usedFallback: merged.usedFallback,
  };
}

function isSafeStartHereSummary(
  value: unknown,
): value is ControlCenterStartHereSummary {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    value.schema_version === "control-center-start-here-summary.v1" &&
    value.contract_ref === "contract-ref:control-center-start-here:v1" &&
    value.backend_owned === true &&
    value.local_read_model_only === true &&
    value.safe_refs_only === true &&
    value.raw_content_included === false &&
    value.provider_model_call_enabled === false &&
    value.runtime_model_call_enabled === false &&
    value.connector_write_enabled === false &&
    value.connector_send_enabled === false &&
    value.browser_execution_enabled === false &&
    value.shell_subprocess_execution_enabled === false &&
    value.background_autonomy_enabled === false &&
    value.production_authority_enabled === false &&
    Array.isArray(value.steps) &&
    typeof value.next_safe_action === "string"
  );
}

function normalizeProofIndex(
  value: ControlCenterProofIndex | undefined,
): {
  value: ControlCenterProofIndex;
  usedFallback: boolean;
} {
  if (!isSafeProofIndex(value)) {
    return {
      value: mockControlCenterData.proofIndex,
      usedFallback: true,
    };
  }
  const merged = mergeMissingFields(mockControlCenterData.proofIndex, value);
  return {
    value: merged.value,
    usedFallback: merged.usedFallback,
  };
}

function isSafeProofIndex(value: unknown): value is ControlCenterProofIndex {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    value.schema_version === "control-center-proof-index.v1" &&
    value.contract_ref === "contract-ref:control-center-proof-spine:v1" &&
    value.backend_owned === true &&
    value.local_read_model_only === true &&
    value.safe_refs_only === true &&
    value.raw_content_included === false &&
    value.provider_model_call_enabled === false &&
    value.runtime_model_call_enabled === false &&
    value.connector_write_enabled === false &&
    value.connector_send_enabled === false &&
    value.browser_execution_enabled === false &&
    value.shell_subprocess_execution_enabled === false &&
    value.background_autonomy_enabled === false &&
    value.production_authority_enabled === false &&
    Array.isArray(value.records) &&
    value.records.every(isSafeProofRecord)
  );
}

function isSafeProofRecord(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    value.schema_version === "control-center-proof-record.v1" &&
    value.contract_ref === "contract-ref:control-center-proof-spine:v1" &&
    typeof value.proof_ref === "string" &&
    value.safe_refs_only === true &&
    value.raw_content_included === false &&
    value.provider_model_call_enabled === false &&
    value.runtime_model_call_enabled === false &&
    value.connector_write_enabled === false &&
    value.connector_send_enabled === false &&
    value.browser_execution_enabled === false &&
    value.shell_subprocess_execution_enabled === false &&
    value.background_autonomy_enabled === false &&
    value.production_authority_enabled === false &&
    isSafeProofRunDetail(value.run_detail, value)
  );
}

function isSafeProofRunDetail(
  value: unknown,
  record: Record<string, unknown>,
): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const deniedFlags = [
    "provider_model_call_enabled",
    "runtime_model_call_enabled",
    "connector_write_enabled",
    "connector_send_enabled",
    "browser_execution_enabled",
    "shell_subprocess_execution_enabled",
    "background_autonomy_enabled",
    "production_authority_enabled",
  ] as const;
  const stringFields = [
    "run_detail_ref",
    "proof_ref",
    "proof_kind",
    "run_ref",
    "status",
    "title",
    "safe_summary",
    "authority_posture",
    "full_strength_goal",
    "repo_safe_scope",
    "blocked_authority_summary",
    "cli_ref",
    "redaction_state",
    "next_safe_action",
  ] as const;
  const refArrays = [
    "exact_promotion_path_refs",
    "related_run_refs",
    "operator_run_event_refs",
    "receipt_refs",
    "evidence_refs",
    "audit_refs",
    "approval_refs",
    "rollback_refs",
    "safe_disable_refs",
    "memory_candidate_refs",
    "blocked_authority_refs",
  ] as const;
  return (
    value.schema_version === "control-center-proof-run-detail.v1" &&
    value.contract_ref === "contract-ref:control-center-proof-spine:v1" &&
    value.source === "python_core_control_center_proof_run_detail" &&
    value.safe_refs_only === true &&
    value.raw_content_included === false &&
    value.control_center_presentation_only === true &&
    value.proof_ref === record.proof_ref &&
    value.proof_kind === record.proof_kind &&
    hasDeniedFlagsFalse(value, deniedFlags) &&
    hasStringFields(value, stringFields) &&
    hasStringArrays(value, ["route_refs", "backend_route_refs"]) &&
    hasSafeProofRunDetailRefArrays(value, refArrays) &&
    (value.related_run_refs as string[]).includes(String(value.run_ref)) &&
    stringFields.every((field) => isSafeEvidenceNarrativeText(value[field]))
  );
}

function hasSafeProofRunDetailRefArrays(
  record: Record<string, unknown>,
  fields: readonly string[],
): boolean {
  return fields.every((field) => {
    const value = record[field];
    return Array.isArray(value) && value.every(isSafeProofRunDetailRef);
  });
}

function isSafeProofRunDetailRef(value: unknown): value is string {
  if (!isSafeEvidenceNarrativeText(value)) {
    return false;
  }
  if (value.includes("@") || value.includes("\\")) {
    return false;
  }
  if (value.includes("/") && !value.startsWith("evidence-timeline:")) {
    return false;
  }
  return /^[A-Za-z0-9:_./-]+$/.test(value);
}

function normalizeTrustAuthorityMatrix(
  value: TrustAuthorityMatrix | undefined,
): {
  value: TrustAuthorityMatrix;
  usedFallback: boolean;
} {
  if (!isSafeTrustAuthorityMatrix(value)) {
    return {
      value: mockControlCenterData.trustAuthorityMatrix,
      usedFallback: true,
    };
  }
  return {
    value,
    usedFallback: false,
  };
}

const TRUST_AUTHORITY_DENIED_FLAGS = [
  "broad_approval_enabled",
  "standing_authority_enabled",
  "runtime_context_injection_enabled",
  "connector_write_enabled",
  "provider_model_call_enabled",
  "shell_subprocess_execution_enabled",
  "browser_execution_enabled",
  "background_autonomy_enabled",
  "production_authority_enabled",
] as const;

const TRUST_AUTHORITY_MATRIX_ARRAYS = [
  "lanes",
  "tier_summaries",
  "available_now_lane_refs",
  "approval_required_lane_refs",
  "planned_lane_refs",
  "blocked_lane_refs",
  "route_refs",
  "proof_refs",
  "verifier_refs",
  "docs_refs",
  "cli_inspection_refs",
  "safe_disable_refs",
  "rollback_refs",
  "promotion_path_refs",
  "blocked_authority_refs",
] as const;

const TRUST_AUTHORITY_LANE_ARRAYS = [
  "route_refs",
  "proof_refs",
  "verifier_refs",
  "docs_refs",
  "cli_inspection_refs",
  "safe_disable_refs",
  "rollback_refs",
  "promotion_path_refs",
  "blocked_authority_refs",
] as const;

const TRUST_AUTHORITY_STATES = [
  "available_now",
  "approval_required",
  "planned",
  "blocked",
] as const;

const TRUST_AUTHORITY_LANE_KINDS = [
  "read_preview",
  "draft_proposal",
  "reversible_local_mutation",
  "external_mutation",
  "background_standing_authority",
] as const;

const TRUST_AUTHORITY_TIER_LABELS: Record<number, { id: string; label: string }> = {
  0: { id: "tier_0_ui_ephemeral_state", label: "UI/ephemeral state" },
  1: { id: "tier_1_local_read_preview", label: "Local read/preview" },
  2: { id: "tier_2_local_draft_proposal", label: "Local draft/proposal" },
  3: { id: "tier_3_reversible_local_mutation", label: "Reversible local mutation" },
  4: { id: "tier_4_external_mutation", label: "External mutation" },
  5: {
    id: "tier_5_background_standing_authority",
    label: "Background/standing authority",
  },
};

function isSafeTrustAuthorityMatrix(value: unknown): value is TrustAuthorityMatrix {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    value.schema_version === "control-center-trust-authority-matrix.v1" &&
    value.contract_ref === "contract-ref:usable-authority-trust-authority-map:v1" &&
    value.route_ref === "GET /control-center/trust-authority/matrix" &&
    value.cli_ref ===
      "python scripts/dev/uaa_founder_loop.py inspect-trust-authority" &&
    value.backend_owned === true &&
    value.local_read_model_only === true &&
    value.safe_refs_only === true &&
    value.raw_content_included === false &&
    value.control_center_grants_authority === false &&
    hasDeniedFlagsFalse(value, TRUST_AUTHORITY_DENIED_FLAGS) &&
    TRUST_AUTHORITY_MATRIX_ARRAYS.every((field) => Array.isArray(value[field])) &&
    typeof value.doctrine === "string" &&
    typeof value.operator_summary === "string" &&
    typeof value.next_safe_action === "string" &&
    !containsUnsafeTrustText(value.doctrine) &&
    !containsUnsafeTrustText(value.operator_summary) &&
    !containsUnsafeTrustText(value.next_safe_action) &&
    (value.lanes as unknown[]).length > 0 &&
    (value.lanes as unknown[]).every(isSafeTrustAuthorityLane) &&
    (value.tier_summaries as unknown[]).length > 0 &&
    (value.tier_summaries as unknown[]).every(isSafeTrustAuthorityTierSummary) &&
    hasTrustAuthorityMatrixRefParity(value)
  );
}

function isSafeTrustAuthorityLane(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    typeof value.lane_ref === "string" &&
    value.lane_ref.startsWith("trust-lane:") &&
    typeof value.label === "string" &&
    typeof value.tier === "number" &&
    typeof value.tier_id === "string" &&
    typeof value.tier_label === "string" &&
    hasExactStringValue(value.lane_kind, TRUST_AUTHORITY_LANE_KINDS) &&
    hasExactStringValue(value.authority_state, TRUST_AUTHORITY_STATES) &&
    hasExpectedTrustTier(value) &&
    (value.tier < 4 ||
      value.authority_state === "blocked" ||
      value.authority_state === "approval_required") &&
    typeof value.authority_state_label === "string" &&
    typeof value.operator_posture === "string" &&
    typeof value.current_posture === "string" &&
    typeof value.approval_posture === "string" &&
    typeof value.operator_can_do_now === "string" &&
    typeof value.next_safe_action === "string" &&
    TRUST_AUTHORITY_LANE_ARRAYS.every((field) => Array.isArray(value[field])) &&
    value.safe_refs_only === true &&
    value.control_center_grants_authority === false &&
    value.rollback_execution_enabled === false &&
    isExpectedTrustOperatorPosture(value) &&
    stringArray(value.cli_inspection_refs).length > 0 &&
    (value.tier < 3 ||
      (stringArray(value.safe_disable_refs).length > 0 &&
        stringArray(value.rollback_refs).length > 0)) &&
    (!["planned", "blocked"].includes(value.authority_state) ||
      stringArray(value.promotion_path_refs).length > 0) &&
    !containsUnsafeTrustText(value.label) &&
    !containsUnsafeTrustText(value.authority_state_label) &&
    !containsUnsafeTrustText(value.current_posture) &&
    !containsUnsafeTrustText(value.approval_posture) &&
    !containsUnsafeTrustText(value.operator_can_do_now) &&
    !containsUnsafeTrustText(value.next_safe_action)
  );
}

function isExpectedTrustOperatorPosture(
  value: Record<string, unknown>,
): boolean {
  if (value.authority_state === "available_now") {
    return (
      value.operator_posture ===
      (value.tier === 2 ? "review_only" : "enabled_read_only")
    );
  }
  return value.operator_posture === value.authority_state;
}

function hasExpectedTrustTier(value: Record<string, unknown>): boolean {
  if (typeof value.tier !== "number") {
    return false;
  }
  const expected = TRUST_AUTHORITY_TIER_LABELS[value.tier];
  const label =
    typeof value.tier_label === "string" ? value.tier_label : value.label;
  return (
    expected !== undefined &&
    value.tier_id === expected.id &&
    label === expected.label
  );
}

function hasExactStringValue(
  value: unknown,
  allowed: readonly string[],
): value is string {
  return typeof value === "string" && allowed.includes(value);
}

function hasTrustAuthorityMatrixRefParity(
  value: Record<string, unknown>,
): boolean {
  const lanes = value.lanes as Record<string, unknown>[];
  const parityFields = [
    "cli_inspection_refs",
    "safe_disable_refs",
    "rollback_refs",
    "promotion_path_refs",
    "blocked_authority_refs",
  ] as const;
  return parityFields.every((field) =>
    hasExactStringList(
      value[field],
      uniqueStrings(lanes.flatMap((lane) => stringArray(lane[field]))),
    ),
  );
}

function isSafeTrustAuthorityTierSummary(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    typeof value.tier === "number" &&
    typeof value.tier_id === "string" &&
    typeof value.label === "string" &&
    hasExpectedTrustTier(value) &&
    typeof value.available_now_count === "number" &&
    typeof value.approval_required_count === "number" &&
    typeof value.planned_count === "number" &&
    typeof value.blocked_count === "number" &&
    typeof value.operator_summary === "string" &&
    !containsUnsafeTrustText(value.operator_summary)
  );
}

function containsUnsafeTrustText(value: string): boolean {
  const lowered = value.toLowerCase();
  return EVIDENCE_NARRATIVE_UNSAFE_TEXT_FRAGMENTS.some((fragment) =>
    lowered.includes(fragment),
  );
}

function normalizeFounderToday(value: FounderLoopTodaySummary | undefined): {
  value: FounderLoopTodaySummary;
  usedFallback: boolean;
} {
  if (value === undefined) {
    const fallbackWithoutDigest = {
      ...(mockControlCenterData.founderToday as unknown as Record<
        string,
        unknown
      >),
    };
    delete fallbackWithoutDigest.today_loop_read_model;
    delete fallbackWithoutDigest.today_loop_tightening_contract_ref;
    delete fallbackWithoutDigest.follow_up_tracker;
    delete fallbackWithoutDigest.follow_up_tracker_contract_ref;
    delete fallbackWithoutDigest.weekly_ceo_review_v1_read_model;
    delete fallbackWithoutDigest.weekly_ceo_review_v1_contract_ref;
    delete fallbackWithoutDigest.founder_loop_runs_integration_read_model;
    delete fallbackWithoutDigest.founder_loop_runs_integration_contract_ref;
    delete fallbackWithoutDigest.loop_trace_refs;
    delete fallbackWithoutDigest.unified_work_thread_read_model;
    delete fallbackWithoutDigest.unified_work_thread_contract_ref;
    delete fallbackWithoutDigest.evidence_memory_loop_binding_read_model;
    delete fallbackWithoutDigest.evidence_memory_loop_binding_contract_ref;
    delete fallbackWithoutDigest.chat_to_loop_handoff_read_model;
    delete fallbackWithoutDigest.chat_to_loop_handoff_contract_ref;
    delete fallbackWithoutDigest.plans_to_actions_bridge_read_model;
    delete fallbackWithoutDigest.plans_to_actions_bridge_contract_ref;
    delete fallbackWithoutDigest.fusion_routing_delegation_read_model;
    delete fallbackWithoutDigest.fusion_routing_delegation_contract_ref;
    return {
      value: stripPlansActionEnvelopePosture(
        fallbackWithoutDigest,
      ) as unknown as FounderLoopTodaySummary,
      usedFallback: true,
    };
  }
  const merged = mergeMissingFields(mockControlCenterData.founderToday, value);
  const valueRecord = value as unknown as Record<string, unknown>;
  let normalized: Record<string, unknown> = {
    ...(merged.value as unknown as Record<string, unknown>),
  };
  if (
    Object.prototype.hasOwnProperty.call(valueRecord, "today_loop_read_model")
  ) {
    normalized.today_loop_read_model = valueRecord.today_loop_read_model;
    normalized.today_loop_tightening_contract_ref =
      valueRecord.today_loop_tightening_contract_ref;
  } else {
    delete normalized.today_loop_read_model;
    delete normalized.today_loop_tightening_contract_ref;
  }
  if (Object.prototype.hasOwnProperty.call(valueRecord, "follow_up_tracker")) {
    normalized.follow_up_tracker = valueRecord.follow_up_tracker;
    normalized.follow_up_tracker_contract_ref =
      valueRecord.follow_up_tracker_contract_ref;
  } else {
    delete normalized.follow_up_tracker;
    delete normalized.follow_up_tracker_contract_ref;
  }
  const weeklyCeoReview = valueRecord.weekly_ceo_review_v1_read_model;
  if (isSafeWeeklyCeoReviewV1ReadModel(weeklyCeoReview)) {
    normalized.weekly_ceo_review_v1_read_model = weeklyCeoReview;
    normalized.weekly_ceo_review_v1_contract_ref = (
      weeklyCeoReview as Record<string, unknown>
    ).contract_ref;
  } else {
    delete normalized.weekly_ceo_review_v1_read_model;
    delete normalized.weekly_ceo_review_v1_contract_ref;
  }
  const productProof = valueRecord.founder_loop_v1_product_proof_read_model;
  if (isSafeFounderLoopProductProofReadModel(productProof)) {
    normalized.founder_loop_v1_product_proof_read_model = productProof;
    normalized.founder_loop_v1_product_proof_contract_ref = (
      productProof as Record<string, unknown>
    ).contract_ref;
  } else {
    delete normalized.founder_loop_v1_product_proof_read_model;
    delete normalized.founder_loop_v1_product_proof_contract_ref;
  }
  normalizeFounderLoopRunsIntegration(normalized, valueRecord);
  const unifiedWorkThread = valueRecord.unified_work_thread_read_model;
  if (isSafeUnifiedWorkThreadReadModel(unifiedWorkThread)) {
    normalized.unified_work_thread_read_model = unifiedWorkThread;
    normalized.unified_work_thread_contract_ref = (
      unifiedWorkThread as Record<string, unknown>
    ).contract_ref;
  } else {
    delete normalized.unified_work_thread_read_model;
    delete normalized.unified_work_thread_contract_ref;
  }
  normalizeEvidenceMemoryLoopBinding(normalized, valueRecord);
  if (
    isSafePlansToActionsBridgeReadModel(
      valueRecord.plans_to_actions_bridge_read_model,
    )
  ) {
    normalized.plans_to_actions_bridge_read_model =
      valueRecord.plans_to_actions_bridge_read_model;
    normalized.plans_to_actions_bridge_contract_ref =
      valueRecord.plans_to_actions_bridge_contract_ref;
  } else {
    delete normalized.plans_to_actions_bridge_read_model;
    delete normalized.plans_to_actions_bridge_contract_ref;
    normalized = stripPlansActionEnvelopePosture(normalized);
  }
  const chatToLoopHandoff = valueRecord.chat_to_loop_handoff_read_model;
  if (isSafeChatToLoopHandoffReadModel(chatToLoopHandoff)) {
    normalized.chat_to_loop_handoff_read_model = chatToLoopHandoff;
    normalized.chat_to_loop_handoff_contract_ref = (
      chatToLoopHandoff as Record<string, unknown>
    ).contract_ref;
  } else {
    delete normalized.chat_to_loop_handoff_read_model;
    delete normalized.chat_to_loop_handoff_contract_ref;
  }
  const fusionReadModel = valueRecord.fusion_routing_delegation_read_model;
  if (isSafeFusionRoutingReadModel(fusionReadModel)) {
    normalized.fusion_routing_delegation_read_model = fusionReadModel;
    normalized.fusion_routing_delegation_contract_ref = (
      fusionReadModel as Record<string, unknown>
    ).contract_ref;
  } else {
    delete normalized.fusion_routing_delegation_read_model;
    delete normalized.fusion_routing_delegation_contract_ref;
  }
  const safeShape = normalizeTodayRouteShape(normalized, valueRecord);
  return {
    value: safeShape.value as unknown as FounderLoopTodaySummary,
    usedFallback: merged.usedFallback || safeShape.usedFallback,
  };
}

const TODAY_ROUTE_REQUIRED_ARRAY_FIELDS = [
  "actions",
  "plans",
  "memory_review_queue",
  "briefing_items",
  "evidence_timeline",
] as const;

function normalizeTodayRouteShape(
  record: Record<string, unknown>,
  source: Record<string, unknown>,
): {
  value: Record<string, unknown>;
  usedFallback: boolean;
} {
  const fallbackRecord = mockControlCenterData.founderToday as unknown as Record<
    string,
    unknown
  >;
  const normalized: Record<string, unknown> = { ...record };
  let usedFallback = false;

  for (const key of TODAY_ROUTE_REQUIRED_ARRAY_FIELDS) {
    const fallbackValue = fallbackRecord[key];
    if (
      Object.prototype.hasOwnProperty.call(source, key) &&
      Array.isArray(fallbackValue) &&
      !Array.isArray(normalized[key])
    ) {
      normalized[key] = fallbackValue;
      usedFallback = true;
    }
  }

  if (
    Object.prototype.hasOwnProperty.call(source, "sections") &&
    !isPlainRecord(normalized.sections)
  ) {
    normalized.sections = fallbackRecord.sections;
    usedFallback = true;
  } else if (
    Object.prototype.hasOwnProperty.call(source, "sections") &&
    isPlainRecord(normalized.sections) &&
    isPlainRecord(fallbackRecord.sections)
  ) {
    const sections: Record<string, unknown> = { ...normalized.sections };
    for (const [key, fallbackValue] of Object.entries(fallbackRecord.sections)) {
      if (
        typeof fallbackValue === "number" &&
        typeof sections[key] !== "number"
      ) {
        sections[key] = fallbackValue;
        usedFallback = true;
      }
    }
    normalized.sections = sections;
  }

  return { value: normalized, usedFallback };
}

function normalizeFounderEvidenceTimeline(
  value: FounderLoopEvidenceTimelineIndex | undefined,
): { value: FounderLoopEvidenceTimelineIndex; usedFallback: boolean } {
  if (value === undefined) {
    const fallbackWithoutNarrative = {
      ...(mockControlCenterData.founderEvidenceTimeline as unknown as Record<
        string,
        unknown
      >),
    };
    delete fallbackWithoutNarrative.narrative_read_model;
    delete fallbackWithoutNarrative.narrative_contract_ref;
    return {
      value:
        fallbackWithoutNarrative as unknown as FounderLoopEvidenceTimelineIndex,
      usedFallback: true,
    };
  }
  const merged = mergeMissingFields(
    mockControlCenterData.founderEvidenceTimeline,
    value,
  );
  const valueRecord = value as unknown as Record<string, unknown>;
  const normalized: Record<string, unknown> = {
    ...(merged.value as unknown as Record<string, unknown>),
  };
  const narrative = valueRecord.narrative_read_model;
  if (isSafeEvidenceTimelineNarrativeReadModel(narrative)) {
    normalized.narrative_read_model = narrative;
    normalized.narrative_contract_ref = (
      narrative as Record<string, unknown>
    ).contract_ref;
  } else {
    delete normalized.narrative_read_model;
    delete normalized.narrative_contract_ref;
  }
  normalizeFounderLoopRunsIntegration(normalized, valueRecord);
  normalizeEvidenceMemoryLoopBinding(normalized, valueRecord);
  return {
    value: normalized as unknown as FounderLoopEvidenceTimelineIndex,
    usedFallback: merged.usedFallback,
  };
}

function normalizeFounderMemoryReview(
  value: FounderLoopMemoryReview | undefined,
): { value: FounderLoopMemoryReview; usedFallback: boolean } {
  const merged = mergeMissingFields(
    mockControlCenterData.founderMemoryReview,
    value,
  );
  const valueRecord = (value ?? {}) as unknown as Record<string, unknown>;
  const normalized: Record<string, unknown> = {
    ...(merged.value as unknown as Record<string, unknown>),
  };
  normalizeEvidenceMemoryLoopBinding(normalized, valueRecord);
  return {
    value: normalized as unknown as FounderLoopMemoryReview,
    usedFallback: merged.usedFallback,
  };
}

function normalizeEvidenceMemoryLoopBinding(
  normalized: Record<string, unknown>,
  valueRecord: Record<string, unknown>,
): void {
  const readModel = valueRecord.evidence_memory_loop_binding_read_model;
  if (isSafeEvidenceMemoryLoopBindingReadModel(readModel)) {
    normalized.evidence_memory_loop_binding_read_model = readModel;
    normalized.evidence_memory_loop_binding_contract_ref = (
      readModel as Record<string, unknown>
    ).contract_ref;
  } else {
    delete normalized.evidence_memory_loop_binding_read_model;
    delete normalized.evidence_memory_loop_binding_contract_ref;
  }
}

function normalizeFounderLoopRunsIntegration(
  normalized: Record<string, unknown>,
  valueRecord: Record<string, unknown>,
): void {
  const readModel = valueRecord.founder_loop_runs_integration_read_model;
  const loopTraceRefs = valueRecord.loop_trace_refs;
  if (isSafeFounderLoopRunsIntegrationReadModel(readModel)) {
    normalized.founder_loop_runs_integration_read_model = readModel;
    normalized.founder_loop_runs_integration_contract_ref = (
      readModel as FounderLoopRunsIntegrationReadModel
    ).contract_ref;
    if (isSafeFounderLoopTraceRefs(loopTraceRefs)) {
      normalized.loop_trace_refs = loopTraceRefs;
    } else {
      delete normalized.loop_trace_refs;
    }
  } else {
    delete normalized.founder_loop_runs_integration_read_model;
    delete normalized.founder_loop_runs_integration_contract_ref;
    delete normalized.loop_trace_refs;
  }
}

function stripFollowUpTrackerIfMissing<T>(
  fallback: T,
  value: T | undefined,
): { value: T; usedFallback: boolean } {
  const merged = mergeMissingFields(fallback, value);
  if (
    value === undefined ||
    !Object.prototype.hasOwnProperty.call(
      value as Record<string, unknown>,
      "follow_up_tracker",
    )
  ) {
    const withoutMockTracker = { ...(merged.value as Record<string, unknown>) };
    delete withoutMockTracker.follow_up_tracker;
    delete withoutMockTracker.follow_up_tracker_contract_ref;
    return {
      value: withoutMockTracker as T,
      usedFallback: merged.usedFallback,
    };
  }
  return {
    value: {
      ...(merged.value as Record<string, unknown>),
      follow_up_tracker: (value as Record<string, unknown>).follow_up_tracker,
      follow_up_tracker_contract_ref: (value as Record<string, unknown>)
        .follow_up_tracker_contract_ref,
    } as T,
    usedFallback: merged.usedFallback,
  };
}

const MORNING_BRIEFING_V1_DENIED_FLAGS = [
  "connector_read_enabled",
  "connector_runtime_enabled",
  "connector_write_enabled",
  "email_calendar_fetch_enabled",
  "account_auth_enabled",
  "live_web_enabled",
  "provider_model_call_enabled",
  "runtime_model_call_enabled",
  "automatic_recommendations_enabled",
  "hidden_memory_write_authorized",
  "memory_write_authorized",
  "context_injection_authorized",
  "action_execution_enabled",
  "repo_write_enabled",
  "workbench_apply_enabled",
  "shell_subprocess_execution_enabled",
  "browser_execution_enabled",
  "notification_delivery_enabled",
  "source_refresh_enabled",
  "production_authority_enabled",
] as const;

const WEEKLY_CEO_REVIEW_V1_DENIED_FLAGS = [
  "raw_logs_included",
  "prompt_content_included",
  "response_content_included",
  "provider_exchange_content_included",
  "connector_read_enabled",
  "connector_runtime_enabled",
  "connector_write_enabled",
  "email_calendar_fetch_enabled",
  "live_web_enabled",
  "model_summary_enabled",
  "provider_model_call_enabled",
  "runtime_model_call_enabled",
  "automatic_memory_write_authorized",
  "context_injection_authorized",
  "action_execution_enabled",
  "shell_subprocess_execution_enabled",
  "browser_execution_enabled",
  "public_beta_claim_enabled",
  "production_claim_enabled",
  "production_authority_enabled",
] as const;

const WEEKLY_CEO_REVIEW_V1_REQUIRED_ARRAYS = [
  "completed_refs",
  "deferred_refs",
  "rejected_refs",
  "blocked_refs",
  "stale_refs",
  "unresolved_refs",
  "carry_forward_refs",
  "next_week_priority_refs",
  "action_decision_refs",
  "memory_decision_refs",
  "follow_up_refs",
  "evidence_event_refs",
  "evidence_refs",
  "receipt_refs",
  "missing_source_refs",
  "blocked_authority_refs",
] as const;

const WEEKLY_CEO_REVIEW_V1_COUNT_ARRAY_PAIRS = [
  ["completed_count", "completed_refs"],
  ["deferred_count", "deferred_refs"],
  ["rejected_count", "rejected_refs"],
  ["blocked_count", "blocked_refs"],
  ["stale_count", "stale_refs"],
  ["unresolved_count", "unresolved_refs"],
  ["action_decision_count", "action_decision_refs"],
  ["memory_decision_count", "memory_decision_refs"],
  ["follow_up_count", "follow_up_refs"],
  ["evidence_event_count", "evidence_event_refs"],
] as const;

const FOUNDER_LOOP_PRODUCT_PROOF_DENIED_FLAGS = [
  "provider_model_call_enabled",
  "runtime_model_call_enabled",
  "a2a_runtime_dispatch_enabled",
  "mcp_runtime_dispatch_enabled",
  "browser_execution_enabled",
  "live_web_enabled",
  "connector_write_enabled",
  "email_calendar_send_enabled",
  "crm_write_enabled",
  "account_sync_enabled",
  "shell_subprocess_execution_enabled",
  "background_autonomy_enabled",
  "memory_write_authorized",
  "context_injection_authorized",
  "public_beta_claim_enabled",
  "public_release_claim_enabled",
  "production_authority_enabled",
] as const;

const FOUNDER_LOOP_PRODUCT_PROOF_REQUIRED_ARRAYS = [
  "exact_promotion_path_refs",
  "productized_surface_order",
  "productized_route_refs",
  "productized_backend_route_refs",
  "loop_order",
  "supported_decision_actions",
  "morning_briefing_refs",
  "today_refs",
  "action_inbox_refs",
  "action_decision_receipt_refs",
  "evidence_timeline_refs",
  "evidence_event_refs",
  "memory_review_candidate_refs",
  "memory_review_receipt_refs",
  "weekly_review_refs",
  "receipt_refs",
  "evidence_refs",
  "blocked_authority_refs",
] as const;

const FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER = [
  "morning_briefing",
  "today",
  "action_inbox",
  "decision_receipt",
  "evidence_timeline",
  "memory_review",
  "weekly_review",
] as const;

const FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER = [
  "start_here",
  "today",
  "action_inbox",
  "proof",
  "evidence",
  "memory",
  "trust",
  "settings",
] as const;

const FOUNDER_LOOP_RUNS_INTEGRATION_DENIED_FLAGS = [
  "provider_model_call_enabled",
  "runtime_model_call_enabled",
  "connector_write_enabled",
  "connector_send_enabled",
  "browser_execution_enabled",
  "live_web_enabled",
  "shell_subprocess_execution_enabled",
  "scheduler_enabled",
  "background_autonomy_enabled",
  "action_execution_enabled",
  "approval_authority_enabled",
  "memory_write_authorized",
  "context_injection_authorized",
  "ui_mutation_authority_enabled",
  "production_authority_enabled",
] as const;

const FOUNDER_LOOP_RUNS_INTEGRATION_REQUIRED_ARRAYS = [
  "surface_order",
  "run_refs",
  "proof_refs",
  "proof_detail_refs",
  "action_source_refs",
  "approval_refs",
  "receipt_refs",
  "evidence_refs",
  "evidence_event_refs",
  "memory_candidate_refs",
  "operator_run_event_refs",
  "blocked_authority_refs",
] as const;

const UNIFIED_WORK_THREAD_DENIED_FLAGS = [
  "provider_model_call_enabled",
  "runtime_model_call_enabled",
  "a2a_runtime_dispatch_enabled",
  "mcp_runtime_dispatch_enabled",
  "browser_execution_enabled",
  "live_web_enabled",
  "connector_read_enabled",
  "connector_write_enabled",
  "email_calendar_send_enabled",
  "crm_write_enabled",
  "account_sync_enabled",
  "shell_subprocess_execution_enabled",
  "background_autonomy_enabled",
  "memory_write_authorized",
  "context_injection_authorized",
  "action_execution_enabled",
  "public_beta_claim_enabled",
  "public_release_claim_enabled",
  "production_authority_enabled",
] as const;

const UNIFIED_WORK_THREAD_REQUIRED_ARRAYS = [
  "step_order",
  "chat_turn_receipt_refs",
  "chat_handoff_receipt_refs",
  "plan_refs",
  "plan_proposal_refs",
  "action_refs",
  "action_decision_receipt_refs",
  "evidence_timeline_refs",
  "evidence_event_refs",
  "memory_review_candidate_refs",
  "memory_review_receipt_refs",
  "weekly_review_refs",
  "receipt_refs",
  "evidence_refs",
  "blocked_authority_refs",
] as const;

const UNIFIED_WORK_THREAD_REQUIRED_BLOCKED_REFS = [
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
] as const;

const UNIFIED_WORK_THREAD_STEP_ORDER = [
  "chat_handoff",
  "plan",
  "action",
  "decision_receipt",
  "evidence",
  "memory_review",
  "weekly_review",
] as const;

const CHAT_TO_LOOP_HANDOFF_DENIED_FLAGS = [
  "model_output_authority",
  "direct_memory_write_authorized",
  "automatic_memory_write_authorized",
  "context_injection_authorized",
  "tool_execution_enabled",
  "connector_write_enabled",
  "action_execution_enabled",
  "plan_execution_enabled",
  "provider_model_call_enabled",
  "runtime_model_call_enabled",
  "live_web_enabled",
  "shell_subprocess_execution_enabled",
  "browser_execution_enabled",
  "production_authority_enabled",
] as const;

const CHAT_TO_LOOP_HANDOFF_REQUIRED_ARRAYS = [
  "outcome_kinds",
  "outcome_refs",
  "turn_receipt_refs",
  "handoff_receipt_refs",
  "action_created_refs",
  "plan_created_refs",
  "memory_proposal_refs",
  "defer_refs",
  "ask_human_refs",
  "evidence_refs",
  "idempotency_refs",
  "blocked_state_refs",
] as const;

const CHAT_TO_LOOP_HANDOFF_REQUIRED_REF_ARRAYS = [
  "outcome_refs",
  "turn_receipt_refs",
  "handoff_receipt_refs",
  "action_created_refs",
  "plan_created_refs",
  "memory_proposal_refs",
  "defer_refs",
  "ask_human_refs",
  "evidence_refs",
  "idempotency_refs",
  "blocked_state_refs",
] as const;

const CHAT_TO_LOOP_HANDOFF_COUNT_ARRAY_PAIRS = [
  ["outcome_count", "outcomes"],
  ["turn_receipt_count", "turn_receipt_refs"],
  ["handoff_receipt_count", "handoff_receipt_refs"],
  ["remember_this_count", "memory_proposal_refs"],
  ["create_action_count", "action_created_refs"],
  ["add_to_plan_count", "plan_created_refs"],
  ["defer_count", "defer_refs"],
  ["ask_human_count", "ask_human_refs"],
  ["blocked_count", "blocked_state_refs"],
] as const;

const CHAT_TO_LOOP_HANDOFF_OUTCOME_KINDS = [
  "remember_this",
  "create_action",
  "add_to_plan",
  "defer",
  "ask_human",
  "blocked",
] as const;

const CHAT_TO_LOOP_HANDOFF_TARGET_SURFACES = [
  "Memory",
  "Actions",
  "Plans",
  "Chat",
  "Authority",
] as const;

const CHAT_TO_LOOP_HANDOFF_STATES = [
  "recorded_reviewable_proposal",
  "blocked_review_required",
  "blocked_authority",
] as const;

const EVIDENCE_NARRATIVE_TRUE_FLAGS = [
  "backend_owned",
  "local_read_model_only",
  "safe_refs_only",
  "redacted_summaries_only",
  "narrative_from_existing_refs_only",
] as const;

const EVIDENCE_NARRATIVE_DENIED_FLAGS = [
  "raw_content_included",
  "approval_ref_authority",
  "rollback_execution_enabled",
  "action_execution_enabled",
  "tool_execution_enabled",
  "workflow_execution_enabled",
  "connector_write_enabled",
  "connector_runtime_enabled",
  "provider_model_call_enabled",
  "runtime_model_calls_enabled",
  "provider_sdk_call_enabled",
  "live_web_enabled",
  "shell_subprocess_execution_enabled",
  "browser_execution_enabled",
  "public_beta_enabled",
  "distribution_enabled",
  "prompt_content_stored",
  "response_content_stored",
  "provider_exchange_content_stored",
  "memory_truth_authority",
  "context_injection_authorized",
  "production_authority_enabled",
] as const;

const EVIDENCE_NARRATIVE_REF_ARRAYS = [
  "source_refs",
  "status_refs",
  "receipt_refs",
  "approval_refs",
  "audit_refs",
  "idempotency_refs",
  "rollback_refs",
  "evidence_refs",
  "blocked_state_refs",
] as const;

const EVIDENCE_MEMORY_BINDING_TRUE_FLAGS = [
  "backend_owned",
  "local_read_model_only",
  "safe_refs_only",
] as const;

const EVIDENCE_MEMORY_BINDING_DENIED_FLAGS = [
  "raw_content_included",
  "memory_truth_authority",
  "context_injection_authorized",
  "automatic_memory_write_authorized",
  "memory_delete_enabled",
  "memory_export_enabled",
  "action_execution_enabled",
  "connector_write_enabled",
  "connector_send_enabled",
  "provider_model_call_enabled",
  "shell_subprocess_execution_enabled",
  "browser_execution_enabled",
  "background_autonomy_enabled",
  "production_authority_enabled",
] as const;

const EVIDENCE_MEMORY_BINDING_AGGREGATE_REF_ARRAYS = [
  "evidence_refs",
  "memory_candidate_refs",
  "action_refs",
  "run_refs",
  "proof_refs",
  "receipt_refs",
  "shared_run_refs",
  "shared_action_refs",
  "shared_proof_refs",
  "promotion_path_refs",
  "blocked_authority_refs",
] as const;

const EVIDENCE_MEMORY_EVIDENCE_BINDING_REF_ARRAYS = [
  "source_refs",
  "action_refs",
  "run_refs",
  "proof_refs",
  "shared_loop_refs",
  "shared_run_refs",
  "shared_action_refs",
  "shared_proof_refs",
  "approval_refs",
  "receipt_refs",
  "evidence_refs",
  "memory_candidate_refs",
  "blocked_authority_refs",
] as const;

const EVIDENCE_MEMORY_MEMORY_BINDING_REF_ARRAYS = [
  "source_refs",
  "why_shown_refs",
  "related_action_refs",
  "related_run_refs",
  "related_proof_refs",
  "shared_loop_refs",
  "shared_run_refs",
  "shared_action_refs",
  "shared_proof_refs",
  "related_evidence_refs",
  "decision_receipt_refs",
  "blocked_authority_refs",
] as const;

const EVIDENCE_NARRATIVE_AGGREGATE_REF_ARRAYS = [
  "narrative_refs",
  "event_refs",
  "timeline_item_refs",
  "group_refs",
  "receipt_refs",
  "approval_refs",
  "audit_refs",
  "idempotency_refs",
  "rollback_refs",
  "evidence_refs",
  "blocked_state_refs",
] as const;

const unsafeFieldMarker = (fieldRef: string): string =>
  `${fieldRef}${globalThis.String.fromCharCode(58)}`;

const EVIDENCE_NARRATIVE_UNSAFE_TEXT_FRAGMENTS = [
  "raw prompt",
  "raw-prompt",
  "raw_prompt",
  "raw response",
  "raw-response",
  "raw_response",
  "provider payload",
  "provider_payload",
  "raw provider",
  "raw-provider",
  "raw_provider",
  "raw path",
  "raw-path",
  "raw_path",
  "raw log",
  "raw-log",
  "raw_log",
  "prompt-content",
  "prompt_content",
  "response-content",
  "response_content",
  "provider-exchange-content",
  "provider_exchange_content",
  "raw private content",
  "raw_private_content",
  "/users/",
  "username ",
  unsafeFieldMarker("username"),
  "hostname ",
  unsafeFieldMarker("hostname"),
  "serial ",
  unsafeFieldMarker("serial"),
  "actor-ref:username",
  "host-ref:hostname",
  "device-ref:serial",
  "private_key",
  "private-key",
  "authorization",
  "bearer token",
  "api key",
  "password",
  "secret",
] as const;

const EVIDENCE_NARRATIVE_UNSAFE_REF_FRAGMENTS = [
  "raw-prompt",
  "raw_prompt",
  "raw-response",
  "raw_response",
  "raw-provider",
  "raw_provider",
  "raw-path",
  "raw_path",
  "raw-log",
  "raw_log",
  "prompt-content",
  "prompt_content",
  "response-content",
  "response_content",
  "provider-exchange-content",
  "provider_exchange_content",
  "username",
  "hostname",
  "serial",
  "private-key",
  "private_key",
  "provider-payload",
  "provider_payload",
  "raw-private-content",
  "raw_private_content",
  "credential",
  "password",
  "secret",
  "bearer",
  "token",
] as const;

function hasExactStringList(
  value: unknown,
  expected: readonly string[],
): boolean {
  return (
    Array.isArray(value) &&
    value.length === expected.length &&
    expected.every((item, index) => value[index] === item)
  );
}

function expectedChatToLoopLabel(kind: unknown): string | null {
  switch (kind) {
    case "remember_this":
      return "remember this";
    case "create_action":
      return "create action";
    case "add_to_plan":
      return "add to plan";
    case "defer":
      return "defer";
    case "ask_human":
      return "ask human";
    case "blocked":
      return "blocked";
    default:
      return null;
  }
}

const MORNING_BRIEFING_V1_REQUIRED_ARRAYS = [
  "repo_status_refs",
  "workbench_status_refs",
  "source_readiness_refs",
  "missing_source_refs",
  "open_action_refs",
  "follow_up_refs",
  "memory_review_refs",
  "evidence_timeline_refs",
  "evidence_refs",
  "blocked_state_refs",
] as const;

function normalizeFounderMorningBriefing(
  value: FounderLoopMorningBriefing | undefined,
): { value: FounderLoopMorningBriefing; usedFallback: boolean } {
  const merged = stripFollowUpTrackerIfMissing(
    mockControlCenterData.founderMorningBriefing,
    value,
  );
  const valueRecord = (value ?? {}) as unknown as Record<string, unknown>;
  const normalized: Record<string, unknown> = {
    ...(merged.value as unknown as Record<string, unknown>),
  };
  if (
    isSafeMorningBriefingV1ReadModel(valueRecord.morning_briefing_v1_read_model)
  ) {
    normalized.morning_briefing_v1_read_model =
      valueRecord.morning_briefing_v1_read_model;
    normalized.morning_briefing_v1_contract_ref =
      valueRecord.morning_briefing_v1_contract_ref;
  } else {
    delete normalized.morning_briefing_v1_read_model;
    delete normalized.morning_briefing_v1_contract_ref;
  }
  const weeklyCeoReview = valueRecord.weekly_ceo_review_v1_read_model;
  if (isSafeWeeklyCeoReviewV1ReadModel(weeklyCeoReview)) {
    normalized.weekly_ceo_review_v1_read_model = weeklyCeoReview;
    normalized.weekly_ceo_review_v1_contract_ref = (
      weeklyCeoReview as Record<string, unknown>
    ).contract_ref;
  } else {
    delete normalized.weekly_ceo_review_v1_read_model;
    delete normalized.weekly_ceo_review_v1_contract_ref;
  }
  const productProof = valueRecord.founder_loop_v1_product_proof_read_model;
  if (isSafeFounderLoopProductProofReadModel(productProof)) {
    normalized.founder_loop_v1_product_proof_read_model = productProof;
    normalized.founder_loop_v1_product_proof_contract_ref = (
      productProof as Record<string, unknown>
    ).contract_ref;
  } else {
    delete normalized.founder_loop_v1_product_proof_read_model;
    delete normalized.founder_loop_v1_product_proof_contract_ref;
  }
  normalizeFounderLoopRunsIntegration(normalized, valueRecord);
  const chatToLoopHandoff = valueRecord.chat_to_loop_handoff_read_model;
  if (isSafeChatToLoopHandoffReadModel(chatToLoopHandoff)) {
    normalized.chat_to_loop_handoff_read_model = chatToLoopHandoff;
    normalized.chat_to_loop_handoff_contract_ref = (
      chatToLoopHandoff as Record<string, unknown>
    ).contract_ref;
  } else {
    delete normalized.chat_to_loop_handoff_read_model;
    delete normalized.chat_to_loop_handoff_contract_ref;
  }
  return {
    value: normalized as unknown as FounderLoopMorningBriefing,
    usedFallback: merged.usedFallback,
  };
}

function isSafeWeeklyCeoReviewV1ReadModel(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    value.schema_version !== "product-loop-008-weekly-ceo-review.v1" ||
    value.contract_ref !==
      "contract-ref:product-loop-008-weekly-ceo-review-v1:v1" ||
    value.source !== "python_core_weekly_ceo_review_v1_read_model"
  ) {
    return false;
  }
  return (
    value.backend_owned === true &&
    value.local_review_artifact_only === true &&
    value.safe_refs_only === true &&
    value.safe_summary_only === true &&
    value.raw_content_included === false &&
    value.evidence_backed === true &&
    typeof value.status === "string" &&
    typeof value.review_period_ref === "string" &&
    typeof value.safe_summary === "string" &&
    typeof value.completed_count === "number" &&
    typeof value.deferred_count === "number" &&
    typeof value.rejected_count === "number" &&
    typeof value.blocked_count === "number" &&
    typeof value.stale_count === "number" &&
    typeof value.unresolved_count === "number" &&
    typeof value.action_decision_count === "number" &&
    typeof value.memory_decision_count === "number" &&
    typeof value.follow_up_count === "number" &&
    typeof value.evidence_event_count === "number" &&
    typeof value.next_safe_action === "string" &&
    typeof value.authority_boundary === "string" &&
    hasDeniedFlagsFalse(value, WEEKLY_CEO_REVIEW_V1_DENIED_FLAGS) &&
    hasStringArrays(value, WEEKLY_CEO_REVIEW_V1_REQUIRED_ARRAYS) &&
    hasStringArrayPrefix(value, "evidence_event_refs", "evidence-event:") &&
    hasMatchingWeeklyCeoReviewV1Counts(value) &&
    Array.isArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-state:weekly-ceo-review-no-production-authority",
    )
  );
}

function hasMatchingWeeklyCeoReviewV1Counts(
  value: Record<string, unknown>,
): boolean {
  return WEEKLY_CEO_REVIEW_V1_COUNT_ARRAY_PAIRS.every(([countKey, refsKey]) => {
    const count = value[countKey];
    const refs = value[refsKey];
    return (
      typeof count === "number" && Array.isArray(refs) && count === refs.length
    );
  });
}

function isSafeFounderLoopProductProofReadModel(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    value.schema_version !== "founder-loop-v1-product-proof.v1" ||
    value.contract_ref !== "contract-ref:founder-loop-v1-product-proof:v1" ||
    value.source !== "python_core_founder_loop_v1_product_proof_read_model"
  ) {
    return false;
  }
  if (
    value.backend_owned !== true ||
    value.local_read_model_only !== true ||
    value.seeded_demo_safe !== true ||
    value.safe_refs_only !== true ||
    value.safe_summary_only !== true ||
    value.raw_content_included !== false ||
    typeof value.status !== "string" ||
    typeof value.scenario_ref !== "string" ||
    typeof value.shared_state_ref !== "string" ||
    typeof value.memory_review_status !== "string" ||
    typeof value.weekly_review_status !== "string" ||
    typeof value.decision_receipt_status !== "string" ||
    typeof value.safe_summary !== "string" ||
    typeof value.next_safe_action !== "string" ||
    typeof value.authority_boundary !== "string" ||
    typeof value.full_strength_goal !== "string" ||
    typeof value.repo_safe_scope !== "string" ||
    typeof value.blocked_authority_summary !== "string" ||
    typeof value.productized_surface_count !== "number" ||
    !isSafeEvidenceNarrativeText(value.full_strength_goal) ||
    !isSafeEvidenceNarrativeText(value.repo_safe_scope) ||
    !isSafeEvidenceNarrativeText(value.blocked_authority_summary) ||
    !hasDeniedFlagsFalse(value, FOUNDER_LOOP_PRODUCT_PROOF_DENIED_FLAGS) ||
    !hasStringArrays(value, FOUNDER_LOOP_PRODUCT_PROOF_REQUIRED_ARRAYS) ||
    !hasExactStringList(
      value.productized_surface_order,
      FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER,
    ) ||
    !Array.isArray(value.productized_surface_bindings) ||
    value.productized_surface_count !== value.productized_surface_bindings.length ||
    value.productized_surface_bindings.length !==
      FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER.length ||
    !value.productized_surface_bindings.every(
      isSafeFounderLoopProductizedSurfaceBinding,
    ) ||
    !hasExactStringList(
      (value.productized_surface_bindings as Record<string, unknown>[]).map(
        (binding) => String(binding.surface_id),
      ),
      FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER,
    ) ||
    !hasExactStringList(value.loop_order, FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER) ||
    !hasExactStringList(value.supported_decision_actions, [
      "approve",
      "edit",
      "reject",
      "defer",
    ]) ||
    !Array.isArray(value.steps) ||
    value.steps.length !== FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER.length ||
    !value.steps.every(isSafeFounderLoopProductProofStep) ||
    !hasExactStringList(
      (value.steps as Record<string, unknown>[]).map((step) =>
        String(step.step_id),
      ),
      FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER,
    ) ||
    !Array.isArray(value.blocked_authority_refs) ||
    !value.blocked_authority_refs.includes(
      "blocked-state:founder-loop-proof-no-production-authority",
    )
  ) {
    return false;
  }
  return (
    value.memory_review_status === "candidate_available" ||
    value.memory_review_status === "none"
  );
}

function isSafeFounderLoopProductizedSurfaceBinding(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    typeof value.surface_id === "string" &&
    FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER.includes(
      value.surface_id as (typeof FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER)[number],
    ) &&
    typeof value.surface === "string" &&
    typeof value.frontend_route_ref === "string" &&
    typeof value.backend_route_ref === "string" &&
    typeof value.status === "string" &&
    typeof value.product_posture === "string" &&
    typeof value.safe_summary === "string" &&
    typeof value.shared_ref === "string" &&
    typeof value.primary_proof_ref === "string" &&
    typeof value.next_safe_action === "string" &&
    isSafeEvidenceNarrativeText(value.surface) &&
    isSafeEvidenceNarrativeText(value.frontend_route_ref) &&
    isSafeEvidenceNarrativeText(value.backend_route_ref) &&
    isSafeEvidenceNarrativeText(value.status) &&
    isSafeEvidenceNarrativeText(value.product_posture) &&
    isSafeEvidenceNarrativeText(value.safe_summary) &&
    isSafeEvidenceNarrativeText(value.next_safe_action) &&
    isSafeFounderLoopTraceRef(value.shared_ref) &&
    isSafeFounderLoopTraceRef(value.primary_proof_ref) &&
    hasSafeFounderLoopTraceRefArrays(value, [
      "source_refs",
      "receipt_refs",
      "evidence_refs",
      "memory_candidate_refs",
      "blocked_state_refs",
    ])
  );
}

function isSafeFounderLoopRunsIntegrationReadModel(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    value.schema_version !== "founder-loop-runs-integration.v1" ||
    value.contract_ref !== "contract-ref:founder-loop-runs-integration:v1" ||
    value.source !== "python_core_founder_loop_runs_integration_read_model"
  ) {
    return false;
  }
  if (
    value.backend_owned !== true ||
    value.local_read_model_only !== true ||
    value.safe_refs_only !== true ||
    value.redacted_summaries_only !== true ||
    value.raw_payloads_persisted !== false ||
    value.ui_truth_source !== "python_core_read_model" ||
    value.primary_run_ref !== "run-ref:founder-loop-v1:governed-local-loop" ||
    value.primary_proof_ref !== "proof-ref:founder-loop-v1:governed-local-loop" ||
    typeof value.status !== "string" ||
    typeof value.surface_count !== "number" ||
    typeof value.action_origin_posture !== "string" ||
    typeof value.decision_receipt_posture !== "string" ||
    typeof value.evidence_path_posture !== "string" ||
    typeof value.proof_detail_posture !== "string" ||
    typeof value.memory_candidate_posture !== "string" ||
    typeof value.weekly_review_posture !== "string" ||
    typeof value.authority_boundary !== "string" ||
    typeof value.next_safe_action !== "string" ||
    !isSafeEvidenceNarrativeText(value.status) ||
    !isSafeEvidenceNarrativeText(value.action_origin_posture) ||
    !isSafeEvidenceNarrativeText(value.decision_receipt_posture) ||
    !isSafeEvidenceNarrativeText(value.evidence_path_posture) ||
    !isSafeEvidenceNarrativeText(value.proof_detail_posture) ||
    !isSafeEvidenceNarrativeText(value.memory_candidate_posture) ||
    !isSafeEvidenceNarrativeText(value.weekly_review_posture) ||
    !isSafeEvidenceNarrativeText(value.authority_boundary) ||
    !isSafeEvidenceNarrativeText(value.next_safe_action) ||
    !hasDeniedFlagsFalse(value, FOUNDER_LOOP_RUNS_INTEGRATION_DENIED_FLAGS) ||
    !hasStringArrays(value, FOUNDER_LOOP_RUNS_INTEGRATION_REQUIRED_ARRAYS) ||
    !hasExactStringList(value.surface_order, FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER) ||
    !Array.isArray(value.surface_bindings) ||
    value.surface_count !== value.surface_bindings.length ||
    value.surface_bindings.length !== FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER.length ||
    !value.surface_bindings.every(isSafeFounderLoopRunsIntegrationBinding) ||
    !hasExactStringList(
      (value.surface_bindings as Record<string, unknown>[]).map((binding) =>
        String(binding.surface_id),
      ),
      FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER,
    ) ||
    !hasSafeFounderLoopTraceRefArrays(
      value,
      FOUNDER_LOOP_RUNS_INTEGRATION_REQUIRED_ARRAYS,
    ) ||
    !Array.isArray(value.blocked_authority_refs) ||
    !value.blocked_authority_refs.includes(
      "blocked-state:founder-loop-runs-no-production-authority",
    )
  ) {
    return false;
  }
  return true;
}

function isSafeFounderLoopRunsIntegrationBinding(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const requiredArrays = [
    "action_source_refs",
    "approval_refs",
    "receipt_refs",
    "evidence_refs",
    "memory_candidate_refs",
    "operator_run_event_refs",
    "blocked_state_refs",
  ] as const;
  return (
    typeof value.surface_id === "string" &&
    FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER.includes(
      value.surface_id as (typeof FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER)[number],
    ) &&
    typeof value.surface === "string" &&
    typeof value.status === "string" &&
    typeof value.frontend_route_ref === "string" &&
    typeof value.backend_route_ref === "string" &&
    typeof value.run_ref === "string" &&
    typeof value.proof_ref === "string" &&
    typeof value.proof_detail_ref === "string" &&
    typeof value.proof_detail_route_ref === "string" &&
    typeof value.safe_summary === "string" &&
    typeof value.next_safe_action === "string" &&
    isSafeEvidenceNarrativeText(value.surface) &&
    isSafeEvidenceNarrativeText(value.status) &&
    isSafeEvidenceNarrativeText(value.frontend_route_ref) &&
    isSafeEvidenceNarrativeText(value.backend_route_ref) &&
    isSafeEvidenceNarrativeText(value.proof_detail_route_ref) &&
    isSafeEvidenceNarrativeText(value.safe_summary) &&
    isSafeEvidenceNarrativeText(value.next_safe_action) &&
    isSafeFounderLoopTraceRef(value.run_ref) &&
    isSafeFounderLoopTraceRef(value.proof_ref) &&
    isSafeFounderLoopTraceRef(value.proof_detail_ref) &&
    hasSafeFounderLoopTraceRefArrays(value, requiredArrays)
  );
}

function isSafeFounderLoopTraceRefs(value: unknown): value is FounderLoopTraceRefs {
  if (!isPlainRecord(value)) {
    return false;
  }
  const requiredArrays = [
    "run_refs",
    "operator_run_event_refs",
    "receipt_refs",
    "evidence_refs",
    "evidence_event_refs",
    "proof_refs",
    "approval_refs",
    "blocked_authority_refs",
  ] as const;
  return hasSafeFounderLoopTraceRefArrays(value, requiredArrays);
}

function hasSafeFounderLoopTraceRefArrays(
  record: Record<string, unknown>,
  fields: readonly string[],
): boolean {
  return fields.every((field) => {
    const value = record[field];
    return Array.isArray(value) && value.every(isSafeFounderLoopTraceRef);
  });
}

function isSafeFounderLoopTraceRef(value: unknown): value is string {
  if (typeof value !== "string" || value.length === 0) {
    return false;
  }
  const lowered = value.toLowerCase();
  if (
    EVIDENCE_NARRATIVE_UNSAFE_REF_FRAGMENTS.some((fragment) =>
      lowered.includes(fragment),
    )
  ) {
    return false;
  }
  if (value.includes("@") || value.includes("\\") || value.includes(".")) {
    return false;
  }
  if (value.includes("/") && !value.startsWith("evidence-timeline:")) {
    return false;
  }
  return /^[A-Za-z0-9:_./-]+$/.test(value);
}

function isSafeFounderLoopProductProofStep(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    typeof value.step_id === "string" &&
    FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER.includes(
      value.step_id as (typeof FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER)[number],
    ) &&
    typeof value.surface === "string" &&
    typeof value.backend_route_ref === "string" &&
    typeof value.frontend_route_ref === "string" &&
    typeof value.status === "string" &&
    typeof value.safe_summary === "string" &&
    typeof value.next_safe_action === "string" &&
    hasStringArrays(value, [
      "source_refs",
      "evidence_refs",
      "receipt_refs",
      "blocked_state_refs",
    ])
  );
}

function isSafeUnifiedWorkThreadReadModel(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    value.schema_version !== "fcc-thread-001-unified-work-thread.v1" ||
    value.contract_ref !==
      "contract-ref:fcc-thread-001-unified-work-thread:v1" ||
    value.source !== "python_core_unified_work_thread_read_model"
  ) {
    return false;
  }
  return (
    value.backend_owned === true &&
    value.local_read_model_only === true &&
    value.seeded_demo_safe === true &&
    value.safe_refs_only === true &&
    value.safe_summary_only === true &&
    value.raw_content_included === false &&
    typeof value.status === "string" &&
    typeof value.thread_ref === "string" &&
    typeof value.thread_title === "string" &&
    typeof value.safe_summary === "string" &&
    typeof value.next_safe_action === "string" &&
    typeof value.authority_boundary === "string" &&
    hasDeniedFlagsFalse(value, UNIFIED_WORK_THREAD_DENIED_FLAGS) &&
    hasStringArrays(value, UNIFIED_WORK_THREAD_REQUIRED_ARRAYS) &&
    hasExactStringList(value.step_order, UNIFIED_WORK_THREAD_STEP_ORDER) &&
    Array.isArray(value.steps) &&
    value.steps.length === UNIFIED_WORK_THREAD_STEP_ORDER.length &&
    value.steps.every(isSafeUnifiedWorkThreadStep) &&
    hasExactStringList(
      (value.steps as Record<string, unknown>[]).map((step) =>
        String(step.step_id),
      ),
      UNIFIED_WORK_THREAD_STEP_ORDER,
    ) &&
    Array.isArray(value.blocked_authority_refs) &&
    UNIFIED_WORK_THREAD_REQUIRED_BLOCKED_REFS.every((ref) =>
      (value.blocked_authority_refs as string[]).includes(ref),
    )
  );
}

function isSafeUnifiedWorkThreadStep(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    typeof value.step_id === "string" &&
    UNIFIED_WORK_THREAD_STEP_ORDER.includes(
      value.step_id as (typeof UNIFIED_WORK_THREAD_STEP_ORDER)[number],
    ) &&
    typeof value.surface === "string" &&
    typeof value.frontend_route_ref === "string" &&
    typeof value.backend_route_ref === "string" &&
    typeof value.status === "string" &&
    typeof value.safe_summary === "string" &&
    typeof value.next_safe_action === "string" &&
    hasStringArrays(value, [
      "source_refs",
      "proposal_refs",
      "receipt_refs",
      "evidence_refs",
      "blocked_authority_refs",
    ])
  );
}

function isSafeChatToLoopHandoffReadModel(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    value.schema_version !== "product-loop-009-chat-to-loop-handoff.v1" ||
    value.contract_ref !==
      "contract-ref:product-loop-009-chat-to-loop-handoff:v1" ||
    value.source !== "python_core_chat_to_loop_handoff_read_model"
  ) {
    return false;
  }
  if (
    value.backend_owned !== true ||
    value.local_read_model_only !== true ||
    value.proposal_only !== true ||
    value.safe_refs_only !== true ||
    value.safe_summary_only !== true ||
    value.raw_content_included !== false ||
    value.idempotency_bound !== true ||
    !isSafeChatToLoopText(value.status) ||
    !isSafeChatToLoopText(value.safe_summary) ||
    !isSafeChatToLoopText(value.next_safe_action) ||
    !hasDeniedFlagsFalse(value, CHAT_TO_LOOP_HANDOFF_DENIED_FLAGS) ||
    !hasStringArrays(value, CHAT_TO_LOOP_HANDOFF_REQUIRED_ARRAYS) ||
    !hasSafeChatToLoopRefArrays(
      value,
      CHAT_TO_LOOP_HANDOFF_REQUIRED_REF_ARRAYS,
    ) ||
    !hasMatchingChatToLoopHandoffCounts(value) ||
    !Array.isArray(value.outcomes) ||
    !value.outcomes.every(isSafeChatToLoopHandoffOutcome) ||
    !hasExactStringList(
      (value.outcomes as Record<string, unknown>[]).map((outcome) =>
        String(outcome.outcome_kind),
      ),
      CHAT_TO_LOOP_HANDOFF_OUTCOME_KINDS,
    ) ||
    !hasExactStringList(
      value.outcome_kinds,
      CHAT_TO_LOOP_HANDOFF_OUTCOME_KINDS,
    ) ||
    !Array.isArray(value.blocked_state_refs) ||
    !value.blocked_state_refs.includes(
      "blocked-state:chat-to-loop-no-production-authority",
    )
  ) {
    return false;
  }
  return (
    Array.isArray(value.outcome_refs) &&
    value.outcome_refs.join("\u0000") ===
      (value.outcomes as Record<string, unknown>[])
        .map((outcome) => String(outcome.outcome_ref))
        .join("\u0000")
  );
}

function isSafeChatToLoopHandoffOutcome(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const expectedLabel = expectedChatToLoopLabel(value.outcome_kind);
  return (
    typeof value.outcome_ref === "string" &&
    isSafeChatToLoopRef(value.outcome_ref) &&
    typeof value.outcome_kind === "string" &&
    CHAT_TO_LOOP_HANDOFF_OUTCOME_KINDS.includes(
      value.outcome_kind as (typeof CHAT_TO_LOOP_HANDOFF_OUTCOME_KINDS)[number],
    ) &&
    CHAT_TO_LOOP_HANDOFF_STATES.includes(
      value.state as (typeof CHAT_TO_LOOP_HANDOFF_STATES)[number],
    ) &&
    typeof value.target_surface === "string" &&
    CHAT_TO_LOOP_HANDOFF_TARGET_SURFACES.includes(
      value.target_surface as (typeof CHAT_TO_LOOP_HANDOFF_TARGET_SURFACES)[number],
    ) &&
    expectedLabel !== null &&
    value.safe_label === expectedLabel &&
    isSafeChatToLoopText(value.state) &&
    isSafeChatToLoopText(value.safe_label) &&
    isSafeChatToLoopText(value.target_surface) &&
    typeof value.source_ref === "string" &&
    isSafeChatToLoopRef(value.source_ref) &&
    typeof value.proposal_ref === "string" &&
    isSafeChatToLoopRef(value.proposal_ref) &&
    isSafeChatToLoopText(value.next_safe_action) &&
    hasStringArrays(value, [
      "receipt_refs",
      "evidence_refs",
      "blocked_state_refs",
    ]) &&
    hasSafeChatToLoopRefArrays(value, [
      "receipt_refs",
      "evidence_refs",
      "blocked_state_refs",
    ])
  );
}

function hasMatchingChatToLoopHandoffCounts(
  value: Record<string, unknown>,
): boolean {
  return CHAT_TO_LOOP_HANDOFF_COUNT_ARRAY_PAIRS.every(([countKey, refsKey]) => {
    const count = value[countKey];
    const refs = value[refsKey];
    return (
      typeof count === "number" && Array.isArray(refs) && count === refs.length
    );
  });
}

function isSafeEvidenceTimelineNarrativeReadModel(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    value.schema_version !==
      "product-loop-010-evidence-timeline-narrative.v1" ||
    value.contract_ref !==
      "contract-ref:product-loop-010-evidence-timeline-narrative:v1" ||
    value.source !== "python_core_evidence_timeline_narrative_read_model"
  ) {
    return false;
  }
  if (
    !hasTrueFlags(value, EVIDENCE_NARRATIVE_TRUE_FLAGS) ||
    !hasDeniedFlagsFalse(value, EVIDENCE_NARRATIVE_DENIED_FLAGS) ||
    !isSafeEvidenceNarrativeText(value.status) ||
    !isSafeEvidenceNarrativeText(value.authority_boundary) ||
    !isSafeEvidenceNarrativeText(value.next_safe_action) ||
    !hasStringArrays(value, EVIDENCE_NARRATIVE_AGGREGATE_REF_ARRAYS) ||
    !hasSafeEvidenceNarrativeRefArrays(
      value,
      EVIDENCE_NARRATIVE_AGGREGATE_REF_ARRAYS,
    ) ||
    typeof value.entry_count !== "number" ||
    typeof value.event_count !== "number" ||
    typeof value.group_count !== "number" ||
    typeof value.narrative_item_count !== "number" ||
    !Array.isArray(value.entries) ||
    value.entry_count !== value.entries.length ||
    value.entries.length > 50 ||
    !value.entries.every(isSafeEvidenceNarrativeEntry)
  ) {
    return false;
  }
  const entries = value.entries as Record<string, unknown>[];
  return (
    hasExactStringList(
      value.narrative_refs,
      entries.map((entry) => String(entry.narrative_ref)),
    ) && hasMatchingEvidenceNarrativeAggregates(value, entries)
  );
}

function isSafeEvidenceMemoryLoopBindingReadModel(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    value.schema_version !== "evidence-memory-loop-binding.v1" ||
    value.contract_ref !==
      "contract-ref:usable-authority-evidence-memory-loop-binding:v1" ||
    value.source !== "python_core_evidence_memory_loop_binding_read_model" ||
    !hasTrueFlags(value, EVIDENCE_MEMORY_BINDING_TRUE_FLAGS) ||
    !hasDeniedFlagsFalse(value, EVIDENCE_MEMORY_BINDING_DENIED_FLAGS) ||
    !hasStringArrays(value, ["route_refs"]) ||
    !hasStringArrays(value, EVIDENCE_MEMORY_BINDING_AGGREGATE_REF_ARRAYS) ||
    !hasSafeEvidenceMemoryBindingRefArrays(
      value,
      EVIDENCE_MEMORY_BINDING_AGGREGATE_REF_ARRAYS,
    ) ||
    typeof value.evidence_binding_count !== "number" ||
    typeof value.memory_binding_count !== "number" ||
    !isSafeEvidenceMemoryBindingRef(value.shared_loop_ref) ||
    !isSafeEvidenceMemoryBindingRef(value.reviewed_memory_write_scope_ref) ||
    !isSafeEvidenceMemoryBindingRef(value.memory_write_safe_disable_ref) ||
    !isSafeEvidenceMemoryBindingRef(value.memory_write_rollback_ref) ||
    !Array.isArray(value.reviewed_memory_write_authorized_decisions) ||
    !hasExactStringList(value.reviewed_memory_write_authorized_decisions, [
      "accept",
      "correct",
    ]) ||
    typeof value.reviewed_memory_write_authorized !== "boolean" ||
    value.broad_memory_write_blocked !== true ||
    !["status", "cli_ref", "operator_summary", "next_safe_action", "authority_boundary"].every(
      (field) => isSafeEvidenceMemoryBindingText(value[field]),
    ) ||
    !Array.isArray(value.evidence_bindings) ||
    !Array.isArray(value.memory_bindings) ||
    value.evidence_binding_count !== value.evidence_bindings.length ||
    value.memory_binding_count !== value.memory_bindings.length ||
    !value.evidence_bindings.every(isSafeEvidenceMemoryEvidenceBinding) ||
    !value.memory_bindings.every(isSafeEvidenceMemoryMemoryBinding)
  ) {
    return false;
  }
  return (
    hasExactStringList(value.shared_run_refs, stringArray(value.run_refs)) &&
    hasEvidenceMemoryAggregateSharedRefs(value) &&
    hasEvidenceMemoryBindingSharedRefs(value)
  );
}

function isSafeEvidenceMemoryEvidenceBinding(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    [
      "binding_ref",
      "timeline_item_ref",
      "event_ref",
      "group_ref",
    ].every((field) => isSafeEvidenceMemoryBindingRef(value[field])) &&
    [
      "event_type",
      "title",
      "why_recorded",
      "next_safe_action",
    ].every((field) => isSafeEvidenceMemoryBindingText(value[field])) &&
    hasStringArrays(value, EVIDENCE_MEMORY_EVIDENCE_BINDING_REF_ARRAYS) &&
    hasSafeEvidenceMemoryBindingRefArrays(
      value,
      EVIDENCE_MEMORY_EVIDENCE_BINDING_REF_ARRAYS,
    )
  );
}

function isSafeEvidenceMemoryMemoryBinding(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    ["binding_ref", "memory_candidate_ref", "review_ref"].every((field) =>
      isSafeEvidenceMemoryBindingRef(value[field]),
    ) &&
    ["title", "why_shown", "write_posture", "context_posture", "next_safe_action"].every(
      (field) => isSafeEvidenceMemoryBindingText(value[field]),
    ) &&
    isSafeEvidenceMemoryBindingRef(value.reviewed_memory_write_scope_ref) &&
    isSafeEvidenceMemoryBindingRef(value.memory_write_safe_disable_ref) &&
    isSafeEvidenceMemoryBindingRef(value.memory_write_rollback_ref) &&
    value.reviewed_recall_only === true &&
    typeof value.reviewed_memory_write_authorized === "boolean" &&
    value.broad_memory_write_blocked === true &&
    value.memory_truth_authority === false &&
    value.context_injection_authorized === false &&
    value.automatic_memory_write_authorized === false &&
    hasStringArrays(value, EVIDENCE_MEMORY_MEMORY_BINDING_REF_ARRAYS) &&
    hasSafeEvidenceMemoryBindingRefArrays(
      value,
      EVIDENCE_MEMORY_MEMORY_BINDING_REF_ARRAYS,
    )
  );
}

function hasEvidenceMemoryAggregateSharedRefs(
  value: Record<string, unknown>,
): boolean {
  if (!Array.isArray(value.evidence_bindings) || !Array.isArray(value.memory_bindings)) {
    return false;
  }
  const evidenceBindings = value.evidence_bindings as Record<string, unknown>[];
  const memoryBindings = value.memory_bindings as Record<string, unknown>[];
  const actionRefs = uniqueStrings([
    ...evidenceBindings.flatMap((binding) => stringArray(binding.action_refs)),
    ...memoryBindings.flatMap((binding) => stringArray(binding.related_action_refs)),
  ]);
  const proofRefs = uniqueStrings([
    ...evidenceBindings.flatMap((binding) => stringArray(binding.proof_refs)),
    ...memoryBindings.flatMap((binding) => stringArray(binding.related_proof_refs)),
  ]);
  return (
    hasExactStringList(value.shared_action_refs, actionRefs) &&
    hasExactStringList(value.shared_proof_refs, proofRefs)
  );
}

function hasEvidenceMemoryBindingSharedRefs(
  value: Record<string, unknown>,
): boolean {
  if (!Array.isArray(value.evidence_bindings) || !Array.isArray(value.memory_bindings)) {
    return false;
  }
  const bindings = [
    ...(value.evidence_bindings as Record<string, unknown>[]),
    ...(value.memory_bindings as Record<string, unknown>[]),
  ];
  return bindings.every(
    (binding) =>
      hasExactStringList(binding.shared_loop_refs, [String(value.shared_loop_ref)]) &&
      hasExactStringList(binding.shared_run_refs, stringArray(value.shared_run_refs)) &&
      hasExactStringList(
        binding.shared_action_refs,
        stringArray(value.shared_action_refs),
      ) &&
      hasExactStringList(
        binding.shared_proof_refs,
        stringArray(value.shared_proof_refs),
      ),
  );
}

function stringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string");
}

function uniqueStrings(values: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const value of values) {
    if (!value || seen.has(value)) {
      continue;
    }
    seen.add(value);
    result.push(value);
  }
  return result;
}

function hasSafeEvidenceMemoryBindingRefArrays(
  record: Record<string, unknown>,
  fields: readonly string[],
): boolean {
  return fields.every((field) => {
    const value = record[field];
    return Array.isArray(value) && value.every(isSafeEvidenceMemoryBindingRef);
  });
}

function isSafeEvidenceMemoryBindingRef(value: unknown): value is string {
  if (typeof value !== "string" || value.length === 0) {
    return false;
  }
  const lowered = value.toLowerCase();
  if (
    EVIDENCE_NARRATIVE_UNSAFE_REF_FRAGMENTS.some((fragment) =>
      lowered.includes(fragment),
    )
  ) {
    return false;
  }
  if (value.includes("@") || value.includes("\\") || value.includes(" ")) {
    return false;
  }
  return /^[A-Za-z0-9:_./#=-]+$/.test(value);
}

function isSafeEvidenceMemoryBindingText(value: unknown): value is string {
  if (typeof value !== "string" || value.length === 0) {
    return false;
  }
  const lowered = value.toLowerCase();
  return !EVIDENCE_NARRATIVE_UNSAFE_TEXT_FRAGMENTS.some((fragment) =>
    lowered.includes(fragment),
  );
}

function isSafeEvidenceNarrativeEntry(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const requiredTextFields = [
    "group_kind",
    "event_type",
    "title",
    "what_happened",
    "why_recorded",
    "approval_posture",
    "change_summary",
    "remaining_blocked",
    "inspection_summary",
  ] as const;
  const requiredRefFields = [
    "narrative_ref",
    "event_ref",
    "timeline_item_ref",
    "group_ref",
  ] as const;
  return (
    requiredTextFields.every((field) =>
      isSafeEvidenceNarrativeText(value[field]),
    ) &&
    requiredRefFields.every((field) =>
      isSafeEvidenceNarrativeRef(value[field]),
    ) &&
    hasDeniedFlagsFalse(value, EVIDENCE_NARRATIVE_DENIED_FLAGS) &&
    hasStringArrays(value, EVIDENCE_NARRATIVE_REF_ARRAYS) &&
    hasSafeEvidenceNarrativeRefArrays(value, EVIDENCE_NARRATIVE_REF_ARRAYS)
  );
}

function hasMatchingEvidenceNarrativeAggregates(
  value: Record<string, unknown>,
  entries: Record<string, unknown>[],
): boolean {
  const expected: Record<string, string[]> = {
    event_refs: uniqueSortedStrings(
      entries.map((entry) => String(entry.event_ref)),
    ),
    timeline_item_refs: uniqueSortedStrings(
      entries.map((entry) => String(entry.timeline_item_ref)),
    ),
    group_refs: uniqueSortedStrings(
      entries.map((entry) => String(entry.group_ref)),
    ),
    receipt_refs: uniqueSortedStrings(
      entries.flatMap((entry) => entryStringArray(entry, "receipt_refs")),
    ),
    approval_refs: uniqueSortedStrings(
      entries.flatMap((entry) => entryStringArray(entry, "approval_refs")),
    ),
    audit_refs: uniqueSortedStrings(
      entries.flatMap((entry) => entryStringArray(entry, "audit_refs")),
    ),
    idempotency_refs: uniqueSortedStrings(
      entries.flatMap((entry) => entryStringArray(entry, "idempotency_refs")),
    ),
    rollback_refs: uniqueSortedStrings(
      entries.flatMap((entry) => entryStringArray(entry, "rollback_refs")),
    ),
    evidence_refs: uniqueSortedStrings(
      entries.flatMap((entry) => entryStringArray(entry, "evidence_refs")),
    ),
    blocked_state_refs: uniqueSortedStrings(
      entries.flatMap((entry) => entryStringArray(entry, "blocked_state_refs")),
    ),
  };
  return Object.entries(expected).every(([field, refs]) =>
    hasExactStringList(value[field], refs),
  );
}

function entryStringArray(
  entry: Record<string, unknown>,
  field: string,
): string[] {
  const value = entry[field];
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string");
}

function uniqueSortedStrings(values: string[]): string[] {
  return Array.from(new Set(values.filter(Boolean))).sort();
}

function hasSafeEvidenceNarrativeRefArrays(
  record: Record<string, unknown>,
  fields: readonly string[],
): boolean {
  return fields.every((field) => {
    const value = record[field];
    return Array.isArray(value) && value.every(isSafeEvidenceNarrativeRef);
  });
}

function isSafeEvidenceNarrativeRef(value: unknown): value is string {
  if (typeof value !== "string" || value.length === 0) {
    return false;
  }
  const lowered = value.toLowerCase();
  if (
    EVIDENCE_NARRATIVE_UNSAFE_REF_FRAGMENTS.some((fragment) =>
      lowered.includes(fragment),
    )
  ) {
    return false;
  }
  if (value.includes("@") || value.includes("\\") || value.includes(".")) {
    return false;
  }
  if (value.includes("/") && !value.startsWith("evidence-timeline:")) {
    return false;
  }
  return /^[A-Za-z0-9:_./-]+$/.test(value);
}

function isSafeEvidenceNarrativeText(value: unknown): value is string {
  if (typeof value !== "string" || value.length === 0) {
    return false;
  }
  const lowered = value.toLowerCase();
  return !EVIDENCE_NARRATIVE_UNSAFE_TEXT_FRAGMENTS.some((fragment) =>
    lowered.includes(fragment),
  );
}

function isSafeMorningBriefingV1ReadModel(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    value.schema_version !== "product-loop-007-morning-briefing.v1" ||
    value.contract_ref !==
      "contract-ref:product-loop-007-morning-briefing-v1:v1" ||
    value.source !== "python_core_morning_briefing_v1_read_model"
  ) {
    return false;
  }
  return (
    value.backend_owned === true &&
    value.local_read_model_only === true &&
    value.safe_refs_only === true &&
    value.raw_content_included === false &&
    value.bounded_preview_only === true &&
    value.source_readiness_required === true &&
    value.missing_sources_visible === true &&
    typeof value.item_count === "number" &&
    typeof value.section_count === "number" &&
    typeof value.open_action_count === "number" &&
    typeof value.follow_up_count === "number" &&
    typeof value.memory_review_count === "number" &&
    typeof value.source_blocker_count === "number" &&
    typeof value.safe_summary === "string" &&
    typeof value.today_summary_ref === "string" &&
    typeof value.source_readiness_posture_ref === "string" &&
    typeof value.next_safe_action === "string" &&
    typeof value.authority_boundary === "string" &&
    hasDeniedFlagsFalse(value, MORNING_BRIEFING_V1_DENIED_FLAGS) &&
    hasStringArrays(value, MORNING_BRIEFING_V1_REQUIRED_ARRAYS)
  );
}

function normalizeFounderActionsInbox(
  value: FounderLoopActionsInbox | undefined,
): { value: FounderLoopActionsInbox; usedFallback: boolean } {
  const merged = stripFollowUpTrackerIfMissing(
    mockControlCenterData.founderActionsInbox,
    value,
  );
  const valueRecord = (value ?? {}) as unknown as Record<string, unknown>;
  const safePlansToActionsBridge = isSafePlansToActionsBridgeReadModel(
    valueRecord.plans_to_actions_bridge_read_model,
  );
  const safeChatToLoopHandoff = isSafeChatToLoopHandoffReadModel(
    valueRecord.chat_to_loop_handoff_read_model,
  );
  const safeActionInboxWorkQueue = isSafeActionInboxWorkQueueReadModel(
    valueRecord.action_inbox_work_queue_read_model,
  );
  const safeRuntimeActionInboxBridge =
    isSafeRuntimeActionInboxBridgeReadModel(
      valueRecord.runtime_action_inbox_bridge_read_model,
    );
  const safeActionToolCodeCatalog = isSafeActionToolCodeCatalogReadModel(
    valueRecord.action_tool_code_lane_catalog_read_model,
  );
  if (
    value === undefined ||
    !isSafeActionInboxDecisionLaneReadModel(
      valueRecord.action_inbox_decision_lane_read_model,
    )
  ) {
    const withoutMockLanes = {
      ...(merged.value as unknown as Record<string, unknown>),
    };
    if (safeActionInboxWorkQueue) {
      withoutMockLanes.action_inbox_work_queue_read_model =
        valueRecord.action_inbox_work_queue_read_model;
      withoutMockLanes.action_inbox_work_queue_contract_ref =
        valueRecord.action_inbox_work_queue_contract_ref;
    } else {
      delete withoutMockLanes.action_inbox_work_queue_read_model;
      delete withoutMockLanes.action_inbox_work_queue_contract_ref;
    }
    if (safeRuntimeActionInboxBridge) {
      withoutMockLanes.runtime_action_inbox_bridge_read_model =
        valueRecord.runtime_action_inbox_bridge_read_model;
      withoutMockLanes.runtime_action_inbox_bridge_contract_ref =
        valueRecord.runtime_action_inbox_bridge_contract_ref;
    } else {
      delete withoutMockLanes.runtime_action_inbox_bridge_read_model;
      delete withoutMockLanes.runtime_action_inbox_bridge_contract_ref;
    }
    if (safeActionToolCodeCatalog) {
      withoutMockLanes.action_tool_code_lane_catalog_read_model =
        valueRecord.action_tool_code_lane_catalog_read_model;
      withoutMockLanes.action_tool_code_lane_catalog_contract_ref =
        valueRecord.action_tool_code_lane_catalog_contract_ref;
    } else {
      delete withoutMockLanes.action_tool_code_lane_catalog_read_model;
      delete withoutMockLanes.action_tool_code_lane_catalog_contract_ref;
    }
    delete withoutMockLanes.action_inbox_decision_lane_read_model;
    delete withoutMockLanes.action_inbox_decision_lane_contract_ref;
    if (safePlansToActionsBridge) {
      withoutMockLanes.plans_to_actions_bridge_read_model =
        valueRecord.plans_to_actions_bridge_read_model;
      withoutMockLanes.plans_to_actions_bridge_contract_ref =
        valueRecord.plans_to_actions_bridge_contract_ref;
    } else {
      delete withoutMockLanes.plans_to_actions_bridge_read_model;
      delete withoutMockLanes.plans_to_actions_bridge_contract_ref;
    }
    if (safeChatToLoopHandoff) {
      withoutMockLanes.chat_to_loop_handoff_read_model =
        valueRecord.chat_to_loop_handoff_read_model;
      withoutMockLanes.chat_to_loop_handoff_contract_ref = (
        valueRecord.chat_to_loop_handoff_read_model as Record<string, unknown>
      ).contract_ref;
    } else {
      delete withoutMockLanes.chat_to_loop_handoff_read_model;
      delete withoutMockLanes.chat_to_loop_handoff_contract_ref;
    }
    return {
      value: withoutMockLanes as unknown as FounderLoopActionsInbox,
      usedFallback: merged.usedFallback,
    };
  }
  const normalized: Record<string, unknown> = {
    ...(merged.value as unknown as Record<string, unknown>),
    action_inbox_decision_lane_read_model:
      valueRecord.action_inbox_decision_lane_read_model,
    action_inbox_decision_lane_contract_ref:
      valueRecord.action_inbox_decision_lane_contract_ref,
  };
  if (safeActionInboxWorkQueue) {
    normalized.action_inbox_work_queue_read_model =
      valueRecord.action_inbox_work_queue_read_model;
    normalized.action_inbox_work_queue_contract_ref =
      valueRecord.action_inbox_work_queue_contract_ref;
  } else {
    delete normalized.action_inbox_work_queue_read_model;
    delete normalized.action_inbox_work_queue_contract_ref;
  }
  if (safeRuntimeActionInboxBridge) {
    normalized.runtime_action_inbox_bridge_read_model =
      valueRecord.runtime_action_inbox_bridge_read_model;
    normalized.runtime_action_inbox_bridge_contract_ref =
      valueRecord.runtime_action_inbox_bridge_contract_ref;
  } else {
    delete normalized.runtime_action_inbox_bridge_read_model;
    delete normalized.runtime_action_inbox_bridge_contract_ref;
  }
  if (safeActionToolCodeCatalog) {
    normalized.action_tool_code_lane_catalog_read_model =
      valueRecord.action_tool_code_lane_catalog_read_model;
    normalized.action_tool_code_lane_catalog_contract_ref =
      valueRecord.action_tool_code_lane_catalog_contract_ref;
  } else {
    delete normalized.action_tool_code_lane_catalog_read_model;
    delete normalized.action_tool_code_lane_catalog_contract_ref;
  }
  if (safePlansToActionsBridge) {
    normalized.plans_to_actions_bridge_read_model =
      valueRecord.plans_to_actions_bridge_read_model;
    normalized.plans_to_actions_bridge_contract_ref =
      valueRecord.plans_to_actions_bridge_contract_ref;
  } else {
    delete normalized.plans_to_actions_bridge_read_model;
    delete normalized.plans_to_actions_bridge_contract_ref;
  }
  if (safeChatToLoopHandoff) {
    normalized.chat_to_loop_handoff_read_model =
      valueRecord.chat_to_loop_handoff_read_model;
    normalized.chat_to_loop_handoff_contract_ref = (
      valueRecord.chat_to_loop_handoff_read_model as Record<string, unknown>
    ).contract_ref;
  } else {
    delete normalized.chat_to_loop_handoff_read_model;
    delete normalized.chat_to_loop_handoff_contract_ref;
  }
  return {
    value: normalized as unknown as FounderLoopActionsInbox,
    usedFallback: merged.usedFallback,
  };
}

function isSafePlansToActionsBridgeReadModel(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    value.schema_version !== "product-loop-006-plans-to-actions.v1" ||
    value.source !== "python_core_plans_to_actions_bridge_read_model" ||
    value.contract_ref !==
      "contract-ref:product-loop-006-plans-to-reviewable-action-envelopes:v1"
  ) {
    return false;
  }
  if (
    !hasTrueFlags(value, PLANS_TO_ACTIONS_BRIDGE_TRUE_FLAGS) ||
    value.raw_content_included !== false ||
    !hasDeniedFlagsFalse(value, PLANS_TO_ACTIONS_BRIDGE_DENIED_FLAGS) ||
    !hasStringArrays(value, PLANS_TO_ACTIONS_BRIDGE_REQUIRED_ARRAYS)
  ) {
    return false;
  }
  if (!Array.isArray(value.items) || typeof value.item_count !== "number") {
    return false;
  }
  if (value.item_count !== value.items.length || value.items.length > 50) {
    return false;
  }
  if (!value.items.every(isSafePlansToActionsBridgeItem)) {
    return false;
  }
  return (
    typeof value.next_safe_action === "string" &&
    typeof value.authority_boundary === "string"
  );
}

function isSafePlansToActionsBridgeItem(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const requiredTextFields = [
    "item_ref",
    "source_plan_ref",
    "plan_title",
    "plan_status",
    "safe_summary",
    "why_proposed",
    "risk_class",
    "action_envelope_ref",
    "action_scope_ref",
    "approval_requirement_ref",
    "rollback_ref",
    "safe_disable_ref",
    "next_safe_action",
  ];
  if (!requiredTextFields.every((field) => typeof value[field] === "string")) {
    return false;
  }
  for (const field of [
    "linked_action_item_ref",
    "task_decomposition_proposal_ref",
    "task_decomposition_review_envelope_ref",
    "task_decomposition_action_inbox_bridge_ref",
  ]) {
    if (
      value[field] !== null &&
      value[field] !== undefined &&
      typeof value[field] !== "string"
    ) {
      return false;
    }
  }
  return (
    hasTrueFlags(value, PLANS_TO_ACTIONS_BRIDGE_ITEM_TRUE_FLAGS) &&
    value.raw_content_included === false &&
    hasDeniedFlagsFalse(value, PLANS_TO_ACTIONS_BRIDGE_DENIED_FLAGS) &&
    hasStringArrays(value, PLANS_TO_ACTIONS_BRIDGE_ITEM_REQUIRED_ARRAYS) &&
    hasRequiredReviewReceiptLabels(value.review_receipt_labels) &&
    isOptionalSafeFusionMetadata(value) &&
    (value.expected_receipt_refs as unknown[]).length > 0 &&
    (value.evidence_refs as unknown[]).length > 0 &&
    (value.blocked_authority_refs as unknown[]).length > 0
  );
}

function isSafeFusionRoutingReadModel(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    value.schema_version !== "fcc_fusion_routing_delegation.v1" ||
    value.source !== "python_core_fusion_routing_delegation_read_model" ||
    value.contract_ref !== "contract-ref:fcc-fusion-routing-delegation:v1" ||
    value.backend_owned !== true ||
    value.safe_refs_only !== true ||
    value.raw_content_included !== false
  ) {
    return false;
  }
  if (
    value.action_execution_enabled !== false ||
    value.sidekick_execution_enabled !== false ||
    value.provider_model_call_enabled !== false ||
    value.background_dispatch_enabled !== false ||
    value.production_authority_enabled !== false
  ) {
    return false;
  }
  return (
    Array.isArray(value.work_classifications) &&
    Array.isArray(value.route_decisions) &&
    Array.isArray(value.delegation_proposals) &&
    Array.isArray(value.cache_context_economics) &&
    Array.isArray(value.dogfood_records) &&
    Array.isArray(value.blocked_state_refs)
  );
}

function isOptionalSafeFusionMetadata(value: Record<string, unknown>): boolean {
  const classification = value.work_classification;
  const delegation = value.delegation_proposal;
  const cacheContext = value.cache_context_economics;
  if (classification !== undefined && !isSafeFusionWorkClassification(classification)) {
    return false;
  }
  if (delegation !== undefined && !isSafeFusionDelegation(delegation)) {
    return false;
  }
  if (cacheContext !== undefined && !isSafeFusionCacheContext(cacheContext)) {
    return false;
  }
  return true;
}

function isSafeFusionWorkClassification(value: unknown): boolean {
  return (
    isPlainRecord(value) &&
    value.schema_version === "fcc_fusion_work_classification.v1" &&
    value.contract_ref === "contract-ref:fcc-fusion-routing-delegation:v1" &&
    value.review_aid_only === true &&
    value.execution_authorized === false &&
    value.action_execution_enabled === false &&
    Array.isArray(value.reason_refs) &&
    Array.isArray(value.source_refs) &&
    Array.isArray(value.evidence_refs)
  );
}

function isSafeFusionDelegation(value: unknown): boolean {
  return (
    isPlainRecord(value) &&
    value.schema_version === "fcc_fusion_delegation_proposal.v1" &&
    value.contract_ref === "contract-ref:fcc-fusion-routing-delegation:v1" &&
    value.future_only === true &&
    value.creates_approval_ref === false &&
    value.creates_execution_ref === false &&
    value.worker_execution_enabled === false &&
    value.background_dispatch_enabled === false &&
    Array.isArray(value.blocked_execution_refs) &&
    isSafeFusionWorkClassification(value.work_classification)
  );
}

function isSafeFusionCacheContext(value: unknown): boolean {
  return (
    isPlainRecord(value) &&
    value.schema_version === "fcc_fusion_cache_context_economics.v1" &&
    value.contract_ref === "contract-ref:fcc-fusion-routing-delegation:v1" &&
    value.explanatory_posture_only === true &&
    value.runtime_model_switch_performed === false &&
    Array.isArray(value.cache_or_context_blocker_refs)
  );
}

const ACTION_DECISION_LANE_REQUIRED_STRING_ARRAYS = [
  "lane_order",
  "blocked_state_refs",
] as const;

const ACTION_DECISION_LANE_ORDER = [
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

const ACTION_DECISION_LANE_ITEM_REQUIRED_STRINGS = [
  "item_ref",
  "lane_id",
  "lane_label",
  "title",
  "status",
  "priority",
  "action_kind",
  "side_effect_class",
  "safe_summary",
  "why_shown",
  "next_safe_action",
  "authority_boundary",
  "approval_envelope_status",
  "expected_receipt_state",
  "cost_state_label",
  "provider_authority_state_label",
] as const;

const ACTION_DECISION_LANE_ITEM_REQUIRED_NUMBERS = [
  "estimated_cost_usd",
  "max_approved_cost_usd",
  "input_metered_units",
  "output_metered_units",
  "total_metered_units",
] as const;

const ACTION_DECISION_LANE_ITEM_REQUIRED_ARRAYS = [
  "expected_receipt_refs",
  "evidence_refs",
  "receipt_refs",
  "blocked_authority_refs",
  "missing_envelope_field_states",
  "cost_receipt_refs",
  "cost_blocked_state_refs",
] as const;

const ACTION_DECISION_LANE_ITEM_DENIED_FLAGS = [
  "approval_alone_executes",
  "approval_ref_authority",
  "approval_grants_runtime_authority",
  "action_execution_enabled",
  "connector_write_enabled",
  "shell_subprocess_execution_enabled",
  "browser_execution_enabled",
  "provider_model_call_enabled",
  "memory_write_enabled",
  "context_injection_authorized",
  "hidden_memory_write_authorized",
  "production_authority_enabled",
] as const;

const ACTION_WORK_QUEUE_DENIED_FLAGS = [
  "action_execution_enabled",
  "connector_write_enabled",
  "connector_send_enabled",
  "provider_model_call_enabled",
  "shell_subprocess_execution_enabled",
  "browser_execution_enabled",
  "memory_write_enabled",
  "context_injection_authorized",
  "background_autonomy_enabled",
  "production_authority_enabled",
] as const;

const RUNTIME_ACTION_INBOX_BRIDGE_DENIED_FLAGS = [
  "action_execution_enabled",
  "arbitrary_command_execution_enabled",
  "provider_model_call_enabled",
  "browser_execution_enabled",
  "connector_write_enabled",
  "production_authority_enabled",
] as const;

const RUNTIME_ACTION_INBOX_BRIDGE_REQUIRED_NUMBERS = [
  "item_count",
  "pending_approval_count",
  "approved_pending_execution_count",
  "receipt_recorded_count",
  "blocked_count",
] as const;

const RUNTIME_ACTION_INBOX_BRIDGE_REQUIRED_ARRAYS = [
  "item_refs",
  "approval_envelope_refs",
  "pending_runtime_approval_refs",
  "execution_result_refs",
  "receipt_refs",
  "signed_evidence_refs",
  "evidence_refs",
  "runtime_parity_loop_stage_refs",
  "items",
  "evidence_timeline",
  "blocked_authority_refs",
] as const;

const RUNTIME_ACTION_INBOX_BRIDGE_ITEM_REQUIRED_STRINGS = [
  "invocation_ref",
  "action_envelope_ref",
  "adapter_id",
  "requested_authority",
  "status",
  "exact_scope_ref",
  "approval_ref",
  "safe_disable_posture_ref",
  "idempotency_ref",
  "policy_decision_ref",
  "payload_fingerprint_ref",
  "rollback_ref",
  "safe_disable_ref",
  "receipt_status",
  "signed_evidence_verification_status",
  "safe_summary",
] as const;

const RUNTIME_ACTION_INBOX_BRIDGE_ITEM_REQUIRED_ARRAYS = [
  "receipt_refs",
  "evidence_refs",
  "blocked_reason_refs",
  "blocked_authority_refs",
] as const;

const RUNTIME_ACTION_INBOX_BRIDGE_EVENT_KINDS = [
  "invocation_requested",
  "policy_decision",
  "approval_requested",
  "approval_accepted",
  "approval_denied",
  "approval_expired",
  "execution_started",
  "execution_completed",
  "execution_failed",
  "execution_timed_out",
  "receipt_recorded",
  "safe_disable_invoked",
] as const;

const ACTION_TOOL_CODE_CATALOG_DENIED_FLAGS = [
  "generic_tool_execution_enabled",
  "unrestricted_shell_execution_enabled",
  "browser_automation_enabled",
  "connector_write_enabled",
  "plugin_runtime_import_enabled",
  "remote_execution_enabled",
  "provider_model_call_enabled",
  "background_autonomy_enabled",
  "production_authority_enabled",
] as const;

const ACTION_TOOL_CODE_ENTRY_DENIED_FLAGS = [
  "generic_tool_execution_enabled",
  "unrestricted_shell_execution_enabled",
  "browser_automation_enabled",
  "connector_write_enabled",
  "plugin_runtime_import_enabled",
  "remote_execution_enabled",
  "provider_model_call_enabled",
  "background_autonomy_enabled",
  "production_authority_enabled",
] as const;

const ACTION_TOOL_CODE_REQUIRED_ARRAYS = [
  "entries",
  "unblock_prompts",
  "blocked_authority_refs",
] as const;

const ACTION_TOOL_CODE_ENTRY_REQUIRED_ARRAYS = [
  "route_refs",
  "cli_refs",
  "receipt_refs",
  "evidence_refs",
  "proof_refs",
  "blocked_authority_refs",
  "unblock_prompt_refs",
] as const;

const ACTION_WORK_QUEUE_LANE_IDS = [
  "ready_for_decision",
  "approved_local_task_lane",
  "blocked_by_authority",
  "expired_stale",
  "receipt_recorded",
  "proposal_only_no_execution_path",
] as const;

function isSafeRuntimeActionInboxBridgeReadModel(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    value.schema_version !== "governed-runtime-action-inbox-bridge.v1" ||
    value.contract_ref !==
      "contract-ref:governed-runtime-action-inbox-execution-bridge:v1" ||
    value.source !==
      "python_core_runtime_gateway_action_inbox_bridge_read_model" ||
    value.backend_owned !== true ||
    value.safe_refs_only !== true ||
    value.raw_content_included !== false ||
    !hasDeniedFlagsFalse(value, RUNTIME_ACTION_INBOX_BRIDGE_DENIED_FLAGS) ||
    !hasNumberFields(value, RUNTIME_ACTION_INBOX_BRIDGE_REQUIRED_NUMBERS) ||
    !hasStringFields(value, [
      "route_ref",
      "cli_ref",
      "runtime_parity_loop_api_ref",
      "runtime_parity_loop_cli_ref",
      "runtime_parity_loop_status",
      "status_cli_ref",
      "capabilities_cli_ref",
      "invocations_cli_ref",
      "receipts_cli_ref",
      "signed_evidence_cli_ref",
      "signed_evidence_verifier_cli_ref",
      "safe_disable_cli_ref",
      "status",
      "runtime_status_ref",
      "default_profile",
      "runtime_profile_status",
      "local_model_readiness",
      "command_runtime_readiness",
      "safe_disable_ref",
      "safe_disable_posture_ref",
      "safe_disable_summary",
      "next_safe_action",
      "operator_summary",
    ])
  ) {
    return false;
  }
  if (
    !RUNTIME_ACTION_INBOX_BRIDGE_REQUIRED_ARRAYS.every((field) =>
      Array.isArray(value[field]),
    )
  ) {
    return false;
  }
  const itemRefs = value.item_refs as unknown[];
  const approvalEnvelopeRefs = value.approval_envelope_refs as unknown[];
  const pendingApprovalRefs = value.pending_runtime_approval_refs as unknown[];
  const executionResultRefs = value.execution_result_refs as unknown[];
  const receiptRefs = value.receipt_refs as unknown[];
  const signedEvidenceRefs = value.signed_evidence_refs as unknown[];
  const evidenceRefs = value.evidence_refs as unknown[];
  const runtimeParityLoopStageRefs =
    value.runtime_parity_loop_stage_refs as unknown[];
  const items = value.items as unknown[];
  const evidenceTimeline = value.evidence_timeline as unknown[];
  const blockedAuthorityRefs = value.blocked_authority_refs as unknown[];
  return (
    value.item_count === items.length &&
    itemRefs.length === items.length &&
    itemRefs.every(
      (ref, index) =>
        isSafeActionWorkQueueRef(ref) &&
        ref ===
          ((items[index] as Record<string, unknown> | undefined)
            ?.invocation_ref ?? null),
    ) &&
    isSafeActionWorkQueueRef(value.runtime_status_ref) &&
    isSafeActionWorkQueueRef(value.safe_disable_ref) &&
    isSafeActionWorkQueueRef(value.safe_disable_posture_ref) &&
    typeof value.safe_disable_active === "boolean" &&
    approvalEnvelopeRefs.every(isSafeActionWorkQueueRef) &&
    pendingApprovalRefs.every(isSafeActionWorkQueueRef) &&
    executionResultRefs.every(isSafeActionWorkQueueRef) &&
    receiptRefs.every(isSafeActionWorkQueueRef) &&
    signedEvidenceRefs.every(isSafeActionWorkQueueRef) &&
    evidenceRefs.every(isSafeActionWorkQueueRef) &&
    runtimeParityLoopStageRefs.every(isSafeActionWorkQueueRef) &&
    blockedAuthorityRefs.every(isSafeActionWorkQueueRef) &&
    items.every(isSafeRuntimeActionInboxBridgeItem) &&
    evidenceTimeline.every(isSafeRuntimeEvidenceTimelineItem)
  );
}

function isSafeRuntimeActionInboxBridgeItem(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    !hasStringFields(
      value,
      RUNTIME_ACTION_INBOX_BRIDGE_ITEM_REQUIRED_STRINGS,
    ) ||
    !hasStringArrays(
      value,
      RUNTIME_ACTION_INBOX_BRIDGE_ITEM_REQUIRED_ARRAYS,
    )
  ) {
    return false;
  }
  const commandIntent = value.command_intent;
  const approvalDecisionRef = value.approval_decision_ref;
  const approvalValidationRef = value.approval_validation_ref;
  const receiptRef = value.receipt_ref;
  const executionResultRef = value.execution_result_ref;
  const signedEvidenceRef = value.signed_evidence_ref;
  const signedEvidenceVerifierRef = value.signed_evidence_verifier_ref;
  return (
    (commandIntent === null ||
      commandIntent === undefined ||
      typeof commandIntent === "string") &&
    (approvalDecisionRef === null ||
      approvalDecisionRef === undefined ||
      isSafeActionWorkQueueRef(approvalDecisionRef)) &&
    (approvalValidationRef === null ||
      approvalValidationRef === undefined ||
      isSafeActionWorkQueueRef(approvalValidationRef)) &&
    (receiptRef === null ||
      receiptRef === undefined ||
      isSafeActionWorkQueueRef(receiptRef)) &&
    (executionResultRef === null ||
      executionResultRef === undefined ||
      isSafeActionWorkQueueRef(executionResultRef)) &&
    (signedEvidenceRef === null ||
      signedEvidenceRef === undefined ||
      isSafeActionWorkQueueRef(signedEvidenceRef)) &&
    (signedEvidenceVerifierRef === null ||
      signedEvidenceVerifierRef === undefined ||
      isSafeActionWorkQueueRef(signedEvidenceVerifierRef)) &&
    typeof value.approval_validated === "boolean" &&
    typeof value.execution_performed === "boolean" &&
    typeof value.timed_out === "boolean" &&
    value.command_output_persisted === false &&
    (value.exit_code === null ||
      value.exit_code === undefined ||
      typeof value.exit_code === "number") &&
    isSafeActionWorkQueueRef(value.invocation_ref) &&
    isSafeActionWorkQueueRef(value.action_envelope_ref) &&
    isSafeActionWorkQueueRef(value.exact_scope_ref) &&
    isSafeActionWorkQueueRef(value.approval_ref) &&
    isSafeActionWorkQueueRef(value.safe_disable_posture_ref) &&
    isSafeActionWorkQueueRef(value.idempotency_ref) &&
    isSafeActionWorkQueueRef(value.policy_decision_ref) &&
    isSafeActionWorkQueueRef(value.payload_fingerprint_ref) &&
    isSafeActionWorkQueueRef(value.rollback_ref) &&
    isSafeActionWorkQueueRef(value.safe_disable_ref) &&
    (value.receipt_refs as string[]).every(isSafeActionWorkQueueRef) &&
    (value.evidence_refs as string[]).every(isSafeActionWorkQueueRef) &&
    (value.blocked_reason_refs as string[]).every(isSafeActionWorkQueueRef) &&
    (value.blocked_authority_refs as string[]).every(isSafeActionWorkQueueRef)
  );
}

function isSafeRuntimeEvidenceTimelineItem(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    !hasStringFields(value, [
      "event_ref",
      "event_kind",
      "invocation_ref",
      "safe_summary",
    ]) ||
    !Array.isArray(value.evidence_refs)
  ) {
    return false;
  }
  const receiptRef = value.receipt_ref;
  const policyDecisionRef = value.policy_decision_ref;
  const actionEnvelopeRef = value.action_envelope_ref;
  return (
    isSafeActionWorkQueueRef(value.event_ref) &&
    RUNTIME_ACTION_INBOX_BRIDGE_EVENT_KINDS.includes(
      value.event_kind as (typeof RUNTIME_ACTION_INBOX_BRIDGE_EVENT_KINDS)[number],
    ) &&
    isSafeActionWorkQueueRef(value.invocation_ref) &&
    (receiptRef === null ||
      receiptRef === undefined ||
      isSafeActionWorkQueueRef(receiptRef)) &&
    (policyDecisionRef === null ||
      policyDecisionRef === undefined ||
      isSafeActionWorkQueueRef(policyDecisionRef)) &&
    (actionEnvelopeRef === null ||
      actionEnvelopeRef === undefined ||
      isSafeActionWorkQueueRef(actionEnvelopeRef)) &&
    (value.evidence_refs as string[]).every(isSafeActionWorkQueueRef)
  );
}

function isSafeActionToolCodeCatalogReadModel(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    value.schema_version !== "uaa-action-tool-code-lane-catalog.v1" ||
    value.contract_ref !==
      "contract-ref:goatcitadel-catchup-action-tool-code-catalog:v1" ||
    value.source !==
      "python_core_action_tool_code_lane_catalog_read_model" ||
    value.backend_owned !== true ||
    value.control_center_presentation_only !== true ||
    value.safe_refs_only !== true ||
    value.raw_content_included !== false ||
    !hasDeniedFlagsFalse(value, ACTION_TOOL_CODE_CATALOG_DENIED_FLAGS) ||
    !hasStringFields(value, [
      "catalog_ref",
      "route_ref",
      "cli_ref",
      "status",
      "next_safe_action",
      "operator_summary",
    ]) ||
    !hasNumberFields(value, [
      "entry_count",
      "preview_only_count",
      "exact_local_mutation_count",
      "exact_runtime_lane_count",
      "proposal_only_count",
      "blocked_count",
    ]) ||
    !hasStringArrays(value, ["blocked_authority_refs"]) ||
    !ACTION_TOOL_CODE_REQUIRED_ARRAYS.every((field) =>
      Array.isArray(value[field]),
    )
  ) {
    return false;
  }
  const entries = value.entries as unknown[];
  const prompts = value.unblock_prompts as unknown[];
  return (
    value.entry_count === entries.length &&
    value.preview_only_count ===
      entries.filter(
        (entry) =>
          isPlainRecord(entry) && entry.status === "implemented_preview_only",
      ).length &&
    value.exact_local_mutation_count ===
      entries.filter(
        (entry) =>
          isPlainRecord(entry) &&
          entry.exact_local_mutation_available === true,
      ).length &&
    value.exact_runtime_lane_count ===
      entries.filter(
        (entry) =>
          isPlainRecord(entry) &&
          entry.exact_runtime_lane_available === true,
      ).length &&
    value.proposal_only_count ===
      entries.filter(
        (entry) => isPlainRecord(entry) && entry.proposal_only === true,
      ).length &&
    value.blocked_count ===
      entries.filter(
        (entry) =>
          isPlainRecord(entry) &&
          entry.status === "blocked_missing_exact_authority",
      ).length &&
    isSafeActionWorkQueueRef(value.catalog_ref) &&
    (value.blocked_authority_refs as string[]).every(isSafeActionWorkQueueRef) &&
    entries.every(isSafeActionToolCodeLaneEntry) &&
    prompts.every(isSafeActionToolCodeUnblockPrompt)
  );
}

function isSafeActionToolCodeLaneEntry(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    !hasStringFields(value, [
      "capability_id",
      "capability_ref",
      "lane_ref",
      "label",
      "capability_kind",
      "surface",
      "status",
      "side_effect_class",
      "required_approval_scope",
      "eligibility_reason",
      "blocked_reason",
      "receipt_requirement",
      "rollback_or_safe_disable_posture",
    ]) ||
    !hasStringArrays(value, ACTION_TOOL_CODE_ENTRY_REQUIRED_ARRAYS) ||
    !hasDeniedFlagsFalse(value, ACTION_TOOL_CODE_ENTRY_DENIED_FLAGS)
  ) {
    return false;
  }
  return (
    isSafeActionWorkQueueRef(value.capability_ref) &&
    isSafeActionWorkQueueRef(value.lane_ref) &&
    typeof value.operator_visible === "boolean" &&
    value.operator_visible === true &&
    typeof value.inspectable_now === "boolean" &&
    value.inspectable_now === true &&
    typeof value.proposal_only === "boolean" &&
    typeof value.exact_local_mutation_available === "boolean" &&
    typeof value.exact_runtime_lane_available === "boolean" &&
    (value.receipt_refs as string[]).every(isSafeActionWorkQueueRef) &&
    (value.evidence_refs as string[]).every(isSafeActionWorkQueueRef) &&
    (value.proof_refs as string[]).every(isSafeActionWorkQueueRef) &&
    (value.blocked_authority_refs as string[]).every(isSafeActionWorkQueueRef) &&
    (value.unblock_prompt_refs as string[]).every(isSafeActionWorkQueueRef)
  );
}

function isSafeActionToolCodeUnblockPrompt(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const prompt = String(value.copy_ready_prompt ?? "").toLowerCase();
  return (
    hasStringFields(value, [
      "prompt_ref",
      "title",
      "target_capability_ref",
      "copy_ready_prompt",
    ]) &&
    hasStringArrays(value, ["blocked_authority_refs"]) &&
    isSafeActionWorkQueueRef(value.prompt_ref) &&
    isSafeActionWorkQueueRef(value.target_capability_ref) &&
    (value.blocked_authority_refs as string[]).every(isSafeActionWorkQueueRef) &&
    !prompt.includes("/users/") &&
    !prompt.includes("raw_prompt") &&
    !prompt.includes("raw_response") &&
    !prompt.includes("provider_payload") &&
    !prompt.includes("credential material") &&
    !prompt.includes("secret")
  );
}

function isSafeActionInboxWorkQueueReadModel(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    value.schema_version !== "action-inbox-work-queue.v1" ||
    value.contract_ref !==
      "contract-ref:usable-authority-action-inbox-work-queue:v1" ||
    value.source !== "python_core_action_inbox_work_queue_read_model" ||
    value.backend_owned !== true ||
    value.local_read_model_only !== true ||
    value.safe_refs_only !== true ||
    value.raw_content_included !== false ||
    !hasDeniedFlagsFalse(value, ACTION_WORK_QUEUE_DENIED_FLAGS)
  ) {
    return false;
  }
  if (
    typeof value.item_count !== "number" ||
    typeof value.operator_actionable_count !== "number" ||
    typeof value.ready_for_decision_count !== "number" ||
    typeof value.approved_local_task_count !== "number" ||
    typeof value.proposal_only_count !== "number" ||
    typeof value.blocked_count !== "number" ||
    typeof value.receipt_recorded_count !== "number" ||
    typeof value.lane_count !== "number" ||
    typeof value.work_item_count !== "number" ||
    typeof value.unsafe_ref_omitted_count !== "number" ||
    !Array.isArray(value.lanes) ||
    !Array.isArray(value.work_items) ||
    !Array.isArray(value.work_item_refs) ||
    !Array.isArray(value.unsafe_ref_blocked_state_refs) ||
    !Array.isArray(value.blocked_authority_refs)
  ) {
    return false;
  }
  const lanes = value.lanes;
  const workItems = value.work_items;
  const workItemRefs = value.work_item_refs;
  if (value.lane_count !== lanes.length) {
    return false;
  }
  if (value.work_item_count !== workItems.length) {
    return false;
  }
  if (
    !workItemRefs.every(
      (ref, index) =>
        typeof ref === "string" &&
        isSafeActionWorkQueueRef(ref) &&
        ref ===
          ((workItems[index] as Record<string, unknown> | undefined)
            ?.item_ref ?? null),
    )
  ) {
    return false;
  }
  return (
    value.fake_mutation_controls_exposed === false &&
    value.unsafe_ref_blocked_state_refs.every(isSafeActionWorkQueueRef) &&
    value.blocked_authority_refs.every(isSafeActionWorkQueueRef) &&
    hasStringFields(value, [
      "queue_ref",
      "route_ref",
      "cli_ref",
      "proof_route_ref",
      "next_safe_action",
      "operator_summary",
      "tier_posture",
      "mutating_controls_posture",
    ]) &&
    lanes.every(isSafeActionInboxWorkQueueLane) &&
    workItems.every(isSafeActionInboxWorkQueueWorkItem) &&
    (value.next_item === null ||
      value.next_item === undefined ||
      isSafeActionInboxWorkQueueNextItem(value.next_item))
  );
}

function isSafeActionInboxWorkQueueLane(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    typeof value.lane_id === "string" &&
    ACTION_WORK_QUEUE_LANE_IDS.includes(
      value.lane_id as (typeof ACTION_WORK_QUEUE_LANE_IDS)[number],
    ) &&
    hasStringFields(value, [
      "lane_ref",
      "label",
      "status",
      "safe_summary",
      "available_action",
      "tier",
    ]) &&
    typeof value.count === "number" &&
    Array.isArray(value.item_refs) &&
    value.item_refs.every(isSafeActionWorkQueueRef) &&
    Array.isArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.every(isSafeActionWorkQueueRef)
  );
}

function isSafeActionInboxWorkQueueNextItem(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    typeof value.lane_id === "string" &&
    ACTION_WORK_QUEUE_LANE_IDS.includes(
      value.lane_id as (typeof ACTION_WORK_QUEUE_LANE_IDS)[number],
    ) &&
    hasStringFields(value, [
      "item_ref",
      "title",
      "lane_label",
      "status",
      "priority",
      "risk_class",
      "action_kind",
      "available_action",
      "next_safe_action",
      "proof_ref",
    ]) &&
    isSafeActionWorkQueueRef(value.item_ref) &&
    isSafeActionWorkQueueRef(value.proof_ref) &&
    typeof value.approval_required === "boolean" &&
    typeof value.local_task_commit_eligible === "boolean" &&
    Array.isArray(value.expected_receipt_refs) &&
    value.expected_receipt_refs.every(isSafeActionWorkQueueRef) &&
    Array.isArray(value.receipt_refs) &&
    value.receipt_refs.every(isSafeActionWorkQueueRef) &&
    Array.isArray(value.evidence_refs) &&
    value.evidence_refs.every(isSafeActionWorkQueueRef) &&
    Array.isArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.every(isSafeActionWorkQueueRef) &&
    isOptionalSafeActionWorkQueueRoute(value.local_task_commit_route_ref) &&
    isOptionalSafeActionWorkQueueRef(value.approval_envelope_ref) &&
    isOptionalSafeActionWorkQueueRef(value.rollback_ref) &&
    isOptionalSafeActionWorkQueueRef(value.safe_disable_ref)
  );
}

function isSafeActionInboxWorkQueueWorkItem(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    !hasStringArrays(value, [
      "expected_receipt_refs",
      "receipt_refs",
      "evidence_refs",
      "blocked_authority_refs",
    ])
  ) {
    return false;
  }
  const expectedReceiptRefs = value.expected_receipt_refs as string[];
  const receiptRefs = value.receipt_refs as string[];
  const evidenceRefs = value.evidence_refs as string[];
  const blockedAuthorityRefs = value.blocked_authority_refs as string[];
  return (
    typeof value.lane_id === "string" &&
    ACTION_WORK_QUEUE_LANE_IDS.includes(
      value.lane_id as (typeof ACTION_WORK_QUEUE_LANE_IDS)[number],
    ) &&
    hasStringFields(value, [
      "item_ref",
      "title",
      "lane_label",
      "status",
      "priority",
      "risk_class",
      "action_kind",
      "side_effect_class",
      "safe_summary",
      "approval_posture",
      "receipt_posture",
      "mutation_control_posture",
      "next_safe_action",
      "proof_ref",
    ]) &&
    isSafeActionWorkQueueRef(value.item_ref) &&
    isSafeActionWorkQueueRef(value.proof_ref) &&
    typeof value.approval_required === "boolean" &&
    typeof value.operator_actionable === "boolean" &&
    typeof value.local_task_commit_eligible === "boolean" &&
    value.fake_mutation_control_exposed === false &&
    isOptionalSafeActionWorkQueueRef(value.approval_envelope_ref) &&
    isOptionalSafeActionWorkQueueRoute(value.local_task_commit_route_ref) &&
    isOptionalSafeActionWorkQueueRef(value.rollback_ref) &&
    isOptionalSafeActionWorkQueueRef(value.safe_disable_ref) &&
    expectedReceiptRefs.every(isSafeActionWorkQueueRef) &&
    receiptRefs.every(isSafeActionWorkQueueRef) &&
    evidenceRefs.every(isSafeActionWorkQueueRef) &&
    blockedAuthorityRefs.every(isSafeActionWorkQueueRef)
  );
}

const ACTION_WORK_QUEUE_REF_RE = /^[A-Za-z0-9][A-Za-z0-9:_./#=-]{0,239}$/;
const ACTION_WORK_QUEUE_ROUTE_RE =
  /^(GET|POST) \/control-center\/[A-Za-z0-9_./{}-]{1,180}$/;

function isSafeActionWorkQueueRef(value: unknown): value is string {
  if (typeof value !== "string") {
    return false;
  }
  const lowered = value.toLowerCase();
  return (
    ACTION_WORK_QUEUE_REF_RE.test(value) &&
    !lowered.includes("/users/") &&
    !lowered.includes("raw_prompt") &&
    !lowered.includes("raw_response") &&
    !lowered.includes("provider_payload") &&
    !lowered.includes("credential") &&
    !lowered.includes("secret")
  );
}

function isOptionalSafeActionWorkQueueRef(value: unknown): boolean {
  return value === null || value === undefined || isSafeActionWorkQueueRef(value);
}

function isOptionalSafeActionWorkQueueRoute(value: unknown): boolean {
  return (
    value === null ||
    value === undefined ||
    (typeof value === "string" && ACTION_WORK_QUEUE_ROUTE_RE.test(value))
  );
}

function isSafeActionInboxDecisionLaneReadModel(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    value.contract_ref ===
      "contract-ref:product-loop-005-action-inbox-decision-lanes:v1" &&
    value.backend_owned === true &&
    value.local_read_model_only === true &&
    value.safe_refs_only === true &&
    value.raw_content_included === false &&
    value.source === "python_core_action_inbox_decision_lane_read_model" &&
    value.missing_envelope_fields_fail_safe === true &&
    value.cost_posture_visible_before_approval === true &&
    value.provider_authority_visible_before_approval === true &&
    value.approval_scope_visible_before_approval === true &&
    value.expected_receipts_visible_before_approval === true &&
    value.action_execution_enabled === false &&
    value.connector_write_enabled === false &&
    value.shell_subprocess_execution_enabled === false &&
    value.browser_execution_enabled === false &&
    value.provider_model_call_enabled === false &&
    value.memory_write_enabled === false &&
    value.context_injection_authorized === false &&
    value.hidden_memory_write_authorized === false &&
    value.production_authority_enabled === false &&
    value.approval_alone_executes === false &&
    hasStringArrays(value, ACTION_DECISION_LANE_REQUIRED_STRING_ARRAYS) &&
    ACTION_DECISION_LANE_ORDER.length ===
      (value.lane_order as string[]).length &&
    ACTION_DECISION_LANE_ORDER.every(
      (laneId, index) => laneId === (value.lane_order as string[])[index],
    ) &&
    Array.isArray(value.lanes) &&
    value.lanes.every(isSafeActionInboxDecisionLane) &&
    Array.isArray(value.items) &&
    value.items.every(isSafeActionInboxDecisionLaneItem)
  );
}

function isSafeActionInboxDecisionLane(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    hasStringFields(value, [
      "lane_id",
      "label",
      "status",
      "safe_summary",
      "next_safe_action",
    ]) &&
    typeof value.count === "number" &&
    hasStringArrays(value, ["item_refs", "blocked_state_refs"]) &&
    value.approval_alone_executes === false &&
    value.action_execution_enabled === false
  );
}

function isSafeActionInboxDecisionLaneItem(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    hasStringFields(value, ACTION_DECISION_LANE_ITEM_REQUIRED_STRINGS) &&
    hasNumberFields(value, ACTION_DECISION_LANE_ITEM_REQUIRED_NUMBERS) &&
    hasStringArrays(value, ACTION_DECISION_LANE_ITEM_REQUIRED_ARRAYS) &&
    value.backend_owned === true &&
    value.safe_refs_only === true &&
    value.raw_content_included === false &&
    typeof value.approval_required === "boolean" &&
    value.expected_receipt_refs_visible === true &&
    typeof value.unknown_paid_cost_requires_explicit_approval === "boolean" &&
    typeof value.frontier_usage_claimed === "boolean" &&
    typeof value.cost_telemetry_complete === "boolean" &&
    typeof value.provider_model_refs_present === "boolean" &&
    hasDeniedFlagsFalse(value, ACTION_DECISION_LANE_ITEM_DENIED_FLAGS)
  );
}

function normalizeFounderMemoryWorkbench(
  value: FounderLoopMemoryWorkbench | undefined,
): { value: FounderLoopMemoryWorkbench; usedFallback: boolean } {
  const merged = mergeMissingFields(
    mockControlCenterData.founderMemoryWorkbench,
    value,
  );
  if (
    value !== undefined &&
    isPlainRecord(value) &&
    isPlainRecord(merged.value)
  ) {
    const workbenchWithoutMockPosture = {
      ...(merged.value as Record<string, unknown>),
    };
    if (Object.prototype.hasOwnProperty.call(value, "lifecycle_posture")) {
      workbenchWithoutMockPosture.lifecycle_posture = (
        value as Record<string, unknown>
      ).lifecycle_posture;
    } else {
      delete workbenchWithoutMockPosture.lifecycle_posture;
    }
    if (Object.prototype.hasOwnProperty.call(value, "learning_posture")) {
      workbenchWithoutMockPosture.learning_posture = (
        value as Record<string, unknown>
      ).learning_posture;
    } else {
      delete workbenchWithoutMockPosture.learning_posture;
    }
    return {
      value:
        workbenchWithoutMockPosture as unknown as FounderLoopMemoryWorkbench,
      usedFallback: merged.usedFallback,
    };
  }
  return merged;
}

function isPlainRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

async function readJsonSafely(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return undefined;
  }
}

function localModelsFailureStatus(
  statusCode: number,
  data: unknown,
  checkedAt: string,
): LocalModelsInspectionStatus {
  const state = statusCode === 401 ? "denied" : "blocked";
  const reasonCode =
    statusCode === 401
      ? "LOCAL_MODELS_BEARER_REQUIRED"
      : "LOCAL_MODELS_ROUTE_BLOCKED";
  return {
    state,
    routeRef: API_ENDPOINTS.localModels,
    checkedAt,
    safeMessage: sanitizeForDisplay(
      extractErrorMessage(data, "Local model route is blocked or disabled."),
    ),
    modelIds: [],
    statusCode,
    reasonCodes: [reasonCode],
  };
}

function extractModelIds(data: unknown): string[] {
  const candidate = unwrapEnvelope(data);
  if (typeof candidate !== "object" || candidate === null) {
    return [];
  }
  const record = candidate as Record<string, unknown>;
  const list = Array.isArray(record.data)
    ? record.data
    : Array.isArray(record.models)
      ? record.models
      : [];
  return list
    .map((item) => {
      if (typeof item === "string") {
        return item;
      }
      if (typeof item === "object" && item !== null) {
        const id = (item as Record<string, unknown>).id;
        return typeof id === "string" ? id : undefined;
      }
      return undefined;
    })
    .filter((id): id is string => Boolean(id));
}

function unwrapEnvelope(data: unknown): unknown {
  if (typeof data !== "object" || data === null) {
    return data;
  }
  const record = data as Record<string, unknown>;
  if ("result" in record) {
    return record.result;
  }
  if ("data" in record && ("ok" in record || "success" in record)) {
    return record.data;
  }
  return data;
}

function extractErrorMessage(data: unknown, fallback: string): string {
  if (typeof data !== "object" || data === null) {
    return fallback;
  }
  const record = data as Record<string, unknown>;
  const detail = record.detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (typeof detail === "object" && detail !== null) {
    const safeMessage = (detail as Record<string, unknown>).safe_message;
    if (typeof safeMessage === "string") {
      return safeMessage;
    }
    const message = (detail as Record<string, unknown>).message;
    if (typeof message === "string") {
      return message;
    }
  }
  const error = record.error;
  if (typeof error === "object" && error !== null) {
    const message = (error as Record<string, unknown>).message;
    if (typeof message === "string") {
      return message;
    }
  }
  return fallback;
}
