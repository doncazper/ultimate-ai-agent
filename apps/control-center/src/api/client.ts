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
  RedactedLocalChatProbeStatus,
  ResultEnvelope,
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
  FounderLoopMemoryReview,
  FounderLoopMemoryWorkbench,
  FounderLoopLocalTaskCommitReceipt,
  FounderLoopLocalTaskCommitRequest,
  ManualMemoryCandidateReceipt,
  ManualMemoryCandidateRequest,
  MemoryReviewDecisionKind,
  MemoryReviewDecisionReceipt,
  MemoryReviewDecisionRequest,
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
  const response = await fetch(`${API_BASE_POLICY.baseUrl}${endpoint}`, {
    headers: withLocalApiAuthHeaders({ Accept: "application/json" }),
  });
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

export async function loadControlCenterData(): Promise<ControlCenterData> {
  if (!API_BASE_POLICY.allowed) {
    return withConnection(
      {
        ...mockControlCenterData,
        founderToday: normalizeFounderToday(undefined).value,
        founderActionsInbox: normalizeFounderActionsInbox(undefined).value,
        founderMorningBriefing: normalizeFounderMorningBriefing(undefined).value,
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
    readEnvelope<FounderLoopActionsInbox>(API_ENDPOINTS.founderActionsInbox),
    readEnvelope<FounderLoopMorningBriefing>(
      API_ENDPOINTS.founderMorningBriefing,
    ),
    readEnvelope<FounderLoopSourceReadiness>(
      API_ENDPOINTS.founderSourceReadiness,
    ),
    readEnvelope<FounderLoopStorageStatus>(API_ENDPOINTS.founderStorageStatus),
  ] as const);

  const manifest = fulfilledValue(results[0]);
  const dashboard = fulfilledValue(results[1]);
  const status = fulfilledValue(results[2]);
  const routes = fulfilledValue(results[3]);
  const runtimeReadiness = fulfilledValue(results[4]);
  const capabilityMatrix = fulfilledValue(results[5]);
  const setupAssistant = normalizeMacOSSetupAssistant(
    fulfilledValue(results[6]),
    mockControlCenterData.macosSetupAssistant,
  );
  const controlCenterSettingsStatus = fulfilledValue(results[7]);
  const controlCenterLocalModelsStatus = fulfilledValue(results[8]);
  const founderToday = fulfilledValue(results[9]);
  const founderEvidenceTimeline = fulfilledValue(results[10]);
  const founderMemoryReview = fulfilledValue(results[11]);
  const founderMemoryWorkbench = fulfilledValue(results[12]);
  const founderMemoryContextPacks = fulfilledValue(results[13]);
  const founderActionsInbox = fulfilledValue(results[14]);
  const founderMorningBriefing = fulfilledValue(results[15]);
  const founderSourceReadiness = fulfilledValue(results[16]);
  const founderStorageStatus = fulfilledValue(results[17]);
  const normalizedFounderToday = normalizeFounderToday(founderToday);
  const normalizedFounderEvidenceTimeline = mergeMissingFields(
    mockControlCenterData.founderEvidenceTimeline,
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
  const normalizedFounderMorningBriefing =
    normalizeFounderMorningBriefing(founderMorningBriefing);
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
    normalizedFounderMorningBriefing.usedFallback ||
    normalizedFounderSourceReadiness.usedFallback;
  const fulfilledCount = results.filter(
    (result) => result.status === "fulfilled",
  ).length;

  if (fulfilledCount === 0) {
    return withConnection(
      {
        ...mockControlCenterData,
        founderToday: normalizeFounderToday(undefined).value,
        founderActionsInbox: normalizeFounderActionsInbox(undefined).value,
        founderMorningBriefing: normalizeFounderMorningBriefing(undefined).value,
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
    dashboard: dashboard ?? mockControlCenterData.dashboard,
    status: status ?? mockControlCenterData.status,
    routes: routes ?? mockControlCenterData.routes,
    runtimeReadiness:
      runtimeReadiness ?? mockControlCenterData.runtimeReadiness,
    capabilityMatrix:
      capabilityMatrix ?? mockControlCenterData.capabilityMatrix,
    m15Review: mockControlCenterData.m15Review,
    m16Trace: mockControlCenterData.m16Trace,
    m17Knowledge: mockControlCenterData.m17Knowledge,
    m18Runtime: mockControlCenterData.m18Runtime,
    m36FileReview: mockControlCenterData.m36FileReview,
    m39ContextProposals: mockControlCenterData.m39ContextProposals,
    macosSetupAssistant: setupAssistant,
    settingsStatus:
      controlCenterSettingsStatus ?? mockControlCenterData.settingsStatus,
    localModelsStatus:
      controlCenterLocalModelsStatus ?? mockControlCenterData.localModelsStatus,
    founderToday: normalizedFounderToday.value,
    founderEvidenceTimeline: normalizedFounderEvidenceTimeline.value,
    founderMemoryReview: normalizedFounderMemoryReview.value,
    founderMemoryWorkbench: normalizedFounderMemoryWorkbench.value,
    founderMemoryContextPacks: normalizedFounderMemoryContextPacks.value,
    founderActionsInbox: normalizedFounderActionsInbox.value,
    founderMorningBriefing: normalizedFounderMorningBriefing.value,
    founderSourceReadiness: normalizedFounderSourceReadiness.value,
    founderStorageStatus:
      founderStorageStatus ?? mockControlCenterData.founderStorageStatus,
    source: "api",
    connection: mockControlCenterData.connection,
  };

  if (fulfilledCount === results.length && !founderLoopFieldFallbackUsed) {
    return withConnection(data, {
      state: "online",
      safeMessage:
        "Live data came from local read-only/preview-only backend API routes.",
      usingMockData: false,
      warnings: [],
    });
  }

  return withConnection(data, {
    state: "degraded",
    safeMessage:
      founderLoopFieldFallbackUsed
        ? "Some local backend summaries or fields were unavailable; non-authoritative mock fallback filled missing Founder Loop panels."
        : "Some local backend summaries were unavailable; non-authoritative mock fallback filled missing panels.",
    usingMockData: true,
    warnings: [
      "LOCAL_BACKEND_DEGRADED",
      "PARTIAL_MOCK_FALLBACK",
      ...(founderLoopFieldFallbackUsed
        ? ["PARTIAL_FOUNDER_LOOP_FIELD_FALLBACK"]
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
  const data =
    (await readJsonSafely(response)) as ResultEnvelope<FounderLoopLocalTaskCommitReceipt>;
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
  return readEnvelope<FounderLoopActionsInbox>(API_ENDPOINTS.founderActionsInbox);
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
  const data = (await readJsonSafely(response)) as ResultEnvelope<ChatTurnReceipt>;
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
  const data = (await readJsonSafely(response)) as ResultEnvelope<ChatHandoffReceipt>;
  const receipt = data.result ?? data.data;
  if (!response.ok || !receipt) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(data, "Chat handoff receipt was not recorded safely."),
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
  const data =
    (await readJsonSafely(response)) as ResultEnvelope<MemoryReviewDecisionReceipt>;
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

export async function fetchFounderMemoryReview(): Promise<FounderLoopMemoryReview> {
  return readEnvelope<FounderLoopMemoryReview>(API_ENDPOINTS.founderMemoryReview);
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
  const data =
    (await readJsonSafely(response)) as ResultEnvelope<ManualMemoryCandidateReceipt>;
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
  const data =
    (await readJsonSafely(response)) as ResultEnvelope<FounderLoopMemoryContextPackActionProposalReceipt>;
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
    return Array.isArray(value) && value.every((item) => typeof item === "string");
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
  const labels = new Set(value.filter((item): item is string => typeof item === "string"));
  return ["approve", "edit", "reject", "defer"].every((label) => labels.has(label));
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

function normalizeFounderToday(
  value: FounderLoopTodaySummary | undefined,
): { value: FounderLoopTodaySummary; usedFallback: boolean } {
  if (value === undefined) {
    const fallbackWithoutDigest = {
      ...(mockControlCenterData.founderToday as unknown as Record<string, unknown>),
    };
    delete fallbackWithoutDigest.today_loop_read_model;
    delete fallbackWithoutDigest.today_loop_tightening_contract_ref;
    delete fallbackWithoutDigest.follow_up_tracker;
    delete fallbackWithoutDigest.follow_up_tracker_contract_ref;
    delete fallbackWithoutDigest.weekly_ceo_review_v1_read_model;
    delete fallbackWithoutDigest.weekly_ceo_review_v1_contract_ref;
    delete fallbackWithoutDigest.plans_to_actions_bridge_read_model;
    delete fallbackWithoutDigest.plans_to_actions_bridge_contract_ref;
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
  if (Object.prototype.hasOwnProperty.call(valueRecord, "today_loop_read_model")) {
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
    normalized.weekly_ceo_review_v1_contract_ref =
      (weeklyCeoReview as Record<string, unknown>).contract_ref;
  } else {
    delete normalized.weekly_ceo_review_v1_read_model;
    delete normalized.weekly_ceo_review_v1_contract_ref;
  }
  if (isSafePlansToActionsBridgeReadModel(valueRecord.plans_to_actions_bridge_read_model)) {
    normalized.plans_to_actions_bridge_read_model =
      valueRecord.plans_to_actions_bridge_read_model;
    normalized.plans_to_actions_bridge_contract_ref =
      valueRecord.plans_to_actions_bridge_contract_ref;
  } else {
    delete normalized.plans_to_actions_bridge_read_model;
    delete normalized.plans_to_actions_bridge_contract_ref;
    normalized = stripPlansActionEnvelopePosture(normalized);
  }
  return {
    value: normalized as unknown as FounderLoopTodaySummary,
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
    return { value: withoutMockTracker as T, usedFallback: merged.usedFallback };
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
  if (isSafeMorningBriefingV1ReadModel(valueRecord.morning_briefing_v1_read_model)) {
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
    normalized.weekly_ceo_review_v1_contract_ref =
      (weeklyCeoReview as Record<string, unknown>).contract_ref;
  } else {
    delete normalized.weekly_ceo_review_v1_read_model;
    delete normalized.weekly_ceo_review_v1_contract_ref;
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
    value.contract_ref !== "contract-ref:product-loop-008-weekly-ceo-review-v1:v1" ||
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

function hasMatchingWeeklyCeoReviewV1Counts(value: Record<string, unknown>): boolean {
  return WEEKLY_CEO_REVIEW_V1_COUNT_ARRAY_PAIRS.every(([countKey, refsKey]) => {
    const count = value[countKey];
    const refs = value[refsKey];
    return typeof count === "number" && Array.isArray(refs) && count === refs.length;
  });
}

function isSafeMorningBriefingV1ReadModel(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  if (
    value.schema_version !== "product-loop-007-morning-briefing.v1" ||
    value.contract_ref !== "contract-ref:product-loop-007-morning-briefing-v1:v1" ||
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
    if (value[field] !== null && value[field] !== undefined && typeof value[field] !== "string") {
      return false;
    }
  }
  return (
    hasTrueFlags(value, PLANS_TO_ACTIONS_BRIDGE_ITEM_TRUE_FLAGS) &&
    value.raw_content_included === false &&
    hasDeniedFlagsFalse(value, PLANS_TO_ACTIONS_BRIDGE_DENIED_FLAGS) &&
    hasStringArrays(value, PLANS_TO_ACTIONS_BRIDGE_ITEM_REQUIRED_ARRAYS) &&
    hasRequiredReviewReceiptLabels(value.review_receipt_labels) &&
    (value.expected_receipt_refs as unknown[]).length > 0 &&
    (value.evidence_refs as unknown[]).length > 0 &&
    (value.blocked_authority_refs as unknown[]).length > 0
  );
}

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
    value.approval_alone_executes === false
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
      value: workbenchWithoutMockPosture as unknown as FounderLoopMemoryWorkbench,
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
