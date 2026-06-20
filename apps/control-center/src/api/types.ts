export type CapabilityStatus =
  | "available_read_only"
  | "preview_only"
  | "validation_only"
  | "planned_disabled"
  | "blocked"
  | "not_implemented"
  | "dry_run_only"
  | "manual_only";

export type ControlCenterActionStatus =
  | "allowed_preview"
  | "approval_required"
  | "blocked";

export type BackendConnectionState =
  | "unknown"
  | "checking"
  | "online"
  | "offline"
  | "degraded"
  | "mock_fallback";

export interface BackendConnectionSummary {
  state: BackendConnectionState;
  apiBaseLabel: string;
  checkedAt: string;
  safeMessage: string;
  usingMockData: boolean;
  warnings: string[];
}

export interface ResultEnvelope<T> {
  success?: boolean;
  ok: boolean;
  data?: T;
  result?: T;
  error?: {
    code: string;
    message: string;
    details?: unknown;
  };
}

export interface StatusCard {
  label: string;
  status: string;
  summary: string;
}

export interface GateSummary {
  status: string;
  passed_count: number;
  failed_count: number;
  summary: string;
}

export interface RuntimeReadinessSummary {
  status: string;
  production_ready: boolean;
  real_model_runtime_ready: boolean;
  remote_execution_ready: boolean;
  mobile_sensor_ready: boolean;
  plugin_or_native_build_ready: boolean;
}

export interface ApprovalSummary {
  pending_count: number;
  approval_grants_created: boolean;
  arbitrary_approval_ref_authority: boolean;
  summary: string;
}

export interface ApiSummary {
  route_count: number;
  control_center_route_count: number;
  operation_ids_unique: boolean;
  execution_routes_present: boolean;
}

export interface FounderLoopActionItem {
  item_ref: string;
  title: string;
  safe_summary: string;
  surface: string;
  priority: string;
  risk_class: string;
  status: string;
  side_effect_class: string;
  authority_boundary: string;
  approval_required: boolean;
  approval_envelope_ref?: string | null;
  approval_envelope_status: string;
  state_change_contract_ref?: string | null;
  state_change_readiness: string;
  blocked_state?: string | null;
  evidence_refs: string[];
  receipt_refs: string[];
  audit_refs: string[];
  idempotency_key_ref?: string | null;
  expires_at?: string | null;
  stale_state: string;
  rollback_ref?: string | null;
  safe_disable_ref?: string | null;
  next_safe_action: string;
  created_at?: string;
  updated_at?: string;
}

export interface FounderLoopPlanSummary {
  plan_ref: string;
  title: string;
  status: string;
  safe_summary: string;
  next_step_summary: string;
  evidence_refs: string[];
  updated_at?: string;
}

export interface FounderLoopMemoryReviewItem {
  review_ref: string;
  title: string;
  safe_summary: string;
  candidate_kind: string;
  priority: string;
  status: string;
  review_state: string;
  side_effect_class: string;
  authority_boundary: string;
  provenance_refs: string[];
  source_refs: string[];
  missing_contract_refs: string[];
  correction_posture: string;
  rejection_posture: string;
  retention_posture: string;
  delete_posture: string;
  confidence_posture: string;
  stale_state: string;
  blocked_states: string[];
  next_safe_action: string;
  evidence_refs: string[];
  created_at?: string;
}

export interface FounderLoopBriefingItem {
  briefing_ref: string;
  title: string;
  safe_summary: string;
  priority: string;
  status: string;
  side_effect_class: string;
  authority_boundary: string;
  source_readiness: string;
  source_refs: string[];
  missing_contract_refs: string[];
  blocked_states: string[];
  stale_state: string;
  evidence_gap: string;
  next_safe_action: string;
  evidence_refs: string[];
  created_at?: string;
}

export interface FounderLoopTodaySummary {
  schema_version: string;
  status: string;
  surface: string;
  storage_ref: string;
  side_effect_class: string;
  approval_required_before_mutation: boolean;
  sections: {
    action_inbox_count: number;
    plan_count: number;
    memory_review_count: number;
    briefing_count: number;
  };
  actions: FounderLoopActionItem[];
  plans: FounderLoopPlanSummary[];
  memory_review_queue: FounderLoopMemoryReviewItem[];
  memory_review_route_ref: string;
  memory_review_backend_route_ref: string;
  memory_review_status: string;
  memory_review_authority_boundary: string;
  memory_write_enabled: boolean;
  memory_delete_enabled: boolean;
  context_injection_enabled: boolean;
  memory_review_missing_contract_refs: string[];
  memory_review_blocked_states: string[];
  briefing_items: FounderLoopBriefingItem[];
  evidence_refs: string[];
  blocked_states: string[];
}

export interface FounderLoopActionsInbox {
  schema_version: string;
  status: string;
  surface: string;
  storage_ref: string;
  side_effect_class: string;
  route_ref: string;
  read_only_route_refs: string[];
  local_prerequisite_refs: string[];
  items: FounderLoopActionItem[];
  approval_required_before_mutation: boolean;
  mutating_controls_enabled: boolean;
  disabled_state_label: string;
  evidence_refs: string[];
  blocked_states: string[];
}

export interface FounderLoopMorningBriefing {
  schema_version: string;
  status: string;
  surface: string;
  storage_ref: string;
  side_effect_class: string;
  route_ref: string;
  read_only_route_refs: string[];
  local_prerequisite_refs: string[];
  source_readiness: string;
  authority_boundary: string;
  bounded_preview_only: boolean;
  refresh_enabled: boolean;
  notification_delivery_enabled: boolean;
  missing_contract_refs: string[];
  items: FounderLoopBriefingItem[];
  evidence_refs: string[];
  blocked_states: string[];
}

export interface FounderLoopStorageStatus {
  schema_version: string;
  migration_version: string;
  storage_ref: string;
  sqlite_state_ref: string;
  jsonl_log_refs: Record<string, string>;
  counts: Record<string, number>;
  safe_refs_only: boolean;
  raw_content_stored: boolean;
  postgres_sync_required: boolean;
  postgres_sync_status: string;
  backup_manifest_ref: string;
  backup_manifest?: {
    schema_version: string;
    manifest_ref: string;
    required_artifact_refs: string[];
    raw_paths_included: boolean;
    raw_logs_included: boolean;
    safe_refs_only: boolean;
  };
  updated_at: string;
}

export interface RemoteWorkerSummary {
  status: string;
  execution_enabled: boolean;
  dispatch_enabled: boolean;
}

export interface PrivateMeshSummary {
  status: string;
  headscale_integrated: boolean;
  tailscale_integrated: boolean;
  wireguard_integrated: boolean;
}

export interface MobilePlanningSummary {
  status: string;
  sensor_access_enabled: boolean;
  mobile_app_implemented: boolean;
}

export interface PluginGovernanceSummary {
  status: string;
  plugin_enablement_allowed: boolean;
  native_build_tools_enabled: boolean;
}

export interface ProviderCredentialReadinessItem {
  provider_id: string;
  provider_label: string;
  provider_kind: string;
  provider_manifest_ref: string;
  credential_ref: string;
  credential_ref_status: string;
  consent_ref: string;
  policy_ref: string;
  revocation_ref: string;
  approval_ref: string;
  risk_class: string;
  invocation_enabled: boolean;
  credential_material_stored: boolean;
  raw_key_visible: boolean;
  readiness_status: string;
  blocker_codes: string[];
  safe_summary: string;
}

export interface ProviderCredentialVaultAdapterReadiness {
  credential_ref: string;
  provider_id: string;
  consent_ref: string;
  policy_ref: string;
  approval_ref: string;
  revocation_ref: string;
  storage_backend_kind: string;
  adapter_available: boolean;
  supports_write: boolean;
  supports_read_handle: boolean;
  supports_revoke: boolean;
  credential_material_stored_by_repo: boolean;
  raw_key_visible: boolean;
  adapter_runtime_enabled: boolean;
  last_validation_ref: string;
  readiness_status: string;
  blocker_codes: string[];
  safe_summary: string;
}

export interface ProviderCredentialEnrollmentReadiness {
  provider_manifest_ref: string;
  credential_ref: string;
  consent_ref: string;
  policy_ref: string;
  approval_ref: string;
  revocation_ref: string;
  idempotency_key_ref: string;
  audit_ref: string;
  rollback_ref: string;
  safe_disable_ref: string;
  enrollment_enabled: boolean;
  raw_key_collection_enabled: boolean;
  credential_material_stored_by_repo: boolean;
  evidence_contains_credential_material: boolean;
  readiness_status: string;
  blocker_codes: string[];
  safe_summary: string;
}

export interface ProviderCredentialValidationReadiness {
  provider_manifest_ref: string;
  credential_ref: string;
  consent_ref: string;
  policy_ref: string;
  approval_ref: string;
  revocation_ref: string;
  validation_enabled: boolean;
  external_validation_allowed: boolean;
  provider_response_persistence_allowed: boolean;
  validation_receipt_ref: string;
  readiness_status: string;
  blocker_codes: string[];
  safe_summary: string;
}

export interface GovernedProviderInvocationReadiness {
  readiness_status: string;
  invocation_enabled: boolean;
  policy_engine_required: boolean;
  local_approval_required: boolean;
  credential_ref_required: boolean;
  provider_manifest_allowlist_required: boolean;
  redacted_request_summary_only: boolean;
  redacted_response_summary_only: boolean;
  receipt_refs_required: boolean;
  audit_refs_required: boolean;
  rollback_or_safe_disable_required: boolean;
  rate_budget_boundary_required: boolean;
  model_output_authoritative: boolean;
  streaming_enabled: boolean;
  tools_functions_enabled: boolean;
  memory_write_enabled: boolean;
  context_injection_enabled: boolean;
  browser_network_automation_enabled: boolean;
  connector_writes_enabled: boolean;
  blocker_codes: string[];
  safe_summary: string;
}

export interface ProviderCredentialReadinessSummary {
  status: string;
  safe_summary: string;
  invocation_enabled: boolean;
  raw_key_collection_enabled: boolean;
  credential_material_stored: boolean;
  vault_adapter_configured: boolean;
  vault_adapter_readiness: ProviderCredentialVaultAdapterReadiness;
  enrollment_readiness: ProviderCredentialEnrollmentReadiness;
  validation_readiness: ProviderCredentialValidationReadiness;
  invocation_readiness: GovernedProviderInvocationReadiness;
  providers: ProviderCredentialReadinessItem[];
  blocker_codes: string[];
  future_gate: string;
}

export interface OperatorLoopStepSummary {
  step_id: string;
  label: string;
  status: string;
  safe_summary: string;
  route_refs: string[];
  evidence_refs: string[];
  next_safe_action: string;
  authority_boundary: string;
  frontend_authority: boolean;
  control_center_mutation_allowed: boolean;
  backend_authority_required: boolean;
  approval_required: boolean;
  prompt_content_recorded: boolean;
  provider_payload_recorded: boolean;
  model_output_authoritative: boolean;
  metadata: Record<string, boolean | string | number>;
}

export interface OperatorLoopSummary {
  loop_id: string;
  milestone_ref: string;
  status: string;
  safe_summary: string;
  backend_authority: string;
  frontend_authority: boolean;
  production_ready: boolean;
  read_only_dashboard: boolean;
  control_center_mutation_allowed: boolean;
  model_output_authoritative: boolean;
  prompt_content_recording_allowed: boolean;
  provider_payload_recording_allowed: boolean;
  steps: OperatorLoopStepSummary[];
  blocked_prerequisites: string[];
  inspection_route_refs: string[];
  next_safe_action: string;
  metadata: Record<string, boolean | string | number>;
}

export interface ControlCenterDashboardSnapshot {
  snapshot_id: string;
  baseline_version: string;
  generated_at: string;
  system_status: StatusCard;
  foundation_gate_summary: GateSummary;
  runtime_readiness_summary: RuntimeReadinessSummary;
  approval_summary: ApprovalSummary;
  api_summary: ApiSummary;
  remote_worker_summary: RemoteWorkerSummary;
  private_mesh_summary: PrivateMeshSummary;
  mobile_planning_summary: MobilePlanningSummary;
  plugin_governance_summary: PluginGovernanceSummary;
  provider_credential_readiness: ProviderCredentialReadinessSummary;
  operator_loop_summary?: OperatorLoopSummary;
  warnings: string[];
  blockers: string[];
  next_recommended_action: string;
  metadata: Record<string, boolean | string>;
}

export interface ControlCenterSurfaceManifest {
  surface: string;
  status: CapabilityStatus;
  description: string;
  route_refs: string[];
  execution_allowed: boolean;
  mutation_allowed: boolean;
  credential_resolution_allowed: boolean;
  approval_grant_allowed: boolean;
  metadata: Record<string, boolean | string | number>;
}

export interface ControlCenterManifest {
  manifest_id: string;
  version: string;
  generated_at: string;
  surfaces: ControlCenterSurfaceManifest[];
  declared_capabilities: string[];
  blocked_capabilities: string[];
  api_route_refs: string[];
  metadata: Record<string, boolean | string | number>;
}

export interface ControlCenterStatus {
  status: string;
  read_only: boolean;
  preview_only: boolean;
  frontend_shell: boolean;
  production_authority: boolean;
  message: string;
}

export interface ApiRouteSummary {
  path: string;
  methods: string[];
  operation_id: string;
  tags: string[];
  validation_only: boolean;
}

export interface ApiRouteInventory {
  route_count: number;
  routes: ApiRouteSummary[];
}

export interface RuntimeReadinessReport {
  report_id: string;
  baseline_version: string;
  status: string;
  production_ready: boolean;
  real_model_runtime_ready: boolean;
  remote_execution_ready: boolean;
  mobile_sensor_ready: boolean;
  plugin_or_native_build_ready: boolean;
  capability_matrix_ref: string;
  warnings: string[];
  blockers: string[];
  metadata: Record<string, boolean | string | number>;
}

export interface RuntimeCapabilityEntry {
  surface: string;
  status: string;
  risk_class: string;
  real_network_allowed: boolean;
  real_model_call_allowed: boolean;
  cloud_allowed: boolean;
  user_content_allowed: boolean;
  secrets_allowed: boolean;
  summary: string;
}

export interface RuntimeCapabilityMatrix {
  matrix_id: string;
  baseline_version: string;
  entries: RuntimeCapabilityEntry[];
  metadata: Record<string, boolean | string | number>;
}

export type OperatorRouteInspectionState =
  | "checking"
  | "ready"
  | "blocked"
  | "denied"
  | "degraded"
  | "unavailable";

export interface LocalModelsInspectionStatus {
  state: OperatorRouteInspectionState;
  routeRef: string;
  checkedAt: string;
  safeMessage: string;
  modelIds: string[];
  selectedModelId?: string;
  statusCode?: number;
  reasonCodes: string[];
}

export interface RedactedLocalChatProbeStatus {
  state: OperatorRouteInspectionState;
  routeRef: string;
  checkedAt: string;
  safeMessage: string;
  modelId: string;
  statusCode?: number;
  durationMs?: number;
  responseVisible: false;
  reasonCodes: string[];
}

export interface ActionPreviewRequest {
  request_id: string;
  actor_context: Record<string, string>;
  action_kind:
    | "view_status"
    | "view_receipt"
    | "view_event_summary"
    | "preview_action"
    | "preview_approval"
    | "preview_runtime"
    | "preview_remote_worker"
    | "preview_mobile_capability";
  target_ref: string;
  purpose: string;
  risk_level: "safe" | "low" | "medium" | "high" | "critical";
  data_classification: string;
  consent_refs: string[];
  metadata: Record<string, string | boolean | number>;
}

export interface ActionPreviewDecision {
  decision_id: string;
  request_id: string;
  allowed: boolean;
  status: ControlCenterActionStatus;
  reason_codes: string[];
  safe_message: string;
  required_next_action?: string | null;
  preview_summary: string;
  metadata: Record<string, boolean | string | string[]>;
}

export type ReviewRiskLevel = "low" | "medium" | "high" | "critical";

export interface ApprovalQueueItem {
  approvalRef: string;
  status: "pending_review" | "preview_only" | "blocked" | "expired";
  riskLevel: ReviewRiskLevel;
  dataClassification: string;
  actorSummary: string;
  requestedActionSummary: string;
  subjectSummary: string;
  reasonCodes: string[];
  createdAt: string;
  expiresAt?: string;
  requiredNextAction: string;
  safeMessage: string;
  previewOutcomeSummary: string;
  relatedRefs: string[];
  previewOnly: boolean;
  readOnly: boolean;
  mock: boolean;
}

export interface ReceiptSummaryItem {
  receiptRef: string;
  eventRefs: string[];
  actionTypeSummary: string;
  actorSummary: string;
  status: string;
  riskLevel: ReviewRiskLevel;
  dataClassification: string;
  redactionStatus: "redacted_summary_only";
  safeMessage: string;
  timestamp: string;
  relatedRefs: string[];
  previewOnly: boolean;
  readOnly: boolean;
  mock: boolean;
}

export interface EventSummaryItem {
  eventRef: string;
  eventType: string;
  actorSummary: string;
  sourceSurface: string;
  resultStatus: string;
  reasonCodes: string[];
  timestamp: string;
  relatedRefs: string[];
  redactionStatus: "redacted_summary_only";
  safeMessage: string;
  previewOnly: boolean;
  readOnly: boolean;
  mock: boolean;
}

export interface M15ReviewData {
  status: "mock_preview_only" | "summary_only";
  readOnly: boolean;
  previewOnly: boolean;
  mock: boolean;
  nonAuthoritative: boolean;
  authorityBoundary: string;
  warningCodes: string[];
  approvalQueue: ApprovalQueueItem[];
  receipts: ReceiptSummaryItem[];
  events: EventSummaryItem[];
}

export interface TimelineEventSummaryItem {
  eventRef: string;
  eventType: string;
  sourceSurface: string;
  actorSummary: string;
  timestamp: string;
  status: string;
  runRef: string;
  correlationRef: string;
  parentEventRef?: string;
  childEventRefs: string[];
  receiptRefs: string[];
  evidenceRefs: string[];
  redactionStatus: "redacted_summary_only";
  safeMessage: string;
  previewOnly: boolean;
  readOnly: boolean;
  mock: boolean;
}

export interface TraceRelationSummaryItem {
  relationRef: string;
  relationType: "parent" | "child" | "receipt" | "evidence" | "correlation";
  fromRef: string;
  toRef: string;
  safeSummary: string;
  redactionStatus: "redacted_summary_only";
}

export interface FoundationGateEvidenceSummaryItem {
  evidenceRef: string;
  criterionRef: string;
  status: string;
  receiptRefs: string[];
  eventRefs: string[];
  safeSummary: string;
  redactionStatus: "redacted_summary_only";
}

export interface M16TraceData {
  status: "mock_preview_only" | "summary_only";
  readOnly: boolean;
  previewOnly: boolean;
  mock: boolean;
  nonAuthoritative: boolean;
  boundarySummary: string;
  warningCodes: string[];
  timelineEvents: TimelineEventSummaryItem[];
  traceRelations: TraceRelationSummaryItem[];
  foundationGateEvidence: FoundationGateEvidenceSummaryItem[];
}

export interface EvidenceSummaryItem {
  evidenceRef: string;
  evidenceType: string;
  sourceType: string;
  sourceRef: string;
  claimRefs: string[];
  eventRefs: string[];
  receiptRefs: string[];
  fileRefs: string[];
  memoryRefs: string[];
  confidenceStatus: string;
  redactionStatus: "redacted_summary_only";
  dataClassification: string;
  safeSummary: string;
  provenanceSummary: string;
  timestamp: string;
  previewOnly: boolean;
  readOnly: boolean;
  mock: boolean;
}

export interface FileReferenceSummaryItem {
  fileRef: string;
  fileKind: string;
  safeFilename: string;
  sizeSummary: string;
  dataClassification: string;
  sourceSurface: string;
  eventRefs: string[];
  receiptRefs: string[];
  evidenceRefs: string[];
  redactionStatus: "redacted_summary_only";
  safeMetadataSummary: string;
  pathDisclosure: string;
  previewOnly: boolean;
  readOnly: boolean;
  mock: boolean;
}

export interface MemorySummaryItem {
  memoryRef: string;
  memoryType: string;
  sourceRefs: string[];
  confidenceStatus: string;
  reviewStatus: string;
  staleStatus: string;
  conflictStatus: string;
  dataClassification: string;
  redactionStatus: "redacted_summary_only";
  safeSummary: string;
  relatedEventRefs: string[];
  relatedReceiptRefs: string[];
  relatedEvidenceRefs: string[];
  authorityNotice: string;
  previewOnly: boolean;
  readOnly: boolean;
  mock: boolean;
}

export interface M17KnowledgeData {
  status: "mock_preview_only" | "summary_only";
  readOnly: boolean;
  previewOnly: boolean;
  mock: boolean;
  nonAuthoritative: boolean;
  boundarySummary: string;
  warningCodes: string[];
  evidence: EvidenceSummaryItem[];
  fileRefs: FileReferenceSummaryItem[];
  memories: MemorySummaryItem[];
}

export interface LocalRuntimeSurfaceSummaryItem {
  surfaceRef: string;
  status: string;
  riskClass: string;
  sourceRoute: string;
  realModelCallAllowed: boolean;
  realNetworkAllowed: boolean;
  userContentAllowed: boolean;
  secretsAllowed: boolean;
  safeSummary: string;
  guardrailRefs: string[];
  redactionStatus: "redacted_summary_only";
}

export interface ManualSmokeReportSummaryItem {
  reportRef: string;
  requestRef: string;
  validationStatus: string;
  endpointSummary: string;
  modelIdSummary: string;
  fixedPromptHash: string;
  responseOrigin: string;
  responsePreviewShown: boolean;
  modelOutputAuthoritative: boolean;
  reasonCodes: string[];
  redactionStatus: "redacted_summary_only";
  safeMessage: string;
  createdAt: string;
}

export interface M18RuntimeData {
  status: "mock_preview_only" | "summary_only";
  readOnly: boolean;
  validationOnly: boolean;
  mock: boolean;
  nonAuthoritative: boolean;
  boundarySummary: string;
  warningCodes: string[];
  localRuntimeSurfaces: LocalRuntimeSurfaceSummaryItem[];
  manualSmokeReports: ManualSmokeReportSummaryItem[];
}

export interface FileReviewBindingRefs {
  reviewPacketRef: string;
  previewResultRef: string;
  redactionSummaryRef: string;
  fileRef: string;
  safePathRef: string;
}

export interface FileReviewReceiptPlanSummary {
  receiptPlanRef: string;
  rawContentStored: boolean;
  unredactedPreviewStored: boolean;
  rawAbsolutePathStored: boolean;
  approvalCaptured: boolean;
  approvalPersisted: boolean;
  contextProposalCreated: boolean;
  contextInjectionPerformed: boolean;
  memoryWritePerformed: boolean;
  exportPerformed: boolean;
  executionPerformed: boolean;
  safeSummary: string;
}

export type FileReviewApprovalCaptureStatus =
  | "approved_for_review_only"
  | "denied_for_review"
  | "not_captured";

export interface FileReviewApprovalCaptureSummary {
  status: FileReviewApprovalCaptureStatus;
  captured: boolean;
  persisted: boolean;
  reviewOnly: boolean;
  rawFileAccessAuthorized: boolean;
  contextProposalAuthorized: boolean;
  contextInjectionAuthorized: boolean;
  memoryWriteAuthorized: boolean;
  exportAuthorized: boolean;
  executionAuthorized: boolean;
  executionPerformed: boolean;
  safeMessage: string;
}

export interface FileReviewPacketSummary {
  reviewPacketRef: string;
  status: "ready_for_review" | "review_only" | "blocked";
  actorSummary: string;
  dataClassification: string;
  redactedPreview: string;
  redactionSummary: string;
  bindingRefs: FileReviewBindingRefs;
  reviewDecisionStatus: string;
  approvalGateContractStatus: string;
  receiptPlan: FileReviewReceiptPlanSummary;
  approvalCapture: FileReviewApprovalCaptureSummary;
  reasonCodes: string[];
  authorityWarnings: string[];
  redactionStatus: "redacted_summary_only";
  previewOnly: boolean;
  readOnly: boolean;
  mock: boolean;
  nonAuthoritative: boolean;
}

export interface M36FileReviewData {
  status: "mock_review_only" | "review_only";
  readOnly: boolean;
  previewOnly: boolean;
  mock: boolean;
  nonAuthoritative: boolean;
  boundarySummary: string;
  captureBoundarySummary: string;
  warningCodes: string[];
  packets: FileReviewPacketSummary[];
}

export interface ContextProposalBindingRefs {
  proposalRef: string;
  approvalRef: string;
  reviewPacketRef: string;
  previewResultRef: string;
  redactionSummaryRef: string;
  fileRef: string;
  safePathRef: string;
  actorRef: string;
}

export interface ContextProposalSectionSummary {
  sectionRef: string;
  title: string;
  redactedContent: string;
  sourceRef: string;
  redacted: boolean;
  bounded: boolean;
  nonAuthoritative: boolean;
}

export interface ContextProposalReceiptPlanSummary {
  receiptPlanRef: string;
  safeSummary: string;
  rawContentStored: boolean;
  fullFileContentStored: boolean;
  unredactedPreviewStored: boolean;
  contextInjected: boolean;
  openwebuiHandoffPerformed: boolean;
  memoryWritePerformed: boolean;
  exportPerformed: boolean;
  executionPerformed: boolean;
}

export interface ContextProposalAuthoritySummary {
  contextInjectionAuthorized: boolean;
  openwebuiHandoffAuthorized: boolean;
  modelCallAuthorized: boolean;
  memoryWriteAuthorized: boolean;
  exportAuthorized: boolean;
  executionAuthorized: boolean;
  rawFileAccessAuthorized: boolean;
  truthAuthorityClaimed: boolean;
}

export interface ContextProposalSummary {
  proposalRef: string;
  status: "proposal_ready_for_review" | "review_only" | "blocked";
  proposalOnly: boolean;
  nonAuthoritative: boolean;
  sourceSummary: string;
  safeSummary: string;
  dataClassification: string;
  bindingRefs: ContextProposalBindingRefs;
  sourceChainRefs: string[];
  sections: ContextProposalSectionSummary[];
  redactionVerificationStatus: string;
  decisionStatus: string;
  receiptPlan: ContextProposalReceiptPlanSummary;
  authority: ContextProposalAuthoritySummary;
  reasonCodes: string[];
  authorityWarnings: string[];
  redactionStatus: "redacted_summary_only";
  previewOnly: boolean;
  readOnly: boolean;
  mock: boolean;
}

export interface M39ContextProposalData {
  status: "mock_review_only" | "review_only";
  readOnly: boolean;
  previewOnly: boolean;
  mock: boolean;
  nonAuthoritative: boolean;
  boundarySummary: string;
  warningCodes: string[];
  proposals: ContextProposalSummary[];
}

export type MacOSSetupStepStatus =
  | "planned"
  | "ready"
  | "dry_run_only"
  | "approval_required"
  | "blocked"
  | "manual_only";

export interface MacOSSetupAssistantStep {
  stepId: string;
  label: string;
  kind: string;
  status: MacOSSetupStepStatus;
  safeSummary: string;
  routeRefs: string[];
  detailPreview: string[];
  logPreview: string[];
  approvalRequired: boolean;
  setupApprovalRef?: string;
  receiptRef: string;
  rollbackRef: string;
  latencyRef?: string;
  reasonCodes: string[];
  nextSafeAction: string;
}

export interface MacOSSetupModelRecommendation {
  recommendationRef: string;
  modelRef: string;
  displayName: string;
  fitSummary: string;
  recommendedFor: string;
  memoryBucket: string;
  diskBucket: string;
  privacySummary: string;
  approvalRequiredBeforeDownload: boolean;
  selectedByDefault: boolean;
  reasonCodes: string[];
}

export interface MacOSSetupBridgePreview {
  bridgeRef: string;
  label: string;
  status: MacOSSetupStepStatus;
  safeSummary: string;
  enablementDefault: string;
  approvalRequired: boolean;
  reasonCodes: string[];
}

export interface MacOSSetupApprovalEnvelope {
  envelopeRef: string;
  status: string;
  setupStepId: string;
  setupStepKind: string;
  safeSummary: string;
  requestedScopeRefs: string[];
  approvalRequestRef: string;
  expectedReceiptRef: string;
  rollbackPlanRef: string;
  idempotencyKeyRef: string;
  riskClass: string;
  sideEffectClass: string;
  notScopedActions: string[];
  blockedRuntimeAuthority: string[];
  evidenceRefs: string[];
  verifierRefs: string[];
  operatorNextAction: string;
  staleStateHandling: string;
  redactionSummary: string;
  dryRunOnly: boolean;
  approvalRequired: boolean;
  approvalRefIsIdentifierOnly: boolean;
  exactScopeRequired: boolean;
  idempotencyRequired: boolean;
  rollbackRequired: boolean;
  redactionRequired: boolean;
  disabledByDefault: boolean;
  reasonCodes: string[];
}

export interface MacOSSetupReceiptPlan {
  receiptPlanRef: string;
  auditRef: string;
  latencyRef: string;
  safeSummary: string;
  receiptCreated: boolean;
  auditEventCreated: boolean;
  terminalLogStored: boolean;
  promptStored: boolean;
  providerPayloadStored: boolean;
  credentialMaterialStored: boolean;
}

export interface MacOSSetupRollbackPlan {
  rollbackPlanRef: string;
  uninstallRef: string;
  safeSummary: string;
  rollbackAvailableAfterApproval: boolean;
  rollbackExecuted: boolean;
}

export interface MacOSSetupAssistantData {
  planRef: string;
  status: MacOSSetupStepStatus;
  macosFirst: boolean;
  localFirst: boolean;
  disabledByDefault: boolean;
  nativeMacosAppReady: boolean;
  controlCenterPreviewReady: boolean;
  setupQuestionAssistantEnabled: boolean;
  modelOutputAuthoritative: boolean;
  installerSideEffectsEnabled: boolean;
  visualShellRef: string;
  steps: MacOSSetupAssistantStep[];
  modelRecommendations: MacOSSetupModelRecommendation[];
  bridgePreviews: MacOSSetupBridgePreview[];
  approvalEnvelopes: MacOSSetupApprovalEnvelope[];
  receiptPlan: MacOSSetupReceiptPlan;
  rollbackPlan: MacOSSetupRollbackPlan;
  blockedCapabilities: string[];
  nextSteps: string[];
  morningReviewChecklist: string[];
}

export interface ControlCenterData {
  manifest: ControlCenterManifest;
  dashboard: ControlCenterDashboardSnapshot;
  status: ControlCenterStatus;
  routes: ApiRouteInventory;
  runtimeReadiness: RuntimeReadinessReport;
  capabilityMatrix: RuntimeCapabilityMatrix;
  m15Review: M15ReviewData;
  m16Trace: M16TraceData;
  m17Knowledge: M17KnowledgeData;
  m18Runtime: M18RuntimeData;
  m36FileReview: M36FileReviewData;
  m39ContextProposals: M39ContextProposalData;
  macosSetupAssistant: MacOSSetupAssistantData;
  founderToday: FounderLoopTodaySummary;
  founderActionsInbox: FounderLoopActionsInbox;
  founderMorningBriefing: FounderLoopMorningBriefing;
  founderStorageStatus: FounderLoopStorageStatus;
  source: "api" | "mock";
  connection: BackendConnectionSummary;
}
