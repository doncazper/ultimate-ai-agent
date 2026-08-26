import { mockControlCenterData } from "../mocks/controlCenterData";
import type {
  ActionPreviewDecision,
  ActionPreviewRequest,
  AutocorrectControlStatus,
  AutocorrectProposal,
  AutocorrectProposalRequest,
  AutocorrectReviewReceipt,
  AutocorrectReviewRequest,
  AuthorityActionRequest,
  AuthorityDecisionPreview,
  AuthorityLeaseApproveAndIssueRequest,
  AuthorityLeaseIssueRequest,
  AuthorityLeaseMutationResult,
  AuthorityLeaseRevokeRequest,
  AuthorityMissionPlan,
  AuthorityMissionPlanRequest,
  AuthorityMissionWorkerJob,
  AuthorityMissionWorkerReadModel,
  AuthorityMissionWorkerStepRecovery,
  AuthorityMissionCompletionReadModel,
  BackendConnectionSummary,
  CommunicationConversation,
  CommunicationsFailedSendPage,
  CommunicationsProviderDescriptor,
  CommunicationsReceipt,
  CommunicationsRoomPage,
  ReviewedCommunicationsThreadPage,
  CommunicationsSecurityPosture,
  CommunicationsSessionPosture,
  MatrixCryptoPosture,
  MatrixHardeningPosture,
  MatrixMessagingPosture,
  MatrixIntelligencePosture,
  MatrixRoomsMediaPosture,
  MatrixSyncPosture,
  CodingCockpitSessionReadModel,
  CodingWorkspaceContextReadModel,
  ControlCenterDashboardSnapshot,
  ControlCenterData,
  ControlCenterLocalModelsStatus,
  ControlCenterManifest,
  ControlCenterCapabilitySurfaceReadModel,
  ControlCenterBackendTruth,
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
  NewsSignalsSummary,
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
  RuntimeBackgroundJobsReadModel,
  RuntimeLspDiagnosticsReadModel,
  RuntimeSubagentIsolationReadModel,
  RuntimeCapabilityMatrix,
  RuntimeCapabilityDiscoveryReadModel,
  RuntimeContextBudgetPressureReadModel,
  RuntimeDelegationAdapterReadModel,
  RuntimeDoctorDiagnosticsReadModel,
  RuntimeInterfaceModeReadModel,
  HermesContextPackReadModel,
  RuntimeHardlineCommandBlocklistReadModel,
  RuntimeManagedScopePolicyReadModel,
  RuntimeMcpCatalogFilteringReadModel,
  RuntimePromptStabilityTiersReadModel,
  RuntimePreviewRailReadModel,
  RuntimeInterruptRedirectReadModel,
  RuntimeLoggingProfileReadModel,
  RuntimeMessagingGatewayPostureReadModel,
  RuntimePluginMetadataPostureReadModel,
  RuntimeRemoteExecutionPostureReadModel,
  RuntimeResultClassificationReadModel,
  RuntimeSkillMarketplaceCatalogEntry,
  RuntimeSkillMarketplaceCatalogFreshness,
  RuntimeSkillMarketplaceSourceSnapshot,
  RuntimeSkillMarketplacePostureReadModel,
  RuntimeVoiceMediaPostureReadModel,
  RuntimeSessionContinuityReadModel,
  RuntimeToolsetCapabilityPosture,
  RuntimeToolRegistryAvailabilityReadModel,
  RuntimeUsageCostAnalyticsReadModel,
  RuntimeVirtualProviderMoaReadModel,
  RuntimeRunEventsReadModel,
  RuntimePersistentGoal,
  RuntimeGoalCreateRequest,
  RuntimeGoalEditRequest,
  RuntimeGoalMutationResult,
  RuntimeGoalMutationApprovalDecision,
  RuntimeGoalMutationApprovalRequestSpec,
  RuntimeGoalTransitionRequest,
  RuntimeStagedOrchestrationReadModel,
  RuntimeStreamingProgressReadModel,
  RuntimeProfileIsolationReadModel,
  RuntimeReadinessReport,
  RuntimeSlashCommandRegistryReadModel,
  RuntimeWorktreePerAgentReadModel,
  ApiRouteInventory,
  FounderLoopActionDecisionKind,
  FounderLoopActionLifecycleDecisionKind,
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
  GovernedMemoryContextManifest,
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
  WorkBoardCardCreateReceipt,
  WorkBoardCardCreateRequest,
  WorkBoardReadModel,
  WorkBoardReorderReceipt,
  WorkBoardReorderRequest,
  WorkBoardTaskCreateReceipt,
  WorkBoardTaskCreateRequest,
} from "./types";
import { resolveApiBaseUrl } from "./baseUrl";
import {
  API_ENDPOINTS,
  actionDecisionEndpoint,
  actionLocalTaskCommitEndpoint,
  actionReceiptEndpoint,
  chatTurnHandoffEndpoint,
  chatTurnReceiptEndpoint,
  communicationsReceiptEndpoint,
  memoryContextPackActionProposalEndpoint,
  memoryReviewDecisionEndpoint,
  memoryReviewReceiptEndpoint,
  runtimeInvocationDecisionEndpoint,
  runtimeInvocationExecuteEndpoint,
  runtimeGoalEditEndpoint,
  runtimeGoalApprovalDecisionEndpoint,
  runtimeGoalApprovalPrepareEndpoint,
  runtimeGoalTransitionEndpoint,
} from "./endpoints";
import { normalizeMacOSSetupAssistant } from "./macosSetupAssistant";
import {
  containsSecretLike,
  safeApiErrorMessage,
  sanitizeForDisplay,
} from "./redaction";
import {
  StrictBackendDataError,
  strictBackendDataFailureRequired,
  strictBackendModeEnabled,
} from "./runtimePolicy";
import { validateControlCenterBackendTruth } from "./backendTruth";

const API_BASE_POLICY = resolveApiBaseUrl(
  import.meta.env.VITE_UAA_API_BASE_URL,
);
export const CONTROL_CENTER_READ_TIMEOUT_MS = 8000;
export const CONTROL_CENTER_MAX_CONCURRENT_READS = 32;
export const ACTION_INBOX_REVISION_REFRESH_EVENT =
  "uaa:action-inbox-revision-refresh-required";

export interface ActionInboxRevisionConflictDetail {
  code: "FOUNDER_LOOP_ACTION_STALE_REVISION";
  currentRevisionRef: string;
  currentGenerationRef: string;
  refreshRouteRef: string;
}

export class ActionInboxRevisionConflictError extends Error {
  readonly detail: ActionInboxRevisionConflictDetail;

  constructor(detail: ActionInboxRevisionConflictDetail) {
    super(
      "The Action changed after this decision was prepared. The authoritative inbox must be refreshed before retrying.",
    );
    this.name = "ActionInboxRevisionConflictError";
    this.detail = detail;
  }
}
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
const LOCAL_API_SESSION_FRAGMENT_KEY = "uaa-session-bearer";

export function setLocalApiBearerForSession(value: string | null): void {
  const trimmed = value?.trim() ?? "";
  sessionLocalApiBearer = trimmed.length > 0 ? trimmed : null;
}

export function consumeLocalApiBearerFromLocation(): boolean {
  const fragment = new URLSearchParams(window.location.hash.slice(1));
  const bearer = fragment.get(LOCAL_API_SESSION_FRAGMENT_KEY)?.trim() ?? "";
  if (!bearer) {
    return false;
  }
  setLocalApiBearerForSession(bearer);
  fragment.delete(LOCAL_API_SESSION_FRAGMENT_KEY);
  const remainingFragment = fragment.toString();
  window.history.replaceState(
    window.history.state,
    "",
    `${window.location.pathname}${window.location.search}${remainingFragment ? `#${remainingFragment}` : ""}`,
  );
  return true;
}

export function resetControlCenterReadLimiterForTests(): void {
  defaultControlCenterReadLimiter.reset();
}

function localApiBearerForRequest(): string | null {
  return sessionLocalApiBearer;
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
  expectedBinding: BackendTruthReadBinding | null = null,
): Promise<T> {
  await readLimiter.acquire();
  try {
    const response = await withReadTimeout(
      fetch(`${API_BASE_POLICY.baseUrl}${endpoint}`, {
        headers: withLocalApiAuthHeaders({ Accept: "application/json" }),
      }),
      endpoint,
    );
    validateBackendResponseBinding(response.headers, expectedBinding);
    const data = (await response.json()) as ResultEnvelope<T> | T;
    if (!response.ok) {
      throw new Error(
        safeApiErrorMessage(data, "Local backend read failed safely."),
      );
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
          safeApiErrorMessage(envelope, "Local backend read failed safely."),
        );
      }
      return result;
    }
    return data as T;
  } finally {
    readLimiter.release();
  }
}

export interface BackendTruthReadBinding {
  snapshotRef: string;
  backendRevisionRef: string;
  backendInstanceRef: string;
}

export function withBackendTruthMutationHeaders(
  headers: Record<string, string>,
  binding: BackendTruthReadBinding | null,
): Record<string, string> {
  if (binding === null) {
    throw new Error("BACKEND_TRUTH_MUTATION_BINDING_REQUIRED");
  }
  return {
    ...headers,
    "X-UAA-Control-Center-Mutation-Binding": "backend-truth.v1",
    "X-UAA-Expected-Backend-Revision-Ref": binding.backendRevisionRef,
    "X-UAA-Expected-Backend-Instance-Ref": binding.backendInstanceRef,
    "X-UAA-Expected-Backend-Truth-Ref": binding.snapshotRef,
  };
}

export function validateBackendResponseBinding(
  headers: Headers,
  expectedBinding: BackendTruthReadBinding | null,
): void {
  if (expectedBinding === null) return;
  const backendRevisionRef = headers.get("X-UAA-Backend-Revision-Ref");
  const backendInstanceRef = headers.get("X-UAA-Backend-Instance-Ref");
  if (
    backendRevisionRef !== expectedBinding.backendRevisionRef ||
    backendInstanceRef !== expectedBinding.backendInstanceRef
  ) {
    throw new Error("BACKEND_RESPONSE_PROVENANCE_MISMATCH");
  }
}

export async function loadControlCenterBackendTruth(): Promise<ControlCenterBackendTruth> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const payload = await readEnvelope<unknown>(
    API_ENDPOINTS.controlCenterBackendTruth,
  );
  return validateControlCenterBackendTruth(payload);
}

export async function loadNewsSignalsSummary(): Promise<NewsSignalsSummary> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const value = await readEnvelope<unknown>(API_ENDPOINTS.newsSignalsSummary);
  if (!isSafeNewsSignalsSummary(value)) {
    throw new Error("NEWS_SIGNALS_RESPONSE_INVALID");
  }
  return value;
}

const NEWS_SIGNALS_SAFE_REF =
  /^[a-z][a-z0-9-]*-ref:[a-z0-9][a-z0-9:-]{1,190}$/;
const NEWS_SIGNALS_TIMESTAMP =
  /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/;

function newsSignalsHasOnlyKeys(
  value: Record<string, unknown>,
  allowed: readonly string[],
): boolean {
  const allowedSet = new Set(allowed);
  return Object.keys(value).every((key) => allowedSet.has(key));
}

function isNewsSignalsSafeRef(value: unknown): value is string {
  return typeof value === "string" && NEWS_SIGNALS_SAFE_REF.test(value);
}

function isNewsSignalsSafeRefArray(
  value: unknown,
  maximum: number,
): value is string[] {
  return (
    Array.isArray(value) &&
    value.length <= maximum &&
    value.every(isNewsSignalsSafeRef) &&
    new Set(value).size === value.length
  );
}

function isNewsSignalsSafeText(value: unknown, maximum: number): value is string {
  return (
    typeof value === "string" &&
    value.length > 0 &&
    value.length <= maximum &&
    value.trim() === value &&
    !value.includes("\n") &&
    !value.includes("\r") &&
    !value.includes("://") &&
    !value.includes("/") &&
    !value.includes("\\") &&
    !value.includes("@") &&
    !containsSecretLike(value)
  );
}

function isSafeNewsSignalItem(value: unknown): value is NewsSignalsSummary["items"][number] {
  if (!isPlainRecord(value)) return false;
  if (
    !newsSignalsHasOnlyKeys(value, [
      "signal_ref",
      "cluster_ref",
      "claim_ref",
      "title",
      "safe_summary",
      "source_ref",
      "source_label",
      "source_kind",
      "source_state",
      "source_revision_ref",
      "content_digest_ref",
      "topic_ref",
      "published_at",
      "observed_at",
      "freshness_state",
      "confidence_percent",
      "confidence_state",
      "evidence_class",
      "external_content_untrusted",
      "conflict_state",
      "coverage_source_refs",
      "coverage_count",
      "provenance_refs",
      "rank_score",
      "rank_reason_refs",
      "briefing_candidate",
      "action_authority_granted",
    ])
  ) {
    return false;
  }
  const sourceKinds = ["official", "community", "rss", "public_social", "local"];
  const sourceStates = ["ready", "blocked", "unknown", "revoked", "safe_disabled"];
  return (
    isNewsSignalsSafeRef(value.signal_ref) &&
    isNewsSignalsSafeRef(value.cluster_ref) &&
    isNewsSignalsSafeRef(value.claim_ref) &&
    isNewsSignalsSafeText(value.title, 140) &&
    isNewsSignalsSafeText(value.safe_summary, 320) &&
    isNewsSignalsSafeRef(value.source_ref) &&
    isNewsSignalsSafeText(value.source_label, 80) &&
    sourceKinds.includes(String(value.source_kind)) &&
    sourceStates.includes(String(value.source_state)) &&
    isNewsSignalsSafeRef(value.source_revision_ref) &&
    isNewsSignalsSafeRef(value.content_digest_ref) &&
    isNewsSignalsSafeRef(value.topic_ref) &&
    typeof value.published_at === "string" &&
    NEWS_SIGNALS_TIMESTAMP.test(value.published_at) &&
    typeof value.observed_at === "string" &&
    NEWS_SIGNALS_TIMESTAMP.test(value.observed_at) &&
    ["fresh", "stale", "unknown"].includes(String(value.freshness_state)) &&
    Number.isInteger(value.confidence_percent) &&
    Number(value.confidence_percent) >= 0 &&
    Number(value.confidence_percent) <= 100 &&
    ["high", "medium", "low"].includes(String(value.confidence_state)) &&
    ["primary", "corroborating", "community", "commentary"].includes(
      String(value.evidence_class),
    ) &&
    value.external_content_untrusted === true &&
    ["none", "conflicting"].includes(String(value.conflict_state)) &&
    isNewsSignalsSafeRefArray(value.coverage_source_refs, 24) &&
    Number.isInteger(value.coverage_count) &&
    value.coverage_count === value.coverage_source_refs.length &&
    isNewsSignalsSafeRefArray(value.provenance_refs, 24) &&
    typeof value.rank_score === "number" &&
    Number.isFinite(value.rank_score) &&
    isNewsSignalsSafeRefArray(value.rank_reason_refs, 24) &&
    typeof value.briefing_candidate === "boolean" &&
    value.action_authority_granted === false
  );
}

function isSafeNewsSignalSource(value: unknown): boolean {
  if (!isPlainRecord(value)) return false;
  if (
    !newsSignalsHasOnlyKeys(value, [
      "source_ref",
      "source_kind",
      "safe_label",
      "state",
      "observed_at",
      "freshness_ttl_seconds",
      "adapter_ref",
      "provenance_ref",
      "retention_ref",
      "reason_refs",
      "external_network_read_performed",
      "account_authority_granted",
    ])
  ) {
    return false;
  }
  return (
    isNewsSignalsSafeRef(value.source_ref) &&
    ["official", "community", "rss", "public_social", "local"].includes(
      String(value.source_kind),
    ) &&
    isNewsSignalsSafeText(value.safe_label, 80) &&
    ["ready", "blocked", "unknown", "revoked", "safe_disabled"].includes(
      String(value.state),
    ) &&
    (value.observed_at === null ||
      (typeof value.observed_at === "string" &&
        NEWS_SIGNALS_TIMESTAMP.test(value.observed_at))) &&
    Number.isInteger(value.freshness_ttl_seconds) &&
    Number(value.freshness_ttl_seconds) >= 300 &&
    Number(value.freshness_ttl_seconds) <= 604_800 &&
    isNewsSignalsSafeRef(value.adapter_ref) &&
    isNewsSignalsSafeRef(value.provenance_ref) &&
    isNewsSignalsSafeRef(value.retention_ref) &&
    isNewsSignalsSafeRefArray(value.reason_refs, 24) &&
    value.external_network_read_performed === false &&
    value.account_authority_granted === false
  );
}

function isSafeNewsSignalsSummary(value: unknown): value is NewsSignalsSummary {
  if (!isPlainRecord(value)) return false;
  if (
    !newsSignalsHasOnlyKeys(value, [
      "schema_version",
      "contract_ref",
      "status",
      "backend_owned",
      "read_only",
      "local_artifact_snapshot_only",
      "external_content_untrusted",
      "live_fetch_enabled",
      "authenticated_source_enabled",
      "background_polling_enabled",
      "model_summarization_enabled",
      "connector_write_enabled",
      "action_authority_granted",
      "observed_at",
      "source_readiness",
      "items",
      "freshness_counts",
      "conflicting_claim_refs",
      "today_projection",
      "morning_briefing_projection",
      "safe_summary",
      "blocked_state_refs",
      "evidence_refs",
    ])
  ) {
    return false;
  }
  if (
    value.schema_version !== "uaa-news-signals-read-model.v1" ||
    !isNewsSignalsSafeRef(value.contract_ref) ||
    ![
      "blocked_no_graduated_source",
      "blocked_source_unavailable",
      "ready_empty",
      "ready",
    ].includes(String(value.status)) ||
    value.backend_owned !== true ||
    value.read_only !== true ||
    value.local_artifact_snapshot_only !== true ||
    value.external_content_untrusted !== true ||
    value.live_fetch_enabled !== false ||
    value.authenticated_source_enabled !== false ||
    value.background_polling_enabled !== false ||
    value.model_summarization_enabled !== false ||
    value.connector_write_enabled !== false ||
    value.action_authority_granted !== false ||
    typeof value.observed_at !== "string" ||
    !NEWS_SIGNALS_TIMESTAMP.test(value.observed_at) ||
    !Array.isArray(value.source_readiness) ||
    value.source_readiness.length > 24 ||
    !value.source_readiness.every(isSafeNewsSignalSource) ||
    !Array.isArray(value.items) ||
    value.items.length > 100 ||
    !value.items.every(isSafeNewsSignalItem) ||
    !isPlainRecord(value.freshness_counts) ||
    !isNewsSignalsSafeRefArray(value.conflicting_claim_refs, 100) ||
    !isPlainRecord(value.today_projection) ||
    !isPlainRecord(value.morning_briefing_projection) ||
    !isNewsSignalsSafeText(value.safe_summary, 320) ||
    !isNewsSignalsSafeRefArray(value.blocked_state_refs, 24) ||
    !isNewsSignalsSafeRefArray(value.evidence_refs, 24)
  ) {
    return false;
  }
  const freshness = value.freshness_counts;
  const today = value.today_projection;
  const briefing = value.morning_briefing_projection;
  return (
    newsSignalsHasOnlyKeys(freshness, ["fresh", "stale", "unknown"]) &&
    [freshness.fresh, freshness.stale, freshness.unknown].every(
      (count) => Number.isInteger(count) && Number(count) >= 0,
    ) &&
    newsSignalsHasOnlyKeys(today, [
      "projection_ref",
      "item_refs",
      "bounded_limit",
      "read_only",
    ]) &&
    isNewsSignalsSafeRef(today.projection_ref) &&
    isNewsSignalsSafeRefArray(today.item_refs, 3) &&
    today.bounded_limit === 3 &&
    today.read_only === true &&
    newsSignalsHasOnlyKeys(briefing, [
      "projection_ref",
      "candidate_refs",
      "bounded_limit",
      "review_required",
      "read_only",
    ]) &&
    isNewsSignalsSafeRef(briefing.projection_ref) &&
    isNewsSignalsSafeRefArray(briefing.candidate_refs, 5) &&
    briefing.bounded_limit === 5 &&
    briefing.review_required === true &&
    briefing.read_only === true
  );
}

const COMMUNICATIONS_SAFE_REF =
  /^[a-z][a-z0-9-]*-ref:[a-z0-9][a-z0-9:-]*$/;
const COMMUNICATIONS_SAFE_CODE = /^[A-Z][A-Z0-9_]{2,127}$/;
const COMMUNICATIONS_MAX_PROVIDERS = 16;
const COMMUNICATIONS_MAX_REFS = 50;
const COMMUNICATIONS_HOST_OR_IP =
  /(?:\b[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+\b)|(?:\b(?:\d{1,3}\.){3}\d{1,3}\b)|(?:\[[0-9a-f:]+\])/i;
const COMMUNICATIONS_FULL_IPV6 =
  /(?:^|[^0-9a-f])(?:[0-9a-f]{1,4}:){7}[0-9a-f]{1,4}(?:$|[^0-9a-f])/i;

function containsCommunicationsIpv6(value: string): boolean {
  return value.includes("::") || COMMUNICATIONS_FULL_IPV6.test(value);
}

function isCommunicationsRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isCommunicationsSafeRef(value: unknown): value is string {
  return (
    typeof value === "string" &&
    COMMUNICATIONS_SAFE_REF.test(value) &&
    !value.includes("@") &&
    !value.includes(".") &&
    !value.includes("/") &&
    !value.toLowerCase().includes("localhost") &&
    !containsCommunicationsIpv6(value)
  );
}

function hasExactCommunicationsKeys(
  value: Record<string, unknown>,
  keys: readonly string[],
): boolean {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  return (
    actual.length === expected.length &&
    actual.every((key, index) => key === expected[index])
  );
}

function isCommunicationsSafeCodeArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.length <= 32 &&
    value.every(
      (item) =>
        typeof item === "string" && COMMUNICATIONS_SAFE_CODE.test(item),
    )
  );
}

function isCommunicationsSafeRefArray(
  value: unknown,
  maximum = COMMUNICATIONS_MAX_REFS,
): value is string[] {
  return (
    Array.isArray(value) &&
    value.length <= maximum &&
    value.every(isCommunicationsSafeRef) &&
    new Set(value).size === value.length
  );
}

function isCommunicationsSafeSummary(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length >= 1 &&
    value.length <= 240 &&
    !value.includes("@") &&
    !value.includes("://") &&
    !COMMUNICATIONS_HOST_OR_IP.test(value) &&
    !containsCommunicationsIpv6(value) &&
    !containsSecretLike(value)
  );
}

function isCommunicationsTimestamp(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(
      value,
    ) &&
    !Number.isNaN(Date.parse(value))
  );
}

function isOptionalCommunicationsSafeRef(value: unknown): boolean {
  return value === null || isCommunicationsSafeRef(value);
}

function isDisabledCommunicationsAvailabilityTuple(
  value: Record<string, unknown>,
): boolean {
  return (
    value.snapshot_ref === "snapshot-ref:communications:matrix-disabled" &&
    value.capability_ref === "capability-ref:communications:matrix-inspection" &&
    value.provider_ref === "provider-ref:communications:matrix" &&
    value.adapter_ref === "adapter-ref:communications:matrix-disabled" &&
    value.catalog_status === "unsupported" &&
    value.compatibility_status === "unknown" &&
    value.configuration_status === "not_configured" &&
    value.health_status === "unknown" &&
    value.authority_posture === "blocked" &&
    value.resource_status === "unknown" &&
    value.cost_posture === "unknown" &&
    value.safe_disable_status === "unknown" &&
    value.declared_or_observed_version_ref === null &&
    value.expires_at === null &&
    value.freshness_status === "unknown" &&
    value.runtime_readiness_status === "unknown"
  );
}

function isPartialMatrixSessionAvailabilityTuple(
  value: Record<string, unknown>,
): boolean {
  const safeDisableTuple =
    (value.safe_disable_status === "inactive" &&
      value.runtime_readiness_status === "unknown") ||
    (value.safe_disable_status === "active" &&
      value.runtime_readiness_status === "blocked");
  return (
    value.snapshot_ref === "snapshot-ref:communications:matrix-session-v1" &&
    value.capability_ref === "capability-ref:communications:matrix-session-v1" &&
    value.provider_ref === "provider-ref:communications:matrix" &&
    value.adapter_ref === "adapter-ref:communications:matrix-session-v1" &&
    value.catalog_status === "supported" &&
    value.compatibility_status === "supported" &&
    new Set(["configured", "not_configured"]).has(
      String(value.configuration_status),
    ) &&
    value.health_status === "unknown" &&
    value.authority_posture === "lease_required" &&
    value.resource_status === "available" &&
    value.cost_posture === "not_metered" &&
    value.declared_or_observed_version_ref ===
      "version-ref:matrix-js-sdk:41-9-0" &&
    value.expires_at === null &&
    value.freshness_status === "unknown" &&
    safeDisableTuple
  );
}

function isBlockedMatrixCryptoAvailabilityTuple(
  value: Record<string, unknown>,
): boolean {
  return (
    value.snapshot_ref === "snapshot-ref:communications:matrix-crypto-v1" &&
    value.capability_ref === "capability-ref:communications:matrix-crypto-v1" &&
    value.provider_ref === "provider-ref:communications:matrix" &&
    value.adapter_ref ===
      "adapter-ref:communications:matrix-crypto-required-v1" &&
    value.catalog_status === "supported" &&
    value.compatibility_status === "unknown" &&
    value.configuration_status === "not_configured" &&
    value.health_status === "unknown" &&
    value.authority_posture === "lease_required" &&
    value.resource_status === "available" &&
    value.cost_posture === "not_metered" &&
    value.safe_disable_status === "unknown" &&
    value.declared_or_observed_version_ref ===
      "version-ref:matrix-js-sdk:41-9-0" &&
    value.expires_at === null &&
    value.freshness_status === "unknown" &&
    value.runtime_readiness_status === "unknown"
  );
}

function isSafeCommunicationsAvailability(value: unknown): boolean {
  if (!isCommunicationsRecord(value)) {
    return false;
  }
  return (
    hasExactCommunicationsKeys(value, [
      "schema_version",
      "snapshot_ref",
      "capability_ref",
      "provider_ref",
      "adapter_ref",
      "catalog_status",
      "compatibility_status",
      "configuration_status",
      "health_status",
      "authority_posture",
      "resource_status",
      "cost_posture",
      "safe_disable_status",
      "declared_or_observed_version_ref",
      "checked_at",
      "expires_at",
      "freshness_status",
      "runtime_readiness_status",
      "reason_codes",
      "blocker_codes",
      "evidence_refs",
      "probe_refs",
      "source_ref",
      "safe_summary",
    ]) &&
    value.schema_version === "uaa-capability-availability.v1" &&
    isCommunicationsSafeRef(value.snapshot_ref) &&
    isCommunicationsSafeRef(value.capability_ref) &&
    isOptionalCommunicationsSafeRef(value.provider_ref) &&
    isOptionalCommunicationsSafeRef(value.adapter_ref) &&
    isOptionalCommunicationsSafeRef(value.declared_or_observed_version_ref) &&
    isCommunicationsTimestamp(value.checked_at) &&
    (value.expires_at === null || isCommunicationsTimestamp(value.expires_at)) &&
    isCommunicationsSafeCodeArray(value.reason_codes) &&
    isCommunicationsSafeCodeArray(value.blocker_codes) &&
    isCommunicationsSafeRefArray(value.evidence_refs, 32) &&
    isCommunicationsSafeRefArray(value.probe_refs, 32) &&
    isCommunicationsSafeRef(value.source_ref) &&
    isCommunicationsSafeSummary(value.safe_summary) &&
    (isDisabledCommunicationsAvailabilityTuple(value) ||
      isPartialMatrixSessionAvailabilityTuple(value) ||
      isBlockedMatrixCryptoAvailabilityTuple(value))
  );
}

function isSafeCommunicationsProvider(
  value: unknown,
): value is CommunicationsProviderDescriptor {
  if (!isCommunicationsRecord(value) || !isCommunicationsRecord(value.availability)) {
    return false;
  }
  return (
    hasExactCommunicationsKeys(value, [
      "schema_version",
      "provider_ref",
      "adapter_ref",
      "capability_ref",
      "provider_status",
      "availability",
      "reason_codes",
      "blocker_codes",
      "evidence_refs",
      "safe_summary",
    ]) &&
    value.schema_version === "uaa-communications.v1" &&
    isCommunicationsSafeRef(value.provider_ref) &&
    isCommunicationsSafeRef(value.adapter_ref) &&
    isCommunicationsSafeRef(value.capability_ref) &&
    isSafeCommunicationsAvailability(value.availability) &&
    isCommunicationsSafeCodeArray(value.reason_codes) &&
    isCommunicationsSafeCodeArray(value.blocker_codes) &&
    isCommunicationsSafeRefArray(value.evidence_refs, 32) &&
    isCommunicationsSafeSummary(value.safe_summary) &&
    ((value.provider_status === "unsupported" &&
      value.adapter_ref === "adapter-ref:communications:matrix-disabled" &&
      value.capability_ref === "capability-ref:communications:matrix-inspection") ||
      (value.provider_status === "partial" &&
        value.adapter_ref === "adapter-ref:communications:matrix-session-v1" &&
        value.capability_ref ===
          "capability-ref:communications:matrix-session-v1"))
  );
}

function isSafeCommunicationsPagination(value: unknown): boolean {
  return (
    isCommunicationsRecord(value) &&
    typeof value.page_size === "number" &&
    value.page_size >= 1 &&
    value.page_size <= 50 &&
    typeof value.returned_count === "number" &&
    Number.isInteger(value.page_size) &&
    Number.isInteger(value.returned_count) &&
    value.returned_count >= 0 &&
    value.returned_count <= value.page_size &&
    value.bounded === true &&
    (value.next_cursor_ref === null ||
      isCommunicationsSafeRef(value.next_cursor_ref))
  );
}

export async function loadCommunicationsProviders(): Promise<CommunicationsProviderDescriptor[]> {
  const value = await readEnvelope<unknown>(API_ENDPOINTS.communicationsProviders);
  if (
    !Array.isArray(value) ||
    value.length > COMMUNICATIONS_MAX_PROVIDERS ||
    !value.every(isSafeCommunicationsProvider)
  ) {
    throw new Error("Communications provider response failed safe validation.");
  }
  return value;
}

export async function loadCommunicationsSessionPosture(): Promise<CommunicationsSessionPosture> {
  const value = await readEnvelope<unknown>(
    API_ENDPOINTS.communicationsSessionPosture,
  );
  if (
    !isCommunicationsRecord(value) ||
    !hasExactCommunicationsKeys(value, [
      "provider_ref",
      "session_ref",
      "status",
      "freshness",
      "account_refs",
      "reason_codes",
      "blocker_codes",
      "safe_summary",
      "network_performed",
      "authentication_performed",
      "sync_performed",
    ]) ||
    !isCommunicationsSafeRef(value.provider_ref) ||
    !isCommunicationsSafeRef(value.session_ref) ||
    value.status !== "not_configured" ||
    value.freshness !== "unknown" ||
    value.network_performed !== false ||
    value.authentication_performed !== false ||
    value.sync_performed !== false ||
    !isCommunicationsSafeRefArray(value.account_refs) ||
    !isCommunicationsSafeCodeArray(value.reason_codes) ||
    !isCommunicationsSafeCodeArray(value.blocker_codes) ||
    !isCommunicationsSafeSummary(value.safe_summary)
  ) {
    throw new Error("Communications session response failed safe validation.");
  }
  return value as unknown as CommunicationsSessionPosture;
}

export async function loadMatrixSyncPosture(): Promise<MatrixSyncPosture> {
  const value = await readEnvelope<unknown>(
    API_ENDPOINTS.communicationsMatrixSyncPosture,
  );
  if (
    !isCommunicationsRecord(value) ||
    !hasExactCommunicationsKeys(value, [
      "schema_version",
      "provider_ref",
      "adapter_ref",
      "runtime_status",
      "freshness",
      "credential_posture_ref",
      "cache_posture_ref",
      "authority_lane_refs",
      "concrete_transport_operation_refs",
      "uncomposed_executor_operation_refs",
      "blocker_refs",
      "evidence_refs",
      "safe_summary",
      "sync_enabled",
      "connector_writes_enabled",
      "message_sends_enabled",
      "browser_automation_enabled",
      "encrypted_content_materialization_enabled",
      "content_untrusted",
      "not_instruction_authority",
      "raw_content_included",
      "desktop_only",
    ]) ||
    value.schema_version !== "uaa-matrix-sync-posture.v1" ||
    value.provider_ref !== "provider-ref:communications:matrix" ||
    !isCommunicationsSafeRef(value.adapter_ref) ||
    ![
      "ready",
      "configuration_required",
      "blocked",
      "unavailable",
      "unknown",
    ].includes(String(value.runtime_status)) ||
    !["current", "stale", "unknown", "locked", "unavailable"].includes(
      String(value.freshness),
    ) ||
    !isCommunicationsSafeRef(value.credential_posture_ref) ||
    !isCommunicationsSafeRef(value.cache_posture_ref) ||
    !isCommunicationsSafeRefArray(value.authority_lane_refs, 32) ||
    !isCommunicationsSafeRefArray(value.concrete_transport_operation_refs, 2) ||
    !isCommunicationsSafeRefArray(value.uncomposed_executor_operation_refs, 10) ||
    !isCommunicationsSafeRefArray(value.blocker_refs, 32) ||
    !isCommunicationsSafeRefArray(value.evidence_refs, 32) ||
    value.authority_lane_refs.length !== 12 ||
    value.concrete_transport_operation_refs.length !== 2 ||
    value.uncomposed_executor_operation_refs.length !== 10 ||
    new Set(value.authority_lane_refs).size !== 12 ||
    new Set(value.concrete_transport_operation_refs).size !== 2 ||
    new Set(value.uncomposed_executor_operation_refs).size !== 10 ||
    new Set(value.blocker_refs).size !== value.blocker_refs.length ||
    new Set(value.evidence_refs).size !== value.evidence_refs.length ||
    !isCommunicationsSafeSummary(value.safe_summary) ||
    typeof value.sync_enabled !== "boolean" ||
    value.sync_enabled !== (value.runtime_status === "ready") ||
    (value.runtime_status === "ready" &&
      (value.freshness !== "current" || value.blocker_refs.length !== 0)) ||
    (value.runtime_status === "configuration_required" &&
      value.blocker_refs.length === 0) ||
    value.connector_writes_enabled !== false ||
    value.message_sends_enabled !== false ||
    value.browser_automation_enabled !== false ||
    value.encrypted_content_materialization_enabled !== false ||
    value.content_untrusted !== true ||
    value.not_instruction_authority !== true ||
    value.raw_content_included !== false ||
    value.desktop_only !== true
  ) {
    throw new Error("Matrix sync posture response failed safe validation.");
  }
  return value as unknown as MatrixSyncPosture;
}

export async function loadMatrixCryptoPosture(): Promise<MatrixCryptoPosture> {
  const value = await readEnvelope<unknown>(
    API_ENDPOINTS.communicationsMatrixCryptoPosture,
  );
  if (
    !isCommunicationsRecord(value) ||
    !hasExactCommunicationsKeys(value, [
      "schema_version",
      "posture_ref",
      "runtime_status",
      "freshness",
      "authority_lane_refs",
      "accepted_authority_operation_refs",
      "live_executor_operation_refs",
      "blocked_operation_refs",
      "provider_ref",
      "runtime_ref",
      "store_backend_ref",
      "key_backend_ref",
      "backup_backend_ref",
      "reason_refs",
      "blocker_refs",
      "evidence_refs",
      "single_owner_required",
      "request_scoped_evaluation_required",
      "recovery_material_included",
      "raw_crypto_payload_included",
      "element_interoperability_status",
      "desktop_only",
      "safe_summary",
      "redaction_status",
    ]) ||
    value.schema_version !== "uaa-matrix-crypto-posture.v1" ||
    !isCommunicationsSafeRef(value.posture_ref) ||
    value.runtime_status !== "adapter_required" ||
    value.freshness !== "unknown" ||
    !isCommunicationsSafeRefArray(value.authority_lane_refs, 17) ||
    !isCommunicationsSafeRefArray(
      value.accepted_authority_operation_refs,
      17,
    ) ||
    !isCommunicationsSafeRefArray(value.live_executor_operation_refs, 17) ||
    !isCommunicationsSafeRefArray(value.blocked_operation_refs, 17) ||
    value.authority_lane_refs.length !== 17 ||
    value.accepted_authority_operation_refs.length !== 17 ||
    value.live_executor_operation_refs.length !== 0 ||
    value.blocked_operation_refs.length !== 17 ||
    new Set(value.authority_lane_refs).size !== 17 ||
    new Set(value.accepted_authority_operation_refs).size !== 17 ||
    new Set(value.blocked_operation_refs).size !== 17 ||
    !isCommunicationsSafeRef(value.provider_ref) ||
    !isCommunicationsSafeRef(value.runtime_ref) ||
    !isCommunicationsSafeRef(value.store_backend_ref) ||
    !isCommunicationsSafeRef(value.key_backend_ref) ||
    !isCommunicationsSafeRef(value.backup_backend_ref) ||
    !isCommunicationsSafeRefArray(value.reason_refs, 32) ||
    !isCommunicationsSafeRefArray(value.blocker_refs, 32) ||
    !isCommunicationsSafeRefArray(value.evidence_refs, 32) ||
    value.single_owner_required !== true ||
    value.request_scoped_evaluation_required !== true ||
    value.recovery_material_included !== false ||
    value.raw_crypto_payload_included !== false ||
    value.element_interoperability_status !== "external_facility_required" ||
    value.desktop_only !== true ||
    !isCommunicationsSafeSummary(value.safe_summary) ||
    value.redaction_status !== "safe_refs_only"
  ) {
    throw new Error("Matrix crypto posture response failed safe validation.");
  }
  return value as unknown as MatrixCryptoPosture;
}

export async function loadMatrixMessagingPosture(): Promise<MatrixMessagingPosture> {
  const value = await readEnvelope<unknown>(
    API_ENDPOINTS.communicationsMatrixMessagingPosture,
  );
  if (
    !isCommunicationsRecord(value) ||
    !hasExactCommunicationsKeys(value, [
      "schema_version",
      "posture_ref",
      "runtime_status",
      "authority_lane_refs",
      "live_executor_operation_refs",
      "blocked_operation_refs",
      "broker_ref",
      "provider_ref",
      "sdk_ref",
      "crypto_store_ref",
      "outbox_store_ref",
      "reason_refs",
      "element_interoperability_status",
      "request_scoped_evaluation_required",
      "approval_ref_is_authority",
      "autonomous_send_enabled",
      "remote_homeservers_enabled",
      "desktop_only",
      "raw_content_included",
      "safe_summary",
    ]) ||
    value.schema_version !== "uaa-matrix-messaging-posture.v1" ||
    !isCommunicationsSafeRef(value.posture_ref) ||
    ![
      "ready",
      "configuration_required",
      "blocked",
      "external_facility_required",
    ].includes(String(value.runtime_status)) ||
    !isCommunicationsSafeRefArray(value.authority_lane_refs, 15) ||
    !isCommunicationsSafeRefArray(value.live_executor_operation_refs, 15) ||
    !isCommunicationsSafeRefArray(value.blocked_operation_refs, 15) ||
    value.authority_lane_refs.length !== 15 ||
    value.live_executor_operation_refs.length !== 15 ||
    ![0, 15].includes(value.blocked_operation_refs.length) ||
    new Set(value.authority_lane_refs).size !== 15 ||
    new Set(value.live_executor_operation_refs).size !== 15 ||
    new Set(value.blocked_operation_refs).size !==
      value.blocked_operation_refs.length ||
    (value.runtime_status === "ready"
      ? value.blocked_operation_refs.length !== 0
      : value.blocked_operation_refs.length !== 15) ||
    !isCommunicationsSafeRef(value.broker_ref) ||
    value.provider_ref !== "provider-ref:communications:matrix" ||
    value.sdk_ref !== "sdk-ref:matrix-rust-sdk:0.18.0" ||
    !isCommunicationsSafeRef(value.crypto_store_ref) ||
    !isCommunicationsSafeRef(value.outbox_store_ref) ||
    !isCommunicationsSafeRefArray(value.reason_refs, 32) ||
    new Set(value.reason_refs).size !== value.reason_refs.length ||
    !["passed", "failed", "external_facility_required"].includes(
      String(value.element_interoperability_status),
    ) ||
    value.request_scoped_evaluation_required !== true ||
    value.approval_ref_is_authority !== false ||
    value.autonomous_send_enabled !== false ||
    value.remote_homeservers_enabled !== false ||
    value.desktop_only !== true ||
    value.raw_content_included !== false ||
    !isCommunicationsSafeSummary(value.safe_summary)
  ) {
    throw new Error("Matrix messaging posture response failed safe validation.");
  }
  return value as unknown as MatrixMessagingPosture;
}

export async function loadMatrixRoomsMediaPosture(): Promise<MatrixRoomsMediaPosture> {
  const value = await readEnvelope<unknown>(
    API_ENDPOINTS.communicationsMatrixRoomsMediaPosture,
  );
  if (
    !isCommunicationsRecord(value) ||
    !hasExactCommunicationsKeys(value, [
      "schema_version",
      "posture_ref",
      "runtime_status",
      "authority_lane_refs",
      "implemented_core_operation_refs",
      "blocked_live_operation_refs",
      "media_max_bytes",
      "media_type_policy_ref",
      "quarantine_policy_ref",
      "preview_policy_ref",
      "progress_policy_ref",
      "cancel_policy_ref",
      "retry_policy_ref",
      "search_index_policy_ref",
      "element_interoperability_status",
      "reason_refs",
      "request_scoped_evaluation_required",
      "standing_authority_granted",
      "multi_account_enabled",
      "raw_content_included",
    ]) ||
    value.schema_version !== "uaa-matrix-rooms-media-posture.v1" ||
    !isCommunicationsSafeRef(value.posture_ref) ||
    value.runtime_status !== "configuration_required" ||
    !isCommunicationsSafeRefArray(value.authority_lane_refs, 20) ||
    !isCommunicationsSafeRefArray(value.implemented_core_operation_refs, 20) ||
    !isCommunicationsSafeRefArray(value.blocked_live_operation_refs, 20) ||
    value.authority_lane_refs.length !== 20 ||
    value.implemented_core_operation_refs.length !== 20 ||
    value.blocked_live_operation_refs.length !== 20 ||
    new Set(value.authority_lane_refs).size !== 20 ||
    new Set(value.implemented_core_operation_refs).size !== 20 ||
    new Set(value.blocked_live_operation_refs).size !== 20 ||
    value.media_max_bytes !== 24576 ||
    !isCommunicationsSafeRef(value.media_type_policy_ref) ||
    !isCommunicationsSafeRef(value.quarantine_policy_ref) ||
    !isCommunicationsSafeRef(value.preview_policy_ref) ||
    !isCommunicationsSafeRef(value.progress_policy_ref) ||
    !isCommunicationsSafeRef(value.cancel_policy_ref) ||
    !isCommunicationsSafeRef(value.retry_policy_ref) ||
    !isCommunicationsSafeRef(value.search_index_policy_ref) ||
    value.element_interoperability_status !== "external_facility_required" ||
    !isCommunicationsSafeRefArray(value.reason_refs, 32) ||
    new Set(value.reason_refs).size !== value.reason_refs.length ||
    value.request_scoped_evaluation_required !== true ||
    value.standing_authority_granted !== false ||
    value.multi_account_enabled !== false ||
    value.raw_content_included !== false
  ) {
    throw new Error("Matrix rooms and media posture response failed safe validation.");
  }
  return value as unknown as MatrixRoomsMediaPosture;
}

export async function loadMatrixIntelligencePosture(): Promise<MatrixIntelligencePosture> {
  const value = await readEnvelope<unknown>(
    API_ENDPOINTS.communicationsMatrixIntelligencePosture,
  );
  const expectedFamilies = [
    "context_materialization",
    "provider_invocation",
    "proposal_persistence",
    "attachment_analysis",
  ];
  if (
    !isCommunicationsRecord(value) ||
    !hasExactCommunicationsKeys(value, [
      "schema_version",
      "posture_ref",
      "runtime_status",
      "family_postures",
      "policy_modes",
      "proposal_kinds",
      "cross_surface_link_refs",
      "request_scoped_evaluation_required",
      "standing_content_authority",
      "provider_invocation_enabled",
      "attachment_analysis_enabled",
      "autonomous_send_enabled",
      "automatic_memory_write_enabled",
      "context_injection_enabled",
      "raw_content_persisted",
      "desktop_only",
      "safe_summary",
    ]) ||
    value.schema_version !== "uaa-matrix-intelligence-posture.v1" ||
    !isCommunicationsSafeRef(value.posture_ref) ||
    value.runtime_status !== "partial_exact_local_lanes" ||
    !Array.isArray(value.family_postures) ||
    value.family_postures.length !== 4 ||
    !value.family_postures.every((item, index) =>
      isCommunicationsRecord(item) &&
      hasExactCommunicationsKeys(item, [
        "family",
        "authority_lane_refs",
        "status",
        "stage_b_runtime_enabled",
        "blocker_refs",
        "safe_summary",
      ]) &&
      item.family === expectedFamilies[index] &&
      ["accepted_request_scoped", "blocked_missing_exact_authority"].includes(
        String(item.status),
      ) &&
      typeof item.stage_b_runtime_enabled === "boolean" &&
      ((item.status === "accepted_request_scoped") === item.stage_b_runtime_enabled) &&
      isCommunicationsSafeRefArray(item.authority_lane_refs, 8) &&
      isCommunicationsSafeRefArray(item.blocker_refs, 8) &&
      isCommunicationsSafeSummary(item.safe_summary),
    ) ||
    !Array.isArray(value.policy_modes) ||
    value.policy_modes.join("|") !== "off|ask_each_time|scoped_allow" ||
    !Array.isArray(value.proposal_kinds) ||
    value.proposal_kinds.length !== 12 ||
    !value.proposal_kinds.every((item) => typeof item === "string") ||
    new Set(value.proposal_kinds).size !== 12 ||
    !isCommunicationsSafeRefArray(value.cross_surface_link_refs, 8) ||
    value.request_scoped_evaluation_required !== true ||
    value.standing_content_authority !== false ||
    value.provider_invocation_enabled !== false ||
    value.attachment_analysis_enabled !== false ||
    value.autonomous_send_enabled !== false ||
    value.automatic_memory_write_enabled !== false ||
    value.context_injection_enabled !== false ||
    value.raw_content_persisted !== false ||
    value.desktop_only !== true ||
    !isCommunicationsSafeSummary(value.safe_summary)
  ) {
    throw new Error("Matrix intelligence posture response failed safe validation.");
  }
  return value as unknown as MatrixIntelligencePosture;
}

export async function loadMatrixHardeningPosture(): Promise<MatrixHardeningPosture> {
  const value = await readEnvelope<unknown>(
    API_ENDPOINTS.communicationsMatrixHardeningPosture,
  );
  const expectedCategories = [
    "large_room_backpressure",
    "cache_queue_bounds",
    "migration_multi_device",
    "rate_limit_malicious_events",
    "retention_deletion_low_disk",
    "restart_offline_recovery",
    "accessibility_keyboard_focus",
    "localization_readiness",
    "telemetry_redaction",
    "dependency_sbom",
    "rollback_safe_disable",
    "element_interoperability",
  ];
  if (
    !isCommunicationsRecord(value) ||
    !hasExactCommunicationsKeys(value, [
      "schema_version",
      "posture_ref",
      "runtime_status",
      "checks",
      "budgets",
      "blocked_later_lane_refs",
      "request_scoped_runtime_evaluation_required",
      "new_runtime_authority_granted",
      "calls_enabled",
      "agent_participants_enabled",
      "hosted_infrastructure_enabled",
      "public_federation_enabled",
      "production_deployment_enabled",
      "element_interoperability_status",
      "raw_content_included",
      "local_paths_included",
      "desktop_only",
      "safe_summary",
    ]) ||
    value.schema_version !== "uaa-matrix-hardening-posture.v1" ||
    !isCommunicationsSafeRef(value.posture_ref) ||
    value.runtime_status !== "partial_hardening_evidence" ||
    !Array.isArray(value.checks) ||
    value.checks.length !== 12 ||
    !value.checks.every((item, index) =>
      isCommunicationsRecord(item) &&
      hasExactCommunicationsKeys(item, [
        "check_ref",
        "category",
        "status",
        "evidence_refs",
        "blocker_refs",
        "safe_summary",
        "raw_content_included",
      ]) &&
      isCommunicationsSafeRef(item.check_ref) &&
      item.category === expectedCategories[index] &&
      ["passed", "partial", "blocked", "external_facility_required"].includes(
        String(item.status),
      ) &&
      isCommunicationsSafeRefArray(item.evidence_refs, 16) &&
      isCommunicationsSafeRefArray(item.blocker_refs, 16) &&
      (item.status === "passed"
        ? item.evidence_refs.length > 0 && item.blocker_refs.length === 0
        : item.blocker_refs.length > 0) &&
      isCommunicationsSafeSummary(item.safe_summary) &&
      item.raw_content_included === false,
    ) ||
    !Array.isArray(value.budgets) ||
    value.budgets.length !== 8 ||
    !value.budgets.every((item) =>
      isCommunicationsRecord(item) &&
      hasExactCommunicationsKeys(item, [
        "budget_ref",
        "unit",
        "limit",
        "evidence_ref",
      ]) &&
      isCommunicationsSafeRef(item.budget_ref) &&
      ["bytes", "events", "rooms", "records", "relations"].includes(
        String(item.unit),
      ) &&
      typeof item.limit === "number" &&
      Number.isInteger(item.limit) &&
      item.limit > 0 &&
      item.limit <= 64 * 1024 * 1024 &&
      isCommunicationsSafeRef(item.evidence_ref),
    ) ||
    !isCommunicationsSafeRefArray(value.blocked_later_lane_refs, 8) ||
    value.blocked_later_lane_refs.length !== 5 ||
    value.request_scoped_runtime_evaluation_required !== true ||
    value.new_runtime_authority_granted !== false ||
    value.calls_enabled !== false ||
    value.agent_participants_enabled !== false ||
    value.hosted_infrastructure_enabled !== false ||
    value.public_federation_enabled !== false ||
    value.production_deployment_enabled !== false ||
    value.element_interoperability_status !== "external_facility_required" ||
    value.raw_content_included !== false ||
    value.local_paths_included !== false ||
    value.desktop_only !== true ||
    !isCommunicationsSafeSummary(value.safe_summary)
  ) {
    throw new Error("Matrix hardening posture response failed safe validation.");
  }
  return value as unknown as MatrixHardeningPosture;
}

function isSafeCommunicationConversation(
  value: unknown,
): value is CommunicationConversation {
  if (!isCommunicationsRecord(value)) {
    return false;
  }
  return (
    hasExactCommunicationsKeys(value, [
      "conversation_ref",
      "account_ref",
      "provider_ref",
      "kind",
      "member_refs",
      "unread_count",
      "freshness",
      "redaction_status",
      "evidence_refs",
    ]) &&
    isCommunicationsSafeRef(value.conversation_ref) &&
    isCommunicationsSafeRef(value.account_ref) &&
    isCommunicationsSafeRef(value.provider_ref) &&
    ["direct", "room", "space", "unknown"].includes(String(value.kind)) &&
    isCommunicationsSafeRefArray(value.member_refs) &&
    typeof value.unread_count === "number" &&
    Number.isInteger(value.unread_count) &&
    value.unread_count >= 0 &&
    value.unread_count <= 100_000 &&
    ["current", "stale", "unknown"].includes(String(value.freshness)) &&
    ["safe_refs_only", "content_omitted", "unknown"].includes(
      String(value.redaction_status),
    ) &&
    isCommunicationsSafeRefArray(value.evidence_refs, 32)
  );
}

export async function loadCommunicationsRooms(): Promise<CommunicationsRoomPage> {
  const value = await readEnvelope<unknown>(API_ENDPOINTS.communicationsRooms);
  if (
    !isCommunicationsRecord(value) ||
    !hasExactCommunicationsKeys(value, [
      "items",
      "pagination",
      "freshness",
      "reason_codes",
      "blocker_codes",
      "safe_summary",
      "message_read_performed",
      "raw_content_omitted",
    ]) ||
    !Array.isArray(value.items) ||
    !value.items.every(isSafeCommunicationConversation) ||
    !isSafeCommunicationsPagination(value.pagination) ||
    value.message_read_performed !== false ||
    value.raw_content_omitted !== true ||
    !["current", "stale", "unknown"].includes(String(value.freshness)) ||
    !isCommunicationsSafeCodeArray(value.reason_codes) ||
    !isCommunicationsSafeCodeArray(value.blocker_codes) ||
    !isCommunicationsSafeSummary(value.safe_summary) ||
    !isCommunicationsRecord(value.pagination) ||
    value.pagination.returned_count !== value.items.length
  ) {
    throw new Error("Communications room response failed safe validation.");
  }
  return value as unknown as CommunicationsRoomPage;
}

function isSafeConversationSourcePosture(value: unknown): boolean {
  if (!isCommunicationsRecord(value)) return false;
  return (
    hasExactCommunicationsKeys(value, [
      "source_ref", "source_kind", "schema_version", "observed_at", "freshness",
      "coverage_ref", "retention_ref", "privacy_ref", "evidence_refs",
      "connector_configured", "live_sync_enabled", "external_actions_enabled",
      "raw_content_persisted",
    ]) &&
    isCommunicationsSafeRef(value.source_ref) &&
    value.source_kind === "reviewed_manual_import" &&
    value.schema_version === "uaa-communications-reviewed-projection.v1" &&
    isCommunicationsTimestamp(value.observed_at) &&
    ["current", "stale", "unknown"].includes(String(value.freshness)) &&
    isCommunicationsSafeRef(value.coverage_ref) &&
    isCommunicationsSafeRef(value.retention_ref) &&
    isCommunicationsSafeRef(value.privacy_ref) &&
    isCommunicationsSafeRefArray(value.evidence_refs, 32) &&
    value.connector_configured === false &&
    value.live_sync_enabled === false &&
    value.external_actions_enabled === false &&
    value.raw_content_persisted === false
  );
}

function isSafeReviewedCommunicationThread(value: unknown): boolean {
  if (!isCommunicationsRecord(value)) return false;
  return (
    hasExactCommunicationsKeys(value, [
      "conversation_ref", "channel_ref", "participant_refs", "item_refs",
      "latest_activity_at", "needs_attention", "safe_label", "safe_summary",
      "evidence_refs",
    ]) &&
    isCommunicationsSafeRef(value.conversation_ref) &&
    isCommunicationsSafeRef(value.channel_ref) &&
    isCommunicationsSafeRefArray(value.participant_refs) &&
    isCommunicationsSafeRefArray(value.item_refs) &&
    isCommunicationsTimestamp(value.latest_activity_at) &&
    typeof value.needs_attention === "boolean" &&
    isCommunicationsSafeSummary(value.safe_label) &&
    String(value.safe_label).length <= 120 &&
    isCommunicationsSafeSummary(value.safe_summary) &&
    isCommunicationsSafeRefArray(value.evidence_refs, 32)
  );
}

async function loadCommunicationsConversationsWithReadContext(
  readLimiter = defaultControlCenterReadLimiter,
  expectedBinding: BackendTruthReadBinding | null = null,
): Promise<ReviewedCommunicationsThreadPage> {
  const value = await readEnvelope<unknown>(
    API_ENDPOINTS.communicationsConversations,
    readLimiter,
    expectedBinding,
  );
  if (
    !isCommunicationsRecord(value) ||
    !hasExactCommunicationsKeys(value, [
      "status", "source", "items", "pagination", "reason_codes", "blocker_codes",
      "safe_summary", "read_only", "send_enabled", "reply_enabled",
      "delete_enabled", "moderate_enabled", "raw_content_omitted",
    ]) ||
    !["ready", "empty", "stale", "blocked"].includes(String(value.status)) ||
    !(value.source === null || isSafeConversationSourcePosture(value.source)) ||
    !Array.isArray(value.items) ||
    value.items.length > 50 ||
    !value.items.every(isSafeReviewedCommunicationThread) ||
    !isSafeCommunicationsPagination(value.pagination) ||
    !isCommunicationsRecord(value.pagination) ||
    value.pagination.returned_count !== value.items.length ||
    !isCommunicationsSafeCodeArray(value.reason_codes) ||
    !isCommunicationsSafeCodeArray(value.blocker_codes) ||
    !isCommunicationsSafeSummary(value.safe_summary) ||
    value.read_only !== true ||
    value.send_enabled !== false ||
    value.reply_enabled !== false ||
    value.delete_enabled !== false ||
    value.moderate_enabled !== false ||
    value.raw_content_omitted !== true
  ) {
    throw new Error("Reviewed communications response failed safe validation.");
  }
  return value as unknown as ReviewedCommunicationsThreadPage;
}

export async function loadCommunicationsConversations(): Promise<ReviewedCommunicationsThreadPage> {
  return loadCommunicationsConversationsWithReadContext();
}

export async function loadCommunicationsFailedSends(): Promise<CommunicationsFailedSendPage> {
  const value = await readEnvelope<unknown>(
    API_ENDPOINTS.communicationsFailedSends,
  );
  if (
    !isCommunicationsRecord(value) ||
    !hasExactCommunicationsKeys(value, [
      "receipt_refs",
      "pagination",
      "reason_codes",
      "blocker_codes",
      "safe_summary",
      "send_performed",
      "raw_content_omitted",
    ]) ||
    !Array.isArray(value.receipt_refs) ||
    !isCommunicationsSafeRefArray(value.receipt_refs) ||
    !isSafeCommunicationsPagination(value.pagination) ||
    value.send_performed !== false ||
    value.raw_content_omitted !== true ||
    !isCommunicationsSafeCodeArray(value.reason_codes) ||
    !isCommunicationsSafeCodeArray(value.blocker_codes) ||
    !isCommunicationsSafeSummary(value.safe_summary) ||
    !isCommunicationsRecord(value.pagination) ||
    value.pagination.returned_count !== value.receipt_refs.length
  ) {
    throw new Error("Communications failed-send response failed safe validation.");
  }
  return value as unknown as CommunicationsFailedSendPage;
}

export async function loadCommunicationsSecurityPosture(): Promise<CommunicationsSecurityPosture> {
  const value = await readEnvelope<unknown>(
    API_ENDPOINTS.communicationsSecurityPosture,
  );
  if (
    !isCommunicationsRecord(value) ||
    !hasExactCommunicationsKeys(value, [
      "posture_ref",
      "provider_ref",
      "encryption_posture_ref",
      "key_lifecycle_posture_ref",
      "cache_posture_ref",
      "crypto_runtime_status",
      "crypto_availability",
      "crypto_authority_lane_refs",
      "crypto_live_executor_refs",
      "crypto_blocked_operation_refs",
      "recovery_posture_ref",
      "backup_posture_ref",
      "single_owner_posture_ref",
      "reason_codes",
      "blocker_codes",
      "safe_summary",
      "credentials_loaded",
      "crypto_initialized",
      "local_cache_opened",
      "recovery_material_included",
      "raw_crypto_payload_included",
      "request_scoped_evaluation_required",
      "desktop_only",
    ]) ||
    !isCommunicationsSafeRef(value.posture_ref) ||
    !isCommunicationsSafeRef(value.provider_ref) ||
    !isCommunicationsSafeRef(value.encryption_posture_ref) ||
    !isCommunicationsSafeRef(value.key_lifecycle_posture_ref) ||
    !isCommunicationsSafeRef(value.cache_posture_ref) ||
    value.crypto_runtime_status !== "adapter_required" ||
    !isSafeCommunicationsAvailability(value.crypto_availability) ||
    !isCommunicationsSafeRefArray(value.crypto_authority_lane_refs, 17) ||
    !isCommunicationsSafeRefArray(value.crypto_live_executor_refs, 17) ||
    !isCommunicationsSafeRefArray(value.crypto_blocked_operation_refs, 17) ||
    value.crypto_authority_lane_refs.length !== 17 ||
    value.crypto_live_executor_refs.length !== 0 ||
    value.crypto_blocked_operation_refs.length !== 17 ||
    !isCommunicationsSafeRef(value.recovery_posture_ref) ||
    !isCommunicationsSafeRef(value.backup_posture_ref) ||
    !isCommunicationsSafeRef(value.single_owner_posture_ref) ||
    value.credentials_loaded !== false ||
    value.crypto_initialized !== false ||
    value.local_cache_opened !== false ||
    value.recovery_material_included !== false ||
    value.raw_crypto_payload_included !== false ||
    value.request_scoped_evaluation_required !== true ||
    value.desktop_only !== true ||
    !isCommunicationsSafeCodeArray(value.reason_codes) ||
    !isCommunicationsSafeCodeArray(value.blocker_codes) ||
    !isCommunicationsSafeSummary(value.safe_summary)
  ) {
    throw new Error("Communications security response failed safe validation.");
  }
  return value as unknown as CommunicationsSecurityPosture;
}

export async function loadCommunicationsReceipt(
  receiptRef: string,
): Promise<CommunicationsReceipt> {
  if (!isCommunicationsSafeRef(receiptRef)) {
    throw new Error("Communications receipt reference is invalid.");
  }
  const value = await readEnvelope<unknown>(
    communicationsReceiptEndpoint(receiptRef),
  );
  if (
    !isCommunicationsRecord(value) ||
    !hasExactCommunicationsKeys(value, [
      "receipt_ref",
      "operation_ref",
      "request_ref",
      "provider_ref",
      "account_ref",
      "conversation_ref",
      "outcome",
      "occurred_at",
      "reason_codes",
      "blocker_codes",
      "evidence_refs",
      "redaction_status",
      "safe_summary",
      "network_performed",
      "authentication_performed",
      "message_read_performed",
      "message_sent",
      "raw_content_stored",
      "provider_payload_persisted",
      "approval_or_lease_minted",
    ]) ||
    value.receipt_ref !== receiptRef ||
    !isCommunicationsSafeRef(value.operation_ref) ||
    !isCommunicationsSafeRef(value.request_ref) ||
    !isCommunicationsSafeRef(value.provider_ref) ||
    !isOptionalCommunicationsSafeRef(value.account_ref) ||
    !isOptionalCommunicationsSafeRef(value.conversation_ref) ||
    !["inspected", "not_executed", "blocked"].includes(String(value.outcome)) ||
    !isCommunicationsTimestamp(value.occurred_at) ||
    !isCommunicationsSafeCodeArray(value.reason_codes) ||
    !isCommunicationsSafeCodeArray(value.blocker_codes) ||
    !isCommunicationsSafeRefArray(value.evidence_refs, 32) ||
    !["safe_refs_only", "content_omitted"].includes(
      String(value.redaction_status),
    ) ||
    !isCommunicationsSafeSummary(value.safe_summary) ||
    value.network_performed !== false ||
    value.authentication_performed !== false ||
    value.message_read_performed !== false ||
    value.message_sent !== false ||
    value.raw_content_stored !== false ||
    value.provider_payload_persisted !== false ||
    value.approval_or_lease_minted !== false
  ) {
    throw new Error("Communications receipt response failed safe validation.");
  }
  return value as unknown as CommunicationsReceipt;
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

export interface RuntimeSkillMarketplacePostureLoadResult {
  posture: RuntimeSkillMarketplacePostureReadModel;
  backendValidated: boolean;
  catalogDisplayable: boolean;
}

export async function loadRuntimeSkillMarketplacePosture(): Promise<RuntimeSkillMarketplacePostureLoadResult> {
  if (!API_BASE_POLICY.allowed) {
    return {
      posture: mockControlCenterData.runtimeSkillMarketplacePosture,
      backendValidated: false,
      catalogDisplayable: false,
    };
  }
  try {
    const posture = await readEnvelope<unknown>(
      API_ENDPOINTS.runtimeSkillMarketplacePosture,
    );
    if (
      isSafeRuntimeSkillMarketplacePosture(posture) &&
      (await hasMatchingSkillMarketplaceSnapshotHash(posture))
    ) {
      return {
        posture,
        backendValidated: true,
        catalogDisplayable: posture.catalog_freshness.catalog_displayable,
      };
    }
  } catch {
    // The Studio discovery surface fails closed to an empty, non-authoritative catalog.
  }
  return {
    posture: mockControlCenterData.runtimeSkillMarketplacePosture,
    backendValidated: false,
    catalogDisplayable: false,
  };
}

export async function computeRuntimeSkillMarketplaceSnapshotHashRef(
  posture: RuntimeSkillMarketplacePostureReadModel,
): Promise<string> {
  if (!globalThis.crypto?.subtle) {
    throw new Error("WEB_CRYPTO_UNAVAILABLE");
  }
  const material: Record<string, unknown> = { ...posture };
  delete material.snapshot_hash_ref;
  const encoded = new TextEncoder().encode(portableCanonicalJson(material));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", encoded);
  const hex = Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
  return `snapshot-hash-ref:skill-marketplace-posture:${hex}`;
}

async function hasMatchingSkillMarketplaceSnapshotHash(
  posture: RuntimeSkillMarketplacePostureReadModel,
): Promise<boolean> {
  return (
    posture.snapshot_hash_ref ===
    (await computeRuntimeSkillMarketplaceSnapshotHashRef(posture))
  );
}

function portableCanonicalJson(value: unknown): string {
  if (value === null) {
    return "null";
  }
  if (value === true) {
    return "true";
  }
  if (value === false) {
    return "false";
  }
  if (typeof value === "string") {
    return pythonCompatibleJsonString(value);
  }
  if (typeof value === "number") {
    return portableCanonicalNumber(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map(portableCanonicalJson).join(",")}]`;
  }
  if (isPlainRecord(value)) {
    return `{${Object.keys(value)
      .sort()
      .map(
        (key) =>
          `${pythonCompatibleJsonString(key)}:${portableCanonicalJson(value[key])}`,
      )
      .join(",")}}`;
  }
  throw new Error("SKILL_MARKETPLACE_CANONICAL_VALUE_INVALID");
}

function pythonCompatibleJsonString(value: string): string {
  return JSON.stringify(value).replace(/[\u007f-\uffff]/g, (character) =>
    `\\u${character.charCodeAt(0).toString(16).padStart(4, "0")}`,
  );
}

function portableCanonicalNumber(value: number): string {
  if (!Number.isFinite(value)) {
    throw new Error("SKILL_MARKETPLACE_CANONICAL_NUMBER_INVALID");
  }
  if (Object.is(value, -0)) {
    return "-0";
  }
  const text = value.toString().toLowerCase();
  if (!text.includes("e")) {
    return text;
  }
  const [rawMantissa, rawExponent] = text.split("e");
  const negative = rawMantissa.startsWith("-");
  const mantissa = negative ? rawMantissa.slice(1) : rawMantissa;
  const [integer, fraction = ""] = mantissa.split(".");
  const digits = integer + fraction;
  const decimalIndex = integer.length + Number.parseInt(rawExponent, 10);
  const plain =
    decimalIndex <= 0
      ? `0.${"0".repeat(-decimalIndex)}${digits}`
      : decimalIndex >= digits.length
        ? `${digits}${"0".repeat(decimalIndex - digits.length)}`
        : `${digits.slice(0, decimalIndex)}.${digits.slice(decimalIndex)}`;
  return `${negative ? "-" : ""}${plain}`;
}

function crmStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string" && item.length > 0);
}

function crmArraysEqual(left: string[], right: string[]): boolean {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

async function isSafeCrmSocialProjection(crm: CrmLocalCommandCenterReadModel | undefined): Promise<boolean> {
  const projection = crm?.social_relationship_projection;
  if (
    crm === undefined ||
    projection === undefined ||
    projection === null ||
    typeof projection !== "object" ||
    projection.contract_ref !== "contract-ref:crm-social-relationship-projection:v1" ||
    projection.projection_ref !== "projection-ref:crm-social-relationship-context:v1" ||
    projection.owner_ref !== "owner-ref:crm" ||
    projection.selection_rule_ref !== "selection-rule-ref:crm-social:person-tag-social-context" ||
    projection.source_posture_ref !== "source-posture-ref:crm-social:reviewed-local" ||
    projection.freshness_ref !== "freshness-ref:crm-social:derived-from-crm-snapshot" ||
    projection.api_ref !== "GET /control-center/crm/relationships" ||
    projection.cli_ref !== "repo-local-command:uaa-crm:inspect-social-relationships" ||
    projection.backend_owned !== true ||
    projection.read_only !== true ||
    projection.stable_deep_links !== true ||
    projection.copies_relationship_truth !== false ||
    projection.live_source_access_enabled !== false ||
    projection.connector_runtime_enabled !== false ||
    projection.provider_model_call_enabled !== false ||
    projection.publishing_enabled !== false ||
    projection.external_write_enabled !== false ||
    projection.production_authority_enabled !== false ||
    !crmStringArray(projection.evidence_refs) ||
    !Number.isInteger(projection.total_item_count) ||
    projection.total_item_count < 0 ||
    !Number.isInteger(projection.returned_item_count) ||
    !Array.isArray(projection.items) ||
    projection.returned_item_count !== projection.items.length ||
    projection.items.length > 50
  ) {
    return false;
  }

  const relationshipByRef = new Map(
    crm.relationships.map((relationship) => [relationship.relationship_ref, relationship]),
  );
  const personByRef = new Map(crm.people.map((person) => [person.person_ref, person]));
  const organizationByRef = new Map(
    crm.organizations.map((organization) => [organization.organization_ref, organization]),
  );
  if (
    relationshipByRef.size !== crm.relationships.length ||
    personByRef.size !== crm.people.length ||
    organizationByRef.size !== crm.organizations.length
  ) {
    return false;
  }

  const selectedRelationshipRefs = new Set<string>();
  for (const person of crm.people) {
    if (!crmStringArray(person.relationship_refs) || !crmStringArray(person.tags)) {
      return false;
    }
    if (!person.tags.includes("social-context")) {
      continue;
    }
    for (const relationshipRef of person.relationship_refs) {
      const relationship = relationshipByRef.get(relationshipRef);
      if (relationship?.person_ref !== person.person_ref) {
        return false;
      }
      selectedRelationshipRefs.add(relationshipRef);
    }
  }
  const expectedRelationshipRefs = [...selectedRelationshipRefs].sort();
  const expectedPageRefs = expectedRelationshipRefs.slice(0, 50);
  if (
    projection.total_item_count !== expectedRelationshipRefs.length ||
    projection.returned_item_count !== expectedPageRefs.length ||
    projection.truncated !== expectedRelationshipRefs.length > expectedPageRefs.length ||
    projection.items.some((item, index) => item?.relationship_ref !== expectedPageRefs[index])
  ) {
    return false;
  }

  try {
    for (const item of projection.items) {
      if (
        item === null ||
        typeof item !== "object" ||
        typeof item.projection_item_ref !== "string" ||
        typeof item.relationship_ref !== "string" ||
        typeof item.person_ref !== "string" ||
        (item.organization_ref !== null &&
          item.organization_ref !== undefined &&
          typeof item.organization_ref !== "string") ||
        typeof item.crm_deep_link_ref !== "string" ||
        typeof item.safe_display_label !== "string" ||
        typeof item.safe_summary !== "string" ||
        item.why_shown !==
          "Shown because CRM owns a reviewed relationship tagged for the Social relationship context projection." ||
        typeof item.health_state !== "string" ||
        typeof item.freshness_state !== "string" ||
        !crmStringArray(item.evidence_refs) ||
        !crmStringArray(item.memory_provenance_refs) ||
        !Number.isInteger(item.evidence_ref_total_count) ||
        !Number.isInteger(item.memory_provenance_ref_total_count) ||
        item.backend_owned !== true ||
        item.read_only !== true ||
        item.raw_content_included !== false ||
        item.connector_runtime_enabled !== false ||
        item.external_action_enabled !== false
      ) {
        return false;
      }
      const relationship = relationshipByRef.get(item.relationship_ref);
      const person = personByRef.get(item.person_ref);
      if (
        relationship === undefined ||
        person === undefined ||
        relationship.person_ref !== item.person_ref ||
        relationship.organization_ref !== item.organization_ref ||
        !person.tags.includes("social-context") ||
        !person.relationship_refs.includes(item.relationship_ref) ||
        (item.organization_ref !== null &&
          item.organization_ref !== undefined &&
          !organizationByRef.has(item.organization_ref)) ||
        item.safe_display_label !== relationship.safe_display_label ||
        item.safe_summary !== relationship.safe_summary ||
        item.health_state !== relationship.health_state ||
        item.freshness_state !== relationship.stale_state ||
        !crmArraysEqual(item.evidence_refs, relationship.evidence_refs.slice(0, 20)) ||
        item.evidence_ref_total_count !== relationship.evidence_refs.length ||
        item.evidence_refs_truncated !== relationship.evidence_refs.length > 20 ||
        !crmArraysEqual(item.memory_provenance_refs, relationship.memory_provenance_refs.slice(0, 20)) ||
        item.memory_provenance_ref_total_count !== relationship.memory_provenance_refs.length ||
        item.memory_provenance_refs_truncated !== relationship.memory_provenance_refs.length > 20
      ) {
        return false;
      }
      const normalized = item.relationship_ref
        .toLowerCase()
        .replace(/[^a-z0-9_.:-]+/g, "-")
        .replace(/^-+|-+$/g, "");
      if (!normalized) return false;
      const digest = await sha256Hex(item.relationship_ref);
      const suffix = `${normalized.slice(0, 80)}-${digest.slice(0, 16)}`;
      if (
        item.projection_item_ref !== `projection-item-ref:crm-social:${suffix}` ||
        item.crm_deep_link_ref !== `control-center-deep-link-ref:crm:${suffix}`
      ) {
        return false;
      }
    }
  } catch {
    return false;
  }
  return true;
}

export async function loadControlCenterData(
  expectedBinding: BackendTruthReadBinding | null = null,
): Promise<ControlCenterData> {
  if (!API_BASE_POLICY.allowed) {
    if (strictBackendModeEnabled()) {
      throw new StrictBackendDataError();
    }
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
    endpoint.startsWith("/api/runtime/")
      ? Promise.resolve().then(() =>
          readEnvelope<T>(endpoint, loadReadLimiter, expectedBinding),
        )
      : readEnvelope<T>(endpoint, loadReadLimiter, expectedBinding);

  const workBoardSettledPromise = Promise.allSettled([
    read<WorkBoardReadModel>(API_ENDPOINTS.controlCenterWorkBoard),
  ] as const);
  const communicationsProjectionSettledPromise = Promise.allSettled([
    loadCommunicationsConversationsWithReadContext(
      loadReadLimiter,
      expectedBinding,
    ),
  ] as const);
  const capabilitySurfaceSettledPromise = Promise.allSettled([
    read<ControlCenterCapabilitySurfaceReadModel>(
      API_ENDPOINTS.controlCenterCapabilitySurface,
    ),
  ] as const);
  const agentLoopSettledPromise = Promise.allSettled([
    read<FounderLoopAgentLoopThread>(API_ENDPOINTS.founderAgentLoopThread),
  ] as const);
  const runtimeCapabilityDiscoverySettledPromise = Promise.allSettled([
    read<RuntimeCapabilityDiscoveryReadModel>(
      API_ENDPOINTS.runtimeCapabilityDiscovery,
    ),
  ] as const);
  const runtimeInterfaceModeSettledPromise = Promise.allSettled([
    read<RuntimeInterfaceModeReadModel>(API_ENDPOINTS.runtimeInterfaceMode),
  ] as const);
  const runtimeHermesContextPackSettledPromise = Promise.allSettled([
    read<HermesContextPackReadModel>(API_ENDPOINTS.runtimeHermesContextPack),
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
  const runtimeToolRegistrySettledPromise = Promise.allSettled([
    read<RuntimeToolRegistryAvailabilityReadModel>(
      API_ENDPOINTS.runtimeToolRegistry,
    ),
  ] as const);
  const runtimeVirtualProviderMoaSettledPromise = Promise.allSettled([
    read<RuntimeVirtualProviderMoaReadModel>(
      API_ENDPOINTS.runtimeVirtualProviderMoa,
    ),
  ] as const);
  const runtimeUsageCostAnalyticsSettledPromise = Promise.allSettled([
    read<RuntimeUsageCostAnalyticsReadModel>(
      API_ENDPOINTS.runtimeUsageCostAnalytics,
    ),
  ] as const);
  const runtimePromptStabilityTiersSettledPromise = Promise.allSettled([
    read<RuntimePromptStabilityTiersReadModel>(
      API_ENDPOINTS.runtimePromptStabilityTiers,
    ),
  ] as const);
  const runtimeContextBudgetPressureSettledPromise = Promise.allSettled([
    read<RuntimeContextBudgetPressureReadModel>(
      API_ENDPOINTS.runtimeContextBudgetPressure,
    ),
  ] as const);
  const runtimeHardlineCommandBlocklistSettledPromise = Promise.allSettled([
    read<RuntimeHardlineCommandBlocklistReadModel>(
      API_ENDPOINTS.runtimeHardlineCommandBlocklist,
    ),
  ] as const);
  const runtimeManagedScopePolicySettledPromise = Promise.allSettled([
    read<RuntimeManagedScopePolicyReadModel>(
      API_ENDPOINTS.runtimeManagedScopePolicy,
    ),
  ] as const);
  const runtimeDoctorDiagnosticsSettledPromise = Promise.allSettled([
    read<RuntimeDoctorDiagnosticsReadModel>(
      API_ENDPOINTS.runtimeDoctorDiagnostics,
    ),
  ] as const);
  const runtimeSessionContinuitySettledPromise = Promise.allSettled([
    read<RuntimeSessionContinuityReadModel>(
      API_ENDPOINTS.runtimeSessionContinuity,
    ),
  ] as const);
  const runtimeMcpCatalogFilteringSettledPromise = Promise.allSettled([
    read<RuntimeMcpCatalogFilteringReadModel>(
      API_ENDPOINTS.runtimeMcpCatalogFiltering,
    ),
  ] as const);
  const runtimeBackgroundJobsSettledPromise = Promise.allSettled([
    read<RuntimeBackgroundJobsReadModel>(API_ENDPOINTS.runtimeBackgroundJobs),
  ] as const);
  const runtimeSubagentIsolationSettledPromise = Promise.allSettled([
    read<RuntimeSubagentIsolationReadModel>(
      API_ENDPOINTS.runtimeSubagentIsolation,
    ),
  ] as const);
  const runtimeWorktreePerAgentSettledPromise = Promise.allSettled([
    read<RuntimeWorktreePerAgentReadModel>(
      API_ENDPOINTS.runtimeWorktreePerAgent,
    ),
  ] as const);
  const runtimeStagedOrchestrationSettledPromise = Promise.allSettled([
    read<RuntimeStagedOrchestrationReadModel>(
      API_ENDPOINTS.runtimeStagedOrchestration,
    ),
  ] as const);
  const runtimeLspDiagnosticsSettledPromise = Promise.allSettled([
    read<RuntimeLspDiagnosticsReadModel>(
      API_ENDPOINTS.runtimeLspDiagnostics,
    ),
  ] as const);
  const runtimePreviewRailSettledPromise = Promise.allSettled([
    read<RuntimePreviewRailReadModel>(API_ENDPOINTS.runtimePreviewRail),
  ] as const);
  const runtimeSlashCommandRegistrySettledPromise = Promise.allSettled([
    read<RuntimeSlashCommandRegistryReadModel>(
      API_ENDPOINTS.runtimeSlashCommandRegistry,
    ),
  ] as const);
  const runtimeInterruptRedirectSettledPromise = Promise.allSettled([
    read<RuntimeInterruptRedirectReadModel>(
      API_ENDPOINTS.runtimeInterruptRedirect,
    ),
  ] as const);
  const runtimeLoggingProfileSettledPromise = Promise.allSettled([
    read<RuntimeLoggingProfileReadModel>(API_ENDPOINTS.runtimeLoggingProfile),
  ] as const);
  const runtimeResultClassificationSettledPromise = Promise.allSettled([
    read<RuntimeResultClassificationReadModel>(
      API_ENDPOINTS.runtimeResultClassification,
    ),
  ] as const);
  const runtimeVoiceMediaPostureSettledPromise = Promise.allSettled([
    read<RuntimeVoiceMediaPostureReadModel>(
      API_ENDPOINTS.runtimeVoiceMediaPosture,
    ),
  ] as const);
  const runtimeMessagingGatewayPostureSettledPromise = Promise.allSettled([
    read<RuntimeMessagingGatewayPostureReadModel>(
      API_ENDPOINTS.runtimeMessagingGatewayPosture,
    ),
  ] as const);
  const runtimeRemoteExecutionPostureSettledPromise = Promise.allSettled([
    read<RuntimeRemoteExecutionPostureReadModel>(
      API_ENDPOINTS.runtimeRemoteExecutionPosture,
    ),
  ] as const);
  const runtimePluginMetadataPostureSettledPromise = Promise.allSettled([
    read<RuntimePluginMetadataPostureReadModel>(
      API_ENDPOINTS.runtimePluginMetadataPosture,
    ),
  ] as const);
  const runtimeSkillMarketplacePostureSettledPromise = Promise.allSettled([
    read<RuntimeSkillMarketplacePostureReadModel>(
      API_ENDPOINTS.runtimeSkillMarketplacePosture,
    ),
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
  const communicationsProjectionResult =
    await communicationsProjectionSettledPromise;
  const capabilitySurfaceResult = await capabilitySurfaceSettledPromise;
  const agentLoopResult = await agentLoopSettledPromise;
  const runtimeCapabilityDiscoveryResult =
    await runtimeCapabilityDiscoverySettledPromise;
  const runtimeInterfaceModeResult = await runtimeInterfaceModeSettledPromise;
  const runtimeHermesContextPackResult =
    await runtimeHermesContextPackSettledPromise;
  const runtimeRunEventsResult = await runtimeRunEventsSettledPromise;
  const runtimeApprovalBridgeResult =
    await runtimeApprovalBridgeSettledPromise;
  const runtimeStreamingProgressResult =
    await runtimeStreamingProgressSettledPromise;
  const runtimeProfilesResult = await runtimeProfilesSettledPromise;
  const runtimeToolRegistryResult = await runtimeToolRegistrySettledPromise;
  const runtimeVirtualProviderMoaResult =
    await runtimeVirtualProviderMoaSettledPromise;
  const runtimeUsageCostAnalyticsResult =
    await runtimeUsageCostAnalyticsSettledPromise;
  const runtimePromptStabilityTiersResult =
    await runtimePromptStabilityTiersSettledPromise;
  const runtimeContextBudgetPressureResult =
    await runtimeContextBudgetPressureSettledPromise;
  const runtimeHardlineCommandBlocklistResult =
    await runtimeHardlineCommandBlocklistSettledPromise;
  const runtimeManagedScopePolicyResult =
    await runtimeManagedScopePolicySettledPromise;
  const runtimeDoctorDiagnosticsResult =
    await runtimeDoctorDiagnosticsSettledPromise;
  const runtimeSessionContinuityResult =
    await runtimeSessionContinuitySettledPromise;
  const runtimeMcpCatalogFilteringResult =
    await runtimeMcpCatalogFilteringSettledPromise;
  const runtimeBackgroundJobsResult = await runtimeBackgroundJobsSettledPromise;
  const runtimeSubagentIsolationResult =
    await runtimeSubagentIsolationSettledPromise;
  const runtimeWorktreePerAgentResult =
    await runtimeWorktreePerAgentSettledPromise;
  const runtimeStagedOrchestrationResult =
    await runtimeStagedOrchestrationSettledPromise;
  const runtimeLspDiagnosticsResult = await runtimeLspDiagnosticsSettledPromise;
  const runtimePreviewRailResult = await runtimePreviewRailSettledPromise;
  const runtimeSlashCommandRegistryResult =
    await runtimeSlashCommandRegistrySettledPromise;
  const runtimeInterruptRedirectResult =
    await runtimeInterruptRedirectSettledPromise;
  const runtimeLoggingProfileResult = await runtimeLoggingProfileSettledPromise;
  const runtimeResultClassificationResult =
    await runtimeResultClassificationSettledPromise;
  const runtimeVoiceMediaPostureResult =
    await runtimeVoiceMediaPostureSettledPromise;
  const runtimeMessagingGatewayPostureResult =
    await runtimeMessagingGatewayPostureSettledPromise;
  const runtimeRemoteExecutionPostureResult =
    await runtimeRemoteExecutionPostureSettledPromise;
  const runtimePluginMetadataPostureResult =
    await runtimePluginMetadataPostureSettledPromise;
  const runtimeSkillMarketplacePostureResult =
    await runtimeSkillMarketplacePostureSettledPromise;

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
  const runtimeInterfaceMode = fulfilledValue(runtimeInterfaceModeResult[0]);
  const runtimeHermesContextPack = fulfilledValue(
    runtimeHermesContextPackResult[0],
  );
  const runtimeRunEvents = fulfilledValue(runtimeRunEventsResult[0]);
  const runtimeApprovalBridge = fulfilledValue(runtimeApprovalBridgeResult[0]);
  const runtimeStreamingProgress = fulfilledValue(
    runtimeStreamingProgressResult[0],
  );
  const runtimeProfiles = fulfilledValue(runtimeProfilesResult[0]);
  const runtimeToolRegistry = fulfilledValue(runtimeToolRegistryResult[0]);
  const runtimeVirtualProviderMoa = fulfilledValue(
    runtimeVirtualProviderMoaResult[0],
  );
  const runtimeUsageCostAnalytics = fulfilledValue(
    runtimeUsageCostAnalyticsResult[0],
  );
  const runtimePromptStabilityTiers = fulfilledValue(
    runtimePromptStabilityTiersResult[0],
  );
  const runtimeContextBudgetPressure = fulfilledValue(
    runtimeContextBudgetPressureResult[0],
  );
  const runtimeHardlineCommandBlocklist = fulfilledValue(
    runtimeHardlineCommandBlocklistResult[0],
  );
  const runtimeManagedScopePolicy = fulfilledValue(
    runtimeManagedScopePolicyResult[0],
  );
  const runtimeDoctorDiagnostics = fulfilledValue(
    runtimeDoctorDiagnosticsResult[0],
  );
  const runtimeSessionContinuity = fulfilledValue(
    runtimeSessionContinuityResult[0],
  );
  const runtimeMcpCatalogFiltering = fulfilledValue(
    runtimeMcpCatalogFilteringResult[0],
  );
  const runtimeBackgroundJobs = fulfilledValue(runtimeBackgroundJobsResult[0]);
  const runtimeSubagentIsolation = fulfilledValue(
    runtimeSubagentIsolationResult[0],
  );
  const runtimeWorktreePerAgent = fulfilledValue(runtimeWorktreePerAgentResult[0]);
  const runtimeStagedOrchestration = fulfilledValue(
    runtimeStagedOrchestrationResult[0],
  );
  const runtimeLspDiagnostics = fulfilledValue(runtimeLspDiagnosticsResult[0]);
  const runtimePreviewRail = fulfilledValue(runtimePreviewRailResult[0]);
  const runtimeSlashCommandRegistry = fulfilledValue(
    runtimeSlashCommandRegistryResult[0],
  );
  const runtimeInterruptRedirect = fulfilledValue(
    runtimeInterruptRedirectResult[0],
  );
  const runtimeLoggingProfile = fulfilledValue(runtimeLoggingProfileResult[0]);
  const runtimeResultClassification = fulfilledValue(
    runtimeResultClassificationResult[0],
  );
  const runtimeVoiceMediaPosture = fulfilledValue(
    runtimeVoiceMediaPostureResult[0],
  );
  const runtimeMessagingGatewayPosture = fulfilledValue(
    runtimeMessagingGatewayPostureResult[0],
  );
  const runtimeRemoteExecutionPosture = fulfilledValue(
    runtimeRemoteExecutionPostureResult[0],
  );
  const runtimePluginMetadataPosture = fulfilledValue(
    runtimePluginMetadataPostureResult[0],
  );
  const runtimeSkillMarketplacePosture = fulfilledValue(
    runtimeSkillMarketplacePostureResult[0],
  );
  const setupAssistantSource = fulfilledValue(results[7]);
  const normalizedSetupAssistant = normalizeMacOSSetupAssistant(
    setupAssistantSource,
    mockControlCenterData.macosSetupAssistant,
  );
  const setupAssistant = normalizedSetupAssistant.value;
  const providerCatalog = fulfilledValue(results[8]);
  const modelProviderControlPlane = fulfilledValue(results[9]);
  const controlCenterSettingsStatusSource = fulfilledValue(results[10]);
  const controlCenterSettingsStatus = isSafeControlCenterSettingsStatus(
    controlCenterSettingsStatusSource,
  )
    ? controlCenterSettingsStatusSource
    : undefined;
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
  const communicationsProjection = fulfilledValue(
    communicationsProjectionResult[0],
  );
  const capabilitySurface = fulfilledValue(capabilitySurfaceResult[0]);
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
  const safeRuntimeInterfaceMode = isSafeRuntimeInterfaceMode(
    runtimeInterfaceMode,
  )
    ? runtimeInterfaceMode
    : undefined;
  const safeRuntimeHermesContextPack = isSafeRuntimeHermesContextPack(
    runtimeHermesContextPack,
  )
    ? runtimeHermesContextPack
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
  const safeRuntimeToolRegistry = isSafeRuntimeToolRegistry(runtimeToolRegistry)
    ? runtimeToolRegistry
    : undefined;
  const safeRuntimeVirtualProviderMoa = isSafeRuntimeVirtualProviderMoa(
    runtimeVirtualProviderMoa,
  )
    ? runtimeVirtualProviderMoa
    : undefined;
  const safeRuntimeUsageCostAnalytics = isSafeRuntimeUsageCostAnalytics(
    runtimeUsageCostAnalytics,
  )
    ? runtimeUsageCostAnalytics
    : undefined;
  const safeRuntimePromptStabilityTiers = isSafeRuntimePromptStabilityTiers(
    runtimePromptStabilityTiers,
  )
    ? runtimePromptStabilityTiers
    : undefined;
  const safeRuntimeContextBudgetPressure = isSafeRuntimeContextBudgetPressure(
    runtimeContextBudgetPressure,
  )
    ? runtimeContextBudgetPressure
    : undefined;
  const safeRuntimeHardlineCommandBlocklist =
    isSafeRuntimeHardlineCommandBlocklist(runtimeHardlineCommandBlocklist)
      ? runtimeHardlineCommandBlocklist
      : undefined;
  const safeRuntimeManagedScopePolicy = isSafeRuntimeManagedScopePolicy(
    runtimeManagedScopePolicy,
  )
    ? runtimeManagedScopePolicy
    : undefined;
  const safeRuntimeDoctorDiagnostics = isSafeRuntimeDoctorDiagnostics(
    runtimeDoctorDiagnostics,
  )
    ? runtimeDoctorDiagnostics
    : undefined;
  const safeRuntimeSessionContinuity = isSafeRuntimeSessionContinuity(
    runtimeSessionContinuity,
  )
    ? runtimeSessionContinuity
    : undefined;
  const safeRuntimeMcpCatalogFiltering = isSafeRuntimeMcpCatalogFiltering(
    runtimeMcpCatalogFiltering,
  )
    ? runtimeMcpCatalogFiltering
    : undefined;
  const safeRuntimeBackgroundJobs = isSafeRuntimeBackgroundJobs(
    runtimeBackgroundJobs,
  )
    ? runtimeBackgroundJobs
    : undefined;
  const safeRuntimeSubagentIsolation = isSafeRuntimeSubagentIsolation(
    runtimeSubagentIsolation,
  )
    ? runtimeSubagentIsolation
    : undefined;
  const safeRuntimeWorktreePerAgent = isSafeRuntimeWorktreePerAgent(
    runtimeWorktreePerAgent,
  )
    ? runtimeWorktreePerAgent
    : undefined;
  const safeRuntimeStagedOrchestration = isSafeRuntimeStagedOrchestration(
    runtimeStagedOrchestration,
  )
    ? runtimeStagedOrchestration
    : undefined;
  const safeRuntimeLspDiagnostics = isSafeRuntimeLspDiagnostics(
    runtimeLspDiagnostics,
  )
    ? runtimeLspDiagnostics
    : undefined;
  const safeRuntimePreviewRail = isSafeRuntimePreviewRail(runtimePreviewRail)
    ? runtimePreviewRail
    : undefined;
  const safeRuntimeSlashCommandRegistry = isSafeRuntimeSlashCommandRegistry(
    runtimeSlashCommandRegistry,
  )
    ? runtimeSlashCommandRegistry
    : undefined;
  const safeRuntimeInterruptRedirect = isSafeRuntimeInterruptRedirect(
    runtimeInterruptRedirect,
  )
    ? runtimeInterruptRedirect
    : undefined;
  const safeRuntimeLoggingProfile = isSafeRuntimeLoggingProfile(
    runtimeLoggingProfile,
  )
    ? runtimeLoggingProfile
    : undefined;
  const safeRuntimeResultClassification = isSafeRuntimeResultClassification(
    runtimeResultClassification,
  )
    ? runtimeResultClassification
    : undefined;
  const safeRuntimeVoiceMediaPosture = isSafeRuntimeVoiceMediaPosture(
    runtimeVoiceMediaPosture,
  )
    ? runtimeVoiceMediaPosture
    : undefined;
  const safeRuntimeMessagingGatewayPosture =
    isSafeRuntimeMessagingGatewayPosture(runtimeMessagingGatewayPosture)
      ? runtimeMessagingGatewayPosture
      : undefined;
  const safeRuntimeRemoteExecutionPosture =
    isSafeRuntimeRemoteExecutionPosture(runtimeRemoteExecutionPosture)
      ? runtimeRemoteExecutionPosture
      : undefined;
  const safeRuntimePluginMetadataPosture =
    isSafeRuntimePluginMetadataPosture(runtimePluginMetadataPosture)
      ? runtimePluginMetadataPosture
      : undefined;
  const safeRuntimeSkillMarketplacePosture =
    isSafeRuntimeSkillMarketplacePosture(runtimeSkillMarketplacePosture) &&
    (await hasMatchingSkillMarketplaceSnapshotHash(
      runtimeSkillMarketplacePosture,
    ).catch(() => false))
      ? runtimeSkillMarketplacePosture
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
    workBoard.local_card_create_enabled !== true ||
    workBoard.local_card_create_contract_available !== true ||
    workBoard.approval_required_for_card_create !== true ||
    workBoard.card_create_route_available !== true ||
    typeof workBoard.card_create_route_ref !== "string" ||
    workBoard.local_task_create_enabled !== true ||
    workBoard.local_task_create_contract_available !== true ||
    workBoard.approval_required_for_task_create !== true ||
    workBoard.task_create_route_available !== true ||
    typeof workBoard.task_create_route_ref !== "string" ||
    workBoard.drag_drop_posture?.durable_reorder_enabled !== true ||
    workBoard.drag_drop_posture?.backend_mutation_route_available !== true ||
    workBoard.drag_drop_posture?.approval_required !== true;
  const communicationsProjectionFallbackUsed =
    communicationsProjection === undefined;
  const workBoardEndpointFallbackWarningRefs = [
    ...(workBoardFallbackUsed ? ["WORK_BOARD_MOCK_FALLBACK"] : []),
  ];
  const safeCapabilitySurface = isSafeControlCenterCapabilitySurface(
    capabilitySurface,
  )
    ? capabilitySurface
    : undefined;
  const capabilitySurfaceFallbackUsed = safeCapabilitySurface === undefined;
  const capabilitySurfaceEndpointFallbackWarningRefs = [
    ...(capabilitySurfaceFallbackUsed
      ? ["CAPABILITY_SURFACE_MOCK_FALLBACK"]
      : []),
  ];
  const safeFounderAgentLoopThread = isSafeFounderAgentLoopThread(
    founderAgentLoopThread,
  )
    ? founderAgentLoopThread
    : undefined;
  const agentLoopThreadFallbackUsed =
    safeFounderAgentLoopThread === undefined;
  const crmSocialProjectionSafe = await isSafeCrmSocialProjection(
    crmLocalCommandCenter,
  );
  const crmEndpointFallbackUsed =
    crmLocalCommandCenter === undefined ||
    !crmSocialProjectionSafe ||
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
  const runtimeInterfaceModeFallbackUsed =
    safeRuntimeInterfaceMode === undefined;
  const runtimeHermesContextPackFallbackUsed =
    safeRuntimeHermesContextPack === undefined;
  const runtimeCapabilityDiscoveryFallbackUsed =
    safeRuntimeCapabilityDiscovery === undefined;
  const runtimeRunEventsFallbackUsed = safeRuntimeRunEvents === undefined;
  const runtimeApprovalBridgeFallbackUsed =
    safeRuntimeApprovalBridge === undefined;
  const runtimeStreamingProgressFallbackUsed =
    safeRuntimeStreamingProgress === undefined;
  const runtimeProfilesFallbackUsed = safeRuntimeProfiles === undefined;
  const runtimeToolRegistryFallbackUsed =
    safeRuntimeToolRegistry === undefined;
  const runtimeVirtualProviderMoaFallbackUsed =
    safeRuntimeVirtualProviderMoa === undefined;
  const runtimeUsageCostAnalyticsFallbackUsed =
    safeRuntimeUsageCostAnalytics === undefined;
  const runtimePromptStabilityTiersFallbackUsed =
    safeRuntimePromptStabilityTiers === undefined;
  const runtimeContextBudgetPressureFallbackUsed =
    safeRuntimeContextBudgetPressure === undefined;
  const runtimeHardlineCommandBlocklistFallbackUsed =
    safeRuntimeHardlineCommandBlocklist === undefined;
  const runtimeManagedScopePolicyFallbackUsed =
    safeRuntimeManagedScopePolicy === undefined;
  const runtimeDoctorDiagnosticsFallbackUsed =
    safeRuntimeDoctorDiagnostics === undefined;
  const runtimeSessionContinuityFallbackUsed =
    safeRuntimeSessionContinuity === undefined;
  const runtimeMcpCatalogFilteringFallbackUsed =
    safeRuntimeMcpCatalogFiltering === undefined;
  const runtimeBackgroundJobsFallbackUsed =
    safeRuntimeBackgroundJobs === undefined;
  const runtimeSubagentIsolationFallbackUsed =
    safeRuntimeSubagentIsolation === undefined;
  const runtimeWorktreePerAgentFallbackUsed =
    safeRuntimeWorktreePerAgent === undefined;
  const runtimeStagedOrchestrationFallbackUsed =
    safeRuntimeStagedOrchestration === undefined;
  const runtimeLspDiagnosticsFallbackUsed =
    safeRuntimeLspDiagnostics === undefined;
  const runtimePreviewRailFallbackUsed = safeRuntimePreviewRail === undefined;
  const runtimeSlashCommandRegistryFallbackUsed =
    safeRuntimeSlashCommandRegistry === undefined;
  const runtimeInterruptRedirectFallbackUsed =
    safeRuntimeInterruptRedirect === undefined;
  const runtimeLoggingProfileFallbackUsed =
    safeRuntimeLoggingProfile === undefined;
  const runtimeResultClassificationFallbackUsed =
    safeRuntimeResultClassification === undefined;
  const runtimeVoiceMediaPostureFallbackUsed =
    safeRuntimeVoiceMediaPosture === undefined;
  const runtimeMessagingGatewayPostureFallbackUsed =
    safeRuntimeMessagingGatewayPosture === undefined;
  const runtimeRemoteExecutionPostureFallbackUsed =
    safeRuntimeRemoteExecutionPosture === undefined;
  const runtimePluginMetadataPostureFallbackUsed =
    safeRuntimePluginMetadataPosture === undefined;
  const runtimeSkillMarketplacePostureFallbackUsed =
    safeRuntimeSkillMarketplacePosture === undefined;

  const routeStates = buildRouteReadStates([
    routeReadStateInput({
      route: API_ENDPOINTS.runtimeRunEvents,
      surfaceLabel: "Durable goals and run events",
      backendRouteRef: "GET /api/runtime/run-events",
      endpointReturned: runtimeRunEvents !== undefined,
      usedFallback: runtimeRunEventsFallbackUsed,
      warningRefs: runtimeRunEventsFallbackUsed
        ? ["RUNTIME_RUN_EVENTS_MOCK_FALLBACK"]
        : [],
    }),
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
      route: "/plans",
      surfaceLabel: "Plans",
      backendRouteRef: "GET /control-center/today/summary",
      endpointReturned: founderToday !== undefined,
      usedFallback:
        normalizedFounderToday.usedFallback ||
        founderToday?.founder_loop_v1_product_proof_read_model === undefined,
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
      route: "/approvals",
      surfaceLabel: "Approvals",
      backendRouteRef: "GET /control-center/approvals/queue",
      endpointReturned: approvalQueue !== undefined,
      usedFallback: approvalQueue === undefined,
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
      backendRouteRefs: [
        "GET /control-center/memory/review",
        "GET /control-center/memory/workbench",
        "GET /control-center/memory/context-packs",
        "GET /control-center/memory/retrieval-diagnostics",
        "GET /control-center/memory/citation-integrity",
        "GET /control-center/memory/quality-issues",
        "GET /control-center/memory/maintenance-runs",
        "GET /control-center/memory/context-manifest",
      ],
      endpointReturned:
        founderMemoryReview !== undefined &&
        founderMemoryWorkbench !== undefined &&
        founderMemoryContextPacks !== undefined &&
        founderMemoryRetrievalDiagnostics !== undefined &&
        founderMemoryCitationIntegrity !== undefined &&
        founderMemoryQualityIssues !== undefined &&
        founderMemoryMaintenanceRuns !== undefined &&
        founderMemoryContextManifest !== undefined,
      usedFallback:
        normalizedFounderMemoryReview.usedFallback ||
        normalizedFounderMemoryWorkbench.usedFallback ||
        normalizedFounderMemoryContextPacks.usedFallback ||
        normalizedFounderMemoryRetrievalDiagnostics.usedFallback ||
        normalizedFounderMemoryCitationIntegrity.usedFallback ||
        normalizedFounderMemoryQualityIssues.usedFallback ||
        normalizedFounderMemoryMaintenanceRuns.usedFallback ||
        normalizedFounderMemoryContextManifest.usedFallback,
    }),
    routeReadStateInput({
      route: "/evidence",
      surfaceLabel: "Evidence",
      backendRouteRef: "GET /control-center/evidence/timeline",
      endpointReturned: founderEvidenceTimeline !== undefined,
      usedFallback: normalizedFounderEvidenceTimeline.usedFallback,
    }),
    routeReadStateInput({
      route: "/chat",
      surfaceLabel: "Chat handoff",
      backendRouteRef: "GET /control-center/agent-loop/thread",
      endpointReturned: founderAgentLoopThread !== undefined,
      usedFallback: agentLoopThreadFallbackUsed,
    }),
    routeReadStateInput({
      route: "/runs",
      surfaceLabel: "Active run",
      backendRouteRef: "GET /control-center/runs/observability",
      endpointReturned: safeObservedRunObservability !== undefined,
      usedFallback: safeObservedRunObservability === undefined,
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
        "GET /api/runtime/interface-mode",
        "GET /api/runtime/hermes/context-pack",
        "GET /api/runtime/capability-discovery",
        "GET /api/runtime/run-events",
        "POST /api/runtime/goals",
        "POST /api/runtime/goals/{goal_ref}/edit",
        "POST /api/runtime/goals/{goal_ref}/transition",
        "GET /api/runtime/approval-bridge",
        "GET /api/runtime/streaming-progress",
        "GET /api/runtime/profiles",
        "GET /api/runtime/tool-registry",
        "GET /api/runtime/virtual-provider-moa",
        "GET /api/runtime/usage-cost-analytics",
        "GET /api/runtime/prompt-stability-tiers",
        "GET /api/runtime/context-budget-pressure",
        "GET /api/runtime/hardline-command-blocklist",
        "GET /api/runtime/managed-scope-policy",
        "GET /api/runtime/doctor-diagnostics",
        "GET /api/runtime/session-continuity",
        "GET /api/runtime/mcp-catalog-filtering",
        "GET /api/runtime/background-jobs",
        "GET /api/runtime/subagent-isolation",
        "GET /api/runtime/worktree-per-agent",
        "GET /api/runtime/staged-orchestration",
        "GET /api/runtime/lsp-diagnostics",
        "GET /api/runtime/preview-rail",
        "GET /api/runtime/slash-command-registry",
        "GET /api/runtime/interrupt-redirect",
        "GET /api/runtime/logging-profile",
        "GET /api/runtime/result-classification",
        "GET /api/runtime/voice-media-posture",
        "GET /api/runtime/messaging-gateway-posture",
        "GET /api/runtime/remote-execution-posture",
        "GET /api/runtime/plugin-metadata-posture",
        "GET /api/runtime/skill-marketplace-posture",
      ],
      endpointReturned:
        runtimeReadiness !== undefined &&
        capabilityMatrix !== undefined &&
        runtimeDelegationAdapter !== undefined &&
        runtimeInterfaceMode !== undefined &&
        runtimeHermesContextPack !== undefined &&
        runtimeCapabilityDiscovery !== undefined &&
        runtimeRunEvents !== undefined &&
        runtimeApprovalBridge !== undefined &&
        runtimeStreamingProgress !== undefined &&
        runtimeProfiles !== undefined &&
        runtimeToolRegistry !== undefined &&
        runtimeVirtualProviderMoa !== undefined &&
        runtimeUsageCostAnalytics !== undefined &&
        runtimePromptStabilityTiers !== undefined &&
        runtimeContextBudgetPressure !== undefined &&
        runtimeHardlineCommandBlocklist !== undefined &&
        runtimeManagedScopePolicy !== undefined &&
        runtimeDoctorDiagnostics !== undefined &&
        runtimeSessionContinuity !== undefined &&
        runtimeMcpCatalogFiltering !== undefined &&
        runtimeBackgroundJobs !== undefined &&
        runtimeSubagentIsolation !== undefined &&
        runtimeWorktreePerAgent !== undefined &&
        runtimeStagedOrchestration !== undefined &&
        runtimeLspDiagnostics !== undefined &&
        runtimePreviewRail !== undefined &&
        runtimeSlashCommandRegistry !== undefined &&
        runtimeInterruptRedirect !== undefined &&
        runtimeLoggingProfile !== undefined &&
        runtimeResultClassification !== undefined &&
        runtimeVoiceMediaPosture !== undefined &&
        runtimeMessagingGatewayPosture !== undefined &&
        runtimeRemoteExecutionPosture !== undefined &&
        runtimePluginMetadataPosture !== undefined &&
        runtimeSkillMarketplacePosture !== undefined,
      warningRefs: [
        ...(runtimeDelegationAdapterFallbackUsed
          ? ["RUNTIME_DELEGATION_ADAPTER_MOCK_FALLBACK"]
          : []),
        ...(runtimeInterfaceModeFallbackUsed
          ? ["RUNTIME_INTERFACE_MODE_MOCK_FALLBACK"]
          : []),
        ...(runtimeHermesContextPackFallbackUsed
          ? ["RUNTIME_HERMES_CONTEXT_PACK_MOCK_FALLBACK"]
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
        ...(runtimeToolRegistryFallbackUsed
          ? ["RUNTIME_TOOL_REGISTRY_MOCK_FALLBACK"]
          : []),
        ...(runtimeVirtualProviderMoaFallbackUsed
          ? ["RUNTIME_VIRTUAL_PROVIDER_MOA_MOCK_FALLBACK"]
          : []),
        ...(runtimeUsageCostAnalyticsFallbackUsed
          ? ["RUNTIME_USAGE_COST_ANALYTICS_MOCK_FALLBACK"]
          : []),
        ...(runtimePromptStabilityTiersFallbackUsed
          ? ["RUNTIME_PROMPT_STABILITY_TIERS_MOCK_FALLBACK"]
          : []),
        ...(runtimeContextBudgetPressureFallbackUsed
          ? ["RUNTIME_CONTEXT_BUDGET_PRESSURE_MOCK_FALLBACK"]
          : []),
        ...(runtimeHardlineCommandBlocklistFallbackUsed
          ? ["RUNTIME_HARDLINE_COMMAND_BLOCKLIST_MOCK_FALLBACK"]
          : []),
        ...(runtimeManagedScopePolicyFallbackUsed
          ? ["RUNTIME_MANAGED_SCOPE_POLICY_MOCK_FALLBACK"]
          : []),
        ...(runtimeDoctorDiagnosticsFallbackUsed
          ? ["RUNTIME_DOCTOR_DIAGNOSTICS_MOCK_FALLBACK"]
          : []),
        ...(runtimeSessionContinuityFallbackUsed
          ? ["RUNTIME_SESSION_CONTINUITY_MOCK_FALLBACK"]
          : []),
        ...(runtimeMcpCatalogFilteringFallbackUsed
          ? ["RUNTIME_MCP_CATALOG_FILTERING_MOCK_FALLBACK"]
          : []),
        ...(runtimeBackgroundJobsFallbackUsed
          ? ["RUNTIME_BACKGROUND_JOBS_MOCK_FALLBACK"]
          : []),
        ...(runtimeSubagentIsolationFallbackUsed
          ? ["RUNTIME_SUBAGENT_ISOLATION_MOCK_FALLBACK"]
          : []),
        ...(runtimeWorktreePerAgentFallbackUsed
          ? ["RUNTIME_WORKTREE_PER_AGENT_MOCK_FALLBACK"]
          : []),
        ...(runtimeStagedOrchestrationFallbackUsed
          ? ["RUNTIME_STAGED_ORCHESTRATION_MOCK_FALLBACK"]
          : []),
        ...(runtimeLspDiagnosticsFallbackUsed
          ? ["RUNTIME_LSP_DIAGNOSTICS_MOCK_FALLBACK"]
          : []),
        ...(runtimePreviewRailFallbackUsed
          ? ["RUNTIME_PREVIEW_RAIL_MOCK_FALLBACK"]
          : []),
        ...(runtimeSlashCommandRegistryFallbackUsed
          ? ["RUNTIME_SLASH_COMMAND_REGISTRY_MOCK_FALLBACK"]
          : []),
        ...(runtimeInterruptRedirectFallbackUsed
          ? ["RUNTIME_INTERRUPT_REDIRECT_MOCK_FALLBACK"]
          : []),
        ...(runtimeLoggingProfileFallbackUsed
          ? ["RUNTIME_LOGGING_PROFILE_MOCK_FALLBACK"]
          : []),
        ...(runtimeResultClassificationFallbackUsed
          ? ["RUNTIME_RESULT_CLASSIFICATION_MOCK_FALLBACK"]
          : []),
        ...(runtimeVoiceMediaPostureFallbackUsed
          ? ["RUNTIME_VOICE_MEDIA_POSTURE_MOCK_FALLBACK"]
          : []),
        ...(runtimeMessagingGatewayPostureFallbackUsed
          ? ["RUNTIME_MESSAGING_GATEWAY_POSTURE_MOCK_FALLBACK"]
          : []),
        ...(runtimeRemoteExecutionPostureFallbackUsed
          ? ["RUNTIME_REMOTE_EXECUTION_POSTURE_MOCK_FALLBACK"]
          : []),
        ...(runtimePluginMetadataPostureFallbackUsed
          ? ["RUNTIME_PLUGIN_METADATA_POSTURE_MOCK_FALLBACK"]
          : []),
        ...(runtimeSkillMarketplacePostureFallbackUsed
          ? ["RUNTIME_SKILL_MARKETPLACE_POSTURE_MOCK_FALLBACK"]
          : []),
      ],
      usedFallback:
        runtimeReadiness === undefined ||
        capabilityMatrix === undefined ||
        runtimeDelegationAdapterFallbackUsed ||
        runtimeInterfaceModeFallbackUsed ||
        runtimeHermesContextPackFallbackUsed ||
        runtimeCapabilityDiscoveryFallbackUsed ||
        runtimeRunEventsFallbackUsed ||
        runtimeApprovalBridgeFallbackUsed ||
        runtimeStreamingProgressFallbackUsed ||
        runtimeProfilesFallbackUsed ||
        runtimeToolRegistryFallbackUsed ||
        runtimeVirtualProviderMoaFallbackUsed ||
        runtimeUsageCostAnalyticsFallbackUsed ||
        runtimePromptStabilityTiersFallbackUsed ||
        runtimeContextBudgetPressureFallbackUsed ||
        runtimeHardlineCommandBlocklistFallbackUsed ||
        runtimeManagedScopePolicyFallbackUsed ||
        runtimeDoctorDiagnosticsFallbackUsed ||
        runtimeSessionContinuityFallbackUsed ||
        runtimeMcpCatalogFilteringFallbackUsed ||
        runtimeBackgroundJobsFallbackUsed ||
        runtimeSubagentIsolationFallbackUsed ||
        runtimeWorktreePerAgentFallbackUsed ||
        runtimeStagedOrchestrationFallbackUsed ||
        runtimeLspDiagnosticsFallbackUsed ||
        runtimePreviewRailFallbackUsed ||
        runtimeSlashCommandRegistryFallbackUsed ||
        runtimeInterruptRedirectFallbackUsed ||
        runtimeLoggingProfileFallbackUsed ||
        runtimeResultClassificationFallbackUsed ||
        runtimeVoiceMediaPostureFallbackUsed ||
        runtimeMessagingGatewayPostureFallbackUsed ||
        runtimeRemoteExecutionPostureFallbackUsed ||
        runtimePluginMetadataPostureFallbackUsed ||
        runtimeSkillMarketplacePostureFallbackUsed,
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
      usedFallback: normalizedSetupAssistant.usedFallback,
    }),
    routeReadStateInput({
      route: "/critical/dashboard-read-model",
      surfaceLabel: "Dashboard",
      backendRouteRefs: [
        "GET /dashboard",
        "GET /approvals/summary",
        "GET /runtime/readiness/summary",
        "GET /foundation-gate/summary",
      ],
      endpointReturned:
        dashboard !== undefined &&
        approvalSummary !== undefined &&
        runtimeReadinessSummary !== undefined &&
        foundationGateSummary !== undefined,
      usedFallback:
        normalizedDashboard.usedFallback ||
        approvalSummary === undefined ||
        runtimeReadinessSummary === undefined ||
        foundationGateSummary === undefined,
    }),
    routeReadStateInput({
      route: "/critical/manifest-read-model",
      surfaceLabel: "Manifest",
      backendRouteRef: "GET /api/manifest",
      endpointReturned: manifest !== undefined,
      usedFallback: manifest === undefined,
    }),
    routeReadStateInput({
      route: "/critical/provider-catalog-read-model",
      surfaceLabel: "Provider catalog",
      backendRouteRef: "GET /control-center/providers/catalog",
      endpointReturned: providerCatalog !== undefined,
      usedFallback: providerCatalog === undefined,
    }),
    routeReadStateInput({
      route: "/storage",
      surfaceLabel: "Storage",
      backendRouteRef: "GET /control-center/storage/status",
      endpointReturned: founderStorageStatus !== undefined,
      usedFallback: founderStorageStatus === undefined,
    }),
    routeReadStateInput({
      route: "/capabilities",
      surfaceLabel: "Capabilities",
      backendRouteRef: "GET /control-center/capabilities/surface",
      endpointReturned: capabilitySurface !== undefined,
      warningRefs: capabilitySurfaceEndpointFallbackWarningRefs,
      usedFallback: capabilitySurfaceFallbackUsed,
    }),
    routeReadStateInput({
      route: "/crm",
      surfaceLabel: "CRM",
      backendRouteRef: "GET /control-center/crm/summary",
      endpointReturned: crmLocalCommandCenter !== undefined,
      usedFallback: crmEndpointFallbackUsed,
    }),
    routeReadStateInput({
      route: "/workspace/communications",
      surfaceLabel: "Communications",
      backendRouteRef: "GET /control-center/communications/conversations",
      endpointReturned: communicationsProjection !== undefined,
      usedFallback: communicationsProjectionFallbackUsed,
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
    runtimeInterfaceMode === undefined ||
    runtimeHermesContextPack === undefined ||
    runtimeCapabilityDiscovery === undefined ||
    runtimeRunEvents === undefined ||
    runtimeApprovalBridge === undefined ||
    runtimeStreamingProgress === undefined ||
    runtimeProfiles === undefined ||
    runtimeToolRegistry === undefined ||
    runtimeVirtualProviderMoa === undefined ||
    runtimeUsageCostAnalytics === undefined ||
    runtimePromptStabilityTiers === undefined ||
    runtimeContextBudgetPressure === undefined ||
    runtimeHardlineCommandBlocklist === undefined ||
    runtimeManagedScopePolicy === undefined ||
    runtimeDoctorDiagnostics === undefined ||
    runtimeSessionContinuity === undefined ||
    runtimeMcpCatalogFiltering === undefined ||
    runtimeBackgroundJobs === undefined ||
    runtimeSubagentIsolation === undefined ||
    runtimeWorktreePerAgent === undefined ||
    runtimeStagedOrchestration === undefined ||
    runtimeLspDiagnostics === undefined ||
    runtimePreviewRail === undefined ||
    runtimeSlashCommandRegistry === undefined ||
    runtimeInterruptRedirect === undefined ||
    runtimeLoggingProfile === undefined ||
    runtimeResultClassification === undefined ||
    runtimeVoiceMediaPosture === undefined ||
    runtimeMessagingGatewayPosture === undefined ||
    runtimeRemoteExecutionPosture === undefined ||
    runtimePluginMetadataPosture === undefined ||
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
  // Studio validates and reports its catalog endpoint independently. Its
  // fail-closed fallback must not relabel unrelated Control Center routes as
  // globally degraded.
  const fulfilledCount =
    coreFulfilledCount +
    (workBoardResult[0].status === "fulfilled" ? 1 : 0) +
    (capabilitySurfaceResult[0].status === "fulfilled" ? 1 : 0) +
    (agentLoopResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeInterfaceModeResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeHermesContextPackResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeCapabilityDiscoveryResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeRunEventsResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeApprovalBridgeResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeStreamingProgressResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeProfilesResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeToolRegistryResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeVirtualProviderMoaResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeUsageCostAnalyticsResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimePromptStabilityTiersResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeContextBudgetPressureResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeHardlineCommandBlocklistResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeManagedScopePolicyResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeDoctorDiagnosticsResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeSessionContinuityResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeMcpCatalogFilteringResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeBackgroundJobsResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeSubagentIsolationResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeWorktreePerAgentResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeStagedOrchestrationResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeLspDiagnosticsResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimePreviewRailResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeSlashCommandRegistryResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeInterruptRedirectResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeLoggingProfileResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeResultClassificationResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeVoiceMediaPostureResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeMessagingGatewayPostureResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimeRemoteExecutionPostureResult[0].status === "fulfilled" ? 1 : 0) +
    (runtimePluginMetadataPostureResult[0].status === "fulfilled" ? 1 : 0);
  const expectedReadCount = results.length + 34;
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
    capabilitySurface:
      safeCapabilitySurface ?? mockControlCenterData.capabilitySurface,
    runtimeReadiness:
      runtimeReadiness ?? mockControlCenterData.runtimeReadiness,
    capabilityMatrix:
      capabilityMatrix ?? mockControlCenterData.capabilityMatrix,
    runtimeDelegationAdapter:
      safeRuntimeDelegationAdapter ??
      mockControlCenterData.runtimeDelegationAdapter,
    runtimeInterfaceMode:
      safeRuntimeInterfaceMode ?? mockControlCenterData.runtimeInterfaceMode,
    runtimeHermesContextPack:
      safeRuntimeHermesContextPack ??
      mockControlCenterData.runtimeHermesContextPack,
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
    runtimeToolRegistry:
      safeRuntimeToolRegistry ?? mockControlCenterData.runtimeToolRegistry,
    runtimeVirtualProviderMoa:
      safeRuntimeVirtualProviderMoa ??
      mockControlCenterData.runtimeVirtualProviderMoa,
    runtimeUsageCostAnalytics:
      safeRuntimeUsageCostAnalytics ??
      mockControlCenterData.runtimeUsageCostAnalytics,
    runtimePromptStabilityTiers:
      safeRuntimePromptStabilityTiers ??
      mockControlCenterData.runtimePromptStabilityTiers,
    runtimeContextBudgetPressure:
      safeRuntimeContextBudgetPressure ??
      mockControlCenterData.runtimeContextBudgetPressure,
    runtimeHardlineCommandBlocklist:
      safeRuntimeHardlineCommandBlocklist ??
      mockControlCenterData.runtimeHardlineCommandBlocklist,
    runtimeManagedScopePolicy:
      safeRuntimeManagedScopePolicy ??
      mockControlCenterData.runtimeManagedScopePolicy,
    runtimeDoctorDiagnostics:
      safeRuntimeDoctorDiagnostics ??
      mockControlCenterData.runtimeDoctorDiagnostics,
    runtimeSessionContinuity:
      safeRuntimeSessionContinuity ??
      mockControlCenterData.runtimeSessionContinuity,
    runtimeMcpCatalogFiltering:
      safeRuntimeMcpCatalogFiltering ??
      mockControlCenterData.runtimeMcpCatalogFiltering,
    runtimeBackgroundJobs:
      safeRuntimeBackgroundJobs ?? mockControlCenterData.runtimeBackgroundJobs,
    runtimeSubagentIsolation:
      safeRuntimeSubagentIsolation ??
      mockControlCenterData.runtimeSubagentIsolation,
    runtimeWorktreePerAgent:
      safeRuntimeWorktreePerAgent ??
      mockControlCenterData.runtimeWorktreePerAgent,
    runtimeStagedOrchestration:
      safeRuntimeStagedOrchestration ??
      mockControlCenterData.runtimeStagedOrchestration,
    runtimeLspDiagnostics:
      safeRuntimeLspDiagnostics ??
      mockControlCenterData.runtimeLspDiagnostics,
    runtimePreviewRail:
      safeRuntimePreviewRail ?? mockControlCenterData.runtimePreviewRail,
    runtimeSlashCommandRegistry:
      safeRuntimeSlashCommandRegistry ??
      mockControlCenterData.runtimeSlashCommandRegistry,
    runtimeInterruptRedirect:
      safeRuntimeInterruptRedirect ??
      mockControlCenterData.runtimeInterruptRedirect,
    runtimeLoggingProfile:
      safeRuntimeLoggingProfile ?? mockControlCenterData.runtimeLoggingProfile,
    runtimeResultClassification:
      safeRuntimeResultClassification ??
      mockControlCenterData.runtimeResultClassification,
    runtimeVoiceMediaPosture:
      safeRuntimeVoiceMediaPosture ??
      mockControlCenterData.runtimeVoiceMediaPosture,
    runtimeMessagingGatewayPosture:
      safeRuntimeMessagingGatewayPosture ??
      mockControlCenterData.runtimeMessagingGatewayPosture,
    runtimeRemoteExecutionPosture:
      safeRuntimeRemoteExecutionPosture ??
      mockControlCenterData.runtimeRemoteExecutionPosture,
    runtimePluginMetadataPosture:
      safeRuntimePluginMetadataPosture ??
      mockControlCenterData.runtimePluginMetadataPosture,
    runtimeSkillMarketplacePosture:
      safeRuntimeSkillMarketplacePosture ??
      mockControlCenterData.runtimeSkillMarketplacePosture,
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
    communicationsProjection:
      communicationsProjection ?? mockControlCenterData.communicationsProjection,
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
    !capabilitySurfaceFallbackUsed &&
    !agentLoopThreadFallbackUsed &&
    !runtimeDelegationAdapterFallbackUsed &&
    !runtimeInterfaceModeFallbackUsed &&
    !runtimeHermesContextPackFallbackUsed &&
    !runtimeCapabilityDiscoveryFallbackUsed &&
    !runtimeRunEventsFallbackUsed &&
    !runtimeApprovalBridgeFallbackUsed &&
    !runtimeStreamingProgressFallbackUsed &&
    !runtimeProfilesFallbackUsed &&
    !runtimeToolRegistryFallbackUsed &&
    !runtimeVirtualProviderMoaFallbackUsed &&
    !runtimeUsageCostAnalyticsFallbackUsed &&
    !runtimePromptStabilityTiersFallbackUsed &&
    !runtimeContextBudgetPressureFallbackUsed &&
    !runtimeHardlineCommandBlocklistFallbackUsed &&
    !runtimeManagedScopePolicyFallbackUsed &&
    !runtimeDoctorDiagnosticsFallbackUsed &&
    !runtimeSessionContinuityFallbackUsed &&
    !runtimeMcpCatalogFilteringFallbackUsed &&
    !runtimeBackgroundJobsFallbackUsed &&
    !runtimeSubagentIsolationFallbackUsed &&
    !runtimeWorktreePerAgentFallbackUsed &&
    !runtimeLspDiagnosticsFallbackUsed &&
    !runtimePreviewRailFallbackUsed &&
    !runtimeSlashCommandRegistryFallbackUsed &&
    !runtimeInterruptRedirectFallbackUsed &&
    !runtimeLoggingProfileFallbackUsed &&
    !runtimeResultClassificationFallbackUsed &&
    !runtimeVoiceMediaPostureFallbackUsed &&
    !runtimeMessagingGatewayPostureFallbackUsed &&
    !runtimeRemoteExecutionPostureFallbackUsed &&
    !runtimePluginMetadataPostureFallbackUsed &&
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
    capabilitySurfaceFallbackUsed ||
    agentLoopThreadFallbackUsed ||
    runtimeDelegationAdapterFallbackUsed ||
    runtimeInterfaceModeFallbackUsed ||
    runtimeHermesContextPackFallbackUsed ||
    runtimeCapabilityDiscoveryFallbackUsed ||
    runtimeRunEventsFallbackUsed ||
    runtimeApprovalBridgeFallbackUsed ||
    runtimeStreamingProgressFallbackUsed ||
    runtimeProfilesFallbackUsed ||
    runtimeToolRegistryFallbackUsed ||
    runtimeVirtualProviderMoaFallbackUsed ||
    runtimeUsageCostAnalyticsFallbackUsed ||
    runtimePromptStabilityTiersFallbackUsed ||
    runtimeContextBudgetPressureFallbackUsed ||
    runtimeHardlineCommandBlocklistFallbackUsed ||
    runtimeManagedScopePolicyFallbackUsed ||
    runtimeDoctorDiagnosticsFallbackUsed ||
    runtimeSessionContinuityFallbackUsed ||
    runtimeMcpCatalogFilteringFallbackUsed ||
    runtimeBackgroundJobsFallbackUsed ||
    runtimeSubagentIsolationFallbackUsed ||
    runtimeWorktreePerAgentFallbackUsed ||
    runtimeStagedOrchestrationFallbackUsed ||
    runtimeLspDiagnosticsFallbackUsed ||
    runtimePreviewRailFallbackUsed ||
    runtimeSlashCommandRegistryFallbackUsed ||
    runtimeInterruptRedirectFallbackUsed ||
    runtimeLoggingProfileFallbackUsed ||
    runtimeResultClassificationFallbackUsed ||
    runtimeVoiceMediaPostureFallbackUsed ||
    runtimeMessagingGatewayPostureFallbackUsed ||
    runtimeRemoteExecutionPostureFallbackUsed ||
    runtimePluginMetadataPostureFallbackUsed ||
    modelProviderControlPlaneFallbackUsed ||
    providerCredentialReadinessFallbackUsed ||
    approvalQueueEndpointFallbackUsed ||
    runObservabilityEndpointFallbackUsed ||
    crmEndpointFallbackUsed;
  if (strictBackendDataFailureRequired(mockFallbackUsed)) {
    throw new StrictBackendDataError();
  }
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
  } else if (capabilitySurfaceFallbackUsed) {
    degradedSafeMessage =
      "The capability-surface read model was unavailable or unsafe; non-authoritative mock fallback kept capability coverage partial.";
  } else if (modelProviderControlPlaneFallbackUsed) {
    degradedSafeMessage =
      "Model/provider control-plane posture was unavailable or unsafe; non-authoritative mock fallback kept broad provider authority blocked.";
  } else if (runtimeDelegationAdapterFallbackUsed) {
    degradedSafeMessage =
      "Runtime delegation adapter posture was unavailable or unsafe; non-authoritative mock fallback kept delegated runtime authority blocked.";
  } else if (runtimeInterfaceModeFallbackUsed) {
    degradedSafeMessage =
      "Runtime interface mode was unavailable or unsafe; non-authoritative mock fallback kept UAA-native agent execution off and Hermes authority blocked.";
  } else if (runtimeHermesContextPackFallbackUsed) {
    degradedSafeMessage =
      "Hermes context pack posture was unavailable or unsafe; non-authoritative mock fallback kept raw Memory and CRM access blocked.";
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
  } else if (runtimeToolRegistryFallbackUsed) {
    degradedSafeMessage =
      "Runtime tool registry posture was unavailable or unsafe; non-authoritative mock fallback kept tool invocation blocked.";
  } else if (runtimeVirtualProviderMoaFallbackUsed) {
    degradedSafeMessage =
      "Virtual multi-agent provider posture was unavailable or unsafe; non-authoritative mock fallback kept provider fan-out blocked.";
  } else if (runtimeUsageCostAnalyticsFallbackUsed) {
    degradedSafeMessage =
      "Runtime usage and cost posture was unavailable or unsafe; non-authoritative mock fallback kept billing and provider execution blocked.";
  } else if (runtimePromptStabilityTiersFallbackUsed) {
    degradedSafeMessage =
      "Runtime prompt stability posture was unavailable or unsafe; non-authoritative mock fallback kept raw prompts, hidden injection, and model-output authority blocked.";
  } else if (runtimeContextBudgetPressureFallbackUsed) {
    degradedSafeMessage =
      "Runtime context budget posture was unavailable or unsafe; non-authoritative mock fallback kept hidden compression, automatic context mutation, and model summarization blocked.";
  } else if (runtimeHardlineCommandBlocklistFallbackUsed) {
    degradedSafeMessage =
      "Runtime hardline command blocklist posture was unavailable or unsafe; non-authoritative mock fallback kept command floor override and catastrophic command categories blocked.";
  } else if (runtimeManagedScopePolicyFallbackUsed) {
    degradedSafeMessage =
      "Runtime managed scope policy posture was unavailable or unsafe; non-authoritative mock fallback kept local policy config writes and privileged delivery blocked.";
  } else if (runtimeDoctorDiagnosticsFallbackUsed) {
    degradedSafeMessage =
      "Runtime doctor diagnostics were unavailable or unsafe; non-authoritative mock fallback kept installs, service starts, credential writes, and runtime config mutation blocked.";
  } else if (runtimeSessionContinuityFallbackUsed) {
    degradedSafeMessage =
      "Runtime session continuity was unavailable or unsafe; non-authoritative mock fallback kept external gateways, account sync, connector writes, and remote sessions blocked.";
  } else if (runtimeMcpCatalogFilteringFallbackUsed) {
    degradedSafeMessage =
      "Runtime MCP catalog filtering was unavailable or unsafe; non-authoritative mock fallback kept server install, tool invocation, and connector writes blocked.";
  } else if (runtimeBackgroundJobsFallbackUsed) {
    degradedSafeMessage =
      "Runtime background job posture was unavailable or unsafe; non-authoritative mock fallback kept schedulers, workers, run-now, and connector writes blocked.";
  } else if (runtimeSubagentIsolationFallbackUsed) {
    degradedSafeMessage =
      "Runtime subagent isolation posture was unavailable or unsafe; non-authoritative mock fallback kept live dispatch, fan-out, tool sharing, and memory transfer blocked.";
  } else if (runtimeWorktreePerAgentFallbackUsed) {
    degradedSafeMessage =
      "Runtime worktree-per-agent posture was unavailable or unsafe; non-authoritative mock fallback kept Git worktree, branch, file, commit, and push mutation blocked.";
  } else if (runtimeStagedOrchestrationFallbackUsed) {
    degradedSafeMessage =
      "Runtime staged orchestration posture was unavailable or unsafe; non-authoritative mock fallback kept autonomous workers and approved runtime commands blocked.";
  } else if (runtimeLspDiagnosticsFallbackUsed) {
    degradedSafeMessage =
      "Runtime LSP diagnostics posture was unavailable or unsafe; non-authoritative mock fallback kept language-server launch, installs, shell execution, and raw diagnostic persistence blocked.";
  } else if (runtimePreviewRailFallbackUsed) {
    degradedSafeMessage =
      "Runtime preview rail posture was unavailable or unsafe; non-authoritative mock fallback kept browser automation, raw sensitive file display, screenshot capture, and direct runtime payload rendering blocked.";
  } else if (runtimeSlashCommandRegistryFallbackUsed) {
    degradedSafeMessage =
      "Runtime slash command registry posture was unavailable or unsafe; non-authoritative mock fallback kept command execution, runtime invocation, state mutation, and raw prompt/response persistence blocked.";
  } else if (runtimeInterruptRedirectFallbackUsed) {
    degradedSafeMessage =
      "Runtime interrupt and redirect posture was unavailable or unsafe; non-authoritative mock fallback kept live stop, process kill, runtime mutation, and raw runtime payload persistence blocked.";
  } else if (runtimeLoggingProfileFallbackUsed) {
    degradedSafeMessage =
      "Runtime logging profile posture was unavailable or unsafe; non-authoritative mock fallback kept verbose logging, raw log persistence, and remote telemetry export blocked.";
  } else if (runtimeResultClassificationFallbackUsed) {
    degradedSafeMessage =
      "Runtime result classification posture was unavailable or unsafe; non-authoritative mock fallback kept tool output from becoming truth or action authority.";
  } else if (runtimeVoiceMediaPostureFallbackUsed) {
    degradedSafeMessage =
      "Runtime voice/media posture was unavailable or unsafe; non-authoritative mock fallback kept microphone, camera, upload, generation, provider, and delivery authority blocked.";
  } else if (runtimeMessagingGatewayPostureFallbackUsed) {
    degradedSafeMessage =
      "Runtime messaging gateway posture was unavailable or unsafe; non-authoritative mock fallback kept connector runtime, reads, sends, OAuth, webhooks, sync, and writes blocked.";
  } else if (runtimeRemoteExecutionPostureFallbackUsed) {
    degradedSafeMessage =
      "Runtime remote execution posture was unavailable or unsafe; non-authoritative mock fallback kept remote execution, host access, cloud sandboxes, file sync, protected material, and process control blocked.";
  } else if (runtimePluginMetadataPostureFallbackUsed) {
    degradedSafeMessage =
      "Runtime plugin metadata posture was unavailable or unsafe; non-authoritative mock fallback kept runtime imports, hooks, installs, marketplace content, plugin code, connector writes, provider calls, command execution, and raw manifests blocked.";
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
      ...(runtimeInterfaceModeFallbackUsed
        ? ["RUNTIME_INTERFACE_MODE_MOCK_FALLBACK"]
        : []),
      ...(runtimeHermesContextPackFallbackUsed
        ? ["RUNTIME_HERMES_CONTEXT_PACK_MOCK_FALLBACK"]
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
      ...(runtimeToolRegistryFallbackUsed
        ? ["RUNTIME_TOOL_REGISTRY_MOCK_FALLBACK"]
        : []),
      ...(runtimeVirtualProviderMoaFallbackUsed
        ? ["RUNTIME_VIRTUAL_PROVIDER_MOA_MOCK_FALLBACK"]
        : []),
      ...(runtimeUsageCostAnalyticsFallbackUsed
        ? ["RUNTIME_USAGE_COST_ANALYTICS_MOCK_FALLBACK"]
        : []),
      ...(runtimePromptStabilityTiersFallbackUsed
        ? ["RUNTIME_PROMPT_STABILITY_TIERS_MOCK_FALLBACK"]
        : []),
      ...(runtimeContextBudgetPressureFallbackUsed
        ? ["RUNTIME_CONTEXT_BUDGET_PRESSURE_MOCK_FALLBACK"]
        : []),
      ...(runtimeHardlineCommandBlocklistFallbackUsed
        ? ["RUNTIME_HARDLINE_COMMAND_BLOCKLIST_MOCK_FALLBACK"]
        : []),
      ...(runtimeManagedScopePolicyFallbackUsed
        ? ["RUNTIME_MANAGED_SCOPE_POLICY_MOCK_FALLBACK"]
        : []),
      ...(runtimeDoctorDiagnosticsFallbackUsed
        ? ["RUNTIME_DOCTOR_DIAGNOSTICS_MOCK_FALLBACK"]
        : []),
      ...(runtimeSessionContinuityFallbackUsed
        ? ["RUNTIME_SESSION_CONTINUITY_MOCK_FALLBACK"]
        : []),
      ...(modelProviderControlPlaneFallbackUsed
        ? ["MODEL_PROVIDER_CONTROL_PLANE_MOCK_FALLBACK"]
        : []),
      ...(providerCredentialReadinessFallbackUsed
        ? ["PARTIAL_PROVIDER_CREDENTIAL_READINESS_FALLBACK"]
        : []),
    ],
  });
}

export async function fetchAutocorrectStatus(): Promise<AutocorrectControlStatus> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.autocorrectStatus}`,
    {
      headers: withLocalApiAuthHeaders({ Accept: "application/json" }),
    },
  );
  const data = (await response.json()) as ResultEnvelope<AutocorrectControlStatus>;
  const status = data.result ?? data.data;
  if (!response.ok || !status) {
    throw new Error(
      safeApiErrorMessage(data, "Autocorrect status was unavailable safely."),
    );
  }
  return status;
}

export async function submitAutocorrectProposalPreview(
  request: AutocorrectProposalRequest,
): Promise<AutocorrectProposal> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.autocorrectProposalPreview}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
        "Content-Type": "application/json",
      }),
      body: JSON.stringify(request),
    },
  );
  const data = (await response.json()) as ResultEnvelope<AutocorrectProposal>;
  const proposal = data.result ?? data.data;
  if (!response.ok || !proposal) {
    throw new Error(
      safeApiErrorMessage(data, "Autocorrect proposal was rejected safely."),
    );
  }
  return proposal;
}

export async function submitAutocorrectReviewPreview(
  request: AutocorrectReviewRequest,
): Promise<AutocorrectReviewReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.autocorrectReviewPreview}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
        "Content-Type": "application/json",
      }),
      body: JSON.stringify(request),
    },
  );
  const data = (await response.json()) as ResultEnvelope<AutocorrectReviewReceipt>;
  const receipt = data.result ?? data.data;
  if (!response.ok || !receipt) {
    throw new Error(
      safeApiErrorMessage(data, "Autocorrect review was rejected safely."),
    );
  }
  return receipt;
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
      safeApiErrorMessage(data, "Preview request was rejected safely."),
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
      safeApiErrorMessage(data, "Turn router preview failed safely."),
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
  binding: BackendTruthReadBinding | null = null,
): Promise<FounderLoopActionDecisionReceipt> {
  return submitActionLifecycleDecision(actionId, decision, request, binding);
}

export async function submitActionCancellation(
  actionId: string,
  request: FounderLoopActionDecisionRequest,
  binding: BackendTruthReadBinding | null = null,
): Promise<FounderLoopActionDecisionReceipt> {
  return submitActionLifecycleDecision(actionId, "cancel", request, binding);
}

async function submitActionLifecycleDecision(
  actionId: string,
  decision: FounderLoopActionLifecycleDecisionKind,
  request: FounderLoopActionDecisionRequest,
  binding: BackendTruthReadBinding | null,
): Promise<FounderLoopActionDecisionReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const expectedRevisionRef = request.expected_revision_ref;
  if (!expectedRevisionRef) {
    throw new Error(
      "The Action revision is unavailable. Refresh the authoritative Action Inbox before recording a decision.",
    );
  }
  const boundRequest = request;
  const endpoint =
    decision === "cancel"
      ? actionDecisionEndpoint(actionId, "approve").replace(/\/approve$/, "/cancel")
      : actionDecisionEndpoint(actionId, decision);
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${endpoint}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key": actionDecisionIdempotencyRef(
              actionId,
              decision,
              boundRequest,
            ),
          },
          binding,
        ),
      ),
      body: JSON.stringify(boundRequest),
    },
  );
  const data = (await readJsonSafely(
    response,
  )) as ResultEnvelope<FounderLoopActionDecisionReceipt>;
  const revisionConflict = actionInboxRevisionConflictDetail(
    response.status,
    data,
  );
  if (revisionConflict) {
    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent<ActionInboxRevisionConflictDetail>(
          ACTION_INBOX_REVISION_REFRESH_EVENT,
          { detail: revisionConflict },
        ),
      );
    }
    throw new ActionInboxRevisionConflictError(revisionConflict);
  }
  const receipt = data.result ?? data.data;
  if (!response.ok || !receipt) {
    throw new Error(
      safeApiErrorMessage(
        data,
        "Action decision receipt was not recorded safely.",
      ),
    );
  }
  return receipt;
}

function actionInboxRevisionConflictDetail(
  status: number,
  data: unknown,
): ActionInboxRevisionConflictDetail | null {
  if (status !== 409 || !isPlainRecord(data) || !isPlainRecord(data.detail)) {
    return null;
  }
  const detail = data.detail;
  if (
    detail.code !== "FOUNDER_LOOP_ACTION_STALE_REVISION" ||
    detail.refresh_required !== true ||
    typeof detail.current_revision_ref !== "string" ||
    typeof detail.current_generation_ref !== "string" ||
    typeof detail.refresh_route_ref !== "string"
  ) {
    return null;
  }
  return {
    code: "FOUNDER_LOOP_ACTION_STALE_REVISION",
    currentRevisionRef: detail.current_revision_ref,
    currentGenerationRef: detail.current_generation_ref,
    refreshRouteRef: detail.refresh_route_ref,
  };
}

export async function fetchActionReceipt(
  actionId: string,
): Promise<FounderLoopActionDecisionReceipt | null> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${actionReceiptEndpoint(actionId)}`,
    {
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
      }),
    },
  );
  const data =
    (await response.json()) as ResultEnvelope<FounderLoopActionDecisionReceipt>;
  if (!response.ok) {
    throw new Error(
      safeApiErrorMessage(
        data,
        "Action decision receipt was not fetched safely.",
      ),
    );
  }
  return data.result ?? data.data ?? null;
}

export async function commitLocalTask(
  actionId: string,
  request: FounderLoopLocalTaskCommitRequest,
  binding: BackendTruthReadBinding | null = null,
): Promise<FounderLoopLocalTaskCommitReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${actionLocalTaskCommitEndpoint(actionId)}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key": localTaskCommitIdempotencyRef(
              actionId,
              request,
            ),
          },
          binding,
        ),
      ),
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
  binding: BackendTruthReadBinding | null = null,
): Promise<WorkBoardReorderReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.controlCenterWorkBoardReorder}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key": idempotencyRef,
          },
          binding,
        ),
      ),
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

export async function createWorkBoardCard(
  request: WorkBoardCardCreateRequest,
  idempotencyRef: string,
  binding: BackendTruthReadBinding | null = null,
): Promise<WorkBoardCardCreateReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.controlCenterWorkBoardCards}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key": idempotencyRef,
          },
          binding,
        ),
      ),
      body: JSON.stringify(request),
    },
  );
  const data = (await readJsonSafely(
    response,
  )) as ResultEnvelope<WorkBoardCardCreateReceipt>;
  const receipt = data.result ?? data.data;
  if (!response.ok || !receipt) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          data,
          "Work Board card create was not persisted; inspect blocked refs.",
        ),
      ),
    );
  }
  return receipt;
}

export async function createWorkBoardTask(
  request: WorkBoardTaskCreateRequest,
  idempotencyRef: string,
  binding: BackendTruthReadBinding | null = null,
): Promise<WorkBoardTaskCreateReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.controlCenterWorkBoardTasks}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key": idempotencyRef,
          },
          binding,
        ),
      ),
      body: JSON.stringify(request),
    },
  );
  const data = (await readJsonSafely(
    response,
  )) as ResultEnvelope<WorkBoardTaskCreateReceipt>;
  const receipt = data.result ?? data.data;
  if (!response.ok || !receipt) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          data,
          "Work Board task record was not persisted; inspect blocked refs.",
        ),
      ),
    );
  }
  return receipt;
}

export async function fetchControlCenterSettingsStatus(
  binding: BackendTruthReadBinding | null,
): Promise<ControlCenterSettingsStatus> {
  return readEnvelope<ControlCenterSettingsStatus>(
    API_ENDPOINTS.controlCenterSettingsStatus,
    defaultControlCenterReadLimiter,
    binding,
  );
}

export async function fetchAuthorityMissionWorkerState(): Promise<AuthorityMissionWorkerReadModel> {
  const value = await readEnvelope<unknown>(
    API_ENDPOINTS.runtimeAuthorityMissionWorkerState,
  );
  if (!isSafeAuthorityMissionWorkerReadModel(value)) {
    throw new Error(
      "Authority mission worker inspection returned unsafe or incompatible data.",
    );
  }
  return value;
}

export async function fetchAuthorityMissionCompletions(): Promise<AuthorityMissionCompletionReadModel> {
  const value = await readEnvelope<unknown>(
    API_ENDPOINTS.runtimeAuthorityMissionCompletions,
  );
  if (!isSafeAuthorityMissionCompletionReadModel(value)) {
    throw new Error(
      "Authority mission completion inspection returned unsafe or incompatible data.",
    );
  }
  return value;
}

export async function previewAuthorityDecision(
  request: AuthorityActionRequest,
): Promise<AuthorityDecisionPreview> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.runtimeAuthorityDecisionPreview}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
        "Content-Type": "application/json",
      }),
      body: JSON.stringify(request),
    },
  );
  const data = (await readJsonSafely(
    response,
  )) as ResultEnvelope<AuthorityDecisionPreview>;
  const result = data.result ?? data.data;
  if (!response.ok || !result) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          data,
          "Authority decision preview was not available.",
        ),
      ),
    );
  }
  return result;
}

export async function planAuthorityMission(
  request: AuthorityMissionPlanRequest,
): Promise<AuthorityMissionPlan> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.runtimeAuthorityMissionPlan}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders({
        Accept: "application/json",
        "Content-Type": "application/json",
      }),
      body: JSON.stringify(request),
    },
  );
  const data = (await readJsonSafely(
    response,
  )) as ResultEnvelope<AuthorityMissionPlan>;
  const result = data.result ?? data.data;
  if (!response.ok || !result) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          data,
          "Authority mission plan was not available.",
        ),
      ),
    );
  }
  return result;
}

export async function issueAuthorityLease(
  request: AuthorityLeaseIssueRequest,
  binding: BackendTruthReadBinding | null = null,
): Promise<AuthorityLeaseMutationResult> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.runtimeAuthorityLeases}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key":
              authorityLeaseIssueIdempotencyRef(request),
          },
          binding,
        ),
      ),
      body: JSON.stringify(request),
    },
  );
  const data = (await readJsonSafely(
    response,
  )) as ResultEnvelope<AuthorityLeaseMutationResult>;
  const result = data.result ?? data.data;
  if (!response.ok || !result) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          data,
          "Authority lease receipt was not recorded safely.",
        ),
      ),
    );
  }
  return result;
}

export async function approveAndIssueAuthorityLease(
  request: AuthorityLeaseApproveAndIssueRequest,
  binding: BackendTruthReadBinding | null = null,
): Promise<AuthorityLeaseMutationResult> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.runtimeAuthorityLeasesApproveAndIssue}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key": authorityLeaseIssueIdempotencyRef(
              request.lease_issue_request,
            ),
          },
          binding,
        ),
      ),
      body: JSON.stringify(request),
    },
  );
  const data = (await readJsonSafely(
    response,
  )) as ResultEnvelope<AuthorityLeaseMutationResult>;
  const result = data.result ?? data.data;
  if (!response.ok || !result || !result.receipt) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          data,
          "Authority lease approval and receipt were not recorded safely.",
        ),
      ),
    );
  }
  return result;
}

export async function revokeAuthorityLease(
  request: AuthorityLeaseRevokeRequest,
  binding: BackendTruthReadBinding | null = null,
): Promise<AuthorityLeaseMutationResult> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.runtimeAuthorityLeaseRevoke}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key":
              authorityLeaseRevokeIdempotencyRef(request),
          },
          binding,
        ),
      ),
      body: JSON.stringify(request),
    },
  );
  const data = (await readJsonSafely(
    response,
  )) as ResultEnvelope<AuthorityLeaseMutationResult>;
  const result = data.result ?? data.data;
  if (!response.ok || !result) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          data,
          "Authority lease revoke receipt was not recorded safely.",
        ),
      ),
    );
  }
  return result;
}

export async function fetchFounderActionsInbox(
  binding: BackendTruthReadBinding | null,
): Promise<FounderLoopActionsInbox> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const inbox = await readEnvelope<FounderLoopActionsInbox>(
    API_ENDPOINTS.founderActionsInbox,
    defaultControlCenterReadLimiter,
    binding,
  );
  return inbox;
}

export type GovernedRuntimeCommandIntent =
  | "git_status"
  | "focused_pytest"
  | "repo_verifier"
  | "frontend_check"
  | "repo_doctor";

export interface GovernedRuntimeLocalModelControlRequest {
  base_url: string;
  model_ref: string;
  messages: Array<{ role: "user"; content: string }>;
  requested_profile: "local-runtime";
  safe_summary: string;
  allow_bounded_preview: false;
  max_preview_chars: 0;
  timeout_seconds: number;
  max_response_bytes: number;
  metadata_refs: string[];
}

export interface GovernedRuntimeCommandControlRequest {
  intent: GovernedRuntimeCommandIntent;
  requested_profile: "local-runtime" | "operator-approved";
  target_refs: string[];
  safe_summary: string;
  timeout_seconds: number;
  output_byte_limit: number;
  metadata_refs: string[];
}

export interface GovernedRuntimeControlMutationResult {
  operation: string;
  status: "recorded" | "blocked";
  invocationRef?: string;
  receiptRef?: string;
  safeMessage: string;
}

const GOVERNED_RUNTIME_MUTATION_METHOD = "POST" as const;

async function governedRuntimeMutationIdempotencyRef(
  operation: string,
  payload: unknown,
): Promise<string> {
  const digest = await sha256Hex(portableCanonicalJson({ operation, payload }));
  return `idempotency-ref:control-center-governed-runtime:${operation}:sha256:${digest}`;
}

function safeRuntimeMutationRef(value: unknown): string | undefined {
  return isSafeActionWorkQueueRef(value) ? value : undefined;
}

async function postGovernedRuntimeControlMutation(
  endpoint: string,
  operation: string,
  request: object,
  binding: BackendTruthReadBinding | null,
): Promise<GovernedRuntimeControlMutationResult> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const idempotencyRef = await governedRuntimeMutationIdempotencyRef(
    operation,
    request,
  );
  const response = await fetch(`${API_BASE_POLICY.baseUrl}${endpoint}`, {
    method: GOVERNED_RUNTIME_MUTATION_METHOD,
    headers: withLocalApiAuthHeaders(
      withBackendTruthMutationHeaders(
        {
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-UAA-Idempotency-Key": idempotencyRef,
        },
        binding,
      ),
    ),
    body: JSON.stringify(request),
  });
  const envelope = (await readJsonSafely(response)) as ResultEnvelope<unknown>;
  if (!response.ok) {
    throw new Error(
      safeApiErrorMessage(
        envelope,
        "The governed runtime request failed closed without changing authority.",
      ),
    );
  }
  const payload = envelope.result ?? envelope.data;
  if (!isPlainRecord(payload)) {
    throw new Error(
      "The governed runtime response did not include a safe backend receipt projection.",
    );
  }
  const record = isPlainRecord(payload.record) ? payload.record : undefined;
  const receipt = isPlainRecord(payload.receipt) ? payload.receipt : undefined;
  const invocationRef = safeRuntimeMutationRef(record?.invocation_ref);
  const receiptRef =
    safeRuntimeMutationRef(payload.receipt_ref) ??
    safeRuntimeMutationRef(receipt?.receipt_ref) ??
    safeRuntimeMutationRef(record?.receipt_ref);
  const recorded = (envelope.success ?? envelope.ok) === true;
  return {
    operation,
    status: recorded ? "recorded" : "blocked",
    invocationRef,
    receiptRef,
    safeMessage: recorded
      ? "The backend recorded the exact governed runtime request. Refreshing receipt truth now."
      : safeApiErrorMessage(
          envelope,
          "The backend blocked the governed runtime request; no broader authority was granted.",
        ),
  };
}

export async function requestGovernedRuntimeLocalModelProposal(
  request: GovernedRuntimeLocalModelControlRequest,
  binding: BackendTruthReadBinding | null = null,
): Promise<GovernedRuntimeControlMutationResult> {
  return postGovernedRuntimeControlMutation(
    API_ENDPOINTS.runtimeLocalModelCall,
    "local-model-call",
    request,
    binding,
  );
}

export async function requestGovernedRuntimeCommand(
  request: GovernedRuntimeCommandControlRequest,
  binding: BackendTruthReadBinding | null = null,
): Promise<GovernedRuntimeControlMutationResult> {
  return postGovernedRuntimeControlMutation(
    API_ENDPOINTS.runtimeCommandRun,
    `command-${request.intent}`,
    request,
    binding,
  );
}

export async function decideGovernedRuntimeInvocation(
  invocationRef: string,
  decision: "approve" | "deny",
  exactEnvelope: {
    approval_ref: string;
    action_envelope_ref: string;
    exact_scope_ref: string;
    payload_fingerprint_ref: string;
    policy_decision_ref: string;
    adapter_id: string;
    command_intent?: GovernedRuntimeCommandIntent | null;
    rollback_ref: string;
    safe_disable_ref: string;
    safe_disable_posture_ref: string;
  },
  binding: BackendTruthReadBinding | null = null,
): Promise<GovernedRuntimeControlMutationResult> {
  return postGovernedRuntimeControlMutation(
    runtimeInvocationDecisionEndpoint(invocationRef),
    `${decision}-invocation`,
    {
      approval_ref: exactEnvelope.approval_ref,
      approval_scope_ref: "approval-scope-ref:governed-runtime-exact-envelope",
      decision,
      action_envelope_ref: exactEnvelope.action_envelope_ref,
      exact_scope_ref: exactEnvelope.exact_scope_ref,
      expected_payload_fingerprint_ref: exactEnvelope.payload_fingerprint_ref,
      expected_policy_decision_ref: exactEnvelope.policy_decision_ref,
      adapter_id: exactEnvelope.adapter_id,
      command_intent: exactEnvelope.command_intent ?? undefined,
      rollback_ref: exactEnvelope.rollback_ref,
      safe_disable_ref: exactEnvelope.safe_disable_ref,
      safe_disable_posture_ref: exactEnvelope.safe_disable_posture_ref,
      safe_summary: `Operator recorded an exact ${decision} decision from the Control Center.`,
      metadata_refs: ["metadata-ref:control-center-governed-runtime-decision"],
    },
    binding,
  );
}

export async function executeGovernedRuntimeInvocation(
  invocationRef: string,
  exactEnvelope: {
    approval_ref: string;
    action_envelope_ref: string;
    payload_fingerprint_ref: string;
    policy_decision_ref: string;
    command_intent?: GovernedRuntimeCommandIntent | null;
  },
  binding: BackendTruthReadBinding | null = null,
): Promise<GovernedRuntimeControlMutationResult> {
  const commandRequest = exactEnvelope.command_intent
    ? {
        intent: exactEnvelope.command_intent,
        requested_profile: "operator-approved",
        target_refs: [
          `target-ref:control-center-governed-runtime:${exactEnvelope.command_intent}`,
        ],
        approval_ref: exactEnvelope.approval_ref,
        safe_summary: "Run one exact approved governed runtime command lane.",
        timeout_seconds: 30,
        output_byte_limit: 4096,
        metadata_refs: ["metadata-ref:control-center-governed-runtime-execute"],
      }
    : undefined;
  return postGovernedRuntimeControlMutation(
    runtimeInvocationExecuteEndpoint(invocationRef),
    "execute-invocation",
    {
      approval_ref: exactEnvelope.approval_ref,
      action_envelope_ref: exactEnvelope.action_envelope_ref,
      expected_payload_fingerprint_ref: exactEnvelope.payload_fingerprint_ref,
      expected_policy_decision_ref: exactEnvelope.policy_decision_ref,
      command_request: commandRequest,
      safe_summary:
        "Execute one exact approval-bound governed runtime envelope and record redacted evidence.",
      metadata_refs: ["metadata-ref:control-center-governed-runtime-execute"],
    },
    binding,
  );
}

export async function safeDisableGovernedRuntime(
  binding: BackendTruthReadBinding | null = null,
): Promise<GovernedRuntimeControlMutationResult> {
  return postGovernedRuntimeControlMutation(
    API_ENDPOINTS.runtimeSafeDisable,
    "safe-disable",
    {
      reason_ref: "reason-ref:control-center-governed-runtime-safe-disable",
      safe_summary: "Operator requested governed runtime safe-disable from the Control Center.",
      metadata_refs: ["metadata-ref:control-center-governed-runtime-safe-disable"],
    },
    binding,
  );
}

export async function submitTodayActionEnvelope(
  request: FounderLoopActionEnvelopePromotionRequest,
  binding: BackendTruthReadBinding | null,
): Promise<FounderLoopActionEnvelopePromotionReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.founderTodayActionEnvelope}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key": todayActionEnvelopeIdempotencyRef(
              request.today_item_ref,
              request,
            ),
          },
          binding,
        ),
      ),
      body: JSON.stringify(request),
    },
  );
  const data =
    (await response.json()) as ResultEnvelope<FounderLoopActionEnvelopePromotionReceipt>;
  const receipt = data.result ?? data.data;
  if (!response.ok || !receipt) {
    throw new Error(
      safeApiErrorMessage(
        data,
        "Today action envelope receipt was not recorded safely.",
      ),
    );
  }
  return receipt;
}

export async function submitWebEvidenceAttachment(
  request: WebEvidenceProductSliceRequest,
  binding: BackendTruthReadBinding | null,
): Promise<WebEvidenceProductSliceReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.controlCenterWebEvidenceAttach}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Ref": request.request_ref,
          },
          binding,
        ),
      ),
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
  binding: BackendTruthReadBinding | null,
): Promise<ChatTurnReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.controlCenterChatTurns}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key": chatTurnReceiptIdempotencyRef(
              request.turn_ref ?? request.model_ref,
              request,
            ),
          },
          binding,
        ),
      ),
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
  binding: BackendTruthReadBinding | null,
): Promise<ChatTurnReceipt> {
  return readEnvelope<ChatTurnReceipt>(
    chatTurnReceiptEndpoint(turnRef),
    defaultControlCenterReadLimiter,
    binding,
  );
}

export async function recordChatHandoff(
  turnRef: string,
  target: ChatHandoffTarget,
  binding: BackendTruthReadBinding | null,
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
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key": chatHandoffIdempotencyRef(
              turnRef,
              target,
              request,
            ),
          },
          binding,
        ),
      ),
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
  binding: BackendTruthReadBinding | null,
): Promise<MemoryReviewDecisionReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${memoryReviewDecisionEndpoint(candidateRef, decision)}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key": memoryReviewDecisionIdempotencyRef(
              candidateRef,
              decision,
              request,
            ),
          },
          binding,
        ),
      ),
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

export async function fetchFounderMemoryContextPacks(
  binding: BackendTruthReadBinding | null,
): Promise<FounderLoopMemoryContextPacks> {
  return readEnvelope<FounderLoopMemoryContextPacks>(
    API_ENDPOINTS.founderMemoryContextPacks,
    defaultControlCenterReadLimiter,
    binding,
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

export async function fetchFounderMemoryReview(
  binding: BackendTruthReadBinding | null,
): Promise<FounderLoopMemoryReview> {
  return readEnvelope<FounderLoopMemoryReview>(
    API_ENDPOINTS.founderMemoryReview,
    defaultControlCenterReadLimiter,
    binding,
  );
}

export async function fetchFounderMemoryWorkbench(): Promise<FounderLoopMemoryWorkbench> {
  return readEnvelope<FounderLoopMemoryWorkbench>(
    API_ENDPOINTS.founderMemoryWorkbench,
  );
}

export async function recordManualMemoryCandidate(
  request: ManualMemoryCandidateRequest,
  binding: BackendTruthReadBinding | null,
): Promise<ManualMemoryCandidateReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.founderMemoryManualCandidate}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key": manualMemoryCandidateIdempotencyRef(request),
          },
          binding,
        ),
      ),
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
  binding: BackendTruthReadBinding | null,
): Promise<MemoryFeedbackReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.founderMemoryFeedback}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key": memoryFeedbackIdempotencyRef(request),
          },
          binding,
        ),
      ),
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
  binding: BackendTruthReadBinding | null,
): Promise<FounderLoopMemoryContextPackActionProposalReceipt> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${memoryContextPackActionProposalEndpoint(contextPackRef)}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key": memoryContextPackActionIdempotencyRef(
              contextPackRef,
              request,
            ),
          },
          binding,
        ),
      ),
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
  decision: FounderLoopActionLifecycleDecisionKind,
  request?: FounderLoopActionDecisionRequest,
): string {
  const safeActionId = actionId
    .replace(/^founder-action:/, "")
    .toLowerCase()
    .replace(/[^a-z0-9_.:-]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `idempotency-ref:control-center-action:${decision}:${safeActionId || "missing"}:${safeChatSuffix(request?.decision_reason_ref ?? "decision")}:${safeHashSuffix(request?.expected_revision_ref ?? "revision-missing")}`;
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

function authorityLeaseIssueIdempotencyRef(
  request: AuthorityLeaseIssueRequest,
): string {
  const refMaterial = stableStringifyForIdempotency(request);
  return `idempotency-ref:control-center-authority-lease:${safeChatSuffix(request.mode)}:${safeHashSuffix(refMaterial)}`;
}

function authorityLeaseRevokeIdempotencyRef(
  request: AuthorityLeaseRevokeRequest,
): string {
  const refMaterial = stableStringifyForIdempotency(request);
  return `idempotency-ref:control-center-authority-revoke:${safeChatSuffix(request.lease_ref)}:${safeHashSuffix(refMaterial)}`;
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

function isSafeRuntimeInterfaceMode(
  value: RuntimeInterfaceModeReadModel | undefined,
): value is RuntimeInterfaceModeReadModel {
  if (
    value === undefined ||
    !isPlainRecord(value.hermes_cli_posture) ||
    !Array.isArray(value.mode_profiles)
  ) {
    return false;
  }
  const deniedFlags: Array<keyof RuntimeInterfaceModeReadModel> = [
    "control_center_mints_authority",
    "uaa_native_agent_enabled",
    "uaa_planning_enabled",
    "uaa_execution_enabled",
    "raw_prompt_persisted",
    "raw_response_persisted",
    "raw_provider_payload_persisted",
    "raw_log_persisted",
    "raw_local_path_persisted",
    "credential_material_persisted",
  ];
  const modes = new Set(value.mode_profiles.map((profile) => profile.mode));
  return (
    value.schema_version === "runtime_interface_mode.v1" &&
    (value.active_mode === "disabled" || value.active_mode === "shell_guarded") &&
    (value.interface_enabled === false || value.active_mode === "shell_guarded") &&
    value.python_core_owns_truth === true &&
    value.memory_update_policy === "candidate_only_review_required" &&
    modes.has("disabled") &&
    modes.has("shell_guarded") &&
    modes.has("operator_override") &&
    modes.has("pure_hermes_pass_through") &&
    value.mode_profiles.every(
      (profile) =>
        profile.uaa_native_agent_enabled === false &&
        profile.uaa_planning_enabled === false &&
        profile.uaa_execution_enabled === false,
    ) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:hermes-unrestricted-command-execution",
    ) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:hermes-direct-memory-write",
    ) &&
    deniedFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeHermesContextPack(
  value: HermesContextPackReadModel | undefined,
): value is HermesContextPackReadModel {
  if (value === undefined || !Array.isArray(value.sections)) {
    return false;
  }
  const deniedFlags: Array<keyof HermesContextPackReadModel> = [
    "hermes_receives_raw_database_access",
    "raw_memory_records_exposed",
    "raw_crm_records_exposed",
    "raw_chat_transcripts_exposed",
    "raw_local_paths_exposed",
    "raw_logs_exposed",
    "credential_material_exposed",
    "unbounded_private_content_exposed",
    "direct_memory_write_enabled",
  ];
  const sources = new Set(value.sections.map((section) => section.source_surface));
  const disabledProjection =
    value.projection_enabled === false &&
    value.status === "disabled_uaa_native_only" &&
    value.section_count === 0 &&
    value.source_count === 0 &&
    value.sections.length === 0;
  const enabledProjection =
    value.projection_enabled === true &&
    value.projected_provenance_visible === true &&
    value.section_count === value.sections.length &&
    value.section_count >= 9 &&
    sources.has("Memory Review and reviewed context") &&
    sources.has("CRM local command center") &&
    sources.has("Chat turns and handoffs") &&
    sources.has("Evidence") &&
    sources.has("Proof") &&
    value.sections.every(
      (section) =>
        section.projected_to_hermes === true &&
        isNonEmptyStringArray(section.provenance_refs) &&
        isNonEmptyStringArray(section.why_shown_refs),
    );
  return (
    value.schema_version === "hermes_context_pack.v1" &&
    value.context_pack_ref ===
      "hermes-context-pack-ref:uaa-curated-runtime-interface-mode" &&
    value.memory_update_policy === "candidate_only_review_required" &&
    (disabledProjection || enabledProjection) &&
    deniedFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeCapabilityDiscovery(
  value: RuntimeCapabilityDiscoveryReadModel | undefined,
): value is RuntimeCapabilityDiscoveryReadModel {
  if (
    value === undefined ||
    !Array.isArray(value.capability_groups) ||
    !isSafeRuntimeToolsetCapabilityPosture(value.toolset_posture)
  ) {
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
    value.toolset_posture.uaa_allowed_execution_count === 0 &&
    value.route_ref === "GET /api/runtime/capability-discovery" &&
    value.cli_ref === "uaa runtime inspect-capability-discovery" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-capability-discovery-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    TRUST_AUTHORITY_DECISION_OUTCOMES.includes(
      value.authority_state_decision_outcome,
    ) &&
    typeof value.authority_state_status === "string" &&
    value.authority_state_status.length > 0 &&
    typeof value.authority_state_operator_message === "string" &&
    value.authority_state_operator_message.length > 0 &&
    isNonEmptyStringArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    isNonEmptyStringArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:runtime-tool-invocation:not-implemented",
    ) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
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

function isSafeRuntimeToolsetCapabilityPosture(
  value: RuntimeToolsetCapabilityPosture | undefined,
): value is RuntimeToolsetCapabilityPosture {
  if (value === undefined || !Array.isArray(value.records)) {
    return false;
  }
  const allowedSupportStatuses = new Set([
    "runtime_supported_by_reference",
    "runtime_configured_metadata_only",
    "runtime_planned_disabled",
    "runtime_unsupported",
    "runtime_blocked_by_uaa",
  ]);
  const allowedAllowanceStatuses = new Set([
    "enabled_read_only",
    "configured_metadata_only",
    "approval_required_future_lane",
    "blocked",
    "unsupported",
  ]);
  const allowedSideEffectClasses = new Set([
    "read_only_metadata",
    "local_workspace",
    "external_mutation",
    "high_authority",
    "unsupported",
  ]);
  const recordCount = value.records.length;
  const runtimeSupportedCount = value.records.filter(
    (record) => record.runtime_supports_toolset,
  ).length;
  const allowanceCounts: Record<string, number> = {
    enabled_read_only: 0,
    configured_metadata_only: 0,
    approval_required_future_lane: 0,
    blocked: 0,
    unsupported: 0,
  };
  for (const record of value.records) {
    if (
      !allowedSupportStatuses.has(record.runtime_support_status) ||
      !allowedAllowanceStatuses.has(record.uaa_allowance_status) ||
      !allowedSideEffectClasses.has(record.side_effect_class)
    ) {
      return false;
    }
    allowanceCounts[record.uaa_allowance_status] += 1;
  }
  const deniedTopLevelFlags: Array<keyof RuntimeToolsetCapabilityPosture> = [
    "live_tool_invocation_enabled",
    "toolset_config_mutation_enabled",
    "hermes_toolset_enablement_enabled",
    "raw_tool_payload_persisted",
    "production_authority_enabled",
  ];
  return (
    value.schema_version === "runtime_toolset_capability_posture.v1" &&
    value.status === "read_only_toolset_capability_posture" &&
    value.toolset_count === recordCount &&
    value.runtime_supported_count === runtimeSupportedCount &&
    value.uaa_allowed_execution_count === 0 &&
    value.enabled_read_only_count === allowanceCounts.enabled_read_only &&
    value.configured_metadata_only_count ===
      allowanceCounts.configured_metadata_only &&
    value.approval_required_future_count ===
      allowanceCounts.approval_required_future_lane &&
    value.blocked_count === allowanceCounts.blocked &&
    value.unsupported_count === allowanceCounts.unsupported &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:runtime-toolset-invocation",
    ) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.records.every(
      (record) =>
        record.uaa_allows_execution === false &&
        record.tool_invocation_enabled === false &&
        record.toolset_config_mutation_enabled === false &&
        record.hermes_toolset_enablement_enabled === false &&
        record.raw_tool_payload_persisted === false &&
        isNonEmptyStringArray(record.blocked_authority_refs) &&
        isNonEmptyStringArray(record.next_safe_action_refs),
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeToolRegistry(
  value: RuntimeToolRegistryAvailabilityReadModel | undefined,
): value is RuntimeToolRegistryAvailabilityReadModel {
  if (value === undefined || !Array.isArray(value.entries)) {
    return false;
  }
  const allowedAvailabilityStatuses = new Set([
    "available_metadata_only",
    "configured_disabled",
    "approval_required_future_lane",
    "blocked",
    "unsupported",
  ]);
  const allowedConfiguredStatuses = new Set([
    "configured_metadata_only",
    "configured_disabled",
    "unconfigured",
    "blocked_by_policy",
    "unsupported",
  ]);
  const allowedAuthorityClasses = new Set([
    "validation_only",
    "preview_only",
    "approval_required_future_lane",
    "blocked_high_authority",
    "unsupported",
  ]);
  const entryCount = value.entries.length;
  const uaaNativeCount = value.entries.filter(
    (entry) => entry.origin === "uaa_native",
  ).length;
  const delegatedReferenceCount = value.entries.filter(
    (entry) => entry.origin !== "uaa_native",
  ).length;
  const previewAvailableCount = value.entries.filter(
    (entry) => entry.uaa_available_for_preview,
  ).length;
  const availabilityCounts: Record<string, number> = {
    available_metadata_only: 0,
    configured_disabled: 0,
    approval_required_future_lane: 0,
    blocked: 0,
    unsupported: 0,
  };
  for (const entry of value.entries) {
    if (
      !allowedAvailabilityStatuses.has(entry.availability_status) ||
      !allowedConfiguredStatuses.has(entry.configured_status) ||
      !allowedAuthorityClasses.has(entry.authority_class)
    ) {
      return false;
    }
    availabilityCounts[entry.availability_status] += 1;
  }
  const deniedTopLevelFlags: Array<
    keyof RuntimeToolRegistryAvailabilityReadModel
  > = [
    "tool_invocation_enabled",
    "remote_discovery_enabled",
    "live_web_fetch_enabled",
    "provider_model_call_enabled",
    "plugin_import_enabled",
    "connector_write_activation_enabled",
    "raw_tool_payload_persisted",
    "production_authority_enabled",
  ];
  return (
    value.schema_version === "runtime_tool_registry_availability.v1" &&
    value.status === "read_only_tool_registry_availability" &&
    value.route_ref === "GET /api/runtime/tool-registry" &&
    value.cli_ref === "uaa runtime inspect-tool-registry" &&
    value.capability_discovery_route_ref ===
      "GET /api/runtime/capability-discovery" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-tool-registry-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    TRUST_AUTHORITY_DECISION_OUTCOMES.includes(
      value.authority_state_decision_outcome,
    ) &&
    typeof value.authority_state_status === "string" &&
    value.authority_state_status.length > 0 &&
    typeof value.authority_state_operator_message === "string" &&
    value.authority_state_operator_message.length > 0 &&
    isNonEmptyStringArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    isNonEmptyStringArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:runtime-tool-invocation:not-implemented",
    ) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.tool_count === entryCount &&
    value.uaa_native_count === uaaNativeCount &&
    value.delegated_reference_count === delegatedReferenceCount &&
    value.invocation_enabled_count === 0 &&
    value.preview_available_count === previewAvailableCount &&
    value.available_metadata_only_count ===
      availabilityCounts.available_metadata_only &&
    value.configured_disabled_count ===
      availabilityCounts.configured_disabled &&
    value.approval_required_future_count ===
      availabilityCounts.approval_required_future_lane &&
    value.blocked_count === availabilityCounts.blocked &&
    value.unsupported_count === availabilityCounts.unsupported &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:runtime-tool-registry-invocation",
    ) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.entries.every(
      (entry) =>
        entry.uaa_allows_invocation === false &&
        entry.execution_enabled === false &&
        entry.remote_discovery_performed === false &&
        entry.live_web_fetch_performed === false &&
        entry.provider_model_call_performed === false &&
        entry.plugin_import_enabled === false &&
        entry.connector_write_activation_enabled === false &&
        entry.raw_tool_payload_persisted === false &&
        isNonEmptyStringArray(entry.proof_refs) &&
        isNonEmptyStringArray(entry.blocked_authority_refs) &&
        isNonEmptyStringArray(entry.next_safe_action_refs),
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeVirtualProviderMoa(
  value: RuntimeVirtualProviderMoaReadModel | undefined,
): value is RuntimeVirtualProviderMoaReadModel {
  if (value === undefined || !Array.isArray(value.presets)) {
    return false;
  }
  const allowedStatuses = new Set([
    "metadata_only",
    "readiness_only",
    "blocked_requires_authority",
  ]);
  const presetCount = value.presets.length;
  const agentSlotCount = value.presets.reduce(
    (count, preset) => count + preset.slots.length,
    0,
  );
  const readyPresetCount = value.presets.filter(
    (preset) => preset.status === "readiness_only",
  ).length;
  const blockedPresetCount = value.presets.filter(
    (preset) => preset.status === "blocked_requires_authority",
  ).length;
  const deniedTopLevelFlags: Array<keyof RuntimeVirtualProviderMoaReadModel> = [
    "live_model_fanout_enabled",
    "provider_sdk_enabled",
    "external_runtime_dispatch_enabled",
    "hidden_advisor_prompts_enabled",
    "raw_prompt_persistence_enabled",
    "raw_response_persistence_enabled",
    "output_authority_enabled",
    "production_authority_enabled",
  ];
  return (
    value.schema_version === "runtime_virtual_provider_moa.v1" &&
    value.status === "read_only_virtual_provider_preset_posture" &&
    value.route_ref === "GET /api/runtime/virtual-provider-moa" &&
    value.cli_ref === "uaa runtime inspect-virtual-provider-moa" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-virtual-provider-moa-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    TRUST_AUTHORITY_DECISION_OUTCOMES.includes(
      value.authority_state_decision_outcome,
    ) &&
    typeof value.authority_state_status === "string" &&
    value.authority_state_status.length > 0 &&
    typeof value.authority_state_operator_message === "string" &&
    value.authority_state_operator_message.length > 0 &&
    isNonEmptyStringArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    isNonEmptyStringArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:virtual-provider-moa-live-fanout:not-implemented",
    ) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.preset_count === presetCount &&
    value.agent_slot_count === agentSlotCount &&
    value.ready_preset_count === readyPresetCount &&
    value.blocked_preset_count === blockedPresetCount &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:virtual-provider-moa-no-live-model-fanout",
    ) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.presets.every(
      (preset) =>
        allowedStatuses.has(preset.status) &&
        preset.slot_count === preset.slots.length &&
        preset.per_agent_output_envelopes_required === true &&
        preset.comparison_proof_required === true &&
        preset.live_model_fanout_enabled === false &&
        preset.provider_sdk_enabled === false &&
        preset.external_runtime_dispatch_enabled === false &&
        preset.hidden_advisor_prompts_enabled === false &&
        preset.raw_prompt_persistence_enabled === false &&
        preset.raw_response_persistence_enabled === false &&
        preset.output_authority_enabled === false &&
        preset.production_authority_enabled === false &&
        isNonEmptyStringArray(preset.blocked_authority_refs) &&
        preset.slots.every(
          (slot) =>
            slot.configured_for_live_call === false &&
            slot.provider_sdk_call_enabled === false &&
            slot.external_runtime_dispatch_enabled === false &&
            slot.hidden_advisor_prompt_enabled === false &&
            slot.raw_prompt_persisted === false &&
            slot.raw_response_persisted === false &&
            slot.output_authoritative === false &&
            slot.production_authority_enabled === false &&
            isNonEmptyStringArray(slot.blocked_authority_refs),
        ),
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeUsageCostAnalytics(
  value: RuntimeUsageCostAnalyticsReadModel | undefined,
): value is RuntimeUsageCostAnalyticsReadModel {
  if (value === undefined || !Array.isArray(value.records)) {
    return false;
  }
  const allowedSources = new Set([
    "manual_diagnostic_receipt",
    "runtime_receipt_metadata",
    "provider_catalog_reference",
    "delegated_runtime_future",
  ]);
  const allowedStatuses = new Set([
    "recorded_diagnostic",
    "read_only_estimate",
    "blocked_missing_authority",
  ]);
  const totalInput = value.records.reduce(
    (sum, record) => sum + record.estimated_input_tokens,
    0,
  );
  const totalOutput = value.records.reduce(
    (sum, record) => sum + record.estimated_output_tokens,
    0,
  );
  const totalUnits = value.records.reduce(
    (sum, record) => sum + record.estimated_total_tokens,
    0,
  );
  const totalLatency = value.records.reduce(
    (sum, record) => sum + record.latency_ms,
    0,
  );
  const totalCostMinor = value.records.reduce(
    (sum, record) => sum + record.estimated_cost_minor_units,
    0,
  );
  const deniedTopLevelFlags: Array<keyof RuntimeUsageCostAnalyticsReadModel> = [
    "operator_export_available",
    "billing_action_enabled",
    "provider_call_enabled",
    "provider_sdk_enabled",
    "live_price_fetch_enabled",
    "raw_prompt_persistence_enabled",
    "raw_response_persistence_enabled",
    "provider_payload_persistence_enabled",
    "output_authority_enabled",
    "production_authority_enabled",
  ];
  return (
    value.schema_version === "runtime_usage_cost_analytics.v1" &&
    value.status === "read_only_redacted_accounting_posture" &&
    value.route_ref === "GET /api/runtime/usage-cost-analytics" &&
    value.cli_ref === "uaa runtime inspect-usage-cost-analytics" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-usage-cost-analytics-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    hasExactStringValue(
      value.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    typeof value.authority_state_status === "string" &&
    value.authority_state_status.length > 0 &&
    typeof value.authority_state_operator_message === "string" &&
    value.authority_state_operator_message.length > 0 &&
    isNonEmptyStringArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    isNonEmptyStringArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:usage-cost-provider-call:not-implemented",
    ) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.record_count === value.records.length &&
    value.manual_diagnostic_receipt_count ===
      value.records.filter(
        (record) => record.source_kind === "manual_diagnostic_receipt",
      ).length &&
    value.runtime_receipt_record_count ===
      value.records.filter(
        (record) => record.source_kind === "runtime_receipt_metadata",
      ).length &&
    value.provider_catalog_reference_count ===
      value.records.filter(
        (record) => record.source_kind === "provider_catalog_reference",
      ).length &&
    value.blocked_record_count ===
      value.records.filter(
        (record) => record.status === "blocked_missing_authority",
      ).length &&
    value.total_estimated_input_tokens === totalInput &&
    value.total_estimated_output_tokens === totalOutput &&
    value.total_estimated_tokens === totalUnits &&
    value.total_latency_ms === totalLatency &&
    value.total_estimated_cost_minor_units === totalCostMinor &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:usage-cost-analytics-no-billing-action",
    ) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.records.every(
      (record) =>
        allowedSources.has(record.source_kind) &&
        allowedStatuses.has(record.status) &&
        record.estimated_total_tokens ===
          record.estimated_input_tokens + record.estimated_output_tokens &&
        record.estimated_input_tokens >= 0 &&
        record.estimated_output_tokens >= 0 &&
        record.estimated_total_tokens >= 0 &&
        record.latency_ms >= 0 &&
        record.estimated_cost_minor_units >= 0 &&
        record.provider_call_performed === false &&
        record.provider_sdk_call_performed === false &&
        record.billing_action_performed === false &&
        record.live_price_fetch_performed === false &&
        record.raw_prompt_persisted === false &&
        record.raw_response_persisted === false &&
        record.provider_payload_persisted === false &&
        record.output_authoritative === false &&
        record.production_authority_enabled === false &&
        isNonEmptyStringArray(record.blocked_authority_refs),
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimePromptStabilityTiers(
  value: RuntimePromptStabilityTiersReadModel | undefined,
): value is RuntimePromptStabilityTiersReadModel {
  if (value === undefined || !Array.isArray(value.tiers)) {
    return false;
  }
  const allowedKinds = new Set([
    "stable_identity_policy",
    "durable_context_refs",
    "retrieval_refs",
    "volatile_runtime_state",
    "operator_turn_ref",
  ]);
  const allowedClasses = new Set([
    "stable_cache_candidate",
    "semi_stable_ref_set",
    "volatile_no_cache",
    "operator_scoped_no_cache",
  ]);
  const deniedTopLevelFlags: Array<keyof RuntimePromptStabilityTiersReadModel> = [
    "raw_prompt_persistence_enabled",
    "raw_response_persistence_enabled",
    "provider_payload_persistence_enabled",
    "hidden_prompt_injection_enabled",
    "context_injection_enabled",
    "model_call_enabled",
    "provider_sdk_enabled",
    "model_output_authority_enabled",
    "cache_write_enabled",
    "production_authority_enabled",
  ];
  return (
    value.schema_version === "runtime_prompt_stability_tiers.v1" &&
    value.status === "read_only_prompt_contract_posture" &&
    value.route_ref === "GET /api/runtime/prompt-stability-tiers" &&
    value.cli_ref === "uaa runtime inspect-prompt-stability-tiers" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-prompt-stability-tiers-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    hasExactStringValue(
      value.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    typeof value.authority_state_status === "string" &&
    value.authority_state_status.length > 0 &&
    typeof value.authority_state_operator_message === "string" &&
    value.authority_state_operator_message.length > 0 &&
    isNonEmptyStringArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    isNonEmptyStringArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:prompt-stability-model-call:not-implemented",
    ) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.tier_count === value.tiers.length &&
    value.stable_cache_candidate_count ===
      value.tiers.filter(
        (tier) => tier.stability_class === "stable_cache_candidate",
      ).length &&
    value.semi_stable_ref_set_count ===
      value.tiers.filter((tier) => tier.stability_class === "semi_stable_ref_set")
        .length &&
    value.volatile_no_cache_count ===
      value.tiers.filter((tier) => tier.stability_class === "volatile_no_cache")
        .length &&
    value.operator_scoped_no_cache_count ===
      value.tiers.filter(
        (tier) => tier.stability_class === "operator_scoped_no_cache",
      ).length &&
    value.safe_prompt_manifest_required === true &&
    value.prompt_hashes_required === true &&
    value.redacted_receipt_required === true &&
    value.proof_link_required === true &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:prompt-stability-no-hidden-prompt-injection",
    ) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.tiers.every(
      (tier) =>
        allowedKinds.has(tier.tier_kind) &&
        allowedClasses.has(tier.stability_class) &&
        tier.cache_write_enabled === false &&
        tier.raw_prompt_persisted === false &&
        tier.raw_response_persisted === false &&
        tier.provider_payload_persisted === false &&
        tier.hidden_prompt_injection_enabled === false &&
        tier.context_injection_enabled === false &&
        tier.model_call_performed === false &&
        tier.provider_sdk_call_performed === false &&
        tier.model_output_authoritative === false &&
        tier.production_authority_enabled === false &&
        isNonEmptyStringArray(tier.source_refs) &&
        isNonEmptyStringArray(tier.blocked_authority_refs),
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeContextBudgetPressure(
  value: RuntimeContextBudgetPressureReadModel | undefined,
): value is RuntimeContextBudgetPressureReadModel {
  if (
    value === undefined ||
    !Array.isArray(value.segments) ||
    !Array.isArray(value.proposals)
  ) {
    return false;
  }
  const allowedPressureLevels = new Set([
    "within_budget",
    "warning",
    "critical",
    "blocked",
  ]);
  const allowedProposalKinds = new Set([
    "trim_context_refs",
    "request_operator_choice",
    "summarize_with_approval",
    "defer_context",
  ]);
  const deniedTopLevelFlags: Array<keyof RuntimeContextBudgetPressureReadModel> =
    [
      "hidden_compression_enabled",
      "automatic_context_mutation_enabled",
      "model_summarization_enabled",
      "raw_context_persistence_enabled",
      "raw_prompt_persistence_enabled",
      "raw_response_persistence_enabled",
      "provider_payload_persistence_enabled",
      "context_injection_enabled",
      "provider_sdk_enabled",
      "cache_write_enabled",
      "production_authority_enabled",
    ];
  return (
    value.schema_version === "runtime_context_budget_pressure.v1" &&
    value.status === "read_only_context_budget_pressure_posture" &&
    value.route_ref === "GET /api/runtime/context-budget-pressure" &&
    value.cli_ref === "uaa runtime inspect-context-budget-pressure" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-context-budget-pressure-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    hasExactStringValue(
      value.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    typeof value.authority_state_status === "string" &&
    value.authority_state_status.length > 0 &&
    typeof value.authority_state_operator_message === "string" &&
    value.authority_state_operator_message.length > 0 &&
    isNonEmptyStringArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    isNonEmptyStringArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:context-budget-model-summarization:not-implemented",
    ) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    allowedPressureLevels.has(value.pressure_level) &&
    value.segment_count === value.segments.length &&
    value.proposal_count === value.proposals.length &&
    value.warning_count ===
      value.segments.filter((segment) => segment.pressure_level === "warning")
        .length &&
    value.critical_count ===
      value.segments.filter((segment) => segment.pressure_level === "critical")
        .length &&
    value.trimming_proposal_count ===
      value.proposals.filter(
        (proposal) => proposal.proposal_kind === "trim_context_refs",
      ).length &&
    value.summarization_proposal_count ===
      value.proposals.filter(
        (proposal) => proposal.proposal_kind === "summarize_with_approval",
      ).length &&
    value.ask_operator_proposal_count ===
      value.proposals.filter(
        (proposal) => proposal.proposal_kind === "request_operator_choice",
      ).length &&
    value.compression_proposal_required === true &&
    value.operator_approval_required === true &&
    value.source_coverage_required === true &&
    value.retrieval_log_required === true &&
    value.summary_receipt_required === true &&
    value.blocked_hidden_compression_label === "blocked" &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:context-budget-no-hidden-compression",
    ) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.segments.every(
      (segment) =>
        allowedPressureLevels.has(segment.pressure_level) &&
        segment.token_budget_remaining ===
          segment.token_budget_limit - segment.token_estimate &&
        isNonEmptyStringArray(segment.evidence_refs) &&
        isNonEmptyStringArray(segment.proof_refs) &&
        isNonEmptyStringArray(segment.blocked_authority_refs) &&
        segment.hidden_compression_enabled === false &&
        segment.automatic_context_mutation_enabled === false &&
        segment.model_summarization_call_performed === false &&
        segment.summary_receipt_created === false &&
        segment.raw_context_persisted === false &&
        segment.raw_prompt_persisted === false &&
        segment.raw_response_persisted === false &&
        segment.provider_payload_persisted === false &&
        segment.context_injection_performed === false &&
        segment.provider_sdk_call_performed === false &&
        segment.cache_write_performed === false &&
        segment.production_authority_enabled === false,
    ) &&
    value.proposals.every(
      (proposal) =>
        allowedProposalKinds.has(proposal.proposal_kind) &&
        proposal.approval_required === true &&
        proposal.source_coverage_required === true &&
        proposal.retrieval_log_required === true &&
        proposal.summary_receipt_required === true &&
        isNonEmptyStringArray(proposal.source_refs) &&
        isNonEmptyStringArray(proposal.retrieval_log_refs) &&
        isNonEmptyStringArray(proposal.proof_refs) &&
        isNonEmptyStringArray(proposal.blocked_authority_refs) &&
        proposal.auto_applied === false &&
        proposal.hidden_compression_performed === false &&
        proposal.automatic_context_mutation_performed === false &&
        proposal.model_summarization_call_performed === false &&
        proposal.summary_receipt_created === false &&
        proposal.raw_context_persisted === false &&
        proposal.raw_prompt_persisted === false &&
        proposal.raw_response_persisted === false &&
        proposal.provider_payload_persisted === false &&
        proposal.context_injection_performed === false &&
        proposal.provider_sdk_call_performed === false &&
        proposal.cache_write_performed === false &&
        proposal.production_authority_enabled === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeHardlineCommandBlocklist(
  value: RuntimeHardlineCommandBlocklistReadModel | undefined,
): value is RuntimeHardlineCommandBlocklistReadModel {
  if (value === undefined || !Array.isArray(value.classifications)) {
    return false;
  }
  const allowedStatuses = new Set(["allowed_shape", "hardline_denied"]);
  const allowedCategories = new Set([
    "allowed",
    "empty_argv",
    "shell_metachar",
    "shell_interpreter",
    "inline_code",
    "destructive_filesystem",
    "disk_writer",
    "network_transfer",
    "remote_access",
    "privilege_escalation",
    "permission_mutation",
    "git_mutation",
    "package_install",
    "production_orchestration",
    "container_runtime",
    "desktop_automation",
    "browser_automation",
  ]);
  return (
    value.schema_version === "runtime_hardline_command_blocklist.v1" &&
    value.status === "read_only_hardline_command_blocklist_floor" &&
    value.route_ref === "GET /api/runtime/hardline-command-blocklist" &&
    value.cli_ref === "uaa runtime inspect-hardline-command-blocklist" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-hardline-command-blocklist-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    hasExactStringValue(
      value.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    typeof value.authority_state_status === "string" &&
    value.authority_state_status.length > 0 &&
    typeof value.authority_state_operator_message === "string" &&
    value.authority_state_operator_message.length > 0 &&
    isNonEmptyStringArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    isNonEmptyStringArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:runtime-hardline-floor-override:not-implemented",
    ) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.non_overridable_floor === true &&
    value.override_bypass_permitted === false &&
    value.command_execution_performed === false &&
    value.raw_command_text_persisted === false &&
    value.raw_command_output_persisted === false &&
    value.classification_count === value.classifications.length &&
    value.denied_classification_count ===
      value.classifications.filter((classification) => classification.denied)
        .length &&
    value.allowed_classification_count ===
      value.classifications.filter((classification) => !classification.denied)
        .length &&
    isNonEmptyStringArray(value.hardline_rule_refs) &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:runtime-hardline-command-floor-override",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.classifications.every(
      (classification) =>
        allowedStatuses.has(classification.status) &&
        allowedCategories.has(classification.denial_category) &&
        classification.non_overridable === true &&
        classification.override_bypass_permitted === false &&
        classification.raw_command_text_persisted === false &&
        classification.raw_command_output_persisted === false &&
        classification.command_execution_performed === false &&
        (classification.denied
          ? classification.status === "hardline_denied" &&
            classification.denial_category !== "allowed"
          : classification.status === "allowed_shape" &&
            classification.denial_category === "allowed"),
    )
  );
}

function isSafeRuntimeManagedScopePolicy(
  value: RuntimeManagedScopePolicyReadModel | undefined,
): value is RuntimeManagedScopePolicyReadModel {
  if (
    value === undefined ||
    !Array.isArray(value.pinned_sources) ||
    !Array.isArray(value.drift_warnings)
  ) {
    return false;
  }
  const allowedSourceKinds = new Set([
    "repo_local_policy",
    "prompt_pack_policy",
    "operator_profile",
    "runtime_default",
  ]);
  const allowedDriftStatuses = new Set(["aligned", "warning", "blocked"]);
  const deniedTopLevelFlags: Array<keyof RuntimeManagedScopePolicyReadModel> = [
    "system_config_write_enabled",
    "privileged_write_enabled",
    "mdm_delivery_enabled",
    "managed_secrets_enabled",
    "unsigned_runtime_config_override_enabled",
    "production_enforcement_claimed",
    "control_center_mints_authority",
    "runtime_config_mutation_performed",
    "raw_config_persisted",
    "raw_local_path_persisted",
    "account_material_persisted",
    "credential_material_persisted",
  ];
  return (
    value.schema_version === "runtime_managed_scope_policy.v1" &&
    value.status === "read_only_local_policy_profile_posture" &&
    value.route_ref === "GET /api/runtime/managed-scope-policy" &&
    value.cli_ref === "uaa runtime inspect-managed-scope-policy" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-managed-scope-policy-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    TRUST_AUTHORITY_DECISION_OUTCOMES.includes(
      value.authority_state_decision_outcome,
    ) &&
    typeof value.authority_state_status === "string" &&
    value.authority_state_status.length > 0 &&
    typeof value.authority_state_operator_message === "string" &&
    value.authority_state_operator_message.length > 0 &&
    isNonEmptyStringArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    isNonEmptyStringArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:managed-scope-system-config-write:not-implemented",
    ) &&
    value.pinned_source_count === value.pinned_sources.length &&
    value.active_pinned_source_count ===
      value.pinned_sources.filter((source) => source.active).length &&
    value.drift_warning_count === value.drift_warnings.length &&
    value.blocked_drift_warning_count ===
      value.drift_warnings.filter((warning) => warning.status === "blocked")
        .length &&
    value.local_config_source_visible === true &&
    value.precedence_visible === true &&
    value.verification_visible === true &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:managed-scope-no-system-config-write",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.pinned_sources.every(
      (source) =>
        allowedSourceKinds.has(source.source_kind) &&
        allowedDriftStatuses.has(source.drift_status) &&
        source.pinned === true &&
        source.verified === true &&
        isNonEmptyStringArray(source.blocked_authority_refs) &&
        source.system_config_write_performed === false &&
        source.privileged_write_performed === false &&
        source.mdm_delivery_performed === false &&
        source.managed_protected_material_performed === false &&
        source.unsigned_runtime_config_override_performed === false &&
        source.production_enforcement_claimed === false,
    ) &&
    value.drift_warnings.every(
      (warning) =>
        allowedDriftStatuses.has(warning.status) &&
        warning.operator_review_required === true &&
        isNonEmptyStringArray(warning.blocked_authority_refs) &&
        isNonEmptyStringArray(warning.proof_refs) &&
        warning.auto_remediation_performed === false &&
        warning.runtime_config_write_performed === false &&
        warning.unsigned_override_accepted === false &&
        warning.production_enforcement_claimed === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeDoctorDiagnostics(
  value: RuntimeDoctorDiagnosticsReadModel | undefined,
): value is RuntimeDoctorDiagnosticsReadModel {
  if (value === undefined || !Array.isArray(value.diagnostics)) {
    return false;
  }
  const allowedDomains = new Set([
    "setup",
    "runtime_readiness",
    "providers",
    "tools",
    "protected_material",
    "local_services",
    "authority",
    "next_actions",
  ]);
  const allowedStatuses = new Set(["ok", "review", "blocked", "unavailable"]);
  const deniedTopLevelFlags: Array<keyof RuntimeDoctorDiagnosticsReadModel> = [
    "install_enabled",
    "service_start_enabled",
    "credential_write_enabled",
    "runtime_config_mutation_enabled",
    "control_center_mints_authority",
    "raw_log_persisted",
    "raw_local_path_persisted",
    "provider_payload_persisted",
  ];
  return (
    value.schema_version === "runtime_doctor_diagnostics.v1" &&
    value.status === "read_only_diagnostics_posture" &&
    value.route_ref === "GET /api/runtime/doctor-diagnostics" &&
    value.cli_ref === "uaa runtime inspect-doctor-diagnostics" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-doctor-diagnostics-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    TRUST_AUTHORITY_DECISION_OUTCOMES.includes(
      value.authority_state_decision_outcome,
    ) &&
    typeof value.authority_state_status === "string" &&
    value.authority_state_status.length > 0 &&
    typeof value.authority_state_operator_message === "string" &&
    value.authority_state_operator_message.length > 0 &&
    isNonEmptyStringArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    isNonEmptyStringArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:runtime-doctor-install:not-implemented",
    ) &&
    value.diagnostic_count === value.diagnostics.length &&
    value.ok_count ===
      value.diagnostics.filter((item) => item.status === "ok").length &&
    value.review_count ===
      value.diagnostics.filter((item) => item.status === "review").length &&
    value.blocked_count ===
      value.diagnostics.filter((item) => item.status === "blocked").length &&
    value.unavailable_count ===
      value.diagnostics.filter((item) => item.status === "unavailable").length &&
    value.setup_visible === true &&
    value.runtime_readiness_visible === true &&
    value.provider_posture_visible === true &&
    value.tool_posture_visible === true &&
    value.protected_material_posture_visible === true &&
    value.service_posture_visible === true &&
    value.authority_posture_visible === true &&
    value.next_safe_actions_visible === true &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:runtime-doctor-no-installs",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.diagnostics.every(
      (item) =>
        allowedDomains.has(item.domain) &&
        allowedStatuses.has(item.status) &&
        isNonEmptyStringArray(item.blocked_authority_refs) &&
        isNonEmptyStringArray(item.proof_refs) &&
        item.install_performed === false &&
        item.service_start_performed === false &&
        item.credential_write_performed === false &&
        item.runtime_config_mutation_performed === false &&
        item.raw_log_persisted === false &&
        item.raw_local_path_persisted === false &&
        item.provider_payload_persisted === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeSessionContinuity(
  value: RuntimeSessionContinuityReadModel | undefined,
): value is RuntimeSessionContinuityReadModel {
  if (value === undefined || !Array.isArray(value.surfaces)) {
    return false;
  }
  const allowedSources = new Set([
    "control_center_desktop",
    "cli",
    "delegated_runtime",
    "future_mobile",
    "coding_cockpit",
  ]);
  const allowedStates = new Set([
    "current",
    "stale",
    "conflict_review",
    "blocked",
  ]);
  const deniedTopLevelFlags: Array<keyof RuntimeSessionContinuityReadModel> = [
    "external_message_gateway_enabled",
    "account_sync_enabled",
    "connector_write_enabled",
    "remote_session_enabled",
    "raw_transcript_persisted",
    "raw_prompt_persisted",
    "raw_response_persisted",
    "raw_provider_payload_persisted",
    "control_center_mints_authority",
  ];
  return (
    value.schema_version === "runtime_session_continuity.v1" &&
    value.status === "read_only_multi_surface_session_continuity_posture" &&
    value.route_ref === "GET /api/runtime/session-continuity" &&
    value.cli_ref === "uaa runtime inspect-session-continuity" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-session-continuity-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    TRUST_AUTHORITY_DECISION_OUTCOMES.includes(
      value.authority_state_decision_outcome,
    ) &&
    typeof value.authority_state_status === "string" &&
    value.authority_state_status.length > 0 &&
    typeof value.authority_state_operator_message === "string" &&
    value.authority_state_operator_message.length > 0 &&
    isNonEmptyStringArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    isNonEmptyStringArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:session-continuity-remote-session:not-implemented",
    ) &&
    value.surface_count === value.surfaces.length &&
    value.current_count ===
      value.surfaces.filter((surface) => surface.continuity_state === "current")
        .length &&
    value.stale_count ===
      value.surfaces.filter((surface) => surface.continuity_state === "stale")
        .length &&
    value.conflict_count ===
      value.surfaces.filter(
        (surface) => surface.continuity_state === "conflict_review",
      ).length &&
    value.blocked_count ===
      value.surfaces.filter((surface) => surface.continuity_state === "blocked")
        .length &&
    value.source_labels_visible === true &&
    value.staleness_states_visible === true &&
    value.conflict_states_visible === true &&
    value.delivery_receipts_required_for_promotion === true &&
    value.revoke_required_for_promotion === true &&
    value.audit_required_for_promotion === true &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:session-continuity-no-remote-session",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.surfaces.every(
      (surface) =>
        allowedSources.has(surface.source) &&
        allowedStates.has(surface.continuity_state) &&
        isNonEmptyStringArray(surface.blocked_authority_refs) &&
        isNonEmptyStringArray(surface.proof_refs) &&
        surface.external_message_gateway_enabled === false &&
        surface.account_sync_enabled === false &&
        surface.connector_write_enabled === false &&
        surface.remote_session_enabled === false &&
        surface.raw_transcript_persisted === false &&
        surface.raw_prompt_persisted === false &&
        surface.raw_response_persisted === false &&
        surface.raw_provider_payload_persisted === false &&
        surface.control_center_mints_authority === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeMcpCatalogFiltering(
  value: RuntimeMcpCatalogFilteringReadModel | undefined,
): value is RuntimeMcpCatalogFilteringReadModel {
  if (value === undefined || !Array.isArray(value.servers)) {
    return false;
  }
  const allowedServerStates = new Set([
    "reviewed_metadata",
    "review_required",
    "activation_blocked",
  ]);
  const allowedToolStates = new Set([
    "metadata_visible",
    "filtered_blocked",
    "grant_required",
  ]);
  const deniedTopLevelFlags: Array<keyof RuntimeMcpCatalogFilteringReadModel> =
    [
      "install_enabled",
      "subprocess_runtime_enabled",
      "oauth_login_enabled",
      "tool_invocation_enabled",
      "connector_write_enabled",
      "raw_manifest_persisted",
      "control_center_mints_authority",
    ];
  const toolSlices = value.servers.flatMap((server) => server.tool_slices);
  return (
    value.schema_version === "runtime_mcp_catalog_filtering.v1" &&
    value.status === "metadata_catalog_filtering_posture" &&
    value.route_ref === "GET /api/runtime/mcp-catalog-filtering" &&
    value.cli_ref === "uaa runtime inspect-mcp-catalog-filtering" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-mcp-catalog-filtering-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    TRUST_AUTHORITY_DECISION_OUTCOMES.includes(
      value.authority_state_decision_outcome,
    ) &&
    typeof value.authority_state_status === "string" &&
    value.authority_state_status.length > 0 &&
    typeof value.authority_state_operator_message === "string" &&
    value.authority_state_operator_message.length > 0 &&
    isNonEmptyStringArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    isNonEmptyStringArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:mcp-catalog-tool-invocation:not-implemented",
    ) &&
    value.server_count === value.servers.length &&
    value.reviewed_metadata_count ===
      value.servers.filter(
        (server) => server.catalog_state === "reviewed_metadata",
      ).length &&
    value.review_required_count ===
      value.servers.filter((server) => server.catalog_state === "review_required")
        .length &&
    value.activation_blocked_count ===
      value.servers.filter(
        (server) => server.catalog_state === "activation_blocked",
      ).length &&
    value.tool_slice_count === toolSlices.length &&
    value.metadata_visible_tool_count ===
      toolSlices.filter((tool) => tool.filter_state === "metadata_visible").length &&
    value.filtered_blocked_tool_count ===
      toolSlices.filter((tool) => tool.filter_state === "filtered_blocked")
        .length &&
    value.grant_required_tool_count ===
      toolSlices.filter((tool) => tool.filter_state === "grant_required").length &&
    value.metadata_catalog_visible === true &&
    value.tool_filter_contracts_visible === true &&
    value.blocked_activation_states_visible === true &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:mcp-catalog-no-tool-invocation",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.servers.every(
      (server) =>
        allowedServerStates.has(server.catalog_state) &&
        server.tool_count === server.tool_slices.length &&
        server.metadata_visible_tool_count ===
          server.tool_slices.filter(
            (tool) => tool.filter_state === "metadata_visible",
          ).length &&
        server.filtered_blocked_tool_count ===
          server.tool_slices.filter(
            (tool) => tool.filter_state === "filtered_blocked",
          ).length &&
        server.grant_required_tool_count ===
          server.tool_slices.filter(
            (tool) => tool.filter_state === "grant_required",
          ).length &&
        isNonEmptyStringArray(server.blocked_authority_refs) &&
        isNonEmptyStringArray(server.proof_refs) &&
        server.install_enabled === false &&
        server.subprocess_runtime_enabled === false &&
        server.oauth_login_enabled === false &&
        server.tool_invocation_enabled === false &&
        server.connector_write_enabled === false &&
        server.raw_manifest_persisted === false &&
        server.tool_slices.every(
          (tool) =>
            allowedToolStates.has(tool.filter_state) &&
            tool.metadata_visible === true &&
            tool.invocation_enabled === false &&
            tool.connector_write_enabled === false &&
            tool.raw_schema_persisted === false &&
            tool.runtime_dispatch_enabled === false &&
            isNonEmptyStringArray(tool.blocked_authority_refs),
        ),
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeBackgroundJobs(
  value: RuntimeBackgroundJobsReadModel | undefined,
): value is RuntimeBackgroundJobsReadModel {
  if (value === undefined || !Array.isArray(value.jobs)) {
    return false;
  }
  const allowedKinds = new Set([
    "runtime_doctor_check",
    "proof_pack_export",
    "context_budget_review",
    "connector_delivery_followup",
  ]);
  const allowedStatuses = new Set([
    "proposal",
    "paused",
    "approval_required",
    "execution_blocked",
  ]);
  const allowedSchedulePolicies = new Set([
    "manual_review_only",
    "operator_window_required",
    "blocked_scheduler",
  ]);
  const deniedTopLevelFlags: Array<keyof RuntimeBackgroundJobsReadModel> = [
    "pause_enabled",
    "resume_enabled",
    "run_now_enabled",
    "scheduler_enabled",
    "background_worker_enabled",
    "autonomous_background_execution_enabled",
    "autonomous_retry_enabled",
    "external_delivery_enabled",
    "provider_call_enabled",
    "shell_execution_enabled",
    "connector_write_enabled",
    "control_center_mints_authority",
    "raw_job_payload_persisted",
  ];
  const reviewableCount = value.jobs.filter((job) =>
    ["proposal", "paused", "approval_required"].includes(job.status),
  ).length;
  return (
    value.schema_version === "runtime_background_jobs.v1" &&
    value.status === "durable_job_proposal_posture" &&
    value.route_ref === "GET /api/runtime/background-jobs" &&
    value.cli_ref === "uaa runtime inspect-background-jobs" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:background-autonomy-scoped" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    hasExactStringValue(
      value.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    typeof value.authority_state_status === "string" &&
    typeof value.authority_state_operator_message === "string" &&
    Array.isArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    Array.isArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:background-worker-runtime:not-implemented",
    ) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.job_count === value.jobs.length &&
    value.proposal_count ===
      value.jobs.filter((job) => job.status === "proposal").length &&
    value.paused_count ===
      value.jobs.filter((job) => job.status === "paused").length &&
    value.approval_required_count ===
      value.jobs.filter((job) => job.status === "approval_required").length &&
    value.execution_blocked_count ===
      value.jobs.filter((job) => job.status === "execution_blocked").length &&
    value.reviewable_job_count === reviewableCount &&
    value.durable_job_refs_visible === true &&
    value.schedule_policy_visible === true &&
    value.approval_scope_visible === true &&
    value.idempotency_visible === true &&
    value.safe_disable_visible === true &&
    value.receipt_plan_visible === true &&
    value.failure_handling_visible === true &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:background-jobs-no-background-worker",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.jobs.every(
      (job) =>
        allowedKinds.has(job.job_kind) &&
        allowedStatuses.has(job.status) &&
        allowedSchedulePolicies.has(job.schedule_policy) &&
        isNonEmptyStringArray(job.proof_refs) &&
        isNonEmptyStringArray(job.blocked_authority_refs) &&
        job.pause_enabled === false &&
        job.resume_enabled === false &&
        job.run_now_enabled === false &&
        job.scheduler_enabled === false &&
        job.background_worker_enabled === false &&
        job.autonomous_retry_enabled === false &&
        job.external_delivery_enabled === false &&
        job.provider_call_enabled === false &&
        job.shell_execution_enabled === false &&
        job.connector_write_enabled === false &&
        job.raw_job_payload_persisted === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeSubagentIsolation(
  value: RuntimeSubagentIsolationReadModel | undefined,
): value is RuntimeSubagentIsolationReadModel {
  if (
    value === undefined ||
    !Array.isArray(value.roles) ||
    !Array.isArray(value.review_artifacts)
  ) {
    return false;
  }
  const allowedRoleKinds = new Set(["implementer", "reviewer", "verifier"]);
  const allowedStatuses = new Set([
    "contract_ready",
    "review_ready",
    "blocked_dispatch",
  ]);
  const allowedArtifactKinds = new Set([
    "plan_comparison",
    "review_packet",
    "disagreement_summary",
  ]);
  const deniedTopLevelFlags: Array<keyof RuntimeSubagentIsolationReadModel> = [
    "live_dispatch_enabled",
    "background_fanout_enabled",
    "cross_agent_memory_transfer_enabled",
    "tool_sharing_enabled",
    "autonomous_delegation_enabled",
    "provider_call_enabled",
    "shell_execution_enabled",
    "connector_write_enabled",
    "control_center_mints_authority",
    "raw_transcript_persisted",
  ];
  return (
    value.schema_version === "runtime_subagent_isolation.v1" &&
    value.status === "identity_isolation_readiness" &&
    value.route_ref === "GET /api/runtime/subagent-isolation" &&
    value.cli_ref === "uaa runtime inspect-subagent-isolation" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-subagent-isolation-live-dispatch" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    hasExactStringValue(
      value.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    typeof value.authority_state_status === "string" &&
    typeof value.authority_state_operator_message === "string" &&
    Array.isArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    Array.isArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:subagent-live-dispatch:not-implemented",
    ) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.role_count === value.roles.length &&
    value.review_artifact_count === value.review_artifacts.length &&
    value.contract_ready_count ===
      value.roles.filter((role) => role.readiness_status === "contract_ready")
        .length &&
    value.review_ready_count ===
      value.roles.filter((role) => role.readiness_status === "review_ready")
        .length &&
    value.blocked_dispatch_count ===
      value.roles.filter((role) => role.readiness_status === "blocked_dispatch")
        .length &&
    value.identity_registry_visible === true &&
    value.scope_envelopes_visible === true &&
    value.context_pack_grants_visible === true &&
    value.tool_grants_visible === true &&
    value.memory_grants_visible === true &&
    value.budget_visible === true &&
    value.kill_switch_visible === true &&
    value.receipt_plan_visible === true &&
    value.proof_visible === true &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:subagent-isolation-no-live-dispatch",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.roles.every(
      (role) =>
        allowedRoleKinds.has(role.role_kind) &&
        allowedStatuses.has(role.readiness_status) &&
        isNonEmptyStringArray(role.blocked_authority_refs) &&
        isNonEmptyStringArray(role.next_safe_action_refs) &&
        role.live_dispatch_enabled === false &&
        role.background_fanout_enabled === false &&
        role.cross_agent_memory_transfer_enabled === false &&
        role.tool_sharing_enabled === false &&
        role.autonomous_delegation_enabled === false &&
        role.provider_call_enabled === false &&
        role.shell_execution_enabled === false &&
        role.connector_write_enabled === false &&
        role.raw_transcript_persisted === false,
    ) &&
    value.review_artifacts.every(
      (artifact) =>
        allowedArtifactKinds.has(artifact.artifact_kind) &&
        isNonEmptyStringArray(artifact.source_role_refs) &&
        isNonEmptyStringArray(artifact.proof_refs) &&
        artifact.raw_agent_output_persisted === false &&
        artifact.executable_authority === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeWorktreePerAgent(
  value: RuntimeWorktreePerAgentReadModel | undefined,
): value is RuntimeWorktreePerAgentReadModel {
  if (value === undefined || !Array.isArray(value.lanes)) {
    return false;
  }
  const allowedRoles = new Set(["implementer", "reviewer", "verifier"]);
  const allowedStatuses = new Set([
    "proposal",
    "review_ready",
    "mutation_blocked",
  ]);
  const allowedIsolationModes = new Set([
    "branch_proposal_only",
    "existing_worktree_ref_only",
    "blocked_worktree_mutation",
  ]);
  const deniedTopLevelFlags: Array<keyof RuntimeWorktreePerAgentReadModel> = [
    "git_worktree_create_enabled",
    "git_worktree_delete_enabled",
    "branch_mutation_enabled",
    "file_write_enabled",
    "commit_enabled",
    "push_enabled",
    "shell_execution_enabled",
    "provider_call_enabled",
    "control_center_mints_authority",
    "raw_path_persisted",
  ];
  return (
    value.schema_version === "runtime_worktree_per_agent.v1" &&
    value.status === "read_only_worktree_lane_posture" &&
    value.route_ref === "GET /api/runtime/worktree-per-agent" &&
    value.cli_ref === "uaa runtime inspect-worktree-per-agent" &&
    value.lane_count === value.lanes.length &&
    value.proposal_count ===
      value.lanes.filter((lane) => lane.lane_status === "proposal").length &&
    value.review_ready_count ===
      value.lanes.filter((lane) => lane.lane_status === "review_ready").length &&
    value.mutation_blocked_count ===
      value.lanes.filter((lane) => lane.lane_status === "mutation_blocked")
        .length &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_decision_count === value.lanes.length &&
    value.authority_state_allowed_count ===
      value.lanes.filter(
        (lane) => lane.authority_state_decision_outcome === "allow",
      ).length &&
    value.authority_state_degraded_count ===
      value.lanes.filter(
        (lane) =>
          lane.authority_state_decision_outcome === "degrade_to_draft",
      ).length &&
    value.authority_state_denied_count ===
      value.lanes.filter(
        (lane) => lane.authority_state_decision_outcome === "deny",
      ).length &&
    isNonEmptyStringArray(value.authority_state_mapping_refs) &&
    value.authority_state_mapping_refs.every(isSafeTrustAuthorityRef) &&
    isNonEmptyStringArray(value.authority_state_decision_refs) &&
    value.authority_state_decision_refs.every(isSafeTrustAuthorityRef) &&
    value.workspace_grants_visible === true &&
    value.branch_name_policy_visible === true &&
    value.checkpoint_plan_visible === true &&
    value.git_receipt_plan_visible === true &&
    value.rollback_plan_visible === true &&
    value.cli_parity_visible === true &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:worktree-per-agent-no-git-worktree-create",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.lanes.every(
      (lane) =>
        allowedRoles.has(lane.agent_role) &&
        allowedStatuses.has(lane.lane_status) &&
        allowedIsolationModes.has(lane.isolation_mode) &&
        isNonEmptyStringArray(lane.proof_refs) &&
        isNonEmptyStringArray(lane.blocked_authority_refs) &&
        isNonEmptyStringArray(lane.next_safe_action_refs) &&
        lane.authority_state_route_ref === "GET /api/runtime/authority-state" &&
        lane.authority_state_cli_ref ===
          "repo-local-command:uaa-runtime-inspect-authority-state" &&
        isSafeTrustAuthorityRef(lane.authority_state_mapping_ref) &&
        value.authority_state_mapping_refs.includes(
          lane.authority_state_mapping_ref,
        ) &&
        isSafeTrustAuthorityRef(lane.authority_state_catalog_ref) &&
        isSafeTrustAuthorityRef(lane.authority_state_decision_ref) &&
        value.authority_state_decision_refs.includes(
          lane.authority_state_decision_ref,
        ) &&
        hasExactStringValue(
          lane.authority_state_decision_outcome,
          TRUST_AUTHORITY_DECISION_OUTCOMES,
        ) &&
        typeof lane.authority_state_status === "string" &&
        typeof lane.authority_state_operator_message === "string" &&
        Array.isArray(lane.authority_state_reason_refs) &&
        lane.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
        Array.isArray(lane.unsupported_adapter_refs) &&
        lane.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
        lane.git_worktree_create_enabled === false &&
        lane.git_worktree_delete_enabled === false &&
        lane.branch_mutation_enabled === false &&
        lane.file_write_enabled === false &&
        lane.commit_enabled === false &&
        lane.push_enabled === false &&
        lane.shell_execution_enabled === false &&
        lane.provider_call_enabled === false &&
        lane.raw_path_persisted === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeStagedOrchestration(
  value: RuntimeStagedOrchestrationReadModel | undefined,
): value is RuntimeStagedOrchestrationReadModel {
  if (
    value === undefined ||
    !Array.isArray(value.plan?.stages) ||
    !Array.isArray(value.plan?.steps) ||
    !Array.isArray(value.plan?.checkpoints) ||
    !Array.isArray(value.plan?.degraded_handoffs) ||
    !Array.isArray(value.plan?.blocked_authority_refs)
  ) {
    return false;
  }
  const allowedStatuses = new Set([
    "pending",
    "running",
    "waiting",
    "degraded",
    "skipped",
    "blocked",
    "failed",
    "completed",
  ]);
  return (
    value.schema_version === "staged_orchestration_engine.v1" &&
    value.plan.schema_version === "staged_orchestration_engine.v1" &&
    value.validation.schema_version === "staged_orchestration_engine.v1" &&
    value.backend_owned === true &&
    value.api_ref === "GET /api/runtime/staged-orchestration" &&
    value.cli_ref ===
      "repo-local-command:uaa-runtime-inspect-staged-orchestration" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:staged-orchestration-read-model" &&
    value.runtime_command_authority_state_mapping_ref ===
      "lane-ref:staged-orchestration-approved-runtime-command" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    isSafeTrustAuthorityRef(value.runtime_command_authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.runtime_command_authority_state_decision_ref) &&
    hasExactStringValue(
      value.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    hasExactStringValue(
      value.runtime_command_authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    typeof value.authority_state_status === "string" &&
    typeof value.runtime_command_authority_state_status === "string" &&
    typeof value.authority_state_operator_message === "string" &&
    typeof value.runtime_command_authority_state_operator_message === "string" &&
    Array.isArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    Array.isArray(value.runtime_command_authority_state_reason_refs) &&
    value.runtime_command_authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    Array.isArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.progress.total_stage_count === value.plan.stages.length &&
    value.progress.total_step_count === value.plan.steps.length &&
    value.validation.plan_ref === value.plan.plan_ref &&
    ["accepted", "denied"].includes(value.validation.status) &&
    allowedStatuses.has(value.plan.status) &&
    value.plan.stages.every(
      (stage) =>
        allowedStatuses.has(stage.status) &&
        isSafeTrustAuthorityRef(stage.stage_ref) &&
        typeof stage.safe_summary === "string" &&
        Array.isArray(stage.step_refs) &&
        stage.step_refs.every(isSafeTrustAuthorityRef) &&
        Array.isArray(stage.checkpoint_refs) &&
        stage.checkpoint_refs.every(isSafeTrustAuthorityRef) &&
        Array.isArray(stage.evidence_refs) &&
        stage.evidence_refs.every(isSafeTrustAuthorityRef) &&
        Array.isArray(stage.degraded_handoff_refs) &&
        stage.degraded_handoff_refs.every(isSafeTrustAuthorityRef),
    ) &&
    value.plan.steps.every(
      (step) =>
        allowedStatuses.has(step.status) &&
        isSafeTrustAuthorityRef(step.step_ref) &&
        isSafeTrustAuthorityRef(step.stage_ref) &&
        typeof step.safe_summary === "string" &&
        Array.isArray(step.depends_on_step_refs) &&
        step.depends_on_step_refs.every(isSafeTrustAuthorityRef) &&
        (step.policy_ref === null || isSafeTrustAuthorityRef(step.policy_ref)) &&
        (step.approval_posture_ref === null ||
          isSafeTrustAuthorityRef(step.approval_posture_ref)) &&
        (step.checkpoint_ref === null ||
          isSafeTrustAuthorityRef(step.checkpoint_ref)) &&
        Array.isArray(step.evidence_refs) &&
        step.evidence_refs.every(isSafeTrustAuthorityRef) &&
        Array.isArray(step.receipt_refs) &&
        step.receipt_refs.every(isSafeTrustAuthorityRef) &&
        Array.isArray(step.blocked_authority_refs) &&
        step.blocked_authority_refs.every(isSafeTrustAuthorityRef) &&
        Array.isArray(step.reason_refs) &&
        step.reason_refs.every(isSafeTrustAuthorityRef) &&
        step.execution_performed === false &&
        step.raw_payload_persisted === false,
    ) &&
    value.plan.checkpoints.every(
      (checkpoint) =>
        isSafeTrustAuthorityRef(checkpoint.checkpoint_ref) &&
        isSafeTrustAuthorityRef(checkpoint.stage_ref) &&
        isSafeTrustAuthorityRef(checkpoint.step_ref) &&
        Array.isArray(checkpoint.evidence_refs) &&
        checkpoint.evidence_refs.every(isSafeTrustAuthorityRef) &&
        Array.isArray(checkpoint.receipt_refs) &&
        checkpoint.receipt_refs.every(isSafeTrustAuthorityRef) &&
        Array.isArray(checkpoint.rollback_refs) &&
        checkpoint.rollback_refs.every(isSafeTrustAuthorityRef) &&
        checkpoint.raw_payload_persisted === false &&
        checkpoint.execution_performed === false,
    ) &&
    value.plan.degraded_handoffs.every(
      (handoff) =>
        isSafeTrustAuthorityRef(handoff.handoff_ref) &&
        isSafeTrustAuthorityRef(handoff.source_step_ref) &&
        isSafeTrustAuthorityRef(handoff.target_stage_ref) &&
        isSafeTrustAuthorityRef(handoff.checkpoint_ref) &&
        Array.isArray(handoff.reason_refs) &&
        handoff.reason_refs.every(isSafeTrustAuthorityRef) &&
        Array.isArray(handoff.evidence_refs) &&
        handoff.evidence_refs.every(isSafeTrustAuthorityRef) &&
        Array.isArray(handoff.receipt_refs) &&
        handoff.receipt_refs.every(isSafeTrustAuthorityRef) &&
        handoff.execution_enabled === false,
    ) &&
    value.plan.blocked_authority_refs.includes(
      "blocked-state:staged-orchestration:no-autonomous-worker",
    ) &&
    value.plan.no_effect === true &&
    value.plan.approved_runtime_command_execution_enabled === false &&
    value.plan.background_autonomy_enabled === false &&
    value.plan.provider_model_call_enabled === false &&
    value.plan.unrestricted_command_execution_enabled === false &&
    value.validation.execution_performed === false &&
    value.safe_refs_only === true &&
    value.raw_payloads_persisted === false &&
    value.execution_performed === false &&
    value.approved_runtime_command_execution_enabled === false &&
    value.runtime_execution_performed_by_read_model === false &&
    value.control_center_can_mint_authority === false
  );
}

function isSafeRuntimeLspDiagnostics(
  value: RuntimeLspDiagnosticsReadModel | undefined,
): value is RuntimeLspDiagnosticsReadModel {
  if (value === undefined || !Array.isArray(value.diagnostics)) {
    return false;
  }
  const allowedLanguages = new Set(["python", "typescript", "docs"]);
  const allowedStatuses = new Set([
    "evidence_placeholder",
    "proof_ready",
    "execution_blocked",
  ]);
  const deniedTopLevelFlags: Array<keyof RuntimeLspDiagnosticsReadModel> = [
    "language_server_started",
    "dependency_install_enabled",
    "shell_execution_enabled",
    "file_read_enabled",
    "file_write_enabled",
    "provider_call_enabled",
    "control_center_mints_authority",
    "raw_path_persisted",
    "raw_diagnostic_payload_persisted",
  ];
  return (
    value.schema_version === "runtime_lsp_diagnostics.v1" &&
    value.status === "diagnostic_evidence_placeholder_posture" &&
    value.route_ref === "GET /api/runtime/lsp-diagnostics" &&
    value.cli_ref === "uaa runtime inspect-lsp-diagnostics" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-lsp-diagnostics-evidence" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    hasExactStringValue(
      value.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    typeof value.authority_state_status === "string" &&
    typeof value.authority_state_operator_message === "string" &&
    Array.isArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    Array.isArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:lsp-server-launch:not-implemented",
    ) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.diagnostic_count === value.diagnostics.length &&
    value.evidence_placeholder_count ===
      value.diagnostics.filter(
        (diagnostic) => diagnostic.status === "evidence_placeholder",
      ).length &&
    value.proof_ready_count ===
      value.diagnostics.filter((diagnostic) => diagnostic.status === "proof_ready")
        .length &&
    value.execution_blocked_count ===
      value.diagnostics.filter(
        (diagnostic) => diagnostic.status === "execution_blocked",
      ).length &&
    value.diagnostic_evidence_contract_visible === true &&
    value.receipt_plan_visible === true &&
    value.proof_link_visible === true &&
    value.redaction_policy_visible === true &&
    value.allowlisted_server_required_for_promotion === true &&
    value.cwd_jail_required_for_promotion === true &&
    value.timeout_required_for_promotion === true &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:lsp-diagnostics-no-language-server-launch",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.diagnostics.every(
      (diagnostic) =>
        allowedLanguages.has(diagnostic.language) &&
        allowedStatuses.has(diagnostic.status) &&
        isNonEmptyStringArray(diagnostic.blocked_authority_refs) &&
        isNonEmptyStringArray(diagnostic.next_safe_action_refs) &&
        diagnostic.language_server_started === false &&
        diagnostic.dependency_install_enabled === false &&
        diagnostic.shell_execution_enabled === false &&
        diagnostic.file_read_enabled === false &&
        diagnostic.file_write_enabled === false &&
        diagnostic.provider_call_enabled === false &&
        diagnostic.raw_path_persisted === false &&
        diagnostic.raw_diagnostic_payload_persisted === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimePreviewRail(
  value: RuntimePreviewRailReadModel | undefined,
): value is RuntimePreviewRailReadModel {
  if (value === undefined || !Array.isArray(value.slots)) {
    return false;
  }
  const allowedKinds = new Set([
    "file_ref",
    "diff_ref",
    "artifact_ref",
    "run_output_ref",
    "proof_ref",
    "runtime_event_ref",
  ]);
  const allowedStatuses = new Set([
    "safe_ref_ready",
    "bounded_preview_placeholder",
    "execution_blocked",
  ]);
  const deniedTopLevelFlags: Array<keyof RuntimePreviewRailReadModel> = [
    "browser_automation_enabled",
    "raw_sensitive_file_display_enabled",
    "direct_runtime_payload_rendering_enabled",
    "screenshot_capture_enabled",
    "file_read_enabled",
    "file_write_enabled",
    "shell_execution_enabled",
    "provider_call_enabled",
    "control_center_mints_authority",
    "raw_path_persisted",
    "raw_file_content_persisted",
    "raw_runtime_payload_persisted",
  ];
  return (
    value.schema_version === "runtime_preview_rail.v1" &&
    value.status === "safe_ref_preview_rail_posture" &&
    value.route_ref === "GET /api/runtime/preview-rail" &&
    value.cli_ref === "uaa runtime inspect-preview-rail" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-preview-rail-safe-ref-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    hasExactStringValue(
      value.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    typeof value.authority_state_status === "string" &&
    typeof value.authority_state_operator_message === "string" &&
    Array.isArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    Array.isArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.slot_count === value.slots.length &&
    value.safe_ref_ready_count ===
      value.slots.filter((slot) => slot.slot_status === "safe_ref_ready").length &&
    value.bounded_preview_placeholder_count ===
      value.slots.filter(
        (slot) => slot.slot_status === "bounded_preview_placeholder",
      ).length &&
    value.execution_blocked_count ===
      value.slots.filter((slot) => slot.slot_status === "execution_blocked")
        .length &&
    value.source_classification_visible === true &&
    value.redaction_policy_visible === true &&
    value.bounded_preview_visible === true &&
    value.operator_attach_visible === true &&
    value.receipt_plan_visible === true &&
    value.proof_link_visible === true &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:preview-rail-no-browser-automation",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.slots.every(
      (slot) =>
        allowedKinds.has(slot.slot_kind) &&
        allowedStatuses.has(slot.slot_status) &&
        isNonEmptyStringArray(slot.blocked_authority_refs) &&
        isNonEmptyStringArray(slot.next_safe_action_refs) &&
        slot.browser_automation_enabled === false &&
        slot.raw_sensitive_file_display_enabled === false &&
        slot.direct_runtime_payload_rendering_enabled === false &&
        slot.screenshot_capture_enabled === false &&
        slot.file_read_enabled === false &&
        slot.file_write_enabled === false &&
        slot.shell_execution_enabled === false &&
        slot.provider_call_enabled === false &&
        slot.raw_path_persisted === false &&
        slot.raw_file_content_persisted === false &&
        slot.raw_runtime_payload_persisted === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeSlashCommandRegistry(
  value: RuntimeSlashCommandRegistryReadModel | undefined,
): value is RuntimeSlashCommandRegistryReadModel {
  if (value === undefined || !Array.isArray(value.commands)) {
    return false;
  }
  const allowedStatuses = new Set([
    "metadata_ready",
    "disabled_requires_exact_lane",
    "blocked_high_authority",
  ]);
  const allowedAuthorityClasses = new Set([
    "read_only_metadata",
    "proposal_only",
    "approval_required_future_lane",
    "blocked_high_authority",
  ]);
  const allowedSideEffectClasses = new Set([
    "none",
    "proposal_only",
    "command_execution",
    "model_call",
    "local_mutation",
    "runtime_invocation",
  ]);
  const deniedTopLevelFlags: Array<keyof RuntimeSlashCommandRegistryReadModel> = [
    "chat_trigger_enabled",
    "runtime_invocation_enabled",
    "state_mutation_enabled",
    "shell_execution_enabled",
    "provider_call_enabled",
    "browser_automation_enabled",
    "connector_write_enabled",
    "control_center_mints_authority",
    "raw_prompt_persisted",
    "raw_response_persisted",
  ];
  return (
    value.schema_version === "runtime_slash_command_registry.v1" &&
    value.status === "metadata_registry_all_commands_disabled" &&
    value.route_ref === "GET /api/runtime/slash-command-registry" &&
    value.cli_ref === "uaa runtime inspect-slash-command-registry" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-slash-command-registry-metadata" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    hasExactStringValue(
      value.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    typeof value.authority_state_status === "string" &&
    typeof value.authority_state_operator_message === "string" &&
    Array.isArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    Array.isArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.command_count === value.commands.length &&
    value.metadata_ready_count ===
      value.commands.filter((command) => command.command_status === "metadata_ready")
        .length &&
    value.disabled_count ===
      value.commands.filter(
        (command) => command.command_status === "disabled_requires_exact_lane",
      ).length &&
    value.blocked_count ===
      value.commands.filter(
        (command) => command.command_status === "blocked_high_authority",
      ).length &&
    value.command_contract_visible === true &&
    value.side_effect_class_visible === true &&
    value.approval_policy_visible === true &&
    value.idempotency_policy_visible === true &&
    value.receipt_plan_visible === true &&
    value.cli_api_alignment_visible === true &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:slash-command-registry-no-chat-execution",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.commands.every(
      (command) =>
        allowedStatuses.has(command.command_status) &&
        allowedAuthorityClasses.has(command.authority_class) &&
        allowedSideEffectClasses.has(command.side_effect_class) &&
        isNonEmptyStringArray(command.blocked_authority_refs) &&
        isNonEmptyStringArray(command.promotion_path_refs) &&
        isNonEmptyStringArray(command.next_safe_action_refs) &&
        command.visible_in_control_center === true &&
        command.registered_metadata_only === true &&
        command.chat_trigger_enabled === false &&
        command.runtime_invocation_enabled === false &&
        command.state_mutation_enabled === false &&
        command.shell_execution_enabled === false &&
        command.provider_call_enabled === false &&
        command.browser_automation_enabled === false &&
        command.connector_write_enabled === false &&
        command.control_center_mints_authority === false &&
        command.raw_prompt_persisted === false &&
        command.raw_response_persisted === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeInterruptRedirect(
  value: RuntimeInterruptRedirectReadModel | undefined,
): value is RuntimeInterruptRedirectReadModel {
  if (value === undefined || !Array.isArray(value.proposals)) {
    return false;
  }
  const allowedStatuses = new Set([
    "read_only_proposal",
    "blocked_until_exact_lane",
    "approval_required_future_lane",
  ]);
  const allowedSideEffects = new Set([
    "none",
    "runtime_control_mutation",
    "operator_instruction_update",
    "recovery_state_transition",
  ]);
  const deniedTopLevelFlags: Array<keyof RuntimeInterruptRedirectReadModel> = [
    "live_stop_post_enabled",
    "process_kill_enabled",
    "runtime_mutation_enabled",
    "background_autonomy_enabled",
    "shell_execution_enabled",
    "provider_call_enabled",
    "browser_automation_enabled",
    "connector_write_enabled",
    "control_center_mints_authority",
    "raw_runtime_payload_persisted",
    "raw_log_persisted",
  ];
  return (
    value.schema_version === "runtime_interrupt_redirect.v1" &&
    value.status === "run_control_proposal_only" &&
    value.route_ref === "GET /api/runtime/interrupt-redirect" &&
    value.cli_ref === "uaa runtime inspect-interrupt-redirect" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-interrupt-redirect-proposals" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    hasExactStringValue(
      value.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    typeof value.authority_state_status === "string" &&
    typeof value.authority_state_operator_message === "string" &&
    Array.isArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    Array.isArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.proposal_count === value.proposals.length &&
    value.read_only_proposal_count ===
      value.proposals.filter(
        (proposal) => proposal.action_status === "read_only_proposal",
      ).length &&
    value.approval_required_future_lane_count ===
      value.proposals.filter(
        (proposal) =>
          proposal.action_status === "approval_required_future_lane",
      ).length &&
    value.blocked_count ===
      value.proposals.filter(
        (proposal) => proposal.action_status === "blocked_until_exact_lane",
      ).length &&
    value.run_ownership_visible === true &&
    value.stop_scope_visible === true &&
    value.idempotency_visible === true &&
    value.cancellation_receipt_visible === true &&
    value.recovery_state_visible === true &&
    value.proof_link_visible === true &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:interrupt-redirect-no-live-stop-post",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.proposals.every(
      (proposal) =>
        allowedStatuses.has(proposal.action_status) &&
        allowedSideEffects.has(proposal.side_effect_class) &&
        proposal.visible_in_control_center === true &&
        proposal.proposal_only === true &&
        isNonEmptyStringArray(proposal.blocked_authority_refs) &&
        isNonEmptyStringArray(proposal.promotion_path_refs) &&
        isNonEmptyStringArray(proposal.next_safe_action_refs) &&
        proposal.live_stop_post_enabled === false &&
        proposal.process_kill_enabled === false &&
        proposal.runtime_mutation_enabled === false &&
        proposal.background_autonomy_enabled === false &&
        proposal.shell_execution_enabled === false &&
        proposal.provider_call_enabled === false &&
        proposal.browser_automation_enabled === false &&
        proposal.connector_write_enabled === false &&
        proposal.control_center_mints_authority === false &&
        proposal.raw_runtime_payload_persisted === false &&
        proposal.raw_log_persisted === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeLoggingProfile(
  value: RuntimeLoggingProfileReadModel | undefined,
): value is RuntimeLoggingProfileReadModel {
  if (value === undefined || !Array.isArray(value.profiles)) {
    return false;
  }
  const allowedStatuses = new Set([
    "active_default",
    "disabled_until_flagged",
    "blocked_raw_detail",
  ]);
  const allowedRetention = new Set([
    "session_only",
    "bounded_local_receipt",
    "no_persistence",
  ]);
  const deniedTopLevelFlags: Array<keyof RuntimeLoggingProfileReadModel> = [
    "verbose_logging_enabled",
    "raw_logs_persisted",
    "raw_prompt_persisted",
    "raw_response_persisted",
    "provider_payload_persisted",
    "local_path_persisted",
    "credential_material_persisted",
    "remote_telemetry_export_enabled",
    "background_log_stream_enabled",
    "control_center_mints_authority",
  ];
  return (
    value.schema_version === "runtime_logging_profile.v1" &&
    value.status === "quiet_default_redacted_troubleshooting_available" &&
    value.route_ref === "GET /api/runtime/logging-profile" &&
    value.cli_ref === "uaa runtime inspect-logging-profile" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-logging-profile-posture" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    hasExactStringValue(
      value.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    typeof value.authority_state_status === "string" &&
    typeof value.authority_state_operator_message === "string" &&
    Array.isArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    Array.isArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.active_profile_ref === "logging-profile-ref:runtime:quiet-normal" &&
    value.profile_count === value.profiles.length &&
    value.quiet_default_count ===
      value.profiles.filter(
        (profile) => profile.profile_status === "active_default",
      ).length &&
    value.disabled_until_flagged_count ===
      value.profiles.filter(
        (profile) => profile.profile_status === "disabled_until_flagged",
      ).length &&
    value.blocked_raw_detail_count ===
      value.profiles.filter(
        (profile) => profile.profile_status === "blocked_raw_detail",
      ).length &&
    value.flag_scope_visible === true &&
    value.ttl_policy_visible === true &&
    value.redaction_rules_visible === true &&
    value.retention_policy_visible === true &&
    value.operator_proof_visible === true &&
    value.safe_disable_visible === true &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:logging-profile-no-raw-log-persistence",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.profiles.every(
      (profile) =>
        allowedStatuses.has(profile.profile_status) &&
        allowedRetention.has(profile.retention_class) &&
        profile.visible_in_control_center === true &&
        profile.operator_flag_required === true &&
        profile.safe_disable_available === true &&
        isNonEmptyStringArray(profile.blocked_authority_refs) &&
        isNonEmptyStringArray(profile.promotion_path_refs) &&
        isNonEmptyStringArray(profile.next_safe_action_refs) &&
        profile.raw_logs_persisted === false &&
        profile.raw_prompt_persisted === false &&
        profile.raw_response_persisted === false &&
        profile.provider_payload_persisted === false &&
        profile.local_path_persisted === false &&
        profile.credential_material_persisted === false &&
        profile.remote_telemetry_export_enabled === false &&
        profile.background_log_stream_enabled === false &&
        profile.control_center_mints_authority === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeResultClassification(
  value: RuntimeResultClassificationReadModel | undefined,
): value is RuntimeResultClassificationReadModel {
  if (value === undefined || !Array.isArray(value.classifications)) {
    return false;
  }
  const allowedKinds = new Set([
    "evidence",
    "mutation",
    "warning",
    "blocked",
    "proposal",
    "diagnostic",
    "untrusted_data",
  ]);
  const allowedVerification = new Set([
    "verified_safe_ref",
    "receipt_required",
    "review_required",
    "blocked_authority",
    "untrusted_until_verified",
  ]);
  const deniedTopLevelFlags: Array<keyof RuntimeResultClassificationReadModel> = [
    "tool_output_as_truth_enabled",
    "action_authority_enabled",
    "mutation_without_receipt_enabled",
    "unverified_evidence_promotion_enabled",
    "raw_output_persisted",
    "provider_payload_persisted",
    "control_center_mints_authority",
  ];
  return (
    value.schema_version === "runtime_result_classification.v1" &&
    value.status === "taxonomy_read_model_only" &&
    value.route_ref === "GET /api/runtime/result-classification" &&
    value.cli_ref === "uaa runtime inspect-result-classification" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-result-classification-taxonomy" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    hasExactStringValue(
      value.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    typeof value.authority_state_status === "string" &&
    typeof value.authority_state_operator_message === "string" &&
    Array.isArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    Array.isArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.classification_count === value.classifications.length &&
    value.evidence_count ===
      value.classifications.filter((item) => item.result_kind === "evidence")
        .length &&
    value.mutation_count ===
      value.classifications.filter((item) => item.result_kind === "mutation")
        .length &&
    value.warning_count ===
      value.classifications.filter((item) => item.result_kind === "warning")
        .length &&
    value.blocked_count ===
      value.classifications.filter((item) => item.result_kind === "blocked")
        .length &&
    value.proposal_count ===
      value.classifications.filter((item) => item.result_kind === "proposal")
        .length &&
    value.diagnostic_count ===
      value.classifications.filter((item) => item.result_kind === "diagnostic")
        .length &&
    value.untrusted_data_count ===
      value.classifications.filter((item) => item.result_kind === "untrusted_data")
        .length &&
    value.labels_visible === true &&
    value.provenance_visible === true &&
    value.redaction_visible === true &&
    value.verification_status_visible === true &&
    value.proof_binding_visible === true &&
    value.receipt_requirement_visible === true &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:result-classification-no-tool-output-as-truth",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.classifications.every(
      (item) =>
        allowedKinds.has(item.result_kind) &&
        allowedVerification.has(item.verification_status) &&
        item.visible_in_control_center === true &&
        item.result_label_required === true &&
        item.provenance_required === true &&
        item.redaction_required === true &&
        item.proof_binding_required === true &&
        isNonEmptyStringArray(item.blocked_authority_refs) &&
        isNonEmptyStringArray(item.promotion_path_refs) &&
        isNonEmptyStringArray(item.next_safe_action_refs) &&
        item.tool_output_as_truth_enabled === false &&
        item.action_authority_enabled === false &&
        item.mutation_without_receipt_enabled === false &&
        item.unverified_evidence_promotion_enabled === false &&
        item.raw_output_persisted === false &&
        item.provider_payload_persisted === false &&
        item.control_center_mints_authority === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeVoiceMediaPosture(
  value: RuntimeVoiceMediaPostureReadModel | undefined,
): value is RuntimeVoiceMediaPostureReadModel {
  if (value === undefined || !Array.isArray(value.lanes)) {
    return false;
  }
  const allowedLaneKinds = new Set([
    "voice_input",
    "speech_to_text",
    "text_to_speech",
    "image_input",
    "image_generation",
    "media_upload",
    "media_delivery",
  ]);
  const deniedTopLevelFlags: Array<keyof RuntimeVoiceMediaPostureReadModel> = [
    "microphone_access_enabled",
    "camera_access_enabled",
    "file_upload_enabled",
    "transcription_enabled",
    "media_generation_enabled",
    "provider_calls_enabled",
    "external_delivery_enabled",
    "raw_media_persisted",
    "control_center_mints_authority",
  ];
  return (
    value.schema_version === "runtime_voice_media_posture.v1" &&
    value.status === "read_model_posture_only" &&
    value.route_ref === "GET /api/runtime/voice-media-posture" &&
    value.cli_ref === "uaa runtime inspect-voice-media-posture" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-voice-media-posture-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    hasExactStringValue(
      value.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    typeof value.authority_state_status === "string" &&
    typeof value.authority_state_operator_message === "string" &&
    Array.isArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    Array.isArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.lane_count === value.lanes.length &&
    value.blocked_lane_count ===
      value.lanes.filter((lane) => lane.status === "blocked_until_authority")
        .length &&
    value.local_only_option_required === true &&
    value.provider_boundary_required === true &&
    value.consent_required === true &&
    value.receipt_required === true &&
    value.safe_disable_required === true &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:voice-media-no-microphone-access",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.lanes.every(
      (lane) =>
        allowedLaneKinds.has(lane.lane_kind) &&
        lane.status === "blocked_until_authority" &&
        isNonEmptyStringArray(lane.blocked_authority_refs) &&
        isNonEmptyStringArray(lane.promotion_path_refs) &&
        isNonEmptyStringArray(lane.next_safe_action_refs) &&
        lane.local_only_option_required === true &&
        lane.provider_boundary_required === true &&
        lane.consent_required === true &&
        lane.receipt_required === true &&
        lane.safe_disable_required === true &&
        lane.microphone_access_enabled === false &&
        lane.camera_access_enabled === false &&
        lane.file_upload_enabled === false &&
        lane.transcription_enabled === false &&
        lane.media_generation_enabled === false &&
        lane.provider_calls_enabled === false &&
        lane.external_delivery_enabled === false &&
        lane.raw_media_persisted === false &&
        lane.control_center_mints_authority === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeMessagingGatewayPosture(
  value: RuntimeMessagingGatewayPostureReadModel | undefined,
): value is RuntimeMessagingGatewayPostureReadModel {
  if (value === undefined || !Array.isArray(value.platforms)) {
    return false;
  }
  const allowedPlatformKinds = new Set([
    "email",
    "slack",
    "telegram",
    "sms",
    "discord",
    "generic_webhook",
  ]);
  const deniedTopLevelFlags: Array<
    keyof RuntimeMessagingGatewayPostureReadModel
  > = [
    "connector_runtime_enabled",
    "connector_read_enabled",
    "send_enabled",
    "oauth_enabled",
    "webhook_exposure_enabled",
    "account_sync_enabled",
    "external_write_enabled",
    "raw_message_persisted",
    "control_center_mints_authority",
  ];
  return (
    value.schema_version === "runtime_messaging_gateway_posture.v1" &&
    value.status === "metadata_readiness_map_only" &&
    value.route_ref === "GET /api/runtime/messaging-gateway-posture" &&
    value.cli_ref === "uaa runtime inspect-messaging-gateway-posture" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-messaging-gateway-posture-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    hasExactStringValue(
      value.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    typeof value.authority_state_status === "string" &&
    typeof value.authority_state_operator_message === "string" &&
    Array.isArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    Array.isArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.platform_count === 6 &&
    value.platform_count === value.platforms.length &&
    value.blocked_platform_count === value.platforms.length &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:messaging-gateway-no-connector-runtime",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.platforms.every(
      (platform) =>
        allowedPlatformKinds.has(platform.platform_kind) &&
        platform.status === "blocked_until_authority" &&
        isNonEmptyStringArray(platform.blocked_authority_refs) &&
        isNonEmptyStringArray(platform.promotion_path_refs) &&
        isNonEmptyStringArray(platform.next_safe_action_refs) &&
        platform.connector_runtime_enabled === false &&
        platform.connector_read_enabled === false &&
        platform.send_enabled === false &&
        platform.oauth_enabled === false &&
        platform.webhook_exposure_enabled === false &&
        platform.account_sync_enabled === false &&
        platform.external_write_enabled === false &&
        platform.raw_message_persisted === false &&
        platform.control_center_mints_authority === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeRemoteExecutionPosture(
  value: RuntimeRemoteExecutionPostureReadModel | undefined,
): value is RuntimeRemoteExecutionPostureReadModel {
  if (value === undefined || !Array.isArray(value.backends)) {
    return false;
  }
  const allowedBackendKinds = new Set([
    "local_workspace",
    "local_container",
    "secure_host",
    "cloud_sandbox",
    "serverless_worker",
    "remote_gpu",
  ]);
  const deniedTopLevelFlags: Array<
    keyof RuntimeRemoteExecutionPostureReadModel
  > = [
    "remote_execution_enabled",
    "ssh_enabled",
    "cloud_sandbox_enabled",
    "remote_shell_enabled",
    "file_sync_enabled",
    "remote_secret_access_enabled",
    "remote_process_control_enabled",
    "credential_material_persisted",
    "control_center_mints_authority",
  ];
  return (
    value.schema_version === "runtime_remote_execution_posture.v1" &&
    value.status === "capability_map_only" &&
    value.route_ref === "GET /api/runtime/remote-execution-posture" &&
    value.cli_ref === "uaa runtime inspect-remote-execution-posture" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-remote-execution-posture-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    hasExactStringValue(
      value.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    typeof value.authority_state_status === "string" &&
    typeof value.authority_state_operator_message === "string" &&
    Array.isArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    Array.isArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.backend_count === 6 &&
    value.backend_count === value.backends.length &&
    value.blocked_backend_count === value.backends.length &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:remote-execution-no-secure-host",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.backends.every(
      (backend) =>
        allowedBackendKinds.has(backend.backend_kind) &&
        backend.status === "blocked_until_authority" &&
        isNonEmptyStringArray(backend.blocked_authority_refs) &&
        isNonEmptyStringArray(backend.promotion_path_refs) &&
        isNonEmptyStringArray(backend.next_safe_action_refs) &&
        backend.remote_execution_enabled === false &&
        backend.ssh_enabled === false &&
        backend.cloud_sandbox_enabled === false &&
        backend.remote_shell_enabled === false &&
        backend.file_sync_enabled === false &&
        backend.remote_secret_access_enabled === false &&
        backend.remote_process_control_enabled === false &&
        backend.credential_material_persisted === false &&
        backend.control_center_mints_authority === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimePluginMetadataPosture(
  value: RuntimePluginMetadataPostureReadModel | undefined,
): value is RuntimePluginMetadataPostureReadModel {
  if (value === undefined || !Array.isArray(value.surfaces)) {
    return false;
  }
  const allowedSurfaceKinds = new Set([
    "adapter",
    "hook",
    "tool",
    "memory_provider",
    "context_engine",
    "ui_extension",
    "skill_bundle",
  ]);
  const deniedTopLevelFlags: Array<
    keyof RuntimePluginMetadataPostureReadModel
  > = [
    "runtime_import_enabled",
    "hook_execution_enabled",
    "package_install_enabled",
    "marketplace_content_execution_enabled",
    "plugin_code_execution_enabled",
    "connector_write_enabled",
    "provider_call_enabled",
    "shell_execution_enabled",
    "raw_manifest_persisted",
    "control_center_mints_authority",
  ];
  return (
    value.schema_version === "runtime_plugin_metadata_posture.v1" &&
    value.status === "metadata_contract_only" &&
    value.route_ref === "GET /api/runtime/plugin-metadata-posture" &&
    value.cli_ref === "uaa runtime inspect-plugin-metadata-posture" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-plugin-metadata-posture-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    hasExactStringValue(
      value.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    typeof value.authority_state_status === "string" &&
    typeof value.authority_state_operator_message === "string" &&
    Array.isArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    Array.isArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.surface_count === 7 &&
    value.surface_count === value.surfaces.length &&
    value.blocked_surface_count === value.surfaces.length &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-authority:plugin-metadata-no-runtime-import",
    ) &&
    isNonEmptyStringArray(value.promotion_path_refs) &&
    isNonEmptyStringArray(value.proof_refs) &&
    isNonEmptyStringArray(value.verifier_refs) &&
    isNonEmptyStringArray(value.next_safe_action_refs) &&
    value.surfaces.every(
      (surface) =>
        allowedSurfaceKinds.has(surface.surface_kind) &&
        surface.status === "blocked_until_grant" &&
        isNonEmptyStringArray(surface.blocked_authority_refs) &&
        isNonEmptyStringArray(surface.promotion_path_refs) &&
        isNonEmptyStringArray(surface.next_safe_action_refs) &&
        surface.runtime_import_enabled === false &&
        surface.hook_execution_enabled === false &&
        surface.package_install_enabled === false &&
        surface.marketplace_content_execution_enabled === false &&
        surface.plugin_code_execution_enabled === false &&
        surface.connector_write_enabled === false &&
        surface.provider_call_enabled === false &&
        surface.shell_execution_enabled === false &&
        surface.raw_manifest_persisted === false &&
        surface.control_center_mints_authority === false,
    ) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeSkillMarketplacePosture(
  value: unknown,
): value is RuntimeSkillMarketplacePostureReadModel {
  if (!isPlainRecord(value)) {
    return false;
  }
  const candidate = value as Partial<RuntimeSkillMarketplacePostureReadModel>;
  if (
    !Array.isArray(candidate.stages) ||
    !isSafeRuntimeSkillMarketplaceCatalog(candidate.catalog)
  ) {
    return false;
  }
  const allowedStageKinds = new Set([
    "external_discovery_signal",
    "quarantine",
    "review",
    "adaptation_proposal",
    "uaa_owned_adaptation",
    "activation_grant",
    "execution_block",
  ]);
  const allowedStageStatuses = new Set([
    "signal_only",
    "review_required",
    "blocked_until_owned_adaptation",
  ]);
  const deniedTopLevelFlags: Array<
    keyof RuntimeSkillMarketplacePostureReadModel
  > = [
    "external_popularity_is_trust",
    "external_code_execution_enabled",
    "direct_marketplace_install_enabled",
    "runtime_import_enabled",
    "automatic_skill_write_enabled",
    "provider_call_enabled",
    "browser_automation_enabled",
    "connector_write_enabled",
    "raw_marketplace_payload_persisted",
    "control_center_mints_authority",
  ];
  return (
    candidate.schema_version === "runtime_skill_marketplace_posture.v1" &&
    candidate.status === "signal_review_adaptation_only" &&
    candidate.route_ref === "GET /api/runtime/skill-marketplace-posture" &&
    candidate.cli_ref === "uaa runtime inspect-skill-marketplace-posture" &&
    candidate.doc_ref ===
      "docs/runtime/UAA_HERMES_RUNTIME_SKILL_MARKETPLACE_POSTURE.md" &&
    candidate.authority_state_route_ref ===
      "GET /api/runtime/authority-state" &&
    candidate.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    candidate.authority_state_mapping_ref ===
      "lane-ref:runtime-skill-marketplace-posture-read-model" &&
    isSafeSkillMarketplaceRef(candidate.contract_ref) &&
    isSafeSkillMarketplaceRef(candidate.snapshot_ref) &&
    isSafeSkillMarketplaceSnapshotHash(candidate.snapshot_hash_ref) &&
    candidate.snapshot_hash_algorithm_ref ===
      "hash-algorithm-ref:uaa-portable-canonical-json-v1:sha256" &&
    isSafeSkillMarketplaceRef(candidate.authority_state_catalog_ref) &&
    isSafeSkillMarketplaceRef(candidate.authority_state_decision_ref) &&
    isSafeSkillMarketplaceRef(candidate.control_center_ref) &&
    hasExactStringValue(
      candidate.authority_state_decision_outcome,
      TRUST_AUTHORITY_DECISION_OUTCOMES,
    ) &&
    isSafeSkillMarketplaceText(candidate.authority_state_status, 160) &&
    isSafeSkillMarketplaceText(
      candidate.authority_state_operator_message,
      320,
    ) &&
    isSafeSkillMarketplaceText(candidate.safe_summary, 640) &&
    isSafeSkillMarketplaceRefArray(candidate.authority_state_reason_refs) &&
    isSafeSkillMarketplaceRefArray(candidate.unsupported_adapter_refs) &&
    candidate.stage_count === 7 &&
    candidate.stage_count === candidate.stages.length &&
    candidate.blocked_execution_count === 1 &&
    isSafeRuntimeSkillMarketplaceFreshness(
      candidate.catalog_freshness,
      candidate.catalog,
      candidate.authority_state_decision_outcome,
    ) &&
    isSkillMarketplaceCatalogVisibilityConsistent(
      candidate.catalog_freshness,
      candidate.catalog,
    ) &&
    candidate.review_required_count ===
      candidate.stages.filter((stage) => stage.status === "review_required")
        .length &&
    isSafeSkillMarketplaceRefArray(candidate.blocked_authority_refs) &&
    candidate.blocked_authority_refs.includes(
      "blocked-authority:skill-marketplace-no-external-code-execution",
    ) &&
    isSafeSkillMarketplaceRefArray(candidate.promotion_path_refs) &&
    isSafeSkillMarketplaceRefArray(candidate.proof_refs) &&
    isSafeSkillMarketplaceRefArray(candidate.verifier_refs) &&
    isSafeSkillMarketplaceRefArray(candidate.next_safe_action_refs) &&
    isSafeSkillMarketplaceRedactionArray(candidate.redactions_applied) &&
    candidate.stages.every(
      (stage) =>
        isPlainRecord(stage) &&
        allowedStageKinds.has(stage.stage_kind as string) &&
        allowedStageStatuses.has(stage.status as string) &&
        isSafeSkillMarketplaceRef(stage.stage_ref) &&
        isSafeSkillMarketplaceText(stage.display_label, 120) &&
        isSafeSkillMarketplaceText(stage.safe_summary, 420) &&
        [
          "signal_policy_ref",
          "quarantine_ref",
          "review_ref",
          "adaptation_ref",
          "activation_grant_ref",
          "safe_disable_ref",
          "receipt_plan_ref",
          "proof_ref",
        ].every((field) => isSafeSkillMarketplaceRef(stage[field])) &&
        isSafeSkillMarketplaceRefArray(stage.blocked_authority_refs) &&
        isSafeSkillMarketplaceRefArray(stage.promotion_path_refs) &&
        isSafeSkillMarketplaceRefArray(stage.next_safe_action_refs) &&
        stage.external_popularity_is_trust === false &&
        stage.external_code_execution_enabled === false &&
        stage.direct_marketplace_install_enabled === false &&
        stage.runtime_import_enabled === false &&
        stage.automatic_skill_write_enabled === false &&
        stage.provider_call_enabled === false &&
        stage.browser_automation_enabled === false &&
        stage.connector_write_enabled === false &&
        stage.raw_marketplace_payload_persisted === false &&
        stage.control_center_mints_authority === false,
    ) &&
    deniedTopLevelFlags.every((flag) => candidate[flag] === false)
  );
}

function isSkillMarketplaceCatalogVisibilityConsistent(
  freshness: unknown,
  catalog: NonNullable<RuntimeSkillMarketplacePostureReadModel["catalog"]>,
): boolean {
  if (!isPlainRecord(freshness)) {
    return false;
  }
  return (
    freshness.catalog_displayable === true ||
    (catalog.entry_count === 0 &&
      catalog.entries.length === 0 &&
      catalog.sources.every((source) => source.record_count === 0))
  );
}

function isSafeRuntimeSkillMarketplaceCatalog(
  value: unknown,
): value is NonNullable<RuntimeSkillMarketplacePostureReadModel["catalog"]> {
  if (
    !isPlainRecord(value) ||
    !Array.isArray(value.sources) ||
    !Array.isArray(value.entries)
  ) {
    return false;
  }
  const snapshotTime = Date.parse(String(value.captured_at));
  if (
    value.schema_version !==
      "runtime_skill_marketplace_catalog_snapshot.v1" ||
    !isSafeSkillMarketplaceRef(value.snapshot_ref) ||
    !Number.isFinite(snapshotTime) ||
    !isBoundedInteger(value.entry_count, 0, 100) ||
    value.entry_count !== value.entries.length ||
    value.default_page_size !== 25 ||
    value.pagination_supported !== true ||
    value.metadata_only !== true ||
    value.live_marketplace_fetch_performed !== false ||
    value.raw_marketplace_payload_persisted !== false ||
    value.sources.length !== 2 ||
    !value.sources.every((source) =>
      isSafeRuntimeSkillMarketplaceSource(source, snapshotTime),
    )
  ) {
    return false;
  }
  const sources = value.sources as RuntimeSkillMarketplaceSourceSnapshot[];
  const sourceRefs = new Set(sources.map((source) => source.source_ref));
  const sourceKinds = new Set(sources.map((source) => source.source_kind));
  const sourceKindByRef = new Map(
    sources.map((source) => [source.source_ref, source.source_kind]),
  );
  if (
    sourceRefs.size !== sources.length ||
    sourceKinds.size !== 2 ||
    !sourceKinds.has("clawhub") ||
    !sourceKinds.has("hermes") ||
    !value.entries.every((entry) =>
      isSafeRuntimeSkillMarketplaceEntry(
        entry,
        snapshotTime,
        sourceKindByRef,
      ),
    )
  ) {
    return false;
  }
  const entries = value.entries as RuntimeSkillMarketplaceCatalogEntry[];
  const skillRefs = new Set(entries.map((entry) => entry.skill_ref));
  const sourceRecordRefs = new Set(
    entries.map((entry) => entry.source_record_ref),
  );
  const sourceSlugs = new Set(
    entries.map((entry) => `${entry.source_ref}:${entry.slug}`),
  );
  return (
    value.entry_count === skillRefs.size &&
    value.entry_count === sourceRecordRefs.size &&
    value.entry_count === sourceSlugs.size &&
    sources.every(
      (source) =>
        source.record_count ===
          entries.filter(
            (entry) => entry.source_ref === source.source_ref,
          ).length,
    )
  );
}

function isSafeRuntimeSkillMarketplaceSource(
  value: unknown,
  snapshotTime: number,
): value is RuntimeSkillMarketplaceSourceSnapshot {
  if (!isPlainRecord(value)) {
    return false;
  }
  const capturedAt = Date.parse(String(value.captured_at));
  return (
    (value.source_kind === "clawhub" || value.source_kind === "hermes") &&
    isSafeSkillMarketplaceRef(value.source_ref) &&
    isSafeSkillMarketplaceRef(value.source_version_ref) &&
    isSafeSkillMarketplaceText(value.display_label, 120) &&
    Number.isFinite(capturedAt) &&
    capturedAt <= snapshotTime &&
    isBoundedInteger(value.record_count, 0, 100) &&
    (value.source_kind !== "clawhub" ||
      (value.rank_signal === "weekly_trending" &&
        value.score_signal === "stars")) &&
    (value.source_kind !== "hermes" ||
      (value.rank_signal === "not_provided" &&
        value.score_signal === "not_provided")) &&
    value.live_fetch_performed === false &&
    value.raw_payload_persisted === false
  );
}

function isSafeRuntimeSkillMarketplaceEntry(
  value: unknown,
  snapshotTime: number,
  sourceKindByRef: Map<string, "clawhub" | "hermes">,
): value is RuntimeSkillMarketplaceCatalogEntry {
  if (!isPlainRecord(value)) {
    return false;
  }
  const updatedAt = Date.parse(String(value.source_updated_at));
  const sourceKind = sourceKindByRef.get(String(value.source_ref));
  const optionalCounts = [
    value.star_count,
    value.download_count,
    value.install_count,
    value.comment_count,
    value.rating_count,
  ];
  return (
    sourceKind !== undefined &&
    value.source_kind === sourceKind &&
    isSafeSkillMarketplaceRef(value.skill_ref) &&
    isSafeSkillMarketplaceRef(value.source_ref) &&
    isSafeSkillMarketplaceRef(value.source_record_ref) &&
    isSafeSkillMarketplaceText(value.source_label, 120) &&
    isSafeSkillMarketplaceText(value.slug, 100) &&
    isSafeSkillMarketplaceText(value.display_name, 120) &&
    isSafeSkillMarketplaceText(value.safe_summary, 320) &&
    isSafeSkillMarketplaceText(value.category, 80) &&
    isSafeSkillMarketplaceText(value.version, 40) &&
    isSafeSkillMarketplaceText(value.license_label, 120) &&
    isSafeSkillMarketplaceText(value.rank_label, 120) &&
    Number.isFinite(updatedAt) &&
    updatedAt <= snapshotTime &&
    isNullableBoundedInteger(value.source_rank, 1, 100_000) &&
    optionalCounts.every((count) =>
      isNullableBoundedInteger(count, 0, 1_000_000_000),
    ) &&
    (value.average_rating === null ||
      (typeof value.average_rating === "number" &&
        Number.isFinite(value.average_rating) &&
        value.average_rating >= 0 &&
        value.average_rating <= 5)) &&
    (value.average_rating === null) === (value.rating_count === null) &&
    value.source_metadata_only === true &&
    value.review_required === true &&
    value.risk_level === "unknown" &&
    value.external_code_imported === false &&
    value.execution_enabled === false &&
    (sourceKind !== "hermes" ||
      (value.source_rank === null &&
        optionalCounts.every((count) => count === null) &&
        value.average_rating === null)) &&
    (sourceKind !== "clawhub" ||
      (value.average_rating === null && value.rating_count === null))
  );
}

function isSafeRuntimeSkillMarketplaceFreshness(
  value: unknown,
  catalog: NonNullable<RuntimeSkillMarketplacePostureReadModel["catalog"]>,
  authorityOutcome: unknown,
): value is RuntimeSkillMarketplaceCatalogFreshness {
  if (!isPlainRecord(value)) {
    return false;
  }
  const checkedAt = Date.parse(String(value.checked_at));
  const capturedAt = Date.parse(catalog.captured_at);
  const expiresAt = Date.parse(String(value.expires_at));
  const expectedExpiresAt = capturedAt + 7 * 86_400_000;
  const expectedStatus =
    checkedAt < capturedAt
      ? "unknown"
      : checkedAt >= expiresAt
        ? "stale"
        : "current";
  const expectedDisplayStatus =
    authorityOutcome !== "allow"
      ? "unavailable_authority"
      : expectedStatus === "current"
        ? "available"
        : expectedStatus === "stale"
          ? "available_stale"
          : "unavailable_unknown";
  return (
    value.catalog_snapshot_ref === catalog.snapshot_ref &&
    isSafeSkillMarketplaceRef(value.catalog_snapshot_ref) &&
    value.freshness_policy_ref ===
      "freshness-policy-ref:skill-marketplace-catalog:seven-days" &&
    Number.isFinite(checkedAt) &&
    Number.isFinite(expiresAt) &&
    expiresAt === expectedExpiresAt &&
    value.status === expectedStatus &&
    value.display_status === expectedDisplayStatus &&
    isSafeSkillMarketplaceRefArray(value.reason_refs) &&
    value.stale === (expectedStatus === "stale") &&
    value.catalog_displayable ===
      (expectedDisplayStatus === "available" ||
        expectedDisplayStatus === "available_stale") &&
    value.unknown_degrades_to_unavailable === true
  );
}

function isBoundedInteger(
  value: unknown,
  minimum: number,
  maximum: number,
): value is number {
  return (
    typeof value === "number" &&
    Number.isSafeInteger(value) &&
    value >= minimum &&
    value <= maximum
  );
}

function isNullableBoundedInteger(
  value: unknown,
  minimum: number,
  maximum: number,
): value is number | null {
  return value === null || isBoundedInteger(value, minimum, maximum);
}

function isSafeSkillMarketplaceSnapshotHash(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^snapshot-hash-ref:skill-marketplace-posture:[a-f0-9]{64}$/.test(value)
  );
}

function isSafeSkillMarketplaceRef(value: unknown): value is string {
  if (
    typeof value !== "string" ||
    value.length === 0 ||
    value.length > 320 ||
    !isSafeTrustAuthorityRef(value) ||
    containsSecretLike(value)
  ) {
    return false;
  }
  const lowered = value.toLowerCase();
  return !EVIDENCE_NARRATIVE_UNSAFE_REF_FRAGMENTS.some((fragment) =>
    lowered.includes(fragment),
  );
}

function isSafeSkillMarketplaceRefArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.length > 0 &&
    value.length <= 100 &&
    value.every(isSafeSkillMarketplaceRef)
  );
}

function isSafeSkillMarketplaceText(
  value: unknown,
  maxLength: number,
): value is string {
  if (!isBoundedDisplayText(value, maxLength)) {
    return false;
  }
  const safetyQualifiedValue = value
    .toLowerCase()
    .replaceAll("without an api key", "")
    .replaceAll("no api key", "");
  return (
    !containsSecretLike(safetyQualifiedValue) &&
    !containsUnsafeTrustText(safetyQualifiedValue)
  );
}

function isSafeSkillMarketplaceRedactionArray(
  value: unknown,
): value is string[] {
  return (
    Array.isArray(value) &&
    value.length > 0 &&
    value.length <= 40 &&
    value.every(
      (item) =>
        typeof item === "string" &&
        item.length <= 120 &&
        /^[a-z][a-z0-9_]+$/.test(item) &&
        (item.endsWith("_only") || item.endsWith("_omitted")) &&
        !containsSecretLike(item),
    )
  );
}

function isBoundedDisplayText(value: unknown, maxLength: number): value is string {
  if (typeof value !== "string") {
    return false;
  }
  const codePointLength = Array.from(value).length;
  return codePointLength > 0 && codePointLength <= maxLength;
}

function containsTerminalControlCharacters(value: string): boolean {
  return /[\u0000-\u001f\u007f-\u009f]/u.test(value);
}

function isSafeRuntimeRunEvents(
  value: RuntimeRunEventsReadModel | undefined,
): value is RuntimeRunEventsReadModel {
  if (
    value === undefined ||
    !Array.isArray(value.lifecycle_mappings) ||
    !Array.isArray(value.run_proposals) ||
    !Array.isArray(value.event_previews) ||
    !Array.isArray(value.stream_summaries) ||
    value.goal_lifecycle === undefined ||
    !Array.isArray(value.goal_lifecycle.goals) ||
    !isSafeRuntimeGoalMutationSubmissions(value.goal_mutation_submissions)
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
    value.status === "durable_local_replay" &&
    value.route_ref === "GET /api/runtime/run-events" &&
    value.cli_ref === "uaa runtime inspect-run-events" &&
    isSafeTrustAuthorityRef(value.snapshot_ref) &&
    isSafeTrustAuthorityRef(value.snapshot_hash_ref) &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-run-events-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    TRUST_AUTHORITY_DECISION_OUTCOMES.includes(
      value.authority_state_decision_outcome,
    ) &&
    typeof value.authority_state_status === "string" &&
    value.authority_state_status.length > 0 &&
    typeof value.authority_state_operator_message === "string" &&
    value.authority_state_operator_message.length > 0 &&
    isNonEmptyStringArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    isNonEmptyStringArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:runtime-run-create:not-implemented",
    ) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.uaa_controls_authority === true &&
    value.no_runtime_control_routes_registered === true &&
    value.safe_refs_only === true &&
    value.proposal_count === value.run_proposals.length &&
    value.approval_wait_count ===
      value.event_previews.filter(
        (event) => event.event_kind === "approval_wait_entered",
      ).length &&
    value.completed_run_count ===
      value.stream_summaries.filter(
        (stream) =>
          stream.successful_receipt_recorded ||
          stream.terminal_event_kind === "completion_verified",
      ).length &&
    value.stream_summaries.every(
      (stream) =>
        Number.isSafeInteger(stream.first_retained_sequence) &&
        stream.first_retained_sequence >= 1 &&
        Number.isSafeInteger(stream.last_sequence) &&
        stream.last_sequence >= stream.first_retained_sequence &&
        Number.isSafeInteger(stream.retained_event_count) &&
        stream.retained_event_count >= 1 &&
        typeof stream.successful_receipt_recorded === "boolean",
    ) &&
    value.stream_count === value.stream_summaries.length &&
    value.retained_event_count ===
      value.stream_summaries.reduce(
        (count, stream) => count + stream.retained_event_count,
        0,
      ) &&
    value.durable_event_source === true &&
    value.cursor_replay_supported === true &&
    value.bounded_retention_enabled === true &&
    value.goal_lifecycle.status === "durable_local_proof_backed" &&
    value.goal_lifecycle.goal_count === value.goal_lifecycle.goals.length &&
    value.goal_lifecycle.verified_complete_count ===
      value.goal_lifecycle.goals.filter(
        (goal) => goal.state === "verified_complete",
      ).length &&
    value.goal_lifecycle.completion_verification_state ===
      "blocked_missing_trusted_criterion_evaluator" &&
    value.goal_lifecycle.completion_verification_available === false &&
    isSafeTrustAuthorityRef(
      value.goal_lifecycle.completion_verification_blocked_reason_ref,
    ) &&
    value.goal_lifecycle.runtime_execution_enabled === false &&
    value.goal_lifecycle.model_output_authoritative === false &&
    value.goal_lifecycle.safe_refs_only === true &&
    value.goal_lifecycle.goals.every(isSafeRuntimePersistentGoal) &&
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
    value.event_previews.every(isSafeRuntimeRunEventPreview) &&
    deniedTopLevelFlags.every((flag) => value[flag] === false)
  );
}

function isSafeRuntimeGoalMutationSubmissions(
  value: RuntimeRunEventsReadModel["goal_mutation_submissions"] | undefined,
): boolean {
  if (
    value === undefined ||
    value.schema_version !==
      "goal_mutation_submission_recovery_read_model.v1" ||
    !Array.isArray(value.records) ||
    value.records.length > 64 ||
    value.pending_count !==
      value.records.filter((record) => record.status === "pending").length ||
    value.committed_count !==
      value.records.filter((record) => record.status === "committed").length ||
    value.rejected_count !==
      value.records.filter((record) => record.status === "rejected").length ||
    value.backend_owned !== true ||
    value.exact_retry_required !== true ||
    value.raw_request_content_persisted !== false ||
    value.redacted_goal_metadata_only !== true
  ) {
    return false;
  }
  return value.records.every((record) => {
    const request = record.request_payload;
    const requestPayloadValid =
      record.operation === "create"
        ? isSafeRuntimeGoalCreateRequest(request)
        : record.operation === "edit"
          ? isSafeRuntimeGoalEditRequest(request)
          : record.operation === "transition"
            ? isSafeRuntimeGoalTransitionRequest(request)
            : false;
    const evidenceRefs = isPlainRecord(request) ? request.evidence_refs : undefined;
    const goalBindingValid =
      record.operation === "create"
        ? record.goal_ref === null || record.goal_ref === undefined
        : typeof record.goal_ref === "string" &&
          isSafeTrustAuthorityRef(record.goal_ref);
    const commitBindingValid =
      record.status === "committed"
        ? typeof record.committed_goal_ref === "string" &&
          isSafeTrustAuthorityRef(record.committed_goal_ref) &&
          (record.rejection_reason_ref === null ||
            record.rejection_reason_ref === undefined) &&
          typeof record.resolved_at === "string" &&
          Number.isFinite(Date.parse(record.resolved_at))
        : record.committed_goal_ref === null ||
          record.committed_goal_ref === undefined;
    const rejectionBindingValid =
      record.status === "rejected"
        ? typeof record.rejection_reason_ref === "string" &&
          isSafeTrustAuthorityRef(record.rejection_reason_ref) &&
          typeof record.resolved_at === "string" &&
          Number.isFinite(Date.parse(record.resolved_at))
        : record.status === "committed"
          ? record.rejection_reason_ref === null ||
            record.rejection_reason_ref === undefined
          : (record.rejection_reason_ref === null ||
              record.rejection_reason_ref === undefined) &&
            (record.resolved_at === null || record.resolved_at === undefined);
    const approvalRecoveryValid =
      isSafeRuntimeGoalMutationSubmissionApprovalRecovery(record);
    return (
      record.schema_version === "goal_mutation_submission_recovery.v1" &&
      ["create", "edit", "transition"].includes(record.operation) &&
      requestPayloadValid &&
      goalBindingValid &&
      commitBindingValid &&
      rejectionBindingValid &&
      isSafeTrustAuthorityRef(record.submission_ref) &&
      isSafeTrustAuthorityRef(record.idempotency_ref) &&
      isSafeTrustAuthorityRef(record.submission_evidence_ref) &&
      isSafeTrustAuthorityRef(record.request_fingerprint_ref) &&
      typeof record.recorded_at === "string" &&
      Number.isFinite(Date.parse(record.recorded_at)) &&
      Array.isArray(evidenceRefs) &&
      evidenceRefs.length <= 32 &&
      evidenceRefs.filter(
        (ref) => ref === record.submission_evidence_ref,
      ).length === 1 &&
      evidenceRefs.every(isSafeTrustAuthorityRef) &&
      approvalRecoveryValid
    );
  });
}

function goalMutationApprovalSpecsEqual(
  left: RuntimeGoalMutationApprovalRequestSpec,
  right: RuntimeGoalMutationApprovalRequestSpec,
): boolean {
  return (
    left.schema_version === right.schema_version &&
    left.operation === right.operation &&
    left.subject_ref === right.subject_ref &&
    left.idempotency_ref === right.idempotency_ref &&
    left.request_fingerprint_ref === right.request_fingerprint_ref &&
    left.mutation_request_fingerprint_ref ===
      right.mutation_request_fingerprint_ref &&
    left.exact_scope_ref === right.exact_scope_ref &&
    left.approval_request_ref === right.approval_request_ref &&
    left.approval_ref === right.approval_ref &&
    left.operator_actor_ref === right.operator_actor_ref &&
    left.requested_at === right.requested_at &&
    left.expires_at === right.expires_at
  );
}

function stringArraysEqual(left: unknown, right: string[]): boolean {
  return (
    Array.isArray(left) &&
    left.length === right.length &&
    left.every((value, index) => value === right[index])
  );
}

function isSafeRuntimeGoalMutationApprovalGrant(
  value: unknown,
  spec: RuntimeGoalMutationApprovalRequestSpec,
  decisionActorRef: string,
  expectedStatus: "granted" | "revoked",
): boolean {
  if (!isPlainRecord(value)) return false;
  const classification = value.data_classification;
  const metadata = value.metadata;
  const allowedKeys = new Set([
    "approval_ref",
    "approval_request_id",
    "run_id",
    "subject_type",
    "subject_id",
    "granted_to_actor_id",
    "approved_by_actor_id",
    "approved_actions",
    "approved_resource_refs",
    "risk_level",
    "data_classification",
    "purpose",
    "status",
    "created_at",
    "expires_at",
    "revoked_at",
    "event_ref",
    "trace_id",
    "metadata",
  ]);
  return (
    Object.keys(value).every((key) => allowedKeys.has(key)) &&
    value.approval_ref === spec.approval_ref &&
    value.approval_request_id === spec.approval_request_ref &&
    isSafeTrustAuthorityRef(value.run_id) &&
    value.subject_type === "kernel_task" &&
    value.subject_id === spec.subject_ref &&
    value.granted_to_actor_id === spec.operator_actor_ref &&
    value.approved_by_actor_id === decisionActorRef &&
    stringArraysEqual(value.approved_actions, [
      `goal_mutation_${spec.operation}`,
    ]) &&
    stringArraysEqual(value.approved_resource_refs, [
      spec.subject_ref,
      spec.exact_scope_ref,
      spec.request_fingerprint_ref,
      spec.mutation_request_fingerprint_ref,
      spec.idempotency_ref,
    ]) &&
    value.risk_level === "low" &&
    isPlainRecord(classification) &&
    classification.classification === "user_private" &&
    classification.source === "goal-runtime-exact-local-mutation" &&
    classification.reason === "Goal metadata remains local and redacted." &&
    stringArraysEqual(classification.allowed_sinks, ["local-goal-journal"]) &&
    stringArraysEqual(classification.forbidden_sinks, [
      "provider",
      "network",
      "runtime-execution",
    ]) &&
    classification.requires_redaction === true &&
    value.purpose ===
      "Record one exact local proof-backed goal metadata mutation; runtime execution and standing authority remain disabled." &&
    value.status === expectedStatus &&
    typeof value.created_at === "string" &&
    Number.isFinite(Date.parse(value.created_at)) &&
    value.expires_at === spec.expires_at &&
    (expectedStatus === "revoked"
      ? typeof value.revoked_at === "string" &&
        Number.isFinite(Date.parse(value.revoked_at))
      : value.revoked_at === null || value.revoked_at === undefined) &&
    isSafeTrustAuthorityRef(value.event_ref) &&
    value.trace_id === spec.approval_request_ref &&
    isPlainRecord(metadata) &&
    Object.keys(metadata).length === 1 &&
    metadata.approval_mode === "local_dev"
  );
}

function isSafeRuntimeGoalMutationSubmissionApprovalRecovery(
  record: RuntimeRunEventsReadModel["goal_mutation_submissions"]["records"][number],
): boolean {
  const recovery = record.approval_recovery;
  if (
    !isPlainRecord(recovery) ||
    recovery.schema_version !==
      "goal_mutation_approval_recovery.v1" ||
    recovery.authoritative_current !== true ||
    ![
      "missing",
      "pending",
      "approved",
      "expired",
      "denied",
      "revoked",
    ].includes(String(recovery.posture))
  ) {
    return false;
  }
  const approvalRequest = recovery.approval_request;
  const latestDecision = recovery.latest_decision;
  if (recovery.posture === "missing") {
    return (
      (approvalRequest === null || approvalRequest === undefined) &&
      (latestDecision === null || latestDecision === undefined)
    );
  }
  if (!isSafeRuntimeGoalMutationApprovalRequestSpec(approvalRequest)) {
    return false;
  }
  const expectedOperation =
    record.operation === "transition" && isPlainRecord(record.request_payload)
      ? `transition-${String(record.request_payload.transition)}`
      : record.operation;
  const expectedSubject =
    record.operation === "create" ? "goal-ref:new" : record.goal_ref;
  if (
    approvalRequest.operation !== expectedOperation ||
    approvalRequest.subject_ref !== expectedSubject ||
    approvalRequest.idempotency_ref !== record.idempotency_ref
  ) {
    return false;
  }
  if (recovery.posture === "pending") {
    return (
      latestDecision === null || latestDecision === undefined
    );
  }
  if (recovery.posture === "expired" && latestDecision == null) {
    return true;
  }
  if (
    !isSafeRuntimeGoalMutationApprovalDecision(latestDecision) ||
    !goalMutationApprovalSpecsEqual(approvalRequest, latestDecision.spec)
  ) {
    return false;
  }
  const terminalDecisionActorBound =
    latestDecision.status === "expired"
      ? latestDecision.decision_actor_ref ===
        "operator-ref:goal-runtime-expiration-recovery"
      : latestDecision.decision_actor_ref === "operator-ref:local-user";
  const terminalDecisionBound =
    isSafeTrustAuthorityRef(latestDecision.decision_reason_ref) &&
    terminalDecisionActorBound &&
    typeof latestDecision.decided_at === "string" &&
    Number.isFinite(Date.parse(latestDecision.decided_at));
  if (recovery.posture === "approved") {
    return (
      latestDecision.status === "approved" &&
      terminalDecisionBound &&
      isSafeRuntimeGoalMutationApprovalGrant(
        latestDecision.approval_grant,
        approvalRequest,
        latestDecision.decision_actor_ref as string,
        "granted",
      )
    );
  }
  if (recovery.posture === "expired") {
    return (
      (latestDecision.status === "expired" &&
        terminalDecisionBound &&
        (latestDecision.approval_grant === null ||
          latestDecision.approval_grant === undefined)) ||
      (latestDecision.status === "approved" &&
        terminalDecisionBound &&
        isSafeRuntimeGoalMutationApprovalGrant(
          latestDecision.approval_grant,
          approvalRequest,
          latestDecision.decision_actor_ref as string,
          "granted",
        ))
    );
  }
  if (recovery.posture === "denied") {
    return (
      latestDecision.status === "denied" &&
      terminalDecisionBound &&
      (latestDecision.approval_grant === null ||
        latestDecision.approval_grant === undefined)
    );
  }
  return (
    latestDecision.status === "revoked" &&
    terminalDecisionBound &&
    isSafeRuntimeGoalMutationApprovalGrant(
      latestDecision.approval_grant,
      approvalRequest,
      latestDecision.decision_actor_ref as string,
      "revoked",
    )
  );
}

function isSafeRuntimeGoalRequestText(value: unknown): value is string {
  const lowered = typeof value === "string" ? value.trim().toLowerCase() : "";
  const rawContentMarkers = [
    "prompt:",
    "response:",
    "transcript:",
    "system:",
    "developer:",
    "assistant:",
    "user:",
    "tool:",
    "model:",
    "<|system|>",
    "<|developer|>",
    "<|user|>",
    "<|assistant|>",
    "<|tool|>",
  ];
  return (
    isBoundedDisplayText(value, 1200) &&
    !containsTerminalControlCharacters(String(value)) &&
    !containsSecretLike(value) &&
    !containsAbsoluteLocalPath(String(value)) &&
    !rawContentMarkers.some((marker) => lowered.includes(marker)) &&
    !["summarize ", "translate ", "respond to "].some((prefix) =>
      lowered.startsWith(prefix),
    )
  );
}

function isSafeRuntimeGoalRequestTexts(
  value: unknown,
  required = false,
): value is string[] {
  return (
    Array.isArray(value) &&
    value.length <= 32 &&
    (!required || value.length > 0) &&
    value.every(isSafeRuntimeGoalRequestText)
  );
}

function isSafeRuntimeGoalRequestRefs(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.length <= 32 &&
    value.every(isSafeTrustAuthorityRef)
  );
}

function isSafeRuntimeGoalBudget(value: unknown): boolean {
  if (!isPlainRecord(value)) return false;
  const deadlineValid =
    value.deadline_at === null ||
    value.deadline_at === undefined ||
    (typeof value.deadline_at === "string" &&
      Number.isFinite(Date.parse(value.deadline_at)));
  return (
    Number.isSafeInteger(value.operation_limit) &&
    Number(value.operation_limit) >= 1 &&
    Number(value.operation_limit) <= 10_000 &&
    Number.isSafeInteger(value.cost_budget_microusd) &&
    Number(value.cost_budget_microusd) >= 0 &&
    Number(value.cost_budget_microusd) <= 10_000_000_000 &&
    deadlineValid
  );
}

function hasRuntimeGoalMutationValue(value: unknown): boolean {
  return value !== undefined && value !== null;
}

function isSafeRuntimeGoalLinks(value: unknown): boolean {
  return (
    isPlainRecord(value) &&
    isSafeRuntimeGoalRequestRefs(value.plan_refs) &&
    isSafeRuntimeGoalRequestRefs(value.run_refs) &&
    isSafeRuntimeGoalRequestRefs(value.action_inbox_refs) &&
    isSafeRuntimeGoalRequestRefs(value.work_board_refs)
  );
}

function isSafeRuntimeGoalCreateRequest(
  value: unknown,
): value is RuntimeGoalCreateRequest {
  if (!isPlainRecord(value)) return false;
  const allowedKeys = new Set([
    "text_redaction_posture",
    "objective",
    "desired_outcome",
    "success_criteria",
    "constraints",
    "in_scope_resource_refs",
    "stop_condition",
    "budget",
    "links",
    "evidence_refs",
  ]);
  return (
    Object.keys(value).every((key) => allowedKeys.has(key)) &&
    value.text_redaction_posture ===
      "operator_authored_redacted_summary_only" &&
    isSafeRuntimeGoalRequestText(value.objective) &&
    isSafeRuntimeGoalRequestText(value.desired_outcome) &&
    isSafeRuntimeGoalRequestTexts(value.success_criteria, true) &&
    isSafeRuntimeGoalRequestTexts(value.constraints) &&
    isSafeRuntimeGoalRequestRefs(value.in_scope_resource_refs) &&
    isSafeRuntimeGoalRequestText(value.stop_condition) &&
    isSafeRuntimeGoalBudget(value.budget) &&
    isSafeRuntimeGoalLinks(value.links) &&
    isSafeRuntimeGoalRequestRefs(value.evidence_refs)
  );
}

function isSafeRuntimeGoalEditRequest(
  value: unknown,
): value is RuntimeGoalEditRequest {
  if (!isPlainRecord(value)) return false;
  const allowedKeys = new Set([
    "expected_version",
    "text_redaction_posture",
    "objective",
    "desired_outcome",
    "success_criteria",
    "constraints",
    "in_scope_resource_refs",
    "stop_condition",
    "budget",
    "links",
    "evidence_refs",
  ]);
  const mutationKeys = [
    "objective",
    "desired_outcome",
    "success_criteria",
    "constraints",
    "in_scope_resource_refs",
    "stop_condition",
    "budget",
    "links",
    "evidence_refs",
  ];
  const textKeys = [
    "objective",
    "desired_outcome",
    "success_criteria",
    "constraints",
    "stop_condition",
  ];
  const hasTextMutation = textKeys.some((key) =>
    hasRuntimeGoalMutationValue(value[key]),
  );
  return (
    Object.keys(value).every((key) => allowedKeys.has(key)) &&
    Number.isSafeInteger(value.expected_version) &&
    Number(value.expected_version) >= 1 &&
    Number(value.expected_version) <= 4096 &&
    mutationKeys.some((key) => hasRuntimeGoalMutationValue(value[key])) &&
    (hasTextMutation
      ? value.text_redaction_posture ===
        "operator_authored_redacted_summary_only"
      : !hasRuntimeGoalMutationValue(value.text_redaction_posture)) &&
    (!hasRuntimeGoalMutationValue(value.objective) ||
      isSafeRuntimeGoalRequestText(value.objective)) &&
    (!hasRuntimeGoalMutationValue(value.desired_outcome) ||
      isSafeRuntimeGoalRequestText(value.desired_outcome)) &&
    (!hasRuntimeGoalMutationValue(value.success_criteria) ||
      isSafeRuntimeGoalRequestTexts(value.success_criteria, true)) &&
    (!hasRuntimeGoalMutationValue(value.constraints) ||
      isSafeRuntimeGoalRequestTexts(value.constraints)) &&
    (!hasRuntimeGoalMutationValue(value.in_scope_resource_refs) ||
      isSafeRuntimeGoalRequestRefs(value.in_scope_resource_refs)) &&
    (!hasRuntimeGoalMutationValue(value.stop_condition) ||
      isSafeRuntimeGoalRequestText(value.stop_condition)) &&
    (!hasRuntimeGoalMutationValue(value.budget) ||
      isSafeRuntimeGoalBudget(value.budget)) &&
    (!hasRuntimeGoalMutationValue(value.links) ||
      isSafeRuntimeGoalLinks(value.links)) &&
    (!hasRuntimeGoalMutationValue(value.evidence_refs) ||
      isSafeRuntimeGoalRequestRefs(value.evidence_refs))
  );
}

function isSafeRuntimeGoalCompletionEvidence(value: unknown): boolean {
  if (!isPlainRecord(value)) return false;
  const allowedKeys = new Set([
    "goal_ref",
    "goal_version",
    "run_ref",
    "receipt_ref",
    "proof_ref",
    "criterion_proof_refs",
    "evidence_ref",
    "verifier_ref",
  ]);
  return (
    Object.keys(value).every((key) => allowedKeys.has(key)) &&
    isSafeTrustAuthorityRef(value.goal_ref) &&
    Number.isSafeInteger(value.goal_version) &&
    Number(value.goal_version) >= 1 &&
    Number(value.goal_version) <= 4096 &&
    isSafeTrustAuthorityRef(value.run_ref) &&
    isSafeTrustAuthorityRef(value.receipt_ref) &&
    isSafeTrustAuthorityRef(value.proof_ref) &&
    isSafeRuntimeGoalRequestRefs(value.criterion_proof_refs) &&
    value.criterion_proof_refs.length > 0 &&
    isSafeTrustAuthorityRef(value.evidence_ref) &&
    isSafeTrustAuthorityRef(value.verifier_ref)
  );
}

function isSafeRuntimeGoalTransitionRequest(
  value: unknown,
): value is RuntimeGoalTransitionRequest {
  if (!isPlainRecord(value)) return false;
  const allowedKeys = new Set([
    "expected_version",
    "transition",
    "reason_ref",
    "evidence_refs",
    "completion_evidence",
  ]);
  const transition = String(value.transition);
  const completionEvidenceValid =
    transition === "verify_completion"
      ? isSafeRuntimeGoalCompletionEvidence(value.completion_evidence)
      : !hasRuntimeGoalMutationValue(value.completion_evidence);
  return (
    Object.keys(value).every((key) => allowedKeys.has(key)) &&
    Number.isSafeInteger(value.expected_version) &&
    Number(value.expected_version) >= 1 &&
    Number(value.expected_version) <= 4096 &&
    [
      "pause",
      "resume",
      "block",
      "wait",
      "cancel",
      "clear",
      "restore",
      "request_completion",
      "verify_completion",
    ].includes(String(value.transition)) &&
    isSafeTrustAuthorityRef(value.reason_ref) &&
    (!hasRuntimeGoalMutationValue(value.evidence_refs) ||
      isSafeRuntimeGoalRequestRefs(value.evidence_refs)) &&
    completionEvidenceValid
  );
}

function isSafeRuntimeRunEventPreview(
  event: RuntimeRunEventsReadModel["event_previews"][number],
): boolean {
  const allowedKinds = new Set([
    "run_proposed",
    "approval_wait_entered",
    "event_stream_preview",
    "stop_requested_preview",
    "proof_bound",
    "goal_linked",
    "plan_linked",
    "run_started",
    "approval_resumed",
    "worker_restart_recovered",
    "allowed_local_action_recorded",
    "receipt_recorded",
    "evidence_linked",
    "completion_verified",
    "cancellation_requested",
    "cancelled",
    "failed_retryable",
    "failed_terminal",
    "dead_lettered",
  ]);
  const terminalKinds = new Set([
    "receipt_recorded",
    "completion_verified",
    "cancelled",
    "failed_terminal",
    "dead_lettered",
  ]);
  const synthesizedPresenceProofRef =
    "proof-ref:runtime-run-events:redacted-event-presence";
  const safeRef = (value: unknown): value is string =>
    typeof value === "string" &&
    value.length <= 320 &&
    isSafeTrustAuthorityRef(value);
  const safeRefs = (value: unknown, maximum: number) =>
    Array.isArray(value) &&
    value.length <= maximum &&
    value.every(safeRef);
  const criterionBindingsValid =
    Array.isArray(event.criterion_verifier_bindings) &&
    event.criterion_verifier_bindings.length <= 32 &&
    event.criterion_verifier_bindings.every(
      (binding) =>
        isSafeTrustAuthorityRef(binding.goal_ref) &&
        Number.isSafeInteger(binding.goal_version) &&
        binding.goal_version >= 1 &&
        binding.goal_version <= 4096 &&
        isSafeTrustAuthorityRef(binding.criterion_ref) &&
        isSafeTrustAuthorityRef(binding.proof_ref) &&
        isSafeTrustAuthorityRef(binding.verifier_ref) &&
        isSafeTrustAuthorityRef(binding.evaluator_receipt_ref),
    );
  const hasDurableSequence = event.sequence !== null && event.sequence !== undefined;
  const durableFieldsValid = hasDurableSequence
    ? Number.isSafeInteger(event.sequence) &&
      Number(event.sequence) >= 1 &&
      typeof event.recorded_at === "string" &&
      Number.isFinite(Date.parse(event.recorded_at)) &&
      safeRef(event.event_hash_ref) &&
      (event.predecessor_hash_ref === null ||
        event.predecessor_hash_ref === undefined ||
        safeRef(event.predecessor_hash_ref))
    : (event.recorded_at === null || event.recorded_at === undefined) &&
      (event.event_hash_ref === null || event.event_hash_ref === undefined) &&
      (event.predecessor_hash_ref === null ||
        event.predecessor_hash_ref === undefined);
  const proofBindingValid =
    event.proof_refs.length > 0
      ? event.proof_ref === event.proof_refs[0]
      : !terminalKinds.has(event.event_kind) &&
        event.proof_ref === synthesizedPresenceProofRef;
  const operationBindingsValid =
    (event.event_kind !== "goal_linked" ||
      (event.goal_ref !== null &&
        event.goal_ref !== undefined &&
        safeRef(event.goal_ref))) &&
    (event.event_kind !== "plan_linked" ||
      (event.plan_ref !== null &&
        event.plan_ref !== undefined &&
        safeRef(event.plan_ref)));
  return (
    allowedKinds.has(event.event_kind) &&
    safeRef(event.event_ref) &&
    safeRef(event.runtime_run_ref) &&
    safeRef(event.uaa_durable_run_ref) &&
    safeRef(event.proof_ref) &&
    isBoundedDisplayText(event.safe_summary, 1200) &&
    !containsTerminalControlCharacters(event.safe_summary) &&
    !containsSecretLike(event.safe_summary) &&
    !containsAbsoluteLocalPath(event.safe_summary) &&
    event.redaction_status === "redacted_safe_ref_only" &&
    safeRefs(event.proof_refs, 97) &&
    safeRefs(event.receipt_refs, 33) &&
    criterionBindingsValid &&
    proofBindingValid &&
    (!terminalKinds.has(event.event_kind) ||
      (event.proof_refs.length > 0 && event.receipt_refs.length > 0)) &&
    (event.goal_ref === null ||
      event.goal_ref === undefined ||
      safeRef(event.goal_ref)) &&
    (event.plan_ref === null ||
      event.plan_ref === undefined ||
      safeRef(event.plan_ref)) &&
    operationBindingsValid &&
    durableFieldsValid &&
    event.runtime_payload_persisted === false &&
    event.raw_log_persisted === false &&
    event.raw_prompt_persisted === false &&
    event.raw_response_persisted === false
  );
}

function isSafeRuntimePersistentGoal(goal: RuntimePersistentGoal): boolean {
  if (
    !isPlainRecord(goal) ||
    !isPlainRecord(goal.links) ||
    !isPlainRecord(goal.budget)
  ) {
    return false;
  }
  const allowedStates = new Set<RuntimePersistentGoal["state"]>([
    "active",
    "paused",
    "blocked",
    "waiting",
    "complete_requested",
    "verified_complete",
    "cancelled",
    "cleared",
  ]);
  const safeText = (value: unknown) =>
    isBoundedDisplayText(value, 1200) &&
    !containsTerminalControlCharacters(String(value)) &&
    !containsSecretLike(value) &&
    !containsAbsoluteLocalPath(String(value));
  const safeRefs = (value: unknown) =>
    Array.isArray(value) &&
    value.length <= 32 &&
    value.every(isSafeTrustAuthorityRef);
  const safeTexts = (value: unknown, required = false) =>
    Array.isArray(value) &&
    value.length <= 32 &&
    (!required || value.length > 0) &&
    value.every(safeText);
  const completionRefs = [
    goal.completion_run_ref,
    goal.completion_evidence_ref,
    goal.completion_receipt_ref,
    goal.completion_proof_ref,
    goal.completion_verifier_ref,
    goal.completion_source_goal_version,
  ];
  const noCompletionRefs = completionRefs.every(
    (ref) => ref === null || ref === undefined,
  );
  const exactCompletionRefs = completionRefs.slice(0, -1).every(
    (ref) => typeof ref === "string" && isSafeTrustAuthorityRef(ref),
  ) &&
    Number.isSafeInteger(goal.completion_source_goal_version) &&
    Number(goal.completion_source_goal_version) >= 1 &&
    Number(goal.completion_source_goal_version) <= 4096;
  const noCompletionPlan =
    goal.completion_plan_ref === null ||
    goal.completion_plan_ref === undefined;
  const exactCompletionPlan =
    typeof goal.completion_plan_ref === "string" &&
    isSafeTrustAuthorityRef(goal.completion_plan_ref) &&
    Array.isArray(goal.links.plan_refs) &&
    goal.links.plan_refs.includes(goal.completion_plan_ref);
  const completionPlanValid =
    exactCompletionRefs &&
    Array.isArray(goal.links.plan_refs) &&
    goal.links.plan_refs.length
      ? exactCompletionPlan
      : noCompletionPlan;
  const criterionProofRefsValid =
    safeRefs(goal.completion_criterion_proof_refs) &&
    (goal.state === "verified_complete" ||
    (goal.state === "cleared" && exactCompletionRefs)
      ? goal.completion_criterion_proof_refs.length ===
        goal.success_criteria.length
      : goal.completion_criterion_proof_refs.length === 0);
  const criterionBindingsValid =
    Array.isArray(goal.completion_criterion_verifier_bindings) &&
    goal.completion_criterion_verifier_bindings.length <= 32 &&
    (goal.state === "verified_complete" ||
    (goal.state === "cleared" && exactCompletionRefs)
      ? goal.completion_criterion_verifier_bindings.length ===
          goal.success_criteria.length &&
        goal.completion_criterion_verifier_bindings.every(
          (binding, index) =>
            isPlainRecord(binding) &&
            binding.goal_ref === goal.goal_ref &&
            binding.goal_version === goal.completion_source_goal_version &&
            isSafeTrustAuthorityRef(binding.criterion_ref) &&
            binding.proof_ref === goal.completion_criterion_proof_refs[index] &&
            binding.verifier_ref === goal.completion_verifier_ref &&
            isSafeTrustAuthorityRef(binding.evaluator_receipt_ref),
        )
      : goal.completion_criterion_verifier_bindings.length === 0);
  const completionPostureValid =
    goal.state === "verified_complete"
      ? exactCompletionRefs &&
        completionPlanValid &&
        criterionProofRefsValid &&
        criterionBindingsValid
      : goal.state === "cleared"
        ? (noCompletionRefs && noCompletionPlan) ||
          (exactCompletionRefs &&
            completionPlanValid &&
            criterionProofRefsValid &&
            criterionBindingsValid)
        : noCompletionRefs &&
          noCompletionPlan &&
          criterionProofRefsValid &&
          criterionBindingsValid;

  return (
    goal.schema_version === "persistent_goal.v1" &&
    goal.contract_ref === "contract-ref:proof-backed-goals-durable-events:v1" &&
    isSafeTrustAuthorityRef(goal.goal_ref) &&
    goal.text_redaction_posture ===
      "operator_authored_redacted_summary_only" &&
    safeText(goal.objective) &&
    safeText(goal.desired_outcome) &&
    safeText(goal.stop_condition) &&
    safeTexts(goal.success_criteria, true) &&
    safeTexts(goal.constraints) &&
    safeRefs(goal.in_scope_resource_refs) &&
    safeRefs(goal.evidence_refs) &&
    safeRefs(goal.links.plan_refs) &&
    safeRefs(goal.links.run_refs) &&
    safeRefs(goal.links.action_inbox_refs) &&
    safeRefs(goal.links.work_board_refs) &&
    allowedStates.has(goal.state) &&
    Number.isSafeInteger(goal.version) &&
    goal.version >= 1 &&
    goal.version <= 4096 &&
    Number.isSafeInteger(goal.budget.operation_limit) &&
    goal.budget.operation_limit >= 1 &&
    Number.isSafeInteger(goal.budget.cost_budget_microusd) &&
    goal.budget.cost_budget_microusd >= 0 &&
    completionPostureValid &&
    goal.safe_refs_only === true &&
    goal.model_output_authoritative === false
  );
}

function isSafeRuntimeGoalMutationResult(
  value: RuntimeGoalMutationResult | undefined,
): value is RuntimeGoalMutationResult {
  if (!isPlainRecord(value)) return false;
  const { goal, approval_binding: approval } = value;
  if (!isPlainRecord(goal) || !isPlainRecord(approval)) return false;
  return (
    isSafeRuntimePersistentGoal(goal as unknown as RuntimePersistentGoal) &&
    approval.schema_version === "goal_mutation_approval_binding.v1" &&
    approval.approval_validated === true &&
    approval.standing_authority_granted === false &&
    isSafeTrustAuthorityRef(approval.approval_ref) &&
    isSafeTrustAuthorityRef(approval.approval_request_ref) &&
    isSafeTrustAuthorityRef(approval.approval_decision_ref) &&
    isSafeTrustAuthorityRef(approval.approval_ledger_entry_hash_ref) &&
    isSafeTrustAuthorityRef(approval.exact_scope_ref) &&
    isSafeTrustAuthorityRef(approval.request_fingerprint_ref)
  );
}

export async function fetchRuntimeRunEvents(
  expectedBinding: BackendTruthReadBinding | null = null,
): Promise<RuntimeRunEventsReadModel> {
  const payload = await readEnvelope<RuntimeRunEventsReadModel>(
    API_ENDPOINTS.runtimeRunEvents,
    defaultControlCenterReadLimiter,
    expectedBinding,
  );
  if (!isSafeRuntimeRunEvents(payload)) {
    throw new Error("Runtime goal/event state failed safe validation.");
  }
  return payload;
}

type RuntimeGoalMutationIdentityMaterial =
  | {
      operation: "create";
      goalRef: null;
      request: RuntimeGoalCreateRequest;
    }
  | {
      operation: "edit";
      goalRef: string;
      request: RuntimeGoalEditRequest;
    }
  | {
      operation: "transition";
      goalRef: string;
      request: RuntimeGoalTransitionRequest;
    };

const RUNTIME_GOAL_MUTATION_IDENTITY_DOMAIN =
  "uaa.control-center.runtime-goal-mutation-idempotency.v1";
const RUNTIME_GOAL_CREATE_SUBMISSION_DOMAIN =
  "uaa.control-center.runtime-goal-create-submission.v1";
const RUNTIME_GOAL_UPDATE_SUBMISSION_DOMAIN =
  "uaa.control-center.runtime-goal-update-submission.v1";
const RUNTIME_GOAL_CREATE_SUBMISSION_EVIDENCE_PREFIX =
  "evidence-ref:control-center-goal-create-submission:sha256:";
const RUNTIME_GOAL_UPDATE_SUBMISSION_EVIDENCE_PREFIX =
  "evidence-ref:control-center-goal-update-submission:";

function newRuntimeGoalMutationSubmissionRef(): string {
  const randomUuid = globalThis.crypto?.randomUUID;
  if (randomUuid === undefined) {
    throw new Error("RUNTIME_GOAL_MUTATION_IDENTITY_UNAVAILABLE");
  }
  return `submission-ref:control-center-goal-mutation:${randomUuid.call(globalThis.crypto)}`;
}

async function sha256Hex(value: string): Promise<string> {
  const subtle = globalThis.crypto?.subtle;
  if (subtle === undefined) {
    throw new Error("RUNTIME_GOAL_MUTATION_DIGEST_UNAVAILABLE");
  }
  try {
    const bytes = new TextEncoder().encode(value);
    const digest = await subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest), (byte) =>
      byte.toString(16).padStart(2, "0"),
    ).join("");
  } catch {
    throw new Error("RUNTIME_GOAL_MUTATION_DIGEST_UNAVAILABLE");
  }
}

export async function runtimeGoalMutationIdempotencyRef(
  material: RuntimeGoalMutationIdentityMaterial,
): Promise<string> {
  if (
    (material.operation === "create" && material.goalRef !== null) ||
    (material.operation !== "create" &&
      (typeof material.goalRef !== "string" ||
        !isSafeTrustAuthorityRef(material.goalRef)))
  ) {
    throw new Error("RUNTIME_GOAL_MUTATION_IDENTITY_INVALID");
  }
  const canonicalIntent = stableStringifyForIdempotency({
    domain: RUNTIME_GOAL_MUTATION_IDENTITY_DOMAIN,
    operation: material.operation,
    goal_ref: material.goalRef,
    request: material.request,
  });
  const digest = await sha256Hex(canonicalIntent);
  return `idempotency-ref:control-center-goal-${material.operation}:sha256:${digest}`;
}

export async function prepareRuntimeGoalCreateSubmission(
  request: RuntimeGoalCreateRequest,
  submissionRef: string = newRuntimeGoalMutationSubmissionRef(),
): Promise<{
  request: RuntimeGoalCreateRequest;
  idempotencyRef: string;
  submissionEvidenceRef: string;
  submissionRef: string;
}> {
  if (!isSafeTrustAuthorityRef(submissionRef)) {
    throw new Error("RUNTIME_GOAL_MUTATION_IDENTITY_INVALID");
  }
  const evidenceRefs = request.evidence_refs.filter(
    (ref) => !ref.startsWith(RUNTIME_GOAL_CREATE_SUBMISSION_EVIDENCE_PREFIX),
  );
  const canonicalIntent = stableStringifyForIdempotency({
    domain: RUNTIME_GOAL_CREATE_SUBMISSION_DOMAIN,
    submission_ref: submissionRef,
    request: {
      ...request,
      evidence_refs: evidenceRefs,
    },
  });
  const intentDigest = await sha256Hex(canonicalIntent);
  const submissionEvidenceRef =
    `${RUNTIME_GOAL_CREATE_SUBMISSION_EVIDENCE_PREFIX}${intentDigest}`;
  const submissionRequest: RuntimeGoalCreateRequest = {
    ...request,
    evidence_refs: [...evidenceRefs, submissionEvidenceRef],
  };
  return {
    request: submissionRequest,
    idempotencyRef: await runtimeGoalMutationIdempotencyRef({
      operation: "create",
      goalRef: null,
      request: submissionRequest,
    }),
    submissionEvidenceRef,
    submissionRef,
  };
}

export async function prepareRuntimeGoalUpdateSubmission(
  operation: "edit",
  goalRef: string,
  request: RuntimeGoalEditRequest,
  submissionRef?: string,
): Promise<{
  request: RuntimeGoalEditRequest;
  idempotencyRef: string;
  submissionEvidenceRef: string;
  submissionRef: string;
}>;
export async function prepareRuntimeGoalUpdateSubmission(
  operation: "transition",
  goalRef: string,
  request: RuntimeGoalTransitionRequest,
  submissionRef?: string,
): Promise<{
  request: RuntimeGoalTransitionRequest;
  idempotencyRef: string;
  submissionEvidenceRef: string;
  submissionRef: string;
}>;
export async function prepareRuntimeGoalUpdateSubmission(
  operation: "edit" | "transition",
  goalRef: string,
  request: RuntimeGoalEditRequest | RuntimeGoalTransitionRequest,
  submissionRef: string = newRuntimeGoalMutationSubmissionRef(),
): Promise<{
  request: RuntimeGoalEditRequest | RuntimeGoalTransitionRequest;
  idempotencyRef: string;
  submissionEvidenceRef: string;
  submissionRef: string;
}> {
  if (!isSafeTrustAuthorityRef(goalRef)) {
    throw new Error("RUNTIME_GOAL_MUTATION_IDENTITY_INVALID");
  }
  if (!isSafeTrustAuthorityRef(submissionRef)) {
    throw new Error("RUNTIME_GOAL_MUTATION_IDENTITY_INVALID");
  }
  const evidenceRefs = (request.evidence_refs ?? []).filter(
    (ref) =>
      !ref.startsWith(RUNTIME_GOAL_UPDATE_SUBMISSION_EVIDENCE_PREFIX),
  );
  const canonicalIntent = stableStringifyForIdempotency({
    domain: RUNTIME_GOAL_UPDATE_SUBMISSION_DOMAIN,
    submission_ref: submissionRef,
    operation,
    goal_ref: goalRef,
    request: {
      ...request,
      evidence_refs: evidenceRefs,
    },
  });
  const intentDigest = await sha256Hex(canonicalIntent);
  const submissionEvidenceRef =
    `${RUNTIME_GOAL_UPDATE_SUBMISSION_EVIDENCE_PREFIX}${operation}:` +
    `sha256:${intentDigest}`;
  const submissionRequest = {
    ...request,
    evidence_refs: [...evidenceRefs, submissionEvidenceRef],
  };
  return {
    request: submissionRequest,
    idempotencyRef: await runtimeGoalMutationIdempotencyRef({
      operation,
      goalRef,
      request: submissionRequest,
    } as RuntimeGoalMutationIdentityMaterial),
    submissionEvidenceRef,
    submissionRef,
  };
}

function isSafeRuntimeGoalMutationApprovalRequestSpec(
  value: unknown,
): value is RuntimeGoalMutationApprovalRequestSpec {
  if (!isPlainRecord(value)) return false;
  return (
    value.schema_version === "goal_mutation_approval_request.v2" &&
    typeof value.operation === "string" &&
    value.operation.length > 0 &&
    value.operation.length <= 80 &&
    isSafeTrustAuthorityRef(value.subject_ref) &&
    isSafeTrustAuthorityRef(value.idempotency_ref) &&
    isSafeTrustAuthorityRef(value.request_fingerprint_ref) &&
    isSafeTrustAuthorityRef(value.mutation_request_fingerprint_ref) &&
    isSafeTrustAuthorityRef(value.exact_scope_ref) &&
    isSafeTrustAuthorityRef(value.approval_request_ref) &&
    isSafeTrustAuthorityRef(value.approval_ref) &&
    value.operator_actor_ref === "operator-ref:local-user" &&
    typeof value.requested_at === "string" &&
    Number.isFinite(Date.parse(value.requested_at)) &&
    typeof value.expires_at === "string" &&
    Number.isFinite(Date.parse(value.expires_at)) &&
    Date.parse(value.expires_at) > Date.parse(value.requested_at)
  );
}

function isSafeRuntimeGoalMutationApprovalDecision(
  value: unknown,
): value is RuntimeGoalMutationApprovalDecision {
  if (!isPlainRecord(value)) return false;
  return (
    value.schema_version === "goal_mutation_approval_ledger.v2" &&
    isSafeRuntimeGoalMutationApprovalRequestSpec(value.spec) &&
    ["pending", "approved", "denied", "revoked", "expired"].includes(
      String(value.status),
    ) &&
    isSafeTrustAuthorityRef(value.entry_hash_ref) &&
    (value.previous_entry_hash_ref === null ||
      value.previous_entry_hash_ref === undefined ||
      isSafeTrustAuthorityRef(value.previous_entry_hash_ref)) &&
    (value.decision_reason_ref === null ||
      value.decision_reason_ref === undefined ||
      isSafeTrustAuthorityRef(value.decision_reason_ref)) &&
    (value.decision_actor_ref === null ||
      value.decision_actor_ref === undefined ||
      isSafeTrustAuthorityRef(value.decision_actor_ref)) &&
    (value.decided_at === null ||
      value.decided_at === undefined ||
      (typeof value.decided_at === "string" &&
        Number.isFinite(Date.parse(value.decided_at))))
  );
}

export async function prepareRuntimeGoalMutationApproval(
  material: RuntimeGoalMutationIdentityMaterial,
  idempotencyRef: string,
  submissionRef: string,
  binding: BackendTruthReadBinding | null,
): Promise<RuntimeGoalMutationApprovalRequestSpec> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  if (
    !isSafeTrustAuthorityRef(idempotencyRef) ||
    !isSafeTrustAuthorityRef(submissionRef)
  ) {
    throw new Error("RUNTIME_GOAL_MUTATION_SUBMISSION_REF_INVALID");
  }
  const endpoint =
    material.operation === "create"
      ? API_ENDPOINTS.runtimeGoalApprovalPrepareCreate
      : runtimeGoalApprovalPrepareEndpoint(
          material.operation,
          material.goalRef,
        );
  const response = await fetch(`${API_BASE_POLICY.baseUrl}${endpoint}`, {
    method: "POST",
    headers: withLocalApiAuthHeaders(
      withBackendTruthMutationHeaders(
        {
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-UAA-Idempotency-Key": idempotencyRef,
          "X-UAA-Goal-Submission-Ref": submissionRef,
        },
        binding,
      ),
    ),
    body: JSON.stringify(material.request),
  });
  const payload = (await readJsonSafely(response)) as ResultEnvelope<{
    approval_request: RuntimeGoalMutationApprovalRequestSpec;
  }>;
  const data = payload.result ?? payload.data;
  const success = payload.ok ?? payload.success;
  const spec = data?.approval_request;
  if (
    !response.ok ||
    success !== true ||
    !isSafeRuntimeGoalMutationApprovalRequestSpec(spec) ||
    spec.idempotency_ref !== idempotencyRef
  ) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          payload,
          "The exact goal mutation approval request failed safely.",
        ),
      ),
    );
  }
  return spec;
}

export async function decideRuntimeGoalMutationApproval(
  approvalRequestRef: string,
  decision: "approve" | "deny",
  reasonRef: string,
  binding: BackendTruthReadBinding | null,
): Promise<RuntimeGoalMutationApprovalDecision> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  if (
    !isSafeTrustAuthorityRef(approvalRequestRef) ||
    !isSafeTrustAuthorityRef(reasonRef)
  ) {
    throw new Error("RUNTIME_GOAL_MUTATION_APPROVAL_REF_INVALID");
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${runtimeGoalApprovalDecisionEndpoint(approvalRequestRef)}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key": `idempotency-ref:goal-approval-decision:${approvalRequestRef}`,
          },
          binding,
        ),
      ),
      body: JSON.stringify({
        decision,
        decision_reason_ref: reasonRef,
      }),
    },
  );
  const payload = (await readJsonSafely(response)) as ResultEnvelope<{
    approval_decision: RuntimeGoalMutationApprovalDecision;
  }>;
  const data = payload.result ?? payload.data;
  const success = payload.ok ?? payload.success;
  const result = data?.approval_decision;
  if (
    !response.ok ||
    success !== true ||
    !isSafeRuntimeGoalMutationApprovalDecision(result) ||
    result.spec.approval_request_ref !== approvalRequestRef ||
    result.status !== (decision === "approve" ? "approved" : "denied")
  ) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          payload,
          "The exact goal mutation approval decision failed safely.",
        ),
      ),
    );
  }
  return result;
}

export async function revokeRuntimeGoalMutationApproval(
  approvalRef: string,
  reasonRef: string,
  binding: BackendTruthReadBinding | null,
): Promise<RuntimeGoalMutationApprovalDecision> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  if (
    !isSafeTrustAuthorityRef(approvalRef) ||
    !isSafeTrustAuthorityRef(reasonRef)
  ) {
    throw new Error("RUNTIME_GOAL_MUTATION_APPROVAL_REF_INVALID");
  }
  const response = await fetch(
    `${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.runtimeGoalApprovalRevoke}`,
    {
      method: "POST",
      headers: withLocalApiAuthHeaders(
        withBackendTruthMutationHeaders(
          {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key": `idempotency-ref:goal-approval-revoke:${approvalRef}`,
          },
          binding,
        ),
      ),
      body: JSON.stringify({
        approval_ref: approvalRef,
        decision_reason_ref: reasonRef,
      }),
    },
  );
  const payload = (await readJsonSafely(response)) as ResultEnvelope<{
    approval_decision: RuntimeGoalMutationApprovalDecision;
  }>;
  const data = payload.result ?? payload.data;
  const success = payload.ok ?? payload.success;
  const result = data?.approval_decision;
  if (
    !response.ok ||
    success !== true ||
    !isSafeRuntimeGoalMutationApprovalDecision(result) ||
    result.spec.approval_ref !== approvalRef ||
    result.status !== "revoked"
  ) {
    throw new Error(
      sanitizeForDisplay(
        extractErrorMessage(
          payload,
          "The exact goal mutation approval revocation failed safely.",
        ),
      ),
    );
  }
  return result;
}

async function postRuntimeGoalMutation(
  endpoint: string,
  request:
    | RuntimeGoalCreateRequest
    | RuntimeGoalEditRequest
    | RuntimeGoalTransitionRequest,
  idempotencyRef: string,
  approvalRef: string,
  submissionRef: string | null,
  binding: BackendTruthReadBinding | null,
): Promise<RuntimeGoalMutationResult> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(`${API_BASE_POLICY.baseUrl}${endpoint}`, {
    method: "POST",
    headers: withLocalApiAuthHeaders(
      withBackendTruthMutationHeaders(
        {
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-UAA-Idempotency-Key": idempotencyRef,
          "X-UAA-Goal-Approval-Ref": approvalRef,
          ...(submissionRef === null
            ? {}
            : { "X-UAA-Goal-Submission-Ref": submissionRef }),
        },
        binding,
      ),
    ),
    body: JSON.stringify(request),
  });
  const data = (await readJsonSafely(
    response,
  )) as ResultEnvelope<RuntimeGoalMutationResult>;
  const result = data.result ?? data.data;
  const success = data.ok ?? data.success;
  const safeFailureMessage = sanitizeForDisplay(
    extractErrorMessage(
      data,
      "The proof-backed goal mutation failed safely.",
    ),
  );
  if (
    !response.ok ||
    success !== true ||
    !isSafeRuntimeGoalMutationResult(result)
  ) {
    if (response.status === 422) {
      throw new RuntimeGoalMutationValidationError(safeFailureMessage);
    }
    if (
      submissionRef !== null &&
      isDurableGoalMutationTerminalFailure(data.error)
    ) {
      throw new RuntimeGoalMutationTerminalRejectionError(
        safeFailureMessage,
        data.error?.code as string,
      );
    }
    throw new Error(safeFailureMessage);
  }
  return result;
}

const DURABLE_GOAL_MUTATION_VALIDATION_FAILURE_CODES = new Set([
  "GOAL_REQUEST_REF_INVALID",
  "GOAL_STORE_CAPACITY_EXCEEDED",
  "GOAL_JOURNAL_CAPACITY_EXCEEDED",
  "GOAL_COMPLETION_TRUSTED_EVALUATOR_UNAVAILABLE",
  "GOAL_REQUEST_VALIDATION_FAILED",
  "GOAL_MUTATION_APPROVAL_DENIED",
  "GOAL_MUTATION_APPROVAL_REVOKED",
  "GOAL_MUTATION_APPROVAL_EXPIRED",
  "GOAL_MUTATION_APPROVAL_SCOPE_MISMATCH",
  "GOAL_MUTATION_APPROVAL_BINDING_MISMATCH",
]);

function isDurableGoalMutationTerminalFailure(
  error: ResultEnvelope<unknown>["error"],
): boolean {
  if (
    error === undefined ||
    typeof error.code !== "string" ||
    error.retryable !== false
  ) {
    return false;
  }
  return (
    error.category === "not_found" ||
    error.category === "conflict" ||
    error.category === "authorization_error" ||
    (error.category === "validation_error" &&
      DURABLE_GOAL_MUTATION_VALIDATION_FAILURE_CODES.has(error.code))
  );
}

export class RuntimeGoalMutationValidationError extends Error {
  readonly deterministicClientOnlyRejection = true;

  constructor(message: string) {
    super(message);
    this.name = "RuntimeGoalMutationValidationError";
  }
}

export function isRuntimeGoalMutationValidationError(
  error: unknown,
): error is RuntimeGoalMutationValidationError {
  return (
    error instanceof RuntimeGoalMutationValidationError &&
    error.deterministicClientOnlyRejection
  );
}

export class RuntimeGoalMutationTerminalRejectionError extends Error {
  readonly durableSubmissionRejected = true;
  readonly code: string;

  constructor(message: string, code: string) {
    super(message);
    this.name = "RuntimeGoalMutationTerminalRejectionError";
    this.code = code;
  }
}

export function isRuntimeGoalMutationTerminalRejectionError(
  error: unknown,
): error is RuntimeGoalMutationTerminalRejectionError {
  return (
    error instanceof RuntimeGoalMutationTerminalRejectionError &&
    error.durableSubmissionRejected
  );
}

export async function createRuntimeGoal(
  request: RuntimeGoalCreateRequest,
  idempotencyRef: string,
  approvalRef: string,
  binding: BackendTruthReadBinding | null,
  submissionRef: string | null = null,
): Promise<RuntimeGoalMutationResult> {
  return postRuntimeGoalMutation(
    API_ENDPOINTS.runtimeGoals,
    request,
    idempotencyRef,
    approvalRef,
    submissionRef,
    binding,
  );
}

export async function editRuntimeGoal(
  goalRef: string,
  request: RuntimeGoalEditRequest,
  idempotencyRef: string,
  approvalRef: string,
  binding: BackendTruthReadBinding | null,
  submissionRef: string | null = null,
): Promise<RuntimeGoalMutationResult> {
  return postRuntimeGoalMutation(
    runtimeGoalEditEndpoint(goalRef),
    request,
    idempotencyRef,
    approvalRef,
    submissionRef,
    binding,
  );
}

export async function transitionRuntimeGoal(
  goalRef: string,
  request: RuntimeGoalTransitionRequest,
  idempotencyRef: string,
  approvalRef: string,
  binding: BackendTruthReadBinding | null,
  submissionRef: string | null = null,
): Promise<RuntimeGoalMutationResult> {
  return postRuntimeGoalMutation(
    runtimeGoalTransitionEndpoint(goalRef),
    request,
    idempotencyRef,
    approvalRef,
    submissionRef,
    binding,
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
    value.route_ref === "GET /api/runtime/streaming-progress" &&
    value.replay_route_ref ===
      "GET /api/runtime/streaming-progress?transport=sse" &&
    value.cli_ref === "uaa runtime inspect-streaming-progress" &&
    value.replay_cli_ref === "uaa runtime inspect-streaming-progress --replay-sse" &&
    isSafeTrustAuthorityRef(value.snapshot_ref) &&
    isSafeTrustAuthorityRef(value.snapshot_hash_ref) &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-streaming-progress-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    TRUST_AUTHORITY_DECISION_OUTCOMES.includes(
      value.authority_state_decision_outcome,
    ) &&
    typeof value.authority_state_status === "string" &&
    value.authority_state_status.length > 0 &&
    typeof value.authority_state_operator_message === "string" &&
    value.authority_state_operator_message.length > 0 &&
    isNonEmptyStringArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    isNonEmptyStringArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:runtime-streaming-progress-live-sse:not-implemented",
    ) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.stream_state === "stale_disconnected" &&
    value.stale_stream === true &&
    value.readonly_sse_replay_enabled === true &&
    value.readonly_sse_replay_source_posture ===
      "deterministic_redacted_preview" &&
    value.readonly_sse_replay_durable_event_source === false &&
    value.readonly_sse_replay_requires_run_ref === true &&
    value.readonly_sse_replay_resume_supported === true &&
    value.readonly_sse_replay_control_messages_accepted === false &&
    value.readonly_sse_replay_mutation_enabled === false &&
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
    value.snapshot_ref ===
      "runtime-profile-isolation-snapshot-ref:uaa:metadata-only" &&
    isSafeTrustAuthorityRef(value.snapshot_hash_ref) &&
    value.route_ref === "GET /api/runtime/profiles" &&
    value.cli_ref === "uaa runtime inspect-profiles" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-profile-isolation-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    TRUST_AUTHORITY_DECISION_OUTCOMES.includes(
      value.authority_state_decision_outcome,
    ) &&
    typeof value.authority_state_status === "string" &&
    value.authority_state_status.length > 0 &&
    typeof value.authority_state_operator_message === "string" &&
    value.authority_state_operator_message.length > 0 &&
    isNonEmptyStringArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    isNonEmptyStringArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:runtime-profile-provider-call:not-implemented",
    ) &&
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
    !isPlainRecord(value.fail_closed_timeout_posture) ||
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
  const failClosedPosture = value.fail_closed_timeout_posture;
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
    value.route_ref === "GET /api/runtime/approval-bridge" &&
    value.cli_ref === "uaa runtime inspect-approval-bridge" &&
    isSafeTrustAuthorityRef(value.snapshot_ref) &&
    isSafeTrustAuthorityRef(value.snapshot_hash_ref) &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    value.authority_state_mapping_ref ===
      "lane-ref:runtime-approval-bridge-read-model" &&
    isSafeTrustAuthorityRef(value.authority_state_catalog_ref) &&
    isSafeTrustAuthorityRef(value.authority_state_decision_ref) &&
    TRUST_AUTHORITY_DECISION_OUTCOMES.includes(
      value.authority_state_decision_outcome,
    ) &&
    typeof value.authority_state_status === "string" &&
    value.authority_state_status.length > 0 &&
    typeof value.authority_state_operator_message === "string" &&
    value.authority_state_operator_message.length > 0 &&
    isNonEmptyStringArray(value.authority_state_reason_refs) &&
    value.authority_state_reason_refs.every(isSafeTrustAuthorityRef) &&
    isNonEmptyStringArray(value.unsupported_adapter_refs) &&
    value.unsupported_adapter_refs.includes(
      "adapter-ref:runtime-approval-resolution-send:not-implemented",
    ) &&
    value.unsupported_adapter_refs.every(isSafeTrustAuthorityRef) &&
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
    failClosedPosture.expired_waits_default_to_deny === true &&
    failClosedPosture.ambiguous_waits_default_to_deny === true &&
    failClosedPosture.explicit_expiration_required === true &&
    failClosedPosture.revoke_required === true &&
    failClosedPosture.safe_disable_required === true &&
    failClosedPosture.auto_approve_enabled === false &&
    failClosedPosture.approve_all_enabled === false &&
    failClosedPosture.standing_broad_authority_enabled === false &&
    failClosedPosture.expired_grant_reuse_enabled === false &&
    failClosedPosture.ambiguous_grant_enabled === false &&
    failClosedPosture.approval_resolution_sent === false &&
    failClosedPosture.control_center_mints_authority === false &&
    isNonEmptyStringArray(failClosedPosture.blocked_authority_refs) &&
    isNonEmptyStringArray(failClosedPosture.promotion_path_refs) &&
    isNonEmptyStringArray(failClosedPosture.next_safe_action_refs) &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    failClosedPosture.blocked_authority_refs.every((ref) =>
      value.blocked_authority_refs.includes(ref),
    ) &&
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
    isSafeCodingPairAgentRelay(value.pair_agent_relay) &&
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

function isSafeCodingPairAgentRelay(
  value: CodingMultiAgentReviewReadModel["pair_agent_relay"] | undefined,
): boolean {
  if (value === undefined) {
    return false;
  }
  const deniedFlags: Array<
    keyof CodingMultiAgentReviewReadModel["pair_agent_relay"]
  > = [
    "execution_promoted",
    "foreground_adapter_execution_enabled",
    "local_agent_process_execution_enabled",
    "provider_sdk_call_enabled",
    "provider_model_call_enabled",
    "background_dispatch_enabled",
    "generic_agent_bus_enabled",
    "arbitrary_command_text_allowed",
    "shell_subprocess_execution_enabled",
    "plugin_runtime_import_enabled",
    "browser_automation_enabled",
    "connector_write_enabled",
    "git_mutation_enabled",
    "automatic_patch_apply_enabled",
    "raw_transcript_durable",
    "raw_prompt_persisted",
    "raw_response_persisted",
    "provider_payload_persisted",
    "raw_log_persisted",
    "raw_local_path_persisted",
    "production_authority_enabled",
    "broad_autonomy_enabled",
  ];
  const refGroups = [
    value.backend_route_refs,
    value.frontend_route_refs,
    value.cli_inspection_refs,
    value.docs_refs,
    value.verifier_refs,
    value.unblock_prompt_refs,
    value.artifact_refs,
    value.receipt_refs,
    value.evidence_refs,
    value.proof_refs,
    value.blocked_authority_refs,
    value.promotion_path_refs,
    value.redactions_applied,
    value.run_contract?.workspace_scope_refs,
    value.run_contract?.stop_condition_refs,
    value.run_contract?.approval_binding_refs,
  ];
  const safeSlots =
    Array.isArray(value.run_contract?.agent_slots) &&
    value.run_contract.agent_slots.length === 2 &&
    value.run_contract.agent_slots.every(
      (slot) =>
        isNonEmptyStringArray(slot.argv_template_refs) &&
        isNonEmptyStringArray(slot.allowed_workspace_refs) &&
        isNonEmptyStringArray(slot.blocked_authority_refs) &&
        slot.arbitrary_command_text_allowed === false &&
        slot.local_agent_process_execution_enabled === false &&
        slot.provider_sdk_call_enabled === false &&
        slot.provider_model_call_enabled === false &&
        slot.background_dispatch_enabled === false &&
        slot.raw_env_persisted === false &&
        slot.raw_prompt_persisted === false &&
        slot.raw_response_persisted === false,
    );
  const safeArtifacts =
    Array.isArray(value.artifacts) &&
    value.artifacts.length >= 7 &&
    value.artifacts.every(
      (artifact) =>
        artifact.raw_content_omitted === true &&
        artifact.raw_prompt_omitted === true &&
        artifact.raw_response_omitted === true &&
        artifact.provider_payload_omitted === true &&
        artifact.raw_log_omitted === true &&
        artifact.raw_local_path_omitted === true &&
        artifact.durable_evidence === false,
    );
  const safeReceipts =
    Array.isArray(value.receipts) &&
    value.receipts.length >= 9 &&
    value.receipts.every(
      (receipt) =>
        receipt.raw_content_included === false &&
        receipt.portable_receipt_ready === true,
    );
  return (
    value.schema_version === "uaa-coding-pair-agent-relay-runner.v1" &&
    value.canonical_lane_name === "coding_pair_agent_foreground_relay_runner" &&
    value.status === "preview_readiness_execution_blocked" &&
    value.backend_owned === true &&
    value.preview_only === true &&
    value.readiness_only === true &&
    value.safe_refs_only === true &&
    value.run_contract?.state === "blocked" &&
    value.run_contract.max_turns <= 12 &&
    value.run_contract.wall_clock_timeout_seconds <= 3600 &&
    value.run_contract.per_turn_output_limit_bytes <= 20000 &&
    value.run_contract.background_dispatch_enabled === false &&
    value.run_contract.unbounded_turns_enabled === false &&
    value.run_contract.unbounded_timeout_enabled === false &&
    value.run_contract.unbounded_output_enabled === false &&
    value.run_contract.arbitrary_command_text_allowed === false &&
    refGroups.every(isNonEmptyStringArray) &&
    deniedFlags.every((flag) => value[flag] === false) &&
    safeSlots &&
    safeArtifacts &&
    safeReceipts
  );
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
    value.reasoning_truth?.schema_version ===
      "uaa-intent-reasoning-truth.v1" &&
    value.reasoning_truth?.contract_ref ===
      "contract-ref:intent-reasoning-truth:v1" &&
    value.reasoning_truth?.backend_owned === true &&
    value.reasoning_truth?.safe_refs_only === true &&
    value.reasoning_truth?.raw_content_included === false &&
    value.reasoning_truth?.authority_posture ===
      "non_authoritative_review_truth" &&
    value.reasoning_truth?.model_assistance_posture === "deterministic_only" &&
    typeof value.reasoning_truth?.intent_ref === "string" &&
    typeof value.reasoning_truth?.intent_fingerprint_ref === "string" &&
    typeof value.reasoning_truth?.request_fingerprint_ref === "string" &&
    [
      "answer_directly",
      "base_answer",
      "answer_with_reviewed_memory",
      "draft_or_plan",
      "prepare_tool_or_action",
      "approval_required",
      "execute_approved_action",
      "ask_clarifying_question",
      "blocked_unsafe",
    ].includes(value.reasoning_truth.turn_contract) &&
    Array.isArray(value.reasoning_truth?.facts) &&
    value.reasoning_truth.facts.length > 0 &&
    value.reasoning_truth.facts.every(
      (item) =>
        item.kind === "fact" &&
        typeof item.statement_ref === "string" &&
        typeof item.safe_summary === "string" &&
        isNonEmptyStringArray(item.source_refs) &&
        isNonEmptyStringArray(item.evidence_refs),
    ) &&
    Array.isArray(value.reasoning_truth?.assumptions) &&
    value.reasoning_truth.assumptions.every(
      (item) =>
        item.kind === "assumption" &&
        item.review_required === true &&
        typeof item.statement_ref === "string",
    ) &&
    Array.isArray(value.reasoning_truth?.unknowns) &&
    value.reasoning_truth.unknowns.every(
      (item) =>
        item.kind === "unknown" &&
        item.review_required === true &&
        typeof item.statement_ref === "string",
    ) &&
    Array.isArray(value.reasoning_truth?.operator_questions) &&
    value.reasoning_truth.operator_questions.every(
      (item) =>
        typeof item.question_ref === "string" &&
        typeof item.safe_question === "string" &&
        isNonEmptyStringArray(item.resolves_refs),
    ) &&
    ((value.reasoning_truth.confidence_band !== "low" &&
      value.reasoning_truth.confidence_band !== "conflicting" &&
      value.reasoning_truth.ambiguity_posture === "clear") ||
      value.reasoning_truth.operator_questions.length > 0) &&
    isNonEmptyStringArray(value.reasoning_truth?.blocked_authority_refs) &&
    value.plan_revision?.schema_version === "uaa-plan-revision.v1" &&
    value.plan_revision?.authority_posture ===
      "non_authoritative_plan_truth" &&
    value.plan_revision?.downstream_authority_bindings_invalidated === true &&
    typeof value.plan_revision?.revision_fingerprint_ref === "string" &&
    value.plan_revision?.decomposition?.schema_version ===
      "uaa-immutable-decomposition.v1" &&
    value.plan_revision.decomposition.intent_fingerprint_ref ===
      value.reasoning_truth.intent_fingerprint_ref &&
    typeof value.plan_revision.decomposition.decomposition_fingerprint_ref ===
      "string" &&
    Array.isArray(value.plan_revision.decomposition.ordered_steps) &&
    value.plan_revision.decomposition.ordered_steps.length > 0 &&
    value.plan_revision.decomposition.ordered_steps.every(
      (step) =>
        typeof step.step_ref === "string" &&
        typeof step.definition_fingerprint_ref === "string" &&
        isNonEmptyStringArray(step.target_refs) &&
        isNonEmptyStringArray(step.source_refs) &&
        Array.isArray(step.dependency_step_refs),
    ) &&
    Array.isArray(value.plan?.steps) &&
    Array.isArray(value.proposed_actions) &&
    Array.isArray(value.evidence?.evidence_refs) &&
    Array.isArray(value.memory_review?.candidate_refs) &&
    value.high_maturity_spine_readiness?.backend_owned === true &&
    value.high_maturity_spine_readiness?.local_read_model_only === true &&
    value.high_maturity_spine_readiness?.safe_refs_only === true &&
    value.high_maturity_spine_readiness?.raw_content_included === false &&
    value.high_maturity_spine_readiness?.contract_ref ===
      "contract-ref:high-maturity-agent-spine-coverage:v1" &&
    Array.isArray(value.high_maturity_spine_readiness?.rows) &&
    value.high_maturity_spine_readiness.rows.length === 13 &&
    value.high_maturity_spine_readiness.rows.every(
      (row) =>
        typeof row.weakness_id === "string" &&
        row.safe_refs_only === true &&
        row.authority_broadened === false &&
        row.runtime_model_calls_added === false &&
        row.provider_sdk_calls_added === false &&
        row.live_web_fetching_added === false &&
        row.browser_automation_added === false &&
        row.connector_writes_added === false &&
        row.unrestricted_shell_added === false &&
        row.plugin_runtime_import_added === false &&
        row.production_authority_added === false &&
        Array.isArray(row.evidence_refs) &&
        row.evidence_refs.length > 0 &&
        Array.isArray(row.test_refs) &&
        row.test_refs.length > 0,
    ) &&
    isSafeExternalInformationHandling(
      value.high_maturity_spine_readiness.external_information_handling,
    ) &&
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
    value.authority_posture?.unrestricted_live_web_fetching_enabled === false &&
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

const WEB_HYBRID_SAFE_REF_RE = /^[a-z][a-z0-9_-]*(?::[a-z0-9][a-z0-9_.-]*)+$/;
const WEB_HYBRID_CODE_RE = /^[A-Z][A-Z0-9_]*$/;
const WEB_HYBRID_UNSAFE_TEXT_RE =
  /(?:(?:^|\s)\/(?:Users|home|private|var)\/|[a-z]:\\|\b(?:file|https?):\/\/|<(?:html|body|script)\b|raw[_ -]?(?:prompt|response|page|payload|log)|provider[_ -]?payload|api[_-]?key|token\x3d)/i;
const WEB_HYBRID_LANE_CONTRACTS: Record<
  string,
  {
    capability_ref: string;
    provider_ref: string;
    adapter_ref: string;
    runtime_availability: string;
    approval_posture: string;
    cost_posture: string;
  }
> = {
  "authority-lane-ref:web-access:searxng-search:v1": {
    capability_ref: "capability-ref:web-access:searxng-search",
    provider_ref: "provider-ref:searxng:self-hosted",
    adapter_ref: "adapter-ref:web-access:searxng-search:v1",
    runtime_availability: "requires_current_loopback_observation",
    approval_posture: "exact_local_approval_and_lease_required",
    cost_posture: "not_metered",
  },
  "authority-lane-ref:web-access:firecrawl-markdown-extract:v1": {
    capability_ref: "capability-ref:web-access:firecrawl-markdown-extract",
    provider_ref: "provider-ref:firecrawl:self-hosted",
    adapter_ref: "adapter-ref:web-access:firecrawl-markdown-extract:v1",
    runtime_availability: "requires_current_loopback_observation",
    approval_posture: "exact_local_approval_and_lease_required",
    cost_posture: "not_metered",
  },
  "web-lane-ref:firecrawl-cloud-markdown:v1": {
    capability_ref: "capability-ref:web-access:firecrawl-cloud-markdown:v1",
    provider_ref: "web-provider-ref:firecrawl-cloud",
    adapter_ref: "web-adapter-ref:firecrawl-cloud-markdown:v1",
    runtime_availability: "requires_credential_and_current_credit_snapshot",
    approval_posture: "exact_approval_lease_budget_and_reservation_required",
    cost_posture: "metered_free_plan_only",
  },
};

function isSafeWebHybridText(value: unknown, maxLength: number): value is string {
  return (
    typeof value === "string" &&
    value.length > 0 &&
    value.length <= maxLength &&
    !containsSecretLike(value) &&
    !WEB_HYBRID_UNSAFE_TEXT_RE.test(value)
  );
}

const EXTERNAL_INFORMATION_LANE_COUNTS: Record<string, number> = {
  trusted_local_evidence: 0,
  operator_supplied_external_metadata: 0,
  allowlisted_gateway_preview: 1,
  untrusted_content_quarantine: 0,
  browser_observe: 0,
  browser_action: 0,
  provider_search_scrape: 3,
  external_content_authority_isolation: 0,
};

function isSafeExternalInformationStringArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.every((item) => isSafeWebHybridText(item, 700))
  );
}

function isSafeNonEmptyExternalInformationStringArray(
  value: unknown,
): value is string[] {
  return (
    isSafeExternalInformationStringArray(value) && value.length > 0
  );
}

function isSafeExternalInformationHandling(value: unknown): boolean {
  if (!isPlainRecord(value) || !Array.isArray(value.rows)) {
    return false;
  }
  const expectedCategoryIds = Object.keys(EXTERNAL_INFORMATION_LANE_COUNTS);
  if (
    value.schema_version !== "external_information_handling_posture.v1" ||
    value.contract_ref !==
      "contract-ref:external-information-handling-posture:v1" ||
    value.status !== "implemented_read_only_posture_map_existing_lanes_only" ||
    value.source !== "python_core_agent_loop_thread_read_model" ||
    value.route_ref !== "GET /control-center/agent-loop/thread" ||
    value.cli_ref !==
      "scripts/dev/uaa_founder_loop.py inspect-high-maturity-spine" ||
    value.backend_owned !== true ||
    value.local_read_model_only !== true ||
    value.safe_refs_only !== true ||
    value.raw_content_included !== false ||
    value.category_count !== expectedCategoryIds.length ||
    value.implemented_or_blocked_count !== expectedCategoryIds.length ||
    value.existing_exact_network_lane_count !== 4 ||
    value.rows.length !== expectedCategoryIds.length ||
    value.new_live_web_fetching_added !== false ||
    value.browser_observe_enabled !== false ||
    value.browser_action_execution_enabled !== false ||
    value.provider_search_enabled !== false ||
    value.exact_bounded_provider_lanes_implemented !== true ||
    value.provider_sdk_calls_added !== false ||
    value.connector_writes_added !== false ||
    value.memory_writes_added !== false ||
    value.context_injection_added !== false ||
    value.production_authority_added !== false ||
    !isSafeWebHybridText(value.safe_summary, 700) ||
    !isSafeNonEmptyExternalInformationStringArray(value.blocked_authority_refs) ||
    !isSafeNonEmptyExternalInformationStringArray(value.redactions_applied)
  ) {
    return false;
  }
  if (
    !hasExactStringSet(
      value.rows.map((row) =>
        isPlainRecord(row) ? row.category_id : undefined,
      ),
      expectedCategoryIds,
    )
  ) {
    return false;
  }
  return value.rows.every((row) => {
    if (!isPlainRecord(row) || typeof row.category_id !== "string") {
      return false;
    }
    const expectedLaneCount = EXTERNAL_INFORMATION_LANE_COUNTS[row.category_id];
    return (
      expectedLaneCount !== undefined &&
      row.exact_network_lane_count === expectedLaneCount &&
      row.existing_exact_network_lane === (expectedLaneCount > 0) &&
      isSafeWebHybridText(row.label, 160) &&
      isSafeWebHybridText(row.status, 160) &&
      isSafeWebHybridText(row.network_posture, 160) &&
      isSafeWebHybridText(row.authority_posture, 160) &&
      isSafeWebHybridText(row.safe_summary, 700) &&
      isSafeExternalInformationStringArray(row.route_refs) &&
      isSafeExternalInformationStringArray(row.cli_refs) &&
      isSafeNonEmptyExternalInformationStringArray(row.evidence_refs) &&
      isSafeNonEmptyExternalInformationStringArray(row.test_refs) &&
      isSafeNonEmptyExternalInformationStringArray(row.blocked_authority_refs) &&
      typeof row.authority_required === "boolean" &&
      row.policy_decision_required === true &&
      typeof row.receipt_required === "boolean" &&
      row.safe_refs_only === true &&
      row.raw_content_included === false &&
      row.untrusted_content_can_instruct_agent === false &&
      row.external_content_can_grant_authority === false &&
      row.new_live_web_fetching_added === false &&
      row.browser_observe_enabled === false &&
      row.browser_action_execution_enabled === false &&
      row.provider_search_enabled === false &&
      row.provider_sdk_calls_added === false &&
      row.connector_writes_added === false &&
      row.memory_writes_added === false &&
      row.context_injection_added === false &&
      row.production_authority_added === false
    );
  });
}

function isSafeWebHybridRef(value: unknown): value is string {
  return typeof value === "string" && WEB_HYBRID_SAFE_REF_RE.test(value);
}

function isSafeWebHybridRefArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.length > 0 && value.every(isSafeWebHybridRef);
}

function isSafeWebHybridCodeArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.length > 0 &&
    value.every(
      (item) => typeof item === "string" && WEB_HYBRID_CODE_RE.test(item),
    )
  );
}

function isSafeWebHybridLane(value: unknown): boolean {
  if (!isPlainRecord(value) || !isSafeWebHybridRef(value.lane_ref)) {
    return false;
  }
  const expected = WEB_HYBRID_LANE_CONTRACTS[value.lane_ref];
  return Boolean(
    expected &&
      value.capability_ref === expected.capability_ref &&
      value.provider_ref === expected.provider_ref &&
      value.adapter_ref === expected.adapter_ref &&
      value.runtime_availability === expected.runtime_availability &&
      value.approval_posture === expected.approval_posture &&
      value.cost_posture === expected.cost_posture &&
      value.implementation_status === "implemented_exact_lane" &&
      value.side_effect_class === "read_only_external" &&
      value.authority_posture === "request_scoped_evaluation_required" &&
      isSafeWebHybridText(value.display_label, 120) &&
      isSafeWebHybridCodeArray(value.reason_codes) &&
      isSafeWebHybridCodeArray(value.blocker_codes),
  );
}

const CAPABILITY_MATURITY_BASELINE_SOURCE_REF =
  "repo-ref:uaa:docs/benchmarks/runtime_capability_foundation/goat_comparison_20260712.json:initial_scores.uaa.components";
const CAPABILITY_MATURITY_BASELINE_FINGERPRINT_REF =
  "fingerprint-ref:capability-maturity-baseline:sha256:4ab2d2160e97df5a823e092445e6725aa8714e14066a34c2baabc46be17366cd";
const CAPABILITY_MATURITY_COMPONENTS = [
  ["reasoning_task_understanding", 8, 8],
  ["planning_orchestration", 10, 8],
  ["learning_adaptation", 8, 8],
  ["memory_context_management", 9, 9],
  ["communication_interaction", 8, 7],
  ["action_tool_calling", 9, 9],
  ["autonomy_authority", 10, 10],
  ["code_implementation_assistance", 8, 6],
  ["research_web_external", 10, 5],
  ["model_provider_management", 8, 6],
  ["evidence_audit_observability", 9, 9],
  ["safety_security_failure", 10, 10],
  ["ux_ai_cockpit", 8, 7],
  ["cli_api_parity", 9, 6],
  ["extensibility_ecosystem", 7, 6],
  ["productized_agent_loop", 8, 10],
] as const;
const CAPABILITY_MATURITY_GATE_KINDS = [
  "implementation",
  "automated_tests",
  "runtime_scenario",
  "operator_surface",
  "recovery_and_failure",
  "independent_acceptance",
] as const;

function maturityWeightedScore(
  components: Record<string, unknown>[],
  scoreKey: "baseline_score" | "target_score" | "verified_score",
): number {
  const weighted = components.reduce(
    (total, component, index) =>
      total + Number(component[scoreKey]) * CAPABILITY_MATURITY_COMPONENTS[index][2],
    0,
  );
  return Math.round((weighted / 1240) * 1000) / 10;
}

function isSafeCapabilityMaturity(value: unknown): boolean {
  if (!isPlainRecord(value) || !Array.isArray(value.components)) {
    return false;
  }
  const components = value.components;
  const shapeIsSafe = (
    value.schema_version === "uaa-capability-maturity.v1" &&
    value.contract_ref === "contract-ref:capability-maturity:v1" &&
    value.baseline_source_ref === CAPABILITY_MATURITY_BASELINE_SOURCE_REF &&
    value.baseline_source_fingerprint_ref ===
      CAPABILITY_MATURITY_BASELINE_FINGERPRINT_REF &&
    value.backend_owned === true &&
    value.read_only === true &&
    value.content_free === true &&
    value.authority_granted === false &&
    value.score_increase_requires_runtime_evidence === true &&
    value.score_increase_requires_independent_acceptance === true &&
    value.trusted_acceptance_verification_implemented === false &&
    value.raw_content_persisted === false &&
    isSafeEvidenceNarrativeText(value.safe_summary) &&
    value.component_count === 16 &&
    components.length === CAPABILITY_MATURITY_COMPONENTS.length &&
    components.every(
      (component, index) =>
        isPlainRecord(component) &&
        component.component_id === CAPABILITY_MATURITY_COMPONENTS[index][0] &&
        typeof component.label === "string" &&
        component.weight === CAPABILITY_MATURITY_COMPONENTS[index][2] &&
        component.baseline_score === CAPABILITY_MATURITY_COMPONENTS[index][1] &&
        typeof component.target_score === "number" &&
        typeof component.verified_score === "number" &&
        component.target_score ===
          Math.min(10, Number(component.baseline_score) + 1) &&
        component.verified_score === component.baseline_score &&
        [
          "baseline_only",
          "automated_evidence_ready",
          "manual_validation_required",
          "external_dependency_required",
          "target_proven",
          "ceiling_defended",
          "evidence_failed",
        ].includes(
          String(component.evidence_status),
        ) &&
        !["target_proven", "ceiling_defended"].includes(
          String(component.evidence_status),
        ) &&
        Array.isArray(component.scenario_refs) &&
        Array.isArray(component.evidence_refs) &&
        component.evidence_refs.length >= 3 &&
        Array.isArray(component.gates) &&
        component.gates.length === CAPABILITY_MATURITY_GATE_KINDS.length &&
        component.gates.every(
          (gate, gateIndex) =>
            isPlainRecord(gate) &&
            gate.gate_kind === CAPABILITY_MATURITY_GATE_KINDS[gateIndex] &&
            ["satisfied", "pending", "blocked"].includes(String(gate.status)) &&
            Array.isArray(gate.evidence_refs) &&
            Array.isArray(gate.blocker_codes) &&
            (gate.status === "satisfied"
              ? gate.evidence_refs.length > 0
              : gate.blocker_codes.length > 0) &&
            isSafeEvidenceNarrativeText(gate.safe_summary),
        ) &&
        Array.isArray(component.blocker_codes) &&
        typeof component.next_acceptance_ref === "string" &&
        isSafeEvidenceNarrativeText(component.safe_summary),
    )
  );
  if (!shapeIsSafe) {
    return false;
  }

  const typedComponents = components as Record<string, unknown>[];
  const statusCount = (status: string) =>
    typedComponents.filter((component) => component.evidence_status === status).length;
  const upliftProven = statusCount("target_proven");
  const ceilingDefended = statusCount("ceiling_defended");
  const automatedReady = typedComponents.filter((component) =>
    [
      "automated_evidence_ready",
      "manual_validation_required",
      "external_dependency_required",
      "target_proven",
    ].includes(String(component.evidence_status)),
  ).length;
  const anyFailed = statusCount("evidence_failed") > 0;
  const expectedPosture = upliftProven === 12
    ? "targets_proven"
    : anyFailed
      ? "evaluation_failed"
      : upliftProven
        ? "partially_graduated"
      : automatedReady
        ? "automated_evidence_ready"
        : "evaluation_required";

  return (
    value.baseline_weighted_score ===
      maturityWeightedScore(typedComponents, "baseline_score") &&
    value.target_weighted_score ===
      maturityWeightedScore(typedComponents, "target_score") &&
    value.verified_weighted_score ===
      maturityWeightedScore(typedComponents, "verified_score") &&
    value.uplift_target_count === 12 &&
    value.uplift_proven_count === upliftProven &&
    value.automated_evidence_ready_count === automatedReady &&
    value.manual_validation_required_count ===
      statusCount("manual_validation_required") &&
    value.external_dependency_required_count ===
      statusCount("external_dependency_required") &&
    value.ceiling_defended_count === ceilingDefended &&
    value.verification_posture === expectedPosture
  );
}

function isSafeControlCenterCapabilitySurface(
  value: unknown,
): value is ControlCenterCapabilitySurfaceReadModel {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    value.schema_version ===
      "control-center-capability-surface-read-model.v1" &&
    value.source === "python_core_control_center_capability_surface_read_model" &&
    value.backend_owned === true &&
    value.read_only === true &&
    value.safe_refs_only === true &&
    value.raw_manifest_dump_included === false &&
    value.runtime_authority_added === false &&
    value.public_beta_claim_enabled === false &&
    value.production_readiness_claim_enabled === false &&
    value.route_ref === "GET /control-center/capabilities/surface" &&
    typeof value.cli_ref === "string" &&
    isPlainRecord(value.summary) &&
    Array.isArray(value.rows) &&
    value.rows.length > 0 &&
    value.rows.every(
      (row) =>
        isPlainRecord(row) &&
        typeof row.capability_id === "string" &&
        typeof row.label === "string" &&
        typeof row.status === "string" &&
        typeof row.authority_posture === "string" &&
        typeof row.missing_reason === "string" &&
        Array.isArray(row.api_routes) &&
        Array.isArray(row.ui_routes) &&
        Array.isArray(row.control_action_ids) &&
        Array.isArray(row.cli_paths) &&
        Array.isArray(row.tests_evidence_refs),
    ) &&
    isSafeCapabilityMaturity(value.maturity) &&
    isPlainRecord(value.web_hybrid) &&
    value.web_hybrid.schema_version === "uaa-web-hybrid-availability.v1" &&
    value.web_hybrid.truth_owner === "python_core" &&
    value.web_hybrid.status === "implemented_runtime_observation_required" &&
    isSafeWebHybridRef(value.web_hybrid.read_model_ref) &&
    isSafeWebHybridRef(value.web_hybrid.cli_ref) &&
    value.web_hybrid.cli_path === "scripts/inspect_web_hybrid_status.py" &&
    value.web_hybrid.routing_policy ===
      "self_host_first_cloud_escalation" &&
    value.web_hybrid.routing_attempt_ceiling === 2 &&
    value.web_hybrid.cloud_first_enabled === false &&
    value.web_hybrid.paid_usage_enabled === false &&
    value.web_hybrid.keyless_enabled === false &&
    value.web_hybrid.provider_zero_data_retention_claimed === false &&
    value.web_hybrid.current_credit_snapshot_status ===
      "not_observed_by_read_only_route" &&
    value.web_hybrid.current_remaining_credits === null &&
    value.web_hybrid.reviewed_free_plan_credits === 1000 &&
    value.web_hybrid.reviewed_free_plan_concurrency === 2 &&
    value.web_hybrid.uaa_effective_cloud_concurrency === 1 &&
    value.web_hybrid.reviewed_standard_scrape_credits === 1 &&
    isSafeWebHybridRef(value.web_hybrid.cost_policy_ref) &&
    isSafeWebHybridRef(value.web_hybrid.credential_ref) &&
    value.web_hybrid.circuit_state === "unknown_until_runtime_inspection" &&
    isSafeWebHybridRef(value.web_hybrid.circuit_ref) &&
    value.web_hybrid.request_scoped_evaluation_required === true &&
    value.web_hybrid.final_start_revalidation_required === true &&
    value.web_hybrid.mission_scoped_lease_required === true &&
    value.web_hybrid.complete_request_fingerprint_required === true &&
    value.web_hybrid.start_deadline_required === true &&
    value.web_hybrid.local_approval_required === true &&
    value.web_hybrid.exact_authority_lease_required === true &&
    value.web_hybrid.budget_reservation_required_for_cloud === true &&
    value.web_hybrid.external_content_untrusted === true &&
    value.web_hybrid.instruction_authority_granted === false &&
    value.web_hybrid.memory_write_allowed === false &&
    value.web_hybrid.context_injection_allowed === false &&
    value.web_hybrid.browser_actions_allowed === false &&
    value.web_hybrid.raw_page_persisted === false &&
    value.web_hybrid.raw_provider_payload_persisted === false &&
    value.web_hybrid.credential_material_returned === false &&
    value.web_hybrid.provider_network_call_performed === false &&
    isSafeWebHybridRefArray(value.web_hybrid.proof_refs) &&
    isSafeWebHybridCodeArray(value.web_hybrid.blocker_codes) &&
    isSafeWebHybridText(value.web_hybrid.safe_summary, 700) &&
    isPlainRecord(value.web_hybrid.research_aggregation) &&
    value.web_hybrid.research_aggregation.schema_version ===
      "uaa-web-research-aggregation-posture.v1" &&
    value.web_hybrid.research_aggregation.status ===
      "implemented_injected_observations_required" &&
    value.web_hybrid.research_aggregation.current_observation_status ===
      "not_injected_by_read_only_route" &&
    value.web_hybrid.research_aggregation.current_citation_count === 0 &&
    value.web_hybrid.research_aggregation.citation_limit === 10 &&
    value.web_hybrid.research_aggregation.summary_character_limit === 4000 &&
    value.web_hybrid.research_aggregation.deterministic_injected_observations_only ===
      true &&
    value.web_hybrid.research_aggregation.provider_readiness_included === true &&
    value.web_hybrid.research_aggregation.provider_latency_posture_included === true &&
    value.web_hybrid.research_aggregation.provider_cost_posture_included === true &&
    value.web_hybrid.research_aggregation.provider_context_posture_included === true &&
    value.web_hybrid.research_aggregation.provider_routing_posture_included === true &&
    value.web_hybrid.research_aggregation.excluded_source_reasons_included === true &&
    value.web_hybrid.research_aggregation.content_untrusted === true &&
    value.web_hybrid.research_aggregation.not_instruction_authority === true &&
    value.web_hybrid.research_aggregation.context_injection_authorized === false &&
    value.web_hybrid.research_aggregation.memory_write_authorized === false &&
    value.web_hybrid.research_aggregation.action_execution_authorized === false &&
    value.web_hybrid.research_aggregation.raw_query_persisted === false &&
    value.web_hybrid.research_aggregation.raw_page_content_persisted === false &&
    value.web_hybrid.research_aggregation.raw_provider_payload_persisted === false &&
    isSafeWebHybridRef(value.web_hybrid.research_aggregation.contract_ref) &&
    isSafeWebHybridText(
      value.web_hybrid.research_aggregation.safe_summary,
      700,
    ) &&
    isSafeWebHybridRefArray(value.web_hybrid.research_aggregation.proof_refs) &&
    isSafeWebHybridCodeArray(value.web_hybrid.research_aggregation.blocker_codes) &&
    Array.isArray(value.web_hybrid.lanes) &&
    value.web_hybrid.lanes.length === 3 &&
    value.web_hybrid.lanes.every(isSafeWebHybridLane) &&
    hasExactStringSet(
      value.web_hybrid.lanes.map((lane) =>
        isPlainRecord(lane) ? lane.lane_ref : undefined,
      ),
      Object.keys(WEB_HYBRID_LANE_CONTRACTS),
    ) &&
    isNonEmptyStringArray(value.blocked_authority_refs) &&
    isNonEmptyStringArray(value.redactions_applied)
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
    blocked: `${input.surfaceLabel} runtime authority requires an active mode/domain AuthorityLease before execution.`,
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

function isSafeControlCenterSettingsStatus(
  value: unknown,
): value is ControlCenterSettingsStatus {
  if (!isPlainRecord(value) || !isPlainRecord(value.authority_lease_state)) {
    return false;
  }
  const authority = value.authority_lease_state;
  const authorityModes = new Set([
    "read_only",
    "ask_before_changes",
    "approved_safe_local_work_session",
    "full_local_workspace_session",
    "full_machine_access_session",
    "delegated_mission_autonomous_window",
  ]);
  return (
    value.schema_version === "uaa-control-center-settings-status.v1" &&
    value.module_id === "settings" &&
    value.status === "read_only_status" &&
    value.route_ref === "GET /control-center/settings/status" &&
    value.proposal_review_only === true &&
    value.settings_mutation_enabled === false &&
    value.settings_toggle_grants_authority === false &&
    value.production_authority_enabled === false &&
    Array.isArray(value.blocked_authorities) &&
    Array.isArray(value.redactions_applied) &&
    authority.schema_version === "uaa-authority-state.v1" &&
    authority.backend_owned === true &&
    typeof authority.active_mode === "string" &&
    authorityModes.has(authority.active_mode) &&
    authority.unknown_authority_default === "deny" &&
    typeof authority.kill_switch_visible === "boolean" &&
    typeof authority.kill_switch_engaged === "boolean" &&
    authority.receipts_required === true &&
    authority.audit_required === true &&
    authority.redaction_required === true &&
    authority.unsupported_adapters_claimed_execution === false
  );
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
  const governedContext = isSafeGovernedMemoryContext(value.governed_context)
    ? value.governed_context
    : undefined;
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
      governed_context: governedContext,
      governed_context_manifest_ref: governedContext?.context_manifest_ref,
      governed_context_receipt_ref: governedContext?.context_receipt_ref,
      governed_context_fingerprint_ref: governedContext?.manifest_fingerprint_ref,
    },
    usedFallback:
      merged.usedFallback ||
      (value.governed_context !== undefined && governedContext === undefined),
  };
}

function isSafeGovernedMemoryContext(
  value: unknown,
): value is GovernedMemoryContextManifest {
  if (!isPlainRecord(value)) return false;
  const selections = Array.isArray(value.selections) ? value.selections : null;
  const exclusions = Array.isArray(value.exclusions) ? value.exclusions : null;
  const budget = isPlainRecord(value.budget) ? value.budget : null;
  if (!selections || !exclusions || !budget) return false;
  const selectionCount = Number(value.selection_count);
  const exclusionCount = Number(value.exclusion_count);
  const candidateCount = Number(value.candidate_count);
  const maxItems = Number(budget.max_items);
  const selectedItems = Number(budget.selected_items);
  const maxTokens = Number(budget.max_tokens);
  const usedTokens = Number(budget.used_tokens);
  const capacityExcludedItems = Number(budget.capacity_excluded_items);
  const hasSafeRefList = (candidate: unknown): candidate is string[] =>
    Array.isArray(candidate) &&
    candidate.length > 0 &&
    candidate.every((ref) => typeof ref === "string" && ref.length > 0);
  const safeSelections = selections.every(
    (item) =>
      isPlainRecord(item) &&
      typeof item.memory_ref === "string" &&
      item.memory_ref.length > 0 &&
      hasSafeRefList(item.source_refs) &&
      hasSafeRefList(item.evidence_refs) &&
      hasSafeRefList(item.receipt_refs) &&
      hasSafeRefList(item.inclusion_reason_refs) &&
      typeof item.confidence_posture_ref === "string" &&
      typeof item.freshness_posture_ref === "string" &&
      typeof item.conflict_posture_ref === "string" &&
      typeof item.sensitivity_posture_ref === "string" &&
      Number.isInteger(Number(item.token_estimate)) &&
      Number(item.token_estimate) > 0,
  );
  const safeExclusions = exclusions.every(
    (item) =>
      isPlainRecord(item) &&
      typeof item.memory_ref === "string" &&
      item.memory_ref.length > 0 &&
      hasSafeRefList(item.reason_refs),
  );
  const selectedRefs = new Set(
    selections
      .filter(isPlainRecord)
      .map((item) => String(item.memory_ref ?? "")),
  );
  const excludedRefs = new Set(
    exclusions
      .filter(isPlainRecord)
      .map((item) => String(item.memory_ref ?? "")),
  );
  const tokenSum = selections.reduce(
    (total, item) =>
      total + (isPlainRecord(item) ? Number(item.token_estimate) : 0),
    0,
  );
  const expectedBudgetStatus =
    selectedItems === 0
      ? "exhausted"
      : capacityExcludedItems > 0 ||
          selectedItems === maxItems ||
          usedTokens === maxTokens
        ? "constrained"
        : "available";
  const requiredBlockedStateRefs = [
    "blocked-state:memory-context-no-hidden-injection",
    "blocked-state:memory-context-no-automatic-memory-truth",
    "blocked-state:memory-context-no-action-authority",
    "blocked-state:memory-context-no-approval-authority",
    "blocked-state:memory-context-no-connector-write",
    "blocked-state:memory-context-no-model-provider-call",
    "blocked-state:memory-context-no-production-authority",
  ];
  const blockedStateRefs = Array.isArray(value.blocked_state_refs)
    ? value.blocked_state_refs
    : [];
  if (
    !Number.isInteger(selectionCount) ||
    !Number.isInteger(exclusionCount) ||
    !Number.isInteger(candidateCount) ||
    !Number.isInteger(maxItems) ||
    maxItems < 1 ||
    !Number.isInteger(maxTokens) ||
    maxTokens < 1 ||
    !Number.isInteger(selectedItems) ||
    selectedItems < 0 ||
    !Number.isInteger(usedTokens) ||
    usedTokens < 0 ||
    selectionCount !== selections.length ||
    exclusionCount !== exclusions.length ||
    candidateCount !== selectionCount + exclusionCount ||
    selectedItems !== selectionCount ||
    selectedItems > maxItems ||
    usedTokens > maxTokens ||
    tokenSum !== usedTokens ||
    !Number.isInteger(capacityExcludedItems) ||
    capacityExcludedItems < 0 ||
    budget.status !== expectedBudgetStatus ||
    value.schema_version !== "governed_memory_context_manifest.v1" ||
    value.contract_ref !== "contract-ref:governed-memory-context-manifest:v1" ||
    value.route_ref !== "GET /control-center/memory/context-manifest" ||
    value.redaction_status !== "safe_refs_only" ||
    !requiredBlockedStateRefs.every((ref) => blockedStateRefs.includes(ref)) ||
    selectedRefs.size !== selections.length ||
    excludedRefs.size !== exclusions.length ||
    (value.status === "ready_for_operator_preview" && selectionCount === 0) ||
    (value.status === "blocked_no_eligible_context" && selectionCount !== 0) ||
    ![
      "ready_for_operator_preview",
      "blocked_no_eligible_context",
    ].includes(String(value.status)) ||
    value.context_receipt_status !== "derived_preview_not_persisted" ||
    typeof value.context_manifest_ref !== "string" ||
    typeof value.manifest_fingerprint_ref !== "string" ||
    typeof value.context_receipt_ref !== "string" ||
    typeof value.query_ref !== "string" ||
    typeof value.checked_at !== "string" ||
    typeof value.source_index_generated_at !== "string" ||
    value.checked_at !== value.source_index_generated_at ||
    typeof value.expires_at !== "string" ||
    Number.isNaN(Date.parse(value.checked_at)) ||
    Number.isNaN(Date.parse(value.expires_at)) ||
    Date.parse(value.expires_at) <= Date.parse(value.checked_at) ||
    !safeSelections ||
    !safeExclusions ||
    [...selectedRefs].some((ref) => excludedRefs.has(ref)) ||
    typeof value.source_scan_truncated !== "boolean" ||
    typeof value.candidate_count_complete !== "boolean" ||
    value.candidate_count_complete === value.source_scan_truncated
  ) {
    return false;
  }
  if (
    value.preview_only !== true ||
    value.context_injection_authorized !== false ||
    value.automatic_memory_inclusion_authorized !== false ||
    value.memory_truth_authority !== false ||
    value.action_execution_authorized !== false ||
    value.approval_authority_granted !== false ||
    value.connector_write_authorized !== false ||
    value.model_provider_authority_allowed !== false ||
    value.raw_content_persisted !== false ||
    value.production_authority_enabled !== false
  ) {
    return false;
  }
  return true;
}

const EXTENSION_SAFE_REF_RE = /^[a-z][a-z0-9_-]*:[a-z0-9][a-z0-9_.:-]*$/;
const EXTENSION_REASON_CODE_RE = /^[A-Z][A-Z0-9_]*$/;

function hasExactStringSet(left: unknown[], right: string[]): boolean {
  const normalizedLeft = left.filter(
    (item): item is string => typeof item === "string",
  );
  return (
    normalizedLeft.length === left.length &&
    new Set(normalizedLeft).size === normalizedLeft.length &&
    new Set(right).size === right.length &&
    normalizedLeft.length === right.length &&
    normalizedLeft.every((item) => right.includes(item)) &&
    right.every((item) => normalizedLeft.includes(item))
  );
}

function isSafePluginGovernanceSummary(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const entries = value.extension_entries;
  if (
    !Array.isArray(entries) ||
    !Array.isArray(value.blocker_codes) ||
    !Array.isArray(value.safe_disable_refs) ||
    !Array.isArray(value.rollback_refs) ||
    !Array.isArray(value.skill_bundle_proposal_refs) ||
    value.status !== "inspectable_non_callable" ||
    value.plugin_enablement_allowed !== false ||
    value.native_build_tools_enabled !== false ||
    value.skill_bundle_proposal_status !== "proposal_only" ||
    value.skill_bundle_activation_enabled !== false ||
    value.skill_bundle_tool_execution_enabled !== false ||
    !Number.isInteger(value.skill_bundle_proposal_count) ||
    Number(value.skill_bundle_proposal_count) !== value.skill_bundle_proposal_refs.length ||
    !Number.isInteger(value.catalog_entry_count) ||
    Number(value.catalog_entry_count) < 0 ||
    !Number.isInteger(value.developer_validation_count) ||
    Number(value.developer_validation_count) < 0 ||
    !Number.isInteger(value.availability_snapshot_count) ||
    Number(value.availability_snapshot_count) < 0 ||
    !Number.isInteger(value.blocked_validation_count) ||
    Number(value.blocked_validation_count) < 0 ||
    Number(value.blocked_validation_count) > Number(value.developer_validation_count) ||
    Number(value.catalog_entry_count) !== entries.length ||
    Number(value.developer_validation_count) !== entries.length ||
    value.catalog_visibility_grants_authority !== false ||
    value.request_scoped_invocation_decision_required !== true ||
    !EXTENSION_SAFE_REF_RE.test(String(value.plugin_metadata_boundary_ref)) ||
    !EXTENSION_SAFE_REF_RE.test(String(value.skill_marketplace_boundary_ref)) ||
    !EXTENSION_SAFE_REF_RE.test(String(value.mcp_catalog_boundary_ref))
  ) {
    return false;
  }
  const safeEntries = entries.every((entry) => {
    if (!isPlainRecord(entry)) {
      return false;
    }
    return (
      EXTENSION_SAFE_REF_RE.test(String(entry.package_ref)) &&
      EXTENSION_SAFE_REF_RE.test(String(entry.manifest_ref)) &&
      EXTENSION_SAFE_REF_RE.test(String(entry.version_ref)) &&
      EXTENSION_SAFE_REF_RE.test(String(entry.safe_disable_ref)) &&
      EXTENSION_SAFE_REF_RE.test(String(entry.rollback_ref)) &&
      Number.isInteger(entry.availability_snapshot_count) &&
      Number(entry.availability_snapshot_count) >= 0 &&
      ["validated_metadata_only", "blocked"].includes(String(entry.validation_status)) &&
      ["supported", "unknown"].includes(String(entry.compatibility_status)) &&
      entry.configuration_status === "not_configured" &&
      entry.health_status === "unknown" &&
      entry.authority_posture === "blocked" &&
      entry.resource_status === "unknown" &&
      entry.safe_disable_status === "unknown" &&
      ["reviewed", "blocked", "unknown"].includes(String(entry.provenance_status)) &&
      typeof entry.hashes_verified_against_pinned_values === "boolean" &&
      ["not_present", "unknown"].includes(String(entry.signature_status)) &&
      entry.signature_verified === false &&
      Array.isArray(entry.blocker_codes) &&
      entry.blocker_codes.every(
        (code) => typeof code === "string" && EXTENSION_REASON_CODE_RE.test(code),
      )
    );
  });
  if (!safeEntries) {
    return false;
  }
  const typedEntries = entries as Array<Record<string, unknown>>;
  const blockedCount = typedEntries.filter(
    (entry) => entry.validation_status === "blocked",
  ).length;
  const availabilityCount = typedEntries.reduce(
    (count, entry) => count + Number(entry.availability_snapshot_count),
    0,
  );
  const safeDisableRefs = typedEntries.map((entry) => String(entry.safe_disable_ref));
  const rollbackRefs = typedEntries.map((entry) => String(entry.rollback_ref));
  const entryBlockerCodes = Array.from(
    new Set(
      typedEntries.flatMap((entry) =>
        (entry.blocker_codes as unknown[]).map((code) => String(code)),
      ),
    ),
  ).sort();
  return (
    Number(value.blocked_validation_count) === blockedCount &&
    Number(value.availability_snapshot_count) === availabilityCount &&
    value.blocker_codes.every(
      (code) => typeof code === "string" && EXTENSION_REASON_CODE_RE.test(code),
    ) &&
    value.skill_bundle_proposal_refs.every(
      (ref) => typeof ref === "string" && EXTENSION_SAFE_REF_RE.test(ref),
    ) &&
    value.safe_disable_refs.every(
      (ref) => typeof ref === "string" && EXTENSION_SAFE_REF_RE.test(ref),
    ) &&
    value.rollback_refs.every(
      (ref) => typeof ref === "string" && EXTENSION_SAFE_REF_RE.test(ref),
    ) &&
    hasExactStringSet(value.safe_disable_refs, safeDisableRefs) &&
    hasExactStringSet(value.rollback_refs, rollbackRefs) &&
    JSON.stringify([...value.blocker_codes].sort()) ===
      JSON.stringify(entryBlockerCodes)
  );
}

function normalizeControlCenterDashboard(
  value: ControlCenterDashboardSnapshot | undefined,
): { value: ControlCenterDashboardSnapshot; usedFallback: boolean } {
  if (!isPlainRecord(value)) {
    return { value: mockControlCenterData.dashboard, usedFallback: true };
  }
  const normalized = { ...value } as Record<string, unknown>;
  const pluginGovernanceSafe = isSafePluginGovernanceSummary(
    normalized.plugin_governance_summary,
  );
  if (!pluginGovernanceSafe) {
    normalized.plugin_governance_summary =
      mockControlCenterData.dashboard.plugin_governance_summary;
  }
  if (
    isSafeProviderCredentialReadiness(normalized.provider_credential_readiness)
  ) {
    return {
      value: normalized as unknown as ControlCenterDashboardSnapshot,
      usedFallback: !pluginGovernanceSafe,
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
  if (
    !isSafeDelegatedRuntimeModelCatalogPosture(
      value.delegated_runtime_model_catalog,
    )
  ) {
    return false;
  }
  if (!isSafeModelSlotPosture(value.model_slot_posture)) {
    return false;
  }
  if (!isSafeProviderRoutingProposal(value.provider_routing_intelligence)) {
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

function isSafeProviderRoutingProposal(value: unknown): boolean {
  if (
    !isPlainRecord(value) ||
    !isPlainRecord(value.request) ||
    !Array.isArray(value.observations) ||
    !Array.isArray(value.candidates) ||
    !Array.isArray(value.evaluated_candidates)
  ) {
    return false;
  }
  const candidates = value.candidates;
  const evaluatedCandidates = value.evaluated_candidates;
  const observations = value.observations;
  const request = value.request;
  const observationRecords = observations.filter(isPlainRecord);
  const evaluatedCandidateRecords = evaluatedCandidates.filter(isPlainRecord);
  const candidateRecords = candidates.filter(isPlainRecord);
  const observationsByRef = new Map(
    observationRecords.map((observation) => [
      String(observation.observation_ref),
      observation,
    ]),
  );
  const evaluatedByCandidateRef = new Map(
    evaluatedCandidateRecords.map((candidate) => [
      String(candidate.candidate_ref),
      candidate,
    ]),
  );
  const recommendedCandidate =
    typeof value.recommended_candidate_ref === "string"
      ? candidates.find(
          (candidate) =>
            isPlainRecord(candidate) &&
            candidate.candidate_ref === value.recommended_candidate_ref,
        )
      : undefined;
  const eligibleCandidates = candidates.filter(
    (candidate) =>
      isPlainRecord(candidate) &&
      candidate.status === "eligible_for_request_scoped_evaluation",
  );
  const strategies = [
    "best_value",
    "lowest_cost",
    "lowest_latency",
    "best_quality",
    "local_first",
  ];
  const observationFingerprintRefs = value.observation_fingerprint_refs;
  return (
    value.schema_version === "provider_routing_intelligence.v1" &&
    value.contract_ref === "contract-ref:provider-routing-intelligence:v1" &&
    value.status === "proposal_only" &&
    value.proposal_only === true &&
    value.deterministic === true &&
    value.safe_refs_only === true &&
    value.approval_refs_are_identifiers_only === true &&
    value.request_scoped_invocation_decision_required === true &&
    value.fresh_local_approval_validation_required === true &&
    value.fresh_authority_lease_evaluation_required === true &&
    value.invocation_authorized === false &&
    value.provider_call_performed === false &&
    value.fallback_execution_performed === false &&
    value.background_fanout_performed === false &&
    value.raw_prompt_persisted === false &&
    value.raw_response_persisted === false &&
    value.raw_provider_payload_persisted === false &&
    isProviderRoutingFingerprintRef(value.proposal_ref, "proposal") &&
    isProviderRoutingSafeRef(value.request_ref) &&
    isProviderRoutingFingerprintRef(value.request_fingerprint_ref, "request") &&
    isProviderRoutingFingerprintRef(
      value.observation_set_fingerprint_ref,
      "observation-set",
    ) &&
    Array.isArray(observationFingerprintRefs) &&
    observationFingerprintRefs.every((item) =>
      isProviderRoutingFingerprintRef(item, "observation"),
    ) &&
    new Set(observationFingerprintRefs).size ===
      observationFingerprintRefs.length &&
    observationFingerprintRefs.length <= 32 &&
    isProviderRoutingSafeText(value.safe_summary, 500) &&
    strategies.includes(String(value.strategy)) &&
    isProviderRoutingNeed(request) &&
    request.request_ref === value.request_ref &&
    request.strategy === value.strategy &&
    request.maximum_presented_candidates ===
      value.maximum_presented_candidates &&
    observations.every(isSafeProviderRoutingObservation) &&
    observationRecords.length === observations.length &&
    providerRoutingUniqueField(observationRecords, "observation_ref") &&
    providerRoutingUniqueField(observationRecords, "provider_ref") &&
    evaluatedCandidates.every(isSafeProviderRoutingCandidate) &&
    evaluatedCandidateRecords.length === evaluatedCandidates.length &&
    providerRoutingUniqueField(evaluatedCandidateRecords, "candidate_ref") &&
    providerRoutingUniqueField(evaluatedCandidateRecords, "observation_ref") &&
    providerRoutingUniqueField(evaluatedCandidateRecords, "provider_ref") &&
    evaluatedCandidates.every(
      (candidate) => isPlainRecord(candidate) && candidate.rank === null,
    ) &&
    evaluatedCandidateRecords.every((candidate) => {
      const observation = observationsByRef.get(String(candidate.observation_ref));
      return (
        observation !== undefined &&
        isProviderRoutingCandidateProjectionOfObservation(candidate, observation)
      );
    }) &&
    providerRoutingSortedArraysEqual(
      evaluatedCandidateRecords.map((candidate) =>
        String(candidate.observation_fingerprint_ref),
      ),
      observationFingerprintRefs,
    ) &&
    Number.isInteger(value.observed_candidate_count) &&
    Number(value.observed_candidate_count) >= 0 &&
    Number(value.observed_candidate_count) <= 32 &&
    Number.isInteger(value.presented_candidate_count) &&
    Number.isInteger(value.omitted_candidate_count) &&
    Number.isInteger(value.maximum_presented_candidates) &&
    value.presented_candidate_count === candidates.length &&
    value.observed_candidate_count === observations.length &&
    value.observed_candidate_count === evaluatedCandidates.length &&
    value.observed_candidate_count === observationFingerprintRefs.length &&
    Number(value.observed_candidate_count) ===
      Number(value.presented_candidate_count) +
        Number(value.omitted_candidate_count) &&
    Number(value.presented_candidate_count) ===
      Math.min(
        Number(value.observed_candidate_count),
        Number(value.maximum_presented_candidates),
      ) &&
    Number(value.maximum_presented_candidates) >= candidates.length &&
    Number(value.maximum_presented_candidates) >= 1 &&
    Number(value.maximum_presented_candidates) <= 4 &&
    isProviderRoutingCodeArray(value.reason_codes) &&
    isProviderRoutingCodeArray(value.blocker_codes) &&
    isProviderRoutingSafeRef(value.approval_queue_route_ref) &&
    isProviderRoutingSafeRef(value.run_detail_group_ref) &&
    isProviderRoutingSafeRef(value.bounded_fanout_presentation_ref) &&
    isProviderRoutingSafeRef(value.source_ref) &&
    candidates.every(isSafeProviderRoutingCandidate) &&
    candidateRecords.length === candidates.length &&
    providerRoutingUniqueField(candidateRecords, "candidate_ref") &&
    providerRoutingUniqueField(candidateRecords, "observation_ref") &&
    providerRoutingUniqueField(candidateRecords, "provider_ref") &&
    candidateRecords.every((candidate) => {
      const evaluated = evaluatedByCandidateRef.get(String(candidate.candidate_ref));
      const observation = observationsByRef.get(String(candidate.observation_ref));
      return (
        evaluated !== undefined &&
        observation !== undefined &&
        isProviderRoutingRankedCopy(candidate, evaluated) &&
        isProviderRoutingEligibleForRequest(candidate, observation, request)
      );
    }) &&
    providerRoutingArraysEqual(
      candidateRecords.map((candidate) => candidate.candidate_ref),
      providerRoutingExpectedPresentedCandidateRefs(
        evaluatedCandidateRecords,
        String(value.strategy),
        Number(value.maximum_presented_candidates),
      ),
    ) &&
    candidateRecords.every((candidate, index) =>
      index < eligibleCandidates.length
        ? candidate.status === "eligible_for_request_scoped_evaluation"
        : candidate.status === "blocked",
    ) &&
    providerRoutingArraysEqual(
      value.blocker_codes,
      providerRoutingSortedUniqueCodes(evaluatedCandidateRecords, "blocker_codes"),
    ) &&
    providerRoutingArraysEqual(value.reason_codes, [
      "PROVIDER_ROUTING_PROPOSAL_ONLY",
      eligibleCandidates.length > 0
        ? "PROVIDER_ROUTING_CANDIDATE_AVAILABLE"
        : "PROVIDER_ROUTING_NO_ELIGIBLE_CANDIDATE",
    ]) &&
    eligibleCandidates.every(
      (candidate, index) =>
        isPlainRecord(candidate) && candidate.rank === index + 1,
    ) &&
    (value.recommended_candidate_ref === null
      ? eligibleCandidates.length === 0
      :
      (isPlainRecord(recommendedCandidate) &&
        recommendedCandidate.rank === 1 &&
        recommendedCandidate.status ===
          "eligible_for_request_scoped_evaluation"))
  );
}

function isProviderRoutingNeed(value: Record<string, unknown>): boolean {
  return (
    isProviderRoutingSafeRef(value.request_ref) &&
    isProviderRoutingSafeRef(value.task_ref) &&
    [
      "best_value",
      "lowest_cost",
      "lowest_latency",
      "best_quality",
      "local_first",
    ].includes(String(value.strategy)) &&
    isProviderRoutingSafeRefArray(value.required_capability_refs, 0, 12) &&
    Number.isInteger(value.minimum_context_tokens) &&
    Number(value.minimum_context_tokens) >= 0 &&
    Number(value.minimum_context_tokens) <= 2_000_000 &&
    Number.isInteger(value.maximum_presented_candidates) &&
    Number(value.maximum_presented_candidates) >= 1 &&
    Number(value.maximum_presented_candidates) <= 4
  );
}

function isSafeProviderRoutingObservation(value: unknown): boolean {
  if (!isPlainRecord(value) || !isPlainRecord(value.availability_snapshot)) {
    return false;
  }
  const snapshot = value.availability_snapshot;
  return (
    isProviderRoutingSafeRef(value.observation_ref) &&
    isProviderRoutingSafeRef(value.provider_ref) &&
    isProviderRoutingSafeText(value.provider_label, 120) &&
    isProviderRoutingSafeRef(value.provider_manifest_ref) &&
    isProviderRoutingSafeRef(value.model_ref) &&
    isProviderRoutingSafeRef(value.adapter_ref) &&
    ["local", "hosted", "unknown"].includes(String(value.runtime_class)) &&
    typeof value.metered === "boolean" &&
    isProviderRoutingOptionalNumber(value.estimated_cost_usd, 0, 1_000_000) &&
    isProviderRoutingOptionalNumber(
      value.estimated_latency_ms,
      0,
      3_600_000,
    ) &&
    isProviderRoutingOptionalNumber(value.quality_score, 0, 100) &&
    isProviderRoutingOptionalInteger(value.context_tokens, 1, 2_000_000) &&
    isProviderRoutingSafeRefArray(value.capability_refs, 0, 24) &&
    isProviderRoutingSafeRefArray(value.evidence_refs, 1, 24) &&
    isProviderRoutingSafeRef(value.source_ref) &&
    isSafeProviderRoutingAvailabilitySnapshot(snapshot) &&
    snapshot.provider_ref === value.provider_ref &&
    snapshot.adapter_ref === value.adapter_ref &&
    snapshot.source_ref === value.source_ref &&
    (value.metered
      ? snapshot.cost_posture === "metered"
      : snapshot.cost_posture === "not_metered") &&
    providerRoutingArraysEqual(snapshot.evidence_refs, value.evidence_refs)
  );
}

function isSafeProviderRoutingCandidate(value: unknown): boolean {
  if (!isPlainRecord(value) || !isPlainRecord(value.availability_snapshot)) {
    return false;
  }
  const snapshot = value.availability_snapshot;
  const eligible = value.status === "eligible_for_request_scoped_evaluation";
  const blocked = value.status === "blocked";
  return (
    (eligible || blocked) &&
    value.proposal_only === true &&
    value.invocation_authorized === false &&
    value.provider_call_performed === false &&
    isProviderRoutingFingerprintRef(value.candidate_ref, "candidate") &&
    isProviderRoutingSafeRef(value.observation_ref) &&
    isProviderRoutingFingerprintRef(
      value.observation_fingerprint_ref,
      "observation",
    ) &&
    isProviderRoutingSafeRef(value.provider_ref) &&
    isProviderRoutingSafeText(value.provider_label, 120) &&
    isProviderRoutingSafeRef(value.provider_manifest_ref) &&
    isProviderRoutingSafeRef(value.model_ref) &&
    isProviderRoutingSafeRef(value.adapter_ref) &&
    ["local", "hosted", "unknown"].includes(String(value.runtime_class)) &&
    isProviderRoutingOptionalNumber(value.estimated_cost_usd, 0, 1_000_000) &&
    isProviderRoutingOptionalNumber(
      value.estimated_latency_ms,
      0,
      3_600_000,
    ) &&
    isProviderRoutingOptionalNumber(value.quality_score, 0, 100) &&
    isProviderRoutingCodeArray(value.reason_codes) &&
    isProviderRoutingCodeArray(value.blocker_codes) &&
    isProviderRoutingSafeRefArray(value.evidence_refs, 1, 24) &&
    isProviderRoutingSafeText(value.safe_summary, 500) &&
    isSafeProviderRoutingAvailabilitySnapshot(snapshot) &&
    snapshot.provider_ref === value.provider_ref &&
    snapshot.adapter_ref === value.adapter_ref &&
    providerRoutingArraysEqual(snapshot.evidence_refs, value.evidence_refs) &&
    providerRoutingArrayContainsAll(value.reason_codes, snapshot.reason_codes) &&
    providerRoutingArrayContainsAll(value.blocker_codes, snapshot.blocker_codes) &&
    (eligible
      ? value.blocker_codes.length === 0 &&
        Number.isInteger(value.rank) &&
        Number(value.rank) >= 1 &&
        Number(value.rank) <= 4 &&
        snapshot.runtime_readiness_status === "ready" &&
        snapshot.authority_posture !== "blocked" &&
        snapshot.safe_disable_status === "inactive" &&
        (snapshot.cost_posture !== "metered" ||
          typeof value.estimated_cost_usd === "number") &&
        Array.isArray(snapshot.blocker_codes) &&
        snapshot.blocker_codes.length === 0 &&
        value.reason_codes.includes(
          "PROVIDER_REQUEST_SCOPED_APPROVAL_REVALIDATION_REQUIRED",
        ) &&
        value.reason_codes.includes(
          "PROVIDER_REQUEST_SCOPED_AUTHORITY_LEASE_REVALIDATION_REQUIRED",
        )
      : value.rank === null && value.blocker_codes.length > 0)
  );
}

function isSafeProviderRoutingAvailabilitySnapshot(
  value: Record<string, unknown>,
): boolean {
  const ready = value.runtime_readiness_status === "ready";
  return (
    value.schema_version === "uaa-capability-availability.v1" &&
    isProviderRoutingSafeRef(value.snapshot_ref) &&
    value.capability_ref === "capability-ref:provider-model-invocation" &&
    (value.provider_ref === null || isProviderRoutingSafeRef(value.provider_ref)) &&
    (value.adapter_ref === null || isProviderRoutingSafeRef(value.adapter_ref)) &&
    ["supported", "unsupported", "unknown"].includes(String(value.catalog_status)) &&
    ["supported", "unsupported", "unknown"].includes(
      String(value.compatibility_status),
    ) &&
    ["configured", "not_configured", "invalid", "unknown"].includes(
      String(value.configuration_status),
    ) &&
    ["healthy", "degraded", "unhealthy", "stale", "unknown"].includes(
      String(value.health_status),
    ) &&
    [
      "eligible_for_policy_evaluation",
      "approval_required",
      "lease_required",
      "blocked",
    ].includes(String(value.authority_posture)) &&
    ["available", "constrained", "exhausted", "unknown"].includes(
      String(value.resource_status),
    ) &&
    ["not_metered", "metered", "unknown"].includes(String(value.cost_posture)) &&
    ["active", "inactive", "unknown"].includes(String(value.safe_disable_status)) &&
    ["ready", "unavailable", "blocked", "unknown"].includes(
      String(value.runtime_readiness_status),
    ) &&
    (value.declared_or_observed_version_ref === null ||
      isProviderRoutingSafeRef(value.declared_or_observed_version_ref)) &&
    isProviderRoutingTimestamp(value.checked_at) &&
    (value.expires_at === null || isProviderRoutingTimestamp(value.expires_at)) &&
    ["current", "stale", "unknown"].includes(String(value.freshness_status)) &&
    isProviderRoutingCodeArray(value.reason_codes) &&
    isProviderRoutingCodeArray(value.blocker_codes) &&
    isProviderRoutingSafeRefArray(value.evidence_refs) &&
    isProviderRoutingSafeRefArray(value.probe_refs) &&
    isProviderRoutingSafeRef(value.source_ref) &&
    isProviderRoutingSafeText(value.safe_summary, 500) &&
    (!ready ||
      (value.catalog_status === "supported" &&
        value.compatibility_status === "supported" &&
        value.configuration_status === "configured" &&
        value.health_status === "healthy" &&
        value.resource_status === "available" &&
        value.cost_posture !== "unknown" &&
        value.safe_disable_status === "inactive" &&
        value.freshness_status === "current" &&
        (value.expires_at === null ||
          Date.parse(value.expires_at) > Date.parse(String(value.checked_at))) &&
        value.blocker_codes.length === 0))
  );
}

function isProviderRoutingCodeArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    new Set(value).size === value.length &&
    value.every(
      (item) =>
        typeof item === "string" && /^[A-Z][A-Z0-9_]{0,119}$/.test(item),
    )
  );
}

function isProviderRoutingSafeRefArray(
  value: unknown,
  minimumLength = 0,
  maximumLength = 64,
): value is string[] {
  return (
    Array.isArray(value) &&
    value.length >= minimumLength &&
    value.length <= maximumLength &&
    new Set(value).size === value.length &&
    value.every(isProviderRoutingSafeRef)
  );
}

function isProviderRoutingSafeRef(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^[A-Za-z][A-Za-z0-9_.:@-]{2,220}$/.test(value) &&
    isProviderRoutingSafeText(value, 220) &&
    !/(?:^|[^A-Za-z0-9])localhost(?:$|[^A-Za-z0-9])|::1/i.test(value) &&
    !/(?:^|[^A-Za-z0-9])(?:\d{1,3}\.){3}\d{1,3}(?:$|[^A-Za-z0-9])/.test(
      value,
    )
  );
}

function isProviderRoutingFingerprintRef(
  value: unknown,
  kind: "proposal" | "candidate" | "request" | "observation" | "observation-set",
): value is string {
  if (typeof value !== "string") {
    return false;
  }
  const prefixes = {
    proposal: "provider-routing-proposal-ref",
    candidate: "provider-routing-candidate-ref",
    request: "request-fingerprint-ref",
    observation: "observation-fingerprint-ref",
    "observation-set": "observation-set-fingerprint-ref",
  } as const;
  return new RegExp(`^${prefixes[kind]}:[a-f0-9]{64}$`).test(value);
}

function isProviderRoutingSafeText(value: unknown, maxLength: number): value is string {
  return (
    typeof value === "string" &&
    value.length > 0 &&
    value.length <= maxLength &&
    !/(?:\/Users\/|\/home\/|\/var\/|\/etc\/|\/private\/|\/tmp\/|[A-Za-z]:\\|\\Users\\|localhost|::1)/i.test(
      value,
    ) &&
    !/(?:^|[^A-Za-z0-9])(?:\d{1,3}\.){3}\d{1,3}(?:$|[^A-Za-z0-9])/.test(
      value,
    ) &&
    !/\b[A-Z][A-Z0-9_]{2,}\s*=/.test(value) &&
    !/(?<![A-Za-z0-9])@[A-Za-z0-9_.-]{2,}/.test(value) &&
    !/\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:com|net|org|io|dev|app|local|internal)\b/i.test(
      value,
    ) &&
    !/(?:api[_-]?key|authorization|bearer\s+|cookie|password|private\s+key|secret|token|client[_-]?secret|-----BEGIN)/i.test(
      value,
    )
  );
}

function isProviderRoutingOptionalNumber(
  value: unknown,
  minimum: number,
  maximum: number,
): boolean {
  return (
    value === null ||
    (typeof value === "number" &&
      Number.isFinite(value) &&
      value >= minimum &&
      value <= maximum)
  );
}

function isProviderRoutingOptionalInteger(
  value: unknown,
  minimum: number,
  maximum: number,
): boolean {
  return (
    value === null ||
    (Number.isInteger(value) &&
      Number(value) >= minimum &&
      Number(value) <= maximum)
  );
}

function isProviderRoutingTimestamp(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length <= 64 &&
    /(?:Z|[+-]\d{2}:\d{2})$/.test(value) &&
    Number.isFinite(Date.parse(value))
  );
}

function providerRoutingArraysEqual(left: unknown, right: unknown): boolean {
  return (
    Array.isArray(left) &&
    Array.isArray(right) &&
    left.length === right.length &&
    left.every((value, index) => value === right[index])
  );
}

function providerRoutingArrayContainsAll(
  outer: unknown,
  inner: unknown,
): boolean {
  return (
    Array.isArray(outer) &&
    Array.isArray(inner) &&
    inner.every((value) => outer.includes(value))
  );
}

function providerRoutingUniqueField(
  records: Array<Record<string, unknown>>,
  fieldName: string,
): boolean {
  const values = records.map((record) => record[fieldName]);
  return values.every((value) => typeof value === "string") &&
    new Set(values).size === values.length;
}

function providerRoutingSortedArraysEqual(
  left: string[],
  right: unknown[],
): boolean {
  return providerRoutingArraysEqual([...left].sort(), [...right].sort());
}

function providerRoutingSortedUniqueCodes(
  records: Array<Record<string, unknown>>,
  fieldName: string,
): string[] {
  return [
    ...new Set(
      records.flatMap((record) =>
        Array.isArray(record[fieldName])
          ? (record[fieldName] as unknown[]).filter(
              (value): value is string => typeof value === "string",
            )
          : [],
      ),
    ),
  ].sort();
}

function isProviderRoutingCandidateProjectionOfObservation(
  candidate: Record<string, unknown>,
  observation: Record<string, unknown>,
): boolean {
  return (
    candidate.observation_ref === observation.observation_ref &&
    candidate.provider_ref === observation.provider_ref &&
    candidate.provider_label === observation.provider_label &&
    candidate.provider_manifest_ref === observation.provider_manifest_ref &&
    candidate.model_ref === observation.model_ref &&
    candidate.adapter_ref === observation.adapter_ref &&
    candidate.runtime_class === observation.runtime_class &&
    candidate.estimated_cost_usd === observation.estimated_cost_usd &&
    candidate.estimated_latency_ms === observation.estimated_latency_ms &&
    candidate.quality_score === observation.quality_score &&
    providerRoutingArraysEqual(candidate.evidence_refs, observation.evidence_refs) &&
    providerRoutingJsonEqual(
      candidate.availability_snapshot,
      observation.availability_snapshot,
    )
  );
}

function isProviderRoutingRankedCopy(
  candidate: Record<string, unknown>,
  evaluated: Record<string, unknown>,
): boolean {
  const { rank: _candidateRank, ...candidateWithoutRank } = candidate;
  const { rank: _evaluatedRank, ...evaluatedWithoutRank } = evaluated;
  return providerRoutingJsonEqual(candidateWithoutRank, evaluatedWithoutRank);
}

function isProviderRoutingEligibleForRequest(
  candidate: Record<string, unknown>,
  observation: Record<string, unknown>,
  request: Record<string, unknown>,
): boolean {
  if (candidate.status !== "eligible_for_request_scoped_evaluation") {
    return true;
  }
  const requiredCapabilityRefs = Array.isArray(request.required_capability_refs)
    ? request.required_capability_refs
    : [];
  const capabilityRefs = Array.isArray(observation.capability_refs)
    ? observation.capability_refs
    : [];
  const minimumContextTokens = Number(request.minimum_context_tokens);
  return (
    (!observation.metered ||
      typeof observation.estimated_cost_usd === "number") &&
    requiredCapabilityRefs.every((ref) => capabilityRefs.includes(ref)) &&
    (minimumContextTokens === 0 ||
      (typeof observation.context_tokens === "number" &&
        observation.context_tokens >= minimumContextTokens))
  );
}

function providerRoutingJsonEqual(left: unknown, right: unknown): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}

function providerRoutingExpectedPresentedCandidateRefs(
  evaluated: Array<Record<string, unknown>>,
  strategy: string,
  maximumPresentedCandidates: number,
): unknown[] {
  const eligible = evaluated
    .filter(
      (candidate) =>
        candidate.status === "eligible_for_request_scoped_evaluation",
    )
    .sort((left, right) =>
      providerRoutingCompareCandidates(strategy, left, right),
    );
  const blocked = evaluated
    .filter((candidate) => candidate.status === "blocked")
    .sort((left, right) =>
      providerRoutingCompareRefs(left.provider_ref, right.provider_ref),
    );
  const selectedEligible = eligible.slice(0, maximumPresentedCandidates);
  const selectedBlocked = blocked.slice(
    0,
    maximumPresentedCandidates - selectedEligible.length,
  );
  return [...selectedEligible, ...selectedBlocked].map(
    (candidate) => candidate.candidate_ref,
  );
}

function providerRoutingCompareCandidates(
  strategy: string,
  left: Record<string, unknown>,
  right: Record<string, unknown>,
): number {
  const tupleFor = (candidate: Record<string, unknown>): number[] => {
    const cost =
      typeof candidate.estimated_cost_usd === "number"
        ? candidate.estimated_cost_usd
        : Number.POSITIVE_INFINITY;
    const latency =
      typeof candidate.estimated_latency_ms === "number"
        ? candidate.estimated_latency_ms
        : Number.POSITIVE_INFINITY;
    const quality =
      typeof candidate.quality_score === "number" ? candidate.quality_score : 0;
    if (strategy === "lowest_cost") {
      return [cost, latency, -quality];
    }
    if (strategy === "lowest_latency") {
      return [latency, cost, -quality];
    }
    if (strategy === "best_quality") {
      return [-quality, cost, latency];
    }
    if (strategy === "local_first") {
      const localRank =
        candidate.runtime_class === "local"
          ? 0
          : candidate.runtime_class === "hosted"
            ? 1
            : 2;
      return [localRank, cost, latency];
    }
    return [-(quality / (1 + cost)), latency, cost];
  };
  const leftTuple = tupleFor(left);
  const rightTuple = tupleFor(right);
  for (let index = 0; index < leftTuple.length; index += 1) {
    if (leftTuple[index] < rightTuple[index]) {
      return -1;
    }
    if (leftTuple[index] > rightTuple[index]) {
      return 1;
    }
  }
  return providerRoutingCompareRefs(left.provider_ref, right.provider_ref);
}

function providerRoutingCompareRefs(left: unknown, right: unknown): number {
  const leftRef = String(left);
  const rightRef = String(right);
  return leftRef < rightRef ? -1 : leftRef > rightRef ? 1 : 0;
}

function isSafeDelegatedRuntimeModelCatalogPosture(value: unknown): boolean {
  if (!isPlainRecord(value) || !Array.isArray(value.records)) {
    return false;
  }
  const falseFlags = [
    "uaa_may_invoke_any_listed_model",
    "live_provider_discovery_enabled",
    "provider_sdk_call_enabled",
    "remote_model_call_enabled",
    "credential_collection_enabled",
    "billing_authority_granted",
    "model_output_authority_enabled",
  ];
  const availableCount = value.records.filter(
    (record) =>
      isPlainRecord(record) && record.runtime_reported_available === true,
  ).length;
  return (
    value.schema_version === "delegated_runtime_model_catalog.v1" &&
    value.status === "read_only_runtime_model_availability" &&
    value.route_ref === "GET /control-center/providers/runtime-control-plane" &&
    value.runtime_says_available_is_not_authority === true &&
    value.static_cost_metadata_only === true &&
    value.static_latency_metadata_only === true &&
    value.uaa_authorized_model_count === 0 &&
    value.model_count === value.records.length &&
    value.runtime_reported_available_count === availableCount &&
    falseFlags.every((field) => value[field] === false) &&
    value.records.every(isSafeDelegatedRuntimeModelAvailabilityRecord) &&
    Array.isArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-state:model-provider:runtime-availability-is-not-invocation",
    )
  );
}

function isSafeDelegatedRuntimeModelAvailabilityRecord(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const falseFlags = [
    "uaa_invocation_allowed",
    "provider_sdk_call_enabled",
    "live_provider_discovery_performed",
    "live_provider_network_call_performed",
    "credential_collection_enabled",
    "credential_material_visible",
    "billing_authority_granted",
    "model_output_authority_enabled",
    "raw_provider_payload_persisted",
  ];
  return (
    typeof value.runtime_ref === "string" &&
    typeof value.runtime_profile_ref === "string" &&
    typeof value.delegated_runtime_profile_ref === "string" &&
    value.runtime_profile_ref !== value.delegated_runtime_profile_ref &&
    typeof value.model_ref === "string" &&
    typeof value.provider_ref === "string" &&
    typeof value.safe_summary === "string" &&
    ["runtime_reports_available", "runtime_reports_planned", "local_gateway_metadata_available"].includes(
      String(value.runtime_availability_status),
    ) &&
    [
      "blocked_no_exact_invocation_lane",
      "blocked_profile_not_configured",
      "metadata_only_existing_lane_separate",
    ].includes(String(value.uaa_invocation_posture)) &&
    falseFlags.every((field) => value[field] === false) &&
    Array.isArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.length > 0
  );
}

function isSafeModelSlotPosture(value: unknown): boolean {
  if (!isPlainRecord(value) || !Array.isArray(value.records)) {
    return false;
  }
  const falseFlags = [
    "live_auxiliary_calls_enabled",
    "provider_sdk_use_enabled",
    "runtime_selection_mutation_enabled",
    "hidden_model_routing_enabled",
    "raw_prompt_persistence_enabled",
    "raw_response_persistence_enabled",
  ];
  const trueFlags = [
    "route_decision_trace_required",
    "cost_estimate_required",
    "approval_profile_mapping_required",
    "model_output_truth_envelope_required",
    "receipts_required_before_execution",
  ];
  const warningCount = value.records.filter(
    (record) =>
      isPlainRecord(record) &&
      Array.isArray(record.warning_refs) &&
      record.warning_refs.length > 0,
  ).length;
  return (
    value.schema_version === "hermes_runtime_model_slot_posture.v1" &&
    value.status === "read_only_model_slot_intent" &&
    value.route_ref === "GET /control-center/providers/runtime-control-plane" &&
    value.trust_lane_ref === "trust-lane:model-slot-posture" &&
    value.slot_count === value.records.length &&
    value.warning_count === warningCount &&
    value.main_slot_ref === "model-slot-ref:uaa:main-thinking" &&
    Array.isArray(value.auxiliary_slot_refs) &&
    value.auxiliary_slot_refs.length === value.records.length - 1 &&
    falseFlags.every((field) => value[field] === false) &&
    trueFlags.every((field) => value[field] === true) &&
    value.records.every(isSafeModelSlotPostureRecord) &&
    Array.isArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.includes(
      "blocked-state:model-slot:hidden-model-routing",
    )
  );
}

function isSafeModelSlotPostureRecord(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const falseFlags = [
    "live_auxiliary_call_enabled",
    "provider_sdk_call_enabled",
    "runtime_selection_mutation_enabled",
    "hidden_model_routing_enabled",
    "raw_prompt_persisted",
    "raw_response_persisted",
  ];
  const trueFlags = [
    "route_decision_trace_required",
    "cost_estimate_required",
    "approval_profile_mapping_required",
    "model_output_truth_envelope_required",
    "receipt_required_before_execution",
  ];
  return (
    typeof value.slot_ref === "string" &&
    typeof value.display_label === "string" &&
    typeof value.intended_provider_ref === "string" &&
    typeof value.intended_model_ref === "string" &&
    typeof value.route_decision_trace_ref === "string" &&
    typeof value.model_output_truth_ref === "string" &&
    [
      "main_thinking",
      "summarization",
      "title",
      "approval_scoring",
      "compression",
      "retrieval",
      "vision",
      "review",
    ].includes(String(value.slot_role)) &&
    [
      "configured_metadata_only",
      "planned_not_configured",
      "runtime_reported_available_not_authorized",
    ].includes(String(value.configured_status)) &&
    [
      "blocked_no_exact_model_authority",
      "blocked_missing_runtime_profile",
      "metadata_only_existing_lane_separate",
    ].includes(String(value.uaa_execution_posture)) &&
    falseFlags.every((field) => value[field] === false) &&
    trueFlags.every((field) => value[field] === true) &&
    Array.isArray(value.blocked_authority_refs) &&
    value.blocked_authority_refs.length > 0
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
    "authority_required",
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
  "authority_domain_coverage",
  "authority_capability_catalog",
  "authority_capability_catalog_refs",
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
  "authority_readiness_refs",
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
  "authority_readiness_refs",
  "promotion_path_refs",
  "blocked_authority_refs",
] as const;

const TRUST_AUTHORITY_DOMAIN_COVERAGE_ARRAYS = [
  "visible_mapping_refs",
  "unsupported_adapter_refs",
] as const;

const TRUST_AUTHORITY_CAPABILITY_CATALOG_ARRAYS = [
  "route_refs",
  "proof_refs",
  "verifier_refs",
  "cli_inspection_refs",
  "safe_disable_refs",
  "rollback_refs",
  "blocked_authority_refs",
  "authority_state_reason_refs",
  "unsupported_adapter_refs",
] as const;

const TRUST_AUTHORITY_DECISION_OUTCOMES = [
  "allow",
  "ask",
  "deny",
  "degrade_to_draft",
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

const TRUST_AUTHORITY_DOMAIN_COVERAGE_STATUSES = [
  "implemented",
  "partial",
  "planned",
  "unknown",
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
    (value.authority_domain_coverage as unknown[]).length > 0 &&
    (value.authority_domain_coverage as unknown[]).every(
      isSafeTrustAuthorityDomainCoverage,
    ) &&
    (value.authority_capability_catalog as unknown[]).length ===
      (value.lanes as unknown[]).length &&
    (value.authority_capability_catalog as unknown[]).every(
      isSafeTrustAuthorityCapabilityCatalogEntry,
    ) &&
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
      value.authority_state === "approval_required" ||
      value.authority_state === "planned") &&
    typeof value.authority_state_label === "string" &&
    typeof value.operator_posture === "string" &&
    typeof value.current_posture === "string" &&
    typeof value.approval_posture === "string" &&
    typeof value.operator_can_do_now === "string" &&
    typeof value.next_safe_action === "string" &&
    typeof value.authority_domain_ref === "string" &&
    value.authority_domain_ref.startsWith("authority-domain-ref:") &&
    typeof value.authority_capability_ref === "string" &&
    value.authority_capability_ref.startsWith("authority-capability-ref:") &&
    typeof value.required_authority_mode === "string" &&
    typeof value.authority_lease_requirement_ref === "string" &&
    value.authority_lease_requirement_ref.startsWith(
      "authority-lease-requirement-ref:",
    ) &&
    TRUST_AUTHORITY_LANE_ARRAYS.every((field) => Array.isArray(value[field])) &&
    value.safe_refs_only === true &&
    value.control_center_grants_authority === false &&
    value.rollback_execution_enabled === false &&
    isExpectedTrustOperatorPosture(value) &&
    stringArray(value.cli_inspection_refs).length > 0 &&
    (value.tier < 3 ||
      (stringArray(value.safe_disable_refs).length > 0 &&
        stringArray(value.rollback_refs).length > 0)) &&
    stringArray(value.authority_readiness_refs).length > 0 &&
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
  const catalog = value.authority_capability_catalog as Record<string, unknown>[];
  const parityFields = [
    "cli_inspection_refs",
    "safe_disable_refs",
    "rollback_refs",
    "authority_readiness_refs",
    "promotion_path_refs",
    "blocked_authority_refs",
  ] as const;
  return parityFields.every((field) =>
    hasExactStringList(
      value[field],
      uniqueStrings(lanes.flatMap((lane) => stringArray(lane[field]))),
    ),
  ) &&
    hasExactStringList(
      value.authority_capability_catalog_refs,
      catalog.map((entry) => String(entry.catalog_ref)),
    ) &&
    hasExactStringList(
      catalog.map((entry) => String(entry.source_lane_ref)),
      lanes.map((lane) => String(lane.lane_ref)),
    ) &&
    catalog.every((entry, index) => {
      const lane = lanes[index];
      return (
        entry.label === lane.label &&
        entry.authority_state === lane.authority_state &&
        entry.operator_posture === lane.operator_posture &&
        entry.authority_domain_ref === lane.authority_domain_ref &&
        entry.authority_capability_ref === lane.authority_capability_ref &&
        entry.required_authority_mode === lane.required_authority_mode &&
        entry.authority_lease_requirement_ref ===
          lane.authority_lease_requirement_ref
      );
    });
}

function isSafeTrustAuthorityCapabilityCatalogEntry(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const authorityStateCatalogRef = value.authority_state_catalog_ref;
  const authorityStateMappingRef = value.authority_state_mapping_ref;
  const authorityStateDecisionRef = value.authority_state_decision_ref;
  const authorityStateDecisionOutcome = value.authority_state_decision_outcome;
  const authorityStateStatus = value.authority_state_status;
  const authorityStateOperatorMessage = value.authority_state_operator_message;
  return (
    typeof value.catalog_ref === "string" &&
    value.catalog_ref.startsWith("authority-capability-catalog-ref:") &&
    typeof value.source_lane_ref === "string" &&
    value.source_lane_ref.startsWith("trust-lane:") &&
    typeof value.label === "string" &&
    hasExactStringValue(value.authority_state, TRUST_AUTHORITY_STATES) &&
    typeof value.operator_posture === "string" &&
    typeof value.authority_domain_ref === "string" &&
    value.authority_domain_ref.startsWith("authority-domain-ref:") &&
    typeof value.authority_capability_ref === "string" &&
    value.authority_capability_ref.startsWith("authority-capability-ref:") &&
    typeof value.required_authority_mode === "string" &&
    typeof value.authority_lease_requirement_ref === "string" &&
    value.authority_lease_requirement_ref.startsWith(
      "authority-lease-requirement-ref:",
    ) &&
    TRUST_AUTHORITY_CAPABILITY_CATALOG_ARRAYS.every((field) =>
      Array.isArray(value[field]),
    ) &&
    stringArray(value.proof_refs).every(isSafeTrustAuthorityRef) &&
    stringArray(value.safe_disable_refs).every(isSafeTrustAuthorityRef) &&
    stringArray(value.rollback_refs).every(isSafeTrustAuthorityRef) &&
    stringArray(value.blocked_authority_refs).every(isSafeTrustAuthorityRef) &&
    stringArray(value.authority_state_reason_refs).every(isSafeTrustAuthorityRef) &&
    stringArray(value.unsupported_adapter_refs).every(isSafeTrustAuthorityRef) &&
    (authorityStateCatalogRef === null ||
      authorityStateCatalogRef === undefined ||
      isSafeTrustAuthorityRef(authorityStateCatalogRef)) &&
    (authorityStateMappingRef === null ||
      authorityStateMappingRef === undefined ||
      isSafeTrustAuthorityRef(authorityStateMappingRef)) &&
    (authorityStateDecisionRef === null ||
      authorityStateDecisionRef === undefined ||
      isSafeTrustAuthorityRef(authorityStateDecisionRef)) &&
    (authorityStateDecisionOutcome === null ||
      authorityStateDecisionOutcome === undefined ||
      hasExactStringValue(
        authorityStateDecisionOutcome,
        TRUST_AUTHORITY_DECISION_OUTCOMES,
      )) &&
    (authorityStateStatus === null ||
      authorityStateStatus === undefined ||
      typeof authorityStateStatus === "string") &&
    (authorityStateOperatorMessage === null ||
      authorityStateOperatorMessage === undefined ||
      typeof authorityStateOperatorMessage === "string") &&
    typeof value.safe_summary === "string" &&
    !containsUnsafeTrustText(value.label) &&
    !containsUnsafeTrustText(value.required_authority_mode) &&
    !containsUnsafeTrustText(value.safe_summary) &&
    (typeof authorityStateStatus !== "string" ||
      !containsUnsafeTrustText(authorityStateStatus)) &&
    (typeof authorityStateOperatorMessage !== "string" ||
      !containsUnsafeTrustText(authorityStateOperatorMessage)) &&
    value.active_lease_required === true &&
    value.unknown_authority_denied === true &&
    value.safe_refs_only === true &&
    value.control_center_grants_authority === false &&
    value.execution_claimed === false
  );
}

function isSafeTrustAuthorityDomainCoverage(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const mappingCount =
    typeof value.mapping_count === "number" ? value.mapping_count : -1;
  const implementedCount =
    typeof value.implemented_mapping_count === "number"
      ? value.implemented_mapping_count
      : -1;
  const partialCount =
    typeof value.partial_mapping_count === "number"
      ? value.partial_mapping_count
      : -1;
  const plannedCount =
    typeof value.planned_mapping_count === "number"
      ? value.planned_mapping_count
      : -1;
  const visibleMappingRefs = stringArray(value.visible_mapping_refs);
  return (
    typeof value.domain_ref === "string" &&
    value.domain_ref.startsWith("authority-domain-ref:") &&
    typeof value.label === "string" &&
    hasExactStringValue(value.status, TRUST_AUTHORITY_DOMAIN_COVERAGE_STATUSES) &&
    typeof value.known_authority === "boolean" &&
    mappingCount >= 0 &&
    implementedCount >= 0 &&
    partialCount >= 0 &&
    plannedCount >= 0 &&
    mappingCount === implementedCount + partialCount + plannedCount &&
    typeof value.hidden_mapping_ref_count === "number" &&
    value.hidden_mapping_ref_count === mappingCount - visibleMappingRefs.length &&
    TRUST_AUTHORITY_DOMAIN_COVERAGE_ARRAYS.every((field) =>
      Array.isArray(value[field]),
    ) &&
    visibleMappingRefs.every(isSafeTrustAuthorityRef) &&
    stringArray(value.unsupported_adapter_refs).every(isSafeTrustAuthorityRef) &&
    typeof value.authority_state_route_ref === "string" &&
    value.authority_state_route_ref === "GET /api/runtime/authority-state" &&
    typeof value.authority_state_cli_ref === "string" &&
    value.authority_state_cli_ref ===
      "repo-local-command:uaa-runtime-inspect-authority-state" &&
    typeof value.operator_summary === "string" &&
    !containsUnsafeTrustText(value.label) &&
    !containsUnsafeTrustText(value.operator_summary) &&
    value.known_authority === (mappingCount > 0) &&
    value.active_lease_required === true &&
    value.safe_refs_only === true &&
    value.execution_claimed === false
  );
}

const CANONICAL_SAFE_REF_RE =
  /^[A-Za-z][A-Za-z0-9_.-]*:[A-Za-z0-9][A-Za-z0-9_.:/@-]*$/;
const ABSOLUTE_LOCAL_PATH_PATTERNS = [
  /(?:^|[^A-Za-z0-9])[A-Za-z]:[\\/][^\s"')>\],;]*/,
  /(?:^|[^A-Za-z0-9])\\\\[^\\\s]+\\[^\s"')>\],;]+/,
  /\bfile:(?:\/\/|%2f)/i,
];
const POSIX_ABSOLUTE_PATH_CANDIDATE_RE =
  /\/(?:\/)?[^\s"')>\],;]+/g;
const CANONICAL_SAFE_REF_TOKEN_RE =
  /[A-Za-z][A-Za-z0-9_.-]*:[A-Za-z0-9][A-Za-z0-9_.:/@-]*/g;
const NETWORK_URI_TOKEN_RE =
  /(?<![A-Za-z0-9_.:@-])\b[A-Za-z][A-Za-z0-9+.-]*:\/\/[^\s"')>\],;]+/g;

function containsAbsoluteLocalPath(value: string): boolean {
  if (ABSOLUTE_LOCAL_PATH_PATTERNS.some((pattern) => pattern.test(value))) {
    return true;
  }
  const safeRefSpans = [...value.matchAll(CANONICAL_SAFE_REF_TOKEN_RE)].map(
    (match) => [match.index, match.index + match[0].length] as const,
  );
  const networkUriSpans = [...value.matchAll(NETWORK_URI_TOKEN_RE)].map(
    (match) => [match.index, match.index + match[0].length] as const,
  );
  for (const match of value.matchAll(POSIX_ABSOLUTE_PATH_CANDIDATE_RE)) {
    const slashIndex = match.index;
    const predecessor = slashIndex > 0 ? value[slashIndex - 1] : "";
    if (/^[A-Za-z0-9]$/.test(predecessor)) {
      continue;
    }
    if (
      networkUriSpans.some(
        ([start, end]) => start <= slashIndex && slashIndex < end,
      )
    ) {
      continue;
    }
    if (
      "._-@_".includes(predecessor) &&
      safeRefSpans.some(
        ([start, end]) => start <= slashIndex && slashIndex < end,
      )
    ) {
      continue;
    }
    return true;
  }
  return false;
}

function isSafeTrustAuthorityRef(value: unknown): value is string {
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
  if (value.includes("\\") || value.includes(" ")) {
    return false;
  }
  return CANONICAL_SAFE_REF_RE.test(value);
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
  normalizeBoundedMemoryPosture(normalized, valueRecord);
  return {
    value: normalized as unknown as FounderLoopMemoryReview,
    usedFallback: merged.usedFallback,
  };
}

const MEMORY_BOUNDED_POSTURE_DENIED_FLAGS = [
  "automatic_memory_write_authorized",
  "autonomous_memory_write_authorized",
  "hidden_prompt_injection_authorized",
  "external_memory_provider_write_authorized",
  "context_injection_authorized",
  "memory_truth_authority",
  "semantic_provider_enabled",
  "vector_db_enabled",
  "embedding_search_enabled",
  "model_provider_call_authorized",
  "live_web_fetch_authorized",
  "connector_write_authorized",
  "delete_export_execution_authorized",
  "background_autonomy_authorized",
  "production_authority_enabled",
] as const;

function normalizeBoundedMemoryPosture(
  normalized: Record<string, unknown>,
  valueRecord: Record<string, unknown>,
): void {
  const posture = valueRecord.bounded_memory_posture;
  if (isSafeBoundedMemoryPosture(posture)) {
    normalized.bounded_memory_posture = posture;
    normalized.bounded_memory_posture_contract_ref = (
      posture as Record<string, unknown>
    ).contract_ref;
  } else {
    delete normalized.bounded_memory_posture;
    delete normalized.bounded_memory_posture_contract_ref;
  }
}

function isSafeBoundedMemoryPosture(value: unknown): boolean {
  if (!isPlainRecord(value)) {
    return false;
  }
  const nestedRecords = [
    value.target_posture,
    value.capacity_posture,
    value.source_posture,
    value.staleness_posture,
    value.why_shown_posture,
    value.quality_review_posture,
    value.context_pack_posture,
  ];
  if (!nestedRecords.every(isPlainRecord)) {
    return false;
  }
  const targetPosture = value.target_posture as Record<string, unknown>;
  const capacityPosture = value.capacity_posture as Record<string, unknown>;
  const sourcePosture = value.source_posture as Record<string, unknown>;
  const stalenessPosture = value.staleness_posture as Record<string, unknown>;
  const whyShownPosture = value.why_shown_posture as Record<string, unknown>;
  const qualityPosture = value.quality_review_posture as Record<string, unknown>;
  const contextPackPosture = value.context_pack_posture as Record<string, unknown>;
  const blockedStateRefs = value.blocked_state_refs;
  return (
    value.schema_version ===
      "hermes_runtime_adoption_bounded_memory_posture.v1" &&
    value.contract_ref ===
      "contract-ref:hermes-runtime-adoption-bounded-memory-posture:v1" &&
    value.source === "python_core_memory_workbench_bounded_memory_posture" &&
    hasStringFields(value, [
      "route_ref",
      "cli_ref",
      "proof_ref",
      "status",
      "next_safe_action",
    ]) &&
    value.backend_owned === true &&
    value.control_center_presentation_only === true &&
    value.safe_refs_only === true &&
    value.raw_content_included === false &&
    hasDeniedFlagsFalse(value, MEMORY_BOUNDED_POSTURE_DENIED_FLAGS) &&
    Array.isArray(blockedStateRefs) &&
    blockedStateRefs.every((item) => typeof item === "string") &&
    blockedStateRefs.length > 0 &&
    hasStringArrays(targetPosture, ["supported_target_kinds", "target_refs"]) &&
    targetPosture.operator_selected_context_required === true &&
    targetPosture.automatic_context_injection_authorized === false &&
    targetPosture.hidden_context_injection_authorized === false &&
    hasNumberFields(capacityPosture, [
      "visible_item_count",
      "candidate_count",
      "context_pack_count",
      "max_visible_items",
      "max_provenance_refs",
      "token_estimate",
    ]) &&
    typeof capacityPosture.token_budget_state === "string" &&
    isPlainRecord(capacityPosture.search_index_status) &&
    hasStringArrays(sourcePosture, [
      "source_refs",
      "provenance_refs",
      "evidence_refs",
      "receipt_refs",
    ]) &&
    sourcePosture.safe_summary_only === true &&
    sourcePosture.source_refs_required === true &&
    hasStringArrays(stalenessPosture, [
      "stale_item_refs",
      "stale_state_refs",
    ]) &&
    typeof stalenessPosture.stale_count === "number" &&
    typeof stalenessPosture.recheck_required_before_recall === "boolean" &&
    hasStringArrays(whyShownPosture, [
      "why_shown_refs",
      "included_reason_refs",
      "quality_state_refs",
    ]) &&
    whyShownPosture.why_shown_required === true &&
    hasStringArrays(qualityPosture, [
      "correction_receipt_refs",
      "rejection_receipt_refs",
      "accepted_receipt_refs",
      "receipt_backed_decision_kinds",
    ]) &&
    qualityPosture.review_required_before_recall === true &&
    qualityPosture.correction_supported === true &&
    qualityPosture.rejection_supported === true &&
    qualityPosture.memory_write_requires_review_receipt === true &&
    typeof qualityPosture.reviewed_recall_write_scope_ref === "string" &&
    typeof qualityPosture.rollback_posture === "string" &&
    hasStringArrays(contextPackPosture, ["context_pack_refs"]) &&
    typeof contextPackPosture.proposal_count === "number" &&
    contextPackPosture.context_pack_preview_only === true &&
    contextPackPosture.prompt_context_written === false &&
    contextPackPosture.context_injection_authorized === false &&
    contextPackPosture.hidden_prompt_context_authorized === false
  );
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
  "control_center_mints_authority",
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
  "authority_reason_refs",
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
    value.control_center_exact_runtime_mutations_enabled === true &&
    value.local_model_call_control_enabled === true &&
    value.command_request_control_enabled === true &&
    value.approval_decision_control_enabled === true &&
    value.exact_envelope_execution_control_enabled === true &&
    value.safe_disable_control_enabled === true &&
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
  const authorityDecisionRef = value.authority_decision_ref;
  const authorityDecisionOutcome = value.authority_decision_outcome;
  const authorityLeaseRef = value.authority_lease_ref;
  const authorityDomainRef = value.authority_domain_ref;
  const authorityCapabilityRef = value.authority_capability_ref;
  const authorityRequiredModeRef = value.authority_required_mode_ref;
  const authorityAuditRef = value.authority_audit_ref;
  const authorityPolicyReceiptRef = value.authority_policy_receipt_ref;
  const authorityOperatorMessage = value.authority_operator_message;
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
    (authorityDecisionRef === null ||
      authorityDecisionRef === undefined ||
      isSafeActionWorkQueueRef(authorityDecisionRef)) &&
    (authorityDecisionOutcome === null ||
      authorityDecisionOutcome === undefined ||
      typeof authorityDecisionOutcome === "string") &&
    (authorityLeaseRef === null ||
      authorityLeaseRef === undefined ||
      isSafeActionWorkQueueRef(authorityLeaseRef)) &&
    (authorityDomainRef === null ||
      authorityDomainRef === undefined ||
      isSafeActionWorkQueueRef(authorityDomainRef)) &&
    (authorityCapabilityRef === null ||
      authorityCapabilityRef === undefined ||
      isSafeActionWorkQueueRef(authorityCapabilityRef)) &&
    (authorityRequiredModeRef === null ||
      authorityRequiredModeRef === undefined ||
      isSafeActionWorkQueueRef(authorityRequiredModeRef)) &&
    (authorityAuditRef === null ||
      authorityAuditRef === undefined ||
      isSafeActionWorkQueueRef(authorityAuditRef)) &&
    (authorityPolicyReceiptRef === null ||
      authorityPolicyReceiptRef === undefined ||
      isSafeActionWorkQueueRef(authorityPolicyReceiptRef)) &&
    (authorityOperatorMessage === null ||
      authorityOperatorMessage === undefined ||
      typeof authorityOperatorMessage === "string") &&
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
    typeof value.authority_scope_required === "boolean" &&
    typeof value.authority_scope_allowed === "boolean" &&
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
    (value.authority_reason_refs as string[]).every(isSafeActionWorkQueueRef) &&
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
      "contract-ref:runtime-action-tool-code-catalog:v1" ||
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
      "exact_local_authority_capability_count",
      "exact_runtime_lane_count",
      "exact_runtime_authority_capability_count",
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
    value.exact_local_authority_capability_count ===
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
    value.exact_runtime_authority_capability_count ===
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
    (value.availability_snapshot_ref == null ||
      isSafeActionWorkQueueRef(value.availability_snapshot_ref)) &&
    (value.canonical_execution_path_ref == null ||
      isSafeActionWorkQueueRef(value.canonical_execution_path_ref)) &&
    (value.canonical_mission_dispatch == null ||
      typeof value.canonical_mission_dispatch === "boolean") &&
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
      "expiry_or_staleness",
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
    isOptionalSafeActionWorkQueueRef(value.exact_scope_ref) &&
    isOptionalSafeActionWorkQueueRef(value.idempotency_ref) &&
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
      "expiry_or_staleness",
    ]) &&
    isSafeActionWorkQueueRef(value.item_ref) &&
    isSafeActionWorkQueueRef(value.proof_ref) &&
    typeof value.approval_required === "boolean" &&
    typeof value.operator_actionable === "boolean" &&
    typeof value.local_task_commit_eligible === "boolean" &&
    value.fake_mutation_control_exposed === false &&
    isOptionalSafeActionWorkQueueRef(value.approval_envelope_ref) &&
    isOptionalSafeActionWorkQueueRef(value.exact_scope_ref) &&
    isOptionalSafeActionWorkQueueRef(value.idempotency_ref) &&
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
    normalizeBoundedMemoryPosture(
      workbenchWithoutMockPosture,
      value as unknown as Record<string, unknown>,
    );
    return {
      value:
        workbenchWithoutMockPosture as unknown as FounderLoopMemoryWorkbench,
      usedFallback: merged.usedFallback,
    };
  }
  return merged;
}

const AUTHORITY_MISSION_WORKER_STATUSES = new Set([
  "pending",
  "claimed",
  "approval_wait",
  "retry_pending",
  "succeeded",
  "failed",
  "recovery_required",
  "cancelled",
]);

const AUTHORITY_MISSION_RECOVERY_STATUSES = new Set([
  "pending",
  "actively_claimed",
  "approval_wait",
  "retry_pending",
  "stale_claim",
  "prepared_dispatch",
  "started_unknown_terminal",
  "succeeded",
  "failed",
  "dependency_blocked",
  "recovery_required",
  "cancelled",
]);

function isSafeAuthorityMissionRef(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length > 0 &&
    value.length <= 320 &&
    !/[\\/\r\n]/u.test(value)
  );
}

function isSafeAuthorityMissionText(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length > 0 &&
    value.length <= 720 &&
    !/[\\/\r\n]/u.test(value)
  );
}

function isAuthorityMissionStringArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.length <= 64 &&
    value.every(isSafeAuthorityMissionRef)
  );
}

function isOptionalMissionTimestamp(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

function isSafeAuthorityMissionWorkerStep(
  value: unknown,
): value is AuthorityMissionWorkerStepRecovery {
  if (!isPlainRecord(value)) {
    return false;
  }
  return (
    isSafeAuthorityMissionRef(value.step_safe_ref) &&
    typeof value.status === "string" &&
    AUTHORITY_MISSION_RECOVERY_STATUSES.has(value.status) &&
    ["active", "stale", "not_claimed", "unknown"].includes(
      String(value.claim_freshness),
    ) &&
    Number.isInteger(value.generation) &&
    Number(value.generation) >= 0 &&
    isAuthorityMissionStringArray(value.reason_refs) &&
    isAuthorityMissionStringArray(value.evidence_refs) &&
    value.adapter_reinvocation_allowed === false
  );
}

function isSafeAuthorityMissionWorkerJob(
  value: unknown,
): value is AuthorityMissionWorkerJob {
  if (!isPlainRecord(value)) {
    return false;
  }
  const safeOptionalRef = (candidate: unknown) =>
    candidate === null || isSafeAuthorityMissionRef(candidate);
  return (
    [
      value.job_safe_ref,
      value.plan_safe_ref,
      value.mission_safe_ref,
      value.run_safe_ref,
    ].every(isSafeAuthorityMissionRef) &&
    typeof value.durable_status === "string" &&
    AUTHORITY_MISSION_WORKER_STATUSES.has(value.durable_status) &&
    typeof value.recovery_status === "string" &&
    AUTHORITY_MISSION_RECOVERY_STATUSES.has(value.recovery_status) &&
    Number.isInteger(value.generation) &&
    Number(value.generation) >= 0 &&
    [
      "enqueued",
      "claimed",
      "heartbeat",
      "deferred",
      "completed",
      "shutdown",
    ].includes(String(value.latest_event)) &&
    typeof value.latest_event_at === "string" &&
    isOptionalMissionTimestamp(value.last_heartbeat_at) &&
    ["active", "stale", "not_observed"].includes(
      String(value.heartbeat_freshness),
    ) &&
    safeOptionalRef(value.worker_safe_ref) &&
    safeOptionalRef(value.claim_safe_ref) &&
    isOptionalMissionTimestamp(value.claim_expires_at) &&
    isOptionalMissionTimestamp(value.retry_not_before) &&
    typeof value.deadline === "string" &&
    Array.isArray(value.steps) &&
    value.steps.length <= 16 &&
    value.steps.every(isSafeAuthorityMissionWorkerStep) &&
    isAuthorityMissionStringArray(value.reason_refs) &&
    isAuthorityMissionStringArray(value.evidence_refs) &&
    value.request_payload_persisted === false &&
    value.request_scoped_authority_required_before_resume === true
  );
}

function isSafeAuthorityMissionWorkerReadModel(
  value: unknown,
): value is AuthorityMissionWorkerReadModel {
  if (!isPlainRecord(value)) {
    return false;
  }
  const nonnegativeIntegerFields = [
    "queue_capacity",
    "queued_job_count",
    "total_job_count",
    "omitted_terminal_job_count",
    "active_claim_count",
    "stale_claim_count",
  ];
  return (
    value.schema_version === "uaa-local-mission-worker.v1" &&
    isSafeAuthorityMissionRef(value.inspection_ref) &&
    typeof value.configuration_enabled === "boolean" &&
    value.canonical_platform === "macos" &&
    [
      "macos",
      "linux_placeholder",
      "windows_placeholder",
      "unsupported",
    ].includes(String(value.observed_platform)) &&
    typeof value.platform_execution_supported === "boolean" &&
    value.linux_surface_posture === "render_placeholder" &&
    value.windows_surface_posture === "render_placeholder" &&
    nonnegativeIntegerFields.every(
      (field) => Number.isInteger(value[field]) && Number(value[field]) >= 0,
    ) &&
    typeof value.kill_switch_engaged === "boolean" &&
    Array.isArray(value.jobs) &&
    value.jobs.length <= 32 &&
    value.jobs.every(isSafeAuthorityMissionWorkerJob) &&
    typeof value.checked_at === "string" &&
    isSafeAuthorityMissionText(value.operator_summary) &&
    value.local_only === true &&
    value.execution_authority_granted === false &&
    value.approval_or_lease_minted === false &&
    value.remote_queue_enabled === false &&
    value.daemon_enabled === false &&
    value.raw_task_input_persisted === false &&
    value.raw_paths_included === false &&
    value.raw_logs_included === false &&
    value.raw_provider_payloads_included === false &&
    isAuthorityMissionStringArray(value.redactions_applied)
  );
}

function isSafeAuthorityMissionCompletionReadModel(
  value: unknown,
): value is AuthorityMissionCompletionReadModel {
  if (!isPlainRecord(value) || !Array.isArray(value.latest_manifests)) {
    return false;
  }
  const integrity = value.integrity_summary;
  const portable = value.portable_evidence_summary;
  if (
    !isPlainRecord(integrity) ||
    integrity.schema_version !==
      "uaa-mission-completion-integrity-summary.v1" ||
    !isSafeAuthorityMissionRef(integrity.verifier_version_ref) ||
    !Number.isInteger(integrity.manifest_count) ||
    Number(integrity.manifest_count) !== Number(value.completion_count) ||
    !isSafeAuthorityMissionRef(integrity.chain_ref) ||
    (integrity.genesis_entry_hash_ref !== null &&
      !isSafeAuthorityMissionRef(integrity.genesis_entry_hash_ref)) ||
    (integrity.terminal_entry_hash_ref !== null &&
      !isSafeAuthorityMissionRef(integrity.terminal_entry_hash_ref)) ||
    integrity.hash_chain_verified !== true ||
    integrity.source_ledgers_verified !== false ||
    integrity.signature_present !== false ||
    integrity.signing_status !==
      "blocked_signing_lifecycle_not_implemented" ||
    integrity.cryptographic_authenticity_verified !== false ||
    integrity.external_anchor_verified !== false ||
    integrity.execution_evidence_grants_authority !== false
  ) {
    return false;
  }
  if (
    !isPlainRecord(portable) ||
    portable.schema_version !==
      "uaa-portable-mission-evidence-inspection.v1" ||
    ![
      "verified_local_hash_chain",
      "not_recorded",
      "not_evaluated",
      "unavailable",
    ].includes(String(portable.status)) ||
    (portable.bundle_ref !== null &&
      !isSafeAuthorityMissionRef(portable.bundle_ref)) ||
    !Number.isInteger(portable.completion_count) ||
    Number(portable.completion_count) < 0 ||
    Number(portable.completion_count) !== Number(value.completion_count) ||
    !Number.isInteger(portable.envelope_count) ||
    Number(portable.envelope_count) < 0 ||
    (portable.terminal_entry_hash_ref !== null &&
      !isSafeAuthorityMissionRef(portable.terminal_entry_hash_ref)) ||
    typeof portable.local_hash_chain_verified !== "boolean" ||
    typeof portable.source_receipts_bound !== "boolean" ||
    portable.source_ledgers_verified !== false ||
    portable.caller_expected_binding_matched !== false ||
    portable.signature_verified !== false ||
    portable.signing_status !==
      "blocked_signing_lifecycle_not_implemented" ||
    portable.cryptographic_authenticity_verified !== false ||
    portable.external_anchor_verified !== false ||
    portable.execution_evidence_grants_authority !== false ||
    !isAuthorityMissionStringArray(portable.reason_refs)
  ) {
    return false;
  }
  const portableVerified = portable.status === "verified_local_hash_chain";
  if (
    portableVerified !== portable.local_hash_chain_verified ||
    portableVerified !== portable.source_receipts_bound ||
    (portableVerified &&
      (!isSafeAuthorityMissionRef(portable.bundle_ref) ||
        !isSafeAuthorityMissionRef(portable.terminal_entry_hash_ref) ||
        Number(portable.completion_count) < 1 ||
        Number(portable.envelope_count) < 1)) ||
    (!portableVerified &&
      (portable.bundle_ref !== null ||
        portable.terminal_entry_hash_ref !== null ||
        Number(portable.envelope_count) !== 0))
  ) {
    return false;
  }
  if (
    (Number(integrity.manifest_count) === 0 &&
      (integrity.genesis_entry_hash_ref !== null ||
        integrity.terminal_entry_hash_ref !== null)) ||
    (Number(integrity.manifest_count) > 0 &&
      (!isSafeAuthorityMissionRef(integrity.genesis_entry_hash_ref) ||
        !isSafeAuthorityMissionRef(integrity.terminal_entry_hash_ref)))
  ) {
    return false;
  }
  return (
    value.schema_version === "uaa-mission-completion-read-model.v1" &&
    isSafeAuthorityMissionRef(value.ledger_ref) &&
    Number.isInteger(value.completion_count) &&
    Number(value.completion_count) >= 0 &&
    value.latest_manifests.length <= 12 &&
    value.latest_manifests.every((manifest) => {
      if (
        !isPlainRecord(manifest) ||
        !Array.isArray(manifest.step_bindings) ||
        !Array.isArray(manifest.dispatch_bindings) ||
        !Array.isArray(manifest.budget_bindings) ||
        !Array.isArray(manifest.approval_refs) ||
        !Array.isArray(manifest.approval_validation_refs) ||
        !Array.isArray(manifest.control_receipt_refs) ||
        !Array.isArray(manifest.cancellation_receipt_refs) ||
        !Array.isArray(manifest.dead_letter_receipt_refs) ||
        !Array.isArray(manifest.redactions_applied) ||
        !Array.isArray(manifest.evidence_refs)
      ) {
        return false;
      }
      const stepBindings = manifest.step_bindings;
      const dispatchBindings = manifest.dispatch_bindings;
      const budgetBindings = manifest.budget_bindings;
      const boundApprovalRefs = dispatchBindings.flatMap((dispatch) =>
        isPlainRecord(dispatch) && typeof dispatch.approval_ref === "string"
          ? [dispatch.approval_ref]
          : [],
      );
      const boundApprovalValidationRefs = dispatchBindings.flatMap((dispatch) =>
        isPlainRecord(dispatch) &&
        typeof dispatch.approval_validation_ref === "string"
          ? [dispatch.approval_validation_ref]
          : [],
      );
      return (
        manifest.schema_version === "uaa-mission-completion.v1" &&
        [
          manifest.completion_ref,
          manifest.plan_ref,
          manifest.plan_fingerprint_ref,
          manifest.plan_receipt_ref,
          manifest.plan_entry_hash_ref,
          manifest.mission_ref,
          manifest.run_ref,
          manifest.lease_ref,
          manifest.lease_mission_ref,
          manifest.control_snapshot_ref,
          manifest.memory_candidate_ref,
          manifest.entry_hash_ref,
        ].every(isSafeAuthorityMissionRef) &&
        (manifest.lease_scope_fingerprint_ref === null ||
          isSafeAuthorityMissionRef(manifest.lease_scope_fingerprint_ref)) &&
        (manifest.previous_entry_hash_ref === null ||
          isSafeAuthorityMissionRef(manifest.previous_entry_hash_ref)) &&
        typeof manifest.lease_issued_at === "string" &&
        typeof manifest.lease_expires_at === "string" &&
        typeof manifest.mission_deadline === "string" &&
        typeof manifest.created_at === "string" &&
        manifest.lease_scope === "mission" &&
        manifest.lease_mission_ref === manifest.mission_ref &&
        manifest.status === "succeeded" &&
        manifest.concurrency_limit === 1 &&
        manifest.parallel_execution_performed === false &&
        stepBindings.length >= 1 &&
        stepBindings.length <= 16 &&
        dispatchBindings.length === stepBindings.length &&
        budgetBindings.length === stepBindings.length &&
        stepBindings.every(
          (step) =>
            isPlainRecord(step) &&
            [
              step.step_ref,
              step.definition_fingerprint_ref,
              step.dispatch_ref,
              step.dispatch_request_fingerprint_ref,
              step.step_receipt_ref,
              step.step_entry_hash_ref,
              step.dispatch_receipt_ref,
              step.dispatch_entry_hash_ref,
            ].every(isSafeAuthorityMissionRef) &&
            isAuthorityMissionStringArray(step.evidence_refs),
        ) &&
        dispatchBindings.every(
          (dispatch, index) => {
            if (!isPlainRecord(dispatch)) {
              return false;
            }
            const step = stepBindings[index];
            return (
              [
                dispatch.dispatch_ref,
                dispatch.receipt_ref,
                dispatch.entry_hash_ref,
                dispatch.request_fingerprint_ref,
                dispatch.lease_ref,
                dispatch.action_ref,
                dispatch.adapter_ref,
                dispatch.capability_ref,
                dispatch.authority_decision_ref,
                dispatch.authority_policy_receipt_ref,
                dispatch.budget_reservation_ref,
                dispatch.budget_reservation_receipt_ref,
                dispatch.budget_start_receipt_ref,
                dispatch.budget_settlement_receipt_ref,
                dispatch.execution_ref,
                dispatch.actual_cost_ref,
              ].every(isSafeAuthorityMissionRef) &&
              typeof dispatch.approval_required === "boolean" &&
              (!dispatch.approval_required ||
                (isSafeAuthorityMissionRef(dispatch.approval_ref) &&
                  isSafeAuthorityMissionRef(
                    dispatch.approval_validation_ref,
                  ))) &&
              (dispatch.approval_ref === null ||
                isSafeAuthorityMissionRef(dispatch.approval_ref)) &&
              (dispatch.approval_validation_ref === null ||
                isSafeAuthorityMissionRef(dispatch.approval_validation_ref)) &&
              Number.isInteger(dispatch.actual_operation_count) &&
              Number(dispatch.actual_operation_count) >= 1 &&
              Number.isInteger(dispatch.actual_cost_microusd) &&
              Number(dispatch.actual_cost_microusd) >= 0 &&
              isAuthorityMissionStringArray(dispatch.evidence_refs) &&
              isPlainRecord(step) &&
              step.dispatch_ref === dispatch.dispatch_ref &&
              step.dispatch_receipt_ref === dispatch.receipt_ref &&
              step.dispatch_entry_hash_ref === dispatch.entry_hash_ref &&
              step.dispatch_request_fingerprint_ref ===
                dispatch.request_fingerprint_ref
            );
          },
        ) &&
        budgetBindings.every(
          (budget, index) => {
            const dispatch = dispatchBindings[index];
            return (
            isPlainRecord(budget) &&
            [
              budget.reservation_ref,
              budget.reserve_receipt_ref,
              budget.reserve_entry_hash_ref,
              budget.start_receipt_ref,
              budget.start_entry_hash_ref,
              budget.settlement_receipt_ref,
              budget.settlement_entry_hash_ref,
              budget.lease_ref,
              budget.action_ref,
              budget.execution_ref,
              budget.actual_cost_ref,
            ].every(isSafeAuthorityMissionRef) &&
            budget.settlement_status === "settled" &&
            budget.unresolved_cost === false &&
            Number.isInteger(budget.reserved_operation_count) &&
            Number(budget.reserved_operation_count) >= 1 &&
            Number.isInteger(budget.reserved_cost_microusd) &&
            Number(budget.reserved_cost_microusd) >= 0 &&
            Number.isInteger(budget.actual_operation_count) &&
            Number(budget.actual_operation_count) >= 1 &&
            Number.isInteger(budget.actual_cost_microusd) &&
            Number(budget.actual_cost_microusd) >= 0 &&
            isPlainRecord(dispatch) &&
            dispatch.budget_reservation_ref === budget.reservation_ref &&
            dispatch.budget_reservation_receipt_ref ===
              budget.reserve_receipt_ref &&
            dispatch.budget_start_receipt_ref === budget.start_receipt_ref &&
            dispatch.budget_settlement_receipt_ref ===
              budget.settlement_receipt_ref &&
            dispatch.lease_ref === budget.lease_ref &&
            dispatch.action_ref === budget.action_ref &&
            dispatch.execution_ref === budget.execution_ref &&
            dispatch.actual_operation_count === budget.actual_operation_count &&
            dispatch.actual_cost_microusd === budget.actual_cost_microusd &&
            dispatch.actual_cost_ref === budget.actual_cost_ref &&
            dispatch.lease_ref === manifest.lease_ref &&
            budget.lease_ref === manifest.lease_ref
            );
          },
        ) &&
        isAuthorityMissionStringArray(manifest.approval_refs) &&
        isAuthorityMissionStringArray(manifest.approval_validation_refs) &&
        manifest.approval_refs.length === boundApprovalRefs.length &&
        manifest.approval_refs.every(
          (ref, index) => ref === boundApprovalRefs[index],
        ) &&
        manifest.approval_validation_refs.length ===
          boundApprovalValidationRefs.length &&
        manifest.approval_validation_refs.every(
          (ref, index) => ref === boundApprovalValidationRefs[index],
        ) &&
        isAuthorityMissionStringArray(manifest.control_receipt_refs) &&
        isAuthorityMissionStringArray(manifest.cancellation_receipt_refs) &&
        isAuthorityMissionStringArray(manifest.dead_letter_receipt_refs) &&
        isAuthorityMissionStringArray(manifest.redactions_applied) &&
        isAuthorityMissionStringArray(manifest.evidence_refs) &&
        manifest.memory_candidate_posture === "review_required_recall_only" &&
        manifest.memory_truth_authority === false &&
        manifest.context_injection_authorized === false &&
        manifest.execution_evidence_grants_authority === false &&
        manifest.signature_present === false &&
        manifest.integrity_posture === "content_free_hash_chain" &&
        manifest.raw_paths_included === false &&
        manifest.raw_prompt_included === false &&
        manifest.raw_response_included === false &&
        manifest.raw_provider_payload_included === false
      );
    }) &&
    value.latest_manifests.length <= Number(value.completion_count) &&
    isSafeAuthorityMissionText(value.operator_summary) &&
    value.request_scoped_authority_still_required === true &&
    value.execution_available_from_read_model === false &&
    value.approval_or_lease_minted === false &&
    value.raw_content_included === false &&
    value.raw_paths_included === false &&
    value.source_ledgers_verified === false
  );
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
  return safeApiErrorMessage(data, fallback);
}
