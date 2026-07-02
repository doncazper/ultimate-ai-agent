import { mockControlCenterData } from "../mocks/controlCenterData";
import type {
  ActionPreviewDecision,
  ActionPreviewRequest,
  BackendConnectionSummary,
  ControlCenterDashboardSnapshot,
  ControlCenterData,
  ControlCenterLocalModelsStatus,
  ControlCenterManifest,
  ControlCenterSettingsStatus,
  ControlCenterStatus,
  FounderLoopActionsInbox,
  FounderLoopMorningBriefing,
  FounderLoopSourceReadiness,
  FounderLoopStorageStatus,
  FounderLoopTodaySummary,
  LocalModelsInspectionStatus,
  ProviderCatalog,
  RedactedLocalChatProbeStatus,
  ResultEnvelope,
  RunAttachedApprovalQueue,
  RuntimeCapabilityMatrix,
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

export function setLocalApiBearerForSession(value: string | null): void {
  const trimmed = value?.trim() ?? "";
  sessionLocalApiBearer = trimmed.length > 0 ? trimmed : null;
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

async function readEnvelope<T>(endpoint: string): Promise<T> {
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

  const results = await Promise.allSettled([
    readEnvelope<ControlCenterManifest>(API_ENDPOINTS.controlCenterManifest),
    readEnvelope<ControlCenterDashboardSnapshot>(
      API_ENDPOINTS.controlCenterDashboard,
    ),
    readEnvelope<ControlCenterStatus>(API_ENDPOINTS.controlCenterStatus),
    readEnvelope<ApiRouteInventory>(API_ENDPOINTS.controlCenterRoutes),
    readEnvelope<RuntimeReadinessReport>(API_ENDPOINTS.runtimeReadiness),
    readEnvelope<RuntimeCapabilityMatrix>(
      API_ENDPOINTS.runtimeCapabilityMatrix,
    ),
    readEnvelope<unknown>(API_ENDPOINTS.setupAssistantSummary),
    readEnvelope<ProviderCatalog>(API_ENDPOINTS.providerSetupGuide),
    readEnvelope<ControlCenterSettingsStatus>(
      API_ENDPOINTS.controlCenterSettingsStatus,
    ),
    readEnvelope<ControlCenterLocalModelsStatus>(
      API_ENDPOINTS.controlCenterLocalModelsStatus,
    ),
    readEnvelope<FounderLoopTodaySummary>(API_ENDPOINTS.founderTodaySummary),
    readEnvelope<FounderLoopEvidenceTimelineIndex>(
      API_ENDPOINTS.founderEvidenceTimeline,
    ),
    readEnvelope<FounderLoopMemoryReview>(API_ENDPOINTS.founderMemoryReview),
    readEnvelope<FounderLoopMemoryWorkbench>(
      API_ENDPOINTS.founderMemoryWorkbench,
    ),
    readEnvelope<FounderLoopMemoryContextPacks>(
      API_ENDPOINTS.founderMemoryContextPacks,
    ),
    readEnvelope<FounderLoopMemoryRetrievalDiagnostics>(
      API_ENDPOINTS.founderMemoryRetrievalDiagnostics,
    ),
    readEnvelope<FounderLoopMemoryCitationIntegrity>(
      API_ENDPOINTS.founderMemoryCitationIntegrity,
    ),
    readEnvelope<FounderLoopMemoryQualityIssues>(
      API_ENDPOINTS.founderMemoryQualityIssues,
    ),
    readEnvelope<FounderLoopMemoryMaintenanceRuns>(
      API_ENDPOINTS.founderMemoryMaintenanceRuns,
    ),
    readEnvelope<FounderLoopMemoryContextManifest>(
      API_ENDPOINTS.founderMemoryContextManifest,
    ),
    readEnvelope<FounderLoopActionsInbox>(API_ENDPOINTS.founderActionsInbox),
    readEnvelope<FounderLoopMorningBriefing>(
      API_ENDPOINTS.founderMorningBriefing,
    ),
    readEnvelope<FounderLoopSourceReadiness>(
      API_ENDPOINTS.founderSourceReadiness,
    ),
    readEnvelope<FounderLoopStorageStatus>(API_ENDPOINTS.founderStorageStatus),
    readEnvelope<ControlCenterDashboardSnapshot["approval_summary"]>(
      API_ENDPOINTS.approvalSummary,
    ),
    readEnvelope<RunAttachedApprovalQueue>(API_ENDPOINTS.approvalQueue),
    readEnvelope<ControlCenterDashboardSnapshot["runtime_readiness_summary"]>(
      API_ENDPOINTS.runtimeReadinessSummary,
    ),
    readEnvelope<ControlCenterDashboardSnapshot["foundation_gate_summary"]>(
      API_ENDPOINTS.foundationGateSummary,
    ),
  ] as const);

  const manifest = fulfilledValue(results[0]);
  const dashboard = fulfilledValue(results[1]);
  const normalizedDashboard = normalizeControlCenterDashboard(dashboard);
  const status = fulfilledValue(results[2]);
  const routes = fulfilledValue(results[3]);
  const runtimeReadiness = fulfilledValue(results[4]);
  const capabilityMatrix = fulfilledValue(results[5]);
  const setupAssistantSource = fulfilledValue(results[6]);
  const setupAssistant = normalizeMacOSSetupAssistant(
    setupAssistantSource,
    mockControlCenterData.macosSetupAssistant,
  );
  const providerCatalog = fulfilledValue(results[7]);
  const controlCenterSettingsStatus = fulfilledValue(results[8]);
  const controlCenterLocalModelsStatus = fulfilledValue(results[9]);
  const founderToday = fulfilledValue(results[10]);
  const founderEvidenceTimeline = fulfilledValue(results[11]);
  const founderMemoryReview = fulfilledValue(results[12]);
  const founderMemoryWorkbench = fulfilledValue(results[13]);
  const founderMemoryContextPacks = fulfilledValue(results[14]);
  const founderMemoryRetrievalDiagnostics = fulfilledValue(results[15]);
  const founderMemoryCitationIntegrity = fulfilledValue(results[16]);
  const founderMemoryQualityIssues = fulfilledValue(results[17]);
  const founderMemoryMaintenanceRuns = fulfilledValue(results[18]);
  const founderMemoryContextManifest = fulfilledValue(results[19]);
  const founderActionsInbox = fulfilledValue(results[20]);
  const founderMorningBriefing = fulfilledValue(results[21]);
  const founderSourceReadiness = fulfilledValue(results[22]);
  const founderStorageStatus = fulfilledValue(results[23]);
  const approvalSummary = fulfilledValue(results[24]);
  const approvalQueue = fulfilledValue(results[25]);
  const runtimeReadinessSummary = fulfilledValue(results[26]);
  const foundationGateSummary = fulfilledValue(results[27]);
  const normalizedFounderToday = normalizeFounderToday(founderToday);
  const normalizedFounderEvidenceTimeline = normalizeFounderEvidenceTimeline(
    founderEvidenceTimeline,
  );
  const normalizedFounderActionsInbox =
    normalizeFounderActionsInbox(founderActionsInbox);
  const normalizedFounderMemoryReview = mergeMissingFields(
    mockControlCenterData.founderMemoryReview,
    founderMemoryReview,
  );
  const normalizedFounderMemoryWorkbench = normalizeFounderMemoryWorkbench(
    founderMemoryWorkbench,
  );
  const normalizedFounderMemoryContextPacks = mergeMissingFields(
    mockControlCenterData.founderMemoryContextPacks,
    founderMemoryContextPacks,
  );
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
  const normalizedFounderMemoryContextManifest = mergeMissingFields(
    mockControlCenterData.founderMemoryContextManifest,
    founderMemoryContextManifest,
  );
  const normalizedFounderMorningBriefing = normalizeFounderMorningBriefing(
    founderMorningBriefing,
  );
  const normalizedFounderSourceReadiness = mergeMissingFields(
    mockControlCenterData.founderSourceReadiness,
    founderSourceReadiness,
  );
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
    normalizedFounderSourceReadiness.usedFallback;
  const providerCredentialReadinessFallbackUsed =
    normalizedDashboard.usedFallback;
  const approvalQueueEndpointFallbackUsed = approvalQueue === undefined;
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
    setupAssistantSource === undefined ||
    providerCatalog === undefined ||
    controlCenterSettingsStatus === undefined ||
    controlCenterLocalModelsStatus === undefined ||
    founderStorageStatus === undefined;
  const fulfilledCount = results.filter(
    (result) => result.status === "fulfilled",
  ).length;
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
        founderEvidenceTimeline:
          normalizeFounderEvidenceTimeline(undefined).value,
        founderActionsInbox: normalizeFounderActionsInbox(undefined).value,
        founderMorningBriefing:
          normalizeFounderMorningBriefing(undefined).value,
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
    m15Review: mockControlCenterData.m15Review,
    runAttachedApprovalQueue:
      approvalQueue ?? mockControlCenterData.runAttachedApprovalQueue,
    m16Trace: mockControlCenterData.m16Trace,
    m17Knowledge: mockControlCenterData.m17Knowledge,
    m18Runtime: mockControlCenterData.m18Runtime,
    m36FileReview: mockControlCenterData.m36FileReview,
    m39ContextProposals: mockControlCenterData.m39ContextProposals,
    macosSetupAssistant: setupAssistant,
    providerCatalog: providerCatalog ?? mockControlCenterData.providerCatalog,
    settingsStatus:
      controlCenterSettingsStatus ?? mockControlCenterData.settingsStatus,
    localModelsStatus:
      controlCenterLocalModelsStatus ?? mockControlCenterData.localModelsStatus,
    founderToday: normalizedFounderToday.value,
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
    crmM1FixtureShell: mockControlCenterData.crmM1FixtureShell,
    source: "api",
    connection: mockControlCenterData.connection,
  };

  if (
    fulfilledCount === results.length &&
    !founderLoopFieldFallbackUsed &&
    !providerCredentialReadinessFallbackUsed &&
    !dashboardSummaryEndpointFallbackUsed
  ) {
    return withConnection(data, {
      state: "online",
      safeMessage:
        "Live data came from local read-only/preview-only backend API routes.",
      usingMockData: false,
      warnings: [],
    });
  }

  const mockFallbackUsed =
    generalMockFallbackUsed ||
    founderLoopFieldFallbackUsed ||
    providerCredentialReadinessFallbackUsed ||
    approvalQueueEndpointFallbackUsed;

  return withConnection(data, {
    state: "degraded",
    safeMessage: providerCredentialReadinessFallbackUsed
      ? "Provider credential and cost posture was unavailable or unsafe; non-authoritative mock fallback kept provider readiness blocked."
      : founderLoopFieldFallbackUsed
        ? "Some local backend summaries or fields were unavailable; non-authoritative mock fallback filled missing Founder Loop panels."
        : approvalQueueEndpointFallbackUsed
          ? "Run-attached approval queue endpoint was unavailable; non-authoritative mock fallback is shown without approval authority."
        : dashboardSummaryEndpointFallbackUsed
          ? "Some dedicated Control Center summary routes were unavailable; backend dashboard summaries kept the visible state bounded."
          : "Some local backend summaries were unavailable; non-authoritative mock fallback filled missing panels.",
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
      ...(founderLoopFieldFallbackUsed
        ? ["PARTIAL_FOUNDER_LOOP_FIELD_FALLBACK"]
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
  return `idempotency-ref:control-center-chat-turn:${safeChatSuffix(turnRef)}:${safeChatSuffix(request?.safe_summary_ref ?? "summary")}`;
}

function chatHandoffIdempotencyRef(
  turnRef: string,
  target: ChatHandoffTarget,
  request?: ChatHandoffRequest,
): string {
  return `idempotency-ref:control-center-chat-handoff:${target}:${safeChatSuffix(turnRef)}:${safeChatSuffix(request?.decision_reason_ref ?? "decision")}`;
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
      reasonCodes: ["LOCAL_CHAT_REDACTED_PROBE_READY"],
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
    delete fallbackWithoutDigest.unified_work_thread_read_model;
    delete fallbackWithoutDigest.unified_work_thread_contract_ref;
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
  return {
    value: normalized as unknown as FounderLoopEvidenceTimelineIndex,
    usedFallback: merged.usedFallback,
  };
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
    !hasDeniedFlagsFalse(value, FOUNDER_LOOP_PRODUCT_PROOF_DENIED_FLAGS) ||
    !hasStringArrays(value, FOUNDER_LOOP_PRODUCT_PROOF_REQUIRED_ARRAYS) ||
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
  if (
    value === undefined ||
    !isSafeActionInboxDecisionLaneReadModel(
      valueRecord.action_inbox_decision_lane_read_model,
    )
  ) {
    const withoutMockLanes = {
      ...(merged.value as unknown as Record<string, unknown>),
    };
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

function isSafeActionInboxDecisionLaneReadModel(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    value.backend_owned === true &&
    value.safe_refs_only === true &&
    value.raw_content_included === false &&
    value.source === "python_core_action_inbox_decision_lane_read_model" &&
    value.action_execution_enabled === false &&
    value.connector_write_enabled === false &&
    value.shell_subprocess_execution_enabled === false &&
    value.browser_execution_enabled === false &&
    value.provider_model_call_enabled === false &&
    value.memory_write_enabled === false &&
    value.context_injection_authorized === false &&
    value.production_authority_enabled === false &&
    value.approval_alone_executes === false &&
    hasStringArrays(value, ACTION_DECISION_LANE_REQUIRED_STRING_ARRAYS) &&
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
