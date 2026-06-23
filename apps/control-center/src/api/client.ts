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
  FounderLoopMemoryContextPacks,
  FounderLoopLocalTaskCommitReceipt,
  FounderLoopLocalTaskCommitRequest,
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
    return withConnection(mockControlCenterData, {
      state: "mock_fallback",
      safeMessage: API_BASE_POLICY.safeMessage,
      usingMockData: true,
      warnings: API_BASE_POLICY.warnings,
    });
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
    readEnvelope<FounderLoopMemoryContextPacks>(
      API_ENDPOINTS.founderMemoryContextPacks,
    ),
    readEnvelope<FounderLoopActionsInbox>(API_ENDPOINTS.founderActionsInbox),
    readEnvelope<FounderLoopMorningBriefing>(
      API_ENDPOINTS.founderMorningBriefing,
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
  const founderMemoryContextPacks = fulfilledValue(results[11]);
  const founderActionsInbox = fulfilledValue(results[12]);
  const founderMorningBriefing = fulfilledValue(results[13]);
  const founderStorageStatus = fulfilledValue(results[14]);
  const normalizedFounderToday = mergeMissingFields(
    mockControlCenterData.founderToday,
    founderToday,
  );
  const normalizedFounderEvidenceTimeline = mergeMissingFields(
    mockControlCenterData.founderEvidenceTimeline,
    founderEvidenceTimeline,
  );
  const normalizedFounderActionsInbox = mergeMissingFields(
    mockControlCenterData.founderActionsInbox,
    founderActionsInbox,
  );
  const normalizedFounderMemoryContextPacks = mergeMissingFields(
    mockControlCenterData.founderMemoryContextPacks,
    founderMemoryContextPacks,
  );
  const normalizedFounderMorningBriefing = mergeMissingFields(
    mockControlCenterData.founderMorningBriefing,
    founderMorningBriefing,
  );
  const founderLoopFieldFallbackUsed =
    normalizedFounderToday.usedFallback ||
    normalizedFounderEvidenceTimeline.usedFallback ||
    normalizedFounderActionsInbox.usedFallback ||
    normalizedFounderMemoryContextPacks.usedFallback ||
    normalizedFounderMorningBriefing.usedFallback;
  const fulfilledCount = results.filter(
    (result) => result.status === "fulfilled",
  ).length;

  if (fulfilledCount === 0) {
    return withConnection(mockControlCenterData, {
      state: "mock_fallback",
      safeMessage:
        "Backend unavailable; showing non-authoritative mock fallback data.",
      usingMockData: true,
      warnings: ["LOCAL_BACKEND_UNAVAILABLE", "MOCK_DATA_ONLY"],
    });
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
    founderMemoryContextPacks: normalizedFounderMemoryContextPacks.value,
    founderActionsInbox: normalizedFounderActionsInbox.value,
    founderMorningBriefing: normalizedFounderMorningBriefing.value,
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
  return `idempotency-ref:control-center-memory-review:${decision}:${safeChatSuffix(candidateRef)}:${safeChatSuffix(request?.reviewer_ref ?? "reviewer")}:${safeChatSuffix(request?.corrected_summary_ref ?? "none")}`;
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
